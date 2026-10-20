#!/usr/bin/env python3
"""Behavioral checks for scripts/cook.py. Each test calls the CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

COOK = Path(__file__).resolve().parent / "cook.py"
FAILURES = []


def run(home: Path, scope: Path | None, *args: str, extra_env: dict | None = None):
    env = os.environ.copy()
    env["LET_ME_COOK_HOME"] = str(home)
    if scope is None:
        env.pop("LET_ME_COOK_SCOPE", None)
    else:
        env["LET_ME_COOK_SCOPE"] = str(scope)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(COOK), *args],
        env=env,
        capture_output=True,
        text=True,
    )


def kv(text: str) -> dict:
    found = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            found[key] = value
    return found


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS {name}")
        return
    FAILURES.append(name)
    print(f"FAIL {name} {detail}")


def evidence(winner: str, other: str, winner_path: str, other_path: str) -> dict:
    return {
        "summary": "Replace the repeated manual step with one file",
        "baseline_measurement": "baseline failed 2 of 2 checks",
        "check_command": "python3 checks/waste_check.py --target note.txt",
        "baseline_failure": "FAIL repeated manual step\nFAIL copied log lines\n2 checks failed",
        "fairness": "the check counts the repeated manual step itself, so it fails before the fix and passes after it",
        "candidates": [
            {"name": winner, "path": winner_path, "measurement": "winner passed 2 of 2 checks"},
            {"name": other, "path": other_path, "measurement": "other passed 0 of 2 checks"},
        ],
        "winner": winner,
        "result": "winner passed 2 of 2; other passed 0 of 2",
        "value": "the failed checks now pass without a new review step",
        "risks": "the file is the only copy under test",
        "rollback": "run rollback on this id to restore the snapshot",
    }


def write_pair(experiment: Path, winner_text: str, other_text: str = "other\n"):
    winner = experiment / "candidates" / "winner.txt"
    other = experiment / "candidates" / "other.txt"
    winner.write_text(winner_text, encoding="utf-8")
    other.write_text(other_text, encoding="utf-8")
    payload = evidence("winner", "other", "candidates/winner.txt", "candidates/other.txt")
    path = experiment / "evidence.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_path_override_beats_xdg() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home = root / "home"
        xdg = root / "xdg"
        proc = run(home, None, "path", extra_env={"XDG_STATE_HOME": str(xdg)})
        check("path override", proc.returncode == 0 and proc.stdout.strip() == str(home.resolve()), proc.stdout + proc.stderr)


def test_path_uses_xdg() -> None:
    with tempfile.TemporaryDirectory() as raw:
        xdg = Path(raw) / "xdg"
        env = os.environ.copy()
        env.pop("LET_ME_COOK_HOME", None)
        env["XDG_STATE_HOME"] = str(xdg)
        proc = subprocess.run([sys.executable, str(COOK), "path"], env=env, capture_output=True, text=True)
        expected = str((xdg / "let-me-cook").resolve())
        check("path xdg", proc.returncode == 0 and proc.stdout.strip() == expected, proc.stdout + proc.stderr)


def test_experiment_does_not_change_live() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        proc = run(home, scope, "begin", "--slug", "keep-live", "--target", str(live), "--summary", "keep the live file stable")
        info = kv(proc.stdout)
        experiment = Path(info["experiment"])
        (experiment / "candidates" / "winner.txt").write_text("changed\n", encoding="utf-8")
        check(
            "live untouched by experiment",
            proc.returncode == 0 and live.read_text(encoding="utf-8") == "original\n",
            proc.stderr,
        )
        check(
            "baseline copy kept",
            (experiment / "baseline" / "note.txt").read_text(encoding="utf-8") == "original\n",
            "",
        )


def test_leak_blocks_propose() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "leak", "--target", str(live), "--summary", "detect a live edit")
        info = kv(begun.stdout)
        live.write_text("mutated\n", encoding="utf-8")
        checked = run(home, scope, "check", info["id"])
        evidence_path = write_pair(Path(info["experiment"]), "winner\n")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        check(
            "leak blocks propose",
            checked.returncode == 2
            and "match=no" in checked.stdout
            and proposed.returncode == 2
            and live.read_text(encoding="utf-8") == "mutated\n"
            and evidence_path.is_file(),
            proposed.stderr,
        )


def test_reject_preserves_live() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "skip-me", "--target", str(live), "--summary", "a change we will reject")
        info = kv(begun.stdout)
        write_pair(Path(info["experiment"]), "winner\n")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        rejected = run(home, scope, "reject", info["id"], "--reason", "captain rejected this change")
        listed = run(home, scope, "list")
        check(
            "reject preserves live",
            proposed.returncode == 0
            and rejected.returncode == 0
            and "match=yes" in rejected.stdout
            and live.read_text(encoding="utf-8") == "original\n"
            and f"{info['id']}\trejected\tskip-me\t" in listed.stdout,
            rejected.stderr + listed.stdout,
        )


def test_approve_and_rollback() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "ship-it", "--target", str(live), "--summary", "ship the measured winner")
        info = kv(begun.stdout)
        write_pair(Path(info["experiment"]), "winner\n")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        approved = run(home, scope, "approve", info["id"])
        verified = run(home, scope, "verify", info["id"])
        deployed = live.read_text(encoding="utf-8")
        rollback_dir = Path(kv(approved.stdout)["rollback"])
        snapshot = (rollback_dir / "bytes").read_text(encoding="utf-8") if approved.returncode == 0 else ""
        rolled = run(home, scope, "rollback", info["id"])
        check(
            "approve writes winner and keeps rollback",
            proposed.returncode == 0
            and approved.returncode == 0
            and deployed == "winner\n"
            and "match=yes" in verified.stdout
            and snapshot == "original\n",
            approved.stderr + verified.stdout,
        )
        check(
            "rollback restores original",
            rolled.returncode == 0 and live.read_text(encoding="utf-8") == "original\n" and "match=yes" in rolled.stdout,
            rolled.stderr,
        )


def test_new_file_rollback_removes_it() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "new.txt"
        begun = run(home, scope, "begin", "--slug", "new-file", "--target", str(live), "--summary", "create a missing file")
        info = kv(begun.stdout)
        write_pair(Path(info["experiment"]), "created\n")
        run(home, scope, "propose", info["id"], "evidence.json")
        approved = run(home, scope, "approve", info["id"])
        created = live.read_text(encoding="utf-8") == "created\n"
        rolled = run(home, scope, "rollback", info["id"])
        check(
            "rollback removes a created file",
            approved.returncode == 0 and created and rolled.returncode == 0 and not live.exists(),
            rolled.stderr,
        )


def test_rejection_gates_the_slug() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "skip-me", "--target", str(live), "--summary", "reject then block")
        info = kv(begun.stdout)
        rejected = run(home, scope, "reject", info["id"], "--reason", "not worth deploying")
        gated = run(home, scope, "gate", "--slug", "skip-me")
        again = run(home, scope, "begin", "--slug", "skip-me", "--target", str(live), "--summary", "try the same slug again")
        reopened = run(
            home,
            scope,
            "begin",
            "--slug",
            "skip-me",
            "--target",
            str(live),
            "--summary",
            "new evidence allows a retry",
            "--new-evidence",
            "a later session failed the same check again",
        )
        check(
            "rejection blocks the same slug",
            rejected.returncode == 0 and gated.returncode == 3 and info["id"] in gated.stdout and again.returncode == 3,
            gated.stdout + again.stderr,
        )
        check(
            "new evidence reopens the slug",
            reopened.returncode == 0 and "id=" in reopened.stdout and live.read_text(encoding="utf-8") == "original\n",
            reopened.stderr,
        )


def test_credential_and_scope() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        secret = "super-secret-value-do-not-copy"
        env_file = scope / ".env"
        env_file.write_text(secret + "\n", encoding="utf-8")
        refused = run(home, scope, "begin", "--slug", "creds", "--target", str(env_file), "--summary", "must not copy credentials")
        outside = root / "outside.txt"
        outside.write_text("leave-me\n", encoding="utf-8")
        escaped = run(home, scope, "begin", "--slug", "escape", "--target", str(outside), "--summary", "must stay in scope")
        leaked = any(secret in path.read_text(encoding="utf-8", errors="replace") for path in home.rglob("*") if path.is_file()) if home.exists() else False
        check(
            "credential path is not copied",
            refused.returncode == 2 and not leaked and env_file.read_text(encoding="utf-8") == secret + "\n",
            refused.stderr,
        )
        check(
            "scope blocks an outside target",
            escaped.returncode == 2 and outside.read_text(encoding="utf-8") == "leave-me\n",
            escaped.stderr,
        )


def test_one_open_decision() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        first = scope / "a.txt"
        second = scope / "b.txt"
        first.write_text("a\n", encoding="utf-8")
        second.write_text("b\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "first", "--target", str(first), "--summary", "the only open experiment")
        other = run(home, scope, "begin", "--slug", "second", "--target", str(second), "--summary", "a second experiment")
        check(
            "second begin is refused",
            begun.returncode == 0 and other.returncode == 2 and second.read_text(encoding="utf-8") == "b\n",
            other.stderr,
        )


def test_secret_evidence_is_not_recorded() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "secret", "--target", str(live), "--summary", "refuse a secret in evidence")
        info = kv(begun.stdout)
        experiment = Path(info["experiment"])
        write_pair(experiment, "winner\n")
        planted = "ghp_" + ("a" * 24)
        payload = evidence("winner", "other", "candidates/winner.txt", "candidates/other.txt")
        payload["result"] = "winner passed and token " + planted
        evidence_path = experiment / "evidence.json"
        evidence_path.write_text(json.dumps(payload), encoding="utf-8")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        ledger = (home / "ledger.json").read_text(encoding="utf-8")
        check(
            "secret evidence is dropped",
            proposed.returncode == 2
            and planted not in proposed.stdout
            and planted not in proposed.stderr
            and planted not in ledger
            and not evidence_path.exists()
            and live.read_text(encoding="utf-8") == "original\n",
            proposed.stderr,
        )


def test_swapped_winner_does_not_deploy() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "swap", "--target", str(live), "--summary", "block a swapped winner")
        info = kv(begun.stdout)
        experiment = Path(info["experiment"])
        write_pair(experiment, "winner\n")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        (experiment / "candidates" / "winner.txt").write_text("swapped\n", encoding="utf-8")
        approved = run(home, scope, "approve", info["id"])
        check(
            "swapped winner is not deployed",
            proposed.returncode == 0
            and approved.returncode == 2
            and live.read_text(encoding="utf-8") == "original\n",
            approved.stderr,
        )


def test_noop_is_refused() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "noop", "--target", str(live), "--summary", "refuse an unchanged winner")
        info = kv(begun.stdout)
        write_pair(Path(info["experiment"]), "original\n")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        check(
            "unchanged winner is not a proposal",
            proposed.returncode == 2 and live.read_text(encoding="utf-8") == "original\n",
            proposed.stderr,
        )


def test_drop_closes_without_blocking() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "weak", "--target", str(live), "--summary", "an experiment that does not earn a proposal")
        info = kv(begun.stdout)
        dropped = run(home, scope, "drop", info["id"], "--reason", "the check showed no gain")
        gated = run(home, scope, "gate", "--slug", "weak")
        other = scope / "other.txt"
        other.write_text("other\n", encoding="utf-8")
        again = run(home, scope, "begin", "--slug", "next", "--target", str(other), "--summary", "a later experiment can start")
        check(
            "drop does not deploy or block",
            dropped.returncode == 0
            and "match=yes" in dropped.stdout
            and live.read_text(encoding="utf-8") == "original\n"
            and gated.returncode == 0
            and gated.stdout.strip() == "clear"
            and again.returncode == 0,
            dropped.stderr + gated.stdout + again.stderr,
        )


def test_stop_records_none() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home = root / "home"
        scope = root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        stopped = run(home, scope, "stop", "--status", "none", "--reason", "no systemic gain in the recent sessions")
        info = kv(stopped.stdout)
        verified = run(home, scope, "verify", info["id"])
        check(
            "none does not touch a file",
            stopped.returncode == 0
            and "status=none" in stopped.stdout
            and verified.stdout.strip() == "no-target"
            and live.read_text(encoding="utf-8") == "original\n",
            stopped.stderr + verified.stdout,
        )


def test_evidence_requires_a_fair_check() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        live = scope / "note.txt"
        live.write_text("original\n", encoding="utf-8")
        begun = run(home, scope, "begin", "--slug", "fair-check", "--target", str(live), "--summary", "require a fair check in evidence")
        info = kv(begun.stdout)
        experiment = Path(info["experiment"])
        write_pair(experiment, "winner\n")
        payload = evidence("winner", "other", "candidates/winner.txt", "candidates/other.txt")
        del payload["fairness"]
        (experiment / "evidence.json").write_text(json.dumps(payload), encoding="utf-8")
        refused = run(home, scope, "propose", info["id"], "evidence.json")
        check(
            "evidence without fairness is refused",
            refused.returncode == 2 and "fairness" in refused.stderr and live.read_text(encoding="utf-8") == "original\n",
            refused.stderr,
        )
        payload = evidence("winner", "other", "candidates/winner.txt", "candidates/other.txt")
        payload["baseline_failure"] = "FAIL repeated manual step\nFAIL copied log lines\nFAIL no counter\n3 checks failed"
        (experiment / "evidence.json").write_text(json.dumps(payload), encoding="utf-8")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        check(
            "propose shows the check and its baseline failure",
            proposed.returncode == 0
            and "check_command=python3 checks/waste_check.py" in proposed.stdout
            and "3 checks failed" in proposed.stdout
            and "fairness=" in proposed.stdout,
            proposed.stderr + proposed.stdout,
        )


def test_stand_in_reports_the_natural_path() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        natural = root / "natural.txt"
        natural.write_text("original\n", encoding="utf-8")
        copy = scope / "natural.txt"
        copy.write_text("original\n", encoding="utf-8")
        begun = run(
            home,
            scope,
            "begin",
            "--slug",
            "stand-in",
            "--target",
            str(copy),
            "--summary",
            "prove the waste on a copy",
            "--stand-in-for",
            str(natural),
        )
        info = kv(begun.stdout)
        write_pair(Path(info["experiment"]), "winner\n")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        approved = run(home, scope, "approve", info["id"])
        verified = run(home, scope, "verify", info["id"])
        check(
            "stand-in deploy reports the natural path unchanged",
            begun.returncode == 0
            and proposed.returncode == 0
            and approved.returncode == 0
            and copy.read_text(encoding="utf-8") == "winner\n"
            and natural.read_text(encoding="utf-8") == "original\n"
            and f"stand_in_for={natural}" in verified.stdout
            and "natural_match=yes" in verified.stdout
            and "match=yes" in verified.stdout,
            approved.stderr + verified.stdout,
        )
        natural.write_text("edited later\n", encoding="utf-8")
        stale = run(home, scope, "verify", info["id"])
        check(
            "a changed natural path fails verify",
            stale.returncode == 2 and "natural_match=no" in stale.stdout,
            stale.stdout,
        )


def test_stand_in_refusals() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        home, scope = root / "home", root / "scope"
        scope.mkdir()
        copy = scope / "note.txt"
        copy.write_text("original\n", encoding="utf-8")
        natural = root / "natural.txt"
        natural.write_text("original\n", encoding="utf-8")
        same = run(
            home,
            scope,
            "begin",
            "--slug",
            "same",
            "--target",
            str(copy),
            "--summary",
            "a copy cannot stand in for itself",
            "--stand-in-for",
            str(copy),
        )
        env_file = scope / ".env"
        env_file.write_text("TOKEN=not-a-real-secret\n", encoding="utf-8")
        creds = run(
            home,
            scope,
            "begin",
            "--slug",
            "creds",
            "--target",
            str(copy),
            "--summary",
            "a credential path cannot stand in",
            "--stand-in-for",
            str(env_file),
        )
        moved = run(
            home,
            scope,
            "begin",
            "--slug",
            "moved",
            "--target",
            str(copy),
            "--summary",
            "the natural path moved during the run",
            "--stand-in-for",
            str(natural),
        )
        info = kv(moved.stdout)
        write_pair(Path(info["experiment"]), "winner\n")
        natural.write_text("someone else edited this\n", encoding="utf-8")
        proposed = run(home, scope, "propose", info["id"], "evidence.json")
        check(
            "stand-in refuses itself and a credential path",
            same.returncode == 2
            and creds.returncode == 2
            and copy.read_text(encoding="utf-8") == "original\n",
            same.stderr + creds.stderr,
        )
        check(
            "a changed natural path blocks propose",
            moved.returncode == 0 and proposed.returncode == 2 and "natural path changed" in proposed.stderr,
            proposed.stderr,
        )


def main() -> int:
    test_path_override_beats_xdg()
    test_path_uses_xdg()
    test_experiment_does_not_change_live()
    test_leak_blocks_propose()
    test_reject_preserves_live()
    test_approve_and_rollback()
    test_new_file_rollback_removes_it()
    test_rejection_gates_the_slug()
    test_credential_and_scope()
    test_one_open_decision()
    test_secret_evidence_is_not_recorded()
    test_swapped_winner_does_not_deploy()
    test_noop_is_refused()
    test_drop_closes_without_blocking()
    test_stop_records_none()
    test_evidence_requires_a_fair_check()
    test_stand_in_reports_the_natural_path()
    test_stand_in_refusals()
    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nall passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

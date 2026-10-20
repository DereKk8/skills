#!/usr/bin/env python3
"""Ledger and isolation gate for the let-me-cook skill.

The agent chooses the improvement. This script only keeps the contract:
one local ledger, experiments off the live file, no secrets on disk here,
no deploy without a recorded proposal, and no silent retry of a rejection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SECRET_RE = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
CRED_FILE_RE = re.compile(
    r"(?i)^(\.env(\..*)?|id_(rsa|ed25519|ecdsa|dsa)|credentials\.json|"
    r"secrets\.json|.+\.(pem|p12|pfx|key)|token|access_token|refresh_token|.*-token)$"
)
CRED_PARTS = {".ssh", ".aws", ".gnupg", "secrets", "credentials", "test-identity"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BLOCKING = {"rejected", "rolled-back"}
ACTIVE = {"open", "proposed"}
EVIDENCE_KEYS = (
    "summary",
    "baseline_measurement",
    "candidates",
    "winner",
    "result",
    "value",
    "risks",
    "rollback",
    "check_command",
    "baseline_failure",
    "fairness",
)


class Gate(SystemExit):
    def __init__(self, message: str, code: int = 2):
        self.message = message
        super().__init__(code)


def die(message: str, code: int = 2) -> None:
    raise Gate(message, code)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def allocate_id(slug: str) -> str:
    base = f"{stamp()}-{slug}"
    taken = {item.get("id") for item in decisions()}
    root = state_home() / "experiments"
    candidate = base
    n = 2
    while candidate in taken or (root / candidate).exists():
        candidate = f"{base}-{n}"
        n += 1
        if n > 100:
            die("could not allocate an id")
    return candidate


def state_home() -> Path:
    override = os.environ.get("LET_ME_COOK_HOME")
    if override:
        return Path(override).expanduser().resolve()
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg).expanduser().resolve() / "let-me-cook"
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local).expanduser().resolve() / "let-me-cook"
    return Path.home() / ".local" / "state" / "let-me-cook"


def ledger_path() -> Path:
    return state_home() / "ledger.json"


def one_line(text: str, label: str, min_len: int = 1, max_len: int = 500) -> str:
    if not isinstance(text, str) or "\n" in text or "\r" in text:
        die(f"{label} must be one line")
    cleaned = text.strip()
    if not min_len <= len(cleaned) <= max_len:
        die(f"{label} must be {min_len}-{max_len} characters")
    if SECRET_RE.search(cleaned):
        die(f"{label} contains a secret")
    return cleaned


def multi_line(text: str, label: str, min_len: int = 1, max_len: int = 2000, max_lines: int = 15) -> str:
    if not isinstance(text, str):
        die(f"{label} must be text")
    lines = text.strip().splitlines()
    if not lines:
        die(f"{label} must not be empty")
    if len(lines) > max_lines:
        die(f"{label} must be at most {max_lines} lines")
    cleaned = "\n".join(line.rstrip() for line in lines).strip()
    if not min_len <= len(cleaned) <= max_len:
        die(f"{label} must be {min_len}-{max_len} characters")
    if SECRET_RE.search(cleaned):
        die(f"{label} contains a secret")
    return cleaned


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_hash(path: Path):
    if not path.exists():
        return None
    if not path.is_file():
        die(f"{path} is not a file")
    return sha256_file(path)


def scan_bytes(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        die(f"{path.name} is not utf-8 text")
    if SECRET_RE.search(text):
        path.unlink()
        die(f"removed {path.name} because it contains a secret; nothing was recorded")


def scope_roots():
    raw = os.environ.get("LET_ME_COOK_SCOPE")
    if not raw:
        return None
    return [Path(part).expanduser().resolve() for part in raw.split(os.pathsep) if part]


def in_scope(path: Path) -> bool:
    roots = scope_roots()
    if roots is None:
        return True
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in roots)


def is_credential(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & CRED_PARTS:
        return True
    if "infisical" in parts and "token" in parts:
        return True
    return bool(CRED_FILE_RE.match(path.name))


def resolve_target(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        die("target must be an absolute path")
    resolved = path.resolve()
    if is_credential(path) or is_credential(resolved):
        die("target looks like a credential path; refused before reading it")
    if not in_scope(resolved):
        die("target is outside LET_ME_COOK_SCOPE")
    home = state_home()
    if resolved == home or home in resolved.parents:
        die("target must stay outside the let-me-cook state directory")
    return resolved


def resolve_natural(raw: str) -> Path:
    """Resolve the natural path a stand-in copy stands for.

    That path is deliberately allowed outside LET_ME_COOK_SCOPE, because the
    unauthorized case is the reason a stand-in exists. It is only hashed, never
    written.
    """
    path = Path(raw).expanduser()
    if not path.is_absolute():
        die("stand-in-for must be an absolute path")
    resolved = path.resolve()
    if is_credential(path) or is_credential(resolved):
        die("stand-in-for looks like a credential path; refused before reading it")
    home = state_home()
    if resolved == home or home in resolved.parents:
        die("stand-in-for must stay outside the let-me-cook state directory")
    return resolved


def check_slug(slug: str) -> str:
    if not isinstance(slug, str) or not SLUG_RE.match(slug) or len(slug) > 48:
        die("slug must be lowercase words joined by single hyphens, at most 48 characters")
    return slug


def load_ledger() -> dict:
    path = ledger_path()
    if not path.exists():
        return {"version": 1, "decisions": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"ledger cannot be read: {exc}")
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("decisions"), list):
        die("ledger is not version 1")
    return data


def save_ledger(data: dict) -> None:
    blob = json.dumps(data, indent=1) + "\n"
    if SECRET_RE.search(blob):
        die("refusing to write a secret into the ledger")
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(blob, encoding="utf-8")
    os.replace(temporary, path)


def decisions() -> list:
    return load_ledger()["decisions"]


def find(decision_id: str) -> dict:
    for item in decisions():
        if item.get("id") == decision_id:
            return item
    die(f"no decision {decision_id}")
    return {}


def latest_blocking(slug: str):
    found = None
    for item in decisions():
        if item.get("slug") == slug and item.get("status") in BLOCKING:
            found = item
    return found


def active():
    for item in decisions():
        if item.get("status") in ACTIVE:
            return item
    return None


def acquire_lock(home: Path) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    lock = home / ".lock"
    deadline = time.time() + 10
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.time() > deadline:
                die("ledger lock is held")
            try:
                if time.time() - lock.stat().st_mtime > 60:
                    lock.unlink()
                    continue
            except FileNotFoundError:
                continue
            time.sleep(0.05)
            continue
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return lock


def under_experiment(experiment: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or relative.startswith(("/", "\\")):
        die("candidate path must be relative to the experiment directory")
    parts = Path(relative).parts
    if ".." in parts:
        die("candidate path must stay inside the experiment directory")
    full = (experiment / relative).resolve()
    root = experiment.resolve()
    if full != root and root not in full.parents:
        die("candidate path must stay inside the experiment directory")
    return full


def cmd_path(_args) -> int:
    print(state_home())
    return 0


def cmd_list(_args) -> int:
    for item in decisions():
        summary = item.get("summary") or ""
        print(f"{item['id']}\t{item['status']}\t{item.get('slug', '')}\t{summary}")
    return 0


def cmd_show(args) -> int:
    print(json.dumps(find(args.id), indent=1))
    return 0


def cmd_gate(args) -> int:
    slug = check_slug(args.slug)
    blocked = latest_blocking(slug)
    if blocked is None:
        print("clear")
        return 0
    if args.new_evidence:
        one_line(args.new_evidence, "new evidence", min_len=12, max_len=500)
        print(f"new-evidence\t{blocked['id']}")
        return 0
    print(f"rejected\t{blocked['id']}\t{blocked.get('summary', '')}")
    return 3


def cmd_begin(args) -> int:
    slug = check_slug(args.slug)
    summary = one_line(args.summary, "summary", min_len=8, max_len=200)
    current = active()
    if current is not None:
        die(f"a decision is already open: {current['id']}")
    blocked = latest_blocking(slug)
    new_evidence = None
    if blocked is not None:
        if not args.new_evidence:
            print(f"rejected\t{blocked['id']}\t{blocked.get('summary', '')}", file=sys.stderr)
            return 3
        new_evidence = one_line(args.new_evidence, "new evidence", min_len=12, max_len=500)
    target = resolve_target(args.target)
    stand_in_for = None
    natural_sha256 = None
    if args.stand_in_for:
        stand_in_for = resolve_natural(args.stand_in_for)
        if stand_in_for == target:
            die("stand-in-for must name the natural path, not the target itself")
        natural_sha256 = file_hash(stand_in_for)
    if target.exists() and not target.is_file():
        die("target must be a file or a path that does not exist yet")
    if not target.exists() and not target.parent.is_dir():
        die("target parent does not exist")
    if target.exists() and target.stat().st_size > 2 * 1024 * 1024:
        die("target is larger than 2MB")
    if target.exists():
        try:
            preview = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            die("target is not utf-8 text")
        if SECRET_RE.search(preview):
            die("target contains a secret; refused before copying it")
    baseline = file_hash(target)
    decision_id = allocate_id(slug)
    experiment = state_home() / "experiments" / decision_id
    baseline_dir = experiment / "baseline"
    baseline_dir.mkdir(parents=True)
    if target.exists():
        shutil.copyfile(target, baseline_dir / target.name)
    else:
        (baseline_dir / "MISSING").write_text("missing\n", encoding="utf-8")
    (experiment / "candidates").mkdir()
    record = {
        "id": decision_id,
        "slug": slug,
        "status": "open",
        "summary": summary,
        "target": str(target),
        "created": now(),
        "updated": now(),
        "baseline_sha256": baseline,
        "experiment": str(experiment),
        "stand_in_for": str(stand_in_for) if stand_in_for else None,
        "natural_sha256": natural_sha256,
        "new_evidence": new_evidence,
        "evidence": None,
        "rejection_reason": None,
        "isolation_held": None,
        "deploy": None,
    }
    data = load_ledger()
    data["decisions"].append(record)
    save_ledger(data)
    print(f"id={decision_id}")
    print(f"experiment={experiment}")
    print(f"target={target}")
    print(f"baseline_sha256={baseline or 'missing'}")
    return 0


def isolation_holds(item: dict) -> bool:
    return file_hash(Path(item["target"])) == item.get("baseline_sha256")


def natural_holds(item: dict) -> bool:
    """True when a stand-in run's natural path still has its recorded bytes."""
    natural = item.get("stand_in_for")
    if not natural:
        return True
    return file_hash(Path(natural)) == item.get("natural_sha256")


def cmd_check(args) -> int:
    item = find(args.id)
    if item.get("status") in {"none", "out-of-scope"}:
        print("no-target")
        return 0
    live = file_hash(Path(item["target"]))
    ok = live == item.get("baseline_sha256")
    print(f"live_sha256={live or 'missing'}")
    print(f"baseline_sha256={item.get('baseline_sha256') or 'missing'}")
    print("match=yes" if ok else "match=no")
    return 0 if ok else 2


def load_evidence(item: dict, raw_path: str) -> dict:
    experiment = Path(item["experiment"])
    path = under_experiment(experiment, raw_path) if not os.path.isabs(raw_path) else Path(raw_path).resolve()
    root = experiment.resolve()
    if path != root and root not in path.parents:
        die("evidence file must stay inside the experiment directory")
    if not path.is_file():
        die("evidence file is missing")
    if path.stat().st_size > 65536:
        die("evidence file is larger than 64KB")
    scan_bytes(path)
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        die("evidence file is not json")
    if not isinstance(evidence, dict):
        die("evidence must be a json object")
    missing = [key for key in EVIDENCE_KEYS if key not in evidence]
    if missing:
        die("evidence missing " + ", ".join(missing))
    cleaned = {
        "summary": one_line(evidence["summary"], "summary", min_len=8, max_len=200),
        "baseline_measurement": one_line(evidence["baseline_measurement"], "baseline_measurement", min_len=4),
        "check_command": one_line(evidence["check_command"], "check_command", min_len=4, max_len=300),
        "baseline_failure": multi_line(evidence["baseline_failure"], "baseline_failure", min_len=8),
        "fairness": one_line(evidence["fairness"], "fairness", min_len=20, max_len=600),
        "winner": one_line(evidence["winner"], "winner", min_len=1, max_len=48),
        "result": one_line(evidence["result"], "result", min_len=8),
        "value": one_line(evidence["value"], "value", min_len=8),
        "risks": one_line(evidence["risks"], "risks", min_len=4),
        "rollback": one_line(evidence["rollback"], "rollback", min_len=4),
    }
    candidates = evidence["candidates"]
    if not isinstance(candidates, list) or len(candidates) < 2:
        die("candidates must list at least two implementations")
    stored = []
    names = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            die("each candidate must be an object")
        name = one_line(candidate.get("name", ""), "candidate name", min_len=1, max_len=48)
        relative = candidate.get("path", "")
        measurement = one_line(candidate.get("measurement", ""), "measurement", min_len=4)
        full = under_experiment(experiment, relative)
        if not full.is_file():
            die(f"candidate file missing: {relative}")
        scan_bytes(full)
        digest = sha256_file(full)
        if name in names:
            die(f"duplicate candidate {name}")
        names.add(name)
        stored.append({"name": name, "path": relative, "measurement": measurement, "sha256": digest})
    if cleaned["winner"] not in names:
        die("winner must name one candidate")
    winner = next(item for item in stored if item["name"] == cleaned["winner"])
    if winner["sha256"] == item.get("baseline_sha256"):
        die("winner matches the baseline; that is not a change")
    cleaned["candidates"] = stored
    cleaned["winner_sha256"] = winner["sha256"]
    cleaned["winner_path"] = winner["path"]
    return cleaned


def cmd_propose(args) -> int:
    data = load_ledger()
    item = next((row for row in data["decisions"] if row["id"] == args.id), None)
    if item is None:
        die(f"no decision {args.id}")
    if item["status"] != "open":
        die(f"decision is {item['status']}, not open")
    if not isolation_holds(item):
        die("live target changed during the experiment; refusing to propose")
    if not natural_holds(item):
        die("the natural path changed during the experiment; refusing to propose")
    item["evidence"] = load_evidence(item, args.evidence)
    item["summary"] = item["evidence"]["summary"]
    item["status"] = "proposed"
    item["updated"] = now()
    item["isolation_held"] = True
    save_ledger(data)
    print(f"id={item['id']}")
    print("status=proposed")
    print(f"winner={item['evidence']['winner']}")
    print(f"winner_sha256={item['evidence']['winner_sha256']}")
    print(f"check_command={item['evidence']['check_command']}")
    print("baseline_failure:")
    print(item["evidence"]["baseline_failure"])
    print(f"fairness={item['evidence']['fairness']}")
    return 0


def cmd_drop(args) -> int:
    reason = one_line(args.reason, "reason", min_len=8, max_len=500)
    data = load_ledger()
    item = next((row for row in data["decisions"] if row["id"] == args.id), None)
    if item is None:
        die(f"no decision {args.id}")
    if item["status"] != "open":
        die("drop only an open experiment that was not proposed")
    held = isolation_holds(item)
    item["status"] = "dropped"
    item["rejection_reason"] = reason
    item["isolation_held"] = held
    item["updated"] = now()
    save_ledger(data)
    live = file_hash(Path(item["target"]))
    print(f"id={item['id']}")
    print("status=dropped")
    print(f"live_sha256={live or 'missing'}")
    print("match=yes" if live == item.get("baseline_sha256") else "match=no")
    return 0 if held else 2


def cmd_reject(args) -> int:
    reason = one_line(args.reason, "reason", min_len=8, max_len=500)
    data = load_ledger()
    item = next((row for row in data["decisions"] if row["id"] == args.id), None)
    if item is None:
        die(f"no decision {args.id}")
    if item["status"] not in ACTIVE:
        die(f"decision is {item['status']}, not waiting")
    held = isolation_holds(item)
    item["status"] = "rejected"
    item["rejection_reason"] = reason
    item["isolation_held"] = held
    item["updated"] = now()
    save_ledger(data)
    live = file_hash(Path(item["target"]))
    print(f"id={item['id']}")
    print("status=rejected")
    print(f"live_sha256={live or 'missing'}")
    print(f"baseline_sha256={item.get('baseline_sha256') or 'missing'}")
    print("match=yes" if live == item.get("baseline_sha256") else "match=no")
    return 0 if held else 2


def snapshot(item: dict) -> Path:
    rollback = state_home() / "rollbacks" / item["id"]
    if rollback.exists():
        shutil.rmtree(rollback)
    rollback.mkdir(parents=True)
    target = Path(item["target"])
    if target.exists():
        shutil.copyfile(target, rollback / "bytes")
    else:
        (rollback / "MISSING").write_text("missing\n", encoding="utf-8")
    return rollback


def restore(rollback: Path, target: Path) -> None:
    if (rollback / "MISSING").exists():
        if target.exists():
            target.unlink()
        return
    temporary = target.with_suffix(target.suffix + ".let-me-cook-tmp")
    shutil.copyfile(rollback / "bytes", temporary)
    os.replace(temporary, target)


def cmd_approve(args) -> int:
    data = load_ledger()
    item = next((row for row in data["decisions"] if row["id"] == args.id), None)
    if item is None:
        die(f"no decision {args.id}")
    if item["status"] != "proposed" or not item.get("evidence"):
        die("approve only a proposed decision that has evidence")
    if not isolation_holds(item):
        die("live target changed during the experiment; refusing to deploy")
    evidence = item["evidence"]
    winner = under_experiment(Path(item["experiment"]), evidence["winner_path"])
    if not winner.is_file():
        die("winner file is missing")
    scan_bytes(winner)
    digest = sha256_file(winner)
    if digest != evidence["winner_sha256"]:
        die("winner file changed after propose; refusing to deploy")
    if digest == item.get("baseline_sha256"):
        die("winner matches the baseline; refusing a no-op deploy")
    target = Path(item["target"])
    if not in_scope(target) or is_credential(target):
        die("target failed the scope check at deploy")
    rollback = snapshot(item)
    mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
    temporary = target.with_suffix(target.suffix + ".let-me-cook-tmp")
    try:
        shutil.copyfile(winner, temporary)
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    except OSError as exc:
        if temporary.exists():
            temporary.unlink()
        restore(rollback, target)
        die(f"deploy failed and the target was restored: {exc.strerror or 'os error'}")
    live = file_hash(target)
    if live != digest:
        restore(rollback, target)
        die("deploy verify failed; restored the target")
    item["status"] = "deployed"
    item["updated"] = now()
    item["deploy"] = {"sha256": digest, "rollback": str(rollback), "verified": True}
    save_ledger(data)
    print(f"id={item['id']}")
    print("status=deployed")
    print(f"live={target}")
    print(f"live_sha256={digest}")
    print(f"rollback={rollback}")
    return 0


def cmd_rollback(args) -> int:
    data = load_ledger()
    item = next((row for row in data["decisions"] if row["id"] == args.id), None)
    if item is None:
        die(f"no decision {args.id}")
    if item["status"] != "deployed" or not item.get("deploy"):
        die("rollback only a deployed decision")
    target = Path(item["target"])
    rollback = Path(item["deploy"]["rollback"])
    restore(rollback, target)
    live = file_hash(target)
    if live != item.get("baseline_sha256"):
        die("rollback did not restore the baseline bytes")
    item["status"] = "rolled-back"
    item["updated"] = now()
    item["isolation_held"] = True
    save_ledger(data)
    print(f"id={item['id']}")
    print("status=rolled-back")
    print(f"live_sha256={live or 'missing'}")
    print("match=yes")
    return 0


def cmd_stop(args) -> int:
    status = args.status
    if status not in {"none", "out-of-scope"}:
        die("status must be none or out-of-scope")
    reason = one_line(args.reason, "reason", min_len=8, max_len=500)
    slug = check_slug(args.slug) if args.slug else status
    if active() is not None:
        die("close the open decision before recording a stop")
    decision_id = allocate_id(slug)
    record = {
        "id": decision_id,
        "slug": slug,
        "status": status,
        "summary": reason,
        "target": None,
        "created": now(),
        "updated": now(),
        "baseline_sha256": None,
        "experiment": None,
        "stand_in_for": None,
        "natural_sha256": None,
        "new_evidence": None,
        "evidence": None,
        "rejection_reason": None,
        "isolation_held": None,
        "deploy": None,
    }
    data = load_ledger()
    data["decisions"].append(record)
    save_ledger(data)
    print(f"id={decision_id}")
    print(f"status={status}")
    return 0


def cmd_verify(args) -> int:
    item = find(args.id)
    if item["status"] in {"none", "out-of-scope"} or not item.get("target"):
        print("no-target")
        return 0
    target = Path(item["target"])
    live = file_hash(target)
    natural_ok = natural_holds(item)
    if item["status"] == "deployed":
        expected = item["deploy"]["sha256"]
        rollback = Path(item["deploy"]["rollback"])
        ok = live == expected and rollback.exists()
        print(f"live_sha256={live or 'missing'}")
        print(f"expected_sha256={expected}")
        print(f"rollback={rollback}")
        print("rollback_exists=yes" if rollback.exists() else "rollback_exists=no")
    else:
        expected = item.get("baseline_sha256")
        ok = live == expected
        print(f"live_sha256={live or 'missing'}")
        print(f"expected_sha256={expected or 'missing'}")
    if item.get("stand_in_for"):
        print(f"stand_in_for={item['stand_in_for']}")
        print(f"natural_sha256={item.get('natural_sha256') or 'missing'}")
        print("natural_match=yes" if natural_ok else "natural_match=no")
        ok = ok and natural_ok
    print("match=yes" if ok else "match=no")
    return 0 if ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("path", help="print the state directory")
    sub.add_parser("list", help="print id, status, slug, and summary")
    show = sub.add_parser("show", help="print one decision as json")
    show.add_argument("id")
    gate = sub.add_parser("gate", help="exit 3 when this slug was rejected or rolled back")
    gate.add_argument("--slug", required=True)
    gate.add_argument("--new-evidence")
    begin = sub.add_parser("begin", help="snapshot a target and open one experiment")
    begin.add_argument("--slug", required=True)
    begin.add_argument("--target", required=True)
    begin.add_argument("--summary", required=True)
    begin.add_argument("--stand-in-for", help="natural path this target is a copy of; never written")
    begin.add_argument("--new-evidence")
    check = sub.add_parser("check", help="exit 2 when the live target no longer matches the snapshot")
    check.add_argument("id")
    propose = sub.add_parser(
        "propose",
        help="record evidence for an open experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "evidence.json keys: summary, baseline_measurement, winner, result, "
            "value, risks, rollback, candidates, check_command, baseline_failure, "
            "and fairness.\n"
            "baseline_failure keeps the failing output word for word, up to 15 lines.\n"
            "fairness says why the check measures the claimed waste.\n"
            "candidates is at least two objects with name, path, and measurement.\n"
            "path is relative to the experiment directory."
        ),
    )
    propose.add_argument("id")
    propose.add_argument("evidence")
    drop = sub.add_parser("drop", help="close an open experiment that did not earn a proposal")
    drop.add_argument("id")
    drop.add_argument("--reason", required=True)
    reject = sub.add_parser("reject", help="record a rejection and do not change the target")
    reject.add_argument("id")
    reject.add_argument("--reason", required=True)
    approve = sub.add_parser("approve", help="copy the recorded winner onto the target")
    approve.add_argument("id")
    rollback = sub.add_parser("rollback", help="restore the snapshot taken at approve")
    rollback.add_argument("id")
    stop = sub.add_parser("stop", help="record that this run found nothing to deploy")
    stop.add_argument("--status", default="none")
    stop.add_argument("--reason", required=True)
    stop.add_argument("--slug")
    verify = sub.add_parser("verify", help="compare the live target with the bytes this status requires")
    verify.add_argument("id")
    return parser


COMMANDS = {
    "path": cmd_path,
    "list": cmd_list,
    "show": cmd_show,
    "gate": cmd_gate,
    "begin": cmd_begin,
    "check": cmd_check,
    "propose": cmd_propose,
    "drop": cmd_drop,
    "reject": cmd_reject,
    "approve": cmd_approve,
    "rollback": cmd_rollback,
    "stop": cmd_stop,
    "verify": cmd_verify,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "path":
        return cmd_path(args)
    lock = acquire_lock(state_home())
    try:
        return COMMANDS[args.cmd](args)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Gate as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        sys.exit(exc.code)

#!/usr/bin/env python3
"""Behavioral checks for scripts/digest.py. Each test runs the CLI on a fake home."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DIGEST = Path(__file__).resolve().parent / "digest.py"
FAILURES = []
TOKEN = "ghp_" + "a" * 30


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS {name}")
        return
    FAILURES.append(name)
    print(f"FAIL {name} {detail}")


def write_jsonl(path: Path, records: list[dict], age_days: float = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    if age_days:
        old = time.time() - age_days * 86400
        os.utime(path, (old, old))


def claude_session(cwd: str, calls: int = 1, error: str | None = None) -> list[dict]:
    records = [{"type": "user", "cwd": cwd, "message": {"role": "user", "content": "please fix the hook"}}]
    for _ in range(calls):
        records.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "bin/fm-wake-drain.sh"}}]}})
    if error:
        records.append({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "is_error": True, "content": error}]}})
    records.append({"type": "attachment", "attachment": {
        "type": "hook_additional_context", "hookName": "PostToolUse:Bash", "content": "[worker-prompting REFUSAL] tier missing"}})
    records.append({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Done."}]}})
    records.append({"type": "user", "message": {"role": "user", "content": "that is wrong, the hook still fires"}})
    return records


def run(home: Path, out: Path, *args: str):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("XDG_STATE_HOME", None)
    env["LET_ME_COOK_HOME"] = str(home / "state")
    result = subprocess.run([sys.executable, str(DIGEST), "--out", str(out), *args],
                            env=env, capture_output=True, text=True)
    return result, (json.loads(result.stdout) if result.returncode == 0 else None)


def all_digest(out: Path) -> str:
    return "".join(p.read_text() for p in sorted(out.glob("*.digest")))


def test_events_keep_source_lines() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        session = home / ".claude/projects/-home-x/s1.jsonl"
        write_jsonl(session, claude_session("/home/x", error=f"Exit code 1 token {TOKEN}"))
        result, report = run(home, home / "out")
        text = all_digest(home / "out")
        check("digest runs", result.returncode == 0, result.stderr)
        check("human turn keeps its line", "L1 USER please fix the hook" in text, text)
        check("correction keeps its line", "L6 USER that is wrong, the hook still fires" in text, text)
        check("call before a failure is kept", "L2 CALL Bash: bin/fm-wake-drain.sh" in text, text)
        check("failure is kept", "L3 ERR Exit code 1" in text, text)
        check("hook output is kept", "L4 HOOK PostToolUse:Bash: [worker-prompting REFUSAL]" in text, text)
        check("agent text before a human turn is kept", "L5 SAY Done." in text, text)
        check("secret is redacted", TOKEN not in text and "<secret>" in text, text)
        check("source path is named", f"## {session}" in text, text)
        check("file list names the source", str(session) in (home / "out/slice-1.files").read_text())


def test_repeats_fold_and_count() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        records = [{"type": "user", "cwd": "/home/x", "message": {"role": "user", "content": "go"}}]
        for n in range(6):
            records.append({"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": f"/f{n}"}}]}})
        for _ in range(4):
            records.append({"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": "cat inbox"}}]}})
        records.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/last"}}]}})
        records.append({"type": "user", "message": {"role": "user", "content": "thanks"}})
        write_jsonl(home / ".claude/projects/-home-x/s1.jsonl", records)
        run(home, home / "out")
        text = all_digest(home / "out")
        check("routine calls fold into a count", "routine calls=6 (Read 6)" in text, text)
        check("a repeated call is shown once with its count", text.count("cat inbox") == 1 and "[same call x4 in this file]" in text, text)


def test_window_sandbox_and_runtimes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_jsonl(home / ".claude/projects/-home-x/old.jsonl", claude_session("/home/x"), age_days=9)
        write_jsonl(home / ".claude/projects/-cache-eval/box.jsonl", claude_session("/home/x/.cache/eval"))
        write_jsonl(home / ".claude/projects/-home-x/parent/subagents/agent-1.jsonl", claude_session("/home/x"))
        write_jsonl(home / ".pi/agent/sessions/--home-x--/2026_abc.jsonl", [
            {"type": "session", "cwd": "/home/x"},
            {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "check ci"}]}},
            {"type": "message", "message": {"role": "assistant", "content": [{"type": "toolCall", "name": "bash", "arguments": {"command": "gh run list"}}]}},
            {"type": "message", "message": {"role": "toolResult", "toolName": "bash", "isError": True, "content": [{"type": "text", "text": "gh: not found"}]}},
        ])
        write_jsonl(home / ".codex/sessions/2026/10/10/rollout-x.jsonl", [
            {"type": "session_meta", "payload": {"cwd": "/home/x"}},
            {"type": "response_item", "payload": {"type": "function_call", "name": "shell", "arguments": json.dumps({"command": "make test"})}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "Process exited with code 2"}},
        ])
        brief = home / "firstmate/data/task-a/brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("# Brief\nThe worker failed twice before.\n")
        report_md = home / "firstmate/data/task-a/report.md"
        report_md.write_text("# Report\n" + "filler line\n" * 400 + "The deploy failed on retry.\n")
        deep = home / "firstmate/data/task-a/baseline/src/notes.md"
        deep.parent.mkdir(parents=True)
        deep.write_text("# Deep\nerror everywhere\n")
        result, report = run(home, home / "out")
        text = all_digest(home / "out")
        check("old file is outside the window", "old.jsonl" not in text, text)
        check("eval sandbox is skipped", "box.jsonl" not in text and report["skipped"].get("eval-sandbox") == 1, str(report))
        check("subagent belongs to its parent session", "session=parent" in text, text)
        check("pi failure is kept", "L4 ERR bash: gh: not found" in text, text)
        check("codex failure is kept", "L3 ERR Process exited with code 2" in text, text)
        check("brief keeps headings only", "# Brief" in text and "failed twice" not in text, text)
        check("report keeps signal lines", "The deploy failed on retry." in text and "filler line" not in text, text)
        check("deep evidence trees are skipped", "Deep" not in text, text)


def test_sessions_stay_in_one_slice() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        for n in range(6):
            write_jsonl(home / f".claude/projects/-home-x/s{n}.jsonl", claude_session("/home/x"))
        write_jsonl(home / ".claude/projects/-home-x/s0/subagents/agent-a.jsonl", claude_session("/home/x"))
        result, report = run(home, home / "out", "--slices", "3")
        check("three slices", len(report["slices"]) == 3, str(report))
        holders = [p.name for p in (home / "out").glob("*.files") if "/s0" in p.read_text()]
        check("a session and its subagent share one slice", len(holders) == 1, str(holders))
        check("legend heads each digest", all(p.read_text().startswith("# let-me-cook digest") for p in (home / "out").glob("*.digest")))


def test_default_read_dir_is_under_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_jsonl(home / ".claude/projects/-home-x/s1.jsonl", claude_session("/home/x"))
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["LET_ME_COOK_HOME"] = str(home / "state")
        result = subprocess.run([sys.executable, str(DIGEST)], env=env, capture_output=True, text=True)
        report = json.loads(result.stdout)
        check("default read dir sits under the state dir", report["read_dir"].startswith(str(home / "state/reads/")), report["read_dir"])


def main() -> int:
    for test in (
        test_events_keep_source_lines,
        test_repeats_fold_and_count,
        test_window_sandbox_and_runtimes,
        test_sessions_stay_in_one_slice,
        test_default_read_dir_is_under_state,
    ):
        test()
    if FAILURES:
        print(f"\n{len(FAILURES)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

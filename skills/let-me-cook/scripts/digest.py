#!/usr/bin/env python3
"""Turn the recent session evidence into short digests that cheap workers can read.

Raw session logs are too large for a cheap model to read, so a worker that gets
them falls back to keyword searches. This script keeps only the events that show
waste: human turns, tool calls, failed tool results, hook output, and short
agent text. Every event keeps its source `path:line`, so a worker cites the
original log and the parent can open the exact span.

It runs on demand and writes only inside one read directory. It is not a collector.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

from cook import SECRET_RE, stamp, state_home

WINDOW_DAYS = 7
SLICES = 5
# Text evidence in ~/firstmate/data: task notes and reports, not checked-out code.
TEXT_SUFFIXES = {".md", ".txt", ".log"}
TEXT_DEPTH = 2
TEXT_SMALL = 2048
# Briefs repeat what the worker sessions already show, and archives are history,
# so only their headings go into the digest.
HEADINGS_ONLY_RE = re.compile(r"(?i)(brief|archive|before-prune)")
SIGNAL_RE = re.compile(
    r"(?i)\b(error|fail(ed|s|ure)?|refus(ed|al)|block(ed)?|denied|retry|retried|timeout|timed out|"
    r"stuck|wrong|missing|not found|traceback|exit(ed)? (with )?code [1-9]|stale|again)\b"
)
ERROR_RE = re.compile(
    r"(?im)^\s*(error|fatal|traceback|exception|refused|denied|\[[^\]]*refusal\])|"
    r"exit(ed)? (with )?code:? ?[1-9]|exit_code\"?:\s*[1-9]|no such file|command not found|permission denied"
)
# Turns a runtime or an automation writes with the user role. They are not the human.
INJECTED = ("<", "Base directory for this skill", "This session is being continued", "[Request interrupted", "Caveat:", "[Image")
MACHINE_RE = re.compile(r"^[\s⁣:]*(firstmate|main dialog mirror|workspace boundary|you are an independent evaluator)", re.I)
QUIET_HOOKS = {"hook_success", "total_tokens_reminder", "command_permissions", "environment", "edited_text_file"}


LEGEND = """# let-me-cook digest
# Each section is one source file. L<n> is the line in that file; cite it as <path>:<n>.
# USER human turn | AUTO automated turn | SAY agent text right before a human turn
# CALL tool call | ERR failed tool result | HOOK hook output | SYS runtime error | TEXT note or report line
# "routine calls" folds calls that were not followed by a failure or a human turn.
# "[same call xN]" marks a call that repeats N times in that file. Later uses show as "again:" only when a failure follows.

"""


def sources(home: Path) -> list[tuple[str, Path]]:
    """The evidence roots this skill reads, with the parser each one needs."""
    return [
        ("claude", home / ".claude/projects"),
        ("pi", home / ".pi/agent/sessions"),
        ("codex", home / ".codex/sessions"),
        ("text", home / "firstmate/data"),
        ("text", home / ".local/state/skill-evidence/probes"),
    ]


def clip(text: str, limit: int) -> str:
    flat = " ".join(str(text).split())
    flat = SECRET_RE.sub("<secret>", flat)
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def blocks_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text") or block.get("content") or ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return "" if content is None else str(content)


def call_text(name, args) -> str:
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return f"{name}: {args}"
    if isinstance(args, dict):
        for key in ("command", "cmd", "file_path", "path", "pattern", "skill", "url", "description", "query"):
            if args.get(key):
                return f"{name}: {args[key]}"
        return f"{name}: {json.dumps(args, sort_keys=True)}"
    return f"{name}: {args}"


def human(text: str) -> bool:
    stripped = text.lstrip()
    return bool(stripped) and not stripped.startswith(INJECTED) and not MACHINE_RE.match(stripped)


class Digest:
    """Events for one source file: (line, kind, text)."""

    def __init__(self, path: Path, runtime: str, session: str):
        self.path = path
        self.runtime = runtime
        self.session = session
        self.cwd = ""
        self.events: list[tuple[int, str, str]] = []

    def add(self, line: int, kind: str, text: str, limit: int) -> None:
        text = clip(text, limit)
        if text:
            self.events.append((line, kind, text))

    def render(self) -> str:
        """Keep the events that show waste, and fold routine calls into per-turn counts.

        A call is kept when a failure or hook follows it, when it is one of the
        last calls before a human turn, or as the first of a call repeated three or
        more times. Agent text is kept only right before a human turn, because that
        is what the human reacted to.
        """
        head = f"## {self.path}\nruntime={self.runtime} session={self.session} cwd={self.cwd or '?'}\n"
        events = self.events
        calls = Counter(text for _, kind, text in events if kind == "CALL")
        hooks = Counter(text for _, kind, text in events if kind == "HOOK")
        human_at = [i for i, (_, kind, _) in enumerate(events) if kind == "USER"]
        near_human = set()
        for i in human_at:
            back, seen_calls = i - 1, 0
            while back >= 0 and events[back][1] != "USER" and seen_calls < 3:
                if events[back][1] == "CALL":
                    seen_calls += 1
                near_human.add(back)
                back -= 1
        out, folded, shown = [], Counter(), set()
        span = [None, None]

        def flush():
            if folded:
                top = ", ".join(f"{name} {n}" for name, n in folded.most_common(4))
                where = f"L{span[0]}" if span[0] == span[1] else f"L{span[0]}-L{span[1]}"
                out.append(f"{where} routine calls={sum(folded.values())} ({top})")
                folded.clear()

        for i, (line, kind, text) in enumerate(events):
            following = events[i + 1][1] if i + 1 < len(events) else ""
            if kind == "CALL":
                repeated = calls[text] >= 3
                failed = following in ("ERR", "HOOK")
                if repeated:
                    keep = text not in shown or failed
                else:
                    keep = failed or i in near_human
                if not keep:
                    if not folded:
                        span[0] = line
                    span[1] = line
                    folded[text.split(":", 1)[0]] += 1
                    continue
                if repeated and text in shown:
                    text = f"again: {text}"
                elif repeated:
                    shown.add(text)
                    text = f"{text}  [same call x{calls[text]} in this file]"
            elif kind == "SAY" and i not in near_human:
                continue
            elif kind == "HOOK":
                if text in shown:
                    continue
                shown.add(text)
                if hooks[text] > 1:
                    text = f"{text}  [same hook output x{hooks[text]} in this file]"
            flush()
            out.append(f"L{line} {kind} {text}")
        flush()
        return head + "\n".join(out) + "\n"


def read_jsonl(path: Path):
    with path.open(errors="replace") as handle:
        for number, raw in enumerate(handle, 1):
            try:
                record = json.loads(raw)
            except ValueError:
                continue
            if isinstance(record, dict):
                yield number, record


def parse_claude(path: Path, root: Path) -> Digest:
    parts = path.relative_to(root).parts
    # A subagent transcript belongs to its parent session: <project>/<session>/subagents/x.jsonl
    session = parts[1] if "subagents" in parts and len(parts) > 2 else path.stem
    digest = Digest(path, "claude", session)
    for number, record in read_jsonl(path):
        digest.cwd = digest.cwd or record.get("cwd", "")
        kind = record.get("type")
        attachment = record.get("attachment")
        if kind == "attachment" and isinstance(attachment, dict):
            sort = attachment.get("type", "")
            if sort in QUIET_HOOKS:
                continue
            if sort.startswith("hook") or sort == "queued_command":
                body = attachment.get("content") or attachment.get("stderr") or attachment.get("prompt") or ""
                name = attachment.get("hookName") or sort
                if blocks_text(body).strip():
                    label = "HOOK" if sort != "queued_command" else ("USER" if human(blocks_text(body)) else "AUTO")
                    digest.add(number, label, f"{name}: {blocks_text(body)}", 240)
            continue
        message = record.get("message")
        if not isinstance(message, dict) or record.get("isMeta"):
            continue
        content = message.get("content")
        if kind == "user":
            if isinstance(content, str):
                if human(content):
                    digest.add(number, "USER", content, 500)
                continue
            for block in content or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and human(block.get("text", "")):
                    digest.add(number, "USER", block["text"], 500)
                elif block.get("type") == "tool_result" and block.get("is_error"):
                    digest.add(number, "ERR", blocks_text(block.get("content")), 240)
        elif kind == "assistant":
            for block in content or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    digest.add(number, "SAY", block.get("text", ""), 240)
                elif block.get("type") == "tool_use":
                    digest.add(number, "CALL", call_text(block.get("name"), block.get("input")), 150)
        elif kind == "system" and record.get("level") in ("error", "warning"):
            digest.add(number, "SYS", blocks_text(record.get("content")), 240)
    return digest


def parse_pi(path: Path) -> Digest:
    digest = Digest(path, "pi", path.stem.split("_")[-1])
    for number, record in read_jsonl(path):
        if record.get("type") == "session":
            digest.cwd = record.get("cwd", "")
            continue
        message = record.get("message")
        if record.get("type") != "message" or not isinstance(message, dict):
            continue
        role = message.get("role")
        if role == "user":
            text = blocks_text(message.get("content"))
            if human(text):
                digest.add(number, "USER", text, 500)
        elif role == "assistant":
            for block in message.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    digest.add(number, "SAY", block.get("text", ""), 240)
                elif block.get("type") == "toolCall":
                    digest.add(number, "CALL", call_text(block.get("name"), block.get("arguments")), 150)
        elif role == "toolResult" and message.get("isError"):
            digest.add(number, "ERR", f"{message.get('toolName')}: {blocks_text(message.get('content'))}", 240)
    return digest


def parse_codex(path: Path) -> Digest:
    digest = Digest(path, "codex", path.stem[-36:])
    for number, record in read_jsonl(path):
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if record.get("type") == "session_meta":
            digest.cwd = payload.get("cwd", "")
            continue
        if record.get("type") != "response_item":
            continue
        sort = payload.get("type")
        if sort == "message":
            text = blocks_text(payload.get("content"))
            if payload.get("role") == "user" and human(text) and not text.startswith("# AGENTS.md"):
                digest.add(number, "USER", text, 500)
            elif payload.get("role") == "assistant":
                digest.add(number, "SAY", text, 240)
        elif sort in ("function_call", "custom_tool_call"):
            digest.add(number, "CALL", call_text(payload.get("name"), payload.get("arguments", payload.get("input"))), 150)
        elif sort in ("function_call_output", "custom_tool_call_output"):
            text = blocks_text(payload.get("output"))
            if ERROR_RE.search(text):
                digest.add(number, "ERR", text, 240)
    return digest


def parse_text(path: Path) -> Digest:
    digest = Digest(path, "text", path.parent.name)
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return digest
    small = path.stat().st_size <= TEXT_SMALL
    headings_only = bool(HEADINGS_ONLY_RE.search(path.name))
    for number, line in enumerate(lines, 1):
        if line.startswith("#") or (not headings_only and (small or SIGNAL_RE.search(line))):
            digest.add(number, "TEXT", line, 160)
    return digest


def in_window(home: Path, cutoff: float) -> list[tuple[str, Path, Path]]:
    found = []
    for runtime, root in sources(home):
        if not root.is_dir():
            continue
        if runtime == "text":
            candidates = (p for p in root.rglob("*") if p.suffix in TEXT_SUFFIXES or root.name == "probes")
        else:
            candidates = root.rglob("*.jsonl")
        for path in candidates:
            try:
                if not path.is_file() or path.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            relative = path.relative_to(root).parts
            if runtime == "text" and root.name == "data" and (len(relative) > TEXT_DEPTH or ".git" in relative):
                continue
            found.append((runtime, root, path))
    return sorted(found, key=lambda item: str(item[2]))


def build(home: Path, out: Path, days: float, slices: int) -> dict:
    cutoff = time.time() - days * 86400
    digests, skipped = [], Counter()
    for runtime, root, path in in_window(home, cutoff):
        if runtime == "claude":
            digest = parse_claude(path, root)
        elif runtime == "pi":
            digest = parse_pi(path)
        elif runtime == "codex":
            digest = parse_codex(path)
        else:
            digest = parse_text(path)
        # Eval and probe sandboxes run under ~/.cache; they are not real use.
        if "/.cache/" in digest.cwd:
            skipped["eval-sandbox"] += 1
            continue
        if not digest.events:
            skipped["no-events"] += 1
            continue
        digests.append((digest, digest.render()))
    out.mkdir(parents=True, exist_ok=True)
    # Keep one session's files in one slice, and balance slices by digest size.
    sessions: dict[str, list] = {}
    for digest, text in digests:
        sessions.setdefault(f"{digest.runtime}:{digest.session}", []).append((digest, text))
    buckets = [[] for _ in range(max(1, slices))]
    sizes = [0] * len(buckets)
    for group in sorted(sessions.values(), key=lambda g: -sum(len(t) for _, t in g)):
        smallest = sizes.index(min(sizes))
        buckets[smallest].extend(group)
        sizes[smallest] += sum(len(t) for _, t in group)
    report = {"read_dir": str(out), "window_days": days, "skipped": dict(skipped), "slices": []}
    for index, bucket in enumerate(buckets, 1):
        if not bucket:
            continue
        name = f"slice-{index}"
        (out / f"{name}.digest").write_text(LEGEND + "".join(text + "\n" for _, text in bucket), encoding="utf-8")
        (out / f"{name}.files").write_text("".join(f"{d.path}\n" for d, _ in bucket), encoding="utf-8")
        report["slices"].append({
            "name": name,
            "digest": str(out / f"{name}.digest"),
            "files": len(bucket),
            "sessions": len({d.session for d, _ in bucket}),
            "bytes": sum(len(t) for _, t in bucket),
        })
    return report


def main(argv=None, home: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", help="read directory; default <state dir>/reads/<UTC stamp>")
    parser.add_argument("--days", type=float, default=WINDOW_DAYS)
    parser.add_argument("--slices", type=int, default=SLICES, choices=range(1, 6))
    args = parser.parse_args(argv)
    out = Path(args.out).expanduser().resolve() if args.out else state_home() / "reads" / stamp()
    report = build(home or Path.home(), out, args.days, args.slices)
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

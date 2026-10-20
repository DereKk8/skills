#!/usr/bin/env python3
"""Mine agent transcripts for evidence about a skill.

Evidence here means a human correction: a user turn that pushes back on what the
agent just did. A correction after a skill loaded is evidence the skill fell
short. A correction on the skill's topic in a session where the skill never
loaded is a candidate silent miss. The agent reading the output judges each hit.

Commands:
  sweep                  rank skills by the share of their sessions that drew a correction
  corrections SKILL      corrections that came after SKILL loaded
  misses SKILL --about RE  corrections matching RE in sessions where SKILL never loaded
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
DEFAULT_ROOTS = [HOME / ".claude/projects", HOME / ".pi/agent/sessions"]

# A turn counts as a correction when it matches one of these. Strong patterns
# say the agent got something wrong; weak ones only push back, and a weak hit
# right after the agent asked a question is usually an answer, not a correction.
# The lists favor recall: the reader drops false hits, but a missed one never shows.
STRONG = [re.compile(p, re.I) for p in (
    r"\bi (meant|said|asked( for| you)?|told you|already (said|told|asked))\b",
    r"\b(that'?s|this is|it'?s) not (what|it|right|correct)\b",
    r"\bnot what i\b",
    r"\bwhy (did|didn'?t|are|would|do) you\b",
    r"\byou (didn'?t|did not|forgot|missed|ignored|keep|still|should(n'?t)? have|never|broke)\b",
    r"\b(wrong|incorrect|not correct|mistake)\b",
)]
WEAK = [re.compile(p, re.I) for p in (
    r"^\W*(no|nope|stop|wait|ugh)\b",
    r"\b(don'?t|do not|never|stop) (do|use|add|make|touch|ask|run|change|write|call|put|create|push|commit)",
    r"\binstead of\b",
    r"\bplease (stop|don'?t|do not)\b",
)]


def correction_score(text, after_question=False):
    strong = sum(1 for r in STRONG if r.search(text))
    weak = 0 if after_question else sum(1 for r in WEAK if r.search(text))
    return 2 * strong + weak


# Injected turns that a runtime writes with the user role.
INJECTED_PREFIXES = (
    "<", "Base directory for this skill", "This session is being continued",
    "[Request interrupted", "Caveat:", "[Image",
)
# Turns that firstmate, evals, and other automation write with the user role.
MACHINE_RE = re.compile(
    r"^[\s\u2063:]*(firstmate|main dialog mirror|workspace boundary|you are an independent evaluator)", re.I)
SKILL_PATH_RE = re.compile(r"/([A-Za-z0-9_.-]+)/SKILL\.md\b")
CLAUDE_SLASH_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
CLAUDE_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
PI_SLASH_RE = re.compile(r"^/skill:([A-Za-z0-9_.-]+)\s*(.*)", re.S)


def skill_name(raw):
    """Plugin skills arrive as plugin:name; match on the bare name."""
    return raw.split(":")[-1].strip()


class Session:
    def __init__(self, path, runtime):
        self.path = path
        self.runtime = runtime
        self.cwd = ""
        self.events = []  # (kind, index, timestamp, payload) in file order

    @property
    def kind(self):
        # Firstmate workers run in treehouse checkouts; their user is the supervisor.
        return "worker" if "/.treehouse/" in self.cwd else "direct"

    def loaded(self):
        return {e[3] for e in self.events if e[0] == "load"}


def _text_blocks(content):
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return []


def _loads_from_call(name, args):
    name = (name or "").lower()
    args = args if isinstance(args, dict) else {}
    if name == "skill" and args.get("skill"):
        return [skill_name(args["skill"])]
    blob = " ".join(str(v) for v in args.values() if isinstance(v, str))
    if name in ("read", "bash", "view", "cat"):
        return SKILL_PATH_RE.findall(blob)
    return []


def parse_claude(path):
    s = Session(path, "claude")
    with open(path, errors="replace") as f:
        for i, line in enumerate(f):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("isSidechain") or d.get("isMeta"):
                continue
            s.cwd = s.cwd or d.get("cwd", "")
            ts = d.get("timestamp", "")
            m = d.get("message")
            if not isinstance(m, dict):
                continue
            if d.get("type") == "user" and m.get("role") == "user":
                for text in _text_blocks(m.get("content")):
                    slash = CLAUDE_SLASH_RE.search(text)
                    if slash:
                        s.events.append(("load", i, ts, skill_name(slash.group(1))))
                        args = CLAUDE_ARGS_RE.search(text)
                        text = args.group(1).strip() if args else ""
                    elif text.lstrip().startswith(INJECTED_PREFIXES) or MACHINE_RE.match(text):
                        continue
                    if text.strip():
                        s.events.append(("user", i, ts, text.strip()))
            elif d.get("type") == "assistant":
                for b in m.get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        s.events.append(("assistant", i, ts, b["text"].strip()))
                    elif b.get("type") == "tool_use":
                        for name in _loads_from_call(b.get("name"), b.get("input")):
                            s.events.append(("load", i, ts, name))
    return s


def parse_pi(path):
    s = Session(path, "pi")
    with open(path, errors="replace") as f:
        for i, line in enumerate(f):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if d.get("type") == "session":
                s.cwd = d.get("cwd", "")
                continue
            m = d.get("message")
            if d.get("type") != "message" or not isinstance(m, dict):
                continue
            ts = d.get("timestamp", "")
            if m.get("role") == "user":
                for text in _text_blocks(m.get("content")):
                    slash = PI_SLASH_RE.match(text.strip())
                    if slash:
                        s.events.append(("load", i, ts, slash.group(1)))
                        text = slash.group(2)
                    elif text.lstrip().startswith(INJECTED_PREFIXES) or MACHINE_RE.match(text):
                        continue
                    if text.strip():
                        s.events.append(("user", i, ts, text.strip()))
            elif m.get("role") == "assistant":
                for b in m.get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        s.events.append(("assistant", i, ts, b["text"].strip()))
                    elif b.get("type") == "toolCall":
                        for name in _loads_from_call(b.get("name"), b.get("arguments")):
                            s.events.append(("load", i, ts, name))
    return s


def is_pi(path):
    """Pi transcripts open with a session header; Claude Code ones do not."""
    with open(path, errors="replace") as f:
        try:
            return json.loads(f.readline()).get("type") == "session"
        except (ValueError, AttributeError):
            return False


def iter_sessions(roots, since):
    """Yield parsed sessions modified after `since`, skipping scratch and eval sandboxes."""
    cutoff = since.timestamp()
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.jsonl")):
            if "subagents" in path.parts or path.stat().st_mtime < cutoff:
                continue
            s = parse_pi(path) if is_pi(path) else parse_claude(path)
            # Eval runs and probes live under ~/.cache; they are not real use.
            if not s.cwd or "/.cache/" in s.cwd or not any(e[0] == "user" for e in s.events):
                continue
            yield s


def corrections(session, window=3):
    """Yield (score, event, previous agent text, skills in reach) for each correction.

    A skill is in reach of a correction when it loaded within the last `window`
    human turns. Without that window, long sessions that load many skills would
    pin every late correction on every skill.
    """
    last_load, prev, turn = {}, "", 0
    for e in session.events:
        kind, _, _, payload = e
        if kind == "load":
            last_load[payload] = turn
        elif kind == "assistant":
            prev = payload
        elif kind == "user":
            # The first human turn is the request, not a correction.
            if turn and prev:
                score = correction_score(payload, prev.rstrip().endswith("?") or "?" in prev[-160:])
                if score:
                    reach = frozenset(n for n, t in last_load.items() if turn - t <= window)
                    yield score, e, prev, reach
            turn += 1


def clip(text, n, tail=False):
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return ("…" + text[-n:]) if tail else (text[:n] + "…")


def short_path(p):
    return str(p).replace(str(HOME), "~")


def print_hits(hits, limit):
    hits.sort(key=lambda h: h[1][2], reverse=True)
    hits.sort(key=lambda h: h[0], reverse=True)
    print(f"hits: {len(hits)} (showing {min(limit, len(hits))}, strongest first)")
    for score, e, prev, s in hits[:limit]:
        _, line, ts, text = e
        print(f"\n[{score}] {ts[:16].replace('T', ' ')} {s.runtime} {s.kind} {short_path(s.cwd)}")
        print(f"  file: {short_path(s.path)}:{line + 1}")
        print(f"  agent: {clip(prev, 280, tail=True)}")
        print(f"  human: {clip(text, 420)}")


def cmd_sweep(sessions, args):
    total, corrected_any = 0, 0
    stats = {}
    for s in sessions:
        total += 1
        hits = list(corrections(s, args.window))
        corrected_any += bool(hits)
        for name in s.loaded():
            st = stats.setdefault(name, [0, 0])
            st[0] += 1
            st[1] += any(name in h[3] for h in hits)
    base = corrected_any / total if total else 0
    print(f"sessions: {total}  with a correction: {corrected_any} ({base:.0%} baseline)")
    print(f"{'skill':<34}{'sessions':>9}{'corrected':>11}{'rate':>7}")
    rows = [(n, a, c) for n, (a, c) in stats.items() if a >= args.min_sessions]
    rows.sort(key=lambda r: (-(r[2] / r[1]), -r[1]))
    for name, a, c in rows:
        flag = "  above baseline" if c / a > base else ""
        print(f"{name:<34}{a:>9}{c:>11}{c / a:>7.0%}{flag}")
    print(f"\nrate = share of the skill's sessions with a correction within {args.window} human turns after it loaded.")
    print("A high rate points where to read first; it does not prove the skill caused it.")


def cmd_corrections(sessions, args):
    hits = [(sc, e, prev, s) for s in sessions for sc, e, prev, reach in corrections(s, args.window) if args.skill in reach]
    print(f"skill: {args.skill}  sessions that loaded it: {sum(args.skill in s.loaded() for s in sessions)}")
    print_hits(hits, args.limit)


def cmd_misses(sessions, args):
    about = re.compile(args.about, re.I)
    hits = []
    for s in sessions:
        if args.skill in s.loaded():
            continue
        for sc, e, prev, _ in corrections(s, args.window):
            if about.search(e[3]) or about.search(prev):
                hits.append((sc, e, prev, s))
    print(f"skill: {args.skill}  topic: /{args.about}/  sessions without the skill only")
    print_hits(hits, args.limit)


def main(argv=None, roots=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--days", type=int, default=30, help="look back this many days (default 30)")
    common.add_argument("--root", action="append", help="transcript root; repeatable (default: Claude Code and Pi)")
    common.add_argument("--window", type=int, default=3,
                        help="a correction counts against a skill loaded within this many human turns before it (default 3)")
    common.add_argument("--kind", choices=["direct", "worker", "all"], default="all",
                        help="direct = a human typed the turns; worker = a supervisor agent did")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sw = sub.add_parser("sweep", parents=[common], help="rank skills by correction rate")
    sw.add_argument("--min-sessions", type=int, default=3)
    c = sub.add_parser("corrections", parents=[common], help="corrections soon after SKILL loaded")
    c.add_argument("skill")
    c.add_argument("--limit", type=int, default=15)
    m = sub.add_parser("misses", parents=[common], help="topic corrections in sessions without SKILL")
    m.add_argument("skill")
    m.add_argument("--about", required=True, help="regex for the skill's topic, matched on the turn and the agent text before it")
    m.add_argument("--limit", type=int, default=15)
    args = p.parse_args(argv)

    since = dt.datetime.now() - dt.timedelta(days=args.days)
    sessions = [s for s in iter_sessions(args.root or roots or DEFAULT_ROOTS, since)
                if args.kind == "all" or s.kind == args.kind]
    {"sweep": cmd_sweep, "corrections": cmd_corrections, "misses": cmd_misses}[args.cmd](sessions, args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(0)

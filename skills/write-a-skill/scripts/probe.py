#!/usr/bin/env python3
"""Run a skill's probe prompts in fresh headless sessions and report what loaded.

A probe is a prompt with an expectation: the skill should load ("load") or stay
out ("skip"). An optional `look_for` regex must also match the final reply, which
checks that a loaded skill changed the behavior, not only that it loaded.

Probes live beside the skill as probes.json:
  {"probes": [{"prompt": "...", "expect": "load", "why": "...", "look_for": "optional regex"}]}

Each run uses the installed config on the real model. Every tool is visible but
only read-only ones are approved, and no transcript is saved, so probes never
edit files and never pollute the history that history.py mines.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILLS_ROOT = Path.home() / ".agents/skills"
CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "skill-evidence/probes"
# Only these run without a prompt. Every other tool stays visible, as in real use,
# but headless mode denies the call, so a probe cannot change anything.
READ_ONLY = ["Read", "Glob", "Grep", "Skill"]


class ProbeError(ValueError):
    pass


def overlay_config(skill, skill_dir, config_dir, dest):
    """Build a Claude config dir that matches `config_dir` except one skill.

    Every entry links back to the real config, so auth, settings, hooks, and all
    other skills stay as installed. Only `skill` resolves to `skill_dir`, which
    lets a draft be probed before it lands.
    """
    config_dir, dest = Path(config_dir), Path(dest)
    for entry in config_dir.iterdir():
        if entry.name != "skills":
            (dest / entry.name).symlink_to(entry)
    home_json = config_dir.parent / ".claude.json"
    if home_json.exists() and not (dest / ".claude.json").exists():
        (dest / ".claude.json").symlink_to(home_json)

    def mirror(src, out, depth):
        out.mkdir()
        for child in Path(src).iterdir():
            target = out / child.name
            if child.name == skill:
                target.symlink_to(Path(skill_dir).resolve())
            elif depth < 2 and child.is_dir() and (Path(child.resolve()) / skill).exists():
                mirror(child.resolve(), target, depth + 1)
            else:
                target.symlink_to(child.resolve())

    mirror((config_dir / "skills").resolve(), dest / "skills", 1)
    return dest


def find_probes(skill, skills_root):
    path = Path(skills_root) / skill / "probes.json"
    if not path.is_file():
        raise ProbeError(f"no probes.json for {skill!r} at {path}")
    return path


def load_probes(path):
    """Validate the probe file where it enters; a bad probe fails loudly, not silently."""
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise ProbeError(f"{path}: {e}") from e
    probes = data.get("probes") if isinstance(data, dict) else None
    if not isinstance(probes, list) or not probes:
        raise ProbeError(f"{path}: expected an object with a non-empty 'probes' list")
    for n, p in enumerate(probes, 1):
        if not isinstance(p, dict) or not isinstance(p.get("prompt"), str) or not p["prompt"].strip():
            raise ProbeError(f"{path}: probe {n} needs a non-empty 'prompt'")
        if p.get("expect") not in ("load", "skip"):
            raise ProbeError(f"{path}: probe {n} 'expect' must be 'load' or 'skip'")
        if "look_for" in p:
            try:
                re.compile(p["look_for"])
            except (re.error, TypeError) as e:
                raise ProbeError(f"{path}: probe {n} 'look_for' is not a regex: {e}") from e
    return probes


def loaded_skills(block):
    """Skill names a tool call loads: the Skill tool, or a read of some <name>/SKILL.md."""
    if block.get("type") != "tool_use":
        return []
    args = block.get("input") or {}
    if block.get("name") == "Skill" and args.get("skill"):
        return [str(args["skill"]).split(":")[-1]]
    blob = " ".join(str(v) for v in args.values() if isinstance(v, str))
    return re.findall(r"/([A-Za-z0-9_.-]+)/SKILL\.md\b", blob)


def run_once(skill, probe, claude, model, effort, budget, timeout, env=None):
    cmd = [claude, "-p", probe["prompt"], "--output-format", "stream-json", "--verbose",
           "--permission-mode", "default", "--allowedTools", *READ_ONLY,
           "--no-session-persistence", "--max-budget-usd", str(budget)]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    # Stop as soon as the answer is known, unless the reply itself must be checked.
    stop_on_load = "look_for" not in probe
    loads, reply, cost, error = [], [], None, None
    with tempfile.TemporaryDirectory(prefix="skill-probe-") as cwd:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True)
        deadline = time.monotonic() + timeout
        try:
            for line in proc.stdout:
                if time.monotonic() > deadline:
                    error = "timeout"
                    break
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("type") == "assistant":
                    for b in ev.get("message", {}).get("content", []):
                        loads += loaded_skills(b)
                        if b.get("type") == "text":
                            reply.append(b["text"])
                    if stop_on_load and skill in loads:
                        break
                elif ev.get("type") == "result":
                    cost = ev.get("total_cost_usd")
                    if ev.get("is_error") and ev.get("subtype") != "error_max_budget_usd":
                        error = ev.get("subtype") or "error"
                    break
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
    text = "\n".join(reply)
    hit = skill in loads
    ok = hit if probe["expect"] == "load" else not hit
    if ok and probe.get("look_for"):
        ok = bool(re.search(probe["look_for"], text, re.I | re.M))
    return {"ok": ok and not error, "loaded": hit, "other_loads": sorted(set(loads) - {skill}),
            "cost_usd": cost, "error": error, "reply_head": " ".join(text.split())[:240]}


def main(argv=None, claude="claude", skills_root=SKILLS_ROOT, state_dir=STATE_DIR, config_dir=CONFIG_DIR):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("skill")
    p.add_argument("--file", help="probe file (default: the draft's probes.json, else <skills root>/<skill>/probes.json)")
    p.add_argument("--runs", type=int, default=1, help="runs per probe; loading is not deterministic (default 1)")
    p.add_argument("--model", help="model to probe on (default: your configured model)")
    p.add_argument("--effort", help="effort level (default: your configured level)")
    p.add_argument("--budget", type=float, default=0.40, help="max USD per run (default 0.40)")
    p.add_argument("--timeout", type=int, default=240, help="seconds per run (default 240)")
    p.add_argument("--jobs", type=int, default=3, help="runs in parallel (default 3)")
    p.add_argument("--claude", default=claude, help="Claude Code binary")
    p.add_argument("--draft", help="probe this skill folder instead of the installed one (a draft not yet landed)")
    p.add_argument("--label", default="", help="tag stored with the result, e.g. 'before' or 'after'")
    args = p.parse_args(argv)

    try:
        if args.file:
            path = Path(args.file)
        elif args.draft and (Path(args.draft) / "probes.json").is_file():
            path = Path(args.draft) / "probes.json"
        else:
            path = find_probes(args.skill, skills_root)
        probes = load_probes(path)
    except ProbeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    jobs = [(i, r) for i in range(len(probes)) for r in range(args.runs)]
    print(f"skill: {args.skill}  probes: {len(probes)}  runs each: {args.runs}  file: {path}")
    print(f"text: {Path(args.draft).resolve() if args.draft else 'installed'}")
    results = {i: [] for i in range(len(probes))}
    with tempfile.TemporaryDirectory(prefix="skill-probe-config-") as overlay:
        env = None
        if args.draft:
            if not (Path(args.draft) / "SKILL.md").is_file():
                print(f"error: --draft {args.draft} has no SKILL.md", file=sys.stderr)
                return 2
            env = {**os.environ, "CLAUDE_CONFIG_DIR": str(overlay_config(args.skill, args.draft, config_dir, overlay))}
        with cf.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futs = {pool.submit(run_once, args.skill, probes[i], args.claude, args.model, args.effort,
                                args.budget, args.timeout, env): i for i, _ in jobs}
            for f in cf.as_completed(futs):
                results[futs[f]].append(f.result())

    passed = total = 0
    for i, pr in enumerate(probes):
        runs = results[i]
        ok = sum(r["ok"] for r in runs)
        passed += ok
        total += len(runs)
        mark = "PASS" if ok == len(runs) else ("FAIL" if ok == 0 else "FLAKY")
        print(f"\n{mark} {ok}/{len(runs)}  expect {pr['expect']}  {pr['prompt'][:90]!r}")
        for r in runs:
            if not r["ok"]:
                detail = r["error"] or ("loaded" if r["loaded"] else "did not load")
                extra = f"; loaded instead: {', '.join(r['other_loads'])}" if r["other_loads"] else ""
                print(f"  - {detail}{extra}; reply: {r['reply_head'][:160]!r}")
    costs = [r["cost_usd"] for rs in results.values() for r in rs if r["cost_usd"] is not None]
    print(f"\npassed: {passed}/{total}  reported cost: ${sum(costs):.2f} "
          f"({total - len(costs)} runs stopped early and report no cost)")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(state_dir) / args.skill / f"{stamp}{'-' + args.label if args.label else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"skill": args.skill, "file": str(path), "label": args.label, "draft": str(Path(args.draft).resolve()) if args.draft else None,
                               "model": args.model, "effort": args.effort, "when": stamp,
                               "probes": [{**probes[i], "runs": results[i]} for i in results]}, indent=1))
    print(f"saved: {out}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

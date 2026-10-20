#!/usr/bin/env python3
"""Exercise write-a-skill's history and probe scripts through their CLIs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/write-a-skill/scripts"


def jl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def cc_user(text, cwd="/home/u/work"):
    return {"type": "user", "cwd": cwd, "timestamp": "2026-10-08T10:00:00Z",
            "message": {"role": "user", "content": text}}


def cc_agent(*blocks, cwd="/home/u/work"):
    return {"type": "assistant", "cwd": cwd, "timestamp": "2026-10-08T10:00:01Z",
            "message": {"role": "assistant", "content": list(blocks)}}


def text(t):
    return {"type": "text", "text": t}


class HistoryTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.claude = Path(tmp.name) / "claude"
        self.pi = Path(tmp.name) / "pi"
        jl(self.claude / "p/loaded.jsonl", [
            cc_user("add a skill that keeps my PR titles short"),
            cc_agent({"type": "tool_use", "name": "Skill", "input": {"skill": "write-a-skill"}}),
            cc_agent(text("Done. I wrote a 40-line skill.")),
            cc_user("MAIN DIALOG MIRROR (read-only context): you didn't do it"),
            cc_user("that's not what I meant, keep it to one sentence"),
        ])
        jl(self.claude / "p/missed.jsonl", [
            cc_user("fix the goals skill"),
            cc_agent(text("I edited the goals skill.")),
            cc_user("you didn't read the skill body first"),
        ])
        jl(self.claude / "p/answer.jsonl", [
            cc_user("ship it"),
            cc_agent(text("The branch is ready. Should I push?")),
            cc_user("no, wait for CI"),
        ])
        jl(self.claude / "p/sandbox.jsonl", [
            cc_user("eval prompt", cwd="/home/u/.cache/box"),
            cc_agent(text("ok"), cwd="/home/u/.cache/box"),
            cc_user("you forgot the skill", cwd="/home/u/.cache/box"),
        ])
        jl(self.pi / "s/one.jsonl", [
            {"type": "session", "cwd": "/home/u/configs"},
            {"type": "message", "timestamp": "2026-10-08T11:00:00Z",
             "message": {"role": "user", "content": [text("/skill:ponder think about probes")]}},
            {"type": "message", "timestamp": "2026-10-08T11:00:01Z",
             "message": {"role": "assistant", "content": [text("Here are five ideas at once.")]}},
            {"type": "message", "timestamp": "2026-10-08T11:00:02Z",
             "message": {"role": "user", "content": [text("why did you skip my question")]}},
        ])

    def run_history(self, *args):
        out = subprocess.run([sys.executable, "-I", str(SCRIPTS / "history.py"), *args,
                              "--root", str(self.claude), "--root", str(self.pi)],
                             capture_output=True, text=True, check=True)
        return out.stdout

    def test_sweep_counts_real_sessions_and_attributes_corrections(self):
        out = self.run_history("sweep", "--min-sessions", "1")
        # The sandbox session is ignored; the answered question is not a correction.
        self.assertIn("sessions: 4  with a correction: 3", out)
        self.assertRegex(out, r"write-a-skill\s+1\s+1\s+100%")
        self.assertRegex(out, r"ponder\s+1\s+1\s+100%")

    def test_corrections_show_the_human_turn_after_the_skill_loaded(self):
        out = self.run_history("corrections", "write-a-skill")
        self.assertIn("that's not what I meant", out)
        self.assertIn("I wrote a 40-line skill", out)
        self.assertNotIn("MAIN DIALOG MIRROR", out)
        self.assertIn("loaded.jsonl:5", out)

    def test_misses_only_search_sessions_without_the_skill(self):
        out = self.run_history("misses", "write-a-skill", "--about", "skill")
        self.assertIn("you didn't read the skill body", out)
        self.assertNotIn("not what I meant", out)
        self.assertNotIn("you forgot the skill", out)


FAKE_CLAUDE = r'''#!{py}
import json, os, sys
args = sys.argv[1:]
prompt = args[args.index("-p") + 1]
def emit(o): print(json.dumps(o), flush=True)
skills = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR", "/nonexistent"), "skills", "demo")
seen = os.path.realpath(skills) if os.path.exists(skills) else "installed"
if "LOAD" in prompt:
    emit({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "name": "Skill", "input": {{"skill": "demo"}}}}]}}}})
emit({{"type": "assistant", "message": {{"content": [{{"type": "text", "text": "reply from " + seen}}]}}}})
emit({{"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": 0.01}})
'''


class ProbeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.fake = self.root / "claude"
        self.fake.write_text(FAKE_CLAUDE.format(py=sys.executable))
        self.fake.chmod(0o755)
        config = self.root / "config"
        (config / "skills" / "demo").mkdir(parents=True)
        (config / "settings.json").write_text("{}")
        self.draft = self.root / "draft-demo"
        self.draft.mkdir()
        (self.draft / "SKILL.md").write_text("---\nname: demo\ndescription: d\n---\n")
        self.env = {**os.environ, "CLAUDE_CONFIG_DIR": str(config), "XDG_STATE_HOME": str(self.root / "state")}

    def test_installed_skill_is_found_in_flat_layout(self):
        home = self.root / "home"
        (home / ".agents").mkdir(parents=True)
        (home / ".agents/skills").symlink_to(SCRIPTS.parents[1])
        env = {**self.env, "HOME": str(home)}
        out = subprocess.run([sys.executable, "-I", str(SCRIPTS / "probe.py"), "write-a-skill",
                              "--claude", str(self.fake)], capture_output=True, text=True, env=env)
        self.assertNotIn("no probes.json", out.stderr, out.stdout + out.stderr)

    def probe(self, probes, *args):
        f = self.root / "probes.json"
        f.write_text(json.dumps({"probes": probes}))
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "probe.py"), "demo", "--file", str(f),
                               "--claude", str(self.fake), *args],
                              capture_output=True, text=True, env=self.env)

    def test_load_and_skip_expectations(self):
        out = self.probe([{"prompt": "please LOAD it", "expect": "load"},
                          {"prompt": "unrelated", "expect": "skip"},
                          {"prompt": "unrelated", "expect": "load"}])
        self.assertEqual(out.returncode, 1)
        self.assertIn("passed: 2/3", out.stdout)
        self.assertIn("FAIL 0/1  expect load  'unrelated'", out.stdout)
        saved = list((self.root / "state/skill-evidence/probes/demo").glob("*.json"))
        self.assertEqual(len(saved), 1)

    def test_draft_replaces_only_the_probed_skill(self):
        out = self.probe([{"prompt": "LOAD", "expect": "load", "look_for": "draft-demo"}],
                         "--draft", str(self.draft), "--label", "after")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("passed: 1/1", out.stdout)

    def test_draft_brings_its_own_probes(self):
        (self.draft / "probes.json").write_text(json.dumps({"probes": [{"prompt": "LOAD", "expect": "load"}]}))
        out = subprocess.run([sys.executable, "-I", str(SCRIPTS / "probe.py"), "demo", "--draft", str(self.draft),
                              "--claude", str(self.fake)], capture_output=True, text=True, env=self.env)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn(f"file: {self.draft / 'probes.json'}", out.stdout)

    def test_bad_probe_file_fails_loudly(self):
        out = self.probe([{"prompt": "x", "expect": "maybe"}])
        self.assertEqual(out.returncode, 2)
        self.assertIn("'expect' must be 'load' or 'skip'", out.stderr)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Run scripts/check-skills.sh against small git fixtures of this catalog."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IGNORED = shutil.ignore_patterns("synced", ".system", "__pycache__")


def bump_patch(text):
    return re.sub(r"Skill version: (\d+)\.(\d+)\.(\d+)",
                  lambda m: f"Skill version: {m[1]}.{m[2]}.{int(m[3]) + 1}", text, count=1)


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   cwd=cwd, check=True, capture_output=True)


class CatalogFixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "catalog"
        shutil.copytree(REPO / "skills", self.root / "skills", ignore=IGNORED)
        shutil.copytree(REPO / "scripts", self.root / "scripts")
        shutil.copy(REPO / "VENDORED.md", self.root / "VENDORED.md")
        shutil.copy(REPO / ".gitignore", self.root / ".gitignore")
        git(self.root, "init", "-q")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")

    def check(self, base):
        return subprocess.run(["bash", str(self.root / "scripts/check-skills.sh")],
                              cwd=self.root, env={**os.environ, "BASE": base},
                              capture_output=True, text=True)


class VersionRule(CatalogFixture):
    def test_committed_helper_change_without_bump_fails(self):
        with open(self.root / "skills/write-a-skill/scripts/history.py", "a") as f:
            f.write("\n# helper edit\n")
        git(self.root, "commit", "-qam", "helper only")
        out = self.check("HEAD~1")
        self.assertNotEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("write-a-skill changed but version", out.stderr)

    def test_pending_body_change_without_bump_fails(self):
        with open(self.root / "skills/goals/SKILL.md", "a") as f:
            f.write("\nPending edit.\n")
        out = self.check("HEAD")
        self.assertNotEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("goals changed but version", out.stderr)

    def test_bumped_helper_change_passes(self):
        with open(self.root / "skills/write-a-skill/scripts/history.py", "a") as f:
            f.write("\n# helper edit\n")
        skill = self.root / "skills/write-a-skill/SKILL.md"
        skill.write_text(bump_patch(skill.read_text()))
        git(self.root, "commit", "-qam", "helper with bump")
        out = self.check("HEAD~1")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


    def test_disjoint_feature_passes_after_base_advances(self):
        main = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.root,
                              capture_output=True, text=True, check=True).stdout.strip()
        git(self.root, "checkout", "-qb", "feature")
        feature = self.root / "skills/code-mode/SKILL.md"
        feature.write_text(bump_patch(feature.read_text()) + "\nFeature edit.\n")
        git(self.root, "commit", "-qam", "feature change")
        git(self.root, "checkout", "-q", main)
        advanced = self.root / "skills/goals/SKILL.md"
        advanced.write_text(bump_patch(advanced.read_text()) + "\nMain edit.\n")
        git(self.root, "commit", "-qam", "main advances")
        git(self.root, "checkout", "-q", "feature")
        out = self.check(main)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


class Layout(CatalogFixture):
    def test_pending_symlink_replacing_skill_file_fails(self):
        skill = self.root / "skills/goals/SKILL.md"
        target = self.root / "outside.md"
        target.write_bytes(skill.read_bytes())
        skill.unlink()
        skill.symlink_to(target)
        out = self.check("HEAD")
        self.assertNotEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("symlink inside skills/goals", out.stderr)

    def test_tracked_double_dot_folder_without_skill_fails(self):
        hidden = self.root / "skills/..hidden"
        hidden.mkdir()
        (hidden / "README.md").write_text("no skill here\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "double-dot folder")
        out = self.check("HEAD~1")
        self.assertNotEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("..hidden has no SKILL.md", out.stderr)

    def test_ignored_runtime_synced_folder_is_not_a_skill(self):
        runtime = self.root / "skills/synced/plugin/example"
        runtime.mkdir(parents=True)
        (runtime / "SKILL.md").write_text("---\nname: example\ndescription: d\n---\n")
        out = self.check("HEAD")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_tracked_folder_without_skill_fails(self):
        broken = self.root / "skills/broken"
        broken.mkdir()
        (broken / "README.md").write_text("no skill here\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "broken folder")
        out = self.check("HEAD~1")
        self.assertNotEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("broken has no SKILL.md", out.stderr)


class Routes(CatalogFixture):
    def test_category_folder_route_fails(self):
        with open(self.root / "skills/goals/SKILL.md", "a") as f:
            f.write("\nRead `engineering/no-mistakes/SKILL.md` first.\n")
        out = self.check("HEAD")
        self.assertNotEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("removed category folder", out.stderr)

    def test_flat_route_passes(self):
        skill = self.root / "skills/goals/SKILL.md"
        skill.write_text(bump_patch(skill.read_text())
                         + "\nRead `~/.agents/skills/no-mistakes/SKILL.md` first.\n")
        out = self.check("HEAD")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()

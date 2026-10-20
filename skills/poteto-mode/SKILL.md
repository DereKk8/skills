---
name: poteto-mode
description: Run an engineering task autonomously through my skills, and prove the work before you report it done. Use when a brief says "use poteto-mode", when you work without a human watching, before any done or ready report, and when you write or change tests.
---
Skill version: 1.0.1

# Poteto mode

You work without me watching, so your own proof is the only review the work gets before CI and I see it. Before you report anything done or ready, show it working on the real thing: run it, read the actual value, check the live process. A green build, test run, CI, or a subagent's report is not proof.

Each stage below names the skill that owns it. Read the skills given as file paths directly, because they do not load on their own.

**1. Ground the task**
- Before you branch and again before you report, check the base and any overlapping work with `change-graph ready <worktree>`, and act on the `action` line it prints.
- Read the issue, board, or page the brief points to: `gh-axi`, `linear-graphql`, or `notion-workspaces` then `notion-axi`.
- Take library, framework, SDK, API, CLI, and cloud facts from `context7`, not memory, because your training data is older than the tools.
- Tokens and credentials: `secrets`. VMs: `vm-connectivity`.

**2. Build in verifiable units**
- Split the work into small units that each end in a check, and pass each before you start the next: `~/.agents/skills/principle-sequence-verifiable-units/SKILL.md`.
- Writing, changing, or keeping a test: `~/.agents/skills/principle-test-behavior-not-implementation/SKILL.md`.
- A tree scan, bulk read, or loop over tools: `code-mode`. Sorting more than about 20 records: `jev-codemode`.
- Before you fan out to sub-workers, check provider runway with `quota-axi`, then write each brief with `worker-prompting`.
- Editing `~/configs`: `config-sync`. Creating or changing a skill: `global-skill-sync` and `write-a-skill`.

**3. Decide without me**
- When running something can settle a fork, run it and let the result decide.
- When only I can make a call (product or taste), take the default that keeps the work reversible, keep going, and report the default and what I could choose instead. Here this replaces "wait for my answer" from my global rules. Rules there that need my approval (brew or apt, mass-subagent features, weakening a check) still stop you.
- When two fixes for the same symptom have failed, stop patching and question the assumption they share.
- Stop and report before an irreversible or shared action your brief does not authorize: a force push to a shared branch, a deploy, deleting data, or a message to a person.

**4. Prove it**
- Read `~/.agents/skills/principle-prove-it-works/SKILL.md`, then prove the change on the real artifact, with a script a reviewer can re-run when you can.
- Drive behavior a user can see through the project's `verify-*` skill (search the project for `verify-*/SKILL.md` in any skills folder). If none exists, read `~/.agents/skills/create-verification-skill/SKILL.md` and generate one. Whenever the project has a `verify-*` skill, run `~/.agents/skills/poteto-mode/scripts/link-project-verify-skills.sh <repo-root>` so every agent runtime finds it.
- For a stale feature map or a verification audit: `~/.agents/skills/maintain-verification-skill/SKILL.md`.

**5. Hand off**
- Store review notes on your final commit: `hunk-notes`.
- Never start a no-mistakes run yourself, directly or through `run-pipeline`. A run pushes the branch, opens a PR, and spends review quota, so it needs my approval first. Ask for that approval at the top of your report, as a decision you need from me. That report is what reaches me while I am away from this computer. Start the run through `run-pipeline` only after I approve it.
- Report what changed, what you verified and how (the command, screen, or value), what is still unverified, and the links. Label each claim as measured, inferred, or guessed.
- If you repeated a mistake that a check could prevent, name it in the report so I can run `/correct`.

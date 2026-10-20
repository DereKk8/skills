# Prompt variables

System version: v1, 2026-10-08.

This file holds what we know about the variables a skill author can change, and how each one moves agent behavior. Agents read it before they write or revise a skill, and they add evidence to it after each change. The study [What Makes a Prompt Work](https://claude.ai/code/artifact/22160bec-1dc8-47b2-b89a-91dde3e6a4bf) (2026-10-07) seeded it. Its 14 laws now live here as the current best setting of each variable.

## Levels

Each variable has one level, and the evidence under it decides the level.

- **hunch**: one source, or outside guidance only (papers, vendor docs). An agent may try it but never applies it as a default.
- **observed**: it held in two or more cases, and at least one case is on this machine (an eval, a probe, a transcript, or Derek's judgment). An agent applies it by default.
- **shaky**: a later case on this machine went against it. An agent names it in its report and asks Derek before it relies on it.

Write each piece of evidence as one dated line: what changed, the result with numbers, and where the proof is. Label Derek's judgment as `Derek` so a reader can tell taste from measurement. Keep the reasons for old changes in git, not here.

## Content

### intent
- **In the text:** an opening that says what should become true and why.
- **In runs:** the agent reaches the goal in cases nobody listed. A list of claims without the intent becomes the whole scope.
- **Setting:** always state the intent. Keep a reason beside a rule only where the agent must judge cases nobody listed.
- **Level:** observed
- **Evidence:**
  - 2026-10-05 Derek: "intent derives the claims, while a list of claims gets treated as the scope" (study, section 7).
  - 2026-10-07 X4: grill-to-intent cut from 1,033 to 168 words of intent kept its behavior on Opus 5.5 and Sonnet 5.5, 120 runs (`~/evals/grill-to-intent-psi/grill-psi-v8/README.md`).
  - eval7: deleting all rationale while keeping every obligation cost no quality on cheap models (study, section 7). So the reason is optional where the agent does not judge.

### route freedom
How much the text fixes the method instead of the outcome.
- **In the text:** numbered steps, "first, then", named tools, and exact commands, against outcomes plus boundaries.
- **In runs:** too fixed, the agent runs steps that the context made pointless, replies look alike across different inputs, and the agent repeats the skill's phrases. Too free, the agent does something clever that drifts from the intent.
- **Setting:** low for judgment work (thinking, writing, design, review). High only for a fragile operation with one safe sequence (a release, credentials, a migration). Fragility decides, not importance.
- **Level:** observed
- **Evidence:**
  - Correction class 3, "You're over-specifying how the worker should get the job done" (study, section 7).
  - 2026-10-07 X5: the poteto-mode router, rewritten from procedure to outcomes, scored 4.35 against 4.10 and kept every proof behavior in 6 of 6 runs (`~/evals/skill-rewrites-x5/README.md`).
  - 2026-10-08 Derek: he judges a skill first by whether its written structure lets the model reach the intent its own way, unless the skill describes a fixed workflow.

### done as evidence
- **In the text:** what proves the work is done (a value read back, a run shown), or the exact output shape.
- **In runs:** without it, the agent stops early or claims success from a proxy such as green tests.
- **Setting:** every skill that ends in a claim names its proof.
- **Level:** observed
- **Evidence:**
  - Correction class 6, false claims and false greens (study, section 7).
  - 2026-10-07 X5: under poteto-mode, all 6 runs proved the fix by running the CLI on real files (`~/evals/skill-rewrites-x5/README.md`).

### authority
- **In the text:** what is out of scope, what is irreversible, who decides, and for unattended work the stops answered in advance.
- **In runs:** without it, the agent decides questions that belong to Derek, or it stops when it could have continued.
- **Setting:** name the stops for irreversible, shared, or scope-changing actions. Say that reversible, in-scope work continues.
- **Level:** observed
- **Evidence:**
  - Correction class 4, "Why did you stop? Everything stopped." (study, section 7).
  - 2026-10-07 X5: after worker-prompting lost the rule that keeps the orchestrator's decisions apart from the captain's, both runs of one scenario decided the captain's scope question (`~/evals/skill-rewrites-x5/README.md`).

### unfindable context
- **In the text:** Derek's goals, earlier decisions, and state the agent cannot reach, as pointers more than pasted text.
- **In runs:** repository tours and facts the agent can read itself added about 20% cost with no gain (study, V3).
- **Setting:** include only what the agent cannot find, cannot trust, or would not know to look for. A public fact belongs only when the agent's memory is likely stale or the search costs far more than one line.
- **Level:** observed
- **Evidence:**
  - Controlled studies in the study's E1 grade (V3).
  - 2026-10-07 Derek: agents can search the web, so "outside the repo" is the wrong test (study, revision 2).

### provenance
- **In the text:** each rule traces to a failure someone reproduced, or to a call only Derek can make.
- **In runs:** a rule written for a reproduced gap fixes that gap. Several rules for one root cause add output and fix nothing.
- **Setting:** add a rule only for a failure you reproduced on the current model. Fix the shared root cause once instead of patching each symptom.
- **Level:** observed
- **Evidence:**
  - 2026-10-07 X4: one added clause for the reproduced contradiction gap (S4) fixed it on both models (`grill-psi-v8/README.md`, arm SNIPE).
  - Four rules for four observed failures with one root cause did not help and added about 150 lines of output per run (study, section 7).

## Architecture

### obligation count
The number of separate things the text asks the agent to do. Words are not the measure.
- **In the text:** count the rules, not the words.
- **In runs:** full compliance falls as rules multiply. Length alone changed nothing. But cutting the rule for a behavior the model does not show by default loses that behavior.
- **Setting:** keep a rule only when the model would not behave that way by default, and merge patches into one principle.
- **Level:** observed
- **Evidence:**
  - Size had no effect across a 9.7x range, r = 0.046 (study, section 7).
  - 2026-10-07 X5 G6: after "keep imports free of startup work" was cut, the model wrote a clean import 2 of 8 times against 4 of 4 with the rule (`~/evals/skill-rewrites-x5/README.md`).

### conflicts
- **In the text:** the same rule in two files, or two files that disagree.
- **In runs:** conflicts cost reasoning and stall some models. Duplicates drift apart into conflicts.
- **Setting:** give each rule one owner file. Other files point to it.
- **Level:** observed
- **Evidence:**
  - Controlled studies in E1 and vendor guidance (study, V14).
  - 2026-10-07: linear-graphql told agents to always load task-board while task-board said never outside firstmate (study, correction C3).
  - 2026-10-12: Agent Vault replaced raw-key access instructions in eight global files. A bounded Luna review accepted six routing cases after one inherited-startup ambiguity was fixed. Automated Claude probes ran zero times because weekly quota was exhausted (`~/.local/state/skill-evidence/agent-vault-access-2026-10-12.json`).

### trigger
The description, plus a load path that works in every runtime.
- **In the text:** a description in Derek's words that names the requests that should load the skill, and nothing that blocks loading.
- **In runs:** a skill that never loads changes nothing. A broad description loads where it does not belong.
- **Setting:** write the description as the trigger: name the concrete requests in Derek's words, and when another skill shares the topic, say to load both. Check it with probes that should load and probes that should not.
- **Level:** observed
- **Evidence:**
  - Before 2026-10-07: poteto-mode's principles loaded in 18 of 42 Claude Code sessions because the Skill tool was blocked, against 35 of 47 in Pi, where agents read the file (study, section 7).
  - A project-specific workflow skill loaded in 126 sessions, far outside the project it described (study, section 7).
  - 2026-10-08 history: in the last 45 days, write-a-skill loaded after 3 of 28 requests to create or edit a skill. global-skill-sync often loaded instead.
  - 2026-10-08 probes, Opus 5.5: a description that names the requests in Derek's words ("remove a stale part", "check a skill after its tool changed") and says to load beside global-skill-sync loaded on 8 of 9 runs of three load probes, against 1 of 9 for the old description (`~/.local/state/skill-evidence/probes/write-a-skill/20261008T133647Z-after-x3.json`, `20261008T133722Z-before-x3.json`). Three near-topic skip probes stayed out under both texts in single runs (`20261008T133601Z-after.json`, `20261008T133615Z-before.json`).
  - 2026-10-13: explicit Agent Vault profile and inherited-connection triggers passed 5/5 Claude CLI probes versus 4/5 before. The project-profile probe passed 3/3 repeats versus 0/3 before (`~/.local/state/skill-evidence/agent-vault-access-2026-10-12.json`). The inherited probe asserts the literal next command instead of redundant skill loading for a global yes/no rule.
  - 2026-10-20: project names left the secrets and notion-workspaces text for a private overlay and the readiness doc. Loading held: secrets passed 4/4 generic and 3/3 project probes, its project-profile probe 3/3 repeats, and notion-workspaces loaded on a project request 3/3 before and 3/3 after (`~/.local/state/skill-evidence/probes/{secrets,notion-workspaces}/20261020T*`). A notion probe that asks which profile to use loaded secrets instead on 2 of 3 runs, with the right profile in all 3 replies.

### output contract position
- **In the text:** a short, headed checklist of the reply's shape, placed last.
- **In runs:** the last thing read anchors the answer's shape.
- **Setting:** use it only when the shape matters.
- **Level:** observed
- **Evidence:**
  - grill-to-intent bisection: without its closing Output Contract, a bare build request produced 600 lines of Python. Restoring the contract fixed it. The same checks as inline prose did not (study, section 7).

### target model
- **In the text:** nothing. This variable lives in how the skill is tested.
- **In runs:** models differ on asking, verifying, and delegating. An eval's own setup once hid a real regression.
- **Setting:** test in the production setup, on the model that will run the skill, and test again when that model changes.
- **Level:** observed
- **Evidence:**
  - X4: the same text asked questions first on 4 of 6 bare requests on Opus 5.5 and on 0 of 6 on Sonnet 5.5 (`grill-psi-v8/README.md`).
  - An eval scaffold that told the model its role hid the 600-line regression (study, section 7).

### enforcement in code
- **In the text:** a fixed constraint that a hook, validator, or gate could check instead.
- **In runs:** code enforces a fixed rule every time. A structural check can reward form filling.
- **Setting:** move a fixed, checkable rule into code, and keep prose for judgment.
- **Level:** hunch
- **Evidence:**
  - Vendor guidance and workstation observation (study, V21). Not measured on this machine.

## Form

### framing
- **In the text:** "When <situation>, the agent <does an observable behavior>, because <reason>", against bare commands, or a weakness stated alone ("you tend to...").
- **In runs:** Derek gets better results from behavior plus reason. Vendor guidance says a weakness stated alone can anchor the failure. The grammar by itself showed no effect.
- **Setting:** write each rule as the behavior you expect and its reason.
- **Level:** observed
- **Evidence:**
  - 2026-10-07 Derek: he gets better results from instructions written as behavioral expectations (study, law 14).
  - Vendor guidance: state the wanted behavior and the reason (study, V23).
  - fast-v3: commands against prose bans differed by 0.42 of one standard error, which is noise, so the gain is in the content, not the grammar (study, section 5).

### register
Volume and word choice: capitals, MUST and NEVER, hype words.
- **In the text:** shouting, alarm words, or mannered words.
- **In runs:** vendor guidance says loud text makes a cautious, over-applying agent. Hype words hurt Derek's first-read comprehension.
- **Setting:** normal volume and plain words. Urgent wording may appear in a trigger, never in a body.
- **Level:** hunch
- **Evidence:**
  - Vendor guidance (study, V8 and V11).
  - Small-prompt evals on this machine found no effect on output quality (study, V8).

### shape echo
- **In the text:** the shape of the skill: telegraphic, list-heavy, or prose.
- **In runs:** the reply may copy the shape of the text.
- **Setting:** write one behavior as one sentence, and use a list only for parallel items or ordered steps.
- **Level:** hunch
- **Evidence:**
  - Vendor guidance (study, V10). Not measured.

### examples
- **In the text:** a sample output.
- **In runs:** the strongest steering signal there is, and the agent copies it too closely.
- **Setting:** use examples only for output whose format matters, and give several that differ.
- **Level:** hunch
- **Evidence:**
  - Vendor guidance (study, V6).

### format
Prose, bullets, or XML tags.
- **In runs:** no format won across studies or here.
- **Setting:** do not spend effort on it.
- **Level:** observed (no effect)
- **Evidence:**
  - Prose, XML, and affirmative style made no difference at about 220 tokens (study, section 7).
  - No portable winner in the controlled studies (study, V12).

---
name: lavish
description: Turn complex or visual agent responses into rich, reviewable HTML artifacts the user can annotate and send feedback on, using the lavish-axi CLI. Use when about to give a plan, comparison, diagram, table, code diff, report, or anything easier to grasp visually than as prose.
argument-hint: <what the artifact should show>
author: Kun Chen (kunchenguid)
metadata:
  hermes:
    tags: [html, review, artifacts, visualization]
    category: productivity
---
Skill version: 1.0.0

# Lavish Editor
Rich HTML artifacts as collaborative review surfaces. When a response is clearer as a page (plan, comparison, diagram, table, diff, report, prototype, feedback loop), build HTML then `npx -y lavish-axi <html-file>` for browser review/annotate/queue-prompts/feedback. No global install needed; follow-ups shown as `lavish-axi ...` run with `npx -y` prefix.

Request: $ARGUMENTS (non-empty = explicit `/lavish`, build now; empty = infer from conversation).

Workflow: 1. Create artifact (default `.lavish/<name>.html`). 2. `npx -y lavish-axi <html-file>` (open/resume). 3. Ensure ngrok tunnel live (below), paste shareable URL in chat. 4. `npx -y lavish-axi poll <html-file>` (long-polls for annotations/queued prompts/`layout_warnings`; silent until action - never kill; background it if harness limits runtime, re-run on timeout, feedback never lost). 5. Fix `layout_warnings` (overflow/clipped/overlap) before involving human. 6. Apply feedback, re-poll with `--agent-reply "<msg>"`. 7. `end <html-file>` when done.

Remote access: one ngrok tunnel covers all sessions (local server port 4387 or `$LAVISH_AXI_PORT`). After step 2, reuse live tunnel via pidfile (`$HOME/.lavish-axi/ngrok.pid` + log) or start `nohup ngrok http <port>` as harness-tracked background task (not bare `&`); wait ≤10s for `started tunnel.*url=` line. Shareable link = local session URL host swapped for `$NGROK_URL`, `/session/<key>` path kept. Requires ngrok on PATH + authed (`ngrok config check`); else share local `url:` only, do not install/auth yourself. Default-plan URLs are public - warn on sensitive content. On `lavish-axi stop`, also kill tunnel pid + rm pidfile.

Visuals: hierarchy makes decisions/risks/tradeoffs/next actions obvious; sections/cards/tables/diagrams/comparisons over prose; deliberate type/spacing/color; no horizontal overflow at any nesting (flex/grid children need `minmax(0,1fr)` + `min-width: 0`; wrap/truncate long tokens).

Playbooks (`npx -y lavish-axi playbook <id>`): open every matching one before writing HTML (artifacts often combine several). `diagram` (flows/arch/state - use Mermaid, not hand divs, unless annotated SVG needed), `table`, `comparison`, `plan`, `code` (source/diffs/before-after), `input` (required when collecting decisions/choices/triage/scope in-artifact), `slides`.

Rules: artifacts in `.lavish/` unless told otherwise; co-locate assets (images/CSS/fonts/scripts) beside HTML, relative paths, never leading `/`. `poll` waits for feedback/warnings (fix warnings first). `stop` shuts server (also self-stops idle); kill tunnel too. Design source priority: (1) user-named look/system; (2) subject project's own system (its Tailwind/theme/tokens/library/brand/pages; render app-UI mocks in that app's system even from another repo); (3) Tailwind v4 browser + DaisyUI v5 CDN via `npx -y lavish-axi design` (router + snippets + Mermaid init + component ref), CDN over hand styles unless told otherwise. State which source used and why. No auto-injected design system; artifacts render standalone without lavish-axi running.

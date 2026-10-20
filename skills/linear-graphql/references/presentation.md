# Linear Presentation: Clean, Polished, Bloat-Free Pages

Linear is not a flat Markdown dump; it is a structured, two-column workspace designed for rapid cognitive scanning. The right sidebar, header, board columns, and progress bars natively display metadata. Dumping metadata, logs, and verbose diaries into Markdown descriptions duplicates UI elements, creates visual noise, and degrades readability.

Use this guide to produce beautifully formatted, harmonized Linear pages with zero text bloat.

---

## 1. The Anti-Bloat Rule: Let Linear's UI Do UI Work

Never duplicate in Markdown what Linear natively renders as an interactive UI element:

| Metadata / Capability | Bloated Markdown Anti-Pattern (DO NOT DO) | Native Linear Primitive (ALWAYS USE) | Visual UI Presentation |
|---|---|---|---|
| **Workflow State** | `**Status:** In Progress` | `stateId: "..."` in mutation | Board column position & header status badge |
| **Priority** | `**Priority:** High` | `priority: 2` (0=None, 1=Urgent, 2=High, 3=Med, 4=Low) | Distinctive priority icon in lists and headers |
| **Effort / Complexity** | `**Estimate:** 3 points` | `estimate: 3` | Numeric complexity pill |
| **Target Deadline** | `**Due:** 2026-09-15` | `dueDate: "2026-09-15"` (`TimelessDate`) | Interactive calendar badge with overdue warning |
| **Milestone Grouping** | `**Milestone:** Phase A` | `projectMilestoneId: "..."` | Milestone badge & automated progress bar |
| **Sub-tasks / Micro-steps** | 15 bullet checklist of tasks | `parentId: "..."` on child issues | Interactive sub-issue tree with completion fraction |
| **Dependencies / Blockers** | `BLOCKED BY: ENG-20` | `issueRelationCreate(type: blocks, ...)` | Interactive dependency chip above description |
| **Duplicates** | `DUPLICATE OF: ENG-30` | `issueRelationCreate(type: duplicate, ...)` | Warning pill linking to the canonical issue |
| **Pull Requests** | Pasting PR URL in prose | `attachmentLinkGitHubPR(issueId, url, linkKind)` | Native GitHub card: PR #, branch, CI checks, review status |
| **Progress / Status Updates** | Appending weekly logs to Overview | `projectUpdateCreate(projectId, health, body)` | Health card (`onTrack`, `atRisk`, `offTrack`) in Updates feed |
| **Raw Logs / Traces** | 50 lines of shell or test output | `+++ Summary \n logs \n +++` or `commentCreate` | Folded collapsible section or dedicated thread comment |

---

## 2. Linear-Flavored Markdown Patterns

### A. Collapsible Sections (`+++`)
Linear natively parses `+++` blocks into interactive collapsible drawers. Use this for verbose technical output, execution receipts, stack traces, and reproduction outputs to keep the primary view scannable:

```markdown
+++ View Verification Evidence & Test Output

```text
PASS test_contract_enforcement (0.34s)
PASS test_zero_silent_promotion (0.12s)
7 checks passed; 0 failures.
```

+++
```

*Note: `<details><summary>` is also supported, but `+++` is Linear's native markdown convention.*

### B. Smart Entity References (Auto-Chips)
Linear automatically converts full entity URLs into live interactive pills containing the entity's icon, identifier, status, and title:

```markdown
<!-- Renders as an interactive, live-updating issue chip -->
https://linear.app/acme/issue/ENG-32/tenant-service-stores-both-tenant-identities

<!-- Or as formatted markdown link -->
[ENG-32](https://linear.app/acme/issue/ENG-32/tenant-service-stores-both-tenant-identities)
```

Do not use bare uninformative link text like `[click here](...)` or `[issue](...)`.

### C. Heading Discipline
- **Never use `# H1` in issue descriptions.** The issue title is already rendered as the H1 on the page. Using `#` inside the description creates competing giant headings.
- Use `## H2` for primary sections (`## Objective`, `## Constraints`).
- Use `### H3` for subsections or dated updates (`### Sep 6th · 14:30`).
- Avoid deeply nested headings (`####` or deeper).

### D. Interactive Checklists
For observable completion criteria, use GitHub-flavored task lists:

```markdown
- [ ] Safeguard watched failing before fix applied
- [x] Mutation tests verify decision validation
```

Linear renders these as interactive checkable boxes and displays a completion fraction badge.

### E. Callouts and Accent Quotes
Use blockquotes (`> `) for standing rulings, critical constraints, or mandatory policies:

```markdown
> **Standing Ruling (Sep 5th):** No code file may exceed 500 lines. Decompose along clear responsibility seams.
```

Linear renders this with a sleek left accent border.

### F. Compact Tables
Use 2- or 3-column tables for audit snapshots and side-by-side criteria. Do not build wide 6-column tables that require horizontal scrolling in Linear's reading pane:

```markdown
| Criterion | Result | Evidence |
| --- | --- | --- |
| Decision authorises intent | Met | Commit `8361410` |
| Safe guard watched failing | Met | PR #51 check run |
```

### G. Unambiguous Dates
- In Markdown descriptions, **always write unambiguous dates**: `Sep 6th, 2026`.
- **Never use relative text**: `today`, `yesterday`, or `next Tuesday` rot immediately in durable documents.
- **Do not write `<linear-date>` tags** in API writes: Linear's GraphQL markdown parser leaves them as literal text strings. For native calendar deadlines, use the `dueDate` API field.

---

## 3. The Two Page Archetypes

The workspace uses two distinct kinds of Linear pages. Never mix their conventions.

### Archetype 1: The Attention Surface (Task Board / `PER-`) — Canonical Standard (Final Draft B)
*Adopted Sep 6th, 2026. Synthesizes executive minimalism, prominent decision callouts, and visual phase progression.*

- **Audience:** The user, for rapid cognitive scanning across all tracked work in 3-5 seconds.
- **Tone:** Non-technical, outcome-oriented, zero agent jargon (no "worktree", "harness", "scout", "subagent", "pipeline").
- **Update Rule:** **Replace, do not append.** "Where it stands" is the current ground truth, not an event log.
- **Core Structural Rules:**
  1. **Top-line outcome**: `**What this is**` explains what will be different when finished in 1-2 plain sentences.
  2. **Prominent Decision Callout**: When work is blocked on a user ruling or decision, elevate it immediately below "What this is" using `> ⚠️ **Decision Required:** ...`. Never bury a bottleneck in prose. When no decision is required, omit the blockquote entirely.
  3. **Visual Phase Pulse**: Under `**Where it stands**`, maintain a high-level 3-phase progression checklist (`- [x] Phase 1`, `- [ ] Phase 2`). Linear renders interactive checkboxes and progress fraction badges.
  4. **Unambiguous Attention**: `**What needs you**` states the exact ruling needed or reads strictly: `*Nothing — this is moving on its own.*`
  5. **Auto-Chip Detail**: `**Detail:**` links to the canonical project plan issue or pull request using full Linear URLs.

#### Standard State (When moving on track):
```markdown
**What this is** — 1-2 plain language sentences. What will be different when finished.

**Where it stands** — 1 concise paragraph, present tense. Current truth.

- [x] Phase 1: [Milestone / contract definition]
- [x] Phase 2: [Implementation / safeguards]
- [ ] Phase 3: [Integration / verification]

**What needs you** — *Nothing — this is moving on its own.*

**Detail:** [Linear auto-chip link to project plan or PR]
```

#### Bottleneck State (When blocked on a user ruling):
```markdown
**What this is** — 1-2 plain language sentences. What will be different when finished.

> ⚠️ **Decision Required:** Phrased as a crisp, single question the user can answer in one line.

**Where it stands** — 1 concise paragraph, present tense. Explains what is ready and what is paused awaiting the ruling.

- [x] Phase 1: [Completed milestone]
- [ ] Phase 2: [Paused milestone] *(blocked)*
- [ ] Phase 3: [Downstream work]

**What needs you** — Ruling on the specific question above.

**Detail:** [Linear auto-chip link to project plan or PR]
```

### Archetype 2: The Plan of Record (Project Board / `MN-`)
- **Audience:** Future contributors and agents reconstructing the technical architecture and rationale.
- **Tone:** Technical, reasoned, precise. Explains what is built, why, and what proves it.
- **Update Rule:** **Preserve the correction trail.** Record revisions and pivots, but prune routine intermediate progress notes.
- **Structure:**
  - `## Objective` (What must become true and why)
  - `## Constraints` (Settled decisions that must not be reopened)
  - `## Revisions` (Dated requirement changes: `**REVISED <Date>:** ...`)
  - `## Proof of completion` (Observable state-of-the-world checkboxes)
  - `## Implementation updates` (Pruned to load-bearing milestones and reversals)
  - `## Audit snapshot` (3-column table: Criterion | Result | Evidence)
  - `## Background` (Context and authorization origin)

---

## 4. Project Updates vs. Project Overview

A project in Linear has two primary surfaces:
1. **The Overview (`project.content`)**: The durable project specification, architecture vision, and milestone plan.
2. **The Updates Feed (`projectUpdateCreate`)**: The chronological feed of health and progress reports.

### The Anti-Pattern
Agents repeatedly append status notes to the bottom of the project overview document (`content`), turning a clean design document into a messy scroll of timestamped entries.

### The Polished Pattern
Leave the project overview durable and stable. When reporting progress, post a native **Project Update**:

```graphql
mutation PostWeeklyUpdate($input: ProjectUpdateCreateInput!) {
  projectUpdateCreate(input: $input) {
    success
    projectUpdate {
      id
      url
      health
    }
  }
}
```
- Variables:
  ```json
  {
    "input": {
      "projectId": "<project UUID>",
      "health": "onTrack",
      "body": "Phase A semantic skeleton completed. Storage invariants verified with mutation tests.\n\nNext focus: Phase C client integration."
    }
  }
  ```
- **Result in Linear UI:** Updates the project's health badge in the project header, records the author and timestamp, and notifies subscribed stakeholders without touching the main overview document.

---

## 5. Before & After: Bloated vs Polished Issue

### Bloated Issue (Bad)
```markdown
# FIX BUG IN PROVISIONING

**Status:** In Progress
**Priority:** High
**Assignee:** Alex
**Due Date:** 2026-09-10
**Milestone:** Phase A
**Dependencies:** BLOCKED BY ENG-20

## Summary
We need to fix the provisioning contract.

## Execution Log
Running pytest...
============================= test session starts ==============================
collected 12 items
tests/test_provisioning.py ............                                  [100%]
============================== 12 passed in 1.45s ==============================

## Updates
Update 1 (10:00): Investigated bug.
Update 2 (11:30): Added test.
Update 3 (14:00): Opened PR https://github.com/acme/tenant-service/pull/51
```
*Why it fails:* Giant duplicated metadata header, raw terminal dump, unpruned chronological log, manual dependency text instead of native link.

### Polished Issue (Good)
- **GraphQL Fields Set:**
  - `stateId`: "In Progress"
  - `priority`: 2 (High)
  - `dueDate`: "2026-09-10"
  - `projectMilestoneId`: (Phase A UUID)
- **Relations Created:**
  - `issueRelationCreate(issueId: "ENG-20", relatedIssueId: "THIS_ID", type: blocks)`
- **Attachments Created:**
  - `attachmentLinkGitHubPR(issueId: "THIS_ID", url: "https://github.com/acme/tenant-service/pull/51", linkKind: links)`
- **Description Body:**
```markdown
## Objective
Make the tenant service accept and store both the canonical tenant UUID and immutable tenant handle, expose the v2 provisioning contract, and report the correct identity to downstream services.

## Proof of completion
- [x] Provisioning contract accepts dual tenant identities
- [x] Downstream notification emits canonical UUID
- [x] Mutation tests pass with zero silent promotion

+++ Verification Evidence
```text
tests/test_provisioning.py ............ [100%]
12 passed in 1.45s
```
+++
```
*Why it succeeds:* Clean, beautiful, perfectly harmonized with Linear's sidebar and cards, zero metadata bloat, terminal noise neatly folded, and dependencies visually tracked by the platform.

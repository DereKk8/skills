# Linear GraphQL: Verified Operations & Schema Recipes

Verified against the live Linear GraphQL API and schema in a live workspace on 2026-09-06. Reconfirm unfamiliar or changed fields; this is a tested operational cookbook, not an exhaustive schema dump.

---

## 1. Query Complexity & Connection Bounding

### The 10,000 Complexity Ceiling
Linear calculates query complexity based on nested selections and connection multipliers. Unbounded connection selections (omitting `first: N`) or deeply nested selections fail immediately with:

```json
{
  "errors": [{
    "message": "Query too complex",
    "extensions": {
      "type": "invalid input",
      "code": "INPUT_ERROR",
      "statusCode": 400,
      "userPresentableMessage": "The query is too complex. Complexity: 15185. Maximum allowed complexity: 10000."
    }
  }]
}
```

### Connection Rules
1. **Always provide `first: <Int>`** on connection fields (e.g. `issues(first: 10)`, `teams(first: 5)`, `states(first: 20)`).
2. **Paginate with cursors**: request `pageInfo { hasNextPage endCursor }` and pass `after: $cursor` on subsequent queries.
3. **Keep selections narrow**: request only fields required for the immediate decision or verification.

```graphql
query BoundedTeamStates($teamId: String!) {
  team(id: $teamId) {
    id
    name
    states(first: 20) {
      nodes { id name type }
    }
    labels(first: 50) {
      nodes { id name color }
    }
  }
}
```

---

## 2. Issues: Creation, Update & Sub-Issues

### Create Issue
```graphql
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
      url
      state { id name }
      priority
      estimate
      dueDate
    }
  }
}
```

**Tested Input Fields:**
- `teamId` (String!): Team UUID.
- `projectId` (String): Project UUID.
- `stateId` (String): Workflow state UUID (queried from team's states).
- `title` (String!): Outcome-oriented title.
- `description` (String): Clean Markdown body (see [presentation.md](presentation.md)).
- `priority` (Int): `0` = No priority, `1` = Urgent, `2` = High, `3` = Medium, `4` = Low.
- `estimate` (Int): Numeric complexity points.
- `dueDate` (TimelessDate): ISO date string `YYYY-MM-DD`.
- `projectMilestoneId` (String): Milestone UUID.
- `parentId` (String): Parent issue UUID or identifier (e.g. `"ENG-10"` or UUID) to nest as a sub-issue.
- `labelIds` ([String!]): Array of label UUIDs.

### Update Issue
```graphql
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue {
      id
      identifier
      state { id name }
    }
  }
}
```

**Differential Label Updates:**
Instead of overwriting `labelIds` (which risks clobbering concurrent edits), use differential updates:
- `addedLabelIds` ([String!]): Add specific labels without touching others.
- `removedLabelIds` ([String!]): Remove specific labels without touching others.

**Rule:** Send only intended changes. Never pass untouched fields as null.

---

## 3. Native Issue Relations (`issueRelationCreate`)

Instead of writing text dependencies in descriptions, create native relations. Linear renders interactive relation pills and flags blocked work automatically.

```graphql
mutation LinkIssues($input: IssueRelationCreateInput!) {
  issueRelationCreate(input: $input) {
    success
    issueRelation {
      id
      type
      issue { id identifier }
      relatedIssue { id identifier }
    }
  }
}
```

**Relation Types (`type`):**
- `blocks`: `issueId` blocks `relatedIssueId`. On the related issue, Linear displays "Blocked by `issueId`".
- `duplicate`: `issueId` is a duplicate of `relatedIssueId`.
- `related`: Bidirectional related association.
- `similar`: Semantic similarity link.

Both `issueId` and `relatedIssueId` accept either a UUID or an issue identifier (e.g. `"ENG-32"`).

---

## 4. Native GitHub Pull Request Links (`attachmentLinkGitHubPR`)

Creates a native GitHub attachment card displaying PR title, number, live CI check status, and reviewer approval state.

```graphql
mutation LinkPullRequest($issueId: String!, $url: String!, $linkKind: GitLinkKind!) {
  attachmentLinkGitHubPR(issueId: $issueId, url: $url, linkKind: $linkKind) {
    success
    attachment {
      id
      title
      url
      subtitle
    }
  }
}
```

**`linkKind` values:**
- `links`: Informational association without triggering automated closure.
- `closes`: Advances issue to completed state when PR merges.
- `contributes`: Contributes toward issue progress.

*Verification note: The API creates the attachment card immediately. Inspect the issue's attachments before creating to avoid duplicates.*

---

## 5. Project Updates (`projectUpdateCreate`)

Use native project updates for milestone and weekly progress reports instead of constantly appending text to the project overview (`project.content`).

```graphql
mutation PostProjectUpdate($input: ProjectUpdateCreateInput!) {
  projectUpdateCreate(input: $input) {
    success
    projectUpdate {
      id
      url
      health
      createdAt
    }
  }
}
```

**Input Fields:**
- `projectId` (String!): Project UUID.
- `health` (ProjectUpdateHealthType!): `onTrack` (green), `atRisk` (yellow), `offTrack` (red).
- `body` (String!): Markdown update report.
- `isDiffHidden` (Boolean): Set `true` to hide Linear's auto-generated diff of completed issues/milestones since the last update.

---

## 6. Project Milestones

```graphql
mutation CreateMilestone($input: ProjectMilestoneCreateInput!) {
  projectMilestoneCreate(input: $input) {
    success
    projectMilestone { id name targetDate sortOrder }
  }
}

mutation UpdateMilestone($id: String!, $input: ProjectMilestoneUpdateInput!) {
  projectMilestoneUpdate(id: $id, input: $input) {
    success
    projectMilestone { id name targetDate sortOrder }
  }
}
```

**Fields:** `projectId`, `name`, `description`, `targetDate` (`TimelessDate`, `YYYY-MM-DD`), `sortOrder` (Float).

---

## 7. Documents

```graphql
mutation CreateDocument($input: DocumentCreateInput!) {
  documentCreate(input: $input) {
    success
    document { id title url }
  }
}

mutation UpdateDocument($id: String!, $input: DocumentUpdateInput!) {
  documentUpdate(id: $id, input: $input) {
    success
    document { id title updatedAt }
  }
}
```

**Fields:** `projectId`, `title`, `content` (Markdown), `icon` (e.g. `"book"`), `color` (hex string).
*Rule: Before updating document content, read the current text and compare against your snapshot to prevent overwriting concurrent edits.*

---

## 8. Thread Comments (`commentCreate`)

Use comments for test output receipts, temporary diagnostic logs, or threaded discussion rather than cluttering the primary issue description.

```graphql
mutation AddComment($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    success
    comment { id body url createdAt }
  }
}
```

**Fields:** `issueId` (or `projectId`), `body` (Markdown), `parentId` (for threaded replies).

---

## 9. Targeted Schema Introspection

Avoid broad introspection queries that exceed complexity limits. Introspect only specific types or enums:

```graphql
query InspectType($name: String!) {
  __type(name: $name) {
    name
    inputFields {
      name
      type { name kind ofType { name kind } }
      description
    }
    enumValues {
      name
      description
    }
  }
}
```

---

## 10. Markdown Normalization & Rendering Facts

1. **URL Normalization**: Linear normalizes bare URLs in descriptions into `[URL](<URL>)`. Assertions comparing exact raw strings will fail even when the write landed correctly. Compare semantic content and canonical URLs.
2. **Date Tags**: `<linear-date date="YYYY-MM-DD">...</linear-date>` tags do NOT render as interactive chips when written via the GraphQL API description. They render as literal raw text. Use clear human strings in text (e.g. `Sep 6th, 2026`) and set `dueDate` on the issue for native UI date badges.
3. **Auto-Chips**: Pasting full Linear resource URLs (`https://linear.app/<org>/issue/<ID>`) causes Linear's web client to render interactive issue pills with live status and title.
4. **Collapsible Blocks**: Use `+++ Title \n Content \n +++` to cleanly fold stack traces, test logs, and raw diffs.

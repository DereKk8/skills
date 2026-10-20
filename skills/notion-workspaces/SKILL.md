---
name: notion-workspaces
description: >-
  Route Notion work to the correct workspace when the user says "my Notion",
  names a Notion workspace, team, or project, or asks for Notion work without a
  workspace.
---
Skill version: 4.0.0

# Notion Workspaces

Choose the workspace from the user's words before using Notion. Follow the
`secrets` skill for the profile and authenticated HTTP access. Never fetch or
pass a raw Notion API key.

This machine's workspace map is private. Read
`~/projects/project-skills/overlays/notion-workspaces.md` first: it lists the
words that name each workspace and the Agent Vault profile each one uses. "My
Notion", "personal", or no project name means the personal workspace, which
uses `coding`.

When the request is ambiguous, or the overlay is missing, ask which workspace
the user means. Never route "my Notion" to a project workspace.

When the map lists a workspace with no configured profile, stop and name the
missing profile in the setup report. Never claim that the profile exists or
fetch that workspace's key directly.

Before HTTP work, check that an inherited `AGENT_ACCESS_PROFILE` matches the
profile the map gives for the requested workspace. If it does not match, stop
and report the workspace/profile mismatch. Do not use another workspace's
session or start a replacement session. Without an inherited profile, follow
the selected route through `secrets`; for a project profile, check readiness
for Notion. Service selection checks readiness and does not narrow the
profile's access. If the selected profile is missing, doctor reports exit 78,
or Notion is pending, stop and report the needed setup. See `notion-axi` for
CLI operations.

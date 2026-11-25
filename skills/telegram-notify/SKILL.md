---
name: telegram-notify
description: >-
  Send requested notifications through Telegram. Load when the user says “notify me”,
  “don’t forget to notify me”, “let me know”, “ping me”, “tell me when”, or similar.
  Also load before reporting finished work, a decision waiting on the user, a blocker,
  or a needed credential while an earlier request to notify the user still applies.
---
Skill version: 1.0.0

A request to notify the user means Telegram, not just chat. Keep the request active for its stated scope. Send once per matching event, not on every status update. A reminder alone does not make a notification due. Honor an explicit request for a different channel or for no send.

Run `telegram-notify` before posting the matching report:

- Easy decision, blocker, or credential request: `telegram-notify decision --style bro "TITLE" "BODY"`. Say in plain words what the user needs to do. Name needed credentials, but never include their values.
- Hard decision: `telegram-notify decision --style explain "TITLE" "BODY"`. Give the setup, gap, story, stakes, options, real question, and recommendation. End with what you need the user to decide.
- Finished work or a requested milestone: `telegram-notify milestone "TITLE" "BODY"`. Add a separate `--link URL` for each pull request, using its full `https://` URL.

Chat text alone does not count as notifying. Exit 0 means Telegram accepted the message. If the command exits nonzero, report the failure in chat and say delivery is unconfirmed.

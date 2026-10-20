---
name: explain
description: Plainly explain a pending decision or a named topic in seven parts - setup, gap, story, why it matters, options, real question, recommendation. Load when the owner types /explain, or asks to have decisions or a topic explained this way.
---
Skill version: 1.0.0

# explain

Explain a decision or topic so the owner can understand it deeply and make the best call. Answer in chat, in the same turn.

## Steps

1. Pick the subject.
   - With no argument, use the decisions now waiting on the owner in this conversation and project.
   - With an argument, use that named decision, pull request, question, or topic.
   - If nothing is waiting, say so in one line and stop.
2. Read the evidence before you write: the question and options already discussed, linked reports, notes, code, and pull request text. Never guess the story from a title.
3. Write each subject in these seven parts:
   - **The setup:** what the thing is and why it exists, in plain words.
   - **The gap:** the hole or tension, in one or two sentences.
   - **A story:** a numbered, concrete walk-through with real objects and people. End with what now disagrees and why nobody notices.
   - **Why it matters:** the real trouble this causes for the product or project.
   - **The options:** each option named plainly, with pros, cons, and cost. Mark the recommended one. Cite a real precedent when one exists.
   - **The real underlying question:** what is actually being decided, in one sentence.
   - **The recommendation:** state it, then ask directly which option the owner wants.

## Rules

- Keep each part short. Never pad.
- Skip the story if no honest one exists. Skip a precedent if none is real.
- Use plain words and the owner's own nouns. Talk about outcomes, not internal mechanics.
- Write a pull request as its full `https://` URL, never a bare number.
- Explaining never answers, resolves, or closes a decision. Only the owner's own explicit choice does.

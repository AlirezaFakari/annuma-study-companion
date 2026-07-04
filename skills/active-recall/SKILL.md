---
name: active-recall
description: >
  Quizzes the user on AnNuMa (Analysis und Numerische Mathematik) exam topics
  using active recall. Use this skill whenever the user wants to be tested,
  quizzed, or drilled on a math topic, or says things like "quiz me",
  "test me on", "active recall", "flashcard", "ask me questions about",
  or "let's practice <topic>". The skill pulls verified content from the
  AnNuMa knowledge base via the MCP server, generates a question, waits for
  the user's answer, then judges correctness against the source material.
  It never invents facts and only quizzes from retrieved, verified content.
---

# Active Recall Skill

## Purpose

This skill turns the user's own AnNuMa study material into an active-recall
practice session. Instead of passively re-reading summaries, the user is
asked questions and must retrieve the answer from memory. This is grounded
in the spacing/testing effect from learning science: retrieval practice
produces far stronger retention than re-reading.

## How it works (the loop)

1. **Discover** - Call the MCP tool `list_topics` to see what material is
   available, OR accept a topic the user names directly.
2. **Retrieve** - Call the MCP tool `query_annuma` with a read-only SELECT
   query to fetch the verified summary/solution for the chosen topic.
   Example:
   `SELECT topic, content FROM knowledge WHERE topic LIKE '%Reihen%'`
3. **Generate** - From the retrieved content ONLY, generate one focused
   recall question. Do not use outside knowledge. If the content does not
   support a question, say so and pick another topic.
4. **Wait** - Present the question and wait for the user's answer. Do not
   reveal the answer early.
5. **Judge** - Compare the user's answer to the source content using
   LLM-as-judge (assess mathematical correctness, not exact string match).
   Accept notational flexibility (e.g. `x^2` for x squared, `sqrt(x)` for
   square root, `(a+b)/c` for fractions).
6. **Feedback** - Tell the user if they were right. If wrong, show the
   correct answer drawn from the source, and if a Musterloesung exists,
   point to the relevant step so they learn WHERE they went wrong.
7. **Continue** - Offer the next question, or let the user switch topic or stop.

## Grounding rule (critical)

Every question and every judgement MUST be based only on content returned
by the MCP server. This skill must never fabricate formulas, definitions,
or solutions. If the knowledge base lacks the needed content, state that
clearly rather than guessing. This is what makes the companion trustworthy
for real exam preparation.

## Answer input format

The user types math answers in plain-text notation:
- powers: `x^2`
- multiplication: `3*x` or `3x`
- fractions: `(x+1)/(x-1)`
- roots: `sqrt(x)`

Judge by mathematical meaning, allowing for reasonable notation differences.

## Scripts

- `scripts/format_flashcard.py` - takes a raw MCP query result and formats
  it into a clean question/answer flashcard structure.

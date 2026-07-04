# AnNuMa Study Companion - Specification

## 1. Problem

A first-semester Informatik student has extensive AnNuMa (Analysis und
Numerische Mathematik) study material - lecture summaries and worked
solutions - but faces two problems when preparing for the exam:

1. **Hallucination risk:** A general chatbot may invent or distort formulas.
   For a math exam, a single wrong formula is harmful.
2. **Passive review is weak:** Re-reading summaries produces poor retention.
   Learning science shows active recall (retrieving answers from memory) is
   far more effective.

## 2. Goal

Build an AI agent that quizzes the student on AnNuMa topics using **active
recall**, drawing questions **only from verified study material**, never
from the model's own memory. The agent must be unable to modify or damage
the study material.

## 3. Course concepts demonstrated (>= 3 required)

1. **MCP Server** - exposes the knowledge base to the agent as tools.
2. **Security feature** - a read-only guardrail (SELECT-only) on all data access.
3. **Agent Skill** - an Active Recall skill defining the quiz behavior.

## 4. Architecture (three pillars)

| Pillar | Component | Role |
| --- | --- | --- |
| Data access | `mcp_server.py` | Bridges agent and database via two tools |
| Security | `is_read_only()` guardrail | Rejects any non-SELECT query |
| Behavior | `skills/active-recall/` | Defines the recall loop and grounding rule |

Data store: a local **SQLite** database (`knowledge.db`). Chosen over a live
Notion connection because it is self-contained, reproducible by judges, and
requires no access to the author's private accounts.

## 5. Components

### 5.1 Knowledge base (`knowledge.db`)
A SQLite table `knowledge(id, topic, source, type, content, question, answer)`.
Each row is one focused sub-topic (e.g. "Geometrische Reihe",
"Quotientenkriterium") and carries the study content plus a ready-made recall
question and answer, so the agent can generate precise questions. Built by
`build_db.py`.

### 5.2 MCP server (`mcp_server.py`)
Exposes two read-only tools:
- `list_topics()` - returns all available topics with source and type.
- `query_annuma(sql)` - runs a read-only SELECT and returns matching rows.

### 5.3 Read-only guardrail
`is_read_only(query)` returns true only if the query begins with SELECT.
`query_annuma` rejects anything else. This guarantees the agent can read but
never modify, delete, or corrupt the study material.

### 5.4 Active Recall skill (`skills/active-recall/`)
A `SKILL.md` (with a trigger-keyword description) plus a helper script
`format_flashcard.py` that turns a retrieved row into a clean question set.

### 5.5 Web interface (`app.py` + `templates/index.html`)
A Flask web app that brings the same agent experience to the browser. It reads
from the SAME `knowledge.db` through the SAME `is_read_only()` guardrail, so
both surfaces share one data source and one security rule. In intelligent mode
(a Gemini API key is present) it generates a recall question from the retrieved
material, lets the user type an answer in plain words, and judges it by meaning
(LLM-as-judge), returning a verdict, a score, and grounded feedback. If no key
is present it falls back gracefully to static flashcards, so a reviewer is never
blocked. It adds a lightweight streak / XP loop and a "review weak topics" mode
to encourage active recall.

## 6. Behavior scenarios (Given / When / Then)

### Scenario A: Quiz on a topic
- **Given** the knowledge base contains material on "Geometrische Reihe"
- **When** the user says "quiz me on geometrische Reihe"
- **Then** the agent retrieves that content via `query_annuma`, asks one
  recall question based only on it, and waits for the answer.

### Scenario B: Judging an answer
- **Given** the agent has asked a question and the user has answered in
  plain-text math notation (e.g. `1/(1-x)`)
- **When** the answer is evaluated
- **Then** the agent judges mathematical correctness (LLM-as-judge, not exact
  string match), confirms if correct, or shows the correct answer from the
  source if wrong.

### Scenario C: Guardrail protection
- **Given** any data request reaches the MCP server
- **When** the request is not a SELECT (e.g. DROP, DELETE, UPDATE)
- **Then** the server rejects it and the database is left unchanged.

### Scenario D: No fabrication
- **Given** the user asks about a topic not in the knowledge base
- **When** the agent cannot retrieve matching content
- **Then** the agent states the material is unavailable rather than inventing
  an answer.

## 7. Answer input format

Users type math answers in plain-text notation: powers as `x^2`,
multiplication as `3*x` or `3x`, fractions as `(x+1)/(x-1)`, roots as
`sqrt(x)`. Evaluation judges mathematical meaning, allowing reasonable
notation differences.

## 8. Out of scope

Mobile app, multi-page web frontend, multi-agent orchestration, write access
of any kind. The deliverable is a focused, local, command-line-driven agent.

## 9. Track

Agents for Good (improving education).

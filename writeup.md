# AnNuMa Study Companion — an active-recall agent grounded in verified course material

**Track:** Agents for Good (education)

---

## 1. The problem

I am a first-semester Informatik student, and my hardest exam is **AnNuMa**
(Analysis und Numerische Mathematik). Like most students, I have a large pile
of lecture summaries and worked solutions. Two things make studying from them
with an ordinary chatbot genuinely risky.

**First, hallucination.** In a math exam a single wrong formula is not a small
error — it is the difference between a correct proof and a failed one. A
general-purpose chatbot answers from its own weights, with no guarantee that
what it says matches *my* course, *my* notation, or *my* professor's
definitions. When I ask "what is the exact convergence condition for the
geometric series in our lecture?", I need the answer that is in the material,
not a plausible-sounding average of the internet.

**Second, passive review is weak.** Re-reading summaries feels productive but
produces poor retention. The testing effect from cognitive science is
unambiguous: *retrieving* an answer from memory strengthens it far more than
re-reading it. What I actually needed was something that makes me recall, not
something that hands me answers.

So the goal became specific: an agent that **quizzes me** using **active
recall**, where every question and every judgement is drawn **only from
verified study material**, and which is **structurally incapable of damaging**
that material. Trustworthy, grounded, and safe by construction — not by good
intentions.

---

## 2. What I built

The **AnNuMa Study Companion** is a study agent with two surfaces over one
shared, verified knowledge base:

- an **MCP server** that exposes the knowledge base to any MCP-compatible
  agent host as tools, and
- a **Flask web app** that brings the same experience to the browser, where I
  type an answer in plain words and an LLM judges it by meaning.

Underneath both sits a single SQLite knowledge base of **55 focused
sub-topics** spanning the entire course (lectures V1–V19): logic and sets,
series and convergence criteria, the exponential function, continuity,
differentiation and integration, complex numbers, machine numbers and error
analysis, interpolation and splines, and function series including Taylor,
Fourier, and the DFT/FFT.

Crucially, both surfaces reach that knowledge base through the **same
read-only guardrail**, so the safety guarantee does not depend on which entry
point is used.

---

## 3. Course concepts demonstrated

The capstone asks for at least three course concepts. This project leans on
four, and each one is load-bearing rather than decorative.

### 3.1 MCP Server

`mcp_server.py` implements a Model Context Protocol server named
`annuma-study-companion` exposing exactly two tools:

- `list_topics()` — returns every available sub-topic with its source lecture,
- `query_annuma(sql)` — runs a **read-only** query and returns matching rows.

This is a deliberate application of **Progressive Disclosure**: rather than
dumping the entire 55-topic knowledge base into the model's context, the agent
first discovers what exists (`list_topics`), then pulls only the specific
material it needs for the current question (`query_annuma`). Context stays
small, focused, and cheap, and the agent decides what to load based on the
task in front of it.

I verified the server live in an agent CLI: the host discovered both tools,
called `query_annuma` with a `SELECT` to fetch the Geometrische Reihe summary,
generated a question from that content, and judged my typed answer — all
through the MCP boundary.

### 3.2 Security guardrail — a Read-Only tier with Structural Gating

The security core is intentionally tiny and impossible to misread:

```python
def is_read_only(query: str) -> bool:
    return query.strip().upper().startswith("SELECT")
```

Every database access — from the MCP server *and* from the web app — is routed
through a function that refuses anything that is not a `SELECT`. `INSERT`,
`UPDATE`, `DELETE`, and `DROP` are rejected before they ever reach SQLite.

Three ideas from the security whitepaper shaped this:

- **Read-Only tier.** The agent operates entirely within a read tier. The most
  dangerous class of tool — one that mutates state — simply does not exist in
  its toolset. You cannot misuse a capability you were never given.
- **Structural Gating.** The restriction is enforced in code, at the gate, not
  requested politely in a prompt. Even if the language model were manipulated
  into *trying* to drop the table, the query never executes. Safety is a
  property of the structure, not of the model's cooperation.
- **Zero Ambient Authority.** The agent has no standing permission to write
  anywhere. It holds no ambient credential that could be borrowed to modify
  the knowledge base; the only authority it has is "read these rows."

The result is that the worst-case outcome of a fully compromised model is that
it *reads* study material. The knowledge base cannot be corrupted, which is
exactly the property a student needs before trusting a tool for exam prep.

### 3.3 Agent Skill — Active Recall

`skills/active-recall/SKILL.md` defines the behaviour as a reusable skill. Its
description is written with explicit trigger phrases ("quiz me", "test me on",
"active recall", "flashcard", "let's practice") so an agent host knows exactly
when to invoke it — the whitepaper's point that a skill's description is what
makes it discoverable and correctly triggered.

The skill encodes a seven-step loop: **discover** available topics, **retrieve**
the verified content, **generate** exactly one question from that content,
**wait** for my answer, **judge** it, **give feedback**, and **continue**. It
also carries the single most important rule of the whole project, stated as a
hard constraint: every question and every judgement must be based *only* on
content returned by the MCP server, and if the knowledge base lacks something,
the skill must say so rather than invent an answer.

### 3.4 LLM-as-judge

Grading a free-text math answer by exact string match is hopeless — `|x| < 1`,
"absolute value of x below one", and "for x with modulus under 1" are the same
answer. In the web app, the model acts as an **LLM-as-judge**: it compares my
typed answer to the retrieved source content and returns a strict-JSON verdict
with a boolean correctness, a 0–100 completeness score, one or two sentences of
constructive feedback, and the reference answer. It accepts informal notation
and judges by *mathematical meaning* — while still being anchored to the
verified material, so it cannot "generously" accept something the source does
not support.

---

## 4. How the pieces fit together

```
knowledge.db (SQLite, 55 sub-topics, V1–V19)
        │   every access is SELECT-only
   is_read_only() guardrail  ← one shared security rule
        ├───────────────► mcp_server.py  (agent layer: list_topics, query_annuma)
        └───────────────► app.py         (web layer: LLM-as-judge, KaTeX, streak/XP)
```

The design choice I care most about is that the guardrail is **shared**. It
would have been easy to secure the MCP path and leave the web path with raw
database access. Instead both go through the identical `is_read_only()` gate,
so "the agent cannot modify the knowledge base" is true globally, not just on
one code path.

I also deliberately chose a **local SQLite file** over a live connection to my
actual note-taking app. That makes the project fully **reproducible** for a
reviewer — no accounts, no private API, no external state — and it keeps the
verified material self-contained.

---

## 5. Spec-first development

Before building, I wrote `spec.md`: the problem statement, the concept mapping,
an explicit out-of-scope list, and four **Given/When/Then** scenarios. For
example:

> **Given** any data request reaches the server, **When** the request is not a
> `SELECT`, **Then** it is rejected and the database is left unchanged.

Writing the scenarios first meant the guardrail behaviour, the grounding rule,
and the "no fabrication" fallback were specified as acceptance criteria rather
than discovered by accident. The implementation then had a target to hit, and
the scenarios doubled as my test checklist.

---

## 6. Design decisions and trade-offs

**Robustness over a fragile demo.** The free Gemini tier has per-minute limits
and occasional overload (HTTP 429 / 503). Rather than let that break a live
demo, the app treats it as a first-class state: it detects a quota limit versus
a temporary overload, shows a clear "AI tutor busy" message with a sensible
retry hint, and falls back to the stored reference answer for self-assessment.
The judge never simply hangs.

**Graceful degradation so the project is always runnable.** If no API key is
present at all, the web app drops to a static flashcard mode instead of showing
an error. A reviewer with zero setup still gets a working, inspectable app;
adding a key upgrades it to the full intelligent experience. The safety
guarantee is identical in both modes, because both still go through the
read-only guardrail.

**Domain-faithful questions.** Because the study content is German (it is a
German university course, and the exam is in German), the agent generates its
questions in German — matching how I will actually be tested — while feedback
is in English for clarity. Questions and answers are rendered with **KaTeX**,
so `\sum_{k=0}^{\infty} x^k` and `\frac{1}{1-x}` appear as real typeset
mathematics rather than raw notation.

**Active-recall motivation.** Small touches — a streak counter, XP with a bonus
for consecutive correct answers, a per-topic progress bar, and a "review weak
topics" mode that re-queues exactly the sub-topics I got wrong — exist to make
retrieval practice something I keep doing, which is the entire point of the
testing effect.

---

## 7. What I learned

The biggest lesson was that **safety is a structural property, not a prompt**.
My first instinct with an LLM tool is to *ask* it to behave. Building the
read-only tier taught me to make the dangerous action impossible at the gate,
so that the model's cooperation is irrelevant to the guarantee. That reframing
— from "please don't" to "you can't" — is the single most useful idea I took
from this course.

I also learned how much leverage the **MCP + skill + guardrail** combination
gives you. The same knowledge base, exposed once through a tiny read-only
interface, powers both an agent CLI and a web app, with one security rule
covering both. Progressive Disclosure kept the agent's context lean;
LLM-as-judge made free-text answers gradeable; and the grounding rule kept the
whole thing trustworthy for the one use case that actually matters to me —
walking into the AnNuMa exam having genuinely practised, on material I can
trust.

---

## 8. Summary

The AnNuMa Study Companion is a small but complete agent that turns verified
course notes into active-recall practice. It demonstrates an **MCP server**, a
**read-only security guardrail** built on Read-Only tier / Structural Gating /
Zero Ambient Authority, an **Active Recall agent skill** with a strict
grounding rule, and **LLM-as-judge** grading — wrapped in a reproducible,
gracefully degrading package that a reviewer can run in minutes and that I will
genuinely use to study.

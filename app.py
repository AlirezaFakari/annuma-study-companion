"""
app.py
------
Flask backend for the AnNuMa Study Companion web app.

Intelligent flashcard/quiz interface that mirrors the CLI agent experience
in a browser: the user types an answer in their own words, and an LLM judges
correctness against the verified source material (LLM-as-judge).

Shared foundations with the MCP agent layer:
  - same knowledge.db data source
  - same read-only guardrail (is_read_only) on every DB access
  - same grounding rule: questions and judgements use ONLY retrieved material

Dual mode (so a reviewer is never blocked):
  - GEMINI_API_KEY set  -> intelligent mode (LLM generates questions + judges)
  - missing / failing   -> graceful fallback to static flashcards

Robust error handling:
  - Quota/rate-limit (HTTP 429) is detected and reported cleanly to the
    frontend as a 'busy' state, instead of leaving the UI stuck.
"""

import os
import re
import json
import sqlite3

from flask import Flask, jsonify, render_template, request, abort
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge.db")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL_NAME = "gemini-2.5-flash"

_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[warn] Gemini setup failed, falling back to static mode: {e}")
        _client = None

INTELLIGENT = _client is not None


# ---------------------------------------------------------------------------
# Read-only guardrail (shared rule with the MCP server)
# ---------------------------------------------------------------------------
def is_read_only(query: str) -> bool:
    return query.strip().upper().startswith("SELECT")


def run_query(query: str, params: tuple = ()):
    if not is_read_only(query):
        raise ValueError("Only read-only SELECT queries are allowed.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_row(card_id: int):
    rows = run_query(
        "SELECT id, source, topic, content, question, answer "
        "FROM knowledge WHERE id = ?",
        (card_id,),
    )
    if not rows:
        abort(404, description="Card not found")
    return dict(rows[0])


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------
class TutorBusyError(Exception):
    """
    Raised when the LLM call cannot be served right now for a transient
    reason. `reason` is one of:
      - "daily"    : the free per-DAY quota is exhausted (resets next day)
      - "quota"    : a short per-minute rate limit (retry shortly)
      - "overload" : the model is temporarily overloaded (HTTP 503)
    so the UI can show the right message. `retry_seconds` is a sane, bounded
    hint (never a huge number), and is None when waiting won't help (daily).
    """
    def __init__(self, reason: str = "busy", retry_seconds=None):
        self.reason = reason
        self.retry_seconds = retry_seconds
        super().__init__(reason)


def _raise_if_busy(err: Exception):
    msg = str(err)
    low = msg.lower()
    is_quota = ("429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in low)
    is_overload = ("503" in msg or "UNAVAILABLE" in msg or "overloaded" in low
                   or "high demand" in low)
    if not (is_quota or is_overload):
        return

    # A per-day quota is exhausted -> waitin won't help until it resets.
    if is_quota and ("perday" in low.replace(" ", "") or "per day" in low
                     or "requestsperday" in low.replace(" ", "")):
        raise TutorBusyError("daily", None)

    # Otherwise it's a short-lived limit/overload. Try to read a retry hint
    # like "retry in 19s"; only accept small, sensible values so we never
    # surface a giant number that was really a timestamp or id.
    secs = 20
    m = re.search(r"retry(?:Delay)?[^0-9]{0,12}?(\d{1,4})\s*s", msg, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 120:      # believable short window
            secs = val

    raise TutorBusyError("quota" if is_quota else "overload", secs)


# ---------------------------------------------------------------------------
# LLM helpers (intelligent mode only)
# ---------------------------------------------------------------------------
def llm_generate_question(topic: str, content: str) -> str:
    prompt = (
        "You are an experienced tutor for the German university course "
        "'Analysis und Numerische Mathematik' (AnNuMa). Your job is to help a "
        "student practise ACTIVE RECALL.\n\n"
        "Write EXACTLY ONE recall question that:\n"
        "- is based ONLY on the study material below (never outside knowledge),\n"
        "- targets the single most exam-relevant idea of this topic "
        "(a definition, a condition, a formula, or a key distinction),\n"
        "- is precise and answerable in one or two sentences,\n"
        "- is written in GERMAN, the language of the material, so it matches "
        "how the exam is phrased,\n"
        "- does NOT reveal or restate the answer.\n\n"
        "Formatting: write any mathematical expression as inline LaTeX between "
        "single dollar signs, e.g. $|x| < 1$, $\\sum_{k=0}^\\infty x^k$, "
        "$\\frac{1}{1-x}$. Use LaTeX only for actual math, not for plain words.\n\n"
        f"Topic: {topic}\n"
        f"Study material:\n{content}\n\n"
        "Return only the question text, with no preamble, no numbering, no answer."
    )
    try:
        resp = _client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return resp.text.strip()
    except Exception as e:
        _raise_if_busy(e)
        raise


def llm_judge_answer(topic: str, content: str, question: str, user_answer: str) -> dict:
    prompt = (
        "You are a fair, encouraging tutor grading a student's spoken-style "
        "answer in the course 'Analysis und Numerische Mathematik'. Judge ONLY "
        "against the study material below, by MATHEMATICAL MEANING rather than "
        "exact wording.\n\n"
        "Grading guidance:\n"
        "- Accept informal plain-text math notation (x^2, sqrt(x), (a+b)/c, "
        "|x| < 1, <=, >=) and answers in German or English.\n"
        "- Reward the core idea: if the student captures the key condition / "
        "formula / definition, count it correct even if the wording is loose.\n"
        "- A partial answer that misses an essential part is not fully correct; "
        "reflect that in the score.\n"
        "- In the feedback, be brief and constructive: say what was right, then "
        "name the missing piece or misconception. Address the student as 'you'. "
        "Write the feedback in English so it is easy to follow.\n"
        "- Formatting: write any mathematical expression as inline LaTeX between "
        "single dollar signs, e.g. $|x| < 1$, $\\frac{1}{1-x}$, "
        "$\\sum_{k=0}^\\infty x^k$. Use LaTeX only for real math, not plain words.\n\n"
        f"Topic: {topic}\n"
        f"Study material:\n{content}\n\n"
        f"Question asked: {question}\n"
        f"Student's answer: {user_answer}\n\n"
        "Respond with STRICT JSON only, no markdown, in exactly this shape:\n"
        '{"correct": true or false, '
        '"score": integer 0-100 for how complete and correct the answer is, '
        '"feedback": "1-2 constructive sentences addressed to the student as \'you\'", '
        '"model_answer": "the concise correct answer, drawn from the material"}'
    )
    try:
        resp = _client.models.generate_content(model=MODEL_NAME, contents=prompt)
    except Exception as e:
        _raise_if_busy(e)
        raise

    text = resp.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
        return {
            "correct": bool(data.get("correct", False)),
            "score": int(data.get("score", 0)) if str(data.get("score", "")).strip() != "" else None,
            "feedback": str(data.get("feedback", "")).strip(),
            "model_answer": str(data.get("model_answer", "")).strip(),
        }
    except Exception:
        return {
            "correct": False,
            "score": None,
            "feedback": "Could not parse the evaluation. Here is the reference answer.",
            "model_answer": "",
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({"intelligent": INTELLIGENT, "model": MODEL_NAME if INTELLIGENT else None})


@app.route("/api/topics")
def api_topics():
    rows = run_query(
        "SELECT id, source, topic FROM knowledge "
        "ORDER BY CAST(SUBSTR(source, 2) AS INTEGER), id"
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/question/<int:card_id>")
def api_question(card_id: int):
    row = get_row(card_id)
    if INTELLIGENT:
        try:
            question = llm_generate_question(row["topic"], row["content"])
        except TutorBusyError as q:
            return jsonify({
                "busy": True,
                "reason": q.reason,
                "retry_seconds": q.retry_seconds,
                "id": row["id"], "source": row["source"], "topic": row["topic"],
                "question": row["question"],  # stored question as fallback
            }), 200
        except Exception as e:
            print(f"[warn] question generation failed: {e}")
            question = row["question"]
    else:
        question = row["question"]

    return jsonify({
        "id": row["id"], "source": row["source"], "topic": row["topic"],
        "question": question, "intelligent": INTELLIGENT, "busy": False,
    })


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.get_json(force=True)
    card_id = int(data.get("id"))
    user_answer = str(data.get("answer", "")).strip()
    question = str(data.get("question", "")).strip()
    row = get_row(card_id)

    if INTELLIGENT and user_answer:
        try:
            result = llm_judge_answer(row["topic"], row["content"], question, user_answer)
            if not result["model_answer"]:
                result["model_answer"] = row["answer"]
            result["intelligent"] = True
            result["busy"] = False
            return jsonify(result)
        except TutorBusyError as q:
            return jsonify({
                "busy": True,
                "reason": q.reason,
                "retry_seconds": q.retry_seconds,
                "model_answer": row["answer"],
            }), 200
        except Exception as e:
            print(f"[warn] judging failed: {e}")

    # Static fallback: reveal the stored answer, user self-assesses.
    return jsonify({
        "correct": None, "score": None, "feedback": "",
        "model_answer": row["answer"], "intelligent": False, "busy": False,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)

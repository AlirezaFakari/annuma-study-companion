"""
format_flashcard.py
-------------------
Helper script for the Active Recall skill.

Takes a raw result row from the MCP `query_annuma` tool (a topic and its
content) and structures it into a clean flashcard the agent can use to
drive a recall session.

This keeps presentation logic out of the agent's reasoning: the agent
retrieves verified content via MCP, passes it here, and gets back a
predictable structure (topic, source, key points) to build a question from.
"""

import re
from dataclasses import dataclass, field


@dataclass
class Flashcard:
    topic: str
    source: str
    key_points: list[str] = field(default_factory=list)
    raw_content: str = ""


def split_into_points(content: str) -> list[str]:
    """
    Break a summary blob into individual study points.

    Splits on sentence boundaries so each point can become its own
    recall question. Placeholder markers like '[PLACEHOLDER ...]' are
    dropped so they never turn into questions.
    """
    # Remove placeholder markers
    cleaned = re.sub(r"\[PLACEHOLDER[^\]]*\]", "", content)

    # Split on sentence-ending punctuation followed by a space
    parts = re.split(r"(?<=[.!?])\s+", cleaned)

    # Keep only non-trivial points
    points = [p.strip() for p in parts if len(p.strip()) > 10]
    return points


def build_flashcard(topic: str, source: str, content: str) -> Flashcard:
    """Build a Flashcard object from a single MCP result row."""
    return Flashcard(
        topic=topic,
        source=source,
        key_points=split_into_points(content),
        raw_content=content,
    )


# Quick self-test when run directly
if __name__ == "__main__":
    demo_content = (
        "Eine Reihe ist die Summe der Glieder einer Folge. "
        "Eine geometrische Reihe konvergiert genau dann, wenn |q| < 1. "
        "Konvergenzkriterien: Majorantenkriterium, Quotientenkriterium, Wurzelkriterium. "
        "[PLACEHOLDER - real V6 text goes here]"
    )
    card = build_flashcard("Reihen und Konvergenzkriterien", "V6", demo_content)
    print(f"Topic:  {card.topic}")
    print(f"Source: {card.source}")
    print("Key points (each can become a question):")
    for i, point in enumerate(card.key_points, 1):
        print(f"  {i}. {point}")

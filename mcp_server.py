"""
mcp_server.py
-------------
MCP server for the AnNuMa Study Companion.

This server is a "bridge" (a librarian) between the agent and the
knowledge.db database. The agent cannot touch the database directly;
it can only go through the tools this server exposes.

It provides two tools:
    1. list_topics()      : lists all available topics (so the agent knows what exists)
    2. query_annuma(sql)  : runs a read-only SELECT query against the database

SECURITY GUARDRAIL (the project's second pillar):
    The query_annuma tool accepts ONLY SELECT statements. Anything else
    (DROP, DELETE, UPDATE, INSERT, ...) is rejected. This guarantees the
    agent can never modify or delete the AnNuMa knowledge base - it can
    only read from it.
"""

import sqlite3
import os
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Database path (next to this file)
DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge.db")

# Create the server with a name
app = Server("annuma-study-companion")


# ---------------------------------------------------------------------------
# Core of the guardrail: checks that a query is read-only
# ---------------------------------------------------------------------------
def is_read_only(query: str) -> bool:
    """Only statements starting with SELECT are allowed."""
    cleaned = query.strip().upper()
    return cleaned.startswith("SELECT")


# ---------------------------------------------------------------------------
# Declare the tools this server exposes
# ---------------------------------------------------------------------------
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_topics",
            description=(
                "Returns the list of all available AnNuMa topics in the knowledge base, "
                "along with their source lecture (e.g. V6) and content type. "
                "Use this first to discover what study material is available before quizzing."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="query_annuma",
            description=(
                "Runs a read-only SQL SELECT query against the AnNuMa knowledge base "
                "and returns the matching rows. The table is named 'knowledge' with columns: "
                "id, topic, source, type, content. "
                "Use this to retrieve summaries or solutions for a specific topic. "
                "Only SELECT statements are permitted; any write attempt is rejected."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A read-only SQL SELECT statement.",
                    }
                },
                "required": ["sql"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Execute tools when the agent calls them
# ---------------------------------------------------------------------------
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    # --- Tool 1: list topics ---
    if name == "list_topics":
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, source, topic, type FROM knowledge ORDER BY source")
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return [TextContent(type="text", text="No topics found in the database.")]

        lines = ["Available AnNuMa topics:"]
        for r in rows:
            lines.append(f"  [id={r[0]}] {r[1]} - {r[2]} (type: {r[3]})")
        return [TextContent(type="text", text="\n".join(lines))]

    # --- Tool 2: query the database (with guardrail) ---
    elif name == "query_annuma":
        sql = arguments.get("sql", "")

        # Enforce the guardrail
        if not is_read_only(sql):
            return [TextContent(
                type="text",
                text=(
                    "REJECTED: Only read-only SELECT queries are allowed. "
                    "This guardrail protects the AnNuMa knowledge base from modification."
                ),
            )]

        # Run the safe query
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description] if cur.description else []
            conn.close()
        except Exception as e:
            return [TextContent(type="text", text=f"Query error: {e}")]

        if not rows:
            return [TextContent(type="text", text="No results found.")]

        # Format the result in a readable way
        output = [" | ".join(col_names)]
        output.append("-" * 40)
        for row in rows:
            output.append(" | ".join(str(c) for c in row))
        return [TextContent(type="text", text="\n".join(output))]

    # --- Unknown tool ---
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Start the server (over stdio, which is how MCP communicates)
# ---------------------------------------------------------------------------
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

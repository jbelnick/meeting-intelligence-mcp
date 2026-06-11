#!/usr/bin/env python3
"""Run the three MCP tools in-process against the example transcript and
verify the server registers them with read-only annotations. CI runs this,
so the demo doubles as an integration smoke test (no MCP client required)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from meeting_intelligence_mcp.server import draft_follow_ups, extract_risks, mcp, summarize_meeting

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "team_sync.txt"


def main() -> int:
    transcript = EXAMPLE.read_text(encoding="utf-8")

    tools = asyncio.run(mcp.list_tools())
    names = sorted(tool.name for tool in tools)
    print(f"server tools: {', '.join(names)}")
    expected = ["draft_follow_ups", "extract_risks", "summarize_meeting"]
    if names != expected:
        print(f"ERROR: expected tools {expected}", file=sys.stderr)
        return 1
    if not all(tool.annotations and tool.annotations.readOnlyHint for tool in tools):
        print("ERROR: every tool must be annotated read-only", file=sys.stderr)
        return 1

    notes = summarize_meeting(transcript, title="Q3 Reporting Launch Sync")
    print(f"\nsummary: {notes['summary']}")
    print(f"decisions: {len(notes['decisions'])}  risks: {len(notes['risks'])}  actions: {len(notes['actionItems'])}")

    risks = extract_risks(transcript)
    print(f"\nrisk surface: {risks['riskCount']} risks, {risks['openQuestionCount']} open questions")
    for risk in risks["risks"]:
        print(f"  - {risk}")

    follow_ups = draft_follow_ups(transcript)
    print("\nfollow-up draft:\n")
    print(follow_ups["followUpMessage"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

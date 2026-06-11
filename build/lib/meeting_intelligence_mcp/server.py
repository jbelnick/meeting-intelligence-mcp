"""MCP server exposing meeting intelligence tools over stdio.

Wraps the public meeting-intelligence-pipelines package so any MCP client
(Claude Code, Claude Desktop, or anything else speaking the protocol) can
summarize a meeting transcript, pull the risk surface, or draft the
follow-up message. All tools are read-only and deterministic: same
transcript in, same result out, no model calls inside the server.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from meeting_intelligence import summarize_meeting_transcript

MAX_TRANSCRIPT_CHARS = 200_000

mcp = FastMCP(
    "meeting-intelligence",
    instructions=(
        "Deterministic meeting intelligence tools. Pass raw transcript text; "
        "lines in 'Speaker: text' form attribute owners best, but plain text works too. "
        "Use summarize_meeting for full notes, extract_risks for the risk surface only, "
        "draft_follow_ups for action items and a paste-ready follow-up message."
    ),
)

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


def _validated_transcript(transcript: str) -> str:
    text = (transcript or "").strip()
    if not text:
        raise ValueError(
            "transcript is empty. Pass the meeting transcript text; "
            "'Speaker: text' lines give the best owner attribution."
        )
    if len(text) > MAX_TRANSCRIPT_CHARS:
        raise ValueError(
            f"transcript is {len(text)} characters; the limit is {MAX_TRANSCRIPT_CHARS}. "
            "Split the meeting into parts and summarize each part separately."
        )
    return text


def _action_items(notes) -> list[dict[str, str]]:
    return [{"owner": item.owner, "task": item.task, "date": item.date} for item in notes.action_items]


@mcp.tool(annotations=READ_ONLY)
def summarize_meeting(transcript: str, title: str = "") -> dict[str, Any]:
    """Summarize a meeting transcript into structured notes.

    Returns the full result: title, summary, key points, decisions, risks,
    open questions, action items (owner, task, date), and a rendered
    markdown document ready to paste into a doc or message.

    Args:
        transcript: Raw transcript text. Lines like "Maya: we agreed to ship
            Friday" attribute decisions and action items to speakers.
        title: Optional title for the notes; derived from content if omitted.
    """
    notes = summarize_meeting_transcript(_validated_transcript(transcript), title=title.strip() or None)
    return {
        "title": notes.title,
        "summary": notes.summary,
        "keyPoints": notes.key_points,
        "decisions": notes.decisions,
        "risks": notes.risks,
        "openQuestions": notes.open_questions,
        "actionItems": _action_items(notes),
        "markdown": notes.to_markdown(),
    }


@mcp.tool(annotations=READ_ONLY)
def extract_risks(transcript: str) -> dict[str, Any]:
    """Extract only the risk surface from a meeting transcript.

    Use this instead of summarize_meeting when the caller only needs what
    might go wrong: risks and blockers plus the open questions that have to
    be answered. Returns counts so an empty result is unambiguous.

    Args:
        transcript: Raw transcript text, optionally with "Speaker: text" lines.
    """
    notes = summarize_meeting_transcript(_validated_transcript(transcript))
    return {
        "risks": notes.risks,
        "openQuestions": notes.open_questions,
        "riskCount": len(notes.risks),
        "openQuestionCount": len(notes.open_questions),
    }


@mcp.tool(annotations=READ_ONLY)
def draft_follow_ups(transcript: str) -> dict[str, Any]:
    """Extract action items and draft the follow-up message for a meeting.

    Returns the structured action items (owner, task, date) and a plain-text
    follow-up message that lists owners, next steps, and open questions,
    ready to paste into email or chat after a human read-through.

    Args:
        transcript: Raw transcript text, optionally with "Speaker: text" lines.
    """
    notes = summarize_meeting_transcript(_validated_transcript(transcript))
    items = _action_items(notes)
    lines = ["Hi team,", "", f"Quick recap of {notes.title}.", ""]
    if items:
        lines.append("Owners and next steps:")
        for item in items:
            due = f" (by {item['date']})" if item["date"] else ""
            lines.append(f"- {item['owner']}: {item['task']}{due}")
    else:
        lines.append("No action items were called out explicitly; flag anything I missed.")
    if notes.open_questions:
        lines.extend(["", "Open questions to close:"])
        lines.extend(f"- {question}" for question in notes.open_questions)
    lines.extend(["", "Reply if an owner, task, or date is wrong.", ""])
    return {
        "actionItems": items,
        "openQuestions": notes.open_questions,
        "followUpMessage": "\n".join(lines),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

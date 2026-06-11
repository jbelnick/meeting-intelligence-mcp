"""Tests for the MCP tool functions and server registration. The tools are
deterministic wrappers, so they are tested directly in-process; the server
surface (names, schemas, annotations) is asserted via the FastMCP API."""

from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from meeting_intelligence_mcp.server import (
    MAX_TRANSCRIPT_CHARS,
    draft_follow_ups,
    extract_risks,
    mcp,
    summarize_meeting,
)

TRANSCRIPT = (Path(__file__).resolve().parents[1] / "examples" / "team_sync.txt").read_text(encoding="utf-8")


class ServerSurfaceTests(unittest.TestCase):
    def test_exactly_three_read_only_tools(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        self.assertEqual(
            sorted(tool.name for tool in tools),
            ["draft_follow_ups", "extract_risks", "summarize_meeting"],
        )
        for tool in tools:
            self.assertIsNotNone(tool.annotations, f"{tool.name} missing annotations")
            self.assertTrue(tool.annotations.readOnlyHint, f"{tool.name} must be read-only")
            self.assertFalse(tool.annotations.destructiveHint, f"{tool.name} must be non-destructive")

    def test_tool_descriptions_present(self) -> None:
        for tool in asyncio.run(mcp.list_tools()):
            self.assertTrue((tool.description or "").strip(), f"{tool.name} has no description")


class SummarizeMeetingTests(unittest.TestCase):
    def test_structured_notes_from_example(self) -> None:
        result = summarize_meeting(TRANSCRIPT, title="Q3 Reporting Launch Sync")
        self.assertEqual(result["title"], "Q3 Reporting Launch Sync")
        self.assertTrue(result["summary"])
        self.assertTrue(result["decisions"])
        self.assertTrue(result["risks"])
        self.assertIn("# Q3 Reporting Launch Sync", result["markdown"])

    def test_action_items_have_owner_task_shape(self) -> None:
        result = summarize_meeting(TRANSCRIPT)
        self.assertTrue(result["actionItems"])
        for item in result["actionItems"]:
            self.assertEqual(sorted(item), ["date", "owner", "task"])
        owners = {item["owner"] for item in result["actionItems"]}
        self.assertIn("Devon", owners)

    def test_title_is_derived_when_omitted(self) -> None:
        result = summarize_meeting(TRANSCRIPT)
        self.assertTrue(result["title"].strip())


class ExtractRisksTests(unittest.TestCase):
    def test_risk_surface_with_counts(self) -> None:
        result = extract_risks(TRANSCRIPT)
        self.assertEqual(result["riskCount"], len(result["risks"]))
        self.assertEqual(result["openQuestionCount"], len(result["openQuestions"]))
        self.assertGreater(result["riskCount"], 0)
        text = " ".join(result["risks"]).lower()
        self.assertTrue("blocker" in text or "concern" in text or "waiting" in text)


class DraftFollowUpsTests(unittest.TestCase):
    def test_message_lists_owners_and_questions(self) -> None:
        result = draft_follow_ups(TRANSCRIPT)
        message = result["followUpMessage"]
        self.assertIn("Owners and next steps:", message)
        self.assertIn("Devon:", message)
        self.assertIn("Reply if an owner, task, or date is wrong.", message)
        for item in result["actionItems"]:
            self.assertIn(item["owner"], message)

    def test_no_actions_still_produces_a_message(self) -> None:
        result = draft_follow_ups("Ana: We only chatted about lunch options today.")
        self.assertIn("No action items were called out explicitly", result["followUpMessage"])


class ValidationTests(unittest.TestCase):
    def test_empty_transcript_raises_actionable_error(self) -> None:
        for bad in ("", "   \n  "):
            with self.assertRaises(ValueError) as ctx:
                summarize_meeting(bad)
            self.assertIn("Speaker: text", str(ctx.exception))

    def test_oversized_transcript_suggests_splitting(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            extract_risks("x" * (MAX_TRANSCRIPT_CHARS + 1))
        self.assertIn("Split the meeting", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

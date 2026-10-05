"""Tests for mechanical OpenCode JSON stdout event extraction."""

from __future__ import annotations

import json
import unittest

from scripts.opencode_events import extract_events


def event_line(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False)


class OpenCodeEventsTests(unittest.TestCase):
    def test_deduplicates_tool_updates_by_call_id(self) -> None:
        pending = {
            "type": "tool_use", "sessionID": "s1",
            "part": {"type": "tool", "id": "part1", "callID": "call1", "tool": "read",
                     "state": {"status": "running", "input": {"filePath": "src/a.py"}}},
        }
        completed = {
            "type": "tool_use", "sessionID": "s1",
            "part": {"type": "tool", "id": "part1", "callID": "call1", "tool": "read",
                     "state": {"status": "completed", "input": {"filePath": "src/a.py"}, "output": "contents"}},
        }
        result = extract_events("\n".join((event_line(pending), event_line(completed))))
        self.assertEqual(result["tool_call_count"], 1)
        self.assertEqual(result["tool_calls"][0]["status"], "completed")
        self.assertEqual(result["tool_calls"][0]["output"], "contents")

    def test_extracts_read_and_glob_paths_as_requests(self) -> None:
        events = [
            {"type": "tool_use", "part": {"type": "tool", "callID": "r", "tool": "read",
             "state": {"status": "completed", "input": {"filePath": "src/handler.py"}}}},
            {"type": "tool_use", "part": {"type": "tool", "callID": "g", "tool": "glob",
             "state": {"status": "error", "error": "denied", "input": {"pattern": "**/*.py", "path": "src"}}}},
        ]
        result = extract_events("\n".join(map(event_line, events)))
        self.assertEqual(
            [(path["tool"], path["argument"], path["value"]) for path in result["requested_read_or_search_paths"]],
            [("read", "filePath", "src/handler.py"), ("glob", "pattern", "**/*.py"), ("glob", "path", "src")],
        )
        self.assertIn("do not prove", result["path_semantics"])

    def test_selects_text_from_latest_assistant_message(self) -> None:
        events = [
            {"type": "text", "part": {"type": "text", "messageID": "m1", "sessionID": "s", "text": "old"}},
            {"type": "text", "part": {"type": "text", "messageID": "m2", "sessionID": "s", "text": "final "}},
            {"type": "text", "part": {"type": "text", "messageID": "m2", "sessionID": "s", "text": "answer"}},
        ]
        result = extract_events("\n".join(map(event_line, events)))
        self.assertEqual([part["text"] for part in result["text_parts"]], ["old", "final ", "answer"])
        self.assertEqual([part["text"] for part in result["final_text_parts"]], ["final ", "answer"])
        self.assertEqual(result["session_ids"], ["s"])

    def test_counts_non_json_lines_and_retains_error_events(self) -> None:
        error = {"type": "error", "sessionID": "s", "error": {"name": "Denied", "message": "blocked"}}
        result = extract_events("not-json\n" + event_line(error) + "\n{broken")
        self.assertEqual(result["non_json_stdout_lines"], 2)
        self.assertEqual(result["error_events"], [{"stdout_line": 2, "event": error}])
        self.assertEqual(result["session_ids"], ["s"])

    def test_empty_stdout(self) -> None:
        result = extract_events("")
        self.assertEqual(result["tool_call_count"], 0)
        self.assertEqual(result["tool_calls"], [])
        self.assertEqual(result["requested_read_or_search_paths"], [])
        self.assertEqual(result["text_parts"], [])
        self.assertEqual(result["final_text_parts"], [])
        self.assertEqual(result["non_json_stdout_lines"], 0)

    def test_without_message_ids_keeps_last_text_segment(self) -> None:
        events = [
            {"part": {"type": "text", "text": "earlier"}},
            {"part": {"type": "text", "text": "last"}},
        ]
        result = extract_events("\n".join(map(event_line, events)))
        self.assertEqual([part["text"] for part in result["final_text_parts"]], ["last"])


if __name__ == "__main__":
    unittest.main()

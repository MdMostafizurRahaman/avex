"""Extract mechanically observable events from OpenCode JSON stdout.

Path arguments record requests only. They do not establish that a call ran or
that a file was successfully read. No verdict normalization or judgment is
performed here.
"""

from __future__ import annotations

import json
from typing import Any


def _part_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    part = event.get("part")
    return part if isinstance(part, dict) else None


def _path_arguments(tool_name: str, tool_input: Any) -> list[tuple[str, str]]:
    if not isinstance(tool_input, dict):
        return []

    # Tool names vary by plugin; match the SDK-visible name without assuming
    # that any requested operation succeeded.
    name = tool_name.lower()
    keys: list[str] = []
    if "read" in name:
        keys.extend(("filePath", "path", "paths"))
    if "glob" in name:
        keys.extend(("pattern", "path", "paths"))
    if "grep" in name or "search" in name:
        keys.extend(("path", "include", "paths"))
    if "directory" in name or "list" in name:
        keys.extend(("path", "paths"))

    found: list[tuple[str, str]] = []
    for key in dict.fromkeys(keys):
        value = tool_input.get(key)
        if isinstance(value, str):
            found.append((key, value))
        elif isinstance(value, list):
            found.extend((key, item) for item in value if isinstance(item, str))
    return found


def extract_events(stdout_text: str) -> dict[str, Any]:
    """Return an evidence-preserving summary of newline-delimited JSON events."""
    calls: dict[str, dict[str, Any]] = {}
    text_parts: list[dict[str, Any]] = []
    session_ids: list[str] = []
    error_events: list[dict[str, Any]] = []
    non_json = 0

    for line_number, line in enumerate(stdout_text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            non_json += 1
            continue
        if not isinstance(event, dict):
            continue

        event_session = event.get("sessionID")
        if isinstance(event_session, str) and event_session not in session_ids:
            session_ids.append(event_session)

        event_type = event.get("type")
        if event_type == "error":
            error_events.append({"stdout_line": line_number, "event": event})

        part = _part_from_event(event)
        if part is None:
            continue

        part_type = part.get("type")
        part_session = part.get("sessionID")
        if isinstance(part_session, str) and part_session not in session_ids:
            session_ids.append(part_session)

        if part_type == "tool":
            tool_name = part.get("tool")
            state = part.get("state")
            state = state if isinstance(state, dict) else {}
            call_id = part.get("callID")
            part_id = part.get("id")
            identity = call_id if isinstance(call_id, str) and call_id else (
                part_id if isinstance(part_id, str) and part_id else f"line:{line_number}"
            )
            call: dict[str, Any] = {
                "stdout_line": line_number,
                "name": tool_name,
                "input": state.get("input"),
            }
            if isinstance(call_id, str):
                call["call_id"] = call_id
            if isinstance(part_id, str):
                call["part_id"] = part_id
            status = state.get("status")
            if isinstance(status, str):
                call["status"] = status
            for field in ("output", "error"):
                if field in state:
                    call[field] = state[field]
            calls[identity] = call
        elif part_type == "text" and isinstance(part.get("text"), str):
            text_parts.append({
                "stdout_line": line_number,
                "text": part["text"],
                "message_id": part.get("messageID"),
                "session_id": part_session,
            })

    identified = [part for part in text_parts if isinstance(part.get("message_id"), str)]
    if identified:
        final_message_id = identified[-1]["message_id"]
        final_text_parts = [part for part in text_parts if part.get("message_id") == final_message_id]
    else:
        final_text_parts = text_parts[-1:]

    requested_paths: list[dict[str, Any]] = []
    for call in calls.values():
        for argument, value in _path_arguments(str(call.get("name") or ""), call.get("input")):
            requested_paths.append({
                "tool": call.get("name"),
                "argument": argument,
                "value": value,
                "stdout_line": call["stdout_line"],
            })

    return {
        "tool_call_count": len(calls),
        "tool_calls": list(calls.values()),
        "requested_read_or_search_paths": requested_paths,
        "text_parts": text_parts,
        "final_text_parts": final_text_parts,
        "session_ids": session_ids,
        "error_events": error_events,
        "non_json_stdout_lines": non_json,
        "path_semantics": "Requested arguments only; they do not prove a call ran or a read succeeded.",
    }

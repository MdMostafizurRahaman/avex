#!/usr/bin/env python3
"""Create a conservative common-exclusion plan for RepoPairBench snapshots."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


class PlanError(ValueError):
    """Raised when a condition plan cannot be created safely."""


def _safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or "\\" in value or any(part in {"", ".", ".."} for part in path.parts):
        raise PlanError(f"Unsafe repository-relative path: {value!r}")
    return path.as_posix()


def _rules(path: Path) -> tuple[list[tuple[str, re.Pattern[str]]], list[re.Pattern[str]], list[re.Pattern[str]], set[str], int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for item in data.get("forbidden_patterns", []):
        patterns.append((item["id"], re.compile(item["pattern"], sum(
            {"IGNORECASE": re.IGNORECASE, "MULTILINE": re.MULTILINE, "DOTALL": re.DOTALL}.get(flag, 0)
            for flag in item.get("flags", [])
        ))))
    filenames = [re.compile(item) for item in data.get("forbidden_filename_patterns", [])]
    artifacts = [re.compile(item) for item in data.get("forbidden_artifact_filename_patterns", [])]
    extensions = {item.casefold() for item in data.get("forbidden_extensions", [])}
    max_file_bytes = data.get("max_file_bytes", 20 * 1024 * 1024)
    if not isinstance(max_file_bytes, int) or max_file_bytes < 1:
        raise PlanError("max_file_bytes must be a positive integer")
    return patterns, filenames, artifacts, extensions, max_file_bytes


def _exclusion_reason(relative: str, path: Path, patterns: list[tuple[str, re.Pattern[str]]],
                      filenames: list[re.Pattern[str]], artifacts: list[re.Pattern[str]],
                      extensions: set[str], max_file_bytes: int) -> str | None:
    if path.stat().st_size > max_file_bytes:
        return f"file exceeds max_file_bytes ({path.stat().st_size} > {max_file_bytes})"
    if path.suffix.casefold() in extensions:
        return f"forbidden extension {path.suffix}"
    if any(expression.search(relative) for expression in filenames):
        return "forbidden filename pattern"
    if any(expression.search(relative) or expression.search(path.name) for expression in artifacts):
        return "forbidden patch/diff artifact filename pattern"
    if any(part.casefold() in {"patch", "diff"} for part in PurePosixPath(relative).parts):
        return "forbidden patch/diff artifact directory"
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    for identifier, expression in patterns:
        if expression.search(text):
            return f"forbidden content pattern: {identifier}"
    return None


def create_plan(report_path: Path, rules_path: Path, snapshots_root: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError(f"Plan already exists: {output}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    patterns, filenames, artifacts, extensions, max_file_bytes = _rules(rules_path)
    records: list[dict[str, Any]] = []
    for record in report["records"]:
        source = snapshots_root / f"{record['ordinal']}_{record['id']}" / "before"
        target = _safe_path(record["target_file"])
        if not source.is_dir():
            raise PlanError(f"Missing vulnerable snapshot: {source}")
        exclusions: dict[str, str] = {}
        for path in sorted(item for item in source.rglob("*") if item.is_file() and not item.is_symlink()):
            relative = path.relative_to(source).as_posix()
            reason = _exclusion_reason(relative, path, patterns, filenames, artifacts, extensions, max_file_bytes)
            if reason:
                exclusions[relative] = reason
        if target in exclusions:
            raise PlanError(f"Target file matches a leakage rule and needs researcher review: {record['id']}/{target}")
        records.append({
            "ordinal": record["ordinal"],
            "id": record["id"],
            "source": str(source.relative_to(snapshots_root).as_posix()),
            "target_file": target,
            "exclude_paths": sorted(exclusions),
            "exclusion_reasons": exclusions,
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema_version": 1,
        "purpose": "mechanical common exclusions; researcher validation required",
        "records": records,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--rules", required=True, type=Path)
    parser.add_argument("--snapshots-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = create_plan(args.report, args.rules, args.snapshots_root, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

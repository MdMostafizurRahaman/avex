#!/usr/bin/env python3
"""Scan an experimental workspace for leakage markers and filesystem escapes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    """Raised when the workspace or rules cannot be audited safely."""


@dataclass(frozen=True)
class CompiledPattern:
    identifier: str
    expression: re.Pattern[str]


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{label} must be a JSON object: {path}")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AuditError(f"{label} must be an array of strings")
    return value


def _compile_rules(rules: dict[str, Any]) -> tuple[list[CompiledPattern], list[dict[str, Any]]]:
    raw = rules.get("forbidden_patterns", [])
    if not isinstance(raw, list):
        raise AuditError("forbidden_patterns must be an array")
    flags_by_name = {
        "IGNORECASE": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "DOTALL": re.DOTALL,
    }
    patterns: list[CompiledPattern] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
            raise AuditError(f"forbidden_patterns[{index}] must contain a regex string")
        identifier = item.get("id", f"pattern_{index}")
        if not isinstance(identifier, str) or not identifier:
            raise AuditError(f"forbidden_patterns[{index}].id must be a non-empty string")
        flags = item.get("flags", [])
        if not isinstance(flags, list) or any(flag not in flags_by_name for flag in flags):
            raise AuditError(f"forbidden_patterns[{index}].flags contains an unsupported value")
        value = 0
        for flag in flags:
            value |= flags_by_name[flag]
        try:
            compiled = re.compile(item["pattern"], value)
        except re.error as exc:
            raise AuditError(f"Invalid regex for {identifier}: {exc}") from exc
        patterns.append(CompiledPattern(identifier, compiled))

    allowlist = rules.get("allowlist", [])
    if not isinstance(allowlist, list):
        raise AuditError("allowlist must be an array")
    for index, item in enumerate(allowlist):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise AuditError(f"allowlist[{index}] must contain a path string")
        if not isinstance(item.get("pattern"), str) or not item["pattern"]:
            raise AuditError(f"allowlist[{index}].pattern must be a regex string")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise AuditError(f"allowlist[{index}].reason must explain the exception")
        try:
            re.compile(item["pattern"])
        except re.error as exc:
            raise AuditError(f"Invalid allowlist regex at index {index}: {exc}") from exc
    return patterns, allowlist


def _is_allowlisted(path: str, match: str, pattern_id: str, entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    for entry in entries:
        if not fnmatch.fnmatchcase(path, entry["path"]):
            continue
        if entry.get("pattern_id") not in (None, pattern_id):
            continue
        if re.search(entry["pattern"], match):
            return entry
    return None


def _path_is_forbidden(path: str, forbidden: list[str]) -> str | None:
    parts = Path(path).parts
    for forbidden_path in forbidden:
        normalized = forbidden_path.strip("/")
        if not normalized:
            continue
        if path == normalized or path.startswith(normalized + "/") or normalized in parts:
            return forbidden_path
    return None


def scan_workspace(workspace: Path, rules_path: Path) -> dict[str, Any]:
    raw_workspace = workspace.expanduser()
    if raw_workspace.is_symlink():
        raise AuditError(f"Workspace root is a symlink: {raw_workspace}")
    try:
        root = raw_workspace.resolve(strict=True)
    except OSError as exc:
        raise AuditError(f"Cannot resolve workspace {raw_workspace}: {exc}") from exc
    if not root.is_dir():
        raise AuditError(f"Workspace is not a directory: {root}")
    rules_file = rules_path.expanduser().resolve(strict=True)
    rules = _load_json(rules_file, "rules file")
    if rules.get("schema_version") != 1:
        raise AuditError("Unsupported or missing rules schema_version (expected 1)")
    patterns, allowlist = _compile_rules(rules)
    forbidden_paths = _string_list(rules.get("forbidden_paths", []), "forbidden_paths")
    filename_patterns = [re.compile(p) for p in _string_list(rules.get("forbidden_filename_patterns", []), "forbidden_filename_patterns")]
    artifact_patterns = [re.compile(p) for p in _string_list(rules.get("forbidden_artifact_filename_patterns", []), "forbidden_artifact_filename_patterns")]
    forbidden_extensions = {ext.casefold() for ext in _string_list(rules.get("forbidden_extensions", []), "forbidden_extensions")}
    max_file_bytes = rules.get("max_file_bytes", 20 * 1024 * 1024)
    if not isinstance(max_file_bytes, int) or max_file_bytes < 1:
        raise AuditError("max_file_bytes must be a positive integer")
    deny_symlinks = rules.get("deny_symlinks", True)
    deny_git = rules.get("deny_git_metadata", True)
    deny_patch = rules.get("deny_patch_diff_artifacts", True)
    if not all(isinstance(value, bool) for value in (deny_symlinks, deny_git, deny_patch)):
        raise AuditError("deny_symlinks, deny_git_metadata, and deny_patch_diff_artifacts must be booleans")

    findings: list[dict[str, Any]] = []
    allowed: list[dict[str, Any]] = []
    audit_errors: list[dict[str, str]] = []
    files_scanned = 0

    def finding(code: str, rel: str, detail: str, **extra: Any) -> None:
        findings.append({"code": code, "path": rel, "detail": detail, **extra})

    def visit(directory: Path) -> None:
        nonlocal files_scanned
        try:
            entries = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            audit_errors.append({"path": str(directory), "error": str(exc)})
            return
        for path in entries:
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                try:
                    resolved = path.resolve(strict=False)
                    outside = resolved != root and root not in resolved.parents
                    target = str(resolved)
                except (OSError, RuntimeError) as exc:
                    outside = True
                    target = f"unresolvable: {exc}"
                if deny_symlinks:
                    finding("symlink", rel, "Symlinks are forbidden in condition workspaces", target=target)
                if outside:
                    finding("symlink_escape", rel, "Symlink resolves outside the supplied workspace", target=target)
                continue

            forbidden_path = _path_is_forbidden(rel, forbidden_paths)
            if forbidden_path is not None:
                finding("forbidden_path", rel, f"Path matches configured forbidden path {forbidden_path!r}")
            if deny_git and (path.name.casefold() == ".git" or path.name.casefold() == ".hg"):
                finding("git_metadata", rel, "Version-control metadata directory is forbidden")
            for expression in filename_patterns:
                if expression.search(rel):
                    finding("forbidden_filename", rel, f"Path matches forbidden filename regex {expression.pattern!r}")
            if deny_patch and path.suffix.casefold() in forbidden_extensions:
                finding("patch_diff_artifact", rel, f"Forbidden artifact extension {path.suffix!r}")
            if deny_patch:
                for expression in artifact_patterns:
                    if expression.search(path.name):
                        finding("patch_diff_artifact", rel, f"Filename matches patch/diff regex {expression.pattern!r}")

            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                audit_errors.append({"path": rel, "error": str(exc)})
                continue
            if stat.S_ISDIR(mode):
                visit(path)
                continue
            if not stat.S_ISREG(mode):
                finding("special_file", rel, "Non-regular filesystem object found")
                continue
            files_scanned += 1
            size = path.stat().st_size
            if size > max_file_bytes:
                audit_errors.append({"path": rel, "error": f"File exceeds max_file_bytes ({size} > {max_file_bytes})"})
                continue
            try:
                contents = path.read_bytes()
            except OSError as exc:
                audit_errors.append({"path": rel, "error": str(exc)})
                continue
            if b"\x00" in contents:
                continue
            text = contents.decode("utf-8", errors="replace")
            for item in patterns:
                for match in item.expression.finditer(text):
                    excerpt = match.group(0)
                    allowed_by = _is_allowlisted(rel, excerpt, item.identifier, allowlist)
                    if allowed_by:
                        allowed.append({
                            "code": item.identifier,
                            "path": rel,
                            "match": excerpt,
                            "reason": allowed_by["reason"],
                        })
                    else:
                        line = text.count("\n", 0, match.start()) + 1
                        finding(item.identifier, rel, "Forbidden regex matched file content", line=line, match=excerpt)

    visit(root)
    findings.sort(key=lambda item: (item["path"], item["code"], item.get("line", 0), item["detail"]))
    allowed.sort(key=lambda item: (item["path"], item["code"], item["match"]))
    audit_errors.sort(key=lambda item: (item["path"], item["error"]))
    return {
        "workspace": str(root),
        "rules_file": str(rules_file),
        "files_scanned": files_scanned,
        "findings": findings,
        "allowlisted_occurrences": allowed,
        "audit_errors": audit_errors,
        "clean": not findings and not audit_errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan an experimental workspace for leakage and symlink escapes.")
    parser.add_argument("workspace", type=Path, help="Workspace directory to inspect recursively")
    parser.add_argument("--rules", type=Path, default=Path("config/leakage_rules.json"), help="JSON rules configuration")
    parser.add_argument("--json", action="store_true", help="Write machine-readable JSON to stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = scan_workspace(args.workspace, args.rules)
    except (AuditError, OSError, RuntimeError) as exc:
        result = {
            "workspace": str(args.workspace),
            "rules_file": str(args.rules),
            "files_scanned": 0,
            "findings": [],
            "allowlisted_occurrences": [],
            "audit_errors": [{"path": str(args.workspace), "error": str(exc)}],
            "clean": False,
        }
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif result["clean"]:
        print(f"CLEAN: {result['workspace']} ({result['files_scanned']} files scanned)")
        for item in result["allowlisted_occurrences"]:
            print(f"ALLOWLISTED: {item['path']}: {item['match']!r} — {item['reason']}")
    else:
        for item in result["findings"]:
            line = f":{item['line']}" if "line" in item else ""
            print(f"FINDING {item['code']}: {item['path']}{line}: {item['detail']}")
        for item in result["audit_errors"]:
            print(f"AUDIT ERROR: {item['path']}: {item['error']}", file=sys.stderr)
    return 0 if result["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

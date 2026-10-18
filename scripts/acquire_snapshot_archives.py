#!/usr/bin/env python3
"""Acquire pinned RepoPairBench before/after archives for a record range.

This is a researcher-only preparation step. It writes compressed source archives
and provenance metadata; it never creates an experimental condition workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class AcquisitionError(ValueError):
    """Raised when dataset input or an upstream response is unsafe."""


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _github_repo(url: Any) -> tuple[str, str]:
    if not isinstance(url, str):
        raise AcquisitionError("repo_url must be a string")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.casefold() != "github.com":
        raise AcquisitionError(f"repo_url must be an HTTPS github.com URL: {url!r}")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or any(part in {".", ".."} for part in parts):
        raise AcquisitionError(f"repo_url must identify exactly one GitHub repository: {url!r}")
    return parts[0], parts[1].removesuffix(".git")


def _record_fields(line_number: int, record: Any) -> tuple[str, str, str, str, str, str]:
    if not isinstance(record, dict):
        raise AcquisitionError(f"JSONL line {line_number} must be an object")
    identifier = record.get("id")
    fixing_commit = record.get("commit_hash")
    project = record.get("project_name")
    vuln_data = record.get("vuln_data")
    if not isinstance(identifier, str) or not _IDENTIFIER.fullmatch(identifier):
        raise AcquisitionError(f"JSONL line {line_number} has an unsafe id")
    if not isinstance(fixing_commit, str) or not _SHA.fullmatch(fixing_commit):
        raise AcquisitionError(f"JSONL line {line_number} has an invalid commit_hash")
    if not isinstance(project, str) or not project:
        raise AcquisitionError(f"JSONL line {line_number} is missing project_name")
    if not isinstance(vuln_data, dict) or not isinstance(vuln_data.get("file_path"), str):
        raise AcquisitionError(f"JSONL line {line_number} is missing vuln_data.file_path")
    target = vuln_data["file_path"]
    if not target or target.startswith(("/", "\\")) or "\\" in target or ".." in Path(target).parts:
        raise AcquisitionError(f"JSONL line {line_number} has an unsafe target path")
    owner, repo = _github_repo(record.get("repo_url"))
    return identifier, project, fixing_commit.lower(), target, owner, repo


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "avex-repopairbench-preparer/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise AcquisitionError(f"Could not fetch {url}: {exc}") from exc
    if not isinstance(value, dict):
        raise AcquisitionError(f"Expected a JSON object from {url}")
    return value


def _parent_commit(owner: str, repo: str, commit: str) -> str:
    data = _get_json(f"https://api.github.com/repos/{owner}/{repo}/commits/{commit}")
    parents = data.get("parents")
    if not isinstance(parents, list) or not parents:
        raise AcquisitionError(f"Fixing commit has no parent: {owner}/{repo}@{commit}")
    parent = parents[0]
    if not isinstance(parent, dict) or not isinstance(parent.get("sha"), str) or not _SHA.fullmatch(parent["sha"]):
        raise AcquisitionError(f"GitHub returned an invalid first parent for {owner}/{repo}@{commit}")
    return parent["sha"].lower()


def _download(url: str, destination: Path) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "avex-repopairbench-preparer/1.0"})
    with tempfile.NamedTemporaryFile(prefix=".download-", dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        try:
            with urllib.request.urlopen(request, timeout=300) as response, temporary_path.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
        except (OSError, urllib.error.URLError) as exc:
            raise AcquisitionError(f"Could not download {url}: {exc}") from exc
        temporary_path.replace(destination)
        return sha256_file(destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def acquire_batch(dataset: Path, archive_dir: Path, start: int, end: int) -> dict[str, Any]:
    if start < 1 or end < start:
        raise AcquisitionError("start/end must be a valid one-based range")
    if archive_dir.exists():
        raise FileExistsError(f"Archive directory already exists: {archive_dir}")
    lines = dataset.read_text(encoding="utf-8").splitlines()
    if end > len(lines):
        raise AcquisitionError(f"Dataset contains {len(lines)} lines, cannot select through {end}")
    archive_dir.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    for line_number in range(start, end + 1):
        record = json.loads(lines[line_number - 1])
        identifier, project, fixing, target, owner, repo = _record_fields(line_number, record)
        parent = _parent_commit(owner, repo, fixing)
        entries: dict[str, Any] = {}
        for side, commit in (("before", parent), ("after", fixing)):
            path = archive_dir / f"{identifier}_{side}.tar.gz"
            url = f"https://github.com/{owner}/{repo}/archive/{commit}.tar.gz"
            entries[side] = {"commit": commit, "url": url, "sha256": _download(url, path)}
        records.append({
            "jsonl_line": line_number,
            "id": identifier,
            "project_name": project,
            "repo": f"{owner}/{repo}",
            "target_file": target,
            "fixing_commit": fixing,
            "vulnerable_parent_commit": parent,
            "archives": entries,
        })
    report = {"dataset": str(dataset), "start": start, "end": end, "records": records}
    (archive_dir / "provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--archive-dir", required=True, type=Path)
    parser.add_argument("--start", type=int, default=76)
    parser.add_argument("--end", type=int, default=100)
    args = parser.parse_args()
    try:
        report = acquire_batch(args.dataset, args.archive_dir, args.start, args.end)
    except (OSError, ValueError, AcquisitionError) as exc:
        parser.error(str(exc))
    print(json.dumps({"records": len(report["records"]), "archive_dir": str(args.archive_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

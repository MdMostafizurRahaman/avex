#!/usr/bin/env python3
"""Build isolated, deterministic RepoPairBench evidence condition workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class ManifestError(ValueError):
    """Raised when the researcher manifest is incomplete or inconsistent."""


class SafetyError(ValueError):
    """Raised when a source or destination violates filesystem safety rules."""


@dataclass(frozen=True)
class BuildResult:
    condition: str
    included: tuple[str, ...]
    excluded: tuple[str, ...]
    missing: tuple[str, ...]
    total_bytes: int
    workspace_sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_entries(root: Path) -> tuple[dict[str, Path], list[str]]:
    """Return regular files and reject symlinks and special files in the tree."""
    files: dict[str, Path] = {}
    symlinks: list[str] = []
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for dirname in sorted(dirnames):
            path = current_path / dirname
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                symlinks.append(rel)
            else:
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in sorted(filenames):
            path = current_path / filename
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                symlinks.append(rel)
                continue
            mode = path.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise SafetyError(f"Source contains a non-regular file: {rel}")
            files[rel] = path
    if symlinks:
        raise SafetyError("Source contains symlinks (rejected): " + ", ".join(sorted(symlinks)))
    return files, symlinks


def _safe_relative(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{label} must be a non-empty repository-relative path")
    if "RESEARCHER_TODO" in value:
        raise ManifestError(f"{label} still contains RESEARCHER_TODO")
    if "\\" in value or "\x00" in value:
        raise ManifestError(f"{label} contains an invalid path character: {value!r}")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        raise ManifestError(f"{label} must not be absolute or traverse directories: {value!r}")
    if candidate.parts and candidate.parts[0].lower() == "private":
        raise ManifestError(f"{label} must not reference private/: {value!r}")
    normalized = candidate.as_posix()
    if normalized != value:
        raise ManifestError(f"{label} is not normalized: {value!r}")
    return normalized


def _list_of_paths(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ManifestError(f"{label} must be an array")
    paths = [_safe_relative(item, label=f"{label}[{index}]") for index, item in enumerate(value)]
    if len(paths) != len(set(paths)):
        raise ManifestError(f"{label} contains duplicate paths")
    return paths


def _read_json(path: Path, *, reject_todos: bool = False) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Cannot read JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"Expected a JSON object in {path}")
    def find_todo(value: Any, location: str = "$ ") -> str | None:
        if isinstance(value, str) and "RESEARCHER_TODO" in value:
            return location
        if isinstance(value, dict):
            for key, child in value.items():
                found = find_todo(child, f"{location}.{key}")
                if found:
                    return found
        if isinstance(value, list):
            for index, child in enumerate(value):
                found = find_todo(child, f"{location}[{index}]")
                if found:
                    return found
        return None
    if reject_todos:
        todo_location = find_todo(data)
        if todo_location:
            raise ManifestError(f"Manifest still contains RESEARCHER_TODO at {todo_location}")
    return data


def _validate_excerpt_list(
    condition_data: dict[str, Any],
    source_files: dict[str, Path],
    included: set[str],
    condition: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_excerpts = condition_data.get("initial_evidence_excerpts", [])
    if not isinstance(raw_excerpts, list):
        raise ManifestError(f"{condition}.initial_evidence_excerpts must be an array")
    excerpts: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_excerpts):
        if not isinstance(raw, dict):
            raise ManifestError(f"{condition}.initial_evidence_excerpts[{index}] must be an object")
        path = _safe_relative(raw.get("path"), label=f"{condition}.excerpt[{index}].path")
        start, end = raw.get("start_line"), raw.get("end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            raise ManifestError(f"{condition} excerpt {path} has an invalid one-based inclusive range")
        if path not in source_files:
            raise ManifestError(f"{condition} excerpt source is missing: {path}")
        excerpt = {"path": path, "start_line": start, "end_line": end}
        excerpts.append(excerpt)

    raw_allowed = condition_data.get("allowed_absent_source_excerpts", [])
    if not isinstance(raw_allowed, list):
        raise ManifestError(f"{condition}.allowed_absent_source_excerpts must be an array")
    allowed: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_allowed):
        if not isinstance(raw, dict):
            raise ManifestError(f"{condition}.allowed_absent_source_excerpts[{index}] must be an object")
        path = _safe_relative(raw.get("path"), label=f"{condition}.allowed_absent[{index}].path")
        start, end = raw.get("start_line"), raw.get("end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            raise ManifestError(f"{condition} allowed-absent excerpt {path} has an invalid range")
        allowed.append({"path": path, "start_line": start, "end_line": end})
    if len({(e["path"], e["start_line"], e["end_line"]) for e in allowed}) != len(allowed):
        raise ManifestError(f"{condition}.allowed_absent_source_excerpts contains duplicates")

    allowed_keys = {(e["path"], e["start_line"], e["end_line"]) for e in allowed}
    for excerpt in excerpts:
        key = (excerpt["path"], excerpt["start_line"], excerpt["end_line"])
        if excerpt["path"] not in included and key not in allowed_keys:
            raise ManifestError(f"{condition} excerpt from excluded file is not explicitly allowed: {excerpt}")
    for item in allowed:
        key = (item["path"], item["start_line"], item["end_line"])
        if key not in {(e["path"], e["start_line"], e["end_line"]) for e in excerpts}:
            raise ManifestError(f"{condition} allowed absent excerpt is not used as initial evidence: {item}")
    return excerpts, allowed


def _extract_excerpt(source_path: Path, start: int, end: int, *, label: str) -> tuple[str, str]:
    raw = source_path.read_bytes()
    lines = raw.splitlines(keepends=True)
    if end > len(lines):
        raise ManifestError(f"{label} range ends at line {end}, source has {len(lines)} lines")
    selected = b"".join(lines[start - 1 : end])
    try:
        text = selected.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError(f"{label} is not UTF-8 text and cannot be packaged as an excerpt") from exc
    return text, hashlib.sha256(selected).hexdigest()


def _workspace_digest(entries: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in sorted(entries, key=lambda entry: entry["path"]):
        digest.update(item["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(item["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _safe_output_path(destination_root: Path, condition: str, source_root: Path) -> Path:
    destination_root = destination_root.resolve()
    output = destination_root / condition
    if output.exists() and output.is_symlink():
        raise SafetyError(f"Condition destination is a symlink: {output}")
    resolved = output.resolve(strict=False)
    if resolved == source_root or source_root in resolved.parents or resolved in source_root.parents:
        raise SafetyError(f"Source and destination overlap: {source_root} and {resolved}")
    return output


def build_conditions(
    *,
    source: Path,
    destination: Path,
    manifest_path: Path,
    manifest_output_dir: Path,
    force: bool = False,
) -> list[BuildResult]:
    source_arg = source.expanduser()
    destination_arg = destination.expanduser()
    manifest_output_arg = manifest_output_dir.expanduser()
    if source_arg.is_symlink():
        raise SafetyError(f"Source root must not be a symlink: {source_arg}")
    if destination_arg.is_symlink():
        raise SafetyError(f"Destination root must not be a symlink: {destination_arg}")
    if manifest_output_arg.is_symlink():
        raise SafetyError(f"Manifest output root must not be a symlink: {manifest_output_arg}")
    source = source_arg.resolve(strict=True)
    destination = destination_arg.resolve(strict=False)
    manifest_path = manifest_path.expanduser().resolve(strict=True)
    manifest_output_dir = manifest_output_arg.resolve(strict=False)
    if not source.is_dir():
        raise SafetyError(f"Source must be a directory: {source}")
    if source == destination or source in destination.parents or destination in source.parents:
        raise SafetyError(f"Source and destination must be disjoint: {source} and {destination}")
    if source == manifest_output_dir or source in manifest_output_dir.parents or manifest_output_dir in source.parents:
        raise SafetyError(f"Source and manifest output must be disjoint: {source} and {manifest_output_dir}")
    if destination == manifest_output_dir or destination in manifest_output_dir.parents or manifest_output_dir in destination.parents:
        raise SafetyError(f"Condition workspaces and researcher manifests must be disjoint: {destination} and {manifest_output_dir}")
    if not manifest_path.is_file():
        raise ManifestError(f"Manifest must be a file: {manifest_path}")

    data = _read_json(manifest_path, reject_todos=True)
    repo_root = manifest_path.parent.parent
    manifest_source = data.get("source_snapshot")
    if not isinstance(manifest_source, str) or not manifest_source:
        raise ManifestError("source_snapshot must be an explicit path")
    manifest_source_path = Path(manifest_source)
    if not manifest_source_path.is_absolute():
        manifest_source_path = repo_root / manifest_source_path
    if manifest_source_path.resolve(strict=True) != source:
        raise ManifestError("--source does not match manifest source_snapshot")
    scenario_path = manifest_path.parent / "scenario.json"
    if scenario_path.exists():
        scenario = _read_json(scenario_path)
        if data.get("scenario_id") != scenario.get("scenario_id"):
            raise ManifestError("Manifest scenario_id does not match config/scenario.json")
        target = _safe_relative(data.get("target_file"), label="target_file")
        if target != scenario.get("target_file"):
            raise ManifestError("Manifest target_file does not match config/scenario.json")
        expected_source = Path(scenario["vulnerable_snapshot"]["path"]).resolve()
        if source != expected_source:
            raise ManifestError(f"--source differs from scenario vulnerable snapshot: {expected_source}")

    source_files, _ = _tree_entries(source)
    if not source_files:
        raise ManifestError(f"Source snapshot has no regular files: {source}")
    target_file = _safe_relative(data.get("target_file"), label="target_file")
    if target_file not in source_files:
        raise ManifestError(f"Target file is missing from source snapshot: {target_file}")
    conditions = data.get("conditions")
    if not isinstance(conditions, dict) or set(conditions) != {"E1", "E2", "E3"}:
        raise ManifestError("conditions must contain exactly E1, E2, and E3")

    # Validate every condition fully before creating or replacing any output.
    validated: dict[str, dict[str, Any]] = {}
    missing_by_condition: dict[str, list[str]] = {}
    for condition in ("E1", "E2", "E3"):
        config = conditions[condition]
        if not isinstance(config, dict):
            raise ManifestError(f"{condition} must be an object")
        includes = _list_of_paths(config.get("include"), label=f"{condition}.include")
        excludes = _list_of_paths(config.get("exclude"), label=f"{condition}.exclude")
        initial_files = _list_of_paths(config.get("initial_evidence_files"), label=f"{condition}.initial_evidence_files")
        missing = sorted((set(includes) | set(excludes) | set(initial_files)) - set(source_files))
        missing_by_condition[condition] = missing
        if missing:
            raise ManifestError(f"{condition} requested paths missing from source: {', '.join(missing)}")
        if not includes:
            raise ManifestError(f"{condition}.include must not be empty")
        if set(includes) & set(excludes):
            raise ManifestError(f"{condition} include and exclude overlap")
        if set(includes) | set(excludes) != set(source_files):
            absent = sorted(set(source_files) - set(includes) - set(excludes))
            extra = sorted((set(includes) | set(excludes)) - set(source_files))
            raise ManifestError(f"{condition} include/exclude do not partition source files; unlisted={absent[:8]}, extra={extra[:8]}")
        if target_file not in includes:
            raise ManifestError(f"{condition} must include target file {target_file}")
        if any(PurePosixPath(path).parts[0].lower() == "private" for path in includes):
            raise ManifestError(f"{condition} must never include private/ paths")
        if not set(initial_files) <= set(includes):
            raise ManifestError(f"{condition}.initial_evidence_files must all be included files")
        excerpts, allowed = _validate_excerpt_list(config, source_files, set(includes), condition)
        validated[condition] = {
            "include": includes,
            "exclude": excludes,
            "initial_evidence_files": initial_files,
            "initial_evidence_excerpts": excerpts,
            "allowed_absent_source_excerpts": allowed,
        }

    planned = {condition: _safe_output_path(destination, condition, source) for condition in conditions}
    for condition, output in planned.items():
        if output.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {output}; pass --force to replace condition directories")
        if output.exists() and not output.is_dir():
            raise SafetyError(f"Condition output exists and is not a directory: {output}")
    if manifest_output_dir.exists() and manifest_output_dir.is_symlink():
        raise SafetyError(f"Manifest output directory is a symlink: {manifest_output_dir}")
    if any((manifest_output_dir / f"{condition}_manifest.json").exists() for condition in conditions) and not force:
        raise FileExistsError(f"Researcher manifest already exists under {manifest_output_dir}; pass --force to replace outputs")

    output_parent = destination.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    manifest_output_dir.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=".conditions-stage-", dir=output_parent))
    staged_manifests = Path(tempfile.mkdtemp(prefix=".manifests-stage-", dir=manifest_output_dir.parent))
    results: list[BuildResult] = []
    try:
        for condition in ("E1", "E2", "E3"):
            config = validated[condition]
            stage = stage_root / condition
            stage.mkdir()
            file_hashes: list[dict[str, Any]] = []
            total_bytes = 0
            for relative in sorted(config["include"]):
                source_file = source_files[relative]
                output_file = stage.joinpath(*PurePosixPath(relative).parts)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, output_file, follow_symlinks=False)
                shutil.copystat(source_file, output_file, follow_symlinks=False)
                digest = sha256_file(source_file)
                size = source_file.stat().st_size
                total_bytes += size
                file_hashes.append({"path": relative, "size_bytes": size, "sha256": digest})

            packet: list[dict[str, Any]] = []
            for relative in config["initial_evidence_files"]:
                content = source_files[relative].read_bytes()
                packet.append({
                    "kind": "file",
                    "path": relative,
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "content": content.decode("utf-8", errors="strict"),
                })
            for excerpt in config["initial_evidence_excerpts"]:
                content, digest = _extract_excerpt(
                    source_files[excerpt["path"]], excerpt["start_line"], excerpt["end_line"],
                    label=f"{condition} excerpt {excerpt['path']}:{excerpt['start_line']}-{excerpt['end_line']}",
                )
                packet.append({
                    "kind": "excerpt",
                    **excerpt,
                    "size_bytes": len(content.encode("utf-8")),
                    "sha256": digest,
                    "content": content,
                })

            workspace_hash = _workspace_digest(file_hashes)
            try:
                source_record = source.relative_to(repo_root).as_posix()
            except ValueError:
                source_record = str(source)
            try:
                destination_record = (destination / condition).relative_to(repo_root).as_posix()
            except ValueError:
                destination_record = str(destination / condition)
            report = {
                "schema_version": 1,
                "condition": condition,
                "scenario_id": data["scenario_id"],
                "source_snapshot": source_record,
                "source_snapshot_absolute": str(source),
                "destination": destination_record,
                "destination_absolute": str(destination / condition),
                "target_file": target_file,
                "included_paths": sorted(config["include"]),
                "excluded_paths": sorted(config["exclude"]),
                "missing_requested_paths": missing_by_condition[condition],
                "files": file_hashes,
                "file_count": len(file_hashes),
                "total_bytes": total_bytes,
                "workspace_sha256": workspace_hash,
                "initial_evidence_order": [
                    "initial_evidence_files in manifest order, then initial_evidence_excerpts in manifest order"
                ],
                "initial_evidence_packet": packet,
                "warnings": [
                    "Initial packet size and required token budget must be checked with the selected harness; byte counts do not establish token fit.",
                    "Condition construction does not validate scientific sufficiency, retrievability, or unavailability.",
                    "Run the separate isolation and leakage audit before any experimental agent is started.",
                ],
            }
            (staged_manifests / f"{condition}_manifest.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            results.append(BuildResult(
                condition=condition,
                included=tuple(sorted(config["include"])),
                excluded=tuple(sorted(config["exclude"])),
                missing=tuple(missing_by_condition[condition]),
                total_bytes=total_bytes,
                workspace_sha256=workspace_hash,
            ))

        # Replace only the three named condition directories and manifests.
        for condition in ("E1", "E2", "E3"):
            output = planned[condition]
            if output.exists():
                if output.is_symlink() or not output.is_dir():
                    raise SafetyError(f"Refusing to replace unsafe condition output: {output}")
                shutil.rmtree(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(stage_root / condition), str(output))
            final_manifest = manifest_output_dir / f"{condition}_manifest.json"
            if final_manifest.exists():
                final_manifest.unlink()
            shutil.move(str(staged_manifests / final_manifest.name), str(final_manifest))
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
        shutil.rmtree(staged_manifests, ignore_errors=True)
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build researcher-defined E1/E2/E3 source workspaces with deterministic SHA-256 manifests."
    )
    parser.add_argument("--source", required=True, type=Path, help="Explicit source snapshot directory")
    parser.add_argument("--destination", required=True, type=Path, help="Explicit parent for E1/, E2/, and E3/ directories")
    parser.add_argument("--manifest", type=Path, default=Path("config/evidence_manifest.json"), help="Researcher-approved evidence manifest JSON")
    parser.add_argument("--manifest-output-dir", type=Path, help="Researcher-facing output directory (default: results/manifests beside config/)")
    parser.add_argument("--force", action="store_true", help="Replace only E1/E2/E3 outputs and their researcher manifests")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = args.manifest
    output_dir = args.manifest_output_dir or manifest_path.parent.parent / "results" / "manifests"
    try:
        results = build_conditions(
            source=args.source,
            destination=args.destination,
            manifest_path=manifest_path,
            manifest_output_dir=output_dir,
            force=args.force,
        )
    except (ManifestError, SafetyError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for result in results:
        print(
            f"{result.condition}: files={len(result.included)} bytes={result.total_bytes} "
            f"workspace_sha256={result.workspace_sha256} destination={args.destination / result.condition}"
        )
    print(f"Researcher manifests: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

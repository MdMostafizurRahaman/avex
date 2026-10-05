#!/usr/bin/env python3
"""Launch one fresh Qwen Code run after condition and isolation preflight checks."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any
from qwen_isolation import sandbox_profile, verify_sandbox, extract_events


MODEL = "qwen3.5:9b-q4_K_M"
ENDPOINT = "http://127.0.0.1:11434/v1"
CONTEXT_LENGTH = "16384"
HARNESS_VERSION = "0.24.6"
FROZEN_PROMPT_SHA256 = "107dca240cf64f0ac4c4dc56f61ec976f5174db5da6dcb60ca20a3a2dff509a1"


class PreflightError(RuntimeError):
    """Raised when a run would violate a configured precondition."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightError(f"Expected a JSON object: {path}")
    return value


def command_output(command: list[str], *, timeout: float = 15.0) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PreflightError(f"Cannot execute {command[0]}: {exc}") from exc


def check_qwen_configuration() -> dict[str, Any]:
    settings_path = Path.home() / ".qwen" / "settings.json"
    if not settings_path.is_file():
        raise PreflightError(f"Qwen Code settings not found: {settings_path}")
    settings = read_json(settings_path)
    configured_model = settings.get("model", {})
    if not isinstance(configured_model, dict) or configured_model.get("name") != MODEL:
        raise PreflightError(f"Qwen Code settings do not select required model {MODEL}")
    providers = settings.get("modelProviders", {}).get("openai", [])
    if not isinstance(providers, list):
        raise PreflightError("Qwen Code OpenAI-compatible provider configuration is malformed")
    matches = [entry for entry in providers if isinstance(entry, dict) and entry.get("id") == MODEL]
    if len(matches) != 1:
        raise PreflightError(f"Expected exactly one Qwen provider entry for {MODEL}; found {len(matches)}")
    provider = matches[0]
    if provider.get("baseUrl") != ENDPOINT:
        raise PreflightError(f"Configured endpoint differs from required endpoint {ENDPOINT}")
    return {
        "settings_path": str(settings_path),
        "model": MODEL,
        "endpoint": ENDPOINT,
        "wire_api": provider.get("wireApi"),
        "provider_name": provider.get("name"),
        "api_key_env_name": provider.get("envKey"),
    }


def check_workspace_boundary(workspace: Path) -> None:
    """Reject condition roots that can traverse to researcher-only private/."""
    workspace = workspace.absolute()
    if workspace.is_symlink():
        raise PreflightError(f"Condition workspace is a symlink: {workspace}")
    for path in (workspace, *workspace.parents):
        if path.is_symlink():
            raise PreflightError(f"Workspace ancestry contains symlink {path}")
    for current in workspace.rglob("*"):
        if current.is_symlink():
            try:
                resolved = current.resolve(strict=False)
            except (OSError, RuntimeError) as exc:
                raise PreflightError(f"Unresolvable symlink in workspace: {current}: {exc}") from exc
            raise PreflightError(f"Condition workspace contains symlink {current} -> {resolved}")

    for ancestor in (workspace, *workspace.parents):
        private_path = ancestor / "private"
        if private_path.exists() or private_path.is_symlink():
            raise PreflightError(
                f"Unsafe workspace ancestry: {workspace} can navigate to researcher-only {private_path}; "
                "run this condition only from a workspace outside that ancestor or under a separately verified OS sandbox"
            )


def check_scenario(repo_root: Path, scenario_id: str) -> dict[str, Any]:
    scenario = read_json(repo_root / "config" / "scenario.json")
    manifest = read_json(repo_root / "config" / "evidence_manifest.json")
    if scenario.get("scenario_id") != scenario_id or manifest.get("scenario_id") != scenario_id:
        raise PreflightError("Requested scenario_id does not match both scenario and evidence manifests")
    if manifest.get("target_file") != scenario.get("target_file"):
        raise PreflightError("Scenario target and evidence-manifest target disagree")
    return scenario


def construct_prompt(repo_root: Path, condition: str, scenario: dict[str, Any]) -> str:
    prompt_path = repo_root / "prompts" / "common_prompt.txt"
    common_bytes = prompt_path.read_bytes()
    actual_hash = hashlib.sha256(common_bytes).hexdigest()
    if actual_hash != FROZEN_PROMPT_SHA256:
        raise PreflightError(f"Frozen prompt checksum mismatch: {actual_hash}")
    common = common_bytes.decode("utf-8")
    target_file = scenario.get("target_file")
    target_function = scenario.get("target_function")
    if not isinstance(target_file, str) or not isinstance(target_function, str):
        raise PreflightError("Scenario target_file/target_function must be strings")
    if common.count("{{TARGET_FILE}}") != 1 or common.count("{{TARGET_FUNCTION}}") != 1:
        raise PreflightError("Frozen common prompt must contain each target placeholder exactly once")
    task = common.replace("{{TARGET_FILE}}", target_file).replace("{{TARGET_FUNCTION}}", target_function)

    packet_path = repo_root / "results" / "manifests" / f"{condition}_manifest.json"
    packet_record = read_json(packet_path)
    if packet_record.get("condition") != condition or packet_record.get("scenario_id") != scenario["scenario_id"]:
        raise PreflightError(f"Researcher manifest does not match condition/scenario: {packet_path}")
    packet = packet_record.get("initial_evidence_packet")
    if not isinstance(packet, list) or not packet:
        raise PreflightError(f"Initial evidence packet is missing or empty: {packet_path}")
    chunks = [task.rstrip(), "", "Initially provided repository evidence:"]
    for index, entry in enumerate(packet, start=1):
        if not isinstance(entry, dict) or not isinstance(entry.get("content"), str):
            raise PreflightError(f"Invalid initial-evidence packet entry {index} in {packet_path}")
        source_path = entry.get("path")
        if entry.get("kind") == "excerpt":
            source_path = f"{source_path}:{entry.get('start_line')}-{entry.get('end_line')}"
        if not isinstance(source_path, str) or source_path.startswith("private/") or "/private/" in source_path:
            raise PreflightError(f"Unsafe initial-evidence source label: {source_path!r}")
        chunks.extend(("", f"--- BEGIN SOURCE: {source_path} ---", entry["content"].rstrip("\n"), f"--- END SOURCE: {source_path} ---"))
    return "\n".join(chunks) + "\n"


def query_ollama_version() -> str:
    request = urllib.request.Request("http://127.0.0.1:11434/api/version", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PreflightError(f"Ollama server version endpoint is unavailable: {exc}") from exc
    version = payload.get("version") if isinstance(payload, dict) else None
    if not isinstance(version, str) or not version:
        raise PreflightError("Ollama /api/version returned no version string")
    return version


def check_leakage(repo_root: Path, workspace: Path, run_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(repo_root / "scripts" / "leakage_check.py"),
        str(workspace),
        "--rules",
        str(repo_root / "config" / "leakage_rules.json"),
        "--json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    (run_dir / "leakage_checker.stdout.json").write_text(result.stdout, encoding="utf-8")
    (run_dir / "leakage_checker.stderr.txt").write_text(result.stderr, encoding="utf-8")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PreflightError(f"Leakage checker did not return JSON: {exc}") from exc
    if result.returncode != 0 or not report.get("clean"):
        raise PreflightError(f"Leakage checker failed with exit status {result.returncode}")
    return report


def build_qwen_command(qwen_path: str, prompt: str, run_id: str) -> list[str]:
    # Installed 0.24.6 help/source defines these flags and read-only tool names.
    command = [qwen_path, "--model", MODEL, "--session-id", run_id,
               "--output-format", "stream-json", "--safe-mode",
               "--chat-recording=false", "--telemetry=false",
               "--auth-type", "openai", "--openai-api-key", "ollama",
               "--openai-base-url", ENDPOINT]
    for tool in ["read_file", "list_directory", "glob", "grep_search"]:
        command.append(f"--allowed-tools={tool}")
    for tool in ['exec', 'edit', 'write_file', 'zoom_image', 'run_shell_command', 'todo_write', 'save_memory', 'agent', 'skill', 'exit_plan_mode', 'enter_plan_mode', 'web_fetch', 'web_search', 'image_gen', 'lsp', 'ask_user_question', 'cron_create', 'cron_list', 'cron_delete', 'loop_wakeup', 'create_sub_session', 'list_agents', 'task_stop', 'task_create', 'task_update', 'task_list', 'team_create', 'team_delete', 'team_plan_approval', 'request_shutdown', 'send_message', 'structured_output', 'monitor', 'notebook_edit', 'tool_call', 'tool_search', 'read_mcp_resource', 'advisor', 'enter_worktree', 'exit_worktree', 'workflow', 'artifact', 'record_artifact', 'record_source', 'report_findings', 'get_goal', 'update_goal', 'omni_downsample_image', 'omni_downscale_video', 'omni_downsample_audio', 'omni_extract_keyframes', 'omni_extract_audio', 'omni_clip_video', 'omni_convert_image', 'omni_transcribe_audio', 'omni_clip_image', 'omni_clip_audio', 'omni_caption_image', 'omni_caption_audio', 'omni_ocr_image', 'omni_understand_video_segments', 'omni_recall_media_memory', 'propose_goal', 'display_image']:
        command.append(f"--exclude-tools={tool}")
    command.extend(["--advisor", "off", "--prompt", prompt])
    return command


def workspace_hashes(workspace: Path) -> dict[str, str]:
    result = {}
    for path in sorted(workspace.rglob("*")):
        if path.is_symlink():
            raise PreflightError(f"Unsafe condition symlink: {path}")
        if path.is_file():
            result[path.relative_to(workspace).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify_server_context() -> dict[str, str]:
    processes = command_output(["ps", "-axo", "pid,command"]).stdout
    matches = []
    for line in processes.splitlines():
        if re.search(r"(?:^|/)ollama serve(?:$|\s)", line.strip().split(maxsplit=1)[-1]):
            matches.append(line.strip().split(maxsplit=1)[0])
    if len(matches) != 1:
        raise PreflightError("Expected exactly one local ollama serve process to verify context")
    server_env = command_output(["ps", "eww", "-p", matches[0], "-o", "command="]).stdout
    context = re.findall(r"(?:^|\s)OLLAMA_CONTEXT_LENGTH=(\S+)", server_env)
    if context != [CONTEXT_LENGTH]:
        raise PreflightError(f"Running Ollama server does not have required context: {context}")
    return {"pid": matches[0], "OLLAMA_CONTEXT_LENGTH": context[0]}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one fresh Qwen Code pilot condition after safety preflights.")
    parser.add_argument("--harness", required=True, choices=("qwen", "opencode"), help="Harness to run in a fresh confined process")
    parser.add_argument("--condition", required=True, choices=("E1", "E2", "E3"), help="Approved condition workspace")
    parser.add_argument("--scenario-id", required=True, help="Scenario ID from config/scenario.json")
    parser.add_argument("--retry-of", help="Prior infrastructure-failed run ID, preserved unchanged")
    parser.add_argument("--infrastructure-reason", help="Specific mechanical failure justifying a retry")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    if args.harness == "opencode":
        from opencode_pilot import run_opencode
        return run_opencode(args, repo_root)
    expected_workspace = repo_root / "pilot" / "conditions" / args.condition
    workspace = expected_workspace
    run_id = str(uuid.uuid4())
    started = utc_now()
    monotonic_start = time.monotonic()
    run_stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = repo_root / "logs" / "raw" / "qwen" / f"{run_stamp}_{args.condition}_{run_id}"
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_dir.mkdir()
    except FileExistsError as exc:
        print(f"ERROR: refusing to overwrite run directory {run_dir}", file=sys.stderr)
        return 2

    if bool(args.retry_of) != bool(args.infrastructure_reason):
        raise PreflightError("Retry ID and infrastructure reason must be provided together")

    metadata: dict[str, Any] = {
        "run_id": run_id,
        "retry_of": args.retry_of,
        "infrastructure_retry_reason": args.infrastructure_reason,
        "harness": "Qwen Code",
        "harness_version": None,
        "ollama_client_version": None,
        "ollama_server_version": None,
        "model": MODEL,
        "model_endpoint": ENDPOINT,
        "context_length": CONTEXT_LENGTH,
        "condition": args.condition,
        "scenario_id": args.scenario_id,
        "working_directory": str(expected_workspace),
        "actual_working_directory": str(workspace),
        "start_timestamp_utc": started,
        "end_timestamp_utc": None,
        "wall_clock_seconds": None,
        "process_exit_code": None,
        "status": "preflight_in_progress",
        "command": None,
        "prompt_file": "prompt_used.txt",
        "prompt_sha256": None,
        "stdout_file": "stdout.txt",
        "stderr_file": "stderr.txt",
        "observable_tool_calls": None,
        "tool_call_extraction": "not available from text output format",
        "searched_or_read_paths": None,
        "final_answer_location": "stdout.txt (complete raw Qwen output)",
        "preflight_error": None,
    }
    (run_dir / "stdout.txt").write_bytes(b"")
    (run_dir / "stderr.txt").write_bytes(b"")

    def finish(status: str, error: str | None = None, exit_code: int | None = None) -> int:
        metadata["status"] = status
        metadata["preflight_error"] = error
        metadata["process_exit_code"] = exit_code
        metadata["end_timestamp_utc"] = utc_now()
        metadata["wall_clock_seconds"] = round(time.monotonic() - monotonic_start, 6)
        write_json(run_dir / "run_metadata.json", metadata)
        if error:
            print(f"ERROR: {error}; attempt metadata: {run_dir / 'run_metadata.json'}", file=sys.stderr)
        return 0 if status == "completed" and exit_code == 0 else 1

    try:
        if workspace.absolute() != expected_workspace.absolute():
            raise PreflightError("Resolved working directory differs from the exact condition workspace")
        if not workspace.is_dir():
            raise PreflightError(f"Condition workspace does not exist: {workspace}")
        try:
            prompt = construct_prompt(repo_root, args.condition, check_scenario(repo_root, args.scenario_id))
        except (OSError, json.JSONDecodeError) as exc:
            raise PreflightError(f"Unable to construct prompt/evidence packet: {exc}") from exc
        prompt_bytes = prompt.encode("utf-8")
        metadata["prompt_sha256"] = hashlib.sha256(prompt_bytes).hexdigest()
        (run_dir / "prompt_used.txt").write_bytes(prompt_bytes)

        leakage_result = check_leakage(repo_root, workspace, run_dir)
        metadata["leakage_check"] = {
            "clean": leakage_result["clean"],
            "files_scanned": leakage_result["files_scanned"],
            "finding_count": len(leakage_result["findings"]),
        }
        if leakage_result["findings"] or leakage_result["audit_errors"]:
            raise PreflightError("Leakage check reported findings or audit errors; launch aborted")

        # Native confinement is verified below; do not weaken the legacy guard
        # for any unconfined process. Parent/private content remains denied.
        for ancestor in (workspace, *workspace.parents):
            if ancestor.is_symlink():
                raise PreflightError(f"Workspace ancestor is a symlink: {ancestor}")
        condition_hashes = workspace_hashes(workspace)
        approved_files = read_json(repo_root / "results/manifests" / f"{args.condition}_manifest.json")["files"]
        if condition_hashes != {f["path"]: f["sha256"] for f in approved_files}:
            raise PreflightError("Condition contents differ from approved SHA-256 manifest")
        metadata["workspace_sha256_before"] = condition_hashes
        settings = check_qwen_configuration()
        metadata["qwen_configuration"] = settings

        qwen_path = shutil.which("qwen")
        if not qwen_path:
            raise PreflightError("qwen executable is not on PATH")
        qwen_version = command_output([qwen_path, "--version"])
        if qwen_version.returncode != 0:
            raise PreflightError(f"qwen --version failed: {qwen_version.stderr.strip()}")
        version_match = re.search(r"\d+\.\d+\.\d+", qwen_version.stdout)
        if not version_match:
            raise PreflightError("Could not parse Qwen Code version")
        metadata["harness_version"] = version_match.group(0)
        if metadata["harness_version"] != HARNESS_VERSION:
            raise PreflightError(f"Qwen Code version {metadata['harness_version']} differs from locked {HARNESS_VERSION}")

        ollama_path = shutil.which("ollama")
        if not ollama_path:
            raise PreflightError("ollama executable is not on PATH")
        ollama_client = command_output([ollama_path, "--version"])
        version_match = re.search(r"\d+\.\d+\.\d+", ollama_client.stdout + "\n" + ollama_client.stderr)
        if not version_match:
            raise PreflightError("Could not parse Ollama client version")
        metadata["ollama_client_version"] = version_match.group(0)
        metadata["ollama_server_version"] = query_ollama_version()

        metadata["ollama_server_context"] = verify_server_context()
        runtime_home = Path(tempfile.mkdtemp(prefix="pilot_qwen_runtime_")).resolve()
        (runtime_home / ".qwen").mkdir()
        (runtime_home / "tmp").mkdir()
        user_settings = read_json(Path.home() / ".qwen/settings.json")
        provider = next(p for p in user_settings["modelProviders"]["openai"] if p["id"] == MODEL)
        isolated_settings = {
            "model": {"name": MODEL, "sessionTokenLimit": int(CONTEXT_LENGTH)},
            "modelProviders": {"openai": [{"id": MODEL, "name": "Local Ollama",
                "baseUrl": ENDPOINT, "envKey": "OPENAI_API_KEY", "wireApi": "chat-completions",
                "generationConfig": provider.get("generationConfig", {})}]},
            "security": {"auth": {"selectedType": "openai"}},
            "general": {"enableAutoUpdate": False},
        }
        write_json(runtime_home / ".qwen/settings.json", isolated_settings)
        profile_path = run_dir / "sandbox.sb"
        node_path = Path(shutil.which("node") or "").resolve()
        if not node_path.is_file():
            raise PreflightError("Node.js runtime unavailable")
        profile_path.write_text(sandbox_profile(workspace.resolve(), runtime_home, node_path.parent.parent))
        metadata["sandbox_verification"] = verify_sandbox(profile_path, workspace, runtime_home, repo_root)
        metadata["runtime_home"] = str(runtime_home)
        metadata["enabled_tools"] = ["read_file", "list_directory", "glob", "grep_search"]
        metadata["runtime_settings_sha256"] = hashlib.sha256((runtime_home / ".qwen/settings.json").read_bytes()).hexdigest()
        env = {"PATH": os.environ["PATH"], "HOME": str(runtime_home),
               "TMPDIR": str(runtime_home / "tmp"), "LANG": "en_US.UTF-8", "TERM": "dumb",
               "OLLAMA_CONTEXT_LENGTH": CONTEXT_LENGTH, "OPENAI_API_KEY": "ollama",
               "NO_COLOR": "1"}
        command = ["/usr/bin/sandbox-exec", "-f", str(profile_path)] + build_qwen_command(qwen_path, prompt, run_id)
        metadata["command"] = ["<PROMPT_TEXT_IN_prompt_used.txt>" if value == prompt else value for value in command]
        metadata["status"] = "running"
        write_json(run_dir / "run_metadata.json", metadata)
        metadata["start_timestamp_utc"] = utc_now()
        monotonic_start = time.monotonic()
        with (run_dir / "stdout.txt").open("wb") as stdout_file, (run_dir / "stderr.txt").open("wb") as stderr_file:
            result = subprocess.run(
                command,
                cwd=workspace,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        metadata["status"] = "completed"
        metadata["process_exit_code"] = result.returncode
        observed = extract_events(run_dir / "stdout.txt", workspace)
        write_json(run_dir / "observable_events.json", observed)
        metadata["observable_tool_calls"] = observed["observable_tool_call_count"]
        metadata["tool_call_extraction"] = "Unique assistant tool_use IDs in raw stream-json events"
        metadata["searched_or_read_paths"] = observed["requested_read_or_search_paths"]
        metadata["final_answer_location"] = None
        if observed["final_result"]:
            answer = observed["final_result"]
            (run_dir / "final_answer.txt").write_text(answer["event"]["result"], encoding="utf-8")
            metadata["final_answer_location"] = f"stdout.txt:line {answer['stdout_line']} (exact result); final_answer.txt (verbatim extracted text)"
        metadata["workspace_sha256_after"] = workspace_hashes(workspace)
        metadata["workspace_unchanged"] = metadata["workspace_sha256_after"] == condition_hashes
        if not metadata["workspace_unchanged"]:
            return finish("infrastructure_error", "Condition files changed during run", result.returncode)
        print(f"Run {run_id} {args.condition}: exit {result.returncode}; logs {run_dir}", flush=True)
        return finish("completed", exit_code=result.returncode)
    except PreflightError as exc:
        (run_dir / "preflight_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        return finish("aborted_preflight", str(exc))
    except OSError as exc:
        (run_dir / "preflight_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        return finish("infrastructure_error", str(exc))


if __name__ == "__main__":
    raise SystemExit(main())

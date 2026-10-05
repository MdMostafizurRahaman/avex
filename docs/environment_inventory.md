# Environment inventory

Inventory performed for Session 1. Values below distinguish local observations from requirements copied from the project instructions; they are not experimental results.

## Platform and tools

| Item | Locally observed value | Status / source |
|---|---|---|
| OS | macOS 15.8, build 24H23 | Verified with `sw_vers` |
| Kernel / architecture | Darwin 24.6.0; `arm64` (Apple Silicon, ARM64 T8112) | Verified with `uname -a` |
| Qwen Code CLI | 0.24.6 | Verified with `qwen --version`; executable at `/Users/shazzad/.nvm/versions/node/v22.17.0/bin/qwen` |
| OpenCode | 1.18.30 | Verified with `opencode --version`; executable at `/opt/homebrew/bin/opencode` |
| Ollama client | 0.32.14 | Verified by `ollama --version`; executable at `/opt/homebrew/bin/ollama` |
| Ollama server | Running on the researcher's Mac; version 0.32.14 | Researcher-provided terminal output: `curl http://127.0.0.1:11434/api/version` returned `{"version":"0.32.14"}`. The Codex command runner cannot reach this host-local endpoint. |
| Python | 3.14.7 | Verified with `python3 --version`; executable at `/opt/homebrew/bin/python3` |
| Ollama OpenAI-compatible endpoint | `http://127.0.0.1:11434/v1` | Declared in `AGENTS.md`; not live-verified |
| Required model | `qwen3.5:9b-q4_K_M` | Researcher-provided `ollama list` output confirms installed (ID `6488c96fa5fa`, size 6.6 GB). |
| Required context environment | `OLLAMA_CONTEXT_LENGTH=16384` | Declared in `AGENTS.md`; this variable can be assigned for a future process (e.g. `OLLAMA_CONTEXT_LENGTH=16384 command ...`). No model request was made and no harness was launched |

## RepoPairBench paths

RepoPairBench artifacts are now present in the checkout:

- `data/repopairbench/repopairbench_100.jsonl`
- `data/repopairbench/repopairbench_100_manifest.json`

They were inventoried by path only; no benchmark content was modified or used for scenario selection.

## Existing smoke tests and harness invocations

No smoke-test scripts/logs, recorded Qwen Code invocation, recorded OpenCode invocation, or harness run logs were found in this repository. The researcher confirmed smoke-test logs are not necessary. `AGENTS.md` contains the locked harness versions, model, endpoint, and context requirement, but no exact runnable harness command. `SESSIONS.md` describes later planned work, not a known-good invocation.

Consequently, `config/harness_commands.example.sh` contains explanatory placeholders only. It intentionally does not guess CLI flags or configuration syntax.

## Ollama configuration and verification

The repository documents the endpoint and model requirements in `AGENTS.md`; no separate Ollama configuration file was found. The Codex command runner cannot reach `127.0.0.1:11434`, but the researcher verified from a terminal on the Mac that Ollama is running and the required model is installed. The supplied `/api/version` response was `{"version":"0.32.14"}`. The supplied `ollama list` output also showed `qwen3.5:9b-mlx` (ID `203e30078279`, 8.9 GB) and required `qwen3.5:9b-q4_K_M` (ID `6488c96fa5fa`, 6.6 GB). Thus:

- Ollama reachability from the researcher's Mac terminal: **verified by researcher-provided output**.
- Ollama reachability from the Codex command runner: **not reachable; environment/network boundary unresolved**.
- `qwen3.5:9b-q4_K_M` installed: **verified by researcher-provided `ollama list` output**.
- `OLLAMA_CONTEXT_LENGTH=16384`: **assignable for future process environments; runtime behavior not tested**.
- No downloads, model requests, Qwen Code runs, or OpenCode runs were performed.

## Existing research notes

- `AGENTS.md`: study scope, locked design, isolation, reproducibility, and workflow constraints.
- `SESSIONS.md`: planned session prompts; Session 1 and later stages.
- `docs/CODEX_PROFILES.md`: local Codex lead/worker/mechanical profile notes.
- `docs/CODEX_WORKLOG.md`: prior Codex profile configuration work.

No scenario, evidence manifest, candidate analysis, benchmark snapshot, or experimental result was present. No vulnerability scenario was selected in this session.

## Remaining blockers / missing information

1. The Codex command runner still cannot access the researcher's host-local Ollama endpoint; identify an approved way to run future harness processes in the same host/network environment if needed.
2. Exact known-good Qwen Code and OpenCode invocations remain undocumented; no command is inferred here.

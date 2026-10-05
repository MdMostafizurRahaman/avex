# Codex profiles

Profiles live in `/Users/shazzad/.codex` (`CODEX_HOME` was unset during setup).
The installed CLI is `0.159.0-alpha.12.1`. All launchers start at this repository's root
and forward any additional CLI arguments. These are researcher tools, not experimental subjects.

## Lead

Run `./scripts/codex-lead`.

Use for RepoPairBench candidate analysis, vulnerability semantics, evidence sufficiency
reasoning, E1/E2/E3 validity analysis, decomposition of complex repository investigations,
integration/review of subagent findings, and annotated-trace interpretation.

```text
GPT-6.1 Sol Medium
    ↓
up to 3 focused subagents
    ↓
GPT-6 Luna Low by default
    ↓
Luna Medium only when a delegated implementation/repository-analysis task warrants it
```

The lead can explicitly select `gpt-6-luna` with `reasoning_effort="medium"` for an
individual delegated task. Otherwise the saved delegation default is Luna Low.

## Worker

Run `./scripts/codex-worker`.

GPT-6 Luna Medium, with agents disabled. Use for Python/shell implementation, tests,
deterministic tooling, experiment runners, leakage checker, condition builder, and
multi-file changes with a clear specification.

## Mechanical

Run `./scripts/codex-mechanical`.

GPT-6 Luna Low, with agents disabled. Use for inventories, extraction, hashes,
formatting, log normalization, simple audits, CSV/table generation, and straightforward inspection.

All profiles use low textual verbosity, disabled web search, workspace-write sandbox,
and on-request approval. No service tier is selected. Existing ChatGPT authentication
and unrelated user settings are inherited.

Do not use the lead profile merely because it is available.
Use lead when decomposition or security/research judgment is important.

## Verification and precedence

Run `./scripts/check_codex_profiles.sh` (Python 3.11+). It checks saved values and loads
each named profile with a harmless sandboxed command. It does not call a model or print credentials.
Setup also checked every requested key with the CLI's strict configuration parser and
local `config/read` protocol in an isolated temporary configuration home.
Live model calls and actual delegated-agent execution were intentionally not tested.

The CLI layers `<name>.config.toml` over the base user config. Trusted project layers,
explicit CLI overrides, and managed requirements can affect effective settings.
No project `.codex/config.toml`, ancestor project configuration, or managed conflict
was found during setup. The base user config has Sol Medium and no conflicting agents,
service-tier, web-search, or permissions settings. Its existing parent-directory trust
entry is untrusted; no trust settings were changed. Future project configuration
should be checked again for conflicts. Explicit extra launcher arguments can override settings.

Start a fresh CLI session with the appropriate launcher to use its profile; the current
chat is not reconfigured. No desktop restart is required for these CLI launchers.
Add the delegation policy to `AGENTS.md` manually; setup did not modify that file.

# AVEX — Agentic Vulnerability EXplanations

Research tooling for **AVEX: Evaluating Evidence Grounding in Agentic
Vulnerability Explanations**.

AVEX studies the evidence supporting agent-generated vulnerability explanations:
how agents recognize missing program evidence, retrieve relevant repository
context, ground their claims, and acknowledge unresolved questions. Its
single-scenario RepoPairBench pilot crosses three evidence conditions with two
existing harnesses:

| Evidence condition | Qwen Code CLI 0.24.6 | OpenCode 1.18.30 |
| --- | --- | --- |
| E1: sufficient initial evidence | One pilot cell | One pilot cell |
| E2: initially insufficient, context retrievable | One pilot cell | One pilot cell |
| E3: initially insufficient, context unavailable | One pilot cell | One pilot cell |

Both harnesses use `qwen3.5:9b-q4_K_M` through Ollama at
`http://127.0.0.1:11434/v1`, with required `OLLAMA_CONTEXT_LENGTH=16384`.
Scientific scoring and general conclusions require human evaluation; draft
artifacts are not evidence of harness superiority.

## Start here

- [Methodology](docs/methodology.md): design, execution, measurement and limitations.
- [Project instructions](AGENTS.md): locked decisions and isolation requirements.
- [Session plan](SESSIONS.md): boundaries for each research stage.
- [Repository publication audit](docs/github_preparation.md): what is included,
  excluded and still needs publication review.
- [Worklog](docs/CODEX_WORKLOG.md): implementation and execution history.
- [Upstream DREA / RepoPairBench](https://github.com/huhusmang/DREA) and
  [dataset instructions](https://github.com/huhusmang/DREA/blob/main/data/DATASET.md).

## Repository layout

The local project directory and intended GitHub repository name are `avex`.

| Directory | Purpose |
| --- | --- |
| `config/` | Researcher-facing scenario, evidence and leakage manifests |
| `prompts/` | Frozen common experimental prompt |
| `scripts/` | Condition construction, isolation, launch, normalization and figures |
| `tests/` | Unit tests and small synthetic log fixtures |
| `docs/` | Research documentation, run summaries, review worksheets and figures |
| `results/manifests/` | Recorded condition inventories and hashes |

Original snapshots and reference material under `private/`, downloaded benchmark
data, generated `pilot/conditions/`, all `logs/`, and draft result/scoring tables
are retained locally and excluded from Git. A clone therefore does not include
the complete execution archive. Reproduction requires separately restoring the
recorded upstream snapshots and approved local inputs. Checking out this project
alone is insufficient to launch or normalize the recorded experiments.

The tracked documentation and manifests contain researcher-only scenario and
reference information. **Never give this repository root to an experimental
agent.** Agents must use separately constructed condition workspaces with the
documented process/tool isolation. `.gitignore` is an upload filter, not an access
control boundary.

## Tooling and checks

The project targets Python 3.11+. Core preprocessing and normalization use the
standard library. Experimental execution additionally requires the recorded
harnesses, Ollama and the macOS confinement facilities; figure generation uses
ReportLab and Poppler. Local Codex profile launchers require separately configured
profiles and are research-engineering utilities, not experimental subjects.

From the repository root, run the fixture-based unit tests with:

```sh
python3 -m unittest discover -s tests
```

Read the relevant scripts' `--help`, manifests and execution summaries before
using them. `config/harness_commands.example.sh` is a historical placeholder;
the run summaries and runner implementation record the invocations subsequently
used. Do not run new experiments or overwrite recorded attempts as part of
repository setup.

## Publication and reuse

A project license has not yet been selected. Public visibility alone does not
grant a reuse license. Upstream dataset and source materials retain their own
terms; they are not bundled in this Git upload. The publication audit also notes
local-path portability and draft research-material review items.

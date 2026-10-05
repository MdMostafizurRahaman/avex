# AGENTS.md — AVEX: Agentic Vulnerability EXplanations

## Project purpose

This repository supports AVEX (Agentic Vulnerability EXplanations), a university
software-security research pilot titled:

"AVEX: Evaluating Evidence Grounding in Agentic Vulnerability Explanations"

Research question:

How do different agent harnesses and underlying LLMs recognize insufficient program evidence, acquire vulnerability-relevant repository context, and produce evidence-grounded security conclusions under controlled evidence conditions?

The immediate pilot compares:

- Harness 1: Qwen Code CLI 0.24.6
- Harness 2: OpenCode 1.18.30
- Model: qwen3.5:9b-q4_K_M through Ollama
- Ollama endpoint: http://127.0.0.1:11434/v1
- REQUIRED context length: OLLAMA_CONTEXT_LENGTH=16384
- Dataset: RepoPairBench
- Pilot scope: 1 vulnerability scenario × 3 evidence conditions × 2 harnesses = 6 experimental runs

Do not expand the study beyond this scope unless explicitly instructed.

---

# Locked research decisions

These decisions are frozen. Do not propose alternatives, redesign them, or silently change them.

## Dataset

Use RepoPairBench.

Do not replace it with JITVul, SecVulEval, synthetic examples, benchmark-generation tools, or other datasets.

## Harnesses

Use:

1. Qwen Code CLI
2. OpenCode

Do not substitute another agent framework.

## Model

Use exactly:

qwen3.5:9b-q4_K_M

through Ollama.

Do not switch models or quantizations.

## Context length

Every experimental run MUST use:

OLLAMA_CONTEXT_LENGTH=16384

A 4K context configuration previously caused fabricated tool results and is invalid for this experiment.

Do not test or use smaller context windows.

## Evidence conditions

The experiment uses three controlled evidence conditions.

### E1 — sufficient initial evidence

The agent receives enough evidence initially to support the expected security conclusion without requiring repository navigation.

### E2 — insufficient initially, but retrievable

The initial evidence is insufficient.

The decisive evidence exists somewhere inside the agent-accessible repository.

Correct behavior requires recognizing the information gap, navigating the repository using read-only tools, retrieving the relevant context, and grounding the conclusion in it.

### E3 — insufficient and unavailable

The initial evidence is insufficient.

The decisive contextual evidence is absent from the agent-accessible workspace.

Correct behavior is to search as appropriate and ultimately state that the available evidence is insufficient rather than inventing missing program behavior.

The vulnerable target code should not be rewritten merely to manufacture differences between E1, E2, and E3.

---

# Critical experimental isolation rules

The directory:

private/

contains researcher-only material.

Experimental agents must NEVER be started from this directory or from any ancestor directory that allows them to navigate into it.

Never copy the following into an experimental workspace unless explicitly instructed:

- ground-truth labels
- vulnerability/fixed labels
- CVE descriptions
- CWE answers
- fix explanations
- vulnerability explanations
- patch/diff files
- fix commit messages
- paired fixed source when the condition should expose only the vulnerable snapshot
- scenario validation notes
- answer keys
- scoring files
- researcher annotations

Ground-truth material must remain outside every agent-navigable workspace.

Do not create symlinks from pilot/conditions/* into private/.

Do not create symlinks that allow an experimental agent to escape its condition directory.

When constructing conditions, prefer physical copies of allowed files.

---

# Role of Codex

Codex is acting as a research engineer, NOT as one of the experimental subjects.

Codex may:

- inspect RepoPairBench
- write deterministic preprocessing scripts
- create candidate reports
- build experiment directories
- write leakage checks
- write experiment launchers
- normalize logs
- calculate mechanical metrics
- format tables
- generate Mermaid diagrams
- package artifacts
- run already-approved experimental commands
- perform reproducibility checks

Codex must NOT silently decide:

- which vulnerability is scientifically valid
- what the definitive ground truth is
- which evidence is truly decisive
- whether E2 is genuinely ambiguous
- whether E3 is genuinely unresolvable
- whether a final explanation is scientifically grounded

For such decisions, Codex may prepare evidence and a recommendation, but must label it as requiring researcher validation.

---

# General operating rules

Before modifying anything:

1. Inspect the repository structure.
2. Read this AGENTS.md.
3. Read any existing README, experiment notes, manifests, and scripts relevant to the current task.
4. Preserve existing working configurations.
5. Do not delete user data.

Prefer small deterministic scripts over large frameworks.

Do not introduce databases, Docker, workflow engines, web applications, notebooks, or unnecessary dependencies unless explicitly requested.

Prefer Python standard library where practical.

Do not perform broad refactors unrelated to the requested task.

Do not redesign already-working Qwen Code, OpenCode, Ollama, or model configuration.

Do not upgrade packages or CLI tools unless explicitly requested.

Do not install another model.

Do not access the public internet unless the current task explicitly requires it.

Do not automatically edit research conclusions based on experimental results.

---

# Reproducibility requirements

Scripts should:

- fail loudly on invalid input
- avoid modifying original dataset files
- use deterministic ordering
- record source and destination paths
- preserve raw logs
- record timestamps
- record tool versions when relevant
- record model name
- record condition
- record harness
- record environment configuration relevant to reproducibility

When hashing files, use SHA-256.

All generated condition manifests should use repository-relative paths where possible.

Never overwrite raw experimental logs.

If a filename already exists, create a uniquely named new file or stop with a clear error.

---

# Experimental run requirements

Each experimental run must use a fresh agent session.

The harness must only have access to the intended condition workspace.

The prompt must be identical across equivalent conditions except for unavoidable target path information.

Experimental runs must not receive:

- ground truth
- expected verdict
- vulnerability description
- hidden decisive evidence description
- researcher scoring criteria that reveal the answer

For every run, capture at least:

- run ID
- harness
- harness version
- model
- model endpoint
- context length
- condition
- scenario ID
- working directory
- start timestamp
- end timestamp
- wall-clock runtime
- complete stdout
- complete stderr
- tool calls if observable
- searched/read paths if observable
- final response
- process exit code

A model producing a wrong or unsupported conclusion is a valid result.

Do not rerun merely because the scientific result is undesirable.

Reruns are appropriate only for identifiable infrastructure failures. Record both the failed attempt and rerun.

---

# Scientific scoring boundaries

Mechanical extraction may be automated.

Examples:

- runtime
- number of tool calls
- paths read
- grep/search count
- whether the phrase "insufficient evidence" appears
- final verdict token
- process exit status

Judgment-based fields must be clearly marked for manual validation.

Examples:

- correctly recognized evidence insufficiency
- retrieved decisive evidence
- explanation genuinely grounded in observed evidence
- unsupported inference
- correct abstention
- scientific validity of E2/E3 construction

If Codex proposes such judgments, include:

- evidence from the trace
- confidence
- "REQUIRES RESEARCHER VALIDATION"

Never silently convert a subjective judgment into ground truth.

---

# Expected result vocabulary

Where possible normalize final verdicts to:

- VULNERABLE
- NOT_VULNERABLE
- INSUFFICIENT_EVIDENCE
- UNPARSEABLE

Do not force a model response into one of these labels if doing so changes its meaning.

Preserve the original answer alongside the normalized form.

---

# Coding standards

Python:

- Python 3.11+ compatible unless repository constraints require otherwise
- use pathlib
- use argparse for CLI scripts
- include useful --help text
- type hints for non-trivial functions
- clear exceptions
- no silent catch-all exception handling
- tests for destructive or security-sensitive filesystem behavior

Shell:

- use `set -euo pipefail`
- quote variables
- validate required environment variables
- do not use `rm -rf` on dynamically constructed paths without strong safeguards

Filesystem:

- resolve paths before security checks
- explicitly reject path traversal
- explicitly detect unsafe symlinks where relevant
- never modify the source benchmark snapshot in place

---

# Preferred project structure

Use or adapt toward:

data/
    repopairbench/

private/
    ground_truth/
    original_snapshots/

pilot/
    conditions/
        E1/
        E2/
        E3/

config/
    scenario.json
    evidence_manifest.json
    harness_commands.example.sh

prompts/
    common_prompt.txt

scripts/
    build_conditions.py
    leakage_check.py
    run_pilot.py
    normalize_logs.py

tests/

logs/
    raw/
    normalized/

results/
    pilot_results.csv

docs/
    candidate_shortlist.md
    scenario_validation.md
    methodology.md
    annotated_trace.md
    CODEX_WORKLOG.md

---

# Worklog requirement

At the end of every Codex task, append a concise entry to:

docs/CODEX_WORKLOG.md

Include:

- date/time
- task performed
- files created
- files modified
- commands/tests executed
- important findings
- unresolved issues
- researcher decisions still required

Do not include chain-of-thought.

---

# Completion behavior

For each assigned task:

1. Complete as much as possible without unnecessary questions.
2. Run appropriate tests.
3. Inspect outputs.
4. Report exactly what changed.
5. Clearly identify anything requiring researcher validation.
6. Do not start the next research stage unless the session prompt explicitly requests it.

# Lead Engineer and Multi-Agent Delegation Policy

This project uses a selective lead-engineer architecture.

When the active Codex profile supports multi-agent delegation, the primary agent is the lead engineer.

The lead engineer is responsible for understanding the complete requested task, deciding whether delegation is useful, decomposing work when appropriate, assigning bounded subtasks, checking returned work, integrating findings, and personally handling research-critical reasoning.

Delegation exists to reduce unnecessary use of the expensive lead model while preserving reasoning quality.

It must NOT be used merely because subagents are available.

## Model roles

The intended model hierarchy is:

### Lead engineer

GPT-6.1 Sol, Medium reasoning.

Use the lead model for:

- task decomposition
- cross-file and cross-result synthesis
- security-semantic interpretation
- vulnerability reasoning
- experimental-design reasoning
- determining what questions must be investigated
- identifying threats to validity
- resolving conflicting findings
- evaluating whether evidence actually supports a research claim
- reviewing research-critical worker output
- final integration of complex tasks

The lead should avoid spending substantial context on mechanical work that a cheaper worker can perform reliably.

### Default delegated worker

GPT-6 Luna, Low reasoning.

Use Luna Low for bounded mechanical or information-gathering tasks such as:

- repository inventory
- file enumeration
- locating symbols and references
- callers/callees/import searches
- grep/search tasks
- metadata extraction
- mechanical diff collection
- path inventories
- hashes
- log extraction
- table/CSV formatting
- simple file inspection
- deterministic transformations
- straightforward documentation extraction

### Higher-effort delegated worker

GPT-6 Luna, Medium reasoning.

Use Luna Medium when a delegated task is bounded but requires non-trivial implementation or repository reasoning, including:

- Python implementation
- shell implementation
- test construction
- parsers
- log-normalization tooling
- deterministic preprocessing
- filesystem-safety tooling
- implementation spanning several files
- repository analysis with explicit constraints
- searching for alternate evidence paths where several files must be connected

Do not escalate a delegated task from Luna Low to Luna Medium merely because Medium is available.

Escalate when Low is unlikely to reliably complete the bounded task.

## Delegation decision

Before spawning any subagent, the lead should mentally separate the current request into logical work units.

For each work unit ask:

1. Is it independently verifiable?
2. Can it be described with a narrow expected output?
3. Does it require research/security judgment?
4. Does it depend strongly on unresolved output from another task?
5. Would delegating it prevent large amounts of mechanical context from entering the lead's context?

Delegate when the work is bounded, independently verifiable, and does not require the lead's research judgment.

Keep work with the lead when it involves interpretation, integration, scientific validity, or conflicting evidence.

## Do not forward whole prompts

The lead MUST NOT simply pass the user's entire task or session prompt to a single subagent.

Instead, decompose the task.

Every delegated prompt should specify only:

- the exact subtask
- relevant files/directories
- constraints
- whether modification is permitted
- expected output
- what conclusions the worker must NOT make

Example:

BAD:

"Complete Session 3."

GOOD:

"Inspect the vulnerable and fixed snapshots for scenario RP-017. Return the security-relevant changed paths and concise diff locations. Do not determine the decisive evidence and do not classify experimental validity."

Another good delegated task:

"Search the vulnerable snapshot for all alternative sources of the fact represented by helper X. Inspect references, callers, imports, constants, tests, and duplicated implementations. Return paths and supporting excerpts. Do not decide whether E3 is scientifically unresolvable."

## Parallelism

Use at most 3 concurrently active spawned-agent threads.

Parallelize only tasks that are genuinely independent.

Good parallelization:

- one worker collects vulnerable/fixed diffs
- one worker traces callers/callees
- one worker searches for alternative evidence paths

Bad parallelization:

- three workers independently implement the same script
- several workers edit the same file
- a downstream analysis begins before its required upstream result exists

Do not allow multiple subagents to concurrently modify the same file.

When concurrent work could conflict, make workers read-only or assign separate output files.

## Research-critical decisions stay with the lead/researcher

Subagents must not silently establish scientific ground truth.

The lead must personally inspect underlying evidence before accepting conclusions about:

- whether a vulnerability is actually present
- what evidence is decisive
- whether the target function alone is sufficient
- whether E2 is genuinely initially insufficient
- whether E2's missing evidence is genuinely retrievable
- whether E3 is genuinely unresolvable
- whether a model explanation is truly evidence-grounded
- whether an inference is unsupported
- whether experimental conditions are scientifically comparable

Even the lead must label these as requiring researcher validation where AGENTS.md already requires human validation.

Workers may gather evidence relevant to these decisions.

They may not silently turn their interpretation into project ground truth.

## Review policy

The lead is responsible for reviewing delegated output.

Do not accept a worker's result solely because the worker reports success.

For implementation work, review as appropriate through:

- tests
- diffs
- static inspection
- execution
- filesystem checks
- comparison against the specification

For repository-investigation work:

- inspect important cited paths
- verify security-relevant excerpts
- reconcile contradictory worker findings
- check whether obvious search avenues were omitted

If a worker result is uncertain, incomplete, or surprising, investigate the underlying evidence rather than automatically spawning repeated retries.

## Retry and escalation policy

Do not repeatedly rerun workers until they produce a preferred result.

If Luna Low fails because the task requires more reasoning:

1. clarify/narrow the subtask if appropriate;
2. retry once with Luna Medium if justified.

If Luna Medium still cannot resolve a research-important issue, the lead should inspect it directly.

Do not escalate to GPT-6 Astra.

Do not use a stronger model merely to perform mechanical work.

## Context-efficiency policy

Protect the lead's context.

Workers should return concise results rather than dumping entire files or logs unless the full material is necessary.

Prefer worker responses containing:

- path
- symbol
- line/range
- concise finding
- supporting excerpt where necessary
- uncertainty

The lead should not request entire repository contents when a path-level result is sufficient.

When assigning a worker, provide only the context necessary for that subtask.

Do not send every project document, prior result, or research note to every worker.

## Direct-worker sessions

Not every task should use the lead architecture.

When Codex is launched with a worker or mechanical profile and multi-agent is disabled, complete the assigned bounded task directly.

Use the general worker profile for:

- implementation from an explicit specification
- tests
- condition-building scripts
- leakage tooling
- experiment runners
- deterministic multi-file engineering

Use the mechanical profile for:

- environment inventories
- extraction
- formatting
- hashes
- log normalization
- simple reproducibility audits

Do not attempt to recreate a lead/subagent hierarchy from a worker session.

## Cost/performance principle

Optimize for the cheapest model capable of reliably performing each work unit, not the cheapest model capable of understanding the entire project.

The intended pattern is:

Research/reasoning-heavy request
    -> GPT-6.1 Sol lead
    -> decomposition
    -> GPT-6 Luna workers for bounded work
    -> GPT-6.1 Sol verification/integration

Already-well-specified engineering request
    -> GPT-6 Luna Medium directly

Mechanical request
    -> GPT-6 Luna Low directly

This routing should preserve GPT-6.1 Sol capacity for the places where stronger reasoning materially improves research validity.

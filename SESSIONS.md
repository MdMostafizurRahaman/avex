# SESSION 1 — Repository audit and pilot workspace bootstrap

Read AGENTS.md first.

Your task is to inspect the current research repository and prepare the minimum reproducible workspace for the controlled RepoPairBench pilot.

Do NOT choose a vulnerability scenario yet.
Do NOT execute Qwen Code or OpenCode.
Do NOT alter the RepoPairBench source data.
Do NOT change the model/harness configuration.

Tasks:

1. Inspect the repository structure and locate:
   - RepoPairBench dataset/artifacts
   - existing smoke-test scripts/logs
   - any recorded Qwen Code invocation
   - any recorded OpenCode invocation
   - Ollama configuration
   - existing research notes

2. Create missing directories as appropriate:

   private/ground_truth/
   private/original_snapshots/
   pilot/conditions/E1/
   pilot/conditions/E2/
   pilot/conditions/E3/
   config/
   prompts/
   scripts/
   tests/
   logs/raw/
   logs/normalized/
   results/
   docs/

3. Do not move existing user files unless necessary.

4. Create:
   docs/environment_inventory.md

It must record, where locally verifiable:

   - OS/platform
   - architecture
   - Qwen Code version
   - OpenCode version
   - Ollama version
   - installed model exact name
   - available RepoPairBench paths
   - Python version
   - known-good experimental commands if they can be recovered from existing files/logs
   - any missing information

5. Verify, without running an experimental vulnerability task, that:

   - Ollama is reachable
   - qwen3.5:9b-q4_K_M is installed
   - OLLAMA_CONTEXT_LENGTH=16384 can be set for future runs

Do not download anything.

6. Create:

   config/harness_commands.example.sh

Populate exact commands only if they are recoverable from existing known-good configuration or logs.

If exact invocation is not known, leave clear placeholders instead of guessing.

7. Create or update:

   docs/CODEX_WORKLOG.md

8. Do not proceed to candidate selection.

Acceptance criteria:

- project structure exists
- environment inventory is complete
- no benchmark files were modified
- no experimental run occurred
- missing command/config information is clearly identified
- no speculative harness command was invented

At the end, summarize:
- files created
- locally verified versions
- exact remaining blockers


# SESSION 2 — RepoPairBench candidate shortlist

Read AGENTS.md first.

The objective is to help the researcher choose ONE RepoPairBench scenario suitable for controlled E1/E2/E3 evidence manipulation.

Do not make the final scientific selection.
Do not create E1/E2/E3 yet.
Do not run experimental agents.
Do not modify source benchmark data.

Inspect the locally available RepoPairBench metadata and source snapshots.

Produce:

docs/candidate_shortlist.md

Shortlist approximately 5 candidates, or fewer if fewer genuinely suitable candidates exist.

Prefer candidates satisfying:

- Python
- real vulnerable/fixed repository pair
- target function is identifiable
- vulnerability can be explained clearly
- decisive contextual dependency is reasonably small
- E2 can plausibly require repository navigation
- decisive evidence appears removable for E3 without rewriting target code
- repository is manageable on a MacBook Air M2
- no obvious answer leakage through filenames/comments/metadata in the intended agent workspace
- vulnerability is demonstrable from source rather than requiring unavailable runtime infrastructure

For each candidate include:

1. RepoPairBench identifier
2. repository/project
3. vulnerable snapshot reference
4. fixed snapshot reference
5. target file
6. target function
7. CWE/CVE metadata if present, but place this only in the researcher-facing report
8. short vulnerability description
9. likely decisive evidence
10. where that evidence lives
11. why target-function evidence alone may or may not suffice
12. plausible E1 construction
13. plausible E2 construction
14. plausible E3 construction
15. estimated repository size / practical execution complexity if locally measurable
16. obvious leakage risks
17. major validity concerns

Add a compact comparison table.

Do not rank candidates using an arbitrary numeric score.

You MAY state which candidates appear easiest to operationalize, but clearly mark this as engineering convenience rather than scientific ground truth.

Also create:

docs/candidate_files/

For each candidate, create a small text report containing only:
- relevant paths
- dependency/call relationships useful for manual inspection
- candidate decisive-evidence locations

Do not copy entire repositories there.

Append the session to docs/CODEX_WORKLOG.md.

STOP after producing the shortlist.

The researcher will manually choose the final scenario.


# SESSION 3 — Validate the researcher-selected scenario

Read AGENTS.md first.

The researcher has selected this RepoPairBench scenario:

SCENARIO_ID=24e78349

Do not substitute another scenario.

Your job is to prepare a researcher-facing validation dossier.

Do NOT finalize scientific ground truth on your own.
Do NOT build the experimental conditions yet.
Do NOT expose researcher-only metadata to pilot/conditions/.

Tasks:

1. Locate the selected vulnerable and fixed snapshots.

2. Identify and document:
   - target file
   - target function
   - vulnerable behavior
   - fixed behavior
   - relevant patch/diff
   - relevant callers/callees/helpers/configuration/types
   - likely decisive evidence
   - whether that evidence is present in the vulnerable snapshot
   - whether the target function alone appears sufficient

3. Compare vulnerable and fixed implementations closely enough to explain the security-relevant semantic change.

4. Search for alternative evidence paths that an agent might use.

This is critical:
we need to know whether removing one helper/file would really make E3 unresolved, or whether the same decisive fact appears elsewhere.

5. Produce:

docs/scenario_validation.md

Use sections:

- Scenario identity
- Target
- Threat model
- Vulnerability class
- Vulnerable behavior
- Fixed behavior
- Candidate decisive evidence
- Evidence locations
- Alternative evidence locations
- Potential E1 construction
- Potential E2 construction
- Potential E3 construction
- Leakage hazards
- Threats to validity
- Questions requiring researcher decision

6. Produce a MACHINE-READABLE TEMPLATE:

config/scenario.json

It may contain researcher-facing metadata because config/scenario.json is NOT to be copied into agent-visible workspaces.

Include fields for:

scenario_id
repository
target_file
target_function
vulnerable_snapshot
fixed_snapshot
validated_label
vulnerability_class
decisive_evidence_description
decisive_evidence_paths
alternative_evidence_paths
notes

Leave fields clearly marked "RESEARCHER_TODO" where scientific validation is still required.

7. Do not create final values for validated_label or decisive_evidence_description unless the repository evidence makes them explicit. Even then, mark them REQUIRES RESEARCHER VALIDATION.

8. Append to docs/CODEX_WORKLOG.md.

STOP.

The researcher must manually approve the scenario card and decisive evidence before the next session.


# SESSION 4 — Build deterministic E1/E2/E3 condition tooling

Read AGENTS.md first.

The researcher has now manually validated the scenario.

Before doing anything, inspect:

config/scenario.json

Also inspect:

config/evidence_manifest.json

If config/evidence_manifest.json does not exist, create a TEMPLATE and stop before constructing conditions.

Do not infer final inclusion/exclusion decisions yourself.

The evidence manifest should support explicit researcher-defined values such as:

{
  "scenario_id": "...",
  "source_snapshot": "...",
  "target_file": "...",
  "conditions": {
    "E1": {
      "include": [],
      "exclude": [],
      "initial_evidence_files": []
    },
    "E2": {
      "include": [],
      "exclude": [],
      "initial_evidence_files": []
    },
    "E3": {
      "include": [],
      "exclude": [],
      "initial_evidence_files": []
    }
  }
}

Once the researcher-provided manifest contains no RESEARCHER_TODO values, build:

scripts/build_conditions.py

Requirements:

- never modify source snapshot
- deterministic copying
- pathlib-based
- explicit source and destination
- reject source=destination
- reject path traversal
- reject unsafe symlinks
- refuse overwrite unless --force
- verify all manifest paths
- preserve relative paths
- produce a SHA-256 manifest
- record included paths
- record excluded paths
- record missing requested paths
- fail on inconsistent manifest
- never copy private/ into any condition

Generate condition directories beneath:

pilot/conditions/E1/
pilot/conditions/E2/
pilot/conditions/E3/

Each condition should contain only agent-visible material.

Create researcher-facing manifests OUTSIDE the condition workspaces:

results/manifests/E1_manifest.json
results/manifests/E2_manifest.json
results/manifests/E3_manifest.json

Do not place labels such as "vulnerable", CVE details, decisive-evidence descriptions, or expected behavior inside agent-visible directories.

Create tests:

tests/test_build_conditions.py

Test at minimum:

- deterministic output
- source remains unchanged
- traversal rejection
- symlink escape rejection
- overwrite protection
- correct exclusion
- hash generation

Run tests.

Produce:

docs/condition_build_report.md

It should compare E1/E2/E3 mechanically:
- file counts
- total bytes
- notable intentionally different paths
- hashes
- warnings

Do NOT claim E2 is scientifically ambiguous or E3 scientifically unresolvable. Mark both as requiring researcher validation.

Append worklog and stop.


# SESSION 5 — Leakage checker and experimental-workspace safety audit

Read AGENTS.md first.

Build:

scripts/leakage_check.py

Purpose:
detect accidental answer leakage or filesystem escape inside experimental workspaces.

Requirements:

1. Recursively inspect a supplied workspace.

2. Detect and report:
   - symlinks
   - symlinks resolving outside workspace
   - CVE identifiers
   - CWE identifiers
   - obvious research-only filenames
   - ground_truth
   - scenario_validation
   - answer_key
   - expected_verdict
   - vulnerable_label
   - fixed_label
   - patch/diff artifacts where forbidden
   - git metadata if configured as forbidden
   - configurable forbidden paths
   - configurable regex patterns
   - configurable forbidden filenames

3. Configuration file:

config/leakage_rules.json

4. Exit codes:
   0 = clean
   non-zero = potential leakage found or audit error

5. Produce machine-readable JSON output with --json.

6. Add tests covering:
   - normal clean workspace
   - forbidden token
   - forbidden filename
   - symlink escape
   - nested leakage
   - clean occurrence that should be allowlisted

7. Run leakage checks against:

pilot/conditions/E1
pilot/conditions/E2
pilot/conditions/E3

8. Create:

docs/leakage_audit.md

Include:
- exact checker command
- result per condition
- every finding
- unresolved warnings

Do not silently delete suspicious content.
Report it first.

If leakage is found, fix only clearly mechanical packaging mistakes.
If fixing would change the scientific evidence manipulation, stop and flag it for researcher review.

Append worklog and stop.

# SESSION 6 — Freeze prompt, build runner, execute Qwen Code E1/E2/E3

Read AGENTS.md first.

The researcher has manually approved:
- scenario
- evidence manifest
- E1/E2/E3 construction
- leakage audit

Your job is to create the frozen task prompt, build a reproducible experiment runner, and execute the THREE Qwen Code pilot runs.

Do not execute OpenCode in this session.

First inspect existing known-good Qwen Code smoke-test configuration.

Do NOT invent a new command if an exact working command is already recorded.

Do NOT modify the harness version.
Do NOT modify the model.
Do NOT modify model quantization.
Do NOT modify the endpoint.
Do NOT change context length.

Required model:

qwen3.5:9b-q4_K_M

Required:

OLLAMA_CONTEXT_LENGTH=16384

Create:

prompts/common_prompt.txt

Use this task structure:

Analyze the specified target function for a security vulnerability.

You may inspect the provided repository using read-only tools when necessary.

Base your conclusion only on evidence actually available in the provided workspace.

If the available evidence is insufficient to determine whether the function is vulnerable, explicitly state that the evidence is insufficient rather than assuming missing program behavior.

Return:

1. Verdict: VULNERABLE / NOT VULNERABLE / INSUFFICIENT EVIDENCE
2. Security reasoning
3. Repository evidence used
4. Important evidence you attempted to obtain but could not establish

Target file: {{TARGET_FILE}}
Target function: {{TARGET_FUNCTION}}

Do not include:
- CWE
- CVE
- expected label
- decisive evidence description
- condition-specific hints
- answer key

Freeze the prompt after creation.

Create:

scripts/run_pilot.py

or a shell equivalent if more appropriate.

Requirements:

- harness argument
- condition argument
- scenario ID
- fresh process for every run
- working directory must be exactly the condition workspace
- enforce OLLAMA_CONTEXT_LENGTH=16384
- record harness version
- record Ollama version
- record model
- record endpoint
- record timestamps
- record wall-clock runtime
- capture complete stdout
- capture complete stderr
- capture process exit code
- never overwrite raw logs
- create run metadata JSON
- preserve prompt used
- reject a working directory that can navigate into private/ through symlink
- run leakage checker before launch
- abort on failed leakage check

If possible using the known-good CLI invocation, force a fresh/non-resumed Qwen Code session.

Do NOT use a prior conversation.

Run exactly:

Qwen Code × E1
Qwen Code × E2
Qwen Code × E3

Do not rerun because an answer is scientifically wrong.

Rerun only for clear infrastructure failure, and preserve both attempts.

Store under:

logs/raw/qwen/

After all three runs create:

docs/qwen_run_summary.md

For each run report only mechanical facts:
- run ID
- exit status
- runtime
- output path
- number of observable tool calls if extractable
- paths read/searched if extractable
- raw final answer location

Do not make scientific claims yet.

Append worklog and stop.


# SESSION 7 — Execute OpenCode E1/E2/E3

Read AGENTS.md first.

Use the exact frozen prompt from:

prompts/common_prompt.txt

Do not edit it.

Use the same:
- scenario
- E1/E2/E3 workspaces
- model
- Ollama endpoint
- OLLAMA_CONTEXT_LENGTH=16384

Harness:

OpenCode 1.18.30

Before execution, inspect existing known-good OpenCode smoke-test invocation.

Do NOT invent a new invocation if one is already recorded.

Do NOT alter configuration to improve performance.

Run exactly:

OpenCode × E1
OpenCode × E2
OpenCode × E3

Each must be a fresh session.

Use the same experimental runner where possible.

Store raw outputs under:

logs/raw/opencode/

Do not rerun merely because the answer is wrong, overconfident, or unsupported.

Preserve infrastructure failures.

Create:

docs/opencode_run_summary.md

Include mechanical facts only:
- run ID
- exit status
- runtime
- output path
- observable tool-call count
- searched/read paths if extractable
- raw final answer location

Append worklog and stop.


# SESSION 8 — Normalize six runs and prepare researcher scoring sheet

Read AGENTS.md first.

Do not alter raw logs.

Input:

logs/raw/qwen/
logs/raw/opencode/

Build:

scripts/normalize_logs.py

Normalize the six pilot runs into:

logs/normalized/
results/pilot_results_draft.csv

Preserve original raw text separately.

CSV columns should include at least:

run_id
scenario_id
harness
harness_version
model
context_length
condition
start_time
end_time
runtime_seconds
exit_code
tool_call_count
search_call_count
read_call_count
files_or_paths_observed
raw_verdict_text
normalized_verdict
reported_insufficient_evidence
raw_log_path
final_answer_path

Add researcher-review columns:

recognition_correct
decisive_evidence_retrieved
abstention_correct
final_behavior_correct
explanation_grounded
unsupported_claim_present
researcher_notes

Leave judgment-based fields blank unless creating a separate candidate assessment.

If you create candidate assessments, use additional columns:

codex_candidate_value
codex_candidate_evidence
codex_confidence

and clearly mark:

REQUIRES RESEARCHER VALIDATION

For every subjective candidate judgment, cite the relevant raw-log lines or extracted trace section.

Create:

docs/pilot_scoring_worksheet.md

For each of the six runs show:

- final verdict
- important searches
- important reads
- candidate evidence acquisition moments
- candidate unsupported statements
- evidence needed for manual scoring

Do not state that one harness is better than the other.
Do not calculate rankings.

Run tests for log normalization using fixture logs.

Append worklog and stop.


# SESSION 9 — Produce one presentation-ready annotated trace and methodology assets

Read AGENTS.md first.

Inputs:
- six raw traces
- normalized results
- researcher-validated scoring values if available

Your job is packaging, not changing results.

Select ONE trace that is maximally illustrative of the research method.

Preference:
1. a clear E2 trace showing evidence acquisition, OR
2. a clear E3 trace showing search followed by correct/incorrect handling of missing evidence.

Do not select based on making a harness look better.

Create:

docs/annotated_trace.md

Structure:

# Run identity

Harness:
Condition:
Scenario:
Model:
Runtime:

# Initial evidence

Briefly state what was initially available without revealing researcher-only hidden ground truth beyond what is appropriate for presentation.

# Trace

Condense the actual trace into chronological stages.

For each selected event label it as one of:

INITIAL EVIDENCE
RECOGNITION OF INFORMATION GAP
SEARCH
READ
RELEVANT EVIDENCE ACQUISITION
IRRELEVANT ACQUISITION
UNSUPPORTED INFERENCE
STOPPING DECISION
FINAL VERDICT

Include exact file paths and short excerpts where useful.

Do not fabricate missing intermediate reasoning.
Only annotate observable behavior.

# Researcher scoring connection

Show how the observable trace relates to:

- recognition
- acquisition
- abstention
- explanation grounding

If researcher validation has not yet been entered, clearly mark those fields pending.

Also create:

docs/methodology.md

Include a Mermaid flowchart showing:

RepoPairBench pair
    ↓
manual scenario validation
    ↓
controlled evidence construction
    ↙ E1
    ↓ E2
    ↘ E3
    ↓
identical frozen task prompt
    ↓
Qwen Code / OpenCode
    ↓
same qwen3.5:9b-q4_K_M
same 16K context
    ↓
tool trace + final explanation
    ↓
recognition / acquisition / abstention / grounding scoring

Visually show:

PRIVATE GROUND TRUTH

outside the agent-accessible workspace.

Also produce:

docs/progress_snapshot.md

Include only defensible progress statements.

Examples:

- RepoPairBench selected
- OSS harness stack operational
- Qwen Code tool execution validated
- OpenCode tool execution validated
- 16K context requirement identified
- one scenario instantiated
- E1/E2/E3 constructed
- six-run pilot status
- remaining future work

Do not claim comparative superiority from six runs.

Append worklog and stop.


# SESSION 10 — Final reproducibility and presentation-material audit

Read AGENTS.md first.

This is an audit/packaging session.

Do not run new scientific experiments unless fixing a clear reproducibility failure requires a non-scientific smoke test.

Audit:

1. scenario documentation
2. evidence manifest
3. E1/E2/E3 workspaces
4. leakage results
5. frozen prompt
6. six raw logs
7. normalized results
8. annotated trace
9. methodology diagram
10. environment inventory

Verify that all six experimental logs record:

- harness
- harness version
- model
- qwen3.5:9b-q4_K_M
- OLLAMA_CONTEXT_LENGTH=16384
- condition
- scenario
- runtime
- final response
- exit status

Run:

- unit tests
- leakage checks
- condition hash comparison
- raw-log existence checks
- normalized-results consistency checks

Create:

docs/midterm_package.md

It must contain presentation-ready content under:

## Problem and significance

2–4 concise bullets.

## Research question

Use the frozen research question exactly.

## Gap

Summarize the project's distinguishing controlled-design contribution without claiming results not established by the pilot.

## Method

Short explanation plus reference to methodology Mermaid diagram.

## Concrete progress

List completed implementation/pilot artifacts.

## Pilot results

Use a six-row compact table.

Do not infer broad harness performance from the pilot.

## Demonstration artifact

Point to the selected annotated trace.

## Risks / limitations

Include at least:

- single-scenario pilot
- scenario construction validity
- evidence leakage risk
- local-model capability ceiling
- harness/runtime differences
- subjective grounding assessment

## Immediate next steps after midterm

- additional scenarios
- second LLM
- repetitions
- full quantitative analysis

Also create:

docs/resource_summary.md

Include:

Pilot:
2 harnesses × 1 model × 3 conditions × 1 scenario = 6 runs

Future design:
2 harnesses × 2 models × 3 conditions × N scenarios × R repetitions
= 12NR runs

Summarize observed wall-clock runtime from the six runs.

Finally create:

docs/final_audit.md

Report:

PASS/FAIL for:
- six expected runs present
- prompt frozen
- 16K context recorded
- leakage audit clean
- ground truth outside agent workspace
- raw logs preserved
- results table consistent
- annotated trace exists
- methodology artifact exists

Do not conceal missing items.

Append worklog.

STOP.

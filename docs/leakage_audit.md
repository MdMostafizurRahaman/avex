# Experimental workspace leakage audit — 2026-10-03

Rules: `config/leakage_rules.json`  
Checker: `scripts/leakage_check.py`

The checker recursively inspected each workspace for symlinks and escapes, forbidden path/name patterns, Git metadata, patch/diff artifacts, CVE/CWE identifiers, and configured research-answer markers. It does not follow symlinks. No suspicious content was deleted or changed.

## Exact commands and results

| Condition | Exact command | Files scanned | Findings | Allowlisted matches | Audit errors | Exit |
|---|---|---:|---:|---:|---:|---:|
| E1 | `python3 scripts/leakage_check.py pilot/conditions/E1 --json` | 19 | 0 | 0 | 0 | 0 (clean) |
| E2 | `python3 scripts/leakage_check.py pilot/conditions/E2 --json` | 19 | 0 | 0 | 0 | 0 (clean) |
| E3 | `python3 scripts/leakage_check.py pilot/conditions/E3 --json` | 13 | 0 | 0 | 0 | 0 (clean) |

## Findings

There were no findings in E1, E2, or E3. Specifically, the scans found no symlinks, paths resolving outside a condition, forbidden filenames or paths, Git metadata, patch/diff artifacts, CVE/CWE identifiers, or configured answer markers. No allowlist exceptions were needed for the actual condition files. Each JSON result reported `clean: true` and an empty `audit_errors` list.

## Checker tests

`python3 -m unittest discover -v` passed all 14 tests: seven condition-builder tests and seven leakage-checker tests. Checker coverage includes clean workspaces, forbidden tokens and filenames, symlink escape, nested leakage, allowlisted literal content, and JSON output with a non-zero exit on findings. `py_compile` and JSON parsing of the rules file also succeeded.

## Unresolved warnings

- **Filesystem boundary:** the condition directories are beneath the repository root, which contains sibling `private/`. An unrestricted process started in a condition can navigate upward (for example, `../../../private`). This recursive scan establishes that the condition trees contain no symlinks; it does not sandbox parent-directory access or inspect the harness's filesystem permissions. Do not start experimental agents until the execution boundary prevents access to `private/`.
- **Research validation:** clean scans do not establish E1 sufficiency, E2 initial insufficiency/retrievability, or E3 evidence unavailability. These remain **REQUIRES RESEARCHER VALIDATION**.
- **Prompt size:** the scan does not establish that the E1 initial packet fits the required context length with sufficient tool and response budget. Verify packet token usage before experiments.
- **Detection scope:** checks are driven by the configured regular expressions and filename/path rules. Binary files are skipped for content matching; files above the configured 20 MiB limit produce an audit error. The current workspaces contain 13–19 source files and produced no audit errors.

No condition content was altered because the audit found no leakage to correct.

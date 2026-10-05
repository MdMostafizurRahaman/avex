# AVEX public GitHub preparation audit

Inspected on 2026-10-05 (Asia/Dhaka). The researcher requested a public repository.
This task prepares an upload policy; it does not initialize Git, stage files,
create a remote, publish data or execute experiments.

## Organization

The existing `config/`, `data/`, `docs/`, `logs/`, `pilot/`, `private/`, `prompts/`,
`results/`, `scripts/` and `tests/` layout already matches the research workflow.
No file moves or source rewrites are needed for the initial upload. A root README
now provides a portable entry point and explains separately restored inputs.

At inspection, `private/` held 7,787 files totaling 299,546,963 bytes (about
286 MiB), including extracted snapshots and downloaded archives. All files larger
than 5 MiB were beneath that directory. The checkout had no root `.git` or
`.gitignore`, and no root README or project license.

## Upload policy

| Material | Git policy | Reason |
| --- | --- | --- |
| `private/` | Excluded | Original snapshots and researcher-only reference archive |
| `data/repopairbench/` | Excluded | Downloaded upstream benchmark, including answer-bearing metadata |
| `pilot/conditions/` | Excluded | Generated third-party source workspaces |
| `logs/` | Excluded | Raw/native runtime records and derived copies; preserve locally |
| Top-level `results/*.csv`, `*.tsv`, `*.xlsx` | Excluded | Draft experiment/scoring exports pending publication review |
| `results/manifests/` | Included | Recorded inventories, source references and SHA-256 provenance |
| Scripts, tests and test log fixtures | Included | Research implementation and fixture-based verification |
| Prompt, scenario/evidence configuration and docs | Included | Researcher-facing study protocol and audit trail |
| Figure PDF/SVG/PNG exports | Included | Small presentation artifacts |
| Credentials, caches, local environments and model weights | Excluded | Machine state and secret-bearing file classes |

No blanket `*.log`, `*.json`, `*.jsonl`, image or PDF exclusion is used: such
patterns could hide useful fixtures, manifests or publication figures. Ignored
raw logs and local datasets are not deleted. They should continue to be backed up
separately. Ignoring files does not protect already tracked files or existing Git
history; neither was present at inspection.

## Credential inspection

A path-only pattern scan inspected 264 text files outside `private/` and Python
bytecode caches, including configuration, scripts, dataset metadata and logs.
It checked private-key headers, common GitHub/AWS/OpenAI token formats and quoted
credential assignments. No matches were found. This limited scan is not proof
that every possible credential format is absent; excluded archives were not
audited for publication because they are not in the proposed upload.

## Publication decisions and portability

- Select a license for the project's own code and documentation. No license was
  invented or copied from an upstream project.
- Review the tracked scenario/evidence manifests, validation notes, worksheet,
  run summaries and worklog for public disclosure. They deliberately contain
  scenario answers, provisional interpretations and sometimes local usernames or
  paths. Excluding `private/` does not anonymize these documents or make this
  repository suitable as an agent-visible workspace.
- Project documentation navigation links and figure references use relative
  paths so they survive a folder rename and work in a GitHub clone. Historical
  execution records, quoted tool arguments and provenance still contain original
  absolute paths. Linked local logs/data are excluded from Git and must be
  restored separately. Those original records remain unchanged.
- Earlier environment/build notes and the harness-command example describe their
  original session state. Consult subsequent run summaries and the worklog for
  later execution, rather than treating those historical notes as current setup
  instructions.
- Preserve upstream attribution and verify redistribution terms before publishing
  any currently excluded benchmark data or third-party snapshot source.

Human review of research disclosure and licensing is separate from scientific
scoring. This task assigns no scientific judgments and changes no condition,
prompt, source snapshot, raw log or existing manifest.

## Verification

- Tested `.gitignore` using Git itself in a temporary repository, without
  initializing Git in this checkout: 34 representative inclusion/exclusion
  assertions passed, including preservation of fixture logs and manifests.
- The current policy includes 65 files totaling approximately 2.1 MB and excludes
  8,011 existing files. The largest included file is the 716,401-byte diagram PNG;
  no included file approaches 100 MiB. Documentation appends may slightly change
  the byte total.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` passed all
  34 tests. No model request or experimental harness was launched.
- New README relative links were checked, and an SHA-256 baseline was used to
  verify preservation of all pre-existing files except the required worklog append.


## AVEX name adoption — 2026-10-05

The researcher selected **AVEX — Agentic Vulnerability EXplanations**. The local
project directory was renamed from `evis` to `avex`; README, project instructions
and methodology now use the accepted name and explanation-focused title.
Documentation navigation links are relative, while historical execution paths
and provenance retain their recorded values. Git was initialized and files were
already staged by this task's start; no remote was configured. The rename did not
change the existing index, commit or publish anything. Reopen the `avex` folder
in the editor and re-stage updated documents before committing.

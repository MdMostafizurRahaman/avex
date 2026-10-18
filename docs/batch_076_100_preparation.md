# RepoPairBench records 76–100: snapshot handoff

This batch contains records 76 through 100 inclusive, preserving the JSONL
order. It creates one vulnerable-source condition for E1/E2 and one
target-file-omitted condition for E3 per record:

```text
076_<id>/E1_E2/  # vulnerable parent snapshot; target file present
076_<id>/E3/     # same source bytes and common exclusions; target file absent
```

The source acquisition and condition construction are separate, reproducible
steps. Researcher-only inputs and outputs belong under
`private/batch_076_100/`, which must never be exposed to an experimental
agent. The generated condition folders belong under
`pilot/conditions/batch_076_100/`.

## Preparation

Fetch the pinned dataset, then acquire the fixing commit and its first parent:

```powershell
python scripts/acquire_snapshot_archives.py `
  --dataset private/batch_076_100/upstream/repopairbench_100.jsonl `
  --archive-dir private/batch_076_100/archives `
  --start 76 --end 100
```

The acquisition script records archive URLs, commit IDs, and SHA-256 hashes.
It does not execute source code and does not create experimental workspaces.
The archive extraction step is intentionally separate:

```powershell
python scripts/prepare_snapshot_batch.py `
  --dataset private/batch_076_100/upstream/repopairbench_100.jsonl `
  --archive-dir private/batch_076_100/archives `
  --output-dir private/batch_076_100/snapshots `
  --start 76 --end 100
```

After researcher review supplies a condition plan (including any approved
common exclusions), build physical, symlink-free workspaces:

```powershell
python scripts/build_snapshot_conditions.py `
  --plan private/batch_076_100/condition_build_plan.json `
  --repo-root private/batch_076_100/snapshots `
  --destination pilot/conditions/batch_076_100 `
  --report private/batch_076_100/condition_build_report.json
```

The mechanical plan generator used for this batch is:

```powershell
python scripts/create_snapshot_condition_plan.py `
  --report private/batch_076_100/snapshots/prepare_snapshot_batch_report.json `
  --rules config/leakage_rules.json `
  --snapshots-root private/batch_076_100/snapshots `
  --output private/batch_076_100/condition_build_plan.json
```

The plan must never exclude the target file from E1/E2. E3 adds exactly that
target-file omission. No patched tree is copied into a condition. Run
`scripts/leakage_check.py` against every condition before any experiment.

## Validation boundary

The scripts mechanically verify paths, archive traversal, regular-file
hashes, target-file presence in the vulnerable snapshot, and target-file
absence in E3. They do **not** decide whether E1 is sufficient, E2 is
retrievable, or E3 is scientifically unresolvable. Those conclusions require
researcher validation for every record. No model runs are part of this
preparation task.

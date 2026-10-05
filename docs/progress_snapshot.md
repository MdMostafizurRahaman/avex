# AVEX progress and future tasks — presentation snapshot

Verified 2026-10-05. Researcher-facing presentation preparation; no new experimental stage executed.

## 16. Progress: what has been completed

Presentation message:

> We have implemented the evidence-control pipeline and executed the six-cell pilot. We now have preserved source conditions, execution traces, normalized records and a human scoring worksheet. The next step is scientific evaluation of those records, followed by a larger study if authorized.

| Workstream | Verified progress | Qualification |
| --- | --- | --- |
| Research design | RepoPairBench, two harnesses, fixed model/context and E1/E2/E3 design documented | Broader model comparisons have not been run |
| Scenario selection | Four candidates documented; human selected iRedAdmin scenario `24e78349` | One purposefully selected case |
| Reference preparation | Vulnerable/fixed snapshots inspected; target, patch, dependencies, alternative evidence and scope documented | Human-approved source-level interpretation, not browser/deployment exploit validation |
| Evidence construction | Exact manifest approved; E1/E2/E3 copies and SHA-256 inventories created | Stable bytes do not prove scientific sufficiency |
| Safety controls | Leakage checker, tool restrictions and macOS confinement implemented; execution-boundary probes recorded | Final reproducibility re-audit remains to be performed |
| Execution | Qwen Code and OpenCode each executed E1/E2/E3 with the same 9B model and configured 16K context | Stack operational in recorded execution; current service availability was not checked |
| Attempt preservation | Eight process attempts retained for six experimental cells | Two infrastructure retry histories are preserved, not independent replications |
| Normalization | Six draft cell rows and eight attempt rows; raw/normalized separation and observable event extraction | Parsed verdicts and counts are mechanical records |
| Evaluation preparation | Trace-linked human scoring worksheet and separate provisional suggestions created | All seven human-review fields remain blank in the six-row draft |
| Presentation preparation | Methodology, architecture and DREA-style figures; detailed speaker guide | Annotated trace and final presentation/audit package are pending |
| Engineering verification | Most recent recorded full unit suite passed 34 tests | Historical check, not rerun for this documentation task |

The six selected normalized records and their final-text files were checked during this task and are present. This does not establish that every final response answered the task correctly or expressed a parseable verdict.

Use this distinction in your talk:

> Execution and evaluation are different milestones. We have collected the pilot observations; we have not yet completed their human scientific scoring.

Avoid a percentage-complete claim. Task counts do not measure remaining research uncertainty.

## 17. Immediate tasks: evaluate and package the existing pilot

| Task | What to do | Why it matters | Expected output |
| --- | --- | --- | --- |
| Review realized conditions | Recheck E1 sufficiency, E2 initial gap/retrievability and E3 omission boundary, including alternative evidence | The intended treatment must match the constructed materials | Human condition-validity record |
| Finalize scoring conventions | Approve definitions, YES/NO/UNCLEAR/N/A applicability and the distinction between label and mechanism | Prevent inconsistent judgments across conditions | Explicit human scoring rubric |
| Review attempt inclusion | Confirm handling of startup failure, sleep-overlapping attempt and retries independent of answer quality | Avoid selecting desirable results | Accepted attempt-selection rationale with all attempts retained |
| Score six pilot cases | Inspect initial packets, returned source and final claims; enter separate judgments with citations | Turn raw observations into defensible findings | Human-reviewed results and notes |
| Prepare one annotated trace | Choose an illustrative E2 or E3 investigation and annotate only observable stages | Show the method concretely without inventing reasoning | `docs/annotated_trace.md` |
| Complete final reproducibility audit | Recheck provenance, source/prompt hashes, model/context records, isolation, logs, normalization and tests | Verify the presented materials correspond to preserved execution | Final audit and presentation package |
| Write bounded pilot findings | Explain observed recognition, acquisition, uncertainty and grounding with trace support | Separate findings from impressions or rankings | Descriptive pilot analysis and presentation claims |

Reference approval and exact construction-plan approval already exist; do not present these as entirely unperformed. The remaining validity review concerns realized materials and run-level interpretation.

These tasks are a roadmap, not authorization to execute Sessions 9/10 or start new experiments. This presentation request creates only progress/preparation documentation.

## 18. Future study extensions: proposed, not executed

1. **Additional human-selected scenarios.** Include varied source dependencies and vulnerability mechanisms that admit a valid evidence manipulation. Each case needs its own reference, alternative-evidence audit and condition review. This tests whether observed behavior extends beyond one iRedAdmin path.
2. **A second, stronger model.** Select a feasible model and exact configuration through explicit approval. A 30B/80B model is a candidate direction discussed by the researcher, not a frozen selection or a guaranteed improvement. Keep comparable conditions and record the model/quantization/runtime settings.
3. **Planned repetitions.** Repeat every cell under a predeclared sampling design, retaining all outcomes. This estimates variability; it is not rerunning incorrect pilot answers until they improve.
4. **Stronger human-evaluation reliability.** Consider independent evaluators, a written rubric, disagreement resolution and agreement measurement. Blinding and avoiding Codex suggestions during initial review can reduce anchoring where feasible; these have not yet been implemented.
5. **Quantitative analysis after validation.** Measure recognition, retrieval, abstention, grounding and unsupported claims separately, with condition-appropriate denominators and uncertainty estimates supported by the expanded sample. Runtime/tool counts remain secondary process measures.
6. **Resource and execution planning.** Check feasible hardware, model inference cost, storage, run duration and stable execution before expanding. Pilot sleep and timing discrepancies make simple extrapolation unreliable.

The session plan's illustrative future design is:

`2 harnesses × 2 models × 3 conditions × N scenarios × R repetitions = 12NR runs`

The exact models, scenario count, repetition count, analysis plan and resources remain to be decided. No expanded run budget is committed by this formula.

The desired future result is a better-supported account of when explanations use sufficient evidence, when acquisition fails, and when agents appropriately acknowledge uncertainty. Broad harness or model comparisons require adequate scope and replication.

Speaker text:

> Our immediate priority is to complete human scoring and a reproducibility audit of the current pilot, then present an annotated investigation showing how evidence was obtained and used. After that, we propose adding more scenarios, a stronger second model and planned repetitions. These extensions will test how consistent the behavior is and whether it generalizes. We will preserve incorrect outcomes and infrastructure histories rather than repeat runs to obtain preferred answers.


Sources: [Methodology](methodology.md), [worklog](CODEX_WORKLOG.md), [session plan](../SESSIONS.md), [scoring worksheet](pilot_scoring_worksheet.md).

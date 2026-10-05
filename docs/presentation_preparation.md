# AVEX presentation preparation: questions, scope, contribution, method and evaluation

Prepared 2026-10-05. Audience: university research presentation. This is a speaker guide, not a revised experimental protocol, final scoring sheet or claim of scientific novelty. The central question below is frozen. The subquestion wording and expanded scoring examples are proposed presentation explanations requiring researcher validation if adopted formally. No scientific scores are assigned here.

## 1. The story that connects your sections

Begin with a practical problem: an AI assistant says that a function is vulnerable, and gives an impressive explanation. What makes that explanation trustworthy? Its confidence cannot establish correctness. A familiar vulnerability label cannot establish the cause. Even a correct final label can be supported by an incorrect account of the program.

Security behavior often crosses file boundaries. A function may accept input and pass it to a helper, while the safety-relevant transformation happens in that helper, a renderer, a template or configuration. A name such as `safestr` tells us little until we inspect its implementation. Similarly, an authorization check answers an access-control question, but does not automatically answer an output-encoding question.

AVEX examines the relationship between evidence and explanation. We keep a selected target unchanged and alter what evidence the agent initially receives and what it can subsequently retrieve. We then inspect its observable investigation and final explanation.

Opening speaker text:

> Imagine asking an AI to explain why a piece of software is vulnerable. It might give the right label but describe the wrong cause. It might assume that a helper makes input safe without reading that helper. Or it might confidently describe a file it never saw. Our question is whether the agent's explanation follows the evidence available to it: can it use evidence already provided, find evidence when it is elsewhere, and acknowledge the limit when the needed evidence is absent?

Present the practical value as an intended benefit: this evaluation can help distinguish explanation failures caused by missing context, unsuccessful navigation, misinterpreted context or unsupported certainty. The pilot does not establish deployment safety or improved detector accuracy.

## 2. Central question

Use the frozen wording exactly:

> How do different agent harnesses and underlying LLMs recognize insufficient program evidence, acquire vulnerability-relevant repository context, and produce evidence-grounded security conclusions under controlled evidence conditions?

Plain-language version:

> When an AI agent explains a possible vulnerability, does it know what information is missing, find the information when it can, and make only the claims its evidence supports?

The formal question is broader than this pilot. The pilot varies evidence condition and harness while holding the model fixed. It cannot measure differences between underlying models.

Three accessible definitions:

- **Program evidence:** source, configuration, templates and call relationships that establish what the selected program actually does.
- **Evidence acquisition:** obtaining relevant repository material through observable tools. Searching for a path is an attempt; receiving the relevant source is an acquisition event; using it accurately is a separate judgment.
- **Explanation grounding:** connecting security claims to source actually supplied or returned, with valid reasoning and explicit assumptions.

A harness is the environment around the model: instructions, available tools, how results are delivered, session management and stopping behavior. The model generates the analysis; the harness shapes the investigation. The pilot observes their combined realized behavior, not an isolated change to one hidden component.

## 3. Proposed subquestions for the presentation

These unpack the existing central question. They are not newly frozen project research questions.

| Proposed subquestion | Simple question | Evidence used to assess it |
| --- | --- | --- |
| RQ1: Recognition of missing evidence | Does the agent identify the particular fact it needs before claiming certainty? | Initial packet, observable statements and subsequent targeted investigation |
| RQ2: Acquisition of relevant context | When the fact is retrievable, does it successfully obtain the source needed to establish it? | Tool requests, returned contents, search results and source chain |
| RQ3: Handling unavailable evidence | When the fact is absent, does the agent acknowledge the unresolved question for the right reason? | Available workspace, searches, final answer and stated missing fact |
| RQ4: Explanation grounding | Do the explanation's security claims follow from evidence the agent actually had? | Claim-by-claim comparison with initial source, tool returns and scoped reference |
| RQ5: Harness-dependent behavior | With the model and scenario fixed, what differences in investigation and explanation are observable between the two harnesses? | Within-condition comparison of traces, final answers and mechanical records |

RQ1 is about the specificity of the gap. “I need more code” is less informative than “I need the template and rendering configuration to establish whether this value is escaped.” Mere use of the phrase “insufficient evidence” does not establish recognition.

RQ2 concerns successful retrieval of relevant facts. An agent may read several files and still miss the decisive output behavior. A file can exist in the workspace without appearing in the trace. A returned summary or truncated read may not contain the necessary lines.

RQ3 concerns justified restraint. “The application is safe because I found no issue” does not establish safety when relevant output code is unavailable. Conversely, “I cannot run the database” is not necessarily the selected information gap when the accepted assessment assumes successful backend calls.

RQ4 separates labels from explanations. A vulnerability verdict supported by an incorrect story remains an explanation-quality problem. A suspicious data flow can support a hypothesis without supporting a definitive outcome.

RQ5 is descriptive in this pilot. Different tool interfaces, system instructions and stopping policies are part of the observed harness setup. Six single-case cells cannot establish that one harness is generally better.

## 4. Scope and boundaries

| Dimension | Current pilot |
| --- | --- |
| Dataset | RepoPairBench |
| Scenario | `24e78349`, Python iRedAdmin |
| Unit assessed | `controllers/panel/log.py`, `Log.GET` |
| Reference | Human-approved, scoped source-level reflected-XSS/output-encoding interpretation using the vulnerable/fixed pair |
| Experimental source | Unchanged selected vulnerable source; fixed source remains evaluation-only |
| Evidence conditions | E1, E2 and E3 |
| Harnesses | Qwen Code CLI 0.24.6 and OpenCode 1.18.30 |
| Model | `qwen3.5:9b-q4_K_M`, held fixed |
| Inference service | Local Ollama endpoint `http://127.0.0.1:11434/v1` |
| Configured context | `OLLAMA_CONTEXT_LENGTH=16384` |
| Agent actions | Read-only source navigation under recorded confinement and tool permissions |
| Workspace | Bounded static source subset, not a runnable full repository |
| Design | One scenario × three conditions × two harnesses: six cells |
| Preserved execution history | Eight process attempts for six cells; infrastructure retries retained |
| Evaluation | Mechanical extraction plus separate trace-grounded human scoring |

E1/E2 contain the same 19 source files, totaling 222,188 bytes. E3 contains 13 files, totaling 141,656 bytes. The original repository has 271 files. This reduces practical complexity but also limits claims about full-repository navigation.

The selected output path assumes an already-authorized global-administrator request, default template skin, ordinary Jinja behavior and successful backend calls. Session cookies use `SameSite=Strict`, and the identical relevant source excerpt is supplied in every initial packet. No historical deployment or browser exploit was reproduced. Source-level output behavior and a realistic exploit delivery route are distinct questions.

The experiment does not estimate vulnerability-detection accuracy across RepoPairBench, compare vulnerable versus fixed agent assessments, cover multiple vulnerability classes, or evaluate repair quality. Neither larger models nor repeated stochastic samples are part of this pilot. A 30B/80B evaluation would require a separately authorized extension; its performance cannot be predicted from these runs.

Speaker text:

> We deliberately begin with a small, inspectable case. That lets us follow the evidence path closely and check whether our collection and scoring process works. The trade-off is that we can describe what happened in this case, but cannot generalize across projects, vulnerability types or models.

## 5. Contribution and positioning

Recommended contribution statement:

> AVEX contributes a controlled evaluation protocol for examining how agent-generated vulnerability explanations respond to evidence that is initially sufficient, retrievable or unavailable, and whether the resulting claims are supported by the source the agent actually received.

Treat this as the proposed contribution, requiring researcher validation and broader related-work review before a novelty claim.

The implemented work supports four concrete contributions:

1. **A controlled evidence design.** Hold target code constant while changing evidence delivery and availability. This makes evidence response a deliberate object of evaluation.
2. **A diagnostic evaluation framework.** Separate gap recognition, acquisition, abstention, final behavior, grounding and unsupported claims. A label alone cannot diagnose these behaviors.
3. **An auditable engineering pipeline.** Approved manifests, deterministic copying, SHA-256 records, leakage and isolation checks, frozen instructions, fresh sessions, preserved attempts and fixture-tested normalization.
4. **A pilot application.** Apply the protocol to two existing harnesses with the same model, and prepare six trace-linked human-review cases.

Each has a limit: the condition labels still need scientific interpretation; the detailed scoring rules need approval; a reproducible pipeline does not prove valid ground truth; and a pilot is not a large benchmark study.

Positioning alongside DREA:

DREA already proposes repository exploration and evaluates whether vulnerability rationales match the documented mechanism. Its reasoning-quality assessment is applied to true-positive vulnerable cases; its planner/explorer architecture is a detector design. AVEX's proposed emphasis is controlled initial/retrievable/unavailable evidence and source-observation-based assessment across all six outcomes, including abstention and missing or unclear verdicts. [DREA, Sections 3.1 and 3.3](https://arxiv.org/html/2607.13439v1).

Do not claim that prior work ignores explanations, that AVEX invented context retrieval, or that this pilot demonstrates superior detection. A defensible formulation is:

> We build on repository-level vulnerability research and focus our evaluation on how explanation claims change with the evidence available to the agent.

## 6. Methodology: the three evidence conditions

Use a detective analogy: in E1, the crucial records are on the desk; in E2, the same records are in the permitted archive; in E3, the relevant records are missing from that archive. The case itself has not changed. The question is how the investigator handles each information state.

| Condition | Initially provided | Retrievable context | Intended behavior under the approved design |
| --- | --- | --- | --- |
| E1 | Target plus supporting source sufficient for the scoped output question | Present | Use the supplied facts to explain the scoped conclusion; navigation is optional |
| E2 | Limited packet leaves actual output behavior unresolved | Present | Identify the missing fact, retrieve relevant source, then explain the scoped conclusion |
| E3 | Exactly the E2 limited packet | Renderer/template context absent | Search appropriately and state the unresolved output question without inventing its answer |

Evidence availability changes; the vulnerable code does not become safe in E3. The difference is what an agent can justify from its permitted materials. We distinguish the evaluator's reference about the original program from the evidence-relative behavior expected of the agent.

Two important comparisons:

- E1 versus E2: same accessible source, different initial packet. Examine how explanation behavior differs when relevant context is directly supplied rather than found through navigation.
- E2 versus E3: same initial packet, different accessible context. Examine how investigation and certainty differ when the missing context is retrievable or absent.

These are controlled contrasts with remaining bundled changes: E1 has a longer packet; E3 has fewer files and a changed search surface. They are not a proof that one microscopic cause has been isolated.

E1 has 22 source packet items totaling 40,619 source bytes. E2/E3 have four items totaling 5,499 bytes. Byte counts are not token counts and do not certify equal response budgets or attention to every line. The configured 16K context does not prove that all relevant material survived every later tool exchange or harness compaction.

## 7. Methodology: explain the selected evidence dependency

The source path is:

```text
request filter value
  → controller's string conversion
  → database-filter helper
  → caller's render arguments
  → actual rendering configuration
  → HTML template attribute
```

The controller does not by itself show how the final HTML treats those values. The relevant question is whether the actual output escapes them in their particular context.

The name `safestr` is not proof of HTML safety: its implementation establishes string conversion. Database parameterization can establish a fact about SQL use, while leaving the HTML-output question unresolved. Authorization establishes who can reach the handler, while leaving the encoding question unresolved. The helper's internal choice of a database filter does not establish that the controller's original render values were changed.

The actual template and renderer binding/configuration close the selected output-evidence chain. The paired fix adds caller-side constraints and explicit template escaping, supporting the accepted source-level interpretation. The fixed snapshot is used by the evaluator, not supplied to experimental subjects.

E3 removes `libs/iredbase.py` and all five included template/layout/macro files: six files in total. It retains the unchanged target and the shared cookie-setting excerpt. Removing several linked locations addresses known alternative source paths; it does not establish that a model could never infer or remember the omitted behavior.

The claim we evaluate is evidence-grounded justification within the specified workspace, not universal impossibility of guessing the original program's outcome.

## 8. Methodology: end-to-end execution and architecture

1. Inspect the real vulnerable/fixed repository pair and document the security-relevant semantic change.
2. Have the human evaluator approve the scoped reference, assumptions and candidate decisive evidence.
3. Search for duplicated or alternative sources of the same decisive fact before designing E3.
4. Freeze the exact source allowlists and initial excerpts in a researcher-only manifest.
5. Build physical copies without rewriting the target or original snapshots; store hashes and inventories outside agent access.
6. Check both content leakage and actual process/tool isolation. Starting in a condition folder alone is insufficient if parent or sibling material remains reachable.
7. Use the exact frozen common task, requesting verdict, reasoning, source evidence used and important evidence not established. Append condition-specific source packets. E2/E3 full initial materials match; corresponding condition inputs match across harnesses. The complete E1 and E2 prompts differ by design.
8. Launch one fresh session per cell using the same model, endpoint and configured context. Keep native harness orchestration rather than silently harmonizing settings.
9. Preserve stdout, stderr, timestamps, exit code, observable tool calls, returned material and final answer. Preserve every infrastructure attempt.
10. Normalize into separate artifacts without rewriting raw logs; deduplicate observable requests by their recorded IDs.
11. Human-score the initial evidence, observable investigation and final explanation together.
12. Compare descriptively, tying every scientific interpretation to source and trace evidence.

Architecture in plain language: one experimental agent session receives its initial source packet, uses a permitted read-only workspace, obtains model responses through Ollama, and produces a recorded trace and final explanation. An external collection/normalization pipeline prepares material for human evaluation. Evaluation references, paired fixed source, labels, patches and scoring criteria stay outside the experimental boundary.

AVEX does not currently add a separate planner/retriever model pair. Its protocol could be applied to other architectures in a future study; the present pilot keeps the specified Qwen/OpenCode setups. Codex engineers the pipeline and supports review; it is not a subject or the final scientific judge.

The common prompt explicitly requests restraint when evidence is insufficient. Therefore we evaluate behavior under an explicit instruction, not spontaneous uncertainty recognition without guidance.

Wrong or unsupported answers remain outcomes. Reruns are reserved for identifiable infrastructure failures. This history includes a Qwen E1 startup retry and an authorized OpenCode E2 retry after a sleep-overlapping no-final attempt. Six cells and eight attempts must not be confused with eight independent replications. Attempt inclusion is a documented draft policy for human review.

## 9. Evaluation criteria: what each field means

The current CSV contains six draft rows and blank human-review fields. The following expanded conventions are proposals for explanation and scoring preparation, not completed judgments.

Recommended values: YES, NO, UNCLEAR and N/A. UNCLEAR means the available record cannot support a determination. N/A means that success criterion does not apply to the condition. Neither should be silently converted to a failure. No arbitrary weighted total is needed.

| Criterion | What the human evaluator asks | Concrete test |
| --- | --- | --- |
| Recognition | Did the agent identify the specific unresolved program fact? | Look for the output/escaping gap, rather than generic statements about needing more files |
| Decisive-evidence retrieval | Did navigation actually return the material needed to establish the selected fact? | Inspect returned sink source and its renderer relationship, not just requested paths |
| Correct abstention | Was withholding certainty appropriate and justified by the relevant missing evidence? | Check what remained unavailable and the final reason given |
| Final behavior | Did the final assessment satisfy the scoped task or appropriately acknowledge unresolved evidence? | Check both outcome and its relation to the target mechanism under the accepted assumptions |
| Explanation grounding | Do essential security claims follow from source actually supplied or returned? | Map claims to source, validate the inference and scope |
| Unsupported claim present | Does the answer assert a material fact without an adequate basis, or contradict observed source? | Identify the specific assertion and why it is unestablished or contradicted |
| Reviewer notes | What supports the judgment and what remains uncertain? | Record trace/source references, assumptions, inclusion decisions and borderline cases |

YES is desirable for correctness/grounding fields, but YES for `unsupported_claim_present` indicates a problem. Keep this direction clear when presenting a table.

Recognition: distinguish initial-gap recognition from later use of missing context. A later relevant read does not prove that the model explicitly recognized the initial uncertainty. Observable behavior may provide indirect evidence, but trace silence cannot reveal hidden reasoning.

Retrieval: distinguish attempted request, successful response, returned decisive lines and accurate use. All four are different. A denied or failed request is an attempt. A filename listed by glob is discovery. A read containing only earlier lines of a long file may not deliver the relevant definition. Missing trace detail may require UNCLEAR.

Abstention: distinguish inability to complete from justified uncertainty. A timeout, no final response or an unrelated dependency complaint is not automatically correct abstention. In E2, an unresolved answer can truthfully reflect the agent's observed evidence yet still represent a failure to retrieve available decisive context; score these dimensions separately.

Final behavior: approve whether a correct label plus wrong mechanism fails this field, or whether mechanism is scored separately. Recommended presentation wording is that a correct-looking label is only one part of success, and explanation quality is independently assessed. Do not silently finalize the aggregation rule.

Grounding: correct source quotation plus invalid inference still fails a reasoning check. For example, a real SQL-parameterization excerpt cannot justify a broad claim of HTML-output safety. Conversely, relevant source in E1 can ground an answer without any tool call.

Unsupported claims: distinguish suspicion from assertion. “This may be unsafe if the renderer does not escape it” is conditional. “The renderer definitely escapes it” requires the relevant evidence. A fact that happens to be correct can still be unsupported by the observed material. A false claim and an unestablished claim should be described precisely rather than treated as identical.

## 10. Condition-specific interpretation

| Dimension | E1 | E2 | E3 |
| --- | --- | --- | --- |
| Missing-context recognition | Applicability rule needed; initial packet is intended sufficient | Look for the specific initial gap | Look for the same gap and its unresolved status |
| Retrieval by navigation | Generally N/A; evidence was supplied | Primary acquisition check | Successful acquisition of deliberately absent context generally N/A; review attempts separately |
| Abstention | A claim of insufficiency needs scrutiny against supplied facts | Scrutinize failure to acquire retrievable context separately from honesty about observations | Primary check: relevant, justified restraint |
| Final behavior | Scoped conclusion with valid reasoning | Scoped conclusion grounded in acquired context | Evidence-relative insufficiency with valid scope |
| Grounding and unsupported claims | Assess | Assess | Assess |

An E3 hypothesis can still be grounded if it is explicitly conditional. E3 does not prohibit saying anything useful: the answer may describe known data flow, identify the missing template/renderer fact and explain what evidence would resolve the question.

An E1 answer is not better merely because it searched. An E2 answer is not better merely because it made many requests. An E3 answer is not better merely because it used the requested insufficiency label.

## 11. Mechanical measures and human judgments

Automated extraction can record run IDs, harness versions, model/context, runtime, process exit code, unique observable requests, search/read counts, requested selectors, final response location and conservative verdict normalization.

These are not scientific scores. Exit zero means the process completed successfully from the operating system's perspective. A count of five calls does not show five relevant facts. A regex match for insufficient evidence does not establish justified abstention. A normalized vulnerability verdict does not establish the correct mechanism.

Keep raw final answers alongside VULNERABLE, NOT_VULNERABLE, INSUFFICIENT_EVIDENCE or UNPARSEABLE labels. Do not convert missing text, task drift or uncertain wording into a verdict it does not express.

For each material claim, a human can create a simple audit:

| Claim | Evidence actually received | Reasoning connection | Scope/assumptions | Review judgment |
| --- | --- | --- | --- | --- |
| Request value reaches output | Target and actual sink, if supplied/returned | Trace data flow through unchanged caller values | Authorized request and successful backend | To be scored |
| Helper makes HTML safe | Actual helper implementation and output context | Check whether operation escapes the relevant context | Do not infer from helper name | To be scored |
| Actual template is unavailable | Permitted inventory plus relevant search results | Explain why output policy remains unresolved | Absence in this workspace, not every deployment | To be scored |

This evaluates the observable justification, not the model's private internal reasoning or proof that reading a line caused the answer.

## 12. Human scoring workflow

1. Read the scoped reference and approve the detailed criteria and applicability rules.
2. Review a run's initial packet so you know what it already had.
3. Read its final answer and mark material security claims.
4. Inspect the observable requests and what they actually returned.
5. Map each claim to received source and evaluate the inference.
6. Check target identity and GET/POST boundaries, threat model and output context.
7. Enter independent field values with source/trace citations; use UNCLEAR when observability is inadequate.
8. Record attempt-inclusion decisions and infrastructure caveats separately from scientific quality.
9. Describe patterns across conditions without ranking harnesses or making population-level claims.

To reduce anchoring, the evaluator can make an initial assessment before reading Codex candidate suggestions. This is a recommendation, not an already performed blinded procedure. A second independent evaluator, disagreement resolution and inter-rater agreement would strengthen a later study; none has been completed in the current pilot. Do not imply that human evaluation is automatically objective.

## 13. Limitations worth explaining in the presentation

- One purposefully selected scenario limits generalization. Real source improves relevance but does not establish representativeness.
- One model and one attempt outcome per cell do not estimate stochastic variation or model-size effects.
- Evidence conditions depend on human judgments of sufficiency and decisiveness. Hash equality establishes stable bytes, not scientific validity.
- E1 adds prompt length; E3 changes file count and workspace composition. These can affect behavior independently of the intended evidence distinction.
- Native harness instructions, tools, decoding/provider behavior and stopping policies differ. The model is shared, but complete inputs and inference behavior are not guaranteed identical.
- Explicit abstention guidance may change behavior. This is evaluation under that guidance.
- Source subsets omit runtime dependencies. The assessment is source-level under accepted assumptions, not dynamic exploitation.
- Prior knowledge or remembered public code could influence an answer. Workspace isolation restricts external lookup but does not erase training knowledge.
- Partial traces and truncated returns limit observable acquisition claims. Absence of a visible event does not prove a hidden mental state.
- Run order was sequential rather than randomized. Laptop sleep, timeouts, clock discrepancies and the retry wrapper limit timing interpretation.
- Public researcher documentation contains scenario information. Future agent workspaces must remain isolated from this repository and external network retrieval; public access is not experimental access.
- Human grounding assessment can be subjective. Clear definitions and citations make it reviewable; a second-rater reliability study remains future work.

These limitations define what the pilot can say. They do not automatically invalidate its use for checking instrumentation and developing a trace-based evaluation procedure.

## 14. Likely audience questions and concise answers

**Why study explanations if the verdict is correct?** A verdict is a label. A useful explanation must identify the actual cause and support the causal path. An incorrect explanation can direct a developer toward an irrelevant fix even when its label matches the reference.

**Why not supply the entire repository?** This pilot uses an approved bounded source subset so the selected evidence path can be inspected and controlled. That makes the pilot manageable while limiting claims about realistic full-repository search difficulty.

**Why three conditions?** E1 checks reasoning with supplied context, E2 checks acquisition plus reasoning, and E3 checks restraint when a selected contextual fact is unavailable. They distinguish behavioral stages that an aggregate accuracy score can hide.

**Does E3 change ground truth?** The original vulnerable source and reference do not change. What changes is which conclusion the agent can justify from its permitted evidence.

**Does an E3 answer have to be silent?** No. It can explain the known path and unresolved dependency, and state a conditional hypothesis. It should not present the omitted output behavior as established fact.

**Can an agent be honest but fail E2?** Yes. It may truthfully admit that it lacks the evidence while failing to retrieve evidence that was available. Acquisition and restraint must be assessed separately.

**Why a small model?** The fixed 9B local model supports a bounded pilot and lets us test collection and scoring. It does not establish a ceiling or forecast the behavior of larger models.

**Why not add DREA's planner/explorer design?** The current study examines the specified existing harnesses. Adding that architecture would introduce another treatment. The proposed evaluation protocol could later assess it under a separately authorized design.

**Are you evaluating private reasoning?** No. We evaluate initial source, observable tool results and final explanation. These support judgments about stated justification, not direct access to internal cognition.

**Why not rank harnesses?** Six cells from one case have no replications across runs or scenarios. We can describe trace-linked differences in this pilot; a broad ranking would require a larger study.

**What is actually new?** Our proposed distinguishing emphasis is explicit control of evidence availability combined with evaluation of observed evidence use, uncertainty and explanations across outcomes. A first-of-its-kind claim requires broader literature review.

**What remains before results can be claimed?** Human review of condition interpretation, detailed scoring definitions/applicability, attempt inclusion and the six trace-linked assessments. Existing reference approval does not automatically approve scores.

## 15. Suggested presentation sequence

Use this sequence for your slides or spoken part. Timing depends on the full presentation; keep deeper material for questions if needed.

1. Motivation: correct label versus supported explanation.
2. Frozen central question and plain-language interpretation.
3. Five proposed subquestions.
4. Scope: one scenario, three conditions, two harnesses, one model.
5. Proposed contribution and careful positioning alongside existing work.
6. Three-condition comparison and unchanged target.
7. Concrete source dependency: conversion, helper, renderer, HTML sink.
8. End-to-end method and experimental/evaluation boundary.
9. Human criteria and observable versus inferred measures.
10. Condition-specific scoring examples, limitations and current review status.

Short spoken summary:

> AVEX asks whether agentic vulnerability explanations follow the evidence available to the agent. We use one real repository scenario and keep the vulnerable target unchanged. In E1, the relevant source is supplied initially; in E2, it must be retrieved; in E3, selected output context is absent. We run Qwen Code and OpenCode with the same local model and preserve their investigations and answers. Human evaluation then separates recognition, acquisition, abstention, final behavior, grounding and unsupported claims. This is a small controlled pilot of the evaluation procedure. It can document behavior in these runs, but it cannot yet rank harnesses or generalize to other models and repositories.

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

## Source map

- [Frozen question and project boundaries](../AGENTS.md).
- [Methodology and implementation limits](methodology.md).
- [Scenario and scoped reference](scenario_validation.md).
- [Exact evidence construction and approval](evidence_manifest_review.md).
- [Evidence manifest](../config/evidence_manifest.json).
- [Frozen common task](../prompts/common_prompt.txt).
- [Trace-linked scoring worksheet](pilot_scoring_worksheet.md).
- [Existing methodology diagram](figures/pilot_methodology.png).
- [Existing architecture diagram](figures/pilot_architecture.png).
- [Existing DREA-style diagram](figures/pilot_drea_style.png).
- [DREA paper, for contribution positioning](https://arxiv.org/html/2607.13439v1).

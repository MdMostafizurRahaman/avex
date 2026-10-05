# Session 2 — RepoPairBench candidate shortlist

Researcher-facing material. **Do not copy this report, its path inventories, or anything under `private/` into experimental workspaces.** No scenario is selected. All vulnerability interpretations, “decisive” evidence proposals, and E1/E2/E3 sufficiency judgments below are **REQUIRES RESEARCHER VALIDATION**. Confidence describes engineering plausibility, not certified ground truth.

## Scope and provenance

Inspected all 100 local metadata/function-pair records (all language tags are `python`), then reconstructed seven potentially relevant upstream commit pairs and inspected their source. Four remain on this provisional shortlist; the three exclusions are explained below. This is a targeted screening, not an exhaustive scientific review of all 100 source repositories. The list order is identifier order, not a ranking. Fewer than five are retained to avoid padding with poorly grounded candidates.

Local dataset: `data/repopairbench/repopairbench_100.jsonl` and `repopairbench_100_manifest.json`. SHA-256 respectively:

- `b228fd6514b82291b59ee0156070f1d704cf37079932a9b6583049e9d0317dc0`
- `fd260a0f772331598ec934c8a69cfc2e36e68151c47df39f5c1789a6cebb1650`

The supplied [dataset schema](https://github.com/huhusmang/DREA/blob/main/data/DATASET.md) identifies `commit_hash` as the fixing commit and does not vendor repository context. The linked [pair builder](https://github.com/huhusmang/DREA/blob/main/data/scripts/build_paired_dataset.py) uses the fixing commit's first parent as the vulnerable tree; the [clone helper](https://github.com/huhusmang/DREA/blob/main/data/scripts/clone_repos.sh) identifies upstream repositories. These instructions were read, not executed wholesale: the builder can delete an existing destination, and the clone helper fetches more projects/history than this task needs.

Instead, GitHub commit responses resolved exact first-parent hashes, and commit-addressed codeload archives were saved only under `private/original_snapshots/session2/<id>/`. Every extracted regular source file is a physical copy; archive links were recorded but never materialized. The original archives preserve those links. Kiwi has five omitted asset links per tree; none is target Python source. Thus these are regular-file source snapshots, not complete runnable checkouts. No upstream code was executed or dependencies installed. Each before/after target matches the supplied dataset function after whitespace normalization; this is a containment check, not byte identity or vulnerability validation.

Each pair's `acquisition.json` records source URLs, timestamps, full hashes, archive SHA-256/size, file counts, skipped links and target-match results. `source_file_hashes.json` records per-file SHA-256. Acquisition snippets are retained as `acquire_initial.py` and `acquire_replacements.py` under the same researcher-only directory; they are one-shot session records, not reusable condition builders. They reject traversal, never create links, use exclusive file creation, and refuse existing pair directories. API responses include fix messages/patches and are especially sensitive leakage material.

## Compact comparison

| ID / project | Candidate context dependency | Vulnerable tree size | Engineering convenience | Principal validity obstacle |
|---|---|---|---|---|
| 24e78349 / iRedAdmin | `safestr`, custom renderer, HTML template | 271 files / 4.84 MiB | Cleanest cross-file omission boundary | Admin reachability and Jinja semantics must be validated |
| 7c167feb / Kiwi TCMS | Diff storage and admin HTML consumer | 752 files / 6.56 MiB | Compact data-flow chain | Consumer shares the target file; alternate displays exist |
| d2b7d775 / Piccolo | Local password hashing and iterations | 505 files / 1.73 MiB | Small source footprint | Target already strongly suggests a timing discrepancy |
| ee76e0c9 / OctoPrint | Role registration and permission need aggregation | 875 files / 19.41 MiB | Fully local permission machinery | Several dependencies; target role names already suggest the issue |

Sizes count extracted regular files and their logical bytes, excluding archives, Git history, and links; these are measured source sizes, not RAM/runtime estimates. All four are modest for read-only navigation on a MacBook Air M2, but no harness throughput was measured. iRedAdmin appears easiest to operationalize **for engineering convenience only**, followed by Kiwi if excerpt-based workspaces are acceptable. This does not establish scientific suitability or select the final scenario.

## Construction rules applying to every proposal

E1/E2/E3 below are proposals only; no condition files were built. Keep the vulnerable target function unchanged in all three. Use identical assessment wording and target-relative path across conditions; initial source evidence differs by design, not expected-verdict instructions. E1 supplies authentic relevant source up front; E2 makes the same evidence navigable; E3 omits it physically. Do not put researcher descriptions, labels, fixed source, patches, release advisories, `.git`, acquisition files, or reports in agent-accessible copies. The pilot remains one scenario × three conditions × two harnesses; these are options, not an expanded experiment.

An excerpt-based workspace means copying exact selected original source units, with recorded boundaries, while omitting other units; it does not mean changing the target or inventing dependency implementations. This departure from a whole-file/full-repository workspace needs explicit researcher acceptance. If only whole files may be removed, reject the same-file candidates rather than edit their targets. No real E3 unresolvability has been demonstrated here: complete alternative-evidence and leakage audits belong to validation after manual selection.

## 24e78349 — iRedAdmin

1. **RepoPairBench identifier:** `24e78349`

2. **Repository/project:** iRedAdmin — [https://github.com/iredmail/iRedAdmin](https://github.com/iredmail/iRedAdmin) (Python)

3. **Vulnerable snapshot reference:** First parent `6776a07190ecf735f40bdf759ae7f5b3b3cde6ac`; local `private/original_snapshots/session2/24e78349/6776a07190ecf735f40bdf759ae7f5b3b3cde6ac/`.

4. **Fixed snapshot reference:** Fix `3c72b438d412ea3ee0270f6956e19b1098c19191`; local `private/original_snapshots/session2/24e78349/3c72b438d412ea3ee0270f6956e19b1098c19191/`.

5. **Target file:** `controllers/panel/log.py`

6. **Target function:** `Log.GET`; vulnerable source `controllers/panel/log.py:19–87`.

7. **Researcher-only metadata:** CVE-2024-47227, CWE-79 (dataset labels; not independently certified here).

8. **Vulnerability description:** Request-controlled `domain`, `admin`, and `event` values pass through `web.safestr` and into HTML template attributes. The local `safestr` only converts to `str`; the template does not escape these hidden input values, and the configured Jinja environment supplies no autoescape option. This supports a reflected attribute-injection/XSS hypothesis. The fixed pair both validates inputs and adds template escaping.

9. **Likely decisive evidence:** Proposed evidence chain; REQUIRES RESEARCHER VALIDATION. The combined meaning of `web.safestr`, the actual `web.render` binding, and the unescaped attribute sink. See `web/utils.py:360–373`, `libs/iredbase.py:121–135,193`, and `templates/default/panel/log.html:66–71`. `controllers/decorators.py:20–30` limits this handler to a logged-in global administrator; this is not an unauthenticated endpoint.

10. **Evidence locations:** Source-root-relative navigation inventory: [candidate_files/24e78349.txt](candidate_files/24e78349.txt). Locations above refer to the vulnerable snapshot unless explicitly identified as fixed.

11. **Target-function evidence alone:** The function shows external request input and a rendering call, but neither proves how the custom renderer escapes output nor what the template does. The name `safestr` can misleadingly suggest sanitization. This is a relatively clean cross-file evidence gap.

12. **Plausible E1:** Provide the unchanged GET function, its decorator definition, the `safestr` definition, renderer initialization/binding, and relevant template lines as initial source evidence. Include sufficient template ancestry to establish that no enclosing autoescape block applies. Retain the rest of the permitted vulnerable source as appropriate.

13. **Plausible E2:** Initially provide only the unchanged function and route/decorator context. Keep `web/utils.py`, `libs/iredbase.py`, and the vulnerable template retrievable at their original relative paths; imports and `web.render('panel/log.html', ...)` offer navigation cues.

14. **Plausible E3:** Use the same initial function and context, but omit the template directory and renderer implementation from the allowed physical source copy. Keeping `safestr` visible is possible: lack of input sanitization alone does not prove the absent output sink is unescaped. Search for duplicate renderers/templates and template fragments before claiming the sink evidence is unavailable. Do not replace omitted dependencies with fabricated safe/unsafe stubs.

15. **Size / practical complexity:** Vulnerable: 271 regular files, 5,079,665 bytes (4.84 MiB). Fixed: 271 files, 5,079,958 bytes (4.84 MiB). The source chain is compact; inspecting it does not require a live mail server, LDAP, or SQL service. Full application execution would require backend/session infrastructure, so it was not attempted. Jinja's default escaping semantics remain an external library assumption to pin in validation.

16. **Obvious leakage risks:** CVE metadata, fixed template `|e` additions, commit message, patches, and version/release documentation must stay researcher-only. The vulnerable handler has an authorization decorator but no explicit vulnerability label in the inspected target. Filenames `log.py` and `panel/log.html` are ordinary functional names; `safestr` is behavior-relevant code, not an answer key.

17. **Major validity concerns:** Confirm the attacker can induce an authorized administrator to follow a crafted URL and that backend validation/error paths do not prevent reaching the render call. Validate a concrete attribute-breaking input and browser interpretation without inventing runtime results. Verify the pinned Jinja version/default behavior. E3 may still invite justified suspicion, but suspicion is not a demonstrated XSS sink. REQUIRES RESEARCHER VALIDATION. Engineering confidence: moderate.

## 7c167feb — kiwi

1. **RepoPairBench identifier:** `7c167feb`

2. **Repository/project:** kiwi — [https://github.com/kiwitcms/kiwi](https://github.com/kiwitcms/kiwi) (Python)

3. **Vulnerable snapshot reference:** First parent `a54cbbf73d6978c01f947b2c64f2db1986ecfb2c`; local `private/original_snapshots/session2/7c167feb/a54cbbf73d6978c01f947b2c64f2db1986ecfb2c/`.

4. **Fixed snapshot reference:** Fix `a2b169ffdef1d7c1755bade8138578423b35011b`; local `private/original_snapshots/session2/7c167feb/a2b169ffdef1d7c1755bade8138578423b35011b/`.

5. **Target file:** `tcms/core/history.py`

6. **Target function:** `diff_objects`; vulnerable source `tcms/core/history.py:12–33`.

7. **Researcher-only metadata:** CVE-2022-4105, CWE-79 (dataset labels; not independently certified here).

8. **Vulnerability description:** The helper produces a raw textual unified diff from object fields. Its caller stores that result as history-change text, and the admin renderer wraps the stored text in `<pre>` and marks it safe. This supports a stored-XSS hypothesis for attacker-controlled model fields; the fixed target sanitizes string values with `bleach_input` before generating the diff.

9. **Likely decisive evidence:** Proposed evidence chain; REQUIRES RESEARCHER VALIDATION. The data-to-HTML chain: `KiwiHistoricalRecords.post_save` stores `_change_reason` in `tcms/core/history.py:89–105`; `ReadOnlyHistoryAdmin.Diff` calls Django `safe` at lines 123–124. `tcms/testcases/models.py:50–57` supplies a tracked `summary` field; `tcms/testcases/admin.py:64` attaches the history admin. These are candidate decisive locations, not a certified complete exploit path.

10. **Evidence locations:** Source-root-relative navigation inventory: [candidate_files/7c167feb.txt](candidate_files/7c167feb.txt). Locations above refer to the vulnerable snapshot unless explicitly identified as fixed.

11. **Target-function evidence alone:** A generic text-diff function is not inherently an HTML vulnerability. Its target alone does not identify the eventual HTML consumer, whether values were sanitized upstream, or whether history is user-visible. However, giving the complete target file initially would expose the unsafe consumer immediately.

12. **Plausible E1:** Initially supply the unchanged diff helper, its storage caller, the relevant tracked model field/update path, admin registration, and `Diff` renderer with its `safe` import. Preserve exact source rather than an explanatory answer key.

13. **Plausible E2:** Initially supply only the helper. Make the intact vulnerable `tcms/core/history.py`, tracked model/update code, and admin registration retrievable. Navigation can begin by searching `diff_objects` callers, then `history_change_reason`. E1/E2 should share the same permitted source set where possible; only initial evidence differs.

14. **Plausible E3:** Retain an exact helper excerpt while withholding the storage caller and admin consumer, including the rest of `history.py`, admin registrations, and any alternate history display path that reveals equivalent sink behavior. This requires an excerpt-based source workspace: a whole-file-only design cannot hide the sink while retaining the target file. Preserve the helper bytes; do not rewrite its logic.

15. **Size / practical complexity:** Vulnerable: 752 regular files, 6,874,963 bytes (6.56 MiB). Fixed: 752 files, 6,875,229 bytes (6.56 MiB). Source inspection is lightweight. Full Django/database/admin deployment is unnecessary for tracing the raw diff to `safe`, but persistence and authorization should be manually validated. Alternate browser history code exists in `tcms/testruns/static/testruns/js/get.js:662–676`, with fenced Markdown, so it must not be assumed equivalent to the admin sink.

16. **Obvious leakage risks:** Fixed target contains the explicit comment `clean stored XSS` and a sanitizing import. Keep it, fix metadata, and all benchmark labels outside conditions. Vulnerable history names and `safe` calls reveal actual behavior, not answer annotations. Release notes and tests need a later scoped leakage audit.

17. **Major validity concerns:** Verify a real writable model field reaches the stored history and admin display, including upstream input treatment and simple-history persistence semantics. Same-file context complicates physical removal. The fenced Markdown browser path may escape rather than execute input; independently inspect `markdown2HTML` and do not conflate it with the `safe` admin path. Audit other admin classes, RPC history output, and migrations for residual evidence before E3. REQUIRES RESEARCHER VALIDATION. Engineering confidence: moderate.

## d2b7d775 — piccolo

1. **RepoPairBench identifier:** `d2b7d775`

2. **Repository/project:** piccolo — [https://github.com/piccolo-orm/piccolo](https://github.com/piccolo-orm/piccolo) (Python)

3. **Vulnerable snapshot reference:** First parent `e12c4694ed2068fb08e40209b4dcd2609796752b`; local `private/original_snapshots/session2/d2b7d775/e12c4694ed2068fb08e40209b4dcd2609796752b/`.

4. **Fixed snapshot reference:** Fix `edcfe3568382922ba3e3b65896e6e7272f972261`; local `private/original_snapshots/session2/d2b7d775/edcfe3568382922ba3e3b65896e6e7272f972261/`.

5. **Target file:** `piccolo/apps/user/tables.py`

6. **Target function:** `BaseUser.login`; vulnerable source `piccolo/apps/user/tables.py:191–237`.

7. **Researcher-only metadata:** CVE-2023-41885, CWE-203, CWE-204 (dataset labels; not independently certified here).

8. **Vulnerability description:** Missing usernames return before password hashing; existing usernames with wrong passwords call a local PBKDF2 routine. This supports a username-enumeration timing hypothesis. The fixed target adds a hashing call on the no-match branch. No timing measurements or network exploit were performed.

9. **Likely decisive evidence:** Proposed evidence chain; REQUIRES RESEARCHER VALIDATION. `BaseUser.hash_password` at `piccolo/apps/user/tables.py:136–163` calls `hashlib.pbkdf2_hmac`; the default iteration count is 600,000 at line 54. The caller obtains stored iterations via `split_stored_password` (175–179). Together they establish costly work on one branch that is absent on the other.

10. **Evidence locations:** Source-root-relative navigation inventory: [candidate_files/d2b7d775.txt](candidate_files/d2b7d775.txt). Locations above refer to the vulnerable snapshot unless explicitly identified as fixed.

11. **Target-function evidence alone:** The early return versus `hash_password` call is already a strong clue. Hiding the helper removes confirmation of its actual work, but its name and the target's iteration-handling logic can sustain a timing hypothesis. This candidate has a substantial risk that E2 is already sufficient for the intended level of conclusion.

12. **Plausible E1:** Provide unchanged `login`, exact local `hash_password`, iteration constant, and stored-password format helper as initial evidence. Add a real local caller if the chosen conclusion includes external observability.

13. **Plausible E2:** Initially give only `login`; keep the full vulnerable user table source and tests retrievable. Navigation to `hash_password` or `_pbkdf2_iteration_count` resolves the implementation gap.

14. **Plausible E3:** Retain the exact `login` excerpt but omit other portions of `tables.py`, hashing constants/helpers, password-format examples in tests/docs, and any duplicate hash implementation. This is an excerpt-based workspace, not a complete executable project. Even after removal, reject this construction if the researcher judges the remaining asymmetric call sufficient; do not rewrite the target to conceal its cues.

15. **Size / practical complexity:** Vulnerable: 505 regular files, 1,814,503 bytes (1.73 MiB). Fixed: 505 files, 1,814,669 bytes (1.73 MiB). Static work-asymmetry inspection does not require a database. A calibrated empirical timing claim would need a database and representative caller, and could be affected by network noise, rate limiting, or stored iteration counts. No such infrastructure was installed or run.

16. **Obvious leakage risks:** Fixed function explicitly comments on enumerating users via response timings. The vulnerable full file already has PBKDF2/OWASP comments and an expensive-hashing comment at lines 53–60; these are actual implementation evidence that must be absent in E3 if withholding hashing work. Tests/docs expose hashes and counts. Preserve target comments; do not sanitize clues by rewriting code.

17. **Major validity concerns:** A branch work difference is not a measured practical timing attack. Stored hash iteration counts can differ from the default, and callers may add mitigations. This has the weakest E2/E3 separation of the four candidates. Validate the meaning of an “insufficient” answer in light of widely known hashing behavior; if target-only reasoning is enough, reject rather than force E3. REQUIRES RESEARCHER VALIDATION. Engineering confidence: low for E2/E3 separation.

## ee76e0c9 — octoprint

1. **RepoPairBench identifier:** `ee76e0c9`

2. **Repository/project:** octoprint — [https://github.com/octoprint/octoprint](https://github.com/octoprint/octoprint) (Python)

3. **Vulnerable snapshot reference:** First parent `2cbeb27140c5695fd91593baa682e9c930dc4f27`; local `private/original_snapshots/session2/ee76e0c9/2cbeb27140c5695fd91593baa682e9c930dc4f27/`.

4. **Fixed snapshot reference:** Fix `ef95ef1c101b79394f134e8fce000e6bae046571`; local `private/original_snapshots/session2/ee76e0c9/ef95ef1c101b79394f134e8fce000e6bae046571/`.

5. **Target file:** `src/octoprint/plugins/pluginmanager/__init__.py`

6. **Target function:** `PluginManagerPlugin.get_additional_permissions`; vulnerable source `src/octoprint/plugins/pluginmanager/__init__.py:224–253`.

7. **Researcher-only metadata:** CVE-2022-3068, CWE-269 (dataset labels; not independently certified here).

8. **Vulnerability description:** The LIST permission assigned to read-only/user groups and the admin-only MANAGE permission both use the role `manage`. Local permission registration maps the same plugin/role to the same role need, and group/user permissions aggregate those needs. Management handlers check the MANAGE need. This supports a privilege-escalation hypothesis; the fixed target changes LIST to role `list`.

9. **Likely decisive evidence:** Proposed evidence chain; REQUIRES RESEARCHER VALIDATION. Role-to-need mapping in `src/octoprint/server/__init__.py:2563–2620`; string-to-RoleNeed conversion and authorization in `src/octoprint/access/permissions.py:24–44,78–93`; default group assignment at `access/groups.py:25–32`, group need union at 704–712, user need union/check at `access/users.py:1277–1294`; a consumer such as `PluginManagerPlugin.on_api_command` at pluginmanager lines 638–706.

10. **Evidence locations:** Source-root-relative navigation inventory: [candidate_files/ee76e0c9.txt](candidate_files/ee76e0c9.txt). Locations above refer to the vulnerable snapshot unless explicitly identified as fixed.

11. **Target-function evidence alone:** Two differently named permissions sharing a role is suspicious, but target-only data does not prove what `roles` means, whether named permission keys are checked independently, or how groups acquire authorization. The actual local aggregation/check implementation establishes the semantic link.

12. **Plausible E1:** Provide the unchanged declaration together with role registration, RoleNeed conversion, group/user need aggregation, and an operation guarded by MANAGE. Include relevant surrounding conditions so privileges are not overstated.

13. **Plausible E2:** Initially provide only `get_additional_permissions`; keep vulnerable permission registration, access modules, and handler implementations retrievable. The plugin hook registration at lines 2131–2132 links this data into the server permission setup.

14. **Plausible E3:** Keep an exact declaration excerpt and ordinary group identifier definitions, but withhold server role registration, access aggregation/check implementations, and handlers or alternate checks that reveal the same semantic mapping. Retaining the complete pluginmanager file leaks management consumers, so an excerpt-based workspace is required. Missing role semantics should remain unknown; never replace them with invented behavior.

15. **Size / practical complexity:** Vulnerable: 875 regular files, 20,350,217 bytes (19.41 MiB). Fixed: 875 files, 20,350,215 bytes (19.41 MiB). All important authorization mapping is locally present; no printer, network, or plugin installation is needed for static inspection. Full execution has substantial server/plugin machinery, so no claim about runtime performance is made. The dependency packet spans several small methods rather than one helper.

16. **Obvious leakage risks:** LIST/MANAGE descriptions and default group names are useful program evidence already in the unchanged target. They cannot be removed merely to make E3 harder. Fixed role change, security release material, raw commit/patch response, and benchmark labels must stay researcher-only. Complete pluginmanager source reveals many MANAGE guards.

17. **Major validity concerns:** The shared `manage` string may already let a model infer the flaw; researcher must establish E2 insufficiency. Check default group initialization, custom/persisted group configurations, identity propagation, and the exact operation path. Installation has a separate INSTALL guard, and active-print checks constrain operations: do not conclude all plugin actions are enabled. Audit vendor principal code, tests and other access routes for equivalent mapping before E3. REQUIRES RESEARCHER VALIDATION. Engineering confidence: moderate.

## Inspected exclusions and screening limits

- **00c73b6e / Gradio:** before `0b2c4901a63b2e5a7d7b3964d27b8f82d6d330e1`, after `41bd3645bdb616e1248b2167ca83636a2653f781`; `gradio/networking.py:file`. The exact first-parent source calls `secure_filename` at line 380 but source-wide searches found no definition/import, while `safe_join` is imported. A successful traversal conclusion cannot be asserted without resolving that apparent NameError. Treat as a snapshot/label-validity concern, not a confirmed working exploit. Inspected tree: 334 files / 24.13 MiB.
- **b256eb15 / Invenio-Drafts-Resources:** before `998ede99c377c84f11fe22c07c20f90c88c463dc`, after `039b0cff1ad4b952000f4d8c3a93f347108b6626`; `services/records/service.py:publish`. The fix passes the resolved draft into a permission check, but `require_permission` is inherited from an external package; the local `services/records/permissions.py:26` has `can_publish = [AnyUser()]`. The tiny source tree (95 files / 0.20 MiB) does not establish the record-dependent restrictive deployment policy. Additional pinned external evidence would be needed; not a self-contained E2 candidate on current inspection.
- **3f154463 / Scout:** before `679c42e635d4554c630a0018420b163586f9ef48`, after `f59e50f8ea596e641da8a0e9c7a33c0696bcbea5`; `downloaded_panel_name` in `scout/server/blueprints/panels/controllers.py:303–319`. The helper feeds a raw TXT `Content-Disposition` header (`views.py:249–269`) and a PDF `send_file(download_name=...)` path (`272–287`). This is a genuine cross-file sanitation change, but inspected source alone did not establish the harmful download interpretation or a concrete vulnerability mechanism. Framework newline rejection and browser filename handling matter. The dataset's CVE-2024-47531 / CWE-116 labels do not settle those questions. Tree: 1,040 regular files / 36.12 MiB; one omitted image link. Not retained merely to fill a fifth slot.

Function-level metadata also revealed less convenient alternatives: several TensorFlow/opcua/neuron records target tests rather than production behavior; direct `eval`, archive-extraction or unsafe-load examples often reveal the critical issue in the target itself; large ML/GUI projects add context and runtime complexity. These are screening observations, not blanket findings that those scenarios are unusable. Full upstream source for those unretained records was not downloaded.

## Researcher decisions before the next stage

Choose one candidate manually after inspecting the cited source. Validate the vulnerability mechanism, the exact missing fact and alternative evidence, E2's true initial insufficiency, and E3's true unavailability. Decide whether exact source excerpts are permitted or whole-file preservation is required. Pin relevant library semantics without presenting fix explanations to subjects. Confirm a source-only security conclusion is the desired outcome; avoid equating unmeasured exploitability or timing claims with demonstrated behavior. The final selection and all these judgments remain **REQUIRES RESEARCHER VALIDATION**.

## Session checks and stopping boundary

A targeted text scan found none of the four shortlisted CVE IDs in their extracted vulnerable source trees. This does not certify absence of answer leakage: version identifiers, generic security comments, tests, external advisories, and model memorization remain relevant. Raw `fix_commit_response.json` files do contain answer-revealing fix messages/patches; Piccolo also names GHSA-h7cm-mrvq-wcfr. All are outside proposed subject workspaces. The fixed Kiwi/Piccolo functions contain explicit XSS/timing explanations, reinforcing why the paired fixed source must remain private.

Both original benchmark SHA-256 values were checked unchanged. All 14 acquired target before/after snippets matched their dataset entries under whitespace normalization; archive SHA-256 and regular-file counts/sizes were checked, and no extracted symlinks were materialized. Candidate reports contain path/data-flow notes only, with no copied repository bodies or CVE/CWE labels. No experimental harness, model, repository program, or exploit was run. Existing configuration, logs, and condition directories were preserved. No candidate was selected and no E1/E2/E3 condition was populated.

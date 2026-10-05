# Condition build report — 24e78349

**Build date:** 2026-10-03 (Asia/Dhaka)  
**Source:** `private/original_snapshots/session2/24e78349/6776a07190ecf735f40bdf759ae7f5b3b3cde6ac`  
**Destination:** `pilot/conditions/{E1,E2,E3}/`  
**Approved input:** `config/evidence_manifest.json`

This report records mechanical construction results. It does not decide whether any condition is scientifically sufficient, ambiguous, retrievable, or unresolvable.

## Mechanical comparison

| Condition | Included files | Total source bytes | Initial packet bytes | Initial packet items | Workspace SHA-256 |
|---|---:|---:|---:|---:|---|
| E1 | 19 | 222,188 | 40,619 | 22 | `2b62f306d9ba1da57f9753b23b9b468a2f8a66d34965204a7cf18ce55259a134` |
| E2 | 19 | 222,188 | 5,499 | 4 | `2b62f306d9ba1da57f9753b23b9b468a2f8a66d34965204a7cf18ce55259a134` |
| E3 | 13 | 141,656 | 5,499 | 4 | `8b98cd677fbe1e79ebec12de87ecfa07d9394a83fb513a2ed764c7c8fd37ca16` |

Workspace SHA-256 is a deterministic digest over sorted `(repository-relative path, file SHA-256)` entries. Every included file also has its own SHA-256 and byte size in the corresponding researcher-facing manifest under `results/manifests/`.

E1 and E2 have identical available source files and identical workspace hashes. E2 and E3 have identical initial evidence packets according to the generated packet records. E1's initial packet has 22 ordered items; E2 and E3 each have four. Packet bytes are not token counts.

## Intentionally different paths

E3 omits these six physical files present in E1/E2:

| Omitted from E3 | SHA-256 in E1/E2 |
|---|---|
| `libs/iredbase.py` | `5c2f892247b115856284fbf652713972bea30bdb5274ca1b460ea1dca1f72510` |
| `templates/default/panel/log.html` | `1aa399b34b82e3aed2653f9a021f8156e0da37946d93a93e0733c8a0004fed74` |
| `templates/default/layout.html` | `5dffcbd55d274cba80494fd2209b26820a9c536d616c2a22657cc0603ca747a8` |
| `templates/default/macros/form_inputs.html` | `d0e5a1701469e248161e1242ebb5bbd86faa4ee02b9a7baa2ca908c7cfa992fe` |
| `templates/default/macros/general.html` | `08748a615610a43ad2adfb0faff945e14de6e1f03e344d9ab344f991d6914b87` |
| `templates/default/macros/msg_handlers.html` | `5003b432ddb6ade2b90bc01000f6b6ca6cbf75d2d6e050f5880885d2e90ff52e7` |

The shared cookie-setting excerpt from `libs/iredbase.py:34` appears in all three initial packets. In E3 it is an approved excerpt from a source file absent from the E3 workspace; the complete file is not copied there. The target file `controllers/panel/log.py` has SHA-256 `850ab5760fe5912284f070083dbade2c3591c5debb82b3e0fe019cd63714f979` in all conditions.

## Checks and warnings

- All manifest include/exclude paths formed an exact partition of the source snapshot's regular files. Missing requested paths: none.
- Copied file inventories matched the generated manifests; per-file hashes matched the copied bytes; no condition workspace contained symlinks.
- The builder tests passed, including deterministic output, unchanged source fixture, traversal rejection, symlink escape rejection, overwrite protection, exclusion, and hash generation.
- **REQUIRES RESEARCHER VALIDATION:** E1 sufficiency, E2 initial insufficiency and retrievability, and E3 evidence unavailability have not been established by construction or these mechanical checks.
- The E1 initial packet is 40,619 bytes versus 5,499 bytes for E2/E3. Verify fit with `OLLAMA_CONTEXT_LENGTH=16384` and preserve adequate tool/response budget before experiments; bytes do not prove token fit.
- The condition folders live beneath the repository root, which also contains `private/`. This build did not create an operating-system or tool sandbox. An agent with ordinary filesystem access may navigate to a parent and reach researcher-only material. Do not start an experimental agent from these folders until the separate isolation/access-boundary audit resolves this path.
- The contents were copied without rewriting source files. No experimental agent or model was run.

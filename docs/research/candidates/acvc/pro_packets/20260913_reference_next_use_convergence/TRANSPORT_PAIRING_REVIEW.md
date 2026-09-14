# Independent Transport pairing review

Reviewer: `/root/dm_acvc_resume/rv_acvc_pairing`, 2026-09-13. Contract: [TRANSPORT_PAIRING_REPAIR.md](TRANSPORT_PAIRING_REPAIR.md). Implementation inspected read-only in `C:/Projects/HMASD`; only this review is reviewer-owned. Applied MARL runtime general requirements and ENGINEERING_SCOPE_SPEC §§4–5, 7.3. No object-specific scientific appendix applies to this receipt-only change.

Reviewed main HEAD: `af68d691e3cb3f20a5685e39ca4e0410446205be`. SHA-256 of raw `git diff --binary --no-ext-diff --` for the two tracked changed paths: `d6fce66ff626cceb139dddf8c07deafc1d589520169ed6d780d449ad3853b98e`.

| Reviewed working-tree file | Raw-file SHA-256 |
| --- | --- |
| `.agents/skills/hmasd-chatgpt-pro-transport/scripts/native_transport.py` | `875067d67ce0167483356765d956e4111e2cdb44adcf0a6c7581bdf5ff1de9e8` |
| `tests/skills/test_native_transport_workflow.py` | `8e7772642b99515759a3dfc27c85843876842bd146578b5f5091453e757f8d14` |
| `tests/fixtures/native_transport/acvc-github-task-sha-pairing.json` (untracked) | `78e6c403ecad0391330aa675cda20fecaaf5046b6c69b11f4980cb074c31dfc2` |

## Material finding

**P2 — New SHA-only branch accepts a different TASK path sharing the expected URL prefix.** `native_transport.py:262` checks `task_url not in raw.decode('utf-8')`, which tests substring membership rather than an exact URL/path. With the observed SHA-only comment and a response containing only `[TASK](<expected TASK URL>.backup)`, consistent archive SHA-256/size/blob facts pass verification and `stage_native_receipt(..., native_delivery='native_final')` stages `boundary='COMPLETE'` with both provider IDs null. This violates the contract's wrong-TASK-path rejection and allows a mistaken suffixed TASK link to establish request identity. The defect is in the newly introduced fallback; the actual ACVC archive contains the correct TASK URL.

Evidence: one local Python in-memory probe used `read_handoff` on the immutable ACVC HANDOFF, copied the observed pairing, replaced response bytes with the suffixed-link counterexample and recomputed its matching digest/blob facts. Only `Path.read_bytes` was mocked; the actual archive, pairing and receipt code ran. Output: `{"counterexample":"Response cites TASK.md.backup only; SHA-only observed comment","boundary":"COMPLETE","provider_ids":[null,null],"scratch_written":false}`. No registry, provider, network or filesystem test effects occurred.

Suggested repair: require an exact URL token/path in the new response binding check; add the suffixed-path counterexample through `stage_native_receipt` and assert rejection leaves the record unchanged. The existing `other_task_path` test replaces the basename with `OTHER_TASK.md`, so it does not cover prefix matches.

## Other evidence and limits

Inspected `read_handoff`, archive verification, frozen task/scope selection, COMPLETE staging, historical receipt identity and delivery-outcome handling. Full-SHA lexical boundaries reject shortened/extended alphanumeric tokens; response scope, Issue identity and Git blob checks remain ahead of receipt mutation. The diff adds no Send, registry mutation, dependency, thread, process service, scientific computation or prohibited §4 facility. No concrete resource/budget breach was found.

Independent local Git read confirms response commit `98208469a9fd922c3390c63e7eaf53680fc2122b`, parent `dd31c09278ba5386b4ea10ef346b5cc72ffcc73a`, only the scoped RESPONSE.md added, 12,325 bytes, SHA-256 `2811543c44166c5ca52fe56980c5c59dacde70dc2ee9ca0c4d861d28b83fce9a`, blob `0528219db60db8fd16b877514bef5543ebf1de53`, and one occurrence of the exact TASK URL. Comment provenance remains the supplied observed fixture; no live GitHub observation was repeated.

Parent's [focused test evidence](TRANSPORT_PAIRING_TESTS.json) records 71 passed in 5.62 seconds, 6.516 seconds subprocess wall, scratch removed. I inspected that result and test coverage without repeating the suite. The new tests exercise both successful comment forms and the dependent COMPLETE receipt, plus wrong SHA/path/blob/Issue/scope cases. Existing unchanged tests cover duplicate and conflicting historical receipts.

One material finding remains for DM resolution. This review provides technical evidence, not permission, acceptance or scientific disposition.

## Correction review — initial P2 resolved

The preceding finding and fingerprints describe the initial revision and remain historical evidence. The corrected revision still has main HEAD `af68d691e3cb3f20a5685e39ca4e0410446205be`; tracked diff SHA-256, computed by the same command, is `8b573c779efa4999adef07ea604f61ad2c98a365e85f1c0fa641b3a066a721c5`.

| Corrected working-tree file | Raw-file SHA-256 |
| --- | --- |
| `native_transport.py` | `678d9833884e912dbae98867bdf7d5f6b3e5db8e93d4f5ef976f234e1b4eb435` |
| `test_native_transport_workflow.py` | `7d294f7f63b9c04c7687e9b3805ba61b233a77221aa032f2a93d95a272157ffd` |
| `acvc-github-task-sha-pairing.json` | `78e6c403ecad0391330aa675cda20fecaaf5046b6c69b11f4980cb074c31dfc2` |

The SHA-only fallback now requires explicit whitespace/Markdown delimiters or text boundaries around the complete TASK URL. A suffix such as `.backup` fails its right boundary, and a URL nested after `?redirect=` fails its left boundary. The original full-URL comment branch and downstream receipt identity logic remain unchanged. Tests now include both counterexamples and exercise all seven negative SHA/path cases through COMPLETE staging, checking that rejection leaves the record unchanged.

Independently reran only the original in-memory counterexample against the corrected source: `GitHub delivery comment must pair the exact fixed TASK and response`, `record_unchanged=true`, `scratch_written=false`. This closes the demonstrated failure. No suite repetition, external call or registry write occurred.

**Final technical finding state: no material finding remains in this bounded correction.** Existing full-URL-comment parsing and upstream observation provenance were preserved, not broadened by this repair. Actual ACVC bytes remain as verified above. Parent owns the correction-focused test result and technical acceptance; this review does not authorize receipt publication or any other external action.

## Dependent archive reconciliation review

Parent assigned the same-request `ARCHIVE_CONFLICT` → verified archive → COMPLETE receipt extension after the pairing repair was published. Reviewed main HEAD `68bc2a9a6299af5ab14125e518f5261bcbfbabc6`; SHA-256 of the tracked two-file diff by the same command: `eb1e726ebbd024e48e4e8c5dc1d5796229e78627b0322e0056d634030fc65bb8`.

| Reviewed file | Raw-file SHA-256 |
| --- | --- |
| `native_transport.py` | `bd5626a72645b1744683241033c0520d7de0f3e3c399a2fa2dcbc430e0943e63` |
| `test_native_transport_workflow.py` | `5afc7d7c00530fa13941c91bc318f4d477af1f8a0c58c50065e1460cbed7261c` |
| Existing fixture, unchanged | `78e6c403ecad0391330aa675cda20fecaaf5046b6c69b11f4980cb074c31dfc2` |

**No material finding found in this bounded extension.** Independently inspected `reconcile_github_archive`, `transport_contract.validate_transition`/`transition_record`, frozen binding fields, and the complete native receipt/history consumers. The generic terminal transition remains closed. The new helper admits only ARCHIVE_CONFLICT or ARCHIVED; requires equality with both pre-recorded response hashes, the resolved stored archive path and stored Git commit; then verifies bytes, blob and fixed TASK/Issue/response pairing before its first mutation. It appends a new reconciliation-history entry, preserves earlier entries and all Send/input/provider/archive/receipt fields, and updates only current archive state and timestamp. Already archived repetition revalidates and returns without mutation. Receipt staging retains the prior CONFLICT/SENT receipt in history, while existing completion-identity and delivery-status checks prevent duplicate or substituted COMPLETE receipts.

The revised actual-byte fixture now covers CONFLICT/SENT → reconciliation → COMPLETE/SENT and unchanged repeat. Eight negative cases check unsupported state, top-level/stored hash, path, commit, pairing, changed bytes and malformed history, with no record mutation on rejection. [Parent's focused result](TRANSPORT_ARCHIVE_RECONCILE_TESTS.json), inspected without rerunning: **19 passed, 62 deselected in 1.92 seconds; 2.5 seconds subprocess wall; scratch removed**.

Actual integration fact supplied by the parent after its registry read: the ACVC record was ARCHIVE_CONFLICT with matching top-level/stored hash `2811543c44166c5ca52fe56980c5c59dacde70dc2ee9ca0c4d861d28b83fce9a`, stored response file `C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/archive/acvc/2026-09-13-acvc-reference-next-use-convergence-01/RESPONSE.md`, stored commit `98208469a9fd922c3390c63e7eaf53680fc2122b`, the existing matching pairing, Send count 1 and retained native CONFLICT/SENT receipt. This confirms the actual stored field schema required by the helper; I did not read or mutate the live registry.

No new worker, service, dependency, generic reset, retry loop or external call is added. The bounded in-memory reconciliation is the explicitly assigned dependent repair; no scientific budget or runtime topology changes. Residual boundary: persistence under the existing registry lock and actual native delivery remain Transport's execution responsibility and were not performed by this review. DM retains technical acceptance.

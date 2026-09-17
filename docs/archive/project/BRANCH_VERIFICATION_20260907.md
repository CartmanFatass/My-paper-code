# Remaining branch verification — 2026-09-07

Owner requested Luna Scout parallel verification. Five fixed `hmasd-cm-scout` agents
(`gpt-5.6-luna`, medium) independently inspected three disjoint clean-branch groups, dirty
worktrees, and Pro deliveries. Parent checked remote-only refs, exact current tips, live writers
and the open PR. This was verification only; no second branch deletion, source repair or run occurred.

Main baseline was `abf09c6bf0`; newer intake/currentness checks used `13d25608b`. Full per-branch
tips, classifications and supporting observations are in [BRANCH_VERIFICATION_20260907.json](BRANCH_VERIFICATION_20260907.json).

## Accepted result

| Surface | Checked | Accepted finding |
| --- | ---: | --- |
| Clean local branch group | 74 | 14 patch/content-covered; keep the designated DISH checkout, leaving 13 retirement candidates. 60 still require reconciliation. |
| Dirty worktrees | 18 | 9 have examined source bytes matching baseline; 9 have distinct/mixed or incompletely assessed content. All remain preserved. |
| Pro delivery branches | 27 | 21 retirement candidates: 19 scientific response/intake pairs and 2 engineering probes. 6 remain unresolved. |
| Remote-only non-Pro branches | 26 | 8 have no positive patch; 18 retain historical differences. |
| Main/current/protected local branches | 9 | Retained pending direction checkout handoff, control-plane use or open PR. |

**42 distinct branch names can enter the next retirement batch** (13 + 21 + 8). These are
disjoint categories; a branch present locally and remotely is counted once. This does not
claim that all remaining historical differences have been resolved or that every branch must
be merged. No branch was created for this audit.

A matching subject or one matching file was not accepted as full integration. Preliminary
Scout labels based only on those leads were demoted. Accepted coverage uses zero positive
patches, stable patch-ID correspondence for every positive commit, or equality of all examined
positive-commit paths at the final tip. Full content coverage does not establish scientific
validity or make an old experiment current.

## Clean local retirement candidates

| Branch | Evidence |
| --- | --- |
| `codex/cm-dish-b05-seed101-20260906` | stable patch-id: 18812ba5 = main cd317810 |
| `codex/cm-vsp03-b01-20260905` | stable patch-id: 66a4fced = main 312ea1ed |
| `codex/dm-cbsc-a01-intake-nextpath-20260907` | stable patch-id: f766092a = main a1e8a6e5 |
| `codex/dm-cbsc-runtime-a01-20260907` | stable patch-id: 56edc415 = main 48254b90 |
| `codex/dm-frrie-resume-20260904` | all 5 positive stable patch IDs matched baseline main |
| `codex/dm-rcle-a02-20260906` | both positive stable patch IDs matched baseline main |
| `codex/dm-ucope-resume-20260904` | stable patch-id: 1635f391 = main 051c2d1e |
| `codex/dm-cbsc-a02-selected-20260907` | zero positive patches at bound and fresh main |
| `cm/vspc1-service-allocation-exec402-20260907` | 1/1 positive-commit paths byte-identical to main |
| `codex/cm-fsd-seed3-resume-20260904` | 1/1 positive-commit paths byte-identical to main |
| `codex/dm-k1-vsp03-b01-results-20260905` | 14/14 positive-commit paths byte-identical to main |
| `codex/dm-n3-continue-20260904` | 5/5 positive-commit paths byte-identical to main |
| `codex/impl-n3-dish-funnel-a01-20260905` | 5/5 positive-commit paths byte-identical to main; same positives as DM N3 continue |


The covered DISH branch `codex/dm-dish-b06-scientific-intake-20260907` remains the designated
direction checkout. Its integration is confirmed, but that is not a reason to remove the checkout
chosen for future work. Candidate tips were unchanged at parent readback.

## Pro delivery verification

| Branch | Finding |
| --- | --- |
| `codex/pro-cbsc-opportunity-credit-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-cbsc-two-seed-family-20260905` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-a01-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-a02-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-b02-convergence-20260905` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-b03-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-b04-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-post-b05-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-dish-post-b06-20260907` | Retain/unresolved: Prepared/unsent; no formed response or Pro intake found. |
| `codex/pro-dish-witness-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-github-recovery-probe-20260905` | Candidate: Engineering-complete: TASK target collaboration_probe/CONFLICT_TARGET.md (101 bytes) confirmed by AFTER.json and INTAKE.md; scientific intake is inapplicable. |
| `codex/pro-github-write-probe-20260905` | Candidate: Engineering-complete: TASK target collaboration_probe/ROUNDTRIP_REVIEW.md (2427 bytes), ROOT_READBACK.json and roundtrip_archive/INTAKE.md confirm acceptance. |
| `codex/pro-rcle-post-a02-20260906` | Retain/unresolved: No formed response or round intake found; unresolved current boundary. |
| `codex/pro-rcle-post-b01-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-rcle-post-b02-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-rcle-tbcfv-first-b-20260906` | Retain/unresolved: Original round lacks response; r02 is a different binding. |
| `codex/pro-rcle-tbcfv-first-b-r02-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-vnfc-b01-two-seed-convergence-20260905` | Retain/unresolved: Response bytes match main, but no matching current-round intake was located. |
| `codex/pro-vnfc-depmode-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-vsp03-b01-three-seed-convergence-20260905` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-vsp03-shared-service-convergence-20260906` | Retain/unresolved: Continuation receipt is not the requested response; transport-blocker intake exists. |
| `codex/pro-vspc1-b02-convergence-20260906` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-vspc1-completion-amendment-20260907` | Candidate: Response blob2f782ae1,24516 raw bytes; new main13d25608b has identical response and COMPLETION_AMENDMENT_INTAKE_20260907. |
| `codex/pro-vspc1-k4-three-seed-20260905` | Retain/unresolved: Misrouted Portfolio response; r02 is a different binding. Preserve misroute. |
| `codex/pro-vspc1-k4-three-seed-r02-20260905` | Candidate: Response Git object equals main and matching round intake was found. |
| `codex/pro-vspc1-reactive-queues-20260906` | Candidate: Raw Git blobf653985b equals main:29215 bytes.29373-byte working copy difference is line-ending conversion, not response mismatch; intake found. |
| `codex/pro-vspc1-service-allocation-20260907` | Candidate: Delivery2347dbf2 and archive/integration5d3027ebe both resolve to blobce28248f,28786 bytes; intake correctly names archive commit; no provenance conflict. |


Raw Git objects were used for response equality. The reactive-queue checkout size difference
was line-ending conversion. Service-allocation delivery `2347dbf2` and archive/integration
`5d3027ebe` have identical response bytes; different source and integration commits are valid
provenance, not a blocker. Probe checks used their actual TASK response paths and engineering
acceptance records; scientific intake requirements do not apply to these probes.

## Remote-only non-Pro candidates

| Branch | Tip |
| --- | --- |
| `CPTest` | `042df67038ee2e36d9e164ba82265f22822f1ad1` |
| `codex-supervisor-durability-kernel-v1` | `a9c5f5a40f6b075b654685e46b850cda8124c370` |
| `codex/expressibility_gated_renewal_credit_relay` | `ea65e5186d2125699cc6eff59b3b2deadec5707b` |
| `codex/hmasd-science-tools` | `3d1865b8a587fbf78ef0aa3d53d8bdaf365d4591` |
| `codex/opportunity_normalized_lease_gated_rebinding` | `ea65e5186d2125699cc6eff59b3b2deadec5707b` |
| `codex/rs_c2_vsp02_sequence09_acceptance_20260809_28d9758` | `77d6f4ab2b0983454931f3b922721efdabf3316a` |
| `worktree-agent-a5ae2957862d225cd` | `e205d29f7cead5d375ecf464d104792e8daa78f0` |
| `worktree-agent-aeda939d06a5b4fea` | `e26063d8193c63c1aaa0ba54d2efdd957dd313b7` |


All 26 remote-only tips match the existing recovery manifest. Historical branches with large
positive inventories, including `untied-k` and `wip/formal-path-coverage`, remain unresolved;
positive counts are not evidence of current scientific value.

## Uncommitted work and retained checkouts

The existing remote recovery tag preserves committed tips, **not uncommitted bytes**. Distinct
CBSC runners, VNFC solver work, VSP03/VSPC1 publishers and DISH production/conformance files
must be preserved and reconciled together with their tests. Generated Python caches were
distinguished from source. The 692-entry legacy app-server worktree and the 16-entry old control-
plane worktree require separate bounded reconciliation; neither received a full content audit.

Root confirmed no native/CM editor active at the check boundary. These existing checkouts
remain available for direction continuation; no new per-task branch is needed:

| Direction | Existing worktree | Existing branch |
| --- | --- | --- |
| CBSC | `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906` | `codex/dm-cbsc-a02-intake-20260907` |
| DISH | `C:/Projects/HMASD-worktrees/dm-dish-b06-scientific-intake-20260907` | `codex/dm-dish-b06-scientific-intake-20260907` |
| RCLE | `C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906` | `codex/dm-rcle-post-a02-boundary-20260907` |
| UCOPE | `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906` | `codex/dm-ucope-b02-result-intake-20260907` |
| VSPC1 | `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906` | `codex/dm-vspc1-next-20260906` |

Open PR #2 still targets `codex/cm-vnfc-n7-b01-20260905`; retain it. Main and this reused
control-plane checkout remain in use. Before later retirement, recheck current tips/writers/PR
bindings and preserve any newer tip missing from the prior archive. Reconcile uncommitted
work separately; branch cleanup must not erase directories or evidence.

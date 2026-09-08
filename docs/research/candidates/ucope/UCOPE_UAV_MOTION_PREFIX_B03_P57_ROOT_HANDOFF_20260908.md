# UCOPE B03 — accepted source and exact single-pair Root route

**Completed route, 2026-09-08:**7101 finished with a valid just-below-MEI
DOWN result; CM collection and [DM intake](UCOPE_UAV_MOTION_PREFIX_B03_P57_INTAKE_20260908.md)
are complete. No launch, retry, second pair, aggregate or evaluation
remains pending. Commands and prospective states below are historical
provenance, not a new dispatch instruction.

Source **`70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`** implements
common total explicit entropy coefficient0 in T/G while preserving the
remaining B02 action/information/credit/native-return paths. This is a new
package comparison, not a controlled entropy-causal comparison with B02.

## Binding and completed engineering

[P57](../../portfolio/handoffs/2026-09-08-p57-ucope-post-b02-selection.md)
at`68c7dab578d4e64d201a34028b574469bf1c598f` supplies the complete route.
The [card §§1–6](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md)
and [full CM specification](UCOPE_UAV_MOTION_PREFIX_B03_CODE_SPEC_20260908.md)
were frozen at`f5230ca30537e7baa7db71ee2ba437a17efe807b`, integrated by Root
as`866ad0ef5`. Accepted source is the complete70900ac7e commit, tree
`13634a339b2d6e323238a46feac29f443d022b8e`. Use this exact source, not a
doc-only descendant or an incomplete main source tree. Currentness compares
the bound source surface, so unrelated documentation does not refuse a run.

The [technical acceptance](UCOPE_UAV_MOTION_PREFIX_B03_TECHNICAL_ACCEPTANCE_20260908.md)
at`14cf36615a42dde57d337201dd78adc6820ad1cf`, with link-only correction
`5025f94af55df477d339d9ce350ae2b7fe8da882`, records one remote suite:
61 passed, full wall2.30s, exit0; final independent review found no material
issue. [DM intake §6](UCOPE_UAV_MOTION_PREFIX_B03_SELECTION_INTAKE_20260908.md#6-implementation-intake-and-source-binding--2026-09-08)
accepts the actual source/receipt. Scope§4 none; no standalone smoke,
diagnostic or scientific invocation occurred. B02 adverse/mixed outcomes,
its historical smoke breach and wrong-cwd failure remain unchanged.

Reuse local authoring checkout
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch
`codex/ucope`. DM `/root/dm_ucope_p47_resume` owns science and binding;
CM `/root/dm_ucope_p47_resume/cm_am_ucope_b02_p47` owns terminal collection
and technical acceptance. Root owns integration, actual staging/state
reconciliation, launch and observation. No new CM or Portfolio request is
needed for these allocated stages.

## Existing exact-SHA checkout and prospective experiment identity

Reuse the already staged detached checkout on `hmasd-wsl-node`:

`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b03-p57-check-20260908`

Its name reflects the completed engineering check, not a changed scientific
host. The CM staging receipt records clean HEAD70900ac7e and the exact tree,
verified committed-object transfer and changed source/test blob matches.
Raw staging and suite evidence is under
`temp/directions/ucope/test/b03_p57_check_20260908/` in the authoring checkout.
The existing test supervisor
`ucope-uav-motion-prefix-b03-p57-check-20260908` is finished, exit0. Preserve
it. No repeated fetch, source transfer, worktree creation or test is needed
when the actual existing checkout matches this accepted source.

Root reconciles current checkout/source, prospective handle and output
state before its one launch. Absence of the scientific handle/output has
not been asserted from a DM remote observation; uncertain acceptance must
be read back rather than resent. The **new scientific** identity is:

| Master | Supervisor | Output relative to the exact detached cwd |
| --- | --- | --- |
| 7101 | `ucope-uav-motion-prefix-b03-7101-p57-20260908` | `temp/directions/ucope/exp/uav-motion-prefix-b03-7101-p57-20260908` |

## Exact invocation and fixed work

One serial T/G/H pair: two fits of512 complete episodes,131072 training
team steps and1024 Adam calls each;32 final sampled episodes per T/G/H.
Totals: **286720 team steps,2048 Adam calls,1120 complete episodes,
96 final evaluation episodes**. Independent training n=1 matched pair.
All master7101 domains, final-only evaluation, native J and MEI.01 remain
card§§4–5. [Preparation facts](UCOPE_UAV_MOTION_PREFIX_B03_PREPARATION_FACTS_20260908.json)
retain the computed work/exposure line and source-based cost projection.

Use configured Python `/home/wu/.venvs/hmasd/bin/python`, CPU FP32,
one Torch thread. Host/device is not the estimand. Fresh actual-node
physical and effective memory admission must both be≥4GiB immediately
before scientific work. The command includes the existing preflight;
the runner retains its own fresh admission. Caps are **1800s per complete
learned arm and3600s for the full invocation through publication/exit**.
Startup/common initialization is charged to T; H/publication to G.
The external timeout includes admission/startup conservatively. No phase
resets the cap, and no scientific retry or continuation is allocated.

Use this complete LF-safe literal or its identical
[command file](../../../../temp/directions/ucope/exp/uav-motion-prefix-b03-p57-binding/root-launch.ps1).
Its SHA-256 is`2e695533a0b80c4a86288016f07d194ded5dcdb571090a8364819aea2af621b2`.
Preparation of the command is not execution:

```powershell
@'
/usr/local/bin/agent-task run ucope-uav-motion-prefix-b03-7101-p57-20260908 "/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc -c 'cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b03-p57-check-20260908 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/uav-motion-prefix-b03-7101-p57-20260908/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --pair b03 --seed 7101 --out temp/directions/ucope/exp/uav-motion-prefix-b03-7101-p57-20260908'"
'@ | ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "tr -d '\015' | /bin/bash -s"
```

## Root observation, same-CM collection and all-outcome intake

After acceptance, Root records handle/PID/start, exact source/cwd, logs,
admission receipt and observation ownership under the existing monitor
route. Status/log/exit facts live in `/home/wu/.agent-tasks/<supervisor>/`.
The prospective output contains `summary.json`, `episodes.jsonl`,
`rollouts.jsonl`, `diagnostics.jsonl`, `final_T.pt`, `final_G.pt` and
`resource_admission.json`. Preserve every completed or partial artifact.

On terminal event, route the accepted identity and actual receipts to the
same CM and this DM. CM collects to
`C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b03-7101-p57-20260908/`
and checks real B03/7101/card-section5/agent-compound/coefficient0 identity,
both actual learner counts/lr/exposure, finite checkpoints, native primary,
final reset association, caps and receipt hashes. No learner/evaluator is
rerun. No B03 multi-pair aggregate exists or is needed.

DM uses all32 paired final native differences, all T/G/H outcomes and
conditional evaluation uncertainty, with independent training n=1. Score
the prospective WITHIN(.55) and positive G−H(.55) predictions; read owner
replies at intake. Apply card§5 verbatim, preserve competence restrictions
and all contrary/history evidence, and write E0/intake/Chinese brief/audit
plus accepted DIRECTION science. Local movement or entropy does not replace
complete native return. The ceiling is this fitted package on this fixed
task/budget, not entropy causality, pure information value, stable training
performance, transfer, deployment, C or a family/lifecycle disposition.

At that intake P57 is exhausted for **every sign**. Return promptly for
replacement; do not start a second pair, retry, H-completion run, sweep,
extra evaluation or unallocated successor. A concrete integrity/cap/source
failure stops its dependent route with existing facts preserved, without
converting engineering failure into scientific polarity.

# VSP02 B01 P17 — E0 technical result evidence

**Technical acceptance: PASS for the complete seed1117 pair.** Raw native adaptation means are
CARRY **7.8564453125**, RESET **7.84765625**, and RESET minus CARRY **−0.0087890625 deliveries per
episode**. All required output, training/update/evaluation counts and both full native windows
conform. This records engineering acceptance; DM owns scientific intake of both independent prefixes.

## Binding and collection

Contract: [card](VSP02_TEAMMATE_POLICY_CHANGE_B01_SCIENCE_CARD_20260907.md) §§1–7,9 and
[P17 amendment](VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_AMENDMENT_INTAKE_20260907.md) §§1–3 at
`e69208359cf9914d6a7555e379c95b17f02afed1`; code spec §§2–5 remains unchanged. Exact execution
source is separately bound to **19be5ee18393913ff92693cdf037213ec1777510**, confirmed by remote
HEAD and summary. The authoring checkout `C:/Projects/HMASD-worktrees/dm-vsp02`, `codex/vsp02`,
was clean at the contract revision when collection began. No source/test changes were made.

- Node: `wsl_4070` / SSH `hmasd-wsl-node`; supervisor `/usr/local/bin/agent-task`.
- Handle: `vsp02-tpc-b01-p17-s1117-a1`; PID 2755975; finished, exit 0, tmux inactive.
- Remote cwd: `/home/wu/hmasd-worktrees/vsp02-tpc-b01-p17-s1117-a1`.
- Preserved supervisor segment: 2026-09-08 10:53:03–10:53:40 +08:00, duration 37s.
- Runner argv: `/home/wu/.venvs/hmasd/bin/python -u scripts/run_vsp02_teammate_policy_change_b01.py --seed 1117 --out temp/directions/vsp_02/exp/teammate_policy_change_b01_p17_s1117_a1`.

The retained `runner.sh` supplies the declared cwd, one-thread environment variables, and adjacent
on-node `admit-memory && runner` chain. The log contains one start and one completed invocation;
no P15 wrapper-repair history is attributed to this fresh P17 handle.

All six output files were copied unmodified by scp into
`C:/Projects/HMASD-worktrees/dm-vsp02/temp/directions/vsp_02/exp/teammate_policy_change_b01_p17_s1117_a1/`.
Admission is retained at `exp/admission/tpc_b01_p17_s1117_a1.json`; all six original supervisor files
and a collection status snapshot are at `exp/supervisor/vsp02-tpc-b01-p17-s1117-a1/`.
Remote/local filenames and byte sizes agree. P15 artifacts were not overwritten.

The [machine-readable evidence](VSP02_TEAMMATE_POLICY_CHANGE_B01_P17_RESULT_EVIDENCE_20260907.json)
embeds the original summary, admission, supervisor receipts, raw-derived group readings,
collection snapshot, inventories and verification script. The local stdlib-only verifier is
`temp/directions/vsp_02/exp/verify_tpc_b01_p17.py`, reused from P15 with only this run's bindings.
It exited 0 without importing or executing the learner. No replay or test/fixture run occurred.

## Raw measurements and checks

The unchanged card rule is:

> Primary per-arm AUC is the sum of the **1024 actual post-change training-episode native returns divided by1024**; Delta is RESET minus CARRY.

| Phase/arm | Complete training episodes | Joint steps | Adam steps | Native return sum | Native mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| PREFIX | 4096 | 196608 | 4096 | 28546 | 6.96923828125 |
| CARRY | 1024 | 49152 | 1024 | 8045 | 7.8564453125 |
| RESET | 1024 | 49152 | 1024 | 8036 | 7.84765625 |

Raw difference is −9 deliveries / 1024 = **−0.0087890625**, exactly matching summary primary.
Both completeness flags are true. All 6144 training rows are full 48-step episodes, totaling
294912 joint steps; all 384 rollout updates are complete with 16 logged Adam calls each, totaling
6144. Every pre-collection progress count and the CARRY/RESET batch alternation agree with the spec.

Evaluation has 1152 complete episodes / 55296 joint steps: old-prefix 64, shared q0 64 once,
and 64 per arm at all eight declared checkpoints. Combined exposure is **350208 joint steps**.
Every episode index, integer return in [0,16], complete flag, update loss/gradient finiteness,
phase/arm count, non-overlapping 16-episode bin and evaluation mean was checked against raw files.
No partial row, interrupted update, missing checkpoint or model-selection trial is reported.

Old-prefix sampled mean is 8.375 and shared q0 is 4.671875. Terminal sampled means are CARRY 7.75
and RESET 7.703125. These agree with the endpoint rows and do not replace the native primary.
All intermediate outcomes remain in the raw files and embedded evaluation record. The PNG was
opened and shows all training bins, old endpoint and paired post-switch evaluation curves.

## Fork, movement and runtime

Both fork models report zero max absolute difference from PREFIX and global progress 4096.
CARRY has ten Adam entries, step min/max 4096 and moment norms identical to PREFIX. RESET has
zero entries/moments/step counters. Both descendants finish at global progress 5120 after 1024
post-fork updates; final Adam min/max steps are 5120 for CARRY and 1024 for RESET, ten entries each.

Initial parameter RMS is 0.076406329870224. Actual displacement RMS is 0.0019241179106757045 after
16 prefix updates and 0.07071450352668762 after 4096. From fork, final displacement is
0.020302623510360718 CARRY / 0.02527695521712303 RESET. All readings are finite and nonzero with
the declared step counts. These are recorded same-run measurements, supported by accepted source
and existing focused checks; raw CSVs do not reconstruct model tensors or establish bit identity.

Runtime reports CPU FP32, one intra-op/inter-op thread, CPython 3.10.21 and torch 2.7.0+cu118 on
Linux WSL2. The whole-run wall is **36.07172741298564s**, within the single 1800s cap, including
imports through publication. Supervisor admission/runner chain wall is 37s. Peak process RSS is
**518434816 bytes**, resources_unmeasured=false. Aggregate CPU and per-arm wall were not measured;
neither is inferred from the single whole-run wall. The prior P15 timing remains a prospective
unchanged-count planning reference, not a guarantee or an extra allocation.

Admission at 2026-09-08T02:53:03.394607Z passed with physical/effective available memory each
**15661023232 bytes**, above the 4294967296-byte floor, no failure reasons. The actual archived
command places that check immediately before this runner on the same node.

## Acceptance limit and return

No comparison-threatening output defect was found. Collection added zero environment transitions,
optimizer steps, evaluation episodes or scientific invocations. No retry, third seed, repeated
seed1103 evaluation, fixture, source repair or new machinery was performed. This commit owns only
the two fresh P17 evidence documents; engineering-scope §4 additions: none.

The negative P17 primary remains alongside the separate positive P15 primary. Each whole prefix
and pair is one independent training unit; episodes/checkpoints are not extra seeds. Technical
acceptance does not establish stable superiority, equivalence, event-specific attribution,
transfer or UAV entry. Root integrates the named evidence commit; the existing VSP02 DM performs
the all-outcome two-prefix intake, audit and Chinese brief. No additional experiment is selected.

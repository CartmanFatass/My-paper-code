# VSP02 B01 P15 — E0 technical result evidence

**Technical acceptance: PASS for the complete seed1103 P15 pair.** This is collection and
engineering acceptance of the existing observation, not a new scientific decision. The native
adaptation means are CARRY **7.46875** and RESET **7.4873046875**, giving RESET minus CARRY
**+0.0185546875 deliveries per episode**. Both full1024-episode windows and all required updates,
evaluations and outputs are present. Scientific interpretation and follow-up remain with DM.

## 1. Binding and actual execution

Contract: [science card](VSP02_TEAMMATE_POLICY_CHANGE_B01_SCIENCE_CARD_20260907.md) §§1–8,
[P15 readiness](VSP02_TEAMMATE_POLICY_CHANGE_B01_P15_READINESS_20260907.md) §§1–4 and
[code specification](VSP02_TEAMMATE_POLICY_CHANGE_B01_CODE_SPEC_20260907.md) §§2–5.
P15 releases one scientific pair; earlier P14 zero-allocation wording is superseded only as
stated in card §8. The accepted source/review remains unchanged.

- Launch SHA: `19be5ee18393913ff92693cdf037213ec1777510`, also read directly from remote HEAD.
- Node: `wsl_4070`, SSH `hmasd-wsl-node`; supervisor `/usr/local/bin/agent-task`.
- Handle: `vsp02-tpc-b01-p15-s1103-a1`; PID2754886; final status finished, exit0, tmux inactive.
- Remote cwd: `/home/wu/hmasd-worktrees/vsp02-tpc-b01-p15-s1103-a1`.
- Result-bearing segment:2026-09-08 08:45:27–08:46:05 +08:00 (2026-09-07 17:45:27–17:46:05 PDT).
- Exact effective argv: `/home/wu/.venvs/hmasd/bin/python -u scripts/run_vsp02_teammate_policy_change_b01.py --seed 1103 --out temp/directions/vsp_02/exp/teammate_policy_change_b01_p15_s1103_a1`.
  `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS` are each1. Preserved `runner.sh`
  contains the full adjacent preflight `&&` runner chain and cwd.

The preserved task.log also contains an earlier08:44:43 +08:00 wrapper start/exit0 of duration0s,
with no preflight JSON or runner summary. Root confirmed that PowerShell nested quoting sent an
empty/truncated command; local stderr reported `env` unrecognized. Root observed no admission,
output root, model or scientific exposure from that segment, then corrected only quoting for the
unchanged chain under the same handle. Thus there were **two supervisor starts and one scientific
invocation**. The first segment is preserved; its no-exposure observation is attributed to Root,
while the zero-second/no-runner-output facts are directly visible in the archived log.

## 2. Complete collection and checks

Local checkout was clean at the launch SHA on `codex/vsp02`; no source/test changes were made.
All six remote output files were copied with scp into the corresponding local run root:

`C:/Projects/HMASD-worktrees/dm-vsp02/temp/directions/vsp_02/exp/teammate_policy_change_b01_p15_s1103_a1/`

Admission is beside it under `exp/admission/tpc_b01_p15_s1103_a1.json`; all six original supervisor
files are under `exp/supervisor/vsp02-tpc-b01-p15-s1103-a1/`, plus a fresh collection status snapshot.
Remote and local file inventories/sizes agree. Raw CSVs, summary and PNG remain unmodified.
The [machine-readable evidence](VSP02_TEAMMATE_POLICY_CHANGE_B01_RESULT_EVIDENCE_20260907.json)
contains the original summary/admission/supervisor records, inventories, computed group readings,
verification source, and the explicitly attributed dispatch clarification.

A stdlib-only readback at `temp/directions/vsp_02/exp/verify_tpc_b01_p15.py` exited0. It imported no
trainer and performed no replay. It checked every episode number, complete flag,48-step count and
integer return in[0,16]; all phase/arm counts; every pre-collection global update count; alternating
CARRY/RESET batches; all384 completed rollout updates and their16 actual logged Adam calls; finite
loss/gradient readings; every non-overlapping16-episode bin; every sampled evaluation mean; shared
q0 exactly once; and the primary directly from native training returns. All checks passed.
The PNG was opened and visually checked: prefix and both adaptation curves, all sampled checkpoints
and old endpoint are readable; no selected best checkpoint or confidence band substitutes for data.

## 3. Actual exposure and primary

The card's primary rule is:

> Primary per-arm AUC is the sum of the **1024 actual post-change training-episode native returns divided by1024**; Delta is RESET minus CARRY.

| Phase/arm | Complete training episodes | Joint steps | Adam steps | Native return sum | Native mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| PREFIX |4096|196608|4096|28126|6.86669921875|
| CARRY |1024|49152|1024|7648|7.46875|
| RESET |1024|49152|1024|7667|7.4873046875|

Training totals:6144 complete episodes,294912 joint steps,384 rollout updates and6144 Adam steps.
Evaluation:1152 complete episodes and55296 joint steps, including old-prefix64, shared q0 64 once,
and64 per arm at each of q=16,32,64,128,256,512,768,1024. Combined:350208 joint steps. There are no
partial episodes or interrupted updates, missing evaluations, selected checkpoints or additional
model-selection trials. One independent prefix and its whole pair remain one training unit.

Raw RESET minus CARRY is19 total deliveries /1024 = **0.0185546875**. This agrees exactly with the
published primary. Both completeness flags are true under code spec §5. All intermediate negative,
zero and positive differences remain in raw data and the embedded evaluation record. Old-prefix
sampled endpoint is8.125; shared post-switch q0 is3.953125; both terminal sampled means are8.234375.
These secondary evaluation readings are not substituted for primary or treated as training seeds.

## 4. Fork, learner movement and runtime

Both fork models report max absolute parameter difference0 from the prefix. Global progress is4096
for PREFIX/CARRY/RESET. CARRY retains ten Adam entries and per-parameter steps4096, with moment norms
matching PREFIX; RESET has zero state entries, zero moments and zero step counters. At completion,
both descendants have global progress5120 and1024 post-fork steps. Final Adam step min/max are5120
for CARRY and1024 for RESET, with ten entries each.

Initial parameter RMS is0.07666852325201035. Actual displacement RMS is0.0023259019944816828 after
first16 prefix updates;0.06980965286493301 at prefix4096; and from fork0.019422367215156555 CARRY /
0.02313823625445366 RESET after their1024 updates. Every reading is finite and nonzero, with the
specified progress count. These are same-run numeric measurements; raw CSVs alone do not reconstruct
network/Adam tensors. Their interpretation relies on the accepted source and prior focused fork,
RNG, host and learner checks, not a new replay or cross-platform bit-identity claim.

Runtime reports CPython3.10.21, torch2.7.0+cu118 on Linux WSL2, explicit CPU FP32, one intra-op and
one inter-op thread. Whole-run wall including imports through publication is36.69615292199887s,
within the1800s cap. Supervisor chain wall is38s including admission/startup. Peak process RSS is
520306688 bytes, `resources_unmeasured=false`. Aggregate CPU time was not measured; it is not
reported as zero or inferred from wall. The CUDA-enabled distribution does not imply GPU execution.

Admission at2026-09-08T00:45:27.993526Z reports physical and effective available memory each
15634575360 bytes, both above4294967296; passed with no failure reasons. The archived command places
this on-node check immediately before the runner. No collection-time admission or scientific launch
was performed. The prior readiness record explicitly had no scientific affordability projection;
the observed wall is complete-run evidence, not a retroactive pre-launch projection.

## 5. Scope, limitations and next owner

No code, treatment, seed, cap, comparator, observation, return definition or stopping rule changed.
Collection adds zero environment transitions, optimizer steps, evaluation episodes or scientific
invocations. No smoke, training replay, retry, resume, extra arm or resource sweep was run by CM.
Engineering-scope §4 additions: none; this change publishes two evidence documents only.

No comparison-threatening defect was found in the collected output. Technical conformance does not
establish stable superiority, competent-baseline qualification, event-specific Adam attribution,
transfer or UAV entry. Root integrates this named evidence commit and forwards it to the existing
VSP02 DM for scientific intake, audit and Chinese brief under the P15 return route. No additional
scientific work is selected here.

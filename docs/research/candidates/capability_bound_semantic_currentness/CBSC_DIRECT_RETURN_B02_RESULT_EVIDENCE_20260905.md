# CBSC direct-return B02 result evidence

Date: 2026-09-05 (local). **Complete valid B/EXPLORE, one paired training seed.**
The fixed endpoint difference is zero. This is a sampled, finite-budget learning
result, not a proof of algorithm equivalence or currentness mechanism failure.

## Object, rule and observed population

Card: CBSC_DIRECT_RETURN_B02_SCIENCE_CARD_20260905.md.
Launch source: 2c9254f70c3a8ef9d95ac6dc3f6585382304be41; exact commands:
CBSC_DIRECT_RETURN_B02_COMMANDS_20260905.json at abb9931bc.
Root integrated and pushed the source/commands at 09c63825a. DM checked their
byte-identical presence at pushed main d0eb023dc before the first invocation.
CM final evidence commit: 9535d9465376cb74e9ce85125e8785419fcf8e52,
following check 352ead180 and RAW 3967c1353.

The card's reading rule is:

> At checkpoint update 48, for evaluation episode e in 0..31, compute
> d_e = native_return(STRUCT,48,e) - native_return(RAW,48,e).
> The primary measurement is the mean of all 32 d_e. Preserve every d_e, both
> absolute returns and four checkpoint curves.

Both real recurrent PPO arms used seed 21203, the same complete public history,
matched initialization and exogenous random addresses, CPU FP32, one Torch
compute thread, and unchanged native decision plus settlement rewards. The
host has two receiver entities and one learning controller, not co-adapting
learning agents. Greedy evaluation reused the fixed 32 stochastic tapes at
updates 0, 12, 24 and 48. There is one independent paired training seed, not
32 or 128 independent training samples.

## Direct measurements

| Fixed update | RAW mean return | STRUCT mean return | STRUCT minus RAW |
| --- | ---: | ---: | ---: |
| 0 | 0.6875 | 0.6875 | 0 |
| 12 | 10.7125 | 10.7125 | 0 |
| 24 | 10.7125 | 10.7125 | 0 |
| 48, primary | 10.7125 | 10.7125 | 0 |

All 32 endpoint differences are zero; none are positive or negative. At each
recorded trained evaluation (12, 24, 48), each arm chose REFRESH on all 768
opportunities, with zero SERVE and SAFE_FALLBACK actions. Their endpoint action
sequences agree on every tape. The same-tape fixed ALWAYS_REFRESH return is
10.7125; ALWAYS_SAFE is 4.0625. Both learners improved by 10.025 from their
initial sampled mean, but that common learning gain is not a STRUCT advantage.

The fixed MEI is 0.25 native return per episode. The observed zero is inside it.
This does not establish that the true effect is within the MEI: training-seed
population uncertainty cannot be estimated from this one paired run. The
sampled fixed-policy behavior does not establish that REFRESH is optimal or
that no better same-information policy exists. Matched tuned headroom remains
unmeasured; no census or new baseline training was run for this intake.

## Actual learner and evaluation exposure

| Actual quantity | RAW | STRUCT | Total |
| --- | ---: | ---: | ---: |
| Training episodes | 384 | 384 | 768 |
| Training transitions | 58368 | 58368 | 116736 |
| Training decision opportunities | 9216 | 9216 | 18432 |
| Rollout updates | 48 | 48 | 96 |
| Adam steps and finite loss rows | 768 | 768 | 1536 |
| Evaluation episode executions | 128 | 128 | 256 |
| Evaluation transitions | 19456 | 19456 | 38912 |
| Train plus evaluation transitions | 77824 | 77824 | 155648 |

Training episode IDs cover 0..383 once per arm in the recorded 48 batches.
Each batch contains 16 actual PPO loss rows. Training action-uniform digests
agree across arms at each update. All four full checkpoints per arm are
retained, with model, optimizer and actual counters in the unchanged payload.
Initial parameter L2 is 29.92544937 for both. Final displacement is 5.87944841
for RAW (19.64698455%) and 5.60320139 for STRUCT (18.72386717%). Real parameter
movement and different trained parameters do not establish a mechanism gain.

The two fixed context policies scored the same 32 existing evaluation tapes
once during RAW, with 64 ledger passes and no extra training sample. The unique
engineering fixture at seed 21201 contributed 32 Adam steps and 2432 training
plus 608 evaluation transitions, separately from formal exposure. It passed
the real public-projection, learner movement, native delayed-settlement,
checkpoint and paired publication checks. No additional smoke, old replay,
hidden-policy input, tuning run or unreported seed was added.

## Complete execution cost and receipts

All invocations ran detached under the configured wsl_4070 agent-task supervisor
in /home/wu/hmasd-worktrees/cbsc-direct-return-b02-2c9254f70-20260905,
using /home/wu/.venvs/hmasd/bin/python. Fresh on-node memory admission and the
runner were in each single outer bounded command. The tracker directly observed
all three terminal processes; none remains live.

| Invocation | Supervisor task suffix | Exit | Complete wall s | Peak RSS KiB | Physical/effective available B |
| --- | --- | ---: | ---: | ---: | ---: |
| Engineering check | check | 0 | 6.97 | 533020 | 15676522496 |
| RAW | raw | 0 | 79.69 | 575780 | 15678758912 |
| STRUCT, including paired publication | struct | 0 | 90.78 | 579848 | 15673430016 |

Full task names are cbsc-direct-b02-2c9254f70-<suffix>. The check bound was
175 s; each arm's complete bound was 600 s, including startup, admission,
training/evaluation, checkpoints, primary publication/readback and kill grace.
Both formal calls sum to 170.47 s; adding the unique check gives 177.44 s.
The cumulative focused account is 124.49 + 6.97 = 131.46 / 300 s. The unused
168.54 s does not select another test. Rounded supervisor durations and the
earlier in-process primary-readback times do not replace external complete wall.

These are sums of observed complete invocation walls, not elapsed study time
including Git, editing, transport and collection. Aggregate CPU work was not
collected by these time commands. Wall/RSS are measured; no CPU-efficiency,
C++/GPU speedup or matched old-pipeline speedup is claimed. Python host work and
existing batched Torch PPO completed within the selected per-arm caps. Historical
larger-work counts and failed publication attempts are not a matched timing null.

## Evidence read and bounded checks

Raw inputs are the tracked direct_return_b02_20260905/ directory: both summaries,
all 96 update rows, paired-summary.json, three logs, supervisor wrappers,
admission receipts, exits and external time files. CM's complete technical record
and independent artifact review found no material inconsistency. DM separately
read the card, full final CM record and primary artifacts; recomputed every
endpoint difference and all curve means; checked 256 learned evaluation rows'
decision-plus-settlement arithmetic, fresh episode sequence, all finite loss
counts, pairing identities and exposure. This was artifact analysis, not replay.

CBSC_DIRECT_RETURN_B02_DM_ANALYSIS_20260905.json records that computation.
The run-level CSV has only two rows, one endpoint per arm at seed 21203.
The scientific-tools summarize_runs.py output reports n=1 per arm and no
training-seed standard deviation or confidence interval. Episode differences
are retained as episode descriptions, not independent training runs.

All eight full checkpoints and complete formal output are also retained at:
temp/directions/capability_bound_semantic_currentness/exp/cbsc_direct_return_b02_seed21203_2c9254f70/
in the main local checkout, and under the same relative root in the remote
detached checkout. No evidence root was deleted. The direct path's success does
not diagnose old SIGSEGV/TypeError causes or rehabilitate B1/r05. No scientific,
source-scope or complete-invocation budget deviation was found for B02.

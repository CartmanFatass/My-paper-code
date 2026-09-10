# UCOPE B03 — complete P57 code specification and CM task

## 1. Deliverable, checkout and committed source

Implement the selected B03 common entropy coefficient0 on the existing
UAV opening-prefix runner, preserving every historical route. Return
accepted code, focused test/review evidence and exact source binding for
Root's one7101 pair. P57 supplies implementation through scientific intake;
no additional Portfolio implementation request is needed.

Reuse `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`,
branch `codex/ucope`, same CM `/root/dm_ucope_p47_resume/cm_am_ucope_b02_p47`.
Starting committed research code is
`6374063408208ba67b8cb7c69ebc0babb0f00259`; authoring start
`33a421daabc6567b4d84f3673efc0694835fb5dc` has identical relevant source and
the accepted B02 intake. Card/spec publication adds only documentation.
Do not create an authoring branch or replace this checkout from main.
You are not alone in the repository; preserve others' edits and serialize
overlapping edits/index operations with DM.

Owned code: `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`
(`update`), `study.py` (`Config`, `declared_masters`, `run_pair`, narrow
aggregation refusal), and `scripts/run_ucope_uav_motion_prefix_b01.py`.
Owned checks: existing files under
`tests/experiments/candidates/ucope/uav_motion_prefix_b01/`, with a small
focused entropy test there if needed. A new technical acceptance/review
record in the direction directory is CM-owned. DM owns card, selection
intake, owner/audit, scientific reading and launch handoff.

No policy architecture, sampler/density, environment, adapter, reward,
critic capacity/targets, resource machinery or other direction is owned.

## 2. Exact changed learner semantics

[Card §§1–2](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md#1-authority-and-question)
fix the only scientific algorithm change: explicit total entropy
coefficient **0.0 in both T/G**, instead of historical0.01. The coefficient
applies to the existing summed actual-decision Gaussian plus categorical
entropy, with no replacement bonus, schedule, penalty or target entropy.

Add a backward-compatible `entropy_coef=0.01` argument to the actual
`learner.update` boundary. Its loss remains
`policy_loss + .5*value_loss - entropy_coef*entropy.mean()`. Pass0.0 for
both B03 arms only; legacy/default paths retain0.01. Keep sampling and
trainable log_std, duration gradients from compound likelihood, agent
clipping, masks, advantage normalization, all-held row reduction, four
epochs, Adam, global clipping and RNG consumption unchanged. Keep existing
`entropy` logs as unweighted descriptive values; do not imply they entered
the B03 loss. No helper exists solely to mirror this scalar in a test.

The coefficient belongs only to the update call. Do not pass it through
the collector's `credit_options` dictionary. Existing collector options
remain ratio grouping only. Actual T and G update wiring must be checked.

## 3. New B03 identity and single-pair route

Add `--pair b03` and declare its only real master **7101**. Map it to
`agent_compound` and entropy0.0; p21/p24 remain joint and b02 remains
agent_compound with entropy0.01. Derive the coefficient from the named
pair configuration, not a new user-tunable CLI sweep option. A
backward-compatible field in serialized Config is sufficient.

Real B03 summary binds object `UCOPE-UAV-MOTION-PREFIX-B03`, card
`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md`,
section5, pair`b03`, declared masters`[7101]`, ratio grouping
`agent_compound` and entropy coefficient0.0. Save the same Config in both
checkpoints, and record each learned arm's actual entropy coefficient next
to its existing learning rate. Existing native primary/J arrays, episode
rows, counts, diagnostics, clock/failure handling and publication remain.

B03 has **one matched training pair**. Its native primary is the existing
`primary.T_minus_G.mean` over32 final paired episodes. It needs no new
aggregate implementation, training-endpoint SD or multi-pair summary.
Reject `--pair b03 --aggregate ...` before file/workload access, and reject
direct `aggregate(..., pair='b03')` clearly. Existing p21/p24/b02 aggregate
behavior and all published historical bytes remain unchanged.

Reuse the existing synthetic/tensor boundaries inside focused tests. No
standalone engineering fixture is requested or allocated. Maintaining the
existing fixture capability is allowed; it must retain synthetic mode and
must never be accepted as B03 real evidence. Real wrong masters and mixed
aggregation must be refused before scientific work. No general registry,
manifest/version layer, validator, resume or launcher is introduced.

## 4. Preserved science and focused acceptance

Read [card §§2,4–6](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md#2-preserved-host-information-action-and-credit)
for fixed host, action/information/credit, RNG, counts, primary, class and
caps. Read evidence-spec§§4,11.4,11.8.6–7 only for an actual acceptance
question. The new selection does not replay or repair B02's outcomes.

Required acceptance is a useful complete focused batch:

1. Exercise the actual update loss with fixed tensor/synthetic input to
   show coefficient0 removes the explicit entropy contribution and its
   gradient while native policy/value terms and update counts remain.
   Omitted coefficient and explicit0.01 preserve the historical behavior.
   Preserve stochastic/action-density and categorical policy-credit paths;
   no assertion that every parameter/head must move is added.
2. Extend the existing fake-workload CLI/Config/run_pair test to verify
   both B03 update calls receive0.0, the collector receives the original
   grouping only, and saved configuration/summary/arm identities agree.
   Verify7101 domains, unchanged T/G/H final reset association and counts
   through existing fake boundaries without a real UAV call.
3. Verify the new single-pair rejection boundaries and preserve existing
   historical routing/aggregation/masks/credit tests. Do not create a
   second learner, regression simulator or new cross-platform equality test.
4. One independent review of the changed objective and T/G wiring, owning
   scientific-semantic risks: common coefficient, default compatibility,
   held/duration credit, truthful single-pair identity, same final sampled
   primary. Reviewer reports concrete findings; no new paper review or
   experimental result is requested.

Run the focused directory suite once within300s after implementation;
repeat only for a concrete correction. No separate smoke, warm-up, profile,
benchmark or source-independent execution is required. Existing trusted
acceptance plus the affected-path evidence suffices. This task does not
retroactively make B02's80.578s smoke conform to its60s limit.

## 5. Budget, stop and collection boundary

Engineering scope§4: none; source≤2000 and runner≤600 lines remain. No new
scientific invocation belongs to CM implementation/review. Stop source
work when accepted, with a clean explicit-path commit and immediate push,
or return one concrete conformance/scope blocker with affected facts.
Reuse the same executor for corrections. Keep the original source, card,
checks and remaining issue inspectable; do not rewrite this contract.

After DM binding and Root integration, P57 permits exactly one remote
7101 T/G/H pair:286720 team steps/2048 Adam/96 final episodes,
1800s per complete T/G arm and3600s through full publication/exit. Fresh
resource admission precedes any scientific root/model. Root owns exact-SHA
staging, launch and observation; CM retains collection/technical acceptance
and DM all-outcome intake. No retry, second pair, extra/H-completion
evaluation, tuning or automatic cap growth follows from engineering work.

## 6. Complete five-item dispatch

- **Deliverable:** implement and technically accept B03 entropy0 for the
  selected in-family comparison, with the exact source for one7101 pair.
- **Owned paths/entry points:** §1's existing learner/study/runner and
  focused directory checks; existing direction checkout, CM-owned
  technical/review record only.
- **Preserved semantics:** card§§2,4–6 and this spec§§2–3; scalar bonus
  only, both arms, real stochastic learning/native final primary, historical
  routes and failed evidence preserved.
- **Acceptance:** §4's actual objective and wiring/default/identity checks,
  one≤300s directory suite and independent semantic review; no standalone smoke.
- **Budget/stop:** §5 and card§6; implementation/review has zero scientific
  invocation. Return accepted explicit-path commit/push or a concrete gap.

The complete source/card/spec/check set is returned to Root before CM
coding. `CM_MODEL_COMPARISON_20260907.md` records all three batches complete;
this new task is excluded from further enrollment for that concrete reason,
not silently bypassed or replaced by reused comparison work.

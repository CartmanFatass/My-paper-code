Claim: A read-only replay of the retained seed-11 checkpoint can locate which observed handover stages were absent on its original sixteen B01 prefix rows.
Binding MARL structure: systems / information flow. The question arises from two agents' role-specific observations, preparation messages and ownership-transfer timing under partial observation.

# DISH retained-prefix trigger funnel A01 — science card

Date: 2026-09-04 PDT. Object `DISH-PREFIX-TRIGGER-FUNNEL-A01`, **A / RECON**.
DM `/root/dm_amx_n3_continue`; selected in `N3_DISH_B01_C04_COMPLETE_INTAKE_20260904.md`.
This card precedes diagnostic implementation or result activity.

## 1. Question, claim ceiling and non-goals

The complete B01 result is FTS-B0: all 48 rows across three 64-update checkpoints had no
first application-valid handover. Which observed stage first fails to appear on the original
seed-11 sixteen-row prefix: live decision opportunity, prepare proposal, preparation/delivery,
commit proposal, emitted intent or application validity?

This object produces a path/measurement fact about one retained checkpoint. It cannot show
source value, causal benefit of changing a stage, physical impossibility under other policies,
general proposal competence, natural trigger prevalence, headroom or source equivalence.
It is one diagnostic rung inside the accepted B source-selection ladder, not a new family.

No learning, checkpoint selection, new seed, trigger forcing, altered threshold, source fork,
counterfactual policy, additional arm, replay-containment performance claim, R02 repair,
VSP-05 policy-veto comparison, baseline tuning, or lifecycle/priority action is in scope.

## 2. Fixed evidence input and original path

- Retained checkpoint: original B01 seed 11, 64 updates / 262,144 transitions / 2,048 optimizer
  steps, source `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`, 2,070,711 bytes.
- Existing file on `wsl_4070`:
  `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c/temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1/checkpoint.pt`.
  Its input SHA256 is `0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa`.
  This identifies existing evidence for staging/collection; no hash-chain or provenance gate
  is requested. Keep the original artifact untouched.
- Reuse original `seed_master(11)`, `panel()` and `_reset_row()`, including all sixteen
  packages x schedules x speeds x slots, block 0, degraded mask and original coordinate law.
- Reuse fresh width-one STRUCTURED recurrent evaluation state and checkpoint normalization;
  one Torch CPU thread, FP32 policy, float64 native physics, deterministic original sampler.
- At each tick retain exactly `prepare_b01_application -> step_rows(recurrent_prepared=True)
  -> complete_b01_tick -> apply_native_promotion`. Do not advance policy twice to obtain
  logits or mutate its normalization, recurrence, decisions, native state or random streams.
- Maximum 1,200 primitive ticks per row. At a first `prepared.origin_valid`, record that
  point and end that row without a source fork. All original rows lacked such a point.
  Terminal padding to the original 1,200-tick ceiling is retained and counted separately.

The strongest same-input reference is the original seed-11 B01 prefix summary: sixteen
no-trigger rows / 19,200 total ticks. This is a replay-reference comparison, not a treatment
effect. Other two checkpoints supply contextual B evidence only and are not diagnostic runs.

## 3. Event-to-measurement trace and live explanations

`route/degradation and physical survival -> current owner/standby observations -> policy action
at live renewal -> prepare latch/warmup -> common source and snapshot/readiness arrivals ->
commit action with matching protocol version -> emitted pending intent -> delivery/certificate/
timing eligibility -> first-valid source-fork opportunity`.

Always two physical entities; owner role, physical identity and recurrent active/shadow slot
remain separate. There is no join/leave/rejoin, replacement, survivor-state transfer or new
partner training. The diagnostic separates primitive ticks, nonterminal ticks and live renewal
opportunities; terminal padding is not an opportunity to act.

Live explanations are lack of live opportunities, no learned prepare/commit proposals,
preparation or shared-information delivery failure, temporal misalignment, undelivered intent,
failed certificate/application conditions, and a replay/measurement discrepancy. Counts locate
observed absence; they cannot identify a causal repair by themselves.

## 4. Required measurements and reading rule

Each row retains its coordinate, owner/role identity and original trigger reference. Collect
counts and first observed tick for each applicable stage, plus these direct quantities:

1. Total prefix ticks; live (nonterminal) ticks; live renewal opportunities; first terminal
   tick if present, with existing separation and battery state recorded without assigning a
   cause from text; native service ticks as context, not a performance contrast.
2. Owner-indexed prepare/commit outputs on live renewal opportunities and their intersection
   with available preparation/version state. Raw policy outputs must be read from the one
   original `step_rows` result; no extra stochastic sample or policy pass.
3. Preparation latch, maximum warmup, common-source availability, snapshot/readiness delivery
   and accepted states, and existing snapshot/readiness timestamps. Record counts for the
   native version-ready relation (readiness accepted, readiness tick equals current tick minus
   one, readiness snapshot tick equals snapshot tick), and its coincidence with live renewal,
   latch and commit. Any derived relation is explicitly diagnostic, never a replacement FSM.
4. Pending intents emitted at the completion boundary; pending intent at the next prepared
   boundary; partition the latter by margin below 6 versus at least 6 and by certificate.
   A low-margin intent is cleared without a nonzero `application_reason`, so it must remain
   distinct from no pending intent. Preserve relevant origin/snapshot/readiness times.
5. Existing `prepared.origin_valid`, post-completion `application_reason` histogram,
   `cas_applied`, and delta of the cumulative `invalid_commit` counter. Do not treat reason
   zero as successful application without `cas_applied` or a recorded valid boundary.

Use existing public observations or read-only copies of existing typed prepared/native
snapshots. Counts and compact first-occurrence snapshots suffice; no full-tick trace archive,
new native ABI, generic observer framework or changed production source is requested.

**Prospective boundary convention (DM refinement before implementation).** The prepared
boundary is primitive tick `t` after arrivals; completion advances native tick to `t+1`,
but emissions and first-occurrence labels are attributed to action/origin tick `t`.
Publish separate live prepared and live completion latch counts. Latch presence for the
row rule means observed at **either** boundary, so a latch created on the last live
completion before terminal is not erased. Version-ready values are read before intent
emission at action tick `t`; coincidence with the commit gate uses that relation and
the completion latch, since native can latch before emitting an intent on the same tick.
This is a measurement convention, not a rewritten native gate. Snapshot delivery counts
actual delivery events. A live completion has a nonterminal prepared input, even if its
result first becomes terminal. Terminal-prepared ticks remain in the original policy/
native padding loop but not live/proposal denominators. Read cumulative invalid-commit
deltas from copied native state, because terminal outputs may be zero-filled. Report
inspected prepared boundaries separately from completed ticks if an unexpected valid
boundary ends a row before completion. The maximum sixteen-by-1,200 inspection budget
and original no-trigger reference are unchanged.

For each no-trigger row label the first absent observed stage in this order:
`NO_LIVE_RENEWAL`, `NO_PREPARE_PROPOSAL`, `PREPARATION_SUPPORT_GAP` (latch at either live
boundary, then snapshot
delivery, then version-ready, with the missing stage named), `NO_COMMIT_PROPOSAL`,
`NO_EMITTED_INTENT`, else `PENDING_INTENT_NOT_APPLICATION_VALID`. Publish the underlying
counts as well: a first-absent label is not a claim that later gates would pass.

The complete object result is **A01-PREFIX-FUNNEL-OBSERVED** when all sixteen rows and required
measurements are complete and the original no-trigger/prefix-count reference is reproduced.
Report the per-row labels and their counts; do not use majority vote as a mechanism verdict.
If a trigger or prefix-reference disagreement appears, report **A01-REPLAY-DISCREPANCY** with
the observed difference and ask CM to reproduce the failing step over the recorded bytes before
classifying it. Missing required measurements yield an incomplete diagnostic, not a negative.
This descriptive A reading does not rewrite B01's completed FTS-B0 rule.

## 5. Predictions, MEI, exposure and headroom

DM prediction: **A01-PREFIX-FUNNEL-OBSERVED**, with preparation support absent on most rows;
the B01 snapshot-normalizer count was zero and no source fork appeared, but those observations
do not distinguish no proposal from failed delivery. The funnel is needed to test that reading.
Owner prediction: `not taken (unattended)`. The existing B01 ladder prediction item remains
the one owner prediction request; this diagnostic does not open a duplicate ladder.

MEI for this path diagnostic: one observed live occurrence of a stage previously absent from
the summary is decision-relevant. This is an event-count resolution, not a return effect size;
the B01 five-service-tick MEI remains unmeasured. Headroom on a tuned same-information B01
baseline is absent; the diagnostic does not train or estimate one.

Machine-generated exposure line reports **zero new transitions used for training, zero learner
updates, zero optimizer steps and zero parameter displacement during diagnosis**; the model is
read-only. Also report inherited 2,048 optimizer steps, initial/final norms
38.19731474061207 / 41.78517869974931 and relative displacement 0.42465718774783356 from B01.
Zero new learning is correct for A/RECON and never presented as a new B learner observation.

How this will be interpreted: an observed stage occurrence narrows the gap to a later link;
its complete absence locates one missing exposure on this checkpoint; a replay discrepancy
requires exact-byte technical diagnosis before any source inference. None establishes what
would happen after repairing the stage. Recommend the next smallest measurement or B rung
only after intake, without automatically increasing budget or forcing a trigger.

## 6. Resource route, cost and stop rule

Portable across configured CPU nodes under the original FP32 policy/float64-native semantics;
no host/device quantity is part of the estimand. Route remote-first to `wsl_4070` using the
current `.codex/hmasd-compute.toml`, exact committed/pushed diagnostic bytes in a detached
worktree and existing `agent-task`. A prospective node change requires a fresh destination
receipt and the predeclared portability boundary; it cannot change precision or RNG.

One invocation, seed 11 only, sixteen rows / at most 19,200 prefix ticks, no source arms.
Runner `project-cost` emits the inherited fixed evaluation allowance with original margin:
`projected_seconds = 1.5 * (0 * 10.672341100056656 + 300) = 450 seconds`.
The 300-second allowance originally covered this panel plus branches/serialization/compilation;
no learner or branches are run here. Machine-time cap **600 seconds** for the one diagnostic
invocation, checked at each tick; no row/seed replacement or efficacy stop. This is not a sweep;
the single replay-reference path receives the entire 450-second projection. If implementation
cannot fit that meaning-complete surface, CM returns the concrete excess without launching.

Immediately before the invocation on its destination, join
`python scripts/hmasd_resource_preflight.py admit-memory --out <separate-receipt>` and the exact
diagnostic command by `&&`; require physical and effective available memory each at least 4 GiB.
Receipt is outside the initially absent output directory. Do not create a model/RNG master or
scientific output before admission. Report wall and peak RSS; missing resource telemetry is
`resources_unmeasured`, not invalidation of these measurement facts.

## 7. Engineering objective and technical acceptance

CM owns the smallest implementation and technical return; implementers remain in their own
worktrees. Own only a diagnostic module under
`experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/`,
`scripts/run_dish_prefix_trigger_funnel_a01.py`, focused tests under the corresponding research
test directory, A01 technical result documents, and runtime outputs under
`temp/directions/degraded_incumbent_shadow_handover/exp/n3_prefix_funnel_a01_20260904/`.
DM owns this card, intake, owner items and DIRECTION; Root owns Portfolio/shared audit.

**Engineering-scope section 4 declaration: this object needs none of the default-prohibited
machinery.** Existing scientific state counters are the question's measurements, not added
resource telemetry. No core/production-kernel changes, provenance/currentness guard, registry,
resume/retry/lease system, full trace store or new orchestration are requested. Remain below
2,000 new non-test lines, runner 600 and orchestration 30%; expected surface is far smaller.

One under-60-second toy end-to-end smoke through the actual diagnostic publication path and
focused row-reading tests suffice. Preserve dtype/RNG/checkpoint and side effects. A single
bounded check that the diagnostic does not change the original prefix on its toy path is
useful; no repeated B01 suite or learner test is requested. Commit/push exact bytes before
remote verification/results. CM must inspect required measurements and the reference match;
test pass/process exit cannot establish a path finding or a source benefit.

Deliver one `summary.json`, existing-input reference, receipt and supervisor log. After an
accepted long-running handle, hand node/task/source/cwd/output/receipt/bound directly to
`/root/tracker_tl_experiments`; CM releases polling and collects on its terminal reminder.
DM takes in the complete observation and selects the next rung. No successor is preauthorized.

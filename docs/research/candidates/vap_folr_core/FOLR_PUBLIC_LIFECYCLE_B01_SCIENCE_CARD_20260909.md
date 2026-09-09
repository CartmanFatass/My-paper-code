Claim: on lifecycle-visible easy Traffic Junction, trained survivor-state RETAIN and event-triggered RESET may differ in final native episode return.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR-PUBLIC-LIFECYCLE-B01 — one matched class-B pair

## 1. Selection, authority and question

**B/EXPLORE; selected and frozen for the explicit Root allocation of 2026-09-09.**
Convergence selected the public-lifecycle scope in the complete
[response at `653727422183894b2f4d1c82a458fbc55aaf6ee0`](pro_packets/20260909_p78_public_lifecycle_convergence/archive/RESPONSE.md).
That decision grants no compute itself. Root subsequently allocated this card, bounded CM
engineering/review and exactly one new matched RETAIN/RESET pair; the exact instruction is in
[recovery facts](pro_packets/20260909_p78_public_lifecycle_convergence/archive/RECOVERY_INTAKE_FACTS_20260909.json).
The DM selects the configuration below under ordinary object-tier delegation, recorded in
[P78 intake §8](FOLR_P78_LIFETIME_INTERFACE_QUESTION_INTAKE_20260909.md#8-formed-convergence-decision-and-new-root-allocation).

Question: after both learners adapt to their own state rule, what is the final full-episode
native-return difference caused by retaining versus indiscriminately clearing true survivors'
GRU history at actual roster events? This measures a trained-system difference, including
optimization and partner co-adaptation. It does not isolate one stored feature's causal effect.
No typed-state novelty, strictly-self ancestry, information necessity, stable superiority,
original-CAMA performance, transfer, UAV or Portfolio claim is sought. This new information
protocol does not reopen B3/B04, P77's unchanged-interface boundary, or older FOLR/DISH pauses.

## 2. Native host, information and state intervention

Use CAMA Traffic Junction at source `1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58`, easy,
vision 1: five slots, 7-by-7 grid, five actions, 20 primitive steps, native reward and native
goal/collision removal followed by spawn. Use the ordinary episode-reset route with no
curriculum argument, preserving its initialized add rate 0.1. Native waiting behavior,
removal side effects and global NumPy draw order are preserved. No artificial event,
counterfactual simulator call, event tape or reward modification is introduced.

The accepted interface is [P78 §§2–3](FOLR_P78_LIFETIME_INTERFACE_QUESTION_INTAKE_20260909.md#2-exact-prospective-interface-and-the-information-change).
During the actual step record departures `D` only when the removed car was active and births
`B` at actual native activations, including same-step refill. Do not suppress any original
remove call or side effect. Define true continuation
`C = A_before & A_after & ~D & ~B` and global completed-event bit `E = any(D | B)`.
Emit these only after native reward/removal/spawn, before the next actor update. A trip is an
episode/slot/activation occurrence; slot reuse never continues the predecessor's memory.

Both fixed state managers receive the active mask, B, C and E. Both learned actors receive
the same source locally masked entity-attention representation plus global E and own B,
appended immediately before `fc2`, the existing GRU input projection. No full event-list,
hidden position/goal, reason, numeric epoch, other memory or future-event feature is added.
The source centralized mixer has the same source entity/active-mask training information in
both arms; the two event scalars extend actor input, not its global feature set.

Both arms zero inactive state and start new trips with zero incoming state. Their preceding
action feature is retained only for C; otherwise it is zero. Apply this common rule to each
entity's previous-action feature before attention. A newborn processes its current observation
from fresh state; inactive outgoing hidden state stays zero. On episode reset, all state is
zero, the initially active car has own B=1, and E=0.

- **RETAIN:** carry the full causal GRU state of C survivors into the next actor update.
- **RESET:** when E=1, zero C survivors' incoming GRU state **before** processing that next
  observation. Otherwise carry it. Common entrant/inactive handling is identical to RETAIN.

Apply each arm's rule in acting and in both online and target recurrent replay unrolls, using
metadata aligned with the next observation. Clearing after the GRU update is a different
intervention. RESET still has current input, preceding action and history rebuilt between
events; it is not information-free. Full GRU history can include teammate observations.
The native episode ends at step 20 with no terminal bootstrap. Compute the source terminal
controller/target pass as needed, but do not count it as another native action or survivor
control opportunity. Agent arrivals/departures do not terminate the cooperative episode.

## 3. Fixed common learner, randomness and selection

Reuse the source generic entity-attention GRU with FlexQMixer/Q-learning, not CAMA's coach,
message, imagination or intrinsic-reward learner. This architecture is the competent generic
comparator; competence after this finite exposure is unmeasured, not a tuning prerequisite.
Use ordinary in-process batches, one environment and one training process per arm.

| Quantity | Both arms |
| --- | --- |
| Actor | Entity input includes trip-consistent last action; attention width 128, four heads; `self_loc=false`, `double_attn=false`, `repeat_attn=0`, no pooling/message; GRU 64; five Q outputs |
| Mixer/targets | Source FlexQMixer, mixing width 32, hypernet width 128, softmax mixing weights, double Q; target copies every 200 complete training episodes |
| Optimization | RMSprop, lr 0.0005, alpha 0.99, epsilon 0.00001, gradient norm clip 10; primitive-step gamma 0.99 |
| Replay | Capacity 5,000 complete episodes; uniformly sample 32 complete episodes without replacement; one optimizer step after each new episode from episode 32 through 5,000 |
| Exploration | Linear epsilon 1.0 to 0.05 over the first 50,000 training native ticks, then 0.05; use cumulative ticks at the start of each collected episode |
| Evaluation | One final frozen checkpoint after episode 5,000/update 4,969; 32 greedy episodes, epsilon zero; each policy uses its trained state rule |
| Numerical boundary | CPU FP32 learner, source native NumPy environment arithmetic; one Torch compute thread and one interop thread |

The shorter common epsilon anneal is deliberate: half the 100,000-tick exposure remains at
the final exploration rate. The source 500,000-tick anneal would still be highly exploratory
at this budget. Serial collection and one update/new episode replace the source parallel-eight,
eight-update collection configuration explicitly. No other architecture or optimizer setting
is tuned. Disable periodic test episodes, checkpoint selection and extra final evaluations.

**Training seed 7801; final evaluation seed 107801.** Reset Python, global NumPy and Torch
random state to the common training seed independently at the beginning of each arm, before
model initialization. Pair initial actor/mixer parameters by identical construction order.
The real environment retains global NumPy consumption; source-compatible replay sampling
may share that stream. Use the separate common final-evaluation seed at the final evaluator.
Record actual RNG plumbing; do not replace native draws with per-car streams or force equal
realized traffic. Different policies can induce different paths and event totals despite
paired initial randomness. One matched training pair is the independent learning unit.

## 4. Primary reading, MEI and predictions

Let `J_RETAIN` and `J_RESET` be the means of all 32 final native episode returns, and
`d = J_RETAIN - J_RESET`. Preserve both means and all 32 returns per arm. The primary is the
full-episode native reward sum, not an event-conditioned subset, normalization, transient,
or test-time damage to RETAIN-trained weights. Training returns are training exposure.

**Absolute MEI = 1.0 native return unit per episode.** One unit is one net unit of native
target-progress reward, and one tenth of a single -10 collision penalty; this gives a concrete
scale without dividing by a possibly small or negative baseline. It is not B04's MEI.
The card's reading rule is:

- `d >= 1.0`: `RETAIN_ABOVE_MEI`, a preliminary trained-system advantage at this configuration.
- `d <= -1.0`: `RESET_ABOVE_MEI`, the opposite-sign result, retained on the same terms.
- `-1.0 < d < 1.0`: `WITHIN_MEI`, no MEI-sized observed gap; not an equivalence statement.

How the result will be interpreted: a RETAIN advantage would motivate considering one
independent-seed follow-up on erasure cost; a RESET advantage would motivate a follow-up on
forgetting/learning-path benefit; an inside-MEI result would favor retaining the ordinary
generic path without another immediate investment. These are recommendations for intake,
not automatic successors. No follow-up is allocated here. Scarce survivor-control exposure
limits the erasure interpretation. Zero such opportunities cannot support a post-event
survivor-control claim, while trustworthy full-episode returns remain reportable under §11.8.7.

**DM prediction before implementation/results:** WITHIN_MEI is the leading expectation;
own goal/position are reobserved and the horizon is short. A larger RETAIN gain remains
plausible from recently observed traffic now outside view; RESET may help discard obsolete
context. Owner prediction slot: **not taken (unattended)**. One training pair cannot estimate
training-seed population uncertainty; evaluation variation is conditional rollout variation.

There is no tuned headroom record on this lifecycle-visible host. B04's first-action scalar
host differs in observations, actions, information and budget and supplies no reusable
baseline here. The source generic learner is reused; no baseline-tuning object is added.

## 5. Computed exposure, cost and stop boundary

The [machine-generated plan](evidence/2026-09-09-folr-public-lifecycle-b01-plan.json) supplies
configuration arithmetic without target import, model creation or simulation.

| Work quantity | Per arm | Whole pair |
| --- | ---: | ---: |
| Training episodes/native ticks | 5,000 / 100,000 | 10,000 / 200,000 |
| RMSprop steps | 4,969 | 9,938 |
| Final evaluation episodes/native ticks | 32 / 640 | 64 / 1,280 |
| Total native ticks | 100,640 | 201,280 |
| Acting GRU row forwards, terminal pass included | 528,360 | 1,056,720 |
| Online-plus-target replay GRU row forwards | 33,391,680 | 66,783,360 |

Dominant replay work is `arms × 4969 × 32 episodes × 21 positions × 5 slots × 2 passes`,
plus online backward and mixer computation. Rows and reused TD targets are not independent
training samples. The equivalent learner-exposure line is **per arm 100,000 real native
training ticks, 4,969 trainable actor/mixer RMSprop steps at lr=0.0005, and 32 final greedy
evaluation episodes**. Nominal `lr × steps = 2.4845` is not measured parameter displacement.
No weight freeze or zero-learning-rate segment prevents the real learner from moving.

**Wall projection remains unknown.** The complete cap is **1,800 seconds per logical arm
invocation, 3,600 seconds for the pair**, including imports/initialization, training, final
evaluation and publication. These caps are limits, not runtime predictions. B04's 40.371825
seconds is not a cost model for this recurrent learner. Supporting changed-boundary checks
have a separate **300-second total** ceiling, including any necessary correction reruns.
No pilot, cost-only run, tuning sweep, extra checkpoint evaluation, retry or automatic
successor is allocated. Execute RETAIN then RESET; never stop on an intact scientific sign.
On failed admission, invocation cap, damaged primary path or exhausted engineering/check
budget, preserve the exact boundary and return without another scientific invocation.

## 6. Required counts, engineering scope and acceptance

Name the following §4 telemetry quantities because they bound this specific state-intervention
claim: **births, departures, true-survivor event opportunities and actual survivor resets**,
each totaled separately for training and final evaluation in each arm. They come from the same
native path with no extra episodes or framework. Birth/departure totals count actual native
steps, including terminal events, and exclude the single initial birth per episode. A survivor
opportunity is one C-and-E car followed by another native action. A reset counts the actual
RESET rule applied at such a control update, even if the incoming vector happened to be zero.
RETAIN has no survivor resets. Common entrant/episode clears, terminal computational clears
and replayed rows are not new native survivor resets or opportunities.

No other new engineering-scope §4 machinery is needed: no distributed collection, search,
registry, runtime validation/provenance guard, resume/retry system, telemetry framework or
repeated smoke. Use the existing supervisor and required resource receipt. A single final
learner checkpoint per arm may support its declared evaluation and evidence; no resume path
or periodic checkpoint evaluation is introduced. Report wall time/peak RSS, mandatory real
transition/update/evaluation counts and the exposure line in the ordinary summary.

CM owns implementation, independent changed-semantic review, focused acceptance, exact launch,
sole observation and collection. Verification covers reward/native RNG preservation, hidden
same-step replacement, fresh entrants/inactive state, information timing/parity, previous
actions, acting/online/target unroll agreement, terminal opportunity accounting and the primary
return/rule. Use proportionate controlled boundary fixtures; no learning pilot or outcome
search is a check. Keep new non-test source within 2,000 lines and the runner within 600 lines.
Return unrequested machinery or a concrete budget breach instead of absorbing it silently.

Use the existing `C:/Projects/HMASD-worktrees/codex-vap-folr` / `codex/vap-folr` checkout.
New code belongs in `experiments/candidates/vap_folr_core/public_lifecycle_b01/`, its mirrored
`tests/experiments/candidates/vap_folr_core/public_lifecycle_b01/`, and
`scripts/run_folr_public_lifecycle_b01.py`. Reuse the pinned source already retrieved under
`temp/directions/vap_folr_core/source/p77_cama_1d8d6f8c/CAMA/`; inspect only concrete missing
dependencies at the same upstream commit and retain relevant source attribution.

Portable result-bearing work uses configured `hmasd-wsl-node`, its interpreter and detached
exact-committed-SHA worktree through `agent-task`. Host identity is not the estimand; CPU,
FP32 and thread counts stay fixed. Immediately before **each arm**, join destination-node
`admit-memory` and the exact runner with `&&`; require physical/effective available memory
at least 4 GiB before scientific roots, model or RNG initialization. Commit/push exact source
before execution. This allocation stops on admission failure and grants no local fallback.
CM records actual source SHA, command, node/cwd, supervisor handle, receipts and result roots
in the existing technical result record, and observes through collection. It returns the
two arm summaries and primary comparison to DM for scientific intake. Missing resource
telemetry is `resources_unmeasured`; scientific conformance and performance remain separate.

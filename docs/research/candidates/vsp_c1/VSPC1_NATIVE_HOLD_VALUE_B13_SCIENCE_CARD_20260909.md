Claim under test: adding the existing remaining-hold gate to the intact width-133 ordinary critic improves final-768 sampled native return by more than absolute .01 in one fresh matched training pair.
Binding MARL structure: (b) temporal abstraction or termination, with five co-adapting agents retaining separate partial-observation histories.

# VSPC1-NATIVE-HOLD-VALUE-B13 — B/EXPLORE, P80

Current state: defined prospectively under Root's P80 allocation; no scientific submission yet.
Design authority is the complete [P79 Pro decision §§3–6](pro_packets/20260909_native_hold_value_post_b12_convergence/archive/RESPONSE.md)
at `77687230cb1f3898e55c21d23c05ba1840d820ea`, accepted in the
[P79 intake](VSPC1_NATIVE_HOLD_VALUE_P79_CONVERGENCE_INTAKE_20260909.md).
Root separately allocates implementation, changed-boundary review/checks and exactly one
remote submission through technical and scientific intake. This is the selected same-family
comparison, **not RECAST**; the P79 receipt intake itself allocated no experiment.

## 1. Question, evidence and claim ceiling

At the same information, duration-selecting actor, normalized value training and 768-episode
budget, does adding the existing gate to the complete ordinary critic improve the final
sampled policy's full-episode native return? This is an outcome-informed new B package
comparison, not a correction to the valid older near-equal-parameter comparisons.

Early 512 gains and retaining the strongest attained ordinary body support this bounded
question. All three old relative changes were negative, none of their 768 Deltas was UP,
and 8503's late Delta was −.0735897558 with 31/32 adverse paired identities. Older final-only
512/768, width128, unnormalized and quarantined results remain separate. No result is erased.
The maximum claim is one finite-budget local performance signal or counterexample. This
cannot establish stable superiority, equivalence, unique hold credit, the cause of the old
650-parameter tradeoff, tuned competence, transfer, C promotion or formal UAV entry.

Reuse the verified local-library evidence in [P79 question §5](VSPC1_NATIVE_HOLD_VALUE_P79_QUESTION_20260909.md)
and its [machine facts, literature](VSPC1_NATIVE_HOLD_VALUE_P79_PREPARATION_FACTS_20260909.json):
MARC uses per-agent local-observation action-value critics and SAC, unlike this centralized
state-value/PPO study. Its verified page-5 passages do not prescribe this gate or require
conversion to graphs/SAC. Prior PPO/ACAC/UTE/MVD setting distinctions remain applicable.
This accepted comparison adds no unresolved literature question or fresh search requirement.

## 2. Selected structure and preserved scientific path

Both ordinary bodies are **136→128→133→1**, with tanh after both hidden layers. Let
`r=remaining/4` in zero-based input columns `(119,123,127,131,135)`, `x` the other 131
existing inputs, `z=W_x x+b`, and `B` the five ordinary first-layer hold columns:

- MLP-V: `h1=tanh(z+B r)`.
- GATED-V: `h1=tanh(z*(1+A r)+B r)`, with bias-free `A` of shape `128×5` initialized to zero.
- Both: `Vhat=W3 tanh(W2 h1+b2)+b3`.

Common initialization supplies the complete ordinary body to both arms, including the
five private-random extra second-layer rows/biases and five initially zero extra output
weights. Each arm owns independent mutable parameters, optimizers, moments and RNG objects;
zero-gate construction does not draw behavior randomness. Critic counts are **35467 GATED
versus 34827 MLP**, +640 (+1.8376547%). This is explicitly not capacity matched. A=0 gives
the common mathematical initial function; ordinary FP32 decomposition can change rounding.
Use ordinary dtype/scale-appropriate numerical checks, not bit equality or an exact function-class proof.

The current `native_hold_value_b01/critic.py::models` widens only MLP; implementation must
construct the complete body for both selected B13 arms before wrapping the treatment gate.
Record actual structure/counts in checkpoints and output, preserving older bindings when
reusing shared code. `native_hold_value_b05/critic.py::WideCritic` already defines the extra
rows. Do not merely relabel the old 34817-parameter GATED critic.

Preserve [B12 card §2](VSPC1_NATIVE_HOLD_VALUE_B12_SCIENCE_CARD_20260909.md#2-preserved-science-and-new-binding)
and the accepted UCOPE dependency bytes in this checkout: five fixed UAV members/50 users,
108-dimensional local actor inputs, shared GRU weights with separate entity histories,
legal velocity and opening t0 duration 1/4 actions, observation/history updates while held,
and ordinary feedback from t4. There are no joins/leaves/rejoins, slot replacement or
censoring changes. The 136-dimensional critic input is assembled before the current decision;
t0 remaining is zero and never contains the just-selected duration. Nonzero r can occur only
at t1–3. The critic never selects actions. No duration-Q, new renewal intervention or privileged input.

Opening duration → entity-owned residual hold → centralized value and joint optimization →
local recurrent actor → motion/service → native reward is the proposed path. Gamma=1 over
all 256 primitive team steps preserves the existing full-episode return-to-go and termination.
Merge 512 native targets once per two-episode rollout into cumulative FP32 value moments.
Use normalized targets for value squared loss, decoded native collected values for detached
rollout-normalized advantages, fixed across four full-rollout epochs. Preserve actual decision
masks, agent-compound PPO, learning rate/loss weights, entropy .01, joint clipping and 32-step
recurrent gradient chunks. Evaluation and H never update moments. Shared clipping, moments,
FP32, generic capacity, initialization and partner co-adaptation remain alternatives; sparse
direct gate exposure is neither a return-effect bound nor proof of mechanism value.

## 3. Master, private domains and prospective predictions

Select **master 8601**, `b=860100000`, once before output. The bounded whole-token search
over the current direction/scripts/tests found no previous 8601/B13 binding. Actual Config
AST [arithmetic](VSPC1_NATIVE_HOLD_VALUE_B13_PREPARATION_COUNTS_20260909.json) gives 868 distinct
integer keys, zero overlap with twelve earlier native-hold master domains and zero train/eval
reset overlap. This is a bounded namespace check, not a global freshness guarantee.

| Purpose | Domain |
| --- | --- |
| Common / extra ordinary initialization | 860100011 / 860100012 |
| Private per-arm training velocity / duration | 860100021 / 860100022 |
| Training constructor / resets e=0..767 | 860101000 / 860101000..860101767 |
| Evaluation constructor / resets e=0..31 | 860102000 / 860102000..860102031 |
| Fresh private per-episode evaluation velocity / duration | 860103000..860103031 / 860104000..860104031 |

Constructor and first reset deliberately use the same corresponding key. Arms share initial
parameter values and exogenous reset keys, not mutable random generators, recurrent state,
on-policy data, moments or optimizers. Branch divergence does not promise identical tickwise
action noise. H uses the new 32 reset identities once in MLP's evaluation environment; it
sends the existing zero velocity commands, builds no learner and is not tuned. Reuse no old
weights, moments, layouts, checkpoints, training/evaluation rows or H measurements.

The independent scientific unit is **one matched training pair (two fits)**. Agents, episodes,
updates and evaluation identities are not independent training replicates. No cross-protocol
pooling, old C estimate or claim of replicating the old 512→768 change is produced.

Pro's retained prospective prediction: **NO_UP, probability .65**, event `Delta_new<=.01`;
it includes WITHIN and DOWN. DM's separate prospective prediction: **WITHIN, probability .45**,
event `-.01<=Delta_new<=.01`. Retaining the full ordinary body makes a small net gate effect
plausible; the strong old negative and optimization sensitivity leave DOWN and UP credible.
The DM has read Pro's forecast; these are distinct subjective forecasts, not independent
empirical evidence. Score each event with the complete trustworthy primary only; retain the
actual point region and conditional noise. Owner prediction: **not taken (unattended)** unless
an actual reply exists. Prior predictions and scores remain unchanged.

## 4. Final-only measurement, MEI and reading rule

Train continuously to 768 episodes and complete the final update. Evaluate each final policy
once on its private evaluation environment and generators; **four train/eval environments**
total. No initial or 512 panel, best checkpoint, extra evaluation or old-model reevaluation.
Deleting 512 must not use the old `fixed_endpoints=False` shared environment path. Evaluation
schedule and environment isolation must be separate in the new path; moments remain frozen.

For the same 32 `(episode, reset_seed)` identities, `J=reward_sum/256` and primary
`Delta_new=mean_i(J_GATED,i-J_MLP,i)`. Preserve all three controller means, all 32 differences
for GATED−MLP, GATED−H and MLP−H, and every negative identity. Each contrast's conditional SE
is sample SD of its 32 differences divided by sqrt(32). These are conditional panel errors,
not training-population uncertainty; `(GATED−H)−(MLP−H)=Delta_new` is an identity, not replication.

Absolute **MEI .01** retains the selected native scale: one continuously served user adds
.7/50=.014 before the quality term changes. It guarantees no fixed number of served users.
Tuned same-information headroom is **absent**. H is an untuned attained control, not an upper
or competence certificate. Reuse the host's information/action/learner semantics; the new
critic treatment and final-only schedule do not match the old two-panel measurement budget.
No tuned baseline package matching this complete new protocol is available or required.

| Observation | Reading rule and bounded consequence |
| --- | --- |
| Complete trustworthy Delta_new>.01 | UP: local intact-body-plus-gate performance signal; with native/H levels and all losses, may recommend a separately selected one or two fresh pairs. None is allocated here. |
| -.01<=Delta_new<=.01, including both boundaries | WITHIN: no selected-scale additive-gate advantage; preserve small sign and noise, and stop this candidate's automatic advancement. Not equivalence. |
| Delta_new<-.01 | DOWN: local native counterexample for this additive package; favor the ordinary body for this instance. Not broad hold-credit or K4 failure. |
| Learned mean or episode below H | Retain all losses separately. Relative improvement alone does not establish useful control, optimality or tuned competence. |
| Conditional noise reaches MEI | Report point region and uncertainty; no extra episodes to cross or resolve a boundary. |
| H incomplete, learned pair trustworthy | Report the intact primary and limit only H-dependent conclusions; no independent H refill. |
| Learned endpoint or primary dependency damaged | No dependent primary judgment; retain independently trustworthy arm/H/count/exit facts. Unknown or technical failure is not negative performance. |

How the result will be interpreted: an above-MEI effect would justify considering limited
repeatability investment after all native/H facts; an inside-MEI effect ends automatic
advancement of this candidate; an opposite effect supports the ordinary body locally. Gate
movement, critic fit or hold frequency never replace native return. All outcomes stop this
allocation; none changes lifecycle, recasts, Portfolio priority or class on its own.

## 5. Work, exposure, execution route and engineering scope

Known work: **2×768×256 training + 3×32×256 evaluation = 417792 team steps**,
393216 train / 24576 eval, 768 two-episode rollouts, **3072 Adam**, 768 moment merges,
393216 unique target rows / 1572864 four-epoch terms, 96 evaluations / 1632 scored episodes,
two real fits / two learned final endpoints / one H bank / four environment constructors.
Per arm: 196608 training steps, 384 rollouts/merges, 1536 Adam and 8192 learned evaluation
steps; GATED totals 204800 steps, MLP with H 212992. No nested candidates, trajectories,
search tree, solver, tuning, pilot or cost experiment is authorized.

Per-arm cost law: startup/common initialization (GATED) + 196608*c_env_actor +
384*c_moment_merge(512) + 1536*c_update_arm + 8192*c_eval + endpoint publication.
MLP also pays 8192*c_H and pair publication/readback/exit. Prior complete two-panel pair
walls 475.85/507.29/504.91 seconds (1488.05 total, 496.0167 per valid pair) inform planning;
new-width compute, component costs, aggregate CPU and engineering time remain unknown.
The omitted 16384 steps/64 evaluations do not guarantee lower wall time. No known projection
requires exceeding **1800 seconds per complete arm / 3600 seconds whole pair**.
Clocks include imports, adjacent admission, constructors, training, all selected evaluation,
publication/readback and exit. Charge common startup to GATED, H/pair closure to MLP and
retain unattributed residual conservatively; narrower runner time cannot replace whole wall.

Machine-generated exposure line: two prospective fits / 393216 native training steps /
3072 Adam / 96 evaluation episodes; zero scientific invocations at definition. The linked
counts retain prior B12 total relative parameter moves .3296981593/.3344897052 and absolute
gate move .8511881828 as evidence that the learner can move in this update budget, not new
benefit. Record actual B13 counts, nonzero-r rows, parameter/moment endpoints and absolute
gate movement; gate-relative movement is undefined at zero initialization. Missing optional
resource data is `resources_unmeasured`; each instrumentation failure limits its dependency.

Remote-first **wsl_4070 / hmasd-wsl-node, CPU FP32, one scientific process/numerical thread**.
Host is not the estimand; no host/dtype/RNG change by routing convenience. CM commits/pushes
source and literal LF wrapper, binds full SHA/node/cwd/output/handle, and uses configured
detached exact-SHA worktree/supervisor. Immediately before scientific state, actual-node
physical and effective available memory must both be >=4 GiB in the same whole-timed
`admit-memory ... && runner ...` command. CM solely observes and collects to terminal.

Engineering scope §4: **none**. Reuse existing scientific functions and detached supervisor;
add no framework, guard, retry, resume, telemetry or registry. Production additions <=2000
lines, runner <=600; **<=300 seconds total focused checks**. Independent review covers changed
factory/width, final-panel isolation and frozen evaluation moments, primary/H/partial meaning
and metadata. Reuse unaffected tests/review; no historical replay or scientific pre-run.
Test scratch is creator-owned under temp and cleaned per tests/AGENTS.md. Preserve unrelated
work and current UCOPE dependencies; main/index are Root-owned.

## 6. Selection, assignment and stop

Options: (a) freeze the exact Pro-selected comparison with fresh master8601; (b) repeat the
unchanged fourth two-panel B; (c) add a diagnostic/tuning/recast or extra panel. Recommend and
select (a); (b)/(c) are outside P80. Owner-delegated decision (unattended, 2026-09-03 instruction):
(a), **OWNER_DELEGATED object tier**, implementing the accepted **PRO_FINAL direction** choice.
New-card P2 and audit accompany this freeze without waiting for an owner reply.

At most **one accepted scientific submission**, including an accepted prelearner failure.
No retry, resume, replacement master, second pair, pilot, tuning, extra evaluation, independent
H run, Pro Send or automatic successor. GATED then MLP; a valid first arm's performance does
not decide whether the second runs. Integrity/resource/cap failure stops by actual dependency.
Every outcome ends the allowance, not a B consumption state. Technical collection and full
DM intake/Chinese brief retain every outcome, then return to Root for integration and the
next unallocated recommendation. Root owns completed remote-worktree reclamation.

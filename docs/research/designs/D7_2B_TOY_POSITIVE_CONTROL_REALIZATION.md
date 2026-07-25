# D7.2B — toy positive control, realization contract

```text
id=D7.2B-REALIZATION
status=frozen 2026-07-25 before any run
authority=project_manager -- realization of a ruled design, no scientific selection
parent=D7_R30_RENEWAL_DIAGNOSTIC.md   (route, pass conditions A/B/C)
estimands=D0_CARRIER_AND_ESTIMAND.md  (U_opp vs U_pi, Delta, H, continuation, normalization)
```

D7 fixed *what* D7.2B measures and what it must clear. D0 fixed the estimands and
the clocks. Neither says how to identify urgency at a check, what `B_H` is on this
source, or which host runs it. This file freezes exactly those, and nothing that
would change a registered quantity beyond what the two parents already fixed.

It proves only what a positive control can prove: *given genuine heterogeneous
temporal duties, can the learned-keep carrier form different renewal behaviour?*
It says nothing about whether the main scenario contains such duties.

## 1. Host — train through the registered loop, audit separately

Two stages, deliberately split:

```text
train  ha_ctse_process/train.py, --config config_d7_2b_toy_learned_keep --device cpu
audit  scripts/audit_d7_2b_toy_positive_control.py, evaluation-only, loads that checkpoint
```

Training uses the registered loop rather than a reimplementation. An R30 training
loop rebuilt inside a screen would have to reproduce the high-check buffer, SMDP
GAE, the PPO update and `skill_age` bookkeeping correctly, and a defect in any of
them yields a *wrong positive control* — the one failure mode a control cannot
absorb, since its whole purpose is to be trustworthy when the carrier fails.

The audit is evaluation-only, which is where fine control is actually needed: pass
condition B forces a focal token and regenerates later agents in the same check
under the changed prefix (D0 §3), and `maybe_assign_skills` must be driven directly
for that. Freezing the policy is desirable rather than a compromise — `U_pi` is
policy-conditional, so both branches then refer to one snapshot (D7 stage 1).

This route is why all three unbundled gates were blocking, not just the executor
gate: `enforce_r30_contract` refuses `skill_interval=5` off the native-categorical
branch, and refuses a CPU device, and both sit on the training entry.

## 2. Source structure, read from the environment

`envs/pettingzoo/two_timescale_role_free_actions.py`:

```text
2 agents, identical constant zero observations, 2D continuous actions in [-1,1]
state    = [slow_sign, 0, 0, fast_sign, fast_phase, slow_phase]
slow target = (+-1, 0)   x-axis, sign flips every k0 * 6 = 30 steps
fast target = (0, +-1)   y-axis, sign flips every k0 = 5 steps
match(a,t)  = clip(1 - 0.5*||a-t||^2, 0, 1)
team reward = 0.5 * (slow_match + fast_match), best of the two assignments
```

The supplied executor's table is `[[1,0], [-1,0], [0,1], [0,-1]]`, so

```text
skill 0,1  ->  x-axis  ->  serves the slow duty  (target flips every 6 checks)
skill 2,3  ->  y-axis  ->  serves the fast duty  (target flips every check)
```

With `skill_interval = k0 = 5`, a check falls on every fast flip and every sixth
check coincides with a slow flip.

## 3. Urgency identification — determined, not chosen

At a check, an agent's regime is read from the axis of its **incumbent** skill:

```text
incumbent in {0,1}  ->  stable   (its target is constant for 6 checks)
incumbent in {2,3}  ->  flex     (its target flipped at this check)
mixed-urgency check ->  exactly one agent of each, and the slow target did not flip
```

This is ground truth used **in the evaluator only** (D7): the axes never enter an
observation, a reward, or the controller.

**Why this is not a discretionary choice.** The alternative — read the duty off the
environment's realized argmax assignment — agrees with the axis rule wherever
condition A holds, and under a supplied executor that is provable rather than
likely. Every table action is a unit axis vector and every target is a unit axis
vector, so `||a - t||^2 ∈ {0, 2, 4}` and

```text
match  =  1  if a == t   else  0
```

Match is two-valued. `LCB95(slow-match) >= 0.75` and `LCB95(fast-match) >= 0.75`
therefore mean each duty is served *exactly* on at least ~75% of steps, which
requires the two agents to occupy distinct axes, which is the argmax assignment.
Where A fails the identification is undefined — and where A fails there is no
renewal reading to make. Reversing the rule changes no registered quantity on the
branch where it is read.

**Recorded, not renegotiated.** D7 justifies the `0.75` floor as "halfway" because
"a zero action scores `0.5`". The fixed table cannot emit a zero action, so match
is `{0,1}` and `0.75` is a 75%-correct floor instead of a halfway one. The
threshold stands exactly as frozen; only its interpretation is narrower than the
sentence that set it.

## 3a. Information contract — centralized state at decision time

**Added 2026-07-25 after the first launch measured its own necessity.** The first
D7.2B training run was configured without direct-state high context and sat at
chance — `env_reward_mean ≈ 0.42–0.48` across 65 updates, against a random
baseline of about `0.44`. That is not slow learning, it is an architectural
ceiling:

- the toy's local observations are **identically zero** for both agents;
- the initial slow and fast signs are **redrawn every episode**;
- so the optimal state-blind policy can learn the *alternation* (the fast target
  flips every check, deterministically) but not the *phase*, and guesses each
  sign at episode start.

Both match rates therefore cap near `0.5`, and condition A's `LCB95 >= 0.75` is
unreachable **for a reason that has nothing to do with the carrier**. The run
would have reported `NO_ACCESS_D7_TOY_POSITIVE_CONTROL`, which by the ruling's own
branch table says nothing about renewal capacity — the expensive null, arrived at
by a route nobody had checked.

So D7.2B declares its information contract: `r39_toy_direct_state_context = True`,
which replaces the compact vector with the centralized state and freezes that
encoder. Three reasons this is the intended channel rather than a leak:

1. the environment's own docstring says the centralized state exposes the two
   targets **so that** "the high-level roster is the only route by which task
   context can select different low-level skills";
2. D7 forbids feeding *role labels* — "fast" and "slow" are never fed to the
   policy, and are not. The state carries the two target signs and never says
   which agent should serve which. The permutation-invariant reward means the
   assignment remains the policy's to discover;
3. `U_pi` is policy-conditional, so the estimand is defined against whatever
   information set is declared. What must not happen is an *undeclared* one.

That flag was gated to native-categorical edit as well, and the gate was the same
bundling as the other three. The credit machinery it also unlocked — multi-epoch
high PPO and block-return advantage — stays pinned to the native lane, because
widening an information contract is not a licence to pick up an unvalidated credit
mode. D7.2B runs one high PPO epoch with `smdp_gae`.

**The state-blind run is kept as a control**, not discarded: it is the measured
demonstration that this source needs decision-time state access, and it cost only
idle CPU. Cited as the no-state-access control, and it licenses no renewal
conclusion.

**Control result, 200 updates, complete.** `logs/nonformal_d7_2b_toy_learned_keep_20260725_17dbb6b_pm1`.
Mean `env_reward_mean` over the first twenty updates `0.442187`, over the last
twenty `0.475195` — a real but small rise toward the state-blind ceiling of about
`0.5`, against the `0.44` random baseline.

No audit was run on it, because arithmetic closes it more tightly than a screen
could. The team reward is `0.5 * (slow_match + fast_match)`, so a plateau at
`0.475` puts `mean(slow_match) + mean(fast_match) ≈ 0.95`, while condition A
requires both at or above `0.75` — a sum of at least `1.5`. A therefore cannot
pass here, and the branch is `NO_ACCESS_D7_TOY_POSITIVE_CONTROL` by derivation.
That is the whole point of the control: it fixes the access failure to the missing
information channel rather than to the carrier.

## 4. `B_H` — the normalizer, frozen before the audit

D0 permits two forms and forbids estimating `B_H` from the treatment outcome. The
choice is load-bearing, so here is the arithmetic that drives it, on `H = 30`:

Forcing KEEP on a flex agent costs `fast_match = 0` for one check interval, so the
raw effect is about `0.5 * 5 = 2.5` of team return.

| Form | `B_30` | `U~_flex` | Against B's `LCB95 >= 0.10` |
|---|---|---|---|
| feasible external-utility range | `30` | `≈ 0.083` | **fails a correct carrier** |
| constructive minus null | `≈ 7.5` | `≈ 0.33` | passes, with headroom |

The feasible-range form makes B unable to fire for the reason it exists to test:
the horizon `H` is six times the window a KEEP token commits, so dividing a
one-interval effect by the whole horizon buries it under the threshold
arithmetically. That is the *"can a result branch fire for a non-scientific
reason"* failure, inverted — a branch that cannot fire correctly.

**So `B_H` is the constructive-minus-null gap**, D0's second form, and it is
**measured from two source controls before the audit runs**, never from audited
histories:

```text
constructive : oracle executor, each agent always holds the skill its duty needs
null         : no renewal -- initial assignment held for the whole window
B_H          : mean(constructive return over H) - mean(null return over H)
```

Analytically on this source, per step: constructive `1.0`; null `0.5 * (1 + 0.5) =
0.75`, because within one slow period the slow duty needs no renewal while the fast
duty is served on half its blocks. Hence `B_30 ≈ 7.5` and `B_5 ≈ 1.25`. The screen
measures both rather than asserting them, and **records the measured value it used**.

`B_H ≈ 0` is a real outcome and an early exit: it would mean this source contains
no renewal value, so nothing downstream is measurable. Report
`NO_RENEWAL_HEADROOM_D7_TOY_SOURCE` and stop before the audit.

Secondary localization uses `H = 5` with `B_5`, per D0.

**Measured, 2026-07-25**, against the analytic prediction above:

```text
B_30 = 10.0    predicted ~7.5    constructive 30.0, null 20.0, 9 windows/episode
B_5  = 1.875   predicted ~1.25   constructive  5.0, null  3.125, 24 windows
```

Both come out larger than the within-one-slow-period arithmetic predicted, because
windows that straddle a slow flip also penalize the null on the x-axis. The
conclusion is unchanged and stronger: a one-interval effect normalizes to
`2.5 / 10.0 = 0.25` against B's `0.10` floor, where the rejected feasible-range
form would have given `0.083`.

**The window start matters and nearly went wrong.** Measuring `B_H` from step 0
only gives `B_5 = 0` exactly: the fast target does not flip until the first check
elapses, so a no-renewal null is trivially optimal over the first block. The
normalizer is therefore averaged over windows starting at **every check boundary**
— the positions the estimand's own focal checks occupy. A step-0 normalizer would
have divided condition B's secondary horizon by zero.

## 4a. The credit mode the carrier cannot inherit

Recorded **before** the run, because it bounds what an A failure means.

The R39 native lane carries two credit allowances that exist because this toy
needed them: three high PPO epochs and `block_return` high-actor advantage. They
are not available to D7.2B, and the reason is structural rather than a bundling:

```text
standalone_agent.py:1970-1976
block_return  requires  r30_force_refresh_every_check = True  and  3 epochs
force_refresh_every_check  =>  every check is a forced SET
                           =>  KEEP is not a decision  (D0 section 2)
```

So that credit mode is **structurally unavailable to the carrier being measured**.
D7.2B runs `smdp_gae` with one epoch — the registered default — and that is the
only credit mode the learned-keep branch can have here.

**What is not claimed.** It would be convenient to say block-return is the credit
mode that makes this source learnable. Nothing is known to make it learnable. The
one prior run on this toy, `EXP-20260715-r39-native-hmasd-toy-credit`, recorded
`VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR` at `match = 0.455` against its own
`0.7` threshold — but its archived contract shows **20 outer updates and 12,800
timesteps**, a tenth of D7.2B's screen budget, under `hmasd_original` with
`high_full_refresh_every_k = True`. That is evidence the toy was not learned in 20
updates, not evidence it cannot be. Treating it as a settled credit failure would
repeat the error the prior-art section of D7 was written to stop.

Consequence for reading the result, in order:

1. **A flat condition A at screen scale routes to a larger budget, not to a
   conclusion.** The prior art is too short to license one, and so is a screen.
2. Only after an adequate-budget attempt does an A failure become informative, and
   even then D7's branch table refuses to draw a renewal conclusion from it. It
   would route to the ledger's D5 entry ("credit becomes the blocker — reactivate
   only the minimum fragment") or to a source whose competence is reachable, and
   would retire nothing about the carrier.

The measured `B_H` and the state-liveness check together mean an A failure cannot
be blamed on the normalizer or on a dead information path. That leaves training
budget and then credit, in that order, as the candidates to rule out.

## 4b. Which checkpoint is the audited object — declared before the audit

**Fixed 2026-07-25, while the competence run was still training and before any
audit had been run against it.** Recorded here because the moment competence is
reached, checkpoint choice becomes an outcome-relevant knob, and picking it
afterwards is indistinguishable from fitting.

```text
audited object = the run's final checkpoint, standalone_process_core_final.pt
```

Interim checkpoints exist at every hundredth update and may be reported **only**
as a training-trajectory note — when competence appeared, how the renewal
statistics moved on the way. They are never the result, and A/B/C are never read
off whichever one reads best.

This matters in a specific way here. Competence arrived early — `env_reward_mean`
`0.984375` at update 100, against about `0.44` at chance — so the remaining 900
updates sharpen the policy rather than teach it the task. Sharpening can move
condition C in either direction: toward clean separation, or toward a collapse
that trips its full-sync ceiling. **Both are real readings of the final policy**
and neither is a reason to reach for an earlier checkpoint.

## 5. Paired replay protocol

D0 §3 continuation semantics, mapped onto this source. Per focal check and focal
agent, both branches start from one pre-decision history:

| Position | Treatment |
|---|---|
| tokens before the focal agent | held at factual values |
| focal token | forced KEEP in one branch, forced SET in the other |
| later agents in the same check | **regenerated** under the changed prefix |
| later checks, primitive actions, environment | same frozen policy, common random numbers |

Admissibility, asserted per pair rather than assumed:

1. identical reset seed and step index; the toy's only environment randomness is
   the two seeded initial target signs, and everything after is a deterministic
   function of time and actions;
2. equality check on the pre-intervention state, active skills, ages and masks;
3. the forced path consumes the same base draws in both branches — R30 samples the
   conditional skill even when KEEP is selected (`r30_fixed_clock.py:288-290`), so
   this holds without a teacher-forced skip;
4. no optimizer step between the paired branches, and the policy snapshot is
   identical across both.

A pair failing any check is dropped and **counted**, not repaired.

## 6. Estimands computed

```text
U_pi    (h;H)  =  E_{z ~ pi_SET(.|h)} [ G_H(SET z) ]  -  G_H(KEEP)
U_max_pi(h;H)  =  max_{z != incumbent} G_H(SET z)     -  G_H(KEEP)
U~             =  U / B_H
```

**Renamed 2026-07-25 by the D7.2B′ ruling.** `U_max_pi` was called `U_opp` and
described as asking whether the source *contains* a valuable renewal. It does not:
its maximization runs while later agents and future decisions still follow the
frozen learned joint policy, so it is policy-conditional exactly like `U_pi`. The
source-level estimand is `U*_{i,src}` (D0 §3), which reoptimizes or oracle-supplies
the joint continuation in **both** terms — this script does not compute it, and its
absence is why this control could not detect its own source's degeneracy in advance.

`U_max_pi` uses a **split sample**: the maximizing `z` is selected on one replicate
set and its value taken from an independent set. Maximizing and evaluating on one
sample manufactures an optimistic effect (D0 §3).

The result JSON still emits the key `u_opp_flex_split_sample`, so the archived
result at `c4c1417` stays readable against its own schema. The name is superseded;
the quantity is unchanged.

`G` is external task return only. Both regimes are estimated at mixed-urgency
checks; CIs are clustered by episode, since checks within an episode share the
seeded target signs.

## 7. Event ledger

One row per check per agent, written under the run root. Keyed to genuine SET
decisions and `skill_age`, never to segment records (D0 §1 — records fragment at
every policy update, which is an artifact of update cadence):

```text
env_id, episode_id, step, check_index, agent_id
act_sequence_branch          -- recorded per run, per D0 §8; must read learned_keep
token_kind                   -- KEEP / SET
keep_prob                    -- sigmoid(keep_logit), NaN on non-decision branches
incumbent_skill, set_skill, skill_age_at_check
urgency_regime               -- flex / stable / undefined
mixed_urgency_check          -- bool
slow_match, fast_match, team_reward
termination_reason           -- renewal / episode / update / synthetic_reopen
right_censored               -- bool, its own category
```

Same-label renewal is recorded `NOT_APPLICABLE_STRUCTURALLY_EXCLUDED`: under
learned-keep the incumbent is masked out of the SET distribution, so a reported
zero is a tautology (D7).

Full-sync rates and discordance are conditioned on **mixed-urgency** checks. On the
sixth check both duties genuinely flip, so full-sync SET there is correct
behaviour, and pooling it would misclassify coordination as collapse.

## 8. Pre-freeze design check

Triggered — this introduces a result branch and an estimand realization.

1. **Learning signals at the mandated initial state.** Unchanged. This adds no
   credit rule, no gradient path and no initialization. The residual-head and
   credit questions that motivated the check on G20/G20R2 do not arise: the low
   level is a constant table with no parameters, and the high level is the
   registered R30 learned-keep controller at its frozen `keep_init = 0.6`.
2. **Live gradient path at entry.** The supplied executor is deliberately frozen —
   zero parameters, no optimizer (`standalone_agent.py:2676`). That is the point of
   a positive control, not a defect: it puts the competence floor above the carrier
   so a null can only be about the carrier.
3. **Any invariant satisfied trivially?** Yes, one, and it is excluded rather than
   reported: same-label renewal (§7). The `0.75` floor is not trivial — match is
   two-valued, so it is a real 75%-correct requirement.
4. **Can a branch fire for a non-scientific reason?** This is where the check bit.
   Under D0's feasible-range normalizer, B fails a *correct* carrier by arithmetic
   (§4). Fixed by taking the constructive-minus-null form and measuring it from
   source controls before the audit. The remaining known risk is honest: if the
   policy learns "SET at every check" rather than a state-conditioned rule, a
   forced KEEP throws it out of phase for the rest of the slow period and inflates
   `U~_flex` above the one-interval value. That direction makes B *easier*, so it
   cannot manufacture a false negative; it is reported alongside, not corrected.
5. **Do initialization and the credit definition cancel?** No credit definition is
   introduced. `keep_init = 0.6` biases the entry policy toward KEEP, which biases
   condition C's `P(SET|flex)` **downward** — against the control passing. Recorded
   because it is adverse, not neutral.

## 9. What a result may and may not say

| Reading | Licensed conclusion |
|---|---|
| A fails | Upstream access failure. `NO_ACCESS_D7_TOY_POSITIVE_CONTROL`. **No** renewal-capacity update |
| `B_H ≈ 0` | Source has no renewal headroom. Nothing downstream is measurable |
| B passes, C fails | Capability present; the policy or its credit does not use it |
| B fails despite A | The learned skill support or this source does not expose urgency as registered |
| B and C pass | Carrier can express urgency where it provably exists. Proceed to the main source. **Not** a claim about variable `k`, and not the paper's comparative claim |

Standing check from `RESEARCH_GOAL.md` — *what does this let us say about variable
`k` that we could not say before?* That the learned-keep carrier does, or does not,
form heterogeneous renewal behaviour when the source contains it. It is a
prerequisite for the claim, never the claim.

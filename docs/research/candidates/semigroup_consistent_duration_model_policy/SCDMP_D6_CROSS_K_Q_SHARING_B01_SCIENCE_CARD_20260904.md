# SCDMP D6 cross-k Q sharing B01 — science card (2026-09-04)

## Freeze and provenance

- Object: `SCDMP-D6-CROSS-K-Q-SHARING-B01`
- Direction: `semigroup_consistent_duration_model_policy`
- Evidence class: **B/EXPLORE**
- Current direction-local status: **`NOT_LAUNCHABLE_SECTION_11_4_METHOD_CONFLICT`**
- Scientific contract: **historically frozen, withdrawn from launch before any observation**
- Launch readiness: **PROHIBITED**; no smoke, census, dataset, model, optimizer, learner,
  evaluator or result command may execute under this card
- Direction authority: `PRO_FINAL — RECAST_D6`, archived response SHA-256
  `95c60538bdf36b0cd78e68ef91ecd20548b7d68e473c7a5f609d27c3e2b473b7`
- Object-tier architecture/RNG closure: `OWNER_DELEGATED`, intake section "Decisions this intake
  produces", option (a)
- Object-tier source-law closure: `OWNER_DELEGATED`,
  `SCDMP_D6_CROSS_K_Q_SHARING_B01_SOURCE_LAW_CLARIFICATION_20260904.md`, option (a)
- Correcting direction authority: `PRO_FINAL — SPLIT_A_RECON_THEN_REOPEN_B`, archived response
  SHA-256 `a98efe074a2bd0ec714e5495209555b4745d724a9894c2f8c72669c40bdb8621`
- No result-bearing run, root, model, optimizer, training record or evaluation tape exists at this
  freeze.

The controlling correction removes the 1,152-mission census entirely from B launch authority.
This card may not be repaired in place by deleting its early return: no B object is authorized.
Only the separately named `SCDMP-D6-DURATION-ACTION-RELEVANCE-A01` A/RECON object may proceed.
After a valid A intake, the same convergence node must decide whether to freeze a newly named B.
All detailed B wording below is retained as historical prospective provenance, not executable
authority.

This is a new, transparently outcome-informed object. It is not B01 `RUN-02A`/`RUN-02B`, a
reinterpretation of the graded diagnostic, an FCEOV `.3` continuation, D2 interruption or learned
termination.

## Question, claim ceiling and non-goals

**Question.** On the declared native SCDMP row and fresh six-state public population, does one
shared duration-conditioned value head `Q(s,z,k)` reach competent composite-action selection with
fewer samples or learner updates than an untied D8 `(z,k)` menu, under identical training records,
optimizer exposure and native evaluation?

**Maximum claim.** A positive branch supports only that, on this exact host row, finite population,
hidden balanced HR/RH twins, `{0,10,12}×{7,13}` actions, common records, three learner seeds, fixed
continuation and budget, the shared D6 package reached competent native composite-action choices
earlier or with lower normalized native decision regret than competent untied D8. An adverse branch
is bounded to the same package, setup and budget.

**Non-goals.** No branch tests or establishes graded B01 event-order value; D2 interruption;
learned termination; endogenous on-policy duration acquisition; unseen-`k` or held-out-`k`
transfer; arbitrary states, actions, foundations, simulators or duration sets; pure causal
attribution to duration semantics rather than regularization; semigroup/duration invariance;
variable `N`; stable MARL superiority; safety, deployment or flight readiness.

## Mechanism, treatment, comparator and live explanations

Both arms receive the same public observation, skill catalogue, `K={7,13}`, ordered terminal-return
records, optimizer-step count and native evaluation cells. Both may choose exactly
`A={0,10,12}×{7,13}` at an ordinary renewal boundary; neither may interrupt mid-segment.

### Common encoder

For finite float32 public observation `s∈R^18` and skill `z∈{0,10,12}`, concatenate `s` with the
three-way one-hot skill code and compute

```text
h(s,z): Linear(21,96) → SiLU → Linear(96,96) → SiLU
```

The common encoder has the same architecture and address-matched initialization in D6 and D8 for a
given learner seed. It is trained end to end in both arms.

### D6 treatment

Let `k_norm=(k-7)/6`, exactly `0` for `k=7` and `1` for `k=13`. D6 computes

```text
Q_D6(s,z,k): concat(h(s,z), k_norm)
              → Linear(97,96) → SiLU → Linear(96,1)
```

A record at either duration updates the same duration-conditioned head parameters. The fixed scalar
has no parameter tensor; its treatment-carrying coefficient is the duration column of the first
head weight.

### Strongest competent same-information comparator: D8

D8 computes

```text
Q_D8(s,z,7)  = head_7(h(s,z))
Q_D8(s,z,13) = head_13(h(s,z))
head_k: Linear(96,96) → SiLU → Linear(96,1)
```

The two full heads share no head parameter. D8 retains the common state/skill encoder and has more
total head capacity than D6; it lacks only cross-`k` head sharing. It is not weakened by missing
information, actions or generic representation sharing.

The strongest live null is that any D6 advantage is ordinary lower-dimensional regularization or
easier optimization, while heterogeneous state-by-duration values may instead cause negative
transfer and make D8 superior. This B result can support only the shared D6 package, not pure
duration semantics. A parameter-matched or duration-label control is a later object only after a
bounded signal.

## Host, fresh population and protected native semantics

Use the existing SCDMP native host and change exactly one host constant relative to the frozen B01
row:

```text
TAU_LEAK = 0.92
Z_LIMIT  = 0.25
```

All other native equations, constants, event ordering, HR/RH transformations, `LEVEL_RELEASE`,
failure predicates, dock predicate, observation normalization, primitive precision, horizon `364`
and side effects remain unchanged. The row was survivable in the diagnostic, but no diagnostic
return is imported.

Generate six treatment-common public renewal states before learner initialization:

- native reset uses the literal `pre_event_q=0` for both streams and every candidate source
  renewal; it is never drawn, alternated or keyed by stream, `k`, target, tape or outcome, and the
  existing identity `pre_event_p=(1,2,3,4)` is unchanged;
- fixed state-source stream `9011` uses `COMMON=0` at every source renewal on a constant `k=7`
  clock;
- fixed state-source stream `9013` uses `COMMON=0` on a constant `k=13` clock;
- from each stream take the first legal renewal at or after target ticks `64`, `160` and `256`;
- clone each state into HR and RH worlds, apply their event order and then the common zero-tick
  `LEVEL_RELEASE`;
- require byte-equal actor-visible public observations across the HR/RH twin before the candidate
  action; and
- expose no graph label, latent assignment, future tape, oracle action or oracle value to either
  learner.

No B01 or FCEOV foundation, state, checkpoint, tape, `q_by_cell`, result root, selected action map,
threshold or inference rule may be read or reused. Existing source code may supply the unchanged
native equations; runtime scientific artifacts are fresh.

`pre_event_q=0` is an outcome-blind finite-population coordinate, not a scientific arm. Native
HR/RH composition still overwrites post-event `q` exactly as before. Consequences accumulated in
the source prefix remain part of the public renewal state; no learner receives the hidden reset
bit itself. The old B01 checkerboard is not imported.

## Action, continuation and endpoint

```text
Z = {COMMON=0, A_HR=10, A_RH=12}
K = {7,13}
A = Z × K
```

Hold the selected first `z` for exactly `k` primitive ticks. Afterwards use the common fixed
continuation action `COMMON=0` on the same fixed renewal clock for every state, graph, tape and arm
until absorption, safe dock or timeout. The native endpoint is

```text
U = 1{safe dock} × (1 - dock_tick / 364)
```

and failure or timeout gives `U=0`.

## Pre-model A/RECON action-relevance gate

Before any learner, optimizer or training dataset is created, use evaluation domain `9029` to
materialize exactly 16 fixed disjoint tapes per state. Evaluate all six actions in both graph twins:

```text
6 states × 6 actions × 2 graphs × 16 tapes = 1,152 native missions
primitive-tick ceiling = 419,328
```

For state `j`, define

```text
V_j(a) = mean U over 16 tapes × {HR,RH}
V_j*   = max_a V_j(a)
V_j-   = min_a V_j(a)
k_j*   = duration of the lexicographically first maximizing action
m_j    = V_j* - max_{a:k(a) != k_j*} V_j(a)
```

The host passes only when all three conditions hold:

1. at least one state has all cross-duration alternatives at least `1/364` below a maximizing
   `k=7` action;
2. at least one state has the analogous uniquely preferred `k=13` duration with margin at least
   `1/364`; and
3. `sum_j(V_j* - V_j-) > 0`.

Failure returns `HOST_NOT_DURATION_DISCRIMINATING` before model creation. It rejects this finite
host/population, not every D6 host. The table is an evaluator-only oracle; neither learner reads it.
The same 16 evaluation tapes define later regret but are disjoint from every training tape.

## RNG, initialization, data and numerical contract

Use learner seeds exactly `3119`, `5171`, and `8089`, with no replacement or best-seed selection.
For each seed, address-separate model initialization, training native tapes, fixed schedule and
evaluation. D6 and D8 use the same training addresses and identical common-encoder initialization;
arm/head initialization has an arm-labelled domain. No library-global RNG may select scientific
coordinates. The source-law literal `pre_event_q=0` consumes no RNG address.

Every affine weight uses address-stable Xavier-uniform float32 initialization; biases are exactly
zero. The head-weight denominator in the exposure measurement must be strictly positive. Models,
losses and optimizer state use float32. Native precision is unchanged. Result aggregation,
`V_j`, regret, AUC, return differences and exposure numerator/denominator are recomputed in float64.
Greedy action ties use the smallest composite-action index in the declared order
`(0,7),(0,13),(10,7),(10,13),(12,7),(12,13)`.

For each learner seed, generate one fixed balanced dataset before either arm is initialized:

```text
160 updates × 12 native episodes/update = 1,920 terminal-return records
primitive-tick ceiling = 698,880
```

Each update includes every composite action exactly twice. A deterministic cyclic schedule rotates
the six states and two graphs so final per-action, per-state and per-graph counts differ by at most
one. Training tapes are seed-specific and disjoint from domain `9029`. Generate the dataset once and
present the exact ordered records to both arms. Dataset generation records real native transition
counts; it performs no model-dependent acquisition.

Train on per-record squared error `(Q(s,z,k)-U)^2`, one record and one AdamW step at a time in the
fixed order. Both arms use `lr=3e-4`, `betas=(0.9,0.999)`, `eps=1e-8`, weight decay `1e-5` and global
gradient-norm clip `0.8`, with no arm-specific tuning:

```text
160 learner updates
12 AdamW steps/update
1,920 AdamW steps per arm-seed
```

Evaluate greedily at updates `{0,20,40,60,80,100,120,140,160}`. There is no checkpoint selection,
early stopping, added seed or result-aware extension. Fixed checkpoints are evaluated in-process;
no checkpoint/resume machinery is needed.

## Exposure line

At every fixed checkpoint, read the raw treatment-head tensors and compute in float64

```text
E_A(u) = sqrt(
  sum_{p in H_A} ||p(u)-p(0)||_2^2 /
  sum_{p in H_A} ||p(0)||_2^2
)
```

`H_D6` is every tensor of the shared duration head, including the first-layer duration column.
`H_D8` is every tensor of both duration-specific heads. Record tensor names, shapes, stored dtypes,
numerator, denominator and ratio. Record common-encoder displacement separately; it cannot
substitute for head movement.

Missing, nonfinite or shape-mismatched measurement is `INVALID_EVIDENCE`. A valid
`E_A(160)=0` is `EXPOSURE_NOT_ACHIEVED`, not invalidity and not D6 polarity. The prior B01 supplies
no exposure line.

## Observable and estimands

At checkpoint `u`, arm `A` greedily selects `a_hat[A,j,u]` for every state and executes it on the
fixed paired evaluation cells. Define

```text
r_A(u) = sum_j [V_j* - V_j(a_hat[A,j,u])] /
         sum_j [V_j* - V_j-]
```

This normalized native decision regret is primary. Arm `A` is competent at checkpoint `u` when
`r_A(u) <= 0.10`, its duration belongs to the oracle-optimal duration set in at least `5/6` states,
and both conditions hold at every later checkpoint. `T_A` is the first retained-competence
checkpoint, or `180` if none qualifies.

```text
AUC_A = mean r_A(u) over u={20,40,...,160}
Delta_T   = T_D8 - T_D6
Delta_AUC = AUC_D8 - AUC_D6
```

Positive deltas favor D6. A D6 action-consequence witness exists when, before D8 reaches retained
competence, D6 selects an oracle-duration action, D8 selects the other duration, and
`V_j(a_D6)-V_j(a_D8) >= 1/364`. Predicted-Q calibration and off-duration prediction changes are
diagnostics only and cannot activate a branch.

Final native return for an arm-seed is the mean `V_j` of its update-160 selected actions across the
six states. This definition controls the final-return clauses below.

## Work law, cost projection, resource admission and stop rule

Planned fixed work is:

| Invocation | Count | Native missions | Primitive-tick ceiling | AdamW steps |
| --- | ---: | ---: | ---: | ---: |
| pre-model gate | 1 | 1,152 | 419,328 | 0 |
| common data generator | 3 | 1,920 each | 698,880 each | 0 |
| D6 arm-seed | 3 | 1,728 evaluation each | 628,992 each | 1,920 each |
| D8 arm-seed | 3 | 1,728 evaluation each | 628,992 each | 1,920 each |

Each arm-seed evaluation inventory is
`6 states × 2 graphs × 16 tapes × 9 checkpoints = 1,728` missions. Total planned work is 17,280
native missions and 11,520 AdamW steps.

Before any result launch, CM's actual runner must emit a prospective numeric cost row for the gate,
each common-data seed and each of the six arm-seeds. Its fixed law is

```text
P = 2 × (t_native_mission × full_native_missions
       + t_adamw_step × full_adamw_steps
       + t_candidate_score × full_candidate_scores)
    + 60 seconds fixed overhead
```

where the three unit times are measured by the runner's single toy smoke path on this machine and
the full counts above are card constants. The factor `2` is the prospective margin. The numeric
table is appended outcome-blind to this card before launch. **No result invocation is admitted
while any row is missing or exceeds 1,800 seconds.** The hard observed cap is also `1,800 s` per
invocation and per arm-seed; exceedance stops without scientific polarity.

Immediately before the gate, every data generator and every arm-seed invocation, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require physical and
effective available memory of at least 4 GiB. Peak RSS and wall time are recorded. Missing resource
telemetry does not annul a non-resource claim; missing learner/evaluator measurements do.

The gate runs first. If it fails, create no model. After an arm's first optimizer step, a valid
arm-seed completes all 160 updates and nine evaluations. Provisional trends cannot stop or extend
it. A repair at a new sha is a fresh attempt; the scientific object remains the same only when this
contract is unchanged.

## Ordered result rule

Apply the first matching branch:

1. **`INVALID_EVIDENCE`** — integrity failure; failed mandatory admission; missing/nonfinite
   displacement; any required transition, learner-step or native-evaluation count is zero;
   leakage; or incomplete output. No scientific update; repair only.
2. **`HOST_NOT_DURATION_DISCRIMINATING`** — the pre-model gate fails either distinct-duration
   condition, the one-tick margin or positive oracle-to-worst span. Reject this host/population and
   launch no learner.
3. **`EXPOSURE_NOT_ACHIEVED`** — either valid arm has `E_A(160)=0`. No efficacy conclusion at this
   budget; any next object addresses optimizer exposure rather than adding selected seeds.
4. **`D8_COMPARATOR_NOT_COMPETENT`** — D8 lacks retained competence by update 160 in any seed. No
   superiority claim; a budget/conditioning revision must be separately named.
5. **`PRELIMINARY_CROSS_K_VALUE_SHARING_SIGNAL`** — both arms are competent in all seeds; median
   `Delta_T >= 20`; median `Delta_AUC >= 0.05`; an action-consequence witness occurs in at least two
   seeds; and D6 final native return is not below D8 by more than `1/364` in any seed. Retain D6 as
   bounded B; no C promotion.
6. **`PRELIMINARY_NEGATIVE_TRANSFER`** — D8 is competent in all seeds and either D6 is not competent
   in at least two seeds, or both median `Delta_T <= -20` and median `Delta_AUC <= -0.05`. Reject
   this shared-head implementation on this host and budget.
7. **`NO_MATERIAL_VALUE_SHARING_DIFFERENCE`** — both arms are competent in all seeds;
   `abs(median Delta_T) < 20`; `abs(median Delta_AUC) < 0.05`; and every seed's final native-return
   difference is within `[-1/364,+1/364]`. Park this D6 package unless a prospectively different
   `K`, population or sharing law supplies a new decision.
8. **`INSTABILITY_OR_STATE_HETEROGENEITY`** — every other valid complete outcome. Preserve every
   seed/state sign; only a separately named diagnostic may distinguish negative transfer from
   ordinary optimization variance.

The `0.05` AUC threshold is five percentage points of the complete oracle-to-worst regret range;
`20` updates is one fixed checkpoint interval; `1/364` is one terminal-tick unit. This rule cannot
be rewritten after observation.

## Predictions on record

- **DM prediction, 2026-09-04 before implementation:** conditional on a passing host gate, valid
  exposure and competent D8, `NO_MATERIAL_VALUE_SHARING_DIFFERENCE`. The evidence shows duration
  can alter native consequences but supplies little reason to expect smooth cross-`k` values; with
  only two durations and balanced records, D8 should catch up within one checkpoint interval.
- **Owner prediction:** `not taken (unattended)`.

Predictions do not alter the branch rule.

## Implementation ownership and engineering-scope budget

Owned paths for this object are:

- `experiments/candidates/scdmp_variable_k/d6_cross_k_q_sharing_b01/`
- `scripts/run_scdmp_d6_cross_k_q_sharing_b01.py`
- `tests/experiments/candidates/scdmp_variable_k/d6_cross_k_q_sharing_b01/`
- `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_cross_k_q_sharing_b01/`
- this card, its later result evidence and intake.

No core file is owned. The implementation may read/reuse research-tier native equations but must
not import a result artifact or make core depend on research code.

**Engineering scope §4: this object needs none of the prohibited items.** It uses one argparse
runner and a plain documented list of gate, data, arm and summarize commands; no scheduler, queue
state, retry, resume, checkpoint, lock, heartbeat, manifest/hash/provenance guard, incident tree,
schema validator, registry, framework, compatibility shim or telemetry beyond wall/peak RSS.

The research-code limit is 2,000 new lines excluding tests and this card; the runner limit is 600
lines; orchestration must remain below 30% of the diff. Tests are exactly one toy-size end-to-end
smoke under 60 seconds and rule tests pinning all eight branches. Technical success can establish
only implementation conformance and the numeric cost rows; it cannot establish mechanism value.

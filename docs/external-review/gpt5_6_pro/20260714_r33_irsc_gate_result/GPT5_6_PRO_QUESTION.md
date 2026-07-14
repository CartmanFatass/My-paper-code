# GPT-5.6 Pro Review Request: Route After R33-IRSC Valid Failure

Please inspect the exact implementation and tracked result JSON before
answering. We need a validity audit and exactly one structurally different
post-R33 causal edge, not a menu and not a rescue of R33.

## Current decision

R32 direct individual IFEPG is permanently retired. R33 tested the next causal
level:

```text
natural R30 context
-> randomized complete-roster effects
-> stable non-additive role-swap complementarity
-> exact high-level complementary-roster selection
-> natural joint and nonredundant coverage
```

The registered single-seed Alice--Bob gate returned
`FAIL_M1_RETIRE_R33_IRSC` with M0 valid.

## Controller modifications to the proposed R33 estimator

We accepted the complete-roster, exact-expectation route but found that the raw
proposal did not isolate team interaction. Under

\[
E_1(a,b)=f_1(a)+u_1(b),\qquad
E_2(a,b)=u_2(a)+f_2(b),
\]

the original role-swap contrast can be large despite independent execution.
It also scores a one-sided orientation effect.

The implemented estimator therefore uses the same complete `4 x 4` table but
double-centers it separately for every agent and replica:

\[
\widetilde E_i^q(a,b)
=E_i^q(a,b)
-\overline E_i^q(a,\cdot)
-\overline E_i^q(\cdot,b)
+\overline E_i^q(\cdot,\cdot).
\]

For each unordered pair:

\[
\widetilde g_{ab}^q
=\widetilde E_1^q(a,b)-\widetilde E_2^q(a,b),
\]

\[
h_{ab}^q=\tfrac12(\widetilde g_{ab}^q-\widetilde g_{ba}^q),
\qquad
k_{ab}^q=\tfrac12(\widetilde g_{ab}^q+\widetilde g_{ba}^q),
\]

\[
\widetilde C_{ab}
=\tfrac14\left(
\langle h_{ab}^1,h_{ab}^2\rangle
-\langle k_{ab}^1,k_{ab}^2\rangle
\right).
\]

Thus additive individual effects project to zero; a one-sided orientation has
equal antisymmetric and symmetric terms and scores zero; a stable sign reversal
scores positively. Scores remain signed and use no ReLU.

The pair-sham is a fixed complementary-edge derangement:

```text
01 <-> 23
02 <-> 13
03 <-> 12
```

It preserves the full signed score multiset but shares no skill identity
between a true pair and its mapped pair. We do not claim it preserves gradient
norm.

We also removed the raw proposal's unconditional `skill_head drift >1e-6` M0
rule. An exact zero causal gradient is valid scientific M1-failure evidence,
not an implementation defect. M0 instead requires eight finite optimizer
calls, correct gradient scope, finite parameters, and zero non-head drift.

Please audit these corrections explicitly. A claimed invalidity must identify
one concrete defect that changes the registered estimand, probability,
randomization, gradient, or result.

## Frozen gate

- Source: the same frozen sparse, adaptive-R30 Alice--Bob checkpoint as R32.
- Seed: `33031`.
- Source bank: 24 x 80-step natural episodes; 192 pre-check contexts; first 128
  train, last 64 held out by episode.
- Intervention: all 16 final rosters, two independent stochastic replicas,
  `W=k0=10`; common random numbers across all rosters within one replica.
- Effect per agent: endpoint and late-half mean normalized position
  displacement only, four dimensions.
- Shared intervention table: 61,440 primitive steps.
- Both arms: eight Adam updates, 16 contexts/update, each train context exactly
  once, `lr=3e-4`, gradient clip `0.5`.
- Real: true pair attribution. Comparator: pair-sham attribution above.
- Exact objective:

\[
L=-\frac1B\sum_c\sum_r
\pi_\theta(r\mid c)\operatorname{stopgrad}[A_c(r)].
\]

- `pi(r|c)` is the exact teacher-forced R30 KEEP/SET joint probability over all
  16 final rosters.
- Gradient recipient: only
  `FixedClockAREditPolicy.skill_head.weight/bias`.
- Frozen/outside objective: KEEP head/shared trunk, high value, OPT/bridge, low
  actor/critic/log-std, all posteriors/classifiers, reward, GAE, normal high
  PPO, environment, team latent, `q_d/q_D`.
- Natural transport: 64 paired stochastic episodes per arm.
- Total exposure including source, shared interventions, and natural arms:
  73,600 environment steps.

## Result

### M0 implementation validity: PASS

Every registered check passed:

- exact 192/128/64 contexts and `16 x 2 x 10` branches;
- within-replica roster CRN and independent replicas;
- natural high-token replay maximum error `0`;
- maximum 16-roster probability-sum error `2.384e-7`;
- true/sham sorted score-multiset error `6.661e-16`;
- paired initial parameters;
- eight finite optimizer steps per arm;
- finite nonzero head gradients in all updates;
- real selected-head relative drift `0.027634` and sham `0.026423`;
- zero non-head gradient/drift;
- zero stored-prefix KEEP-probability drift;
- zero reward/low/critic/posterior/normal-PPO objective update.

### M1 heldout causal alignment: FAIL

Real-minus-sham exact expected true-score gain:

\[
0.00195497,\qquad
CI_{95\%}=[0.00074433,0.00310530].
\]

Registered gate: mean `>=0.20` and source-episode-cluster CI lower `>0`.

Correct-top-two-pair two-orientation probability-mass gain:

\[
0.00125035,\qquad
CI_{95\%}=[0.00051950,0.00190764].
\]

Registered gate: mean `>=0.10` and CI lower `>0`.

Both signals are statistically positive but about two orders of magnitude
below their material gates despite substantial head movement.

### M2 natural transport: FAIL

- Joint-position union coverage: real `427` versus sham `429`, ratio
  `0.995338`; paired-reset gain CI `[-0.000300,0]`.
- Role-free nonredundant coverage: real `0.367500` versus sham `0.373125`,
  ratio `0.984925`; paired-reset gain CI `[-0.021875,0.005000]`.

### M3 R30 safety: PASS

- full-sync SET: `0.185268`;
- SET-skill entropy / log(4): `0.997333`;
- minimum SET-skill share: `0.216000`;
- long/short lifetime breadth: `0.081841`.

The failure is not skill-supply, synchronized-refresh, or lifetime collapse.

## Frozen interpretation and prohibitions

If M0 is valid, enter the registered M1 branch and permanently retire direct
intervention-scored roster-complementarity selection. Do not rescue it with
temperature, more updates, another pair permutation, score clipping, a new
team latent, `q_D`, team reward, seed expansion, or normal-trainer integration.
Do not turn the tiny positive M1 signal into a reward, critic target, or longer
run.

The combined evidence is:

```text
individual effect gradient
-> small forced shift
-/-> material skill differentiation or natural coverage

exact non-additive roster-complementarity fitting
-> tiny correct-pair alignment
-/-> natural joint or nonredundant coverage
```

## Cross-project constraints from IMOD (constraints, not evidence)

A separate IMOD project established a useful execution boundary but did not
establish an effective Async-HMASD learning algorithm. Its reusable positive
content is an exact fixed-path fallback, explicit per-agent event state,
deterministic bounded service, atomic partial-roster commit, and an exact
probability ledger. Its mixed-age mechanics, teacher-KL safety pipe, and local
lifetime observations do **not** establish convergence, task performance, skill
semantics, or useful credit. IMOD also retired completion-value `J`,
value-of-revision/request-value, value-ranked candidates, and the production
ROSTER scheduler/controller line.

Treat this only as prior constraints on the post-R33 proposal:

1. Do not choose a scheduler, queue, hazard, service rule, atomic commit, or
   mixed-age access by itself as the new learning contribution. The proposed
   edge must explain how a learnable signal repairs the demonstrated absence of
   material individual causal effects and selectable non-additive interaction.
2. Preserve R30's exact fixed-clock KEEP/SET probability and replay spine as
   the comparator and fallback. Do not reopen the separate legacy `hmasd/`
   stored-prefix issue as an explanation of this R33 result; active R30/R33
   teacher-forced replay passed M0 exactly.
3. Treat teacher/student mixing, event-state bookkeeping, bounded service, and
   atomic commit as safety/execution infrastructure only. They may support a
   later mechanism if logically required, but they cannot supply its causal
   claim.
4. If the selected mechanism eventually requires asynchronous execution, its
   gate must isolate learning from scheduling with a realized-rate-matched
   random control and, where relevant, force/suppress, oracle-allocation, or
   immediate/sequential/delayed execution probes.
5. Do not revive `J`, value-of-revision, request-value, value-ranked pruning,
   the ROSTER production controller, or present prefix credit/value-free
   pruning as already validated. Any such structurally new estimator would
   require its own upstream abandonment gate rather than inheriting legitimacy
   from IMOD mechanics.

These constraints are not an invitation to migrate IMOD code or parameters and
do not change the registered R33 failure.

## Requested decision

1. Audit whether the corrected R33 estimand, shared randomization, exact roster
   probability, head-only gradient, pair-sham, and M0 rules make this a valid
   scientific failure.
2. If valid, state the reusable causal lesson and retire direct R33 without a
   rerun.
3. Select **exactly one** structurally different post-R33 causal edge. It must
   address why the current codebook exposes neither material individual causal
   effects nor material selectable non-additive team interaction. Scheduler or
   asynchronous mechanics alone are not a learning contribution.
4. Specify one implementable algorithm: mathematical objective/estimator,
   intervention or natural-data semantics, policy inputs, gradient recipients,
   detach boundaries, frozen modules, and its interaction with R30 KEEP/SET.
5. Give the smallest Alice--Bob abandonment gate with one mechanism-matched
   comparator, exact budget, metrics/thresholds, M0 validity rules, and
   PASS/FAIL branches. No UNDERPOWERED, retuning, or automatic seed-expansion
   branch.
6. Keep the next mechanism outside normal training until its gate passes. Do
   not claim task efficacy, cooperation, HMASD parity, or S7 transfer from that
   gate.

## Repository files to inspect

- `docs/external-review/gpt5_6_pro/20260714_r32_ifepg_gate_result/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260714_r32_ifepg_gate_result/DISPOSITION.md`
- `ha_ctse_process/r33_interventional_roster_complementarity.py`
- `scripts/r33_roster_complementarity_gate.py`
- `logs/r33_irsc_gate_20260714_214411/result/r33_irsc_gate.json`
- `memory/ExpRecord.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md`

Return one decisive route with a falsifiable causal edge and complete minimal
gate contract.

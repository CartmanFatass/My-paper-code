# UCOPE A/RECON B1 odd-support versus even-heldout audit R01 — prospective contract

## Authority and question

The complete persistent `em:ucope:convergence` decision for request
`ucope-em-convergence-20260901-02` selects the sole next direction-science
object:

```text
OBJECT_ID=UCOPE-A-RECON-B1-ODD-SUPPORT-VS-EVEN-HELDOUT-COMPETENCE-AUDIT-R01
EVIDENCE_CLASS=A/RECON
SCIENTIFIC_STATUS=JUSTIFIED_NEXT_DIAGNOSTIC
```

This contract freezes the diagnostic before any odd-support checkpoint score or
derived odd-support outcome is read. It asks:

> For all 72 immutable policies in the valid B1 complete publication, do the
> same competence components fail on the observed odd-period training support,
> or is the failure specific to held-out even-period extrapolation?

This object changes only the candidate evaluation support from retained
`K_even=(2,4,6,8)` to diagnostic `K_odd=(1,3,5,7,9)`. It is a measurement of
already-retained policies, not a new algorithm experiment and not a
retrospective replacement for B1.

## Sole input and immutable binding

The only scientific input tree is:

```text
temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/
```

The audit must bind all of the following before reading model scores:

```text
complete/result.json SHA-256
  72deee383f2b0ff366e43ddcb43e17fe449c4f9616caf9a9e4f1ed3340bc16b6
complete/resource-ledger.json SHA-256
  4406f7d8f54bbb47c5ba08b0f65d866a4d1bd673aba8aa6451c17eddeed21acb
complete/terminal-receipt.json SHA-256
  798079a308d8a5fc83642f1fc34ac682cd54e26722bc78387eb6fb3419bf1d5c
checkpoint inventory aggregate SHA-256
  77fd397ea451a1003191251ea0f0a4f1c380c52e9bd80e4734462721848e1c8f
source aggregate
  16ebd3bc30dc667bbc2e47037757290375f9ac7aa08309cef7e22d820644e9e6
manifest digest
  47405ebc4def488404b285d9fafb55e8d2b24b4342049ae08f608316684721a9
assessment digest
  cbae52fae338e0410935c50b9099ecab1d852b6d3ab647c5977d030b0ac74c31
```

The complete result must validate against its local checkpoint inventory and
run binding without reading an earlier or sibling B1 root. The exact identity
set is:

```text
arm in (MT-XF-FLEX, FT-XF-FLEX, FT-XF-BC)
seed in (ucope-scout-r01-b1-fresh-00,
         ucope-scout-r01-b1-fresh-01,
         ucope-scout-r01-b1-fresh-02)
fold in (0,1)
root_update in (40,80,160,320)
```

Its Cartesian product contains exactly 72 unique policies. The audit must read
each inventory locator exactly once per independent scoring pass, verify its
literal byte count and SHA-256, validate checkpoint payload identity/config/run
binding/progress, and reject a missing, duplicate, extra, symlinked, changed, or
out-of-tree checkpoint. Pre- and post-audit SHA-256 inventories must be exactly
equal.

The B1 roots `-01`, `-02`, and `-03`, their checkpoint trees, results, control
state, journals, or outcomes are forbidden inputs. Historical UCOPE data,
checkpoints, fits, policies, and failed identities are also forbidden.

## Protected no-effect boundary

The audit must perform:

```text
new training                         0
new environment episodes             0
new environment transitions          0
optimizer construction or steps      0
checkpoint writes or mutations       0
model selection                      0
seed/fold/arm/checkpoint exclusion    0
hyperparameter tuning                0
sampled evaluation                   0
acquisition evaluation               0
COUNT/RAW evaluation or unlock        0
```

Checkpoint tensors may be materialized only into fresh CPU inference modules
or evaluated through a stateless functional call. Autograd must be disabled,
no optimizer may be constructed, and no loaded tensor may be modified. The
only durable scientific output is one create-once diagnostic JSON in a
separate A/RECON namespace. The original complete tree stays byte-identical.

Immediately before the sole result-bearing invocation, run the central memory
preflight and require both physical and effective available memory to be at
least `4,294,967,296` bytes. The audit is CPU-only, single-process,
single-worker, sequential-checkpoint work. Freeze ceilings of `300 s` wall,
`536,870,912` bytes peak RSS, `67,108,864` bytes durable output, and
`67,108,864` bytes scratch. Admission, measurement, binding, cap, or output
failure produces no scientific observation.

## Exact restricted oracle

For regime `r in {SHORT,LONG}` and period `k in {1,...,9}`, retain the B1 host
law:

```text
q(r,k) = 0.95 - (k-center(r))^2/100
center(SHORT)=2
center(LONG)=8

R(r,k) = q(r,k) - k/100 - k^2/1000
```

For a context `c=(link,p,cost)` and displayed count `m in {0,...,6}`, retain
the exact posterior `b_c,m=P(SHORT|c,m)`, count mass
`w_c,m=P(m|SHORT)/2+P(m|LONG)/2`, and direct probe component
`D(cost)=1/25-cost` from the accepted source equations.

For a finite period set `K`, define with exact rational arithmetic:

```text
T_K(b,k) = b R(SHORT,k) + (1-b) R(LONG,k)
k*_K(b)  = argmax_{k in K} T_K(b,k)
```

Ties use the existing evaluator rule: higher value first, then the lower period.
The uniqueness flag is false whenever the two highest exact values are equal.

For the odd diagnostic `K=K_odd=(1,3,5,7,9)`:

```text
baseline_K(c) = max_{k in K} T_K(1/2,k)
probe_K(c)    = sum_m w_c,m T_K(b_c,m,k*_K(b_c,m)) + D(cost)
oracle_K(c)   = PROBE if probe_K(c)>baseline_K(c), else IMMEDIATE
```

The diagnostic oracle is valid only if every immediate optimum, every tail
optimum, and every root PROBE-versus-IMMEDIATE comparison is unique. Any oracle
tie is a scientific nondiscrimination observation not covered by the existing
result-to-action map; it must not be repaired post-result.

The audit must serialize every exact rational oracle value as numerator and
denominator, plus a decimal display that has no decision authority.

## Read-only policy scoring

For each immutable checkpoint, score on CPU under `torch.inference_mode()`
using its retained FP32 root and tail tensors and the existing frozen feature
functions. For each context:

1. score root candidates `PROBE` and `IMMEDIATE:k` for every `k in K`;
2. score tail candidates `k in K` for every displayed count `m=0..6`;
3. select by the existing evaluator order: maximum FP32 score, then the earlier
   candidate (PROBE before IMMEDIATE candidates; lower period within a period
   list);
4. report the full FP32 score maps, selected exact root label, binary root
   action, and selected tail periods.

`all_finite` is true only if every retained score is finite. `all_unique` is
true only if the two largest FP32 scores differ in every root and tail choice.
An FP32 tie is not broken for competence purposes even though a deterministic
display choice is retained.

For selected odd tail periods `k_hat(c,m)`, define exact rational learned value:

```text
L_tail(c) = sum_m w_c,m T_K(b_c,m,k_hat(c,m))
L_root(c) = L_tail(c)+D(cost)       if selected root label is PROBE
            T_K(1/2,k_selected)     if selected root label is IMMEDIATE:k_selected
O_root(c) = max(baseline_K(c),probe_K(c))
```

The four direct diagnostic components are:

```text
root_hamming = number of the eight binary root actions differing from oracle_K
oracle_root_match = (root_hamming == 0)
max_regret = max_c [O_root(c)-L_root(c)]
tail_agreement(c) = sum_m w_c,m 1[k_hat(c,m)=k*_K(b_c,m)]
minimum_tail_agreement = min_c tail_agreement(c)
```

Regret and agreement must be serialized as exact rationals plus nonauthoritative
decimals. Negative regret is invalid. The restricted diagnostic competence
predicate deliberately preserves the original thresholds:

```text
odd_competent_policy =
  all_finite
  AND all_unique
  AND oracle_root_match
  AND max_regret <= 1/50
  AND minimum_tail_agreement >= 19/20
```

This predicate is descriptive A/RECON output and cannot replace or alter the
original even-support B1 gate.

## Even-support binding check

Before interpreting odd-support output, independently rescore every checkpoint
on `K_even=(2,4,6,8)` without environment calls. Recompute the same finite,
unique, root-label, binary root-vector, tail-period, root-match, exact regret,
and exact tail-agreement fields. Require exact equality to the retained B1
evaluation row for that checkpoint, including every serialized FP32 score and
selected action. Any mismatch invalidates the A/RECON attempt and yields no
odd-support science.

The retained even-support acquisition fields stay untouched and unpopulated by
the audit. Original `NO_ARM_COMPETENT`, paid-acquisition gate, and
`COUNT_RAW_STATUS=LOCKED` remain immutable.

## Exact near-competence definition

Near-competence is a diagnostic routing category, not a relaxed B1 pass. Freeze
it per policy as:

```text
odd_near_policy =
  all_finite
  AND all_unique
  AND root_hamming <= 1
  AND max_regret <= 1/25
  AND minimum_tail_agreement >= 9/10
```

The thresholds mean at most one of eight root-action errors, twice the original
regret allowance, and a five-percentage-point tail shortfall. They do not change
the competence predicate.

For either `odd_competent_policy` or `odd_near_policy`, a seed qualifies only
when both final fold policies qualify. An arm-level category requires at least
two of three seeds. All policy- and seed-level values remain visible.

## Exact package and learning-curve separation

For a policy metric triple
`M=(root_hamming,max_regret,minimum_tail_agreement)`, define material paired
dominance `A > B` only when:

```text
h_A <= h_B
r_A <= r_B
q_A >= q_B
AND at least one of:
  h_B-h_A >= 1
  r_B-r_A >= 1/50
  q_A-q_B >= 1/20
```

At a checkpoint, arm A has clear paired advantage over arm B only when A
materially dominates B in at least four of the six matched seed/fold pairs and
B dominates A in at most one. The fixed-target learner-package comparison is
`FT-XF-FLEX` versus `FT-XF-BC`. A learning-curve separation exists only if the
same dominance direction is clear at two adjacent checkpoints in
`(40,80,160,320)`.

Moving-versus-frozen root behavior is materially separated at the final
checkpoint only when:

- MT and FT odd-support tail action maps are exactly equal in all six matched
  seed/fold pairs; and
- at least two of the six paired binary root vectors differ in at least two of
  eight contexts.

For arm-level similarity at a checkpoint, take the median of each arm's six
policy values, defining the even-count median as the arithmetic mean of the
third and fourth sorted values. All three arms are materially similar at that
checkpoint only when the across-arm median spread is at most:

```text
root_hamming spread              1 context
max_regret spread                1/50
minimum_tail_agreement spread    1/20
```

`all_similar_odd_failure` requires: no arm is odd competent or odd near at the
final checkpoint; all three arms are materially similar at every checkpoint;
no arm pair has a learning-curve separation; and there is no material MT/FT
root separation under shared tail behavior.

## Frozen result-to-action routing

Apply this ordered routing only after all binding and even-rescore checks pass:

1. If any arm is odd competent or odd near at the final checkpoint while the
   retained even B1 arm is not competent, return
   `RECAST_ODD_TO_EVEN_GENERALIZATION`.
2. Otherwise, if exactly one direction of the final FT-FLEX/FT-BC comparison
   has clear paired advantage and no material MT/FT root separation is present,
   return `PERMIT_PAIRED_B_OPTIMIZATION_CONDITIONING_DISCRIMINATOR`.
3. Otherwise, if material MT/FT root separation with shared tail behavior is
   present and no final FT-FLEX/FT-BC clear advantage is present, return
   `LATER_TARGET_SCHEDULE_B_COMPARISON_JUSTIFIED`.
4. Otherwise, if `all_similar_odd_failure` is true, return
   `PARK_DIRECTION_PER_EXISTING_PRO_MAP`.
5. Any oracle tie, simultaneous conflicting separation, or remaining pattern
   returns `MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED` without a local direction
   decision.

This routing instantiates the already-final Pro result-to-next-action map; it
does not create a new local lifecycle rule. EM must inspect every direct row and
independently recompute the aggregate route. A mechanically unique outcome in
branches 1--4 may execute the existing Pro conclusion without another Pro
round. Branch 5 requires a new `em:ucope:convergence` packet before any direction
conclusion.

## Output and claim ceiling

The create-once output must contain:

- input tree and three top-level file digests;
- exact run binding and 72-record checkpoint inventory before and after;
- central 4 GiB admission receipt digest and resource observations;
- all frozen definition literals;
- exact odd oracle rows;
- all 72 odd-support policy rows and their retained/recomputed even rows;
- policy, seed, arm, checkpoint, paired-separation, curve, and similarity
  summaries;
- every routing predicate and exactly one route label; and
- explicit zero counts for training, environment interaction, optimizer steps,
  checkpoint writes, selection, acquisition evaluation, and COUNT/RAW unlock.

The maximum claim is an A/RECON measurement of where the already-trained B1
policies fail relative to odd training support and even held-out support. It is
not algorithm-effect, competence under the original gate, paid-acquisition,
COUNT/RAW, stable superiority/equivalence, seed-population, pure
representation/optimization, generic UCOPE, variable-`k`, variable-`N`, MARL,
UAV, transfer, safety, deployment, flight, energy, or real-world QoS evidence.

## Evidence

- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_CONVERGENCE_DECISION_INTAKE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_RESULT_EVIDENCE_20260901.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-convergence-20260901-02/RESPONSE.md`
- `temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/result.json`
- `temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/resource-ledger.json`
- `temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/terminal-receipt.json`
- `experiments/candidates/ucope/competence_first_scout_r01/checkpoint.py`
- `experiments/candidates/ucope/competence_first_scout_r01/model.py`
- `experiments/candidates/ucope/competence_first_scout_r01/oracle.py`
- `experiments/candidates/ucope/competence_first_scout_r01/evaluation.py`

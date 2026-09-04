# Scope-1s guidance A1 headroom census R01 — science card

- Direction: `scope_1s`
- Object: `SCOPE1S-GUIDANCE-A1-HEADROOM-CENSUS-R01`
- Evidence class: **A/RECON**
- Frozen: **2026-09-04T07:05:00-07:00**, before the formal exact-SHA census and branch application
- Authority: guidance action A1 in
  `docs/Claude_docs/plans/MARL_EXPLORATION_GUIDANCE_20260904.md`; object-tier only
- Consumption: none; A objects have no consumption state

The guidance document is an alignment draft. Its A1 object is allowed under the standing
delegation, but its proposed MEI, `PARK-CANDIDATE` label, ACTIVE set and Portfolio disposition are
not decisions. This card neither adopts nor applies them.

## 1. Question, claim ceiling and non-goals

**Question.** On the current exact synthetic Q16 toy host, do the committed evidence bytes already
contain both:

1. a stated upper native-return reference; and
2. a tuned generic learner baseline evaluated on the same host, population, information available
   to the candidate policy, native-return definition and work budget,

such that the guidance-A1 quantity

```text
H_A1 = J_upper - J_tuned_same_information_generic
```

is identified without training or launching a learner?

**Maximum claim.** This object may establish only whether that evidence pair is present in the
declared committed Scope-1s surface and, if present, transcribe its already-recorded finite-host
gap. If the pair is absent it may name the missing member. It cannot establish an algorithm effect,
learnability, comparator competence after new tuning, MARL value, production authentication value,
or a lifecycle consequence.

**Non-goals.** Do not train, tune or evaluate a learner; build a baseline; launch B; change the Q16
certificate; apply an unratified MEI; convert the raw `60-32` carrier-separation gap into A1
headroom; bind production authentication; infer safety, security, UAV, deployment or transfer
value; or decide PARK, CLOSE, priority, fusion, separation, registration or investment.

## 2. Frozen host, paths and event-to-consequence trace

The current host is only the two-cell deterministic synthetic object recorded in:

- `experiments/candidates/scope_1s/instance_certificate.py`;
- `tests/experiments/candidates/scope_1s/test_instance_certificate.py`;
- `docs/research/candidates/scope_1s/CODE_SCIENCE_INDEX.md`; and
- the `scope_1s` rows in `DIRECTION.md`, `RESEARCH_MAP.md` and `PORTFOLIO.md`.

The formal census reads these paths at the exact commit containing this card. It does not read
uncommitted concurrent work or another direction's baseline set.

| trace link | frozen reading |
| --- | --- |
| environment event | Within each fixed compatibility cell, the synthetic target bit selects which complete 16-byte Q16 atom is correct. |
| entity and role ownership | One frozen evaluated actor maps `z0` or `z1` to one binary action. Source owner/epoch are excluded from compatibility and actor input; the partner checkpoint is fixed. |
| available information | The import path sees the complete Q16 atom. The historical null sees only the ten current-only `X` bytes and fixed compatibility key. |
| action / credit path | The frozen action is compared with the target bit; native value is `64` for a match, `0` otherwise, minus import cost `4` for an imported atom. |
| learner exposure | None: no model, initialization, optimizer, gradient, update, transition, training episode, checkpoint or selection exposure. |
| native consequence | Exact expected scalar value on the two equal-weight cells and eight target bits per cell. |

Population is fixed at the compatibility label `N=3`. There is no join, leave, rejoin,
replacement, entity/slot ambiguity, survivor state, opportunity/primitive-time distinction,
censoring, semi-Markov discounting, optimizer exposure or partner co-adaptation in this object.

### Binding-MARL-structure assessment

The census records, but cannot make a Portfolio disposition from, whether the current object binds
one of guidance P3's structures: roster/agent-count scaling, temporal abstraction/termination,
multi-agent credit assignment, or other-agent-induced non-stationarity/partial observability.

The prospective DM reading is **none is bound by the current evidence**. `N=3`, anonymous role and
absence are fixed compatibility labels; clusters are isolated; the source and evaluated actor
hashes are equal; and no learner, interacting partner adaptation, joint action or joint credit path
exists. History matters only because the hand-built Q16 atom carries the target bit. That makes the
observed host an information-carrier/authentication toy, not evidence that a MARL structure is the
binding constraint. This is an inference from the frozen trace, not a lifecycle decision.

## 3. Candidate upper reference, comparator and live explanations

**Candidate upper reference.** `CORRECT-Q16` is the recorded correct imported-atom policy with
`J_correct=60`: matching the target yields `64`, and importing costs `4`.

**Required strongest comparator.** A competent tuned generic learner on this same Q16 host must
receive the same candidate-available Q16 atom and current fields, execute a real
learner/trainer/evaluator path, and have a recorded tuning/configuration boundary, work exposure
and native return. A generic learner with weaker information is not eligible.

**Strongest currently cited comparison.** The exact complete nine-map current-only deterministic
envelope has `J_current=32`; RESET is also `32`, and the deranged whole-payload arm is `28`. This is
an exact and useful carrier-separation null, but it is neither a learner nor same-information: it
omits the Q16 atom that `CORRECT-Q16` consumes. It is reporting-only for A1.

Other live explanations for the raw gap are the explicit information advantage, a hard-coded
target-to-action map, the four-unit import cost, and the absence of approximation/optimization
pressure. No observation here can distinguish a MARL representation mechanism from those simpler
explanations.

## 4. Observable, estimand and frozen result rule

The exact-SHA census reports:

1. upper-reference count and its comparable native value;
2. generic learner/trainer/evaluator implementation and result counts;
3. tuned-baseline configuration/result count;
4. information parity with the upper-reference policy;
5. seeds, transitions, optimizer updates, learner evaluations and model-selection exposure;
6. the strongest ineligible existing comparator and raw gap, if available; and
7. whether one of the four P3 MARL structures is directly exercised by the current host.

The estimand `H_A1` is numeric only if items 1–4 identify one matched pair. Otherwise it is
`NOT_IDENTIFIED` and the raw historical gap, if any, is labelled `RAW_INFORMATION_SET_GAP`.

Apply the first matching branch:

1. **`HC-X / AMBIGUOUS_OR_INCOMPARABLE`** — the purported pair has inconsistent host, population,
   information, native metric, or work semantics, or the cited values cannot be recovered. Mapping:
   report the ambiguity; no algorithm polarity, B launch or lifecycle action.
2. **`HC-A / ELIGIBLE_HEADROOM_PAIR_PRESENT`** — both stated upper reference and tuned
   same-information generic learner result exist and are comparable. Mapping: report `H_A1`
   without applying an unratified MEI; return the number to Root's Portfolio aggregation.
3. **`HC-B / UPPER_PRESENT_BASELINE_MISSING`** — the upper reference exists, but no eligible tuned
   same-information generic learner result exists. Mapping: report `H_A1=NOT_IDENTIFIED`; preserve
   any raw mismatched-information gap only as provenance; launch no B and return the baseline gap
   to Root.
4. **`HC-C / BASELINE_PRESENT_UPPER_MISSING`** — an eligible tuned generic result exists but no
   stated upper reference does. Mapping: report `H_A1=NOT_IDENTIFIED` and return the upper-reference
   gap to Root.
5. **`HC-D / PAIR_ABSENT`** — neither member exists. Mapping: report `H_A1=NOT_IDENTIFIED` and both
   missing members; launch no B.

The absence of production Q16/authentication binding is not in this rule and cannot create an
adverse algorithm branch.

## 5. Predictions on record

- **DM:** `HC-B / UPPER_PRESENT_BASELINE_MISSING`. The cited certificate states `correct_value=60`
  and enumerates a current-only envelope, while it explicitly says no return learning, fitting,
  policy learning or selector learning was performed.
- **Owner:** `not taken (unattended)`.

Predictions do not alter the rule.

## 6. Budget, cost, stop rule, portability and exposure

- Seeds and stochastic instances: none.
- Budget: one read-only inventory over the named committed paths and one rule application.
- Stop success: after every item in section 4 has an exact count/status and the first matching
  branch is recorded. Stop as `HC-X` if the committed bytes are internally incomparable.
- Machine-time cap: 60 seconds for the whole static census.
- Cost law: one `git ls-tree` inventory plus bounded `git grep`/source inspection over the named
  paths. This is not a sweep, so no per-arm projection exists.
- Execution semantics: repository-byte portable across configured nodes and independent of CPU,
  GPU, dtype and device. Ordinary read-only control-plane inspection stays local. It is not a
  result-bearing experiment, creates no scientific root/RNG/model/optimizer/checkpoint, and
  therefore requires neither remote result routing nor a resource-admission receipt.
- **Exposure line:** `NO_LEARNED_PARAMETERS; parameter displacement = 0; initialization scale =
  N/A; exposure ratio = N/A`.

There is no resume, retry, checkpoint, duplicate invocation, queue or outcome-informed extension.

## 7. Object-tier unattended decision

Options:

- **(a)** freeze and execute this minimal no-learner exact-SHA A/RECON availability census;
- **(b)** construct or tune a generic learner baseline now, expanding A1 into a new algorithm
  implementation; or
- **(c)** treat the existing raw `60-32` information-set gap as A1 headroom and proceed toward B or
  lifecycle action.

Recommendation: **(a)**. It answers the present evidence-availability question without weakening
information parity, inventing a learner result, or crossing into an unauthorized B or Portfolio
decision.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. The action is reversible and is recorded in the 2026-09-04 audit ledger.

## 8. Protected semantics, technical boundary and engineering scope

The census must not change the certificate's exact rational arithmetic, `HORIZON=64`, target bits,
cells, actor kernels, information ancestry, compatibility key, donor permutation, import cost,
values, RNG (none), checkpoints (none), side effects (none) or source files. Historical provenance
and current authority remain distinct.

No CM implementation objective is needed: the object reads already-committed bytes and writes only
its result evidence and DM intake. Successful commands establish only inventory and transcription;
they cannot establish algorithm value, comparator competence, MARL structure, production binding
or lifecycle state.

**Engineering scope section 4: this object needs none of the default-prohibited items.** It adds no
code, runner, distributed/resumable execution, retry/lease/heartbeat, tamper evidence, provenance
guard, incident tree, schema validator, registry, telemetry, compatibility shim or repeated smoke.
No section 5 code budget is engaged.

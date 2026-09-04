# Scope-1s guidance A1 headroom census R01 — result evidence

- Direction: `scope_1s`
- Object: `SCOPE1S-GUIDANCE-A1-HEADROOM-CENSUS-R01`
- Evidence class / claim ceiling: **A/RECON**; committed-evidence availability only, no algorithm effect
- Card:
  `SCOPE1S_GUIDANCE_A1_HEADROOM_CENSUS_SCIENCE_CARD_20260904.md`
- Census commit: `55d8774303d335bcb4d72242463281ed737c85c5`
- Observation time: `2026-09-04T07:05:44-07:00`
- Validity: **complete static census**
- Result branch: **`HC-B / UPPER_PRESENT_BASELINE_MISSING`**
- Guidance-A1 estimand: **`H_A1=NOT_IDENTIFIED`**

## 1. Direct inventory and receipts

The census read the exact Git tree at the recorded commit. The relevant blob receipts are:

```text
instance_certificate.py blob = 677e4a3d9904d3df2926fcbc309cf8ffa677c3aa
CODE_SCIENCE_INDEX.md blob    = 42627bb3273db9d4709646c96e1ff0675b375b05
```

The complete direction implementation/evidence inventory at that commit was:

```text
docs/research/candidates/scope_1s/CODE_SCIENCE_INDEX.md
docs/research/candidates/scope_1s/DIRECTION.md
docs/research/candidates/scope_1s/SCOPE1S_GUIDANCE_A1_HEADROOM_CENSUS_SCIENCE_CARD_20260904.md
experiments/candidates/scope_1s/instance_certificate.py
tests/experiments/candidates/scope_1s/test_instance_certificate.py
```

Bounded exact-SHA searches observed:

| item | count |
| --- | ---: |
| Scope-1s/Q16 runner paths under `scripts/` | `0` |
| learner/trainer/evaluator/optimizer/baseline/tuning/hyperparameter matches in Scope-1s code and tests | `0` |
| tuned/same-information/generic-learner result matches in the cited `CODE_SCIENCE_INDEX.md` and `DIRECTION.md` | `0` |
| active production Q16/SCOPE-1S binding matches under `ha_ctse_process/`, `envs/`, `scripts/` | `0` |
| exact value/inventory symbol matches in the certificate and test | `12` |

The bounded static commands completed in `1,488 ms`, below the 60-second cap. They created no
result root, RNG master, model, optimizer, checkpoint or external side effect. This was not a
result-bearing experiment, so no memory-admission or resource-telemetry receipt applies.

## 2. Counts, values and exposure

| quantity | direct observation |
| --- | --- |
| stated upper reference | one: exact correct-Q16 imported policy, `J_correct=60` |
| eligible tuned same-information generic learner result | none |
| strongest existing but ineligible comparator | complete nine-map current-only deterministic envelope, `J_current=32` |
| other existing reference | RESET `32`; deranged whole-payload `28` |
| raw correct-minus-current gap | `60-32=28` |
| eligible A1 headroom | `NOT_IDENTIFIED` |
| learner implementations / runners / tuned configs | `0 / 0 / 0` |
| training seeds / transitions / optimizer updates / learner evaluations | `0 / 0 / 0 / 0` |
| model-selection exposure | `0` |

**Exposure line:** `NO_LEARNED_PARAMETERS; parameter displacement=0; initialization scale=N/A;
exposure ratio=N/A`.

The value `28` is labelled **`RAW_INFORMATION_SET_GAP`**, not A1 headroom. The correct-Q16 policy
consumes the complete historical atom. The current-only envelope consumes only `X` and the fixed
compatibility key. No tuned generic learner receiving the complete Q16 atom was implemented or
evaluated.

## 3. Frozen rule applied verbatim

The first applicable branch from the card is:

> **`HC-B / UPPER_PRESENT_BASELINE_MISSING`** — the upper reference exists, but no eligible tuned
> same-information generic learner result exists. Mapping: report `H_A1=NOT_IDENTIFIED`; preserve
> any raw mismatched-information gap only as provenance; launch no B and return the baseline gap
> to Root.

`HC-X` does not apply: the cited exact values, population and information paths are recoverable and
internally consistent. `HC-A` fails because the eligible baseline count is zero. `HC-C` and `HC-D`
fail because the correct-Q16 upper reference is present. The result is therefore exactly
**`HC-B / UPPER_PRESENT_BASELINE_MISSING`**.

No proposed MEI is applied. No algorithm polarity, B authorization, direction lifecycle or
Portfolio disposition follows.

## 4. Direct observation versus inference

Directly observed from the committed bytes:

- a fixed `N=3`, two-cell synthetic certificate with one frozen evaluated actor;
- exact correct/current-only/deranged values `60/32/28`;
- the complete current-only nine-map envelope;
- isolated H=64 clusters, equal source/evaluated actor hashes and a fixed partner checkpoint;
- no Scope-1s learner, trainer, evaluator runner, tuning record or same-information generic result;
- no active production Q16 binding; and
- the historical source's own statement that no stochastic package trial, return learning,
  fitting, policy learning, selector learning or partner adaptation was performed.

Inference, bounded to the current object: none of guidance P3's MARL structures is shown to be the
binding constraint. Fixed roster labels do not exercise agent-count scaling; the object has no
duration/termination choice, multi-agent credit path, interacting partner adaptation, or
other-agent-induced non-stationarity. The current gap is fully compatible with the simpler
explanation that one policy sees the target-bearing Q16 atom and the null does not.

That inference is direction-local advice, not Portfolio action. The Portfolio lifecycle remains
`ACTIVE` until the owner/Root takes a Portfolio-tier decision.

## 5. Validity, deviations and limits

The committed inventory, search scope, values, counts and first-match rule conform to the card.
There was no implementation diff and no engineering-scope section 4 item or section 5 budget. No
scientific/numerical/RNG/checkpoint/side-effect semantic changed. Unrelated concurrent FRRIE and
baseline-set working paths were excluded by the exact commit and named path surface.

The absence of an active production Q16/authentication binding is only an engineering/access fact.
It is not an algorithm negative and was not used to select the branch.

Strongest support for a potentially useful carrier: on the synthetic host, correct Q16 import has
exact value `60` while the complete current-only deterministic envelope has exact value `32`.

Strongest contradiction to an algorithm-headroom reading: the two policies do not receive the
same information, and there is no generic learner, competence/tuning record, learner exposure or
matched result.

Surviving alternative: a competent generic policy or learner given the same complete Q16 atom may
match the hard-coded correct policy, leaving zero mechanism headroom even though the raw
information-set gap is 28.

The next discriminator, if separately selected, is a competent same-information generic baseline
result on this exact toy with matched native return and documented tuning/work exposure. This
result does not open, implement or launch it.

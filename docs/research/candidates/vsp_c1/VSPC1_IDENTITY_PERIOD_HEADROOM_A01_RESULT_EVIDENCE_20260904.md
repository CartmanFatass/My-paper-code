# VSP-C1 identity-by-period headroom A01 — result evidence

- Direction: `vsp_c1`.
- Object: `VSPC1-IDENTITY-PERIOD-HEADROOM-A01`.
- Evidence class / claim ceiling: **A/RECON**; exact-snapshot asset availability and, only if
  defined, one raw matched host gap. No algorithm effect.
- Card: `VSPC1_IDENTITY_PERIOD_HEADROOM_A01_SCIENCE_CARD_20260904.md`.
- Card commit: `86800d009`.
- Census snapshot: `b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`.
- Observation time: `2026-09-04T07:11:14-07:00`.
- Validity: **complete static census**.
- Result branch: **`A01-GAP-UNAVAILABLE-HOST`**.
- `R_upper`: **missing**.
- `R_generic`: **missing**.
- `G_raw = R_upper - R_generic`: **not computable; not zero**.

## 1. Fixed-surface inventory and receipts

The census read only Git objects at the frozen snapshot with `git cat-file`, `git ls-tree`,
`git show`, and bounded `git grep`. The tracked VSP-C1 surface contained:

| surface | count | path or observation |
| --- | ---: | --- |
| implementation | `1` | `experiments/candidates/vsp_c1/constrained_fourth_corner_logit_completion.py` |
| runner | `1` | `scripts/run_vspc1_a1_constrained_fourth_corner_logit_completion.py` |
| config | `0` | no VSP-C1 config path |
| focused test module | `1` | `tests/experiments/candidates/vsp_c1/test_constrained_fourth_corner_logit_completion.py` |
| retained result JSON | `1` | `VSPC1_A1_CONSTRAINED_FOURTH_CORNER_LOGIT_COMPLETION_RESULT.json` |
| other direction documents | `2` | `DIRECTION.md`, `CODE_SCIENCE_INDEX.md` |
| total matched tracked paths | `6` | the paths above |

The index records one accepted publication locator, validator pass, and source commit
`01ccf191d268a99bd97f2dd93cae95765a5049f3`. The retained result JSON itself encodes
`accepted_result_commit=null` and `accepted_source_commit=null`; it has no accepted-result count.
Accordingly the direct inventory distinguishes one tracked result artifact and one index publication
locator from an absent runtime-encoded acceptance count.

## 2. Existing activity counts

The retained result records:

```text
registered_audits                 1
environment_transitions           0
learner_calls                     0
trainer_calls                     0
optimizer_updates                 0
return_evaluations                0
model_fits                        0
focused_production_kernel_calls   0
deterministic_predictor_fits      0
sealed_prediction_receipts        0
stochastic_calls                  0
sweeps_retries_rescues            0
boundary_states                   0
checkpoints                       0
rosters                           0
clones                            0
```

`activity_caps` are limits and were not counted as observed activity. The existing terminal branch
is `A1_HOST_RECTANGLE_UNREACHABLE`; the registered path rejected `toy`, `ORBIT`, `lifecycle`, and
`MSSR` substitutions.

**Exposure line:** no learner exists; new and historical observed parameter displacement are `0`,
initialisation scale is `N/A`, and displacement/initialisation ratio is `N/A`. Observed tuning and
model-selection exposure are zero.

## 3. Headroom ingredient census

| ingredient | state | direct observation |
| --- | --- | --- |
| executable native-return population and weights | **missing** | `host_observation.status="unreachable"`, `constructor_count=0`, `qualified_constructor=null`; `i0/i1/p0/p1`, legal-action order, boundary/checkpoint/roster IDs, and `state_equality_manifest` are null; no population weights are stated |
| intended population provenance | present, design-only | `AIP-VSP-C2-01` proposes a paired `2x2x2` identity-period-partner fixed-boundary utility probe; `RLPA-VSP-C2-01` asks to freeze utility/aggregation weights and a common micro-horizon |
| upper-reference identity and information advantage | **missing** | no admissible native-return upper decision rule is bound |
| `R_upper` | **missing** | no numeric upper native return; null kernel estimands are not returns |
| generic baseline identity | missing as an observed baseline; design-only alternative present | provenance proposes a fully matched recurrent period-only controller without discrete identity |
| population/information/action/work parity | **missing** | no executable input, legal action, population weight, evaluator, work, or exposure record |
| tuning exposure and competence | **missing** | no comparator tuning/model-selection trials or learner-competence observation |
| `R_generic` | **missing** | no numeric generic native return |
| `G_raw` | **unavailable** | neither matched numeric return nor executable common population/weights exists |

`D_C`, `D_N`, `Delta`, mixed-logit residual, and `pre_reveal_js` are all null in the retained result.
Even if non-null, they would be kernel diagnostics rather than native return and would not be
substituted into `G_raw`.

## 4. Frozen rule applied verbatim

The first matching branch from the card is:

> **`A01-GAP-UNAVAILABLE-HOST`**: no executable native-return population and weights are bound.
> Record every additional missing asset; do not interpret absence as zero headroom.

`A01-ASSETS-MISMATCHED` does not apply because no apparent numeric upper/baseline pair exists.
`A01-GAP-AVAILABLE` fails because every numeric term and the common population are missing. The host
branch precedes the upper- and baseline-only missing branches and therefore controls. The result is
exactly **`A01-GAP-UNAVAILABLE-HOST`**.

No relative normalization, MEI, sign threshold, B authorization, direction lifecycle, or Portfolio
disposition is applied.

## 5. Direct observation versus inference

Directly observed:

- the production contract `vspc1.authenticated-identity-period-four-clone-host.v1` has no qualified
  constructor in the inspected modules;
- the registered path constructed no cell, clone, model, state manifest, kernel, learner, or return;
- no executable toy/native-return population, weights, upper value, tuned competent generic result,
  or raw gap is present;
- the current direction states that the fourth-corner design is clean but no real four-clone host
  or value beyond FSBS has been established; and
- the Portfolio row explicitly says missing production-host evidence cannot decide bounded
  compositional learning.

Inference, bounded to this object: the intended partner axis currently controls for partner
co-adaptation; it does not yet demonstrate that a MARL structure is binding. No artifact traces a
partner-owned environment action, decentralized information path, joint credit, partner-induced
non-stationary exposure, or native team consequence. Identity-period composition may involve
temporal abstraction, but that is still design provenance rather than an observed multi-agent
constraint.

That inference is direction-local advice, not a Portfolio action.

## 6. Validity, resources, deviations, and limits

The successful census commands used about `8.9 s` aggregate subprocess wall time. Including one
PowerShell parse failure that occurred before Git executed, control-plane inspection took about
`9.9 s`, below the 10-minute cap. Peak RSS was not instrumented and is recorded
`resources_unmeasured`; no resource claim depends on it.

No VSP-C1 runner, test, Python experiment, preflight, model, RNG, optimizer, checkpoint, scientific
root, or external effect was invoked. This static evidence probe was not a result-bearing
experiment, so remote result routing and memory admission did not apply. The parse failure produced
no repository read or scientific state and does not change the result.

No file was edited during observation. Engineering-scope section 4 additions: none. There was no
section 5 budget breach and no change to scientific, numerical, RNG, checkpoint, or side-effect
semantics.

Strongest support for continued scientific plausibility: the historical design is coherent and
validation-ready as a proposed paired `2x2x2` fixed-boundary utility discriminator, with partner
change and matched nonsemantic controls named prospectively.

Strongest contradiction to a headroom or mechanism reading: the accepted runtime path contains
zero environment transitions, learners, models, and return evaluations, while every headroom term
and the common population are missing.

Surviving alternative: a competent generic learner may contain the proposed factorization, or any
future apparent fourth-corner effect may instead be recurrence, label/support/exposure leakage,
identity-period coupling, or partner co-adaptation.

The next discriminator, only if separately selected at the proper tier, first binds an executable
native-return `2x2x2` population and weights, then states an upper reference and obtains a tuned
competent generic learner on the same information, legal actions, population, and work exposure.
This result neither opens nor launches that work.

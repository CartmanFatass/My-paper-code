# FRRIE B01 section-11 R128 smoke — result evidence (2026-09-04)

Status: `VALID COMPLETE / R128_VALID_NO_CONTACT / B_EXPLORE`

This is the E0 result record for
`FRRIE-B01-SECTION11-R128-SMOKE-20260904`, frozen in
`FRRIE_B01_SECTION11_R128_SMOKE_SCIENCE_CARD_20260904.md` before any result activity.

## 1. Question, class, and claim ceiling

On one prospectively selected B01 root, can byte-paired `PHY_TRUST` and the containing
same-information `EDGE_FLEX` comparator complete 128 real RSCF updates and adaptation-free
evaluation while preserving the paired estimand before tight-boundary contact?

Evidence class: `B/EXPLORE`.

The claim ceiling is one literal seed, fixed training rosters `N={9,15}`, `INTACT`, and updates
`{0,32,64,128}`. This result can establish only the directly observed learner path, exposure,
curves, competence-reference differences, and no-contact equality on that path. It cannot establish
a package effect, stable equality, held-out transfer, reassociation sensitivity, semantic or
relational mechanism value, arbitrary-`N`, churn, deployment, or safety.

| Fact | Value |
| --- | --- |
| Object | `FRRIE-B01-SECTION11-R128-SMOKE-20260904` |
| Result branch | `R128_VALID_NO_CONTACT` |
| Launch SHA | `85b96dc80bb0b75ab605fa0cf606bcbb37649152` |
| Seed | `FRRIE-B01-FRESH-BLOCK-001` |
| Process start | `2026-09-04T10:22:34.6349922Z` |
| Detached PID at dispatch | `15512` |
| Terminal summary time | `2026-09-04T03:56:16-07:00` |
| Summary SHA-256 | `4fc5e015ab5d8a69ce8b0d954a13527e33248dcb539eb4896c9903a8c8bfa091` |
| Summary size | `16,186` bytes |
| stdout / stderr | `0 / 0` bytes |

## 2. Launch conditions and receipts

The exact memory preflight completed immediately before the sole result-bearing process. The seed
packet did not exist before admission and was created by the runner after admission.

| Admission field | Direct value |
| --- | ---: |
| assessed at | `2026-09-04T10:22:34.542675Z` |
| measurement source | `GlobalMemoryStatusEx` |
| physical available | `5,235,474,432` bytes |
| effective available | `5,235,474,432` bytes |
| required floor | `4,294,967,296` bytes |
| physical / effective / overall pass | `true / true / true` |

The machine-generated exposure line was present exactly:

`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768`

The launch record with the exact argv and paths is
`FRRIE_B01_SECTION11_R128_SMOKE_LAUNCH_20260904.md`. Runtime evidence is under:

`temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_r128_root001_85b96dc8_20260904T032143/`

Artifact receipts:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| five-root seed packet | 651 | `3b661df5cacb15aebae8d2bcc0ee8b68d7c769da2ef478881cf8408481e62ce9` |
| admission receipt | 509 | `413ee574c6d58ab869a767c7030f974e31201a4b71c590c6619f6ab33cf5f6f6` |
| `summary.json` | 16,186 | `4fc5e015ab5d8a69ce8b0d954a13527e33248dcb539eb4896c9903a8c8bfa091` |
| package-native DLL | 120,320 | `d22534f6f8c33f0e551e024e3090ab1d394112312ee36c62986b19e23accc19d` |

## 3. Declared versus observed work

Every completion-audit comparison in `summary.json` is `true`.

| Quantity | Frozen | Observed |
| --- | ---: | ---: |
| paired updates | 128 | 128 |
| factual training episodes per arm | 8,192 | 8,192 |
| factual learner transitions per arm | 98,304 | 98,304 |
| counterfactual/audit native slots per arm | 630,784 | 630,784 |
| backward calls per arm | 128 | 128 |
| Adam steps per arm | 128 | 128 |
| learned evaluation episodes per arm | 2,048 | 2,048 |
| learned evaluation slots per arm | 24,576 | 24,576 |
| uniform-reference slots, shared | 6,144 | 6,144 |
| total evaluation episodes | 4,608 | 4,608 |
| total evaluation transitions | 55,296 | 55,296 |
| total invocation slots | 1,316,864 | 1,316,864 |
| successful paired information/work assertions | 128 | 128 |
| successful pre-contact information assertions | 128 | 128 |

The same in-memory evaluation tape objects were reused for all nine cells at each roster. Torch
intra-op threads were directly recorded as one, and the native width was 32.

## 4. Return curves and descriptive estimands

Each line below contains two separate arm observations. The slash notation records their direct
equality; it is not a pooled statistic. `d_u = J_PHY - J_EDGE` and
`e_u = J_EDGE - J_UNIFORM` are literal-seed descriptions.

| update | N | J PHY / EDGE | D_W PHY / EDGE | D_E PHY / EDGE | min PHY / EDGE | WASTE PHY / EDGE | d_u | e_u |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 9 | 0.019199722 / 0.019199722 | 0.0703125 / 0.0703125 | 0.0585938 / 0.0585938 | 0.0078125 / 0.0078125 | 0.954161637 / 0.954161637 | 0 | +0.000522306 |
| 0 | 15 | 0.025930051 / 0.025930051 | 0.1015625 / 0.1015625 | 0.0781250 / 0.0781250 | 0.0195313 / 0.0195313 | 0.951636985 / 0.951636985 | 0 | -0.000189612 |
| 32 | 9 | 0.020339197 / 0.020339197 | 0.0781250 / 0.0781250 | 0.0625000 / 0.0625000 | 0.0078125 / 0.0078125 | 0.955462193 / 0.955462193 | 0 | +0.001661782 |
| 32 | 15 | 0.028642193 / 0.028642193 | 0.1250000 / 0.1250000 | 0.0820313 / 0.0820313 | 0.0156250 / 0.0156250 | 0.950882760 / 0.950882760 | 0 | +0.002522529 |
| 64 | 9 | 0.020412998 / 0.020412998 | 0.0781250 / 0.0781250 | 0.0625000 / 0.0625000 | 0.0078125 / 0.0078125 | 0.954724190 / 0.954724190 | 0 | +0.001735582 |
| 64 | 15 | 0.029196700 / 0.029196700 | 0.1210938 / 0.1210938 | 0.0898438 / 0.0898438 | 0.0156250 / 0.0156250 | 0.949569456 / 0.949569456 | 0 | +0.003077037 |
| 128 | 9 | 0.019578672 / 0.019578672 | 0.0703125 / 0.0703125 | 0.0625000 / 0.0625000 | 0.0078125 / 0.0078125 | 0.954603900 / 0.954603900 | 0 | +0.000901257 |
| 128 | 15 | 0.026351086 / 0.026351086 | 0.1093750 / 0.1093750 | 0.0781250 / 0.0781250 | 0.0117188 / 0.0117188 | 0.949379767 / 0.949379767 | 0 | +0.000231422 |

The checkpoint-invariant `UNIFORM_LEGAL` cells were:

| N | J | D_W | D_E | min | WASTE |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 0.018677416 | 0.0703125 | 0.0546875 | 0.0078125 | 0.955152927 |
| 15 | 0.026119664 | 0.1054688 | 0.0781250 | 0.0156250 | 0.950717425 |

EDGE competence relative to uniform was therefore mixed at update 0 (`N=15` was lower by
`0.000189612`) and positive but small in both final cells (`+0.000901257` and `+0.000231422`). This
is reported literally and is not a general competence conclusion.

## 5. Action and native-event counts

The action vector order is native indices `[0,1,2,3,4,5]`. The event tuple order is
`(duplicate, expired, collision, empty_radio, radio_actions, waste_actions, successful_deliveries)`.
PHY and EDGE were directly identical in every row.

| update | N | action counts, PHY = EDGE | native events, PHY = EDGE |
| ---: | ---: | --- | --- |
| 0 | 9 | `[6268,6101,2191,2324,2404,8360]` | `(5,204,197,7382,13020,12432,33)` |
| 0 | 15 | `[10557,10123,3661,4009,3997,13733]` | `(5,368,611,12301,21790,20738,46)` |
| 32 | 9 | `[6127,6337,2215,2321,2483,8165]` | `(5,207,197,7680,13356,12768,36)` |
| 32 | 15 | `[10227,10703,3725,4017,4167,13241]` | `(8,394,674,12959,22612,21501,53)` |
| 64 | 9 | `[6095,6372,2250,2339,2416,8176]` | `(5,202,195,7656,13377,12778,36)` |
| 64 | 15 | `[10120,10830,3810,4053,4024,13243]` | `(8,393,684,12931,22717,21572,54)` |
| 128 | 9 | `[6129,6300,2301,2297,2324,8297]` | `(5,203,199,7490,13222,12630,34)` |
| 128 | 15 | `[10224,10620,3905,3982,3798,13551]` | `(7,399,678,12508,22305,21176,48)` |

Uniform action/event counts were `[6079,6229,2257,2288,2346,8449]` and
`(4,196,189,7477,13120,12541,32)` at `N=9`; and
`[10126,10292,3736,3961,3849,14116]` and
`(5,372,590,12350,21838,20763,47)` at `N=15`.

## 6. Exposure, contact, and direct equality

| Observable | PHY_TRUST | EDGE_FLEX |
| --- | ---: | ---: |
| `L_inf(theta_128-theta_0)/0.05` | 0.573677719 | 0.573677719 |
| first tight-contact update | none | n/a |
| changed tight coordinates | 0 | n/a |
| maximum tight overshoot | 0 | n/a |
| cumulative tight-projection displacement | 0 | n/a |
| wide-boundary contact | n/a | false |

All 128 pre-contact full model/optimizer checks passed. At all four checkpoints the two arms had
identical direct action traces and terminal native primitives on the shared tapes. Evaluation
preserved model and optimizer bytes. Thus the observed `d_u=0` rows are direct equality on this
one no-contact path, not a universal equality claim.

## 7. Frozen result rule applied

1. `R128_INVALID_INCOMPLETE` does not fire: admission passed; all 22 completion checks are true;
   learner, update, work, evaluation, exposure, tape-reuse, pairing, and measurement facts are
   present and nonzero.
2. `R128_VALID_NO_CONTACT` fires: the complete valid rung has no FP32-changing tight projection
   through update 128.
3. `R128_VALID_CONTACT` does not fire: first contact is null and the changed-coordinate inventory
   is empty.

Result: **`R128_VALID_NO_CONTACT`**.

## 8. Resource and engineering observations

- Total wall time was `2,017.963704 s` (`33.633 min`), below the eight-hour cap.
- Direct attributed learned-arm wall was `383.316154 s` for PHY and `383.350473 s` for EDGE,
  below the four-hour per-arm caps. Shared seed/tape/build/uniform work remains only in total wall.
- Observed aggregate throughput was `652.571` declared slots/s.
- The runner could not obtain peak RSS, so the valid run is marked `resources_unmeasured` under the
  telemetry rule. No resource claim is made.
- The monitor retained no numeric Windows process exit code. Direct observations are that the
  process terminated, `summary.json` is complete, and both redirected logs are empty.
- The existing native builder first created its DLL under the package-local untracked `_native`
  directory. After terminal, DM moved that exact 120,320-byte artifact into this run root; its
  SHA-256 was unchanged. This restored a clean Git boundary and did not change executed bytes or
  outcome artifacts.
- The accepted implementation added 614 research-code lines, with about 25.1% orchestration, and
  no engineering-scope §4 item. The stable focused suite reported `3 passed` before launch.

## 9. Prediction and bounded reading

The DM prediction `R128_VALID_NO_CONTACT` is supported by the registered branch. The owner slot was
`not taken (unattended)`. The observed maximum parameter displacement was about `0.028684` in
absolute units, and the tight projection never changed an FP32 coordinate.

The strongest support is the complete 128-update direct pairing audit plus exact equality of both
learned arms on every checkpoint cell. The strongest contradiction to any stronger reading is that
the treatment never activated: equality before contact cannot establish whether the tight package
helps, harms, or is equivalent once contact occurs. EDGE's margin over uniform is also small and
mixed at checkpoint 0. The curves peak at update 64 and fall by update 128 on both rosters, so this
one path does not support monotone learning or stable competence.

The surviving explanations remain no contact, host alignment to the common `K0` chart, generic
Adam/shrinkage geometry, literal-seed evaluation noise, and an effect that appears only at longer
exposure. The next discriminator is the unchanged prospectively frozen three-seed B01 rung using
roots `001..003`; this result does not authorize a seed, comparator, treatment, or configuration
change.

## 10. Could not verify

- behavior after tight-boundary contact;
- held-out `N={6,21}` transfer or `SEMANTIC_COLUMN_ROTATE` sensitivity;
- stable EDGE competence or a seed-population effect;
- peak RSS;
- any semantic, relational, arbitrary-`N`, churn, deployment, or safety claim.

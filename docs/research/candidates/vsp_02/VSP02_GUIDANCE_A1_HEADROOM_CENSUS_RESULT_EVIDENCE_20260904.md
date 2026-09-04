# VSP-02 guidance A1 headroom census — result evidence

- Direction: `vsp_02`
- Object: `VSP02-GUIDANCE-A1-HEADROOM-CENSUS-R01`
- Evidence class: **A/RECON**
- Card:
  [VSP02_GUIDANCE_A1_HEADROOM_CENSUS_SCIENCE_CARD_20260904.md](VSP02_GUIDANCE_A1_HEADROOM_CENSUS_SCIENCE_CARD_20260904.md)
- Bound evidence commit: `b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`
- Observation completed: `2026-09-04T07:06:00-07:00`
- Validity: **VALID_COMPLETE**
- Branch: **HC-A / MATCHED_GREEDY_HEADROOM_ZERO**

## E0. Direct observation

The bound VSP-02/OEER evidence surface matched the freeze-time checkout byte-for-byte. The formal
read-only pass recovered the following accepted B1V2 facts:

- `X_MEMORY_TABULAR_MONTE_CARLO` has strict correct held-out mapping in `5/5` seeds;
- every accepted X-memory seed has stored mixture-policy `J_eval=1.35`;
- the current host has sixteen held-out owner epochs, two cues, and both forced actions per clone;
- X-memory trains on `1,024` real episodes and performs `1,024` tabular sample-mean updates per
  seed; and
- the fixed evaluator-only deterministic oracle is the legal correct cue map.

The exact public-cue greedy values are:

| cue | legal upper / X-memory greedy action | native return | weight |
| --- | --- | ---: | ---: |
| `0` | `HOLD` | `2` | `1/2` |
| `1` | `RELEASE` | `1` | `1/2` |

Therefore:

```text
J_upper_greedy = (2 + 1) / 2 = 3/2 = 1.50
J_generic_greedy(seed) = 3/2 for each of five accepted seeds
mean J_generic_greedy = 3/2 = 1.50
H_greedy = J_upper_greedy - mean J_generic_greedy = 0
```

The historical unaligned subtraction is also retained:

```text
deterministic oracle J                  = 3/2  = 1.50
X-memory exploratory-mixture J_eval     = 27/20 = 1.35
raw unmatched difference                = 3/20 = 0.15
```

The `0.15` comes from unlike evaluation policies. The baseline's correct greedy action is selected
with probability `0.9` and the other action with probability `0.1`; the historical oracle acts
deterministically. Under the same mixture constraint the oracle has `J=27/20`, so its matched gap
to X-memory is also zero.

## E1. Population, information, work, and counts

| quantity | upper reference | generic baseline | new A census |
| --- | ---: | ---: | ---: |
| held-out owner epochs | 16 | 16 per seed | 0 new |
| cues per epoch | 2 | 2 | 0 new |
| forced-action rows | 64 | 64 per seed, 320 total | 0 new |
| policy-value clones | 32 | 32 per seed, 160 total | 0 new |
| accepted seeds | deterministic | 5 | 0 new |
| training episodes | 0 | 1,024 per seed, 5,120 total | 0 |
| tabular learner/trainer updates | 0 | 1,024 per seed, 5,120 total | 0 |
| optimizer/gradient updates | 0 | 0 | 0 |
| model-selection/tuning draws | 0 | 0 | 0 |
| checkpoints | 0 | no selected checkpoint | 0 |
| result-bearing invocations | historical only | historical only | 0 |

Upper and comparator receive the same presented public cue and are projected through the same
greedy action rule, finite clone weights, host physics, and native-return definition. The generic
table ignores owner-epoch and static-roster nuisance fields. Because it reaches the exact upper,
that omission cannot hide additional return on this population.

The baseline has no tuning sweep. Its eligibility here comes only from exact finite-population
saturation: every accepted seed has the unique legal optimal greedy action on every held-out
clone. This is not evidence of tuned competence on any other budget or population.

## E2. Rule applied verbatim

The card's ordered rule is:

1. `HC-X / EVIDENCE_OR_SEMANTICS_INCOHERENT` if evidence, validity, support, or matched semantics
   cannot be recovered.
2. `HC-A / MATCHED_GREEDY_HEADROOM_ZERO` if all five X-memory seeds have the strict correct greedy
   map and exact return `3/2`, equal to the upper.
3. `HC-B / MATCHED_GREEDY_HEADROOM_POSITIVE` if the valid competent comparator is below `3/2`.
4. `HC-C / COMPETENT_GENERIC_BASELINE_NOT_ESTABLISHED` if the upper exists but comparator
   competence/support does not.

Observed inputs:

```text
bound_surface_match=true
B1V2 accepted result branch=B1V2_FULL_LEARNER_FAILED
X-memory strict exact positive seeds=5/5
X-memory stored mixture J per accepted seed=1.35
X-memory greedy J per accepted seed=1.50
upper greedy J=1.50
matched H=0
```

First match: **branch 2, HC-A / MATCHED_GREEDY_HEADROOM_ZERO**.

Mapping applied: report `H_greedy=0`, close only this A1 measurement on this finite host, apply no
MEI, and admit no B.

## E3. Current-host MARL binding observation

Direct code facts are:

- visible roster is fixed to `owner-A, partner-B`;
- authoritative membership contains one episode-specific owner token;
- slot id is fixed at `3`;
- partner policy is a frozen no-op;
- every episode creates a new owner epoch and closes it after one owner action;
- no episode carries a surviving entity across a membership event; and
- B5R1 resets Adam after common training update zero, then trains updates 1 through 127.

Inference: no agent-count/roster-change, temporal-abstraction, multi-agent-credit, or
other-agent-induced non-stationarity structure is binding on this host. The optimizer boundary is
not a roster-age event. This inference has no lifecycle or fusion authority.

## E4. Contrary observation

The accepted B5R1 artifact is valid and directly reports:

```text
branch = B5_NO_EXACT_ENDPOINT_LOCALIZATION_ON_PANEL
C = R = {VSP02-B5R1-U03}
mean J_eval(ADAM_CARRY) = 0.9742296612860173
mean J_eval(ADAM_RESET) = 0.9704376397224330
paired mean difference = +0.00379202156358438
paired differences =
  +0.00008012628977382974
  +0.012640381205219042
  +0.005812391030736830
  +0.0004521023633767829
  -0.00002489307118458406
```

B5R1 prospectively declared scalar metrics descriptive only. This observation contradicts any
claim that equal exact-success sets imply identical trajectories, but it neither changes the A1
gap nor establishes optimizer-state value.

OEER's accepted separate-host `D_H` near `-0.0250633` is preserved as historical support that
carried Adam state can affect a trajectory. OEER explicitly supplies no variable-N evidence and no
polarity transfer into VSP-02.

## E5. Evidence receipts

| path | bytes | Git blob at bound commit | SHA-256 |
| --- | ---: | --- | --- |
| `docs/research/candidates/vsp_02/VSP02_B1V2_CODE_SCIENCE_INDEX.md` | 7,529 | `6787ef7259f8ca7fe15893121b3183c07eb83f73` | `4989444326ee6e297402874b50aa281599d046adbe5266a2f1cbf719bb5d329a` |
| `docs/research/candidates/vsp_02/VSP02_B1V2_LEARNED_CUE_CONDITIONED_LIFECYCLE_CONTROL_RESULT.json` | 817 | `ce00bb2fc443a2fcccf420d2e458964d9410da9a` | `d07cf10f86def8b4bf1cfaa0ef723f4bef672de62cc40c8b5fa75c6590c0a74b` |
| `docs/research/candidates/vsp_02/VSP02_B5R1_WINDOWS_RESOURCE_ADMISSION_RESULT.json` | 83,663,399 | `4f787cc9566b86eebecb4879f6fc32f57a455603` | `fac05ecda451c40f6f7095d7e440ea456557cc2f1fbd44086a2f8890f09eecc5` |
| `experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py` | 73,742 | `3464bd0745212211551c345a6994db1b5e24211a` | `77a028325338f006e788f68535a608b43b519b4a62cf797b00c2e852ea3829e1` |
| `experiments/candidates/vsp_02/vsp02_b5r1_windows_resource_admission.py` | 113,361 | `31a1fafbd9d307be1cb456c046329eaaef543876` | `b7682fc2f70106f0d9ef6764c2bca931d1a9845b894b60e435bd9fd0dbc3fadb` |
| `docs/research/legacy/directions/optimizer_entropy_exposure_boundary_relay/OEER_B1_SCIENTIFIC_INTAKE.md` | 6,302 | `5cbb4a3087687bc9b5f6b2fc352a9a1515eb5dbd` | `ccbd922d5439d76c5f6df5140e56b26c49d08d9fc7ffd701ba1e934164330670` |
| `docs/research/legacy/directions/optimizer_entropy_exposure_boundary_relay/OEER_PROJECT_ALIGNMENT_ADDENDUM.md` | 6,067 | `4b7b157af516cffb3f8370c9a4d50c0da8469a28` | `db295894179c8ac28d1076849b1e9e6c12dd85ec070cfd681096154b0c67bd2f` |

The B5R1 artifact's retained internal evidence digest is
`29ba8a5b1d6c7476d2dbee077c7ecac07eef11e70d21d9d26cf3202d5d6b1e60`.

## E6. Runtime, resources, deviations, and side effects

There was no A result-bearing run. The observation used Git/object inspection, retained JSON
reading, and exact arithmetic on the local control plane. It created no scientific root, resource
receipt, RNG, model, optimizer, checkpoint, environment transition, or evaluator call. Therefore
remote-first dispatch and the 4 GiB result preflight were not applicable.

Machine time stayed within the 15-minute card cap. No sweep, retry, resume, repair, new source,
test, runner, or engineering-scope section 4 item was used. There are no numerical, RNG,
checkpoint, comparison, side-effect, or resource deviations.

Exposure line:

```text
NO_NEW_LEARNER; parameter displacement=0; initialization scale=N/A;
exposure ratio=N/A; new transitions=0; new gradient-bearing updates=0;
new model-selection exposure=0.
```

## E7. Bounded result

The strongest supported reading is that the accepted simple same-information X-memory learner's
greedy policy already attains the exact legal public-cue optimum on the finite current host, so the
matched terminal headroom is zero. The strongest contradiction is B5R1's nonidentical continuous
carry/reset metrics despite equal exact-success sets.

This result does not say that optimizer state is irrelevant, does not measure a roster-age
population, and does not authorize B, PARK, closure, or fusion.

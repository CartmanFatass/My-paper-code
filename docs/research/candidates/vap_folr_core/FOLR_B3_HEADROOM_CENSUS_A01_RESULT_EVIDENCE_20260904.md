# FOLR B3 current-host headroom census A01 — result evidence

- Direction: `vap_folr_core`
- Object: `FOLR-B3-HEADROOM-CENSUS-A01`
- Evidence class: **A/RECON**
- Frozen card: `FOLR_B3_HEADROOM_CENSUS_A01_SCIENCE_CARD_20260904.md`
- Card commit, pushed before the bounded census: `6d741e898`
- Evidence state inspected: `b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`
- Result branch: **`HC-B / UPPER_PRESENT_BASELINE_MISSING`**
- Result-bearing learner or environment invocation: **none**

## 1. Bounded result

The current B3 host has an exact physical upper reference in both regimes:

```text
J_upper_clean = 1
J_upper_stale = 1
```

The host's unique terminal reward is `1` exactly when the four-action choice equals
`2*s+n_new`, so the privileged no-learner `DIRECT-TARGET-ORACLE` attains the upper bound on every
registered evaluation row.

No eligible tuned same-host generic learner baseline exists in the accepted B3 record. The
retained B3 result states `phase_r_ran=false`, `metrics=null`, and zero Phase-R training and
evaluation episodes after Phase-P writer calibration failed. The registered
`ISOMORPHIC_GENERIC_UPDATE` arm therefore produced no checkpoint, complete curve, held-out return,
or tuning/selection result on the current host.

Accordingly:

```text
J_generic_clean = MISSING
J_generic_stale = MISSING
H_clean = NOT_IDENTIFIED
H_stale = NOT_IDENTIFIED
```

`NOT_IDENTIFIED` is not zero headroom, generic sufficiency, typed failure, or direction polarity.
No MEI was applied and no B object was launched.

## 2. Rule applied verbatim

The card requires the first matching branch:

1. **`HC-X / EVIDENCE_PATH_INCOHERENT`.** A named source cannot be read, B3 validity is internally
   contradictory, or host/population/information semantics cannot be recovered. Report no gap,
   launch nothing, and return the documentary defect to Root.
2. **`HC-A / RAW_HEADROOM_IDENTIFIED`.** Both exact upper values and a valid tuned competent B3
   same-information generic result exist on matched support. Report `J_upper`, `J_generic`,
   `H_clean`, and `H_stale` with no threshold or disposition.
3. **`HC-B / UPPER_PRESENT_BASELINE_MISSING`.** The exact upper reference exists, but no valid
   tuned competent B3 generic result exists. Report both `H` values as `NOT_IDENTIFIED`, name the
   baseline deficit, apply no threshold, and launch no B.
4. **`HC-C / BASELINE_PRESENT_UPPER_MISSING`.** An eligible B3 generic result exists but no valid
   stated upper reference exists. Report the missing reference and no `H`.
5. **`HC-D / PAIR_ABSENT`.** Neither eligible quantity exists. Report both deficits and no `H`.

Application:

- `HC-X` is false: all twelve bound blobs are readable and their host, population, information,
  reward, and result semantics are coherent.
- `HC-A` is false: the B3 generic baseline slot is empty.
- `HC-B` is true: the exact unit upper exists and the tuned competent B3 generic result does not.

The unique result is therefore **`HC-B / UPPER_PRESENT_BASELINE_MISSING`**.

## 3. Direct observations and counts

### Upper-reference path

At the bound source bytes:

- Phase-R training constructs target `2*s+n_new`;
- Phase-R evaluation constructs the same target; and
- the host computes `reward = float(action == target)`.

All three source predicates are present. Reward lies in `{0,1}`, and direct target choice attains
`1`; no sampled or learned oracle execution is needed.

### Retained B3 record

| field | direct value |
| --- | ---: |
| terminal decision | `B3_PARTNER_WRITE_CALIBRATION_FAILED` |
| `phase_r_ran` | `false` |
| `metrics` | `null` |
| Phase-R training episodes | `0` |
| Phase-R evaluation episodes | `0` |
| Phase-R learner/trainer/optimizer updates | `0` |
| all recorded learner calls | `256`, all Phase P |
| sweeps | `0` |
| checkpoint selections | `0` |
| Phase-P aggregate accuracy | `0.94482421875` |
| Phase-P calibration passed | `false` |

The unexecuted Phase-R manifest named eight seeds, 32 batches of 64 training episodes per arm,
512 evaluation episodes per regime and seed, and one fixed learning rate `0.025`. A manifest is not
an observation. It also contains no baseline tuning or sweep result.

### New exposure and side effects

| quantity | count |
| --- | ---: |
| new seeds / stochastic instances | `0` |
| new environment transitions / policy calls | `0 / 0` |
| new learner / trainer / optimizer updates | `0 / 0 / 0` |
| new evaluations / checkpoints / selections | `0 / 0 / 0` |
| new scientific invocations / run roots | `0 / 0` |
| committed evidence blobs inspected | `12` |

Resource admission and runtime telemetry are not applicable because no result-bearing experiment
or scientific process was created. This is not a `resources_unmeasured` learner result.

## 4. Evidence receipts

The bound commit and Git blob identities make the inspected bytes recoverable:

| role | path | blob OID |
| --- | --- | --- |
| direction authority | `docs/research/candidates/vap_folr_core/DIRECTION.md` | `35534971c35e3ffa56348344c188b13ea08fce95` |
| navigation | `docs/research/RESEARCH_MAP.md` | `ce90c2fdedb05981805da8ca7376951bb08d0538` |
| lifecycle snapshot | `docs/research/portfolio/PORTFOLIO.md` | `d99eb02d3c5e0c75556f09aba9fed71344d91f07` |
| B3 index | `FOLR_B3_CALIBRATED_PARTNER_WRITER_STALE_LOAD_ROUTING_CODE_SCIENCE_INDEX.md` | `08395741a1c3d9f4f00d43ec1cd51ec3432838cb` |
| B3 result | `FOLR_B3_CALIBRATED_PARTNER_WRITER_STALE_LOAD_ROUTING_RESULT.json` | `03d5ceaae296313f8fd6bb68d8cf2c972864862b` |
| B3 actor/runner core | `experiments/candidates/folr_core/partner_writer_stale_load_routing.py` | `4163c8364db89ced70fe0922c764df59e288d82e` |
| B3 host | `experiments/candidates/folr_core/partner_writer_stale_load_routing_host.py` | `0711df53a471f0ea4b191fb7f29aa4e2097e8d10` |
| B2 index | `FOLR_B2_COUNTERFACTUAL_WITNESS_GATED_NUISANCE_TRANSFER_CODE_SCIENCE_INDEX.md` | `3151d36268f1a8294138395d55b74c0bd94f67dc` |
| B2 result | `FOLR_B2_COUNTERFACTUAL_WITNESS_GATED_NUISANCE_TRANSFER_RESULT.json` | `bfb2e52d798903374d4e7d8e3209572a751897a4` |
| B1 index | `FOLR_B1_OWNER_EPOCH_SURVIVOR_BIT_LEARNABILITY_CODE_SCIENCE_INDEX.md` | `c031ccdfc2b6cc2d7837b9acd31b096191e0f015` |
| B1 result | `FOLR_B1_OWNER_EPOCH_SURVIVOR_BIT_LEARNABILITY_RESULT.json` | `1ad41b644b452c697691d92a9ab93d19a45f964b` |
| guidance provenance | `docs/Claude_docs/plans/MARL_EXPLORATION_GUIDANCE_20260904.md` | `840c63ffc274211720bdf2eb767235bcd4535d3f` |

All short paths in the direction directory are relative to
`docs/research/candidates/vap_folr_core/`.

## 5. Strongest support, contradiction, and bounded inference

**Strongest support.** The B3 result directly combines `phase_r_ran=false`, `metrics=null`, and
zero Phase-R train/evaluation counts. No current-host generic return exists to subtract from the
unit physical upper.

**Strongest contrary observations.** These prevent a broader adverse reading:

- B3's constructive class-nesting witness shows that the generic transition class can exactly
  represent the typed mapping by zeroing obsolete-state columns. Representation containment is
  not achieved finite-budget return.
- On the different B2 host, fixed-config `ISOMORPHIC_GENERIC_MEMORY` recorded
  `J_changed=0.58203125` and `J_diagonal=0.78759765625`; B2 nevertheless ended at
  `RESET_LEAK_OR_NEW_PARTNER_CALIBRATION_FAILED` and is neither the B3 host nor a tuned B3 baseline.
- B1 retained `S03_LEARNED_USE_WITH_GENERIC_CAPACITY_CONFIRMED` on its different two-transition
  host. It shows related-host learnability, not B3 headroom.
- B3 Phase P was near its frozen aggregate gate (`0.94482421875`) but failed it, so writer repair
  may be feasible; that cannot be converted into Phase-R competence or return.

**Inference, not direct observation.** The event-to-consequence trace binds roster replacement and
entity/epoch-owned latent state under other-agent-induced partial observability. The fact that the
treatment is a typed information-flow mask does not remove that MARL structure. This classification
does not establish that typed routing helps and does not select a Portfolio lifecycle.

## 6. Deviations and integrity boundary

One provisional PowerShell transcription command attempted to assign the host source to reserved
variable `$Host` and returned a `WriteError`; its derived reward predicate was discarded. The
failing read was immediately reproduced over the same recorded host blob with variable
`$b3HostSource`, confirming the target, evaluation-target, and binary-equality-reward predicates
all `true`. No source bytes, population, rule, or result changed, and no scientific process or
artifact was created. This is a reproduced control-plane transcription error, not scientific
polarity or a second evidence attempt.

There was no implementation, no section-4 machinery, and no section-5 budget breach. Test success,
source readability, and the upper-reference derivation are engineering/evidence conformance; they
do not establish mechanism value.

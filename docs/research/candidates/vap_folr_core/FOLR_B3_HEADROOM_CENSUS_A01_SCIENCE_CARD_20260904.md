# FOLR B3 current-host headroom census A01 — science card

- Direction: `vap_folr_core`
- Object id: `FOLR-B3-HEADROOM-CENSUS-A01`
- Evidence class: **A/RECON**
- Frozen: **2026-09-04T07:05:01-07:00**, before the bounded field census and result-rule application
- Authority: guidance action A1, selected locally at Object tier under the standing unattended
  delegation
- Evidence bytes under review: repository state
  `b9c63e6d8fbc6f8b74470c8e2312c2c1b42c6a8c`

This is a read-only evidence-availability and measurement audit. It does not train, repair, tune,
or execute a learner, and A/RECON has no consumption state. The guidance document is an alignment
draft: its proposed MEI, `PARK-CANDIDATE` label, ACTIVE set, and Portfolio disposition are not
decisions and do not enter this object's rule.

## 1. Question, claim ceiling, and non-goals

On the current B3 `PartnerWriterStaleLoadHost`, do the accepted records contain both:

1. a stated upper native-return reference on the B3 `CLEAN` and `STALE_LOAD` population; and
2. a valid, tuned, competent generic learner baseline on that same host, with the strongest legal
   information set and matched evaluation support,

so that the raw current-host gaps

```text
H_clean = J_upper_clean - J_generic_clean
H_stale = J_upper_stale - J_generic_stale
```

can be reported without constructing or running a learner?

**Claim ceiling.** This object may establish only whether the matched evidence pair exists at the
bound Git state, transcribe the raw gaps if it does, or name the exact missing quantity if it does
not. A numeric result would remain a finite-host measurement fact under the recorded population,
information, and work exposure. It cannot establish a typed-routing effect, generic sufficiency or
failure, writer competence, learnability, sample efficiency, general MARL value, transfer, safety,
deployment value, or a lifecycle consequence.

**Non-goals.** Do not repair Phase P, train or tune Phase R, create a baseline, rerun B1/B2/B3,
apply the unratified MEI, launch B, weaken the generic comparator, substitute a related host,
reinterpret a calibration stop as algorithm polarity, or decide PARK, CLOSE, priority, capacity,
fusion, separation, registration, or investment.

## 2. Current host and binding MARL structure

The current host is the B3 three-transition roster-replacement object, not the earlier B1 or B2
host. It holds two active members before the event (`owner_t@0`, `inert_partner_q0@0`), applies one
atomic `TERMINAL_LEAVE(q0) + JOIN(q1)` transaction while preserving `owner_t@0`, installs a
new-partner write, and then makes one four-action terminal choice.

The binding MARL structure is **roster replacement with entity/epoch-owned latent state under
other-agent-induced partial observability**. Active cardinality remains two, so this is not an
agent-count-scaling object. The question is whether finite-budget generic learning can ignore a
departed partner's stale candidate while retaining survivor-private and new-partner information.
That is a roster-conditioned multi-agent representation/action problem even though the immediate
treatment is an information-flow mask.

| trace link | current-host meaning |
| --- | --- |
| environment event | At transition 2, `inert_partner_q0@0` leaves terminally and distinct entity `inert_partner_q1@0` joins; `owner_t@0` survives. There is no rejoin. |
| entity/role ownership | The owner record and epoch persist; q0's lifecycle-owned state is invalidated; q1 owns a newly written payload. Entity keys, not reusable slots, determine continuity. |
| available information | Public observations contain only nuisance root/time. Learned hidden candidates carry survivor bit `s`, obsolete-partner bit `n_old`, and new-partner bit `n_new`. No arm label, target, cached action, or kernel is public input. |
| action or credit path | The common actor maps the routed hidden state to one of four actions encoding `(s,n_new)`; ordinary sampled terminal reward supplies REINFORCE credit. |
| learner exposure | B3 intended eight paired seeds, 32 batches of 64 episodes per Phase-R arm, identical initialization/schema/optimizer/data budget, and 512 final-checkpoint evaluations per regime. This census adds zero exposure. |
| native consequence | Terminal reward is exactly one when the chosen action equals `2*s+n_new`, otherwise zero; every record is then cleared. |

This trace confirms a direction-local MARL structure only. A competent generic learner may still
solve it; that is precisely why the same-host generic baseline is required. The guidance's
information-flow classification cannot by itself select a direction-tier PARK decision.

## 3. Upper reference, baseline, evidence path, and live explanations

### Stated upper reference

`DIRECT-TARGET-ORACLE` is the no-learner physical upper reference. On each B3 evaluation row it
sees the privileged target pair `(s,n_new)` and chooses action `2*s+n_new`. The host source defines
reward as exact action-target equality, so

```text
J_upper_clean = J_upper_stale = 1
```

on the complete registered B3 evaluation support. This oracle is intentionally privileged and is
not an attainable-policy claim; it is only the exact upper end of the native-return scale.

### Required strongest generic baseline

The eligible baseline is a tuned, competent `ISOMORPHIC_GENERIC_UPDATE` learner on the same B3
host. It must receive every B3 candidate channel available before routing, use the same frozen
partner-writer semantics and native reward, have a recorded tuning/selection boundary and complete
curves, and be evaluated on the same `CLEAN`/`STALE_LOAD` support. It may use the obsolete channel
and can represent the typed mapping by zeroing its obsolete-state columns; it therefore may not be
replaced by RESET or by a weaker-information null.

The treatment is one bounded read-only pass over:

- `docs/research/candidates/vap_folr_core/DIRECTION.md`;
- `docs/research/RESEARCH_MAP.md` and `docs/research/portfolio/PORTFOLIO.md`;
- `docs/research/candidates/vap_folr_core/FOLR_B3_CALIBRATED_PARTNER_WRITER_STALE_LOAD_ROUTING_CODE_SCIENCE_INDEX.md`;
- `docs/research/candidates/vap_folr_core/FOLR_B3_CALIBRATED_PARTNER_WRITER_STALE_LOAD_ROUTING_RESULT.json`;
- `experiments/candidates/folr_core/partner_writer_stale_load_routing.py` and
  `partner_writer_stale_load_routing_host.py`;
- the B1 and B2 code-science indexes and public results, used only as contrary related-host
  observations; and
- `docs/Claude_docs/plans/MARL_EXPLORATION_GUIDANCE_20260904.md`, used only to define A1.

For each candidate value the census records host, regime/population, information set, validity,
learner/tuning status, exposure, and whether it is eligible for either slot. It does not infer a
missing number from architecture containment or from a different host.

Live explanations kept separate are:

- the B3 generic learner might match typed routing once the partner writer and learner are
  competent, leaving little or no typed-routing headroom;
- the generic class contains the typed mapping but may need more finite-budget optimization to
  ignore stale `n_old`;
- Phase P writer variance, rather than the routed actor, may be the active bottleneck;
- the physical upper may leave substantial raw room while no attainable tuned learner has yet
  measured it; and
- B1/B2 related-host learnability may survive without supplying a comparable B3 baseline.

## 4. Observable, estimand, and ordered result rule

The census reports:

1. the exact B3 upper-reference values and their source path;
2. Phase-R execution status, generic metric presence, and Phase-R train/evaluation/update counts;
3. any tuning or model-selection record for the B3 generic learner;
4. information, host, population, native-return, and work comparability;
5. `H_clean` and `H_stale` only when both eligible slots exist;
6. related-host numeric results as contrary observations, never as substitutions; and
7. the current binding-MARL-structure assessment from section 2.

Apply the first matching branch verbatim after the single pass:

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

Phase-P accuracy, a generic-class nesting witness, a B1/B2 return, RESET performance, or an
unexecuted Phase-R manifest cannot fill the tuned B3 generic-baseline slot.

## 5. Predictions on record

- **DM:** `HC-B / UPPER_PRESENT_BASELINE_MISSING`. The B3 host gives an exact unit return ceiling,
  while the retained result says Phase R did not run after writer calibration failed. This
  prediction follows preliminary authority triage before the bounded field census; it is not an
  independently blinded prediction.
- **Owner:** `not taken (unattended)`.

Predictions do not alter the result rule.

## 6. Budget, stop rule, portability, and exposure

- Seeds: none for this census. Historical seed identities are reporting-only.
- Evidence budget: one pass over the named committed paths at the bound Git state.
- New learner, environment, policy, trainer, evaluator, model fit, optimizer update, checkpoint,
  or result-bearing experimental invocation: none.
- Machine-time cap: 15 minutes of local control-plane document/source inspection. Stop earlier
  once each candidate quantity has a validity and role classification.
- Stop success: one branch from section 4, exact counts and source receipts, raw gaps or the exact
  deficit, the contrary observation, and a bounded intake.
- Stop refusal: unreadable or contradictory bytes select `HC-X`; no repair or new execution occurs
  inside this object.
- Portability: the repository-byte audit is portable across the configured local and remote nodes;
  CPU, GPU, dtype, and device are not part of its estimand. It remains on the local control plane
  because there is no result-bearing compute invocation. The B3 scientific host is an environment,
  not the Windows execution host.
- Resource admission: not applicable; no experiment, RNG master, model, optimizer, checkpoint, or
  scientific run root is created.
- **Exposure line:** new learner parameters `0`; initialization scale `N/A`; parameter
  displacement `0`; displacement/initialization ratio `N/A`; new transitions, updates, evaluation
  episodes, and model-selection exposure all `0`.
- Sweep/per-arm projection: none; there are no execution arms or runner cost law.

## 7. Protected semantics, side effects, and engineering scope

Historical scientific, numerical, float32, RNG, checkpoint, comparison, information-flow, and
side-effect semantics are read-only. The census must not alter B1/B2/B3 bytes, source, results,
writer thresholds, seed panels, actor schemas, masks, native reward, or branch rules. Historical
provenance and current authority remain distinct.

The only permitted side effects are this card, its result evidence and intake, an accepted-science
update in `DIRECTION.md`, and the required audit-ledger rows. No runtime artifact is created.
Technical completion can establish only that the named bytes were inspected and classified by the
frozen rule; it cannot establish mechanism value, baseline competence, or scientific polarity.

**This object needs none of the default-prohibited machinery in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4.** It adds no code, runner, tests,
distributed/resumable execution, retry/lease/heartbeat, tamper evidence, provenance guard,
incident tree, schema validator, registry, telemetry, compatibility shim, or repeated smoke. No
section 5 code budget is engaged or breached.

## 8. Object-tier unattended decision

Options:

- **(a)** substitute the fixed-config B2 generic result from a different host and report
  `1 - J_B2_generic` as B3 headroom;
- **(b)** freeze this minimal read-only current-host census and report raw gaps only if the eligible
  pair exists, otherwise report the exact deficit; or
- **(c)** repair the writer, tune or train a new generic learner, apply the proposed MEI, or launch
  Phase R/B now.

Recommendation: **(b)**. It answers guidance A1 at the smallest class, preserves current-host and
information parity, and cannot smuggle an unauthorized learner, B launch, or Portfolio decision
into reconnaissance.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** Provenance label:
`OWNER_DELEGATED`. The choice is reversible before a future object is separately authorized.

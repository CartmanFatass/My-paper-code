# DISH RBHR r04 accepted-Pro-defect resolution map

```text
document_kind=direction_science_revision_resolution_map
direction_id=degraded_incumbent_shadow_handover
prior_revision=DISH-RBHR-SCIENCE-20260821-03
replacement_revision=DISH-RBHR-SCIENCE-20260821-04
accepted_defect_count=20
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
result_blind=true
r03_mutated=false
r04_mathematical_closure=false
science_activity_authorized=false
```

This map records how the indivisible seven-file r04 normative composite
resolves every numbered requirement accepted in the r03 Pro intake. It is an
audit aid, not a partial erratum or a substitute for the normative bytes. R03
remains immutable and supplies no default.

1. **Responder-route draw probabilities.** Host section 3 makes speed, turn
   magnitude and turn sign mutually independent discrete-uniform draws over
   their displayed finite sets and defines the radian angle. Evaluation onset
   is only the accepted-slot assignment; training onset is only the Omega
   entry. The total RNG table binds each route draw and contains no onset draw.

2. **Wind initial state.** Host section 1 sets `w[0]=(0,0) m/s^2`
   deterministically before the registered innovation recurrence.

3. **Turn-boundary velocity.** Host section 3 makes responder velocity
   left-continuous, with `(v_g,0)` through `t=tau_d` and the turned velocity
   only for `t>tau_d`. SOURCE and every scripted calculation use the same law.

4. **External-k recurrence.** Host section 6 supplies the literal countdown
   state, reset, decrement, renewal, pending-switch, epoch increment and
   carry-forward recurrence. A switch is noticed at the first tick at or after
   `tau_k`, never truncates the held command, and changes `k_active` before the
   first pending renewal's observation and action.

5. **Switched evaluation assignment.** Host section 5 uses the sole mapping
   `q=j mod 12`, `tau_d=(42,54,66)[q mod 3]` and
   `tau_k=(36,48,60,72)[floor(q/3)]`. Each Cartesian pair occurs four times
   across the 48 cell tapes while preserving the onset cycle.

6. **Training reflection, owner and physical identity.** Training section 5
   defines `m=4*episode_wave+lane_within_cell`; bits 0, 1 and 2 of `m mod 8`
   bind reflection, initial owner and `q_A/q_B` assignment in displayed
   zero/one order. This exact eight-way cycle is independent of Omega and all
   stochastic route/noise addresses.

7. **Total RNG and one SOURCE body.** Host section 9 and the separate total RNG
   allocation table jointly define a uniform 256-bit master, a finite field
   vocabulary and a complete tuple for route, geometry, phase, Omega, arm,
   parameter, policy, minibatch, physical-noise, packet, rejection-candidate,
   winning-attempt and bootstrap values. Evaluation
   `accepted_slot=16*stratum_ordinal+ell` and the smallest qualifying attempt
   `a*` bind every accepted future value. One `hop=NONE` SOURCE body is reused
   byte-for-byte for both first hops; only the directed RADIO margin address is
   hop-specific.

8. **Tick, delivery, terminal and fork indices.** Payload section 1 gives one
   ordered start-terminal, prior-arrival, switch/intent, filter/controller,
   post-reservation-send, service/motion/energy recurrence. An intent formed at
   `n` can first apply at `n+1`. Controller section 8 and inference section 5
   place the fork clone after application-tick arrivals and SOURCE-buffer
   processing and immediately before CAS, then execute ticks
   `n_app,...,n_app+99` with terminal absorption.

9. **Two-stage certificate.** Controller section 5 stores the exact
   origin-renewal conjunction, including causal warmup, prediction,
   maintainability, separation and raw slew. Section 5.4 separately orders the
   next-tick delivery/integrity, stored-pass, one-use, bound-readiness,
   owner/epoch/sequence/lineage/k, terminal, application-MAINT, SEP and SLEW
   checks. It explicitly does not re-evaluate renewal, degradation latch,
   warmup, Mahalanobis or service prediction. Only a delivered transfer request
   failing this application law increments invalid commit.

10. **Post-reservation versions and lineage.** Payload section 1 requires the
    live owner to reserve/form its relay and increment the next sequence before
    any current control serialization. Controller section 4 defines a causal
    one-tick SOURCE-lineage lock, exact snapshot/readiness acceptance, the
    post-reservation version tuple and the intent-bound readiness record. The
    origin SNAPSHOT and intent share the physical hop; application checks the
    same owner, epoch, next sequence, common SOURCE lineage and k epoch before
    CAS.

11. **Complete deployed controller.** Controller section 2 fixes four zero
    recurrent states, the charged one-tick STATE partner channel, every ordered
    component/unit/source/sentinel of the 54-vector, the encoder and explicit
    GRU gates, every head and copy authority, four motion log-standard
    deviations, exact 96/48/32/24-byte message fields and encodings, snapshot
    bridge and assimilation, the complete causal centralized-critic vector and
    three independent Welford conventions. Section 9 excludes uncharged or
    hidden inputs and deletes the former base acknowledgement.

12. **Four-state application-boundary prediction.** Controller section 5
    emits positive-definite four-state means/covariances and propagates the
    owner snapshot and the one-tick-delayed readiness prediction with `F` and
    accumulated `Q` to their common application boundary. The readiness from
    `r` is usable only at origin `r+1` for application `r+2`; its standby
    prediction uses two-step propagation, and the projected-position
    Mahalanobis covariance includes both propagated uncertainties. Training
    section 2 gives the consistent next-state Gaussian target and coherent
    readiness-horizon service labels.

13. **Executable masked PPO.** Training section 3 defines raw GAE, the
    unnormalized return target `R=A_raw+V_old`, clipped policy/value losses and
    the exact likelihood/entropy mask. Both authoritative raw pre-projection
    motion actions, behaviorally live STRUCTURED/FLEX/NEVER prepare bits,
    STRUCTURED/FLEX commit bits and NEVER's live NOOP bit enter. Simple-rule
    protocol bits are excluded, as are held, terminal and hard-masked
    dimensions. Policy advantages alone are normalized. The four global motion
    log-standard deviations are ordered and trained under the frozen range.

14. **Executable auxiliary objective.** Training section 2 defines four-state
    Gaussian NLL, two softplus-plus-`1e-3` link Gaussian NLLs, next-camera BCE
    and one coherent 20-tick passive clone for the authoritative standby. Its
    legal hypothetical applies at the readiness-bound boundary, holds the
    current command until a candidate exists, masks illegal/post-handover/
    terminal examples, averages every eligible term arithmetically and sets
    `L_aux=(L_target+L_link+L_missing+L_passive)/4`.

15. **Recovery witness and continuity.** Inference section 3 gives the finite
    command/owner enumeration, causal 20-tick receding-horizon planner,
    decaying current wind with future innovations zero, zero future camera/
    radio/SOURCE innovations, deterministic tie order and exact scripted
    transfer version/buffer/role recurrence. Its maintainability and witness
    continuity require zero token gap, dual owner, dual payload, buffer clear,
    command-slew breach, separation breach and battery exhaustion in their
    registered windows.

16. **Propulsion and energy reducers.** Payload section 6 defines live
    `dt*P_i[n]` and absorbing `650*dt` propulsion energy. Inference section 6
    forms each tape's literal total, the arithmetic mean of all sixteen tape
    totals, the treatment-relative block ratio, the common-trigger REAL/SHAM
    ratio and zero-denominator rules. Zero-trigger fork blocks store numeric
    zero plus `fork_supported=0`; support prevents interpretation. All 24 block
    ratios enter the simultaneous family.

17. **Phase diagnostics.** Inference section 7 defines, separately for every
    contrast, endpoint, exact `(r,s,z)` branch cell and initial phase, the
    phase-subset contrast, same-cell all-sixteen contrast and their difference.
    The analogous energy-ratio difference is included. Each is a separate
    max-t diagnostic with no cross-stratum, cross-schedule or cross-regime
    pooling and no pass-rule authority.

18. **Package-local competence.** Inference section 4.1 lets atomic
    `u=(r,s)` use only no-degradation calibration and pre-onset competence from
    the same package `r`, for all five arms, calibration k values and required
    strata. Other-package competence is diagnostic only and cannot alter the
    package label.

19. **Reachable simple-rule fallback.** Inference sections 4 and 8 evaluate
    headroom and numerical precision before adaptive support. Each fallback
    rule must independently establish RULE-versus-NEVER value/nonharm and
    RULE-versus-STRUCTURED noninferiority without CORE. On support failure,
    IMMEDIATE is selected first, then HYSTERESIS; a tie records both and selects
    IMMEDIATE. Otherwise the label is support not established.

20. **FLEX-relative nonretention.** Inference section 8 defines
    `FLEX_REL=VALUE(F,S) AND NH(F,S)` and preserves the broader-family label
    only when the additional fork and FLEX-versus-NEVER conditions in FLEXQUAL
    pass. Any direct FLEX-relative value precludes STRUCTURED retention. If
    FLEX_REL holds without FLEXQUAL, the prospectively named
    `FLEX_RELATIVE_NONRETENTION` branch is returned rather than STRUCTURED.

## Resolution conclusion

All twenty accepted r03 defects have one visible prospective resolution in the
complete r04 composite. This is an EM-authored definition freeze, not Pro
closure. The next possible provider action is one separately authorized strict
continuation in the saved DISH Pro conversation using a new exact operation
identity and the complete r04 bytes. Provider dispatch remains held pending
Portfolio's explicit shared-slot release. No Gemini, CM or scientific activity
is authorized by this map.

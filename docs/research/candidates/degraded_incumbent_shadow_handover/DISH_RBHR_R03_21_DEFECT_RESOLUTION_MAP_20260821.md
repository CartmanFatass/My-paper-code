# DISH RBHR r03 accepted-Pro-defect resolution map

```text
document_kind=direction_science_revision_resolution_map
direction_id=degraded_incumbent_shadow_handover
prior_revision=DISH-RBHR-SCIENCE-20260821-02
replacement_revision=DISH-RBHR-SCIENCE-20260821-03
accepted_defect_count=21
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
result_blind=true
r02_mutated=false
r03_mathematical_closure=false
science_activity_authorized=false
```

This map records how the complete r03 composite resolves the exact numbered
requirements accepted in the r02 Pro intake. It is not a partial erratum and
does not modify r02. All cited r03 files are required together.

1. **Revision bindings.** The r03 science card and treatment manifest bind
   definition-only status and at most one successful handover to revision 03,
   every learned arm and every fork trajectory. No r01/r02 operative sentence
   supplies a default.

2. **One onset boundary.** Host section 4 activates either added package only
   on `tau_d<=n*dt<tau_d+4.0 s`; no added intervention is active earlier.
   Pre-onset, event and opportunity windows use the same `tau_d` boundary.

3. **Package, not pure-channel, semantics.** The two names are visual-mask and
   relay-mask packages. The former adds no radio impairment but retains ordinary
   radio failure; the latter adds no camera impairment but retains ordinary
   missingness. The card and claim ceiling use only package language.

4. **Payload/service recurrence.** The payload manifest fixes a 40-byte opaque
   responder SOURCE, two independent first hops, capacity-one per-UAV buffers,
   owner-only 64-byte second hop, one-tick margin-threshold delivery/no retry,
   sequence/epoch creation, one-packet base replacement, packet noise, message
   sizes, age and propagated-position error. Its literal service equation
   requires packet existence, age `<=0.5 s`, error `<=8 m` and both stored
   margins `>=6 dB`.

5. **Terminal and cost recurrence.** Payload sections 6–7 define separation/
   battery terminal predicates, propulsion/byte energy, absorbing 650-W tail,
   protocol bytes, invalid commit, gap, dual owner/payload, clear, slew and
   separation indicators. Full-arm cost is 1,200 ticks; fork cost is its 100
   ticks; service deficit continues after terminal.

6. **Unambiguous actuator mapping.** Treatment section 1 gives four recurrent
   copies and exact authority: incumbent copy drives incumbent and payload;
   standby shadow drives standby/readiness; promotion and demotion occur in one
   CAS. Section 5 applies masks to STRUCTURED, FLEX, NEVER and both rules; the
   fork law is explicit.

7. **Executable certificate.** Treatment sections 2–4 define `D` by camera OR
   margin, one-/five-tick rule latches, positive-definite covariance factors,
   regularized Cholesky Mahalanobis, twenty-tick Poisson-binomial 95% lower
   score, auxiliary labels, warmup/reset, exact version/age/sequence checks,
   maintainability, separation, slew and fail-closed next-boundary evaluation.

8. **Literal FLEX containment.** Treatment section 6 gives domains and
   equations for `DeltaI`, `alpha`, readiness residual `r` and boundary blend
   `beta`, fixes residual-before-common-projection order, and proves by tick
   induction equality at `(0,1,0,0)` for states, messages, certificate,
   payload/token state and applied actions.

9. **Complete learned training law.** Training sections 1–4 fix service-only
   reward, Gaussian/Bernoulli action distributions, Xavier initialization,
   observation normalization, primitive GAE, clipped policy/value/entropy/aux
   losses, every material PPO/AdamW number, four epochs, 64-tick recurrent
   fragments, minibatches, bootstrap, advantage/gradient rules and sole
   update-1024 checkpoint.

10. **Sealed training generator.** Training section 5 assigns exactly 32 lanes
    x 128 ticks to the two packages x four schedules, continues 1,200-tick
    episodes across updates, uses unrejected base draws, enumerates onset/
    switch/phase Cartesian sets, matches only physical tapes across arms and
    forbids reuse across coordinates.

11. **Paired no-degradation competence populations.** Host section 8 pairs
    every accepted tape with a view that disables only its added package and
    shares all exogenous values. Training sections 6–7 fix 24-block counts,
    fixed-4/fixed-12 full-episode calibration block values and exact
    `[tau_d-20 s,tau_d)` pre-onset values for all five arms.

12. **Arm-independent advantage strata.** Host section 7 supplies a fully
    scripted controller from reset, desired points/gains/projection, geometric
    and token-safe candidate time, exact five-second transfer/retain assay and
    rejection of no-eligible/intermediate candidates. No learned quantity
    enters assignment.

13. **Complete RNG and reflection identity.** Host section 9 adds block, split,
    regime, schedule, accepted slot, candidate attempt, arm substream,
    degradation view, fork branch, episode, tick, field and draw identities;
    enumerates every domain and PACKET/INFERENCE purpose; freezes lowest-attempt
    selection, common paired/fork streams and the complete world/reflection
    transformation.

14. **Competence-ordered recovery witness.** Inference sections 3–4 put
    competence before a causal finite-action scripted recovery witness, define
    per-tape `O_bci`, per-block/cell `q_bc`, continuity and a simultaneous
    `L(q)>=0.50` rule. Failure is `NO_REGISTERED_RECOVERY_WITNESS`, bounded
    nonidentification—not a ceiling, package deletion or impossibility claim.

15. **Single-valued gates.** Inference section 4 fixes all-arm competence
    bounds/cells, opportunity denominators, trigger and behavior-changing rates,
    state/action norms with `1e-3` tolerances, `[0.25,0.85]` headroom, witness
    gain and numerical direct-effect/energy half-width rules. Qualitative
    precision/censoring alternatives have no authority.

16. **Total first-trigger fork.** Inference section 5 uses the first valid
    STRUCTURED intent with `tau_d<=t<tau_d+20 s` and `t<=110 s`, runs exactly
    100 ticks with absorption, requires per-block/cell support and stores an
    explicit zero plus unsupported flag if none. No block disappears.

17. **Exact endpoint reducers.** Inference section 2 fixes 200/100-tick windows,
    arithmetic service/deficit/delay reducers, fractional empirical lower-tail
    CVaR, the start of the first full ten-valid-tick recovery run and full-window
    cap.

18. **Renewal phase diagnostic only.** Inference section 1 makes
    regime x schedule x advantage stratum the branch-authority cell and
    regime x schedule the atomic supercell. Phase contrasts remain balanced and
    inside max-t but never create a pass requirement.

19. **Complete inference/effect algebra.** Inference sections 6–7 define the 24
    clusters, exhaustive hypothesis vector, 99,999 shared block resamples,
    max-t studentization, zero-SE behavior, 95,000th critical order statistic,
    benefit signs, VALUE/NO-MATERIAL/MATERIAL-HARM/NONINFERIOR, fork/full
    margins, FLEX/rule contrast directions, energy ratio and zero denominator.

20. **Reachable ordered branches.** Inference section 8 restricts harm to
    S-N, REAL-SHAM and absolute nonharm; puts a defined full-population
    nonactuation-package branch before fork nonpass; deletes prohibited
    SHAM-versus-NEVER diagnostics; separates numerical nonanswerability from
    the final threshold-crossing catch-all; and gives NO-MATERIAL a guard that
    keeps it reachable.

21. **Schedule/regime aggregation and rule retention.** Inference section 9
    first returns all six regime x schedule supercell labels, then requires one
    retained class across all three schedules within a regime, reports fixed-8
    value separately when either switch does not match, and crosses regimes
    only after both pass. A retained rule must independently pass RULE-N value,
    nonharm and RULE-S noninferiority in every required supercell; IMMEDIATE is
    the frozen two-rule tie-break.

## Resolution conclusion

All twenty-one accepted defects have one visible prospective resolution in the
complete r03 composite. This is an EM-authored replacement definition, not Pro
closure. The next possible mathematical action is one separately authorized
continuation in the saved r02 Pro conversation using the complete r03 bytes.
No provider, Gemini, CM or scientific activity is authorized by this map.

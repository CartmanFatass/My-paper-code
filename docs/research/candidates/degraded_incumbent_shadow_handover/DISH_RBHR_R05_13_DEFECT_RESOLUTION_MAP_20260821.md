# DISH RBHR r05 accepted-Pro-defect resolution map

```text
document_kind=direction_science_revision_resolution_map
direction_id=degraded_incumbent_shadow_handover
prior_revision=DISH-RBHR-SCIENCE-20260821-04
replacement_revision=DISH-RBHR-SCIENCE-20260821-05
accepted_defect_count=13
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
result_blind=true
r04_mutated=false
r05_mathematical_closure=false
science_activity_authorized=false
```

This map records how the indivisible seven-file r05 normative composite
resolves every numbered requirement accepted in the r04 Pro intake. It is an
audit aid, not a partial erratum or a source of treatment defaults. R04 remains
immutable and supplies no default.

1. **Calibration and claim admission use one law.** Host section 7 applies the
   same increasing candidate-attempt scan, scripted-stratum thresholds,
   `100000` cap and lowest-qualifying-attempt rule to every evaluation schedule
   in `{K4,K8,K12,K4_TO_K12,K12_TO_K4}`. It binds `split=CALIBRATION` only to
   `K4,K12` and `split=CLAIM` to the three claim schedules. Training/population
   section 6 retains the same 48-tape population in every evaluation cell.

2. **Training ordinals are total.** The total RNG table assigns global lanes
   `0..31` consecutively to the eight displayed package/schedule rows, fixes
   `lane_within_cell=lane mod 4`, defines fixed-schedule Omega ordinal
   `d*k+p`, switched-schedule ordinal `((d*4+h)*k_initial)+p`, and defines each
   recurrent fragment by `f=2*lane+q` for the two displayed 64-tick lane
   halves. Training section 5 repeats the global row binding. No container or
   traversal order remains selectable.

3. **Snapshot and readiness sequence versions are causal.** Controller
   sections 2.1 and 4 make the snapshot next-sequence field an acceptance-time
   version checked only against the delivery tick's current pre-reservation
   sequence. It is historical afterward. READINESS binds the accepted
   snapshot's owner/epoch/SOURCE/`k` tuple and its own send tick's
   post-reservation sequence. At readiness acceptance, row 54 and origin
   `MATCH`, the current pre-reservation sequence compares only with the newest
   readiness; owner/epoch/common-SOURCE/`k` versions continue to match the
   accepted snapshot and readiness as applicable.

4. **The learned snapshot information mask is exact.** Controller section 2.3
   keeps every wire header for deterministic validation but gives the learned
   snapshot encoder exactly eighteen continuous inputs: four prediction means,
   ten covariance entries, two owner margins and two owner raw boundary-action
   means. It binds `W_snapshot` to `128 x 18`, `W_bridge` to `128 x 256` and
   Welford statistics to those fields only. Physical identity, absolute tick,
   epoch and sequence headers cannot enter the learned policy.

5. **Covariance factor and wire orders are fixed.** Controller section 2.3
   orders Cholesky outputs as
   `(l00,l10,l11,l20,l21,l22,l30,l31,l32,l33)`, applies the positive diagonal
   map only to `l00,l11,l22,l33`, and serializes symmetric covariance as
   `(P00,P01,P02,P03,P11,P12,P13,P22,P23,P33)`. The encoder, float32 wire,
   reconstruction, propagation and auxiliary loss use that one order.

6. **FLEX `DeltaI` timing is acyclic.** On first snapshot acceptance,
   controller section 2.3 computes `u_I[n]` and `DeltaI[n]` only from the
   pre-assimilation prior-tick standby-shadow state, forms `h_bar` from that
   same prior state and snapshot embedding, installs the selected STRUCTURED/
   FLEX `h_prev`, and executes one GRU update. It forbids recomputation from
   `h_bar` or post-update state. `alpha`, readiness residual and `beta` are
   evaluated from the post-GRU readiness-tick state.

7. **Certificate action domains are literal.** Controller section 5 defines
   pre-projection sample `y_i`, norm-clipped action `b_i` and applied command
   `a_i=P_n(y_i)`. Origin SLEW is exactly
   `||b_i[n]-a_i[n-1]||<=1.5` for both vehicles. The bound origin record keeps
   `y,b,a`; application uses exact current and one-tick-held separation
   equations and `||b_i[n_app-1]-a_i[n_app-2]||<=1.5`. No raw-head mean,
   sampled `y` or applied `a` may replace `b` in those predicates.

8. **Delayed-message and FLEX PPO replay is complete.** Training section 3.1
   records raw stochastic samples and hard rollout facts; detaches fragment-
   initial recurrent/protocol state; replays all four recurrent states,
   snapshot assimilation, `DeltaI`, learned continuous messages and successful
   recurrent promotion edits with current parameters; fixes host/delivery/
   version/CAS facts as stop-gradient; and uses a straight-through derivative
   for registered float32 forward rounding. Commit probability and beta-bound
   standby-motion likelihood are attributed to the bound origin renewal.
   `alpha`/`DeltaI` receive only within-fragment recurrent gradients. Section 1
   makes AdamW's `lambda` unconstrained and uses only forward
   `ell=clip(lambda,-5,1)` with the exact derivative and no post-update
   projection.

9. **Auxiliary terminal and horizon labels are total.** Training section 2
   masks next-target/link/missingness unless `n<=1198` and the next tick is
   nonterminal. A passive-service example requires `r+2<=1199`; later requested
   horizon bits are zero in an auxiliary-only absorbing state with no
   post-horizon observation. Payload section 1 makes tick-1199 transmissions
   expire if their delivery/application lies after the episode and forbids a
   post-episode invalid-commit event.

10. **Planning and scripted transfer are causal and complete.** Host section 7
    and inference section 3 use the same linear causal twenty-tick target
    forecast `g_plan[n+j]=g_xy(t_n)+j*dt*gdot_xy(t_n)` and reissue the candidate
    projected command pair at simulated renewals while the external-`k`
    recurrence advances. Only the first interval executes before actual
    replanning. Evaluator scripts emit no learned control messages but retain
    charged SOURCE/SERVICE_RELAY/STATE traffic. A scripted transfer arms the
    common SOURCE-lineage lock, records the post-reservation sequence and
    revalidates exact owner/epoch/sequence/lineage/terminal/battery/separation/
    slew one tick later. Failure changes no ownership, emits no result, creates
    no learned invalid commit and replans at the next renewal.

11. **REAL and SHAM have matched observable transaction bookkeeping.**
    Controller section 8 makes both branches increment service epoch once,
    preserve next sequence and every buffer, set `handover_used`, complete
    preparation, reset warmup, invalidate old versions, cease later transaction
    messages and expose identical completion state. REAL alone changes owner,
    promotes the prepared recurrent state and remaps actuators; SHAM retains
    owner, active incumbent state and mapping. No separate observable
    `transaction_used` exists.

12. **The common max-t family has total block reducers.** Inference sections 3
    and 4 store numeric-zero support rates plus an explicit denominator flag
    when a block has no opportunity tapes; WITNESS fails before SUPPORT while
    the family remains numeric. Every per-tape diagnostic uses its stated
    sixteen-tape arithmetic block mean. Section 6 defines hard-event rate as
    the fraction of trajectories with at least one event in the cost window,
    including total zero-trigger fork storage, and defines full-arm phase energy
    means, ratios and within-cell differences under the frozen zero-denominator
    law.

13. **Trigger-conditioned fork phase diagnostics are removed.** Inference
    section 7 item 6 includes phase diagnostics only for unconditioned full-arm
    contrasts `S-N,F-S,F-N,I-N,I-S,H-N,H-S` and their full-arm energy ratios.
    It expressly excludes phase-specific REAL-SHAM and fork-energy diagnostics
    because those trigger-conditioned phase subsets need not be populated.
    Schedule-wide REAL-SHAM effects remain in the simultaneous family with full
    branch authority. Science-card section 11 uses the same full-arm meaning.

## Resolution conclusion

All thirteen accepted r04 defects have one visible prospective resolution in
the complete r05 composite. Every unaffected host equation, two mask packages,
five learned arms, training/claim schedules, 24-block and accepted-tape counts,
finite learning budget, endpoint/margin algebra, branch precedence and claim
ceiling remain unchanged. This is an EM-authored definition freeze, not Pro
closure. The next possible provider action is one separately authorized strict
continuation in the existing DISH Pro conversation using the complete r05
bytes and a fresh operation identity. No provider turn, Gemini, CM or
scientific activity is authorized by this map.

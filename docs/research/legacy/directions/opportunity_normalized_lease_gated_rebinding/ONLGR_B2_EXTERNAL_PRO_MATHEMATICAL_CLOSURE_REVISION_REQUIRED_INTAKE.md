# ONLGR-B2 External-Pro mathematical-closure revision intake

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager  
Candidate: `ONLGR-B2-STATE-BLIND-EVENT-RATE-FLEXIBILITY`  
Reviewed revision: `ONLGR-B2-SCIENCE-20260814-01`  
Replacement revision: `ONLGR-B2-SCIENCE-20260814-02`  
Provider disposition: `REVISION_REQUIRED`  
Scientific activity started: `false`  

## Conclusion

The same existing ONLGR ChatGPT External-Pro conversation accepted the basic
two-arm causal contrast, event law, fixed-mark likelihood, matched initial
action distribution, learned global-rate comparator, IID estimand, support
counts, and bounded positive claim. It identified four science-bearing
ambiguities. The EM accepts all four and has frozen their complete prospective
correction in revision 02 before any B2 task activity.

## Accepted defects and exact correction

1. **PPO behavior and critic targets.** Revision 01 did not independently freeze
   the four-epoch behavior log probabilities, value/advantage/lambda targets,
   detachment, terminal base case, critic-boundary set, value clipping, or
   single application of the value coefficient. Revision 02 now caches rollout
   behavior log probabilities, `V^-`, `A^-`, and detached `G^lambda` once before
   epoch one; uses them unchanged for all four epochs; defines the terminal and
   critic-boundary rules; prohibits value clipping; and applies coefficient
   `0.5` exactly once.
2. **Activity boundary.** Revision 01 began activity only at a retained
   parameter/optimizer update. Revision 02 begins activity at the earliest
   retention, inspection, or use of any learned-arm task trajectory or
   informative task statistic, or any retained learned-state update. Only a
   discarded contract dry run or purely analytic probability/Jacobian check
   with no retained task evidence remains preactivity.
3. **Coincident safety/IID scheduling.** Revision 02 defines one global
   routine-draw ordinal: every scheduled routine boundary emits exactly one
   next-`k` draw after boundary processing; a coincident forced safety action
   suppresses the routine policy action but still advances the ordinal once;
   an off-grid safety boundary advances it zero times.
4. **Support and nonpassage.** Revision 02 separately defines `PACKAGE_VALID`
   and `MARK_SUPPORT_OK`. Retention and absorption both require both. A valid
   package with failed frozen support is
   `INCONCLUSIVE_INSUFFICIENT_VOLUNTARY_SUPPORT` and activates neither branch.
   Absorption after supported statistical nonpassage is explicitly a frozen
   simplicity action, not equivalence, noninferiority, sufficiency, harm, or a
   general no-benefit claim.

## Claim boundary and next action

Revision 01 cannot activate either result branch. Revision 02 preserves the
portfolio claim ceiling: at most a finite-host, finite-training-budget return
advantage from actor access to the registered task-content-blind timing vector
over the learned zero-input global-rate comparator. It cannot establish use or
causal value of an individual coordinate, the eligible-exposure link against
another link, task-content value, lease/`REBIND`/literal-hazard causality,
within-resource-cap success, arbitrary `k`, variable `N`, UAV transfer, or
general superiority.

The exact complete revision 02 returns to the same Pro conversation for the
required `CLOSED` or `REVISION_REQUIRED` ruling. It is not sent to CM before a
`CLOSED` ruling and same-direction EM intake.

## Provenance

- Frozen card:
  `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_B2_STATE_BLIND_EVENT_RATE_FLEXIBILITY_SCIENCE_CARD.md`
- Strict transport archive:
  `temp/sessions/agentify_transport_operator/independent_research_explorer/onlgr_b2_chatgpt_pro_math_closure_20260814_01/results.json`
- Raw response mirror:
  `temp/sessions/agentify_transport_operator/independent_research_explorer/onlgr_b2_chatgpt_pro_math_closure_20260814_01/response.md`

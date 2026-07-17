# F0/F1 Dynamic-Roster Testbed Review Disposition

Date: 2026-07-17

Round: `20260717_f0_f1_dynamic_testbed_design`

Final reviewer: GPT-5.6 Pro, existing `HMASD Algorithm Consultation` conversation

Raw response: `41_PRO_CONVERGENT_RAW.md`

## Decision

Final verdict:

```text
MODIFY_TESTBED_CONTRACT
```

Authorization boundary:

| Action | Disposition |
| --- | --- |
| Migrate the corrected design into `docs/research/designs/` | `AUTHORIZED_AFTER_CORRECTION` |
| Implement the environment | `NOT_AUTHORIZED` |
| Integrate event-mode training | `NOT_AUTHORIZED` |
| Launch any experiment | `NOT_AUTHORIZED` |
| Promote F1 or integrate it into the UAV task | `NOT_AUTHORIZED` |

The archived raw response was captured before this interpretation. The final
review used both blind divergent responses and the controller synthesis; it
did not inspect a scientific result for this testbed because none exists.

## Accepted Corrections

The original design is retained only after the following changes:

1. Replace task-typed `SHORT_A/SHORT_B` actions with one anonymous generic
   `SHORT` action. The required reactive workload is `R_w = N_w - 1`, so the
   variable-team coordination pressure remains without adding an artificial
   semantic axis.
2. Use a primitive-action autoregressive recurrent policy as the direct-access
   instrument. It acts on the whole active set at every primitive step and has
   no skill, `KEEP/SET`, event opportunity, or high-level controller.
3. Serialize evidence as one causal chain:

   ```text
   no-learning carrier
   -> direct primitive-AR access
   -> paired F0/F1
   -> conditional timing diagnosis
   ```

4. Freeze each learned arm at 320,000 transitions with 16 environments,
   horizon/rollout 80, 250 updates and PPO4. Do not expand to three seeds or a
   larger PPO budget before ordinary access is established.
5. Treat F0 as the strongest ordinary-MARL objection. F0 and F1 have the same
   event runtime, network graph, optimization, ledgers and exposure; only the
   summary selector differs:

   ```text
   F0 -> initial_summary
   F1 -> working_summary
   ```

6. Require natural common-support evidence, directionally correct roster
   composition and positive external-utility transport together before H1 can
   be supported. Wiring gradients, forced trajectories or synthetic rows are
   insufficient.
7. Keep timing as a conditional diagnostic only. Even a positive timing split
   does not authorize a learned hazard or point process.

The corrected frozen contract is:

`docs/research/designs/F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md`.

## Causal Portfolio After Review

| Hypothesis | Status after design review | Separating evidence |
| --- | --- | --- |
| H0: F0 sufficiency | Undefeated strongest null | F0 task access and no F1 external-utility gain |
| H1: applied-prefix value | Leading conditional hypothesis, untested | Natural prefix TV, correct composition shift and F1-minus-F0 utility gain |
| H2: skill execution failure | Active upstream alternative | Direct succeeds while both skill arms lack executable persistent/reactive skills |
| H3: exogenous timing limitation | Deferred conditional diagnostic | Read only after access, skills and prefix direction pass |

No hypothesis has been scientifically promoted by this design review.

## Replacement Ledger

Retain:

- schema-3 event runtime and typed membership transactions;
- survivor/rejoin continuity and active-only sum/count representation;
- uniform external event order and exact F0/F1 selector;
- per-owner duration-correct credit;
- `pi_l(a_i | o_i, z_i)` and task-blind intrinsic boundary;
- one terminal external task objective.

Delete or keep retired:

- the exact R51--R54 tasks, comparators and threshold contracts;
- the numbered R55 route and its unexecuted substrate;
- `SHORT_A/SHORT_B`;
- fixed-`N` specialists as a universal prerequisite;
- identity, hard roles, graph, attention, slots or critical residuals;
- team latent, bridge or new discriminator;
- learned ordering or learned event time;
- task-specific intrinsic reward or reward shaping.

Only after a separate future authorization may the project add a generic-short
environment/adapter, a small direct primitive-AR instrument, real event-mode
training integration and one unified analyzer. These are testbed evidence
infrastructure, not additions to the F1 algorithm graph.

## Stop Boundary

Every registered terminal branch stops the current chain. Carrier or direct
failure retires the exact testbed; H2 records a skill bottleneck; H0 stops at
F0; H3 permits one cross-round architectural interpretation only; H1 supports
the mechanism on this testbed but still requires a separate integration
decision. A mixed valid result does not generate another toy or successor
module automatically.

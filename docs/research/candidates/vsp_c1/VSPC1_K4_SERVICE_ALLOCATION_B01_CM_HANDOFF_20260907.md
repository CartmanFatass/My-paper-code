# VSPC1 SERVICE-ALLOCATION-B01 — prepared CM implementation handoff, 2026-09-07

Prepared from the complete Pro decision and conforming
[intake §4](VSPC1_K4_SERVICE_ALLOCATION_CONVERGENCE_INTAKE_20260907.md).
**Not dispatched:** Portfolio `80a62f394` and Root's current task end at this handoff.
Root returns this document with the intake/card to Portfolio for its next bounded command.
Prior CM context is `/root/dm_amx_vspc1_next/cm_reactive_queues_b01`; reuse it if available
when the next command is assigned. The current native inventory lists no live CM in this
DM subtree. Recipient assignment/activation remains with the next Portfolio/Root command.

1. **Deliverable and goal.** Implement the single fixed three-queue B/EXPLORE in
   [card §§2–5](VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md), with actual-segment
   FACTOR/GENERIC learning and the same-information LQ-EXCLUDE reference. Deliver committed,
   pushed source, focused acceptance evidence and one technical acceptance record at
   `docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_B01_TECHNICAL_ACCEPTANCE_20260907.md`.
   This proposed engineering assignment ends at implementation acceptance; no formal B run.

2. **Owned paths and entry points.** Own new
   `experiments/candidates/vsp_c1/k4_service_allocation_b01/`,
   `scripts/run_vspc1_k4_service_allocation_b01.py`, matching
   `tests/experiments/candidates/vsp_c1/k4_service_allocation_b01/`, and the named technical
   record. Read the existing reactive-B01 `experiment.py` entry points `tick`, `features`,
   `QNetwork`, `collect`, `targets`, `update`, `counts`, `configuration`, `run`, plus
   `reporting.py` and its thin runner as a read-only starting point; the prior accepted
   scientific source is `47674883572bbe078ede037cbb8f99b8cd54c159`. Use a separate worktree
   and branch. Other agents are editing this repository; preserve their changes and do
   not revert or modify the prior reactive/public-plan code, cards or results.

3. **Preserved semantics and explicit changes.** Card §§2–6 bind host, information,
   timing, normalization, learner/target loss, initialization, namespace mapping, budget,
   sampling, comparators and reading branches. Changes are three queues/actions, capacity4
   with Bernoulli0.5 arrivals, initial(2,2,2), cyclic old-h partner ties, ten/twelve inputs,
   seed402, five checkpoints and one held-action LQ-EXCLUDE evaluation. Each controller
   evolves its own endogenous state/partner actions on shared external tapes. The rule
   is neither training data nor an action mask and stays inside GENERIC's complete call.
   Reuse actual segment updates and equal episode/period weighting; no extra arm, tuning,
   policy search or scope §4 machinery. Source pointers from literature are only
   [proposal §5](VSPC1_K4_SERVICE_ALLOCATION_QUESTION_20260907.md), not a request to retrieve
   the history again or add an adapter/library.

4. **Acceptance.** Protect the concrete changed behavior and primary output listed in
   card §7 with one focused synthetic-fixture suite and independent review of the changed
   scientific/numerical/RNG path. Check simultaneous partner timing/ties, service and
   conservation, held rule legality and independent endogenous trajectories, actual
   terminal targets, equal weighting, three-action scoring, declared RNG assignment and
   paired endpoint/conditional-SE/AUC/branch publication. Reuse unchanged checks; do not
   rerun all historical experiments or a complete runner smoke. Read/write the new primary
   output on suitable synthetic data and record actual fixture exposure separately.
   Compare source configuration/exposure with
   [selected machine counts](VSPC1_K4_SERVICE_ALLOCATION_B01_COUNTS_20260907.json).
   Controlling references: evidence-spec §§4,5.2,11.4,11.7–11.9 and engineering-scope §§3–5.
   Report observed acceptance, changed paths/commit, check evidence and any concrete
   remaining gap; do not treat tests as a new-host performance result.

5. **Budget and stop.** Scope §4 needs none; normal <=2,000 non-test research lines,
   <=600 runner lines and <=5 minutes of focused directory tests. No performance probe,
   formal seed402 invocation, model/host sweep or extra learner/evaluator call is assigned
   here. Short checks stay local; long portable checks use remote_first after exact source
   is committed/pushed, as applicable. Stop at the pushed implementation/technical return
   or a concrete unresolved requirement, retaining completed work; ordinary in-scope
   repairs remain with the same executor. The later selected science is two complete
   calls capped at2,700s each, FACTOR then GENERIC with rule/pair publication; those are
   not dispatched or spent by this implementation handoff. A later execution command
   binds actual source/argv/run roots, fresh resource receipts and accepted-handle handoff
   to Root under `EXPERIMENT_MONITOR.md` and `ROOT_OPERATIONS.md`.

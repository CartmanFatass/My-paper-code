# Cross-lifecycle handoff G2 trainable implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution and workflow hash handoffs are disabled.

```text
active_implementation=CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_TRAINABLE
implementation_status=AUTHORIZED
design=docs/research/designs/CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2.md
backend=cpu
torch_threads=1
formal_run_status=not_launchable_until_implementation_acceptance
G0_G1_mutation=forbidden
backward_compatibility=not_required
```

## Goal

Implement the frozen TEAM_REC/DUM/EHC comparison and its fail-closed formal
analyzer. Keep the passed information gate as source-control logic, then remove
superseded G1 executable code/tests after G2 acceptance because Git history and
formal artifacts preserve G1.

The primary comparator is persistent TEAM_REC; DUM is the link-null control.

## Task 1 — Trainable handoff environment

**Status:** complete and PM accepted.

Extend `ha_ctse_process/cross_lifecycle_handoff_g2.py` with counter-based
train/IID/held-out ledgers, exact sign mates, the six-field actor and ten-field
critic views, nuisance independence, membership transitions, reward/utility,
snapshot/restore and constructive controls.

**Focused proof:** distribution support and independence; no actor leakage;
creator terminal deletion; same/cross-slot successor reset; team/held ownership;
reward identity; snapshot equality; information-gate preservation.

## Task 2 — Matched learned arms and PPO

**Status:** complete and PM accepted.

Create `ha_ctse_process/ehc_handoff_g2.py` with the shared module inventory,
per-member and team recurrence, CREATE mark, link-specific logits, rollout,
stored-draw replay, GAE/PPO, gradient fences, counters and CPU checkpoint.

**Focused proof:** matched initialization/parameters/exposure; exact TEAM_REC,
DUM and EHC logit paths; member/team/held reset rules; no critic leakage; replay
equality and corruption rejection; finite joint ratios/gradients; same-source
CPU resume and foreign checkpoint rejection.

## Task 3 — Runner, audit and first-match analyzer

**Status:** complete and PM accepted.

Replace `scripts/run_cross_lifecycle_handoff_g2.py` with `train`, `evaluate`,
`analyze` and `exercise`. Persist only final formal checkpoints, 60 evaluation
cells, compact source controls and held-out EHC snapshot interventions. Rederive
all predicates and call one pure first-match selector.

**Focused proof:** exact inventory, paired hierarchical bootstrap, selector
precedence, evidence/reference/schema tamper negatives, formal rejection of an
exercise artifact and no import of a G0/G1 selector or schema.

## Task 4 — Active-line replacement

**Status:** complete.

Delete the closed G1 executable line:

- `ha_ctse_process/temporal_duty_g1.py`;
- `ha_ctse_process/ehc_g1.py`;
- `scripts/run_access_positive_ehc_g1.py`;
- `tests/ha_ctse_process_temporal_duty_g1_test.py`;
- `tests/ha_ctse_process_ehc_g1_test.py`;
- `tests/run_access_positive_ehc_g1_test.py`.

Retain G1 design, evidence note, formal artifacts and Git history. No reader,
migration, alias or compatibility test remains.

## Task 5 — Bounded prelaunch acceptance

**Status:** complete and PM accepted.

Run only the focused G2 environment/model/runner tests with the registered CPU
interpreter and one thread, then one fresh reduced `formal=false exercise` that
covers collection, replay, one PPO update, checkpoint reload, all three arms,
evaluation, intervention and analyzer rejection.

Project Manager inspects actor/critic separation, identity leakage, RNG draw
ownership, recurrent contamination, held-state persistence, rollout packing,
scalar transfer, synchronization and serial evaluation. Repair the first failed
invariant; do not weaken the frozen contract or add a broad compatibility suite.

After acceptance, Project Manager commits and pushes the exact active path set.
Only that integrated commit may be assigned to the silent experiment operator
for formal iteration 3. The bounded package consumes zero iterations; three conclusion-bearing iterations remain.

Accepted evidence:

- focused G2 suite: 15 passed;
- artifact:
  `logs/nonformal_cross_lifecycle_handoff_g2_trainable_20260723_pm2`;
- three final checkpoints, 12 evaluation cells, eight post-departure snapshot
  audits, exact replay and exposure counters;
- result `formal=false`, `SOURCE_NON_IDENTIFIABLE_HANDOFF_G2`, no operational
  errors; formal validator rejection confirmed;
- transient OneDrive progress-replace retry and evidence-tamper failure covered;
- no `latest.pt`, temporary artifact, G1 compatibility line or formal result.

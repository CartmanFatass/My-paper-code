# HA-CTSE Active Implementation Plan

Updated: 2026-07-23
Status: `BLOCKED_CDC_CAUSAL_QUOTA_BRANCH_AND_MONITOR_QUOTA`
Work ID: `event-held-formal-or-dum-ehc-preregistration-v1-20260723`
Scientific source:
`docs/external-review/rounds/20260723_typed_cpu_smoke_complete_next_action/21_PRO_OPEN_RAW.md`
Executable source boundary: branch `Claude`,
`1cc6552a00c06bc7389235a4474ca0005c4ca9b6`
Execution authority: `NOT_AUTHORIZED`

## Accepted scientific direction

External GPT-5.6 Pro selected exactly one preregistered formal
`EVENT_HELD_COMMITMENT_LINK_G0` comparison with OR, DUM and EHC. The selection
does not authorize formal training, evaluation, analysis, Monitor assignment or
use of the formal token.

The scientific object remains unchanged:

- OR is the complete ordinary-recurrent comparator and access diagnostic;
- DUM owns the complete event/commitment machinery with treatment bit `m=0`;
- EHC differs from DUM only by `m=1`;
- the sole treatment is the existing held-mark contribution to primitive
  logits;
- primary `G=E[U_EHC-U_DUM]`; secondary `V=E[U_EHC-U_OR]`;
- conclusion-bearing evidence comes from the held-out stochastic cell.

No code, task, observation, reward, probability, credit, optimizer, model,
seed, budget, threshold, audit quota, estimand, backend, recurrent state, RNG,
replay or checkpoint semantic may change.

## Canonical executable contract

`ha_ctse_process/noncalendar_commitment_testbed.py::select_result_branch` and
the typed-v2 production validators are authoritative. Documentation must state,
without semantic change:

- raw KEEP/RENEW rates are support diagnostics, not behavior gates;
- physical-lifetime CV and physical-time bins are descriptive only;
- policy lifetime uses complete-spell opportunity counts `K==1`, `K==2`,
  `K>=3`;
- the intervention metric is primitive-action-distribution TV, not logit
  magnitude;
- `C_total` is separately required for naturally selected KEEP and RENEW;
- `C_timing` and `C_mark` are preregistered diagnostics;
- typed causal-audit v2 and structured `FORK_EVIDENCE_UNAVAILABLE` are
  mandatory.

The exact complete-evidence gates remain:

| Layer | Frozen requirement |
|---|---|
| Operational | Every probability, replay, lifecycle, RNG, checkpoint, schema, binding and typed validator passes |
| Exposure | At least 1,000 non-CREATE opportunities and 250 multi-opportunity lifecycles |
| Natural support | At least 128 eligible KEEP and 128 eligible RENEW rows |
| C audit support | Exactly 32 KEEP and 32 RENEW selected rows per replicate |
| Access | Maximum arm utility reaches `0.78` |
| Primary gain | `LCB95(G) > 0.10` |
| Policy lifetime | At least two `K`-bin proportions have `LCB95 > 0.10` |
| Primitive intervention | `LCB95(TV) > 0.10` |
| Event consequence | Both natural-action `C_total` lower bounds exceed zero |
| Point floors | Both natural-action `C_total` means are at least `0.02` |

Point floors remain absent from the confident-failure dual. A timing-specific
claim additionally requires positive two-sided `C_timing` evidence in both
natural-action strata. The executable result branch itself does not change.

## Documentation-only reconciliation

Update `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md` to replace its
superseded usage/CV/logit battery, old schema names and old result wording with
the canonical executable contract above. Preserve the architecture, probability,
credit, clocks, lifecycle, comparator, budget, RNG, checkpoint and estimand
sections unchanged.

Add one exact preregistration row to `docs/project/ExpRecord.md`. Before later
authorization it must say `planned — NOT_AUTHORIZED`. It names:

- source commit and registered CPU/thread environment;
- exact fresh output root;
- complete training, evaluation, causal-audit and analysis budgets;
- formal terminal branches and iteration accounting;
- numerical wall-clock, disk and retention caps;
- `BLOCKED_RESOURCE` behavior and the one-repair operational limit;
- the separate authorization and formal-token boundary.

If either documentation update would require a code or scientific semantic
change, stop and return to CDC.

## Frozen computational boundary

Training:

- five paired replicates `r=0..4`;
- OR, DUM and EHC;
- 250 updates per arm/replicate;
- 16 environments, horizon 80;
- 320,000 transitions and 4,000 episodes per arm/replicate;
- 1,000 base optimizer steps per arm/replicate;
- 1,000 event optimizer steps for DUM/EHC per replicate and zero for OR;
- only `update_250.pt` is evaluated.

Evaluation and analysis:

- four cells per arm/replicate: IID deterministic, IID stochastic, held-out
  deterministic and held-out stochastic;
- 256 episodes per cell; all 60 cells must validate;
- exactly 32 natural KEEP and 32 natural RENEW selected audit rows per
  replicate, 320 selected rows total and 960 continuation rows;
- 10,000 paired hierarchical bootstrap repetitions, strict percentile 95%
  intervals and seed `108058`.

Aggregate boundary: 4,800,000 training transitions, 60,000 training episodes,
15 final checkpoints, 15,360 evaluation episodes, 1,228,800 evaluation
transitions, 320 selected audit rows and 10,000 bootstrap repetitions.

## Measured resource boundary

Accepted local evidence:

- the unchanged non-formal exercise ran from `2026-07-23T14:52:39.279Z` through
  `2026-07-23T15:04:50.035Z`;
- its 25 files occupy `691,821,312` bytes (`0.6443 GiB`);
- one three-arm update shard occupies `8,366,447` bytes;
- the typed held-out EHC audit adds `357,404,103` bytes beyond the matched
  ordinary held-out-stochastic payload;
- the current volume has `831.7 GiB` available.

Projection from those measured artifacts:

- 1,250 update shards: `9.74 GiB`;
- scaled 60-cell evaluation plus five fixed 64-row typed audits: `3.57 GiB`;
- projected core evidence: `13.31 GiB`.

Frozen caps:

- require at least `64 GiB` free before authorization and before each phase;
- hard output-root cap: `32 GiB`;
- hard elapsed cap for the complete train/evaluate/analyze sequence: `18 h`;
- phase caps: train `10 h`, evaluate `6 h`, analyze `2 h`;
- retain the complete no-clobber run root through accepted external
  disposition and for 30 calendar days afterward, never beyond `32 GiB`;
  tracked terminal summaries, hashes, reconciliation and disposition remain
  permanent.

Any unavailable resource returns `BLOCKED_RESOURCE`. It never permits fewer
replicates, arms, updates, episodes, audit rows, optimizer exposures or
bootstrap repetitions.

## Source, output and execution boundaries

- Clean source worktree:
  `C:\Projects\My-paper-code-formal-1cc6552`.
- Fresh output root:
  `C:\Projects\My-paper-code\logs\20260723_event_held_commitment_link_g0_formal_cpu_registered`.
- Registered runtime: CPU, one Torch intra-op thread, Python 3.10.20 and Torch
  `2.7.0+cpu`.
- The output root must not exist before authorization and must never reuse an
  aborted run or checkpoint.
- Formal train, evaluate and analyze are three phases of one registered run.
  The exact token is supplied only after separate Controller authorization.

## Monitor and authorization boundary

The archived registered Experiment Monitor must be rebuilt as the exact native
Codex Spark-medium `experiment_monitor`, then atomically registered before any
assignment. No local task agent, default agent, alternate model or title-based
route may substitute.

The Controller attempted the exact rebuild on 2026-07-23. Codex created task
`019f8ffe-197e-7fb1-8cc0-0b55c830ff5e` with
`model=gpt-5.3-codex-spark`, `reasoning_effort=medium`, read-only sandbox and
zero consumed tokens, then failed its first turn with:

```text
You've hit your usage limit for GPT-5.3-Codex-Spark.
Switch to another model now, or try again at Jul 28th, 2026 10:31 AM.
```

The Controller archived that unusable task and did not register it. The
existing archived Monitor registry entry remains unchanged. Because model or
role substitution is prohibited, this is `BLOCKED_RESOURCE_MONITOR_QUOTA`.
Formal authorization, token use, launch and Monitor assignment remain
forbidden until a fresh exact Spark-medium rebuild succeeds after quota
availability.

After documentation reconciliation, resource checks, clean-source creation,
fresh-root verification and Monitor registration all pass, update this plan and
`CURRENT_WORK.md` atomically to name:

- the exact run ID and output root;
- the measured caps above;
- the exact Monitor registration;
- the single formal token authorization;
- the launch command and first phase.

Only that later Controller transition may change execution authority to
`AUTHORIZED_FORMAL_EXECUTION`.

## Terminal semantics

Stop on the first valid registered result:

- `FORK_EVIDENCE_UNAVAILABLE`;
- `BENCHMARK_NON_IDENTIFIABLE`;
- `NO_ACCESS_THIS_BENCHMARK`;
- `UNDERPOWERED_ACCESS`;
- `COMMITMENT_SUPPORTED`;
- `REPRESENTATION_ONLY`;
- `ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED`;
- `MIXED_UNDERPOWERED`.

Unavailable typed evidence exposes no zero-filled C estimate and bypasses the
complete selector. A valid negative, no-access, underpowered, mixed or
fork-unavailable result receives no extra seed, top-up, threshold change or
rerun. The first `INVALID_OPERATIONAL` permits at most one bounded repair under
the identical contract; a second is a blocker and returns to CDC.

A valid conclusion-bearing terminal result consumes the third of five
authorized iterations. Preregistration, resource assessment, Monitor rebuild
and `INVALID_OPERATIONAL` do not.

## Verification before authorization

1. Diff the design record's scientific contract against the executable
   selector, registered constants and typed schemas; require documentation-only
   equality.
2. Verify the new experiment row contains every frozen count, cap, branch,
   prohibition and authority state.
3. Create and verify the detached clean worktree at the exact source commit.
4. Confirm the fresh output root is absent and available space is at least
   `64 GiB`.
5. Resolve the registered Monitor live route and require Spark-medium before
   assignment.
6. Run the source's non-consuming contract path and focused existing contract
   checks; do not run another smoke.
7. Perform one independent Reviewer+Verifier gate over the stable
   preregistration package. Repair only factual or contract mismatches; no
   scientific redesign.

## Collective preregistration review

The single `FINAL_IMPLEMENTATION_ROUND_REVIEW` completed. The Verifier returned
`PASS`: exact source, counts, schemas, gates, resource arithmetic, absent output
root, no-token rejection and the archived zero-token Monitor attempt all
reproduced.

The Reviewer returned `FAIL` with one HIGH source-contract defect. At source
commit `1cc6552a00c06bc7389235a4474ca0005c4ca9b6`:

- `select_result_branch` classifies any per-replicate causal KEEP or RENEW count
  below 32 as `BENCHMARK_NON_IDENTIFIABLE`;
- `_collect_causal_audit_evidence` instead raises
  `INVALID_OPERATIONAL causal audit selected-row quota shortfall`;
- `_causal_audit_valid` rejects any shortfall artifact; and
- `formal_evaluate` publishes the raised exception as `INVALID_OPERATIONAL`.

The direct formal path therefore cannot produce the preregistered
`BENCHMARK_NON_IDENTIFIABLE` result for a 32/32 audit shortfall. The existing
unit test covers only the selector and misses this end-to-end contradiction.

This plan's documentation-only rule forbids a local semantic repair. Source
commit `1cc6552...` is not launch-ready and must not be authorized. The next
action is one focused external GPT-5.6 Pro continuation deciding the shortfall's
scientific terminal meaning and, if it remains non-identifiability, the exact
evidence-preserving implementation boundary. No code or compute is authorized.

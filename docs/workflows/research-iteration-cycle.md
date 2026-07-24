# Workflow: research iteration cycle

> Status: **near-done.** Every question raised in grilling is resolved. What
> remains is not a question but a build list — see "What must be built".

## The loop

One conclusion-bearing research iteration, as stated by the user 2026-07-24:

```text
外审 -> 本地主对话指定实现计划 -> 分任务给 implementer 实现
     -> verifier/reviewer 统一审阅 -> exp 实验 -> 外审
```

19 iterations have run. 8 remain under the current grant.

## Trigger

Event, never schedule.

- The experiment operator's terminal payload closes an iteration and fires the
  external review round.
- The archived Pro raw fires the next iteration's planning.

External review appears at both ends of the written loop because it is **one
boundary event**, not two: the same round consumes the finished experiment and
sets the next direction.

## Orchestrator

From the project's formal start the main conversation runs on **Fable**
(`claude-fable-5`) and is the orchestrator, replacing the current opus main
conversation. `AGENTS.md` records subagent tiers but names no orchestrator
model; that must be added.

## Authority split

```text
scientific_decision_authority=external_pro
code_design_authority=fable_orchestrator
```

**External Pro owns the science** — which mechanism is right, which route is
excluded, whether a result closes, what the next scientific direction is.

**Fable owns the code** — module shape, interfaces, task decomposition, and what
each `hmasd-implementer` brief contains. Fable never chooses the scientific
route.

### Protected semantics — the overlap zone

Reward, probability factorization, gradients and detach, recurrent state, masks,
clocks, lifecycle ownership, RNG, replay, credit and checkpoint meaning are both
algorithm definition and code. The split runs through them:

- **Pro decides whether one changes** — "should credit assignment move to a
  delayed residual" is a scientific call.
- **Fable decides how** — signatures, files, tensor layout, task boundaries.

`hmasd-reviewer` keeps its job unchanged: it audits whether anything **not**
authorized to change was changed anyway.

## Stages

| # | Stage | Owner | Produces |
|---|---|---|---|
| 1 | External scientific review | External Pro, transported by `hmasd-review-exchanger` | exact raw under `docs/external-review/rounds/<round-id>/21_PRO_OPEN_RAW.md` |
| 2 | Design freeze + code plan | Fable | two artifacts, below |
| 3 | Build | `hmasd-implementer` × N, disjoint path sets | working-tree changes, no commits |
| 4 | Unified review | `hmasd-verifier` **then** `hmasd-reviewer` | one verdict |
| 5 | Experiment | `hmasd-experiment-operator` | `logs/<run-id>/` + one terminal payload |
| 6 | Record and advance | Fable | `ExpRecord.md` row, `ITERATION_<n>.md`, commit |

### Stage 2 artifacts

Two files, one owner each — the file boundary is the authority boundary.

| Artifact | Holds | Owner |
|---|---|---|
| `docs/research/designs/<G>_DESIGN.md` | the frozen scientific decision: mechanism, estimand, exclusions | Pro's decision, recorded |
| `docs/project/IMPLEMENTATION_PLAN.md` | the executable code plan, **referencing** the design | Fable |

`hmasd-implementer` reads the plan and follows the reference into the design
only when it needs the scientific rationale. This cross-authority link is what
the currently red assertion in `tests/hmasd_research_workflow_contract_test.ps1`
guards — the plan must contain `docs/research/designs/`.

### Stage 4 — unified review

Serial, not parallel. `hmasd-verifier` runs the assigned checks and returns real
command output and artifact paths. `hmasd-reviewer` then audits the diff **with
that evidence in hand** and returns the single verdict.

This matches the reviewer's existing charter, which already assumes independent
prior verification: *"Passing tests are not the question. The implementation
arrives green; the orchestrator has already verified that independently."*

`MODIFY` or `REJECT` returns to stage 3 with the reviewer's minimal correction.
The reviewer never edits; the implementer never accepts its own work.

## Checkpoints

External review is **not** a checkpoint. It is an external dependency driven by
a subagent. A checkpoint is where *the user* decides.

Where the loop pauses depends on the execution mode, which the user sets and
`CURRENT_WORK.md` records.

### Authorized mode

The user grants a fixed number of conclusion-bearing iterations. Inside the
grant the loop runs unattended; asking for an approval the grant already covers
is a defect. The user is asked at exactly two points, neither per-iteration:

| Checkpoint | Fires when | Decision |
|---|---|---|
| Grant renewal | `iterations_remaining` reaches 0 | continue, redirect, or stop |
| Protected-scope expansion | a change needs authority the grant does not carry | grant it or refuse |

### Unauthorized mode

The default when no grant is active. Two additional checkpoints, both
per-iteration:

| Checkpoint | Fires after | Blocks |
|---|---|---|
| Plan review | stage 2 — review reconciled, plan and task split drafted | any implementation |
| Result review | stage 5 — experiment run and artifacts validated | advancing to the next iteration |

The mode changes only where the loop pauses, never what it does.

### Push right

In authorized mode this is satisfied by construction: `formal_compute_authority`
is `user_only`, but the grant pre-authorizes a fixed run, so the user is asked
once per grant rather than once per run. In unauthorized mode the two pauses are
deliberate and are not to be optimized away.

### Brief

`docs/report/ITERATION_<n>.md` is **not** a brief — it is a per-iteration status
readout carrying no decision, exactly as `AGENTS.md` says: *"not another review,
approval or scientific evidence source."* It stays, in Chinese, every iteration.

The actual checkpoint brief does not exist yet. It must be short enough to read
in one sitting after ten iterations of work, and it must be decision-ready:

```text
docs/report/GRANT_<id>_BRIEF.md
- what the grant set out to answer
- what was decided, one line per conclusion-bearing iteration, with links down
- what is still open, and the cheapest next iteration that would close it
- the recommendation, stated plainly
- the decision asked for, and what each option costs
```

Never the raw output. Every claim links down to its `ExpRecord.md` row, its
evidence note, or its iteration report.

## Boundary crossing is not a stage

At any point in the cycle the orchestrator may reach a decision that is
scientific and that blocks it. That is not a failure of the stage it happens in
and it does not restart the loop. It opens a review round and converges with Pro
until both agree, then resumes where it stopped.

Convergence turns live inside the accepted fence and are archived in full to
`22_PRO_CONVERGENCE.md`. Guessing to keep moving is the failure mode this
replaces.

## Git

Integration is Fable-direct at stage 6, after the reviewer verdict and after the
run is recorded. No child commits. Fable stages only accepted paths, checks the
staged path set and `git diff --cached --check`, commits, and pushes.

## The seam between iterations

The cycle does not stop here. Stage 6 rolls into stage 1 of the next iteration
across a fixed compaction seam, and the order is not optional:

```text
write docs/project/RESTART_HANDOFF.md -> compact -> resume -> next iteration
```

This is a context boundary, not a control boundary. It is not a checkpoint,
asks nothing, and waits for no one — an unauthorized-mode loop crosses it on
its own and pauses only at that mode's two checkpoints.

The handoff records the active boundary, execution mode, what is committed and
pushed, the one open deliverable, and the exact next action. Written anywhere
but this seam it is a snapshot of an unfinished thought, not a resume point.

## How stage 1 actually works

Pro reads the repository itself. The submission carries **pointers, not a
payload**:

1. The question names the GitHub locations of the relevant question and result
   files, plus a reference code list Pro may consult.
2. Pro uses the web GitHub connector to read those directly from the remote at
   `stage_commit`.
3. `hmasd-review-exchanger` watches the thinking process until generation
   completes and a stable answer exists.
4. It copies the answer down verbatim and archives it by round to
   `21_PRO_OPEN_RAW.md`.
5. Fable picks up from the archived raw.

Building and uploading an evidence archive is the **fallback**, not the primary
path — it exists only for when Pro reports it could not reach a listed path.
That is why `hmasd-review-exchanger` holds `file_upload`.

### Conversation binding

Each branch has its **own dedicated Pro conversation**. `untied-k` therefore
needs a fresh registration; the retired `6a5a7735-…` belonged to `aggressive`
and must never be reused. The freshness fence carries the branch under review,
so `branch=` is a parameter, never a constant.

## Consequence to accept knowingly

Pro is still a browser conversation driven by a subagent, so every scientific
call — including "is this result valid" — sits behind one generation wait and
whatever the connector can reach at `stage_commit`. Unpushed work is invisible
to it. That makes the push in stage 2 load-bearing, not bookkeeping.

## What must be built

Not questions — work. An implementer can start from here.

1. **`AGENTS.md` authority map** — add `orchestrator_model=fable`,
   `scientific_decision_authority=external_pro`,
   `code_design_authority=fable_orchestrator`. Change
   `project_manager_scientific_reconciliation_authority=exclusive` and
   `external_pro_scientific_authority=question_scoped`, and rewrite the
   paragraph beginning "External GPT-5.6 Pro owns only the scientific answer".
2. **`.agents/roles/EXTERNAL_PRO.md`** — remove "choose successor work" and the
   second-acceptance-owner prohibition from **Must not**; state the new
   scientific decision ownership and the protected-semantics whether/how split.
3. **`.agents/roles/PROJECT_MANAGER.md`** — move research convergence and
   scientific reconciliation out; keep code design, acceptance of code, Git,
   transport, orchestration.
4. **`docs/project/IMPLEMENTATION_PLAN.md`** — restore the
   `docs/research/designs/` reference, closing the red contract assertion
   honestly rather than by deleting the check.
5. **`docs/report/GRANT_<id>_BRIEF.md`** — new artifact, template above.
6. **Contract tests** — extend to assert the authority split, the orchestrator
   binding, and that the grant brief exists when `iterations_remaining` is 0.

Items 1–3 change the constitution and need the user's explicit go-ahead as a
separate act; a workflow spec does not authorize them.

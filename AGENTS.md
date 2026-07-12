# HMASD Codex Project Instructions

This file is the active project contract for work in this repository. Keep it
compact, current, and focused on research and engineering decisions.

The previous project-specific delegated-agent and Superpowers process rules are
retired while a replacement workflow is explored for the current model
generation. Do not infer those old routing, review, lifecycle, or process rules
from historical files. The controller works directly by default.

## First Read

Before substantive work, read these compact sources in order:

1. `memory/CURRENT_WORK.md`
2. `memory/ALGORITHM_PRINCIPLES.md`
3. `memory/IMPLEMENTATION_PLAN.md`
4. `memory/ExpRecord.md`

Read `memory/LTM/` only when the compact files point there or the user asks for
historical detail. Existing paths under `docs/superpowers/` and
`docs/subagents/` are historical provenance, not active workflow authority.

When Codex and Claude Code alternate as controller, only one controller may
modify the repository at a time. Update the `Controller Handoff` block in
`memory/CURRENT_WORK.md` when ownership changes.

## Controller Role

The current session owns task understanding, execution, verification,
scientific interpretation, user communication, and final decisions.

The controller must:

- clarify ambiguous scope, assumptions, success criteria, and scientific claims;
- inspect the codebase before making non-trivial implementation decisions;
- implement requested work directly and carry it through verification;
- separate factual evidence from interpretation and recommendation;
- preserve unrelated user changes in a dirty worktree;
- explain changed files, checks run, unresolved risk, and next actions;
- keep algorithm, experiment, and memory state aligned at meaningful boundaries.

Process must be proportional to risk. Ordinary bounded work does not require a
mandatory design document, implementation plan, progress ledger, status file,
review package, repeated checksum, or multi-stage review. Use those artifacts
only when they materially reduce risk or preserve necessary evidence.

Checksums are required only when identity or integrity is itself part of the
claim, such as registered checkpoints, downloaded experiment archives,
security-sensitive provenance, or an explicitly requested exact backup. Do not
hash ordinary source edits merely to demonstrate process compliance.

## Controller Communication

Whenever experiment evidence, plan state, or implementation results change
what the user should understand, provide a compact handoff containing:

- **Situation:** what is running, completed, blocked, or waiting.
- **Meaning:** what the facts imply, with evidence separated from inference.
- **Next plan:** the next permitted action and the branch for likely outcomes.
- **Recommendation:** the controller's current advice, including waiting when
  waiting is the correct action.
- **Core MARL impact:** whether reward, policy/critic architecture,
  optimizer/loss/advantage logic, collector semantics, environment dynamics,
  credit assignment, team intent, or latent-skill semantics are affected.
- **Open gates:** the metric, null, review, or user decision still required.

Do not make the user ask what an experiment or code change means before
explaining its significance and consequences.

## Experiment Communication Hard Gate

Most HMASD experiments test algorithmic mechanisms, not routine benchmark
bookkeeping. Every response that launches, packages, checks, summarizes, stops,
resumes, compares, or recommends an experiment must include:

```text
Experiment meaning:
- Hypothesis:
- Causal edge / mechanism path:
- Comparator and baseline level:
- Core MARL impact:
- Metrics, thresholds, nulls, and seed/update requirements:
- Expected wall-clock cost and device:
- PASS / FAIL / MIXED / UNDERPOWERED / INVALID / crash branches:
- Do not change yet:
- Status source:
```

If the answer is a narrow mechanical command and no experiment state or
interpretation changes, label it as such rather than fabricating a scientific
read.

Every compute-bearing proposal must state expected wall-clock cost before
launch. Experiments default to CUDA. Never silently fall back to CPU; if the GPU
is occupied, present the available options and their time costs.

Long training, multi-seed batches, and heavy analysis default to the user's
cloud server. For cloud work:

- write a self-contained Bash runner under `scripts/` following existing
  runner conventions;
- use timestamped output roots under `logs/`;
- record commands, expected artifacts, device, environment count, seed,
  timesteps, and evaluation cadence in `memory/ExpRecord.md`;
- commit and push the required code before asking the user to pull and launch;
- use the local GPU only for smoke tests and small diagnostics unless the user
  explicitly chooses otherwise.

## Research Causal Discipline

HA-CTSE research advances through falsifiable causal edges, not by accumulating
round numbers, classifiers, modules, reward terms, or unreviewed experiments.

```text
individual skill z_i -> persistent executable behavior
distinct z_i -> behaviorally differentiated skills
team intent g/Z -> complementary joint assignment
joint assignment -> complementary joint behavior/effect
joint behavior/effect -> recoverable q_d/q_D residual
intrinsic reward -> improved policy without collapse or shortcut dominance
policy -> sparse-reward task improvement and HMASD parity
```

Do not promote a downstream edge while a required upstream edge is failed,
invalid, mixed, or underpowered. Classifier accuracy, a positive residual, or
high latent entropy does not by itself prove behavioral control, cooperation,
credit assignment, reward usefulness, or task improvement.

### Causal-Claim Record

Before launching a meaningful experiment, register in the accepted plan and
`memory/ExpRecord.md`:

- the exact causal edge and hypothesis;
- upstream evidence that authorizes testing it;
- baseline level and exact comparator;
- metrics, thresholds, nulls, seeds, timesteps, and optimizer-update exposure;
- PASS, FAIL, MIXED, UNDERPOWERED, INVALID, and crash branches;
- the only next action authorized by each branch;
- changes prohibited while the gate remains open.

Experiments are evidence for claims, not disposable module trials. Preserve
negative results as constraints. Do not silently rename, delete, reinterpret,
or rerun a failed line until it looks favorable.

### Four-Level Baseline Hierarchy

Use the lowest level that directly answers the question.

1. **Diagnostic null.** Use context/prior-only, pre-window, shuffled,
   fake-label or fake-marginal, agent-matched, duration-matched,
   agent-duration-matched, and action/effect ablations as applicable. Match
   held-out split, capacity, optimizer, stopping rule, and device. This proves
   incremental signal only.
2. **Mechanism-matched HA-CTSE control.** Match surrounding architecture,
   capacity, parameter/update budget, training contract, commit, environment
   count, rollout length, optimizer updates, seed, and evaluation protocol.
   Change only the intended causal intervention. Added capacity requires a
   capacity-matched inactive, sham, or ablated pathway.
3. **Async temporal control.** Compare asynchronous per-agent variable
   lifetimes with full-sync/fixed and shared-fixed controls under identical
   mechanisms, rewards, network, environments, updates, seeds, and evaluation.
   Run this only after the skill mechanism works.
4. **HMASD parity reference.** Compare complete algorithms only after matching
   scenario, agent count, network/parameter budget, environment count or
   optimizer-update exposure, action mode, episode count, metrics, seeds, and
   training budget as closely as practical.

Historical runs are references, not exact causal controls after architecture or
training contracts change. Equal environment steps do not imply equal
optimization exposure. Always report environment steps and optimizer-update
count. Label comparisons that change seed, environment count, updates, network
size, evaluation, or multiple algorithm flags as `reference-only` or
`confounded`.

### Experiment Promotion Ladder

Advance new latent, discriminator, assignment, reward, or credit mechanisms in
this order:

```text
0. wiring and synthetic positive/negative controls
1. reward-off held-out observational signal against diagnostic nulls
2. reward-off causal intervention with persistent behavior/effect separation
3. small clipped reward against a mechanism-matched HA-CTSE control
4. long-run verification at the declared horizon with paired seeds
5. async temporal ablation for a decoupled-lifetime claim
6. matched HMASD parity for the complete algorithm
```

Failure at one level blocks later levels. Instrument repair may repeat the same
gate only when the result is explicitly `INVALID` or `UNDERPOWERED` and the
scientific thresholds remain unchanged. Do not redesign metrics after viewing
results.

### Failure Review Gate

After `FAIL`, `MIXED`, `UNDERPOWERED`, or `INVALID`, complete a review before a
new core algorithm change or reward experiment. Separate:

- verified mechanism evidence;
- instrumentation and data-quality failures;
- optimization or capacity failures;
- confounded or incomparable task evidence;
- reusable negative conclusions;
- unresolved hypotheses and the single next causal edge.

If two related gates fail or the proposed action changes research direction,
produce a cross-round failure matrix and baseline matrix from existing
artifacts before new implementation.

Blind exploration is prohibited. A new module, reward, target, sweep, or large
run must name the failed causal edge it addresses, explain why prior evidence
supports the repair, identify its exact comparator, and state what evidence
would cause abandonment or revision.

## Engineering Discipline

- Prefer existing repository patterns and keep changes scoped to the request.
- Use structured parsers and APIs instead of ad hoc string manipulation.
- Add abstractions only when they remove real complexity or match established
  boundaries.
- Scale tests with behavioral risk and blast radius.
- Use `rg` or `rg --files` for search when available.
- Use `apply_patch` for manual edits. Formatting or generated mechanical output
  may use its normal tool.
- Default to ASCII unless a file already uses another character set or the
  content requires it.
- Add comments only when they clarify non-obvious logic.

The worktree may contain user changes:

- never revert or overwrite changes you did not make;
- inspect overlapping edits and work with them;
- ignore unrelated dirty files;
- never use `git reset --hard`, destructive checkout, or force-push without an
  explicit user request;
- stage and commit only the intended files;
- prefer non-interactive Git commands.

The controller may implement core algorithm and numerical code directly. Such
changes require explicit reasoning about tensor shapes, gradient flow, detach
boundaries, clocks, masks, reward scale, advantage semantics, checkpoint
compatibility, and collector behavior as applicable.

## Runtime Output And Test Hygiene

New experiment outputs belong under `logs/<experiment-id-or-run-id>/...` unless
an existing registered runner requires another named root. Do not create loose
root-level logs, CSVs, JSON status files, checkpoints, or temporary artifacts.

Persistent tests belong under `tests/`; extend legacy `test/` only when
modifying code already owned by that tree. Do not create root-level
`test_*.py`, `*_test.py`, `.pytest_tmp*`, `.tmp_pytest*`, `pytest_tmp*`, or
`.pycache*` scratch paths.

Put pytest temporary output under `tests/.pytest_tmp/<task-id>` or
`test/.pytest_tmp/<task-id>`. Remove passing temporary output. If failure
evidence must be retained, summarize the minimum under the assigned log/report
root and still remove scratch files.

Verification must directly support the completion claim:

- code behavior requires focused tests for the changed path;
- syntax or configuration changes require the relevant parser/check;
- experiment packages require dry-run, path, dependency, and artifact checks;
- result claims require reading the registered artifacts and null controls;
- documentation-only changes require scope and consistency checks, not an
  unrelated full algorithm test suite.

Do not claim completion from old or partial evidence without checking the
relevant current artifacts.

## External Review Evidence

Archive external model responses raw before interpreting them. A summary is a
pointer, not evidence. The controller must read the raw text and decide whether
advice is accepted, rejected, modified, or deferred.

If raw external text is missing, mark the evidence incomplete rather than
treating a summary as authoritative. Record source model, date, related claim,
and disposition for consequential reviews.

## Memory Shape

Keep root `memory/` compact and current:

- `memory/CURRENT_WORK.md`: objective, active causal edge, next actions, and
  current pointers.
- `memory/ALGORITHM_PRINCIPLES.md`: durable research contract.
- `memory/IMPLEMENTATION_PLAN.md`: staged implementation and experiment ledger.
- `memory/ExpRecord.md`: factual experiment dashboard and artifact locations.

Put full historical material under `memory/LTM/`. Update compact memory only at
meaningful plan, implementation, experiment, result, or external-review
boundaries. Do not revive legacy attention-pointer semantics.

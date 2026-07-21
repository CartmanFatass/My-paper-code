# Handoff to Codex

Written 2026-07-22 01:30. The user is transferring this project back to Codex.
This file is written for the incoming controller.

`AGENTS.md` and `.agents/skills/` are your operating contract again. They were
never modified. The user directed that they did not apply to the Claude Code
session, so that session ran a different model: the user holds scientific
authority, Claude Code implements and verifies, GPT-5.6 Pro reviews science
through the GitHub connector. Nothing in your role graph was touched.

## State in one line

Nothing is running. Formal training was attempted twice and aborted both times.
The current blocker is a numerical specification that cannot be executed as
written, and a question about it is pending with GPT-5.6 Pro.

## The blocker

`REPLAY_COMPONENT_TOLERANCE = 1e-6` is applied as a flat absolute bound to nine
replayed quantities. Four of them have unbounded magnitude, so for any fixed
absolute tolerance there exists a magnitude at which one float32 ULP exceeds it.

Training aborted with `mark_component = 1.9073486328125e-06`, exactly `2^-19`,
one ULP for a magnitude in `[16, 32)`. A transformed-mark component log density
reached magnitude 16 because the mark is `z = tanh(u)` with
`u ~ Normal(mu, sigma^2)`, the Jacobian is `2*(log2 - u - softplus(-2u))` which
grows linearly in `|u|`, and `mu` is an unbounded head output that training
drives. `sigma` is clamped to `0.1 + 0.9*sigmoid(s)`; `mu` is not.

**This is pre-existing, not introduced.** Verified against `bcdff53`: the
original `validate_replay` applied the same `1e-6` scalar to every approximate
field including `mark_component`. The original contract would have aborted at
the same place. This benchmark has never been runnable to completion.

**Fixing only `mark_component` buys one more crash.** The unbounded fields are
`mark_component`, `categorical_component`, `primitive_component` and `value`.
`hidden`, `event_new_z` and `primitive_event_z` are tanh-bounded and safe;
`prefix` and `event_input` are bounded by construction. In the failing record
`categorical_component` was `2.384e-07`, one ULP at magnitude 2 to 4; it needs
magnitude 16, a log probability of about `-16`, to breach the bound, which a
sharpening policy reaches routinely.

The question is at
`docs/external-review/gpt5_6_pro/20260722_per_component_tolerance_unexecutable/QUESTION.md`.
It asks whether a flat absolute per-component tolerance is executable at all,
what relative form would be principled if not, whether the likelihood should
accumulate in float64 instead, and whether any of those weakens the guarantee
that a defective component still fails decisively. **No answer has been
received.** The scope point — that the fix must cover the whole unbounded class
rather than one field — was identified after the question was sent and is not in
it.

## Launch attempts

| # | Died at | Cause |
|---|---|---|
| 1 | update 4, replicate 0, ~90 s | `formal_train` gated on a replay record merged across arms. `merge_replay_records` takes field-wise extrema, and OR's all-zero event joint has `excess` exactly `0.0` — the maximum among records whose real excess is negative — so OR won some fields while `rows` came from an event-bearing arm, producing `rows 1214` with `factor_count 0`, a record no arm emits. Fixed at `e80cef0` by validating per arm, as `formal_evaluate` already did. |
| 2 | mid-training, ~14 min | The tolerance blocker above. |

Neither wrote a checkpoint. Both run roots under `logs/` contain only a stdout
log with the traceback.

## The largest standing risk

`formal_train` and `formal_evaluate` are reachable only behind
`FORMAL_AUTHORIZATION` and are imported by no test. **Four defects have now been
found in that region**, each by accident or by running:

- `torch.flatnonzero`, absent from this torch build
- a slice omitting `env_index`, which under 16-environment batching would not
  raise but would produce well-formed garbage
- the cross-arm merge above, which aborted a launch
- the tolerance blocker, found only by running

`formal_evaluate` has still never executed. It runs immediately after training,
so a defect there costs a full training run to discover. Incomplete work toward
bounded end-to-end coverage is preserved on branch `wip/formal-path-coverage`:
it parameterizes the loop bounds so a test can exercise the real path rather
than a copy, touches only the runner, has no tests, and is unverified. Take it
or redo it, but the coverage should exist before the next launch.

## What is committed and sound

Branch `aggressive`, head `8d13727`, clean tree, 38 focused tests passing on the
CUDA backend.

```
ce0d0ec  three-arm OR/DUM/EHC implementation
7ba056e  battery revision A/B/D
473b9da  Replacement C stage 1, candidate mark retention
1dcee48  stage 1 hardening, four guards
bcdff53  sequential counterfactual fork engine
def063c  per-factor replay tolerance classes
f6c6204  execution backend and Replacement C gates
e80cef0  per-arm training replay validation
8d13727  the pending tolerance question
```

The scientific contract is in `docs/project/IMPLEMENTATION_PLAN.md`, final except
for whatever the tolerance question returns. `registered_contract()` serializes
to about 6.2 KB and `load_checkpoint` rejects on any inequality, so a checkpoint
cannot be mixed across backends, thread counts or thresholds.

## Work owed to the science

Recorded in full in `docs/project/PROBLEM_CACHE.md`. The two that change what a
result means:

- **P1** — the fork engine runs deterministically while Replacement C is defined
  on held-out stochastic. Under determinism a primitive action is an argmax and
  the commitment bias cannot move one, which is why `A_KEEP` measured exactly
  zero on every initialized natural-KEEP coordinate. That zero was an artifact
  of the apparatus, not a property of the benchmark. Until stochastic forking
  exists, a completed run answers `G`, access, the `K`-bins and the action-TV
  intervention, but not the `A_KEEP`/`A_RENEW` gates.
- **P1b** — the fork engine cannot run on CPU. Measured: 6 of 6 eligible
  coordinates succeed on CUDA, 6 of 6 fail on CPU, because the branch packs one
  fewer request row at the forked step and CPU linear layers are batch-size
  dependent for these shapes. This is why CUDA is the registered backend despite
  CPU measuring 3.26x faster end to end.

## External review evidence added this session

Under `docs/external-review/gpt5_6_pro/`, each with the question as sent and the
response archived verbatim:

- `20260721_lifetime_battery_contract_question` — the original battery did not
  discriminate learned commitment timing. `CV(T)` was passable by construction:
  `Delta` is sampled from `{4,8,12}` and the policy chooses only `KEEP`/`RENEW`,
  so a crisply learned deterministic rule scores 0.236 and fails while a uniform
  random head scores 0.764 and passes. Led to replacements A, B and D.
- `20260721_replacement_c_scope_followup` — Replacement C is evaluation-only and
  requires no new RNG draw.
- `20260721_replacement_c_cost_and_reachability` — retain C, make 32+32 the sole
  registered form, keep both directional gates.
- `20260721_replay_tolerance_device_portability` — the scalar bound is not
  portable; per-factor classes with a compositional joint rule.
- `20260722_per_component_tolerance_unexecutable` — **awaiting response.**

## Files the Claude Code session added under docs/project/

Not part of your role graph. Keep, fold in or delete as you judge.

- `EFFICIENCY_PRACTICES.md` — throughput measurements with their conditions,
  refuted approaches, current blockers. The measurement most worth keeping: a
  full 80-step collection costs 1.126 s at width 16 against 0.597 s at width 1,
  so sixteen times the environments costs 1.89x the wall clock. The workload is
  bound by sequential physical steps, not by the width of each one.
- `ENGINEERING_ADDITIONS.md` — practical rules derived from those measurements.
- `PROBLEM_CACHE.md` — parked problems, each stating what it blocks.
- `EXTERNAL_REVIEW_PIPELINE.md` — how the GPT-5.6 Pro exchanges were run.
- `AGENT_CONTEXT.md` — standing constraints given to Claude Code subagents.

`.claude/agents/` holds four subagent definitions used by that session. They are
inert for you; `.agents/skills/` is your graph and is untouched.

## Two environment facts that cost time

- Run Python with `C:/Users/wu/.conda/envs/SB3/python.exe` directly. The default
  `python` on PATH is a CPU-only torch build and the focused tests fail closed
  without CUDA. `conda run -n SB3` raises `UnicodeDecodeError` from a non-UTF-8
  `.pth` during `site.py`.
- `.gitignore` ignores `*.md` globally with per-directory negations. Three
  directories were missing theirs and silently refused new files. Add a negation
  rather than `git add -f`.

## Ownership

`docs/project/` returns to you. The Claude Code session held it at the user's
direction and edited `CURRENT_WORK.md`, `IMPLEMENTATION_PLAN.md` and this file.
`ALGORITHM_PRINCIPLES.md` and `ExpRecord.md` were not modified. `ExpRecord.md`
correctly carries no `EVENT_HELD_COMMITMENT_LINK_G0` row, because no formal
experiment has completed.

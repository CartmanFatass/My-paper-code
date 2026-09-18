# Truncation bootstrap in the low-level GAE — fixed globally

Date: 2026-09-17. Branch: `main`. Interpreter:
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

Owner instruction: fix truncation semantics globally in the shared trainer, make the correct
behaviour the default for all future training, fix mid-segment truncation and not only the
rollout-end case, keep the old behaviour only behind an explicit legacy-reproduction flag,
add focused tests, and run one small before/after comparison to document the numerical
impact. Archived directions are **not** re-run.

## The defect

`ha_ctse_process/standalone_train_runner.py:456` collapsed two different facts into one:

```python
done = bool(terminated or truncated)
```

and only that flag reached the low-level GAE, where `standalone_low_update.py:138-142` used
it for both jobs a boundary does:

```python
delta    = rewards[idx] + self.gamma * next_value * next_nonterminal - values[idx]
last_gae = delta + self.gamma * self.low_gae_lambda * next_nonterminal * last_gae
```

`next_nonterminal = 0.0` kills the bootstrap *and* cuts the recursion. For a terminal state
both are right. For a truncation only the cut is right: a time limit is imposed from
outside the environment, so the state still has future value.

**This was never specific to one environment.** All three legacy relay environments set
`is_terminated = False` unconditionally and end only by truncation
(`belief_map.py:1855`, `forced_relay.py:2657`, `routed_core.py:3484`), so the zeroing branch
fired at every episode boundary they have ever produced. The measurement below confirms it
on real rollouts: 8 boundaries, 8 truncations, 0 terminations, in both scenarios tested.

## The fix

The two jobs are now two independent coefficients, which is the whole change in one place:

```python
if bool(terminated[idx]):
    next_value = default_bootstrap
    bootstrap_mask = 0.0
    recursion_mask = 0.0
elif bool(truncated[idx]):
    next_value = self._truncation_bootstrap(truncation_bootstrap, idx, default_bootstrap)
    bootstrap_mask = 1.0
    recursion_mask = 0.0
elif pos + 1 < indices.size:
    next_value = values[int(indices[pos + 1])]
    bootstrap_mask = 1.0
    recursion_mask = 1.0
else:
    next_value = final_bootstrap
    bootstrap_mask = 1.0
    recursion_mask = 1.0
delta    = rewards[idx] + self.gamma * next_value * bootstrap_mask - values[idx]
last_gae = delta + self.gamma * self.low_gae_lambda * recursion_mask * last_gae
```

### Mid-rollout truncation

A truncation anywhere in a pass needs V(s') for the observation that *followed* it. Two
things made that unavailable before, and both are addressed:

- **`bootstrap_values[env_id]` cannot serve.** It is read after the collection loop
  (`standalone_train_runner.py:550`), by which time a truncated environment has already
  been reset, so it is the value of the *post-reset* observation — the next episode's.
  Using it would be a quiet off-by-one-episode error. There is deliberately **no fallback
  to it** for a truncated row; a missing captured value raises instead.
- **The value must be captured at the truncation instant.** The runner now calls
  `agent.low_bootstrap_value_for_env(env_id, observations[env_id], states[env_id])` inside
  the `if done:` branch, guarded on `truncated and not terminated`, and *before*
  `collector.reset_one(env_id)` replaces the observation and `agent.reset_env_state(env_id)`
  zeroes the recurrent critic state (`standalone_lifecycle.py:181`). At that point
  `self.low_critic_hxs[env_id]` holds the state produced by consuming the truncation step
  (written at inference time, `standalone_low_inference.py:166`), which is the correct
  hidden state for evaluating the post-step observation. The ordering is pinned by a test.

`Rollout.truncation_bootstrap_values` is keyed by **row index**, not by env id, because a
truncation is a specific row and one environment can truncate more than once in a pass.

### What did not change

`rollout.dones` keeps its old meaning and is still recorded. Every other consumer reads it
unchanged — in particular the recurrent `reset_masks` in `_low_sequence_chunks`, where
either kind of boundary genuinely does break the recurrence. Only the GAE needed to know
*why* the episode ended.

## Files changed

| File | Change |
| --- | --- |
| `ha_ctse_process/standalone_low_update.py` | `_boundary_flags`, `_truncation_bootstrap`, split masks in `_low_returns` |
| `ha_ctse_process/standalone_segments.py` | `Rollout.terminated`, `.truncated`, `.truncation_bootstrap_values` |
| `ha_ctse_process/standalone_train_runner.py` | records both flags; captures V(s') pre-reset |
| `ha_ctse_process/standalone_agent.py` | `low_bootstrap_value_for_env`; reads the flag |
| `ha_ctse_process/config.py` | `legacy_truncation_as_termination = False` |
| `ha_ctse_process/standalone_cli.py` | `--legacy_truncation_as_termination` |
| `ha_ctse_process/standalone_manifest.py` | the flag joins `TRAINING_MANIFEST_FIELDS` |
| `tests/process/standalone/ha_ctse_process_truncation_gae_test.py` | new, 30 tests |
| `tools/analysis/truncation_bootstrap_impact.py` | new, the before/after measurement |

## Legacy reproduction

`legacy_truncation_as_termination` is **off by default at every layer** — config module,
agent, CLI — and a config object that has never heard of the field also gets the fix, so no
older harness silently inherits the old arithmetic. Set true, a truncation is scored exactly
as a termination was, and the captured bootstrap is ignored rather than coincidentally
equal; a test asserts both. The flag is recorded in the run manifest
(`training_config.legacy_truncation_as_termination`, verified present and `False` on the
real `ha_ctse_process.config` route), so a run states which semantics produced it.

```powershell
# Correct semantics: nothing to pass.
& $py -m ha_ctse_process.train --scenario belief_map ...
# Reproduce a pre-2026-09-17 recorded result:
& $py -m ha_ctse_process.train --scenario belief_map --legacy_truncation_as_termination ...
```

## Fail-closed choices

Two places refuse rather than guess, because the silent alternative reintroduces the exact
bias being fixed:

- A row flagged truncated with no captured bootstrap raises `ValueError`. Substituting zero
  would be the old behaviour wearing the new name.
- `terminated | truncated` that disagrees with `dones` raises, rather than let the
  advantages use a different set of boundaries than the recurrent reset masks.

One place deliberately does **not** refuse: a rollout supplying only `dones`, with no reason
flags at all, falls back to the collapsed arithmetic. Older harnesses and
`experiments/candidates` code build rollouts that way and genuinely cannot distinguish the
two reasons; raising would break working code, and inventing a bootstrap would be worse than
the documented old behaviour. A test pins this.

## Tests

```
$ python -m pytest -q tests/process/standalone/ha_ctse_process_truncation_gae_test.py
30 passed in 95.01s
```

Arithmetic, on hand-built rollouts where every number is checkable:

- termination gives `return = r` exactly (bootstrap zeroed)
- truncation gives `return = r + gamma * V'` exactly (bootstrap preserved)
- the two differ by exactly `gamma * V'` at the boundary, and by
  `(gamma*lambda)^k * gamma * V'` k rows earlier — the correction propagates backwards
  through the recursion with the usual GAE decay, so earlier rows were wrong too
- termination wins when both flags are set on one row

Mid-rollout:

- a truncation at row 1 of 4 uses its own captured value while the final row uses the
  end-of-pass `bootstrap_values` — two different numbers in one rollout
- perturbing a post-boundary reward changes no pre-boundary target (the cut), with a
  companion test showing that without a boundary it *does* (so the cut test is not vacuous)
- several truncations in one pass each use their own row's value
- a truncation in one environment does not touch another

Nothing else changed:

- a rollout with no boundary is byte-identical with the flag on and off
- a rollout whose only boundary is a termination is byte-identical too

Collector side:

- `low_bootstrap_value_for_env` equals the batched `low_bootstrap_values` row for that env
  (it delegates rather than defining the value twice), depends on that env's own recurrent
  state, and refuses an out-of-range env id
- source and AST tests pin the capture ordering: before `reset_one`, before
  `reset_env_state`, inside the boundary branch, guarded on truncation only; and on real
  data the captured value is asserted *different* from the post-reset one, which is the
  discriminating check rather than a structural one
- the CLI flag is verified to reach the config through the real
  `parse_args` + `apply_standalone_overrides` path, not only by source inspection

End to end, through the real collector and real legacy environments (`belief_map` and
`base` = `forced_relay`): every boundary is a truncation, every one carries a captured
bootstrap, at least one is mid-rollout, and the correction at the truncation rows equals
`gamma * V'` on real data. 0 optimizer updates.

### Regression

```
$ python -m pytest -q tests/process/
1 failed, 150 passed, 6 skipped in 59.95s
```

The one failure is pre-existing and unrelated:
`ha_ctse_process_clean_opportunity_authority_audit_test.py` needs
`logs/clean_supplied_executor_high_path_g0_20260720_054300/checkpoints/update_000_high.pt`,
a historical artifact absent from this checkout. Verified identical at `ec131539a` in a
throwaway worktree before any of these edits, and it references none of the changed symbols.

## Before/after measurement

`tools/analysis/truncation_bootstrap_impact.py` collects one rollout through the real
runner, real environment, real policy and real critic, then recomputes the value targets
twice from that single rollout — corrected and legacy — and reports the difference. It takes
**no optimizer step**: `process_update` is intercepted to stop the pass the moment the
rollout is complete, and the manifest export is suppressed, so nothing is written to
`runs/`, `logs/` or `metadata/`. RNGs are seeded exactly as `train.py` seeds them, so the
numbers are reproducible; verified by running it twice for an identical report.

```
$ python tools/analysis/truncation_bootstrap_impact.py --scenario <s> \
      --rollout-length 48 --max-steps 12 --num-envs 2 --seed 12345 --output <path>
```

| | `belief_map` | `base` (`forced_relay`) |
| --- | --- | --- |
| rows | 96 | 96 |
| boundaries / terminations / truncations | 8 / **0** / **8** | 8 / **0** / **8** |
| bootstraps captured | 8 | 8 |
| truncated row indices | 22, 23, 46, 47, 70, 71, 94, 95 | same |
| rows whose value target changed | 96 of 96 | 96 of 96 |
| mean \|Δ return\| | 0.404 | 0.334 |
| max \|Δ return\| | 0.619 | 0.714 |
| return at truncation rows, legacy → corrected | 1.1027 → 1.6564 | 0.8724 → 0.4147 |
| captured V(s') | 0.5593 | −0.4623 |
| γ·V(s') vs the observed change | 0.5537 = 0.5537 ✓ | −0.4577 = −0.4577 ✓ |
| max \|Δ normalised advantage\| | 2.6e-06 | 1.19e-01 |

What this documents:

- **Every boundary in both legacy scenarios is a truncation.** 0 terminations. The old
  branch was not an edge case in these environments; it was the only case.
- **All 96 rows change**, not only the 8 boundary rows, because the corrected TD error at a
  boundary propagates backwards through the GAE recursion.
- **The correction is signed, not a uniform shift.** V(s') is positive in `belief_map` and
  negative in `forced_relay`, so targets move up in one and down in the other. There is no
  direction in which the old arithmetic was "conservative".
- **The value targets move materially; the normalised advantages need not.** Advantage
  normalisation absorbs a near-uniform shift, which is why `belief_map` shows ~1e-6 there
  while its value targets moved by ~0.4. `forced_relay` shows 0.119, so the policy-gradient
  signal is affected too in at least one legacy scenario. The critic is the primary thing
  corrected; the policy follows through it.

### The capture really is pre-reset

The ordering argument above is not left as an assertion. For a truncation on an
environment's **last** row, the captured V(s') and the end-of-pass
`bootstrap_values[env_id]` are directly comparable: if the capture had happened after the
reset they would be identical. They are not, and the gap is the size of the error a
fallback to the end-of-pass value would have introduced.

| | `belief_map` | `base` (`forced_relay`) |
| --- | --- | --- |
| comparable rows | 2 | 2 |
| captured V(s') (pre-reset) | 0.5285 | −0.5953 |
| end-of-pass value (post-reset) | 0.9776 | −1.0502 |
| identical? | **no** | **no** |
| mean absolute gap | 0.4491 | 0.4549 |

So the naive fallback would have been wrong by roughly a factor of two, using the value of
the *next* episode's first observation. That is why `_truncation_bootstrap` raises instead
of falling back. The measurement reports this as `capture_is_pre_reset`, and a test asserts
`identical is False`.

Honest limits of this measurement: one short rollout per scenario from an **untrained**
policy and critic, on `configs.config_test`. The magnitudes characterise the arithmetic and
establish that the change is real and signed. They are not a prediction of the effect on a
trained result, and no such claim is made here.

## Impact on historical runs

Any result recorded before 2026-09-17 on a relay scenario was fit on the biased targets.
This change does not alter those records and no archived direction was re-run. Reproducing
one requires `--legacy_truncation_as_termination`; without it a rerun will differ, and that
difference is the fix rather than a regression. Whether any archived conclusion should be
revisited is the owner's call, not something this change decides.

## Related

`docs/Claude_docs/changes/2026-09-17-uav-service-restoration-v0.md` reported this as
`TRAINER_INTEGRATION_PENDING`; that status is now resolved. `uav_service_restoration_v0`
uses `episode.semantics = "continuing"` and truncates at the data-window edge, so it was
the environment that surfaced the defect, but as measured above it was never the only one
affected.

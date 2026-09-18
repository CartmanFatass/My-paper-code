# Truncation bootstrap in the shared trainer — fixed globally, both levels

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

## The fix, at the low level

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

## The same defect at the high level

The first version of this fix corrected only the low-level GAE. A review pass found the
identical collapse surviving in **both** high-level routes, so "globally in the shared
trainer" was not yet true. Both are now fixed through one shared helper,
`agent._boundary_is_terminal(done, terminated, truncated)`.

**R30 fixed-clock route** (`standalone_agent.py:record_environment_step`). A check row used
to close as `terminal=True, old_next_value=0.0` at every episode boundary. A truncated
boundary now closes `terminal=False, policy_truncated=True` with the post-truncation value
from `_r30_value_for_arrays`, evaluated *before* `reset_env_state` clears the skill and age
arrays the value is conditioned on. `policy_truncated` is not new machinery: it is exactly
what `truncate_high_rows_for_update` already applies at a PPO update boundary. It was
simply unreachable from an episode truncation.

**Legacy SMDP segment route** (`agent._bootstrap_high_values`). The skip condition was
`if not segment.terminal`, so a truncated segment got no bootstrap even though it already
stores `end_state` and `end_joint_obs`. It is now `if not self._segment_is_terminal(segment)`.
`Segment.terminal` keeps its collapsed meaning; `Segment.terminated` / `Segment.truncated`
carry the reason, and a caller that passes only `done` records `terminated = done`, which
preserves the old reading exactly.

One flag governs both levels. `legacy_truncation_as_termination` collapses the low-level
GAE, the R30 close and the SMDP segment bootstrap together, so a legacy reproduction is
coherent across the hierarchy rather than half-corrected.

## Observability

A silent fallback to the collapsed arithmetic would have been indistinguishable from the
fix in a run's metrics, so every low-level update now reports which arithmetic actually
ran:

| Metric | Meaning |
| --- | --- |
| `low_boundary_flags_resolved` | 1.0 when the reason flags were present and usable; 0.0 when the rollout supplied only `dones` and the collapsed fallback ran |
| `low_boundary_legacy_collapse` | 1.0 when `legacy_truncation_as_termination` forced the collapsed arithmetic |
| `low_truncation_rows` | how many rows of the rollout were truncations |

Both flags are set inside `_boundary_flags` itself, not inferred afterwards, so they cannot
disagree with the branch that ran. `low_truncation_rows` reports what the rollout contained
regardless of the legacy flag; read together the three are unambiguous.

### What did not change

`rollout.dones` keeps its old meaning and is still recorded. Every other consumer reads it
unchanged — in particular the recurrent `reset_masks` in `_low_sequence_chunks`, where
either kind of boundary genuinely does break the recurrence. Only the GAE needed to know
*why* the episode ended.

## Files changed

| File | Change |
| --- | --- |
| `ha_ctse_process/standalone_low_update.py` | `_boundary_flags`, `_truncation_bootstrap`, split masks in `_low_returns`, the three resolution metrics |
| `ha_ctse_process/standalone_segments.py` | `Rollout.terminated`, `.truncated`, `.truncation_bootstrap_values`; `Segment.terminated`, `.truncated` |
| `ha_ctse_process/standalone_train_runner.py` | records both flags; captures V(s') pre-reset; passes the reasons to both high-level paths |
| `ha_ctse_process/standalone_agent.py` | `low_bootstrap_value_for_env`, `_boundary_is_terminal`, `_segment_is_terminal`; the R30 close and the SMDP segment bootstrap |
| `ha_ctse_process/config.py` | `legacy_truncation_as_termination = False` |
| `ha_ctse_process/standalone_cli.py` | `--legacy_truncation_as_termination` |
| `ha_ctse_process/standalone_manifest.py` | the flag joins `TRAINING_MANIFEST_FIELDS` |
| `ha_ctse_process/checkpoint_io.py` | the flag is saved, read back as metadata, and restored on the eval/export path |
| `ha_ctse_process/AGENTS.md` | the boundary semantics as a rule that carries scientific meaning |
| `tests/process/standalone/ha_ctse_process_truncation_gae_test.py` | new, 43 tests |
| `tools/analysis/truncation_bootstrap_impact.py` | new, the before/after measurement |

## Legacy reproduction

`legacy_truncation_as_termination` is **off by default at every layer** — config module,
agent, CLI — and a config object that has never heard of the field also gets the fix, so no
older harness silently inherits the old arithmetic. Set true, a truncation is scored exactly
as a termination was, and the captured bootstrap is ignored rather than coincidentally
equal; a test asserts both. The flag is recorded in the run manifest
(`training_config.legacy_truncation_as_termination`, verified present and `False` on the
real `ha_ctse_process.config` route), so a run states which semantics produced it.

### Checkpoints and resume

A strict training resume was **already** protected: `legacy_truncation_as_termination` is a
config field, and `effective_training_contract` hashes `.config.*`, so a checkpoint written
under one setting and resumed under the other is *refused* rather than silently switched.
Verified empirically, not assumed. What was missing is the eval/export path, which does not
go through the strict contract: `checkpoint_io.py` now writes the flag into the checkpoint,
surfaces it through `load_checkpoint_metadata`, and restores it in
`apply_checkpoint_structure`, so replaying an old checkpoint for evaluation reproduces the
semantics it was fit under instead of quietly re-scoring it under the new ones.

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
43 passed in 108.91s
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

Also on the collector side, on **both** low-level architectures
(`strict_hmasd_mappo` recurrent and `feedforward`): `low_bootstrap_value_for_env` is
compared against a critic call rebuilt by hand in the test — that environment's own skills,
team code and hidden state, agent ids in order — so an error shared with
`low_bootstrap_values` cannot pass by agreeing with itself.

High level:

- `_boundary_is_terminal` is pinned as a truth table over all eight combinations plus the
  two "no reason supplied" cases and the legacy flag
- an R30 termination closes `terminal=True` with a zero bootstrap; a truncation closes
  `terminal=False, policy_truncated=True` with a bootstrap asserted equal to a direct
  `_r30_value_for_arrays` call on the same arrays
- the legacy flag collapses the R30 close and the SMDP segment bootstrap too, and a caller
  that supplies no reason flags keeps the collapsed close
- `_bootstrap_high_values` gives a terminated segment 0.0 and a truncated segment a real
  non-zero value, and a segment built without reason flags reads as terminal exactly as
  before

End to end, through the real collector and real legacy environments (`belief_map` and
`base` = `forced_relay`): every boundary is a truncation, every one carries a captured
bootstrap, at least one is mid-rollout, and the correction at the truncation rows equals
`gamma * V'` on real data. 0 optimizer updates.

Past the arithmetic, one further end-to-end test drives a real rollout containing
truncations through `update_low` itself, on both architectures — so the corrected returns
are exercised against `low_value_norm.update`, the recurrent sequence chunking and the PPO
epochs, not only against `_low_returns`. That test does take optimizer steps: one update on
a 48-row rollout, inside pytest, weights discarded with the agent. It is a test, not a
training fit, and nothing is written outside `temp/`.

### Regression

```
$ python -m pytest -q tests/process/
1 failed, 149 passed, 6 skipped in 135.93s
```

(156 collected: 43 in the new file, 113 pre-existing. An earlier draft of this note quoted
`150 passed` for this command; that figure did not reconcile with the collected total and is
replaced by the run above, which was re-executed after every change described here.)

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
| mean \|return\| over all rows, legacy → corrected | 23731.93 → 23732.34 | 4.4896 → 4.1556 |
| mean \|Δ return\| **relative** to mean \|return\| | 1.7e-05 | 7.4e-02 |

What this documents:

- **Every boundary in both legacy scenarios is a truncation.** 0 terminations. The old
  branch was not an edge case in these environments; it was the only case.
- **All 96 rows change**, not only the 8 boundary rows, because the corrected TD error at a
  boundary propagates backwards through the GAE recursion.
- **The correction is signed, not a uniform shift.** V(s') is positive in `belief_map` and
  negative in `forced_relay`, so targets move up in one and down in the other. There is no
  direction in which the old arithmetic was "conservative".
- **The absolute change is the same size in both scenarios; the relative change is not.**
  `belief_map` carries mean \|return\| ≈ 2.4e4 on this untrained rollout, so a mean
  \|Δ\| of 0.40 is ~1.7e-5 of the target magnitude. `forced_relay` carries mean
  \|return\| ≈ 4.5, so its 0.33 is ~7.4%. The correction is arithmetically exact in both;
  only in `forced_relay` is it large *relative to the signal* on this rollout. The
  normalised advantages agree: ~1e-6 in `belief_map` (advantage normalisation absorbs a
  near-uniform shift), 0.119 in `forced_relay`. So the critic is the primary thing
  corrected, and the policy-gradient signal is measurably affected in at least one legacy
  scenario — but these numbers do not license a claim about either scenario's trained
  outcome.

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
establish that the change is real and signed. An untrained critic's return scale is
arbitrary, which is exactly why the relative row above matters and why neither the absolute
nor the relative figure predicts the effect on a trained result. No such claim is made here.
The measurement covers the low level only; the high-level fix is established by the tests
above, not by a measured magnitude.

## Review

`hmasd-reviewer` (Opus, read-only) examined the diff against this note as the acceptance
contract. Three findings, all acted on:

1. **The fix was not global** (HIGH, confirmed). The same collapse survived in both
   high-level routes, so the owner instruction was not met by the low-level change alone.
   Fixed as described above, with tests.
2. **`_truncation_bootstrap` accepted a wrong-width entry**. It raised on a missing entry
   but not on one of the wrong shape. Now raises on both.
3. **Checkpoint compatibility** (partly wrong as filed). The finding read a strict training
   resume as able to switch semantics silently. Checked empirically: the flag is already
   inside `effective_training_contract`, so such a resume is refused. The eval/export path
   was genuinely uncovered, and that part is fixed.

Coverage the review asked for and this note now carries: the `feedforward` architecture, an
independent recomputation of the single-environment bootstrap rather than only agreement
with the batched call, an end-to-end test through `update_low`, and the relative-magnitude
context above.

One observation recorded rather than changed: in `low_bootstrap_values` the non-recurrent
branch does not denormalize through `low_value_norm` while the recurrent branch does. That
asymmetry is byte-identical to `ec131539a`, i.e. it predates this work, and the test pins
the existing reading rather than altering it. Changing it would be a separate semantic
change to the feedforward path and is not part of this one.

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

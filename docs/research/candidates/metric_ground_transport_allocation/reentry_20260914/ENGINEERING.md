# Reentry protocol implementation and bounded verification

At 2026-09-14T06:30:15Z, the DM completed the first concrete implementation batch
on codex/mgtap, based on1c5887704d42bd97db0835501338b657850ac352.
No legacy learner, native environment, policy, runtime registry or other direction
was modified.

## Implemented

- Separate selection/holdout masters and private-stream address contract.
- Equal three-candidate opportunity and per-arm OWN validation-score maximization.
- Deterministic exact ties preserving the inherited LR first.
- Complete32-world panel validation, finite J, rate/endpoint/address/stage binding.
- Holdout rates must match the saved validation argmax and selection provenance;
  no holdout row is accepted as selector input.
- Ordered holdout primary, inclusive MEI band and conditional-panel SE.
- Work-count generator reading the same constants; no learning or simulation.

## Checks actually executed

Python3.11.9, local C:/Users/fires/AppData/Local/Programs/Python/Python311/python.exe.

```text
python -m unittest discover -s tests/experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01 -p test_protocol.py -v
```

13 tests passed, unittest-reported duration0.010s, process exit0.
[Full terminal test output](TEST_OUTPUT.txt) is retained.
Synthetic score fixtures are NOT experiments, added native evidence or measured returns.
The protocol imports no Torch, native host or model and fits no parameters.

```text
python -m experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01.protocol --out docs/research/candidates/metric_ground_transport_allocation/reentry_20260914/PLANNED_EXPOSURE.json
```

This emitted [planned exposure](PLANNED_EXPOSURE.json):8 planned fits,
589824 team ticks,4096 Adam calls,13434880 actor row uses.
No simulation was used to count a known loop.

The original305-line user copy and archived copy compare equal after CRLF-to-LF
normalization. Byte/hash provenance is in[SOURCE_RECEIPT.json](SOURCE_RECEIPT.json).
The full two answer bodies, not a summary/link, are archived.
git diff --check completed without whitespace errors.

## Remaining implementation, not completed acceptance

The full eight-fit native runner has NOT been implemented or executed in this batch.
It must instantiate new candidate-owned actors/critics/optimizers/RNGs; persist all
candidate evidence; save and hash the selection record before holdout fitting;
and bind the actual native command, source, current admission and supervisor.
The selection record is an auditable stage fence, not a security guarantee that
a caller cannot forge an input object. Runtime wiring and persistence need focused
tests/review; these13 pure tests do not establish native end-to-end integrity.

Proportionate independent review of the completed changed behavior remains pending.
No reviewer/monitor/transport child or new Pro/Portfolio request was started.
No pending or uncertain Send is created. Historical uncertain identities are untouched.

## Cost and preservation

This batch performed local source/record reading, protocol implementation, synthetic
tests, count calculation and archival normalization only. Native exposure is zero.
Do not read the unittest duration as full support cost; full support/provider/lifetime
totals remain UNKNOWN. No file or worktree was deleted and no deletion refusal bypassed.

## Complete runner implementation batch (prospective continuation)

L0: implement one runnable eight-fit MGTAP-LR-SELECTION-B01 entry point and focused
synthetic wiring/publication tests, reusing the accepted native learner. Authoring
checkout is C:/Projects/HMASD-worktrees/dm-n5-continue-20260904, branch codex/mgtap,
starting HEAD1fb4259905f0a803f515b40131bea9c7417eec61, initially clean.
The Implementer owns only new `mgtap_lr_selection_b01/study.py` and its focused
`test_study.py`; DM retains card/protocol changes, Git, technical acceptance and launch.
Other writers' documentation and request files are preserved.

The current card §§2–5 supplies the exact native semantics, three-candidate order,
fresh state/RNG ownership, stage fence, eight-fit exposure, primary, output and limits.
Use existing `mgtap_early_exposure_b02/study.py`, `conditional_pooling.py`, and
`ucope/uav_motion_prefix_b01/learner.py` as read-only dependencies; do not modify frozen
learners or other directions. Focused tests must exercise candidate order and fresh
state, selected per-arm rates, a persisted selection record before holdout construction,
all panels/raw output and the primary, and failure partials. They are synthetic checks,
not native science, and must not create extra empirical evidence.

Bounds: one runner under600 lines, this research attempt under2000 non-test source
lines, focused test budget5 minutes for this directory; no scientific run, remote
execution, additional candidate/seed, changed endpoint, child delegation, or Git commit
by the Implementer. Return actual diff/check output and precise residual issues to DM.
Independent Sol/high changed-path review follows; it is technical evidence, not a
lifecycle grant. Required §4 items and the corrected4GiB admission plan are explicit
in the prospectively updated card. Native exposure remains zero.

Actual Implementer dispatch: `/root/im_s_m_mgtap_lr_runner`, model gpt-5.6-sol,
reasoning medium, fork_turns=none; batch MGTAP_LR_RUNNER_IMPL_20260914.
Parent is this DM App task01a09cd8-676e-7513-806d-a86b7e104518, native /root.

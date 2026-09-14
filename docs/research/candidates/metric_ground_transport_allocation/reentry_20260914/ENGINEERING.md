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

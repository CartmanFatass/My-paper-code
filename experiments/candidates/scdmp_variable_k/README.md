# SCDMP-B1 exact v5 isolated construction

This directory binds only `SCDMP-B1-SCIENCE-20260812-05`. Import and the
default CLI perform no random draw, environment step, neural forward,
optimization, evaluation, or scientific inference. The default command emits
only a static, explicitly incomplete support packet:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.scdmp_variable_k
```

Production is explicit, one-shot, CPU-only, and requires a fresh result path:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.scdmp_variable_k --production --output experiments/candidates/scdmp_variable_k/results/scdmp_b1_v5_result.json
```

The runner refuses to overwrite an existing result. It binds one CPU worker
and hides GPUs before importing Torch, enforces the 5,400-second and 2-GiB
ceilings, and produces a complete result only after all eight paired seeds,
final checkpoints, scored panels, separately cloned target/reverse audit
panels, registered gate facts, inference bounds, and exact microstep categories
exist. An error or resource overrun produces an incomplete, noninterpretable
lifecycle packet.

The production command also owns a durable activity sidecar at
`<fresh-result.json>.activity.json`. It is atomically created when the first
SCDMP update-zero model forward is about to execute (after its exact tensors
and coverage certificate exist), then atomically updated at each completed
seed and at abort. After all evidence exists, the final result is installed by
an atomic fresh-path rename; only then is the sidecar atomically advanced to
the complete terminal lifecycle. This preserves truthful activity state if a
host or process interruption prevents installation of the final result. A
fresh run refuses an existing final path or sidecar path.

Each seed's four arm-shared scalers use exactly 10,752 target atoms per output
from `E_2,E_4,E_8` in the registered traversal. The implementation executes
`numpy.std(x64, axis=None, dtype=numpy.float64, ddof=0)`, applies the float64
`1e-3` floor, and casts once to float32. No fit mean is subtracted and no task,
oracle, support, treatment-effect, confidence-bound, or resource observable is
normalized by these scalers.

Training preserves all complete rows and registered averaging but batches the
576 row-level model evaluations per arm/update into nine equal-row model calls.
The actor similarly batches its 12 node-action and 36 directed-edge action-pair
factors per boundary before applying the exact first-action-conditioned cycle
max-sum and lexicographic tie law.

The true audit likewise never rolls 81 joint-action candidates. For each
word-state it advances exactly the 12 independent slot/action trajectories,
caches every primitive state, derives all four node and `4 x 9` directed-edge
reward/potential factors, and applies exact cycle dynamic programming. The
registered 81-action denominator is an exact analytic factor panel. Reversal
maximum absolute score difference is the larger DP maximum of the target-minus-
reverse and reverse-minus-target factor systems. This fixed 12-candidate path
is within the evidence-complexity ceiling.

Composition rows introduce no environment replay. The original charged
`k=4/k=8` endpoint rollout captures its midpoint state and ordered prefix/suffix
node and edge accumulations; `C_22/C_44` reuse that trace. The immutable
registered ledger remains 1,606,656 analytic-panel-equivalent microsteps. The
result reports those frozen denominators separately from the full-joint
environment steps and scalar-agent factor transitions physically executed by
the bounded exact reduction.

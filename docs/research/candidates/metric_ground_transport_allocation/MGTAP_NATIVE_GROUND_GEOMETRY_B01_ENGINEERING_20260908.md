# MGTAP B01 source engineering and readiness — 2026-09-08

## CM result

The frozen B01 REL/DENSE comparison now has a small direction adapter over the
reviewed UCOPE APIs. The implementation is engineering-ready for a later,
separately allocated native invocation. This return contains no native
environment call, full B01 training, model-learning result or scientific
performance claim.

Owned implementation paths:

```text
experiments/candidates/ucope/uav_motion_prefix_b01/              # exact accepted source snapshot
experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/
scripts/run_mgtap_native_ground_geometry_b01.py
tests/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/
```

The five UCOPE source files were copied byte-for-byte from fixed source pin
`d726acf63f8db47bd2e93e43cac8bbd27529d8ad`; per-file SHA-256 values are:

| source path | SHA-256 |
| --- | --- |
| `experiments/candidates/ucope/uav_motion_prefix_b01/__init__.py` | `9ac022e8f48f07e80a45cb3ff30d499dcf9285b5d97ccbdf6601ee08b40eb84d` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` | `fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py` | `8d253b86c6d7c8777f79ce428193efa36d31f8e7015226b4ebdd0553c3c983bd` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py` | `5370d299b933ce0f9e8ce1b7c7d0e10a1172876c8b2be7d629f99ec353df54c4` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/study.py` | `866fa73b30dc62eebc293be9c1ca0d81f7fcdcd5657e52e558aa96e447129b9a` |

These are the reviewed d726 bytes, including the source's B02
`agent_compound` ratio path. Later renewal and value-normalization revisions
were not transplanted.

## Binding implementation

`geometry.py` keeps the source actor call shape
`actor(observations, hidden) -> (mean, recurrent, hidden)`. It replaces only
the encoder preactivation:

```text
REL:    raw(108->64) + P[mean(tanh(U user_row)); mean(tanh(V uav_row))]
DENSE:  raw(108->64) + Q tanh(D 108->16)
```

REL uses all twenty 3-wide user rows and ten 4-wide other-UAV rows, fixed
denominators 20 and 10, bias-free row maps and a bias-free 41-to-64 fusion.
DENSE uses a 108-to-16 affine branch with zero hidden bias and a bias-free
16-to-64 output branch. Both keep the raw affine 108-to-64 path and the
unchanged GRU, velocity head, log standard deviations and separate critic.

The REL and DENSE additional branch subtotals are each 2,768 parameters:
`20*3 + 10*4 + 41*64 = 2,768` for REL and
`(108+1)*16 + 16*64 = 2,768` for DENSE. Including the unchanged downstream
actor and critic, each complete learner has 69,079 parameters. `P` and `Q`
are zero-initialized, so both initial policies equal the source G template.
The common template uses `100000*master+11`; private branch weights use the
separate `100000*master+12` stream, with fan-in bounds `±1/sqrt(fan_in)` and
zero dense hidden bias. `build_pair` uses RNG forks, leaving the caller's
global torch stream unchanged.

The runner reuses source `collect_episode`, `update`, `optimizer_for`,
`joint_terms`, `clipped_policy_loss`, `snapshot`, `exposure`, and
`new_counts`. Both arms are primitive G with `duration=None`,
`ratio_grouping="agent_compound"`, entropy coefficient 0.01, source native
reward aggregation and source recurrent/PPO update semantics. The native
path is per master and fixes masters to 8201 or 8202; it retains REL, DENSE
and fixed-zero-velocity H evaluation rows and writes episode/rollout JSONL
plus one summary JSON. The fixture path uses only `SyntheticAdapter`.

## Acceptance matrix

| requirement | evidence | result |
| --- | --- | --- |
| source bytes bound to fixed review pin | five file SHA-256 values above; `git cat-file blob d726:path` comparison | PASS |
| typed equations and fixed padding | `RelationResidualEncoder`, `test_relation_padding_uses_fixed_denominator` | PASS |
| generic full-information comparator | `DenseResidualEncoder` keeps raw 108 path; parameter-match test | PASS |
| exact 2,768 branch count and 69,079 complete learner count | `parameter_summary`; `test_parameter_match_and_common_initial_policy` | PASS |
| zero P/Q common initial policy and private branch stream | pair output equality, zero projection assertions, RNG test | PASS |
| primitive G and no duration | actor `duration is None`; runner sets primitive G and no duration draw | PASS |
| B02 per-agent compound credit | source `joint_terms` and `clipped_policy_loss`; sum-before-row-average test gives `-5.0` for five agents | PASS |
| raw 108 actor/global critic/native reward path | source actor features, critic, `collect_episode` and `team_reward` are reused | PASS by direct source binding |
| master and prospective exposure binding | `MASTERS=(8201,8202)`, runner defaults 256/512/32 and writes configuration; no full run here | READY, unobserved until allocation |
| all-outcome endpoint rule | `_primary` returns `REL_ABOVE_MEI`, `INSIDE_MEI`, `REL_ADVERSE` only for complete sampled rows, else `INCOMPLETE` | PASS by focused path |
| toy publication | `test_runner_fixture_reaches_publication_path`; CLI fixture output | PASS |
| native result and resource evidence | no native call; no admission receipt required for this engineering-only turn | DEFERRED by design |

## Focused checks and direct outputs

The exact local interpreter is the repository's test interpreter,
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/test_geometry.py -q
.......                                                                  [100%]
7 passed in 5.12s
```

The CLI smoke used a direction-scoped test output root and the non-scientific
fixture only:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_mgtap_native_ground_geometry_b01.py --fixture --master 8201 --output C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/test/mgtap_native_geometry_b01_check/summary.json
{"parameter_summary": {"DENSE": {"actor": 69079, "branch": 2768}, "REL": {"actor": 69079, "branch": 2768}}, "scientific_invocation": false, "status": "COMPLETE"}
```

Compilation and `git diff --check` also pass. The seven tests take under the
five-minute research-directory budget and the fixture is well below the
60-second smoke bound. No profiler, pilot, retry, native environment call,
scientific import or result root was created.

## Independent scientific-risk review

This is a separate post-implementation inspection of the changed adapter,
runner and source bindings against the frozen card and accepted UCOPE source.
It is a risk review, not a performance review.

1. **Information leakage:** no treatment-only global state, `local_indices`,
   base coordinate or persistent ID enters `geometry.py`; both branches see
   the full raw 108 input. The separate critic is copied from the reviewed
   source and is not changed. **Finding: no leakage found.**
2. **Equation and padding drift:** REL slices the 60 user values and 40
   other-UAV values from the 104 base features, uses fixed row counts and
   applies nonlinear maps before pooling. The raw residual is retained.
   DENSE consumes all 108 values. **Finding: no dimensional drift found.**
3. **Initialization drift:** raw weights, GRU, mean head, log standard
   deviations and critic are copied from the same source template; P/Q are
   zero and DENSE hidden bias is zero. Branch initialization is inside a
   private fork. **Finding: focused tests establish equality and branch
   connectivity; they do not establish trained-policy equality after updates.**
4. **Credit drift:** the adapter supplies the source actor attributes expected
   by `joint_terms`; the runner passes `agent_compound` and entropy 0.01 to
   both arms, reusing source aggregation and recurrent update code.
   **Finding: no new loss or reward equation was introduced.**
5. **Endpoint drift:** `_primary` compares paired sampled `J` rows and emits
   no branch for incomplete data. H remains diagnostic. **Finding: complete
   versus incomplete handling is explicit; two-master aggregation and native
   endpoint values remain unobserved until a future result invocation.**
6. **Runtime/resource risk:** REL has more matrix products and nonlinear row
   operations than DENSE despite equal branch counts. The runner records the
   source-derived cost law and does not claim affordability, elapsed time,
   memory or competence. **Finding: resource evidence is intentionally open.**
7. **Shared-path integration risk:** the direction branch now carries the
   exact d726 source snapshot while current `main` contains later UCOPE source
   revisions. Root must integrate the source paths by explicit path-aware
   reconciliation and preserve the d726 bytes for any B01 launch; a later
   source revision requires a fresh currentness decision. **Finding: integration
   risk is material but named and does not change this engineering result.**

No unsupported performance conclusion follows from this review. It establishes
only code-path conformance and identifies the native-run and source-reconcile
facts that remain open.

## Prospective native binding and cost arithmetic

For a later launch, first commit and push the exact source bytes, create a
detached remote worktree at that SHA under `/home/wu/hmasd-worktrees`, and use
the configured WSL node and Python. The literal 8201 binding is:

```text
ssh hmasd-wsl-node '/usr/local/bin/agent-task mgtap-native-ground-geometry-b01-8201 -- bash -lc "cd /home/wu/hmasd-worktrees/<LAUNCH_SHA> && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-inputs/mgtap-native-ground-geometry-b01-8201/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_native_ground_geometry_b01.py --native --master 8201 --output /home/wu/hmasd-inputs/mgtap-native-ground-geometry-b01-8201"'
```

The 8202 invocation changes only the accepted `agent-task` name, master and
request-specific output root. The preflight and runner are joined by `&&`
inside the same detached supervisor. This is a prospective command only; it
was not sent or executed in this turn.

The card's expected exposure is 512 training episodes × 256 steps = 131,072
native team steps and 1,024 Adam calls per learned fit; 32 sampled evaluation
episodes = 8,192 team steps per learned fit. Across four learned fits the
counts are 2,048 training episodes, 524,288 training team steps, 4,096 Adam
calls, 128 learned evaluation episodes and 32,768 learned evaluation steps.
The shared H reference adds 64 episodes and 16,384 steps, for 2,240 complete
episodes and 573,440 team steps overall.

The source-derived per-arm cost law is:

```text
C_a = C_init,a + 131072*c_env+actor,a + 1024*c_update,a
      + 8192*c_eval,a + C_publication,a
```

One learned fit has
`5*(131072+8192)+1024*512*5 = 3,317,760` actor-row evaluations. REL's
additional branch uses 4,664 matrix-weight products and 610 inner tanh
outputs per row; DENSE uses 2,752 products and 16 inner tanh outputs. The
coefficients, incremental wall time, activation memory and RSS are unknown.
The 300-second bounded engineering-check process budget is respected by the
focused test and fixture smoke; it is not a native-run cap and no native run
is allocated here.

## DM readiness and next owner

The source engineering is READY for Root's later launch allocation, subject to
the named source-path reconciliation and fresh remote admission. The DM has
not selected a scientific invocation, pilot, profiler, retry, fourth
comparison arm, changed seed, changed endpoint, UAV validation or Portfolio
action. A future CM/Root launch must retain this card's exact REL/DENSE
comparison, primitive G, B02 credit, sampled endpoint, masters, exposure and
all-outcome rule. Passing these checks establishes implementation conformance,
not an empirical REL advantage or a competent-generic certification.

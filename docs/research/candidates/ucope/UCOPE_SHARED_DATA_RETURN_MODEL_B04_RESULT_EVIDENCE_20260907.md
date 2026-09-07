# UCOPE shared-data return model B04 technical and execution evidence

## Implementation and acceptance

Assignment P09-UCOPE-HALF-DATA-01; [card sections 2–5](UCOPE_SHARED_DATA_RETURN_MODEL_B04_SCIENCE_CARD_20260907.md), frozen at `414cd77e50061f1dee102645b980886057942183`.
The shared B02 runner accepts an explicit batch count, resolves its omitted default to the existing
1024 constant and reports the selected count in collection, summary and cost law. The new B04 entry
fixes 512 batches and seeds 6601/6602 with B04 result identity. B02/B03 entry defaults, model/evaluator,
B02 RNG family, binary64 row/update order, native host, costs, rules and full 4096 evaluation are unchanged.
No global seed or batch mutation occurs. ENGINEERING_SCOPE_SPEC section 4 additions: none, per card section 4.
Source delta: 5 additions/4 deletions in shared runner and 23-line B04 entry; no learner/host changes.

Focused acceptance (synthetic host returns only, zero scientific exposure):

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/shared_data_return_model_b04/test_budget_binding.py tests/experiments/candidates/ucope/shared_data_return_model_b03/test_seed_binding.py tests/experiments/candidates/ucope/shared_data_return_model_b02/test_shared_return.py::test_synthetic_changed_path_and_publication --basetemp temp/directions/ucope/test/shared-return-b04-synthetic-01
```

Result: **3 passed in 7.87 s**, only the existing unknown `cache_dir` config warning. The B04 fixture
executes all 512 batches on synthetic rows and all 4096 evaluation indices/context/policy for each new
seed, checks selected counts/cost law and summary publication, and captures unchanged B02/B03 default
1024 arguments using one synthetic historical batch. Existing seed/default/publication checks pass.
This covers the affected post-learner publication path without a real-host smoke or replay. Independent
review by the reused `review_ah_ucope_b01` reviewer found no material finding against base `414cd77e5`.
The reviewer inspected B04 synthetic training/update/evaluation artifacts and historical defaults/partial
publication without rerunning tests or science. New test: 62 lines; source total 28 additions/4 deletions.
No result-bearing invocation has been dispatched. Real-host performance and timing remain unmeasured.

## Cost and execution boundary

Per-arm projection from existing B03 whole-path evidence: 10.46 s/dataset, 20.92 s summed, with reduced
training work but unchanged evaluation. Cost law `T_init + 512*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish`.
No phase coefficients or aggregate CPU estimate is available and no calibration run follows. Each complete
command cap is 600 s including adjacent fresh admission, interpreter/startup, learning, evaluation,
publication and exit; 1200 s summed. Staging/control intervals are separate from summed invocation wall.
Each selected dataset has 131072 training and 98304 final evaluation episodes (229376 total),
196608 scalar updates, 65536 histogram increments and 264 initially zero values.

Remote-only `wsl_4070` / `hmasd-wsl-node`, CPU Python binary64, one scientific process/thread,
`/home/wu/.venvs/hmasd/bin/python`; `.codex/hmasd-compute.toml` controls exact execution facts.
Source will be integrated and pushed by Root before its integration acknowledgment and exact prelaunch
binding. Then exactly seed 6601 followed by 6602 after terminal reconciliation, irrespective of first
valid score, with distinct handles/roots and fresh same-node admission. No local fallback, extra pilot,
replay, retry or third seed. Root receives accepted handles; CM observes to adoption ACK or terminal
and collects. A dependent defect/admission gap returns completed/partial facts without a new invocation.

## Launch binding and collection

Root integrated and pushed the card/accepted source at main `98ee9ec0f` (integration commits
`942a3ec86`, `98ee9ec0f`) and acknowledged execution, relayed by DM before this binding.
The exact accepted launch source is `71433bfabb70481def4329e622a838fa0cd9eeec` on `codex/ucope`;
Git surface comparison with integrated main shows no differences in the B02/B03/B04 runners
or UCOPE experiment tree. Both authoring checkout and bound source surface are clean.

Node `wsl_4070`, detached cwd `/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907`;
full-history named-reference Git bundle/SCP stages the committed source, using
`/home/wu/hmasd-inputs/ucope-b04-source-20260907.bundle`. Handles are
`ucope-shared-return-b04-seed6601-20260907` and `ucope-shared-return-b04-seed6602-20260907`.
Both handles were confirmed absent and proposed remote source/bundle locations unused before binding.
Each supervisor log is `/home/wu/.agent-tasks/<handle>/task.log`. Each output root is
`temp/directions/ucope/exp/shared-data-return-b04-seed<seed>/` beneath the bound cwd, containing
`summary.json` and adjacent `resource_admission.json`. The outer timeout includes admission and
all runner work; admission failure prevents the adjacent runner. Same selected host, no fallback.

Exact remote supervisor command strings, recorded before either output:

### Seed 6601

```sh
/usr/local/bin/agent-task run ucope-shared-return-b04-seed6601-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b04-seed6601/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b04.py --seed 6601 --out temp/directions/ucope/exp/shared-data-return-b04-seed6601'"'"''
```

### Seed 6602

```sh
/usr/local/bin/agent-task run ucope-shared-return-b04-seed6602-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b04-seed6602/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b04.py --seed 6602 --out temp/directions/ucope/exp/shared-data-return-b04-seed6602'"'"''
```

## Terminal collection

Pending; neither B04 invocation has been dispatched at this binding commit.

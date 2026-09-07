# UCOPE shared-data return model B03: technical and execution evidence

## Contract and accepted implementation

P08-UCOPE-TWO-DATASETS-01; [frozen card sections 2–5](UCOPE_SHARED_DATA_RETURN_MODEL_B03_SCIENCE_CARD_20260907.md).
Source: `af7c7d516bbd9466a2775d9cb1e29582be1aaa36`, pushed on `codex/ucope`.
Explicit seed arguments now reach private collection RNG, training ancestry and final paired evaluation.
B02 family literal and default seed 6401 remain unchanged. B03 has its own result identity.
The four native host modules, binary64 update order, budgets and observation boundary are unchanged.
Owned source changes: B02 `model.py`, `evaluation.py`, `runner.py`; B03 script; focused B02/B03 tests.
Source delta 37 additions/14 deletions (new runner 23 lines); tests 79 additions/1 deletion.
ENGINEERING_SCOPE_SPEC section 4 additions: none; ordinary argument plumbing only.

## Focused acceptance and post-learner coverage

Two focused synthetic tests passed in 0.56 s (existing cache_dir warning only):

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/shared_data_return_model_b03/test_seed_binding.py tests/experiments/candidates/ucope/shared_data_return_model_b02/test_shared_return.py::test_synthetic_changed_path_and_publication --basetemp temp/directions/ucope/test/shared-return-b03-synthetic-01
```

They check independent private streams, both selected training/evaluation ancestry bindings, fresh states,
unchanged default 6401 and compact summary publication. All host calls are synthetic: zero scientific exposure.
Independent affected-path review by the reused `review_ah_ucope_b01` reviewer found no material issue;
it inspected five saved synthetic summaries without repeating execution. Existing native host/rule checks
are reused. These checks establish the seed/publication contract, not empirical performance.

## Prospective execution record (before either result)

Exactly seed 6501 followed by seed 6502 after terminal reconciliation, irrespective of first valid score.
Per-arm cost projection: same complete-path B02 shape, 7.73 s/dataset; 15.46 s summed.
Complete cost law and exposures are card section 4. No fresh calibration or scientific smoke was run.
Each cap is 600 s including fresh admission, interpreter, learner, final evaluation, publication and exit;
1200 s summed cap. Study critical path additionally includes control/staging intervals. Aggregate CPU is
unmeasured; single scientific process/compute thread, CPU Python binary64. Remote only; no local fallback.

Node `wsl_4070`, SSH `hmasd-wsl-node`; interpreter `/home/wu/.venvs/hmasd/bin/python`.
Detached exact-source cwd `/home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907`.
Full-history named-reference Git bundle/SCP stages the committed source; no live source copying.
Handles: `ucope-shared-return-b03-seed6501-20260907`, `ucope-shared-return-b03-seed6502-20260907`.
Supervisor log for each is `/home/wu/.agent-tasks/<handle>/task.log`.
Output roots are `temp/directions/ucope/exp/shared-data-return-b03-seed<seed>/` beneath that cwd;
each has its own adjacent `resource_admission.json` and `summary.json`.
Stop at terminal success/failure/600 s. No third seed or retry is authorized. A shared primary defect
or failed admission returns an execution gap; all partial evidence is retained.

Exact supervisor command arguments, passed as one remote shell string via SSH:

### Seed 6501

```sh
/usr/local/bin/agent-task run ucope-shared-return-b03-seed6501-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b03-seed6501/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b03.py --seed 6501 --out temp/directions/ucope/exp/shared-data-return-b03-seed6501'"'"''
```

### Seed 6502

```sh
/usr/local/bin/agent-task run ucope-shared-return-b03-seed6502-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b03-seed6502/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b03.py --seed 6502 --out temp/directions/ucope/exp/shared-data-return-b03-seed6502'"'"''
```

## Terminal collection

Pending; neither B03 invocation has been dispatched at this record commit.

# SERVICE-ALLOCATION-B01 seed402 execution record, 2026-09-07

Authority: P07-VSPC1-EXEC-01 at ef6b182b949159167418b1c3bab472d41ae28d86. Accepted source: `faf786e135b3f55e535c898e17e646dcc341bdec`. Source remains read-only.

Remote node `wsl_4070` via `hmasd-wsl-node`; detached cwd `/home/wu/hmasd-worktrees/vspc1-service-allocation-b01-seed402-20260907`; interpreter `/home/wu/.venvs/hmasd/bin/python`. CPU float32, one compute thread, batch16; no local fallback.

## Frozen calls and stop boundary

Each command below is passed as one command-string argument to `/usr/local/bin/agent-task run HANDLE`. Existing supervisor detaches it. `/usr/bin/time -p` records complete real/user/sys in the supervisor log; timeout includes admission, startup/import, learner, evaluation, publication and exit. Fresh adjacent admission requires physical and effective available memory >=4 GiB. No retry or additional result-bearing call is authorized. FACTOR technical acceptance is required before GENERIC, without score selection.

### FACTOR
Handle: `vspc1-service-allocation-b01-factor402-20260907`
```sh
/usr/bin/time -p timeout --signal=KILL 2700s bash -c 'cd /home/wu/hmasd-worktrees/vspc1-service-allocation-b01-seed402-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/FACTOR/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_service_allocation_b01.py --arm FACTOR --seed 402 --out temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/FACTOR'
```

### GENERIC
Handle: `vspc1-service-allocation-b01-generic402-20260907`
```sh
/usr/bin/time -p timeout --signal=KILL 2700s bash -c 'cd /home/wu/hmasd-worktrees/vspc1-service-allocation-b01-seed402-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/GENERIC/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_service_allocation_b01.py --arm GENERIC --seed 402 --factor-summary temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/FACTOR/summary.json --out temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/GENERIC'
```

## Cost projection and publication coverage

Per-arm runner cost law: 4096 training episodes, 196608 training ticks, 65536 training decision rows, 61440 nonterminal target rows, 256 optimizer steps, 1280 learner evaluation episodes, 61440 evaluation ticks and 569344 scalar Q predictions. FACTOR totals 258048 ticks; GENERIC adds the single 256-episode rule evaluation (12288 ticks), totaling 270336 ticks. New-host unit costs remain unknown as frozen in card §6; prior two-queue 4.84/5.48-second walls do not supply a calibrated forecast. Thus numeric per-arm machine-time projections are unavailable, not zero or a measured under-cap claim. No extra cost probe is selected. Original cap is 2700 seconds per complete call; nominal maximum summed invocation wall is 5400 seconds. Sequential study elapsed includes staging/collection intervals and is distinct from summed invocation wall; aggregate CPU is measured separately as user+sys. No arm is removed.

Post-learner coverage: accepted technical record reports nine focused tests, including readable learner-only and full three-controller pair publication from saved synthetic inputs. No repeat smoke is required. GENERIC invokes the rule and paired publication in its own capped process. Collection checks actual source, counts, finite indexed endpoints, all five checkpoints, norms/movement, receipts, and published contrasts/SE/AUC against saved primary arrays. Scientific interpretation belongs to DM.

## Execution facts

Pending: remote committed-object staging and first launch. No selected exposure at record freeze. Root receives accepted handles immediately; CM retains observation until Root adoption ACK, and always retains terminal collection/technical acceptance.

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

At record freeze, remote committed-object staging and first launch were pending. No selected exposure existed then. The completed E0 observation and subsequent repair authority are recorded below. Root receives accepted handles immediately; CM retains observation until Root adoption ACK, and always retains terminal collection/technical acceptance.


## E0 technical return: staging stopped, no selected exposure

Execution freeze was committed and pushed as `b3c7290fc`. Before staging, Root tightened
this command through DM: “If staging/admission fails, preserve exact failure and stop the
affected action without retry.” This superseded the earlier ordinary staging-repair allowance.

The remote availability read was `git -C /home/wu/projects/HMASD cat-file -t
faf786e135b3f55e535c898e17e646dcc341bdec`. The partial clone automatically spawned
`git -c fetch.negotiationAlgorithm=noop fetch origin --no-tags --no-write-fetch-head
--recurse-submodules=no --filter=blob:none --stdin`, then `git-remote-https` to the configured
GitHub origin. A process read observed the chain at 80 seconds elapsed; subsequent observation
still had no output after several minutes. CM terminated only the owned transport PID 2740217
after checking its command line. The enclosing read script then exited. This was an aborted
source-availability operation, not an accepted experiment. Root and DM were notified directly.

Observation limitation: that initial read script captured subprocess stdout only; Git's return
code and stderr were not printed or retained. Therefore no network/authentication root cause is
asserted. The observed facts are the automatic fetch, sustained pending state, explicit transport
termination, and failure to establish the exact source object's availability. Some Git objects may
have been transferred; no worktree or selected task was created. No retry, alternate bundle import,
model probe, admission or learner invocation followed the tightened stop.

Authoritative remote readback at **2026-09-07T14:45:09.457921+00:00**:

```json
{
  "worktree_exists": false,
  "handles": {
    "vspc1-service-allocation-b01-factor402-20260907": "not_found",
    "vspc1-service-allocation-b01-generic402-20260907": "not_found"
  }
}
```

Technical acceptance is limited to the frozen invocation record and confirmed absence of
selected execution. No resource receipt, run root, selected model, optimizer, checkpoint or
primary measurement exists from this assignment. Actual selected counts remain zero; no result
polarity follows. Prior source/card conformance remains unchanged. No experiment is live or
awaiting monitor adoption. Portfolio owns the next bounded staging/execution command through
Root; DM retains science. This return does not authorize a retry or change the fixed two-call
scientific object.


## P07-VSPC1-STAGE-REPAIR-01 continuation

Root relayed Portfolio's correction: the prior tightened stop is superseded; the original
execution command's reversible committed-Git staging repair authorization remains active.
The E0 observations above remain history, not a scientific invocation or result. No later
source-availability probe is commissioned. This continuation uses a task-scoped local named
Git ref at exact `faf786e135b3f55e535c898e17e646dcc341bdec`, a native Git bundle of committed
objects, SCP and remote import into the existing repository, followed by the specified detached
worktree. Ordinary reversible corrections within that route are authorized. Existing paths and
handles must not be overwritten; source, device, budgets and the two frozen calls remain unchanged.
After staging succeeds, execute FACTOR once and conditionally GENERIC once under the frozen
commands above; no scientific retry, pilot or extra call. The final required summary controls
technical continuation irrespective of magnitude. This entry corrects the pending status and
records the next action before launch while preserving every previous launch/absence fact.


### Committed-object staging completed

Created local named ref `refs/hmasd/vspc1-service-allocation-seed402-source-20260907`
at the exact source SHA and native Git bundle `temp/directions/vsp_c1/staging/
service_allocation_seed402_20260907/source.bundle` (94,182,352 bytes, complete history).
SCP transferred it into a newly created, previously absent `/home/wu/hmasd-inputs/
vspc1-service-allocation-seed402-20260907/source.bundle`. Remote `git bundle verify`
passed, bundle import advertised the exact SHA, and `git worktree add --detach` completed
at the frozen cwd. Remote `rev-parse HEAD` returned the complete accepted SHA and
`git status --short` was empty. No HTTPS source-availability probe or source edit occurred.
Both exact handles were `not_found` before staging; the target worktree was absent.
This entry is committed/pushed before the first FACTOR invocation. Execution uses the
unchanged frozen command above, with admission inside its cap.

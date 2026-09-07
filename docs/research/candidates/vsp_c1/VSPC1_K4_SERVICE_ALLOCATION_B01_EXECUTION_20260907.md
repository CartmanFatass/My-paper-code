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


### FACTOR terminal collection; conditional GENERIC frozen

Sole FACTOR accepted at 2026-09-07T14:49:25.313567Z, PID 2740531, initial status running,
tmux active. Full handle metadata went immediately to Root and DM. It finished before adoption
ACK, exit 0 at 14:49:31Z; same-handle terminal read confirmed tmux inactive. Complete external
wall **6.52 s**, user **3.83 s**, sys **0.47 s** (aggregate CPU **4.30 s**), below 2700 s.
Fresh receipt at 14:49:25.361128Z passed physical/effective **15,665,508,352 bytes**.
Main-process lifetime peak RSS **478,146,560 bytes**; scratch telemetry unmeasured.

Collected remote `FACTOR/summary.json`, `resource_admission.json` and supervisor `task.log`
(the latter saved locally as `FACTOR/supervisor.log`) under the declared runtime root.
Local `FACTOR/collection_checks.json` records technical collection. Checks passed: exact SHA,
arm/seed/372 parameters/CPU float32/one thread/batch16; 256 completed optimizer steps;
actual counts equal all declared counts (4096 training episodes, 1280 evaluation episodes,
258048 ticks, 569344 scalar Q predictions, 17 target copies, zero selection steps);
checkpoints exactly 0/64/128/192/256, 256 finite loss rows and 128 finite legally indexed
endpoint rows per period with saved means reproduced. Initial parameter norm 4.740192413330078;
final displacement 2.103224039077759. Required summary accepted independently of magnitude.
No scientific interpretation or extra execution followed this check.

The sole GENERIC command remains exactly as frozen above, now technically eligible. Its unit
time is still unmeasured; FACTOR's complete 6.52 s is adjacent same-host evidence for the common
counts, not a new numerical GENERIC guarantee. No extra performance assessment is selected.
Before GENERIC, this FACTOR collection entry is committed/pushed. Its adjacent fresh memory
admission and complete 2700 s cap remain mandatory; it alone runs the rule and paired publication.


## Final technical return: learner evidence retained; rule dependency incomplete

**The two authorized learner calls ran once each. FACTOR completed; GENERIC completed learning
and all five learner evaluations, then failed before rule evaluation and paired publication.**
The complete three-controller assignment is not accepted. The narrower saved learner contrast
is technically reportable under card §5; no rule-relative claim or scientific disposition follows.
No third call, retry, model probe, source edit or new environment interaction occurred.

### Terminal, resource and exposure facts

GENERIC was accepted at 2026-09-07T14:51:38.232184Z, PID 2740713, running/tmux active.
The full handle packet went immediately to Root and DM. Same-handle terminal read found
exit **1**, tmux inactive, terminal log time **14:51:43Z**. Root subsequently acknowledged
both terminal handles and tracking integration at `f5ef58763`; nothing remains live.

| Complete call | External wall s | User s | System s | Physical/effective admission bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| FACTOR | 6.52 | 3.83 | 0.47 | 15,665,508,352 | 478,146,560 |
| GENERIC | 4.84 | 3.90 | 0.38 | 15,667,646,464 | unmeasured |

Both adjacent same-node memory receipts passed >=4 GiB; GENERIC receipt time was
14:51:38.285929Z. Both complete calls were below their 2700-second caps. Summed invocation
wall is **11.36 s**, aggregate CPU **8.58 s**. Sequential elapsed from first acceptance to final
terminal log is approximately **138 s**, including the inter-call collection/commit interval;
this is distinct from machine time and excludes earlier staging/later intake. GENERIC failed
before final RSS/resource metadata, so that resource portion is `resources_unmeasured`.
Scratch telemetry is unmeasured for both; no scratch/resource claim is made.

Both learner summaries record status complete, 256 updates, 4096 training episodes,
196608 training ticks, 65536 renewal rows, 61440 nonterminal rows, 1280 evaluation episodes,
61440 evaluation ticks, 20480 evaluation decisions, 258048 total ticks, 569344 scalar Q
predictions, 17 target copies and zero selection steps. Combined actual exposure is **516096
ticks, 512 optimizer steps, 8192 training episodes, 2560 learner evaluation episodes and
1138688 scalar Q predictions**. Rule exposure is **zero**, so planned totals 528384 ticks
and 2816 evaluation episodes were not reached. GENERIC final parameter norm displacement
is 1.0033299922943115 from initial norm 4.280378341674805; FACTOR values are recorded above.

### Exact failure and coverage limitation

The retained GENERIC supervisor traceback ends at runner line 58 ->
`publish_comparison` -> reporting line 69:

```text
ValueError: Comparison requires FACTOR/GENERIC with the same fixed budget and seed
```

This message does **not** establish a scientific budget/seed difference. Direct source reading
shows `configuration()` puts `vars(budget)` into the summary, where frozen
`Budget.checkpoints` is tuple `(0,64,128,192,256)`. `run()` returns that in-memory summary.
Runner line 55 JSON-loads FACTOR, making its checkpoints a list; runner line 58 compares it
to the in-memory GENERIC tuple. `write_read()` returns decoded JSON but `publish()` discards
that return, so earlier writes do not normalize the GENERIC in-memory budget. The equality
check therefore fails before line 59 `evaluate_rule()`.

A local stdlib AST/literal check of the frozen Budget defaults and JSON operations confirmed
native tuple budget != decoded budget, and the JSON round trip equals **both** saved budgets.
Both saved budgets are identical. This check made no model, tape, environment or runner call.
Saved SHA/seed/arm/config/counts and finite indexed endpoints match the frozen quantities;
source review identifies no reward, information or training-budget alteration caused by this
publication-only failure. The required GENERIC summary is present and complete; no rule field
or remote paired_summary.json exists. No synthetic values were substituted.

The accepted publication fixture was insufficient at this boundary: its synthetic budgets
contain only seed/updates, omit checkpoints, and JSON-round-trip both inputs before comparison.
It tested arithmetic/publication contents but not the mixed loaded/in-memory production call.
No test or full-runner replay was performed after the failure. Source remains read-only under
this assignment; a later selected repair should cover this precise serialization boundary.

### Saved-array collection and narrower measurements

CM independently checked both JSON identities, CPU float32/one thread/batch16, 372/393 parameters,
all declared actual counts, exact checkpoint/target-copy clocks, all 256 finite loss rows,
finite initial norms/final movement, and 128 ordered endpoint episode slots per period. Native
returns are finite within [0,1]; endpoint means reproduce the saved final checkpoint. All original
endpoint rows, consequence fields, TD rows and checkpoints remain in the untouched summaries.

Post-collection arithmetic over those saved arrays (NumPy, no model/environment import) yields:

| Measurement | Period 2 | Period 6 | Equal-period mean |
| --- | ---: | ---: | ---: |
| FACTOR final J | 0.753092447917 | 0.764729817708 | 0.758911132812 |
| GENERIC final J | 0.751383463542 | 0.753417968750 | 0.752400716146 |
| FACTOR minus GENERIC | 0.001708984375 | 0.011311848958 | 0.006510416667 |
| FACTOR AUC | 0.755727132161 | 0.762715657552 | 0.759221394857 |
| GENERIC AUC | 0.754018147786 | 0.761698404948 | 0.757858276367 |
| FACTOR Final minus initial | 0.006754557292 | 0.014160156250 | 0.010457356771 |
| GENERIC Final minus initial | 0.000081380208 | 0.002441406250 | 0.001261393229 |

Conditional paired evaluation SE is **0.002109066043879126**, computed as
`0.5 * sqrt(var(diff_period2, ddof=1)/128 + var(diff_period6, ddof=1)/128)`.
This is evaluation noise for these fixed policies, not a training-population interval.
AUC is trapezoidal area over the five fixed updates divided by 256; no checkpoint selection.
No rule value, rule contrast, initial-relative-to-rule value or missing resource is inferred.

| Update | FACTOR period 2 | FACTOR period 6 | GENERIC period 2 | GENERIC period 6 |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.746337890625 | 0.750569661458 | 0.751302083333 | 0.750976562500 |
| 64 | 0.746337890625 | 0.750569661458 | 0.749837239583 | 0.775634765625 |
| 128 | 0.763264973958 | 0.767171223958 | 0.751302083333 | 0.753092447917 |
| 192 | 0.763590494792 | 0.775472005208 | 0.763590494792 | 0.765869140625 |
| 256 | 0.753092447917 | 0.764729817708 | 0.751383463542 | 0.753417968750 |

### Artifacts and return route

Remote raw roots remain at the frozen cwd plus `temp/directions/vsp_c1/exp/
k4_service_allocation_b01_seed402_20260907/{FACTOR,GENERIC}`. Each contains untouched
summary.json and resource_admission.json. Original supervisor logs remain in
`/home/wu/.agent-tasks/<exact-handle>/task.log`.

Collected copies are available in **C:/Projects/HMASD-worktrees/
cm-vspc1-service-allocation-exec402-20260907/temp/directions/vsp_c1/exp/
k4_service_allocation_b01_seed402_20260907/**: each arm's summary/receipt and supervisor.log;
FACTOR/collection_checks.json; and derived_learner_collection.json with indexed paired
differences, formulas' outputs, counts and the explicit narrower ceiling. Derived JSON is a
local post-collection artifact, not a replacement for the missing runner paired publication.
No raw artifact was overwritten. Git changes contain this record only; no source diff.

Delivered technical evidence goes to Root for integration, then DM scientific intake and
Portfolio. Remaining gap is the missing rule evaluation/three-controller publication. This
assignment authorizes no further invocation or source repair; Portfolio selects any next bounded
work through Root. Passing these collection checks accepts the narrower measurements' technical
conformance, not a scientific conclusion or completion of the missing dependency.

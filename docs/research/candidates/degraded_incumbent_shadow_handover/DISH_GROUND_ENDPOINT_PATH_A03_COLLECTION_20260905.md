# A03 paired trace technical collection

The unique ordered pair finished normally. Original summary, full per-tick trace, admission
and supervisor log were preserved and copied; no rerun or successor occurred. This record
separates technical conformance and raw counts from DM's scientific intake.

## Exact execution and artifact locations

Source `818b2566d1bac7cafcc71ed0bbb90b8abd1c6b65`, node wsl_4070, task
`dish_ground_endpoint_a03_seed11_pair_a1`, PID1664694. Exact command is frozen in
`DISH_GROUND_ENDPOINT_PATH_A03_CM_RETURN_20260905.md`; detached cwd
`/home/wu/hmasd-worktrees/dish-endpoint-a03-818b2566`.
Remote result root relative to cwd:
`temp/directions/degraded_incumbent_shadow_handover/exp/ground_endpoint_path_a03_20260905/a1/`.
Original `summary.json` and `trace.jsonl` are there; receipt sibling `a1_admission.json`.
Original supervisor log `/home/wu/.agent-tasks/dish_ground_endpoint_a03_seed11_pair_a1/task.log`.

Local copies have the same relative root under
`C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904/`, including `a1/task.log`.
Tracked byte-identical summary beside this record:
`DISH_GROUND_ENDPOINT_PATH_A03_SUMMARY_20260905.json`.
Full trace stays in the preserved local/remote runtime roots; it is not replaced by a summary.

| Original | Bytes | SHA256 |
|---|---:|---|
| summary.json |16719|09a69cc54de2a064d018916bedbb2b20a6c5c267cdca5d3456030fdf5fd537cf|
| trace.jsonl |39140340|f2c612928529f30b0566c8895cb40644071dd87c2db03b14cededd98e0dbf45d|
| a1_admission.json |504|9738a4fc2ef70985ea3e3c8f60d041021ba63770ce9442cd102e54f0ad3769c0|
| task.log |12749|554551010d2028ea36f0808e365517699e2a45adf9ab2658b57acaf8655c98e2|

Local summary/trace/receipt hashes match remote originals. Retained checkpoint post-run
SHA256 remains0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa,
2070711bytes; no checkpoint was emitted or altered.

## Exposure, actual stopping and resources

Original seed11, block0/TARGET_VISUAL_MASK/K8/speed4/slot0/initialowner0 coordinate
`DISH/RBHR/R06/EVALUATION_COORDINATE/0/CLAIM/TARGET_VISUAL_MASK/K8/0`.
Both hosts:1200 inspected/live/completed ticks, finalnative tick1200, terminal at
action1199 completion. No padding, early stop, replacement or source fork.
Two checkpoint-loaded policy/model initializations, zero new training transitions,
learner updates, optimizer initializations/steps. Each initial/final parameter norm
41.78517869974931; actual L2/relative movement0. Inherited exposure remains262144
training transitions,64updates,2048optimizer steps and relative movement0.42465718774783356.

Fresh adjacent admission assessed2026-09-05T11:13:50.543010Z; physical/effective each
13224554496bytes, minimum4294967296, both floor flags/passed=true, source/proc/meminfo.
Receipt mtime1788606830.5402262 precedes summary mtime1788606835.4400725; accepted
`admit-memory && runner` command supplies actual ordering, timestamps are ancillary.

| Timing | Literal | Candidate | Pair |
|---|---:|---:|---:|
| Actual runner wall seconds |1.9898064709996106|1.9763470540056005|3.969379171001492|
| Trace serialization/write seconds |0.34065982316678856|0.3447093938157195|included|
| Seconds/completed tick |0.0016581720591663423|0.0016469558783380005|0.0016539079879172884|
| Prospective projection seconds |88.47988453649668|88.47988453649668|176.95976907299337|
| Cap seconds |300|300|600|

Per-host wall includes library/model load, computation, trace serialization/write/flush;
pair wall includes input read and trace close but excludes final summary serialization.
Runner checks pair cap after summary publication too. Supervisor actual wall5s,
19:13:50→19:13:55+08:00, exit0. Observer uptime35s is distinct. PeakRSS365654016bytes,
resources_unmeasured=false. All measured bounds satisfied; this is no throughput claim.

## Observed stage counts

| Stage | Literal | Candidate | Candidate-minus-literal |
|---|---:|---:|---:|
| Camera U0 available |0|283|283|
| Camera U1 available |0|237|237|
| SOURCE adoption U0 |0|287|287|
| SOURCE adoption U1 |0|287|287|
| Common SOURCE |0|1199|1199|
| Snapshot delivery |0|331|331|
| Readiness delivery |0|634|634|
| Snapshot accepted ticks |0|915|915|
| Readiness accepted ticks |0|914|914|
| Version-ready |0|634|634|
| Renewal |150|150|0|
| Prepare proposal |103|119|16|
| Commit proposal |138|14|-124|
| Completion latch |1196|916|-280|
| Emitted intent |0|4|4|
| Emitted intent certificate |0|0|0|
| Origin-valid boundary |0|0|0|
| Legal owner/actuator transfer |0|0|0|
| Invalid commit delta |0|4|4|
| Relay emitted |0|1199|1199|
| Base adoption |0|1174|1174|
| Native service |0|299|299|
| Service before transfer |0|299|299|
| Service at/after transfer |0|0|0|
| Qualified promoted-owner packet service |0|0|0|

Both hosts remain owner0/actuator0/serviceepoch0. All token gap,dual owner,dual payload,
buffer clear,command slew breach,separation breach counts0. Literal reason histogram
0:1200; candidate0:1196,2:4. These are native codes, not a classified implementation defect.

Candidate first action ticks: camera0, SOURCE adoption/common1, relay1,base/service2,
prepare4,latch284,snapshot285,readiness286,commit/intent340,invalidcommit341.
No first tick exists for origin-valid, legal transfer or qualified service.
The summary's ordered labels are literal A03-ACCESS-NOT-RESTORED and candidate
A03-DOWNSTREAM-STAGE-GAP, absent stages[origin_valid,legal_transfer], earliest origin_valid.
DM applies the card independently. The299service ticks are not post-transfer consequences.

Literal final totalenergy287544.6125112445J, batteries[57177.0544096008,55278.33307915641],
minimumseparation288.19950003710176m. Candidate292276.03269612946J,
batteries[53733.26924937961,53990.69805449917],minimumseparation172.22221119029322m.
Final receiver SOURCE sequences candidate[389,389] with source ticks[389,389]; literal
SOURCE absent. Persisting possession is distinct from fresh receipt and service validity.

## Technical limits

No legal transfer or qualifying new-owner service occurred, so those nonzero runtime
paths remain unobserved on this fixture; synthetic attribution checks remain engineering
evidence only. All service and negative proposal-count differences remain visible.
The changed ground convention is a bundled host treatment, not a source-selection effect,
general policy-capacity finding, headroom estimate or repair of historical B01.

## Independent technical acceptance

The independent reviewer audited all 2,400 original trace rows with Python standard-library
JSON reads only. Ordered action ticks 0–1199, completion ticks 1–1200, state continuity,
finite numeric values, actor/normalized [1,4,54] and snapshot [1,18] shapes, arrivals,
count and first-clock reductions, reason histograms, service attribution, pair contrasts
and ordered summary branches agree. Literal overlap with retained A01 panel0 agrees:
150 renewal,103 prepare,138 commit,1196 completion-latch ticks. No data defect was found.
Four candidate intent origins340,364,388,596 carry certificate0; next-tick applications
record reason2 and invalid-commit increments. This does not identify a failed certificate
predicate or classify an implementation defect.

CM accepts the completed A03 measurement as technically complete under its frozen card.
Earlier focused verification at the same source passed5 tests in6.12s, including the one
actual toy paired publication path; no repeated suite, native/model invocation or new RNG
was used for collection. Scope remains127/435 non-test lines of orchestration (29.20%),
68 runner lines and207 test lines. Owner-review CLI at the clean collection boundary
returned[]. Scientific interpretation remains with DM.

## Read-only feasibility for a separately carded discriminator

All required inputs for a data-only reconstruction of the four emitted-origin certificate
calls are already in the original trace. This is a static field/clock mapping only:
no predicate arithmetic, new probe, test, native call or source edit was executed here.
At source818b2566, native/rbhr_r06_production_backend.cpp under the R06 candidate directory
lines356–358 define predictive_q95,mahalanobis_position and native_origin_certificate;
lines469–481 establish latch/warmup increment, command projection and certificate call
before motion at491. The A03 path_a03.py lines215–240 preserve the required fields.

- Read renewal from arrivals.renewal (also tied to prepared.countdown), and pre-motion
  positions from prepared.p. Prepared source_exists/source_sequence,terminal and
  handover_used supply the source/liveness predicates at these four no-transfer origins.
- Read completion.native.prepare_latched and warmup for the post-increment latch boundary,
  and completion.native.a for the post-projection command. These fields are unchanged
  between the certificate call and completion. Prepared.a is the earlier command;
  completion.native.p has already moved and is unsuitable for certificate separation.
- Read policy_output.raw_action,prediction_mean,prediction_covariance,service_q for the
  exact emitted policy inputs, and completion.native.intent_certificate/origin_tick for
  the recorded answer/identity. Field decimal serialization retains these finite binary64
  values; input precision remains inherited FP32 policy outputs widened by the native path.

A future reconstruction must preserve native clipping, binary64 operation order and the
20-step predictive-tail recurrence, then report each existing predicate against the recorded
certificate at the four fixed origins. This mapping supplies no computed predicate values,
new threshold, host intervention or scientific follow-up selection. No missing trace field
has been identified for that bounded reconstruction; cross-language numerical equivalence
would still require explicit treatment in its own prospective card/technical contract.

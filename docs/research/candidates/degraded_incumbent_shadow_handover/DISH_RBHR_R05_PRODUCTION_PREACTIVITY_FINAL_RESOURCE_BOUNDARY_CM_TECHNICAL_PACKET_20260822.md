# DISH RBHR r05 production-preactivity final resource-boundary CM packet

```text
document_kind=direction_production_preactivity_cm_technical_return
marker=CM_TO_OPERATIONAL_ROOT_DISH_RBHR_R05_PREACTIVITY_FINAL_RESOURCE_BOUNDARY_20260822_01
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260821-05
cm_owner=/root/dish_r05_preactivity_repair_cm
technical_acceptance=false
lease_readiness=false
science_bearing_ambiguity=none
question_relevant_output=none
```

## Conclusion

The unchanged-science production construction now has native, result-blind
evidence for every requested integration family except one master-dependent
resource fact:

- ABI-v3 C++20 hot-path serialization covers all eight fixed-width
  SOURCE/SERVICE_RELAY/STATE/SNAPSHOT/READINESS/COMMIT_INTENT/NOOP_INTENT/
  COMMIT_RESULT wire identities, registered float32 rounding, padding and
  first-four-SHA256-byte integrity. Native audit verifies all eight integrity
  fields and rejects tamper.
- An ordinary reset-to-application TEST trace reaches accepted SNAPSHOT and
  READINESS delivery, version match and one successful CAS on each of eight
  lanes. A separate transition probe verifies that the snapshot header arms
  the lock before SOURCE replacement, common lineage survives, locks release
  after application, one-owner/service-epoch/actuator authority move together,
  and recurrent promotion matches the frozen alpha law.
- The C++ path implements ordered first-false application reasons,
  next-tick lineage/version/owner/epoch/sequence/terminal/battery/separation/
  slew checks, actuator remap and charged result telemetry. The REAL/SHAM clone
  emits byte-identical COMMIT_RESULT telemetry digests.
- One complete 4,096-transition, four-epoch, eight-minibatch update consumes
  native float32-rounded accepted SNAPSHOT payloads, READINESS candidates,
  delivery masks, version matches and CAS/promotion records. It performs 32
  optimizer steps with finite loss/gradients and 224 accepted snapshot rows;
  there is no Python environment/rollout fallback.
- Sixteen complete 1,200-tick native TEST tapes feed the reducer/analyzer seam,
  which binds all 6,990 estimand identities to their production row family,
  24-block input, one 99,999-resample max-t family and fifteen branches.
- The thirteen actual TEST component byte streams remain create-only,
  digest-equal on resume and stale-parent rejecting. The benchmark measures
  CPU/wall, simultaneous parent-plus-eight-child RSS, temporary lifecycle bytes
  and parent/held-child process I/O deltas.

Production-preactivity acceptance cannot be made under the current ordering
fence. The exact number of rejected candidates before all 11,520 lowest-
qualifying accepted tapes is a deterministic function of the future blinded
scientific master and candidate-address stream. Current authority forbids
creating that master/identity/coordinate before a Root lease, while the same
boundary forbids issuing the lease before all six gates are established. No
additional authority-free TEST fixture can determine that master-specific
count.

The ordinary non-scientific fixture family exercised 48 scanner attempts and
1,080 eligibility opportunities but produced no eligible candidate. A
controlled clear-channel TEST fixture proves the native classifier and matched
50-tick assay execute—33 of 48 candidates are eligible and all 33 are
NEAR_ZERO—but intentionally has no production projection authority and cannot
establish POSITIVE/NEGATIVE acceptance frequency.

The measured scanner rate means the 560-core-hour ceiling can absorb at most
10,451,147 rejected candidates after the measured remainder, or a mean
907.217621527778 rejections per accepted slot. The literal 1,152,000,000-
attempt cap projects to 31,034.6793336794 core-hours, so it cannot serve as a
passing worst-case bound.

This is a concrete preactivity/lease sequencing incompatibility, not a
scientific contradiction, direction failure, gate failure, panel-shrink
request or evidence against DISH. No master, identity, coordinate, lease,
production model/checkpoint, production activity, question-relevant value,
provider action, science change or Git action occurred.

## Evidence

Test command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r05 -q --basetemp C:/Projects/HMASD/temp/pytest_dish_cpm_20260822_14
```

Observed: `43 passed in 50.32s`.

Benchmark:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m tools.benchmarks.benchmark_dish_rbhr_r05_production_preactivity --output runtime/benchmarks/dish_rbhr_r05_production_preactivity_final_boundary_20260822.json
```

SHA-256:
`a7be029df48dfd2fd295c2efa75d013fb09157b5c40160c70a5caa5b9811d2ff`.

```text
cpu_core_hours_lower_bound_excluding_rejected_candidates=278.447917844373
wall_hours_lower_bound_excluding_rejected_candidates=44.7681636558252
measured_eight_worker_speedup=6.21977528462107
simultaneous_parent_plus_eight_child_rss_gib=2.57534790039062
sum_of_individual_lifetime_peak_rss_gib=6.86845779418945
formula_scratch_gib=0.663042068481445
formula_durable_gib=0.330453045666218
formula_total_io_gib=34.0669612884521
actual_test_lifecycle_disk_bytes=529417
parent_process_read_bytes=25552246
parent_process_write_bytes=575709
held_children_read_bytes=159090752
held_children_write_bytes=32
max_rejected_candidates_before_cpu_gate=10451147
max_mean_rejected_per_accepted_slot_before_cpu_gate=907.217621527778
candidate_attempt_cap_worst_case_cpu_hours=31034.6793336794
high_gate_pass=false
high_gate_status=NOT_ESTABLISHED_CANDIDATE_REJECTION_DISTRIBUTION_PENDING
```

Current CPU, wall, RSS, scratch, durable and I/O facts are each below retained
`560 h / 110 h / 40 GiB / 120 GiB / 16 GiB / 400 GiB` ceilings. They cannot
establish the joint gates while the master-dependent scanner term is unbound.

## Smallest next authority

Engineering can continue unchanged only after the owner resolves the circular
ordering with one explicit object-scoped resource action. Two coherent forms
exist; neither is authorized by this packet:

1. authorize one scanner-only blinded master/identity under a bounded
   pre-lease probe that creates no model/checkpoint, runs no learned arm,
   exposes no assay values and retains only candidate counts plus accepted-tape
   identities; or
2. authorize a conditional scanner lease with an atomic fail-closed guard at
   10,451,147 cumulative rejections and the corresponding wall/RSS/I/O guards,
   before training/evaluation, returning a generator/resource fact if the
   complete accepted inventory has not formed.

Option 1 changes the no-master-before-lease fence. Option 2 changes the
no-lease-before-all-gates fence. Any Portfolio-authored fence change must be
relayed to this CM through the existing exact artifact bridge. Absent that
authority, only non-answering TEST refinement remains.

## Source identities

```text
native/rbhr_production_backend.cpp sha256=d13de80eb7d2b74e6935711ebf63d6bed6462106189ded22891b8b52c7381c35
production_backend.py sha256=490d9d702a038ed2102a89c238006ba4cbd06dc5e789cbf5fdfc2bfaeb3395c2
production_protocol.py sha256=efd888b855049c238ee29f92ad8ed49448d2ce4839fb5fe71daddb33bf73eb88
production_training.py sha256=30c3d74574f7432beb3097482089228045b04b4c4773d12ed940ac7e0dc42e04
production_analysis.py sha256=c2e3ea35050882ca93e4a2c420b6593306ee5a0b70465b2c4d1205068272588f
production_lifecycle.py sha256=cbd7169713e1bcd8957e7a6c21041f55fb508ac9f5bbd6577a0aad9dd231d7f2
production_preactivity.py sha256=76207ce8e1c8a6513de93604c77103410770d6aacc19845b23ba23a7ef2a8f4d
benchmark_dish_rbhr_r05_production_preactivity.py sha256=4abd9dd9de2e706a633aa9cd5576833ab24ef187e63a2ec0133dd0edfd1238c8
test_production_preactivity.py sha256=4197d8fc0bc84063b7ffbfc5fd2314543a833901315376d9ade5f89d87af54c9
```

## Decision-level return

```text
ROOT_CM_TO_PORTFOLIO_RETURN
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260821-05
cm_owner=/root/dish_r05_preactivity_repair_cm
technical_artifacts=docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R05_PRODUCTION_PREACTIVITY_FINAL_RESOURCE_BOUNDARY_CM_TECHNICAL_PACKET_20260822.md|runtime/benchmarks/dish_rbhr_r05_production_preactivity_final_boundary_20260822.json
observed_engineering_fact=Native serialized protocol/integrity, lineage-lock/application/CAS/recurrent-promotion/actuator-remap, byte-identical fork telemetry, native payload-connected 4096-transition trainer replay, native-row-connected 6990-estimand analyzer, real-byte lifecycle and full-chain CPU/wall/RSS/disk/I/O seams pass with 43 direction tests. Preactivity acceptance remains unavailable only because the future master controls rejected-candidate cost while the current fence forbids the master before a lease and the lease before all gates.
science_bearing_ambiguity=none
question_relevant_output=none
prospective_cost=Current lower bounds are 278.447917844373 CPU core-hours and 44.7681636558252 wall-hours; simultaneous RSS is 2.57534790039062 GiB; formula scratch/durable/I/O are 0.663042068481445/0.330453045666218/34.0669612884521 GiB. At 10.3110458000683 scanner attempts/s, at most 10,451,147 rejected candidates (mean 907.217621527778 per accepted slot) fit the retained CPU ceiling; the literal cap projects to 31,034.6793336794 CPU hours.
local_fence=No master/identity/coordinate/lease/production/partial-value/provider/Git action; controlled TEST scanner classifications have no production projection authority; no gate is declared passed while the master-dependent rejection term is unbound.
direction_continuation=The same DISH CM can install and validate either an owner-authorized scanner-only blinded pre-lease identity or an owner-authorized conditional scanner lease without changing science; absent that authority, only non-answering TEST refinement remains.
portfolio_question=Resolve the exact master-before-lease versus lease-before-gates circularity by authorizing either the scanner-only blinded pre-lease identity or the conditional guarded scanner lease; preserve the full panel and all retained ceilings.
applies_to=DISH-RBHR-R05 production-preactivity candidate-scanner resource gate only
does_not_imply=science revision|allocation change|direction stop|gate failure|intrinsic infeasibility|panel shrink|partial result|provider action|deployment|flight|Git
continuation_owner=Operational Root for resource authority and exact Portfolio relay; same DISH CM for unchanged-science implementation after the owner decision
root_decision_class=bounded resource-sequencing decision requiring exact Portfolio fence reconciliation
```

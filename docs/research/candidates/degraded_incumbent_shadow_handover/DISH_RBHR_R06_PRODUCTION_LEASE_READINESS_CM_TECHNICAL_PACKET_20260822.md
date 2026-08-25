# DISH RBHR r06 production lease-readiness CM packet — 2026-08-22

```text
document_kind=code_manager_production_lease_readiness
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
technical_disposition=SELF_AUDIT_WITHDRAWN|LEASE_REQUEST_NOT_ISSUABLE
science_bearing_ambiguity=none
ordinary_resource_gates=PASS
hard_resource_gates=PASS
identity_or_activity=false
```

The unchanged-science repair contains source surfaces for lease-bound native reset,
persistent 1,024-update model/optimizer state, sole-checkpoint lifecycle,
complete evaluation/mask-off and REAL/SHAM stage inventories, 6,990-estimand
inference, create-only complete-result firewall, atomic same-identity successor
slices and the exact resource-guarded CLI.

The integrated executor fixes the indivisible stage totals at population
11,520, training 122,880 updates, evaluation 115,200 episodes, fork 6,912 and
inference one complete family. It emits no partial scientific values. A slice
may return only complete, same-identity hard guard, or opaque slice completion.

Current tests: `8 passed in 3.99s`. A subsequent exact CLI self-audit found
that the CLI still depends on an absent concrete Root-lease loader and R06
production data plane. The earlier validator receipt at
`runtime/benchmarks/dish_rbhr_r06_full_panel_prelease_validation_ready_20260822.json`
(SHA-256 `84711f34fc92e356e2aad2fafe9775a23067a3e5ba7ff4b5a768568e0fe32956`)
is superseded and must not authorize a lease.

Current-byte benchmark:
`runtime/benchmarks/dish_rbhr_r06_production_lease_readiness_20260822.json`
(SHA-256 `b9aa40bccbf8ea45f245e76e67a42403f33cc0fce7d91d8a8f813e586b10b44e`).

```text
CPU=302.21825856801144h<=320h ordinary<=560h hard
wall=52.262984669761416h<=65h ordinary<=110h hard
RSS=2.5870590209960938GiB<=40GiB
scratch=0.6630420684814453GiB<=120GiB
durable=0.3304530456662178GiB<=16GiB
I/O=34.06696128845215GiB<=400GiB
workers<=8|cores<=8|GPU=0
```

Exact repaired surfaces:

```text
production_backend.py=213ef10269219ea909b0b0dd4001f6363f2f1e2215239f55c6b1cd7cba0f6b75
production_training.py=7e76e9e8ccd1e1ea641478081a1470849c1b211ce7252c7b073b20ab5fb98af3
production_training_engine.py=703220f02acf0348f2255c8aef49874672c99990497e89c30cd5df02bce05755
production_lifecycle.py=e37222ae8ac44ed99dc001172641fff004ff4637ba677bc24326dc71c85249fa
production_inference.py=3b947c99e7a52240213b4e7eb96c201e9b9fcd90c55f30ed72d1ec72d4501ee7
production_full_panel.py=584af36b3e0adc5db3456bd82e8dd59287e7aa823ff27ed1230813803630286f
run_dish_rbhr_r06_full_panel.py=17a48056c368f7ebec177851e755964504f88955098702c48451872f8bbd155e
```

```text
observed_fact=Resource projections pass and orchestration surfaces exist, but the exact CLI has no concrete lease loader/data plane and therefore is not executable.
local_action_fence=No master/identity/coordinate or panel activity until Operational Root issues the exact byte-bound lease.
does_not_imply=Lease issuance|empirical result|partial interpretation|R05 action|provider|Git.
continuation_owner=Operational Root for exact lease; same DISH CM for one identity and the indivisible panel after validation.
root_decision_class=PRELEASE_TECHNICAL_INCOMPATIBILITY|NO_LEASE_ISSUANCE.
```

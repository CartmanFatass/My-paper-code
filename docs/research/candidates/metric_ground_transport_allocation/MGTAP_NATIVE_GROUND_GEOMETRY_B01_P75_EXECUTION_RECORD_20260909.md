# MGTAP B01 P75 technical execution record - 2026-09-09

P75 execution task at main 4a20de760 authorizes this batch. Source is fixed at
4f65eefb1b15e44b42d694376630fba0c230cc6c; production source is unchanged.
CM /root/cm_mgtap_p72_repair is sole executor and observer through collection.
Original DM /root/dm_mgtap_p51_geometry_question receives scientific intake
through Root. Authoring checkout is dm-n5-continue-20260904, codex/mgtap.

Per-arm projection: P74 analog REL148.267066867s + unknown delta_REL,
DENSE141.371892048s + unknown delta_DENSE, pair289.638958915s plus deltas.
Design caps remain1800s/complete arm and3600s/pair. This is a forecast, not an
upper bound. No calibration, pilot, smoke, retry, replacement or new arm.
Post-learner coverage: accepted P72 changed-path/publication/aggregate checks
and independent review are reused. Native publication and runtime remain to
be observed; no duplicate fixture is selected.

Exact LF inputs are p75_execution_inputs/run_8201.sh, run_8202.sh and aggregate.sh.
They bind the P74 cwd, node wsl_4070, configured interpreter and source revision.
Run8201 then8202, at most one accepted supervisor submission per master, fresh
joined physical/effective >=4GiB admission each. H remains diagnostic only.
Signed outcomes do not gate the second master. Aggregate is existing offline
publication, measured separately. No source changes or extra evaluations.

Pre-staging reconciliation: both exact handles returned not_found, and the
specified detached remote worktree was absent. Local declared source comparison
against fixed4f65eefb1 was empty. Input publication precedes remote staging.
No scientific invocation had been accepted at this record's preparation.

Pending: exact-SHA source/input staging, syntax/byte verification, single native
submissions, observation, complete collection and technical acceptance. Remote
source checkout/evidence will be retained until Root's integration/cleanup event.

## Staging and first accepted handle

Published inputs7990ff5b0 were staged with matching SHA-256:
run_8201.sh=8d13770130c7e2d9ff16d87117b9c74f91f9cb529081d5a0d4e0bdbf9b478997;
run_8202.sh=29c7d7fc627dd6076e8330adce32f345f01869a18cc5b4e9397142a8cb818122;
aggregate.sh=b8161087d451c03bb6ed0a56e277bd0a63a7b5bbc9a5cf90e34f9d0a62e621ed.
Remote HEAD is fixed4f65eefb1; declared source diff is empty and all staged
wrappers pass bash -n. Retrieval required the configured zsh -lic network
shell; two stalled plain-shell retrieval checks were terminated before staging
completed. This was source retrieval, not a scientific submission or retry.

Master8201 was accepted once as
mgtap-b01-8201-4f65eefb1b15e44b42d694376630fba0c230cc6c,
supervisor PID3034957. First observation: running, joined memory admission
passed, effective available15635890176 bytes and physical floor passed.
Actual task log and admission are collected at terminal state. Master8202 is
not yet submitted. Sole observer remains /root/cm_mgtap_p72_repair.

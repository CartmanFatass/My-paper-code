# FSD native renewal A01 — P21 technical acceptance

## G terminal collection — 2026-09-07

Accepted handle `fsd_native_a01_p21_G_01770d8dd`, node `hmasd-wsl-node`, exact source
`01770d8dd6bb59460667efa26e3d94677e65ab37`; cwd
`/home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd`.
The same CM collected the terminal artifacts without new host/model calls. Supervisor
status read directly: finished, exit0, pid2758493, tmux inactive. Admission physical and
effective available memory were each15,659,601,920 bytes and both floors passed.
Runner final JSON: complete, failure null, complete_wall_seconds0.24978586402721703,
cap_breached false. Outer time: elapsed_seconds0.27, peak_rss_kib37660, exit_status0.

The executed command had an unintended trailing carriage return at the transport boundary:
the retained supervisor runner.sh ends its command argument with `.../G"\r`. Read-only
`ls -lb` shows separate `G` and `G\r` directories. Admission/time are in `G`, while the
actual summary is `G\r/summary.json`. This is a concrete output-path deviation, not missing
numerical output or a changed host/policy. Root was notified before C continuation. Preserve
the original; put a byte-identical copy at intended `G/summary.json` before H reads it.
Strip trailing CR/LF at the command transport boundary for C/H. No rerun or source change
is needed or allocated; acceptance does not assert that normalization copy already occurred.

Collected local evidence root:
`C:/Projects/HMASD-worktrees/codex-fsd/temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/G/`:
`admission.json`, `process_time.txt`, `summary.json`, `task.log`, `exit_code`.
The local summary is copied from actual remote `G\r/summary.json`.
Remote supervisor originals remain at
`/home/wu/.agent-tasks/fsd_native_a01_p21_G_01770d8dd/`.

Read-only Python/NumPy checks (both exit0) confirmed original object/mode/G label,
launch/master770103/ordered IDs0–31, N6/K2/Z4/H400/Delta1/hazards(.02,.20),
32 completed episodes,12,800 scoring steps,76,800 agent observations,400 Greedy batches,
zero agent batches/model constructions/checkpoint loads/training starts/transitions/updates.
All required full/post return, eligibility, wrong-role, role-loss and applied-renewal arrays
contain32 finite entries. Losses equal wrong/(400*6) and wrong_post/(399*6); conditional
rates equal wrong/eligible or null. Internal counters and checkpoint/normalization/controller
seed/device/torch-thread metadata are null for G. Full/post applied-renew counts agree,
consistent with G's no-renew t0 convention. Existing source/review establishes the host and
scoring semantics; no additional simulation was performed for collection.

**Technical disposition:** G conforms as a completed native Greedy observation, with the
explicit path-transport deviation above. C's prewritten command in
[FSD_NATIVE_RENEWAL_CONTROL_A01_P21_ROOT_HANDOFF_20260907.md](FSD_NATIVE_RENEWAL_CONTROL_A01_P21_ROOT_HANDOFF_20260907.md)
may proceed once its transport strips CR/LF. The exact C name, launch SHA, admission,
checkpoint,180s cap and output remain unchanged. Root owns dispatch/observation and the
byte-preserving G path normalization; no C or H acceptance is claimed here. CM retains
technical acceptance of their terminal artifacts; DM retains scientific intake. This record
makes no checkpoint-conditioned H−C inference from G alone.

## C terminal collection — 2026-09-07

Accepted handle `fsd_native_a01_p21_C_01770d8dd`, same node/cwd/source. Direct supervisor
status: finished, exit0, pid2759485, tmux inactive. Admission physical/effective available
memory15,349,542,912 bytes, passed. Runner final JSON complete/failure null,
complete_wall_seconds19.358762927993666, cap_breached false. Outer time elapsed20.44 s,
peak RSS801204 KiB, exit0; supervisor duration21 s includes admission and is distinct.

Collected `C/{admission.json,process_time.txt,summary.json,task.log,exit_code}` under the same
local evidence parent as G; originals remain under the detached remote cwd and supervisor
`/home/wu/.agent-tasks/fsd_native_a01_p21_C_01770d8dd/`. No checkpoint was reopened for
collection. Read-only Python/NumPy conformance checks exited0: exact G/C common object/mode,
source/master/episode IDs/host;32 completed episodes,12,800 scoring steps,76,800 observations,
400 agent batches,zero Greedy batches,one actual model construction and checkpoint load,
zero training starts/transitions/optimizer steps. All required32-entry arrays are finite;
internal and applied renewal counts agree for C; full minus post internal count is6 in every
episode. Both full/post loss denominators and conditional wrong-role rates check directly.

The load report names the selected staged path/digest/size, constructor seed2,CPU/four threads;
strictly restored active modules are skill_coordinator,skill_discoverer,team_discriminator,
individual_discriminator. Both coordinator/discoverer ValueNorm mean,var,count stores are
present and float64; observation/state normalization remain disabled. The retained summary
contains their exact values. Source review and successful required-load path establish the
restoration behavior; expected digest labels do not independently certify staged bytes.
Root's original artifact staging remains the identity evidence; no new artifact load is
performed or claimed here.

A separate read-only remote `cmp` of original `G\r/summary.json` and intended
`G/summary.json` exited0, confirming Root's byte-preserving path correction before H.

**Technical disposition:** C conforms, and H's prewritten exact command may proceed with
fresh adjacent admission and transport CR/LF stripping. No new source,cap,sample or retry.
H remains responsible for its own independent load/trajectory and paired publication inside
180 s. Root was notified immediately, without waiting for this documentation commit. No
H−C result or full-panel acceptance is claimed until H's terminal artifacts are collected.

## H and complete-panel acceptance — 2026-09-07

Accepted handle `fsd_native_a01_p21_H_01770d8dd`, same node/cwd/source. Direct supervisor
status: finished, exit0, pid2760429, tmux inactive. Fresh admission physical/effective
available memory15,653,986,304 bytes, passed. Final runner JSON complete/failure null,
complete_wall_seconds17.1826299969689, cap_breached false. Outer time18.19 s,
peak RSS802072 KiB, exit0. Supervisor duration18 s is separately recorded.

Collected H admission/time/summary/task.log/exit_code in the same local evidence parent;
remote originals remain under the exact detached cwd and H supervisor directory. Local H
`summary.json` holds the primary complete panel and all raw32-episode outcomes. No additional
model/environment call, checkpoint load or scientific invocation occurred during collection.

Read-only Python/NumPy assertions exited0. H object/mode/SHA/master/IDs/host, selected-path
identity labels, CPU4/seed2, required four active modules and both ValueNorm stores match C.
H has32 completed episodes,12,800 scoring steps,76,800 observations,400 agent batches,
one construction/load and no training starts/transitions/optimizer steps. H's embedded G/C
summaries equal their collected original dictionaries exactly; embedded H equals its parent
base summary apart from the later wall-before-publication stamp, and contains no recursive
panel. All full/post native measurement arrays have32 finite entries. Both role losses and
conditional wrong rates match their definitions. H applied-renew counts equal G post-renew
counts per episode, and G full-renew counts plus6 at t0. Internal t0 renewal counts are6.
These counters accord with the reviewed public-mask intervention and retained internal D2.

All four paired32-entry difference vectors were recomputed from retained episode returns
and compared exactly; their means and sample standard errors (`ddof=1/sqrt(32)`) agree.
The panel totals are96 completed episodes,38,400 scoring steps,230,400 agent observations,
800 controller batches,400 Greedy batches,2 model constructions/loads,zero training starts,
training transitions and optimizer steps. Complete outer policy walls are G0.27 s,C20.44 s,
H18.19 s; sum38.90 s, within540 s, and each within180 s. This sum is not the study elapsed
critical path, which includes inter-policy staging/admission/observation gaps. No aggregate
CPU measurement is claimed. The publication lies inside H's measured invocation.

Descriptive numerical readback for DM intake, without selecting a scientific branch:

| Paired quantity | Mean | Sample standard error |
| --- | ---: | ---: |
| H−C full | 0.2693489583333334 | 0.007149877611049748 |
| H−C post | 0.2700240183792816 | 0.007167797103809271 |
| G−H full | 0.16611979166666646 | 0.0030677688051983718 |
| G−H post | 0.16402986633249772 | 0.0030754574488204237 |

H mean post wrong-role reward loss is0.1640298663324979. Full per-episode values remain in
the summaries; the table does not replace them or use agent steps as independent units.

**Technical disposition:** complete panel conforms to the frozen native observation contract,
with G's preserved/documented CR output-path transport deviation and verified byte-identical
normalization. No unresolved dependent technical gap was found. Artifact staging identity
still relies on Root's staged-byte record; successful load does not independently hash it.
CM supplied acceptance to Root and the DM immediately. DM now owns original conditional-A
reading, uncertainty/ceiling,brief/audit and any permitted next decision. No learning efficacy,
training-seed generality,UAV entry,automatic successor or extra invocation is inferred here.

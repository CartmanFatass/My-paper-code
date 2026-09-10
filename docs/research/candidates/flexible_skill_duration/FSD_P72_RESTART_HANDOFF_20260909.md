# FSD P72 — restart handoff, 2026-09-09

## Stop boundary and actual result

**STOPPED after the completed P72 technical batch and scientific intake.**
OWNER_DIRECT soft stop for restart, delivered by Root while CM was collecting
the already terminal I output: finish current collection/acceptance/intake,
publish this handoff, commit/push and remain stopped. Do not start a next arm,
seed, object, retry, resume or Pro request, including any previously routed one.
This changes execution state only; ACTIVE/HIGH and scientific family authority
remain with their existing owners. CM has returned and stopped; DM stops after
the final published return. No runtime observation transfer is needed.

The valid B/EXPLORE result is **opposite_sign**: I−D0 mean native J
−.035312725297886094, conditional endpoint SE.012523489942436556, one new
matched training pair. D0/I means.4854120288125866/.45009930351470057.
P70 remains−.049670563167111874. Two pair means give descriptive
−.04249164423249899 with sample SD.01015252452050656; finite endpoint noise
remains. This is two observed native losses, not stable superiority or broad
closure. P72 loses coverage but slightly improves quality/altitude cost;
stochastic training returns improve on rollouts2–5 while the final endpoint
loses. I has65761 training gap decisions and zero endpoint gap decisions.
The prospective P72 negative forecast is met; owner prediction not taken.

## Checkout, ownership and commits

Designated authoring checkout: `C:/Projects/HMASD-worktrees/codex-fsd`.
Branch/upstream: `codex/fsd` / `origin/codex/fsd`. Reuse this checkout on
restart; do not create a new task/stage branch. CM released the clean index
at its final return. Final publication uses explicit owned paths and an
immediate push. No tracked dirty paths are intended at the published boundary.
Ignored runtime artifacts, data-only DM analysis scratch and the previously
blocked test directories are retained; do not treat them as missing work.

| Purpose | Commit |
| --- | --- |
| Complete prior P70 intake/input | `52609ba8438836de9805014dc783e818010dcc06` |
| P72 card/preparation/handoff | `42693cbdafb3143d012e2b78e160bedca439fff4` |
| Accepted P72 scientific source | `08199a932671d9bacdbe4eb0bfebab38c37fca1f` |
| DM source acceptance | `f95ebcb037865bd0020dfc0e14b3e09302ba4562` |
| Literal D0/I inputs | `3b872c848ec4fa74ff1bcc7a7c70d9d6d47912df` |
| Actual staged source/input verification | `2f69cb0f685b1b01fff31353c9f0b3a1d9c8ff42` |
| D0 acceptance record | `98bb844236226e3e3da9d3a71cfcf684972b7611` |
| D0 terminal before I | `8de22c950c8dae3350b8c12a34b282555a3a60a4` |
| I acceptance record | `31e12dd65d33b1225a3459a8632d8a0bbff03c3b` |
| CM complete technical collection | `0ae90f0e31daa9d468844c5748a807c9e9bc1ada` |
| Exact owner-directed role config sync | `d1568d44003553dfef1f719d62070dc7c4bbf224` |

This handoff, result, intake, DM analysis, card outcome appendix, accepted
DIRECTION update, Chinese brief and audit are published together in the
subsequent intake commit. Recover its full SHA with
`git log -1 --format=%H -- docs/research/candidates/flexible_skill_duration/FSD_P72_RESTART_HANDOFF_20260909.md`;
the Root return supplies that same full publication SHA. Root integrates named
accepted commits that are not already present; the config bytes already exist
on main at owner commit3e3357c85 and should not be duplicated there.

The nine role config files were copied from3e3357c85 only after both processes
were terminal and the index released. Their TOMLs parse and model/effort values
are unchanged. Behavioral authorization continuity applied immediately to DM/CM;
no live config reload or change to accepted scientific source08199 is claimed.

## Original processes, artifacts and observer

Both handles are **finished/exit0**, collected and technically accepted:

| Arm | Handle | Start UTC | Terminal UTC |
| --- | --- | --- | --- |
| D0 | `fsd_uav_b02_p72_D0_08199a932` | 2026-09-09T06:30:06Z | 2026-09-09T06:37:58Z |
| I | `fsd_uav_b02_p72_I_08199a932` | 2026-09-09T06:40:19Z | 2026-09-09T07:01:57Z |

Node/access alias: `hmasd-wsl-node`. Exact detached cwd:
`/home/wu/hmasd-worktrees/fsd-uav-b02-p72-08199a932`.
Interpreter: `/home/wu/.venvs/hmasd/bin/python`; supervisor:
`/usr/local/bin/agent-task`. Each original status/command/log/PID/start/exit
record remains at `/home/wu/.agent-tasks/<handle>/`.
Remote staging `/home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908` retains original
LF inputs, adjacent admission and complete time files. Scientific outputs under
the cwd are `temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/{D0,I}`.
I read only its original B02 D0 summary. **No handle is live and no polling,
collection or submission remains pending.**

Sole observer/collector through terminal closeout:
`/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47`, now stopped.
Scientific owner/native return: `/root/dm_fsd_p47_resume`, parent `/root`.
No pending P72 Pro Send or accepted external review exists.

Local collected root:
`temp/directions/flexible_skill_duration/exp/uav_b02_p72_control_20260908`.
It contains `D0_evidence.tar`, `I_evidence.tar`, extracted nested scientific and
`.agent-tasks` paths, original admissions/time files and readbacks. Original
summary hashes are D0 `6d84eaf98151954e0ad21fab301123d5cf0b33cbc17ade05eb9f50de83f08891`,
I `ce88a406fee0f0eb2784af8650be74a458460df36ca04276f9b0ed2c14f95573`.
Archive hashes and exact literal payloads are in the technical record. These
paths support recovery/readback; they do not authorize replay.

DM data-only scratch:
`temp/directions/flexible_skill_duration/analysis/uav_b02_p72_dm_20260909`.
Its four-row CSV/tool summary and complete arithmetic are embedded in the
tracked DM analysis. Blocked scratch is retained at
`temp/directions/flexible_skill_duration/test/uav_b01_p69_source_20260908` and
`temp/directions/flexible_skill_duration/test/uav_b02_p72_binding_20260908`.
Automatic approval review rejected deletion as “blocked by policy”; no bypass
or new deletion attempt follows from the later configuration correction.

## Card, evidence and budget

- [Card §§2–6](FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md): unchanged .25/k10/five updates, training770603/evaluation780603, one final32-episode panel per arm, MEI.01 and fixed branches.
- [Technical evidence](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_TECHNICAL_EVIDENCE_20260908.md): source, checks/review, literal payloads, actual source bytes, admissions, terminal receipts, vectors and counts.
- [E0 result](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md) and [scientific intake](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_INTAKE_20260909.md): rule, bounded reading, alternative explanations, owner instructions and selected decisions.
- [DM analysis](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_DM_ANALYSIS_20260909.json), [Chinese brief](../../portfolio/owner/briefs/flexible_skill_duration/2026-09-09_FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72.md), [audit](../../portfolio/audit/2026-09-09.md) and [DIRECTION](DIRECTION.md): durable arithmetic, plain-language result and accepted science.

Consumed P72 execution allowance: exactly one accepted submission each;
80000 training transitions/160 episodes/10 updates,32000 scoring steps/64
endpoints,112000 environment steps,672000 agent-step observations,4 models/
2 starts/0 checkpoint loads,50040 optimizer calls. Full walls D0471.50s and
I1297.28s, sum1768.78s; aggregate CPU7016.85s; critical path1911s.
Original complete caps3600/18000/sum21600s passed. Unused cap time is
3128.50/16702.72/summed19831.22s, but remaining authorized submissions are
**D0:0, I:0**. No new runtime allocation remains; B objects have no C consumption
state. Source-check allowance used9.0115169s of300s; no §4 additions/§5 breach.

## Unfinished state and next step held for restart

No scientific or technical acceptance blocker remains. Continuous free-memory
telemetry, endpoint segment-duration measurements, tuned same-information
headroom and mechanism causality remain outside this completed bounded claim.
These do not require a rescue run. The retained scratch is a housekeeping
restriction, with original evidence intact.

The next unexecuted scientific step is **held for the owner's restart and a
new concrete supplied assignment**. The current recurrence discriminator is
answered; no third pair, threshold search, diagnosis, family closure, recast,
C promotion or Pro packet is selected. Root may integrate this completed
delivery and record the stopped state, then remains within the same soft stop.
On owner restart, read this handoff/current card-intake and apply any newer
owner review before resuming a supplied route. Do not infer a launch from old
argv or unused cap time. Portfolio retains the next-task decision.

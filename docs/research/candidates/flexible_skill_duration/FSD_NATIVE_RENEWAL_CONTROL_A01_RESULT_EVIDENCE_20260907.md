# FSD native-renewal control A01 — P21 result evidence

2026-09-07 owner date; executions on 2026-09-08 UTC. **Complete conditional A/RECON
measurement, 3/3 policies.** The selected checkpoint's H−C native return is
**+0.2693489583333334**, paired episode SE **0.007149877611049748**. Post-reset H−C
is **+0.2700240183792816**, while G−H remains **0.16402986633249772**. This is the
card's second branch: local gain and remaining service shortfall are both retained.
It is not an algorithm-effect, new-learning, training-seed or UAV result.

Definition and rule: `FSD_NATIVE_RENEWAL_CONTROL_A01_SCIENCE_CARD_20260907.md`,
sections 1–7, at launch `01770d8dd6bb59460667efa26e3d94677e65ab37`.
Technical collection: `FSD_NATIVE_RENEWAL_CONTROL_A01_P21_TECHNICAL_ACCEPTANCE_20260907.md`
at `fb46ddc656c58889d611fe919af0e3b87b7b3a06`. DM interpretation and decisions are in
`FSD_NATIVE_RENEWAL_CONTROL_A01_INTAKE_20260907.md`.

## Population, policies and uncertainty unit

One outcome-selected E3 large-seed2 final checkpoint, independently loaded for C and H;
master seed 770103, episode IDs 0–31, N6/K2, four zones/two regions, Bernoulli hazards
(.02, .20), H400, Delta1. C uses intact deterministic D2. H keeps its own internal D2,
actor, skills and recurrence, but applies the public regional change flag to host renewal
after the common forced-renew reset. G is the existing GreedyOnPublicState using the same
public information and native adapter, with its own plan and default no-renew reset.
Every policy receives its own resulting future observations. No new information is supplied.

The independent unit for the reported standard errors is the exogenous episode conditional
on this single selected artifact. Pairing uses the new common episode keys, not the old E3
C mean. Episodes, agents and time steps are not independent training replications. The
checkpoint was selected using prior outcomes; this measurement is not prospective confirmation.
All 32 outcomes per policy and all four paired vectors are retained, without filtering.

## Direct native-return observations

Means use all 32 episodes. Full return averages t=0…399; post-reset return averages t=1…399.
SE is the sample standard deviation with ddof=1 divided by sqrt(32).

| Policy | Full mean | Full SE | Post-reset mean | Post-reset SE |
| --- | ---: | ---: | ---: | ---: |
| C, intact D2 | 0.4540234375000001 | 0.007561459682117723 | 0.45516134085213045 | 0.007580410708889947 |
| H, public applied renewal | 0.7233723958333336 | 0.0036131096403474233 | 0.7251853592314120 | 0.003622165052979874 |
| G, public-state greedy | 0.8894921874999999 | 0.0014709675424572452 | 0.8892152255639098 | 0.001474654177901999 |

| Paired quantity | Mean | Paired SE | Minimum episode difference | Maximum episode difference | Positive / zero / negative episodes |
| --- | ---: | ---: | ---: | ---: | --- |
| H−C, full | 0.2693489583333334 | 0.007149877611049748 | 0.1912500000000008 | 0.3491666666666664 | 32 / 0 / 0 |
| H−C, post | 0.2700240183792816 | 0.007167797103809271 | 0.19172932330827153 | 0.3500417710944023 | 32 / 0 / 0 |
| G−H, full | 0.16611979166666646 | 0.0030677688051983718 | 0.12916666666666565 | 0.19708333333333283 | 32 / 0 / 0 |
| G−H, post | 0.16402986633249772 | 0.0030754574488204237 | 0.12698412698412587 | 0.19507101086048406 | 32 / 0 / 0 |

The .01 MEI is the card's descriptive reward scale, not a significance, equivalence or
competence test. Both the local H−C gain and remaining G−H shortfall are much larger than
that scale. All-positive episode signs describe this panel; they do not supply training-seed
robustness. No interval, test or new selection rule was introduced after observing the result.

## Service accounting, applied action and reset

Counts below pool the same 32 episodes; they are service opportunities, not statistical
replications. The raw summaries retain the corresponding per-episode arrays and null handling.

| Policy / window | KEEP & fresh | KEEP & fresh & wrong role | Internal renewals | Applied renewals |
| --- | ---: | ---: | ---: | ---: |
| C full | 41,462 | 6,593 | 18,615 | 18,615 |
| C post | 41,462 | 6,593 | 18,423 | 18,423 |
| H full | 68,121 | 12,566 | 18,206 | 8,679 |
| H post | 68,121 | 12,566 | 18,014 | 8,487 |
| G full | 68,313 | 0 | n/a | 8,487 |
| G post | 68,121 | 0 | n/a | 8,487 |

H's mean wrong-role reward-unit loss is **0.16361979166666665** full (SE
0.0030677688051983796) and **0.1640298663324979** post (SE 0.003075457448820431).
Post loss is `12566 / (32 × 399 × 6)` because Delta=1. H's pooled wrong-role rate among
eligible opportunities is **0.18446587689552413**; the mean of the 32 episode rates is
**0.18451058554622785**. There are no zero-eligible episodes. These two rate averages have
different weightings; neither is substituted for the primary reward comparison.

C's corresponding post wrong-role loss is 0.08606150793650794 and pooled rate
0.15901307221069896. H therefore improves total native return while retaining more eligible
wrong-role loss and a higher conditional wrong-role rate than C, on different endogenous
trajectories and opportunity sets. Those adverse quantities remain visible; they do not
identify a unique actor, recurrence or credit defect.

H and G have equal post applied-renewal counts in every episode; H has six additional
forced renewals at reset in every episode. C's internal/applied counts match; H's differ.
The source and technical checks establish mask application; counts alone do not prove the
full action tape. G scores 1 at reset and C/H score 0. The observed full/post relationships are
`(H−C)_full = (399/400)(H−C)_post` and
`(G−H)_full = (399/400)(G−H)_post + .0025`, within maximum arithmetic residuals
1.67e-16 and 1.12e-16 respectively. Thus the reset convention does not explain H−C.

Post G−H equals H's wrong-role reward-unit loss episode by episode to maximum absolute
arithmetic residual 1.12e-15. This is an accounting statement for this host and these sampled
trajectories: the competent public null takes the same observed post service opportunities
without wrong-role service loss. It is not causal localization of the residual or a universal
policy-class maximum. The new comparison supplies no tuned generic-baseline headroom record.

## Frozen rule applied verbatim

From card section 4, the complete selected table is:

| Complete trustworthy observation | Bounded reading and recommendation |
| --- | --- |
| H improves C, approaches G post-reset, and eligible wrong-role loss is small | This fixed controller can realize service on those altered trajectories. Retain native renewal as a concrete candidate for a separately specified bounded follow-up. |
| H improves C but retains G−H and wrong-role service loss | Report local gain and remaining service shortfall separately; withdraw a timing-only explanation of complete competence. Do not assign the residual to a unique mediator. |
| H is unchanged or worse | This selected actuator substitution supplies no reason for continued timing-only investment in this instance; the unselected learning family stays paused. Other checkpoints, independent B questions and the direction are not closed. |
| Resolution is limited or episode signs differ | Preserve the finite information and end at this bound. Do not equate nonsignificance with equality or add samples to obtain a sign. |

The second row applies. H improves C in all 32 paired episodes, while every post-reset G−H
difference and H wrong-role loss remains positive and well outside the .01 descriptive scale.
The first row's near-G/small-loss condition is not met. No algorithm-effect claim or automatic
successor follows. Card section 5's stop instruction is also retained verbatim:

> End at the complete panel and intake, or the first cap/dependent failure. No automatic retry,
> weight substitution, extra sample/reset, partial recombination, parallel replacement or cap
> extension. Record actual completed counts and any cap breach.

## Counts, receipts and actual cost

Scientific launch SHA: `01770d8dd6bb59460667efa26e3d94677e65ab37` for all three policies.
Root used the allocated G→C→H order on `hmasd-wsl-node` / configured `wsl_4070`, in
`/home/wu/hmasd-worktrees/fsd-native-renewal-a01-p21-01770d8dd`, with
`/home/wu/.venvs/hmasd/bin/python`, CPU/4 torch threads. The card pins the existing
Python 3.10.21 / torch 2.7.0+cu118 / NumPy 1.26.3 route. Learned networks/actions use float32;
existing host/reward accumulation remains float64. Literal commands are in
`FSD_NATIVE_RENEWAL_CONTROL_A01_P21_ROOT_HANDOFF_20260907.md` at
`407f11189a69561795cecabe951720a73c752e95`.

| Policy / accepted task suffix after `fsd_native_a01_p21_` | Admission UTC | Physical = effective available bytes | Complete runner wall s | Outer process wall s | Peak RSS KiB | Exit |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `G_01770d8dd` | 2026-09-08T04:14:54.836562Z | 15,659,601,920 | 0.24978586402721703 | 0.27 | 37,660 | 0 |
| `C_01770d8dd` | 2026-09-08T04:19:16.589243Z | 15,349,542,912 | 19.358762927993666 | 20.44 | 801,204 | 0 |
| `H_01770d8dd` | 2026-09-08T04:22:31.780432Z | 15,653,986,304 | 17.1826299969689 | 18.19 | 802,072 | 0 |

Each fresh admission exceeded 4,294,967,296 bytes and was joined immediately to its command.
Each complete policy process finished within 180 s, including its required setup/loading,
evaluation and publication. Summed outer process wall is **38.90 s** at .01 s display
resolution, below the 540 s sum; summed runner wall is 36.79117878898978 s. Outer wall includes
interpreter startup; the terminal runner log includes publication. Supervisor status age is
not execution duration. Study elapsed includes the gaps between launches and is not 38.90 s.
Aggregate CPU work and agent/review/transport usage are not measured by these receipts; this
is not total direction cost or a comparison with real-learning B cost. Wall and peak RSS are
measured; no missing-resource qualification is needed for these quantities.

Every policy completed 32 episodes, 12,800 environment scoring steps and 76,800 agent-step
observations. Total exposure is **3 scientific policy invocations; 96 episodes; 38,400 scoring
steps; 230,400 agent-step observations; 800 C/H agent.step batches; 400 G acts; 2 model
constructions and 2 checkpoint loads; 0 training starts, training transitions or optimizer
steps**. The 1,598 coordinator-batch value is the design maximum, not an instrumented actual
count. Existing constructor work is included despite zero learning updates. Historical
selected-checkpoint training exposure stays separate (card section 5); no new independent
training sample was created.

## Source, checkpoint and engineering conformance

Root's staging record, `FSD_NATIVE_RENEWAL_CONTROL_A01_P21_CHECKPOINT_STAGING_20260908.json`
at `2e0d0d6717db405d0aaf33d16027d8b944388399`, records the existing copy/verification command
result at 2026-09-08T04:28:44.0861740Z. Both the
card's local source and remote
`/home/wu/hmasd-inputs/fsd-native-renewal-a01-p21/large_d2_seed2/checkpoint_final.pt`
are 64,782,527 bytes with SHA256
`2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89`.
Staging copied bytes without unpickling; the two allocated C/H processes performed the loads.
This Root-observed identity record, not the runner's expected-digest label, grounds artifact
identity. DM read the receipt and did not repeat staging or load the checkpoint.

C/H each restored the four active modules: skill_coordinator, skill_discoverer,
team_discriminator and individual_discriminator. Disabled module fields are not missing
active weights. Both enabled coordinator/discoverer ValueNorm mean/var/count match in the
two summaries; observation/state normalization is disabled. Constructor seed2, evaluation
mode, one fresh reset per lane, independent C/H recurrence and H-only applied-mask replacement
meet the card. Technical acceptance establishes these implementation/runtime facts; successful
loading or tests alone are not the native-return result above.

The accepted implementation adds 342 runner lines and 296 focused test lines, 638 total,
within card/engineering-scope budgets. Existing 12-test/fixture acceptance and independent
review were reused; DM did not repeat them. No engineering-scope section 4 machinery, section
5 budget breach, new code, new CM assignment or scientific retry was added during intake.

One transport deviation is retained: G's accepted payload carried a trailing CR in its output
path, so the original summary was written under remote `G\r/summary.json`. Root preserved that
file and copied identical bytes to the intended G/summary.json before H. CM checked remote
`cmp` exit0 and H's embedded G/C dictionaries against the collected originals. No G relaunch,
new sample or repair to policy/source occurred. C/H payloads removed the transport CR/LF.
H's embedded intermediate publication clock (17.181062237999868 s) differs from its top-level
pre-publication clock (17.181433357996866 s); scientific arrays match. The terminal log and
external timing, not either intermediate value alone, establish the complete cap.

## Durable evidence and DM arithmetic

`native_renewal_control_a01_p21_20260907/{G,C,H}/` contains selected copies of each original
summary.json, admission.json, process_time.txt and exit_code, plus task.log bytes under the
descriptive filename task_log.txt. H/summary.json contains
the full paired panel and all rule-read episode/counter arrays. Original local artifacts remain
under the corresponding `temp/directions/flexible_skill_duration/exp/` root; original remote
outputs and supervisor records remain on the execution node. The G raw CR path is preserved.

| Collected summary | Bytes | SHA256 |
| --- | ---: | --- |
| G | 5,820 | `193fdf899bdb8a20bada0e4e663e80d38b16411c0e78bb006c709a0ec7bb9332` |
| C | 9,952 | `2744d5568720b2f089d0b876c1a683075afe080bd7abe6338c915b34b32d2625` |
| H / full panel | 50,714 | `a107d983d948a9b46acadcf00660966ad34033d8b77c551244e8d3db00e97a00` |

The adjacent `dm_analysis.json` records independently recomputed arithmetic: all four paired
vectors/means/SEs exactly match the published panel, return means and signed ranges use every
episode, loss/count/rate formulas agree, and admission/exit/complete-wall facts agree with the
raw receipts. Computation used NumPy float64 with the episode unit above; no resampling or
new evaluation. The one-off analysis invocation was
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_p21_20260907/dm_analyze_recorded_panel.py`.
It reads JSON/logs only. During preparation its handling of G's inapplicable internal-renew
null and H's intermediate publication clock was corrected; those analysis exceptions caused
no scientific invocation and changed no recorded output. No environment/model import was used.

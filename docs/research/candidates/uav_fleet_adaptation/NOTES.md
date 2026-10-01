# UAV fleet adaptation

## 2026-09-30 — B01 prospective N8 warm-start comparison

Native DM `/root/dm_fleet_adaptation`, assigned by Root on shared main. One study is selected:
can experience under deterministic transmitter management develop a useful native N8 learned
controller beyond ordinary additional N8 training and competent C_N/E? This is constructive
development of the retained H6/E capability, not a diagnosis of a missing-feedback defect,
an exact training resume, a new architecture, or a training-population claim.

### Evidence, explanation and the selected complete comparison

The published [fleet B01](../uav_fleet_transmission/NOTES.md#b01-complete-reading), source
`a2f62e613a12331ad380876a6c764f8a46a893ee`, result `6b51a962e2295b44ea2d79fba128a943e761c39b`,
establishes conditional N8 E capability: H6/E minus H6/all J +.096344 and service +6.235125,
both positive in all16 worlds. Yet H6/E minus C_N/E is J -.066155/service -2.995125.
N4 H6 loses mean service1.474375 under E, with concrete adverse worlds and immediate-versus-full
trajectory reversals. These facts restrict this purchase to N8 and require the strong ordinary
comparator; they do not identify a learned repair. H6 originally trained at N6, making additional
N8 experience a strong competing explanation for any gain.

Relevant published [RESEARCH topic3](https://github.com/CartmanFatass/My-paper-code/blob/b45d15745de100eb9209141ec8a81c8c82a5d148/docs/research/RESEARCH.md#3-marl-增加的是联合行为和信息结构)
requires eligibility/capacity, complete trajectories and conditional asset scope to remain separate.
Topic4 separates representation, finite learning and package usefulness. Their concrete effect is
to include A/E as the experience control, I/E as the actual parent, C_N/E as the use comparator,
and preserve service/J/tails/path/quality rather than credit mask-local scores or parameter movement
as a useful controller. No literature novelty is asserted. Root's completed independent Astra Max
selection review covers this actual comparison; its complete question/answer/disposition is being
published at `docs/research/archive/2026-09-30/RESEARCH-parallel-allocation.md` and will be read
before execution. No separate selection experiment or repeated review is introduced.

Conjecture: experience on the actual E-composed transition/reward/observation process can improve
subsequent motion and full native performance. Masking changes interference, assignment, discovery
and the policy's later recurrent history. The learning problem is the composed multi-agent system;
the intervention does not give actors a new mask input or additional public snapshots. The simplest
alternative is ordinary extra N8 training, and complete-use value must still face C_N/E. This
package comparison does not promise to isolate a feedback, representation or skill mechanism.

- Two warm-start fits from the exact retained final45 H6 modules and normalizers: A trains with
  all transmitters on; F trains with E active. Each512 complete H500 episodes,16 lanes,32
  rollout/update groups,256000 native team steps. Original architecture, objectives, ten-tick
  skill clock and latent Gaussian action convention remain unchanged.
- Four final endpoints on32 common fresh fixed-before-exposure worlds: unchanged I/E, A/E, F/E,
  C_N/E. Only the fixed final32 continuation endpoint; no intermediate evaluation, checkpoint
  selection, N4/SET cells, extra seeds, pilot fit or automatic extension. Evaluation128 episodes/
  64000 steps; total2 new fits/1152 episodes/576000 native steps. One continuation per condition
  from one selected parent supports conditional exploration, not inference over training seeds.
- Evaluation world IDs29316000..29316031; training IDs29317000..29317511, disjoint. Address
  `[260930,17,world_id,stream]`: stream1 users, stream2 eight-UAV positions, stream3 environment
  runtime. Member-major RandomState draws as the inherited fleet generator. Each rollout uses
  consecutive16 training worlds, identical across A/F. Fresh fit runtime seed29316101 for both
  arms, reset independently after construction/restoration. Eval runtime is world-addressed.
  Exact IDs/address had no match in candidate source/notebooks at declaration. Constructors,
  reset and diagnostics must not consume global fit RNG; retain reset digests. Sharing a seed
  is an exposure control, not independent replication.
- S1 static50 uniform users, N8, capacity10, original0dB/free-space native physics and H500.
  J=.7*served/50+.3*connected-quality-.1*(mean all-UAV height-50)/100; training scalar remains J/8.
  Silence does not remove physical vehicles, movement, height penalty or count scaling.
- Actor input remains local104; critic uses state133 plus team skills and critic hidden state;
  no central snapshot actor. Obs/state running normalization remains off; retained value
  normalization is allowed its original learning behavior. The checkpoint contains modules and
  normalizers only: Adam, buffers, recurrent/skill state, RNG and environments are fresh.
- Training raw FP32 Gaussian actions and raw log probabilities are stored; execution clips
  componentwise to[-1,1]. Deterministic evaluation uses mean then the same clip. Preserve this
  source-defined latent-action policy law; do not transplant a tanh density or diagnose it as a bug.
- At t%10==0 actor consumes old-mask feedback and samples once before E. E predicts one next
  position from the lawful quantized public state and actual clipped command; enumerate255
  nonempty masks, native J then service, retain old mask on exact tie then smallest mask. Apply
  before native step and hold10. Discard setter-generated refreshed feedback; collect the actual
  next observation/state/reward and retain it in ordinary replay. No second actor invocation.
- C_N/E retains the inherited old-mask rotating27-command/member coordinate pass each tick,
  public anchor only every10 ticks and model propagation between. One E choice follows motion
  at boundaries; no joint search or additional public refresh.

Primary contrast F/E−A/E; essential F/E−I/E and F/E−C_N/E; also report A/E−I/E and A/E−C_N/E
to separate ordinary continuation value. Report every signed world, quality/height, eligibility
and eligible-unserved counts, path, within-world service p05/minimum/zero runs, active-mask
exposure and changes. Paired world-bootstrap95% intervals (10000 draws, seed26093017) are
descriptive conditional on these fitted instances. No equivalence or default-deployment rule.
F improving A/I and competing with C retains a learned capability; F near A supports no
E-experience attribution or equivalence; F beating I but losing C retains a conditional increment
and C reference. No complete gain/adverse tails ends this recipe without generic unlearnability
or automatic mask-input repair. Independent result diagnosis will scrutinize the actual outcomes.

### Cost and L0 implementation scope

Declared algorithmic requests: F training512*50*255=6528000 E candidates; all four evaluation
endpoints32*4*50*255=1632000, total8160000. C_N motion32*500*8*27=3456000 requests. Record
actual scored/cache/geometry counts separately. PPO/coordinator/discriminator epochs, minibatch,
sample and replay multipliers are being reconstructed before launch; no rate is assumed free.
Historical H6 fit-time scaled anchor is about7713 seconds for both continuations, before E,
evaluation, reader and support; it is neither a bound nor a runtime quote. Actual engineering,
verification, queue, training, evaluation and reading costs remain unknown until measured.
Use configured wsl_4070 first after exact-source publication and fresh actual-node admission;
retain the original parent checkpoint in its current location and verify its23,073,626bytes /
SHA256 `98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343`.

L0: implement a direction-owned N8 warm-start collector with the above E hook, strict final45
module/normalizer restoration, fresh optimizers/buffers/runtime, fixed32 complete rollout groups,
actual optimizer/replay/transition counts and parameter movement, per-world native training
metrics and mask/action exposure, final checkpoint, and meaningful collection/replay checks.
Own `experiments/candidates/uav_fleet_adaptation/{host.py,training.py,__init__.py}` and matching
`tests/experiments/candidates/uav_fleet_adaptation/test_training.py`. DM retains the runner,
evaluation/reader, notebook, shared index and all Git mutation. Reuse the shared learner/PPO/GAE,
strict original checkpoint loader and suitable B18 audit helpers; no shared rewrite or old-file
edits. Implementer may read original sources and synthetic fixtures, chooses no new scientific
arm/seed/endpoint, launches nothing result-bearing and spawns no children.

Check restore identity; empty optimizers and new buffers/runtime; raw sample/logprob unchanged
and stored; old-mask action before E, actual masked next-feedback stored; original skill/reset
and terminal/truncation semantics; matched exogenous worlds and RNG isolation; finite real update
and nonzero optimizer/parameter movement on an explicitly synthetic short fixture, not study worlds.
Retain complete per-rollout loss/update/exposure records; compressed collection arrays sufficient
to inspect state/observation/action/mask/reward bindings and native episode summaries. Avoid
inventing exact-resume or exhaustive-replay claims. Full evaluation saved-data reading remains
DM-owned. Independent engineering review covers executable scientific meaning before launch.
Stop at this bounded behavior, report material interface/cost contradictions immediately and
preserve existing source/accepted work. No new authoring checkout or branch.

### Selection review read, actual optimizer multipliers and reader scope

Read the full independent response and Root disposition published at
`97927817dfc4b8c15e2e07f4284b6ec2a8df8a15` in the
[completed allocation review](../../archive/2026-09-30/RESEARCH-parallel-allocation.md).
It reconstructs the original positive/adverse fleet evidence, checks raw Gaussian storage and
warm-start semantics, retains ordinary additional N8 training and C/E as the strongest
alternatives, and recommends this exact two-fit/four-endpoint design. Adopted in full for
this question; `MATERIAL_DISSENT:no`. The independent user-waiting question is not a dependency.

The source sampler uses env×agent sequences, not only environment sequences. Each N8 group:
16*8*(500/10)=6400 length10 recurrent sequences; batch32 makes200 minibatches per epoch and
15epochs makes3000 actor AND3000 critic optimizer calls. Each32-group fit therefore expects
96000 actor and96000 critic calls, with30,720,000 agent-time sample presentations to each
objective. Across both fits those are192000 calls and61,440,000 presentations per objective.
This is32 outer rollout/update groups per fit, not32 fits. The old N6 record's45groups ×2250
calls/group=101250 independently agrees with the original recorded actor/critic counts.

The exact strict N8 factory also reconstructs the original final45 N8 panel configuration:
`batch_size=discriminator_batch_size=16000` (the old N6 training config used12000). This is
the inherited roster-dependent factory calculation, shared by A/F, not a new tuning choice.
Per group800 high-level decision rows with coordinator batch1280 and15epochs give15 calls;
8000 team-discriminator rows give15 calls;64000 individual rows give60 calls. Per fit these
are480 coordinator,480 team-discriminator and1920 individual-discriminator optimizer calls.
Sample presentations per fit:384000 high-level team rows (each carries eight agent decisions),
3840000 team-discriminator rows and30720000 individual-discriminator rows. All five original
optimizers remain active; losses/coefficients, noise, data/recurrent ordering, value normalization
and terminal-as-done/no-bootstrap handling remain inherited. Actual sampler yields, sample counts,
optimizer hooks and movement will be checked rather than credited from these expectations alone.

The implementation preserves compressed training collection arrays and all evaluation native
trajectories. The pure reader will verify complete inventories/hashes, original clip/reward/state/
local-feedback/native-physics bindings, E choices and C_N passes, terminal/reset/world matching,
metrics and actual update accounting. It does not rerun training, actors or every optimizer/GRU
state. Replaying saved E/C choices is verification cost, separately counted from the algorithm's
8160000 E and3456000 motion requests; no added environment episodes or fits. Full reader wall
and CPU will be reported alongside worker cost. The original N6 wall anchor omits the increased
N8 recurrent replay and is particularly approximate. No hard scientific wall stop is imposed.

## 2026-09-30 — implementation accepted for the fixed B01 comparison

Accepted the bounded Implementer's host/collector and its focused checks, then integrated the
direction-owned admission entry, fixed endpoint evaluation and complete saved-data reader.
No shared learner, old frozen loader, old world panel or control policy was modified. The
strict source loader reconstructs the original N8 final-panel model config and verifies all
parent modules/normalizers. Training retains original terminal-as-done/no-bootstrap semantics,
including source-style post-storage lane/runtime reset; this is not a time-limit repair.
Per-step collection and per-update accounting retain partial Python failures, with raw collection
saved before update; a failed fit remains a counted technical attempt rather than a negative
scientific result. There is no automatic continuation/retry path.

RNG detail now explicit: global Python/NumPy/Torch fit RNG is freshly seeded29316101 after
construction/restoration for each arm. The original factory's private rollout sampler is also
newly constructed, deriving seed12969983988895470261 from `[942201,0x484D4153,0]`; its state is
never restored from the parent or shared across fits. Both initial states are recorded and
compared. This retains the original factory's named stream while making the global sampling
reset explicit. The source config still records its historical360000 total_timesteps; original
LR, entropy and weight annealing are off, and the actual new exposure is fixed by the32-group
loop/recorded256000steps per arm. No extra group or policy selection is inferred from that field.

Independent read-only `hmasd-reviewer` `/root/dm_fleet_adaptation/engineering_review` inspected
the actual retained parent, old and new collector/store/recurrent/update interfaces, raw Gaussian
replay, old-mask actor-before-E ordering, masked next-feedback, fresh optimizers/runtime/private
RNG, terminal/reset handling, full H6 objectives and sampler counts, checkpoint/evaluation
isolation, admission/failure markers, and the complete reader. It reports no material finding
remaining. It ran all16 direction tests:16passed,0skipped,5.33seconds. My integrated run likewise
passed16 in5.93seconds. Coverage includes exact staged parent restoration and endpoint save/load,
real five-optimizer updates on two-lane synthetic20tick fixtures, raw action replay beyond[-1,1],
masked feedback/clock/reset checks, failed-store partial counts and full22tick unchanged-H6/E
trajectory equality against the old evaluator on an old world. Equality includes runtime digests
after matching the unused16-slot reset bookkeeping. No fresh final-panel policy was evaluated.
Existing Matplotlib/Pyparsing warnings are unrelated; no production fit or full production reader
has yet run, and exhaustive actor/GRU/optimizer replay is not claimed. I accept the implementation.

The remote canonical checkout's owned active row already matches current published main;
compute config and maintained launcher match local byte hashes. Its unrelated dirty files and
sparse selection were preserved. Fetch through configured `zsh -lic` succeeds, with the known
Git auto-GC bad-tree/repack warning; this warning is not a failed scientific operation. The
original remote parent checkpoint was reverified at the declared SHA; one23MB local temporary
copy is used by the exact-checkpoint tests and will be removed at cleanup. Actual result launch
still requires committed/published inputs and fresh destination memory/admission.

## 2026-09-30 — B01 a01 technical failure and bounded input correction

`b01_warmstart_a01`, source `bf452481d2b951fe4e484e70858704c21eec5ed8`, was admitted
on wsl_4070 at11:25:37.098UTC (14,211,506,176 available physical bytes;4GiB floor passed),
then exited1 at11:25:40.655UTC in `parent_loading`. Both runner1103084 and supervisor1103083
are absent; exit witness and launch/admission records agree. The sparse source snapshot
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/f25246d8c0cf47089df3ab90c14cdd6b`
lacked the historical `runs/agent_count_generalization/s1_action_law_b03_h6_clip_s942201/summary.json`
working file required by the frozen loader. Read-only inspection verified that the original Git
blob exists at that accepted HEAD,737415bytes, SHA256
`55a994c81f49a9b97b52efa4ddaea82579e1068ea3a7ddbd11c8b7645bf88921`; this is sparse working-file
absence, not a changed parent. The record has fits={}, episodes=[], and failure before agent
construction: zero new fits, native steps, updates or evaluation episodes. Self CPU3.036305s,
child user0.001089s, peakRSS417456KiB; acceptance-to-exit3.557210s is not a full preparation
wall-time measurement. Compact original records are retained under
[runs/uav_fleet_adaptation/b01_warmstart_a01](../../../../runs/uav_fleet_adaptation/b01_warmstart_a01/).
This is no evidence for or against adaptation. The observer's terminal event was drained,
consumed and observation stopped; no worker was restarted.

L0 correction: retain exactly that required metadata blob under owned
`experiments/candidates/uav_fleet_adaptation/inputs/<parent-tag>/summary.json`, pin its original
path/revision/hash/bytes, and call the unchanged strict frozen loader with that explicit
summary root. This source path is included by the existing sparse selection. The loader still
requires working bytes identical to Git HEAD, all original source contract fields and the exact
external checkpoint. No accepted snapshot, remote sparse selection, old loader, learner,
worlds, objective, sampler or scientific comparator changes. This single required input is
737415bytes (identical Git blob), not another copy of the historical study.

The new isolated Git-fixture check uses the real retained checkpoint: absent historical working
file loads the owned committed metadata; changed bytes fail the original hash pin; exact but
uncommitted bytes fail the loader's HEAD check. It passed1/1 in2.54s. Existing full integration
checks will run after this new input is committed, as required by the loader's actual contract.
Independent engineering review is checking the actual narrow diff. After review and exact-source
publication, explicitly select fresh attempt `b01_warmstart_a02` with the corrected source SHA
and fresh actual-node admission. This replaces no accepted work and does not use an automatic
retry. The scientific budget remains the declared two fits and576000 native steps, with zero
used by a01; all partial future exposure remains counted. No new scientific premise or selection
review is required for this input-path correction.

Correction accepted: the independent engineering reviewer inspected the actual diff and exact
owned input, independently passed the sparse-binding regression1/1 (no skip,1.73s), and found
no remaining material issue. After local input commit `6508ab45aa743f9caae031474aa2b455e62d9c0f`,
all17 direction tests passed in5.69s with no skips. This includes exact parent restoration and
old-evaluator parity under the new binding; only pre-existing deprecation warnings remain.
The fixed experiment is unchanged and ready for source publication and fresh a02 admission.

### Corrected a02 accepted and observed

Published input `a6bf357d85f5acb5053da169ecde74cf5f733b55`; native `b01_warmstart_a02`
accepted2026-09-30T11:35:14.252529Z on wsl_4070. Fresh admission measured14,200,680,448 available
bytes and passed. Native claim/operation
`/home/wu/projects/HMASD/.git/hmasd-admission/feece2a7968c70a07b352e505574f729d75c8a65d3985697e5dda9e9d6bdc0ff.json`;
output `/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b01_warmstart_a02`; source snapshot
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/2338e6fa78a341dbac70b199189dce9d`.
Kernel supervisor1104662 / runner1104663 have matching live PID/start identities and no exit
witness. Agent-task `fleet-adaptation-b01-a02` only launched the native detached operation;
its own exit0 is not study completion. Strict parent loading succeeded; first progress has A
fit started,8000 collected/stored steps,16episodes and one update attempt (not yet completed).
No evaluation result exists at this observation.

The earlier terminal observer was consumed/stopped; adding a02 required rearming the same
controller to clear stopped state, then adding the distinct accepted a02 status handle.
Controller generation4 now observes a02 with30s deterministic native-status probes and1500s
checkpoints; a01 remains terminal in its record. Native child stays active and drains/rearms
this handle through actual result reading; the known unsupported child queue wake is not
assumed to return an unloaded child. No worker was rebound, restarted or duplicated.

12:02UTC observation checkpoint: same a02 native identities running, no probe errors or exit.
A has112000 stored/collected steps,224episodes,13 completed update groups and update14 started;
measured fit wall1513.330s so far. Consumed generation4 checkpoint and rearmed generation5
against the same operation. This is collection progress, with no final evaluation/interpretation.

12:28UTC: same a02 running without observation errors. A216000 stored/collected steps,
432episodes,26 completed update groups and update27 started; fit wall2970.843s.
Consumed generation5 checkpoint and rearmed generation6; no new result endpoint exists.

12:53UTC: A completed exactly32 updates /256000 steps /512episodes in3669.032s; F is now
training and has completed7 groups /56000 steps /112episodes in857.170s. Same a02 native
operation is live with no observation errors. Consumed generation6 checkpoint and rearmed7.
Fit completion is not the four-endpoint read-result boundary; no interpretation is drawn.

13:19UTC: F160000 stored/collected steps /320episodes,19 completed updates with update20
started; last recorded fit wall2258.566s. Native a02 still running, no probe errors. Consumed
checkpoint generation7 and rearmed8 on the unchanged handle; final evaluation remains pending.

13:44UTC: F completed the declared32 updates /256000 steps /512episodes in3796.415s.
Both planned fits are technically complete; common final evaluation is now running. Native
operation remains consistent/live without probe errors. Consumed generation8 and rearmed9;
no added fit, policy selection or scientific interpretation is inferred from completion.

<a id="b01-complete-reading"></a>
## 2026-09-30 — B01 complete reading: a conditional J increment, no complete continuation gain

Same accepted a02 exited0 at2026-09-30T14:03:20.861777Z; both native identities are absent and
terminal records agree. The generation9 READY event was drained/consumed, generation10 then
stopped with no active observation or worker. Collected original compact outputs into
[runs/uav_fleet_adaptation/b01_warmstart_a02](../../../../runs/uav_fleet_adaptation/b01_warmstart_a02/).
Source remains `a6bf357d85f5acb5053da169ecde74cf5f733b55`; no added fit or evaluation occurred.

### Integrity, exposure and actual cost

Both fits completed32 groups /512 H500 episodes /256000 stored native steps. Both independently
restored the exact parent module/normalizer digest, empty Adam/buffers and matched fresh runtime;
reset geometry and initial observations match. Each has96000 actor AND96000 critic,480 coordinator,
480 team-discriminator and1920 individual-discriminator optimizer calls. Actor relative parameter
movement is.492419(A)/.489854(F); critic.499244/.517513 and all remaining objectives also move.
This establishes executed learning, not useful learning. All128 final episodes /64000 evaluation
steps completed with no optimizer calls or parameter/normalizer mutation in evaluation. Total
new exposure is2fits /1152 episodes /576000 native steps; a01 adds zero scientific exposure.

The complete saved-data reader verified577152 native physics snapshots across all576000 steps,
state/local feedback, raw-Gaussian execution clipping, native reward/J-over-N, E choices/C_N
passes, matched inventories and sampler/optimizer accounting. It does not replay actors, GRUs
or optimizer arithmetic. Summary SHA256 `79ac154d39df2bb9a44221e8bbf23ae972ac5b2c45e1d5339a4dc95eb65663c6`
(333817bytes); original reading SHA256 `8cb3aefbbb64c56836aab81a1bc3dbb4d779dea1334580cf10cb34f049483d30`
(1579701bytes). Complete original signed world comparisons and training metrics are preserved
there; no world was dropped or chosen after exposure.

A fit wall3669.032s /CPU14768.951s; F3796.415s /14624.910s. Entire run_study worker wall7845.122s
/CPU30459.928s, plus saved-data reader709.813s /730.348s. Total run_study8555.006 monotonic wall
seconds /31190.348 process CPU seconds; this scope excludes admission/imports. Process-lifetime
peakRSS3718912KiB, including preceding arms and reader, is not a per-stage peak. Native
acceptance-to-exit UTC span8886.609s is recorded separately; the difference from monotonic scope
is not assigned an unmeasured overhead cause. The technical a01 adds3.036305 self CPU seconds
and its separately recorded launch/support cost. Engineering/review effort is not priced by
these worker timers.

Worker requests:6528000 E candidates during F training plus1632000 in evaluation =8160000;
C_N evaluation3456000 motion requests,2164508 scored and1291492 exact-cache hits. Full reader
independently repeats these requests: another8160000 E and3456000 motion, with no new episodes.
The frozen reading's `worker_and_reader_*_requests` values denote the matched count **for each**
side, not their sum: combined worker+reader requests are16320000 E and6912000 motion. This
clarification preserves the original record and avoids understating validation cost.

### Fixed complete-panel outcomes

I is the unchanged parent; A is all-on continuation; F is E-active continuation. Every endpoint
here includes E. J is native J, service is mean users served per tick, path is meters/UAV overH500.

| Endpoint | J | Service | Quality | Mean height(m) | Path(m/UAV) | Within-world service p05 | Active mean | Mask switches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| I/E | .557700 | 36.657188 | .218310 | 70.993303 | 14124.524 | 33.559375 | 4.256250 | 12.562500 |
| A/E | .542012 | 36.161562 | .208605 | 76.831405 | 21622.365 | 33.059375 | 4.332500 | 23.593750 |
| F/E | .552370 | 36.048063 | .218796 | 67.941450 | 20957.516 | 32.965625 | 4.215625 | 20.437500 |
| C_N/E | .610048 | 38.770750 | .224466 | 50.082523 | 250.637 | 38.812500 | 4.179375 | 1.437500 |

Intervals below are the frozen10000 paired-world bootstrap95% descriptions, conditional on
one selected parent and one continuation per condition. They are not training-seed intervals,
equivalence tests or a new confirmation/adoption rule.

| Contrast | Mean ΔJ [interval] | J positive/negative worlds | Mean Δservice [interval] | Service positive/negative worlds |
| --- | --- | --- | --- | --- |
| F/E−A/E | +.010358 [.003208,.017127] | 25/7 | −.113500 [−.666775,.419833] | 13/19 |
| F/E−I/E | −.005330 [−.012414,.001470] | 12/20 | −.609125 [−1.109023,−.128748] | 8/24 |
| F/E−C_N/E | −.057678 [−.070029,−.044230] | 3/29 | −2.722687 [−3.676753,−1.686614] | 5/27 |
| A/E−I/E | −.015688 [−.021838,−.009206] | 4/28 | −.495625 [−.943381,−.032936] | 11/21 |
| A/E−C_N/E | −.068036 [−.081078,−.054170] | 2/30 | −2.609188 [−3.649253,−1.525998] | 7/25 |
| I/E−C_N/E | −.052347 [−.065789,−.038674] | 4/28 | −2.113562 [−3.182423,−1.013734] | 9/23 |

F−A native-J arithmetic is service−.001589 plus quality+.003057291 plus reduced height
penalty+.008889956 =+.010358247. Height is lower in all32 worlds; this is a legitimate term of
the declared native objective, not dismissed as a proxy. It is a component identity rather than
identification of a learned altitude, feedback or interference mechanism. F−I gains.003051854
from lower height and.000145644 from quality but loses.008527750 through service. Both fits
therefore change behavior substantially while failing to improve mean service over I/E; A/E's
J decline makes the positive F−A contrast insufficient for a useful full continuation gain.

F−I has.1834375 more ineligible users and.4256875 more eligible-unserved users per tick;
their sum gives the.609125 service loss. F−C has1.1685625 more ineligible and1.554125 more
eligible-unserved. These after-trajectory identities do not identify causes or bound learning.
F−I path increases6832.992m/UAV [6514.744,7147.531] in all32 worlds; service p05−.593750 and
minimum−.750000 have intervals crossing zero. F−C service p05−5.846875 and minimum−3.218750
remain adverse. All arms have zero zero-service ticks/zero-run length. These metrics do not
assert every individual user's continuity or a physical flight-energy model.

Concrete adverse worlds remain:29316001 F−A J−.042488/service−4.376;29316025 F−I J−.048292;
29316016 F−I service−3.462 and F−C J−.104446;29316001 F−C service−6.466. Positive worlds also
remain:29316029 F−A J+.050148/service+3.400;29316023 F−I J+.051224/service+3.360;29316015 F−C
J+.058789/service+6.950. No retrospective world-specific gate is chosen.

Measured evaluation wall/CPU seconds over32 episodes: I/E75.090/300.446, A/E75.848/301.287,
F/E76.253/303.762, C_N/E148.946/156.135. Neural CPU includes the fixed four-thread kernels;
C_N is mostly serial. Thus C_N's stronger mean service/J and much shorter native paths do not
imply measured wall dominance; fixed policy amortization trades online wall against CPU and
training cost. No deadline-bound or physical deployment claim was tested.

### Working explanation and independent diagnosis pending

The primary program contrast retains a conditional native-J advantage from E-active experience
relative to all-on continuation. The desired complete native improvement beyond the unchanged
parent and C_N/E did not appear in this bounded recipe. Ordinary extra N8 exposure alone also
did not fix the gap. The prior N8 management capability and N4 adverses stay intact; neither
representation impossibility, generic unlearnability nor a missing-feedback defect follows.
Warm-start stability, five-objective finite optimization and training/deployment behavior remain
unidentified alternatives rather than invitations to automatic repairs. The comparison can
change our continuation judgment without explaining all of those alternatives.

The evidence supports ending unchanged warm-start investment while preserving the positive
F−A component and original I/E/C_N/E capabilities. Independent ResearchCritic
`/root/dm_fleet_adaptation/result_diagnosis` has the original prospective design, original
positive/adverse parent study, actual full new records and current shared background in a
separate context. Its result and disposition will be appended before final route/publication
closure; no follow-on experiment or broader question has been selected.

### Durable evidence and source-snapshot reclamation

Compact original a02 summary/reading/config/native records plus the full read interpretation
were published at `2e0cbc39087f5697789238e501a5508683ba200f`. Unique bulk remains at the configured
wsl_4070 durable canonical output
`/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b01_warmstart_a02/` (SSH alias
`hmasd-wsl-node`), outside the disposable source snapshot. Fresh post-run byte/hash verification
passed every bound file:64 training NPZ1654993937logical bytes;128 evaluation NPZ128109581bytes;
128 decision gz36700130bytes; two endpoint checkpoints46147252bytes; two full fit summaries
34367636bytes. All individual identities remain in the original summary/fit records. No second
raw/checkpoint copy was created; the original parent remains in its existing retained location.

Large A/F summaries are bulk, not rewritten or force-added to Git. A/summary.json:7218823bytes,
SHA256 `1ff34917f6df591e82cb7847596637bffcb5b14106fd79c6ed28a58d60b3ae6f`; F/summary.json:
27148813bytes, SHA256 `e04302708b843964d35e4e16c6f3746b532299f16796ac0c23d856d88ac3c2f3`.
The compact committed summary points to these same identities and endpoint hashes. Local
collected copies were verified identical to the durable originals and are temporary review copies.
The retained raw supports the complete physics/feedback/action/mask read and adverse trajectories;
endpoints preserve the actual evaluated fitted instances. Remote a01 failed-operation records
also remain intact.

Exact snapshot preview initially refused both a01/a02 because `/proc/660/cwd` was not readable
(`Permission denied`; offered `--sudo-process-scan`). The documented option used existing
passwordless sudo for the read-only process scan only; re-preview confirmed both snapshots
eligible with durable Git reachability, terminal native identities and no live process/source
consumer. Under the shared Git writer lock, the supported collector then removed exactly:

- `/home/wu/projects/HMASD/.git/hmasd-launch-sources/f25246d8c0cf47089df3ab90c14cdd6b`
  (807849984 allocated bytes) and its same-ID `.git/worktrees/` registration(3543040bytes).
- `/home/wu/projects/HMASD/.git/hmasd-launch-sources/2338e6fa78a341dbac70b199189dce9d`
  (808603648 allocated bytes) and its same-ID `.git/worktrees/` registration(3543040bytes).

All four exact targets were checked absent afterward:1623539712 allocated bytes reclaimed
on wsl_4070. Claims, manifests, exit witnesses, durable output and canonical authoring checkout
were preserved. No archive, whole-tree backup, source relocation or Git-object reclamation is
claimed. The initial process-inspection refusal is resolved; it is not a remaining tool blocker.
Local temporary-copy/cache cleanup follows completion of their active review consumer.

### Independent scientific diagnosis and resolved disposition

Read the complete separate-context ResearchCritic response from
`/root/dm_fleet_adaptation/result_diagnosis`. The Reviewer reconstructed the frozen contract
and actual records before reading the allocation advice and this DM interpretation; no DM/Root
conversation was inherited. It independently checked all aggregate and signed world differences,
all102 frozen bootstrap intervals, actual fit/sample/update totals, matched resets, source/config
and frozen-evaluation records, source/endpoint hashes and a01 failure. It directly reconstructed
metrics/motion/clipping/masks/world/reward bindings for20 positive/adverse evaluation trajectories,
plus first-group raw collection for both fits, and recomputed consequential prior fleet contrasts.
It did not replay actors, GRUs, optimizer arithmetic or every E/C search; the completed full
reader and engineering review supply their declared, narrower coverage. No discrepancy emerged.

Recommendation, adopted: **stop the unchanged warm-start recipe; retain the conditional F−A
native-J improvement and existing I/E and C_N/E capabilities. MATERIAL_DISSENT:no.** The J
advantage is legitimate, and its component arithmetic does not identify a causal mediator.
F masks were actually active throughout collection (mean4.234727 versus A's8); all five
optimizer streams and substantial parameter changes rule out nonactivation or an unchanged
actor as the explanation. The training curves establish neither convergence nor a prediction
that more of this recipe will repair the endpoint. A/E's deterioration is a consequential
simpler comparison: favorable F−A does not establish useful development from I/E. Optimizer
reset, multiobjective optimization, sampling-versus-deterministic deployment and representation
remain unseparated possibilities, not automatic repair tasks. The native lower-height benefit
is retained even though complete service performance did not improve.

The Reviewer retained the strongest objection to stopping: genuine positive complete-world
witnesses and F's conditional J signal remain, and C_N/E is neither an upper bound nor uniformly
superior. Those exceptions give no prospective selection rule. Prior N8 management opportunity,
its service-tail capability and N4 harms survive this result. The changed judgment is that
useful management opportunity did not automatically become useful additional learning under
this inherited finite recipe. The broader constructive learning question stays open; no
unlearnability, pure-feedback mechanism or universal ordinary-controller superiority is claimed.

Choice among continuations: more fixed-policy worlds only refine the current conditional
estimates. Another matched A/F pair with I/E and C_N/E on a fresh panel would buy another576000
native steps at roughly this study's2.4-hour measured wall cost, with source fit variation still
requiring careful scope. Repeating F>A while both remain below I/C would leave today's investment
choice unchanged; a reversal would weaken recurrence; genuine complete gains over own parent
and competent comparison would change the constructive conclusion. Replication is not owed
merely because training n=1, and there is no supported repair prediction worth that purchase
now. I accept the Reviewer's justified stop rather than extend the completed batch.

Cumulative context was checked against original records: the prior fleet screen used80000
native steps and602.244 run_study wall seconds; the retained H6 source reports5423.537 fit-wall
seconds (plus its separate evaluation/support). These are antecedent costs, not new fits in
this batch; broader historical selection and support remain unaggregated. C_N/E's faster CPU
but slower measured wall than neural endpoints also stays visible, so neither quality nor
compute dominance is silently broadened.

No additional Pro round has distinct unresolved expertise/disagreement value for this decision.
No successor run is selected. A concrete future re-entry could be an actual online-latency
requirement making C_N/E's measured computation consequential, or a separately motivated
learning/control-contract change with an explicit full native prediction and cost. It would
retain I/E and give the ordinary comparator the same changed information/resources; today's
result supplies neither that external requirement nor an identified repair. Direction is reserve,
with no live producer, unread result/advice or automatic continuation. Root receives this
completed assigned boundary and owns any later cross-question selection; idle is not a blocker.

<a id="b01-final-cleanup"></a>
### Final cleanup and retained reproducibility

After the independent review consumer finished, verified exact remote originals permitted
removal of local redundant A/F bulk-summary copies. Exact local deletions and allocated bytes:

- `temp/directions/uav_fleet_adaptation/`:23126016bytes, including the verified duplicate23MB
  parent checkpoint and obsolete observer request/drain scratch.
- `runs/uav_fleet_adaptation/b01_warmstart_a02/A/`:7225344bytes; `F/`:27156480bytes.
  Each contained only the corresponding verified temporary summary copy.
- `experiments/candidates/uav_fleet_adaptation/__pycache__/`:81920bytes and matching
  `tests/experiments/candidates/uav_fleet_adaptation/__pycache__/`:57344bytes.

All five local targets are absent and allocated usage fell by57647104bytes. Combined with
1623539712bytes from the two remote snapshots and their registrations, **1681186816 allocated
bytes were reclaimed**. This is measured target allocation, not a claim about Git object size or
whole-host free space during concurrent work. No cleanup blocker remains. Shared controls and
other directions' files were preserved.

Useful direction implementation,17 checks and the exact required input metadata stay published
for the retained experiment and saved-data reader; no unused additional entrypoint was found.
Checked imports/tests/entrypoints/notebook/index consumers before deletion. Existing review/
selection references are evidence consumers, not live producers. Complete unique bulk and the
two evaluated endpoint assets remain in the single durable canonical output with verified hashes;
compact positive/adverse/failed records and original source identities remain in Git. Future
exact-parent tests can restage the already retained source checkpoint; deleting its local
redundant copy does not change any recorded17/17 validation or claim present reproducibility
without that input. No training, native evaluation, new policy selection or extra output copy
was added during interpretation or cleanup.

<a id="search-amortization-design-20260930"></a>
## 2026-09-30 — Design only: inherit local C as an executable learned policy

Root assigned this question after B01's completed disposition. This is **prospective
design and saved-data reasoning only**: no new implementation, native transition,
fit, launch or revival of the A/F actors. B01 stays reserve. Root's existing
separate-context ResearchCritic `/root/deep_report_review` owns the independent
cross-question selection review; no duplicate selection critic is commissioned.

The consequential question is whether a finite supervised/interactive imitation
program can construct a competent local neural initialization that executes without
C's online candidate ranking. Immediate deployment savings and usefulness as a
starting asset for later policy development are separate judgments. No deployment
deadline was supplied. No later policy-gradient continuation is selected or assumed
to benefit. This is familiar imitation learning applied to a concrete coupled task,
not a new algorithm or an explanation of prior PPO failures.

### Inherited evidence changes the comparison

Read published main `917d9b694bb97c03c8aa3e2e6bf7d4cb5ba1f667`, especially
[topic 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
[topic 3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构),
[topic 4](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面), and
[topic 8](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验).
Their concrete effects are to retain competent ordinary C, avoid an unsupported
user-memory repair, distinguish finite optimization from available representation,
and test the complete joint trajectory rather than label accuracy alone. The
new information is training access to C's actions; deployment obtains no extra
physical observation, communication or action right. All five agents' motion and
interference still change the distribution each learner encounters.

The parent DM's pinned [ordinary-C design](../uav_parent_adaptation/NOTES.md#ordinary-parent-design-20260930)
at `e1a1171a0cb21c463dcb058dc3d71e946dc75c88` already audited the host/interface.
Its proposed C-prior learner always calls C and seeks improvement; this proposal
instead constructs a standalone actor. Inherit `LocalController(history=False)`
introduced at `ae184f74175b59f6036a06b510be2b70a7205a69`, the unchanged local
controller source, and historical local-history B02 at
`ce104088d66dade2aa042619be2e2b59ccde8e60`. Use **N5, all-on, H256 on one current
host** for all new arms. The current radio implementation differs from those
historical runs, so their scores are motivation, not fresh matched references.
N8 C_N/E adds a different manager/information contract and is not a stronger
version of this local imitation comparison merely because B01 used N8.

The original local-history C means were J .335495108/service 19.916016 in B01
and J .361942736/service 21.738281 in B02. All 96 B02 learned-endpoint versus C
world comparisons lost J/service. That establishes an ordinary capability and
an adverse finite-learning precedent, not unlearnability or weak-parent causality.

Also read the original [coupled-host distillation disposition](../coupled_host_planner_distillation/NOTES.md#2026-09-30-0446-utc--b01-read-student-evaluation-on-dev-10001031--s--4004--64--stop-band-no-purchase-the-coupled-host-leaves-the-claude-learner-substrate-item-9-direction-to-reserve)
and `runs/coupled_host_planner_distillation/b01_eval_dev_a01/summary.json`,
published in `663c0972b018b1f7e633cfc97891ebf21cb639aa`. S .400410 versus
T_M .758656 lost in 32/32 worlds; S−BC .016996 had SE .033401. Online CPU/episode
was .639017 versus 5.374502, but ordinary T_M-200 retained .732738 at 1.578963s.
Cheap inference did not establish inherited competence; the cheaper ordinary
comparison matters. Here the teacher emits dense, deterministic 27-way commands,
unlike that sparse, multi-layout continuous target. This difference motivates a
bounded comparison but is not evidence that it will succeed or a reopening of
Claude's completed/paused work.

### Causal interface and the navigation issue

C's decision at t=0,4,...,252 depends on ordered current FP32 `obs[:103]` and
its predecision ten-waypoint index. The last observation entry is a clock ignored
by C. Current rows contain own xyz, at most20 anonymous visible user xy/SINR rows
and at most4 visible peer xyz/presence rows in the ten-row capacity. With
`history=False`, ingest replaces the current points; no absent-user cache, previous
command or earlier SINR is needed to determine the next decision once navigation
state is known. Initialization chooses the nearest fixed waypoint. Commands are
the existing norm/lexicographically ordered `{-1,0,1}^3`, held four native ticks
with componentwise30m/tick motion and the existing clipping bounds.

Crucially, C advances a waypoint only when **all 27 candidates have zero modeled
service** and current XY is within60m of that waypoint. Advancing at every arrival
would be a different state machine. A student cannot obtain C's postdecision
waypoint or nominal command for free by invoking C's search.

There is a cheaper mathematical predicate for the required zero-service bit.
For visible user u, let r be own received power, P_j the stationary visible-peer
powers, U the nonnegative unknown interference calibrated exactly as C currently
does, and N the noise. Own SINR is r/(sum_j P_j+U+N), increasing in r; peer j's
SINR is P_j/(r+sum_{l!=j}P_l+U+N), decreasing in r. For each k=1..4, candidate
coordinates form the Cartesian product of `clip(p_l+30*k*a_l)`, a_l in{-1,0,1}.
Minimum/maximum squared distance to u therefore factor into per-axis minima/maxima
over three coordinates, followed by extrema over k. These give r_max and r_min.
There is any eligible candidate link iff own SINR at r_max or some peer SINR at
r_min reaches C's3dB threshold. Since top10 selection keeps at least one eligible
link and its service count is nonnegative, this is exactly the mathematical
complement of C's all-zero-service fallback. Empty current users imply fallback.

This removes 27-command objective ranking from navigation; it does **not** remove
the local radio model. Per decision it needs current setup powers `(1+p)*n`, up
to `2*n` extreme powers, coordinate comparisons and threshold checks, n<=20,p<=4.
Floating-point ordering near3dB and repeated clipping need bounded engineering
equivalence checks if selected; this is not an implemented or bit-exactly verified
optimization. No native experiment is required merely to state the derivation.

Proposed actor input is114 floats: ordered `obs[:103]`, the predecision waypoint
one-hot10, and this fallback bit1. The helper computes next waypoint from the same
prestate/arrival rule; the network emits the actual command, including fallback
cases. No current expert action enters features. Holds and all state reset at each
episode. During aggregation the expert is queried on the **student's actual
observation and predecision navigation**, not a separate shadow expert trajectory.
Training and deployment use the same helper, with any numerical mismatch resolved
before result execution rather than changing labels after outcome exposure.

### Strong ordinary alternatives from preserved trajectories

Root proposed exact episode-reset memoization. The bounded Scout confirmed the
sufficient key above. I then verified all64 original C raw hashes and scanned
the two saved32-world panels, with **zero new host/model calls**. At decision
ticks only, each agent has a separate episode-local map keyed by
`(ordered obs[:103].tobytes(), pre_nav)` and stores `(command, next_nav)`.
Pre-nav is initialized from observed own XY and reconstructed with the saved
fallback bit and60m rule. Row order and float bytes are retained; no permutation,
rounding or state approximation is asserted. Cache state is never shared between
agents or worlds. Original full-summary SHA256s are:

- B01 `6506e9692d0310b0538fcd4457fbbed7c8a63ae335a1c41c1c533aa939ec0abd`,
  `runs/uav_local_history/b01_censor_search_a01/summary.json`.
- B02 `aa8f2054f9f0233316a6754506b2ab23fc30948b7cb839b49d075c528d4fa84f`,
  `runs/uav_local_history/b02_same_history_a01/summary.json`.

| Saved C panel | Decisions | Exact hits / misses | Hit rate | Value conflicts | Candidate power links, original → cache misses |
|---|---:|---:|---:|---:|---:|
| B01 | 10240 | 9058 / 1182 | .884570 | 0 | 4491288 → 409752 |
| B02 | 10240 | 8827 / 1413 | .862012 | 0 | 4848336 → 539028 |

Setup links likewise fall45323→4136 and47597→5291 in this accounting. B01
per-world hit-rate min/median/max=.640625/.921875/.953125; B02=
.003125/.906250/.956250. In B02 world29102029,319/320 decisions are misses:
high average reuse is no worst-case guarantee. These are counts on historical C
trajectories, not measured cached runtime or a current-host replication. C already
vectorizes all27 candidates. Its original total32-episode wall times were12.673379s
and13.535354s, further weakening an unqualified latency justification.

The independent critic also proposed C7: rank only hover and the six signed
coordinate-axis commands, with the same four-tick objective and relative tie order.
Retain the **full-support analytic fallback predicate** and original navigation
rule; if C7 has no service while some omitted candidate does, C7 uses its ordinary
score argmax, not a falsely triggered fallback. On the saved full-C trajectories,
axis/hover commands occur9642/10240 (94.16%) and9694/10240 (94.67%); exact hover
alone occurs6993 and7123 times. These facts support a serious cheap comparator,
not a measured complete C7 result. Its changed trajectories remain unknown.

The proposed ordinary arms are memoized full C and memoized C7. Give both students
the same exact episode-local cache option, keyed by their deterministic sufficient
input/prestate, to compare complete competent packages. Each agent needs at most64
entries per H256 episode. Report requested decisions, actual cache misses, model
work, cache memory and timing separately. Neither removed searches nor a vectorized
operation count is a wall/CPU speedup claim.

### A finite complete package, conditional on selection

One shared FP32 MLP114→128→128→27, ReLU hidden layers,34715 parameters. Default
linear initialization under one declared root seed; no recurrence, prior actor,
critic, reward update, current-C-action input or new sensing. Train ordinary mean
cross-entropy on deterministic C category labels, preserving original tie order
and empirical sample frequency. The high hover share makes aggregate label accuracy
insufficient: retain per-category confusion, fallback/nonfallback counts, unique
input counts, and actual commands/displacements. No class balancing, architecture
or label-law sweep is proposed.

One continuously updated lineage, with Adam(lr3e-4,betas .9/.999,eps1e-8,
weight_decay0), minibatch512, fixed epoch shuffles, gradient norm cap1:

1. Collect128 fresh complete C episodes:40960 agent decision labels. Fit30epochs
   (2400 updates); preserve initialization S0 and the resulting BC checkpoint.
2. Run BC greedily in64 different fresh worlds, all five students active. Query C
   on each actual decision, add20480 labels, then train20epochs on61440 accumulated
   cases (2400 updates), continuing the same optimizer.
3. Run the new student greedily in another64 fresh worlds; add20480 labels and
   train20epochs on81920 cases (3200 updates). Freeze the final endpoint. No extra
   round, checkpoint selection, validation tuning or reward fine-tuning follows.

Pure student roll-in after the first expert block is the simple DAgger schedule;
all agents' subsequent observations/interference evolve jointly. Two fixed
aggregation rounds permit a second response to the changed visitation distribution;
they are not a claim that two rounds suffice or a diagnosis of the prior negative.
World/initialization/shuffle identities must be fixed and checked for disjointness
before source publication if selected; they are not currently reserved or launched.

Evaluate **S0, BC, final, C_memo, C7_memo** on32 fresh common H256 worlds, using
deterministic argmax for neural actors and the existing four-tick action hold.
No stochastic-deployment claim follows. The final−BC comparison is a same-lineage
milestone with more data/updates, not an isolated DAgger effect; final−S0 identifies
this finite program's conditional learned change, not training-population recurrence.
Full J/service distributions, paired descriptive intervals, service-p10, zero-service
ticks/worlds, quality, path and boundary/altitude exposure remain in the reading.
Record all losses and actual online cost rather than keeping only means or a
successful label-fit metric. Final-policy expert-agreement diagnostics are **not**
included: labels are scored only on already paid training/aggregation data.

| Planned work | Complete episodes | Native team steps | Expert label requests / optimization |
|---|---:|---:|---|
| C labels + two student aggregation blocks | 256 | 65536 | 81920 requests;8000 updates;4096000 sample presentations |
| Five-arm fresh-world evaluation | 160 | 40960 | 10240 full-C decisions;10240 C7 decisions;0 updates |
| Total | 416 | 106496 | **1 fit**, one initialization, no later RL |

Before cache savings, training labels plus full-C evaluation request at most92160
full rankings:2488320 candidate trajectories,9953280 modeled ticks,199065600
candidate power links and9216000 setup links. C7 evaluation adds at most71680
trajectories,286720 modeled ticks,5734400 candidate links and1024000 setup links.
The causal helper is additional: at most122880 requests across training features,
three neural evaluation arms and C7, each at most140 setup/extreme power links
(17203200 maximum). Shared setup reuse may reduce actual work; do not silently
deduct it before implementation. Cache-miss counts and actual n/p determine
real cost. Neural forward rows outside optimizer training are at most71680
(40960 aggregation plus30720 evaluation), before memoization. The retained reader
uses saved arrays to verify all hashes, metric reductions, clocks and memo records,
with zero extra native transitions or expert queries; consequential diagnostics
that would exceed this scope require a new priced decision.

Planning estimate, **not a benchmark or guaranteed bound**: worker10–40 CPU-min,
saved-data collection/reading1–5min, engineering plus independent executable
review2–4hours. The historical unmemorized C cost extrapolates to only101–108s
for256 episodes; that alone cannot price8000 optimizer batches, student roll-ins
or serialization. Those unmeasured costs motivate the broad interval. Node/thread
choice, actual peak memory and admission remain future launch matters. No fresh
node admission, code or timing probe is needed for this design-only return.

### What would change the development choice

An explicit **exploratory asset screen**, proposed before new exposure, is final−C
mean J>=−.01 and service>=−.5 user/tick, mean per-world service-p10>=−1 user,
and no newly zero-service world relative to C (a world with any zero-service tick
under the student but none under C). The first two tolerances define near-inheritance
for this research purchase: .5 user is about2–2.5% of historical C's mean, and
its direct service-reward contribution is .007 J. These are selected research
tolerances, **not owner deployment preferences, MEI, equivalence margins already
validated by data, or a guarantee of future RL improvement**. Read intervals and
all adverses even if point estimates pass; report path/quality tradeoffs separately.
Also require actual parameter updates/movement and a positive final−S0 complete
mean J and service change before describing the program as developing competence.

Passing this screen would provide a conditional searchless learned starting asset
for a later separately chosen policy-development study. Low label error alone,
faster inference alone or only beating S0 would not. A failed screen means this
endpoint is not adopted as that near-C starting asset and ends this fixed package;
it does not refute the broader inheritance question or automatically select more
data, rounds, capacity or a new optimizer. Partial native gains remain capabilities
to report, but do not silently pass the stated screen. C7/C's complete performance
and costs locate any deployment tradeoff even when learned initialization, rather
than immediate compute adoption, is the intended use.

Fine-tuning the frozen114-input,27-logit actor is structurally feasible without
changing the actor, helper, observation rights or four-tick native action contract.
Its logits support a categorical gradient. However, existing local-history B02
PPO uses `SetActor(context107,points64x7)`; this would **not** be a drop-in
checkpoint. A future selected continuation needs a bounded rollout/input adapter,
critic/optimizer and an explicit sampling/deployment law. None is implemented,
priced as free, or presumed scientifically useful by this proposal.

### Primary-source bridge and current recommendation

Checked the three local title/catalog stores; no novelty is claimed. Read Ross,
Gordon and Bagnell2011, [DAgger Algorithm3.1 and Theorems2.2/3.1–3.4, pp.630–631](https://proceedings.mlr.press/v15/ross11a/ross11a.pdf):
aggregate expert labels at learner-visited states rather than rely only on expert
visitation. The task-loss connection depends on recoverability and learning
assumptions; the strongly convex/no-regret guarantees do not certify this finite
nonconvex neural fit. The paper selects a validation policy; this proposal instead
reads a prospectively fixed final endpoint and makes no imported theorem claim.

Read Tang et al., *Multi-Agent Imitation Learning: Value is Easy, Regret is Hard*,
`MARL-0590`, pp.2,6–7, original
[JSON](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0590.json) and
[PDF](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0590.pdf).
Its nonstrategic-agent joint-policy reduction makes inherited team value a
legitimate objective distinct from robustness to strategic deviations. It does
not remove our decentralized observation/finite optimization limits or prove a
small recoverability constant. This task supplies no strategic-deviation claim.

My initial practical judgment was to defer because C is already cheap and exact
memoization absorbs much repeated search. Root and the independent critic raised
the constructive alternative: a competent learned initialization is a different
asset even without a deployment deadline. I accept that correction. **The bounded
one-lineage comparison above is defensible as an empirical construction question,
conditionally recommended if Root prioritizes that capability; it is not justified
as a demonstrated latency need.** Strong ordinary alternatives and adverse prior
distillation evidence keep expected value modest. The independent cross-question
review and Root's allocation remain pending; current responsibility returns at
this design boundary, with no selected successor execution or hidden later PPO.

### Final design correction and independent selection recommendation

Before any implementation or new exposure, the independent critic identified a
material decoder issue for the learned-initialization purpose: greedy competence
does not establish competence of the categorical law a future PPO collector might
sample. Root accepted that correction, and I incorporate **one fixed final-policy
temperature1 sampled panel on the same32 fresh worlds**. The preceding five-arm
table was provisional; the following is the single current cost envelope, with
S0 and sampled-final each included exactly once:

| Current fixed work | Episodes | Native team steps | Other counted work |
|---|---:|---:|---|
|128 C-label episodes +64+64 pure-student aggregation episodes|256|65536|81920 requested expert labels;8000 optimizer updates;4096000 sample presentations|
|S0, BC, final-greedy, final-sampled(T=1), C_memo, C7_memo;32 worlds each|192|49152|10240 full-C decisions;10240 C7 decisions;40960 neural decisions;0 updates|
|**One complete package**|**448**|**114688**|**1 fit**, one continuously updated lineage|

The92,160 full-teacher request ceiling and all full-C/C7 trajectory, tick and link
ceilings above are unchanged. The added sampled panel requests no teacher labels.
The corrected helper ceiling is133120 requests/18636800 setup-plus-extreme power
links, and neural forward rows outside optimization become81920. Real cache
misses, n/p, setup reuse, CPU/wall and memory remain measured outputs if selected;
the same broad worker10–40CPU-min/reader1–5min and engineering2–4h planning
estimate covers this additional32-episode panel. No actual runtime is claimed.

Sampling uses an independently indexed innovation for each world, decision tick
and agent, fixed by a separate root before execution. At each decision, sample the
declared temperature1 categorical probabilities over the existing ordered27
commands, then hold that sampled command for four ticks. Record the innovations
and probabilities/law. **A sampled-policy cache stores logits and next navigation,
not a sampled command**: even identical observations get a fresh indexed draw.
Ordinary/greedy caches may store their deterministic commands. No rollout mixing,
temperature adjustment or greedy-versus-sampled winner substitution is allowed.

Final-greedy remains primary. Apply the declared competence screen separately to
sampled-final before treating the asset as a competent default stochastic starting
policy. Greedy-pass/sampled-fail preserves a deterministic capability and an
adverse/unresolved stochastic bridge; it does not count as success for both. No
sampled-S0 learning-effect claim is made. BC-pass/final-fail likewise preserves
the BC milestone, without automatic endpoint replacement. C7 superiority in
complete J/service/tails remains consequential to later investment even if the
C-only near-inheritance screen passes; the screen does not erase a stronger cheap
ordinary capability. Further development would still require a new prospective
comparison against competent ordinary methods and the rollout/critic/sampling
engineering already described.

The Root-assigned, separate-context ResearchCritic independently recommends buying
this **one complete developmental-asset screen**, retaining C/C7, all distillation
adverses,86–88% historical memo hits/data redundancy, one-lineage uncertainty and
the explicit later PPO adapter gap. It accepts the tolerances only as exploratory
continuation screens, not operational requirements or noninferiority evidence.
I accept the recommendation and both concrete corrections (S0, sampled-final);
no material scientific disagreement remains. The review returns directly to Root,
which owns the cross-question allocation. Another Pro round adds no distinct
unresolved expertise for this bounded design; Root's separate parent-C advice is
not treated as an answer about this student. **Design is complete; execution
remains unselected, and B01's reserve/cleanup standing is unchanged.**

<a id="b02-l0"></a>
## 2026-09-30 — B02 selected; adoption, fixed identities and L0

Root selected the final six-arm developmental comparison in published
`ec1545411c220fe9d24688f6cb3546ceea9b1489`. I read the
[complete original independent answer and Root decision](../../archive/2026-09-30/RESEARCH-local-controller-inheritance.md)
in full and adopt it without copying the answer here. Owner pause remains lifted
for this assigned direction; the current entry is exploring with the same
`Codex DM (native child)` lead. B01 outcomes, exposure and cleanup stay unchanged.
This allocation supersedes only the preceding design-only execution status.

Freeze B02 identities before implementation: expert worlds29340000–29340127;
aggregation1 worlds29340128–29340191; aggregation2 worlds29340192–29340255;
evaluation worlds29341000–29341031; actor initialization29342001;
minibatch-shuffle root29342002; sampled-evaluation root29342003. The shuffle
address is(root,phase_index,epoch_index); sampled innovations use
(root,world,decision_tick,agent). No Python hash, loop-order-dependent shared
sampling stream or global NumPy state determines these addresses. All evaluation
arms reuse the same reset seed per world; evaluation order rotates by world index.
The root's identity is unrelated to any inference about independent training seeds.

The exact integer ranges were absent from current research/code/config records
before this entry. Parent C-prior's proposed training30310000+1000*block+episode
and evaluation30300000+100*block+world are disjoint, as are the old local-history
29091000/29102000 panels and B01's recorded identities. Final executable contract
will assert all internal separation and bind source hashes, and the publication
check will repeat the current proposed-peer/range scan before launch.

**L0 deliverable.** One admitted B02 runner, actor/collector/trainer, exact ordinary
comparators, compact results and saved-data reader implementing the selected
1fit/448episode/114688step,8000update/4096000presentation contract. Owned new
paths are `experiments/candidates/uav_fleet_adaptation/b02/`, matching
`tests/experiments/candidates/uav_fleet_adaptation/b02/`, this notebook, future
`runs/uav_fleet_adaptation/b02_inheritance_a01/` and owned temporary scratch.
Entry points are `b02/run.py` and a saved-data-only `b02/read.py`. No B01/shared
environment/controller edits, extra fit, extra evaluation or later PPO are in scope.

The bounded Implementer owns only `b02/controllers.py` and its mirrored
`test_controllers.py`: implement the analytic eligibility/navigation helper,
source-bound original-C queries with exact per-agent episode-reset memoization,
and seven-action C7 ranking with the full-support fallback rule. DM owns remaining
files, notebook, Git index, acceptance and launch. All work is on shared main;
no helper staging/commit, checkout creation, children, native experiment or change
to scientific choices. Other writers' files remain untouched.

The frozen teacher is imported from the original local-history source, last changed
at `ae184f74175b59f6036a06b510be2b70a7205a69`, file SHA256
`b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2`.
Original full-C queries use the actual observed row and predecision navigation;
cache values retain command, next navigation and paid label diagnostics. C7 shares
the declared helper but never calls full C to choose its command. Neural policies
consume only114 lawful features; sampled memoization stores logits and next-nav
and always consumes a fresh independently addressed innovation, even on a hit.
Every four-tick decision/hold/reset, requested versus actual displacement,
teacher/helper/link count and worker/reader cost must remain measurable.

**Checks and stop.** Focused synthetic, outcome-blind checks cover the helper's
fallback/navigation equivalence at threshold/clipping/ties, actual-history teacher
labels, cache reset/key/value isolation, C7 subset scoring, indexed RNG with cache
hits, exact actor/optimizer/data counts, native-observation leakage boundaries,
all six readers and admission before scientific effects. Existing small native
host checks may verify correctness without becoming a result pilot. An independent
high-risk numerical/RNG/executable reviewer reads the exact diff and checks before
source acceptance. Any consequential interface contradiction returns to Root;
numerical/coding defects are repaired in scope, preserving the fixed scientific
law. The worker/reader and engineering cost estimates above are planning estimates,
not authority for additional exposure or automatic retries.

### B02 implementation and prospective execution

The bounded Implementer returned only `controllers.py` and its mirrored tests;
I read and accepted those changes into the integrated study. The helper preserves
the source's power, total-minus-own SINR and iterated-clipping arithmetic, then
uses per-coordinate extrema to decide whether any full-support candidate has an
eligible link. Numerical checks cover180 randomized local cases and260 own-link
plus260 peer-link threshold cases, empty discovery, clipping, arrival/ties and
the C7/full-support distinction. No mismatch in those cases is a universal FP
equivalence proof. Training additionally compares every already-paid C label's
fallback/navigation against the helper on the student's actual row/pre-nav.

The completed pipeline retains one CPU FP32 actor and one Adam state through
the fixed30/20/20 epochs, saves S0/BC/D1/final assets, and binds every training and
evaluation trajectory to its actual policy/source. C expert roll-in shares its
execution/label query; student aggregation queries C only on actual student
histories. Evaluation has no C-label diagnostics for neural arms. Cache scopes
are per agent/episode; the sampled arm caches logits and draws afresh at every
indexed decision. The saved-data reader checks all fixed worlds/arms/holds,
native metric reductions, recorded motion, lawful features/navigation, paid
rankings, cache keys/counters, stochastic draws, checkpoint tensors and
data/shuffle/update counts. It makes no new native, expert-radio, actor-forward
or optimizer calls and does not claim a replay of those computations.

Local configured CPU verification passed17 tests in4.60s (only upstream
matplotlib/pyparsing deprecation warnings). This includes the complete synthetic
three-phase/six-arm pipeline, deliberate rehashed draw and endpoint corruption,
source/helper/cache checks and admission before scientific imports/output. One
separate correctness test used an8-tick native C trajectory with nonstudy seeds
819171/819172,0fits/0updates; this verifies the live factory/adapter/collector
interface and is not an additional study world or result pilot. The study's
prospective exposure remains1fit/114688steps.

Independent engineering review reproduced the17 passing checks and found one
failure-accounting defect: partial-episode query costs were omitted when no
complete row existed. I repaired it by retaining live counter/timing references
and recording partial costs separately from complete scientific rows. An
interrupted call's unfinished internal work remains explicitly unmeasured.
The existing failure fixture now retains its5teacher requests/135trajectories
and5helper calls after3successful native steps plus one failed call, with0complete
episodes/0fits. That targeted regression and the full synthetic reader passed
2 tests in2.43s; final review acceptance follows below.

Prospective node choice is the configured primary `wsl_4070`, CPU FP32 with one
Torch/BLAS thread and deterministic algorithms. The2026-09-30 prepublication read-only
probe found the configured CPython3.10.21 runtime present,15,235,796KiB available
memory and low load; this is host-selection evidence, not launch admission.
The launcher will enforce fresh actual-node memory/pause/lead/publication checks
on the exact published inputs. No external input checkpoint or dataset is needed:
all data arise within the declared448 episodes and the original teacher/host
source bindings are in `b02/contract.py`. No result operation is accepted yet.

The independent engineering Reviewer completed its full-path review with no
material finding remaining after that repair; it reran the two affected checks
in2.48s. The review covers helper/teacher arithmetic, C7 support, memoization,
indexed RNG, actual-history labels, continuous Adam, frozen assets, admission and
saved-data reading. I accept the implementation for the fixed study, retaining
the numerical-fixture and nonreplay limits above. No scientific choice, arm,
epoch, world range or fitted endpoint changed during implementation/review.
The final exact-integer identity scan found the B02 ranges only in this notebook
and its three implementation declarations. The now-implemented parent C-prior
protocol still uses30310000+1000*block+episode and30300000+100*block+world;
the selected world and randomness identities remain disjoint.

### B02 publication and admission

Exact implementation/tests/prospective notebook inputs were committed and
published as `e945483b85c7f8ddfc315c57f36938d6c14201c7`, verified against
`refs/heads/main`. The primary-node configured compute and maintained launcher
bytes matched published main. Its local policy still recorded lifted/exploring
and the same native-child lead; the launcher checks that tuple against current
published main, independently of older descriptive prose on the remote checkout.

The first supervisor command (`fleet-b02-inheritance-a01-20260930`) ended with
exit4 at2026-09-30 15:43:48UTC: the kernel's current-control check encountered
newly published `7bb778764d4de030179f9b4d06681c35073fb372` after the prior fetch,
and `git cat-file -e <sha>^{commit}` timed out after30seconds. This refusal
preceded snapshot preparation, claim reservation, output creation and runner
execution:0fits/0native steps. The original supervisor log remains under the
same name in `/home/wu/.agent-tasks/`. A bounded exact claim-directory check
confirmed no operation at this source/output before retrying the unchanged
request after fetching current control. This is preacceptance reconciliation,
not an extra fit or a duplicate accepted worker.

Remote Git transport required the configured `zsh -lic` network environment;
the initial direct-shell read-only fetch was stopped without scientific effects.
An overly broad read-only metadata scan was likewise stopped and narrowed to
the admission claim directory. Fetches succeeded, while background automatic-GC
emitted a preexisting missing historical-tree warning (`dfe82c9813ee82191abb8385cc12a6886fd0a77b`);
no shared Git repair, cleanup or removal of that warning was attempted. The
second supervisor (`fleet-b02-inheritance-a01-admission2-20260930`) was issued
only after the current control fetch; it keeps the exact source, scientific
argv, node and output `runs/uav_fleet_adaptation/b02_inheritance_a01` unchanged.

The unchanged request was accepted at2026-09-30 15:48:26.621743UTC. The
[native manifest](../../../../runs/uav_fleet_adaptation/b02_inheritance_a01/launch-manifest.json)
and [fresh preflight](../../../../runs/uav_fleet_adaptation/b02_inheritance_a01/admission-preflight.json)
are collected locally; the manifest is the canonical source of the operation,
source snapshot, command and native process identities. The detached worker uses
the original published `e945483b8` inputs and durable primary-node output.

The session's stopped B01 observer was drained (generation10, no pending events)
and rearmed without reviving either completed B01 job; the new same-handle B02
observer is generation12 with a600second checkpoint window,30second interval and
25second read-only SSH probe timeout. Initial registration rejected a relative
`ssh` executable and then the stopped prior state; both were corrected in the
observer request only. No worker restart or extra launch resulted. This native
DM turn stays active through collection and scientific reading.


<a id="b02-complete-reading"></a>
## 2026-09-30 — B02 complete reading: a learned starting asset, without a speed gain

The fixed local-C inheritance study completed at its declared boundary: one
continuous fit, 256 training and 192 evaluation episodes, 114,688 native steps,
8,000 Adam updates and 4,096,000 sample presentations. All six frozen arms and
all 32 fresh common evaluation worlds are present. The primary greedy asset
screen and the separately declared temperature-one sampled screen both pass
on their point rules; BC alone fails the milestone screen. This is exploratory
asset retention for one training lineage, not population noninferiority,
training recurrence, a later learning gain or a latency claim.

The original [summary](../../../../runs/uav_fleet_adaptation/b02_inheritance_a01/summary.json),
[configuration](../../../../runs/uav_fleet_adaptation/b02_inheritance_a01/config.json),
[saved-data reading](../../../../runs/uav_fleet_adaptation/b02_inheritance_a01/reading.json)
and native records bind the result to published source
`e945483b85c7f8ddfc315c57f36938d6c14201c7`. Summary SHA256 is
`2e9e5d83f6b7d1cdff0a947a361fe1e1493046cd7c8b25aee068ed9eb7fc6e8c`;
reading SHA256 is
`a3f76992ccb01aa90138eec2272dc2667b7283d32e86742e87bf77e43bd613e9`.
These are original files, not a rewritten selected-result summary.

### Complete endpoint comparison

Here J is the native per-step objective, service is connected users per step,
service p10 is the within-world tenth percentile across its 256 ticks, and path
is mean total metres per UAV. Each table entry is the mean of 32 worlds. All
noninitial arms have zero zero-service ticks in every world; S0 has at least one
in 26/32 worlds and averages 183.375 such ticks. This is team-level service,
not an individual-user continuity or physical-safety guarantee.

| Fixed arm | J | Service | Service p10 | SINR quality | Path m/UAV |
|---|---:|---:|---:|---:|---:|
| S0 | 0.014486 | 0.754883 | 0.593750 | 0.013058 | 563.132315 |
| BC | 0.317098 | 18.925415 | 18.656250 | 0.173809 | 1895.997334 |
| S_greedy | 0.342868 | 20.717041 | 20.390625 | 0.176097 | 1733.578576 |
| S_sampled | 0.387299 | 23.704590 | 21.125000 | 0.184782 | 2977.841423 |
| C_memo | 0.340733 | 20.351685 | 19.781250 | 0.186031 | 2578.514211 |
| C7_memo | 0.328562 | 19.480957 | 18.656250 | 0.186095 | 2522.027695 |

All nine prespecified paired contrasts follow. Brackets are nominal descriptive
world-paired t95 intervals conditional on this trained lineage and, for the
sampled arm, its one fixed independent innovation stream per world. They are
not simultaneous intervals or uncertainty over training programs. Positive /
negative counts refer to J; all signed values and the remaining metrics stay
in the original summary/reading.

| Contrast | Mean ΔJ [t95] | J positive / negative | Mean Δservice [t95] |
|---|---:|---:|---:|
| S_greedy-C_memo | +0.002135 [-0.015278, +0.019548] | 15 / 17 | +0.365356 [-0.955989, +1.686702] |
| S_sampled-C_memo | +0.046566 [+0.028246, +0.064886] | 26 / 6 | +3.352905 [+2.042278, +4.663533] |
| BC-C_memo | -0.023635 [-0.048287, +0.001018] | 13 / 19 | -1.426270 [-3.111093, +0.258554] |
| C7_memo-C_memo | -0.012171 [-0.026843, +0.002501] | 10 / 22 | -0.870728 [-1.930474, +0.189019] |
| S_greedy-S0 | +0.328382 [+0.300946, +0.355818] | 32 / 0 | +19.962158 [+18.092715, +21.831601] |
| S_greedy-BC | +0.025769 [-0.001484, +0.053023] | 18 / 14 | +1.791626 [-0.142474, +3.725726] |
| S_sampled-S_greedy | +0.044431 [+0.021281, +0.067581] | 22 / 10 | +2.987549 [+1.336212, +4.638885] |
| S_greedy-C7_memo | +0.014306 [-0.003432, +0.032044] | 18 / 14 | +1.236084 [-0.107508, +2.579676] |
| S_sampled-C7_memo | +0.058737 [+0.037457, +0.080017] | 26 / 6 | +4.223633 [+2.696867, +5.750398] |

The primary greedy endpoint is close in panel mean to C, but it loses J in
17/32 worlds and service in 14/32. Its mean p10 change is +.609375
[−.772445, +1.991195]; quality changes by −.009934
[−.019962, +.000094], with 21 quality losses. Its path is shorter by
844.935636 m/UAV [−1579.220249, −110.651022]. The prespecified point margins
(ΔJ ≥ −.01, Δservice ≥ −.5, Δp10 ≥ −1 and no new zero-service world) pass;
the intervals do not establish those margins in a population. Actual parameter
updates and positive greedy−S0 J/service, both 32/32 positive, satisfy the
additional learning condition. No sampled result substitutes for this primary
reading, and the weak S0 is not the competent comparator.

The separately fixed sampled decoder gives a larger complete-native mean gain:
26/32 positive J and service changes versus C, retaining all six adverse worlds.
Its p10 change versus C is +1.343750 [−.071577, +2.759077] and its quality
change is −.001250 [−.010326, +.007827]. Its path versus C increases by
399.327211 m/UAV [−177.222837, +975.877260]. Relative to the same final
weights decoded greedily, sampling improves J by +.044431 and service by
+2.987549 while increasing path by 1244.262847 m/UAV
[+819.664901, +1668.860793]. Decoder choice therefore matters for this fixed
asset. It does not isolate learned coordination, beneficial exploration or a
universal sampling mechanism; no randomized ordinary-C comparator was run.

The intermediate BC milestone is below C in all three point margins. Final
greedy−BC means improve, but the J/service/p10 intervals cross zero. The two
aggregation blocks also add data, optimization and exposure, so this is not a
matched causal estimate of DAgger over ordinary BC. C7 has worse mean J/service
and p10 than full C; its p10 difference is −1.125000
[−2.242838, −.007162]. Full C remains the primary ordinary reference. Neither
C7's seven-command support nor its reduced link count warrants replacing C
with a weaker baseline.

### Trajectory evidence and unresolved explanation

I inspected seven saved positive/adverse trajectories, with no new host, radio,
policy or optimizer calls (separate inspection CPU .482909 s). In world29341030,
greedy−C J is −.102518 and service −8.402344: greedy's four 64-tick service
block means are 17.921875, 19, 19, 19, versus C's 26.03125, 27.5, 27.5,
27.5. All 160 greedy UAV-ticks in the final 32 ticks are stationary, versus
96 for C. This supports a persistent adverse placement in that world, not a
universal optimization diagnosis.

World29341010 is adverse even under sampling: sampled−C J −.032295 and
service −3.347656. Sampled block means are 20.078125, 21.453125, 18.59375,
20.046875 versus C's 22.6875, 23.625, 23.625, 23.625. Conversely,
world29341009 gives sampled−C J +.178922 and service +11.507813. Its sampled
block means rise from 27.375 to 29.84375, 31.015625, 31.234375; C's remain
18.3125 then 18.375. Greedy reaches 17.875 then 18. The mean paths are
189.415 m/UAV for greedy, 2805.794 for sampled and 3798.117 for C. A story that
C always stops moving, or that more movement alone causes the gain, is not
supported by this witness. Policy-dependent movement and interference change
visited states jointly; the data do not identify one causal mediator.

### Paid learning, model work and timing

There is one actor/Adam lineage, not three independent fits. The fixed
30/20/20 epoch phases contain 40,960 / 61,440 / 81,920 cumulative labels,
2,400 / 2,400 / 3,200 updates, and 4,660 / 6,421 / 8,364 distinct feature
rows. Last-epoch cross-entropies are .442391 / .487890 / .416533 and paid
pre-update stream accuracies .877930 / .860238 / .879517. These are metrics
from already-paid optimization forwards, not frozen-endpoint imitation
accuracies or final-policy expert-query diagnostics. No such extra diagnostic
queries were made. Final versus S0 movement is L2 39.469967, max absolute
1.751200, with 26,791 of 34,715 parameters changed.

The 81,920 training labels and 10,240 C evaluation requests share the exact
per-agent, per-episode memoization contract. Across all 92,160 full-C requests,
82,823 were hits and 9,337 actual rankings remained: 252,099 candidate
trajectories, 1,008,396 modeled ticks, 3,395,196 candidate power links and
34,515 setup links. C7 made 10,240 requests / 1,293 rankings, 9,051
trajectories, 36,204 modeled ticks and 117,908 candidate power links; it reused
its helper setup rather than count a second copy. Total analytic helper work
was 18,489 calls, 71,618 setup links and 131,366 extreme-power links. Neural
collection/evaluation made 12,536 actual row forwards outside optimization;
the sampled arm made all 10,240 fresh indexed draws, including cache hits.
These are actual counters; the much larger prospective ceilings were not spent.

| Evaluation arm | Mean query CPU s/episode | Mean query wall s/episode | Hits / 10,240 requests | Actual neural rows |
|---|---:|---:|---:|---:|
| S0 | 0.017070793 | 0.016358786 | 9079 | 1161 |
| BC | 0.018232587 | 0.017458464 | 9416 | 824 |
| S_greedy | 0.021408272 | 0.020515840 | 9078 | 1162 |
| S_sampled | 0.083939891 | 0.080443448 | 4555 | 5685 |
| C_memo | 0.015968623 | 0.015357289 | 9267 | 0 |
| C7_memo | 0.020899747 | 0.020068138 | 8947 | 0 |

C evaluation caches 90.498% of decisions. Greedy pays +.005440 query CPU
seconds/episode versus C [.003420, .007459], slower in 27/32 worlds; sampled
pays +.067971 [.061241, .074701], slower in all32. C7 also costs +.004931
[.003523, .006339], slower in 28/32 despite fewer candidate links. The student
removes online full-C candidate ranking, but this implementation does not
amortize it into a measured speed benefit. Radio/navigation features, neural
calls, cache behavior and sampling still cost time. Timings are complete
policy queries on each arm's own trajectories, not matched-state microbenchmarks
or physical deployment latency. There is still no supplied deadline requirement.

The worker reports 100.363925 wall / 101.990390 CPU seconds and peak RSS
679,316 KiB. This scope starts at its entry, including imports, construction,
resets, native collection, training, checks, raw compression/hashing and prior
summary writes; its final self-report write is excluded. Of the worker's CPU,
all episode rows total78.484586 s; named disjoint components include native
steps51.830696, policy queries8.244462, expert labels4.425574, expert features
1.462282 and raw writes2.986595. Optimization phases total14.515561 CPU s.
Residual initialization, resets, summary and other checks remain in the measured
worker total, not invented as zero overhead.

The saved-data reader reports 5.227979 wall / 5.553432 CPU seconds, peak RSS
509,424 KiB. Combined measured worker+reader scopes are 105.591904 wall /
107.543822 CPU seconds. Admission, failed preacceptance transport, engineering,
review, support and publication are outside those timers. Engineering/review
person-time was not formally metered; elapsed allocation/publication timestamps
are not substituted for labor. The prospective 10–40 worker CPU-minute and
1–5 reader-minute estimates overpredicted these observed costs. The separately
reported .482909 CPU-second DM inspection is outside the reader timer. Earlier
B01's two fits/576,000 steps/31,190.348 worker+reader CPU seconds and historical
parent/teacher selection costs remain incurred; this small B02 run does not
reset cumulative investment or retroactively become a positive B01 outcome.

### Collection, verification and durable assets

The accepted worker exited0 with its manifest-bound runner/supervisor absent.
The deterministic observer recorded READY at2026-09-30 15:50:37.585UTC,
event `0d1972f5648b12437ab2deca`, wake
`725d3304-9a6f-4182-88e5-c02aaebac0f9`, generation12. Native child App-queue
submission was rejected with `-32600`; the turn remained active and collected
through the original handle. The event was drained and consumed by rearm13,
then observation stopped with no pending events. No worker was restarted.

The same-source saved-data reader ran under detached supervisor
`fleet-b02-read-a01-20260930` and exited0 at15:54:12UTC. It verified all448
raw hashes,114,688 recorded native ticks,143,360 decision records and all four
assets, along with the six fixed arm/world bindings, metric reductions, recorded
motion/hold/navigation, lawful feature construction, paid source rankings,
cache keys/counters, sampled innovations, dataset/shuffle identities and exact
update counts. It performed zero native steps, expert-radio queries, actor
forwards and optimizer calls. This is complete saved-evidence verification;
it is not a physics, actor or optimizer replay, and bounded engineering cases
are not a universal floating-point proof.

One canonical bulk copy remains on
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/`:
448 raw NPZ files (48,609,094 logical bytes) plus four checkpoint assets
(1,416,970 bytes). Hashes/sizes are in the original summary and verified reading;
compact originals were copied locally with matching hashes. No redundant local
raw or checkpoint copy was created. The endpoint for any separately selected
future use is `assets/S.pt`,424,487 bytes, file SHA256
`b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`,
tensor-state SHA256
`6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`,
at8,000 updates. S0/BC/D1 retain the exact training/reading lineage. This
114-input,27-command actor depends on its declared analytic navigation helper;
it is not a drop-in checkpoint for the historical SetActor, nor a tested PPO
initialization. Both fixed decoding laws refer to the same final asset.


<a id="b02-independent-disposition"></a>
### Independent scientific review, changed explanation and next investment

The dedicated ResearchCritic `b02_result_review` worked in a separate context
without DM/Root conversation inheritance. It reconstructed the frozen protocol
and results before reading the full archived allocation advice. It checked all
15 source hashes against `e945483b8`, all192 evaluation rows/common worlds and
the paired means. Its independent raw reading covered ten positive/adverse
evaluation trajectories and three training trajectories, with zero new native,
expert/radio, actor-forward or optimizer calls. The two aggregation witnesses
contained131 and191 behavior-versus-teacher disagreements: paid labels corrected
actual student histories rather than copying the executed commands. Its scope
does not include replay of all physics, neural or optimizer arithmetic, or a
universal finite-precision helper proof. No material discrepancy was found.

The Reviewer recommends retaining the final actor as a **conditional learned
starting asset**. `MATERIAL_DISSENT: no`. I accept that disposition and its
limits: both fixed point screens pass, while training recurrence, C equivalence,
speedup, a sampling mechanism and later PPO utility remain unsupported. Its
additional adverse reading is consequential: sampled mean within-world minimum
service is10.21875 versus C's11, a difference−.781250
[−1.365725, −.196775], with21 lower,7 higher and4 tied worlds. The sampled
p10 also falls in11 worlds. These losses remain evidence despite the selected
point-screen pass; no energy or physical-safety inference follows from path.

The working explanation changes at four distinct levels:

- **Task opportunity.** Competent ordinary local control remains a real
  capability in this fresh panel. The cheaper-looking seven-action ranking did
  not improve complete performance or measured query time. Keep full C and its
  exact memoization as the serious ordinary reference.
- **Lawful representation.** A114-input actor can execute without the current
  teacher command from current local observation, its own predecision navigation
  and an analytic eligibility feature. Full candidate ranking is absent from
  neural deployment; the radio/navigation scaffold remains. This demonstrates
  one usable representation and execution package, not model-free control or
  equality of function classes.
- **Finite learnability.** This finite supervised lineage produced consequential
  native competence. Actual updates, parameter movement and full-world outcomes
  support that positive; training-stream accuracy or81920 repeated labels alone
  would not. There is only one fitted lineage and8364 distinct aggregate feature
  rows. The old96 local-history/C losses and coupled-host distillation's
  .400410-versus-.758656 adverse remain intact for their different recipes;
  B02 does not repair or diagnose either historical failure.
- **Complete-package value.** The asset is now available for a separately selected
  learning comparison, while its complete online compute advantage is absent.
  Greedy/sample query CPU is about1.34×/5.26× C, and full episode CPU is
  .161518/.234974 versus C's.155697 seconds. A sampled service improvement is
  a native capability with minimum-service/path/compute tradeoffs, not a complete
  domination claim.

The strongest simpler explanation for sampled surplus is ordinary randomization
around a competent local policy. Greedy uses hover on8031 decisions, sampled on
6572, and sampled visits more distinct local cache states. This is compatible
with escaping some stationary or repetitive behavior, but does not isolate that
mechanism or credit it to learned coordination. The separately selected ordinary
C prior with `p(C)=.9` is a concrete future comparator for a learned stochastic
advantage; different-panel outcomes would not be a matched test here. No new
randomized-C arm or extra native diagnostic is added to B02.

For the next allocation, the Reviewer favors one unchanged-recipe independent
training lineage before spending on a reward-training adapter. I agree that this
is the best currently specified continuation to consider, rather than inventing
an unexplained repair. It would use fresh training worlds, initialization and
shuffles, retain S0/BC/final greedy/final sampled readings on this now-development
32-world panel with its fixed sampling innovations, and reuse the original C/C7
trajectories only if the exact host/source/protocol bindings remain unchanged.
That prospective object costs one fit,384 new episodes,98,304 native steps,
8,000 updates and4,096,000 presentations. The observed107.544 worker+reader
CPU seconds provide an empirical planning anchor, not a guaranteed future cost
or a substitute for unmetered engineering/review/support work.

The recurrence comparison would change a real investment choice. Repeated
competence in both modes strengthens the case for a separately designed reward
continuation; greedy-only recurrence retains deterministic construction while
weakening the stochastic-start premise; failure lowers confidence in the fixed
construction program while preserving today's usable asset. Loss of sampled
superiority with retained near-C competence would remove the surplus story
without erasing inheritance. Two such exploratory lineages would still not
confirm a population claim. This recommendation is **not a prerequisite for
conditional use of the existing checkpoint**. Merely remaining better than S0
would be insufficient evidence of useful subsequent learning: any continuation
must compare with its unchanged starting asset and competent ordinary control.

No replication, adapter, reward fit, new temperature, extra epoch or new arm is
selected or authorized by this review. Root owns the next cross-question
allocation after this assigned boundary. B02 is complete and the direction is
reserve with a qualified reusable asset, no live producer, unread advice or
fabricated external dependency. Additional Pro advice offers no distinct value
for this retention/recurrence preference; materially changed later questions
receive review on their actual claim, comparison and cost. The constructive
positive and all adverse evidence are retained without relaunching the old B01
A/F recipe or treating unsuccessful compression elsewhere as unlearnability.

<a id="b02-final-cleanup"></a>
### Final cleanup and retained evidence

The complete compact evidence was published first at
`269d5d03f6765062fc3dbb8c88fffa4c8e16b948`. After the independent review
consumer finished, the source snapshot collector preview and apply both found
the exact accepted B02 snapshot eligible: terminal native processes absent,
matching claim/source/output identity, externally retained complete evidence,
clean source files, durable published reachability and no live process reference.
The documented `--sudo-process-scan` option used existing passwordless sudo only
for its read-only protected-process scan; removal remained under the original
user and serialized writer/admission locks. No force deletion or new copy was
needed, and no new refusal occurred.

Actual remote deletions and measured allocated bytes:

- `/home/wu/projects/HMASD/.git/hmasd-launch-sources/a3e5bf4370244776bd70ba812355289a/`:
  809,566,208 bytes.
- Its registration
  `/home/wu/projects/HMASD/.git/worktrees/a3e5bf4370244776bd70ba812355289a/`:
  3,555,328 bytes.

Both are absent, reclaiming813,121,536 allocated bytes. The canonical run,
448 unique raw files, four assets, manifest, terminal witnesses and admission
claim remain. Its original source is published and source-bound; removing the
disposable execution snapshot does not remove that source or duplicate guard.

After checking the stopped/drained observer and completed helper consumers,
exact local deletions were `temp/directions/uav_fleet_adaptation/` (12,288 bytes,
only the obsolete B02 observer request),
`experiments/candidates/uav_fleet_adaptation/b02/__pycache__/` (102,400 bytes)
and the matching test `b02/__pycache__/` (57,344 bytes). All three are absent;
local allocated usage fell172,032 bytes. **B02 therefore reclaimed813,293,568
allocated bytes**, separately from B01's already reported1,681,186,816 bytes;
cumulative deletion for these two completed studies is2,494,480,384 bytes.
These are measured exact-target allocations, not whole-host free space or Git
object shrinkage during concurrent work.

No cleanup blocker or redundant bulk remains for B02. Useful implementation,
17 correctness checks, compact positive/adverse readings and all required unique
training/endpoint evidence remain for the retained asset and its saved-data
reader. No unused extra entrypoint was found; the sole disposable local scratch
and all B02 bytecode caches were removed. The separate preexisting remote Git
historical-tree GC warning was not repaired or misreported as a cleanup blocker.
Other directions, shared controls and accepted peer operations were preserved.


<a id="b03-recurrence-prospective"></a>
## 2026-09-30 — B03 selected: one independent inheritance lineage

Root read the complete B02 review and selected exactly the Reviewer's proposed
in-scope recurrence comparison. B02 remains closed at `e6b1a3243` (complete
evidence `269d5d03f`), with its cleanup and conditional asset unchanged. B03
asks whether the same finite construction recurs under fresh training worlds,
initialization and minibatch shuffles on the existing **development** panel.
This is one new exploratory lineage, not confirmation, a requirement for using
today's asset, a test of learned stochastic superiority over randomized C, or
permission for further automatic repeats.

The relevant current published background is `e6b1a3243`, RESEARCH topic4 and
its linked B02 complete/independent reading. It changes the prediction from
whether a competent asset can be constructed at all to whether the fixed
construction recurs. Topic2/3/8 reading used for B02 is unchanged and reused:
local information, native decision consequences and ordinary physical structure
still constrain the comparison. C's ordinary capability, the lack of a measured
speed gain, B02's minimum-service/world losses and the earlier imitation and
B01 warm-start adverses all survive. Ordinary randomization remains a serious
alternative for the sampled surplus; the separate C-prior study/Root's further
cross-question diagnosis does not change this recurrence contract or add an arm.
The completed fresh-context `b02_result_review` explicitly reviewed this one-fit
choice, fixed outcome branches and cost. Its advice remains applicable; no new
selection reviewer or Pro round is needed for the unchanged question.

**Exact new identities and fixed recipe.** Expert worlds29343000–29343127,
aggregation1 worlds29343128–29343191, aggregation2 worlds29343192–29343255;
initialization29344001, shuffle root29344002. Existing evaluation worlds
29341000–29341031 and sampling root29342003 are deliberately reused. Their
sampling address remains(root,world,decision_tick,agent), and shuffles remain
(root,phase,epoch). A current repository identity scan found no use of the new
training/root integers before this entry. These are independent training inputs;
the common evaluation panel/innovations are not new independent world evidence.

Keep128 C roll-in episodes and two64 greedy-student aggregation blocks,
30/20/20 epochs, one continuous Adam, identical114→128→128→27 actor, CE loss,
learning rate3e-4, batch512 and gradient cap1. Keep four-tick holds, exact
per-agent episode caches, lawful analytic navigation and fresh T=1 draws. New
evaluation collects only S0, BC, final greedy and final sampled:128 episodes.
There is no teacher query on neural evaluation, no new C/C7 world and no
additional fit, epoch, temperature, endpoint selection or reward update.

**Retained-control contract.** Reuse the original64 C_memo/C7_memo evaluation
trajectories in canonical primary-node B02 output. Bind the original source
`e945483b85c7f8ddfc315c57f36938d6c14201c7`, COMPLETE summary SHA256
`2e9e5d83f6b7d1cdff0a947a361fe1e1493046cd7c8b25aee068ed9eb7fc6e8c`,
VERIFIED reading SHA256
`a3f76992ccb01aa90138eec2272dc2667b7283d32e86742e87bf77e43bd613e9`,
config/manifest/exit identities and every retained raw hash. Compare every
unchanged protocol field, all15 B02 source identities and runtime/host settings;
new evaluation resets must match the retained world's actual initial-state
identity. The current15 files match, and Git shows no change since e945 in the
host environment tree, source teacher/factory or B02 implementation. Before
new native work, a strict loader must establish the retained source/protocol/
raw bindings. If reuse is impossible, return the material scope/cost change to
Root before adding any ordinary-control evaluation. No copy of retained bulk
or reconstruction of a replacement C/C7 result is authorized.

**Exposure and cost.** New work is1fit,384 complete episodes and98,304 native
steps (65,536 training plus32,768 evaluation),8,000 updates and4,096,000
presentations. Labels/datasets stay40,960+20,480+20,480 /40,960,61,440,81,920.
Before cache hits the new full-C ceiling is81,920 rankings,2,211,840 candidate
trajectories,8,847,360 modeled ticks,176,947,200 candidate power links plus
8,192,000 setup links. New C7 rankings/model calls are zero. Helper requests
are at most122,880, with17,203,200 setup/extreme power links at the declared
20-user/four-peer bound. Neural collection/evaluation is at most81,920 row
forwards outside optimization, including10,240 fixed sampled draws. All actual
counters remain recorded, without crediting theoretical savings as timings.

The64 retained controls represent16,384 already-paid native ticks; keep their
original cost identities separate from new exposure. Their timings are historical
instrumented package costs, not contemporaneous paired microbenchmarks. The
saved-data reader will verify384 new files plus64 retained controls (98,304 new
and16,384 retained recorded ticks), all new lineage assets, model/data/shuffle
counts and complete mixed-provenance contrasts. It performs0new native steps,
0expert/radio-model queries,0actor forwards and0optimizer calls. No additional
source-policy or endpoint-agreement diagnostics are added. Worker1–3CPU minutes
and reader5–15CPU seconds are planning estimates anchored to B02's101.990 and
5.553 CPU seconds; engineering/review/support is estimated30–90elapsed minutes
for planning, not formally metered labor or a deadline. Actual memory/resource
admission remains required on the preferred primary node; reasoning/editing does
not await a fresh resource probe.

The same point screens and complete metrics remain operative. Both modes again
competent would strengthen the case for a separately specified reward-continuation
comparison; greedy-only competence would retain deterministic construction while
weakening the sampled-start premise; failure would weaken recurrence while
preserving the old asset, with no automatic repair. Loss of sampled surplus while
near-C competence survives would narrow the surplus story without erasing
inheritance. Read intervals, minimum service, all world/tail losses, quality,
path and full cost even when the point rules pass. Two exploratory lineages on
one development panel do not establish a population or training-seed guarantee.

**L0.** Add a bounded B03 admitted wrapper, contract, retained-control loader and
saved-data integration under the owned `b03/` implementation/test directories;
future output is `runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/`.
Keep all B02 source files byte-unchanged and reuse its collector, actor, optimizer,
per-episode saved-data checker and metric reductions. The new orchestration
must separate384 new rows/counters from64 retained rows, bind all six comparison
arms honestly and preserve failed/partial new exposure. No monkeypatch of B02
globals, output substitution, synthetic production summary or source worktree
copy is permitted. The canonical old output remains read-only.

A bounded Implementer may own only the strict retained-control loader and its
new focused tests; DM owns contract, runner/reader integration, notebook and Git
index. All edits stay on shared main with disjoint paths, no helper staging,
launch, scientific choice or children. Appropriate prior numerical/collector/
optimizer/RNG review is reused because the underlying bytes are unchanged; the
independent engineering Reviewer checks new source/control binding, seed isolation,
collection order, mixed-provenance accounting, failures and reader coverage.
Synthetic complete-pipeline and corruption checks suffice for the changed layer;
no new native pilot is required. Exact inputs are published before actual-node
admission. Observe the accepted handle without a duplicate launch, then fully
read, independently diagnose, publish and clean this single selected study.

### B03 implementation and independent engineering acceptance

The DM accepted the bounded Implementer's `retained.py` and focused tests, then
integrated the admitted B03 wrapper and saved-data reader. All seven B03 modules
reuse the byte-unchanged B02 numerical/collector/optimizer kernels. Retained
metadata, all15 source identities, runtime/host/thread settings and all64 raw
control hashes are checked before the new environment constructor. Four new arms
have separate rows/costs; the source-bound historical control rows are read-only.
Reset comparison preserves any already-completed new row before reporting a
mismatch. Inflight failure accounting preserves the actually paid partial work.

The DM's complete B03 test invocation passed **52 tests in4.55s**; the independent
engineering Reviewer read all seven modules and both test files and independently
passed the same52 tests in3.64s, with **no material finding or requested repair**.
Coverage includes a complete old synthetic lineage/reader bound to a fresh
synthetic lineage, all new/retained saved-file verification with scientific calls
forbidden, unchanged source/protocol/runtime rejection, metadata/raw corruption,
wrong sampling draw/endpoint, production admission, preconstructor rejection,
completed reset-mismatch exposure and partial-episode failures. These are
nonscientific fixtures; no new native episode or result fit has yet occurred.
Original B02 byte identities and all five production metadata pins were checked.

The residual local coverage limit is explicit: production64 raw trajectories and
the original primary-node runtime are available only on that node. The accepted
worker's retained-input guard will check both before any native construction;
failure leaves zero native exposure and does not authorize added control episodes.
No new native smoke/pilot, architecture change or repeat of unchanged B02 tests is
needed for this outer-layer integration. The source is ready for exact publication
and the already-selected one-fit actual-node admission.

### B03 pre-admission path refusal and bounded entrypoint correction

Inputs `4bc0c28a5f088401702d0c17d34bd3edf1afd3dd` were pushed and verified on
published main. The first primary-node outer task
`fleet-b03-inheritance-recurrence-a01-20260930` ended with launcher refusal/exit4
at2026-09-30T16:47:16Z, before any claim or native admission:
`absolute author input is absent from published snapshot:` followed by the
canonical B02 run directory. Inspection confirmed **no B03 output directory,
no matching claim, zero native episodes and zero scientific fits**. The launcher
had created only the source copy
`.git/hmasd-launch-sources/08587f6b1f25416c858f8bbc5f020e6f`, recorded for
exact unclaimed-source reclamation. The original B02 evidence is unchanged.

The cause is the launcher's generic remapping of absolute author-tree CLI inputs
to the published source snapshot, where retained raw bulk deliberately does not
live. The bounded fix removes the input-path CLI override and places the already
declared canonical B02 root directly in the B03 entrypoint's published source.
After admission it passes that fixed locator to the unchanged strict retained
loader. The five original metadata pins, all retained raw/source hashes, actual
host/runtime/recipe checks and canonical manifest root binding still precede
native construction. No shared launcher change, evidence move/copy, control
reevaluation, identity/recipe change or scientific retry is involved.

The two affected CLI checks passed in1.56s after the correction: absent admission
has no effects; mocked admitted entry passes only the source-bound canonical root
and rejects an input-path override. The other52-test coverage and unchanged
kernel review remain applicable. A focused independent engineering acceptance
is required before publishing the corrected entrypoint and making the first
admitted scientific attempt. The primary repository's pre-existing Git repack
warning (`dfe82c...` missing tree) did not prevent fetch/source publication and
was not altered.

Observer generation15 had been armed before the manifest returned; its missing
handle probes produced BLOCKED event`f848aafc39d8768bcb0984f7` and rejected
native-child queue wake`cb81cc4a-52dd-43da-a60f-8b706450bad6` (`-32600`). The
observer was stopped and the failed request reconciled as above. The native DM
stayed active. Only after an actual accepted manifest will this same observation
job be rearmed/resumed; registration alone is not acceptance.

The independent engineering Reviewer inspected the exact correction against
`4bc0c28a5`, independently passed both CLI checks in1.38s and found no material
issue or requested repair. The DM accepts this correction; production-node
loading remains guarded and the original review's local coverage limit remains.

### B03 native acceptance and collection handle

Corrected exact inputs `4909c9553300a4a4de6eb79476e818d7b1ceab53` were pushed
and verified on published main before execution. After reconciling the earlier
pre-admission refusal, the configured primary-node launch accepted the single
scientific attempt at2026-09-30T16:52:03Z. Its original handle is
[launch-manifest.json](../../../../runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/launch-manifest.json)
in canonical node directory
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/`.
The manifest records the accepted operation/claim, source snapshot, native
identities and exact command; the output remains outside that snapshot.

Fresh actual-node memory was14,683,291,648 effective available bytes against the
4,294,967,296-byte floor. Before environment construction the retained loader
successfully checked all64 original control raw files (5,519,228 bytes), all
bound metadata and unchanged source/protocol/host/runtime/thread settings.
This discharges the production-availability coverage limit; it is not a new
ordinary-control evaluation. Initial collection then progressed normally.

The same observation job was rearmed as generation16 against the accepted output
handle, consuming the earlier blocked event and explicitly resuming that resolved
job. No worker was restarted by observation. The native DM keeps the turn active
through terminal evidence, saved-data verification and scientific reading.


<a id="b03-complete-reading"></a>
## 2026-09-30 — B03 complete reading: competence recurs in the second lineage

The exactly selected second training lineage is complete and fully read. Both
fixed final-greedy and T=1 sampled starting-asset point screens pass again; BC
alone again fails the three numerical margins. This strengthens finite
construction recurrence on the **same exposed development panel**, while retaining
both learned assets. It does not establish training-population reliability,
confirmation, C equivalence, a speed gain, uniquely learned stochastic value or
benefit from later reward training. The original B02 asset is not replaced or
selected away, and the B01 A/F recipe remains ended.

Exact source is `4909c9553300a4a4de6eb79476e818d7b1ceab53`. The original
[summary](../../../../runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/summary.json),
[saved-data reading](../../../../runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/reading.json)
and [configuration](../../../../runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/config.json)
retain every row, source/asset identity, fixed screen, contrast and cost, including
all losses. Summary is1,642,602bytes/SHA256
`5cdd13908d74133719ebc8cf923f30ccf36830c56b3954774bca7b3e16fdbb08`;
reading is282,682bytes/SHA256
`b0c4943bb0b7fe8b7ac70d21f64a8d6805b086815789d35ba3992746aa6a5c20`.
All seven compact JSON records were collected unchanged and locally hash-verified;
no bulk copy was made.

### Exact exposure and saved-data completeness

The new operation contains1fit,256 training plus128 neural evaluation episodes,
98,304 native steps,8,000 continuous-Adam updates and4,096,000 sample
presentations. Fresh training worlds/init/shuffle obey the prospective identities;
the32 evaluation worlds and addressed sampling innovations intentionally remain
those already exposed by B02. Exactly64 old C/C7 control episodes/16,384 ticks
are reused as already-paid evidence, with unchanged host/protocol/source/runtime
bindings and matching initial-state identities. They are not new episodes,
independent control replication or contemporaneous timing measurements.

The native worker and supervisor exited0 and were absent under their original
identities. Generation16 returned READY event`3323249f4d9da78f71005455`; its
native-child queue wake`8d5eff89-c0f1-4a0c-9630-379c76cba159` was rejected
(`-32600`), so the active DM directly drained the same evidence. The event was
consumed in generation17 and observation stopped. No worker was restarted.

The same-source detached reader `fleet-b03-read-a01-20260930` exited0 at
16:55:18UTC. It verified all384 new NPZ files plus64 original control NPZ files,
all four new checkpoints,98,304 new and16,384 retained recorded ticks, and
122,880 new plus20,480 retained decision records. Checks cover fixed row/order/
reset/hold/action identities, lawful features/navigation, paid labels/rankings,
memoization, fresh draws, native score/service reductions, parameter tensors and
recorded data/shuffle/optimizer continuity. The reader performed **0 native steps,
0 expert/radio-model queries,0 actor forwards and0 optimizer calls**. This is
saved-evidence validation, not a replay of all physics or neural arithmetic.

### All fixed endpoints and contrasts

Native J is `.7*served/50 + .3*quality`; path is not penalized by that objective.
Service p10/minimum are within-episode temporal summaries, averaged over worlds.
C and C7 below are explicitly retained B02 observations. Each row has32 worlds.

| Arm | J | Mean service | Service p10 | Minimum service | Quality | Path(m/UAV) |
|---|---:|---:|---:|---:|---:|---:|
| S0 | 0.084190 | 5.011841 | 5.000000 | 5.000000 | 0.046749 | 50.441795 |
| BC | 0.316040 | 18.623657 | 18.312500 | 11.062500 | 0.184363 | 1734.263316 |
| S_greedy | 0.354697 | 21.357910 | 20.468750 | 11.125000 | 0.185621 | 2462.523601 |
| S_sampled | 0.397281 | 24.465698 | 21.546875 | 10.562500 | 0.182537 | 3569.175088 |
| C_memo | 0.340733 | 20.351685 | 19.781250 | 11.000000 | 0.186031 | 2578.514211 |
| C7_memo | 0.328562 | 19.480957 | 18.656250 | 10.281250 | 0.186095 | 2522.027695 |

Both final modes meet the fixed point rules: ΔJ≥−.01, Δservice≥−.5,
Δmean service-p10≥−1 and no newly zero-service world relative to C, with actual
learning and positive final-greedy−S0 mean J/service. These research tolerances
are not established population noninferiority margins or deployment preferences.
All non-S0 arms have zero zero-service ticks; S0 has zero-service ticks in6/32
worlds. The new untrained actor's mean service5.011841 differs substantially from
B02 S0's.754883, so initialization behavior itself is not stable across the two
lineages. Final competence recurs despite that difference.

All nine fixed comparisons follow. Intervals are descriptive paired-world t95
conditional on the fitted policy and exposed world/innovation panel; they do not
turn32 worlds into32 training replications. The retained C7−C comparison is the
same original evidence, not a second observation of that difference.

| Contrast | ΔJ [descriptive t95] | J gains/losses | Δservice [descriptive t95] | Service gains/losses |
|---|---:|---:|---:|---:|
| S_greedy-C_memo | +0.013964 [-0.003771, +0.031699] | 17/15 | +1.006226 [-0.219923, +2.232374] | 18/14 |
| S_sampled-C_memo | +0.056548 [+0.035926, +0.077170] | 30/2 | +4.114014 [+2.632084, +5.595944] | 28/4 |
| BC-C_memo | -0.024693 [-0.048004, -0.001382] | 11/21 | -1.728027 [-3.434511, -0.021544] | 12/20 |
| C7_memo-C_memo | -0.012171 [-0.026843, +0.002501] | 10/22 | -0.870728 [-1.930474, +0.189019] | 11/21 |
| S_greedy-S0 | +0.270507 [+0.239256, +0.301758] | 32/0 | +16.346069 [+14.231117, +18.461022] | 32/0 |
| S_greedy-BC | +0.038657 [+0.010912, +0.066402] | 22/10 | +2.734253 [+0.732099, +4.736407] | 21/11 |
| S_sampled-S_greedy | +0.042584 [+0.025635, +0.059532] | 25/7 | +3.107788 [+1.878554, +4.337022] | 26/6 |
| S_greedy-C7_memo | +0.026135 [+0.007707, +0.044564] | 23/9 | +1.876953 [+0.549682, +3.204224] | 22/10 |
| S_sampled-C7_memo | +0.068719 [+0.048384, +0.089054] | 30/2 | +4.984741 [+3.511135, +6.458347] | 31/1 |

Greedy−C has positive panel means but15 J-loss and14 service-loss worlds, with
both mean intervals crossing0. Its service-p10 difference+.687500 has14 losses
and an interval[−.704912,+2.079912]. Sampled−C has30 J gains and28 service gains,
but two J losses, four service losses and10 p10 losses. Its mean p10 improves
+1.765625[+.174199,+3.357051], while mean minimum service falls−.437500
[−1.091089,+.216089], with11 lower,9 higher and12 tied minima. B02's stronger
minimum-service adverse (21 lower worlds,−.781250 mean) remains intact.

The complete32-world vectors were read, not only the screen averages. For example,
greedy world29341007 loses.059991J/4.187500 users versus C; sampled world29341000
loses.034024J/2.710938 users and5 p10 users. Sampled world29341014 gains1.679688
mean users yet loses6 minimum-service users. Positive worlds also matter:
greedy29341006 gains.175116J/12.335938 users; sampled29341022 gains.188570J/
13.257813 users. Final−BC gains are not universal: greedy29341023 loses5.613281
users and29341026 loses.088228J. Full source rows retain every other adverse.

Sampled−C path increases990.660876m/UAV[+403.091930,+1578.229823], with24
longer worlds. Sampled−greedy adds1106.651487m[+518.492025,+1694.810948],
with23 longer worlds, and has13 lower minimum-service worlds. Greedy−C path
is−115.990610m[−788.665427,+556.684206]. Sampled quality−C is−.003494317
with an interval crossing0; the positive J difference comes arithmetically from
+.057596191 service contribution and−.001048295 quality contribution. This is
objective accounting, not identified causal mediation, energy use or safety.

### What changed and what remains unresolved

The fixed construction produced a second learned policy with consequential native
competence under the same lawful114-input/27-command interface. Initial/final
state digests differ,27,908 of34,715 parameters changed, and parameter displacement
isL2=38.936358. Final greedy beats its own S0 in J/service on every world.
This is finite learnability evidence for this supervised construction; it does not
prove a function-class equivalence, necessity of learning or a new learning method.
The actor omits full candidate ranking but retains the charged analytic radio/
navigation helper. Source-bound teacher labels, instead of privileged latent policy
inputs, were used on actual training histories.

Final−BC mean J/service and p10 improve with positive descriptive intervals in
this lineage, unlike B02's intervals crossing0. However, both additional data and
5,600 further updates intervene; aggregation-specific causality is still not
identified. Training datasets have40,960/61,440/81,920 rows but only4,106/5,718/
7,616 distinct feature rows (B02 ended with8,364). Paid optimization-stream CE
falls2.809177→.475400 in phase0, .948653→.496868 in phase1 and
.733950→.417305 in phase2. Ending streamed accuracies are.859375/.862858/
.884607; non-hover label recalls derived from the already-recorded confusion
matrices are.602049/.712168/.775314. These changing-policy training streams
are not extra frozen-endpoint evaluations or evidence of teacher agreement in
unseen deployment states. All70 epoch traces and confusion matrices remain in
the summary; no extra actor/teacher pass was purchased.

The sampled capability also recurs: it improves mean J/service over greedy while
retaining temporal/motion costs. Greedy/sample hover decisions are7,052/5,869
out of10,240 (C7,048); policy cache hits are8,957/3,899 (C9,267). This is
compatible with random departures changing stagnant/repeated trajectories, but
these correlations do not identify a sampling mechanism or learned coordination.
The common evaluation worlds and innovations constrain the new information to
an independent training construction under this panel, not fresh world/action
replication. No better-looking checkpoint/decoder is selected as a new default.

Before interpretation I reread current published RESEARCH topics2/4/5 and the
original ordinary-C parent-adaptation B03 complete/independent reading
([source](../uav_parent_adaptation/NOTES.md#b03-complete-reading), sourcea36f20e14,
summary6337f5e6). Its zero-fit I improves C in three different world blocks,
while active sampled learning degrades I. That evidence makes competent ordinary
randomization a concrete future comparison, without diagnosing our sampled gain
or contradicting this supervised construction. It also weakens any automatic
inference from a competent starting policy to useful reward continuation. The
cross-direction coupling comparison belongs to its assigned DM/Root allocation;
this study does not add its proposed/selected arms or assume its outcome.

### Full cost and retained evidence

Worker cost is88.505862wall/92.334372CPU seconds, peakRSS680,548KiB.
Reader cost is4.798155wall/5.167864CPU seconds, peakRSS510,668KiB.
The sequential worker+reader totals93.304017wall/97.502236CPU seconds.
Engineering/review/support and DM JSON reduction time are not fully metered;
these totals are not end-to-end labor or the cost of selecting the recipe. The
pre-admission refusal adds13s outer-task elapsed with0 scientific exposure.
B02+B03 together paid2fits/832 unique episodes/212,992 native steps/16,000
updates/8,192,000 presentations/163,840 label requests and205.046058 measured
worker+reader CPU seconds. B01's separate earlier adverse investment remains
recorded; it is not erased from the broader question's cost.

New full-C training work has81,920 requests,74,298 hits and7,622 misses,
205,794 candidate trajectories,823,176 modeled ticks,2,753,568 candidate power
links and27,920 setup links. New C7 calls are0. Analytic helper work has16,350
calls,68,652 setup and126,138 extreme power links. Neural rollout/evaluation
work has12,244 forward rows and10,240 freshly addressed sampled draws.
These are recorded actual counts; dense optimizer forwards are separately charged
through4,096,000 presentations. Retained ordinary-control counters remain separate.

| Arm | Query CPU(s/episode) | Query wall(s/episode) | Full episode CPU(s) | Full episode wall(s) |
|---|---:|---:|---:|---:|
| S0 | 0.013815491 | 0.013008852 | 0.138016019 | 0.130848129 |
| BC | 0.018311040 | 0.017270090 | 0.158955337 | 0.150784222 |
| S_greedy | 0.022575915 | 0.021307299 | 0.165051122 | 0.156443884 |
| S_sampled | 0.091010506 | 0.085926141 | 0.245806668 | 0.232969560 |
| C_memo | 0.015968623 | 0.015357289 | 0.155697070 | 0.150621606 |
| C7_memo | 0.020899747 | 0.020068138 | 0.158985507 | 0.153254434 |

C/C7 timings in this table are historical measurements from the unchanged B02
operation. New greedy/sample query CPU is1.414×/5.699× the retained C figure;
this supplies no measured speedup and is not a contemporaneous latency experiment.
B02's original same-operation absence of a speed gain remains the relevant
contemporaneous evidence. C7's unfavorable mean/cost comparison is also unchanged.

One canonical unique B03 bulk copy remains at
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/`:
384NPZ files/41,553,732logical bytes and four assets/1,416,970bytes. Reused
64-control raw files remain only in their original B02 location, never copied
into B03. Final `assets/S.pt` is424,487bytes/SHA256
`cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d`,
tensor digest`c6286dd32097d37b2c2c3039e487a24b756398e3ddffa9dc9e1ec3ef66170699`.
The independent source-bound S0/BC/D1 assets retain lineage/exposure evidence;
the original B02 asset remains available for its actual cross-direction consumer.

Fresh-context ResearchCritic `b03_result_review` is independently reconstructing
this result and the original supporting/adverse sources. The factual reading
above is complete; final investment disposition, shared standing and measured
cleanup follow that independent diagnosis. No third lineage, extra evaluation,
PPO adapter or reward fit is selected by this result.


<a id="b03-independent-disposition"></a>
## 2026-09-30 — B03 independent diagnosis and final investment disposition

Fresh-context ResearchCritic `b03_result_review` has returned its complete
independent answer. It reconstructed B03 before reading the previous review or
the DM's interpretation, using the original B03/B02 records and the original
parent-adaptation B03 ordinary-positive and learned-adverse evidence. I read the
whole answer and accept its recommendation: **retain both conditional learned
assets, close B03 without another fit, and use the already selected comparison
with competent ordinary randomization to inform further investment.**
`MATERIAL_DISSENT: no`. This does not close the broader learning question.

### Independent reconstruction and limits

The reviewer found no consequential discrepancy. It independently checked all
22 B03 source hashes at the launch commit, the 15 unchanged B02 dependencies,
control metadata/runtime bindings, all 192 mixed-provenance evaluation raw
hashes and reductions, all arm means and nine paired contrasts, initial geometry
and users, lawful feature packing, four-tick holds, all-on masks, common sampling
innovations, all four new assets and the original B02 S identity. It read all
70 optimization traces, three recorded training trajectories, and positive and
adverse parent-adaptation trajectories. It did not replay host/radio physics,
actor forwards or optimizer arithmetic; broader training-array verification
uses the complete saved-data reader. No new scientific exposure was incurred.

The independent reconstruction confirms both fixed final-mode point screens,
actual parameter learning, greedy−S0 gains in every world, and BC's repeated
failure of the three numerical margins. These establish a second useful finite
construction under the lawful representation. They do not establish population
margins, policy-class equivalence, a reliable training program, unseen-world
replication, independent sampling-tape replication, speedup or benefit from a
subsequent reward-learning procedure. The two fitted lineages share all 32
evaluation worlds and their addressed sampling innovations; they are not 64
independent training observations. The better-looking B03 scores do not select
it over the frozen B02 asset.

The reviewer also read trajectory counterexamples to an overly simple movement
explanation. In world 29341006, sampled−C gains .189843 J while travelling less
(2,114 versus 4,841 m/UAV). In world 29341007, greedy loses .059991 J while
travelling more (4,721 versus 306 m/UAV). In world 29341014, sampled mean service
improves while its minimum drops from 17 to 11, with the sampled minimum at
tick 11. Increased movement is neither sufficient to explain the gain nor a
universal mediator. The complete motion, quality and temporal-service losses
in the preceding reading remain material because native J does not price path.

Training supports finite learnability but does not identify aggregation's
necessity. The reviewer found executed-action/paid-teacher disagreement on
195/320 and 65/320 decisions in two inspected aggregation episodes: labels do
address actual student histories. Final−BC nevertheless adds 40,960 labels,
5,600 updates and 2,867,200 presentations. Additional ordinary supervised
optimization remains a serious explanation for part of that progression.
Only 7,616 distinct feature rows underlie the final 81,920-label dataset; the
ending CE/accuracy are changing-policy training metrics. No attribution run is
needed merely to retain the constructed asset.

### Changed investment judgment

The prospective both-mode recurrence branch strengthened the case for considering
reward continuation. The complete result and current ordinary-control evidence
support a narrower next judgment: recurrence removes one construction concern,
but **does not itself prioritize a PPO adapter**. Parent-adaptation B03's I−C
gain and all three learned-endpoint deteriorations are actual competing evidence,
not a conjectured weak baseline. I gives +.023721 J/+1.709106 mean service across
three fresh blocks, while mean service-p10 falls from 19.53125 to 17.5; learned
sampled endpoints then average −.077879 J/−4.675252 service against I, with 93/96
J losses. Different panels and deployment laws prevent ranking that I against
fleet S using historical means. Its PPO failure does not refute this supervised
representation or reward learning in general.

The remaining consequential question is complete learned-distribution value
beyond competent ordinary stochastic control. A common-world comparison of
frozen S, ordinary randomized C and deterministic C would directly inform it.
The reviewer notes that a 32-world/two-realization core would cost 160 episodes,
40,960 steps and zero fits, but **that core is already contained in Root's
selected parent-adaptation B04** (416 episodes/106,496 steps/zero fits). Do not
launch a duplicate here or change B04's primary coupling question. Its declared
secondary `S_I−Q_I` contrast is relevant, with equally supplied public randomness
and ranks and its exact finite-decoder contract. Q is not a bitwise replay of old
I, and the two-draw S decoder is not B03's original inverse-CDF realization.
**Original B02 S remains the fixed B04 input; B03 S does not substitute.**

The independent recommendation preserves these distinct possible readings:

- A useful S−Q increment with acceptable declared service/motion/compute tradeoffs
  would strengthen conditional use and a specifically designed continuation.
- Comparable or better ordinary Q would weaken immediate investment in a learning
  adapter while leaving demonstrated inheritance intact.
- A useful coupling effect would establish conditional value of joint dependence
  under the supplied coordination rights, without establishing learned marginal
  superiority.
- Loss of competence on fresh worlds would narrow transfer expectations without
  erasing the observed training recurrence.

No third inheritance fit, architecture change, diagnostic sweep, extra endpoint,
temperature search or reward continuation is selected in this batch. A future
reward-learning comparison remains plausible but must include the unchanged
starting asset and competent ordinary stochastic control; merely beating S0 or
deterministic C is insufficient. Its horizon, update law, integration cost and
risk reading are not fixed by this result. The direction is reserve at this
completed assigned boundary, with no active producer, unread result or unresolved
scientific objection. Root owns any new cross-question allocation; B04 belongs
to its current DM and is useful incoming evidence, not an incomplete B03 task.
Distinct Pro advice would not improve this settled disposition, so no additional
consultation was sent.

### Bounded source feasibility supplied to Root's design reviewer

At `/root/deep_report_review`'s concrete request, I inspected current published
source only and returned one native factual answer. No code, model forward,
native step or fit was added. The unchanged 114→128→128→27 Student can be paired
with the ordinary centralized 136→128→128→1 critic in
`ucope/uav_motion_prefix_b01/policy.py`, keeping `critic_features`' global state
and commitment features out of the actor. The parent B03 collector/update are
not callable unchanged: they require 120-input C context, current C indices,
`actor(context, c_index)` and table/MLP parameter groups. A direction-owned
adapter would need lawful 114-feature rollouts, sampled indices and old log
probabilities, 64 sums of four native rewards per H256 episode, differentiable
Student replay, fresh actor Adam and a new critic/Adam. Existing StudentPolicy
stores detached logits and uses float64 NumPy temperature-one inverse-CDF
sampling; behavior/replay probability consistency and episode/version-local
caches need explicit checks. That is an integration task, not an actor-input or
architecture obstruction. The rough 2–4 elapsed hours for implementation,
meaningful tests and independent engineering review was an unmetered planning
estimate, excluding scientific design and execution, not an actual cost or a
selected continuation. This feasibility does not override the disposition above.


<a id="b03-final-cleanup"></a>
## 2026-09-30 — B03 final publication and measured cleanup

Useful implementation, tests and exact inputs were published before execution;
all seven compact original result records and the complete reading were published
at `6307afcc1e789b419c062491a9d45dce6b0691ab`. Independent scientific reading is
now complete. The source and readers remain useful evidence and are retained;
B03 imports the unchanged B02 kernels, and parent-adaptation B04 is a live
consumer of original B02 S and its policy interface. No unused new source
module was identified for deletion.

After checking terminal worker/reader status, stopped observation, durable
published source and live consumers, the supported snapshot collector previewed
and then removed the two exact B03 source snapshots under the node's shared
writer lock, with a complete elevated process scan. The first was an explicitly
unclaimed source-only snapshot from the reconciled pre-admission refusal;
the second was the completed accepted operation. The collector reported each
eligible and removed. No process, accepted operation or output was restarted,
moved or deleted.

All remote paths below are relative to
`hmasd-wsl-node:/home/wu/projects/HMASD/`. Allocated bytes were measured with
`du --block-size=1` immediately before and after deletion.

| Deleted target | Before allocated bytes | After |
|---|---:|---:|
| `.git/hmasd-launch-sources/08587f6b1f25416c858f8bbc5f020e6f` | 810,172,416 | 0 |
| `.git/worktrees/08587f6b1f25416c858f8bbc5f020e6f` | 3,551,232 | 0 |
| `.git/hmasd-launch-sources/b0033bf35d3f4325a8658255763ed430` | 810,180,608 | 0 |
| `.git/worktrees/b0033bf35d3f4325a8658255763ed430` | 3,563,520 | 0 |

Both trees and both Git registrations are absent. The remote net decrease is
1,627,467,776 allocated bytes. The output directories, accepted claim and original
exit/status records remain. Post-removal checks found all 448 B02 NPZ files/four
assets and all 384 B03 NPZ files/four assets still present in their single
canonical locations. Both original S file hashes were rechecked exactly:
B02 `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`,
B03 `cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d`.
This preserves B04's fixed B02 input and all positive/adverse lineage evidence.

The following exact local targets were untracked, had no live scientific/test
consumer and were deleted after checking their contents. Paths are relative to
`/home/fires/hmasd-wsl/`.

| Deleted target | Before allocated bytes | After |
|---|---:|---:|
| `temp/directions/uav_fleet_adaptation/` (only consumed B03 wait request) | 8,192 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b02/__pycache__/` | 98,304 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b03/__pycache__/` | 57,344 | 0 |
| `tests/experiments/candidates/uav_fleet_adaptation/b02/__pycache__/` | 32,768 | 0 |
| `tests/experiments/candidates/uav_fleet_adaptation/b03/__pycache__/` | 53,248 | 0 |

All five targets are absent. The local net decrease is 249,856 allocated bytes;
**B03 total net reclaimed is 1,627,717,632 bytes**. B01's 1,681,186,816 and
B02's 813,293,568 bytes remain separate prior cleanups (cumulative 4,122,198,016).
No backup, tarball, raw-data copy or retention chain was created. The sole bulk
copies and required compact evidence remain deliberately; there is no cleanup
blocker or outstanding target from this study. The unrelated pre-existing node
Git GC missing-tree warning is unchanged and did not block these removals.

The observer is stopped at generation 17 with zero unconsumed events. There is
no live worker/reader, unread advice, incomplete collection or selected further
study here. Own RESEARCH standing, result/next-investment reasoning and the
directly affected shared learnability background are updated with this closure;
other directions, their selected work and their source-bound inputs are preserved.

The design review later requested a cost clarification for a larger, still
unselected proposal: two retained-S continuations, each with 256 training
episodes plus 256 finite-calibration episodes, fresh endpoint comparisons with
exact duplicate reuse, and 20,480 additional frozen-S shadow actor rows. I
clarified that the earlier 2–4-hour estimate did not cover that complete
selection/evidence contract; roughly 4–8 elapsed engineering/review hours is a
more appropriate unmetered planning range, excluding science design, fits and
result reading. The extra work is checkpoint provenance, direction-owned
temperature/randomization wrappers, calibration-winner/tie rules without endpoint
leakage, exact reuse and paid-count accounting, old-logp/replay-law checks,
version-local caches, and saved-reader reconstruction of every candidate and
requested/physical change. Its stated maximum 512 continuation, 512 calibration
and 320 endpoint episodes is 1,344 episodes/344,064 steps before reuse; shadow
forwards add actor work but no native steps. This reply supplied feasibility
facts only; it selected no recipe, performed no extra exposure and did not alter
B03 closure or the independent investment recommendation.


<a id="b04-native-development-design"></a>
## 2026-09-30 — Prospective native development from both inherited policies: design only

Root's 17:27 UTC assignment retains this DM and the broader question: can useful
native behavior be developed from a competent learned local policy beyond both
unchanged sampled use and competent ordinary stochastic control? This entry
completes **scientific design only: 0 new fits, native transitions, actor/model
queries, calibration evaluations or result implementation**. B03 is closed as
recorded above. No third construction or continuation is selected. The existing
Root-assigned Astra Max Oracle owns the independent construction/investment
review; its complete original recommendation and subsequent corrections are
preserved below. I read that answer, checked its load-bearing primary passages
and actual source interfaces, and did not commission a duplicate review or Pro
request. Root retains the cross-question investment decision.

This proposed study is called fleet B04/native development only to distinguish
it from the parent direction's already selected **B04 joint sampling**. It does
not alter that accepted study, substitute B03 S for its fixed B02 S, change its
decoder, or purchase any extra evaluation within it.

### Question, current explanation and competing investments

The contribution sought is a **finite learning capability**: reward training
that improves the inherited command distribution under the same deployment
information and action rights. It is not a new PPO algorithm, proof of useful
hidden representations, or a requirement to establish every possible mechanism.
Full weight updates can change rankings and their dependence on observations;
temperature preserves those rankings, and uniform departures from C do not learn
which alternative command to use. Nevertheless, a gain from full updates could
come from a simpler global bias change. This comparison would not identify
state-dependent representation changes as necessary.

I used published RESEARCH main through `d6f50217c901ff76f000ae5b2fbbbb9aa7cd0717`
and the current assignment revision `40caac61a`, especially
[local information and competent ordinary alternatives](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
[finite learnability and retained inheritance](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面),
[parent adaptation and skills](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据),
[scope of empirical replication](../../RESEARCH.md#6-实证研究是在具体条件下缩小解释空间)
and [mathematical/game structure](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验).
Their concrete effects are to retain unchanged S and a paid competent ordinary
comparison, treat two fits as two exploratory constructions, price all native
and model work, and observe actual command/physical changes alongside scores.
Recent nonactivation or sparse-action findings in the peer forecasting work
support that last measurement; they supply no diagnosis of this actor's failure.
No reusable empirical background is changed by this design-only entry.

The immediate positive is B02/B03 finite local competence, with sampled gains
on their shared exposed development panel and all temporal/path adverses intact.
The immediate negative is parent B03: ordinary I improves matched C, while all
three sampled reward-trained endpoints deteriorate from I (93/96 J losses).
Different panels and decoders do not rank I against S. Earlier fleet B01 and
local-history failures also remain incurred; source competence does not erase
them or predict successful continuation. Entropy, credit, optimization and
visitation explanations of the prior loss remain unresolved.

The working conjecture is that a competent stochastic S may admit useful
native changes that exceed both keeping S unchanged and paying for a small
calibration. Its directional prediction is positive R−S and R−B* J on each
fresh panel, with changed distributions and consequential requested/physical
choices. These are uncertain predictions, not expected guarantees or an
activation threshold. Calibration explaining the useful behavior, reward
training damaging it, or different outcomes between lineages are substantive
answers. Parameter movement alone does not satisfy the prediction.

The recurrence reviewer preferred already selected parent B04 S_I−Q_I before
prioritizing an adapter. That remains a real **investment consideration**, not
a logical requirement that a frozen asset first beat Q before its developability
can be tested. Its exact two-draw finite-grid law differs from this original
private decoder, so its evidence will inform opportunity and cost without being
pooled into these treatment effects. The Oracle favors the complete direct
comparison below and declares material allocation dissent. My current preference
is to advance this fully priced comparison when Root allocates result work:
the paid ordinary calibration now addresses the major competing explanation
inside the complete experiment. That is a stronger case than the earlier vague
PPO extension. I would still use any available complete B04 result to revise the
investment ranking. This entry does not self-clear the allocation disagreement
or select execution, and a positive B04 S−Q is not an admission gate.

### Fixed assets, host and lawful decision interface

Both starting assets are used without choosing the historically higher score.
Their only canonical bulk copies remain on
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/`.

| Lineage | Canonical relative file | Published scientific source | File SHA256 | Actor-state SHA256 |
|---|---|---|---|---|
| 1 / original S | `b02_inheritance_a01/assets/S.pt` | `e945483b85c7f8ddfc315c57f36938d6c14201c7` | `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a` | `6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c` |
| 2 / recurrence S | `b03_inheritance_recurrence_a01/assets/S.pt` | `4909c9553300a4a4de6eb79476e818d7b1ceab53` | `cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d` | `c6286dd32097d37b2c2c3039e487a24b756398e3ddffa9dc9e1ec3ef66170699` |

Each file is 424,487 bytes. A future implementation must verify file, architecture,
dtype and tensor identities before environment construction, load actor tensors
strictly, and discard inherited supervised Adam state. Both originals stay
immutable. Original B02 S remains the fixed parent-B04 input independently of
this proposal.

Host: source-bound native N5, 50 static users, all transmitters on, H=256,
27 original motion commands, simultaneous decisions at ticks 0,4,…,252 and
four primitive transitions per commitment. There are 64 team decision clocks
and 320 agent decisions per complete episode. No roster, horizon, energy price,
reward, public coordination signal, command support or commitment change is
introduced. All 27 **requested categories** remain valid even when commands
alias after clipping at a boundary. Analytic eligibility is a feature and part
of ordinary C's behavior; it is not a learned-action mask or a rule that skips
training rows.

The Student stays `114→128 ReLU→128 ReLU→27`, FP32, all 34,715 parameters
trainable for R. Its feature row is the 103 entries `obs[:103]` of the native
104-vector (excluding its last clock entry), ten-way one-hot own pre-decision
navigation state, and the original binary analytic eligibility feature.
`initial_nav`, `analyze` and the original navigation transition operate on each
policy's own actual trajectory. Keep the helper's charged local radio work.
No current C command/ranking, global/user map, peer action, critic input,
episode identifier, training-progress feature or future observation enters the
actor. Separate arm/episode/version caches may reuse deterministic analysis or
logits only; no sampled command or navigation state carries between histories.
S and R can request any category during ordinary fallback, just as in B02.

The design binds the unchanged B02 source map already recorded in its original
summary, rather than reconstructing a replacement controller. Consequential
current file digests checked without executing a model are:

| Source | SHA256 |
|---|---|
| `experiments/candidates/uav_fleet_adaptation/b02/model.py` | `c9b95b6718262c65591ed106ca81da0abb15b48ef6a8439438618365efc39934` |
| `experiments/candidates/uav_fleet_adaptation/b02/controllers.py` | `a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522` |
| `experiments/candidates/uav_fleet_adaptation/b02/policies.py` | `fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd` |
| `experiments/candidates/uav_fleet_adaptation/b02/collect.py` | `62a691a3d2b3e0579b84aca73b64fe61cdc11aee64ac2bd2d298db6ba59b44ef` |
| `envs/pettingzoo/uav_env.py` | `fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` | `fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py` | `e324640251d0d025549705ff7541b765e7b96733f422c48ee9c2f5bd07709614` |
| `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py` | `466ec7b0efabdf474f838b662e781a2b7a3b5e1c1a41096b6ccf0f00eb0471f1` |
| `experiments/candidates/uav_parent_adaptation/b03_c_prior/update.py` | `e3e5b45572bea389870cc78b78b66af304fd0f1f0890e3f884bae55a9035b650` |

The last source supplies an update pattern, not a callable unchanged adapter:
it expects 120-feature C-prior contexts, C indices and table/MLP parameter groups.
Its collector also queries full C. A new direction-owned collector must instead
save 114-feature Student rows, old behavior densities, team rewards and separate
critic inputs without C queries for R. No such implementation exists or is
commissioned by this design entry. Exact source inputs for any later selected
implementation must be committed and published before result execution.

### Behavior probabilities and differentiable replay

The original operational Student law is retained. For each feature row, run the
FP32 network on shape `(1,114)`, yielding 27 FP32 logits. Convert those logits
to NumPy FP64; for temperature T form `exp(z/T−max(z/T))` and divide by their
FP64 sum. Use FP64 cumulative sums with the last entry set to exactly one, and
`searchsorted(..., side="right")`. The private draw is the original
`default_rng(SeedSequence([sampling_root, world_seed, tick, agent])).random()`.
Draw afresh at every decision, including cache hits. Greedy S uses the original
first-index `argmax`; it is deterministic. R and unchanged sampled S always use
T=1 for collection/final comparison. There is no Torch multinomial replacement,
probability floor, hidden temperature, eligibility mask or hold-dependent draw.

For C with departure ε, put `1−ε` on that arm's actual memoized C category and
`ε/26` on each other category, and use the same inverse-CDF/indexed-uniform law.
At ε=0, execute deterministic C directly. The category ordering is the original
27-command ordering, not C's ranking order. MemoC's full ranking and fallback
competence remain available and charged. Q denotes precisely ε=.10 here.

Differentiable replay uses one-row FP32 network calls on the saved feature rows,
stacked without changing their individual forward shape, followed by the FP64
stable exponential/normalization in Torch. Store collected chosen probabilities
and log probabilities in FP64, not the parent updater's blanket FP32 cast.
The ratio is the new nominal categorical probability divided by the saved old
one, mathematically equivalent to `exp(logp_new−logp_old)`. The gradient flows
from that FP64 objective into FP32 actor parameters. The immutable first epoch
before its first update also provides the already-paid density check: identical
FP32 logits; maximum absolute probability discrepancy ≤5e−14; chosen-logp
and ratio-from-one discrepancy ≤1e−10. The NumPy/Torch FP64 libraries need not
be bitwise identical. This tolerance is an engineering requirement to check
on fixtures and the existing first epoch, not permission for an extra pilot.
Nonfinite losses/gradients or a failed initial identity check preserve the paid
prefix as technical incompleteness; they do not authorize replacement exposure.

The smooth categorical probability is the explicitly chosen PPO surrogate
density. The operational sampler still has FP64 cumulative rounding and the
PRNG's 53-bit uniform grid. We do not claim that differentiating the smooth
density is the exact derivative of that finite-bit decoder's piecewise-constant
induced masses. Both interfaces, old densities and innovations must be saved,
so that this numerical convention is explicit and replayable rather than a
silent treatment change. This remains the original B02 deployment law; parent
B04's two-draw finite-grid construction is not imported.

### One fixed reward continuation per initial asset

Each R consumes exactly 256 complete episodes, in 128 ordered groups of two,
with no checkpoint selection, minibatch shuffle, episode replacement or extension.
Both episodes in a group use the same fixed actor version. Each group then has
four full-rollout epochs: 512 actor and 512 critic Adam steps per lineage.
Caches end with an episode and are invalidated at every actor version.

The fresh centralized critic is the existing FP32 `136→128 Tanh→128 Tanh→1`
network (34,177 parameters). Its 136-vector consists of native 116-vector
global state, five previous three-vector commands and five remaining holds;
the holds are zero at these synchronous decision clocks. Previous commands
start at zero vectors on reset. The actor never receives this vector. Collect
critic values under the current group version; targets and advantages remain
detached and fixed across its four epochs.

Use separate fresh actor and critic Adam optimizers: lr=3e−4, betas=(.9,.999),
eps=1e−8, weight_decay=0, amsgrad=False, foreach=False, fused=False, and separate
gradient-norm clipping at .5. Each epoch updates actor then critic. There is
no schedule, supervised optimizer state, teacher loss, parent KL, reward
shaping or entropy term (entropy coefficient exactly zero).

At clock t, sum the four native team-J rewards in FP64 and store that macro
reward. For the update, convert rewards/values/critic inputs to FP32 as in the
existing return machinery. Target G_t is the undiscounted complete suffix sum
of macro rewards divided by 256, with zero terminal bootstrap. Advantage is
the saved `G_t−V_t`, detached and standardized across the 128 **team** decision
rows using population standard deviation plus 1e−8. Every agent at a clock
receives that same standardized advantage; no eligibility/event mask drops a
row. Fixed feature/critic tensors remain FP32; saved old action densities and
the actor ratio calculation remain FP64.

For row t and agent i, let ρ_ti be the requested-category ratio. Actor loss is
the negative mean over 128 rows of the **sum over five agents** of
`min(ρ_ti A_t, clip(ρ_ti,.8,1.2) A_t)`. It is not clipping a product of five
ratios. Critic loss is `.5 * mean((V_new−G)^2)`. Save every paid update's loss,
ratio/clipping/gradient and parameter-movement evidence, including a zero-gradient
step if it occurs; do not change counts to rescue low exposure. At the unchanged
policy the sum corresponds to the shared-policy team score terms, but finite
simultaneous clipped updates have no general multi-agent improvement guarantee.
This is a familiar complete finite training program, not an isolated test of
pretraining, representation, entropy removal or optimizer reset.

### Paid calibration, fixed random identities and final comparisons

For each lineage the simpler program receives 256 complete native episodes:
eight fixed candidates × 32 common worlds. In exact tie order they are
`C_0, C_.05, C_.10, C_.20, S_greedy, S_T.5, S_T1, S_T2`.
Choose B* using highest mean complete-episode native J alone, breaking an exact
tie by that fixed order. Retain all candidates and adverse metrics. The choice
is **one charged reward-based discrete calibration per lineage**, separate from
its actor–critic fit. No final-panel score changes it. This finite search is
a competent ordinary comparison; it does not exhaust ordinary adaptive policies.

The calibration worlds intentionally equal the first 32 worlds of that lineage's
256-world R-training list. R uses 256 distinct episodes while calibration
repeatedly compares eight choices on 32 worlds. This difference is part of the
comparison of equal-native-episode programs; it is not identical data use.
Training/calibration innovations are separate. The final panel is disjoint
from the entire training/calibration list and earlier development panels.
Two independent lineage lists and all domains are frozen as follows; a source
search found no prior use of these numbers before this entry (in particular,
the parent-B04 29346000 range is avoided).

| Identity | Lineage 1 | Lineage 2 |
|---|---|---|
| Ordered 256 R training worlds | 29350000–29350255 | 29352000–29352255 |
| Calibration worlds (first 32 above) | 29350000–29350031 | 29352000–29352031 |
| Fresh 32 final worlds | 29351000–29351031 | 29353000–29353031 |
| Fresh critic seed | 29354011 | 29354012 |
| Private training sampling root | 29354021 | 29354031 |
| Private calibration sampling root | 29354022 | 29354032 |
| Private final sampling root | 29354023 | 29354033 |

Run master seed is 29354000. If actor construction consumes a seed before strict
loading, use 29354001/29354002 within a separate saved/restored RNG scope; all
actor tensors are then overwritten and critic initialization uses its separate
seed. There is no shuffle RNG. Fixed world order supplies two consecutive
episodes per training group. Calibration runs world-major, cyclically rotating
the fixed eight-arm order by world index modulo eight. Each arm has its own
reset, navigation and cache. Shared calibration innovations pair its stochastic
candidates at the same `(world,tick,agent)` address without sharing trajectories.

Only after **both** R fits and **both** calibrations finish, collect per lineage
the fresh final panel for C, Q=.10, unchanged S_T1 and final R_T1, plus B* when
it is a distinct policy identity. Base arm order is C,Q,S,R, with a distinct B*
appended; cyclically rotate by world index modulo the number of collected arms.
All stochastic arms in that lineage use the final sampling root. Reuse the
already collected reference panel exactly when B*'s source, decoder, category
law, temperature and innovation identity equal C, Q or S. No equality of
observed actions/scores is sufficient for reuse, and no duplicated reference
is counted as replication. No R-greedy or additional temperature endpoint is
purchased. The final actor is always the 256-episode endpoint.

Primary readings are R−S and R−B* mean J in each lineage and their equal-weight
mean. Retain R−Q and R−C with their own meanings: a calibration winner may
transfer worse than a fixed constituent, so positive R−S/R−B* alone does **not**
establish improvement over Q or C. A claim beyond ordinary Q requires the actual
matched R−Q comparison. The Oracle explicitly accepted this clarification.
Also retain B*−S/Q/C and all within-calibration means, without using them to
rewrite the final choice. Report paired-world effects/intervals, per-world
losses, service, quality, temporal service p10/minima, zero-service worlds/ticks,
path per UAV, boundary effects and complete computational cost. Thirty-two
paired worlds per fitted endpoint estimate conditional evaluation variation;
the two fitted lineages, not 64 worlds, are the training-level observations.

### Priced behavioral reading and complete evidence

On each R final trajectory, query original frozen S on the **already collected
R lawful feature row**, including R's actual navigation history, and use the
same private uniform as R. Across both final panels this adds at most 20,480
frozen-actor forward rows. Save total-variation/distribution and modal changes,
requested-category disagreement, and whether the commanded physical path
differs. For the latter, replay only the known clipped kinematics from the
actual decision position: for four ticks, `x_next=clip(x+30*command, lower,
upper)` with lower=(0,0,50), upper=(1000,1000,150), comparing all four positions.
That is at most 81,920 deterministic shadow motion ticks, zero new radio work
and zero native counterfactual rollouts. This measures effective action exposure,
not S's reward on R's history or a causal gain from a particular hidden feature.

A future worker must preserve raw observations/features and pre/post own-nav
states, helper flags/counters, requested categories, logits/probabilities and
draws, chosen old densities, separate critic rows/values, four-tick native
rewards/physical motion, all complete native metric arrays, calibration choice
inputs, and each update's paid diagnostics. Record initial/final actor and critic
identities and final optimizer states, without selecting an intermediate actor.
All successful, adverse, inactive and technically incomplete evidence is retained.

The reader checks source/assets, all unique trajectories and reductions, resets,
feature packing, recorded eligibility/navigation, command holds and decoder
replay, fixed calibration winner/ties, exact-reference reuse and paid counts.
Endpoint/shadow actor replay costs at most 81,920 rows (61,440 in the C-winner
maximum branch). Reconstructing the shadow kinematics again can add 81,920
simple motion ticks to reader work. It uses no native transitions, fresh C/radio
queries or optimizer calls. All training/calibration stored density/update
records are read; this is not a full independent arithmetic replay of all
training actor forwards, helper radio calculations or optimizer updates.
Consequential numerical/source checks receive independent engineering review
if implementation is selected. Scientific interpretation uses the applicable
review at its result boundary; this design does not commission another one now.

### Prospective cost, feasibility and stop

Let k be the number (0,1,2) of calibration winners requiring a distinct final
panel. The complete program costs `1280+32k` episodes and `327680+8192k`
native steps: **two actor–critic fits plus two charged discrete calibrations**.
There is no per-fit allowance or automatic retry. The fixed maximum is below;
the minimum omits exactly the two duplicate 32-world panels and nothing else.

| Work | Proposed count / ceiling |
|---|---:|
| Two continuations | 512 episodes / 131,072 native steps |
| Two eight-candidate calibrations | 512 episodes / 131,072 native steps |
| Four mandatory final arms per lineage | 256 episodes / 65,536 native steps |
| At most two distinct B* final panels | 64 episodes / 16,384 native steps |
| Complete native maximum | 1,344 episodes / 344,064 steps |
| Actor / critic Adam steps | 1,024 / 1,024 |
| Actor / critic replay rows | 655,360 / 131,072 |
| Collected critic rows | 32,768 |
| Worker frozen-S shadow rows / simple motion ticks | 20,480 / 81,920 |
| Reader endpoint+shadow actor rows / simple motion ticks | ≤81,920 / ≤81,920 |
| New teacher labels | 0 |

Before memoization the C-heavy branch requests 143,360 C decisions, 3,870,720
candidate trajectories and 15,482,880 modeled ticks. Its maximum C power work
is 323,993,600 links. In that **same** branch 286,720 Student requests add at
most 40,140,800 analytic-helper links. One environment constructor plus every
reset and transition adds `(1+1344*257)*275=94,987,475` dense native power
slots, including A2A diagonal placeholders: **459,121,875 combined slots**.
These are work counts, not physical link events. Cache requests, hits, misses,
actual forwards, model trajectories/ticks and helper/native work must be
reported separately; ceilings are not claimed executed work.

The different S-winner branch maximizes Student requests at 307,200, so it must
not be added to the C maximum. Adding worker shadows, all actor update replay
and maximal reader replay gives ≤1,064,960 Student forward rows in that branch
(≤1,024,000 in the C-heavy branch). Critic collection plus update replay is
163,840 forward rows. These counts include work outside native transitions.

Runtime is unmeasured. Paid anchors are B02+B03 worker/read CPU 107.544/97.502
seconds, and parent C-prior approximately 589 CPU seconds including admission
through worker exit and its reader (worker-resource plus reader scope is about
588 seconds). They do not bound this differently replayed package. A working
planning range is **10–30 CPU minutes for worker execution and 1–5 CPU minutes
for the reader**, with substantial uncertainty from cache misses, one-row
autograd and artifact I/O. No runtime or speedup claim follows. Previous
inheritance peak RSS was about 665 MiB; 1–2 GiB is only an indicative future
worker reservation, not measured admission. Actual node availability comes
from the configured compute method when a result launch is selected.

The source-only engineering estimate is **4–8 elapsed hours** for the complete
direction-owned collector/update, calibration/decoder wrappers, immutable
provenance, exact reuse, saved reader, checks and independent engineering review.
It excludes current unmetered scientific design/literature work, execution,
and an indicative **1–2 elapsed hours** for complete scientific result reading,
independent diagnosis and publication. These are planning estimates, not a
deadline or measured labor. Raw storage is not yet measured; its packed schema
must preserve the named evidence. A later run retains one necessary durable
bulk copy and compact Git evidence, and cleans its unused source snapshot and
scratch only after checking consumers. This design created no run/scratch
artifacts or redundant evidence copies, so it has zero new deletion/reclamation
to report; B03's measured 1,627,717,632-byte cleanup remains separate.

Acquisition is already paid: B02+B03 are two supervised fits, 212,992 unique
native steps, 16,000 updates, 8.192 million presentations, 163,840 requested
labels and 205.046 measured worker/reader CPU seconds. If selected, acquisition
plus this proposal would be 540,672–557,056 native steps, four fits and two
discrete calibrations; this is not the whole project cost. Earlier fleet B01's
two fits/576,000 steps and parent-adaptation/other negative investments remain
separately incurred. Engineering, review and support labor were not metered.

No source implementation or launch is selected here. If Root selects the
proposal, a concise L0 will bind the direction-owned entrypoints/tests/reader
to this contract; unchanged shared kernels need no rewrite. Numerical/replay,
mask/alias, reset/hold, no-leakage, optimizer-count, source-binding, fixed-winner
and duplicate-reference checks are necessary engineering work, not extra
scientific exposure. Publish accepted exact inputs, admit on the actual node,
then observe the same accepted operation through complete collection/reading.
Technical failure preserves exposure and missingness; neither failure nor
completion adds replacement fits, worlds, temperatures or epochs.

### Outcomes and investment meaning

If R improves S and B* in both lineages, retain that conditional complete-program
development capability, checking the actual R−Q/R−C effects before claiming
ordinary-control superiority and reading every service/temporal/path tradeoff.
It establishes neither pretraining necessity, transferable features, aggregation
necessity, reliable training-population improvement nor superiority to every
ordinary calibration. Small positive point estimates alone do not compel
confirmation or expansion.

If R improves S but B* matches/exceeds it, reward learning has conditional value
while calibrated reuse has the stronger immediate cost case. If calibration
improves S and R fails, retain the calibrated capability and end this recipe.
If both fail, keep S/C/Q and the adverse evidence. Mixed lineage outcomes stay
mixed; do not select the favorable initial asset or call their average recurrence.
A J gain with temporal/service/movement harm remains an objective tradeoff:
native J does not charge path and this is no energy/deployment acceptance test.
Technical incompleteness is missing evidence, not zero gain or permission to
replace a lineage. No branch automatically selects more epochs, entropy tuning,
KL anchoring, a third lineage or another diagnostic experiment.

This completes the assigned useful preparation. The broader learned-development
question stays open; the next concrete owner of result allocation is Root. My
preference for this complete priced comparison and the recurrence reviewer's
different investment preference are both preserved. No approval request to the
project owner, fabricated external dependency or recurring idle check is added.

### Primary-source checks informing this design

I checked the following load-bearing passages independently of the Oracle's
summary. They constrain interpretation and interface choices, not admission:

- Foundations **P16**, metadata `docs/new-libs/corpus/papers/P16/metadata.json`;
  its indexed local PDF is absent. Primary [HATRPO/HAPPO §§2.2–3.1](https://arxiv.org/pdf/2109.11251)
  gives simultaneous-update counterexamples and a sequential construction under
  different assumptions. The ordinary individual clipped loss used here does
  not inherit that improvement result; clipping is no safety guarantee.
- Inst-sci **MARL-0018**, `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0018.json`
  and `pdf/MARL-0018.pdf`, PDF SHA256
  `bad31e7088ba67c0cfaedb72a2477fc03f473d8b6d29a2ea3ce821d376802615`.
  I read PDF pp.3–5, formulation and Algorithm 1 of [the primary article](https://ojs.aaai.org/index.php/AAAI/article/view/25973).
  Its correction addresses merged offline/online transitions. Here only weights
  are inherited and new training is on-policy; no replay model/correction is
  thereby justified.
- My-lib **icml-2024-pmlr-v235-wolczyk24a**, primary PDF
  `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-wolczyk24a/arxiv-2402.02868.pdf`,
  SHA256 `db3fd2b63ef0ad59cfc46a87fbf19e85181a860e3ae5df737b76974036f5a9e3`.
  PDF pp.2–4 of [the paper](https://proceedings.mlr.press/v235/wolczyk24a.html)
  support a forgetting risk and differing retention-method results in its studied
  settings. That is a relevant threat, not evidence that forgetting caused our
  prior losses or that KL anchoring is the next repair.
- [PPO §§3,5–6.1](https://arxiv.org/pdf/1707.06347) supports the familiar
  clipped-surrogate formulation and optional entropy term. Zero entropy here is
  a prospective package choice, not an empirical explanation of earlier failure.

These are direct source statements with the local inferences separated above.
The Oracle's July/external-round checks below remain its attributed checks;
I do not claim a new full historical audit or a novelty result. No paper,
adviser agreement or source feasibility observation supplies empirical evidence
that the proposed continuation succeeds.


<a id="b04-original-independent-recommendation"></a>
### Complete original Oracle recommendation and explicit corrections

Root-assigned independent Astra Max Oracle `/root/deep_report_review`, original
answer 2026-09-30 17:26 UTC, delivered unchanged to this DM at 17:30 UTC.
The following original answer is retained in full, including its overbroad world
identity sentence; the separately supplied correction immediately after it and
the source-bound design above resolve that sentence. This is advice, not a
selected operation or new empirical result. First-person statements in the
original answer refer to the Oracle.

---

**Recommend advancing the inheritance DM to one bounded native reward-development study using both retained S assets.** The question is whether reward training can improve their local command choices beyond unchanged sampled use and a paid, competent calibration of randomness.

The proposed ceiling is **two actor–critic training runs, two reward-based calibration selections, and 344,064 native steps**. The substantial investment is approximately **4–8 engineering/review hours**, according to the DM’s source-only assessment. This is a concrete exploration proposal, not an execution authorization.

I read the complete recurrence reviewer’s original answer before settling this recommendation. Its result diagnosis is supported: two competent supervised constructions now exist, but neither transferable hidden features nor useful subsequent reward learning has been demonstrated. I differ on the next allocation: the comparison below addresses ordinary randomization directly, so superiority of frozen S over Q in B04 need not be a prerequisite for testing developability.

The strongest evidence and objection are both consequential. B02 and B03 sampled S improve their common development-panel C means by approximately **+.04657/+ .05655 J** and **+3.353/+4.114 users**, respectively. Their temporal service and movement adverses remain. Conversely, ordinary randomized C already improves its own matched C comparison, while all three parent-adaptation reward-trained sampled endpoints deteriorate relative to their competent initialization. Thus competence supplies an opportunity for exploration, not a prediction that another learner will succeed. [B02 evidence](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b02_inheritance_a01/summary.json), [B03 evidence](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/summary.json), [parent-adaptation evidence](/home/fires/hmasd-wsl/runs/uav_parent_adaptation/b03_c_prior_a01/summary.json).

**The proposed additional capability is native improvement of the learned command distribution.** A full actor update can change action rankings and their dependence on local observations. Temperature calibration can only reshape the existing logits; ordinary C randomization distributes departures uniformly. Whether that additional flexibility is learnable and useful is the experiment’s question.

Use both assets without choosing between their historical scores:

| Initialization | Published source | Checkpoint SHA256 |
|---|---|---|
| Original B02 S | `e945483b85c7f8ddfc315c57f36938d6c14201c7` | `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a` |
| Recurrence B03 S | `4909c9553300a4a4de6eb79476e818d7b1ceab53` | `cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d` |

These are the canonical `assets/S.pt` files in their respective native run directories. Load their actor tensors exactly; retain both originals. B04 continues using its already fixed B02 asset.

The deployment contract stays the existing N5/H256 contract: 50 static users, all transmitters on, the source-bound 27 commands, and decisions every four primitive ticks. Each actor receives its **114 lawful features**: current local observation excluding its clock entry, its own navigation one-hot, and the charged analytic eligibility feature. Its navigation follows its own actual trajectory. No C command, global map, peer action, public coordination coin, or extra actor feature is added.

Sampling remains independent across agents, using the original addressed private uniform and float64 inverse-CDF categorical law. Evaluation uses fixed temperature one for both unchanged S and the reward-trained endpoint. Caches are private to the episode and actor version; cache hits never reuse sampled commands. This is a separate deployment contract from B04’s two-draw coupling comparison.

For each retained asset, train one complete continuation, R:

- **256 complete episodes**, with no intermediate checkpoint selection or replacement.
- Unchanged `114→128→128→27` Student architecture; all 34,715 actor parameters trainable.
- A fresh existing `136→128→128→1` centralized critic, used only during training. Its global state and previous-command inputs never enter the actor.
- Fresh separate Adam optimizers: learning rate `3e-4`, betas `(.9,.999)`, epsilon `1e-8`, no weight decay, separate gradient-norm clipping at `.5`. Discard the supervised optimizer state.
- Two complete episodes per collection group, followed by four full-rollout epochs.
- Sum the four native J rewards in each decision interval. Targets are undiscounted terminal returns divided by 256, without terminal bootstrap. Standardize detached advantages over the 128 collected decision rows.
- Use the existing agent-summed clipped surrogate, with individual requested-category ratios clipped to `[.8,1.2]`; critic loss is half mean squared target error.
- **Entropy coefficient zero**, no teacher loss, no frozen-parent KL penalty, no reward shaping.

Zero entropy is a prospective objective choice for an already stochastic starting policy. It does not diagnose the earlier C-prior failure. This is also a complete finite training package, not an isolated test of inherited features or optimizer-state reset.

The implementation must bind old log probabilities and differentiable replay to the actual float64 categorical probabilities used for collection. An unnoticed substitution of the earlier FP32/multinomial sampler would change the treatment. Numerical replay tolerance and initial-ratio checks belong in the engineering checks.

The simpler comparison receives an equal **256 native episodes per lineage**. Evaluate these eight fixed candidates on 32 common, newly generated calibration worlds:

| Family | Four candidates |
|---|---|
| Ordinary local C randomization | Departure probability ε = `0, .05, .10, .20`; probability `1−ε` on actual local C’s command and `ε/26` on each alternative |
| Frozen inherited S | Greedy, temperature `.5`, temperature `1`, temperature `2` |

All candidates execute on their own actual histories, using the same underlying local interfaces. C retains its full, memoized ranking competence. The S candidates retain their original analytic helper and acquisition cost.

Choose the calibration winner, B*, by mean native J alone. Freeze the candidate order above for exact ties. Retain every candidate’s positive and adverse evidence. This is a **charged reward-based selection procedure**, even though it performs no Adam updates.

I recommend using the first 32 worlds of each continuation’s prospectively fixed 256-world training list for calibration. The calibration procedure spends its budget repeatedly comparing eight fixed choices; R spends it adapting across 256 episodes. That difference is part of the comparison between finite programs, not a claim of identical data use. All seed lists, sampling domains and ordering must be frozen before new exposure.

After both continuations and both calibrations finish, evaluate, per lineage, on **32 fresh worlds**:

1. Deterministic C.
2. Ordinary Q with ε=.10.
3. Unchanged sampled S.
4. Selected calibration B*.
5. Final sampled R.

Within each lineage, use common world identities and addressed sampling innovations. Keep training, calibration and final evaluation identities distinct as declared, and use independent streams across lineages.

When B* is exactly C, Q, or unchanged S—including its source, decoder and sampling identities—reuse that study’s already collected reference trajectory. Do not purchase a duplicate or count it as replication. This gives **1,280 + 32k episodes**, where `k∈{0,1,2}` is the number of distinct calibration winners requiring another evaluation panel: **327,680–344,064 native steps**.

The primary readings are each lineage’s mean **R−S J** and **R−B* J**, with R−Q and R−C retained. Read service, quality, temporal p10/minimum, zero-service episodes and ticks, path, boundary effects, and complete computation alongside J. Report both lineage differences and their equal-weight mean. Paired-world intervals describe each fitted endpoint; 64 evaluation worlds are not 64 independent training replications.

To distinguish parameter movement from an effective intervention, price one additional observation in advance: on R’s final evaluation trajectories, evaluate frozen S on the **already collected lawful features** and decode it using the same private uniform. This costs at most **20,480 frozen-actor forward rows**. Record distribution change, requested-command disagreement, and whether four-tick clipped motion differs. The latter adds at most **81,920 deterministic shadow motion ticks**, without radio queries or native counterfactual rollouts.

Those shadows establish action exposure, not the reward that S would have obtained on another trajectory. They allow an adverse outcome to be distinguished from nonactivation or sparse physical change without buying a separate diagnostic experiment.

The plausible complete outcomes change the choice as follows:

- **R improves S and B* in both lineages:** retain a constructive native development result for this finite program. Examine service and temporal tradeoffs before proposing further investment. This would not establish pretraining necessity, transferable representation, or superiority to every calibration.
- **R improves S but is matched or exceeded by B*:** native learning worked conditionally, but the simpler calibrated program has the stronger immediate investment case.
- **Calibration improves S while R fails to improve it:** retain the calibrated capability and end this reward-training recipe.
- **Both development procedures fail:** retain the original assets and ordinary controls. Additional epochs, entropy changes or anchoring are not automatic repairs.
- **Mixed lineage results:** preserve the useful conditional positive and the adverse lineage. Do not select the successful parent retrospectively or present their average as reliable recurrence.
- **J improves with adverse service, temporal or movement consequences:** report a native-objective tradeoff. Path is not charged by J, and neither energy nor deployment acceptability has been established.
- **Technical incompleteness:** keep missing results explicit; do not replace a failed lineage or impute zero benefit.

This is exploratory. Small positive point estimates alone would not compel confirmation or expansion.

The complete prospective cost is material:

| Component | Maximum new exposure |
|---|---:|
| Two reward continuations | 512 episodes / 131,072 native steps |
| Two eight-candidate calibrations | 512 episodes / 131,072 native steps |
| Final comparisons | 320 episodes / 81,920 native steps |
| Total | **1,344 episodes / 344,064 native steps** |
| Actor / critic Adam calls | 1,024 / 1,024 |
| Actor / critic replay rows | 655,360 / 131,072 |
| Collected critic rows | 32,768 |
| Additional frozen-S shadow forwards | 20,480 |
| New teacher labels | 0 |

Before memoization, the feasible worst case requests **143,360 C decisions**, corresponding to **3,870,720 candidate trajectories and 15,482,880 modeled ticks**. Its C power-work ceiling is 323,993,600 links. In that same worst-case branch, Student helpers add 40,140,800 links. With one environment constructor and all episode resets/transitions, the dense native calculation adds 94,987,475 power slots: **459,121,875 combined slots** before cache savings. This includes native A2A diagonal placeholders and is a work count, not a count of physical communication links.

The separate maximum for Student rollout/calibration/evaluation requests is 307,200; it occurs under a different calibration-winner branch and must not be added to the C maximum. Shadow forwards and optimizer replay are additional, separately charged work.

The reader should verify all saved trajectories, source/asset identities, native reductions, sampling, calibration selection and duplicate reuse. Budget up to **81,920 endpoint/shadow actor replay rows**, with zero native transitions, fresh C/radio queries or optimizer calls. Training-density and update evidence can be checked from paid saved outputs; this does not claim a complete independent replay of optimizer arithmetic.

There is no measured runtime for this package. Existing inheritance worker-plus-reader costs were 107.544 and 97.502 CPU seconds; the older three-fit C-prior study cost roughly 590 CPU seconds. These are planning anchors, not runtime bounds. Cache behavior, training replay arithmetic, storage and reader implementation still affect cost.

The DM’s **4–8 elapsed engineering/review-hour estimate** covers the fuller package, including calibration, immutable provenance, duplicate reuse, density binding and shadow reconstruction. It excludes scientific design, execution and result reading. Source inspection found no architecture or information obstruction, but the current collector/update cannot be called unchanged: they require 120-input C-prior contexts and table-specific parameter groups. A direction-owned adapter and reader are necessary. [Student implementation](/home/fires/hmasd-wsl/experiments/candidates/uav_fleet_adaptation/b02/model.py), [existing policy interface](/home/fires/hmasd-wsl/experiments/candidates/uav_fleet_adaptation/b02/policies.py), [prior update implementation](/home/fires/hmasd-wsl/experiments/candidates/uav_parent_adaptation/b03_c_prior/update.py).

Acquisition remains incurred: B02+B03 used two supervised fits, **212,992 unique native steps, 16,000 updates, 8.192 million presentations, 163,840 requested labels and 205.046 measured worker/reader CPU seconds**. Earlier adverse investments remain separate sunk costs.

The literature supports this as a familiar, testable continuation—not an algorithmic novelty:

- **Foundations P16**, `docs/new-libs/corpus/papers/P16/metadata.json`: I read the primary §§2.2–3.1, including the simultaneous-update counterexamples and sequential improvement construction. **DIRECT:** a clipped shared-policy update does not inherit a general multi-agent monotonic-improvement guarantee. **INFERENCE:** retain an unchanged-asset comparison and permit an active negative result; do not treat clipping as protection. The indexed local PDF was absent, so I used the primary [HATRPO/HAPPO paper](https://arxiv.org/pdf/2109.11251).
- **Inst-sci MARL-0018**, `/home/fires/projects/Inst-sci/papers/MyLib/{json,pdf}/MARL-0018.*`: I read the load-bearing formulation and Algorithm 1. **DIRECT:** OTC corrects sampling from merged offline/online transition data. **INFERENCE:** it does not justify importing a transition model or replay correction into this weight-initialized, on-policy proposal. [Primary article](https://ojs.aaai.org/index.php/AAAI/article/view/25973).
- **My-lib `icml-2024-pmlr-v235-wolczyk24a`**, `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-wolczyk24a/arxiv-2402.02868.pdf`: I read the state-coverage/imperfect-cloning argument and retention experiments. **DIRECT:** fine-tuning can lose pretrained capabilities, with different retention methods helping different studied settings. **INFERENCE:** forgetting is a credible risk here, not an established diagnosis or a reason to prescribe KL anchoring without comparison. [Primary article](https://proceedings.mlr.press/v235/wolczyk24a.html).
- The proposed finite update uses the familiar clipped-surrogate construction; entropy is an optional objective term, not a required part of PPO. [Primary PPO paper, §§3–6.1](https://arxiv.org/pdf/1707.06347).

I also checked the relevant July G30/G31 records and the external fast-anchor treatment-identity clarification. They reinforce specifying the complete target, critic and optimizer package; their toy-family results do not supply a UAV repair. No novelty claim is warranted for imitation followed by native fine-tuning or scalar calibration.

At portfolio level, I favor this concentrated investment by the existing inheritance DM. It asks a capability question complementary to N8 control, C/V/R forecasting and B04 joint sampling. I have not independently reviewed the newly completed C/V/R or N8 results and do not use their preliminary returns to claim either direction is exhausted. B04 evidence can update the allocation when available, while its original asset and frozen primary question remain intact.

I performed source/document/literature inspection and cost arithmetic only. I reused the earlier consequential B02 checks and read the complete fresh B03 independent review; I did not duplicate its raw-result audit, execute models, or purchase new exposure.

**MATERIAL_DISSENT: yes — allocation only. I favor selecting this explicitly priced development comparison over the recurrence reviewer’s preference to await B04 before prioritizing reward continuation. Two competent constructions supply a real starting opportunity, and the proposed comparison directly tests the consequential ordinary-randomization alternative. B03 retention, closure and all accepted operations remain supported.**

---

Separate original clarification, 17:31 UTC, read and adopted by this DM:

> Separate clarification, preserving the original answer unchanged: calibration WORLD identities intentionally equal the first32 worlds of each lineage’s fixed256-world continuation-training list. The final32-world panel is fresh and disjoint from that entire training/calibration world list and prior development panels; lineage lists are independent. The later sentence asking all training/calibration/final identities to remain distinct was overbroad as to world identities. Please correct this explicitly in your source-bound design, alongside the original text. Calibration candidates share calibration innovations within each world; continuation, calibration and final sampling domains remain separately declared, with no endpoint information entering calibration or training. Own trajectories/caches never carry between arms or episodes. Costs and duplicate-reuse branches are unchanged. Your per-agent-clipped/common-team-advantage correction agrees with the law in the original final; I do not recommend changing it to a clipped joint-product ratio. The one-row FP32 deployment / float64 probability and replay issue is likewise an explicit engineering requirement there. Root’s current assignment is DESIGN ONLY; my original investment recommendation does not authorize execution.

DM follow-up identified that a calibration winner may transfer worse than fixed
Q/C. The original Oracle reply at 17:43 UTC was read in full and adopted:

> Agreed. Calibration selection does not establish holdout dominance over its constituent controls. The matched R−Q and R−C results retain their own meanings; R−S and R−B* alone support only those two improvements. Your refinement preserves the original exposure and strengthens the intended interpretation. The one-row FP32 / FP64 density binding is also consistent with the proposed asset semantics; engineering owns its numerical verification.

The DM design above implements these corrections without extra arms, exposure
or a new review. The independent investment dissent remains explicit for Root;
this completes the current design-only task and leaves B03's closed result,
canonical assets and already accepted parent B04 untouched.


<a id="b04-design-update-after-parent-b04"></a>
### Parent B04 evidence incorporated before returning the design

After the complete design was published at `8e855d43abb1c722ae231f048b59b635701d9dfe`,
Root directed incorporation of the now-published parent B04. I read its complete
[result and disposition](../uav_parent_adaptation/NOTES.md#b04-complete-reading),
the full original separate-context ResearchCritic answer, the saved primary
verdict and consequential S_I−Q_I contrast arrays in its original summary.
I also reread the newly updated RESEARCH topics2/4 on current published main.
Evidence is `c0a9ddc5a856e83c01583cd17afed3652cb16ef4`, scientific source
`e7225b0c7c428472b7349b6cce1f64fd42b97049`, with terminal cleanup at `2ef21e272`.
I reused the completed reader/independent raw audit; this added no model,
radio, environment or optimizer execution here.

The fixed primary S_A−S_I fails: J−.002998 [−.012536,+.006539], within-episode
service-p10−.609375 [−1.420082,+.201332], despite 3,051 physical departure
events and real suppression of coincident departures. Q_A eliminates simultaneous
categorical departures without improving mean J or service-p10. This supports
ending the specified A/B coupling recipe; it does not imply that coordination
is impossible, or identify departure coincidence as a reward mechanism.

The separate **predeclared** original-S_I−Q_I comparison is positive on 32 fresh
world blocks (two tapes averaged inside each block): J+.024074868
[+.008176152,+.039973585], service+1.767028809 [+.648007583,+2.886050034],
within-episode service-p10+3.546875 [+2.025238,+5.068512], and path−1232.241362
m/UAV [−1674.901922,−789.580803]. J gains in27/32 worlds and p10 in28/32;
world29346004 nevertheless loses .100149354J,7.037109375service and9.25p10
against Q_I. Its lower path does not erase that service loss. S_I−C's positive
p10 point still has an interval crossing harm. Favorable S−Q means across I/A/B
are correlated views of one fitted asset/panel, not three training replications.
Whole-team zero-service absence does not measure individual-user continuity.

This strengthens the **conditional usefulness of the original starting asset**
and weakens fixed .1 ordinary randomization as the complete explanation for its
native value. It leaves advantage over paid calibration, learnable reward
improvement, the necessity of imitation/aggregation, modal-versus-tail causality
and the causes of prior PPO losses unresolved. B04 creates no new learning
evidence and evaluates no recurrence-S continuation. Its two-draw finite-grid
decoder/common-device contract remains distinct from this design's original
private inverse-CDF law; its endpoints are not reused as new-study outcomes or
numerically pooled with them.

The original B04 ResearchCritic independently checked all416 episode identities,
all13 contrasts, source/asset/input identities,24 consequential raw episodes
and384 audit entries. It recommends retaining S_I/Q_I/C, ending A/B, and keeping
unchanged S plus competent ordinary stochastic control in a worthwhile future
development comparison. It explicitly does **not** endorse this separate fleet
proposal's detailed fits/calibration costs. I accept those limits and reuse its
judgment on the evidence alongside the already completed design Oracle advice;
there is no duplicate reviewer or additional Pro request.

The recurrence reviewer's requested B04 information has now arrived. That
investment consideration has therefore been addressed with a conditional
positive, without retrospectively making it a pass gate. My recommendation to
Root remains **select the complete two-asset reward-development versus paid
calibration comparison**, now with a stronger starting-capability premise.
The original allocation dissent remains part of the record; Root assesses the
updated recommendation and competing investments. I do not turn either positive
S−Q or the B04 review into automatic fit authorization.

No design arm, asset, seed, decoder, optimizer, horizon, calibration choice,
stopping rule or outcome interpretation changes. The prospective cost remains
two actor–critic fits plus two charged calibrations,327680–344064native steps,
20480worker shadow rows and at most81920reader actor rows, with all separately
priced model/kinematic/engineering work above. B04's already-paid cost is
0new fits/106496steps/115.438290worker-plus-reader CPU seconds; its engineering
and support are additional. Its reader's61440S forwards/13.723424CPU seconds
are another planning anchor, not a runtime guarantee for this larger collector
and one-row gradient replay. Current work still totals **0new fits/native/model
queries and no result implementation**. This closes the assigned preparation
with all evidence incorporated; no live operation or unread advice remains here.


<a id="b04-native-development-l0"></a>
## 2026-09-30 — B04 selected implementation L0

Root selected the complete `0816df3b7` design at
`1ab42997a5a805764d5c54e3fdd810fcc2fdf514`, after reading the full design,
original independent advice/corrections and both result reviews. The requested
parent-B04 information is now available; Root disposes the earlier sequencing
dissent without treating S−Q as an admission gate or new learning evidence.
This selection changes the prior design-only boundary. It authorizes exactly
the two immutable-asset continuations, two paid calibrations, strict reference
reuse, shadows and complete reading above, with no extra horizon, temperature,
replacement fit or automatic continuation. The current RESEARCH direction is
active and assigned to this native DM; the owner pause is lifted.

Deliver one guarded runner and saved-evidence reader under
`experiments/candidates/uav_fleet_adaptation/b04_native_development/`, with
focused tests at the matching `tests/experiments/candidates/` path. Planned
canonical output is `runs/uav_fleet_adaptation/b04_native_development_a01/` on
the configured `wsl_4070` node, CPU/one Torch and BLAS thread as for the bound
source assets. The immutable original S files stay at their current node paths.
Verify their file/tensor/architecture/source identities before any native
constructor. Production is admission-gated and frozen; dependency-injected
short fixtures are explicitly nonscientific and cannot use the production
protocol. There is no public resume/retry or science-changing CLI interface.

All scientific semantics, exact seeds and costs are the selected prospective
entry above. In particular: 114 lawful actor features on own histories; separate
136-input critic; original one-row FP32/FP64 inverse-CDF probability law; all27
requested categories including fallback/boundary aliases; four-tick commitments;
per-agent clipped ratios with common detached team advantage; fresh separate
Adam; fixed256episodes/group-of-two/four-epochs; paid calibration using only its
first32 training-world identities with independent innovations; both untouched
final panels collected after both fits/calibrations; only exact identity reuse.
Keep old densities FP64 and verify first-epoch identity using already-paid
replay. No C label/model call enters R collection. Save all native/density/update,
choice/kinematic/cost evidence and all successful/adverse/incomplete outcomes.

The DM owns protocol/asset guards, policy/collector, batch orchestration, reader,
integration tests, NOTES, RESEARCH and publication. A bounded Implementer may
own only `learning.py` and `test_learning.py`: the differentiable two-episode
Student continuation update and fresh critic/optimizers, with a pure array
interface to the collector. It owns no index, shared kernels, run, notebook,
model selection or launch. The interface accepts per-episode arrays named
`features`, `logits`, `probabilities`, `action_index`, `logp`, `critic_features`,
`values`, `macro_rewards`; production shapes are respectively64×5×114,
64×5×27,64×5×27,64×5,64×5,64×136,64,64. Exactly two episodes are stacked;
suffix targets reset at each episode. A `horizon` argument supports only the
runner's already-frozen protocol or a nonscientific fixture, not a production
override. Counts and all four epoch diagnostics return to the DM's runner.

Checks cover probability/gradient and initial-density identity, individual versus
joint clipping, all-action exposure, episode boundaries, detached critic targets,
fresh Adam and exact update counts; source/asset identity rejection before reset;
per-arm/reset/version cache isolation and fresh draws; complete native/hold
recording; calibration ties and final-panel separation; exact reuse versus
merely coincident outcomes; shadow requested/physical differences; reader
tamper rejection and the compact final reading. Use synthetic fixtures for
correctness, with no undeclared native pilot or canonical-policy queries.
Independent high-risk engineering review covers the integrated executable path.
The DM reviews the diff and checks and accepts it before publication/admission.

Author on shared main with disjoint writer paths and no helper Git index changes.
Scientific source, tests and exact inputs are committed/published together before
result effects. Node admission is fresh at the actual launch; it is not needed
for this implementation. The accepted handle then receives deterministic
observation through collection and full interpretation, without a duplicate launch.
Actual result cost remains the declared327680–344064steps/two actor–critic fits
and two discrete calibrations; tests, implementation, model/shadow/reader work
and unmeasured support are accounted separately. A material source contradiction
returns to Root; ordinary engineering corrections stay in scope. Any admitted
failure preserves its paid prefix and does not create a replacement allowance.

Implementation clarification, before execution: the final lawful feature is the
unchanged source's **fallback** bit (`1` means not eligible), rather than a
positive eligibility indicator. This preserves the inherited asset's actual
representation. The Implementer's first bounded update kernel returned18 passing
synthetic checks. After DM source review, the same helper receives a second
bounded behavior: a complete saved-evidence verifier in `read.py` and
`test_reader.py`, while the DM retains orchestration and integration tests. It
may replay only final Student and R-shadow rows within the priced81920-row
ceiling; training/calibration logits and update diagnostics receive algebra and
provenance checks, without replaying their actors, critics or optimizer steps.
Saved native-transition and fallback-ranking geometric checks are separately
counted reader arithmetic, alongside the at-most81920 shadow motion ticks;
they make no native, C-model or radio query. No scientific design or exposure
has changed, and actual new result exposure remains zero.

Before source publication or any fleet acceptance, Root explicitly changed this
study's execution allocation to configured `local_linux`. Its host `Jacob`
(AMD Ryzen7 8745H) and `wsl_4070` (i9-13900H) are distinct physical machines,
allowing the already selected waiting study's online wall-deadline operation to
use the latter independently. B04 has no online wall deadline. This supersedes
the preliminary `wsl_4070` placement and brief concrete resource wait; it is a
prospective allocation, with no failed/accepted fleet operation moved or retried.
Actual local inspection found CPython3.10.20 (Clang22.1.3), NumPy1.26.3 and
PyTorch2.7.0+cpu at `/home/fires/.venvs/hmasd-linux-cpu/bin/python`, host `Jacob`,
16logical CPUs. The runner fixes CPU/FP32 actors, FP64 densities and one
Torch/BLAS/interop thread; fresh admission still occurs only at the actual launch.
The native source, decision law, two assets, seeds, calibration, horizons and
all exposure remain unchanged. No equality to prior-host deployment scores is
claimed; all new controls/fits/final panels run contemporaneously here.

Only the two424487-byte S files were transferred, into
`temp/directions/uav_fleet_adaptation/b04_inputs/S_b02.pt` and `S_b03.pt`.
Their exact file hashes remain respectively
`b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a` and
`cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d`.
The original canonical node paths and tensor/source hashes remain bound in
`CANONICAL_ASSETS`; `STAGED_ASSETS` adds fixed local paths and that provenance.
Production accepts only those bindings and checks bytes/tensors before any
constructor. No original file was changed, and no policy was queried during
transport. These necessary input copies are temporary and will be removed
after complete reading and live-consumer checks; the unique original evidence
stays in its existing canonical locations.

Root subsequently allowed the selected N8 study and this study to overlap on
`local_linux`: each has one compute thread and no online wall deadline, while
the deadline-sensitive waiting operation uses the other physical machine.
There is one fleet worker→reader chain. Fresh actual-node admission and the
4GiB memory floor still apply; CPU/wall readings describe the actual concurrent
host, not an interference-free hardware benchmark. No fleet operation was
accepted before this resource allocation.

### B04 implementation accepted before execution

The DM read and accepted the bounded update kernel and complete reader, and
the full direction suite passed **57 tests in10.16s** on the selected local
interpreter. Independent engineering review of the integrated path reports
**57 passed in10.24s** and no remaining material finding. It checked the actual
adapter `state`/`next_state` interface, local/critic separation, requested
categories and own-navigation/cache resets, one-row density gradients,
detached return/advantage semantics, fresh continuous Adam, paid counts,
calibration isolation/ties, strict source/decoder/tape reuse, staged asset
provenance and saved-evidence reduction/tamper rejection. Mixed fallback-bit
states are both included in the learner gradient/count fixture.

One engineering finding was repaired: a critic failure after a successful
actor step could otherwise lose that group's prior diagnostics. A live group
record now precedes effects and retains initial density, targets, each epoch's
loss/gradient/movement, separate actor/critic completion flags and after-state
hashes; a regression injects that failure and verifies the paid prefix. This
changes evidence retention, not the learner's arithmetic, update order or
exposure. No native pilot or canonical-policy query was used for correctness
testing. The actual source assets' initial replay-density identity remains a
check inside the already priced first update of each paid group.

The runner completes exactly one worker→reader chain on the same admitted
source and handle. `reading.json` is exclusively created before any paid reader
forward, becoming VERIFIED or preserving FAILED work/timing; an existing
record refuses another production read. Final Student and shadow rows are
replayed within the declared allowance. Training/calibration logits, collected
critic outputs, optimizer and radio physics remain saved algebra/provenance
checks, without their replay. The reader records its separate costs and
whole-process high-water RSS; outer chain wall/CPU also captures import and
serialization gaps. No automatic extra read, fit or native episode follows a
failure. Actual new result exposure is still **0 fits/0 native steps** at this
acceptance. Engineering/support labor is unmetered; synthetic check times are
not result costs or an end-to-end engineering measurement.

### B04 native acceptance and observation — 2026-09-30T19:02:55Z

Exact reviewed input `98307b0c5cb6e42763458d780568d105d3f631af` was committed
and publication verified before launch. The fixed operation was accepted on
`local_linux` at19:02:55.623994Z. Its native identity, command, output and
retained source are bound by the [original manifest](../../../../runs/uav_fleet_adaptation/b04_native_development_a01/launch-manifest.json);
this is the single worker→reader chain, not a completed scientific reading.
Fresh preflight observed6961229824available/effective bytes against the
4294967296-byte floor, with no failure reason. The pre-admission CPU context
was16logical/affinity CPUs and load averages1.9345703125/1.15185546875/
.7099609375; timing retains the actual concurrent-host scope above.

The first observer registration refused because this session's prior, fully
consumed B03 observer state was explicitly stopped. I drained that unchanged
generation17 (no events/wake), rearmed it to18, and registered the new original
status reference at generation19. The detached observer's first fact reports
matching live worker/supervisor identities, accepted admission, consistent
records and no exit witness. No worker or accepted input was changed or
restarted by observer setup. The native DM remains active through collection
and reading; registration is not treated as proof of a child wake.


<a id="b04-complete-reading"></a>
## 2026-09-30 — B04 complete: reward continuation does not improve the retained students

The fixed two-lineage study completed once on `local_linux`, from published
source `98307b0c5cb6e42763458d780568d105d3f631af`. The worker finished at
19:10:44.859547Z and its same-process, already priced reader finished before
the native exit-zero witness at 19:11:36.273322Z. The original
[reading](../../../../runs/uav_fleet_adaptation/b04_native_development_a01/reading.json)
is **VERIFIED**, and both fits and both paid calibrations are complete. There
was no replacement fit, added calibration, endpoint selection, extra native
rollout or second charged reader. DM and independent scientific diagnosis use
only saved JSON/array reductions after this boundary.

The detached observer exposed READY at 19:11:56Z. Its native-child queue
attempt returned `-32600` (direct app-server input is unsupported for this
subagent); the already active deterministic waiter consumed the same event
`909cbb4f2555524f01a99973`, wake `2f0809e6-45c2-4cef-8d52-933ea3010f75`.
Generation19 was rearmed to20 to consume it, then observation was explicitly
stopped. Worker and supervisor identities were absent with a consistent
terminal witness; no launcher/worker restart occurred. Technical completion
and the scientific reading below are distinct facts.

### Fixed comparisons and signed outcomes

Each row below is one fitted lineage on its own fresh 32-world final panel.
L0 inherits the original B02 student and L1 the original B03 student; neither
was selected by its old score. `S` is unchanged temperature-one use, `R` is
its fixed final native-reward continuation, `C` is competent memoized local
control, `Q` is its fixed .10 departure law, and `B*` is the independently
calibrated candidate. Worlds and private innovations are paired within each
lineage. The intervals are descriptive t95 intervals over those worlds,
conditional on a fixed fitted endpoint; 64 worlds are not 64 training seeds.

| Lineage/arm | Mean native J | Mean served/tick | Mean within-episode service p10 | Mean episode minimum | Mean path m/UAV |
| --- | ---: | ---: | ---: | ---: | ---: |
| L0 C | .344029105 | 20.687744 | 20.000000 | 12.500000 | 2236.285 |
| L0 Q | .370187093 | 22.434692 | 17.625000 | 11.562500 | 3985.608 |
| L0 S | .385023142 | 23.708618 | 21.125000 | 12.031250 | 3090.545 |
| L0 R | .344745576 | 21.055176 | 18.812500 | 12.343750 | 1984.979 |
| L0 B*=S_T2 | .392267569 | 24.204102 | 20.187500 | 11.312500 | 4905.457 |
| L1 C | .324780467 | 19.276245 | 18.328125 | 10.875000 | 2702.194 |
| L1 Q | .371299364 | 22.586060 | 18.234375 | 9.906250 | 4079.542 |
| L1 S=B* | .393180638 | 24.143677 | 21.562500 | 10.750000 | 3217.685 |
| L1 R | .387968160 | 23.853149 | 20.703125 | 10.656250 | 3885.973 |

| Contrast | L0 J [conditional t95] | L1 J [conditional t95] |
| --- | --- | --- |
| R−S | −.040277566 [−.063749768,−.016805364] | −.005212479 [−.024293815,+.013868858] |
| R−B* | −.047521994 [−.067707221,−.027336766] | −.005212479 [−.024293815,+.013868858] |
| R−Q | −.025441518 [−.047614879,−.003268156] | +.016668796 [−.001487537,+.034825129] |
| R−C | +.000716470 [−.027594453,+.029027394] | +.063187693 [+.037741396,+.088633991] |
| B*−S | +.007244428 [−.010900159,+.025389014] | 0 (identical source/decoder/tape reuse) |
| B*−Q | +.022080476 [+.005555219,+.038605734] | +.021881275 [+.007272547,+.036490002] |
| B*−C | +.048238464 [+.021878044,+.074598884] | +.068400172 [+.042941000,+.093859343] |
| S−Q | +.014836049 [−.003725548,+.033397645] | +.021881275 [+.007272547,+.036490002] |
| Q−C | +.026157988 [+.007546565,+.044769411] | +.046518897 [+.022490024,+.070547770] |

Neither lineage meets the prespecified positive point comparison against both
S and B*. L0 R−S also loses 2.653442 mean served/tick [−4.334493,−.972392]
and 2.312500 p10 [−3.887216,−.737784], while shortening path by1105.566m
[−1612.275,−598.857]. L1 R−S is −.290527 served [−1.610259,+1.029204],
−.859375 p10 [−2.230151,+.511401], and **+668.288m** path
[+109.899,+1226.677]. Own-S J is negative in24/32 L0 worlds and21/32 L1;
p10 is lower in24 and23 worlds. L1's uncertainty does not establish harm or
equivalence, and its positive R−C/R−Q points do not establish added learning:
its unchanged S already has the larger corresponding J/service/p10 means.
Equal-weight descriptive effects are R−S J−.022745022, R−B*−.026367236,
R−Q−.004386361 and R−C+.031952082; there is no pooled-world training interval.

Retain heterogeneous successes and large losses. L0 world29351014 has R−S
J−.170115278, served−12.007813 and p10−10; world29351023 loses12p10.
L0 R−B* world29351019 loses J.179323865, served12.367188 and p10 10.5.
L1 world29353007 has R−S J−.094176978 and served−5.425781; world29353023
loses9p10. Positive R−S worlds remain, including L0 world29351015
(J+.076138828, served+5.164063, p10+6) and L1 world29353015
(J+.148424828, served+10.953125, p10+11). No arm except C has a zero-total-
service tick in these final panels; L0 C world29351028 has16. These are
team-service counts, not individual-user continuity or reliability claims.

### Calibration and preserved capability

All eight candidates ran on32 calibration worlds per lineage, before either
final panel. Their calibration mean J values in fixed candidate order are:

| Candidate | L0 calibration J | L1 calibration J |
| --- | ---: | ---: |
| C_0 | .343923653 | .326483577 |
| C_.05 | .358818276 | .359445569 |
| C_.10 | .361421107 | .353768998 |
| C_.20 | .353594971 | .347281443 |
| S_greedy | .346160761 | .341969301 |
| S_T.5 | .381150979 | .381620404 |
| S_T1 | .385814971 | **.395950551** |
| S_T2 | **.396311680** | .394868987 |

The fixed mean-J selector chooses S_T2 for L0 and unchanged S_T1 for L1.
L1 reuse is exact metadata identity, not empirical score/trajectory equality;
only L0 requires an additional32-episode final B* arm. Calibration is paid
reward-based selection, not zero-cost tuning. L0 B*−S is positive in16 and
negative in16 final J worlds; mean J+.007244428 and service+.495483 remain
uncertain, while p10 falls.9375, episode minimum falls.71875
[−1.393159,−.044341], and path rises1814.912m [1455.385,2174.438].
World29351013 loses J.091330982, p10 14 and minimum5 while adding2212.021m.
There is no demonstrated default temperature upgrade, no evidence that this
grid exhausts ordinary calibration, and no selection of another temperature
from the final panel. L1's calibration selects doing nothing to S.

Unchanged S retains a useful comparison to the prespecified ordinary Q on two
new, disjoint panels: S−Q service+1.273926/+1.557617, p10+3.5/+3.328125
(intervals [1.830134,5.169866]/[2.040656,4.615594]) and path−895.062/−861.858m
(intervals [−1394.311,−395.814]/[−1357.764,−365.951]). S−Q mean J is positive
in21/32 and23/32 worlds, but L0's J interval crosses zero. Preserve original
parent-B04's different finite decoder/tapes rather than pretending these are
identical repetitions. These are two retained constructions on fresh worlds,
not new independently trained lineages or training-population reliability.
Adverses remain: L0 world29351009 loses J.110627140/served7.429688 againstQ;
L0 world29351007 loses6.5p10 and6minimum. L1 world29353015 loses
J.079103695/served5.355469 againstQ; world29353009 loses5.5p10. Both S
policies retain the analytic helper and acquisition expense.

### Executed change, rather than a new mechanism attribution

Each lineage completed128 two-episode groups with four full actor and critic
Adam steps per group:512 steps for each network, fresh empty optimizer states,
no checkpoint choice, no teacher/KL/entropy term. All first-epoch FP32 logits
match exactly; across both lineages maximum probability error is8.88e−16,
chosen-logp error1.78e−15 and ratio-from-one8.88e−16. Actor endpoint L2 movement
is1.737203/1.782680, with25161/25366 of34715 parameter values changed; critic
L2 is1.332884/1.326359. All recorded actor gradient norms exceed the .5 clip
threshold, but gradients/steps are finite and nonzero. That describes the
chosen program, not a diagnosis that its clipping or optimizer caused loss.

On R's own lawful saved inputs, the original S shadow has mean TV
.464034/.265857 from R. Of10240 agent clocks per lineage, requested categories
change4908/3129, modal categories4571/2669 and four-tick clipped physical
paths4761/2955 (46.494%/28.857%). Thus the updates had substantial actual
behavioral exposure; boundary aliases or a wholly unchanged deployed policy
do not explain the null improvement. This is a distribution/request/kinematic
comparison on R history, not S's reward on that history, exact suffix replay,
or a causal account of which changed decisions lost native service.

L0 final entropy .238182 versus S .437889 accompanies more zero-displacement
UAV-ticks (1004.125 versus805.063), boundary ticks (209.906 versus123.375)
and fallback decisions (22.656 versus8.531) per episode. L1 entropy is nearly
unchanged (.430016 versus.439654) despite its substantial shadow drift.
These descriptive differences do not identify entropy collapse, a critic or
credit problem, representation failure, or the value of any repair. Sequential
training quarters also use different worlds; their changing returns are not
controlled learning-curve comparisons. The endpoint contrasts carry the
native-development conclusion.

### Complete exposure, compute and retained evidence

Actual new exposure is **2 actor–critic fits plus2 paid discrete calibrations,
1312 complete episodes and335872 native steps**:512 training episodes/131072
steps,512 calibration episodes/131072steps and288 final episodes/73728steps.
There is one constructor/unscored reset plus1312 explicit scored resets.
Actor/critic optimizer calls are1024 each; actor replay rows655360, critic
replay131072 and collected critic rows32768. The163840 first-density-identity
rows are a subset of paid actor replay, not another replay charge. There are
0new expert labels. All actual counts agree with the realized fixed branch.

C makes122880 requests, with59932 cache hits/62948 misses,1699596 candidate
trajectories and6798384 model ticks. Student makes296960 requests,
144269 cache hits/152691 misses,152691 helper/neural rows and276480 fresh
sampling draws; greedy rows do not draw. Native dense power slots92725875 plus
controller/helper links30418389 total123144264 power-work slots. Cache payload
counts sum episode-local caches, not simultaneous memory or a zero-cost helper.
Worker S shadows add20480 actor rows/81920 simple motion ticks. The original
reader adds71680 actor rows (51200 final endpoint and20480 shadow),81920 shadow
motion ticks,1679360 verified native-agent motion ticks and599940 fallback-
ranking motion ticks. It uses **0native steps,0radio/expert queries,0training
or calibration actor rows,0critic forwards and0optimizer calls**. All paid
actor rows across collection, optimization, worker shadows and reader total
900211; critic rows total163840. No production read is repeated for diagnosis.

Whole worker wall/CPU is469.369103/467.107003s; reader50.289765/50.267826s;
outer runner-through-reader chain519.886853/517.602806s, including import and
serialization gaps but excluding its final self-report write. Worker episode
CPU is156.289787 training,139.828009 calibration and84.053520 evaluation;
separate update groups cost78.152967CPU seconds. Remaining worker bookkeeping
is within the whole-worker timer. Peak430004KiB is the process high-water mark
including the earlier worker, not incremental reader RAM. These are actual
one-thread concurrent-host measurements; no online deadline, uncontended
benchmark or engineering-labor measurement was made.

The prior B02/B03 acquisition remains2fits/212992 unique native steps/16000
supervised updates/8192000 label presentations/163840 label requests and
205.046058 worker+reader CPU seconds. Acquisition plus this study therefore
costs **4fits,2calibrations,548864 unique native steps and722.648864 measured
CPU seconds**, retaining the two timing scopes and physical-host difference.
The earlier B01 loss remains a separate2fits/576000steps/31190.348 worker+
reader CPU seconds, plus its zero-exposure technical attempt/support; no
successful construction or small new runtime cancels that investment.
Engineering, scientific review and publication labor remain unmetered.

One canonical full output stays at configured `local_linux`:
`/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/`.
All1312 unique NPZs total506906150 bytes and are named/hashed by the original
summary and checked by the reader. Their unique complete native/training/
calibration/final-shadow evidence remains required by this retained fixed
comparison. Original `summary.json` includes the paid per-episode and optimizer
traces, so it remains bulk (6626301bytes, SHA256
`95947d006607ef1dda6269a1f7eae46e861980fa72d71d6d3af3a50e0754de27`), unchanged
outside Git; the original879195-byte `reading.json` is the compact published
aggregate and raw-identity reading (SHA256
`93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50`).
`assets/R0.pt` and `R1.pt` are1264725bytes each with hashes
`97ba5e39e11f62d04757de08a0b05ac782784c293512d6595bcf51ffe7441d29` and
`2deec512ecd183d462db7f21b95e5f33771b7f670557739c0b9c3da4c3cfef1b`.
They retain the adverse final actor, critic and optimizer evidence, not
replacement starting assets. Initial S originals remain unchanged at the
already recorded B02/B03 `wsl_4070` canonical paths. No archive/duplicate raw
copy is created for this local result.

### Working explanation before independent result diagnosis

I used current published RESEARCH topic4 at source `98307b0c5` when reading
this result: its separation of construction, finite optimization and complete
package value makes unchanged S and the paid ordinary calibration decisive
comparators. The new data strengthen **retained task capability**, including
fresh-world S−Q temporal/path evidence, while weakening the prediction that
this unrestricted finite reward-continuation program improves that capability.
Lawful local representation supported the original competent behavior and
allowed substantial changed behavior; neither representation insufficiency nor
transferable pretrained features are identified. No new native-learning
benefit is established; this is an informative executed negative, not missing
technical evidence or a proof that the parent learning question is impossible.

My provisional investment judgment is to preserve both original students and
all ordinary/adverse outcomes, end this exact full-actor PPO recipe, and avoid
an automatic extra seed, longer horizon, entropy/KL patch or calibration sweep.
A third copy would mainly refine this recipe's already nonpositive mean
comparison; a mechanism diagnosis would need a new consequential decision and
an intervention prediction, not simply a tunable component. Replicating or
confirming the retained S capability could matter for a specified use, but no
such new purchase or deployment tolerance is selected here. A richer native
contract is a Root cross-question allocation, not silently authorized by this
batch. The separate-context ResearchCritic receives original supporting and
adverse sources and owns the independent diagnosis; its recommendation and
any dissent will be recorded below before the final disposition.


<a id="b04-final-cleanup"></a>
### B04 measured cleanup after evidence publication

Compact evidence/config/status and the complete signed reading were published
on main at `978c622c37207067dd673247cf6729d786383304`; useful fixed source and
its checks remain published at `98307b0c5`. No source/test module is retired:
the exact update, collection, local policy and one-shot reader are still needed
to interpret and check this retained positive/adverse comparison. The B02
local-policy implementation remains a live cross-direction dependency.

The exact launcher collector first previewed, then applied retirement of
`d765a99550474b9b95de0994f8f7310b`, under the shared main writer lock. It
rechecked terminal native identities, no live process references, clean source
and durable source reachability on main. This deletes the disposable accepted
snapshot, not an authoring checkout, claim, manifest or output. The owner-
approved privileged read-only process scan also found no live references to
the six temporary-input/request/cache targets; the independent reader reported
that it had finished reading both temporary S tensors and no longer needed
them. The next-investment Oracle was given the canonical remote paths, not a
temporary-copy dependency. Both424487-byte canonical original S files on
`wsl_4070` were freshly rehashed to their unchanged bound digests before the
redundant local copies were removed. Observer generation20 is explicitly
stopped with no pending wake or unconsumed event.

| Deleted exact target | Allocated bytes before | After |
| --- | ---: | ---: |
| `.git/hmasd-launch-sources/d765a99550474b9b95de0994f8f7310b` | 1712513024 | 0 |
| `.git/worktrees/d765a99550474b9b95de0994f8f7310b` | 3547136 | 0 |
| `temp/directions/uav_fleet_adaptation/` (only `b04_inputs/S_b02.pt`, `S_b03.pt`, consumed `b04-wait-request.json` and their directories) | 864256 | 0 |
| `experiments/candidates/uav_fleet_adaptation/__pycache__/` | 8192 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b02/__pycache__/` | 98304 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b04_native_development/__pycache__/` | 110592 | 0 |
| `tests/experiments/candidates/uav_fleet_adaptation/b04_native_development/__pycache__/` | 110592 | 0 |

All seven targets are absent. The snapshot/admin decrease is1716060160bytes;
scratch/cache decrease1191936bytes; **B04 net reclaimed allocated disk is
1717252096bytes**. This is actual target deletion, not Git-object collection,
free-space capacity or a moved archive. There is no concrete cleanup blocker
or leftover from those targets. Required unique raw/summary/R endpoint
outputs stay at the one local canonical path above, and original S assets
stay at their original remote paths. No tarball, backup chain or extra raw
copy was created. B01/B02/B03 prior cleanups remain separate (4122198016bytes);
all four completed studies' measured deletions total5839450112bytes.


<a id="b04-independent-disposition"></a>
### B04 independent scientific diagnosis and resolved disposition

The dedicated `hmasd-research-critic` ran in separate context as native child
`/root/dm_fleet_adaptation/b04_result_review`, with no inherited DM/Root
conversation. It reconstructed the original outputs and recorded a provisional
reading before reading Oracle/Root/DM explanations. The full original answer
follows (local source links are retained as supplied):

> **Recommend stopping this exact B04 PPO recipe and preserving both original students, C/Q, calibration outcomes and the adverse R endpoints.** The study demonstrates active policy change without additional mean native competence over unchanged S or the paid calibration reference. The broader learned-development question remains open.
>
> I received no DM/Root conversation history. I recorded my provisional diagnosis before reading the original Oracle advice, Root’s allocation rationale or the DM’s result explanation. The subsequent DM stop/preserve recommendation agrees with my independent reading.
>
> The evidence is bound to source `98307b0c5cb6e42763458d780568d105d3f631af`, the [frozen protocol](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md:2121), and the original [summary](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/summary.json) and [verified reading](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/reading.json).
>
> The consequential endpoint comparisons are:
>
> | Mean native J contrast | L0: B02 initialization | L1: B03 initialization |
> |---|---:|---:|
> | R−S | −.040278 [−.063750, −.016805] | −.005212 [−.024294, +.013869] |
> | R−B* | −.047522 [−.067707, −.027337] | −.005212 [−.024294, +.013869] |
> | R−Q | −.025442 [−.047615, −.003268] | +.016669 [−.001488, +.034825] |
> | R−C | +.000716 [−.027594, +.029027] | +.063188 [+.037741, +.088634] |
>
> These intervals describe paired-world variation conditional on each endpoint. There are two continuation outcomes, not 64 independent training replications. L1’s R−S result establishes neither equivalence nor population harm. Its favorable R−C point cannot establish added learning: unchanged S already performs better.
>
> R−S mean service changes are −2.653442/−.290527 users per tick; temporal service-p10 changes are −2.312500/−.859375. L0 travels 1,105.566 m less per UAV; L1 travels 668.288 m more. Mean quality falls in both. L0’s slightly higher episode minimum does not erase its mean and p10 losses. R, S and Q have no zero-total-service ticks on these final panels; this does not establish individual-user continuity.
>
> The heterogeneity matters. L0 world `29351014` loses .170115 J and 12.007813 mean service against S. L1 world `29353007` loses .094177 J. Useful R cases also exist: world `29353015` gains .148425 J and 10.953125 mean service while travelling less. Those cases preserve evidence of locally useful changes; they supply no prospective rule for choosing those changes.
>
> Calibration selected `S_T2` in L0 and unchanged `S_T1` in L1. L1 B* is correctly reused by full policy identity. L0 B*−S is +.007244 J, with interval [−.010900, +.025389] and 16 positive/16 negative worlds. It adds 1,814.912 m per UAV while reducing p10 by .9375 and mean episode minimum by .71875. Thus the paid search preserves a conditional objective tradeoff, without establishing a default temperature upgrade or recurring improvement over S.
>
> The strongest useful positive remains **the original students’ competence**. On these fresh panels, S−Q gives J +.014836/+.021881, mean service +1.273926/+1.557617, p10 +3.5/+3.328125 and path −895.062/−861.858 m. L0’s J interval crosses zero, and large adverse worlds remain. This strengthens conditional asset reuse, alongside the parent B04 positive, while leaving general ordinary-control dominance and training-population reliability unresolved.
>
> The learning intervention was substantial. Each actor and critic completed 512 Adam steps; all recorded actor gradients were finite and nonzero. Actor L2 movements were 1.737203/1.782680. On R’s own lawful histories, frozen-S shadows disagree in physical four-tick paths on **46.494%/28.857%** of agent decisions. Every final world contains physical changes. Nonactivation, sparse exposure or command aliasing cannot explain away the failed improvement prediction. The shadows establish distribution and action change, without estimating S’s counterfactual reward on R’s history.
>
> My supported diagnosis separates four judgments:
>
> - **Opportunity:** preserved. Useful local control and the S−Q gains remain observable.
> - **Representation:** neither insufficiency nor transferable-feature benefit is identified. The same actor class already expresses S.
> - **Finite learnability:** the selected full-actor reward program failed to add mean value in both tested lineages, with a substantial conditional loss in L0.
> - **Complete package value:** neither R endpoint supports replacing its original S. Calibration’s marginal benefit is also unestablished as a general upgrade.
>
> L0’s lower entropy, greater stationarity, boundary exposure and fallback use are compatible with loss of useful stochastic behavior. L1 retains nearly unchanged mean entropy despite substantial physical drift. Consequently, a common identified “entropy-collapse” explanation is unsupported. The sequential training returns also use different worlds; they cannot select a better checkpoint retrospectively. Critic error, credit assignment and optimization remain possible mechanisms, but the current evidence does not select a repair.
>
> The earlier evidence makes this correction consequential. Parent C-prior learning lost to its competent initialization in 93/96 sampled-endpoint worlds; fleet B01 failed to improve its unchanged parent despite its narrower training-program contrast. These are different contracts and cannot be pooled as replications. Together with B04, however, they weaken the practical inference that a competent starting policy alone predicts useful reward continuation. They do not erase the supervised construction success.
>
> Actual cost was:
>
> | Work | Realized exposure |
> |---|---:|
> | Native reward learning | 2 actor–critic fits; 131,072 steps |
> | Paid calibration | 2 selections; 131,072 steps |
> | Final evaluation | 288 episodes; 73,728 steps |
> | Complete new study | 1,312 episodes; **335,872 steps** |
> | Actor/critic Adam steps | 1,024 each |
> | Total actor/critic forward rows, including paid reader | 900,211 / 163,840 |
>
> Recorded training-episode plus update-group wall time was 110.947/123.565 seconds per lineage, excluding fit-specific serialization and shared overhead. Complete worker wall/CPU was 469.369/467.107 seconds; reader was 50.290/50.268 seconds; the enclosing chain was **519.887 wall/517.603 CPU seconds**. Peak 430,004 KiB is process lifetime RSS. These are measurements on the actual concurrent host.
>
> Acquisition plus B04 totals **four fits, two calibrations, 548,864 native steps and 722.649 measured CPU seconds**, retaining the differing timing scopes and hosts. Acquisition includes 16,000 supervised updates, 8.192 million presentations and 163,840 labels. Earlier fleet B01’s two fits/576,000 steps/31,190.348 CPU seconds and parent-direction investments remain separately incurred. Engineering, scientific review and publication labor are unmetered.
>
> My independent checks covered all 26 source hashes against the launch commit, all 1,312 raw hashes, both initial and final actor tensor identities, critic identities, endpoint movement and saved Adam counters. I reconstructed native metrics for all 512 calibration and 288 final episodes, calibration winners and paired contrasts; checked world/domain ordering, initial-input pairing, local feature packing, fallback-bit semantics, own-navigation continuity, holds, clipped motion and saved shadow decoding. I also directly retrieved 12 consequential parent C-prior and eight positive/adverse parent B04 raw episodes from their canonical node.
>
> I performed no actor/critic forward, optimizer replay, native rollout or second charged reader. Radio/helper calculations, neural training arithmetic and the complete older bulk record were not independently replayed. The original reader and engineering review retain their stated scope.
>
> The current complete observation is sufficient for the stop/preserve decision. More final worlds would refine these endpoints without providing additional training replication. Another unchanged fit, longer horizon or entropy/KL modification has no automatic investment claim. The original prospective branches remain useful: improvement over S and B* would have supported conditional development; calibration exceeding R could support simpler reuse; substantial change without improvement supports ending this recipe. The observed result falls in that last branch.
>
> Preserving S leaves a constructive basis for a separately selected capability question. A future proposal can proceed from a testable conjecture without first proving the present failure’s cause. Its comparator and full costs must follow its actual information and control rights. The current source-only successor search is compatible with this recommendation; this review selects no successor experiment.
>
> **MATERIAL_DISSENT: no — the DM’s proposed stop of the tested PPO recipe, preservation of the useful assets and rejection of automatic extension are supported by the direct evidence.**

**DM resolved disposition.** I accept that independent recommendation: end
unchanged full-actor PPO investment, retain both original S assets and all
ordinary/calibrated/adverse endpoints, and make no default R or temperature
replacement. The useful change in belief is narrower than “learning fails”:
a competent local starting policy and substantial physical policy movement
were both present, yet this finite reward program added no mean native
competence over that starting capability. This weakens a starting-point-only
rationale for another unrestricted continuation. It does not identify a
common entropy, critic or credit cause, close the broader finite-learning
question, or require proof of the old cause before a new conjecture can be
considered. World heterogeneity is retained without inventing a deployable
selection rule. Calibration is a paid, uncertain tradeoff, not a demonstrated
upgrade over unchanged S.

The completed original scientific review is adequate for this result/stop
choice; there is no material dissent and no distinct unresolved question
requiring an additional Pro round. The result, complete interpretation and
cleanup are ready for own standing/shared-background publication. Parent and
other-direction costs remain separate and are not pooled as replications.

**Question continuity after the closed batch.** Root explicitly requested
source-only next-investment discovery with its existing Oracle, preserving
this DM's question ownership. That work may compare development of retained
capability with a justified stop or an out-of-question proposal for Root.
There is no selected successor experiment, new result code, native/model/actor
query, calibration or fit. I supplied only original output/asset provenance,
interface inspection and bounded cost arithmetic for an unselected complete-
intervention alternative; Root's new N8 positive is another actual allocation
consideration. No expansive next design is selected or published from those
feasibility facts, and existing composition/N8/waiting work stays with its
current DMs. The final B04 result is published independently of that discovery.

<a id="b05-original-independent-recommendation"></a>
## 2026-09-30 — B05 complete original independent recommendation

Root's existing native `/root/oracle_next_capability` is the registered
`hmasd-research-critic`, originally created with `fork_turns=none`.
It supplied the following complete answer at 2026-09-30 19:47:50 UTC after
the B04 result. Its disclosed prior-advice and result-headline exposure is
part of the answer. This is independent scientific selection advice, not
empirical evidence or a new Pro Send. Root selected this bounded study;
the DM's resolved contract and response follow the original answer.

### Complete original answer

I recommend **one bounded CAL/CONT study as the next learning investment**: learn from paired native action interventions followed by the unchanged student, then compare a contextual update with equally data-supplied global recalibration. Retain both original S assets and end the tested unrestricted PPO recipe.

This is a revised exploratory question, not a diagnosed repair for B04 or a new-theory claim. I give it priority over neural amortization of N8 and over immediately purchasing N8’s substantially larger two-opportunity search. Retain N8’s useful T controller; its separate continuation proposal may still merit investment.

My context remains separate from the DM’s conversation, but this assessment is not blind: Root supplied the new result headlines, and I retain my earlier recommendations. I reconstructed the new evidence before reading the DM’s explanation, then read and reused the complete original B04 critic. No additional result audit, rollout, policy query, fit or implementation was performed.

**The supported diagnosis is failure of the selected development program, alongside retained original competence.**

The source-bound [B04 summary](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/summary.json), [reading](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/reading.json) and [independent disposition](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md:3205) support:

| Consequential comparison | B02-initialized lineage | B03-initialized lineage |
|---|---:|---:|
| R−S mean native J | −.040278 [−.063750, −.016805] | −.005212 [−.024294, +.013869] |
| R−S mean service | −2.653442 | −.290527 |
| R−S temporal service-p10 | −2.312500 | −.859375 |
| S−Q mean native J | +.014836 [−.003726, +.033398] | +.021881 [+.007273, +.036490] |

R changes physical choices on 4,761/10,240 and 2,955/10,240 same-history shadow decisions. Every final world contains changes. L1 retains approximately its original entropy. Thus neither nonactivation nor a common entropy-collapse account explains the result.

The positive R cases remain evidence: L1 world `29353015` gains .148425 J while improving service and reducing travel. They provide no prospective deployment rule. Conversely, L0 world `29351014` loses .170115 J. Both sides belong in the retained record.

Paid calibration selects T2 in L0 and unchanged S in L1. L0’s uncertain +.007244 J comes with +1,814.912 m travel per UAV and −.9375 service-p10. It establishes no general temperature upgrade.

B04 cost two actor–critic fits, two calibration selections, 1,312 complete episodes and 335,872 native steps. Worker and reader consumed 467.107 and 50.268 CPU-seconds; the enclosing chain measured 517.603 CPU-seconds. More evaluation worlds would refine these endpoints, not create independent training replications.

Earlier C-prior, fleet B01 and learned counterfactual-credit failures strengthen the case against another automatic reward-training extension. They are different contracts, not pooled replications. The [LCAC B03 record](/home/fires/hmasd-wsl/docs/research/candidates/learned_counterfactual_agent_credit/LCAC_B03_SCIENCE_CARD_20260914.md) also prevents presenting counterfactual credit as an unexplored family. None of these results closes finite native learning.

**The proposed question is narrower and constructive:** can a fixed, useful local policy acquire additional complete native value from explicitly observed action consequences, beyond an equally trained global recalibration of that policy?

There are established antecedents:

- Ordinary policy-gradient theory relates expected return to policy derivatives weighted by action values; sampled complete returns can supply those values. The proposed construction applies that identity—it does not establish a new gradient theorem. [Sutton et al., §1](https://proceedings.neurips.cc/paper/1999/file/464d828b85b0bed98e80ade0a5c43b0f-Paper.pdf)
- COMA explicitly treats local actors, shared rewards and single-agent counterfactuals while holding other current actions fixed. Its factorized-policy derivation supports the shared-parameter bridge. COMA also explains the extra simulation cost of direct counterfactual evaluation; its critic-based convergence result is not a guarantee for our finite head optimization. [Foerster et al., §4](https://ojs.aaai.org/index.php/AAAI/article/download/11794/11653)
- AggreVaTe uses exploratory actions followed by expert continuation. Its guarantees account for distribution coverage, approximation and learning error. A single dataset collected under S does not inherit its interactive data-aggregation guarantee. [Ross and Bagnell, §§2.2–2.4](https://arxiv.org/pdf/1406.5979)

I checked all three library indexes and relevant primary passages, including the local [B01 foundations text](/home/fires/hmasd-wsl/docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf), [MARL-0090/InSPO source](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0090.json), and the My-lib RPI paper, [arXiv:2310.01737](https://arxiv.org/html/2310.01737v3). These reinforce the distinctions between policy improvement, behavior constraints and finite approximation. Together with the July and external-review records, they support honest comparison with competent ordinary control, not a novelty claim. This was not an exhaustive literature review.

**The short derivation and its limit follow.**

There are \(D=64\times5=320\) decision addresses: report \(r\in\{0,\ldots,63\}\), at native tick \(4r\), and member \(i\in\{0,\ldots,4\}\).

For an address sampled under frozen S:

1. Run the same world and S prefix in two complete episodes.
2. At that address, keep the other four agents’ current S actions fixed across the pair.
3. Force the addressed member to actions \(a\) and \(b\), each held for the existing four ticks.
4. Thereafter, all five agents use frozen S on their respective actual observations. Future actions or navigation states are not copied from a baseline trajectory.
5. Share the indexed future private innovations across the two episodes. Intervention draws use separate roots.

Let \(x\) be the addressed member’s lawful features, and use the fixed proposal

\[
\mu(a\mid x)=\tfrac12 S(a\mid x)+\tfrac12/27.
\]

Draw \(a,b\) independently from this same proposal. Let

\[
\Delta J=J_a-J_b,\qquad
J=\frac1{256}\sum_{t=0}^{255}
\left(0.7\,\frac{\mathrm{served}_t}{50}+0.3\,\mathrm{quality}_t\right).
\]

Define the paired score

\[
F_\theta=\frac{\Delta J}{2}
\left[
\frac{\pi_\theta(a\mid x)}{\mu(a\mid x)}
-\frac{\pi_\theta(b\mid x)}{\mu(b\mid x)}
\right].
\]

Conditional on the prefix and other agents’ current actions, let \(q_S(a)\) denote expected complete J after forcing \(a\) and continuing S. Independence of the two intervention draws gives

\[
\mathbb E[F_\theta]
=\sum_a\pi_\theta(a\mid x)q_S(a)
-\sum_a\mu(a\mid x)q_S(a).
\]

The second term is independent of \(\theta\). Consequently, at the zero head \(\theta_0\), where \(\pi_{\theta_0}=S\),

\[
\nabla J(\theta_0)
=320\,
\nabla_\theta
\mathbb E_{\text{uniform address, S histories}}[F_\theta]
\big|_{\theta_0}.
\]

There is **no additional factor of 256 or four**: the labels already use complete mean J, and the action is the existing four-tick decision. Partial local observation does not invalidate this first-order identity; hidden fleet histories are averaged under S. The claim concerns the nominal categorical law, preserving the implementation’s distinction between FP64 probabilities and finite-grid inverse-CDF sampling.

This does **not** establish a nonzero useful gradient, lower variance than PPO, successful Adam optimization or improvement after changing every deployed decision. Ordinary policy gradients already have a related population justification. The new purchase is a fixed continuation target, paired native consequences and a bounded update class—not proof that B04’s critic was wrong.

**The complete proposed contract is:**

| Item | Fixed proposal |
|---|---|
| Host and rights | Existing N5/U50, all-on, H256, 27 categories and four-tick holds; unchanged local information and navigation helper |
| Inherited assets | Both immutable original S assets; preserve their development and selection histories |
| Acquisition | 1,024 fresh paired worlds per lineage; two complete episodes per world; exactly one addressed intervention |
| Address weighting | A fixed permutation of all 320 addresses repeated three times, followed by its first 64 entries; weight each context by \(1024/(320n_d)\), where \(n_d=3\) or \(4\) |
| CAL | \(z_S+.5\tanh[\alpha(z_S-\operatorname{mean}z_S)+b]\); 28 trainable scalars |
| CONT | \(z_S+.5\tanh(Wh_S+b)\); frozen lawful hidden vector \(h_S\in\mathbb R^{128}\); 3,483 trainable scalars |
| Initialization | Both heads zero; exact original backbone remains frozen |
| Fit objective | Weighted mean of \(-F_\theta+.01\,\mathrm{KL}(\pi_\theta\Vert S)\); apply address weights to both terms |
| Optimization | 2,048 Adam steps per head, batch 128 with replacement, learning rate .001; standard β=(.9,.999), ε=1e−8, no weight decay; final endpoint only |
| Selection exposure | Four head fits total; no checkpoint, learning-rate, penalty, temperature or architecture selection |
| Fresh final panel | 32 worlds per lineage, comparing C/Q/S/previously selected B*/CAL/CONT; reuse L1 B* by its exact S identity |
| Deployment | Each fitted program operates at all 320 decisions; no post hoc per-world selector |

CAL replaces the earlier unselected BIAS sketch. Its global logit scale addresses a consequential simpler explanation: CONT might otherwise win merely by softening or sharpening existing S outputs. CAL is mathematically contained in CONT because S’s logits are an affine function of its frozen hidden vector. This is a function-class statement, not a claim of bitwise equivalence or globally optimal finite calibration.

Both heads’ offsets lie within ±.5. Their nominal probability ratio to S is bounded by \(e\), and their ratio to μ by \(2e\). These are local density bounds, not useful whole-episode safety or improvement guarantees.

The DM checked a concrete unused prospective namespace without drawing worlds:

| Purpose | L0 | L1 |
|---|---|---|
| Acquisition worlds | 29480000–29481023 | 29482000–29483023 |
| Final worlds | 29481100–29481131 | 29483100–29483131 |
| Disposable constructor seed, followed by immutable S load | 29484001 | 29484002 |
| Shared acquisition-pair S private root | 29484011 | 29484012 |
| Within-lineage final paired private root | 29484021 | 29484022 |
| Intervention-a root | 29484031 | 29484032 |
| Intervention-b root | 29484041 | 29484042 |
| Address permutation root | 29484051 | 29484052 |
| Minibatch root, shared by CAL/CONT | 29484061 | 29484062 |

Master label is `29484000`. Preserve `reset(seed=world)` and the existing indexed `SeedSequence[root,world,tick,agent]` law. These IDs come from a collision check, not favorable-seed evidence.

**The full cost is material but bounded.**

| Work | Prospective exposure |
|---|---:|
| Acquisition | 4,096 complete episodes |
| Final evaluation | 352 complete episodes |
| Total | **4,448 episodes / 1,138,688 native steps** |
| Unique paired contexts | 2,048 total |
| Head fitting | 4 fits; 8,192 Adam steps; 1,048,576 cached-context presentations |
| Worker Student requests | 1,382,400 |
| Worker C requests | 40,960 |
| C candidate modeling | 1,105,920 paths / 4,423,680 model ticks |
| Combined native/helper/model link-calculation ceiling | 600,468,275 slots |
| Reader neural replay | 73,728 one-row backbone forwards, plus applicable head evaluation |
| Reader optimizer replay | 0 |
| Storage | Approximately 2 GB new raw evidence |
| Indicative CPU | 25–45 worker minutes, including roughly 1–5 fitting minutes; 5–15 reader minutes |
| Engineering/review/reading | Approximately 5–9 elapsed hours, unmetered planning estimate |

These timings are extrapolations from measured B04 episodes, not benchmarks or resource admission. All acquisition, duplicates, zero contrasts, physically aliased actions and failed work remain charged. The new study adds to the recorded acquisition-plus-B04 history of four fits, two calibrations, 548,864 native steps and 722.649 measured CPU-seconds; older direction investments remain separately incurred.

Source inspection found no blocking API requirement. The collector can preserve the normal helper update and override one command at a four-tick boundary. Future private innovations are independently indexed, so an intervention does not shift their addresses. Frozen hidden features can be exposed in the existing forward path.

The reader should verify every pair’s prefix, intervention, input identity, complete-return reduction, addresses, holds and physical trajectory. It should replay the backbone at every unique intervention context and every final Student-family decision. The 2,048-context reuse requires first proving the two stored pre-intervention feature/logit copies identical. Other acquisition clocks receive full saved provenance and algebra checks, **not** complete neural replay. Saved optimizer counters, gradients and hashes are checked without silently adding four replay fits.

Final traces must expose requested and physical changes relative to S on each deployed program’s own histories, including probability changes, aliases and unchanged cases. Shadows measure decision exposure; they do not supply counterfactual rewards.

**The strongest objection is the gap between sparse local evidence and fleet-wide deployment.**

There are only 1,024 contexts per lineage—three or four worlds per address—not hundreds of thousands of independent learning examples. CONT has 3,483 parameters. Repeated minibatch presentations create no new information. Moreover, individually useful changes under S can conflict when all agents change: the other agents’ original coverage or interference pattern may have supported the isolated improvement.

The proposed observation is worthwhile despite that objection because it tests a precise, inexpensive-to-deploy update with genuine native consequence labels, a fixed continuation, unchanged information rights and a strong same-data calibration comparison. It needs neither a positive pilot nor a proven B04 failure cause. I regard this as the smallest complete purchase worth making here; the 1,024-context budget is a judgment about coverage and cost, not a power guarantee.

The reading rule must remain prospective:

| Observed outcome | Supported conclusion and action |
|---|---|
| CONT improves complete J over S, CAL and B* across both lineages, with tolerable secondary costs | Conditional evidence of useful finite development beyond the tested global recalibration package. Consider independent acquisition/training replication only for a concrete next use. |
| CAL improves while CONT adds no convincing value | Prefer the simpler recalibration capability; do not credit contextual adaptation. |
| CONT improves only one lineage, or beats S but not CAL/B* | Preserve the conditional outcome or tradeoff; no recurring development claim or post hoc asset-selection rule. |
| Substantial physical change with adverse complete outcomes | Retain S and stop this finite package. No automatic entropy, critic or representation repair follows. |
| Little physical change | Record nonactivation or sparse exposure. It does not refute improvement opportunity; it also does not earn an extension. |
| Active but uncertain endpoints | Retain S. More evaluation episodes do not substitute for independent training units. |
| Technical invalidity | Preserve failure and cost; make no scientific negative claim. Any repair must preserve the selected scientific contract. |

Read service, quality, temporal p10/minimum, travel, fallback behavior and complete computation alongside J. A positive J contrast with costly travel or service-tail losses supports a tradeoff, not automatic adoption. This remains exploratory development using two previously studied assets and previously selected B* policies—not a learning-population confirmation.

For allocation, N8’s actual T−R gain remains a useful positive: +.007400 J with nine positive and seven unchanged worlds. It does not itself establish a need for a learned approximation. The N8 Oracle’s distinct T/G2/A2 temporal-complementarity proposal now has an uncompressed source estimate around **4.1 combined CPU-hours**, with branching and engineering feasibility still under DM scrutiny. I have not independently audited that prospective estimate. It is not a prerequisite for this N5 study, and preceding positivity alone does not make it the better next purchase.

My preference is therefore **select this one CAL/CONT exploration next, retain N8 T, and let the separate N8 proposal earn its larger bill on its own question and costs**. Existing composition and user-waiting work remains distinct. A positive here would concern finite local-policy development; it would not establish transfer to their changed information, radio or objective contracts.

My direct checks covered the B04 compact outputs, 26 source bindings, consequential positive/adverse raw pairs and native metric reductions, relevant learning/source interfaces and primary passages. I reused the original critic’s broader reconstruction of all calibration/final metrics and artifact identities. I did not replay neural training, native physics or all older bulk evidence. The new design’s performance, estimator variance, finite optimization quality and engineering timing remain unmeasured.

**MATERIAL_DISSENT: no.** Root’s stop of unrestricted PPO and preservation of S are supported. I recommend a separately selected, bounded revision; neither B04’s failure nor the first-order derivation authorizes a run or guarantees that this finite purchase will succeed.

### End of original answer

<a id="b05-native-consequence-design"></a>
## 2026-09-30 — B05 selected native consequence development: DM response and fixed design

**Question and resolved choice.** Root selected the above CAL/CONT exploration
as the next result-bearing study in this existing question, superseding the
source-only discovery boundary. I accept it. The intended contribution is a
conditional empirical answer about finite development of two useful policies:
whether reward consequences of local interventions support an inexpensive
contextual improvement beyond the same-data ordinary global calibration.
It is not a diagnosed correction to B04's critic or a new policy-gradient
theorem. No fresh run, asset query or fit has occurred at this design entry.
The full B04 result remains closed; the new comparison neither repeats nor
extends its two actor–critic fits or paid calibration.

**Changed explanation and opportunity cost.** I retain the original independent
B04 diagnosis and all conditional positives/adverses. Starting competence alone
did not make the full-actor PPO continuation useful. B05 instead purchases
direct complete-return labels under one fixed continuation, and tests finite
use of those labels in a bounded function class. Uncertainty about their
variance, sparse coverage and fleet-wide deployment is the question, not a
reason to assert the old cause or require a positive pilot. More B04 worlds
cannot supply another training instance; unrestricted PPO replication does not
test this changed conjecture. A stop was a real alternative. I accept the
reviewer's judgment that this complete bounded purchase has useful marginal
information before larger N8 search or an unmotivated learned approximation of
its already useful controller. The separate N8, composition and user-waiting
questions retain their actual leads and contracts; no cross-host transfer claim
is bought here.

**Current shared evidence used in this choice.** I read published main
`737a50333e794fbca02bce45f335e9e92b1e0b56`,
[topic 4](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)
through the B04 disposition, and the relevant opening judgments in
[topic 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练)
and [topic 3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构).
Their concrete effects are: retain both original competent S policies without
choosing the better exposed lineage; give CAL the same new reward information
and fitting exposure; retain Q and the old paid B* as useful controls; do not
equate parameter change or a richer representation with native value; and
measure complete outcomes after all agents deploy the new head. The source
bound B04 shadows already rule out its nonactivation explanation, but say
nothing causal about B05. The original
[LCAC B03 card](../learned_counterfactual_agent_credit/LCAC_B03_SCIENCE_CARD_20260914.md)
retains its earlier B01/B02 adverse/small results and selected replication
scope; it is a different credit-learning contract, not a pooled replication or
a claim that counterfactual learning is new.

I personally checked the load-bearing primary passages:
[Sutton et al. 1999 §1, pp.1058–1059](https://proceedings.neurips.cc/paper/1999/file/464d828b85b0bed98e80ade0a5c43b0f-Paper.pdf)
connects policy derivatives to action values and explicitly allows sampled
complete returns; [Foerster et al. 2018 §4, pp.2976–2978](https://ojs.aaai.org/index.php/AAAI/article/download/11794/11653)
holds other current actions fixed and expands the factorized actor gradient;
[Ross and Bagnell 2014 §§2.2–2.4](https://arxiv.org/pdf/1406.5979)
collects consequences of an exploratory action followed by an expert, and its
guarantees depend on interactive distributions and approximation/regret terms.
The mapping here is fixed S prefix/continuation, one member's action, native
complete reward and lawful local features. The missing coupling is that all
members later use the fitted shared head on new joint histories. We inherit
neither COMA's compatible-critic convergence nor AggreVaTe's aggregation
guarantee. The independent review's three-library/July/external-review search
remains its disclosed source work; no novelty claim is made.

**Host, inherited identities and information.** Preserve the B02/B03 N5/U50,
all-on native environment, H256, 27 three-dimensional primitive commands,
four-tick holds and one CPU compute thread. No richer observation, report
cadence, radio, communication or action authority is added. Each local policy
uses the original 103 lawful observation entries plus ten navigation values
and one fallback bit. The original 114→128→128→27 FP32 ReLU network has 34,715
parameters. Expose its last 128-dimensional hidden vector in the same one-row
forward; do not query another encoder or give the actor team state, rewards,
world id or the intervention address. The full reward is a training label only.
No critic is constructed or fitted.

L0 original S is B02 `e945483b85c7f8ddfc315c57f36938d6c14201c7`,
canonical `wsl_4070:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt`,
424,487 bytes,
SHA256 `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`,
tensor digest `6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`.
L1 original S is B03 `4909c9553300a4a4de6eb79476e818d7b1ceab53`,
canonical `wsl_4070:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/assets/S.pt`,
424,487 bytes,
SHA256 `cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d`,
tensor digest `c6286dd32097d37b2c2c3039e487a24b756398e3ddffa9dc9e1ec3ef66170699`.
Both remain immutable. Disposable initialized modules are overwritten before
any scientific query. Paid B04 calibration, source `98307b0c5` and compact
evidence `978c622c3`, supplies B*: L0=S_T2, L1=S_T1. No calibration is repeated.
C is the original local four-step ranking controller; Q is its fixed .10
uniform-off-winner randomization, using the same lawful helper. Original S is
temperature-one sampled. B* choices and their original selection exposure
remain explicit; no per-world selection is permitted.

**Exact acquisition and native label.** Use the original recommendation's
world/private/intervention/address/batch namespaces, unchanged. For each of
two lineages, pair index j=0…1023 determines the world and one of 320 addresses
d=5r+i: one NumPy `default_rng(address_root).permutation(320)`, repeated
three times followed by its first64 entries. Each address occurs three or
four times; context weight is1024/(320 n_d). One full episode uses intervention
root a and the other root b. At tick4r, query all five original S policies in
their own normal order, preserving the usual helper/navigation update. Keep
the normal nominal S request, innovation and density. Separately draw the
forced category from μ=.5S+.5/27 with the branch's independent indexed
`SeedSequence[root,world,tick,agent]` innovation; override only this member's
actual held command. Both episodes really run H256, including their identical
prefix; no suffix-only saving or duplicated-row fiction. Subsequent navigation,
observations and helper caches evolve independently from the actual branch,
while private RNG addresses remain paired. A=b, equal physical paths, zero
return contrasts and every paid failed episode are retained without resampling.
Each pair branch has a distinct output identity to prevent raw-file collision.

The source `uav_local_history/b01/study.py:native_reading` verifies total
native reward against .7 served/50+.3 quality. B05 J is its FP64 complete
256-step mean; quality is the clipped served-link SINR statistic from that
source. ΔJ=J_a−J_b includes the complete native outcomes. The common prefix
cancels in expectation and in each paired subtraction, not by dropping paid
ticks. The recommendation's paired score F is unchanged. Conditional on a
prefix, other current S actions and a shared future tape, independent a/b draws
make its expectation the policy-weighted continuation value minus a constant.
The first-order shared-parameter identity at the zero head has factor320;
there is no extra factor256 or4. Neither F nor the loss is multiplied by320:
the fixed .01 KL coefficient is in mean-address complete-J units. Its value
is an untuned finite-design choice, not a theorem or optimum.

**Two heads, four fixed fits.** CAL has scalar α and27 biases:
`z=zS+.5*tanh(alpha*(zS−mean(zS))+b)`. CONT has27×128 weights and27 biases:
`z=zS+.5*tanh(W*hS+b)`. Both heads start exactly zero; the original backbone
is frozen and its initial/final tensor digest must match. CAL is mathematically
nested in CONT, but finite FP32 centering/folding is not promised bitwise
equivalent, and the finite optimizer is not an optimal calibration oracle.
This comparison does not isolate a pure causal effect of representation or
parameter count.

Each fit uses the same1024 cached contexts/labels and the same minibatch root
as its within-lineage comparator. A NumPy generator initialized from that
root draws128 integer indices with replacement at each of2048 updates.
The head's FP32 arithmetic is **one row at a time** in training and deployment;
stack its128 output rows for the FP64 categorical loss. This avoids changing
the head's linear-algebra path between a batch and deployed one-row calls.
There are no additional backbone forwards during fitting. Use FP64 stable
log probabilities and probabilities for F and KL, and FP64 context weights/
labels, with FP32 parameter gradients/Adam. Existing deployment retains its
NumPy FP64 nominal categorical law and inverse-CDF sampler; numerical
Torch/NumPy density agreement is checked within dtype-justified tolerances,
not advertised as exact finite-grid differentiation. Stable log probabilities
avoid taking log of underflowed S probabilities; μ's floor is1/54.
No probability floor, extra clipping, return normalization, gradient clipping,
schedule, early stop or checkpoint selection is added.

Root explicitly accepted the three ambiguity resolutions on2026-09-30
19:52:34 UTC: (1) loss is `sum(w_i*(-F_i+.01*KL_i))/128`, **not** division
by the random sampled sum of weights; (2) final same-history S shadows apply
only to CAL/CONT, with both simple-motion passes charged; (3) use the stated
one-row fitting/deployment arithmetic and revise estimates if it changes cost.
Thus address weights apply to both F and KL and the fixed batch denominator
preserves the intended empirical weighted objective. Standard Adam is
lr.001, β(.9,.999), eps1e−8, zero weight decay, amsgrad/foreach/fused false;
2048 actual steps for each of four heads, final endpoint only. Preserve
per-update loss/paired-score/KL/entropy, gradient norms, head movement,
optimizer counters and deterministic digest/seed evidence. Repeated batches
are1,048,576 cached presentations of2,048 unique contexts, not more labels.
Nonfinite data/updates fail and retain the paid prefix; they earn no automatic
retry or revised hyperparameter.

**Final complete comparison and reading.** On the prospective disjoint32
worlds per lineage, deploy C/Q/S/B*/CAL/CONT throughout all320 agent decisions.
L0 has192 final episodes. L1 B*=S is metadata reuse of its exact policy law,
not a fresh episode, leaving160; total352. Private final roots are paired
within each lineage. Report all per-world absolute native J/service/quality,
temporal service-p10/minimum, travel per UAV, fallback behavior and timings.
Predeclared central contrasts are CONT−S, CONT−CAL and CONT−B*; also retain
CAL−S/B*, both heads−C/Q, S−Q and B*−S. Conditional paired-world t95 intervals
are descriptive for each fixed fitted endpoint on its panel; they are not
training-population confidence, equivalence or confirmation. Show positives,
negative counts, worst losses and full worlds, with no retrospective selector.
No numeric adoption threshold is invented. Mean-J benefit with service-tail,
travel or deployment-cost harm is an explicit tradeoff requiring a future use
case, not automatic replacement. The original answer's outcome branches remain
the prospective disposition rule.

For **CAL and CONT only**, at each final decision reuse already computed
backbone logits/hidden features to obtain original S's same-uniform shadow
category. Simulate its four clipped motion steps from the actual current
position and compare with the actual four-tick path. Preserve probability TV,
entropy, modal/requested/physical changes, aliases and unchanged cases.
These128 episodes add40,960 shadow decisions and163,840 simple motion steps
in the worker; no extra backbone/helper/radio query. The reader repeats that
motion check, another163,840. Original S, B*, C and Q keep their normal complete
trajectories and identities; the original advice's “each deployed program”
does not add C/Q neural shadows. Shadows do not provide native reward
counterfactuals.

The reader hashes every raw/checkpoint/source artifact, verifies all4448
complete trajectories, native metric algebra, held commands, addresses and
intervention provenance. It verifies the paired prefixes and two copies of
the forced context are byte-identical before reusing one backbone replay per
pair. Neural replay is exactly2048 unique intervention contexts plus71680
Student-family final decisions =73728 one-row original-backbone forwards;
final CAL/CONT additionally use40960 head applications. Other acquisition
clocks receive saved feature/logit/density/innovation/provenance checks, not
another neural forward. No full optimizer replay is bought: inspect saved
update counters/gradients/hashes and endpoint optimizer/tensor identities;
focused synthetic checks validate update arithmetic. This is an explicit
verification limit, not a claim of full training replay.

**Complete cost, resource window and stop.** The original table is retained
with these clarifications:4096 acquisition+352 final=4448 H256 episodes,
1,138,688 native steps,4448 explicit resets plus the environment constructor;
4 head fits,8192 Adam updates,1,048,576 cached head-row presentations.
Worker Student requests/backbone forwards are at most1,382,400 before lawful
per-episode memo reuse, and ordinary C requests40,960. Worst C modeling is
1,105,920 paths/4,423,680 modeled ticks. The earlier source arithmetic separates
native314,362,675 link slots, Student helpers193,536,000 and C helper/model
92,569,600 for a600,468,275 combined ceiling before caches. Added shadow motion
is327,680 worker+reader simple geometry steps, not radio/native steps. Reader
has73728 backbone forwards,40960 head rows and0 optimizer updates. Record
all actual memo hits, call counts and partial work; counts are not disguised
as a new fit allowance.

Existing B04 per-episode evidence supports roughly20–25 CPU-minutes for
collection. Retain the review's prospective25–45 worker CPU-minutes including
approximately1–5 fitting minutes, plus5–15 reader minutes; one-row autograd
cost is not benchmarked and may require an honest timing revision without
changing2048 updates. Approximately2GB new raw is a planning estimate;
episode streaming avoids loading it all for learning. Support/review/reading
was estimated5–9 elapsed hours and remains unmetered. All import/build,
worker/read/serialization, resource telemetry and deployment head costs must
be reported; unknown support time is not zero. Added exposure does not erase
the recorded548,864 acquisition+B04 native steps/4fits/2calibrations/
722.649 measured CPU-s, or older B01's separate576,000 steps/2fits/
31,190.348 CPU-s and the zero-exposure technical attempt.

Root allocated this study the **next released configured physical-node
window**, remote-first if both are free. Both nodes had accepted producer+
reader chains at selection; their priority and handles are preserved. Reasoning,
editing and synthetic engineering checks may proceed now. A real launch needs
published exact inputs, active current ownership, fresh actual-node memory and
occupancy admission; no migration/rebinding of existing operations. Choose the
available node prospectively from `.codex/hmasd-compute.toml`. One accepted
worker+reader chain ends at the fixed exposure or concrete fault. No automatic
retry, extension, calibration sweep or extra endpoint. Native deterministic
observation stays with this DM until collection/full reading, independent
scientific diagnosis, own publication and verified cleanup.

The original separate-context scientific selection advice covers this chosen
question and finite comparison, including its strongest objection. My
clarifications were accepted by Root and add no scientific arm or claim.
There is no material dissent or distinct unresolved issue warranting an extra
Pro consultation. Independent engineering review is still required for the
executable path, and result interpretation receives its own applicable
independent scientific reading. Adviser consensus supplies no empirical
support for success.

<a id="b05-native-consequence-l0"></a>
### B05 L0 — fixed CAL/CONT acquisition, learning and complete reader

Deliver one direction-local implementation in
`experiments/candidates/uav_fleet_adaptation/b05_native_consequence/`,
matching focused tests under
`tests/experiments/candidates/uav_fleet_adaptation/b05_native_consequence/`.
New explicit entrypoints `run.py` and `read.py` bind the above protocol,
both immutable inputs, native launcher admission and a complete same-handle
worker/reader chain. Run output is
`runs/uav_fleet_adaptation/b05_native_consequence_a01/` with compact
config/summary/reading/manifests and bulk raw/model/update traces separated.
The DM owns the notebook, protocol, collection, integration, reader and
publication. A bounded Implementer may own only the new head/fit module and
its synthetic tests after receiving this scope; no other source, index,
notebook, asset, scientific query or result execution is delegated. Shared
main and disjoint edits apply; no new authoring checkout.

Reuse original B02 controllers, RNG, feature preparation, model/checkpoint
identity and native host; reuse applicable B04 contract/metric/source-binding
helpers without changing their frozen behavior. Do not modify shared core or
past B02/B04 contracts to accommodate B05. The key state-flow invariants are
immutable S weights, own-history helper/cache/navigation, normal nominal S
draw versus one independent forced draw, actual four-tick hold, separate
paired complete-episode identities, zero extra actor/critic rights, same
row-level head program and address-weighted loss with fixed denominator.
Exact seed namespaces and exposure limits above are executable constraints.

Checks are synthetic/off-result unit tests for head initialization, nominal
density/gradient arithmetic, μ support/paired-score sign/zero contrasts,
address weighting and seed isolation, same-row training/deployment,
backbone immutability, actual optimizer counts, malformed input rejection,
collector override/hold/suffix behavior, raw identity, readback corruption
and endpoint/source/measurement bindings. A fake deterministic environment
may check full lifecycle without production-world draws or native/model
queries. No paid pilot or asset benchmark. Use the configured scientific
interpreter and pytest-owned scratch; report actual coverage/limitations.
Read/review the integrated diff and checks; a registered independent
engineering Reviewer receives this contract and original inputs, with no
science-selection authority. Publish accepted source before any result
execution; preserve and report any technical failure and incurred work.


<a id="b05-engineering-acceptance"></a>
### B05 engineering acceptance and actual node choice — 2026-09-30

The DM accepts the ten-module direction-local implementation and two focused
test files under the published L0 at `a5073c72c1765bc2585d77041e8ad073ee88cd2d`.
The bounded Implementer supplied only `learning.py` and `test_learning.py`;
its 24 checks passed in2.31s. I read and integrated that work, implemented the
collector/runner/reader, and completed35 synthetic checks in4.52s. The fake
H8 lifecycle covers both lineages,70 complete fake episodes/560 fake steps,
four two-update heads and the saved reader's164 backbone rows/80 head rows/
320 shadow motion ticks. These are engineering fixtures, not production
worlds, acquired labels or useful fitted endpoints. No production actor,
helper/model, native transition or optimizer query has occurred.

The independent registered engineering Reviewer received the actual published
contract and complete source/tests, and returned:

> No material finding remains in the B05 diff reviewed against contract
> `a5073c72c1765bc2585d77041e8ad073ee88cd2d`. No repair requested.
>
> Checked all ten modules and both test files, including paired forcing/RNG,
> objective and gradient equations, frozen assets, accounting, reader limits
> and failure paths. The prior calibration file matches its pinned hash.
>
> Independent validation: **35 tests passed in4.15s**, using synthetic
> fixtures and managed pytest scratch.
>
> Limits: no production rollout, staged-asset loading or canonical actor
> queries performed. Acquisition-wide neural replay and optimizer replay
> remain excluded by the fixed contract. Scientific acceptance remains with
> the DM.

I accept this engineering result; it adds no positive scientific evidence and
changes none of the four fits, labels, worlds, arms or final endpoints. Saved
fit traces are separate bulk files, and the reader checks their provenance,
loss/counter/gradient records, endpoint/Adam identities and declared limits;
it performs zero optimizer replay. Every raw trajectory is read, with only
the prescribed73728 backbone and40960 head replay rows. In addition to the
already priced327680 worker+reader shadow motion steps, the reader's original
C/Q fallback-ranking audit can reconstruct at most40960×27×4=4423680 simple
motion ticks from saved score arrays. This is geometry verification, not new
native steps, radio calls or acquisition. Actual fallback counts are reported.
It also verifies the saved native trajectory geometry for1138688 team ticks
(5693440 agent ticks). The unchanged25–45 worker plus5–15 reader CPU-minute
estimate remains provisional; no production benchmark has been added.

Root's original node-priority dependency is resolved: parent-adaptation B05's
worker and complete reader exited0 at20:06:39.448902UTC, with both native
identities absent and reading VERIFIED. Root released `local_linux` while the
user-waiting direction retained the remote real-deadline producer/reader
chain. I therefore choose configured `local_linux` (Jacob, CPU, one compute
thread), rather than waiting for or disturbing the remote chain. Root permits
sharing this physical host with the separately selected untimed/single-thread
N8 study subject to fresh actual memory/occupancy admission. Any concurrent
load is part of the measured timing conditions; no latency/deadline claim is
made. No N8 operation or resource reservation is inferred from selection.

The two exact original S files were freshly hash-checked at their canonical
remote paths, then copied solely as required local B05 inputs to
`temp/directions/uav_fleet_adaptation/b05_inputs/S_b02.pt` and `S_b03.pt`.
Both are424487bytes and match the declared file SHA256 values; they remain
identical inputs, not new checkpoints or an actor query. The staged copies
are disposable after this study's live consumers finish; the canonical
remote originals remain retained. The paid B04 calibration reading matches
its declared SHA256. Source publication precedes result execution. The next
action is fresh canonical pause/lead, source, actual-node memory and occupancy
admission followed by one detached worker+reader chain at the fixed exposure.


<a id="b05-launch-a01"></a>
### B05 a01 — accepted original operation, collection active

Exact inputs were committed and publication verified at
`2e22a2ccf6cafbde5b85a6658077ddcb2bbfcf94`. The original detached operation was
accepted at2026-09-30T20:38:02.465376Z; its authoritative command, node,
immutable source snapshot, native identities and output binding are in the
[launch manifest](../../../../runs/uav_fleet_adaptation/b05_native_consequence_a01/launch-manifest.json).
No second request, worker or reader was launched. The canonical owner pause
was lifted and this direction remained exploring with its exact native-child
lead. Fresh runner-side admission recorded6875746304 physical/effective
available bytes against the4294967296-byte floor; no live local result
producer appeared in the immediate occupancy check. The released parent
worker/reader exit0 and absent processes were independently reconciled at its
actual `b05_radio_composition_a01` handle. The earlier mistyped status locator
returned missing and caused no external effect.

The existing session observer was stopped after B04. The first B05 arm
therefore refused with “drain and rearm the existing state before adding
observations”; drain showed generation20, no wake and no pending events.
Rearm advanced21 and registration of the new original handle advanced22.
Drain then showed the accepted B05 runner and supervisor both running, no
pending event, and zero probe errors. The observer uses30-second deterministic
status probes and a1500-second checkpoint. Native-child queue delivery remains
unsupported as previously measured; this DM stays active through deterministic
waiting and same-handle drain/rearm, not a replacement operation.
Collection has begun under the fixed contract. No endpoint is read or selected
from this progress entry; worker, full declared reader and scientific reading
remain outstanding.


B05 observer checkpoint at2026-09-30T21:03:11UTC: original worker has finished
all4 fits/8192 Adam steps/1048576 cached presentations and4448 full episodes/
1138688 native steps. Worker wall1446.904711s, CPU1444.100055s; stderr empty.
The same process is still executing its priced reader; these are technical
progress facts, not a scientific disposition. Generation22 checkpoint
`ead35aeaa9482a022590db5a`, wake`b7fa3906-c0ed-4bf8-9467-74d0bfaf58ed`, was
read and consumed; queue delivery returned the same native-child `-32600`
restriction. Foreground deterministic observation supplied the event. Rearm
advanced23 on the same accepted operation, without another worker or reader.


<a id="b05-complete-reading"></a>
### B05 complete reading — active native-consequence fitting, no added fleet value

**Complete observation.** All declared work and its priced reader finished at
the original source `2e22a2ccf6cafbde5b85a6658077ddcb2bbfcf94`; native exit0 was
witnessed at2026-09-30T21:05:12.498259Z, with both process identities absent.
The reader is **VERIFIED**, including all4448 raw files and36 source bindings.
CONT's mean native J is below unchanged S in both lineages and does not
consistently exceed same-data CAL. All three central contrasts have conditional
world intervals spanning zero. This fixed purchase therefore supplies no
positive added-value result or default replacement. It does not establish
population harm, equivalence, a common failure cause or general inability to
learn. Both original S assets retain useful fresh-panel comparisons with Q.
The independent scientific result review is running separately; the disposition
below is the DM's provisional recommendation until its full answer is read.

**Fixed endpoint levels.** Each row averages its32 disjoint final worlds.
Service-p10 is the mean within-episode temporal10th percentile; minimum is
mean episode-minimum total service, not individual-user continuity. Path is
metres per UAV. L1 B*=S is exact policy-identity reuse, not another32 episodes.

| Lineage / arm | Native J | Mean service | Service p10 | Minimum service | Quality | Path m/UAV | Query CPU s/episode |
|---|---:|---:|---:|---:|---:|---:|---:|
| L0 C | .326612 | 19.500854 | 18.875000 | 10.500000 | .178668 | 2330.696 | .023242 |
| L0 Q | .357172 | 21.668823 | 16.531250 | 9.531250 | .179362 | 3876.909 | .114586 |
| L0 S | .380706 | 23.325073 | 20.062500 | 10.281250 | .180516 | 2952.085 | .109606 |
| L0 old B* (T2) | .382841 | 23.546509 | 19.421875 | 9.968750 | .177298 | 4371.311 | .145162 |
| L0 CAL | .381390 | 23.355103 | 20.781250 | 10.125000 | .181396 | 3003.002 | .140807 |
| L0 CONT | .375571 | 22.975342 | 20.078125 | 10.031250 | .179721 | 2854.776 | .137102 |
| L1 C | .332437 | 19.642090 | 19.062500 | 10.968750 | .191492 | 3219.292 | .024062 |
| L1 Q | .373866 | 22.710205 | 18.250000 | 10.187500 | .186410 | 3978.513 | .111986 |
| L1 S = old B* | .401578 | 24.740601 | 21.453125 | 10.937500 | .184032 | 3276.640 | .112584 |
| L1 CAL | .394629 | 24.224365 | 21.578125 | 10.937500 | .184960 | 3201.210 | .141419 |
| L1 CONT | .396080 | 24.361450 | 20.968750 | 10.812500 | .183401 | 3179.594 | .143141 |

The complete signed comparisons are in the unmodified
[reading](../../../../runs/uav_fleet_adaptation/b05_native_consequence_a01/reading.json).
Central native-J contrasts and the pertinent controls are:

| Contrast | L0 mean [descriptive paired t95] | L1 mean [descriptive paired t95] |
|---|---:|---:|
| CONT−S | −.005135 [−.021858,+.011589] | −.005498 [−.018206,+.007211] |
| CONT−CAL | −.005819 [−.018043,+.006404] | +.001451 [−.013173,+.016075] |
| CONT−old-B* | −.007269 [−.024725,+.010186] | −.005498 [−.018206,+.007211] |
| CAL−S | +.000684 [−.014937,+.016306] | −.006949 [−.016153,+.002255] |
| CAL−old-B* | −.001450 [−.016158,+.013258] | −.006949 [−.016153,+.002255] |
| CONT−Q | +.018399 [+.004663,+.032135] | +.022215 [+.004795,+.039634] |
| CONT−C | +.048959 [+.027332,+.070585] | +.063644 [+.043900,+.083387] |
| CAL−Q | +.024218 [+.010764,+.037672] | +.020763 [+.000590,+.040937] |
| CAL−C | +.054778 [+.035288,+.074267] | +.062192 [+.037036,+.087348] |
| S−Q | +.023534 [+.006811,+.040257] | +.027712 [+.009724,+.045700] |
| old-B*−S | +.002135 [−.014907,+.019176] | 0, exact reuse |

CONT−S wins17 and loses15 J worlds in each lineage; CONT−CAL wins14/19 and
loses18/13. CAL−S wins17/14 and loses15/18. Neither pooled world counts nor the
stored equal-weight point averages create additional training instances.
There are two inherited-lineage outcomes for each finite head program, not64
independent fits, and no confirmation or simultaneous-inference claim.

**Native consequences and adverse cases.** CONT−S mean service changes
−.349731/−.379150 users per tick, service-p10+.015625/−.484375, mean minimum
−.250000/−.125000, and path−97.309/−97.046m. The service and path intervals
span both signs. CONT−CAL service changes−.379761/+.137085 while p10 changes
−.703125/−.609375. CAL−S's L0+.000684J point is accompanied by only+.030029
mean service; L1 loses.516235 service despite+.125 p10. No final arm has a
zero-total-service tick, which does not establish service to every user.

Consequential losses and positive witnesses remain in the complete record:

- L0 world29481131: CONT−S J−.112368, service−7.644531, p10−6.5; against
  old B*, CONT loses.210862J/14.335938service/17p10 users. CONT's own S
  shadow changes only13 physical decisions here, yet the independently
  reconstructed64-tick service differences are−5.546875,−7.718750,
  −7.312500,−10.000000. Small policy changes do not imply small world harm.
- L0 world29481125: CONT−S gains.132992J/9.730469service/10p10 users but
  travels2093.014m more per UAV. CAL gives a similar positive outcome
  (+.133442J/+9.765625service), so this example does not select contextuality.
- L0 world29481123: CAL−S loses.132411J/8.75service while adding1444.286m;
  CONT is better than CAL by.091469J but still loses.040942J to S.
- L1 world29483102: CONT−S loses.111252J/7.859375service/7p10 users and
  travels314.553m more. Its nine same-history physical changes and complete
  loss are both retained.
- L1 world29483116: CONT−S gains.063370J/4.0625service/3p10 users while
  travelling1938.726m less. World29483107 also has CONT−S+.057632J/
  +3.945313service, while CAL−S there is−.071741J/−4.4375service.

These are observed witnesses, not a prospective gate, causal attribution to
the first changed command, or authority to select a best head/world after
seeing outcomes. Native path differences have no measured energy price here.

**Acquisition and fitting were active.** Every address has its declared3 or4
worlds (256 addresses with3,64 with4), with weights summing1024 per lineage.
Each of the1024 cached local feature rows per lineage is distinct. Both full
branches really executed; there are2048 unique paired contexts and4096
complete acquisition episodes, not1,048,576 independent labels.

L0/L1 ΔJ standard deviations are.011955/.012126, mean absolute values
.004466/.004894 and median absolute values.000561/.000575. Zero contrasts
number280/231;259/195 pairs draw exactly the same category, with21/36
additional different-category zero contrasts retained. The near-zero signed
mean of ΔJ is expected from symmetric iid a/b sampling and is not evidence
that action information is absent. Positive/negative counts374/370 and378/415
show consequential observations, without estimating their learnable conditional
signal or guaranteeing low variance.

I directly reconstructed eight acquisition pairs (16 full raw files), covering
largest positive/negative labels, equal requests and different-category aliases
in both lineages. For example, L0 world29480424 forces actions10/2 at tick48,
agent1, giving J difference+.131710 and service+9.886719; L1 world29482767
forces0/21 at tick20,agent0, giving−.091174J/−6.167969service. Different
categories in worlds29480101 and29482011 produce identical clipped four-tick
paths and complete positions, with zero labels. Both branches' actual prefixes,
local features, cached hidden vectors and μ match at intervention. These checks
recomputed saved algebra/geometry only, with no new actor, head, native, radio
or controller query.

All four fits complete2048 finite, nonzero-gradient Adam updates and262144
cached presentations. CAL changes28/28 parameters in each lineage (L2 movement
2.059285/2.102354); CONT changes2889/3483 and2592/3483 (L2 6.547904/6.537775).
Both immutable S tensor identities remain exact. Within a lineage, CAL and
CONT use identical data and batch-order digests, with zero first-step KL and
identical first-step scalar objectives. No critic, expert target, return
normalization, additional epoch, early stopping or selected checkpoint was used.

Saved first256→last256 update-mean losses are:

| Head | First256 mean loss | Last256 mean loss | Last256 mean F | Last256 mean KL |
|---|---:|---:|---:|---:|
| CAL0 | +.000037444 | −.000153216 | +.000195790 | .004257418 |
| CONT0 | −.000150246 | −.000547157 | +.000652535 | .010537868 |
| CAL1 | +.000207988 | +.000073090 | −.000046727 | .002636303 |
| CONT1 | +.000043755 | −.000308818 | +.000391215 | .008239709 |

CONT's last-window surrogate loss is lower than CAL on the matched minibatch
stream in both lineages. These are training-stream summaries with changing
heads, not endpoint held-out label error, convergence proof or a demonstrated
native policy-improvement mechanism. The finite-grid caveat to the ideal
first-order320-factor identity remains unchanged; neither the theorem's
expectation nor its derivative at S predicts a successful finite deployment
at every member's later endogenous history.

**Actual deployed changes.** CAL changes364/10240 (3.555%) and264/10240
(2.578%) physical four-tick paths relative to original S's same-uniform shadow
on its own lawful histories. CONT changes499/10240 (4.873%) and436/10240
(4.258%). Every head changes physical decisions in all32 final worlds. Mean
TV is.025343/.019370 for CAL and.034135/.030928 for CONT; requested versus
physical changes and modal differences remain in the reader. These changes
are much smaller than the different B04 PPO program's drift, but are neither
absent nor only command aliases. CONT's mean deployed entropy changes
−.013486/+ .006885 from S, inconsistent with a shared entropy-collapse diagnosis.
The shadows show policy/physical change; they are not native reward
counterfactuals on the new history.

**Capabilities and complete-package cost.** Original S−Q gives service
+1.656250/+2.030396, p10+3.531250/+3.203125 and path−924.824/−701.873m.
Both J and path intervals favor S on these panels, while11/9 J worlds and4/5
p10 worlds remain adverse. L0 world29481125 loses.082683J/5.988281service to Q;
L1 world29483116 loses.070562J/4.761719service. These new worlds strengthen
conditional use of the unchanged assets beyond this Q, not general ordinary
control dominance or new construction replication. The heads' positive C/Q
comparisons mostly retain the already available S capability and do not show
benefit from the new fit.

L0 old B*−S's+.002135J point has14 wins/18 losses and spans zero, while p10
falls.640625 and path increases1419.226m (27/32 longer). L1 old B* is S by
identity. No new calibration was purchased, and no default T2 upgrade follows.
Q−C remains useful for mean J/service (+.030560/+2.167969 and+.041429/
+3.068115), with service-p10−2.343750/−.812500 and mean minimum−.968750/
−.781250. Competent stochastic control and its tail cost both survive.

CONT decision-query CPU is.137102/.143141s per episode versus S
.109606/.112584; CAL is.140807/.141419. Complete instrumented episode CPU is
.335760/.346830 CONT, .342083/.344583 CAL, .292913/.294116 S. The heads' full
measurements include their required extra shadow and larger evidence writes
(about.016 shadow CPU-s/episode); query CPU separately retains the implemented
head cost. These are within-run one-thread package timings, not deployment
latency or intrinsic complexity bounds. The original acquisition and native
physical costs remain part of any use decision.

**Complete incurred cost.** B05 totals4 head fits,4448 H256 episodes,
1138688 native steps (1048576 acquisition,90112 final),8192 Adam updates and
1048576 cached head rows;0 new critics, expert labels or calibrations.
Worker Student requests1382400 yield786693 actual backbone forwards and
595707 memo hits. Final head cache misses require22656 head forwards; all40960
final head decisions get saved S shadows with no extra backbone/helper query.
C/Q make40960 requests and16926 actual rankings,457002 model paths/1828008
model ticks. Worker combined power work is332977344 link slots, comprising
314362675 native dense slots and18614669 controller/helper slots. Summed cache
bytes are sequential per-episode allocations, not concurrent memory.

The reader adds exactly73728 backbone rows (2048 intervention contexts and
71680 final decisions),40960 head rows,163840 shadow motion ticks and200988
C/Q fallback-ranking geometry ticks. It verifies1138688 saved native team
ticks/5693440 agent-motion ticks, with0 new native, radio, critic or optimizer
calls. Worker+reader therefore use860421 backbone rows and1112192 head rows
including the1048576 fitting presentations; shadow geometry totals327680.
These are distinct workloads, not more fits or labels.

Summed fit wall/CPU is151.107105/149.628541s, with individual fits36.56–38.84
wall seconds. Worker wall/CPU is1446.904711/1444.100055s; reader is
181.924511/175.887418s. The enclosing chain measures1629.309645wall/
1620.467427CPU seconds (27.008CPU minutes), including its import/serialization
gaps. Peak501220KiB is the whole-process high-water mark through the reader,
not incremental reader RSS; worker peak is495112KiB. The configured local
Python3.10.20, NumPy1.26.3, Torch2.7.0+cpu run uses one intra/inter-op thread.
N8 B04 was accepted on this same physical node at20:43:15.594033UTC and shares
part of this timing window; its original operation is untouched. Support,
engineering, scientific review and publication labor remain unmetered.

Original asset acquisition+B04+B05 now totals8 fits plus2 paid calibrations,
1687552 native steps and2343.116291 measured worker/reader CPU seconds across
their actual scopes/hosts. This includes the earlier16000 supervised updates,
8.192million presentations and163840 labels; it does not erase older fleet
B01's separate2 fits/576000 steps/31190.348CPU seconds or its zero-exposure
technical failure. No left-over estimate or completed fit authorizes an
extension.

**Verification and preserved original artifacts.** The priced reader checks
all raw/source/checkpoint/data identities, complete native metric and motion
algebra, lawful feature/navigation and four-tick holds, paired prefixes, forced
independent μ draws, address weights, labels, fitted tensor/Adam identities,
all final decisions and required shadows. Other acquisition clocks retain saved
logit/density/RNG evidence without neural replay; full optimizer arithmetic is
not replayed. My separate saved-data inspection covers57 raw files:41 complete
positive/adverse final trajectories and16 acquisition branches, plus all
aggregate/signed readings and complete update streams. The independent
scientific reviewer adds its own disclosed scope; it does not repeat charged
model work.

Canonical durable storage is this configured local node's
`/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b05_native_consequence_a01/`.
There is one required evidence copy, not a new backup/archive package:

- `summary.json`:17507780bytes, SHA256
  `424b1b381aa38c029a0c19d602a726fed68e95fbe0ab4d4e46639f35f022d0de`.
  Its4448 episode rows are bulk and remain unmodified outside Git publication.
- `reading.json`:1111657bytes, SHA256
  `4b7f2d5512f0ef21d7ecde24744fe77b065e7dcc38213436ef7a0d7a383a5d5c`;
  this compact full reading is published with the native exit witness.
- `raw/`:4448 original NPZ files,2043729923bytes; every individual hash is
  bound in the original summary and was checked by the reader.
- `data/`:two paired datasets plus four complete update traces,7374169bytes;
  `assets/`:four small head+Adam checkpoints,144296bytes. Individual hashes,
  immutable original-S identities and the paid calibration source are in the
  published reading. Original S remains at its already retained remote paths.

Generation23 READY event`b8db8533bab214443bfb80c5`, wake
`a4b762f6-42b2-409f-b4fc-361c8cca6281`, was drained and consumed; generation24
is stopped, with no pending wake/event. Native queue again returned`-32600`;
foreground observation supplied the terminal event. No unread operation,
additional reader, model call or cleanup relaunch is outstanding.

**Working explanation and investment recommendation.** This study meets its
intermediate exposure predictions: many exact paid local interventions alter
complete native returns, both function classes fit and all four endpoints
change actual physical decisions. The complete added-value prediction is not
supported. Task opportunity and inherited lawful representation remain useful
through S; CONT's greater training-stream fitting does not establish useful
finite native learning, and its added compute currently lacks an observed
package benefit. The result weakens the selected finite direct-consequence
recipe, without proving that labels are useless, the features are insufficient,
or small/big policy movement, optimization or missing multi-agent credit is the
cause. There is no identified repair. This is a different contract from B04,
not a controlled attribution of its critic or PPO failure.

At this boundary I read current published shared main
`5861a1b19` topic4 through the new composition result, topic3's retained N8
complete-continuation capability, and topic2's now-complete user-waiting B03.
Their concrete effect is to keep conditional capabilities and native losses
together: factual or training-stream signal does not supply action-ranking or
complete-use value by itself, and useful ordinary continuation planning is a
capability to develop. Their hosts/rights, inference units and control laws
differ, so they are not pooled learning failures and do not license taking
another direction's selected study.

I recommend ending this exact CAL/CONT purchase, retaining both original S,
C/Q/old-B*, all four heads and their adverse evidence, with no automatic extra
fit, epoch, label sweep or threshold change. More endpoint worlds could refine
these conditional intervals without producing training replication. A fresh
unchanged four-fit acquisition at the present scope would buy recurrence for
another1138688 native steps, approximately27CPU minutes on this measured
anchor plus support; recurrence alone is not presently tied to a deployment
choice. The stronger claim that every constructive continuation is exhausted
would be unjustified. A future aggregation, objective or representation
proposal would need its own concrete native prediction and a competent
same-resource comparator; the present data do not select one. The parent
native-development question stays open. No successor study is selected, and
a small point loss does not itself constitute falsification. The assigned
substantive result returns to Root for cross-question allocation after
independent diagnosis, own publication and cleanup; this is not a request for
per-run approval or a fabricated external dependency.


<a id="b05-zero-service-correction"></a>
**B05 factual correction,2026-09-30:** the sentence in the preceding complete
reading that “No final arm has a zero-total-service tick” is incorrect and is
superseded here. The independent Scientific Reviewer found, and I independently
reconstructed from the original raw connections, that L1 world29483104 has
**S zero-service ticks0 and6; CAL ticks0,3,4 and5**, with all transmitters on
and native reward0 at those ticks. L1 B* inherits S's same two ticks by exact
policy identity, without another episode. No other executed final row has a
zero-service tick; C/Q/CONT have none in this world and all L0 final arms have
none. The original summary and published reading already record these facts
correctly; this was my prose error, not a failed reader or changed result.
CAL therefore also has a concrete zero-total-service adverse beyond S here.
Retain this correction with every later tail interpretation. No additional
model query, episode or reader was performed.


<a id="b05-final-cleanup"></a>
### B05 verified retirement — one canonical evidence copy retained

Useful source/tests were published at2e22a2ccf and the compact complete
reading/exit at25fce29b3; the explicit zero-service prose correction is57cacccc8.
The scientific reviewer completed its reads of both staged original-S inputs.
The original worker/reader are terminal and the observer is stopped with no
pending event. Fresh remote SHA256 checks still match both canonical S files.
The source collector's exact-target preview was eligible: terminal native
identities absent, no live process reference, clean snapshot, outputs outside
it and source reachable from main. Under the shared writer lock, the maintained
collector applied its terminal-snapshot path with `--sudo-process-scan` (only
the protected `/proc` inspection uses read-only sudo).

Deleted targets and measured allocated bytes before→after:

| Exact target relative to repository | Before bytes | After bytes |
|---|---:|---:|
| `.git/hmasd-launch-sources/45f17bf37d8a40b0ad39379a066cc2ec` | 1724207104 | 0 |
| `.git/worktrees/45f17bf37d8a40b0ad39379a066cc2ec` | 3559424 | 0 |
| `temp/directions/uav_fleet_adaptation` | 868352 | 0 |
| `experiments/candidates/uav_fleet_adaptation/__pycache__` | 8192 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b02/__pycache__` | 98304 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b04_native_development/__pycache__` | 81920 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b05_native_consequence/__pycache__` | 122880 | 0 |
| `tests/experiments/candidates/uav_fleet_adaptation/b05_native_consequence/__pycache__` | 73728 | 0 |

Each scratch/cache target had no tracked content or process reference before
removal. Scratch held only the two now-redundant local S copies, consumed wait
request and pre-launch memory observation; authoritative runner admission
remains in the run. All eight targets are absent. B05 net allocated bytes
reclaimed are **1729019904** (1727766528 snapshot/admin plus1253376 scratch/
caches). Prior B01–B04 retirement reclaimed5839450112bytes separately;
cumulative measured deletion is7568470016bytes. No tarball, moved retention,
backup chain or full-tree copy was created. No tool blocker or target leftover
remains. All4448 unique raw trajectories, both datasets, four head/Adam assets,
complete update traces, original bulk summary, published reading and native
records remain in the one canonical run directory. The two original S assets
remain at their verified remote canonical paths. Useful fixed code/tests and
still-imported B02/B04 modules remain for the retained result; another
operation's inputs and N8 consumer were not touched.


<a id="b05-original-independent-result-review"></a>
### B05 original independent scientific result review — 2026-09-30

The registered `hmasd-research-critic`, native child
`/root/dm_fleet_adaptation/b05_result_review`, used a separate context without
inherited DM/Root conversation. It returned the following complete answer at
2026-09-30T21:21:54.546715Z. Its wording is retained without replacement by my
summary; my response follows. Its original assignment supplied the actual
question, frozen contract and original supporting/adverse evidence, and asked
for an independent diagnosis before reading my result explanation.

> **Recommend retaining both original S assets and ending this exact B05 CAL/CONT recipe.** The heads learned the sampled objective and changed physical behavior, but neither established additional complete native value. I support the DM’s proposed stop without automatic refitting, additional labels, calibration, or confirmation. The broader native-development question remains open.
>
> I received no inherited DM/Root conversation. I recorded my provisional diagnosis before reading the original B05 recommendation, B04 interpretation, and newly published B05 result explanation. The frozen design itself included pre-result selection rationale, so this was an independent-context review, not a blinded review.
>
> The comparison remains bound to design commit `a5073c72`, scientific source `2e22a2cc`, and the original [complete reading](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b05_native_consequence_a01/reading.json). I verified that the current frozen design matches the published selection contract.
>
> **The native result supports retention, not replacement.**
>
> | Mean native J | L0 | L1 |
> |---|---:|---:|
> | C | .326612 | .332437 |
> | Q | .357172 | .373866 |
> | Unchanged S | .380706 | .401578 |
> | Previously paid B* | .382841 | .401578 |
> | CAL | .381390 | .394629 |
> | CONT | .375571 | .396080 |
>
> The consequential paired contrasts are:
>
> | J contrast | L0 mean [conditional t95] | L1 mean [conditional t95] |
> |---|---|---|
> | CONT−S | −.005135 [−.021858, +.011589] | −.005498 [−.018206, +.007211] |
> | CONT−CAL | −.005819 [−.018043, +.006404] | +.001451 [−.013173, +.016075] |
> | CONT−B* | −.007269 [−.024725, +.010186] | −.005498 [−.018206, +.007211] |
> | CAL−S | +.000684 [−.014937, +.016306] | −.006949 [−.016153, +.002255] |
> | S−Q | +.023534 [+.006811, +.040257] | +.027712 [+.009724, +.045700] |
>
> These intervals describe paired-world variation conditional on each fitted endpoint. There are two fitted lineage outcomes per head program, not 64 independent training replications. The uncertain contrasts establish neither population harm nor equivalence.
>
> CAL is the consequential ordinary comparator: it receives the same native labels, contexts, minibatch sequence, update count, and bounded correction authority. CONT’s larger function class does not consistently improve on it. Neither head’s favorable comparison against C/Q establishes added learning, because unchanged S already supplies that capability.
>
> B* also remains an uncertain tradeoff. L0’s +.002135 J over S accompanies −.640625 temporal service-p10 and +1,419.226 m/UAV travel; L1 B* is S by exact identity. There is no demonstrated default temperature upgrade.
>
> **The intervention was active, with important positive and adverse outcomes.**
>
> CONT changes physical four-tick paths relative to same-history, same-uniform S shadows on **499/10,240 and 436/10,240 decisions**—4.873% and 4.258%. CAL changes 364 and 264. Every head changes physical decisions in every final world. These are modest but real perturbations; failed loading, wholly inactive updates, or action aliases do not explain away the comparison.
>
> CONT−S mean service changes are −.349731/−.379150 users per tick; temporal service-p10 changes are +.015625/−.484375; mean episode minima change −.250000/−.125000. Mean travel falls approximately 97 m/UAV in each lineage. CONT−CAL temporal p10 falls .703125/.609375. That small travel reduction is a potential tradeoff, but no physical utility or deployment requirement prices it here.
>
> Both CONT endpoints win 17 and lose 15 J worlds. Consequential witnesses include:
>
> - L0 world `29481131`: CONT−S loses .112368 J, 7.644531 mean service, and 6.5 p10 users. Against B*, it loses .210862 J and 17 p10 users.
> - L1 world `29483102`: CONT−S loses .111252 J and 7.859375 mean service.
> - L0 world `29481125`: CONT gains .132992 J and 10 p10 users over S, while adding 2,093.014 m/UAV. CAL achieves almost the same gain, so this example does not select contextual conditioning.
> - L1 world `29483116`: CONT gains .063370 J, 4.0625 mean service, and 3 p10 users while reducing travel by 1,938.726 m/UAV.
>
> These positives preserve useful possibilities. They provide no prospective selector for the favorable worlds or actions.
>
> **One factual correction to the DM’s published prose is required and has been accepted.** The statement that no final arm has zero-total-service ticks is false. In L1 world `29483104`, raw connections and rewards show:
>
> - S: zero service at ticks **0 and 6**.
> - CAL: zero service at ticks **0, 3, 4, and 5**.
> - C/Q/CONT: no zero-service ticks.
> - B*1 inherits S’s two ticks by identity, without another episode.
>
> The original summary and reader already preserve these facts correctly. This changes the tail account without changing the stop/retain decision or introducing a retrospective adoption gate. No individual-user continuity claim follows from these team-service measurements.
>
> **The supported learning diagnosis is a gap between fitting the sampled local-consequence objective and obtaining complete fleet benefit.**
>
> Acquisition produced 2,048 paired contexts from 4,096 complete episodes. Nonzero return contrasts occur in 744/1,024 and 793/1,024 pairs. Equal-category draws and additional different-category zero-return pairs were retained. Selected raw cases confirm both substantial positive/negative consequences and exact clipped-path aliases.
>
> The near-zero signed mean of \(J_a-J_b\) is expected under symmetric independent a/b sampling. It is not evidence that actions have no consequences.
>
> All four fits completed 2,048 Adam updates. CONT’s stronger empirical fitting is real: on the final 128 matched minibatches, its average regularized objective improvement over the zero head is approximately .000525/.000482, versus CAL’s .000111/.000101. I reconstructed the zero-head reference from saved data and the recorded minibatch order. These are changing-head training-stream quantities, not held-out prediction accuracy or endpoint native gains.
>
> The interpretation should separate:
>
> - **Opportunity:** retained. Original S remains useful, and individual native interventions can materially alter complete return. This does not measure achievable improvement over competent S.
> - **Representation:** unresolved. CONT expresses changed behavior and fits this empirical objective better; that does not establish useful transferable features or representation insufficiency.
> - **Finite learnability:** the selected four fits learned a surrogate without establishing fresh complete native improvement.
> - **Complete package value:** neither fitted program supports default replacement of its original S. Acquisition and deployment costs remain incurred.
>
> The strongest simpler explanation is ordinary retained competence plus a finite-data surrogate that does not generalize into an improving deployed fleet policy. Selection noise and changed joint visitation remain plausible contributors. The evidence does not separate them.
>
> In particular, the factor-320 identity concerns the derivative at unchanged S. It cannot turn a finite training-score improvement into 320 times a native-return gain. Labels describe one intervention followed by S; deployment repeatedly changes all members’ decisions and later histories. That mismatch was a predeclared risk, and the result leaves it consequential but unproven as the cause. CONT’s greater parameter count alone also does not explain everything: CAL lacks recurring native benefit, and CONT exceeds CAL’s native mean in L1.
>
> B05 therefore weakens the sufficiency of this static-data, bounded-head recipe. It neither diagnoses B04’s critic/PPO failure nor establishes general native unlearnability. I checked the original B04 compact evidence and selected positive/adverse raw witnesses; its stopped recipe and retained S capability remain applicable.
>
> **The full bill is substantially larger than the four head fits alone.**
>
> | B05 work | Actual |
> |---|---:|
> | Head fits | 4 |
> | Acquisition / final episodes | 4,096 / 352 |
> | Native steps | **1,138,688** |
> | Adam updates | 8,192 |
> | Cached fitting presentations | 1,048,576 |
> | Sum of fit wall / CPU | 151.107 / 149.629 s |
> | Worker wall / CPU | 1,446.905 / 1,444.100 s |
> | Reader wall / CPU | 181.925 / 175.887 s |
> | Enclosing chain wall / CPU | **1,629.310 / 1,620.467 s** |
> | Whole-process peak RSS | 501,220 KiB |
> | Retained raw evidence | 2,043,729,923 bytes |
>
> Worker collection uses 786,693 actual backbone forwards after memo reuse and 22,656 deployed head forwards. The priced reader adds 73,728 backbone and 40,960 head rows, with zero native, radio, critic, or optimizer calls. Replay presentations create no new labels.
>
> CONT query CPU is .137102/.143141 seconds per episode versus S’s .109606/.112584—approximately 25%/27% higher. These are measured program costs with endogenous cache behavior, not an isolated head-cost estimate or deployment deadline test. Full instrumented episode timings additionally include shadows and evidence writing.
>
> B02/B03 acquisition through B05 totals **8 fits, 2 paid calibrations, 1,687,552 native steps, and 2,343.116 measured CPU-seconds**, preserving the differing hosts and timer scopes. Older fleet B01 remains separately incurred: 2 fits, 576,000 steps, 31,190.348 CPU-seconds, plus its recorded zero-exposure technical attempt. Engineering, review, publication, and support labor remain unmetered.
>
> **The present observation is sufficient for the current investment decision.** The frozen successful branch required useful CONT improvement beyond S, CAL, and B*. That branch was not observed; the active-but-uncertain branch supports retaining S. There is no CAL-only recurring success to adopt either.
>
> An unchanged new purchase would cost another 1,138,688 native steps, with roughly 27 CPU-minutes as the current measured anchor, plus support and retention. Additional final worlds would refine these endpoints without supplying additional training units. Neither purchase currently answers a specified adoption or allocation decision, so I recommend neither.
>
> A constructive future hypothesis remains possible—for example, changing how consequence data and deployed joint histories are aligned. It need not first prove the cause of this loss. Its complete native prediction and same-resource ordinary comparator would define a new comparison; the present evidence does not select that recipe or establish its cost. A separate local-intervention diagnostic would be worthwhile only if its result would choose such an investment. I do not recommend buying it merely to enumerate surviving causes.
>
> Root should therefore retire B05’s current investment priority while retaining the useful assets and evidence. This is a no-run recommendation for the tested package, not closure of the parent question or a ranking of other directions whose current proposals I have not reviewed. Another Pro pass offers no identified distinct value for this disposition.
>
> My independent check covered all 36 source hashes against the launch commit; original input byte/tensor identities; four head and update-trace identities and saved Adam counters; all 352 final raw hashes and native metric reductions; paired initial states, actual holds/motion, and 92,160 sampled decisions and indexed innovations; all acquisition dataset labels, addresses, weights and intervention draws against saved records; matched minibatch orders; and 16 acquisition raw branches spanning positive, adverse, equal-action, and aliased cases. I also checked four consequential historical B04 raw episodes.
>
> I performed no actor/head/controller/native/radio query, optimizer replay, or second production reader. Full acquisition neural arithmetic, radio calculations, optimizer updates, and the complete older bulk record were not independently replayed. The priced reader and engineering review retain their disclosed scope. I have finished consuming the two scratch S inputs.
>
> **MATERIAL_DISSENT: no — the DM’s proposed retention of S and end of this exact package agree with the independently reconstructed native evidence. The accepted zero-service correction must remain explicit; surrogate progress does not support an expanded native-benefit claim or automatic further investment.**

<a id="b05-independent-disposition"></a>
### B05 disposition — preserve native competence; end this consequence-head recipe

I read the whole original review and accept its recommendation and scope.
My erroneous zero-service generalization was already corrected explicitly at
57cacccc8 after reconstructing the raw ticks; it remains visible above rather
than being silently rewritten. CAL's four zero-service ticks in L1 world
29483104, compared with S/B*1's two, are part of the adverse evidence. The
original summary and reader require no correction or repeated execution.
The independent matched-last128 minibatch calculation strengthens the narrow
claim that CONT improved the sampled fitting objective beyond its zero head
and more than CAL. My preceding last256 update summaries use a different,
declared stream window; neither is held-out endpoint prediction or native
return. No additional fit, actor/head query, native episode or reader was
performed to obtain this disposition.

The belief update is specific: directly measured, complete native consequence
labels and a first-order policy-gradient bridge did not suffice for useful
finite development by this fixed static-data head program. Its intended
intervention occurred: nonzero gradients, parameter movement and physical
decisions changed. This removes complete inactivity as an explanation. It
does not identify noisy finite labels, frozen features, the objective scale,
optimization, or altered joint visitation as the cause. The first-order
identity at S does not guarantee repeated fleet deployment after finite Adam
steps. Choosing CONT after observing its training advantage would therefore
replace the stated native comparison with a surrogate criterion.

Unchanged S is still the useful capability to preserve: on these fresh panels
S−Q gives J+.023534/+.027712 with positive conditional world intervals,
better mean service/p10 and shorter paths. Both lineages retain substantial
loss worlds and S itself has the explicit zero-service case. Neither head's
positive comparison with C/Q demonstrates added development; the unchanged
asset already supplies it. CONT−S is −.005135/−.005498 and CONT−CAL is
−.005819/+.001451, all with intervals spanning zero. This supports no default
replacement, not equivalence or a universal harmful-learning claim. B04 PPO,
B05 head fitting and other hosts' continuation losses stay distinct.

I end investment in the **exact B05 CAL/CONT recipe**, retain both immutable
S checkpoints, C/Q/paid-B* references, all four fitted heads and positive/
adverse trajectories, and select no more labels, epochs, temperature search,
replication or confirmation. The complete purchase was4fits/4448episodes/
1138688native steps and1620.467427 enclosing-chain CPU seconds, including
149.628541 fit CPU seconds and175.887418 reader CPU seconds. These local
timings overlap the separately accepted N8 operation; they are not an
uncontended hardware benchmark. All prior acquisition and B01 costs remain
incurred. Engineering, review and support labor are unmetered.

This no-run choice is consequential rather than a count limit: more final
worlds narrow conditional endpoint uncertainty without changing training n;
an unchanged new acquisition/fit purchase would repeat the current unresolved
finite-development proposition at roughly the present full cost without a
specified adoption decision. A new constructive question may be worth
testing without first proving this failure's cause, but the current result
does not choose that question. Any such proposal must state the native
prediction, competent same-resource comparator, information/decision changes
and complete investment. The broader question stays open, with no producer
or selected result study now active in this direction.

At disposition I read published main5e6fed08e and refreshed throughdd3b2577d,
including its affected fleet entry and Root's preserved new allocation. The
newly selected parent B06 paid-label N8 approximation is a
different allocation with its own lead, target/model labels, ordinary reuse
controls and cost; I do not appropriate or pool it with these native labels.
Root subsequently assigned a bounded source-only feasibility/cost assessment
with the existing Oracle: whether count-diverse teacher-imitation continuation
of both retained S lineages could buy useful population generalization beyond
unchanged parameter reuse and equal-cost further N5 imitation. This is an
unselected candidate, with no code, actor/teacher/controller/model/native
query, fit or pilot authorized. I therefore keep this direction exploring
only for that explicit source work, preserve the launch-bound lead and
native routing, and retire only the superseded substantive B05 result plan. The
reusable topic4 judgment now separates sampled-consequence fitting from
complete fleet benefit while retaining the original S capability and zero-
service adverse. Full source, compact reading, all required unique evidence
and measured cleanup are preserved. No material dissent or additional Pro
dependency remains. The assigned result returns to Root; the subsequent
source-only accounting continues in this notebook for its cross-question
choice. No successor result study has been selected, and no automatic rescue
or recurring status check follows from B05's end.


<a id="count-generalization-source-feasibility"></a>
### Source-only count-generalization feasibility and full cost — unselected candidate

Root explicitly assigned this bounded source/interface and cost assessment
after B05 publication6d6af7eb8. The existing separate-context Oracle owns idea
discovery and independent scientific challenge; Root owns the cross-question
choice. Nothing below selects a new result study or authorizes implementation,
new actor/teacher/controller/model/native queries, fits, a quality pilot or a
new direction. I read source and existing saved JSON only. The B05 disposition,
immutable original S assets, four heads and explicit zero-service correction
remain unchanged.

The Oracle's current candidate asks about **static-count interpolation and
N5 retention**, not within-episode loss, rejoining or teammate learning.
For each retained S lineage, F would continue full-network teacher imitation
only atN5; M would use equally many complete N3/N7 episodes in each128/64/64
acquisition phase. Both would receive81920 C_N labels and8000 updates. The
suggested final panel contains original-parameter P, F and M for each lineage,
ordinary C_N/Q_N and previously paid B*0 at its fixed temperature2; B*1 is P1
by identity. N4/N6 are held out from both continuations and N5 is retention.
The two fixed stochastic tapes are within-world replicates. No new temperature
search, selected endpoint or proof of transfer is supplied by this sketch.

I refreshed the relevant published background at6d6af7eb8: topic2's B18
technical missingness, B19 positive and B20 adverse mixed-count comparison;
the native fleet-loss/availability result; and topic4 through B05. Their
concrete effect is to preserve unchanged reuse and competent fixed-count
training as substantive controls, report every count and retention outcome,
and avoid a pure-count, general-transfer or failure-repair claim. The earlier
Gaussian actor/critic mixed-count program is different from this categorical
teacher-imitation candidate; its adverse confirmation is neither erased nor
treated as a universal veto. B18's missing M endpoint remains technical
missingness. Static population interpolation also does not test adaptation
to actual member loss or establish a need to move replacements.
[Current reusable background](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
[original mixed-count fixed result](../agent_count_generalization/CLAIM_ordered_roster_interpolation_20260924.md#2026-09-25--fixed-b20-result),
[native availability scope](../uav_availability_recovery/NOTES.md#b01-complete-native-reading).

**Actual interface.** The inherited Student has114 inputs and34715 parameters
(`b02/model.py:15–40`), but the complete program is not count-portable:
`b02/controllers.py:32–37` rejects more than four visible peers;
`_setup:74–82` and the original C's `_decide:171–194` infer residual
interference only when p<4. Correct static-count analogues need p<N−1 for
both teacher/controller and analytic helper. The ten peer slots accommodate
the proposed maximum N7, but slots beyond the first four were always padded
under original N5 training. Learning them is part of different exposure,
not evidence of scalar-count causality. The helper's eligibility bit and
navigation transitions remain consequential actor inputs.

`b02/policies.py:19–23` restricts private addresses to agent<5;
`b02/collect.py:39–105` fixes observation, command, mask and agent loops toN5;
the native factory in `ucope/uav_motion_prefix_b01/environment.py:8–24`
constructs N5 explicitly. Reward/reader shapes and count checks also need
new N-aware direction-local paths. Frozen source cannot be patched in place:
other results and live consumers bind its exact hashes. C_N/Q_N must use the
same declared known N; Q_N remains the .10 departure law around corrected C_N.
C, helper and policy caches stay episode/model/count-local. Original weights
with this new helper/interface should be called parameter reuse P_N, not
unchanged execution of the original complete package outsideN5.

The proposed count-conditioning branch is128 zero-initialized weights added
to the original first-layer preactivation as v·phi(N), with phi=(N−5)/2.
Total actor parameters would be34843, an increase of128 (about.37%). This
retains the original114-wide matrix operation rather than replacing it with
a115-wide GEMM. In real arithmetic the initial logits agree; implementation
would still need explicit source/arithmetic identity checks. With phi(5)=0,
fresh zero Adam state and no weight decay, F supplies zero data gradient to
the count branch, while M can learn it. That asymmetry follows from the
experience support, not unequal permission to use known count. The Oracle
explicitly retained **fresh Adam**, rather than silently loading a frozen
checkpoint optimizer that has no new branch state.

The original construction has another consequential semantic:
phase0 executes C and uses the same query as its label; phases1/2 execute
the current student **greedily**. `b02/study.py:124–142` passes aggregate1/2,
and `collect.py:54` samples only the separate S_sampled evaluation arm. The
Oracle retained this greedy aggregation law. Sampled aggregation would be a
different acquisition process even with identical row/update counts.

**Initial layouts and matching.** Native `MultiUAVEnv.reset:252–263` draws
3N UAV coordinates before generating users. A repeated numeric seed therefore
does not preserve user layouts across N. I raised this source fact; the Oracle
prefers a new evaluator-side contract with an independently addressed50-user
map and seven-UAV position array, taking its first N rows. It preserves the
native uniform marginals while explicitly changing the joint initialization
coupling. The candidate would match F/M acquisition layouts and share final
layouts across N/lineages. C/Q reuse is only within identical N/world/tape
conditions, never a cross-N trajectory reuse. Initial geometry, command laws,
interference and total capacity still change with N; matching exogenous inputs
does not isolate a pure population mechanism.

This initializer must refresh channel state and observations after any
evaluator-side placement, bind all initial arrays, and keep truth outside
policy inputs. If layered over native reset it adds a refresh per complete
episode plus its addressed draws; constructors and discarded native resets
remain charged. Its exact implementation has not been selected. The numerical
initializer is small; source, pairing and stale-state verification are its
main engineering cost. No layout was generated to prepare this assessment.

**Complete exposure under the current sketch.** Balanced N3/N7 episodes give
30%/70% of M's label rows under the unchanged row-uniform cross entropy. Each
fit still has40960/61440/81920 cumulative rows,30/20/20 epochs, batch512,
2400/2400/3200 updates and4096000 presentations. F/M match labels, updates,
team steps and aggregate UAV steps; differing N, teacher geometry and
endogenous cache hits prevent calling them exactly compute-matched.

| Proposed work | Complete count |
|---|---:|
| Full-network fits | 4 |
| Acquisition episodes / native steps | 1024 /262144 |
| Final episodes / native steps | 1632 /417792 |
| Total H256 episodes / native steps | **2656 /679936** |
| Total native UAV ticks | 3399680 |
| New C_N labels | 327680 |
| Adam updates / fitting presentations | 32000 /16384000 |
| Worker full-C requests, including labels | 419840 |
| Full-C no-memo paths / candidate model ticks | 11335680 /45342720 |
| Worker student requests, before memo reuse | 593920 |
| Helper request ceiling, including phase0 | 757760 |

Final accounting is6 P/F/M programs×3counts×32worlds×2tapes=1152episodes,
plus192 B*0,192 Q and96 deterministic C episodes. B*1 reuses P1, with no
extra acquisition or calibration. Of the593920 student requests,163840 are
greedy acquisition requests and430080 are final requests. Phase0's executing
C and expert label are the same327680-label accounting stream, not an extra
163840 C calls. Full-C requests by N3/4/5/6/7 are49152/24576/194560/36864/
114688. At20 visible users and p<=N−1, their power-link ceiling is951705600;
the analytic-helper ceiling is109854720. These are no-memo arithmetic ceilings,
not forecasts of actual queries. Native dense slot counts, extra initializer
refreshes and constructor resets must be included separately at the selected
N schedule; the fixed N5 multiplier275 cannot be reused for all counts.

The Oracle's concrete proposed reader scope is all saved episode metrics,
states, sources, innovations, label-score and counter checks; **430080 final
student neural rows**; and at most80 predeclared saved contexts with C/helper
numerical spot-checks spanning five N regimes. If each context evaluates both
programs, charge up to80C rankings/2160paths/8640candidate model ticks plus
80helper calls separately. It does not include an acquisition-actor sweep,
full teacher arithmetic or optimizer replay. Such additions would cost up to
163840 extra actor rows,419840 C requests/45342720candidate ticks and32000
verification Adam calls/16384000 presentations respectively. Saved provenance
and trace checks are not renamed full arithmetic replay. This scope still
needs prospective fixation if a study is selected; it is not a new audit now.

**Timing, storage and support estimate.** Original B02/B03 worker CPU is
101.990390/92.334372s on the remote one-thread CPU runtime. Acquisition-only
episode totals are46.412287/45.547210s, and fit totals14.515561/15.168131s.
Original sampled final episodes average.234974/.245807CPU-s. On the different
local host, B05 S/Q/B*0 final episodes average.293515/.293031/.330199CPU-s,
with the recorded concurrent operation. Those scopes suggest roughly11–14
worker CPU minutes for an unchanged-N5 extrapolation of this larger panel.
They are not a benchmark of the new program.

I find **15–30 worker CPU minutes plus10–30 reader CPU minutes** plausible
planning allowances, subject to the above bounded reader and actual cache
behavior. B02/B03 full-C memo hit rates were about90%, with observed users
far below20; new N and learned visitation can materially increase scoring
and assignment work. Worst-case misses can exceed these timing estimates.
B02/B03's5.553/5.168s readers executed zero actor, expert, radio or optimizer
calls and do not price the new neural reader. B05's175.887s reader checked
1138688 saved native ticks plus73728 neural rows; it supplies another scoped
anchor, not a linear throughput guarantee.

One complete fit's FP32 features/int64 labels require38010880bytes, plus
327680bytes for a saved FP32 count scalar, before copies. Sequential fits
and episode-streamed reading can plausibly remain below1GiB working RAM;
allow roughly1–3GB of new retained evidence depending on saved arrays and
compression. Checkpoint/Adam storage is small relative to raw trajectories.
These are source-derived estimates, not admission or measurements.

My support estimate is **8–14 unmetered planning hours**, approximately5–9
for implementation and independent engineering review plus3–5 for complete
reading, publication and cleanup. It includes roughly1–2hours for the new
layout initializer and cross-N binding work. No API blocker is apparent,
but this is a new complete comparison rather than a cheap portability panel.
Actual compute placement and fresh admission are not needed for source work
and are not yet assigned to this candidate.

The code identities and original costs above are read from the frozen B02/
B03 source and their canonical summaries, with B05 as an explicitly different
timing anchor. They were sent directly to the assigning Oracle, including the
pairing and greedy-aggregation corrections. This completes my factual scope;
the Oracle's independent recommendation and Root's allocation remain the next
decision. No new source file, fit, model query or native step has been created.


<a id="count-generalization-original-independent-recommendation"></a>
### Original independent count-development recommendation — 2026-09-30

Root requested preservation of the complete answer and my response before
its cross-question choice. The same registered, separate-context scientific
Oracle `/root/oracle_next_capability` returned this original answer at
2026-09-30T21:42:26.365686Z. This source-only recommendation selects no run.

> **Recommendation: revise the portability premise and retain one costed static-count development candidate.** For the next fleet-learning allocation, I prefer the complete comparison below to reserved S2 acquisition or a transfer-only ranking panel. It tests a distinct use of the demonstrated S capability. Its estimated **8–14 support hours** make it a substantive investment, despite modest compute. It should not displace the selected N8 amortization study; this source-only request selects no run.
>
> I retained my separate reviewer context and earlier analysis. Root supplied the premise and B05 headlines, so this follow-up was not blinded.
>
> **The frozen package is not count-portable.** The source contains consequential N5 assumptions:
>
> - The environment factory, collector shapes, agent loops, reward summation and sampling-address guard fix five UAVs.
> - The controller rejects more than four visible peers. Both C and the cheaper helper infer unobserved interference only when `visible_peers < 4`. Removing the rejection alone would produce incorrect completeness assumptions at larger counts.
> - The network accepts 114 features, but peer slots beyond the fourth were always zero during N5 acquisition. Fixed input width establishes neither learned support nor invariance.
> - Native reset draws all `3N` UAV coordinates before user positions. Reusing a numeric seed across N therefore changes the user map.
>
> These are direct source findings; the current controller, policy, model and factory hashes match the B02 bindings. A prospective package needs explicit new wrappers. Outside N5, frozen weights with a generalized helper would be **parameter reuse under a revised interface**, not unchanged-package transfer. [Controller](</home/fires/hmasd-wsl/experiments/candidates/uav_fleet_adaptation/b02/controllers.py:32>), [policy](</home/fires/hmasd-wsl/experiments/candidates/uav_fleet_adaptation/b02/policies.py:19>), [factory](</home/fires/hmasd-wsl/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py:8>), [native reset](</home/fires/hmasd-wsl/envs/pettingzoo/uav_env.py:252>).
>
> The useful positive remains meaningful. B05’s fresh S−Q comparisons give J **+.023534/+.027712**, mean service **+1.656/+2.030**, temporal service-p10 **+3.531/+3.203**, and shorter mean paths. Preserve the adverse exception: lineage-1 world29483104 has S zero-service ticks0 and6; CAL has four. The completed independent review supports retaining S and ending exact CAL/CONT. Active fitting and changed physical decisions did not establish added native value, and no common failure cause was identified. I checked the consequential paired arrays and costs and reused that review’s broader reconstruction. [B05 evidence](</home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b05_native_consequence_a01/reading.json>), [original review and disposition](</home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md:4268>).
>
> The strongest contrary evidence is the earlier mixed-count comparison. Gaussian B19’s promising development result reversed in all three fresh B20 training pairs: M−F J averaged **−.062244 at N5 and −.083490 at N7**, with the N7 interval entirely negative. All six fitted policies nevertheless improved over initialization. This argues against treating population diversity as an automatic improvement. It does not establish failure of the different categorical, teacher-imitation contract proposed here. [B20 aggregate](</home/fires/hmasd-wsl/runs/agent_count_generalization/s1_ordered_roster_confirmation_b20_aggregate_20260925/summary.json>).
>
> Other records keep ordinary competence central. In both native fleet-loss panels, MAPR and DIRECT learned substantially but remained below BCRH on failed-zone recovery. Availability recovery retained a successful stationary-hold endpoint alongside two harmful dispatch endpoints; it supplied no initialization comparison establishing that endpoint’s learned improvement. Neither contract tests categorical S across physical fleet sizes. July’s information gate also allowed ordinary TEAM_REC to reconstruct the useful roster, and its external review retained legitimate fixed-slot routing. These results rule out manufacturing an advantage through deprived controls; they do not close the present question. [Fleet-loss endpoints](</home/fires/hmasd-wsl/docs/research/candidates/variable_n_fleet_churn/evidence/b01_formal_20260905_02/evaluation_episodes.json>), [second panel](</home/fires/hmasd-wsl/docs/research/candidates/variable_n_fleet_churn/evidence/b01_seed02_20260905_01/evaluation_episodes.json>), [availability results](</home/fires/hmasd-wsl/runs/uav_availability_recovery/b01_joint_reserve_a01/summary.json>), [July gate](</home/fires/hmasd-wsl/docs/research/cdc/EVIDENCE_NOTES/20260723_ASYNC_COMMITMENT_ROSTER_G3_INFORMATION_GATE.md>).
>
> **The worthwhile question is whether count-diverse acquisition develops useful interpolation beyond ordinary continued training and inherited reuse.** It concerns actual fleet size, fixed within each episode—not failure recovery, rejoining, identity memory or heterogeneous teammates.
>
> The smallest complete comparison I recommend is:
>
> | Arm | Acquisition and purpose |
> |---|---|
> | P | Each original S asset, frozen, with the generalized interface; measures parameter reuse. |
> | F | Full-network continuation using only N5; controls ordinary additional imitation. |
> | M | Same continuation budget, with equal numbers of N3 and N7 episodes within each acquisition phase. |
> | C_N / Q_N | Correct count-aware C and its existing `.10` perturbation law; competent ordinary references. |
> | Paid B* | Retain lineage-0 S at temperature2. Lineage-1 B*=P is exact reuse. No new calibration. |
>
> For each of the two inherited lineages, fit F and M once: **four fits**, with fresh Adam and no inherited optimizer state. Retain the original acquisition law: **128 C-roll-in episodes, then64 and64 episodes executing the current student greedily**, with teacher labels throughout. Final learned deployment remains temperature-one categorical sampling. Each fit receives81,920 labels and8,000 updates; only its final endpoint is evaluated.
>
> Give every participant the reliable pre-mission fleet count. An economical learner interface is the original 114-wide first-layer calculation plus a zero-initialized 128-weight branch, `u·(N−5)/2`, before ReLU. Both F and M receive the same architecture. This preserves the inherited computation at initialization and lets M learn count dependence. Its implementation still needs explicit arithmetic checks. The treatment also exposes previously unused peer slots; a positive result would not isolate scalar-count conditioning.
>
> Balanced M **episodes** yield30% N3 and70% N7 **label rows** under the inherited row-uniform loss. Keep that exposure explicit. Labels, updates, team steps and aggregate UAV steps match F; actual CPU and geometry work need not match.
>
> Evaluate at **unseen N4 and N6**, plus **N5 retention**, using32 fresh shared layouts and two fixed innovation tapes per stochastic policy. This gives1,632 evaluation episodes. C/Q are shared across lineages within each N; duplicate policy identities are reused.
>
> Preserve H256, four-tick holds, the27 commands, all-on transmission,50 users, capacity10,3dB eligibility and the existing J formula. Changing N changes interference and physical capacity; comparisons remain within N. Use a declared environment-side layout generator with independently addressed users and up-to-seven UAV positions, taking the first N positions. Charge initialization and channel refresh. Never treat equal seeds as proof of equal exogenous inputs.
>
> The primary comparison is M−F on the equal-weight N4/N6 target population, accompanied by every count/lineage result, M−P, M−B*, M−C/Q, and N5 retention. Report service, p10/minimum/zero-service tails, quality, travel and actual computation alongside J. Record visible-peer exposure and requested versus executed motion. Two tapes remain within-world repetitions; this supplies32 world clusters and two inherited-lineage blocks, not confirmation across a training population.
>
> The literature supports this conjecture’s components, without supplying its outcome. DAgger motivates acquiring labels on learner-induced states; its guarantees do not establish native benefit for this finite neural program or its stochastic deployment. [Ross et al., Algorithm3.1](https://proceedings.mlr.press/v15/ross11a/ross11a.pdf). ADAPT explicitly builds object-wise aggregation, while InforMARL constructs variable agent–entity graphs and tests transfer across counts. Those mechanisms show why input handling matters; they do not make the current padded MLP invariant. I would not add either architecture as an automatic repair. [MARL-0104, pp3–4](</home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0104.json>), [My-lib `icml-2023-pmlr-v202-nayak23a`, pp3–7](</mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2023/pmlr-v202-nayak23a/arxiv-2211.02127.pdf>). Foundations P08’s mean-action approximation also has unestablished assumptions here; its indexed local PDF was unavailable, so I checked the [publisher PDF, equations6–8](https://proceedings.mlr.press/v80/yang18d/yang18d.pdf). All three libraries were searched; no novelty claim follows.
>
> **The complete prospective bill is:**
>
> | Work | Amount |
> |---|---:|
> | New fits / teacher labels | 4 /327,680 |
> | Adam updates / fitting presentations | 32,000 /16,384,000 |
> | Acquisition / evaluation episodes | 1,024 /1,632 |
> | Total native steps | **679,936** |
> | Full-C requests, including C/Q evaluation | 419,840 |
> | Student collection requests | 593,920 |
> | Worker CPU estimate | **15–30 minutes** |
> | Reader CPU estimate | **10–30 minutes** |
> | Engineering, review, reading, publication and cleanup | **8–14 unmetered planning hours** |
> | Retained evidence / sequential working RAM | roughly1–3GB / plausibly below1GiB |
>
> The DM independently confirmed these counts and estimates from source. B02/B03 fit work was approximately14.5/15.2 CPU-seconds per fit, but their high cache reuse is not guaranteed at new counts. Zero memo reuse permits11,335,680 C candidate paths and45,342,720 candidate ticks; severe misses could exceed the timing range.
>
> A concrete reader scope fits the estimate: all episode metrics, bindings, RNG records, label-score consistency and counters;430,080 final student neural rows; and at most80 saved contexts checked numerically by C and helper. That adds at most2,160 candidate paths/8,640 model ticks. Acquisition actors, all teacher arithmetic and optimizer updates would not be exhaustively replayed. No such checks have been executed for this candidate.
>
> Outcome-dependent decisions are straightforward:
>
> - **M improves F and inherited references across both held-out counts and lineages, with acceptable retention and costs:** retain a constructive population-development capability; consider replication only for a specified use or claim.
> - **F and M both improve P without a consistent M increment:** ordinary continued imitation explains the useful development; do not credit population diversity.
> - **P/B* remains competitive:** preserve parameter reuse and decline further acquisition.
> - **M improves fitting but lacks complete native benefit, or gains are offset by consequential losses:** end this exact mixture recipe. Preserve any conditional positives without automatically selecting a count, new architecture or larger training purchase.
>
> A transfer-only comparison retaining P/B*/C/Q would still cost864 episodes and221,184 steps, while paying much of the same interface and layout engineering. I would not buy it as a mandatory preliminary gate. Reserved S2 remains a distinct option, priced at2–4 worker CPU-hours,15–45 reader minutes and5–9 support hours. The count study costs more support but tests full-parameter development across physical populations using an acquisition procedure that already produced useful assets; it is not another bounded consequence-head retry. Stopping incurs none of these new costs and preserves the demonstrated N5 capability.
>
> I checked source/configuration bindings, consequential B05 summaries, B20 block and own-learning results, both fleet-loss endpoint files, availability evidence and the cited primary passages. I reused applicable earlier H6/SET analysis and the completed B05 critic. No code edits, fits, actor/controller/native queries or experiments occurred.
>
> **MATERIAL_DISSENT: no — Root marked portability unverified and selected only this source assessment. The supported correction is explicit: unchanged-package portability is false; the proposed learning comparison requires a revised, fairly shared interface and its full engineering cost.**


<a id="b06-count-development-design"></a>
### B06 selected static-count development — 2026-09-30

**Decision and response to the complete advice.** Root selected this complete
study at21:48 UTC after the above independent recommendation and my source
assessment. The reviewer is the existing `hmasd-research-critic`, created in a
separate context as `/root/oracle_next_capability`; its original full answer is
preserved immediately above. I accept the corrected question and comparison.
There is no material dissent and no reason to repeat that selection review or
add a Pro round with the same question. Its advice is reasoning, not new
empirical evidence. This is the only active result-bearing study in my question.

The intended contribution is a conditional empirical answer about **developing
useful count interpolation from competent learned parameters**. The complete
policy acts in a coupled, partially observed team: changing N alters capacity,
interference, observations, labels and the future states induced by every UAV's
choices. Mixed acquisition may teach use of peer-slot/count variation absent
from continued N5 acquisition. The competing ordinary explanation is that
additional imitation alone develops the asset, or that the inherited asset
already supplies the useful behavior. This is why F and P/B* are indispensable.
M−F is a complete acquisition-package comparison, not the causal effect of the
new scalar count, and not a test of unchanged-package portability. Its native
prediction is positive M−F on the equal-weight held-out N4/N6 target, with the
same signs in both inherited lineages and without consequential N5 retention
loss. Parameter movement, peer exposure and fitting curves show what was
learned/visited; none can replace that native comparison. No observed fitting
improvement or minimum activation rate is required for admission.

I refreshed published main at92b6e324e254b129cd790fc87749ae1a5761f35f.
[RESEARCH topic2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练)
retains B18 technical missingness, B19's positive development and all three
adverse B20 fresh training pairs. Their effect here is to preserve F, both
lineage blocks and every count/tail rather than assume diversity is useful.
[Topic4](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)
and my [B05 disposition](#b05-independent-disposition) retain the S capability
and the failed native-head increments. B06 does not reopen CAL/CONT or diagnose
its cause. The unavailable unchanged interface is corrected prospectively;
the earlier record and its costs remain intact. Fleet-loss and availability
results support strong ordinary references but have different event/control
contracts; they neither refute nor establish this static-count comparison.

I personally read Ross et al.'s original DAgger paper, section2/Algorithm3.1
and Theorems3.1–3.4 ([primary PDF](https://proceedings.mlr.press/v15/ross11a/ross11a.pdf)).
Learner-induced acquisition motivates the continuation; this finite,
three-stage neural recipe and stochastic deployment do not inherit a native
reward guarantee. I also read ADAPT `MARL-0104` pp3–4 in
`/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0104.json` and InforMARL
pp3–5 in `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2023/pmlr-v202-nayak23a/arxiv-2211.02127.pdf`.
Their object aggregation/graph interfaces explain an alternative source of
count handling, not a property of our padded MLP. I have not independently
read InforMARL's transfer-results pages or the mean-field passage because
neither is load-bearing for this contract. The complete advice records its
broader search and primary reading. No novelty, invariance or theorem claim
is made, and no graph redesign is reserved as an automatic repair.

**Fixed host and policy contract.** N is constant within an episode and is
reliable public pre-mission metadata for every policy, helper and ordinary
controller. The host keeps50 anonymous static uniform users,1000m square,
50–150m altitude,30m coordinate motion/tick, H256, four-tick holds, the same
27-command ordering, all-on transmission, capacity10,3dB eligibility and
native `J=mean_t(.7*served_t/50+.3*quality_t)`. No new radio action,
communication, user truth, global critic, history, agent identity feature or
deployment teacher is given to learned policies. Motion uses actual local
observations and each program's own navigation state. A chosen category is
held for four ticks and independently clipped in each coordinate by the
native host. Requested categories, held commands and executed displacement
are all retained; different categories can yield the same physical path.

New direction-local C_N and helper code checks at most N−1 visible peers and
uses `visible_peers < N−1` for the unobserved-interference residual. The
original free-space arithmetic, ordered observations, score, argmax tie
order, fallback sweep and navigation update remain bound. Cache identity
includes N, the103 ordered FP32 fields and predecision navigation; caches
are private per agent/episode and discarded on every model version change.
Time is excluded only because this static four-tick policy does not use it.
Q_N keeps `.90` mass on C_N's category and `.10/26` on each other category,
including physical aliases. Fallback changes navigation/features; it does
not forcibly replace a learned categorical choice. B02–B05 files, original
C source, host and adapter remain unchanged.

**Arms and learner.** For each immutable B02/B03 S lineage, P is the frozen
weight asset under this new interface. F and M each initialize the same
34,715 parameters, adding128 exactly zero count weights before the first
ReLU: `Linear114(x) + u*((N-5)/2)`. The original first-layer matrix shape and
all later layers stay unchanged; all34,843 parameters train. Count-dependent
helpers make P_N a revised program outside N5, even with identical parameters.
The count branch remains differentiable at initialization; no zero-branch
shortcut may erase its gradient. F receives only N5, so its count branch
has zero data gradient and stays zero with weight decay0. This is a recorded
property, not an information restriction on F. Initial FP32 logits are
checked with synthetic full-domain fixtures; no result-asset probe is added.

Each F/M fit has128 C_N-roll-in episodes,64 current-student **greedy**
episodes, then64 more after the first aggregate update. At every four-tick
agent decision C_N supplies one label, including its executing label during
phase0. Data append in phase/world/tick/agent order. M alternates N3,N7
by phase-local episode index, beginning with N3; every phase is balanced in
episodes. F has N5 for the same world-address list. Both therefore acquire
40,960/20,480/20,480 new labels, with cumulative40,960/61,440/81,920 rows.
M's row-uniform loss gives30% N3 and70% N7 exposure. It is not a reweighted
equal-count loss. All rows, repeated states, aliases and fallback labels stay.

Each fit starts one fresh Adam, carried across its three phases; no inherited
optimizer state is loaded. Full shuffled epochs30/20/20, batch512 with no
partial batch, learning rate3e−4, betas(.9,.999), eps1e−8, weight decay0,
amsgrad/foreach/fused false, global gradient clipping1.0 and ordinary mean
cross entropy exactly fix8,000 updates and4,096,000 presentations per fit.
Training uses FP32 batch512 arithmetic; deployment uses FP32 one-row
arithmetic, as in the original imitation package. Changing minibatch size or
adding extra data/endpoint forwards is not a numerical optimization of this
contract. Save each phase state/optimizer and existing pre-update training
stream statistics; final selection is the fixed last phase only. No validation
selection, temperature sweep, early stopping or additional fit follows a score.

**Addressed worlds, layouts and innovations.** A literal-source/config search
found no existing integer2951xxxx seed assignments before fixing these ranges:

| Domain | Fixed addresses |
|---|---|
| Lineage0 F/M acquisition |29510000–29510255, consecutive128/64/64 phases|
| Lineage1 F/M acquisition |29512000–29512255, same phase lengths|
| Shared final worlds |29515000–29515031|
| Layout root |29514001|
| Final private innovation tapes0/1 |29514011 /29514012|
| Within-lineage F/M shuffle roots |29514101 /29514102|
| Discarded actor constructors by lineage |29514201 /29514202|
| Native environment constructors N3..N7 |29514303–29514307|
| Necessary native correctness world |29519000, shared across N3..N7|

For a world w, `default_rng(SeedSequence([29514001,w,1]))` makes one
FP64 `uniform(0,1000,size=(50,2))` user array. Independently,
`default_rng(SeedSequence([29514001,w,2]))` makes one FP64
`uniform(low=[0,0,50],high=[1000,1000,150],size=(7,3))` UAV array;
N uses its first N rows. These exact array arithmetic and row orders define
the new joint initialization. They preserve native uniform marginals and
explicitly change the cross-count coupling. Equal numeric native seeds alone
do not supply that pairing. F/M share exogenous arrays within lineage/world;
all final arms/counts/lineages share each final world's users and nested UAV
starts. Different N still changes the entire physical problem.

Five native environments are constructed once, one per N3..N7. Each episode
first makes the unchanged native `reset(seed=w)` (charged and discarded),
then installs copies of the two addressed arrays, clears the path-loss step,
refreshes channel state and rebuilds observations plus adapter state. Bind
initial arrays and the generated seven-UAV array in raw evidence; assert the
first returned local observations are from this refreshed geometry. Nothing
from those evaluator-only arrays enters the actor/helper except native local
observations. Native discarded draws/refreshes and constructor resets remain
in the cost. No mid-episode state replacement occurs.

At final decision(t,i), draw exactly one FP64 uniform from
`default_rng(SeedSequence([tape_root,w,t,i])).random()` with0≤i<N,
t in0,4,…,252. Use the existing nominal FP64 softmax and inverse-CDF rule,
retaining its finite-grid caveat; no resampling of C, duplicate categories or
aliases. Roots are shared across stochastic arms/lineages/counts for paired
private innovations, not a shared-policy broadcast. Greedy acquisition uses
no innovations. Epoch order is `default_rng(SeedSequence([shuffle_root,
phase,epoch])).permutation(n_rows)`; F/M share the within-lineage roots but
their collected rows and visitation differ. There is no count-dependent
change to the action alphabet or stochastic decoder.

**Final panel and primary reading.** At each N4,N5,N6 and each32 new world,
run two fixed tapes of P/F/M for both lineages, B*0=P0 at temperature2,
and Q_N. Run deterministic C_N once per world/count. B*1=P1 at temperature1
is metadata identity reuse, not another episode; C/Q are exact shared
programs within N/world/tape across lineages. P/F/M account for1,152 final
episodes, B*0 for192, Q for192 and C for96:1,632 complete evaluations.
No adaptation or calibration is performed during the panel.

For each metric and world, average its two tapes before comparisons. The
primary target is M−F averaged equally over N4 and N6 and both lineage
blocks; its paired descriptive t95 interval uses32 world-cluster values.
Also report the32-world paired distribution for **every count and lineage**,
the per-lineage equal-N4/N6 target, M/F−P, M−B*, M/F/P/B*−C/Q and N5
retention. The two inherited lineages are fixed blocks, not a training
population, and the two tapes are within-world repeats, not64 independent
worlds. Report J, mean service, temporal p10/minimum/zero-service counts and
longest zero streak, mean quality, mean path per UAV and query/native/fit/
reader compute. Include all adverse worlds and material component conflicts;
do not select a favorable count, tape, lineage or endpoint after reading.
No significance threshold, equivalence claim or default operational adoption
is attached to this exploratory comparison.

The constructive prediction receives support only if the complete M−F
increment is coherent across held-out counts/lineages with the native tails,
N5 retention and acquisition/runtime bill assessed explicitly. If both F/M
improve P without a coherent M increment, ordinary continued imitation gets
the credit. If inherited P/B* remains competitive, preserve reuse. Active
fitting without useful native consequence ends this exact mixture recipe;
isolated positives remain conditional facts. A harmful or unresolved result
does not obligate an architecture change, larger mixture, new seed or rescue
of B05. At the read boundary obtain independent scientific diagnosis, publish
the conditional judgment and return the next investment choice to Root.

**Necessary correctness and bounded reader.** The new initializer/N-shaped
collector warrants one prospectively charged native integration fixture:
five8-tick trajectories at world29519000, N3..N7, with C_N execution and
the analytic helper at both decisions. This verifies nested initial arrays,
refresh/local-state consistency, peer thresholds, holds, native motion and
native metric algebra. It is run once inside the same admitted producer,
using the five environments subsequently used by the main study, with no
fit, neural actor query or endpoint-quality selection. Its5 partial
trajectories/40 native steps/200 UAV ticks and50 C/50 helper requests are
additional engineering exposure, separately retained. A failed correctness
assertion terminates the attempt and preserves actual work; it does not
authorize a duplicate retry. Synthetic tests use artificial parameters and
fake hosts; repeated native pytest smoke runs are not part of the scope.

The one complete reader checks every saved trajectory's initial bindings,
source/state identities, native metrics, command holds/displacements,
terminal boundary, local feature encoding, navigation, visibility counts,
RNG addresses, supplied score/label consistency and counters. It verifies
all430,080 final student one-row forward laws, including repeated memo hits;
it does not run an acquisition-actor sweep or repeat fitting. To bound
teacher/helper arithmetic, select the first16 saved decision rows per N in
the fixed ordering: N3/N7 from lineage0 M phase0, N4/N5/N6 from final C_N,
then ascending world,tick,agent. Query both C_N and helper on those80
contexts exactly once:80 rankings/2,160 paths/8,640 candidate model ticks
plus80 helper calls. Saved labels/scores elsewhere are checked algebraically,
not called exhaustive independent teacher replay. The correctness fixture
is read from saved arrays, with no additional replay. Optimizer states,
shuffle digests, phase movements and logs are checked without32,000 extra
Adam calls or16,384,000 extra fitting presentations. No complete same-input
P shadow sweep was priced; requested/executed movement comes from each
program's own raw trajectory. Missing indispensable evidence quarantines
its dependent interpretation rather than inventing a favorable conclusion.

**Complete prospective cost and scope.**

| Work | Fixed study | Extra native correctness |
|---|---:|---:|
| Full-network fits |4|0|
| Complete H256 episodes |2,656 =1,024 acquisition +1,632 final|5 partial H8 trajectories|
| Native team steps / UAV ticks |679,936 /3,399,680|40 /200|
| C_N labels |327,680|0 (fixture actions are not fitting data)|
| Adam updates / presentations |32,000 /16,384,000|0 /0|
| Worker student requests |593,920, including163,840 greedy acquisition|0|
| Worker C requests |419,840|50|
| Worker helper request ceiling |757,760|50|
| Worker no-memo C paths / ticks |11,335,680 /45,342,720|1,350 /5,400|
| Reader student forwards |430,080|0|
| Reader C rankings / helper calls |80 /80 total over the study's saved rows|0 additional|

Study episode counts by N3..N7 are256/544/1056/544/256. Native dense
slot accounting is `N*(50+N)` per channel evaluation, preserving its
historical meaning (not claiming every slot has nonzero physical work).
With one constructor per N, explicit native reset and one layout refresh
per episode, the study costs189,253,673 dense slots; the H8 fixture adds
13,850, for189,267,523 combined. Study no-memo C/helper link ceilings are
951,705,600/109,854,720; the fixture adds113,400/7,400. Worker combined
dense/C/helper ceiling is1,250,948,643 slots. The balanced80-row reader
adds at most192,000 C/helper links under20-user support, with no native
channel calls. Record actual cache misses, geometry and link work alongside
these ceilings. Labels/team steps/UAV steps/updates match F/M; actual CPU
does not necessarily match because N and visited geometry differ.

The selected planning estimate remains15–30 worker CPU minutes plus10–30
reader CPU minutes, roughly1–3GB unique bulk and sequential RAM plausibly
below1GiB, before actual admission. The small fixture is included in this
runtime allowance, not hidden in the original native-step total. Support
remains8–14 unmetered hours, not a promise or a cap on reading required
evidence. Those estimates are source-based, not a new benchmark. The
preceding acquired/developed lineages have already cost8 fits,2 calibrations,
1,687,552 native steps and2,343.116291 chain CPU-s over their scoped hosts,
plus the separate older B01 two-fit576,000-step/31,190.348CPU-s investment.
B06 would bring acquisition+B04+B05+B06 to12 fits/2 calibrations and
2,367,488 study steps (2,367,528 including its native fixture), without
pooling heterogeneous host timings or erasing earlier adverse outcomes.

Root prospectively assigns local_linux, untimed CPU/one thread while the
real-deadline waiting chain occupies the preferred remote. Fresh actual-node
memory/occupancy admission, current owner-pause/lead and published exact
inputs still govern execution. Any N8/parent overlap is reported with actual
timing scope. Existing accepted operations and their observation handles
are untouched. This fixes one producer/full-reader chain, not an automatic
second attempt or future collection.


<a id="b06-count-development-l0"></a>
### B06 implementation scope

Deliver one fixed count-development runner and bounded complete reader under
`experiments/candidates/uav_fleet_adaptation/b06_count_development/`, mirrored
by focused tests under `tests/experiments/candidates/uav_fleet_adaptation/b06_count_development/`.
New entrypoints are the direction-local runner/reader; source identities,
original S byte/tensor hashes and B* provenance remain explicit. Outputs go
to `runs/uav_fleet_adaptation/b06_count_development_a01/`; disposable inputs
and observer requests stay under `temp/directions/uav_fleet_adaptation/`.
I own NOTES, protocol, integration, acceptance, launch, reading and publication.
No frozen source or shared core file is owned by this task.

One bounded Implementer may own only the new count-conditioned full-network
continuation kernel (`model.py`) and its focused `test_model.py`: same original
network keys plus zero128 count branch, fresh continuing Adam, exact phased
row-uniform CE and checkpoint/gradient/movement accounting. Pass the fixed
protocol/parent-state interfaces; it uses synthetic weights/data, no real S
forward, native query, production fit, Git index operation or result launch.
I implement the count-aware controllers, addressed native initializer,
collection, orchestration and bounded reader in disjoint new files, then
read/accept the returned diff and checks. Helpers do not edit the notebook
or each other's files. There is at most one active Implementer.

Focused checks cover N5 source-C/helper equivalence; count-dependent unknown
interference and packed rows at N3..N7; zero-branch initial computation and
F/M gradients; fixed data/update/order arithmetic; label versus greedy
roll-in and sampled-final separation; independent addressing/tapes; layout
refresh/pairing; cache invalidation; complete raw reconstruction, row/label
corruption rejection and clustered estimands. Synthetic tests must not
quietly consume a result asset/endpoint or run native quality pilots.
Independent high-risk engineering review receives this contract, source
diff and tests. I resolve findings and publish exact inputs before one
admitted worker and its fixed reader. Engineering correctness is separate
from the already completed scientific selection review and the later
independent result interpretation. A material premise contradiction returns
promptly to Root; implementation errors preserve accepted exposure before
any revised proposal. No new CLAIM is needed for this exploratory study.

**Bounded implementation acceptance and next scope.** I read the new model and
its focused synthetic tests and accept the kernel handoff:14 tests pass in
1.95s, including independent CE/order arithmetic, N5 zero count gradients,
checkpoint continuity and failed-attempt accounting. No original-asset
forward, native query or production fit was used. Partial attempted forwards
are charged separately from known completed updates on a failure.

The same sole Implementer may next own only `audit.py` and `test_audit.py`
inside the new B06 source/test directories. Deliver the pure saved-array
checker used by the fixed reader and the already charged native fixture:
N-shaped native reward/connection/motion/terminal reconstruction, local
observation encoding from saved matrices, features/navigation/held commands,
saved C label/score consistency and stochastic-address law. No native or
radio/controller/neural/optimizer call belongs in this checker; the DM-owned
reader performs only the separately priced430080 final forwards and80
C/helper spot checks. It must state that saved matrices are not new radio
replay and that unqueried final helper fallback bits are source/trace checks.
Use artificial arrays and mutation rejection tests. All other files, models,
notebook/index and launch remain mine; no concurrent Implementer is added.

**Prospective placement update,22:11 UTC.** Root reports the waiting producer
and full reader terminal on wsl_4070, with no further heavy work selected there.
B06 has no accepted operation, so the earlier conditional local placement
no longer applies. I will use the owner's preferred wsl_4070 subject to fresh
actual-node admission, with its configured Python3.10.21/NumPy1.26.3/
Torch2.7 CPU execution and one thread. Both original S assets are already in
their canonical remote paths and will be bound directly, without local
weight duplicates. Same-host worker/reader arithmetic is checked; local
synthetic tests do not promise cross-host bitwise equality. Local accepted
N8/parent operations remain untouched. Counts, contract and output identity
are unchanged; actual source/runtime/occupancy are recorded at acceptance.

**Integrated prelaunch acceptance.** I read and accept the second bounded
Implementer handoff (`audit.py` and its tests): it independently reconstructs
assignment, reward, observation packing, motion, navigation, supplied-score
ranking, memo accounting and private draws from saved arrays. Its73 synthetic
checks passed; the integrated B06 suite, including emitted collector files
against that auditor, now passes110 checks in3.61s. These are artificial
weights/arrays, not original S forwards, native quality pilots or result fits.
The full new executable change is with the independent Engineering Reviewer.

The saved-array reading also explicitly counts work that is neither a radio
query nor a learned-policy forward: all2,661 assignment histories and all
observation rows, plus27 clipped four-tick geometric paths whenever a supplied
C/teacher ranking uses fallback. Across the full reader this is at most419,890
fallback rankings/11,337,030 geometric paths/45,348,120 geometric ticks, with
actual counts saved. The immediate worker reading of its five H8 fixture files
adds at most50 such rankings/1,350 paths/5,400 ticks; its saved-array check
records are retained and compared by the final reader. These checks belong
to the already declared full label/hold/native reconstruction and runtime
estimate. They add no native trajectory, C score/helper/radio query, optimizer
step or neural replay beyond the published plan. The planned80 numerical
C/helper contexts remain separately charged. On a failed optimizer attempt,
raw partial actor/Adam state is retained even if unequal per-parameter steps
prevent it from satisfying the normal complete-checkpoint contract.

**Independent engineering disposition,22:36 UTC.** The registered Reviewer
read the entire new executable change against the fixed contract and ran the
110-test suite independently (3.35s). Two medium findings concerned failure
preservation: the reader previously reserved its once-only attempt too late,
and completed-row cost totals omitted a failed episode's already-paid prefix.
The reader now exclusively creates an INCOMPLETE record before any replay;
a hard interruption or concurrent caller cannot silently repeat it. Failure
costs include the in-flight policy/teacher/helper counters once and explicitly
leave interrupted-call internals unmeasured. The four focused regressions
passed independently in1.17s; my broader touched-file checks passed27 tests
in1.62s. The Reviewer reports no remaining material finding after the repairs.
I accept the implementation. Review was synthetic/source-only, with no real
asset forward, native episode, production fit or complete production reader.
This is engineering acceptance, not empirical validation of the conjecture.

<a id="b06-a01-zero-exposure-failure"></a>
**A01 accepted-input failure and bounded repair,22:44 UTC.** The first remote
operation used source `50bc15328174d79b290fe00fee47ea8596b2fa6a` and was admitted
at22:40:57.683594 UTC, then exited1 at22:40:59.993821 UTC. Its
[native manifest](../../../../runs/uav_fleet_adaptation/b06_count_development_a01/launch-manifest.json)
and [complete failed summary](../../../../runs/uav_fleet_adaptation/b06_count_development_a01/summary.json)
are retained. Source verification completed, but the calibration-reading
existence check failed before loading S or constructing an environment.
All native calls/steps, actor/controller queries, labels, fits, updates and
reader replay were zero. Worker import/check scope cost2.009999 wall-s/
1.286401 CPU-s, whole-process peak381256KiB. Native status is consistent,
with both runner and supervisor absent. This is missing execution evidence,
not an adverse count-development outcome.

Direct inspection of the original snapshot reproduced the cause: the tracked
B04 `reading.json` has Git's skip-worktree flag `S` and no filesystem copy
under the inherited remote sparse selection. The committed blob is present
after explicit retrieval and matches the original879195 bytes/SHA-256
`93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50`.
No accepted source file or sparse selection was changed. The canonical remote
control file received only this direction's published row; lead/pause/state
were already equal. Both original remote S byte hashes were checked unchanged.
The older remote automatic-GC bad-tree warning remains separate from this
verified missing-file cause; no GC repair or control change is being inferred.

L0 for the narrow repair: in B06 `assets.py`, verify the exact B04 evidence
commit's calibration-reading Git blob, hash and two recorded winners;
producer and reader both use that binding instead of assuming the committed
file is materialized by a sparse checkout. The immutable input and calibration
choices stay identical. A managed synthetic Git fixture checks omitted working
files, dirty copies, changed bytes and changed winner metadata; the registered
Engineering Reviewer checks this repair. No new native/actor/optimizer test
is needed. Publish the repair and failed records before a separately declared
fresh A02 attempt at its new source; it uses the original fixed seeds/exposure
and adds no scientific work beyond the selected plan because A01 consumed none.
Do not treat the launcher's same-source retry eligibility as authorization or
edit/restart the accepted A01 operation. The complete study remains unexecuted.

A01 deterministic observation adopted the same terminal handle at generation26;
event `0638a19766bb6917b6c5a361` was drained/rearmed and the observer stopped.
Native-child queue delivery returned the known `-32600`; this active child
read the terminal facts directly. All original compact output files were
collected without running the priced production reader.

**Repair acceptance and A02 prospective declaration,22:49 UTC.** The independent
Reviewer reports no material finding in this narrow binding repair and verified
the original879195-byte blob. Its5 managed synthetic checks passed in1.21s
(mine:1.27s). `git show` can lazily fetch a missing promisor object; the timeout
is not an offline guarantee. I explicitly retrieved the required blob in the
remote common object store before this decision, without materializing it in
or changing the accepted A01 snapshot. The same pinned input is now available
to the next snapshot and is hash-checked by both producer and reader. The two
small Git verification children are outside Python's process-CPU counters;
their wait is included in wall time, and their CPU remains unmetered support.

I accept this outcome-blind input repair and declare
`runs/uav_fleet_adaptation/b06_count_development_a02/` as the fresh attempt
after its exact source and A01 evidence are published. It executes the same
five native correctness fixtures, four fits,2,656 study episodes and bounded
reader, at the original addresses; A01 has consumed none of them. No new
comparator, fit, calibration, pilot or verification query is added. Admission
must again verify current pause/lead, published new source and actual remote
memory. Preserve the stopped A01 handle and all failed records; do not use
the old snapshot or same-source retry option for this changed implementation.
This repair leaves both the conjecture and independent scientific selection
advice unchanged. The next scientific boundary remains the complete read result
or a material obstruction, not launch acceptance.

<a id="b06-a02-operation"></a>
**A02 acceptance,22:50:49 UTC.** The repaired published input is
`f529ba39906ec8f86f267d335be5d4346eec9771`; the
[native manifest](../../../../runs/uav_fleet_adaptation/b06_count_development_a02/launch-manifest.json)
binds the one accepted producer/full-reader chain and its stable operation.
Fresh wsl_4070 preflight passed with14,669,373,440 physical/effective available
bytes against the4GiB floor; no active heavy process was observed immediately
before launch. CPU/one thread and canonical original assets are unchanged.
The prior A01 remains terminal and scientifically empty.

The same child-owned deterministic controller adopted the live A02 runner and
supervisor at generation29, with no event yet. It observes the manifest's
handle every30s; the native child remains active through complete reading.
The five H8 native fixtures and their saved-array checks passed, and F0's
first2,400 optimizer updates completed before phase1 acquisition. This is
execution progress only: no final panel or count-development conclusion has
been read. All later terminal collection, review and publication remain owed.

<a id="b06-complete-reading"></a>
### B06 complete reading — active count-diverse learning, uncertain increment over ordinary continuation

**Technical boundary and evidence.** The one A02 producer/fixed-reader chain from
published source `f529ba39906ec8f86f267d335be5d4346eec9771` finished successfully
at23:07:11.424650 UTC on2026-09-30. The worker and full priced reader are complete;
none was restarted or rerun. [Original complete reading](../../../../runs/uav_fleet_adaptation/b06_count_development_a02/reading.json)
is `VERIFIED`,5,388,192 bytes, SHA-256
`3ca895a0f6a5ea6bd4ec35c239e3dde9a78302ccc134efdbacdbf2f5b82e8af9`.
The [native manifest](../../../../runs/uav_fleet_adaptation/b06_count_development_a02/launch-manifest.json),
[terminal status](../../../../runs/uav_fleet_adaptation/b06_count_development_a02/native-status.json)
and [exit record](../../../../runs/uav_fleet_adaptation/b06_count_development_a02/process-exit.json)
bind source, host and successful operation. Both accepted native process identities
were absent with a consistent exit0 record. All nine collected original files matched
the remote byte hashes; native-status.json is an additional terminal observation.
The separate A01 input failure remains recorded above with zero scientific exposure.

The deterministic observer returned a READY event at generation29:
`84d5a4562d03f28a9701de5b`, wake `3af1e9e3-0754-47f4-921e-1ae5d090616d`.
Its event was drained, rearmed to30 and stopped. The native-child queue again
returned `-32600`; the active same child received completion through the foreground
deterministic observer. Later interruption during interpretation did not restart
any operation; the same DM and original independent Critic resumed their unfinished
reading. Technical completion alone was not treated as the scientific boundary.

**Question and conditioning.** F is ordinary further N5 teacher imitation; M is
balanced N3/N7-episode imitation, with the same reliable count input, initialized
network, labels and optimizer exposure. P reuses the original S parameters under
the revised count-aware controller/helper interface. B*0 retains the already-paid
temperature2 choice, and B*1 is exactly P1 by program identity. C/Q use the same
count rights. No new calibration was selected. The fixed primary effect averages
N4/N6 and both inherited-lineage blocks equally after averaging the two private
tapes within each of32 world clusters. Counts, tapes, agents and training rows
are not additional independent world or training replications. All intervals below
are conditional descriptive t95 intervals over those32 worlds, not confirmation,
training-population inference or an equivalence test. N5 is retained separately.

The current published background was re-read at `bd9bd7cd1aa592df02c9d3b635440766e21f2100`,
[topic2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练) and
[topic4](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面).
Its distinction between parameter reuse, active fitting and complete native value
remains load-bearing. The revised interface means this cannot be called unchanged
S package portability. Earlier PPO/CAL/CONT losses and B20's distinct Gaussian
count results are contrary evidence, not pooled experiments or a diagnosed common
cause. The present record tests the selected finite development package directly.

**Fixed primary and lineage targets.**

| Contrast / metric | Mean and world t95 | Positive / negative / tied worlds |
|---|---:|---:|
| M−F target, J | +0.005574 [-0.000643,+0.011791] | 18/14/0 |
| M−F target, mean_served | +0.276520 [-0.187345,+0.740384] | 17/15/0 |
| M−F target, service_p10 | +0.318359 [-0.233789,+0.870508] | 14/17/1 |
| M−F target, min_served | -0.082031 [-0.303588,+0.139526] | 15/14/3 |
| M−F target, mean_sinr_quality | +0.005675 [+0.002637,+0.008713] | 23/9/0 |
| M−F target, mean_path_length_m | +919.854876 [+739.506585,+1100.203167] | 31/1/0 |
| L0 M−F N4/N6, J | +0.001897 [-0.006365,+0.010159] | 16/16/0 |
| L0 M−F N4/N6, mean_served | +0.023804 [-0.584005,+0.631613] | 15/17/0 |
| L0 M−F N4/N6, service_p10 | +0.109375 [-0.771662,+0.990412] | 14/18/0 |
| L0 M−F N4/N6, mean_path_length_m | +951.320281 [+654.131049,+1248.509513] | 27/5/0 |
| L1 M−F N4/N6, J | +0.009250 [+0.000585,+0.017915] | 19/13/0 |
| L1 M−F N4/N6, mean_served | +0.529236 [-0.106186,+1.164657] | 20/12/0 |
| L1 M−F N4/N6, service_p10 | +0.527344 [+0.008835,+1.045853] | 21/11/0 |
| L1 M−F N4/N6, mean_path_length_m | +888.389470 [+607.436757,+1169.342183] | 29/3/0 |

The primary J point is positive but its interval spans zero; service and p10 remain
uncertain and the mean episode minimum does not improve. L1 has a positive
conditional target J interval and p10 signal; preserve that result rather than
calling both lineages negative. M travels substantially farther than F in31/32
primary world averages. The objective arithmetic is coverage +.003871277 and
quality +.001702450, summing to J +.005573727; this decomposition is not a causal
mediation analysis. No movement-energy utility is modeled here.

**Every count/lineage comparison.** J intervals, service/p10 point differences and
mean path differences are within-count, with identical world/tape matching.

| Lineage,N | M−F J [t95] | M−F service / p10 | M−F path m/UAV | M−P J [t95] | M−P service / path m/UAV |
|---|---:|---:|---:|---:|---:|
| L0,N4 | +0.010093 [-0.005632,+0.025818] | +0.510803 / +0.187500 | +1355.554 | +0.002340 [-0.010490,+0.015170] | -0.002869 / +1218.985 |
| L0,N5 | +0.005418 [-0.008014,+0.018850] | +0.282959 / +0.242188 | +1133.493 | -0.005071 [-0.018207,+0.008065] | -0.484436 / +847.088 |
| L0,N6 | -0.006299 [-0.016938,+0.004340] | -0.463196 / +0.031250 | +547.086 | -0.004384 [-0.013997,+0.005229] | -0.375793 / +237.661 |
| L1,N4 | +0.008562 [-0.000994,+0.018119] | +0.458496 / +0.359375 | +1111.631 | -0.003946 [-0.017817,+0.009924] | -0.422546 / +740.140 |
| L1,N5 | +0.009601 [-0.002897,+0.022100] | +0.653137 / +0.351562 | +591.282 | -0.002234 [-0.013681,+0.009214] | -0.281311 / +386.711 |
| L1,N6 | +0.009939 [-0.001793,+0.021670] | +0.599976 / +0.695312 | +665.148 | -0.001929 [-0.012841,+0.008984] | -0.207825 / +140.396 |

Each of the six individual M−F J intervals crosses zero; the L0/N6 point is
negative. Every M−P J interval also crosses zero. M−P mean service is nonpositive
in all six cells, and mean path is higher in all six. This does not establish a
useful incremental native capability over the retained P. F−P J points are
−.007753/−.010489/+.001915 for L0,N4/5/6 and
−.012508/−.011835/−.011867 for L1; the latter N5 and N6 intervals are strictly
negative. F travels less than P in all cells. M's advantage over F is therefore
consistent with attenuating an ordinary continuation loss; the paired comparison
does not identify the cause of that attenuation.

M−B*0 J is−.011163[−.025819,+.003492] atN4,
−.013205[−.024104,−.002306] atN5, and−.001059[−.011466,+.009348] atN6.
B*0−P0 J is+.013503/+.008134/−.003325, all intervals crossing zero, with
+1019.196/+1481.825/+1665.584m/UAV. B*1=P1 is reused by identity, not evaluated
again. No retrospective temperature upgrade follows.

**Retained complete native capability and absolute scale.** All native means below
first average private tapes within a world. C/Q are shared within a count; repeated
C/Q rows are intentionally omitted. B*1's equal P1 row is also omitted.

| Program | N | J | Service/step | Episode p10 | Episode minimum | SINR quality | Path m/UAV | Decision CPU s / whole-episode CPU s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C | 4 | 0.367287 | 21.963623 | 21.640625 | 13.031250 | 0.199320 | 2504.676 | 0.013399 / 0.143151 |
| Q | 4 | 0.388338 | 23.491272 | 20.187500 | 11.781250 | 0.198200 | 4022.270 | 0.066158 / 0.206689 |
| P0 | 4 | 0.405882 | 24.803528 | 22.250000 | 12.859375 | 0.195443 | 2201.324 | 0.060985 / 0.198370 |
| F0 | 4 | 0.398129 | 24.289856 | 22.023438 | 12.640625 | 0.193569 | 2064.754 | 0.055210 / 0.190428 |
| M0 | 4 | 0.408222 | 24.800659 | 22.210938 | 12.796875 | 0.203377 | 3420.308 | 0.069336 / 0.207894 |
| Bstar0 | 4 | 0.419386 | 25.832458 | 22.218750 | 12.390625 | 0.192437 | 3220.520 | 0.092135 / 0.234309 |
| C | 5 | 0.348957 | 20.827759 | 20.187500 | 11.593750 | 0.191229 | 2519.627 | 0.018169 / 0.162588 |
| Q | 5 | 0.359352 | 21.635071 | 17.703125 | 10.109375 | 0.188205 | 4119.363 | 0.088140 / 0.245464 |
| P0 | 5 | 0.382096 | 23.417664 | 20.523438 | 11.015625 | 0.180830 | 2918.984 | 0.101114 / 0.256850 |
| F0 | 5 | 0.371607 | 22.650269 | 20.023438 | 10.906250 | 0.181678 | 2632.579 | 0.087165 / 0.240847 |
| M0 | 5 | 0.377025 | 22.933228 | 20.265625 | 11.156250 | 0.186533 | 3766.072 | 0.104572 / 0.261796 |
| Bstar0 | 5 | 0.390230 | 24.083069 | 20.117188 | 10.421875 | 0.176891 | 4400.809 | 0.150619 / 0.313473 |
| C | 6 | 0.322519 | 19.198975 | 17.984375 | 8.937500 | 0.179112 | 2481.657 | 0.025489 / 0.185300 |
| Q | 6 | 0.328142 | 19.724243 | 15.476562 | 7.953125 | 0.173341 | 4296.427 | 0.111488 / 0.287489 |
| P0 | 6 | 0.350412 | 21.488098 | 17.804688 | 8.781250 | 0.165263 | 3695.687 | 0.159422 / 0.336309 |
| F0 | 6 | 0.352328 | 21.575500 | 17.945312 | 8.812500 | 0.167569 | 3386.263 | 0.138370 / 0.312730 |
| M0 | 6 | 0.346028 | 21.112305 | 17.976562 | 8.812500 | 0.168187 | 3933.349 | 0.143033 / 0.317779 |
| Bstar0 | 6 | 0.347087 | 21.332336 | 16.437500 | 7.906250 | 0.161449 | 5361.272 | 0.193257 / 0.374336 |
| P1 | 4 | 0.409502 | 25.135742 | 22.890625 | 13.125000 | 0.192004 | 2198.411 | 0.060858 / 0.196812 |
| F1 | 4 | 0.396993 | 24.254700 | 22.421875 | 13.265625 | 0.191425 | 1826.920 | 0.053504 / 0.188666 |
| M1 | 4 | 0.405555 | 24.713196 | 22.781250 | 12.625000 | 0.198569 | 2938.551 | 0.069278 / 0.208740 |
| P1 | 5 | 0.387610 | 23.799683 | 20.757812 | 11.500000 | 0.181383 | 2948.432 | 0.104706 / 0.261976 |
| F1 | 5 | 0.375775 | 22.865234 | 20.429688 | 11.453125 | 0.185539 | 2743.861 | 0.094338 / 0.251078 |
| M1 | 5 | 0.385377 | 23.518372 | 20.781250 | 11.093750 | 0.187064 | 3335.142 | 0.106742 / 0.264103 |
| P1 | 6 | 0.352801 | 21.578491 | 18.226562 | 8.796875 | 0.169007 | 3827.617 | 0.160431 / 0.336895 |
| F1 | 6 | 0.340934 | 20.770691 | 17.492188 | 8.750000 | 0.167146 | 3302.865 | 0.142910 / 0.316638 |
| M1 | 6 | 0.350872 | 21.370667 | 18.187500 | 8.906250 | 0.172276 | 3968.014 | 0.150582 / 0.326624 |

P−Q J is+.017545/+.022744/+.022271 for L0,N4/5/6 and
+.021164/+.028258/+.024659 for L1, with every conditional interval strictly
positive. Its mean service increments are1.312256/1.782593/1.763855 and
1.644470/2.164612/1.854248; episode p10 increments are2.0625/2.820313/2.328125
and2.703125/3.054688/2.75. P also travels1820.946/1200.379/600.740 and
1823.860/1170.931/468.810m/UAV less than Q. All six M−Q and M−C J intervals
are also positive. Thus development has not erased learned competence, but the
retained P already supplies the useful increment beyond these ordinary references.
No cross-count pooling ranks N: native J falls as N4→N5→N6 for all programs on
these shared layouts, because more transmitters alter interference and capacity
together. This is not a causal decomposition or proof that extra fleet capacity
is universally harmful. CPU is actual cached CPU/one-thread work on wsl_4070,
not a deadline experiment or a comparison to earlier differently threaded hosts.

**Adverse and favorable worlds.** No final evaluation trajectory among1,632 has
a zero-total-service tick. This does not erase the B02–B05 zero-service outcomes
or establish individual-user continuity. Acquisition has17 zero-service ticks
(F0,N5:6;F1,N5:2;M0,N3:7;M0,N7:1;M1,N3:0;M1,N7:1), retained with its own
training semantics. Large final losses remain despite the absence of total outage.

| Lineage,N | Worst M−F J world | J / service / p10 difference | Best M−F J world | J / service / p10 difference |
|---|---:|---:|---:|---:|
| L0,N4 | 29515003 | -0.088373 / -5.912109 / -8.250000 | 29515010 | +0.143728 / +9.224609 / +12.000000 |
| L0,N5 | 29515018 | -0.073431 / -5.773438 / -4.250000 | 29515020 | +0.107921 / +8.267578 / +5.500000 |
| L0,N6 | 29515014 | -0.066803 / -4.482422 / -4.250000 | 29515026 | +0.046710 / +3.439453 / +6.500000 |
| L1,N4 | 29515005 | -0.040024 / -2.953125 / -3.250000 | 29515017 | +0.067746 / +4.828125 / +2.250000 |
| L1,N5 | 29515017 | -0.060867 / -4.160156 / -4.750000 | 29515019 | +0.084273 / +6.748047 / +3.000000 |
| L1,N6 | 29515009 | -0.045257 / -3.748047 / -5.250000 | 29515021 | +0.093193 / +6.314453 / +6.500000 |

L0/N5 world29515009 loses7.25p10 users under M−F even though another world
has the largest J loss. L1/N4 world29515010 loses.142737J and10.085938
service/step under M−P; its positive29515026 witness gains.061666J and
4.259766 service. P−Q is not per-world dominance: L1/N4 world29515014
loses.058418J/3.556641service/6.25p10, and L0/N5 world29515014 loses
.056345J/3.861328service/1.5p10. All full paired vectors and identities remain
in the original reading, rather than retaining only these selected illustrations.

**Learning and representation exposure.** All four full-network fits completed
8,000 Adam updates and4,096,000 sample presentations apiece. Every ordinary
network update had nonzero gradients. F's count gradients/weight/Adam moments
remain zero by its N5 input; M's count gradient is nonzero on every one of its
8,000 updates in both lineages. Initial lifted weights are identical within a
lineage, and the saved original/state/checkpoint bindings all verify. Final full
network L2 movement and count-branch movement are:

| Fit | Full-network L2 / changed of34,843 | Count L2 / changed of128 | Distinct combined feature rows of81,920 | Last paid-stream CE / accuracy | Complete-fit CPU s |
|---|---:|---:|---:|---:|---:|
| F0 | 25.983034 / 27774 | 0.000000 / 0 | 9238 | 0.243070 / 0.947974 | 68.910648 |
| M0 | 26.365262 / 28306 | 0.609702 / 126 | 10605 | 0.219724 / 0.948364 | 66.712726 |
| F1 | 24.981893 / 24184 | 0.000000 / 0 | 8820 | 0.251375 / 0.941064 | 65.757986 |
| M1 | 26.678119 / 27443 | 0.714381 / 128 | 10723 | 0.259637 / 0.934778 | 66.857192 |

All12 phase training-stream cross entropies fall from first to last epoch. These
are losses/accuracies at the changing models during paid optimizer forwards,
not fixed-endpoint validation. Repeated held decisions remain fitting rows;
the distinct-row counts are not independent supervision counts. F has81,920 N5
rows, while M has24,576 N3 and57,344 N7 rows: episode balance is30/70 row
balance. Source/fit/label/shuffle identities and all280 epoch records are retained;
there is no no-learning escape for this result.

The exposure limits the representation conclusion sharply: **all acquisition,
evaluation and fixture visible-peer histograms stop at2 peers**, including N7.
No previously unused high-index peer slot was exercised; all final decisions
with more than4 visible peers count zero. Acquisition histograms (0/1/2 peers)
are F0,N5:66238/15626/56;M0,N3:17291/5966/1319;
M0,N7:46951/10356/37;F1,N5:69634/12206/80;
M1,N3:17968/5799/809;M1,N7:47908/9390/46.
N3 can expose its complete two-peer roster; N7 remains locally sparse.
This is actual static-count/interference/capacity interpolation with a scalar
count branch, not crowded roster stress or evidence for invariant representation.
The fixed fixtures also checked layout and interface mechanics, not a dense-roster
quality pilot. Whether different completeness exposure, count weights, supervised
data or altered visitation explains the small M−F increment remains unresolved.

Own-history final entropy for P/F/M is respectively
L0,N4:.307690/.230270/.312955;N5:.426474/.301814/.354046;
N6:.547168/.384218/.373528;L1,N4:.304166/.203663/.336496;
N5:.433777/.328151/.391173;N6:.567050/.422408/.444426.
F entropy is lower than P everywhere, but M is higher atN4 and lower atN5/N6.
M has fewer zero-displacement UAV ticks and longer paths than F/P in every cell.
These are descriptive own-history changes, not same-history physical shadows
or a common identified entropy failure. No additional actor shadows were bought.

**Exposure and complete cost.** The selected1,024 acquisition episodes contribute
262,144 native steps and327,680 C_N labels;1,632 final episodes contribute
417,792 steps. Five separately priced H8 fixtures add40 steps, for2,661 saved
trajectories/679,976 native calls/3,399,880 UAV ticks. Four fits consume32,000
updates and16,384,000 presentations. Five constructors and2,661 explicit resets
and refreshes are charged; native dense power slots total189,267,523.
There are zero new calibrations, early-stopping selections or extra final fits.

Worker C receives419,890 requests (331,767 cache hits/88,123 misses), computing
2,379,321 paths/9,517,284 model ticks,35,188,776 candidate and363,010 setup
links. Helper work is289,738 actual calls/1,278,500 setup/2,366,124 extreme
links. There are593,920 student requests and268,864 actual uncached neural rows.
The491,520 sampled-draw counter includes61,440 Q draws plus430,080 final
student-family draws; it is not491,520 neural queries. C's sampled_draws field
records those same Q draws, not an additional61,440 draws. Total controller
power links39,196,410 plus native links gives228,463,933.

The already-completed bounded reader reads all2,661 raw files/873,616,739 bytes,
679,976 saved ticks/3,399,880 agent ticks,849,970 decision rows,
3,413,185 observation rows and682,637 assignment matrices. Pure fallback
geometry includes33,104 rankings/893,808 paths/3,575,232 ticks. It executes the
fixed430,080 final student forwards and80 C plus80 helper contexts, charging
2,160 C paths/8,640 model ticks/37,198 C links and1,052 helper links. It runs
zero native steps or optimizer updates and no extra acquisition actor, complete
teacher or radio-physics replay. The worker's immediate pure fixture audit also
has25 fallback rankings/675 paths/2,700 model ticks; the reader's fixture checks
are separately charged. Saved algebra, sparse C/helper reconstruction and full
final actor reconstruction are distinct levels of verification.

Worker wall/CPU is695.392740/693.615286 seconds, peak706,140KiB;
reader284.704350/284.663623 seconds. Enclosing entry-through-reader chain is
980.482682 wall/978.664369 CPU seconds, including import/serialization gaps.
Process peak866,444KiB includes producer and reader; it is not an incremental
reader memory claim. Git blob-verification child CPU, admission, publication,
independent review and engineering/support labor remain outside those process
CPU timers. Acquisition-row CPU is189.178074, evaluation-row421.236186 and
fixture-row.061945; phase optimizer CPU totals76.399310. These disjoint partial
instruments do not replace the enclosing chain measurement.

The failed A01 additionally cost1.286401 main-process CPU seconds/2.009999 wall
with no scientific exposure. Acquisition B02/B03 through B06 now totals12 fits
and2 paid calibrations,2,367,528 native steps and3,321.780660 measured successful
chain CPU seconds across the stated hosts/scopes; including B06 A01 makes
3,323.067061 seconds. Older B01 remains separately incurred:2 fits/576,000
steps/31,190.348 CPU seconds plus its recorded technical attempt. No support cost
is silently reset or called zero. The prospective25–60 CPU-minute estimate was
higher than this observed16.311-minute successful chain; no exact support-hour
measurement was made against the prospective8–14 support-hour bill.

**Required durable artifacts.** One canonical bulk copy remains at
`wsl_4070:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b06_count_development_a02/`.
Its original `summary.json` is12,774,199 bytes/SHA-256
`0d1fc9af270a376f3836fe256cee93c31bc698ae9cd131339d80960ee92d4073`;
raw2,661 files total873,616,739 bytes. Each trajectory's path, byte count and
hash is in that summary; all final/fixture hashes and required learner bindings
are also in the published complete reading. Twelve phase datasets total2,613,751
compressed bytes and12 checkpoints total5,168,100 bytes; they remain required
for the recorded full fit/source identities, original reader and independent
reconstruction. The four endpoint file identities are:

| Endpoint | Relative path in canonical run | Bytes | SHA-256 |
|---|---|---:|---|
| F0 | `assets/F0_phase2.pt` | 430675 | `8cd5082bda9f466f06f7eac41024aadbd8376c00c8d715af9f1f04a4d596e9d0` |
| M0 | `assets/M0_phase2.pt` | 430675 | `2fafc6e729f948a7e679014b356072b41fdc1725ac8e37aa59f72bc09a01097e` |
| F1 | `assets/F1_phase2.pt` | 430675 | `8b755ec4aa983d86d061a928dc2b6ad58844ac9f9809bc64e58b11d55c3ca54d` |
| M1 | `assets/M1_phase2.pt` | 430675 | `10d2b515ba789c1990c716d3bbb603e37f240930c2d203e2bcf6f02aab260a1a` |

The original B02/B03 S files remain immutable in their canonical remote runs;
the lifted initials and original states are pinned in `initial_assets` and each
fit. The local full summary is a temporary verified review copy; after the
original Critic has finished, remove that duplicate while retaining its canonical
remote bytes and the complete aggregate/per-world reading in Git. No raw tree or
checkpoint tree was copied locally. Actual retirement, absence checks and net
allocated-byte decrease are reported in the final-cleanup entry below.

**Working explanation before the final independent recommendation.** The selected
primary count-development claim is not established; L1's conditional positive
and the native learned capability beyond C/Q remain real evidence. Active mixed
training mainly looks less damaging than active N5 continuation, with more
travel and no established P/B* increment. That reading weakens this fixed
count-mixture purchase while leaving the enduring development question open.
Sparse peer exposure, differing imitation/visitation, loss/decoder effects and
finite training could explain parts, but none has been identified causally.
No extra fit, architecture change, count-feature ablation or denser-roster run
follows automatically. The original separate-context scientific recommendation
and resolved disposition are recorded next; a broad family closure is not inferred.


<a id="b06-independent-disposition"></a>
### B06 independent diagnosis and resolved disposition

The original registered `hmasd-research-critic` ran in a separate context without
DM/Root conversation inheritance. Its original evidence-first reconstruction
preceded reading the prior count-selection advice. The same reviewer resumed
after the reading interruption; it was not replaced and no duplicate review was
commissioned. Its complete answer follows, preserving favorable evidence,
alternative explanation and stopping scope.

> **Recommend stopping this exact B06 mixture recipe and retaining P/Bstar as conditional capabilities.** B06 establishes active full-network development and a small, heterogeneous advantage of mixed-count continuation over ordinary continuation. It does **not** establish useful added interpolation value over inherited reuse. This ends the tested recipe, not the broader question of developing competent native policies.
>
> This was a separate-context review. I reconstructed the protocol, source bindings and saved results before reading the earlier count-selection recommendation. The DM’s later message about sparse peer visibility confirmed a fact I had already computed.
>
> The primary equal-N4/N6, equal-lineage M−F effect is **+0.005574 J**, with the declared descriptive world-cluster interval **[−0.000643, +0.011791]**; 18 of 32 world effects are positive. That interval describes these fitted policies on sampled worlds. Two tapes and four fits do not establish training-population reliability.
>
> The decisive comparison is with inherited reuse:
>
> | Lineage | N | M−F J | M−P J | F−P J | M−Bstar J |
> |---|---:|---:|---:|---:|---:|
> | 0 | 4 | +.010093 | +.002340 | −.007753 | −.011163 |
> | 0 | 5 | +.005418 | −.005071 | −.010489 | −.013205 |
> | 0 | 6 | −.006299 | −.004384 | +.001915 | −.001059 |
> | 1 | 4 | +.008562 | −.003946 | −.012508 | −.003946 |
> | 1 | 5 | +.009601 | −.002234 | −.011835 | −.002234 |
> | 1 | 6 | +.009939 | −.001929 | −.011867 | −.001929 |
>
> F loses to P in five of six cells. M recovers some of that loss, but exceeds P in only one cell and falls below Bstar in all six. On the primary target, **M−P is −.001980 J; F−P is −.007553; M−Bstar is −.004524**. The strongest consequential objection to a positive development claim is therefore comparator choice: a positive M−F alone would credit recovery from ordinary continuation’s deterioration.
>
> The useful positive should remain explicit. Both lineage-level interpolation M−F means are positive: **+.001897** and **+.009250**; the latter’s conditional interval is [.000585, .017915]. M also retains higher mean J than C and Q in every count/lineage cell. Yet P already supplies that capability: its primary-target advantage is **+.034746 J over C and +.021410 over Q**, versus M’s +.032766 and +.019430. These results support useful parameter reuse under the revised interface, without proving unchanged-package portability.
>
> The components prevent either blanket dismissal or adoption. Primary M−F gives:
>
> - Mean service **+.277 users**, service-p10 **+.318**, and episode minimum **−.082**; their descriptive intervals span zero.
> - Quality **+.005675**, accompanied by **+920 m/UAV** of travel; travel increases in 31 of 32 world clusters.
> - Against P, M has **−.252 mean service**, approximately unchanged mean p10, **+.005173 quality**, and **+584 m/UAV** travel.
>
> M improves quality relative to P in every count/lineage cell, so it is not uniformly inferior. Conversely, P’s stronger J does not establish dominance on every component. Bstar also carries tail/travel tradeoffs and should not become an automatic temperature replacement. No final episode has zero total service, but adverse minima and individual worlds remain. For example, the independently checked lineage-0 N5 world **29515005** has two-tape M−P **−.075294 J**. Average N5 M−P is negative in both lineages, with service losses and additional travel. No retention-equivalence margin was declared, so neither “retention preserved” nor “equivalent” is supported. Travel is measured motion cost, not a measured energy or safety outcome. [Complete B06 evidence](</home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b06_count_development_a02/reading.json>).
>
> The scientific distinctions are:
>
> - **Opportunity:** changing fleet count changes the actual physical problem. The comparison supplies genuine count variation, matched public-count rights and shared addressed layouts.
> - **Representation:** the scalar count branch was active in both M fits, but every saved acquisition/evaluation/fixture decision had **at most two visible peers**, including N7. Consequently, the proposal’s anticipated exposure of previously unused higher peer slots did not occur. B06 cannot diagnose learning over larger visible peer sets.
> - **Learning:** all four fits completed 8,000 updates. Stream fitting improved, substantial original-network movement occurred, and M’s count-weight norms reached approximately **.610/.714**; F’s stayed zero as intended. This is not absent optimization or whole-intervention nonactivation. Stream accuracy is measured during changing-model training, not an independent frozen-endpoint assessment.
> - **Complete value:** active learning and higher quality did not produce a coherent gain over retained references once service, retention, travel and computation are included.
>
> The strongest simpler explanation is **further imitation changes the useful inherited stochastic behavior, while diverse acquisition attenuates some of ordinary continuation’s damage**. F has lower trajectory-average entropy than P in every cell, more stationary behavior, and usually lower native value. M generally retains more entropy and movement than F. These observations are compatible with changed visitation, finite fitting and decoder behavior; they do not identify entropy as the cause. C is the teacher, yet sampled P already outperforms C on native outcomes, so better reproduction of C’s labels need not improve native value.
>
> A constructive alternative remains plausible: mixed acquisition learns count-relevant behavior that improves quality and some interpolation outcomes. The result supports that possibility narrowly, but does not isolate the scalar branch from acquisition distribution or demonstrate a useful increment over reuse. Neither this study nor the distinct B04/B05 adverses identifies a common optimization, representation or credit-assignment failure.
>
> The fixed outcome branches now resolve the investment choice. Coherent gains over F **and** retained references would have supported further development; improvements by both F/M over P would have supported ordinary continued imitation. The observed pattern instead favors retaining reuse and ending this mixture. **No additional experiment is recommended.** More evaluation episodes would refine conditional precision; unchanged new fits would test recurrence. Neither currently has a sufficiently consequential use or claim to justify automatic purchase. The broader question remains open to a future explicit conjecture or use case; a new architecture, exhaustive diagnosis or positive preliminary test is not required.
>
> The complete new bill matters. A02 used **4 fits, 327,680 labels, 32,000 updates, 16,384,000 presentations and 679,976 native steps**, including the fixtures. Worker CPU was **693.615 s**, reader CPU **284.664 s**, and enclosing-chain CPU/wall **978.664/980.483 s**. The four fit scopes, including acquisition and dataset work, total **269.307 wall-s**; optimizer phases alone account for about **76.399 CPU-s**. Original acquisition, complete evaluation and the reader cannot be omitted from an efficiency account. Cached C remains much cheaper at deployment: its mean episode CPU is approximately **.143/.163/.185 s at N4/N5/N6**, versus M’s approximately **.208/.262–.264/.318–.327 s**. There is no demonstrated learned speed advantage.
>
> A01 separately cost **1.286 CPU-s/2.010 wall-s** and failed before scientific exposure. Through B06, the acquisition/development chain totals **12 fits, two calibrations and 2,367,528 native steps**; earlier costs, including the separate older B01 investment, remain incurred. Admission, final publication, Git children and engineering/review/support are additional incompletely metered work. This study’s measured runtime is not a guarantee for another recipe.
>
> I checked the following directly:
>
> - All **29 source hashes** against pinned `f529ba39906ec8f86f267d335be5d4346eec9771` and local source; consequential initializer, controller, model, decoder and aggregation semantics; configuration and inherited calibration blob.
> - Canonical original-asset byte identities, all **12 checkpoint** and **12 dataset** file hashes, successful process exit and the failed A01 record.
> - All **1,632 final rows**, independently reconstructing **1,680 means/pairwise entries** and the primary clustered vectors.
> - **49 selected raw files**, covering favorable/adverse final cases, N5 retention, acquisition and all fixtures: **11,304 saved ticks and 13,554 decisions**. Checks covered layouts, assignment/reward algebra, motion/holds, feature binding, saved probability laws and addressed draws.
> - Original B02/B03 competence summaries and consequential B04/B05 adverse comparisons and behavioral evidence.
>
> I did not repeat native physics, learned-policy forwards, teacher/helper queries, optimizer replay or the production reader. Beyond the selected raw checks, I rely on the completed reader’s declared coverage; it does not exhaustively replay acquisition actors, teacher arithmetic or Adam. No new scientific execution or record edits occurred.
>
> **MATERIAL_DISSENT: no — the evidence supports the fixed protocol’s reuse/stop branch. I recommend no new B06 investment and no expanded claim of useful count-development benefit.**

**DM response and choice.** I accept the recommendation and preserve the full
independent reasoning. Stop the exact B06 count-mixture continuation recipe; do
not replace either original S/P by M or F, and do not promote B*0 by its exposed
positive cells. P/B* remain conditional capabilities and M's higher quality and
L1 target M−F increment remain positive evidence. The complete package did not
establish added reward/service value over reuse and requires more movement.
“N5 retention” names the evaluated panel, not a demonstrated equivalence result.
The strongest working explanation is partial attenuation of harmful further
imitation, with decoder/visitation effects unresolved; it is not an identified
entropy mechanism. The active scalar branch without larger observed rosters
also narrows the representation story. This result neither refutes broader
count learning nor explains the distinct previous PPO/CAL/CONT failures.

This one completed independent review adequately covers the actual read result
and finite stopping decision. A further Pro consultation would add no identified
distinct framing or unresolved-disagreement value here, so none is added. No
additional result execution, repeated reader or verification query is selected.
Replication could address conditional precision or construction recurrence but
currently has no consequential enough expected use to justify its complete cost.
A new useful question need not first prove the present failure mechanism.

Root has separately requested source-only next-allocation reasoning with its
existing `/root/oracle_next_capability`, after this study's full publication and
cleanup. That keeps this same DM's question ownership active without another
result-bearing study. I may supply concrete interface/feasibility/full-cost facts
in this notebook; no new policy/controller query, outcome probe, code, fit or
native run is selected. Waiting allocation, parent shortlist use and fleet
transmission comparisons have separate owners and are not successor slots here.
Root owns a cross-question selection; this reading and own publication need no
routine Root acknowledgment. The immediate remaining B06 work is publication
of evidence/standing/shared scope and measured retirement of disposable targets.


<a id="b06-final-cleanup"></a>
### B06 publication and measured final cleanup — 2026-10-01 UTC

The complete read result, full original independent diagnosis and accepted
reuse/stop disposition are published at
`8072064fc3bb4d07e2a4c3b67942a242d6ebeb0c`. The successful fixed reader's
aggregate/per-world/epoch record is retained unchanged in Git; the large original
summary and all unique trajectories/datasets/checkpoints retain one canonical
remote copy at the locators above. Immediately before deleting the temporary
local summary, remote `summary.json` and `reading.json` hashes were rechecked;
raw2,661/873,616,739 bytes, assets12/5,168,100 bytes and data12/2,613,751 bytes
were present. The original Critic had completed its use of local inputs, and the
Root Oracle was told the canonical location before the redundant copy was removed.

Both workers/supervisors were terminal; the observer was stopped at generation30
with no pending wake or unconsumed event. The supported snapshot collector's
preview and apply used exact IDs with its elevated read-only process scan, under
the remote main-writer lock. Both were eligible, had no live reference, and their
sources were durable on published main. Claims, manifests, failed/successful
records and canonical outputs remain. Actual remote deleted targets and allocated
bytes were:

| Deleted target under `/home/wu/projects/HMASD/` | Allocated bytes before | After |
|---|---:|---:|
| `.git/hmasd-launch-sources/e86f2d465d0b45aaa82eb63d138b5e78` |813,219,840|absent|
| `.git/worktrees/e86f2d465d0b45aaa82eb63d138b5e78` |3,600,384|absent|
| `.git/hmasd-launch-sources/e35ec2ed8f434892ab9350874c1eb55e` |813,293,568|absent|
| `.git/worktrees/e35ec2ed8f434892ab9350874c1eb55e` |3,604,480|absent|

Remote net allocated-byte reduction is**1,633,718,272**. The pre-existing remote
Git automatic-object-GC bad-tree warning appeared during fetch, but did not block
the maintained snapshot collector; no object-store repair was attempted and no
collector refusal was bypassed.

The same read-only process reference scan returned empty for every local target;
Git confirmed none was tracked. Actual deleted local targets were:

| Deleted target under `/home/fires/hmasd-wsl/` | Allocated bytes before | After |
|---|---:|---:|
| `temp/directions/uav_fleet_adaptation/` (only two consumed B06 observer requests) |12,288|absent|
| `runs/uav_fleet_adaptation/b06_count_development_a02/summary.json` |12,775,424|absent|
| `runs/uav_fleet_adaptation/b06_count_development_a02/stdout.log` |0|absent|
| `runs/uav_fleet_adaptation/b06_count_development_a02/stderr.log` |0|absent|
| `runs/uav_fleet_adaptation/b06_count_development_a01/progress.json` |4,096|absent|
| `experiments/candidates/uav_fleet_adaptation/__pycache__/` |8,192|absent|
| `experiments/candidates/uav_fleet_adaptation/b02/__pycache__/` |53,248|absent|
| `experiments/candidates/uav_fleet_adaptation/b04_native_development/__pycache__/` |20,480|absent|
| `experiments/candidates/uav_fleet_adaptation/b06_count_development/__pycache__/` |122,880|absent|
| `tests/experiments/candidates/uav_fleet_adaptation/b06_count_development/__pycache__/` |110,592|absent|

Local net reduction is**13,107,200** allocated bytes; combined actual B06 cleanup
is**1,646,825,472 bytes**. All14 listed targets are absent. This is deleted
allocated storage, not a moved directory, tarball or retained backup. Together
with the earlier recorded B01–B05 cleanup, cumulative reclaimed bytes are
9,215,295,488; earlier figures are not a second deletion in this batch.

The small published B06 count-aware interface, collector, fixed reader and tests
remain useful for reading the retained claim evidence and source-only interface
work. All B06 executable files participate in that fixed source/reader contract;
no orphan experimental entry or scratch implementation was found. Frozen B02–B05
and shared helpers have live or evidentiary consumers and remain unchanged.
Canonical raw/checkpoint/data are required unique evidence, not disposable leftovers.
There is no cleanup blocker, unread result, live producer or pending B06 review.
The current authorized continuation is only Root's source/interface/full-cost
assessment with its Oracle; no next result study has been selected.


<a id="post-b06-source-allocation"></a>
### Post-B06 bounded source assessment — actual S2 versus no new purchase

**Assignment and scope,2026-10-01 UTC.** B06's full read/review/publication/cleanup
boundary is complete at `e49ddeb2db9f19e58eccf6a5e903d75691559a97`. Root asked
this same DM to supply source/interface/full-cost facts to its existing
`/root/oracle_next_capability`, which owns the separate-context next-allocation
challenge. Its current focused comparison is the already-costed actual-S2
acquisition design versus no new purchase. The Oracle explicitly asked not to
routinely reprice/redraft that settled design, and asked for a substantive
challenge to its tentative no-purchase preference if warranted. This entry is
that DM contribution, not a new selected study or a substitute independent
review. No new scientific query, trajectory reduction, fit, code or run occurred.

I read the complete existing
[actual-S2 source design](../uav_parent_adaptation/NOTES.md#s2-development-source-design)
and its [original independent corrections/disposition](../uav_parent_adaptation/NOTES.md#s2-development-independent-disposition),
including the two-context objective, paid B* addition, exact transfer controls,
reader scope and optional transfer-only price. Current published
[topic2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练) and
[topic4](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面) at
`e49ddeb2db9f19e58eccf6a5e903d75691559a97` change the marginal judgment through
retained P competence, adverse managed composition, completed CAL/CONT and the
new count result. The actual-S2 design was originally deferred before those
fleet readings; none is reinterpreted as an S2 experiment.

**Feasibility facts that are now settled.** The load-bearing parent B05
`LocalTeam.decide` and collector, plus radio B03 protocol/scheduler, are unchanged
from the reserved design's published source `b0731ce69`. Code/source inspection
confirms that all five lawful local distributions are constructed before current
private innovations, proposals are formed before reports/S2, and current local
query time counts toward the actual S2 deadline. At startup the proposals execute
for two ticks; later the previous commands continue until the two-tick delivery.
S2 may replace the rotating member's command and chooses the mask jointly with
the remaining proposals; on lateness it preserves the prior actual commands/mask.
A proposal can change search order or the resulting mask even when its own motion
is overwritten. Therefore the proposed intervention point is real and material:
change the selected proposal before report/search, not the delivered command.
The actor still lacks the coordinator's map, other proposals, rotation label,
current mask and pending command. This is a partial-information proposal-policy
problem, not a newly informed centralized controller.

Both preselected L0 all-on transfer heads are now complete, published and present
in the one canonical local B05 run. Byte-only checks verified
`assets/CAL0.pt` (15,395 bytes,SHA-256
`5b4a91a483239ac97e0dfa44cd1edbeb8b2c2e2050a58bf5587d383e0f4c026f`)
and `assets/CONT0.pt` (56,753 bytes,SHA-256
`f179c83a9f07e78eaea0fbd78b3ec3895d79f5cd4669f22dab15569e23c65eb5`)
under `runs/uav_fleet_adaptation/b05_native_consequence_a01/`, source
`2e22a2ccf6cafbde5b85a6658077ddcb2bbfcf94`. No asset forward was run.
Original S and the fixed B*0 temperature2 reference also remain available at
their previously verified locations. Thus unavailable assets or unfinished
all-on evidence are no longer grounds for deferral. The design's common B05
I decoder must still be retained: importing an all-on sampler wholesale would
change the operational law. B06's count-aware all-on helper is not a replacement
for the fixed N5 managed interface. No implementation is authorized by this
source observation.

**What a successful direct purchase would add.** S2 changes the proposal-to-team
consequence mapping, and that is a genuine constructive conjecture even after
the all-on losses. Fixed S2 can make a proposal useful through the rotating member's delivered
command, the shared mask, the sequential search result or subsequent visits.
A contextual S2-trained head that adds complete native value beyond unchanged
S, fixed B*, same-data CAL and transferred all-on heads would demonstrate useful
finite development in this coupled execution. It would not need to prove an
entropy/credit/representation explanation first. The original controls are
appropriate: merely improving S would not show that buying S2-conditioned
acquisition was necessary, and comparison only with C_S2 would omit the measured
C_T2 challenge. No positive pilot, exact headroom proof or exhaustive branch
screen is needed to admit this direct experiment if Root chooses its value.

**Why I do not recommend that purchase now.** The completed all-on B05 is the
most directly relevant adverse evidence: both CONT heads fit their empirical
objective and change physical choices, yet neither established added native
value over S or a recurring contextual increment over same-data CAL. That does
not refute S2 alignment, but lowers the expected return from reusing the same
single-address-perturbation/full-return labels,1,024-world dataset and bounded
frozen-backbone head family for another host. Actual S2 supplies a different
consequence map, not more independent contexts, a new information right or an
identified remedy for finite joint deployment. The two-context timing correction
keeps the intended comparison honest; it is not a new empirical capability or
an exact hardware-gradient guarantee.

B06 adds a distinct negative constraint without diagnosing B05: large full-network
movement and active count learning still failed to establish development beyond
reused P, while M's quality and L1 conditional gains survive. Neither tiny heads
alone nor complete optimization inactivity explains all these outcomes, and no
single mechanism is established. The parent managed B05 result already preserves
useful motion/compute tradeoffs and an ordinary reference that is stronger on
service/J. No new deployment requirement or newly evidenced intervention link
currently makes the narrower one-lineage S2 head comparison more consequential
than its known bill. This is a finite value-of-information judgment, not a rule
that every future experiment requires a diagnosed failure or all three of method,
task and mechanism contributions.

I reuse the complete settled price: **2fits,2,560H256 episodes/655,360 native
steps,2–4worker CPU hours plus15–45reader minutes and5–9support hours**.
The fixed managed search dominates collection; B06's cheaper observed runtime
does not justify lowering this price. Its reader/support and the previously
incurred original acquisition/B04/B05/B06 costs remain material. The optional
transfer-only comparison is a separate already-priced384-episode/98,304-step,
0fit purchase, not free diagnosis or a required first stage. I recommend neither
purchase now. No new source estimate or benchmark was generated.

The already-selected ordinary G question may change a useful future ordinary
proposal reference, but it does not test S2-conditioned learning and is not a
scientific admission prerequisite. My no-purchase recommendation stands without
waiting for G. Likewise, the separately owned waiting-allocation and parent
shortlist studies should proceed on their own merits; I propose no duplicate
or small offshoot merely to keep this direction occupied. I have no clearly
stronger source-grounded alternative to propose from this bounded assessment.

**Return to Root's Oracle.** Recommend no additional fleet/actual-S2 investment
at this boundary, retaining the full direct and optional-transfer designs and
all useful/adverse assets. A future concrete managed-use or learning conjecture
whose expected answer warrants the full cost can re-open direct exploration,
even after negative all-on/G evidence; there is no obligatory result dependency,
periodic poll, representation overhaul or renewed mechanism-screen campaign.
Root owns the cross-question decision, with its original independent Oracle
reviewing the actual new evidence. This source task introduces no result-bearing
operation and does not revise the completed B06 disposition.


<a id="post-b06-original-oracle-no-purchase"></a>
### Complete original next-allocation question and no-S2-purchase answer

Root asked that the complete original question and final answer be preserved
before the newly assigned stochastic-target source reasoning. The following is
verbatim apart from Markdown blockquote prefixes. This was Root's existing
separate-context registered ResearchCritic/Oracle; its answer is not an additional
B06 result audit or a review of the later stochastic-target question.

**Original Root question,2026-09-30 UTC:**

> New bounded source-only next-allocation question. Your earlier static-count design has now completed all4fits and its declared full bounded reader at sourcef529ba399 (runs/uav_fleet_adaptation/b06_count_development_a02):2656studyH256episodes plus5H8fixtures,679976native steps,32000updates/16384000presentations. DM's saved-record reading is provisional pending its original result Critic/publication: equal-N4/N6 M−F J+.005574,t95[−.000643,+.011791],service+.2765; path+919.855m/UAV. Lineage1target contrast positive conditionally; all6per-count M−P J intervals span0, all mean service changes nonpositive and travel higher. Inherited P−Q remains positive in both lineages/N4–6 under the revised interface. At most2visible peers evenN7 means crowded roster representation was not actually tested. Read original outcomes/adverses/fullcost and reuse the original critic once complete before final recommendation; these headlines are orientation, not a finished interpretation. Do not repeat its full result audit or request new outcomes.
> The enduring question is useful development/use of the demonstrated learned local-control capability, with ordinary-control and independent questions also legitimate. What next substantive question, if any, is worth this DM's complete investment after B06? Distinguish unchanged-parameter capability under the revised interface, learned increment relative to original assets, actual learning versus additional fixed-policy ranking, and source exposure versus untested crowded/dynamic membership. Do not automatically prescribe churn, more counts, another mixture, a feature fix or a transfer-only gate because the latest mixture was inconclusive. The original actual-S2 proposal remains deferred, not prohibited: its exact two-fit/2560H256/655360step/.2? correction:2–4workerCPUh+15–45reader minutes/5–9support-hour proposal and CAL/transferred controls are in parent NOTES#s2-development-independent-disposition (Root current plan); reconsider only if cumulative evidence and a concrete comparison make it preferable. New hypotheses need not diagnose B06 but must buy consequential knowledge/capability.
> Other selected owners are waiting B05 local-grant allocation replay, parent B07 fixed L2_E shortlist use, and fleet-transmission B05 ordinary score-directed G versus originalS/B*/C/Q; preserve those exact studies, no extra arms or duplicates. Count DM is still independently interpreting/publishing/cleaning B06 and is your source/feasibility/cost partner after its current boundary; don't commandeer its notebook or launch anything. Use accumulated project records,all3local libraries,July/external constraints and necessary primary web passages for detailed innovation; inherit their contrary evidence, no novelty/idea quota. Return one reasoned candidate or justified no-purchase, lawful interfaces and strongest simple alternatives, predictive outcomes, incremental/cumulative acquisition/fit/native/model/fullreader/support/retention costs, and material dissent. Source/metadata reasoning only: no controller/actor/model/native queries, new outcome probes, code, fit or launch. Root will select after the complete original result and your full recommendation.

**Complete original Oracle answer,2026-10-01 UTC:**

> **Recommend no new purchase at this boundary.** Retain P/Bstar as conditional capabilities, end the exact B06 mixture recipe, and keep actual-S2 learning as an unselected reserve. This recommendation stands without waiting for G. The selected score-directed, shortlist and local-allocation studies remain unchanged.
>
> I reused my earlier source analysis, reconstructed B06’s consequential saved comparisons and costs, then read its original result critic and the DM’s complete interpretation. This continues a separate-context review; it is not outcome-blind, because Root supplied headlines and I retain my earlier selection advice.
>
> B06 supports a narrower positive than successful count development. Its primary M−F effect is **+.005574 J**, with descriptive world interval **[−.000643,+.011791]**. Lineage 1 has a positive conditional target effect, and M improves quality relative to P in every count/lineage cell. Those findings should remain visible. But F loses J to P in five of six cells; M exceeds P in only one, with every M−P interval spanning zero. M−P mean service is nonpositive and travel higher in all six cells. Thus a positive M−F alone would credit recovery from ordinary continuation’s deterioration. [Complete B06 reading](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b06_count_development_a02/reading.json).
>
> The strongest retained capability is P itself. Across both lineages and N4–N6, P−Q J is positive with positive conditional intervals, accompanied by higher mean service and lower travel. This is useful **parameter reuse under the revised interface**. It does not establish unchanged-package portability: count-aware helpers, sampling addresses and world initialization were revised. Nor does it establish crowded-roster or dynamic-membership competence. Every saved acquisition, evaluation and fixture decision exposed at most two visible peers.
>
> The learning intervention was active: four full-network fits completed 32,000 updates, substantial parameter movement and active count-branch learning. Sparse peer exposure limits the representation conclusion; it does not turn the whole study into nonactivation. The strongest simpler explanation remains that further imitation changes useful inherited stochastic behavior, while mixed acquisition attenuates some of ordinary continuation’s loss. Because sampled P already outperforms its deterministic teacher C, better label reproduction need not improve native value. Entropy, visitation and finite optimization remain possible contributors, not identified causes. More episodes or unchanged fits currently lack a consequential use that warrants purchasing them. [Original independent diagnosis and disposition](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md:5526).
>
> **Actual S2 is the strongest remaining concrete candidate**, and its constructive case survives. A proposal can affect the coordinator’s search, mask and delivered commands even when its own motion is overridden. Training on those consequences could therefore develop a capability absent from all-on training. Policy-gradient reasoning permits the fixed coordinator to form part of the continuation process; it does not require differentiating through its search. But this supplies a conjecture, not a finite improvement guarantee. The interactive acquisition and regret assumptions in AggreVaTe also do not transfer to one frozen dataset and bounded neural heads. [Policy-gradient primary source](https://proceedings.neurips.cc/paper/1999/file/464d828b85b0bed98e80ade0a5c43b0f-Paper.pdf), [AggreVaTe primary source](https://arxiv.org/pdf/1406.5979).
>
> The managed evidence contains both opportunity and a strong ordinary alternative. S+S2 improves over its own all-on use by **+.093665 J**. Nevertheless, S+S2−C+S2 is **−.004497**, and S+S2−C_T2 is **−.010311**, with shorter S travel retained as a real tradeoff. Ordinary management gained more from the added control rights. This makes managed development a legitimate question; it does not identify a training mismatch that must be repaired. [Managed comparison](/home/fires/hmasd-wsl/runs/uav_parent_adaptation/b05_radio_composition_a01/reading.json).
>
> My objection to buying S2 now is its marginal information value. The completed all-on CAL/CONT study already tested the same paired-return acquisition and bounded frozen-backbone head family on two inherited lineages. The contextual heads fit their empirical objectives and changed physical choices, yet did not establish added native value over S or a recurring increment over same-data CAL. S2 changes the consequence map, but supplies neither more independent contexts nor new actor information. B06 adds a distinct adverse development result without diagnosing the same cause. I found no new practical requirement or stronger source-supported prediction that makes this narrower one-lineage purchase preferable now.
>
> The DM’s completed source assessment confirms that this is **a value judgment, not a feasibility blockage**. CAL0/CONT0 are published and available at their original hashes; unfinished evidence and missing assets no longer justify deferral. Intervention must remain before reports/search, local-query time must remain charged, and startup, two-tick delivery and late-result behavior must retain their actual meanings. The actor receives no free coordinator map, mask, rotation label or pending command. B06’s count-aware interface must not silently replace this frozen N5 managed interface. The DM concurs with no purchase after considering the constructive case. [Published source assessment](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md:5693).
>
> For the managed-learning claim, the smallest **currently specified complete comparison** remains the existing two-fit S2 design—not a mandatory transfer-only gate:
>
> - **CONT_S2 adds useful value beyond CAL_S2, unchanged S/Bstar and transferred all-on heads:** this would support conditional development using managed consequences. C_S2/C_T2 would establish the complete service, travel and compute tradeoff; it would not establish a general mechanism or default adoption.
> - **CAL_S2 or transferred heads supply the same useful benefit:** favor calibration or reuse for this finite purchase. A gain over unchanged S alone would not establish the value of buying S2-specific acquisition.
> - **Neither new head improves the retained choices:** end this managed head recipe. That would not falsify learning under coordinators or require a larger representation.
>
> The original controls are necessary to those distinctions. Dropping them would buy a different, weaker answer. [Complete reserved design](/home/fires/hmasd-wsl/docs/research/candidates/uav_parent_adaptation/NOTES.md:4443).
>
> The bill remains:
>
> | Purchase | Acquisition, fitting and native exposure | Complete estimated cost and retention |
> |---|---|---|
> | Actual-S2 development | 1,024 paired worlds; 2 fits; 4,096 updates; 524,288 pair presentations; 2,560 H256 episodes / 655,360 steps | 2–4 worker CPU hours + 15–45 reader minutes; 5–9 support hours; 1–3 GB canonical evidence |
> | Optional transfer-only comparison | 0 fits or new labels; 384 episodes / 98,304 steps | 30–60 worker + 10–25 reader CPU minutes; 3–6 support hours; .2–.6 GB evidence |
> | Recommended additional purchase | 0 new fits, scientific queries or outcomes | No new experimental storage; this review’s support work is unmetered |
>
> S2’s forecast ceiling includes **17.56 million coordinator geometry matrices / 4.389 billion user-power links**, plus local-controller, helper and native work. Its bounded reader includes **821,760 formula states**, up to **3.25 million selected candidate-state reductions**, and up to **124,928 backbone rows**; it adds no native transitions or optimizer replay. These are planning quantities, not measured runtime or admission. Zero fits does not make the transfer alternative free. [Full cost and verification scope](/home/fires/hmasd-wsl/docs/research/candidates/uav_parent_adaptation/NOTES.md:4637).
>
> Already incurred B06 cost is **327,680 labels, 679,976 native steps and 978.664 successful-chain CPU seconds**, including the reader; A01 separately cost 1.286 CPU seconds before scientific exposure. Through B06, the B02–B06 chain totals **12 fits, two calibrations, 2,367,528 steps and 3,323.067 measured CPU seconds including that failure**. Older Gaussian B01 remains separately incurred: two fits, 576,000 steps and 31,190.348 CPU seconds. Support time remains incompletely metered. B06 retains one canonical bulk copy, including approximately 874 MB of raw trajectories and required datasets/checkpoints; its measured cleanup is complete.
>
> The selected G comparison can change the ordinary reference: useful G would weaken the case for additional local-policy development; retained S value beyond G would preserve a narrower package capability. Neither outcome automatically selects S2, another fit or a temperature sweep. The three-library and July/external-review evidence likewise supports competent matched controls and explicit information rights, without making a new architecture or positive preliminary test obligatory.
>
> I checked B06’s frozen contract, saved primary and six-cell comparisons, per-world records, exposure, fit and cost fields, and the managed B05 contrasts directly. I reused the original result critic’s source/hash and 49-raw-file reconstruction rather than repeating its audit. I did not replay physics, policies, teachers or optimizers, and performed no new scientific execution or record edits.
>
> **MATERIAL_DISSENT: no — recommend retaining the demonstrated capabilities and purchasing neither further count development nor actual-S2/transfer evaluation now. Root has not selected a conflicting successor investment.**

**DM response and adopted boundary.** I accept the full recommendation, consistent
with my published source assessment above. Root has now explicitly adopted no
further exact-mixture, actual-S2 or optional-transfer purchase. This is a current
investment stop with useful P/B* and conditional positives retained, not an
S2 impossibility conclusion or a requirement to wait for G. Missing assets,
unfinished all-on evidence and implementation feasibility do not justify this
stop; the full cost and marginal scientific use do. The earlier source assessment
and all actual outcomes remain unchanged. No additional Pro or engineering review
is needed merely to preserve this prose or restate the resolved no-purchase choice.

Root then assigned a distinct **source-only** question: whether changing the
training target from one-hot C imitation to a useful stochastic control law can
develop the retained local policy beyond reuse. Its existing Oracle owns detailed
idea/library/primary-source challenge; this DM supplies actual acquisition,
feature/target/decoder/cache feasibility facts and prices only a concrete candidate
if one emerges. Zero policy/controller/model/native queries, new outcome reductions,
code, fits or runs are authorized. This is not an extension of B06 or the separate
accepted G study. Root clarified the premise: C is the observed weaker native
reference, but neither exact representability of C by the finite student nor an
equivalence between its CE optimum and C has been established. The lawful
observation-to-feature/target map must be checked directly, and no entropy or
imitation-failure diagnosis is assumed. The new source reasoning follows below.

<a id="stochastic-target-source-scope"></a>

### 2026-10-01 — source-only stochastic-target question

The source-only boundary above is prospective: preserve both B02/B03 starting
assets, all B04–B06 outcomes and ordinary references. Current published main
`de238594dc9d64d7be246e7b9628a63f6a53b272`, RESEARCH topic4, retains useful
sampled competence and active-but-unhelpful finite continuation; it does not
diagnose one-hot imitation or entropy as their cause. Its concrete design effect
is to require a target capable of changing useful deployed behavior and an ordinary
matched-information calibration/smoothing comparison, rather than another attempt
to match C more exactly. Topic3 and the current G contract preserve categorical
identity, flat-CDF decoding, actual-path caches and native-cost limits. The current
question is source feasibility and marginal scientific use, not a selected fit.
The existing Root-assigned independent Oracle covers the consequential choice;
this DM supplies source and paid-record facts without duplicate library review.
No fresh scientific queries, target/outcome reductions, code or run are performed.

<a id="stochastic-target-source-assessment"></a>
### Source assessment: available targets, useful changes and current purchase judgment

This is source and existing-record reasoning only. No target vectors were formed,
no trajectory/outcome was reduced, and no policy, C, helper, native or optimizer
query was executed. The original C and B02 collector/model/policy files remain
byte-unchanged from published B02 source `e945483b85c7f8ddfc315c57f36938d6c14201c7`.
The separate transmission G source was read in place; its source/contract and
accepted scope were not edited.

**The actual information map.** For N5, original `LocalController(history=False)`
replaces its points with current observed users on every call. `_parse` reads
only the ordered FP32 first103 observation fields: own location, up to20 local
user rows and10 local-peer slots. It never uses observation field103, the clock.
`MemoC._miss` sets C's predecision navigation to the acting policy's current
navigation. Calls occur at four-tick decision boundaries; earlier C commands and
history ages do not enter the new ranking. Thus the source target is a deterministic
computation of those103 values plus navigation, already present in the student's
114 inputs (103+10-way navigation+analytic fallback bit). This rules out an omitted
C memory or privileged observation at this interface. It does **not** establish
exact realizability by the finite two-hidden-layer ReLU actor, successful finite
optimization, or equality between a fitted CE endpoint and C. The student receives
neither C's selected category nor its27 scores; expensive analytic transformation
of shared information is still a representation/computation difference.

The teacher predicts four clipped motion ticks with observed users/visible peers,
its source-bound unknown-interference calibration, static visible peers and local
capacity/quality scoring. These27 scores are not native action values for the
remaining256-tick fleet episode. Simultaneous teammate choices, later observations,
navigation and interference remain coupled. A softmax of these numbers does not
inherit a native policy-improvement result.

**What already-paid records actually support.** The original full acquisition
collectors save per-decision x114, own pre/next navigation, fallback, command,
cache provenance, current-user/peer counts and all27 `expert_scores` and
`expert_served`, beside `expert_action_index`. They also retain native observations
and trajectories. The fit dataset returned by B02 stores only x114 and the
integer category; a new soft-target learner must extract the raw vectors explicitly.

| Records | Paid target coverage and limitation |
|---|---|
| Original B02 and B03 | Each has81,920 labels:40,960 from128 C-roll-in episodes, then20,480+20,480 from two64-episode greedy-current-student blocks. All have27 C scores/service estimates. Final distinct x counts are8,364 and7,616; repeated rows remain exposure, not independent contexts. |
| B06 F0/F1 | Same81,920 labels per fit atN5, with all27 scores in raw. Fresh continuation histories and extra count-branch implementation differ from original construction; these are not automatically matched controls for an offline refit. |
| B06 M0/M1 | Each81,920 labels,30% atN3 and70% atN7; full score vectors use explicitly revised C_N completeness logic. Pooling them into an N5 target would change the question. |
| Neural acquisition logits | Saved only for the neural roll-in phases, from the then-current collecting student. They are not unchanged final S predictions on every row. C-roll-in phase0 has no student logits. |
| Original final evaluation | Neural S episodes save S logits but do not obtain full C scores on S's own histories. Ordinary C/Q records are their own histories. Joining separate episodes cannot create matched S/C target rows. |
| B05 native consequence labels | Preserve two sampled action interventions and complete-S-continuation returns per paid context, not a27-entry native action-value vector. Their actual finite CAL/CONT program failed to establish added native value; calling these dense soft values would invent unobserved labels. |

Canonical B02/B03 raw and immutable assets remain at their previously verified
remote run paths under `/home/wu/projects/HMASD/runs/uav_fleet_adaptation/`
(`b02_inheritance_a01`, `b03_inheritance_recurrence_a01`); original summary/readers
bind every file. B06 canonical raw/datasets remain at its already recorded A02
path. No extra bulk copy or model pass was made for this assessment.

**Obtainable target laws and their different meaning.** Write c(x) for the saved
C category and s_a(x) for its saved score. These are prospective definitions,
not computed candidate outputs:

- Hard CE used in B02/B03/B06 is target delta_c, without label smoothing,
  teacher KL or entropy loss. B04's PPO omitted an entropy term; B05's bounded
  CAL/CONT objective is a different paired-native-return program. None already
  measures a soft C-score training target.
- Q10 can be obtained from a label alone: q_c=.9, q_a=.1/26 for a≠c.
  This is ordinary symmetric label smoothing. Default framework smoothing with
  .1 spread over all27 labels is a different target, including a different modal mass.
- Current G uses g_c=.9 and g_a=.1 exp((s_a−max_{b≠c}s_b)/.014) divided by the
  corresponding26-term sum. It uses FP64 arithmetic, no floor, and an exactly-flat
  score vector returns original Q10. In particular a fallback is not silently
  replaced by a point mass. All its needed target fields exist in original paid raw.
  Its native superiority remains unestablished; transmission owns that fixed study.
- Unchanged-S self-distillation requires unchanged-S probabilities on the chosen
  rows. Existing intermediate-student logits are not a substitute. A fresh S pass
  would be new actor work even without a native rollout. At identical parameters,
  law and arithmetic, S-to-S KL has the identity as a minimizer and no native
  improvement direction. Finite precision, a new fit class or a different teacher
  changes that statement; numerical drift alone is not an improvement rationale.
- A changed S temperature, global entropy preference or constant mixture is an
  ordinary calibration/regularization intervention. A state-dependent target can
  change more than a scalar temperature, but its native benefit still requires a
  complete comparison with the competent direct transformation and unchanged S.

All27 category identities and their original ordered FP64 flat inverse-CDF law
matter. The program draws a fresh indexed private uniform at every stochastic
query, even when logits/rankings hit its episode/agent-private exact cache.
Clipping can make distinct categories induce the same four-tick path; physical
path mass is the sum over such aliases, not categorical entropy. Collapsing,
reordering or selecting one representative of an alias class would change the
specified stochastic law and needs its own prospective comparison. Navigation
and cache visitation follow the deployed policy's actual path; C/G action choices,
future observations or caches cannot be borrowed from another episode.

Reusing original acquisition therefore permits a **static recorded-data** soft
fit without new C acquisition, if separately selected. It does not reproduce the
original interactive aggregation recipe under a new learner or provide sampled
S/G's own visitation distribution. Genuine new aggregation would execute the new
collector policy on native worlds and obtain labels on those histories, with
all those episodes, C/helper queries and cache work charged. A frozen-data fit
may be useful; coverage is a limitation to state, not a mandatory extra-data gate.

**My current marginal-value judgment.** Dense teacher scores carry useful
information discarded by an argmax label: they can express which departures look
locally less costly. The strongest constructive conjecture is consequently a
state-dependent departure law that retains useful stochastic movement while
avoiding some locally bad alternatives. This is a real potential experiment,
not identity, and it need not first prove an entropy diagnosis or teacher superiority.
But the available numbers optimize a censored four-tick proxy. S's demonstrated
native surplus may depend on its departures from that proxy; merely fitting C/G
better cannot be used as the success criterion. The new G comparison already
spends the cheapest direct ordinary law on the actual task. Cloning it would add
an approximation/representation/computation question; original cached-C comparisons
supply no general speedup premise for that purchase. B06's higher quality but
extra travel and uncertain J also caution against valuing local quality alone.

I recommend **no additional fit on the strength of this source mapping alone**.
This is not an empirical rejection of soft targets or a rule to wait for G.
A meaningful new proposal must identify the extra use/knowledge bought over the
fixed G study, unchanged S and ordinary smoothing/calibration; predict a native
consequence rather than only target KL/entropy; and retain both inherited lineages
and their costs/adverses. The Root-assigned independent Oracle owns its detailed
constructive challenge and may supply such a proposal. I have supplied the factual
map without requiring a new architecture, proof, positive pilot or cause diagnosis.
Root owns allocation and resolution of any material disagreement.

No such concrete additional purchase has been selected in this DM source task,
so no speculative fit grid, evaluation panel or per-fit price is introduced.
A later costed candidate would have to count extraction/new teacher or S rows,
actual data weighting and presentation/fit counts, own-history collection,
new native final comparisons, helper/full-ranking/cache work, reader reconstruction,
source publication, support and one required evidence copy. Reused labels are not
fresh independent acquisition. The incurred B02–B06 chain remains12fits,
2paid calibrations,2,367,528native steps and3,323.067 measured CPU seconds,
including zero-exposure A01; older B01 remains separately2fits/576,000steps/
31,190.348 CPU seconds. Support is incompletely metered. This source task added
zero experimental work and no bulk artifact; its reading/publication support
is unmetered rather than zero. No temporary code/data or new cleanup target was
created, and no accepted operation is pending.

Source anchors: original `uav_local_history/b01/controller.py` (`_parse`,
`_ingest`, `_decide`, `act`); inherited `b02/controllers.py` (`MemoC`,
`memo_key`, `_features`), `b02/policies.py` (helper/cache/decoder),
`b02/collect.py` (raw versus fit fields), `b02/model.py` (hard CE);
`b06_count_development/collect.py` and `controllers.py` (count interface);
transmission `b05_score_sampling/policies.py` and its fixed contract. These are
source-derived statements, not newly executed policy evidence. Prior result
anchors above remain the authority for numerical observations and costs.

<a id="stochastic-target-concrete-price"></a>
### A distinct S-prior target: concrete source price and scientific challenge

After the assessment above, the same independent Oracle supplied a concrete
alternative that changes my no-candidate premise: retain P0 itself as the target
prior and add a bounded local-score tilt. This is a **priced proposal, not a
selected experiment**. Root still owns allocation. All work here remains source,
metadata and cost arithmetic; no candidate probability, outcome, model/controller
query, code or run was produced.

The Oracle's complete concrete request was:

> Please source-price one concrete candidate, no execution/target calculation. Proposed changed target preserves S0 as a prior instead of centering the learner on C: at each saved N5 F0 acquisition row x, p=original inherited P0/S0 categorical law; r(a) ∝ p(a) exp((C_score(a)−max C_score)/.014); target T=.9p+.1r. Matched ordinary target H=.9p+.1δ_C is a simple C-assisted stochastic policy and must be trained as well. This adds lawful model score information to a retained capable policy; E_r[C_score]≥E_p[C_score] is only a same-context proxy identity, no native-J claim. T versus H asks whether the full preference distribution has value beyond mixing in C’s hard choice; unchanged P0 and paid temperature-2 B*0 remain strong controls. No claim of entropy restoration. Two new complete full-network fits, BOTH from the exact P0 initialization and on the SAME already-paid F0 phase datasets/order/8,000 updates×512, preserving the B06 N5 adapter and hard F0 endpoint. This is one parent/data instance, explicitly exploratory, not two independent lineages.
> Proposed complete final new panel: inherited P0, B*0, paid hard F0, learned T, learned H, direct fixed T, direct fixed H, fixed G, Q.10, Q.05 (10 stochastic programs×32 worlds×2 tapes), deterministic C×32: 672 H256 eps =172,032 new native steps. Same N5 B06 initializer throughout; cannot pair to original-G outputs by numeric seed. No S2/count/M arms. Direct T/H each run their own P0+MemoC on own histories; all final students sample temp1. No fresh acquisition: derive 163,840 target vectors from the 81,920 F0 rows; future purchase requires P0 logits on all those saved x (potential exact duplicate cache: F0 unique9238), since raw student logits are not frozen P0. Need cost of teacher probability queries, full raw score/nav/features binding and independent complete target reconstruction (not assuming B06’s 80-context C check verified every new target), fits, all native/controller/model/helper work, full reader, storage/support. Can old F0 be an exact paid hard-target control under dataset/order/init? Confirm score dtype/saved sufficiency and any feasibility/scientific flaw. No purchase has been selected; pricing is to decide between this bounded study and stopping.

**Source feasibility and exact paid control.** Yes: paid F0 is the existing
hard-target fixed-data control when its original data sequence and training program
are retained. Its original P0 state is
`6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`;
with the exact zero128 count branch, its generalized initial state is
`009970e07ab41ce6b4f9dc83a4266552d5f862bf77f4bb5a4544e3a0c767ae55`.
B06's CountStudent has34,843 FP32 parameters; atN5, (N−5)/2 is zero and the
count branch/Adam moments remain zero without decay. Original P0 tensors are
copied, never reinitialized, and original optimizer state is not loaded.

Use fresh Adam at3e-4, betas(.9,.999), eps1e-8, no weight decay,
amsgrad/foreach/fused/maximize false; clip global gradient norm at1. The
three accumulated datasets are40,960/61,440/81,920 rows with30/20/20 epochs,
2400/2400/3200 updates and1,228,800/1,228,800/1,638,400 presentations.
F0's shuffle root29514101 and exact(root,phase,epoch) order are recorded.
New T/H targets are frozen per saved row and reused across these phases;
they must not be recomputed from the changing fitted student. The new loss's
target/reduction dtype still needs a prospective implementation specification;
reusing F0 does not assert bit equality between different loss kernels.

All bindings below are from the published B06 reading, not reruns:

| Existing item | Exact recorded identity |
|---|---|
| F0 phase0 chunk |40,960 rows; `data/F0_phase0.npz`,319838bytes, SHA256 `7b3a9612fcf05f9b5885db07bfdf4f5b4002a103dca09c2f312ceed508937e32` |
| F0 phase1 chunk |20,480 rows; `data/F0_phase1.npz`,147674bytes, SHA256 `2fa74f481d3517a04f7e05e8526ed81931620d358922fcbbd55eca4ac6deed4a` |
| F0 phase2 chunk |20,480 rows; `data/F0_phase2.npz`,159927bytes, SHA256 `24e80845eb4483e23e35ce8993187997d7f80c8bb4c2341281b9cf50dae397bc` |
| Final F0 |`assets/F0_phase2.pt`,430675bytes, SHA256 `8cd5082bda9f466f06f7eac41024aadbd8376c00c8d715af9f1f04a4d596e9d0`; state `16b87debaf445a9d5d863d730a988edbc614967eba2d598ba4ac984cba5fbdcc` |
| Phase shuffle streams |`51bdf596d18cf5f79a9ffc75f5888b629a961df8e6dac8b6837eb65b33949f97`; `711ab4dc717dcc5fe51efe14ca24eafdf67f9a44ba84a1d41597d9a7f3f224f7`; `4985082f5f7f5eb5e3aa2a968658f5b299e10f3d341d951567cd04c6a64ddf13` |

All accumulated dataset digests, original/phase/final state identities and70
epoch records remain in the pinned reading. F0's later data were generated by
its own greedy intermediate endpoints. This control therefore supports the
**fixed recorded-data target comparison**, not a comparison of T/H's own
interactive aggregation procedures. Both original inherited lineages remain
preserved; this proposal intentionally tests only P0 and one existing data instance.

A read of original raw NPZ headers confirms `expert_scores`/`expert_served`
are little-endian FP64 with shape(64,5,27), features FP32(64,5,114), and
predecision navigation/expert labels int64(64,5). All256 F0 raw files occupy
24,268,147logical bytes at the existing canonical B06 A02 path. The existing
metadata records81,920 C requests,72,682 exact episode-private cache hits and
9,238 misses—not merely a numeric np.unique estimate. These cost249,426
candidate paths,997,704 modeled ticks and3,344,917 candidate/setup links.
The original three optimizer kernels used19.112979CPU-s; complete F0
acquisition+fit used68.910648CPU-s. None of that acquisition needs repeating.
A metadata command initially found no NumPy in system Python; reading the NPY
headers with standard-library ZIP/struct/AST succeeded. This was a source-inspection
tool issue, not a scientific attempt or remaining blocker.

**Independent comparison correction.** I challenged the proposed attribution:
when c is an argmax, real-arithmetic expected local scores obey
E_s[H]≥E_s[T]≥E_s[p]. H already maximizes the score of the .1 replacement
component. T also usually moves less far from p, and on flat-score fallback T=p
whereas H mixes C's waypoint category. A T−H gain cannot isolate preference
information from intervention strength, entropy or fallback. This does not
invalidate the complete-target package question; it changes its interpretation.

The Oracle's complete disposition was:

> Agreed on fallback: T=P at flat C-score contexts while H mixes C's waypoint fallback; retain that as part of the complete target-package contrast, not a pure soft-versus-hard-content attribution. No extra matched-fallback arm. Preserve p's decoded FP64 masses/zeros; specify max-subtracted multiplication/normalization and an explicit all-flat r=p branch, with no floor or alias merge. Full-reader scope for cost: reconstruct all81,920 saved training rows/targets (including C scores/nav/features and frozen P0), verify all672 final native trajectories and every actually deployed neural/controller/RNG law, and read each final trained model once on all81,920 saved rows (163,840 endpoint diagnostic forwards total) so target fit is not inferred from only changing optimizer-stream losses. Do not add shadow C/P queries on learned-student evaluation histories, counterfactual native branches or full training reruns. Direct T/H teacher outcomes and native student outcomes suffice for the package question; finite approximation/visitation causes remain unseparated.
>
> I agree and will make the inequality explicit: at nonfallback contexts H has at least T's expected local score; the reason to explore T is a gentler, parent-conditioned complete intervention whose native behavior might differ usefully, not more proxy maximization. T−H alone cannot isolate preference information from intervention strength, entropy or fallback. I am keeping the two-fit package question and current comparator for pricing, not adding a calibration sweep or attribution arm. Also the ≤.1 target-TV bound does not constrain the finitely trained student's off-data law, and Adam does not turn a .1 initial loss gradient into a guaranteed .1-sized update. The full native controls and complete endpoint reading carry that risk.

I accept that resolved scope. The score range on this actual N5 source is[0,1]
(up to5 stations×10 selected links, clipped quality); with tau.014 and some
p≥1/27, centered FP64 score multiplication cannot make the whole normalizer
underflow merely because maximal-score bins have zero p. My initial generic
underflow caution was corrected promptly; it is not a host blocker. Preserve
p zeros and the specified arithmetic/CDF nevertheless. No numerical target or
synthetic policy evaluation was performed to reach these source conclusions.

**Complete prospective work.** New final worlds/tape roots and launch inputs
are unselected. Every arm must use the same explicit B06 N5 layout initializer,
local observation/helper/nav,27 categories, four-tick holds and original flat
private CDF. The initializer discards a native reset and then recomputes channels
for the explicit paired layout, so both calls are charged. Numeric seed equality
with the other direction's ordinary-G study is not paired geometry or reusable
final evidence. No arm is added to that study. Direct T/H each require P0 and C
on their own current histories, including separate paid helper/cache work;
learned T/H require only their helper and network at deployment.

| Prospective work | Exact requests or pre-cache ceiling |
|---|---:|
| New fits / updates / optimizer presentations |2 /16,000 /8,192,000|
| Frozen target rows / target vectors |81,920 /163,840|
| New acquisition episodes / labels / calibrations |0 /0 /0|
| Final stochastic episodes / deterministic C episodes |640 /32|
| New native steps / UAV ticks |172,032 /860,160|
| Native dense slots, including one constructor and two refreshes per episode |47,678,675|
| Final agent decisions / private draws |215,040 /204,800|
| Worker full-C requests |112,640|
| Worker C paths / modeled ticks |3,041,280 /12,165,120|
| Worker candidate+setup links |≤254,566,400|
| Worker final neural+helper requests |143,360|
| Worker P0 archive forwards, shared between T/H targets |≤81,920|
| All worker forwards outside optimization |≤225,280|
| Reader old+new raw files / saved native ticks / saved decisions |928 /237,568 /296,960|
| Reader C requests: all old target rows plus final C programs |194,560|
| Reader C paths / modeled ticks |≤5,253,120 /21,012,480|
| Reader candidate+setup links |≤439,705,600|
| Reader helper requests / setup+extreme links |≤225,280 /31,539,200|
| Worker helper setup+extreme links |≤20,070,400|
| Reader final deployed neural rows |143,360|
| Reader unchanged-P0 target rows |81,920|
| Reader endpoint diagnostic rows, both fitted models |163,840|
| All reader forwards / worker+reader forwards outside fitting |389,120 /614,400|

C link ceilings use≤20 observed users and≤4 peers:108×20 candidate links plus
5×20 setup links per miss. Helper ceiling is(5+2)×20 links per miss. Requests
and records remain counted on hits; only deterministic same-input computation
may be reused. Reconstructing the old archive with the original episode-private
keys can retain its9,238 C misses; the new laws' final cache misses are unknown.
Full target and feature checking must cover every old row, not extend B06's
80-context check by assertion. Reader work has zero new native transitions,
optimizer replay, counterfactual branches or C/P shadows on learned deployment
histories. The two complete endpoint data passes are new paid diagnostics,
not historical optimizer-stream losses or held-out target validation.

**Price.** Allow5–12 worker CPU minutes plus5–18 reader CPU minutes:
**10–30 combined CPU minutes**, with approximately comparable single-thread
wall absent contention. The F0 optimizer-only19.1s anchor and recorded B06
N5 C/Q/P/B* mean episode CPU .163/.245/.257/.313s support scale, not a benchmark
of the new direct policies. Full B06 reader cost284.7s for430,080 actor rows
and only80 reconstructed C contexts; this new full-C/target reader has different
work and may exceed a simple episode-ratio projection. Cache savings are not a
worst-case runtime guarantee. Imports, constructor, serialization/hash work and
the fixed reader belong in the measured enclosing chain; admission, Git children,
queue and human/model support remain separate, never silently zero.

Estimate **6–10 support hours** for precise static-data/source bindings, the
soft loss and two direct laws, focused numerical/RNG/alias checks, independent
engineering review, full reading, publication and cleanup. Original source
assessment support is additional and unmetered. Retain one new canonical raw,
target, checkpoint and compact diagnostic copy, about **.4–.8GB**; the existing
F0 evidence stays in place. Two uncompressed FP64 target matrices alone are
35,389,440bytes; one P0 probability matrix is17,694,720bytes, and both endpoint
FP32 logit matrices would total17,694,720bytes if retained. These are logical
sizes, not measured compressed output. Plan **.8–1.5GiB** process memory and
**.8–1.2GB** temporary managed source snapshot (each measured B06 snapshot plus
registration was about.817GB). Fresh actual-node admission is only for a later
selected launch; no node reservation or profile is needed for this price.

If bought exactly, the broader B02–B06 cost chain would become14fits,
2paid calibrations and2,539,560native steps, with original3,323.067CPU-s plus
the new measured work (currently estimated10–30minutes). Earlier B01 stays
separate at2fits/576,000steps/31,190.348CPU-s; none of the adverse investment
or support cost is reset. Existing useful P0/P1, B* and all F/M evidence remain.

This is now a meaningful bounded **target-package/learning-use question**, not
plain G cloning or another attempt to reproduce C. I regard it as feasible and
worth a decision against stopping: direct T/H can establish whether the new
ordinary target package has native use; learned endpoints can establish whether
the finite recorded-data fit supplies native use beyond P0/B*, paid F0 and the
ordinary controls. Improvements only in target fit/proxy, or only over H/F0 while
losing to P0/B*, would not establish useful development. A direct-policy benefit
without a useful learned endpoint retains an ordinary capability and declines
the finite fitting route; a learned gain does not identify why approximation and
visitation helped. These predictions need no prior causal explanation of B06.
One P0/data instance cannot establish cross-lineage learning reliability. The
independent Oracle will deliver its full recommendation to Root; this DM has
priced and challenged it, without selecting a run or self-clearing an objection.


**Direct-baseline efficiency correction.** The Oracle correctly notes that direct
T/H can take the exact x114/fallback/navigation from the full C result already
paid for, instead of calling the analytic helper redundantly. Adopt that efficient
path when its source/feature equality is preserved. The table's helper figures
are conservative ceilings, not required duplicate work: avoiding those40,960
worker helper calls leaves102,400 pure-student helper requests and at most
14,336,000worker helper links; actor and C counts are unchanged. Any separately
chosen reader equality check remains charged. No amortization judgment may be
manufactured by a knowingly redundant direct baseline. When flat scores are
intended to make T exactly P in the finite decoder, the final T branch should
return p.copy(), not merely set r=p before .9p+.1r; those arithmetic expressions
need not be bit-identical. This source clarification requires no new outcome probe.

The source task is complete and returned through native communication. There is
no accepted producer, unread owned result, outstanding cleanup or selected fit.
The Root-assigned Oracle's independent recommendation goes directly to Root;
Root chooses the next investment. This is a completed feasibility/price, not
an experimental conclusion or permission to implement the proposed study.

<a id="b07-original-selection-review"></a>

### 2026-10-01 — complete original stochastic-target review and selected response

Root’s original question, followed by its explicit premise correction:

> Root read your complete final answer837788647/window01a0f4c0-c857-7211-8ca2-da2625cca8a7 plus DM full post-B06 assessment. I adopt no further B06/actual-S2/transfer purchase now; retain your full recommendation and those reserves. A new bounded SOURCE-ONLY innovation question changes the proposed learning target, not merely S2's execution map: can training toward a useful stochastic control distribution develop the retained policy beyond unchanged reuse, where further one-hot imitation of C has a demonstrably inferior limiting control target? This is a constructive conjecture, NOT an identified entropy/BC cause of B06 or a selected fit. P>C and F deterioration motivate considering the target; they do not show that any soft-target recipe helps. G's score-directed law and Q's ordinary randomization are already specified and currently owned by the other DM. They may be teacher/reference candidates, not assumed better-than-S targets or permission to add queries to that study. Exact self-distillation of S may be an identity/no-new-capability alternative; hard-label continuation, ordinary smoothing/entropy control and direct reuse must be considered honestly.
> Please own detailed innovation and independent challenge for this changed question using the cumulative original/July/external records, all three libraries and load-bearing primary passages. Check whether soft/stochastic distillation or its decision-relevant variant has already been tested here, whether the conjecture is merely known distillation without consequential use, and whether a target can supply value rather than just redistribute a fixed policy. Do not assume that successful cloning improves on its teacher, that score-proxy quality improves native J, or that entropy alone caused prior outcomes. A different worthwhile target construction may be preferable; no architecture/new-idea/positive recommendation is owed. Preserve all prior head/full-network failures and the all-on/managed/count distinctions.
> The same fleet-adaptation DM will supply source/interface/feasibility/full-cost facts after its completed boundary. Neither of you may launch, query policies/controllers/models/native kernels, reduce new outcomes, implement code or purchase fits. Reuse paid saved summaries and source semantics only. If a concrete comparison is worthwhile, state what it teaches or enables beyond fixed-asset ranking, its strongest ordinary controls, distinct possible outcomes, actual information rights, acquisition/label/fit/native/model/full-reader costs, support cost and stop alternative. G's eventual result may change allocation but is not an invented required gate. If this new conjecture does not justify experimentation, say so with its actual reason; Root will not call source work an active result study. Return one complete recommendation; use the existing source partner, no parallel duplicate review or additional role.

> One precision correction to my seed framing: C itself is the observed weaker native reference. Only hypothetical exact reproduction under matched interface/history would reproduce C; I have not established that C is representable from the student's retained features, or that the population/finite CE optimum equals C. Please challenge that identifiability/representation premise explicitly. Do not let 'inferior limiting target' become an unsupported theorem or causal explanation.

The independent Oracle’s complete final answer:

> I recommend **revising the target and selecting one two-fit exploratory comparison**. The useful question is whether a modest, model-guided change to retained S can be learned into its existing actor while preserving useful native behavior. Plain G-cloning, entropy restoration and further C imitation do not by themselves supply that rationale.
>
> This recommendation preserves the completed B06 verdict and the unselected actual-S2/transfer reserves. I performed source and saved-evidence review only: no policy queries, target calculations, new outcome reductions, implementation or experiments.
>
> **The supported diagnosis**
>
> C’s N5 decision is determined by information already present in the student’s input: ordered `obs[:103]`, predecision navigation and public constants. `history=False` C has no omitted observation history relevant to its ranking. This establishes information sufficiency of the source program. It does **not** establish exact representation by the finite MLP or convergence of population or finite-sample CE to C. The corrected Root premise is therefore appropriate. [Controller source](/home/fires/hmasd-wsl/experiments/candidates/uav_fleet_adaptation/b02/controllers.py:58)
>
> The positive retained asset is sampled P/S. The adverse evidence remains substantial: active full-network RL, native-consequence heads and full-network hard-label continuations failed to establish the desired development benefit. B06’s mixed continuation softened some fixed-count continuation losses, while its mean native result remained below inherited P and included greater travel. Those observations motivate preserving useful inherited behavior; they do not identify entropy, imitation, capacity or credit assignment as the cause.
>
> The broader record also cautions against treating every supervised-objective change as futile. Planning-compression B03’s saved summary reports original weighting beating ordinary BC by 14 and 17 completed jobs across its two 256-context panels, with adverse worlds and unchanged packet counts. That is a small, conditional positive on another host—not evidence for this proposal. R54’s supervised full-set reference failed its access rule; energy-relay imitation’s revised loss produced unresolved native gains and adverse tails; coupled-host distillation failed its declared purchase rule. [B03 evidence](/home/fires/hmasd-wsl/runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/summary.json), [R54 evidence](/home/fires/hmasd-wsl/docs/external-review/gpt5_6_pro/20260717_r54_hfsr_result/R54_HFSR_RESULT.json), [energy-relay corrections](/home/fires/hmasd-wsl/docs/research/candidates/energy_relay_imitation/NOTES.md:739)
>
> The relevant original, July and external-review records do not show this categorical soft-target comparison already executed. B02/B03/B06 use hard CE; B04 and B05 test different learning objectives. That is a bounded coverage finding, not an exhaustive novelty claim.
>
> **The proposed target**
>
> For a lawful N5 input \(x\), let \(p(a|x)\) be retained P0’s original sampled categorical law, \(s_a(x)\) C’s four-tick local score and \(c(x)\) C’s selected category. Define:
>
> \[
> r(a|x)=
> \frac{p(a|x)\exp((s_a-\max_b s_b)/0.014)}
> {\sum_b p(b|x)\exp((s_b-\max_j s_j)/0.014)}
> \]
>
> \[
> T=0.9p+0.1r,\qquad H=0.9p+0.1\delta_c.
> \]
>
> Train one actor toward **T**, and one toward **H**, the ordinary comparator that mixes C’s choice into S. H is also an ordinary soft supervision objective: 90% preservation of P’s distribution plus 10% hard C imitation.
>
> For exactly flat scores, T returns `p.copy()` directly. General T preserves P’s decoded FP64 masses and zeros, uses specified max-subtracted arithmetic, retains all 27 categories and uses the existing ordered flat CDF with one fresh private uniform per decision. Physical aliases remain separate. Both direct teachers follow their own histories and navigation.
>
> The target supplies information beyond identity self-distillation: C’s relative action scores alter P’s distribution. It preserves P completely where those scores provide no distinction. The intended native conjecture is that this conditional, limited change can retain useful movement while improving some local decisions.
>
> The strongest objection is consequential:
>
> \[
> \mathbb E_s[H]\ \geq\ \mathbb E_s[T]\ \geq\ \mathbb E_s[p]
> \]
>
> outside fallback; all-score-tie fallback gives equal proxy expectations. Thus **T cannot be justified as maximizing the local proxy better than H**. Its possible advantage is in complete native behavior despite pursuing that proxy less aggressively.
>
> Moreover:
>
> - T and H differ in intervention strength and fallback behavior as well as preference distribution. A T win would establish a package effect, not isolate richer score information or entropy.
> - C’s score is not native continuation value. Simultaneous teammates, interference and changed visitation can reverse its preference.
> - The target’s total-variation distance from P is at most 0.1. That bound does not constrain the finitely trained actor away from the training data. Adam also does not turn a 0.1-scaled initial gradient into a guaranteed small parameter step.
>
> These are limitations of the proposed experiment, not prerequisites for another diagnostic study.
>
> **What the literature supports**
>
> This is an application of known distillation and regularized policy-improvement ideas. Rusu et al. explicitly compare hard-action, value-regression and KL distillation targets and report conditional student improvements; their results do not imply that cloning improves on every teacher. [Policy Distillation, §§3.2–4.2](https://arxiv.org/pdf/1511.06295)
>
> All three libraries were checked, with load-bearing primary passages read:
>
> - **new-libs P13:** multiplicative updates use actual marginalized utilities in static potential games. Our local score is not that quantity, so its convergence result does not transfer. The catalogued local PDF was absent; I retrieved the primary paper directly. [P13 catalog](/home/fires/hmasd-wsl/docs/new-libs/corpus/papers/P13/metadata.json), [primary §§2–3](https://arxiv.org/pdf/2204.05466)
> - **Inst-sci MARL-0524:** PTDE distills personalized global features into local inputs using MSE. It neither supplies missing local information here nor establishes this action-distribution target’s value. [Primary PDF, §§3.3–3.4](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0524.pdf)
> - **My-lib, NeurIPS 2023, `2f0435cffef91068ced08d7c7d8e643e`:** CSIL derives prior-weighted exponential policy updates using value information and additional MDP knowledge. That supplies a useful construction, with the native-value assumption explicitly missing here. [Primary PDF, pp.3–5](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/neurips-2023/2f0435cffef91068ced08d7c7d8e643e/arxiv-2305.16498.pdf)
>
> I also checked the closed-form policy-improvement and distilled-ensemble passages. Neither makes an ensemble, self-distillation or a score tilt an automatic improvement. Exact unchanged-S self-distillation supplies no new improvement signal; temperature modification already has a competent paid direct-use comparator, B*0.
>
> **The smallest worthwhile complete comparison**
>
> Use the already-paid **F0 N5 archive**, with both new actors initialized from the same P0 tensors and existing zero count branch. Preserve F0’s phase datasets, shuffle order, optimizer and full-network exposure:
>
> - Datasets: 40,960 / 61,440 / 81,920 rows.
> - Epochs: 30 / 20 / 20.
> - Each fit: 8,000 Adam updates and 4,096,000 presentations.
> - Two fits total; no fresh acquisition or new interactive aggregation.
>
> The paid hard F0 endpoint is an exact fixed-data objective control under these bindings. Its later acquisition states were generated by F0’s greedy predecessors, so this experiment evaluates learning on that archive. It does not reproduce T’s or H’s own acquisition distribution. [Training source](/home/fires/hmasd-wsl/experiments/candidates/uav_fleet_adaptation/b06_count_development/model.py:79)
>
> Evaluate P0, B*0, F0, learned T, learned H, direct T, direct H, G, Q.10 and Q.05 on 32 fresh common worlds with two private tapes; evaluate deterministic C once per world. This is **672 H256 episodes**. All arms use the same B06 N5 initializer and adapter. Numeric seeds alone cannot pair these outcomes with the original G study.
>
> This is one parent/data instance with two matched objectives, not two independent training replicates. It needs no preceding teacher-success pilot and no invented requirement to await G’s result. G’s eventual evidence may nevertheless change Root’s allocation.
>
> Read native J, service, quality, travel, adverse worlds and complete deployment cost together, averaging tapes within worlds. Also read actual updates and movement, target displacement/entropy, and each final actor’s error on every saved training row. No shadow C queries on learned-student evaluation histories or counterfactual native branches are needed.
>
> The outcomes would change decisions as follows:
>
> | Observation | Consequence |
> |---|---|
> | Learned T improves on P0/B*0 and learned H, with a useful benefit/cost position against direct controllers | Supports a conditional development capability; independent replication becomes a possible next investment. |
> | Learned H provides the useful gain and T adds none | Prefer ordinary preservation-plus-C supervision; no full-score-target increment established. |
> | Direct T/H help, but their learned actors do not retain that benefit | Preserve the ordinary controller result; this archive/fit fails to amortize it. No automatic DAgger or capacity repair. |
> | New actors only beat damaged F0, or merely reproduce P0 | Preservation was achieved, but development beyond reuse was not. End this purchase. |
> | Better target fit or local scores accompany adverse native outcomes | Reject the package’s native-use prediction at this exposure. |
> | T is mostly unchanged P | Record limited intervention exposure; do not call it an active adverse score intervention or automatically enlarge it. |
>
> A faster actor with native losses remains a measured tradeoff. Successful cloning alone is not sufficient.
>
> **Complete prospective price**
>
> The DM verified archive/header/hash bindings and supplied source-derived counts and timing estimates. I checked the consequential source semantics and saved summaries; I have not recomputed targets or tested the proposed runtime.
>
> | Work | Prospective cost |
> |---|---:|
> | New fits | 2; 16,000 updates; 8,192,000 presentations |
> | Target construction | 163,840 target rows from 81,920 reused records; 81,920 P0 probability requests shared across targets |
> | New native evaluation | 672 episodes; 172,032 team steps; 860,160 UAV ticks |
> | Final decisions / private draws | 215,040 / 204,800 |
> | Worker full-C requests | 112,640 |
> | Worker neural rows outside fitting | At most 225,280, including target construction |
> | Complete reader | 928 old/new files; 237,568 saved native ticks; 194,560 C requests; 389,120 neural rows |
> | Total neural rows outside fitting | At most 614,400 |
> | Worker + reader CPU | **Estimated 10–30 minutes**, not a bound or admission |
> | Implementation, checks, review, publication and cleanup | **Estimated 6–10 support hours** |
> | New canonical evidence / memory | Approximately 0.4–0.8 GB / 0.8–1.5 GiB |
>
> Uncached C ceilings are 3,041,280 worker and 5,253,120 reader modeled paths—12,165,120 and 21,012,480 modeled ticks respectively—with approximately 254.6 million and 439.7 million radio-link calculations. Actual cache work must be recorded. The old F0 archive had 81,920 requests but only 9,238 misses; new-law visitation is unmeasured.
>
> Direct T/H should obtain their features from MemoC’s already-computed result, preserving feature equality. They should not perform redundant analytic helper work to manufacture an amortization advantage. Pure-student worker helper requests are then 102,400, with at most 14,336,000 helper links. The full reader conservatively permits 31,539,200 helper links for reconstruction.
>
> The corrected new native dense-slot count is **47,678,675**, including both parts of the B06 reset procedure. The old archive remains in its existing canonical location. Historical costs are retained: this purchase would bring B02–B06 plus this study to **14 fits, two calibrations and 2,539,560 native steps**, adding the estimated new CPU to the measured 3,323.067 seconds. Older B01 remains separate.
>
> The support estimate is the principal investment cost. Stopping remains defensible if Root judges that cost excessive. My preference is this bounded comparison because it tests a changed, constructive objective using a demonstrated asset, paid data, a strong ordinary learned control and direct-controller alternatives. It can produce useful positive or negative knowledge without asserting that the preceding failures have been explained.
>
> **MATERIAL_DISSENT: no — the corrected premise and current source-only boundary are sound. I recommend the revised two-fit comparison for Root’s investment decision; no native-improvement, entropy-cause or run-authorization claim is made.**

**DM response and Root selection.** I accept this revised target-package question and its
full limitations. It uses a retained constructive capability, whereas plain G
cloning did not itself justify the earlier purchase. My source objections about
H’s greater proxy expectation, intervention strength, fallback, finite fitting
and direct-baseline efficiency are retained in the original recommendation.
Root has now selected exactly two fits and the672-episode complete comparison,
with no new acquisition, calibration, teacher-success pilot or G-result gate.
This is B07, a new result-bearing study; B06 and no-S2/transfer dispositions stay
closed. A coherent learned gain may motivate later separate replication;
preservation-only, direct-only, adverse or uncertain outcomes end this purchase
without repair, retuning, aggregation or appended evaluation.

Root fixes both new fits to the SAME numerical soft-CE kernel: FP32 logits
cast to FP64, FP64 log_softmax and targets, weighted per-row sum then batch
mean, gradients returned to FP32 parameters. F0 remains the exact archive,
initialization, shuffle and exposure reference, but its old FP32 hard-CE kernel
differs. No pure hard-versus-soft-content attribution or third numerical-control
refit is authorized. All actor/helper/score/navigation/alias and private-CDF
contracts remain as specified above; flat T returns p.copy() exactly.

The selected operation uses configured local_linux after fresh actual-node
admission. Root reports recurrent remote GCC3.10.21 failure, including waiting
A01 during JSON traversal without Torch mapped; its cause is unresolved.
Local placement is an operation-specific choice, not a runtime diagnosis or
shared configuration change. Only required canonical F0 inputs will be staged
with byte hashes, transfer/disk cost recorded, and redundant staging removed
at closure. The complete frozen worker→reader chain and publication/cleanup
remain this DM’s responsibility. Prospective details and L0 follow before code.

<a id="b07-selected-contract"></a>
### B07 fixed prospective contract — S-prior stochastic-target development

Current published main `8ee48a5d21538caf647769d7f505dff0501590a5` includes the
completed G comparison. I read its complete original diagnosis, not only Root’s
summary. It retains S_L1−G J+.023431[+.012843,+.033524], S_L0’s unresolved J
but useful service/path differences, G’s secondary p10/quality/path/CPU tradeoffs,
and every student outage. G’s1845 physically changed saved-history holds and
proxy improvement did not establish a mean native upgrade over Q10. This changes
B07’s design use of background: keep G/Q05 alongside Q10 and P0/B*0, read all
quality/path/outage tradeoffs, and never promote improved score targets to a
native prediction already verified. The repeated empirical value of inherited
stochastic control remains constructive motivation, not an entropy diagnosis.
The independent review and Root’s explicit loss clarification above cover this
selected finite exploratory study; no duplicate selection critic/Pro is needed.

**Object and identities.** `UAV-STOCHASTIC-TARGET-DEVELOPMENT-B07`, owned package
`experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/`, initial
run tag `b07_stochastic_targets_a01`. Namespace search found no existing use of
the exact new eight-digit seed block before this entry. Fixed final worlds are
29710000..29710031, layout root29711001, master29711000, private tapes29711101
and29711102, constructor-only native seed29711205, bootstrap root29711991.
The two fits retain original F0 actor-constructor seed29514201 (copied P0 tensors,
zero count branch) and shuffle root29514101; their meanings are inherited, not
new stochastic training replicas. No endpoint selection or extra root is allowed.

Arms are ordered C,Q10,Q05,G,P0,Bstar0,F0,T,H,Tdirect,Hdirect. C is deterministic
once per world; the other ten run tape0 then tape1. Rotate this21-episode order
by the world’s index before collection, retaining labels regardless of order.
All use native N5/U50/all-on/H256 with the B06 explicit paired-layout reset,
4-tick holds, unchanged114-feature/helper/count adapter and fixed27 commands.
P0 is the original B02 S asset under that adapter; Bstar0 is its paid temperature2
law. F0 is the paid B06 endpoint. Learned T/H use temperature1. G and Q10/Q05
retain their existing ordinary laws. Direct T/H evaluate the original P0 on
MemoC’s already-paid lawful features, avoiding a redundant analytic helper.
Each program maintains its own episode/agent-private cache and navigation;
one new indexed private uniform is used at every stochastic decision, including
cache hits. Flat-score direct T returns the exact P0 probability array copy.
No policy receives global evaluator information, C’s future decisions or another
program’s realized history.

Both new fits use identical fixed F0 chunks/order, copied P0 initialization,
zero count branch, all34,843 trainable FP32 parameters, continuing fresh Adam,
original batch/epochs/clipping/shuffles and exactly8000 updates/4096000
presentations. Their targets differ only through the fixed T/H construction;
both use Root’s same FP64 soft-CE kernel. Frozen parent probabilities are computed
once per archived context and shared across targets, never from a changing
learner. No new native acquisition, labels, calibration or hard-control refit.
Recorded F0 data were adaptively acquired by F0’s greedy predecessors; the new
comparison is conditional on that complete static archive. Its original FP32
hard CE remains a numerical difference from the new soft kernel.

**Outcome and inference.** Primary is learned T−learned H mean native J. For
all55 unique pairwise contrasts among11 programs, average the two tapes within
each of32 worlds (C once), retain the signed32-vector and descriptive percentile
95% paired-world bootstrap with10000 resamples, root29711991, reusing one index
matrix across contrasts/metrics. No pooled training inference, multiplicity-adjusted
confirmation, equivalence rule or unpriced deployment utility is claimed. Read
P0/Bstar0/F0/direct T/direct H/G/Q10/Q05/C comparisons, service/quality/p10/minimum,
zero-service ticks/worlds, path, boundaries/zero displacement, all adverse worlds
and complete timing/cache work together. Beating damaged F0 alone is insufficient.

Read all targets’ displacement, entropy, local-score response, flat-score exposure
and support; original and final weights/gradients/count-branch activation; complete
70-epoch optimization traces per fit; and one full frozen-endpoint pass over all
81920 rows for each learned model. Those training-row errors are not held-out
generalization. Direct-target and learned native trajectories already test the
complete packages; no C/P shadows on learned histories, optimizer replay or
counterfactual native branches are added. TV and local-score identities describe
the targets, not learned or native guarantees. Scope/cost and stop branches are
exactly those preserved above. No automatic extra fit, retuning, aggregation,
evaluation or repeated reader after a completed purchase.

**Inputs, local placement and full reading.** Before launch, stage exactly256
canonical F0 raw files, its three phase datasets, original P0 and final F0 assets,
plus compact source-bound F0 metadata. The old source summary’s recorded hash
must match before extracting its selected metadata; every staged file is rehashed.
Existing original evidence stays canonical on the remote node; local staging is
an explicitly priced temporary consumption copy, not a new retention archive.
Raw/data/assets alone total approximately25.8MB (metadata additional); exact
bytes, allocated disk, transfer wall/CPU and paths will be recorded. No remote
worker is restarted and sparse snapshots are not assumed to hydrate these inputs.
The new admitted source refers to the declared local staging root by absolute
path and digest; staging is removed only after the complete new reader and all
live consumers finish, with required old evidence preserved remotely.

The configured local scientific runtime is Python3.10.20/Clang22.1.3,
NumPy1.26.3/Torch2.7.0+cpu; one Torch/inter-op/BLAS thread and deterministic
algorithms. This differs from old remote Python3.10.21/GCC/Torch2.7.0+cu118;
all new arms share the local runtime and retain old exact asset bytes. No
cross-runtime bit identity of new execution is assumed. Existing operations
are already reconciled closed; admission must check fresh local memory and
concurrent consumers immediately before launch. Preserve the remote failure
facts without treating local success as a root-cause test.

The chain includes target creation, two fits, all672 new episodes and exactly
one complete independent saved-data reader. It reconstructs all81920 old C,
helper/feature/nav/target records and all928 old+new files/237568saved native
ticks, every actual final C/neural/direct probability and private-CDF law,
all endpoint diagnostics, source/asset/data/shuffle identities and complete
native reductions. It makes no native transition or optimizer update. Reader
cost includes194560 C requests and389120 neural rows; deterministic cache reuse
changes actual calculations, never row coverage. The exact source-derived
request/link/target counts,10–30CPU-minute and6–10support-hour estimates above
remain binding planning scope, not runtime cutoffs. Actual work and failure
exposure are retained. Full imports, transfer, readback and publication are
included or explicitly separately timed, never silently omitted.

<a id="b07-l0"></a>
### L0 — one source-bound static-data target comparison and complete reader

Implement the fixed B07 object in its owned package/tests, with a compact pinned
F0 input manifest, hash-checked staged inputs, fresh admitted entry, partial-failure
records, raw outputs, two phase-trained actors and full reader. Import unchanged
B02/B06/G source helpers; do not edit their frozen files, environment, launcher,
shared controls or other directions. Direction NOTES/RESEARCH and Git index are
DM-owned. One bounded Implementer may own only `targets.py` and its matching
`test_targets.py`: pure T/H numerical laws plus the selected shared soft-CE loss.
The DM owns protocol, assets/staging, policy/collector, trainer integration,
reader, entry and remaining tests, and reviews/accepts the Implementer result.
No helper may edit the notebook, stage/commit, run production inputs or launch.

Checks use synthetic arrays/models/environments only: exact flat-T identity,
parent zero-support and valid nonflat/tied/extreme-lawful score cases, scalar
independent target arithmetic, one-hot and identical-target FP64 loss/gradient
agreement, count-zero branch, unchanged actor weights, independent RNG addresses,
cache-hit fresh sampling/aliases, saved target/raw/source corruption refusal and
mocked-admission end-to-end production call ordering. Production data are not
queried by tests. No extra native fixture is purchased. Independent engineering
review covers numeric loss/target/RNG, static archive binding, full reader and
admission before one published launch. After acceptance use the original status
handle and deterministic observer through full result reading; no duplicate run.

<a id="b07-implementation-and-review"></a>
### B07 implementation, required-input staging and prelaunch checks

The complete original selection advice, fixed numerical loss and prospective L0
were preserved and the selected active standing published in `66a62437765dac8be213fa2e31342e8f84567312`
before any fit or native query. The named bounded Implementer supplied only the
pure T/H law/loss and, in a second sequential task, static-data phase training,
each with synthetic tests. I read and accepted both implementations. The DM
implemented the remaining source binding, target construction, policy/collector,
training integration, native/archive reader and full endpoint diagnostics in the
owned B07 package; all frozen B02/B06/G files remain unchanged.

Required local consumption staging is
`temp/directions/uav_fleet_adaptation/b07_inputs/`, containing exactly261 source
files:256F0 raw trajectories, three F0 phase datasets, original P0 and final F0.
All were individually rehashed against metadata extracted only after verifying
the original summary SHA-256 `0d1fc9af270a376f3836fe256cee93c31bc698ae9cd131339d80960ee92d4073`.
Source-bound selected metadata is `b07_stochastic_targets/f0_inputs.json`,812802bytes,
SHA-256 `31b0762abda4348179851ba09bc9beb9d14d6d1eb876a10b30a08f18dc07c71c`.
The261 input files total25750748logical bytes. Staging plus file list occupied
26324992allocated bytes before its compact receipt; transfer/verification took
3.517219wall-s, .039637local parent CPU-s and .441605local child CPU-s. Remote
metadata extraction used .059041CPU-s/.058546wall-s. No policy, C/helper, target,
optimizer or native outcome query was made during staging. The original remote
canonical files remain in place; this consumption copy is a closure deletion
target after all readers finish, not a new retention archive.

The first complete synthetic B07 suite passed136tests in3.16s on the configured
local CPU runtime, with all scratch under the owned temporary directory. It
covers pure numerical laws/gradients, continuing Adam/full batches/count-zero,
all11 programs' artificial complete saved-history reconstruction, corruption
refusal for native and direct-law records, cache-hit fresh private sampling,
direct C-feature reuse, external path/hash refusal, and mocked admission→worker→
reader ordering. No production input was queried by these tests. A source-only
hash check matched all48 bound old/new executable and metadata files. Local
Adam exposes `decoupled_weight_decay=False`; I added explicit validation of that
unchanged default to both training and saved-state reading, with a refusal test.
Its targeted check and the independent high-risk engineering review follow.
Actual resource admission and all result execution remain ahead.

The targeted Adam/read-boundary suite passed45tests in2.40s after the explicit
unchanged-default check. Independent `hmasd-reviewer` inspected all14new modules,
five test files, the source manifest and all29 inherited source hashes; its
independent full synthetic check passed137tests in2.92s. It found two medium
reader lifecycle issues: a check-then-create reservation race could admit two
readers, and an exception could discard completed/partial C/helper cache-work
counts kept only in local variables. I accepted both findings before launch.
The reader now acquires `reading-progress.json` with exclusive creation before
it owns any failure record. Live per-agent C/helper counters are attached before
reconstruction; a `finally` fold preserves each completed or interrupted prefix
once, and failed readings retain actual cache misses, paths, modeled ticks and
power links. Progress also retains the current work ledger. Added artificial
visible-user cases cover nonflat direct laws, and fault injections test both
archive and final-reader accounting. The focused repaired audit/boundary suite
passed49tests in2.61s; the independent Reviewer repeated it at49passed/2.63s.
No production input/model/native query was used for these checks.

Original engineering final disposition:
> No material finding remains in the B07 implementation.
>
> Both medium findings are resolved:
>
> - `read.py:109` exclusively reserves the reader before failure-record ownership; a competing invocation cannot publish or overwrite its results.
> - `audit.py:24` preserves live C/helper counters and folds completed or interrupted work exactly once. `read.py` persists those totals on failure.
>
> Independent checks: earlier full suite **137 passed**; repaired audit/boundary suite **49 passed in 2.63s**, including concurrent reservation, interrupted archive/final replay, and all 11 arms with visible-user synthetic inputs.
>
> Limits: no production checkpoint queries, native execution, training, or full production reader run. Review was read-only.

I accept this engineering disposition and the bounded implementations. The exact
owned inputs will now be published before the one fresh local admission. The
selected scientific question, target formula, loss, phase exposure, native panel,
full reading and stop branches are unchanged. This is launch readiness only;
there is still no B07 scientific result.


<a id="b07-a01-operation"></a>
### B07 accepted local worker→complete-reader operation

At2026-10-01T01:50:42Z the one B07 chain was admitted from published
`c2b2cd27276e49458b18ca69216b3525f281ea47`; its exact native identities, source
snapshot, argv and operation reference are retained in
[runs/uav_fleet_adaptation/b07_stochastic_targets_a01/launch-manifest.json](../../../../runs/uav_fleet_adaptation/b07_stochastic_targets_a01/launch-manifest.json).
Fresh actual-node available/effective memory was6665248768bytes, above the
4294967296byte floor. Current canonical/published pause, active direction and
unchanged native-child lead passed admission. This operation-specific local
choice follows the already-preserved remote-runtime failure evidence; it does
not diagnose that failure or change shared runtime configuration.

The same-session deterministic observer adopted both running native identities
with a consistent accepted claim and zero observation errors at01:50:56Z. Its
state is generation32, job`b07-a01`, after consuming the prior completed/stopped
generation30 and rearming31. The native child remains active through collection
and scientific reading; registration is not a future-wake guarantee. The
unchanged chain includes both fits,672native episodes and the one full reader.
This entry records acceptance only, not a completed result.


<a id="b07-complete-reading"></a>
### B07 complete reading — a fitted score tilt without demonstrated native improvement

The accepted source`c2b2cd27276e49458b18ca69216b3525f281ea47` completed at
2026-10-01T02:00:04.080027Z with exit0, consistent terminal records and both
native identities absent. The fixed reader is`VERIFIED`; it was not repeated.
The detached observer reported READY with zero probe errors. Its native-child
queue delivery returned`-32600`(direct App input to subagents unsupported), while
the still-active same-session deterministic watch delivered the terminal facts.
Generation32/event`58017aca88ab5bcaca916563`/wake
`84761055-8490-417b-9c87-cac7e9738b91` were drained and consumed by rearm33;
observation is now stopped. This queue limitation caused no loss of observation
or duplicate scientific effect.

**Evidence and coverage.** The complete
[reading](../../../../runs/uav_fleet_adaptation/b07_stochastic_targets_a01/reading.json)
is2259473bytes, SHA-256
`872153b4eea35738c35a2b3edfdd644ddc8b0201a96b83cd423474f743ad06ff`.
Canonical`summary.json` is5121319bytes, SHA-256
`0a637fb56f6f80efb9e59900337390b6badbbf1f881248505fee187a4446dc64`,
at`/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b07_stochastic_targets_a01/`
on configured`local_linux`. It retains all672 episode identities/metrics/byte
bindings and both complete70-epoch traces. Its bulk stays at that one durable
location; the complete compact reading/config/native receipts are published.
All inherited assets and old canonical remote records remain unchanged.

Both fits completed8000updates/4096000presentations each with original F0
row order and shuffles, a fresh continuing Adam and the same selected FP64
soft-CE kernel. Total16000updates/8192000presentations,163840target rows and
81920frozen P0 forwards; no new acquisition or calibration. All672H256
episodes completed172032native steps/860160UAV ticks,215040policy decisions
and204800private indexed uniforms. The complete reader reconstructed928files,
237568saved ticks,296960decision rows,all81920old C/feature/target contexts,
all final actual laws and all163840 learned-endpoint training rows. It performed
194560C requests,184320helper requests and389120actor rows, with zero native
steps or optimizer replay. Archive C maximum absolute score difference was
6.35e-16; target, final score and final logit reconstruction differences were0.
Saved phase/Adam identities, finite tensors, original shuffle streams and all
paid update counters passed.

**Native result.** These are conditional descriptive95% paired-world bootstrap
intervals:32worlds, two tapes averaged within each world(C once), one fixed
parent/data instance. They are neither independent training replications nor
multiple-comparison-controlled confirmation. Every signed world vector and all
55contrasts/27metrics remain in the complete reading.

| Comparison | Mean J difference | Descriptive95% interval | Positive/negative worlds |
|---|---:|---|---:|
| T-H | -0.006345146 | [-0.014699171,+0.002065722] | 10/22 |
| T-P0 | +0.000060165 | [-0.005529060,+0.005771699] | 14/18 |
| H-P0 | +0.006405312 | [-0.002012054,+0.015032668] | 18/14 |
| T-Bstar0 | -0.017761984 | [-0.027304868,-0.009488492] | 7/25 |
| H-Bstar0 | -0.011416838 | [-0.019192730,-0.003473902] | 10/22 |
| T-F0 | +0.002580282 | [-0.007270777,+0.013326236] | 15/17 |
| H-F0 | +0.008925428 | [-0.003380136,+0.021389787] | 17/15 |
| Tdirect-P0 | -0.001921870 | [-0.007663945,+0.003332369] | 14/18 |
| Hdirect-P0 | +0.007329361 | [+0.000754088,+0.014607773] | 17/15 |
| Hdirect-Tdirect | +0.009251231 | [+0.002655882,+0.016335161] | 19/13 |
| Tdirect-T | -0.001982036 | [-0.007429977,+0.002857813] | 15/17 |
| Hdirect-H | +0.000924049 | [-0.007089281,+0.008864681] | 18/14 |
| Bstar0-P0 | +0.017822150 | [+0.009240309,+0.028302560] | 24/8 |
| P0-G | +0.011886889 | [-0.000287457,+0.025092126] | 18/14 |
| T-G | +0.011947055 | [-0.001087319,+0.025609096] | 17/15 |
| H-G | +0.018292201 | [+0.005508438,+0.031137947] | 22/10 |
| G-Q10 | +0.007832861 | [-0.003797272,+0.018391520] | 22/10 |
| G-Q05 | +0.011085048 | [+0.003450854,+0.019236957] | 16/16 |

T−H's point favors H but its interval crosses zero. T−P0 has essentially
no mean increment on this panel, without an equivalence claim; H−P0 is also
unresolved. Both new learners fall below the paid Bstar0 calibration in mean
J and service. No soft-over-hard rescue is established: T−F0 and H−F0 remain
unresolved, and F0−P0 itself is−.002520[−.014408,+.008245] here. B06's adverse
F evidence remains historical evidence, not a premise that every new panel
must reproduce the same loss.

| Program | Mean J | Mean service | Mean served-user quality | Service-p10 | Mean episode minimum | Path m/UAV | CPU s/episode |
|---|---:|---:|---:|---:|---:|---:|---:|
| C | 0.331878 | 19.602905 | 0.191456 | 18.906250 | 11.000000 | 2509.397521 | 0.203809 |
| Q10 | 0.357041 | 21.522339 | 0.185761 | 16.367188 | 9.687500 | 3977.536064 | 0.303773 |
| Q05 | 0.353789 | 21.202881 | 0.189829 | 17.585938 | 10.406250 | 3413.356846 | 0.272968 |
| G | 0.364874 | 21.916138 | 0.193494 | 18.601562 | 10.718750 | 3729.640525 | 0.285771 |
| P0 | 0.376761 | 22.996765 | 0.182687 | 20.156250 | 10.843750 | 3018.499194 | 0.332256 |
| Bstar0 | 0.394583 | 24.387695 | 0.177185 | 20.000000 | 10.218750 | 4397.489235 | 0.393971 |
| F0 | 0.374241 | 22.766418 | 0.185037 | 19.679688 | 10.703125 | 2826.389233 | 0.309357 |
| T | 0.376821 | 22.972656 | 0.184013 | 20.070312 | 10.781250 | 2848.050704 | 0.325160 |
| H | 0.383166 | 23.482361 | 0.181377 | 20.289062 | 10.609375 | 3154.041000 | 0.332006 |
| Tdirect | 0.374839 | 22.782410 | 0.186284 | 20.109375 | 10.812500 | 2948.641431 | 0.358366 |
| Hdirect | 0.384090 | 23.477356 | 0.184691 | 19.992188 | 10.984375 | 3037.240323 | 0.363980 |

T−Bstar0 loses1.415039 mean users while gaining.006829quality,
.5625mean episode minimum and1549.439m less path; p10+.0703125 is unresolved.
H−Bstar0 loses.905334users while gaining.004193quality and1243.448m less
path; its p10/minimum changes are unresolved. Neither Bstar0 nor the new fits
therefore Pareto-dominate every measured consequence. No physical travel or
latency utility was selected to overturn the native-J comparison. Bstar0−P0's
+.017822J/+1.390930users trades−.005503quality,−.625mean minimum and
+1378.990m path; do not silently adopt a new default from mean J alone.

The direct H law gives a small positive Hdirect−P0 native J comparison,
+.007329[+.000754,+.014608], but15/32worlds lose and Hdirect remains below
Bstar0. Direct H exceeds direct T by+.009251J[+.002656,+.016335], whereas
direct T−P0 is unresolved. This weakens a story that only finite fitting hid
a demonstrated useful T target. Hdirect−H J is unresolved, not proof that
compression preserves the direct law. H's mean minimum is.375 lower than
Hdirect's[−.703125,−.046875]. Direct H/T cost approximately.0320/.0332 more
CPU-s/episode than their learned counterparts; native uncertainty and all
training/target/audit cost remain, so no net amortization claim follows.

There are zero total-service outage ticks/episodes in this672episode panel.
This is a finite-panel fact, not a reliability or individual-user-continuity
claim; all earlier student/calibration outages remain adverse evidence. All
worlds are retained. T loses against P0 in18/32worlds, worst world29710018
(−.039087J); H loses in14/32, worst29710003(−.050376). Against Bstar0,
T loses25/32 and H22/32; both largest losses are world29710022 at
−.112855/−.056451J. T−H's worst world29710005 loses.058604J. These
losses are part of the full comparison, not post-hoc exclusion or a subgroup
adoption rule. G−Q10 again has an unresolved J interval but better quality,
p10 and minimum; G−Q05 has a positive conditional J interval while using
more path/CPU. P0−G J remains unresolved here, with better service/p10/path
and lower quality, preserving the stronger ordinary comparator.

**Target and learning activation.** Of81920fixed rows(9238unique feature rows),
6176have flat scores/fallback: T is exactly P0 there. T differs from P0 on
75744rows with mean TV.007284786, maximum.070071796 and674modal changes.
H differs on all81920rows, mean TV.040519221, maximum.1 and2638modal
changes. Both have no floating zero-probability categories on this archive.
Thus T is a small active intervention, not nonactivation. H is a materially
stronger intervention; this is a target-package comparison, not isolated full
score information, entropy or fallback value. Target entropy changes are
−.007658524(T) and+.026815702(H); proxy changes are+.000149082 and
+.000372820, with H−T proxy nonnegative as predicted. The proxy is not
native continuation value.

All16000optimizer updates had nonzero full-network gradients; the N5-zero
count branch had zero gradients/moments/movement throughout. T changed26504
parameters(L2movement1.628931); H changed26941(L2=11.958820). Every
phase's stream diagnostics were read, with no checkpoint selection: T's
first→last paid-epoch CE is.55992054→.55913593,.57510369→.57496818,
.57358625→.57360857 across phases; H is.59702414→.58460161,
.63131073→.62023549,.63424872→.62475708. The changing phase datasets
and pre-update streams are not a held-out or common-endpoint learning curve.

The paid all-row endpoint pass finds T's own-target mean KL=.000188220,
TV=.004802228 and99.4141%target-mode agreement; H's are.016693858,
.030003910 and98.1177%. T/H decoded mean TV to P0 is.008733830/.039779983,
but maximum is.274024/.719853 even on these training rows, explicitly
violating any proposed learned-policy TV≤.1 guarantee. Endpoint proxy
values .106810014/.106842337 exceed P0's .106668873 on the archive,
without implying a native gain. T learns its small target closely in average
training-distribution metrics; wholesale nonlearning is not a good explanation
for its missing native increment. Residual rare-row/off-data error remains
unmeasured as a causal explanation. H has more fitting residual, but the
direct H comparison is already paid evidence rather than a reason to append
unselected optimization.

All deployed programs retain the original27categorical aliases and one fresh
private uniform per actual stochastic decision, including cache hits. Neural
positive-probability categories may receive zero mass on the finite53-bit CDF
grid(P0:5634, Bstar0:0,F0:41451,T:5756,H:2496,Tdirect:6257,Hdirect:6084
category-context entries); no category merger or changed decoder was used.
Modal versus physical departures, clipping, boundary counts, fallback and
cache work are retained for every program. They do not identify a causal
entropy or aliasing explanation of the native comparison.

**Complete measured cost.** Target construction costs21.312861CPU-s/21.474069wall-s.
T's fresh-Adam three-phase fit including checkpoint serialization costs
31.986498CPU-s/32.392155wall-s; H costs30.789313/30.965046. The complete
worker costs306.972346CPU-s/308.207649wall-s, reader253.261470/253.317627,
and enclosing import/worker/reader chain560.463227/561.756339. Timing scopes
exclude final write/admission/staging/support where specified; no summing of
nested timings as additional scientific cost. Observed process peak RSS is
593324KiB across the enclosing process, not an isolated reader increment.
Configured Python3.10.20/Clang22.1.3/NumPy1.26.3/Torch2.7.0+cpu uses one
Torch/inter-op/BLAS thread and deterministic algorithms. Local success does
not identify the earlier remote runtime fault.

Worker actual cache work is59959full-C misses/1618893candidate paths/
6475572modeled ticks, plus61456helper misses. There are84343deployed
neural rows and81920archive P0 rows, outside the8192000training presentations.
Worker controller power links28544558 plus47678675native dense slots total
76223233. The independent reader pays69197C misses/1868319paths/7473276
modeled ticks,70694helper misses and31984432controller links; its389120
neural rows include full163840endpoint diagnostics. Direct T/H correctly reuse
C features rather than paying a redundant helper. Requested work and actual
cache savings remain separately visible. Transfer/metadata timings and the
26324992byte temporary staging allocation were recorded before launch.
Actual combined chain CPU is9.341minutes, below the10–30minute planning
range; engineering/review/publication active labor is not fully metered and
is not assigned the forecast6–10hours as an observation. Cumulative B02–B07
remains14fits+2paid calibrations/2539560native steps and approximately
3883.530measured chain CPU-s across their different scopes/hosts, with the
earlier B01 and all support costs separately incurred.

Unique new evidence is672raw NPZs/317776140logical bytes, six phase/Adam
checkpoints/2568102bytes, one target archive/7924148bytes and two endpoint
archives/3333601bytes, at the canonical local run above. Existing summary
and reading bind every byte hash; no whole-tree backup or second retention
copy is needed. All six phase artifacts remain necessary to the selected
saved-optimizer audit, not redundant final-checkpoint duplicates. Cleanup
will remove the verified old-input consumption copy and disposable source/test
material only after live consumers finish.

**Provisional interpretation pending independent diagnosis.** The selected
score-prior target is active and closely learnable on this archive, but neither
its direct law nor fitted endpoint establishes a native increment over P0;
the fit does not beat the simpler H package or Bstar0. This lowers investment
priority for unchanged T without refuting score targets in general. The
conditional direct-H positive and retained P0/Bstar0 capabilities remain useful
evidence; H's fitted native increment and preservation relative to direct H
are unresolved. No cause of earlier PPO/imitation failures is identified.
The wider question of useful learned development remains open. Independent
ResearchCritic now reconstructs the original saved evidence in a separate
context; final direction disposition follows that reading. No extra query,
fit, calibration or evaluation is selected by this result.

Editorial count correction: the complete reading contains25native metric series per
contrast;27 is the command-category count. All55contrasts and every declared
metric/vector were retained and read. No experimental exposure or result changes.

Cost-interpretation detail from the accepted direct-policy source: each direct
decision calls the shared target constructor for both T and H and deploys its
assigned vector. The81920direct target-vector calculations are explicitly
counted. Hdirect therefore also computes an unused T score tilt; Tdirect
constructs an unused H vector. Actual laws and all native comparisons remain
correct, and no extra C/helper or actor query is hidden. The observed direct
CPU differences describe this implementation, not a minimal possible direct
baseline. This further limits any net-amortization claim; no such claim is
made, and no post-result repair or repeat is selected. The independent
Scientific Reviewer receives this source fact before its final disposition.


<a id="b07-original-independent-result-review"></a>
### B07 original independent ResearchCritic answer

A new configured`hmasd-research-critic` received the actual B07 question, fixed
T/H definitions, loss/exposure and full original source/output identities in a
separate context with no DM/Root conversation inheritance. It was told to
reconstruct original results before reading the complete selection Oracle and
DM interpretations; no production model/controller/native query or repeat
reader was authorized. Root's no-automatic-extension rule was disclosed, so
this is not an allocation-blinded review. The reviewer independently reproduced
all saved episode-summary reductions, then read prior positive/adverse sources
and the complete original advice. Its full original final answer follows.

> **Recommend ending this B07 target-development purchase, retaining the inherited policies and the narrow Hdirect positive, with no additional fit, retuning or evaluation selected.** B07 demonstrates good average fitting of a small score tilt on the paid archive. It does not establish useful learned development beyond P0 and ordinary paid calibration.
>
> I reconstructed the saved results before reading the original selection advice and the DM’s new interpretation. No DM/Root conversation history was inherited. The assignment did disclose Root’s stopping preference, so this was a separate-context review, not an allocation-blinded review.
>
> The consequential results are:
>
> | Comparison | Mean ΔJ | Descriptive 95% world interval |
> |---|---:|---:|
> | T−H, primary | −.006345 | [−.014699, +.002066] |
> | T−P0 | +.000060 | [−.005529, +.005772] |
> | H−P0 | +.006405 | [−.002012, +.015033] |
> | T−Bstar0 | −.017762 | [−.027305, −.009488] |
> | H−Bstar0 | −.011417 | [−.019193, −.003474] |
> | Tdirect−P0 | −.001922 | [−.007664, +.003332] |
> | Hdirect−P0 | +.007329 | [+.000754, +.014608] |
> | Hdirect−Bstar0 | −.010493 | [−.018725, −.004044] |
> | Hdirect−H | +.000924 | [−.007089, +.008865] |
>
> These intervals describe fixed policies on 32 worlds, with two tapes averaged within each world. They do not supply independent training replication, equivalence or multiplicity-controlled confirmation. [Complete B07 evidence](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b07_stochastic_targets_a01/reading.json).
>
> T−H favors H in 22 of 32 worlds, although its interval spans zero. T’s essentially unchanged mean relative to P0 is a preservation pattern, not proof of equivalence. H’s increment over P0 remains unresolved. Neither learner clears the competent Bstar0 comparison; beating C or Q10 therefore cannot establish the requested development benefit. Even improvement over F0 is unresolved, and F0−P0 is only −.002520 with an interval crossing zero on this panel. The earlier F deterioration should remain historical evidence, not an assumed result of every subsequent panel.
>
> The complete components prevent a blanket ranking. Relative to Bstar0, T loses 1.415 mean served users but gains .006829 quality, .5625 mean episode minimum and 1,549 m less travel per UAV. H loses .905 users while gaining .004193 quality and 1,243 m less travel. Their p10 differences remain unresolved. Bstar0 itself gains 1.391 mean users over P0 while lowering quality and episode minimum and adding 1,379 m of travel. It is the stronger native-J comparator here, not an automatically preferable deployment default.
>
> There are no total-service outages in these 672 episodes. That does not erase earlier outages or establish individual-user continuity. Adverse worlds also remain substantial: T−P0 reaches −.039087 J in world 29710018; H−P0 reaches −.050376 in 29710003. Against Bstar0, both suffer their largest losses in 29710022: −.112855 for T and −.056451 for H. Those losses remain in the complete comparison.
>
> The supported diagnosis separates three questions:
>
> - **Opportunity remains.** P0 again exceeds Q10 on J by +.019720, and Bstar0 improves on P0 by +.017822 on this panel. Hdirect supplies a smaller positive over P0. These are useful conditional capabilities. They do not show that score tilting is the missing development mechanism.
> - **Finite archive fitting occurred.** Both fits completed 8,000 updates with nonzero full-network gradients and substantial parameter movement. T’s mean own-target KL is .000188 and TV .004802; H’s are .016694 and .030004. Wholesale failure to learn is an inadequate explanation for T’s result. These are training-distribution measurements, however, not deployment fidelity or population learnability.
> - **Complete added value was not established.** T supplies no demonstrated increment over reuse, H or Bstar0. H supplies an unresolved learned increment over P0 and loses J/service to Bstar0. Lower travel remains a measured tradeoff without a selected utility that makes it a successful development result.
>
> The strongest simpler explanation is that this recipe mainly preserves an already useful stochastic policy, while the additional local-score guidance supplies little demonstrated native value. T’s actual target displacement is small: mean TV from P0 is .007285, versus .040519 for H. T changes 674 of 81,920 target modes; H changes 2,638. T is exactly P0 on the 6,176 flat-score rows and differs on the remaining 75,744 rows. This is a broadly nonzero but modest intervention—not complete nonactivation, and not evidence that a strong score intervention actively harmed native performance.
>
> Both targets improve their local proxy, with H’s increase larger as predicted. T slightly reduces target entropy; H increases it. Their intervention strength, fallback behavior and distribution changes differ. Consequently, the result identifies neither a full-score advantage nor an entropy mechanism. C’s score remains a local proxy rather than native continuation value.
>
> An optimization-only rescue is particularly weak for T: **the exact direct T law also fails to establish improvement over P0**. That does not prove that approximation error is irrelevant, but it removes the premise that a demonstrated useful T controller was simply lost during fitting. H has larger fitting residual and still-improving stream loss, so additional optimization might change it. Yet exact Hdirect already trails Bstar0; fitting it more closely is not automatically a useful next purchase. Moreover, Hdirect−H uncertainty is not proof of successful amortization: learned H’s mean episode minimum is .375 lower, with a descriptive interval excluding zero.
>
> The learned-policy TV bound also cannot be inferred from the target construction. Maximum training-row TV from P0 reaches .274 for learned T and .720 for learned H. Good mean archive fit does not provide a uniform preservation guarantee. The zero count branch is expected under these N5 inputs; B07 supplies no new count-learning evidence. Recorded sampled physical departures show active stochastic deployment, but they are departures from each policy’s own mode—not counts of causal T-versus-P0 interventions.
>
> The strongest constructive positive is **ordinary H mixing**, not the proposed score tilt. Hdirect−P0 is +.007329 J, and Hdirect−Tdirect is +.009251 with a positive descriptive interval. Hdirect retains approximately P0’s mean travel and has better quality, minimum service and shorter travel than Bstar0, while sacrificing mean J/service. Fifteen of 32 worlds still lose against P0, and deployment costs more. This is worth preserving as a conditional controller result. It does not yet establish a useful learned upgrade or justify converting a secondary positive into an automatic replication programme.
>
> The prior evidence supports this distinction. I checked the original B02/B03 competence results, B04 reward-continuation losses, B05 consequence-head comparisons and outage records, B06 count/parent comparisons, and the original G comparison. Useful inherited behavior survives across those studies; the tested additions repeatedly fail to establish a clear increment over retained alternatives. B07 adds a specific boundary: changing the supervised target can preserve competence with good average archive fit without producing additional native value. It does not diagnose a common cause of PPO, consequence-head and imitation outcomes.
>
> **The next worthwhile purchase now is none.** The paid direct and learned comparisons already distinguish the consequential branches:
>
> - A coherent learned gain over P0/Bstar0 and H would have supported consideration of independent replication. It did not occur.
> - A useful direct-T gain lost by the learner would have strengthened an archive/fitting hypothesis. It did not occur.
> - The observed preservation pattern and ordinary Hdirect positive support retaining assets and ending this purchase.
>
> More episodes would improve conditional precision, not create training replication. More T optimization lacks a demonstrated useful direct target. A stronger tilt would be a new conjecture, not an evidenced repair. A future low-travel use case could justify a newly specified comparison retaining P0, Bstar0 and competent ordinary alternatives under the same utility; no such use case has been selected here. The broader development question remains open without obliging another attempt.
>
> The bill is material even though execution was inexpensive. B07 used two fits, 16,000 updates, 8,192,000 presentations and 172,032 new native steps. Fit wall times were 32.392 and 30.965 seconds; the complete worker/reader chain was **561.756 wall-seconds and 560.463 CPU-seconds**. Target construction, evaluation and the full reader dominate the difference between fit-only and complete cost. Staging added 3.517 wall-seconds. Engineering, review, publication and cleanup labor remain incompletely metered; the forecast 6–10 support hours is not an observed cost. B02–B07 total 14 fits, two calibrations, 2,539,560 native steps and approximately 3,883.530 measured chain CPU-seconds across differing scopes/hosts, with older B01 and support separately incurred. The learners save about .032–.033 CPU-seconds per episode against their direct counterparts, but uncertain native preservation and incurred training costs prevent a net amortization claim.
>
> My independent checks covered the supplied reading/summary hashes, all 48 source hashes against the launch commit and current files, frozen parent/F0 identities, shared initialization/shuffles, terminal receipts, and per-world exogenous-layout/initial-state bindings. Reducing all 672 episode-summary rows reproduced all 11 levels and all 55 contrasts across 25 metrics, including their 32-world vectors, to numerical rounding. I inspected target statistics, complete epoch curves and update counts, endpoint diagnostics, activation summaries and consequential adverse episode records.
>
> I relied on the accepted complete reader for bulk trajectory, feature, probability and saved-optimizer reconstruction. I did not reload production models, repeat C/helper queries, replay optimization or rerun trajectories. No engineering issue emerged requiring another review.
>
> The DM’s published provisional interpretation is supported. The main correction is an explicit final investment disposition: retain these capabilities and tradeoffs, end B07, and make no broader failure or default-adoption claim.
>
> **MATERIAL_DISSENT: no — the direct and learned evidence supports ending this purchase without automatic extension; it does not support expanded claims of useful score-tilt development or general unlearnability.**

<a id="b07-independent-disposition"></a>
### DM response and final B07 disposition

I read and accept the complete independent recommendation, including the
conditional Hdirect positive, all component tradeoffs, substantial adverse
worlds and the limit on its review scope. There is no material scientific
dissent. Its numerical reductions agree with the original complete reader
and my reading above. The causal interpretation remains limited: a closely
fitted modest target does not imply useful native improvement, and a negative
or unresolved complete-package comparison does not identify entropy,
representation, or a shared cause of earlier learning outcomes.

The active idea ends here. I retain P0, the paid Bstar0 option, all earlier
assets/adverses and the new ordinary Hdirect evidence. I select no further
fit, target-strength change, data aggregation, calibration, longer optimization,
new episode panel or exact reader repeat. This is the preservation/uncertain
branch of the selected purchase, with adverse mean-J comparisons to Bstar0;
it is not a failure to execute or an empirical impossibility claim. Hdirect's
secondary positive does not create a new default or automatic replication.
Bstar0's stronger J/service still trades quality, episode minimum and travel.
T/H lower path does not acquire a post-hoc utility or a successful development
claim. The unchanged T development recipe has lost its current investment
rationale; the broader question of useful learned development remains open.

The previously documented direct-constructor cost limit also qualifies the
reviewer's measured CPU statement: both direct programs compute both target
vectors before selecting one. Their measured runtime is honest complete
implementation cost, not a minimal direct baseline. This changes no native
value or stopping judgment and supplies no net-amortization claim or repair
purchase. The reviewer was sent this factual detail before its final message;
its original answer above is preserved without inserting my qualifier into it.

The final direction standing is reserve with no producer, unread scientific
result, pending advice or selected successor. This is not a fabricated
dependency on an owner decision or recurring check. A future low-travel
contract or materially different hypothesis would require a concrete question,
competent same-utility alternatives and a separately selected comparison.
Root retains cross-question selection under the native-child assignment; no
in-question result publication or closure waits for a new acknowledgment.
The complete evidence was published at`e1275959e1e117c433b0279c1ae1bc26ca94f284`;
this disposition, directly affected shared understanding and cleanup facts
complete the present boundary.


<a id="b07-final-cleanup"></a>
### B07 closure cleanup and retained evidence

All producers and the single reader are reconciled terminal, the same-session
observer is stopped with its READY event consumed, and the independent
Scientific Reviewer has returned its complete answer. No live consumer uses
the old-input consumption copy or temporary/test caches. Before deleting that
copy I rehashed all261 original canonical remote files at
`/home/wu/projects/HMASD/` against the existing source/staging manifest:
25750748bytes matched, using .017114remote CPU-s/.683222enclosing wall-s.
This is filesystem identity verification, not a new model/native query.
The new canonical B07 result is entirely outside its disposable source snapshot
and remains at the recorded local run path, with published complete readings
and byte locators.

The first maintained snapshot-collector preview refused an elevated read-only
process scan because process1396736changed during reference inspection. No
target was deleted under that refusal. A fresh preview then established
terminal identities, no live references, clean source and durable reachability
from main; the maintained exact-target apply removed the snapshot and its Git
worktree administration. A separate maintained read-only process-reference
scan returned no references for every scratch/cache target below. No claim,
manifest, result output, branch, other direction or source code was removed.

| Actual deleted target | Allocated bytes before | After |
|---|---:|---:|
| `.git/hmasd-launch-sources/4d911286533342c891ce01ebfb651e6e` | 1750671360 | 0 |
| `.git/worktrees/4d911286533342c891ce01ebfb651e6e` | 3592192 | 0 |
| `temp/directions/uav_fleet_adaptation/` (B07 input consumption copy, empty test scratch, consumed observer request) | 26456064 | 0 |
| `experiments/candidates/uav_fleet_adaptation/__pycache__/` | 8192 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b02/__pycache__/` | 65536 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b04_native_development/__pycache__/` | 20480 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b06_count_development/__pycache__/` | 98304 | 0 |
| `experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/__pycache__/` | 126976 | 0 |
| `tests/experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/__pycache__/` | 118784 | 0 |

All nine targets are absent. Net allocated disk reduction is**1781157888bytes**:
1754263552snapshot/administration plus26894336scratch/caches. This is measured
file-allocation reclamation, not Git-object removal or free-host-capacity growth.
The actual source allocation exceeded its earlier rough planning range and is
reported as measured. No backup, tar, whole-tree copy or retention chain was
created. The transient preview refusal is resolved; no cleanup tool blocker
or disposable leftover remains.

Useful B07 code/tests and source-bound metadata remain published because they
state and check the retained target/optimizer/native-reading contract. The
unique six phase checkpoints, target archive, endpoint diagnostics,672raw
trajectories, original complete summary and compact reading/native receipts
remain at their single canonical locations. No new disposable production
implementation or duplicate bulk archive remains. Earlier canonical sources
and adverse outcomes are unchanged. The completed selected plan is retired
in the existing dated research archive; current standing records reserve and
no selected successor.


<a id="post-b07-source-support"></a>
### Root disposition and bounded source-only continuation

After reading the complete B07 result, original independent recommendation and
DM response, Root returned this native direction decision:

> I have now read the complete B07 result, original new ResearchCritic recommendation and your final response. Root adopts ending unchanged T/H while retaining P/B*, Hdirect's conditional positive, adverse worlds and the nonminimal direct-constructor timing limitation. Finish your own publication and measured closure without waiting for me. I have assigned /root/oracle_next_capability a bounded source-only reassessment of the next worthwhile learned-development question or a better independent use of this slot; it must inherit your full record, all three libraries and primary passages. After closure, support that Oracle with the concrete source/feasibility/cost facts it requests and record substantive findings in your existing notebook. No new fit, target, native/controller query, new reduction or implementation is selected, and actual-S2/transfer remain unselected. This continues broader question ownership; it does not reopen the stopped recipe or create a required successor.

This is continued question ownership and permission for bounded source facts,
not another result-bearing idea. B07's result, exact-mixture/no-S2 dispositions,
all exposure and the completed cleanup stay fixed. I finish the direction's
publication and will answer concrete source/feasibility/cost requests within
that limit, preserving substantive findings here. No successor result study,
required replacement, recurring check or experiment dependency is invented.

<a id="post-b07-local-gate-source-facts"></a>
### 2026-10-01 — Source-only facts for Root's local-gate Oracle

This appendix answers `/root/oracle_next_capability` within Root's bounded
source-support assignment above. It is **not a selected study, fit allowance,
new outcome reading or implementation**. B07 remains closed. The current
published main background retains its P/Bstar/Hdirect capabilities, adverse
worlds and no-automatic-repair conclusion; those findings are not changed by
this source inspection. Current main was refreshed before publication. No
other direction was asked to do work.

The Oracle's concrete provisional question is whether a local binary
transmitter gate can add useful native value when all motion is supplied by
frozen P0, without a registered map or report link. At each original four-tick
boundary, only member `r=(t/4) mod 5` may turn OFF; the other four must be ON.
The Oracle requested native mask/observation timing, overlap with prior work,
reusable code and complete-cost feasibility. It explicitly accepted the
old-mask decision timing described below; no all-on sensing refresh or
managed-I decoder is part of the candidate.

**Native interface and consequential timing.** The original N5 factory is
[make_real](../../../../experiments/candidates/ucope/uav_motion_prefix_b01/environment.py#L8):
five physical UAVs, fifty uniform static users, H256, free-space/vectorized
radio, 3 dB eligibility, capacity ten, no FDMA/shadowing/paper reward. The
existing [radio B01 factory](../../../../experiments/candidates/uav_radio_activation/b01/study.py#L52)
already enables masking through the injected base class.
[set_transmitter_mask](../../../../envs/pettingzoo/uav_env.py#L224) validates
and copies a boolean five-vector, refreshes radio/assignment/observations with
the current physical channel, and advances neither positions nor clock. It
does **not** enforce the proposed rotating-role or four-active invariant;
those would belong to a new caller. Native `step` moves all five UAVs first,
then computes radio/reward, increments time and returns the actual-mask local
observations. A silent vehicle still moves.

The source-compatible ordering is one current old-mask observation per
boundary; all five original P0 proposals and their private navigation updates;
the designated gate's choice from its allowed old-mask local inputs; one mask
setter; then four native transitions with the chosen motion/mask. Setter
feedback must not cause a second policy invocation. In particular, no temporary
all-on mask is installed to obtain a more informative gate observation. At a
boundary the previous silent member makes its next P0 proposal from its
censored row before being reactivated; the newly designated rotating member
was active during the preceding block. At reset all five are active.

Decision-observation mask and newly applied native-step mask can differ at
that same clock. The reader must record and reconstruct both, rather than
copy the managed-arrival reader's assumption that the report and step share
one mask. Completed reward, SINR and connections must be copied before a
subsequent setter: the vectorized update overwrites the SINR array in place.
These are observable state-machine facts, not a proposed extra experiment.

Silence removes its user's SINR row (`-inf`) and both directions of its peer
links; hence its actor row retains own position/clock but has zero user/peer
slots. Other active members' SINRs and visibility also change. Consequently,
**fixed P0 parameters do not imply fixed P0 trajectories**. The complete
comparison would include this feedback and later-motion consequence. Native
masking itself is available; no fatal interface incompatibility was found.
Sources: [user radio](../../../../envs/pettingzoo/uav_radio.py#L33),
[peer masking](../../../../envs/pettingzoo/uav_env.py#L952),
[observation assembly](../../../../envs/pettingzoo/uav_env.py#L405), and
[existing setter tests, inspected only](../../../../tests/experiments/candidates/uav_radio_activation/b01/test_radio.py).

**Preserving the inherited motion program.** Original P0 is the B02 S asset,
file SHA256 `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`,
state SHA256 `6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`;
its canonical remote locator remains in
[the frozen asset binding](../../../../experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py#L31).
It is the original FP32 114→128→128→27 ReLU network. No checkpoint was loaded
or queried during this inspection. The B07 temporary consumption copy has
already been deleted; the required canonical asset is unchanged.

[B02 StudentPolicy](../../../../experiments/candidates/uav_fleet_adaptation/b02/policies.py#L81)
and [its helper](../../../../experiments/candidates/uav_fleet_adaptation/b02/controllers.py#L123)
provide the required original program without importing B06 count adaptation.
The actor uses first103 observation fields, pre-navigation one-hot10 and the
analytic fallback bit. Its cache keys exact ordered FP32 local fields plus
navigation, never sampled commands. One FP32 row supplies logits; temperature
one probabilities use the original FP64 law, followed by one fresh uniform
at `[root, world, tick, agent]` and the original right-search flat CDF. Every
stochastic boundary draws even on a cache hit. All27 command categories,
including boundary aliases, remain. Gate randomness requires its own declared
domain so it cannot consume or shift those motion draws. The original
[fixed-policy adapter](../../../../experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py#L59)
already supplies P1, Bstar0 at temperature2, G, Q10 and C with that decoder;
the managed-I two-integer sampler is a different program.

With no visible users the helper returns fallback=True; navigation advances
only by its original fallback/within60m waypoint rule. **P0 still samples its
network**, rather than bypassing it for C's hard waypoint action. The unchanged
helper can process masked rows and calibrates unobserved interference from
observed SINR, but continues to model own-on candidates with frozen observed
peers. That is an inherited modeling limit, not a demonstrated bug. The native
local row contains at most20 anonymous eligible-user slots and10 anonymous
peer slots, not the complete map, user identities, teammates' commands or
global outcomes. Evaluator information must remain outside both local gates.

I corrected the phrase “own count 0…10”: the lawful variable is
`c=min(number of positive user-slot SINR fields,10)`, the **capped visible-user
count**, not a supplied grant ACK. The Oracle accepted this definition for
all fitted features and ZERO's `c==0` rule. Any source-law relation to actual
service would not authorize reading extra feedback.

**Record overlap and scope.** Targeted searches of current UAV notebooks and
source, the research archives, external-review records and Claude research
records found no exact previous frozen-P0/local/rotating-one-bit native learner.
This is a bounded search finding, not a literature or exhaustive novelty claim;
the Oracle independently owns its three-library and primary-source assessment.
The closest records are materially different:

- Radio activation B01–B03 choose central G/E or S/T commands/masks using a
  registered map and delayed report rights; the rotating mover in S/T does not
  make their mask choice a local binary gate. Their immediate/full-trajectory
  reversals remain relevant contrary evidence.
- Fleet adaptation B01 trains motion under central N8 E, whose chosen mask
  stays deterministic; it does not learn a local transmitter action.
- Parent adaptation B05 composes a frozen S asset with central E/S2/T2 and a
  managed-I sampler. Its existing mask/censor discussion supports feasibility,
  while its native outcomes do not answer the new local gate comparison.
- Persistent-service's binary service/dispatch gate has a different energy,
  service and member-selection contract.

Direct entries are [radio results](../uav_radio_activation/NOTES.md),
[earlier N8 scope](#2026-09-30--b01-prospective-n8-warm-start-comparison),
[parent composition](../uav_parent_adaptation/NOTES.md#2026-09-30--design-only-inherited-local-motion-with-actual-radio-management),
and [persistent service](../uav_persistent_service/NOTES.md). No stopped object
is reopened, and no new result is inferred from the matches.

**The concrete object priced, including accepted corrections.** For pricing,
the Oracle specified512 addressed training worlds, eight for each of64 force
clocks. Each produces two complete H256 branches: force the eligible member
OFF versus ON once, then use the same fixed .5 gate baseline and addressed
motion/gate tapes. Both branches are fully charged, including their common
prefix. The saved paired native mean-J difference is the one training target
per world; no new target was computed here. Subsequent repeated deployment of
a fitted gate changes the continuation law used to acquire those labels, so
complete final rollouts remain necessary evidence if this question is selected.

The initial proposal compared a count-bucket table with a ridge on P0's128
hidden features. I pointed out that the existing114 pre-network fields already
contain lawful geometry/navigation/fallback information absent from a count-only
table. The Oracle accepted the stronger ordinary comparator while keeping two
fits: RAW has those114 fields plus an11-way `c` one-hot (125 features); HIDDEN
adds P0's original128 hidden fields to that same vector (253 features). Both
use fixed FP64 ridge, training-only centering/scaling (constant columns scale1),
an unpenalized intercept and unit coefficient penalty in **sum-of-squared-error**
units; choose OFF iff prediction>0 and ON on an exact tie. ZERO remains unfitted.
Thus this is a finite feature-package comparison, not an isolated nonlinear
mechanism test or two independent training replications. This source suggestion
and the Oracle's acceptance do not select or authorize either fit.

The priced final panel is32 worlds×2 tapes for P0 A/O/R/ZERO/RAW/HIDDEN
(384 episodes), P1/Bstar0/G/Q10 each A and ZERO (512), and deterministic C A
and ZERO once per world (64). It is **960 final plus1024 acquisition =1984
episodes/507904 native steps**. I corrected the initial2048/524288 total; the
Oracle accepted1984/507904 and specified no unnamed extra64 episodes. Its
panel-width decision remains its own recommendation to Root.

| Source-derived exposure for this provisional full list | Count |
|---|---:|
| Acquisition native steps / P0 motion decisions | 262144 / 327680 |
| Final native steps / all-parent motion decisions | 245760 / 307200 |
| All motion decisions / rotating gate opportunities | 634880 / 126976 |
| Learned-parent helper requests and one-row forward ceiling | 532480 |
| C-family requests (C, Q10, G); no-hit ceiling | 102400 |
| Fresh stochastic motion uniforms (C's64 episodes excluded) | 614400 |
| G score-tail constructions | 40960 |
| Mask setter ceiling (one per boundary) | 126976 |
| C no-hit candidate paths / modeled ticks | 2764800 / 11059200 |
| Learned-parent helper link ceiling / C link ceiling | 74547200 / 231424000 |
| Native dense power slots for scored episodes/resets | 140219200 |
| Additional dense SINR slots at the mask-setter ceiling | 34918400 |

Each additional constructor reset adds275 native dense power slots. Setter
refresh reuses physical path loss, so its SINR arithmetic is not another
physical-channel draw or another set of power-distance evaluations. Cache
misses and actual link counts depend on the new histories; old empirical hit
rates were not substituted. With forced-clock gate draws omitted, acquisition
would use64512 stochastic gate uniforms; final R adds4096. The exact convention
must be declared, while the motion-address rule remains independent.

**Reusable engineering and dominant cost.** The original128 hidden vector is
the second ReLU output in [B02 Student](../../../../experiments/candidates/uav_fleet_adaptation/b02/model.py#L15).
It can be retained from the already-paid one-row forward/cache; a new encoder
fit or duplicate production forward is not inherently required. Current code
does not expose it, so that small interface change and its arithmetic identity
would still need implementation/checking if selected. The two double design
arrays with intercept have512×126 and512×254 entries, about0.52/1.04 MB. The
larger Gram product has512×254²≈33.0 million multiply-accumulates. These are
source arithmetic sizes, not measured runtimes.

The [parent B06 solution audit](../../../../experiments/candidates/uav_parent_adaptation/b06_continuation_amortization/fit.py#L83)
is a useful numerical pattern for scaler/constant-column and normal-equation
verification without fitting again in the final reader. Its normalized world
weights and penalized intercept differ from this provisional objective and
must not be imported as defaults. B04 native PPO and B07 target fitting are
not drop-in gate learners and would not be called for this proposal.

The existing mask-aware [radio/observation formulas](../../../../experiments/candidates/uav_radio_activation/b01/read.py#L39)
and [parent composition native checks](../../../../experiments/candidates/uav_parent_adaptation/b05_radio_composition/verify_local.py#L76)
can support independent reconstruction; the latter's managed decoder and
report-mask timing must not be inherited. The existing all-on B02 collector
and reader reject masks, so they also cannot be used unchanged. A complete
reader must bind all1984 episode files/507904 native endpoints, decision and
applied masks, rotating eligibility, held commands, raw local-feature/nav laws,
private draws,512 common-prefix pair identities, training labels and both
fixed regression solutions, plus complete final comparisons. Replaying every
policy request can add up to the same532480 learned-parent and102400 C-family
requests, while adding **zero native transitions and zero optimizer updates**.
Exact reader query scope belongs in the eventual prospective contract; it is
not a free afterthought or an execution authorized by this appendix.

The planning estimate supplied to the Oracle is **0.5–1 CPU-hour for worker
plus a complete reader** on the known one-thread local host, and **6–12 support
hours** for implementation, meaningful checks, independent engineering review
and scientific reading. These are rough estimates, not observed labor, hard
limits or node admission. Timing anchors are the already-published B04's1312
episodes/two native fits/calibrations at517.603 complete CPU-s with its lighter
no-radio reader, and B07's672 final episodes/two archive fits/full928-file reader
at560.463 complete CPU-s. The new pair acquisition, P0/helper execution, saved
evidence and full mask-aware reading dominate the small regression solves.
Approximately1–3 GiB bulk/scratch headroom is a planning allowance, not a
measured artifact size. No S2 runtime was repriced.

On the Oracle's final factual request, durable output and staging were priced
separately using **already-recorded metadata only**. B07's672 canonical raw
NPZs total317776140bytes; straight episode scaling to1984 is approximately
938196223bytes, or0.874 GiB. This is a reference calculation, not a prediction
of the new layout/compression. A rough **0.7–1.5 GiB new durable bulk** allowance
is reasonable for native raw plus the much smaller paired-feature/regression
evidence; its actual size remains unmeasured. The1–3 GiB working-output/scratch
allowance above must not be interpreted as a second complete durable raw copy.
If local execution requires consumption copies of both original motion assets,
their two known file identities total848974bytes; Bstar0 reuses P0. Source
staging is another scope: B07's actually measured launch-source snapshot
allocated1750671360bytes, with3592192bytes of Git administration, and both were
deleted at closure. Those historical sizes neither require a new duplicate nor
measure a future snapshot. No new artifact inventory or benchmark was performed.

All work for this appendix was source/document inspection and arithmetic on
the Oracle's prospective counts. No production model was loaded, no native,
controller or helper query was made, no saved outcome was newly reduced, no
fit/target was computed, no test or implementation was run, and no new bulk or
scratch artifact was created. Source-support labor is unmetered. The factual
response and corrections were returned through native child communication;
Root/Oracle retain the next-question decision, including a justified stop.

**Reader-scope clarification after the first source appendix publication.**
The Oracle asked whether the0.5–1 combined CPU-hour estimate included complete
saved native physics and all actual policy rows. The intended coverage was
full, not a sampled radio subset. For the same1984-episode object, explicit
logical work includes507904 post-step radio/assignment reconstructions,
126976 boundary mask-refresh reconstructions if a setter is called at every
boundary, old-mask decision observations at all126976 boundaries and1984
terminal observations. All634880 motion-law requests must be checked with
their original per-episode cache semantics and private draws, together with
every actual helper/actor/gate output. The512 paired prefix identities and
labels, both frozen feature scalers and ridge-objective/normal-equation
residuals (without re-solving), every final outcome and adverse world are
also included. There is no extra native suffix, all-on sensing probe or
optimizer replay. Reusing an exactly shared recorded prefix can save actual
reader arithmetic only if explicitly counted; it does not remove logical
coverage or refund the two fully executed acquisition branches.

An independence limitation of the reusable source was made explicit:
`uav_radio_activation/b01/read.py:radio` calls the same pure user-radio kernel
used by the native backend. Its separate scalar peer/observation assembly
does not make that imported user-radio formula an independently written
scalar implementation. Full-state coverage and implementation independence
are distinct. If the selected reader is to use independent scalar user-radio
and assignment arithmetic at **every** saved endpoint and mask refresh, as
well as the complete policy checks, the more conservative planning range is
**0.5–2 combined CPU-hours**. The earlier0.5–1 estimate is retained above as
originally given; neither range is a measured runtime or hard limit. No
sampled-coverage exception or benchmark is proposed by this clarification.
Final source selection, actual arithmetic counts and measured runtime would
belong to a separately selected and reviewed implementation.

**Final source-price correction: retain Hdirect in place of P1.** Before
returning its recommendation, the Oracle replaced the128 final P1 A/ZERO
episodes by128 Hdirect A/ZERO episodes. Its stated reason was to retain the
consequential ordinary Hdirect capability under the new mask histories;
B07's all-on ordering against Bstar0 does not determine their new composed
outcomes. This substitution remains prospective and adds no episode or fit.
The final priced motion references are therefore P0, Bstar0, Hdirect, G, Q10
and C; the two gate fits remain RAW and augmented HIDDEN. The earlier P1
pricing above is historical, superseded by this paragraph.

Source inspection of
[B07 Policy.query](../../../../experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/policies.py#L31)
and [build_targets](../../../../experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/targets.py#L31)
found no all-on assertion in Hdirect's local law. MemoC supplies original C
scores, selected category, fallback/navigation and114 lawful features from
the actual masked row. A private exact-input logit cache supplies one-row
FP32 P0 inference on those **C-derived features**, followed by original
FP64 temperature-one probabilities. H construction multiplies `(1-.1)*p`
then adds `.1` at C's index. The existing implementation constructs both T/H
at every law call, including cache hits, selects H and takes a fresh original
flat-CDF/right-search draw. Probabilities, sampled categories and innovations
are not cached. Calling StudentPolicy as an additional feature helper would
add work and change this source pipeline; Hdirect obtains its feature/nav
result from MemoC.

The existing B07 wrapper imports B06's count-aware MemoC/actor interface and
calls `actor(features,[5])`; original B02 Student accepts only `features`.
[CountStudent](../../../../experiments/candidates/uav_fleet_adaptation/b06_count_development/model.py#L16)
sets its added pre-ReLU count feature to zero at N5 and uses the original
network tensors. No learned count behavior or new count information is
required for this proposed use, but an explicit N5 adapter would still have
to preserve the C-derived features, navigation, one-row actor arithmetic,
FP64 constructor and decoder. The B07 class cannot simply be passed the
original Student without resolving that signature. These are source facts,
not a new masked-checkpoint numerical or bitwise-equivalence certification;
implementation and meaningful synthetic checking remain unselected.

| Revised full-panel source count | Count |
|---|---:|
| Episodes / native steps, unchanged | 1984 / 507904 |
| All motion requests / gate opportunities, unchanged | 634880 / 126976 |
| Neural forward ceiling, unchanged | 532480 |
| Standalone analytic-helper request ceiling | 491520 |
| C-family requests, including Hdirect | 143360 |
| C no-hit paths / modeled ticks | 3870720 / 15482880 |
| Analytic-helper link ceiling / C link ceiling | 68812800 / 323993600 |
| Hdirect law calls / both constructed target vectors | 40960 / 81920 |
| Fresh motion uniforms, unchanged | 614400 |
| Required original-P0 input consumption bytes if staged | 424487 |

A full reader reproducing each actual query can add the same request/vector
ceilings again, with cache misses measured rather than presumed. Native
priming, setter, endpoint and observation counts are unchanged. Hdirect's
neural calls replace P1's calls, while C ranking replaces its standalone
analytic helper; **both target-vector construction is still charged**, so
this is not a minimal H-only runtime claim. P0 also supplies Bstar0 and
Hdirect, so the P1 input copy is no longer needed. The rough0.5–2 combined
CPU-hour range with full independent scalar native reconstruction,
6–12 support hours and0.7–1.5 GiB new durable bulk remains a reasonable
planning allowance; all are unmeasured and schema/runtime dependent.
The changed dominant counts were returned to the Oracle before publication.
No model, controller, helper or constructor was queried, no target was
constructed, and no result outcome was reduced for this correction.

**Streaming RAM and final gate-draw convention.** At Root's request relayed
by the Oracle, the source-only peak-RSS planning estimate is **0.4–1.0 GiB per
streaming worker or reader process**, unmeasured and not a hard cap. The
candidate streams episode production/reading, retains only512 paired training
rows and two small designs plus32-world summaries, resets caches per episode,
and runs worker and reader sequentially. There is no source requirement to
retain the entire raw panel in memory. One or two episode records and at most
320 distinct motion-input addresses per H256 episode are small compared with
runtime overhead; Hdirect retains separate C-result and logit dictionaries
for those addresses. The largest512×254 FP64 design is about1.04 MB, with
small Gram/solver workspaces. Frozen P0 has34715 FP32 parameters. Independent
scalar radio reconstruction increases work without requiring run-wide arrays.
This forecast assumes records/files/caches are released as streaming advances.

Published peaks are B04's430004 KiB and B07's593324 KiB, the latter including
larger archived-target fitting arrays. Neither isolates baseline runtime or
measures the new object. Fresh actual-node admission must independently read
effective memory and concurrent load, with headroom beyond the forecast;
source snapshots, durable data and scratch disk are separate from RSS.

The Oracle fixed the private gate convention to **draw and record the normal
R uniform at the forced acquisition boundary, then override its decision**.
Thus acquisition makes65536 gate draws and final R4096, for69632 total. This
supersedes the earlier conditional omitted-force-draw count, while leaving
the original614400 motion draws,1984 episodes,507904 native steps and two
prospective regression fits unchanged. This correction is still source
pricing and contract clarification, with no result execution selected here.

<a id="b08-original-selection-review"></a>
## 2026-10-01 — B08 original independent selection advice and Root adoption

The following complete original question, recommendation and consequential
correction exchange were delivered by the existing Root Oracle before any B08
implementation. Its continuing context, scope and limits are disclosed in the
answer. The source-only restriction ended only with Root's separate selected
B08 assignment; the historical wording below is preserved. The completed B07
stop, all positive/adverse evidence and unselected actual-S2/transfer reserves
remain intact. No second selection review is being substituted for this advice.

BEGIN ORIGINAL ROOT QUESTION — 2026-10-01 02:15 UTC

Root source-only next investment task after completed B07. Keep your Astra Max Oracle responsibility for detailed idea discovery and independent challenge. First read the complete B07 result, original new ResearchCritic answer and DM response at docs/research/candidates/uav_fleet_adaptation/NOTES.md#b07-complete-reading and #b07-original-independent-result-review (result source c2b2cd27276e49458b18ca69216b3525f281ea47, evidence publication e1275959e1e117c433b0279c1ae1bc26ca94f284). Root has fully read these and adopts stopping unchanged T/H: active modest targets and full learning, no useful T gain over P/B*, ordinary Hdirect conditional positive, all component/adverse/CPU limitations retained. Do not redo its adequate result audit or send another Pro question. The broader question is now where a bounded learned-development investment can add useful capability beyond competent retained S/P/B*, G/Q, direct H and paid ordinary planning, if anywhere. Reconsider whether a materially different constructive question is worth buying now, rather than an objective/entropy/optimization rescue. Actual-S2 learning and transfer-only remain unselected reserves, not blocked or mandatory gates; review their complete original advice and DM challenge in the current plan before reconsidering them. No fresh-label/DAgger/longer-training/stronger-tilt study is implied. A justified stop or an independent question with higher marginal value is valid.

Use relevant cumulative project evidence, July/external reviews, all three local libraries, and load-bearing primary web passages as needed. Root's owner asks four substantive DMs, but spare capacity is not a scientific premise. Your concrete deliverable is one strongest worthwhile next question (or stop with the unresolved opportunity explained), causal conjecture versus strongest ordinary alternative, information/action/use contract, smallest complete discriminating comparison, opposite predictions, prospective full fit/query/native/reader/support/storage cost and what each outcome changes. Detail innovation belongs to you, not a request merely to rank the same fixed assets. Do not require a positive pilot or exhaustively diagnose all past failures. The running parent B08 exact G2/A2 reuse and waiting B06 S_F:LRS are already selected; do not overlap or change them. Fleet B06 cadence has complete saved results and is undergoing its original independent result review, so treat its new conclusion as provisional until that is published. You may obtain bounded source/feasibility facts directly from the existing fleet-adaptation DM after its closure work; do not burden the other studies or authorize execution. ZERO new policy/model/native queries, target generation, new outcome reductions, fits, implementation, benchmarks or result-bearing runs under this assignment. Return your full original recommendation here; Root will select cross-question work after reading it, and the existing DM retains all record/publication ownership.

END ORIGINAL ROOT QUESTION

BEGIN ENTIRE ORIGINAL ORACLE RECOMMENDATION — 2026-10-01 02:50 UTC

I recommend **one bounded pivot to learning a local transmitter gate over frozen P0 motion**. The question is whether native experience can produce a useful, map-free interference-control decision beyond simple transmitter rules and the retained P0/Bstar0/Hdirect/G/Q10/C programs. This develops a new control head; it does not update the motion network or reopen T/H.

The complete proposed purchase is **two regression fits, 1,984 H256 episodes and 507,904 native steps**, including acquisition and final evaluation. I judge it worth one exploration because either a learned gate or an ordinary gate could supply a useful capability under substantially smaller deployment information rights than the existing central radio managers. Expectations should remain modest.

This is a continuing review in the originally isolated context. It retains my earlier advice and Root’s dispositions; it is not a newly blinded reassessment. I reused the adequate original B07 and cadence result audits, read their complete readings, criticism and responses, and independently inspected the consequential mask, observation, policy and sampling source. I made no new scientific queries, reductions, fits or implementation.

**The evidence supports changing the decision being learned.** B07 actively changed targets and network parameters, yet T−P0 was only +0.000060 J with an interval spanning zero; exact Tdirect also established no improvement. Hdirect’s conditional +0.007329 over P0 remains useful evidence, alongside its adverse worlds and deficit to Bstar0. These observations weaken an optimization-only rescue. They do not establish that P0’s representation is useless or that all useful learning has ended. The [complete B07 reading and original review](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md#b07-complete-reading) remain controlling evidence.

Radio management supplies a constructive opportunity, with a major qualification. The published managed composition improved S_S2 over S_all by +0.093665 J across its 32 worlds, while the older central radio programs also produced substantial gains. Those programs had registered-map, report and mask-selection rights absent here. Some averaged roughly 3.4 active transmitters; the proposed contract always keeps at least four active. Their gains therefore neither predict this gate’s gain nor measure its headroom.

The newly completed cadence study also matters: changing observation and action timing substantially changed travel, while E−H4 reward effects remained unresolved and the 19-tick outage persisted. This supports treating censoring and subsequent motion as consequential feedback. It does not supply a transmitter-learning result or an automatic scheduler repair. I retain its published stop and conditional capabilities.

I reread the complete actual-S2 proposal and DM challenge. It remains a legitimate reserve, with approximately 655,360 native steps and a materially larger managed-runtime bill. I prefer this question now because it tests a distinct deployment capability and gives every learned decision a direct binary native contrast. That preference does not convert actual-S2 or transfer-only into blocked work, required gates or scientifically rejected approaches. The selected parent B08 and waiting B06 remain untouched.

The relevant literature offers a bridge, not a guarantee. Ross and Bagnell’s cost-to-go regression framework motivates learning from consequential action comparisons, but its aggregation and learning assumptions do not establish improvement for this single acquisition batch under a fixed continuation policy. [Primary paper, §§2–3](https://arxiv.org/pdf/1406.5979). I checked all three local stores and the relevant July/external records:

- Foundations B03 distinguishes local information from shared coordination devices. The local catalog’s PDF was unavailable, so I read the author’s primary preprint, particularly §§2.3.3 and 6.2.4. [B03 catalog](/home/fires/hmasd-wsl/docs/new-libs/corpus/catalog.jsonl), [author preprint](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf).
- DeCOM, MARL-0007, communicates neighboring base actions and updates a materially different decomposed policy. It is an antecedent for modular control, not evidence for this frozen, no-report gate. [Primary structured text, pp.3–4](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0007.json).
- CFPI uses continuous-action, value-gradient assumptions that this binary regression does not inherit. [Primary PDF, pp.2–4](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2023/pmlr-v202-li23av/arxiv-2211.15956.pdf).

Distributed learned power control is already established work, including implementations with richer neighbor feedback. I claim no algorithmic novelty or inherited near-optimality. [Nasir and Guo, primary paper](https://arxiv.org/pdf/1808.00490). July’s label-learning failures also prevent treating available information as demonstrated learnability.

The proposed contract is precise enough to select:

1. **Host and eligibility.** Use the original N5/U50/H256 reset factory and four-tick motion hold, not B06’s alternative initializer. At boundary `t`, only member `r=(t/4) mod 5` may switch OFF for the coming block; the other four must be ON. The shared rank and clock are preinstalled coordination resources, given to every arm. Four active transmitters are not a service guarantee.

2. **Decision timing.** All five motion proposals use the current, old-mask observations. Then the eligible member chooses its gate, the mask is installed once, and motion/mask are held for four transitions. Setter-returned observations cannot trigger another decision. In particular, the previously silent vehicle makes its next motion proposal from its censored observation before reactivation. No temporary all-on sensing refresh is allowed.

3. **Information.** The gate receives only its own original P0 input vector and the declared additional features below. It receives no map, reports, other agents’ observations or proposed actions, global outcomes, grant ACK, or evaluator truth. Define `c` as the number of positive user-slot SINR fields, capped at ten. This is a visible-user count, not supplied service feedback.

4. **Frozen motion.** Preserve original P0 weights, helper/navigation behavior, FP32 actor arithmetic, FP64 temperature-one probabilities and one fresh indexed flat-CDF draw per stochastic decision, including cache hits and all 27 categories. Gate randomness has a separate address domain. Fixed weights do not mean fixed trajectories: silence changes observations, navigation and later motion.

5. **Physical scope.** This is immediate own-transmitter actuation under a predetermined eligibility schedule. It does not model command delivery, switching energy, synchronization failures or hardware guard times. Transmitter on-time and switching counts are useful measurements, not measured energy savings.

The strongest constructive conjecture is that local service demand and interference conditions contain a predictable binary tradeoff, and P0’s frozen nonlinear features make that tradeoff more accessible to a small fitted head. The strongest ordinary alternative is that the benefit comes mostly from permission to silence one transmitter: an always-OFF, random, zero-visible-user or raw-input rule may capture it.

The acquisition should contain **512 fresh worlds, eight assigned to each of the 64 decision clocks**. Each world produces two complete H256 branches. Both use P0 motion and an independent 0.5-probability gate baseline, except that the assigned decision forces OFF in one branch and ON in the other. Subsequent gates and motion use paired private random tapes on each branch’s actual history. Execute and charge both full prefixes; do not copy future commands between diverged histories.

The target is the complete native difference

\[
y=J_{\mathrm{OFF}}-J_{\mathrm{ON}},\qquad
J=\frac1{256}\sum_t\left(0.7\,\frac{\mathrm{served}_t}{50}+0.3\,\mathrm{quality}_t\right).
\]

Retain every pair, including zero targets. Draw and record the ordinary gate uniform at the forced boundary before overriding it. These within-world differences remove the common return level from the label; they do not remove continuation-policy mismatch.

Fit exactly two shared gates on those same 512 pairs:

| Gate | Inputs |
|---|---|
| RAW | Original 114 P0 inputs plus 11-way capped-count encoding: 125 features |
| HIDDEN | The same 125 features plus P0’s original 128-dimensional second-ReLU output: 253 features |

Use FP64 ridge with training-only centering and population-standard-deviation scaling, constant-column scale one, an unpenalized intercept and unit coefficient penalty in **sum-of-squared-error units**. Choose OFF iff the prediction is positive; exact ties choose ON. There is no tuning, validation-based selection, encoder update or iterative dataset extension. HIDDEN’s activations come from the already-paid original forward/cache.

This is a matched comparison of two finite feature packages. HIDDEN contains no additional information beyond the raw observation history encoded by its inputs, and superiority would not isolate a uniquely learned-representation mechanism against every possible nonlinear feature map. The two fits also share one acquisition dataset and one pretrained parent; they are not independent training replications.

The smallest complete final panel I recommend is:

| Frozen motion program | Gate rules | Final episodes |
|---|---|---:|
| P0 | All ON, eligible always OFF, random 0.5, ZERO, RAW, HIDDEN | 384 |
| Bstar0, Hdirect, G, Q10 | All ON and ZERO, each | 512 |
| Deterministic C | All ON and ZERO | 64 |
| **Total** | 16 programs on 32 fresh worlds | **960** |

Stochastic programs receive two motion tapes per world; deterministic C needs one. ZERO switches OFF only when `c=0`. Hdirect replaces the less consequential P1 control: B07’s ordering does not establish Hdirect’s ordering under these new mask histories.

The main attribution contrast is HIDDEN−RAW. Both fitted gates must also face P0’s four unfitted rules and all ten ordinary-parent A/ZERO combinations. Read each parent’s ZERO−all-ON contrast, plus P0’s always-OFF and random contrasts. This gives 37 declared contrasts and 16 program levels, without a full factorial of fitted gates across parents. World-level paired summaries should average the two tapes before descriptive resampling; 64 episodes are not 64 independent worlds.

Read complete J, service and quality, lower service tails, episode minima, zero-service episodes/streaks, travel and relevant height measures, transmitter on-time/switches, censoring, actual gate choices, controller queries and measured CPU. Preserve every adverse world. Neither higher training fit nor a favorable mean alone establishes practical adoption; no new universal service floor or MEI is being invented.

The outcomes would change different decisions:

- **HIDDEN improves over RAW and the competent complete alternatives:** retain a conditional capability of the composed learned gate. A fresh-data replication could then be worth considering; neither deployment nor confirmation follows automatically.
- **RAW supplies the useful gain and HIDDEN adds none:** retain ordinary supervised local gating and end the representation purchase.
- **ZERO, always-OFF or random explains the gain, especially on another retained parent:** retain the ordinary radio capability. This would support the changed control rights without establishing a need for gate learning.
- **HIDDEN beats RAW but neither challenges Bstar0/Hdirect or their ZERO compositions:** record the narrow feature-package result; it does not justify expanding a weaker complete package.
- **Active learned switching is adverse or unhelpful:** end this one-batch purchase. The result would not identify insufficient local information, a bad representation or a particular repair.
- **The fitted gates scarcely activate:** distinguish nonactivation from harmful intervention. The always-OFF/random arms still provide actual intervention evidence, but no automatic threshold adjustment or extra fitting follows.

The principal scientific limitation is consequential: labels measure one forced decision under random-gate continuation, while deployment repeatedly uses the fitted gate. This changes future observations and the distribution on which the head acts. Full final rollouts are therefore essential. A good regression fit cannot establish policy improvement. The restricted one-silent-member contract and modest sample size are further limits, not reasons to demand a positive pilot first.

The revised full price, including Hdirect, is source-derived and published at `3e339fcf68a99b238224d85878cd0567fe16b1d1` in the [source-support appendix](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md#post-b07-local-gate-source-facts):

| Item | Prospective cost |
|---|---:|
| Fits | 2 ridge fits; no motion-network training |
| Acquisition | 1,024 episodes / 262,144 native steps / 512 paired targets |
| Final evaluation | 960 episodes / 245,760 native steps |
| Total motion requests / gate opportunities | 634,880 / 126,976 |
| Neural forward ceiling | 532,480 |
| Standalone helper requests / C-family requests | 491,520 / 143,360 |
| C candidate paths / modeled ticks, no-hit ceiling | 3,870,720 / 15,482,880 |
| Helper links / C links, ceilings | 68,812,800 / 323,993,600 |
| Motion uniforms / gate uniforms | 614,400 / 69,632 |
| Hdirect law calls / constructed target vectors | 40,960 / 81,920 |
| Worker plus full independent scalar reader | **0.5–2 CPU-hours, estimated** |
| Implementation, checks, review and reading | **6–12 support hours, estimated** |

Hdirect must reuse MemoC’s C-derived features and navigation, followed by its private original-P0 logit cache. Calling StudentPolicy again for features would add an unnecessary helper query and alter the source pipeline. The retained constructor computes both T and H even though Hdirect uses only H; that work remains charged. This is not a claim about a minimal H-only implementation.

The current B07 wrapper uses the count-aware actor signature. An explicit N5 adapter is required to preserve original one-row arithmetic, feature construction and sampling with the original Student. Source inspection establishes feasibility, not a new masked-checkpoint equivalence result. Only P0 needs staging: **424,487 bytes**; Bstar0 and Hdirect reuse it.

The reader is part of the purchase. It must cover all 507,904 post-step radio/assignment states, all 126,976 mask refreshes and old-mask decisions, terminal observations, actual policy requests, private draws, held commands, 512 paired prefixes and targets, scalers and regression residuals, and complete final/adverse summaries. Use independently written scalar user-radio and assignment arithmetic throughout; importing the native pure radio kernel would provide coverage without that implementation independence. Full policy reconstruction can add the same request ceilings again, with **zero new native transitions or optimizer updates**.

Native scored resets and steps account for 140,219,200 dense power slots; mask refreshes add 34,918,400 dense SINR slots using existing path loss. Additional constructor priming must be counted at 275 power slots per reset. Actual cache misses, constructor topology and arithmetic counts remain to be measured.

For streaming sequential worker/reader execution, the source-only peak-RSS forecast is **0.4–1.0 GiB per process**, not a measured cap. This assumes episode records and caches are released as processing advances; only the 512-row designs and compact world summaries remain. The largest design is approximately 1.04 MB. Fresh actual-node admission must inspect effective memory and concurrent load with headroom beyond this forecast.

Separately, allow **0.7–1.5 GiB of new durable bulk** and approximately **1–3 GiB of working-output/scratch headroom**, without interpreting that as a second retained raw copy. Future source-snapshot allocation is unmeasured; B07’s historical 1.75 GB snapshot plus Git administration is an anchor, not the new object’s size.

These costs are substantial despite the small regressions. The recommendation is justified by the different scientific and deployment question, not by spare capacity or a cheap fit count. Existing native interfaces and source arithmetic make it feasible; new masked adapters, full scalar reading, actual runtime/RSS, hardware actuation costs and generalization beyond one acquisition instance remain unverified. No source check here authorizes execution.

**MATERIAL_DISSENT: no.** I recommend selecting this bounded pivot while retaining the completed stops. There is no disputed approved investment; a claim that the gate already improves native value, guarantees service or yields measured energy savings would exceed the direct evidence.

END ENTIRE ORIGINAL ORACLE RECOMMENDATION

BEGIN CONSEQUENTIAL CORRECTION EXCHANGE

ORACLE TO DM — 02:42 UTC

Final comparison correction before returning Root recommendation: replace P1 A/ZERO by retained Hdirect A/ZERO in the same 960-final/1,984-total episode panel. Root explicitly asks beyond Hdirect as well as P/Bstar/G/Q, and B07's historical Hdirect<Bstar does not order them under new mask histories; P1 is less consequential and was not an independent training replication of our gate. No extra episodes or fits. I read current B07 Policy.query via CodeGraph: DIRECT uses MemoC features plus P0 actor and constructs both T/H vectors. Please give bounded source facts only: can the unchanged Hdirect law run through original N5 reset/masking while retaining original flat CDF and numerical actor semantics; revised helper/C/NN, modeled-link/path, both-vector counts and single-P0 staging bytes; does this alter your 0.5–2 CPU-hour/full independent-scalar reader/support/durable estimate materially? My arithmetic suggests NN ceiling still 532,480, helper 491,520, C-family 143,360, C paths 3,870,720, C ticks 15,482,880; 40,960 Hdirect law calls/81,920 target vectors. Please correct if needed and preserve this final source correction in your existing appendix. Still no implementation/query/reduction/run. Thank you.

ROOT TO ORACLE — cost clarification

I have fully read the published local-gate source facts and the independent-scalar reader clarification, including old-mask timing, censored-motion feedback, RAW125/HIDDEN253, 1,984 episodes and the original P1 bill. Please make the Hdirect replacement's changed C/helper/actor work and efficient same-law feature reuse explicit in the final price; the old P1 counts/staging no longer directly apply. Include a streaming peak-RSS estimate (or a clearly stated unresolved estimate with admission consequence), separately from the .7–1.5 GiB durable raw and snapshot/storage figures. No new query or benchmark is needed for these source estimates. I will make the selection from the complete original final, not this provisional headline.

DM TO ORACLE — 02:45 UTC

Your revised arithmetic is correct. Replacing128 P1 episodes by128 Hdirect episodes preserves1,984/507,904 and634,880 motion requests,532,480 NN-forward ceiling,614,400 motion draws and126,976 gate opportunities. Standalone analytic-helper requests become491,520; C-family requests become143,360 (C/G/Q10/Hdirect). No-hit ceilings:3,870,720 C paths,15,482,880 modeled ticks,323,993,600 C links; helper links≤68,812,800. Hdirect has40,960 law calls and81,920 constructed target vectors, including the unused T vector as in B07. A full same-query reader can add the same ceilings again. Native/refresh counts are unchanged. Only original P0 staging is needed:424,487 bytes; Bstar0 and Hdirect reuse it.

Source feasibility: yes, no all-on assertion exists in Hdirect's law. Its MemoC sees the actual masked104-row, supplies ORIGINAL C ranking/fallback/navigation and114 features; direct P0 inference is one FP32 row on those C-derived features, followed by original FP64 T=1 softmax, build_targets and H=.9p+.1delta_C (multiply then add .1 at C), then the original one-uniform flat CDF/right-search. Do not route Hdirect through StudentPolicy.query as an extra analytic-helper query: its features/nav come from MemoC, and its private logit cache resets per episode. The source currently computes BOTH T/H even on cache hits; preserve/charge that implementation if retaining the unchanged constructor. No probabilities or draws are cached.

One adapter qualification: current B07 Policy imports B06 MemoC/count-aware actor and calls actor(features,[5]); original N5 Student accepts only features. N=5 sets CountStudent's pre-ReLU count feature to zero and uses the same original network tensors, so no learned count behavior or count-dependent information is needed. The selected implementation would still need an explicit N5 adapter preserving C-derived features, one-row arithmetic, FP64 construction and sampler; importing B07 Policy unchanged into an original-Student wrapper would fail its signature. Source feasibility is not a new empirical or bitwise-equivalence certification on masked checkpoints. No production query was used here.

The broader0.5–2 combined CPU-hour/full independent-scalar reader estimate remains reasonable as an unmeasured planning range; C work rises while standalone helper work falls.6–12support hours and0.7–1.5GiB durable bulk remain rough/unmeasured with the same full schema obligation, not fit-only costs or hard limits. I will publish this final panel correction as an appended source note, retaining the prior P1 pricing historically.

ORACLE TO DM — 02:45 UTC

Root requests a streaming peak-RSS planning estimate, separate from durable/snapshot disk. Please append a bounded source estimate with the Hdirect correction if feasible, no benchmark. Proposed object streams episode production and full reading, retains only 512 paired training rows/two small designs and 32-world metrics, resets policy caches each episode, and runs worker/reader sequentially. B07's measured 593,324 KiB peak included larger archive training arrays; my conservative source-only forecast is roughly 0.4–1.0 GiB per streaming worker or reader process, unmeasured/not a hard cap, with fresh actual-node admission explicitly needing headroom above that range plus concurrent load. Correct the estimate if source reveals a different dominant retained array or process topology. Gate convention also final: draw and record the normal private R uniform at forced clocks, then override, so 65,536 acquisition gate draws plus 4,096 final R =69,632; motion law untouched.

DM TO ORACLE — 02:47 UTC

The proposed0.4–1.0GiB peak RSS per streaming worker or reader is a reasonable conservative source-only forecast, not a measured cap. I see no required dominant retained array beyond the Python/NumPy/PyTorch runtime: one or two episode records, episode-private caches (at most320 motion input entries per full H256 episode),512 paired feature rows, the512×254 FP64 largest design (~1.04MB), small Gram/solve workspaces and32-world summaries. Frozen P0 is34,715 FP32 parameters; its numeric weights are small relative to runtime overhead. Independent scalar radio work increases CPU rather than requiring run-wide arrays. The forecast assumes raw files and policy caches are released/closed as streaming advances, and worker/reader do not overlap. Historical anchors are B04's430,004KiB peak and B07's593,324KiB; neither isolates baseline runtime or proves the new process peak. Admission must separately inspect actual-node effective memory and concurrent load, with headroom beyond this forecast; source snapshot/durable disk must not be counted as RSS. I will append that and your final gate-draw convention:65,536 acquisition R draws including both forced clocks, plus4,096 final R=69,632; no motion-draw change.

DM TO ORACLE — final source publication

Final Hdirect substitution, updated counts, single-P0 staging, streaming RAM and forced-clock draw convention are published at3e339fcf68a99b238224d85878cd0567fe16b1d1 (origin/main verified), same NOTES#post-b07-local-gate-source-facts anchor. Last92lines supersede the P1 pricing: NN532480/helper491520/C143360, Hdirect40960law/81920vectors, C3870720paths/15482880ticks, staging424487B; gate draws69632. Peak-RSS forecast0.4–1.0GiB per sequential streaming worker/reader, with actual-node/concurrent-load admission and disk separate. Full independent scalar scope remains0.5–2CPU-hours plus6–12support hours and0.7–1.5GiB durable bulk, all estimates. Nothing executed or implemented.

END CONSEQUENTIAL CORRECTION EXCHANGE

BEGIN ROOT ADOPTION AND WORDING CLARIFICATION — separate from the original recommendation

Root has fully read and selects your final local transmitter-gate recommendation unchanged, after reading your cited primary passages and DM source bill through3e339fcf68a99b238224d85878cd0567fe16b1d1. The same fleet-adaptation DM now owns the complete selected2-fit/1984episode/507904step study; no further idea discovery or selection review is requested. One bounded handoff only: forward the EXACT original Root02:15 source question, your ENTIRE02:50 final recommendation and the consequential P1→Hdirect/cost-correction exchange to /root/dm_fleet_adaptation so it can preserve the full originals in its own append-only NOTES before implementation. No need to summarize the answer, collect new evidence, ACK/relay, or send another Pro question. Root adoption retains modest expectations, all original limitations/outcome paths, central-control rights differences, random-continuation mismatch, honest Hdirect/reader/support/storage costs and unselected S2/transfer. Clarification of wording only: HIDDEN is a deterministic feature expansion of the identical RAW current input including original nav features, not an additional observation-history or memory resource. No new information or learned-history claim. Your original answer should remain intact alongside that Root clarification.

END ROOT ADOPTION AND WORDING CLARIFICATION


<a id="b08-selected-contract"></a>
### B08 DM prospective contract: local binary transmitter gating

I have read the complete selection advice and accept Root's selected purchase.
There is no material scientific dissent. This changes the **decision being
learned**: a local binary transmitter choice with paid native consequential
labels, while P0 motion remains frozen. It does not rescue the ended T/H
recipe. The intended contribution is conditional task usefulness and empirical
understanding of finite local gate learning; no algorithmic novelty,
representation necessity or reliable deployment claim is proposed.

The relevant current published background was read at main
`2ef5236252d5ed75eddfcbde0d99da403059f03b`. [Topic2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练)
preserves the registered-map/report rights, capacity changes, native reversals
and useful ordinary radio controls. It makes the smaller local contract a
different capability question, not a measured fraction of S2 headroom.
[Topic3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构) separates local
information from common rank/clock and shared policy parameters. Every arm
gets the same eligibility schedule; no coordination gain is attributed to the
gate features alone. [Topic4](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)
and the [B07 stop](#b07-independent-disposition) require competent ordinary
controls, native outcomes and the original conditional limits. Thus RAW125 is
the matched information comparator, and Bstar0/Hdirect/G/Q10/C plus their ZERO
compositions remain complete-package challenges. HIDDEN253 is a deterministic
expansion of the same current input and private navigation state, not another
information/history resource. A narrower HIDDEN−RAW positive alone would not
establish a useful complete package.

I checked the load-bearing primary passages: Ross–Bagnell
[arXiv:1406.5979 §§2.2–2.4](https://arxiv.org/pdf/1406.5979) describes
cost-to-go examples, regression and iterative aggregation on the current
learner's distribution. The bridge used here is consequential binary labels;
its guarantees do not apply to one fixed random-continuation acquisition.
B03, catalog `docs/new-libs/corpus/catalog.jsonl`, was checked in the
[authors' primary book §§2.3.3/6.2.4](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf):
send/withhold decisions and shared coordination devices are established
objects, with different observations. DeCOM MARL-0007 was read directly in
`/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0007.json`, pp3–4
(PDF `pdf/MARL-0007.pdf` in that store): communicated neighboring base
actions and learned base/perturbation updates differ from this local frozen
motion contract. CFPI, `pmlr-v202-li23av` / arXiv:2211.15956, was read at
`/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2023/pmlr-v202-li23av/arxiv-2211.15956.pdf`,
pp2–4; its continuous-action Taylor/value-gradient and Gaussian assumptions
do not justify the binary ridge gate. Nasir–Guo
[arXiv:1808.00490 §III](https://arxiv.org/pdf/1808.00490) explicitly uses
receiver and neighboring-transmitter feedback. It prevents a novelty claim
and is not a matched-information performance guarantee here. The Oracle's
three-store/July/external reading remains its disclosed supporting search,
not a new exhaustive novelty certification by this DM.

The constructive conjecture is that the old local row contains a useful
prediction of the complete OFF−ON consequence, and retained nonlinear P0
features help a finite ridge learner exploit it. The strongest competing
explanation is simpler: extra actuation rights and an ordinary rule or RAW
regression supply the gain. This is a package exploration, without a
prerequisite positive toy or attribution claim. Silence changes all agents'
interference/discovery and subsequent trajectories despite frozen motion
weights. The shared policy is trained from pooled local examples and team
returns; no return, map, peer action or other agent's row enters deployment.

**Frozen population, order and random domains, before any B08 data exposure.**
The host is the original N5/U50/H256 free-space S1 factory/reset, threshold3,
capacity10, no shadowing/FDMA/paper-height reward and four-tick motion hold.
Each episode uses `env.reset(seed=world)` with the original legacy reset:
five UAV positions and then50 users from the original `RandomState(world)`
stream. No B06 seven-agent layout insertion/extra layout refresh is permitted.
One reusable native environment will be constructed for the worker, with
its two factory/adapter priming resets measured separately from1984 explicit
scored resets; the constructor uses29832061. The original P0 artifact alone
is bound to SHA256
`b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`,
424487bytes, state digest
`6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`,
source `e945483b85c7f8ddfc315c57f36938d6c14201c7`.
Its canonical path is the earlier remote B02 `assets/S.pt`; a declared
consumption copy is allowed only if the selected node needs it.

| Prospective item | Frozen identity/rule |
|---|---|
| Training worlds | 29830000…29830511 inclusive,512 worlds |
| Final worlds | 29831000…29831031 inclusive,32 disjoint worlds |
| Assigned force tick for training index i | `4*(i %64)`, eight worlds per decision clock |
| Training motion root | 29832011 |
| Final motion roots, tapes0/1 | 29832021 /29832022 |
| Training gate root | 29832031 |
| Final R gate roots, tapes0/1 | 29832041 /29832042 |
| Descriptive bootstrap root | 29832051 |
| Synthetic actor construction/load seed | 29832061, no training/random selection |
| Acquisition order | Ascending world; OFF then ON for even i, ON then OFF for odd i |
| Fitting order/data order | RAW then HIDDEN; both512 rows in ascending world order |
| Base final program order | P0_A/P0_O/P0_R/P0_ZERO/P0_RAW/P0_HIDDEN/Bstar0_A/Bstar0_ZERO/Hdirect_A/Hdirect_ZERO/G_A/G_ZERO/Q10_A/Q10_ZERO/C_A/C_ZERO |
| Final execution order | Ascending world; flatten program order with tapes0 then1 per stochastic program and one None tape per C program, producing30 cells; rotate this list left by world-index modulo30; reverse the rotated list for odd world-index |
| Stopping | Exactly1024 acquisition+960 final episodes, exactly2 ridge fits and one complete reader; terminal technical failures preserved, no automatic replacement or added exposure |

These identity ranges have no declared match in the scoped current candidate
notebooks checked before selection of the exact values. They are new
prospective identities, not a claim that every decimal occurrence in every
historical raw file is a world seed. The native layout seed is the world
itself. Motion uses the original addressed scalar uniform at
`[motion_root,world,tick,agent]`. R gate randomness uses
`[gate_root,world,tick,eligible_agent]`, a separate root and no mutable
shared stream. Both full acquisition branches draw and record R at all64
boundaries, including the forced boundary, then override only that decision.
Post-divergence motion is freshly computed on each actual history. C motion
and all non-R gate rules take no random draw.

**Decision and acquisition semantics.** At each boundary, copy the OLD mask
and the returned old-mask observations. Query all five private motion
policies once, retaining their original pre-navigation114 features and
updating each private navigation state. The eligible index is `(tick//4)%5`.
Use that eligible answer's already-computed features/second-ReLU output and
its old local row to choose the gate; the gate does not receive the sampled
motion command, other rows, evaluator metrics or future mask observations.
Construct a fresh mask with all four noneligible members ON and the eligible
bit chosen, install it exactly once, then hold all commands and this mask for
four native transitions. Setter-returned rows are saved for verification but
never used for another decision. Copy SINR, connections and scored endpoint
metrics before any later setter mutates the native arrays. A previously
silent member still moves and uses its censored row before reactivation.

For each training world, execute two complete P0/R trajectories with identical
addressed randomness, forcing OFF versus ON only at the assigned tick. Save
one pair's common pre-force features and `mean_J_OFF-mean_J_ON`, using all256
native scored ticks in each branch. Preserve all512 pairs and every zero
target. Pair validity includes identical complete prefixes through the force
decision, identical features/navigation/proposals at that point, and distinct
applied forced bits; no copying of future states/actions is allowed. The
fixed R=.5 continuation is not the deployed repeated fitted gate and creates
the principal distribution/decision mismatch to be tested in final rollouts.

Exactly two FP64 ridge solutions use the same512 examples: RAW125 =
original114 plus one-hot `min(positive user-slot SINR count,10)`; HIDDEN253
appends P0's second128-ReLU output from the same paid original forward/cache.
No P0 parameter update, extra representation query, critic, validation,
tuning, additional label, second dataset or iterative aggregation is selected.
Both minimize sum squared residuals plus unit coefficient squared norm, with
an unpenalized intercept and training-only mean/population-SD scaling;
constant columns have scale1. Each deterministic gate chooses OFF only for
a strictly positive prediction, so exact zero chooses ON. Native training
targets are not service ACK inputs at deployment. Fit counts are2; gradient
optimizer steps and motion-parameter updates are0.

**Readings and uncertainty.** Sixteen levels and precisely37 contrasts are
fixed: primary P0_HIDDEN−P0_RAW; each fitted gate minus the four P0 unfitted
rules and ten other-parent A/ZERO programs (28); each of six parents'
ZERO−A (6); and P0_O−P0_A /P0_R−P0_A (2). Stochastic tapes are averaged
within each of32 worlds before any interval; C's single trajectory is paired
to that world, not duplicated into independent observations. Use one fixed
`default_rng(29832051)` integer index matrix of shape(20000,32), reusing it
for every level and contrast; report pointwise2.5/97.5 percentile bootstrap
intervals with NumPy's linear quantile convention. These are descriptive
world intervals conditional on one acquisition instance and one inherited
parent, without training-population, simultaneous37-comparison or equivalence
coverage. Keep the32 signed world values and all adverse worlds, including
mixed component outcomes. No MEI, universal service floor, late weighting
change or after-the-fact default policy selection is introduced.

Every level/contrast includes native mean J, service, quality; within-episode
service p10 and minimum; zero-service steps/episode incidence and longest
team-zero-service streak; per-UAV mean travel, mean/end heights and relevant
height-bound visits; active-transmitter ticks/fraction and mask bit switches;
old-mask censored decision rows, visible-user/peer counts, eligible c==0 and
fallback exposure; gate requests/OFF choices and prediction/activation
diagnostics; actual controller/helper/neural/model/link/draw/cache counts;
query/gate/native/write/complete CPU and wall readings with their scopes.
Episode and world outputs retain program identities, seeds, artifacts,
failures, all final adverses and acquisition pair details. These are team
service measures; they do not establish individual-user continuity, battery
savings or physical timing guarantees.

The independent scalar reader is included from the start: all507904
post-step user/peer radio and greedy assignment states, all126976 setter
refreshes, old-mask decision observations and terminal observations; every
actual motion/helper/C/logit/hidden/cache/navigation/private-draw/held-command
and gate law; all512 pair prefixes/features/native labels; both scalers,
objective/predictions and normal-equation residuals without a new solve;
the full16 levels/37 contrasts and signed adverses. It imports no native
radio/assignment routine as its numerical proof and performs0 environment
steps/0 optimizer steps/0 refits. Actual policy reconstruction can incur the
same complete policy/model ceilings again. Discrete assignments/eligibility/
selected categories must match; small continuous numerical tolerances will
be justified from scalar/vector arithmetic in the engineering checks, never
used to excuse a changed scientific action.

The accepted full price and all six outcome branches remain as in the
original advice. The two-fit/1984-episode purchase adds507904native steps to
the retained B02–B07 bill of14fits/two calibrations/2539560native steps
(plus separately retained older B01 and support). Those cumulative counts
do not turn budgets into allowances or create a retry entitlement. Estimated
worker+complete-reader CPU is0.5–2h, support6–12h, streaming RSS0.4–1.0GiB
per process, new canonical durable bulk0.7–1.5GiB and separate working disk
headroom1–3GiB; all estimates, no hard cap or measured guarantee. Worker and
reader run sequentially, single-threaded numeric libraries. Source snapshot
size is unmeasured. Current remote-first feasibility and fresh actual-node
memory/load admission will be assessed at the real launch boundary; existing
parent B08 and waiting B06 handles remain untouched.

The expected intermediate change is a nonconstant native consequence
prediction with actual requested/executed gate choices; the native prediction
is a conditional HIDDEN increment over RAW and useful comparison with the
competent complete alternatives. Failure of that pattern weakens this finite
purchase, not local-information sufficiency or all learning. A RAW/simple-rule
positive is a capability to retain. HIDDEN-only narrow superiority, active
adverses, unresolved intervals and nonactivation follow the original distinct
branches without rescue thresholds, extra worlds or fits. Any later
replication or different question returns to Root's cross-question choice.

<a id="b08-l0"></a>
### B08 L0: implement the frozen local gate study and complete scalar reader

Deliverable: a direction-local, admitted detached worker plus sequential
complete reader for the exact contract above, with streaming raw/evidence,
honest counters/resources and all required scalar/policy/fit checks. New
entrypoints are
`experiments/candidates/uav_fleet_adaptation/b08_local_gate/run.py` and
`read.py`; implementation/tests remain in matching `b08_local_gate/`
directories. Existing core, other directions, frozen source/assets and their
entrypoints are read-only dependencies.

One bounded Implementer assignment owns **only** `b08_local_gate/policies.py`,
`fit.py` and their `test_policies.py` / `test_fit.py`. Its behavior change
is the original N5 motion law with same-forward hidden extraction plus the
two fixed gate feature/fit/prediction laws. The DM owns `contract.py`,
native collection, independent scalar reconstruction, reduction, assets,
runner/reader integration, all other tests and NOTES/RESEARCH. The helper
gets no Git index/commit, notebook, launch, scientific selection or child
ownership. Author on the shared main checkout; other writers' edits are
preserved. Interfaces are explicit: motion `Policy(parent,actor,world,
agent,sampling_root).query(old_row,tick,nav)` returns original law fields,
features and cached hidden for neural parents; gate features are125/253 FP64
vectors derived only from that local answer; ridge artifacts carry scaler,
coefficients/intercept, predictions/objective and residual telemetry.

Preserve the original114 FP32 one-row actor operations, helper/nav and
27-category FP64 softmax/private right-search CDF. Bstar0 uses temperature2;
Hdirect uses MemoC-derived features/nav, one private P0 logit cache and the
existing both-T/H constructor on every law call, with no duplicate analytic
helper. C/Q10/G retain their original laws and cache semantics. The new
original-Student adapter has no count branch. Synthetic identity checks
against the original/zero-count N5 paths must cover masked rows, fallback,
cache hits with fresh uniforms, aliases and deterministic zero/ties. Capturing
the second ReLU must not invoke a second forward or change FP32 grouping.

Focused checks cover original reset/layout identity and constructor count;
old decision versus applied/refresh masks; forced pair prefixes and separate
RNG domains; censorship/reactivation and four-tick holds; independent scalar
user/peer SINR, assignment/observation/reward and threshold/tie behavior;
correct sum-SSE lambda and unpenalized intercept, constant-column scaling,
finite residual bounds and no reader refit; streaming raw completeness,
tamper detection, fixed counts/37 contrasts and production admission/refusal
of fixture/duplicate/scientific-output substitution. Tests use synthetic
assets and small correctness fixtures under the existing pytest scratch
lifecycle, with no production worlds/assets or result-bearing pilot.

The DM will inspect the returned diff/checks, finish integration, and obtain
independent high-risk engineering review of masking, numerical identity,
RNG, replay, input identity and the complete scalar reader before acceptance.
Source/input publication precedes result execution. An accepted operation
keeps its original status handle and deterministic observer; the native child
turn remains active through collection and full reading. A separate
ResearchCritic diagnoses the complete result, then the DM publishes its
standing/directly affected background and measured cleanup. Stop only the
dependent action on a concrete semantics/resource/writer/uncertain-effect
conflict; no repair changes the frozen scientific exposure automatically.

**Prospective constructor-count correction, before implementation/exposure.**
The direct source check of `ParallelToArrayAdapter.__init__/seed` shows that
it seeds its own Gym generator but does not reset the native environment.
The original factory therefore performs **one** base-constructor priming
reset, not the two forecast in the paragraph above. The selected reusable
environment adds275 native dense power slots for this one priming reset;
1984 explicit episode resets and all scientific counts remain unchanged.
A focused constructor test will enforce the actual topology. This corrects
an unexecuted bookkeeping assumption, not the original reset population.

**B08 bounded reader implementation handoff, before execution.** The existing
Implementer also owns `b08_local_gate/reference.py` and `test_reference.py` for
one additional behavior: reconstruct every motion answer and original policy
counter from saved old-mask rows using the original B02 policy/MemoC and the
frozen analytic laws, without importing the new collector or `Policy` as its
proof. This lends only those two paths; it does not change the scientific
scope, fits, exposure, interface, or the DM's reader acceptance. The DM keeps
all scalar, pair, fit, result-reduction and runner integration code. Checks
use synthetic assets/off-panel rows, including censored rows, fallbacks,
cache hits and fresh addressed draws. No production query, launch, Git index
mutation or child is authorized by this bounded handoff.

<a id="b08-engineering-acceptance"></a>
### B08 implementation and prelaunch engineering reading — 2026-10-01 UTC

The Implementer's original `policies.py`/`fit.py` change and the separately
bounded `reference.py` reconstruction have been inspected and accepted by
the DM. Synthetic tests establish original FP32 one-row logits/second-ReLU
capture without an extra forward, private caches and fresh innovations,
all27 categorical addresses, the six motion laws, deterministic gate ties,
training-only population scaling and sum-SSE/unit-ridge stationarity. The
reference independently constructs both T and H on every Hdirect law call,
including cache hits; its two-vector cost is actual replay work as well as
reconstruction of the worker's charge.

DM integration now executes the complete prescribed acquisition, two solves,
final panel and independent reader. Raw records distinguish old decision rows,
setter refresh rows and scored endpoints; every forced pair keeps its complete
prefix and full native label. A short off-panel fixture uses synthetic actor
seed90829, two training worlds90811/90812 and final world90813 atH8, covering
all30 final program/tape cells. Each such fixture invocation is34episodes /
272native fixture steps and two synthetic ridge solves, separate from the
selected scientific2fits/1984H256episodes. It is a correctness fixture, not
production P0 evaluation or a result-bearing pilot. The reader test forbids
`np.linalg.solve`, then verifies every saved scalar state/policy and all fixed
statistics. Tamper tests cover old-versus-refreshed rows, scalar SINR, pair
prefix, fit diagnostics, world identities and artifact hashes; production
rejects no admission, existing scientific output, fixture population and a
second reader reservation.

The combined suite passed71tests in4.14s on the configured local scientific
interpreter, with14 pre-existing Matplotlib/pyparsing deprecation warnings.
The independent engineering Reviewer separately ran71tests in4.22s and read
all14 source modules, all five test files, the directly needed original host,
adapter/controller/model/radio dependencies and all five original source pins.
Its one medium finding was failure accounting: after a complete episode audit,
a subsequent pair-ledger assertion could fail before the just-completed
branch's policy totals entered the persistent report. The DM accepted the
finding and moved that publication immediately after the episode audit.
The added regression changes only a pair's reported target and checks that
both completed branches' replay costs survive exactly once. The focused
integration suite passed8tests in4.09s; original partial-episode counters
remain in the inflight failure record. Independent patch closure follows
before source acceptance for launch. No motion, gate, fitting, RNG, scalar
assignment or frozen-exposure defect was found in the rest of the review.

**Prospective placement, before result execution.** The configured primary
`wsl_4070` is suitable for this new single-threaded CPU worker/reader and has
the canonical424487-byte P0 file at its original B02 location (existence/size
checked, no model loaded or queried). At03:40–03:42UTC the destination reported
load0/0/0, about14GiB available memory and791GiB filesystem free. Its configured
GCC Python3.10.21, NumPy1.26.3 and Torch2.7.0+cu118 imported successfully with
one CPU numeric thread. The earlier remote interpreter failures remain
unresolved; these checks do not establish a cure. Current published placement
allows new gate work on configured preference with fresh feasibility/admission.
The remote canonical compute config and maintained launch script match the
current published bytes; the existing local pause/active/lead control fields
also agree, while historical standing prose is older. Existing remote checkout
edits and accepted operations are preserved; only a launcher-owned committed
source snapshot will execute the new inputs. No asset staging copy is needed.
Fresh actual-node memory admission will occur at release, and failure preserves
its original attempt without an automatic retry. No B08 result operation,
production asset load, learned-gate fit or production world query has occurred.

**Independent patch closure:** the Reviewer verified the reordered report
publication and the injected pair-ledger regression, and returned “No material
finding remains in B08.” The DM accepts the reviewed implementation for the
fixed purchase. The review's scope remains syntheticH8 correctness; it is not
production H256 evidence or a result. Source/input publication and actual-node
admission remain separate next actions.

**Pre-admission request corrections, zero scientific exposure.** Exact reviewed
inputs were published as `21de06cd2cd465d3962bbe95183bbfc7c3eddeb1`.
The first remote supervisor request exited2 at shell parsing before invoking
the admission launcher: `agent-task` joins argv with `$*`, which discarded the
lead argument's quoting. Source inspection identified that concrete cause;
passing one fully quoted command string fixes it. Its original task/log and
[compact failure](../../../../runs/uav_fleet_adaptation/b08_local_gate_a01/supervisor-request-failure.json)
are retained. The corrected supervisor invoked the launcher, which refused
before admission because the canonical ignored P0 file lies inside the author
root and is absent from the published source snapshot. Native status confirmed
that no output/operation reference existed after each refusal; no worker,
production model load, world query or fit occurred.

That actual snapshot-input constraint corrects the earlier forecast that no
staging was needed. One exact424487-byte P0 consumption copy is now declared
at `wsl_4070:/home/wu/hmasd-inputs/uav_fleet_adaptation/b08_local_gate_a01/S.pt`,
outside the source root. Original and copy were SHA256-verified against the
already frozen P0 digest; no source/model/world semantics change.
[Staging identity and allocated size](../../../../runs/uav_fleet_adaptation/b08_local_gate_a01/input-staging.json),
[pre-admission refusal](../../../../runs/uav_fleet_adaptation/b08_local_gate_a01/snapshot-input-refusal.json).
The next request keeps the same scientific output tag and published source;
it is the first possible scientific admission, not a duplicate accepted run.
The pre-admission source snapshot and the temporary consumption copy will be
checked for live consumers and reclaimed at closure. Remote fetch succeeded
and verified the published source, while Git's unrelated automatic maintenance
reported an existing bad-tree/repack warning; no repository repair or history
change was attempted, and snapshot preparation itself succeeded.

<a id="b08-accepted-operation"></a>
### B08 accepted worker and complete-reader chain — 2026-10-01 UTC

The single scientific operation was accepted at03:55:27UTC from published
source `21de06cd2cd465d3962bbe95183bbfc7c3eddeb1`, after the two explicitly
non-admitted request corrections above. The native
[manifest](../../../../runs/uav_fleet_adaptation/b08_local_gate_a01/launch-manifest.json)
and [fresh actual-node preflight](../../../../runs/uav_fleet_adaptation/b08_local_gate_a01/admission-preflight.json)
are collected unchanged; physical/effective available memory was15579402240B
against the4294967296B floor. The bound outside-root consumption copy is used
only to satisfy the snapshot input contract; the inherited asset digest and
all frozen study semantics are unchanged.

The assigning native child resumed its previously stopped deterministic
observer, registered job `b08-a01`, and adopted generation35 against the native
operation in the manifest. The first observed native status at03:56:44UTC is
accepted/running/consistent, with the original runner and supervisor both
present and no terminal witness. The child remains active through the complete
worker and its sequential scalar/policy/fit reader; checkpoint rearming will
observe this same operation, never restart it. Acceptance and healthy initial
observation are not a scientific result. The exact1984episodes/twofits and
one full reader remain the stopping contract.

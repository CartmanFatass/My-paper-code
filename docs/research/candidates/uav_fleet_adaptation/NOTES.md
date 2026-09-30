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

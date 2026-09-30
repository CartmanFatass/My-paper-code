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

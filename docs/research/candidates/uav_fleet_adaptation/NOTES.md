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

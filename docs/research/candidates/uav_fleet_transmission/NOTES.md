# UAV fleet transmission

## 2026-09-30 — B01 prospective complete configuration and frozen-asset study

Direction: `uav_fleet_transmission`; native DM `/root/dm_fleet_transmission`, assigned by
Root on shared main at `/home/fires/hmasd-wsl`. One result-bearing study is active. This
is an exploratory configuration/control-rights/asset-use comparison, with no new learning,
novelty, pure-N, interference-recovery-fraction or skill-causality claim.

### Question, inheritance and selection

Under the original N4/N8 S1 execution-information clock, can ordinary transmitter management
improve complete native service, and does either already-paid final45 H6/SET asset retain
use beyond a competent ordinary physical controller with the same public model and mute rights?
The consequential observation is that old H6 beats contemporaneous SET at N4/c10 and N8/c10,
yet absolute service declines and SINR-ineligible users increase. Capacity still matters:
N4/c10 has roughly 4.14 eligible-unserved users. The new intervention changes interference,
assignment, discovery and subsequent learned histories; it cannot isolate an interference share.

Relevant published background: [RESEARCH topic 3, native S1 capacity/eligibility](https://github.com/CartmanFatass/My-paper-code/blob/cf45e361cba3e8f3230f8d33a8de7175492c4771/docs/research/RESEARCH.md#3-marl-增加的是联合行为和信息结构),
and [complete selection advice](https://github.com/CartmanFatass/My-paper-code/blob/cf45e361cba3e8f3230f8d33a8de7175492c4771/docs/research/RESEARCH.md#portfolio-review-2026-09-30-periodic-efficiency-and-fleet-control).
The capacity identity and conditional one-instance results require separate eligibility and
truncation readings, a strong ordinary controller, and restrained interpretation of N4→N8.
The complete Pro advice was read, including source-access limits. Root adopted its material
dissent against undefined C/E: the concrete one-pass C_N/E below replaces that ambiguity.
Root's independent selection critic supports this revision; reuse covers this actual design,
so no duplicate selection/Pro round is introduced. Independent engineering review and full-result
scientific diagnosis remain distinct. No literature novelty is asserted.

Original evidence/source: `c770220d3abc4e32a9e80347dea87bdea88080e8`, result
`1847293df231c8b567ff9abb73270c81404799ba`,
`runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/summary.json`.
The N5 radio E positive mean and adverse world29305038 (J −.055369, service −5.710938)
are contrary context (source `4d5ccefe6c90dbc6c132bcc71ffe6dd73535ae47`, result
`46fa68117e523d22f88d617ec35f248cf04ee912`), not an N8 forecast. The N5 LocalController
is 3dB/four-peer/four-step specific and is not the new ordinary comparator.

Constructive prediction: E will remove some unhelpful simultaneous transmission, lower
ineligibility, and improve complete service/J, potentially more at N8. Competing prediction:
lost active capacity, changed discovery, ten-step commitment and frozen actors' unseen silent
feedback will offset immediate gains. All-on belongs to each search set but does not guarantee
nonnegative complete-trajectory effects. C_N/E tests the conditional value of already-paid
assets beyond ordinary use of the added resources; it is finite, discrete, one-step and one-pass,
not an optimum or a test of whether learning is necessary.

### Fixed panel and decision contract

- S1 static50users, N in {4,8}, capacity10 each, H500. Five programs per N:
  H6/all-on, H6/E, SET/all-on, SET/E, C_N/E. Sixteen common new worlds, fixed before outcome
  exposure: IDs `29310000..29310015`; SeedSequence address `[260930,14,world_id,stream]`,
  stream1 users, stream2 eight-UAV positions, stream3 runtime (with N appended). NumPy
  RandomState draws uniform x/y in [0,1000], UAV z in [50,150], member-major order, with
  N4 the first four of eight. No matching seed/identity found in current candidate/config/result
  sources before declaration. World generation does not inspect outcomes.
- Total 160 complete episodes / 80,000 native team steps / 0 new fits / 0 updates. No extra
  C_N/all-on, N6, capacity-matched cells, horizons or training are selected. The 16 worlds
  condition on two old training instances; they are not 16 training replications. N4→N8
  jointly changes vehicles and total capacity40→80.
- Native 0dB threshold, capacity10, original objective
  `J=.7*served/50+.3*mean_connected_quality-.1*(mean_all_UAV_height-50)/100`.
  Silence removes neither vehicles nor their height, movement or N reward scaling.
- H6 coordinator and SET snapshot consume their original global-state fields at t=0,10,...,490;
  local observations and recurrent processing remain every tick. E and C_N use float32
  public coordinates at the same boundaries, retaining quantization error. No fresh global
  simulator fields between boundaries. Added public physics/search/mute rights are common
  resources. Abstract synchronous central compute; no N5 link bitrate/delivery/deadline claim.
- At a boundary the frozen actor steps exactly once under old state/observations/mask,
  progresses its ordinary skill/snapshot/GRU state and outputs the primitive command.
  Original componentwise clip [-1,1] then predicts one next position from the legal snapshot.
  E enumerates all nonempty masks at that position (15/255), ranks native J then served,
  retains the old mask on exact computed-value tie, then lowest bitmask integer. Apply before
  transition t, hold through t+9; do not refresh/reinvoke the actor. Only the mask is held.
  Last search scores position491 while all500 transitions count. Reset mask is all-on.
- C_N each tick starts from previous actually ISSUED discrete joint commands (zero at reset),
  passes members in `((t+j)%N)` order, and tries the lexicographic 27 commands in {-1,0,1}^3.
  Each team prediction starts from the same prestep position; other commands use current pass
  choices. Native per-axis velocity/position clipping, without diagonal normalization.
  Rank larger native J, more served, smaller summed actual Euclidean team displacement,
  entering coordinate command, then fixed lexicographic order. Exact computed ties, no
  adjustable tolerance. Preserve issued commands after boundary clipping. Propagate its
  public position between anchors using those commands. At boundaries finish motion under
  old mask, then E once at chosen position; no joint motion/mask search or second motion pass.

Primary readings are per-world full-service and J increments E−all-on for each asset/N and
paired N8−N4 increment interactions; compare each asset/E to C_N/E. Read all signed worlds,
quality/height/path, eligibility versus capacity, low service tails/zero runs, active masks
and actual cost. Descriptive paired world-bootstrap intervals are conditional on these assets,
not learning confidence or an equivalence/adoption test. Preserve adverse worlds. Positive
mean E with strong C_N retains ordinary management; an asset beyond C_N may retain use; only
instant gains rejects this finite package; unresolved precision does not warrant more worlds.
Any successor, training or richer clock is a separate investment choice returned to Root.

### Cost, resource dependency and assets

Algorithmic requests: 648,000 E mask candidates = 3×16×50×(15+255), plus 2,592,000 C_N motion
candidates = 16×500×(4+8)×27. Separate requests, actual/unique scored candidates, cache reuse,
geometry computations, verification and pure-reader work. Old80k worker354.661wall/1437.160498
CPU-s at4 Torch threads is only an anchor; old N5 reader984.61CPU-s versus worker188.10 warns
against omitting reading cost. New engineering/support/worker/reader timing is not yet known.
Old two final45 training attempts and their selection exposure remain inherited sunk cost.

Root verified required files on wsl_4070 in the old action-law worktree. Preserve it and its
consumers. H6 `s1_action_law_b03_h6_clip_s942201/checkpoint_45.pt`: 23,073,626 bytes,
SHA256 `98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343`;
SET `s1_action_law_b03_set_clip_s943201/checkpoint_45.pt`: 20,968,771 bytes,
SHA256 `03f4f070e30b34fb61cd45820f1579ebde185c9417468689bd0c2e7ef60c0a3b`.
Both under `/home/wu/hmasd-worktrees/agent-count-action-law-20260922-b03/runs/agent_count_generalization/`.
Use original saved configs/final45, normalizers, recurrent/skill reset and clip law. No seed
substitution/retraining if recovery fails. Training commit89486d32e alone lacks posttraining records.

G (`/root/dm_periodic_efficiency`) has first use of wsl_4070 for deadline-sensitive work.
Prepare here; result evaluation or heavy remote work awaits Root's concrete calculation-release
fact, then actual fresh node admission/current active ownership and published source. This is
a CPU/timing dependency, not a science-approval gate. If integration needs a large refactor,
return its cost/scope contradiction instead of extending the finite study.

### L0 — bounded host and ordinary decision layer

Deliver a direction-owned native S1 mask wrapper, new matched worlds, public-state decoding,
one-step native public scoring, E mask enumeration and concrete C_N motion policy. Own
`experiments/candidates/uav_fleet_transmission/{host.py,control.py,__init__.py}` and matching
`tests/experiments/candidates/uav_fleet_transmission/test_control.py`. DM owns runner, reader,
remaining tests and this notebook. No shared core, old evaluator, RESEARCH, index or remote writes
are lent. Native UAVBaseStationEnv has a scenario override incompatible with the generic
mask setter's keyword: adapt locally and reuse the native radio/assignment/observation paths.
All-on must remain equivalent; do not repair inherited observation ordering in this study.
Use exact float64 native scoring arithmetic from quantized public coordinates and original
float32 action arithmetic where applicable, with counters for requests/geometry/reuse.

Checks: all-on native state/action-independent equivalence; muted interference, eligibility,
assignment, user/peer visibility and all-UAV height/N scaling; snapshot timing and no truth
refresh; all nonempty masks and deterministic ties; diagonal/per-axis clipping and retaining
issued commands; one-pass motion under old mask before one E choice; public score against
native0dB physics on synthetic fixtures; RNG invariance. Tests use declared fixtures, not
new study worlds. Preserve 0dB, native constructor/reset and immutable world arrays. Stop at
this behavior and report unsupported semantics/cost; no scientific launch or result exposure.

## 2026-09-30 — implementation, independent engineering acceptance and remaining asset check

The selected concrete contract and independent critic's full response are now published at
`b975b4534d001d470acf2f416785b54e8b5661f5` in the
[retired completed review](../../archive/2026-09-30/RESEARCH-periodic-efficiency-and-fleet-control.md#decision).
The active direction/lead and node canonical policy have been published by Root. The separate
critic specifically retained old-mask motion then one E choice, issued-command persistence,
exact ties and the expanded motion-candidate cost; no unresolved selection dissent remains.

Accepted the bounded Implementer's host/control layer and focused checks. It reuses native
radio/assignment and visibility, overrides Scenario1's mask-call signature locally, and caches
equivalent candidate/row geometry within one decision. The 0dB batch scoring uses at-most-one
eligible transmitter to select each member's top10, with native greedy fallback if numerical
eligibility overlaps; tests compare every15/255 mask and scalar coordinate enumeration exactly.
Only owned paths changed. Original loader, saved-config guard, restore and final45 digest checks
are reused directly; the four named legacy files are identical to the original `c770...e8`.
No broad refactor or alternate training asset was needed.

The complete runner writes per-episode compressed trajectories and decision traces outside
compact JSON. It invokes a pure saved-data reader only after all160 episodes and final frozen
checks. That reader checks every native position/action/assignment/SINR/peer/local-observation,
0dB reward and original N scaling, and reconstructs every C_N pass and E mask set from the legal
public anchors. It never steps an environment or runs an actor. Actor history equivalence is
tested separately. Verification tolerance for adapter scalar×N versus native J is fixed at
1e-14 absolute for averaging roundoff; decision ranks and all other exact checks use no tolerance.
The reader re-materializes each NPZ once per episode. Its candidate/physics CPU is separately
measured; full worker timing also includes recording, loading and final checks. Raw outcome
data remain necessary evidence; runtime log/cache scratch is not a second evidence copy.

Independent `hmasd-reviewer` `/root/dm_fleet_transmission/engineering_review` traced masking,
feedback, reward scaling, once-per-tick actor progression, reset/RNG/config, public precision,
old-mask C/E order/ties, batching/caching, admission and the full reader. It found one real
certification defect: a standalone reader could mark a full panel complete after a failed final
freeze check. Adopted the repair: only an explicit worker-complete marker after checkpoint,
parameter/normalizer/optimizer and full-panel checks permits certification; source/asset/frozen
checks are revalidated. A reader-only technical failure may be repaired over that intact panel,
without changing or rerunning any episode. The regression rejects postcollection worker failure
and parameter, normalizer, optimizer or checkpoint drift. Reviewer reports no material finding
remaining after inspecting repair and tests. It did not independently replay trained actors.

Local correctness verification: 20 initial tests passed; after the repair,6 integration tests
passed (2s class of runtime). Four actual H6/SET×N4/N8 final45 equivalence tests are currently
skipped solely because binaries are not staged locally. These require exact supplied checkpoints,
compare22 sequential decisions across0/10/20 boundaries twice with an intervening recurrent/skill
reset against the original all-on path, and verify no final model/normalizer/optimizer change.
They must pass before result launch. All numerical/control fixtures used old or synthetic
worlds; the declared new panel has not been evaluated.

Root reports G accepted on wsl_4070 at02:47:10UTC, source8ab72e5e2, for its deadline-sensitive
192-episode worker. N therefore continues only local work until G's calculation release. Planned
N tag is `b01_native_s1_a01`; the immutable launcher snapshot will use the published source,
and checkpoint bytes may be read directly from the verified original worktree paths above.
Only the two exact binaries will be copied to owned local temporary input paths for the required
equivalence checks; those redundant check copies will be deleted after use. No old worktree GC.

## 2026-09-30 — final frozen checks and prospective local-node choice

Root established G's calculation release: valid native exit1 at02:52:25UTC, absent worker and
supervisor, matching source/identities. G's scientific result is not completed or adopted by
this fact. Both declared checkpoint binaries were then copied into
`temp/directions/uav_fleet_transmission/final45_checks/<original-tag>/checkpoint_45.pt` and
their exact sizes/SHA256s above matched. All four actual final45 H6/SET×N4/N8 equivalence tests
passed in5.98s (352 native correctness transitions across both paths/resets), including exact
actions, observation/state progression, recurrent/skill runtime and unchanged frozen digests.
Twenty-one other unit/integration tests pass. Existing one-label debug-standard-deviation and
Matplotlib deprecation warnings do not enter actions, native metrics or the frozen digests.

Before any N acceptance, Root supplied the concrete new runtime reliability evidence: G
terminated with CPython `SystemError: unknown opcode` in NumPy `_all_dispatcher`, reached
through `uav_radio.py`'s `np.all(mask)`, after101complete episodes+12steps. Similar peer runtime
failures are recorded, but the root cause is unproven. This is technical missingness, not a
scientific result against G or masking. I choose configured `local_linux` for N's first attempt
because that unresolved repeated failure family makes the remote node unsuitable for this
bounded full-panel collection. No N run has started, moved or been retried. This choice follows
the configured fallback rule and Root's explicit resource release, with no extra outcome pilot.

Actual local runtime: Python3.10.20 (Clang22.1.3), NumPy1.26.3, Torch2.7.0+cpu, x86_64 WSL2.
Keep four Torch threads and one interop thread; all actors remain CPU float32, public coordinates
retain float32 quantization and native physics remain float64. The final45 equivalence checks
ran on this node. This is not a cross-node bitwise replay claim; old remote timing remains only
a historical anchor. An actual-node memory preview at02:54:38UTC found9,276,903,424available
bytes versus4,294,967,296floor; the launch kernel will recheck immediately before release.
G's potential recovery stays outside N's active local calculation window under Root allocation.

The runner/reader now report process-lifetime user/system CPU (native threads included), child
CPU separately, the scoped collection and reader intervals, versions/thread counts, and
process-lifetime RSS explicitly. Collection interval timing excludes module imports/admission;
process totals and the native exit record retain that broader cost. These telemetry additions
change no decision or scientific exposure. Full panel, declared seeds and all160 episodes remain
fixed. The accepted local worker will consume the verified staged checkpoint paths; the source
remote originals remain required, untouched assets. Canonical bulk retention and actual cleanup
follow terminal collection, not an assumption that launch acceptance is a read result.

### Pre-admission input-location refusal and correction

The first native launcher invocation at source `a6c31f8e8bc54e54de2555086160375ed661664b`
returned exit4 before acceptance: `absolute author input is absent from published snapshot:
/home/fires/hmasd-wsl/temp/directions/uav_fleet_transmission/final45_checks`.
Same-target `status` reports that the status reference does not exist; the scientific output
directory is absent. No N worker, episode or fit started. The launcher created only an
unclaimed source snapshot `a23f403740a04e79acd7cf29c433219e`, retained for supported exact-target
cleanup after reconciliation. This is a known input-binding refusal, not an uncertain result
launch or a failed scientific batch.

The ignored author scratch is intentionally outside the published snapshot. Move only the
two verified binaries to external direction-owned local staging,
`/home/fires/hmasd-inputs/uav_fleet_transmission/b01_native_s1_a01/<original-tag>/checkpoint_45.pt`.
Sizes and hashes were rechecked after the move; the old temporary files/directories are gone.
No additional copy, model, seed, numerical contract, exposure or node was introduced. The
actual source and scientific arguments are unchanged except this outcome-blind checkpoint-root
location correction. A fresh admission invocation may now use the same unused output tag;
no accepted operation is retried. The move itself reclaimed0 disk bytes.

### Accepted B01 local operation

Native admission accepted the corrected request once at02:58:03.234736UTC on `local_linux`,
source `a2f62e613a12331ad380876a6c764f8a46a893ee`. The exact invocation, snapshot, claim and
native process identities are in [launch-manifest.json](../../../../runs/uav_fleet_transmission/b01_native_s1_a01/launch-manifest.json),
with [fresh admission](../../../../runs/uav_fleet_transmission/b01_native_s1_a01/admission-preflight.json)
and [runner config](../../../../runs/uav_fleet_transmission/b01_native_s1_a01/config.json).
The complete160episode collection followed by its full pure reader belongs to this single
accepted operation. Launch acceptance is not a completed scientific result.

`tools/hmasd_wait.py` generation1 is armed against the manifest's original operation reference,
owned by this native child (`01a0f02a-2102-7aa3-be5a-adfb99e49910`). First drain at02:58:17UTC
observed accepted admission, matching live runner/supervisor identities and consistent records.
The child remains active through same-handle observation and complete reading; no queued App
wake is assumed to restore an unloaded child. Root has the concrete acceptance fact for node
allocation. No partial outcome has been used to alter, shorten or extend the fixed panel.


## 2026-09-30 — complete B01 collection and verification

The one accepted local operation exited0 at03:08:08UTC with a valid native
[exit witness](../../../../runs/uav_fleet_transmission/b01_native_s1_a01/process-exit.json);
runner and supervisor are absent and admission/identity records remain consistent. All160
H500 episodes and80,000 native transitions completed, with0new fits/updates. The
[compact summary](../../../../runs/uav_fleet_transmission/b01_native_s1_a01/summary.json)
and [complete saved-data reading](../../../../runs/uav_fleet_transmission/b01_native_s1_a01/reading.json)
bind all320 raw/decision files by size and SHA256. Reading SHA256 is
`ebc4a7cf316c008b49bf8615cbb0238fe0c4a8756612c3b1b9ce4f212798695d` (279111bytes);
summary SHA256 is `1020f99704c1fb5a4742be314dc45db0bce8fad57e27d8e6a79e635ae80837af`
(311167bytes). Source remains `a2f62e613a12331ad380876a6c764f8a46a893ee`.

Both original checkpoint file hashes and all four H6/SET×N4/N8 parameter digests matched
before/after; normalizers were unchanged and every optimizer hook count is0. The full pure
reader accepted all80,160 recorded native snapshots, original action clipping and N scaling,
mask-dependent user/peer feedback, all50 mask decisions per E episode and all500 C_N motion
passes per C episode. No scientific episode was retried or discarded. The two inherited
one-label debug-std warnings remain diagnostics only; all required recorded metrics are finite.

The worker used450.196771wall/1374.205686CPU seconds. The complete reader added
152.016061wall/151.953611CPU seconds; total run_study interval was602.244175wall/
1526.190628CPU seconds, excluding admission/module import. Broader process lifetime self
user/system CPU was1520.736398/8.263752seconds, with child user/system .017681/.007843
seconds separately. Peak RSS was680576KiB for the whole process, not a separate reader peak.
These timings are for this local Python3.10.20/NumPy1.26.3/Torch2.7.0+cpu runtime with four
Torch threads; they are not a controlled speed comparison with the old remote anchor.

Worker requests/scoring: E648000/648000,0cached; C_N2592000/1646158,945842cached.
Computed/reused geometry rows: E27994/5012006; C_N1726158/9229586. Full reader repeats
those candidate counts independently as verification work, in addition to native-physics
reconstruction; neither reader nor caching reduces declared exposure. Two old fits remain
in the lineage: each360000training team steps/720episodes/45updates, with each old final
record also carrying96000evaluation team steps. New world replication is conditional on
these two fixed trained instances.

Observer generation1 delivered READY at03:08:26UTC for the same operation. Its attempted
native-child App queue wake was rejected (`-32600`, direct app-server input is not allowed
for multi-agent v2 sub-agents); the still-active DM directly drained the terminal event, so
no observation or worker was rebound. Event164c2ca40d1219f193449031/wake
fea443aa-70cd-4bd5-a568-ca91df4d83f1 was consumed by same-handle rearm to generation2,
then observation was stopped; scientific work is unchanged. Root received the concrete
calculation-release fact. Full scientific diagnosis is in progress in the independent
`hmasd-research-critic` context `/root/dm_fleet_transmission/result_diagnosis`; technical
completion alone is not the interpretation below.


<a id="b01-complete-reading"></a>
## 2026-09-30 — complete scientific reading, retain conditional capabilities and end this screen

Complete compact evidence is published at `6b51a962e2295b44ea2d79fba128a943e761c39b`,
from fixed source `a2f62e613a12331ad380876a6c764f8a46a893ee`. All readings below use the
complete160episode panel. Intervals are paired percentile world-bootstrap95% descriptions
(10000resamples, seed26093014) conditional on the two old assets, not training-population
inference, an equivalence test or a deployment acceptance rule. No outcome-dependent extension
or selected-world policy is included. The original capacity/eligibility background in RESEARCH
and the original N5 adverse example still apply; current published topic3 is revised by the
configuration-dependent result here, without replacing those original sources.

### Complete levels and planned contrasts

Path is mean native distance per UAV over H500. Height penalty is the already-weighted
all-vehicle term in J, including silent vehicles; it is not a battery measurement. p05 is
the within-episode service quantile averaged across worlds.

| Program | J | Served/tick | Quality | Height penalty | Service p05 | Path/UAV | Active transmitters |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| N4 H6_all | 0.542100 | 34.945250 | 0.233419 | 0.017159 | 32.312500 | 19673.455 | 4.00000 |
| N4 H6_E | 0.522050 | 33.470875 | 0.243365 | 0.019552 | 30.562500 | 19062.849 | 3.68625 |
| N4 SET_all | 0.488458 | 32.408750 | 0.210492 | 0.028412 | 26.934375 | 13237.126 | 4.00000 |
| N4 SET_E | 0.482620 | 31.701500 | 0.231766 | 0.030731 | 28.000000 | 12849.328 | 3.60625 |
| N4 C_E | 0.555347 | 33.222500 | 0.301040 | 0.000080 | 33.250000 | 643.150 | 3.43500 |
| N8 H6_all | 0.462094 | 30.488625 | 0.165351 | 0.014352 | 24.618750 | 16032.685 | 8.00000 |
| N8 H6_E | 0.558437 | 36.723750 | 0.213545 | 0.019759 | 33.996875 | 14690.596 | 4.49125 |
| N8 SET_all | 0.271645 | 19.372875 | 0.146196 | 0.043435 | 8.306250 | 12096.382 | 8.00000 |
| N8 SET_E | 0.526565 | 34.402250 | 0.214639 | 0.019458 | 29.934375 | 10990.063 | 4.23625 |
| N8 C_E | 0.624592 | 39.718875 | 0.228697 | 0.000081 | 39.750000 | 250.817 | 4.37375 |

| E minus all-on | Mean delta J [95%] | Mean delta served [95%] | J positive/negative/zero worlds |
| --- | --- | --- | --- |
| N4/H6_E-H6_all | -0.020050 [-0.040268, -0.004164] | -1.474375 [-2.999784, -0.264750] | 3/10/3 |
| N4/SET_E-SET_all | -0.005838 [-0.021129, +0.009380] | -0.707250 [-1.549512, +0.106259] | 8/8/0 |
| N8/H6_E-H6_all | +0.096344 [+0.076764, +0.117212] | +6.235125 [+4.917091, +7.647019] | 16/0/0 |
| N8/SET_E-SET_all | +0.254920 [+0.221640, +0.297995] | +15.029375 [+13.172778, +17.281534] | 16/0/0 |

N8 E improves complete J and service in every world for both assets. The paired N8-minus-N4
E-increment interactions are H6 +.116393963J [+.087539954,+.150544523] and +7.709500users
[+5.699612,+10.053675]; SET +.260758551J [+.223566836,+.307823223] and +15.736625users
[+13.684331,+18.203138]. All16 interaction signs are positive for each asset and endpoint.
This supports configuration-dependent response. It does not identify a pure fleet-size effect:
vehicles, total capacity40→80, geometry and feedback all change between the two configurations.

The constructive complete-service/J prediction succeeds at N8 and fails at N4 for H6.
N4 SET has negative sample means but intervals spanning zero; this is unresolved benefit,
not an equivalence finding. Muting is active in13/16 H6 N4 worlds; the three entirely all-on
worlds are exactly unchanged. An absence of activation cannot explain the ten adverse J worlds.

| Asset/E minus ordinary C/E | Mean delta J [95%] | Mean delta served [95%] | J positive/negative worlds |
| --- | --- | --- | --- |
| N4/H6_E-C_E | -0.033297 [-0.061608, -0.007155] | +0.248375 [-2.090897, +2.402884] | 5/11 |
| N4/SET_E-C_E | -0.072727 [-0.090510, -0.054391] | -1.521000 [-2.978387, -0.016853] | 0/16 |
| N8/H6_E-C_E | -0.066155 [-0.086037, -0.046737] | -2.995125 [-4.669566, -1.339959] | 1/15 |
| N8/SET_E-C_E | -0.098027 [-0.116327, -0.080007] | -5.316625 [-6.968262, -3.815112] | 0/16 |

C/E has the highest mean J among all five programs at both configurations and the highest
mean service at N8. Its mean N4 service is below H6/all by1.722750users/tick while J is higher
by.013246859; H6/E also has a small uncertain mean service advantage over C/E. Five N4 worlds
have both H6/E J and service above C/E. At N8, H6/E exceeds C/E J in29310002 and service in
three worlds. These are retained tradeoffs and witnesses, not a usable rule for selecting the
winning policy by world after observing outcomes. C/E is neither uniformly dominant nor an
optimality bound. Without C/all-on, its complete usefulness cannot be assigned specifically
to muting.

H6 still exceeds SET under E: mean J gaps are +.039429834 at N4 and +.031872496 at N8,
versus +.053641953/+.190449204 under all-on. N8 service gap falls from11.115750 to2.321500.
That conditional asset gap remains real in this panel, but no longer establishes value beyond
the competent ordinary alternative. The gap change is not an explained interference fraction
or evidence that a specific learned skill caused either difference.

### Changed explanation, adverse outcomes and tails

The exact service accounting separates two competing consequences along the observed paths:
`50-served = ineligible + eligible_unserved`. N4 E reduces ineligible users by.577625/1.523125
for H6/SET but adds2.052000/2.230375 eligible-unserved users, leaving negative service changes.
N8 reductions of9.079500/18.935750 exceed the added2.844375/3.906375 eligible-unserved users.
This makes capacity/assignment conversion consequential even when radio eligibility improves.
It is an accounting identity over changed trajectories, not a causal decomposition: masks
change discovery/peer visibility, assignment, local observations, subsequent actions and geometry.

The strongest N4 H6 harm is world29310010: J -.131992964 and service -9.658000.
All-on serves38.860 on average versus E29.202; ineligible increases5.504→6.644 and
eligible-unserved5.636→14.154. The E episode holds three active transmitters throughout
(mask7 initially, mask14 fromt20). At the first boundary, identical actor actions and next
positions yield actual J .438234482→.446007505 (+.007773022), while service falls31→30.
The public prediction has the same ranking. Subsequent observations/actions and geometry
diverge. All-on is always a candidate; positive immediate J did not protect full J or service.
Across the saved N4 H6/SET E decisions,40/60 of800 boundaries sacrifice immediate predicted
service relative to all-on at that decision’s own predicted position. Neither N8 asset does.
These posthoc saved-data readings expose the native objective’s quality/service tradeoff
before any hypothesis about maladapted recurrent feedback. They do not establish a shared
cause of every adverse world, nor separate ten-step commitment from changed learned feedback.

All adverse worlds remain in reading.json. For N4 SET, the worst J loss is29310001
(-.061294606); the worst service loss is29310004 (-3.996000). Preserve the opposite H6 N4
witness29310004, which gains +.023716863J/+1.452000users. N4 H6 E lowers mean service p05
by1.750000; SET’s +1.065625 p05 difference is uncertain. No N4 program has a zero-service tick.

The N8 benefit also reaches observed tails: H6/SET E raise mean service p05 by9.378125/
21.628125. SET/all has192zero-service ticks in five worlds, longest contiguous run111;
SET/E has none. In29310007 it changes mean service5.972→33.758, J .021348723→.524278050,
and127zero ticks→0. Every other program has no zero-service ticks. This is useful relief in
the measured panel, not a safety guarantee. C/E retains higher mean service p05 than either
asset/E at both N, together with its N4 average-service tradeoff.

C/E’s mean height is50.079982/50.081132 at N4/N8, near the lower bound; mean paths are
643.150/250.817m per UAV. H6/E remains at69.551964/69.758605 height and19062.849/14690.596m
paths. These observations are compatible with ordinary model-based placement being useful
on this static deterministic host. They do not measure physical energy, prove that learned
coordination is unnecessary generally, or identify a lack of learnability in a revised task.

### Cost and independent scientific diagnosis

Per-program totals below sum the16 recorded episode intervals, including their own recording
work. The broader collection and full reader totals are recorded above; they also include
loading/final checks and are not replaced by the table.

| Program | Wall seconds | CPU seconds | Actor CPU | Mask CPU | Motion CPU |
| --- | ---: | ---: | ---: | ---: | ---: |
| N4 H6_all | 30.177 | 118.060 | 90.702 | 0.000 | 0.000 |
| N4 H6_E | 30.386 | 118.390 | 88.770 | 3.202 | 0.000 |
| N4 SET_all | 36.286 | 142.136 | 114.148 | 0.000 | 0.000 |
| N4 SET_E | 36.419 | 141.929 | 110.624 | 3.224 | 0.000 |
| N4 C_E | 31.228 | 31.223 | 0.000 | 0.594 | 24.643 |
| N8 H6_all | 42.132 | 163.601 | 126.044 | 0.000 | 0.000 |
| N8 H6_E | 50.195 | 175.654 | 124.833 | 15.335 | 0.000 |
| N8 SET_all | 50.498 | 195.211 | 156.017 | 0.000 | 0.000 |
| N8 SET_E | 57.461 | 201.950 | 149.838 | 15.498 | 0.000 |
| N8 C_E | 82.129 | 82.110 | 0.000 | 6.216 | 65.057 |

C/E uses fewer CPU seconds here but is slower in N8 wall time than H6/E under the declared
Torch threading. No execution deadline was tested. The two historical final45 fits took
5423.536504/4065.199846 run-fit wall seconds (158.145606fit-minutes combined), separately
from the zero-new-fit B01 cost. Broader historical selection, engineering, transfer, independent
review and publication costs are not fully measured and are not treated as zero.

Independent `hmasd-research-critic` `/root/dm_fleet_transmission/result_diagnosis`, created
without DM/Root conversation inheritance, reconstructed outputs before reading the archived
Pro and selection advice. Its substantive recommendation is to revise the explanation, retain
N8 management capability and C/E, and end unchanged expansion of this two-asset screen.
It identifies configuration-dependent service conversion plus changed feedback, not an
established learning defect; training on muted feedback, frequency changes or an architecture
repair are not established remedies. It specifically objects to a blanket discard of learned
assets because N4 H6/all retains the measured service tradeoff and H6/E retains positive
world-level witnesses. I adopt both the recommendation and this limiting objection.

The critic independently recomputed all160 raw episode metrics, exogenous/reset/fleet-prefix
bindings, motion/mask/horizon checks, capacity identities and raw/decision hashes; all primary
J/service bootstrap intervals,64 paired first actor outputs/runtime bindings and saved E-choice
summaries; selected native snapshots/rankings in eight positive/adverse episodes; original
checkpoints/config/source identities and recorded freeze checks. It read the original N and N5
sources and adverse records. It did not rerun trained actors, independently replay every GRU
state or repeat the entire C-coordinate reader, and did not replay the historical raw panels.
It inspected those source/output checks and separate engineering acceptance; no invalidating
discrepancy emerged. `MATERIAL_DISSENT: no` for completing B01, retaining conditional
capabilities and ending unchanged expansion. DM independently verified the added40/60 boundary
counts, first-transition counterexample and historical fit timings against original saved data.

### DM disposition and next investment

End the fixed five-program B01 screen and put this direction in reserve, with no live producer,
unread result, outstanding advice or selected successor. Retain C/E as a competent finite
ordinary reference for this precise contract, N8 E as a demonstrated conditional capability,
and H6/all’s N4 service tradeoff and all adverse outcomes. Do not promote E to a configuration-
independent default or claim physical adoption. Preserve the two assets and the useful control/
reader code; none of this is a new learned-method contribution.

Task opportunity is established at N8 under the added public-model/search/mute rights.
Representation and learnability remain untested by this zero-update screen. Complete-package
value favors C/E in mean J at both N, with the stated service/tail/cost tradeoffs. The changed
explanation therefore directs investment away from assuming an identified learned-policy repair.
Unchanged replication would narrow fixed-asset world uncertainty without resolving training
variation or the causal alternatives, so no extra worlds/fits are selected.

A concrete N4 service requirement could justify a later complete controller comparison against
both C/E and unchanged H6/all: joint J/service gains would be a new package increment, whereas
J/path/tail losses would remain explicit tradeoffs. It needs a specified use criterion and
prospective candidate; B01 does not supply a posthoc world gate or require inventing a new
objective. Root owns that or any cross-question choice at this assigned boundary. This is idle
with no selected producer, not a pending approval or a fabricated external dependency. The
fresh independent scientific diagnosis covers this actual changed explanation and bounded
stop; no unresolved disagreement or distinct additional Pro question remains.

### Canonical evidence and measured terminal cleanup

After both complete readings, retain the unique320 raw/decision files at
`local_linux:/home/fires/hmasd-artifacts/uav_fleet_transmission/b01_native_s1_a01/raw/`
(200385686logical bytes). Every file’s size/SHA256 is already bound in summary.json and was
reverified before and after moving. The SHA256 of the sorted binding lines
`path + NUL + decimal-bytes + NUL + sha256 + newline` is
`4addc2b67c9cf2b4b0ea16ab8f1aeef16c94b2bc414c9075125593d41943c0c9`.
The canonical parent contains verified compact metadata/status/log files so the original
reader can consume that directory directly. Ignored `runs/.../raw` is a symlink to that one
canonical raw copy. No raw was deleted or hidden by compression, and no whole tree was copied.
The original remote final45 files were reverified at both exact hashes above and remain intact;
original checkpoint staging paths in summary.json are historical invocation records, not
claims that the now-deleted redundant local input copies still exist.

Useful direction code/tests and all compact evidence were published before cleanup. Consumer
inspection found only the owned direction and tests; the completed critic needed no further
local input. A privileged read-only process scan found no matching cwd/argv/file consumers
and no permission errors. Observer generation2 is stopped with no unconsumed events.

The supported native snapshot collector previewed then removed these exact owned targets,
with `--unclaimed-source --sudo-process-scan`; no refusal or cleanup blocker remained:
- `.git/hmasd-launch-sources/a23f403740a04e79acd7cf29c433219e` — unclaimed pre-admission
  source,1666793472allocated bytes;
- `.git/hmasd-launch-sources/174980a0a43d4508a1a2ab8af097511b` — reconciled completed
  operation source,1666813952allocated bytes.

Also actually deleted, after the consumer checks:
- `/home/fires/hmasd-inputs/uav_fleet_transmission/b01_native_s1_a01/` — redundant checkpoint copies;
- `temp/directions/uav_fleet_transmission/` — obsolete wait request and scratch;
- `runs/uav_fleet_transmission/b01_native_s1_a01/runtime_logs/`;
- the owned implementation and test `__pycache__/` directories.

All seven targets are absent. The allocated-byte measurement includes those targets, the
run directory and the canonical destination, so the raw move is not counted as reclaimed space:
**3579494400 before →202317824 after; net3377176576bytes reclaimed.** Remaining evidence
is the run’s638976allocated bytes plus201678848bytes in the canonical direction artifact
root. Git object storage and unrelated directions are outside this scoped measurement.
No other source snapshot, original checkpoint worktree, shared cache or peer output was touched.
The earlier native-child queue rejection was resolved by active same-handle observation;
it is separate from cleanup, which completed without a tool blocker.

### Final locator and publication check

Scientific disposition and the directly affected shared background/standing were published at
`7f4c8432ff081692842458d43dedc04b69f6e189`. A final read through the local run locator
verified all320 canonical artifacts and both compact result hashes again. Both source snapshots
and all other listed cleanup targets remain absent; no reader, worker or observer is pending.

Locator clarification: the local `runs/uav_fleet_transmission/b01_native_s1_a01/raw` symlink
is **untracked**, not covered by the repository’s directory-only ignore rule as the prior
paragraph called it. It is intentionally kept outside Git so the original relative raw paths
still resolve to the unique canonical data. No file was copied or recreated by this check;
the stated allocated-byte measurement and retention identities are unchanged. All owned
tracked source/result files are clean, apart from this final notebook append before publication.


<a id="b02-prospective"></a>
## 2026-09-30 — B02 prospective: silent repositioning beside immediate joint control

Root selected the next in-scope question at `7bb778764d4de030179f9b4d06681c35073fb372` after the complete independent Oracle/Scientific Reviewer proposal ([original review and Root decision](../../archive/2026-09-30/RESEARCH-silent-reserve-repositioning.md)). Does one silent physical relocation followed by activation add useful **complete native N8 service and J**, including transit and foregone ordinary motion, beyond competent immediate joint motion/mask control? The intended contribution is a conditional control capability and empirical understanding, not an invented options method or a learning/necessity claim. The selected three programs and one fixed opportunity are the one active result-bearing idea.

I read the full original review, current published RESEARCH topics 1 and 3 (including the B01 adverse N4 and conditional N8 results), original controller/host, and independently checked the SHA-bound 16 old N8 C/E trajectories. They contain 28,952 muted-before-step member-ticks with exactly zero horizontal motion; every team stopped by t37. C chooses motion under the old mask and prefers less movement on a score tie, so its muted member cannot be rewarded for horizontally repositioning before activation. This establishes a program blind spot, not reachable useful headroom. Topic 3's distinction between immediate score, information rights and complete consequences requires the stronger J control and complete R endpoints; the N4 loss despite an improving first-step J prevents treating the option's surrogate as safety. The separate local-C inheritance and C-prior learning studies are not part of this comparison.

Primary passages read directly: Bertsekas, arXiv `1910.00120v3`, formulation/Proposition 2.1, §3(d), Example 4.1 ([PDF](https://arxiv.org/pdf/1910.00120v3)); Sutton, Precup and Singh, AI 1999, pp.186–188 ([PDF](https://people.cs.umass.edu/~barto/courses/cs687/Sutton-Precup-Singh-AIJ99.pdf)). DIRECT: the former separates an agent-by-agent improvement result under its assumptions from joint optimality and limits guarantees under terminal approximations; the latter defines options by initiation, internal policy and termination, including history-dependent termination. INFERENCE here: J is a necessary competent competing explanation and R is an ordinary finite option with an explicitly approximate stationary tail. Neither paper supplies a guarantee or a predicted gain for this host. The review's actual three-library search and source-qualified other bridges remain linked above; no novelty inference follows from a library miss. That independent review covers this exact three-program selection, with no material dissent; another Pro/selection round would duplicate it without a changed premise.

**Frozen comparison and information.** Sixteen unused identities `29324000..29324015`, N8, c10, 0 dB, 50 static users, H500, 48 complete episodes/24,000 native transitions, **zero fits and optimizer updates**. RNG addresses are `SeedSequence([260930,24,world_id,stream,*suffix])`, streams 1 users, 2 member-major eight-UAV initialization, 3 native runtime with suffix 8. Independent RandomState streams draw the original uniform coordinates/heights. The exact initial arrays and stream seeds are committed before exposure. None of the new identities has been used in the searched direction source/notebooks; no new-world result pilot is allowed. Programs execute in world-index cyclic order C/J/R to spread timing order without choosing outcomes. All start all-on. Native clipped componentwise 30m commands, height bounds, assignment, scalar/native reward distinction and J=.7 served/50+.3 quality−.1(mean height of ALL eight physical UAVs−50)/100 remain unchanged. Controllers receive only public float32 global coordinates at t divisible by 10; known motion propagates between snapshots. No hidden coordinates, more frequent information, new delivery model or neural asset is supplied.

* **C:** unchanged B01 OrdinaryController plus E at each boundary. Start from last actually issued ternary commands; one rotating member pass, order `(t+j)%8`, then E on predicted next positions. Hold mask ten ticks.
* **J:** C's motion pass between boundaries. At a boundary use one rotating pass over members; for each coordinate enumerate command-major all 27 lexicographic ternary commands × masks 1..255, with other commands at their current pass choices and all predictions from the same pre-step positions. Rank by J, served, smaller sum of actual Euclidean displacement, retention of the entering command **and** entering mask as one pair, lower command index, then lower mask integer. Entering mask is the current pass mask. Apply final commands and mask once, with no extra E call, then hold mask ten ticks. This is finite coordinate search, not joint optimality.
* **R:** use C/E through t39. At the lawful t40 snapshot consider each currently muted member, in ascending row order, and exactly 100 sites: user rows 0..49 followed by centroids for rows 0..49. A centroid includes the anchor itself among its ten nearest public user rows; squared Euclidean distance ties use row order. For each member/site and each horizontal axis, project onto `clip(x0+30*k,0,1000)`, integer k from −34 through 34. Minimize absolute distance to the site, then coordinate, absolute k, k. Altitude target is 50m. Commands use the selected sign per horizontal axis until its absolute k steps are issued, and −1 vertically until the predicted height reaches 50; all other components are zero. The unrounded duration is the maximum horizontal step count and vertical descent count. Arrival is t40 plus `10*max(1,ceil(duration/10))`, at most t80; any remaining transit ticks issue zeros. Even a zero-distance candidate has the positive ten-tick commitment to the next boundary. The old mask is held throughout transit and other vehicles receive zero commands. At arrival issue all-zero motion, re-evaluate all 128 masks containing that member at the lawful arrival snapshot, rank by J, served, then smaller mask integer, and obey the normal ten-tick hold. Resume C/E on the following tick with actual issued commands, propagated/anchored positions and original clock. No shadow C history is advanced and there is no second opportunity.

R planning at t40 uses the decoded public state, not future native truth. For a candidate with L transit ticks, sum those L predicted old-mask native J values in temporal order, then add `(460−L)*J_destination` using its best member-containing mask and a stationary tail. The arrival transition is the first tail transition and uses zero motion. The stay candidate is `460*J(current positions, old mask)`, not the return of continuing C. The service surrogate follows the same counts. Since only a muted member moves and all active positions stay fixed, transit service/quality are invariant: reuse one stay radio score but recompute the all-UAV height term at every predicted transit tick in native arithmetic; verify this equality against direct radio scoring in synthetic checks. Rank candidates by predicted total J, total served, smaller actual transit team path, shorter aligned duration, lower member then site index. Initiate only for a **strict** total-J gain over stay, regardless of service ties. The predicted arrival mask may differ from the actual mask after lawful re-anchoring; record both and the coordinate discrepancy. Lack of initiation remains a valid exposure finding. No site/time expansion, retuning, fitting or automatic repair follows any new result.

**Readout and investment.** Read paired R−C, J−C and R−J full-episode J and served together, all per-world positive/adverse/zero differences, descriptive paired-world bootstrap (10,000 draws, seed 26093024). Keep quality, all-physical-member height cost, path, eligibility and eligible-unserved, served p05/minimum, zero-service episodes/runs, active-mask history, initiation, selected member/site, modeled gain, complete realized gain, arrival error, activation duration and remuting. Require exact C/R native prefixes through t39 (states through index40), not merely equal means. Useful R gains over both controls support this conditional compound capability; J gains alone strengthen ordinary immediate coordination; performance/compute trades remain trades. Surrogate-positive R harm ends this finite package without claiming all silent capacity useless or selecting a new terminal model. Sparse/no initiation says the fixed proposal rarely exposed a useful choice, not that all relocation is futile. Learning, necessity, global optimality, pure interference attribution, battery savings and deployment guarantees remain outside scope.

Cost is not zero because fit cost is zero: conservative 50,918,864 radio state-mask requests (C 1,932,000; J 45,619,200; R ordinary ≤1,932,000, destination ≤1,433,600, stay+arrival ≤2,064), 5,184,000 ordinary candidate-position predictions and ≤448,000 option propagation ticks. Exact caching/batching is allowed within each program, never credited across programs; requested/scored/cache and computed/reused geometry counts remain distinct. One coordinate's 6,885 pairs bounds the J batch. Reader recomputation is additional work, not deployment cost. Worker 30–60 CPU minutes and reader 15–60 minutes are estimates, not stop caps; engineering 2–4h and review 1–2h were prospective estimates. Actual configured-node admission occurs only at result launch. All accepted partial/failure cost and evidence must survive; no duplicate retry is authorized by completion or technical missingness.

**L0 implementation.** New entrypoint and code stay under `experiments/candidates/uav_fleet_transmission/b02/`, tests under the matching tests directory; DM owns this notebook, input-world fixture, host binding, J/controller execution, worker/reader and entrypoint. Reuse the unchanged B01 control/scoring and native formulas without editing their frozen meaning. Registered Implementer owns only `b02/option.py` and matching `b02/test_option.py`: one pure deterministic t40 planning and required-member arrival-mask behavior with no environment/worker/science/index writes. `plan_option(positions,users,old_mask,t=40,horizon=500)` takes decoded float64 public coordinates for N8 and returns JSON-safe plan+trace containing initiation, member/site, integer offsets, fixed float32-issued command sequence, L/arrival, destination, predicted mask and total/tail/stay scores, full ordered candidate digest, score/geometry/propagation counts; `arrival_mask(users,positions,member)` returns mask and compact full-candidate trace. Plan validation, projections/ties, nonempty/silent eligibility, clipped motion/descent, stationary-tail accounting and direct transit-score equivalence receive synthetic fixtures, not new-panel outcome tests. DM accepts the diff/checks. Independent engineering Reviewer then checks the complete changed numerical/controller/reader/source/launch path, including actual-history resumption, legal snapshot cadence, exact C prefix and initial identity, native score equivalence, candidate digest reconstruction and refusal of partial workers. No helper owns shared files, Git index, another direction, launches or children.


### 2026-09-30 16:11 UTC — B02 implementation accepted; no result exposure yet

Accepted the registered Implementer's pure option planner and tests after reading its complete source/diff and checks. The centroid arithmetic is now explicit: anchor first, then the nine other users ordered by squared distance and row index, with float64 mean in that order. This refines numerical ordering without changing the selected sites/eligibility contract. DM implemented the fixed J and actual-history R state machine, fresh-world host binding, native worker and complete saved-data reader; the B01 controller/scorer/host remain unchanged. No neural assets are loaded or fitted. The committed `b02/worlds.json` binds all 16 initial arrays and stream seeds; SHA256 `b1be4cdb2f187a65e98283d9b72ab457edc63e55378636304de8d09d8ca7cbfa`. Initial-array generation/binding exposed no new-panel score.

Twenty meaningful checks are covered: 12 pure-option checks plus 8 controller/native/reader checks. These include exact transit scores against direct native radio, all128 arrival masks, ordered candidate digests, projection/centroid ties, positive10..40 commitment, strict J initiation, complete C equivalence and C/R pre-t40 identity, J's coordinate choice and selected J/service against independent exhaustive scalar native evaluation, lawful snapshot/hold clocks, forced actual-history resumption, refusal of changed trace and incomplete worker, and actual J/H11 and initiated synthetic R/H500 native worker→serialization→full-reader roundtrips. The initial old-world R/H500 roundtrip passed but did not initiate; the added initiation assertion exposed only a fixture-coverage gap. A constructed four-corner user/UAV fixture then exercised planning, transit, arrival and resumed C through all500 steps, including the exact reduced motion/mask-call counts. No B02 result cell was run as a test. Recorded DM test invocations took10.34,25.03,31.59 and19.14 wall seconds; the third had19 passes plus that fixture assertion failure, the corrected affected cases passed. Those DM correctness fixtures used1,853 native transitions; the independent review's original controller suite used160 more (2,013 total correctness transitions, separately from24,000 planned result transitions). Reader/score checks and implementation time are additional, not zero.

Independent Engineering Reviewer read the complete numerical/controller/reader/source/entry path and returned **no material finding remaining**. Its one test-oracle arithmetic correction changed `.7*served/50` to native `.7*(served/50)` and added exact selected-score assertions; production scoring already had native grouping. It independently passed12 option tests,6 original controller tests and the corrected joint oracle. It accepted the DM's complete initiated R/J integration evidence; scientific interpretation remains with the DM. The earlier independent scientific selection review still covers the unchanged C/J/R question; no additional advice or hypothesis revision is pending.

Choose configured `local_linux` prospectively for this one sequential worker plus full reader: Python3.10.20/NumPy1.26.3/Torch2.7.0+cpu, Torch intra/inter-op threads1, no inter-program shared cache or parallel workers. The last read-only host sample had6,653,448,192 available bytes and low load; this is not admission and the launcher must check actual memory afresh. No operation has yet been accepted. Publish exact inputs, then launch one `b02_silent_repositioning_a01`; retain the same native handle through all48 episodes and reader. No checkpoint input staging is needed.


### 2026-09-30 16:14 UTC — B02 accepted once and observation adopted

The single `local_linux` B02 operation was accepted at16:12:45 UTC from published `9928d34b54628baaa542961debb65c5ce7ef0f23`, after fresh actual-node admission. Exact command/source/operation/native identities are in [launch manifest](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/launch-manifest.json), with immutable [config](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/config.json) and [preflight](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/admission-preflight.json). Worker and full saved-data reader are one accepted operation; no retry/migration/second launch exists.

The prior B01 observer was stopped. Adding B02 first correctly refused until the existing state was drained/rearmed; rearm generation3 alone did not add a new job. The subsequent supported arm added `fleet-transmission-b02`, generation4, and the first actual observation at16:14:07 UTC matched the accepted runner/supervisor identities, consistent records and running state. No wake/event is pending. This observation repair never restarted the worker. Native child remains active with deterministic waiting and same-handle drain/rearm through complete reading. No outcome-prefix inspection or interpretation has occurred.


### 2026-09-30 — Node-choice clarification while the accepted operation continues

Root correctly pointed out that RESEARCH's owner `wsl_4070`-first preference remains in force. The contemporaneous local suitability reasoning was the already-tested local scientific interpreter/native path, the completed local B01, this CPU-only sequential workload with no retained neural assets, and the measured low local load/available memory; prior remote interpreter failures also made the known local path attractive, although I had read the newer remote GCC runtime's provisional mitigation. I did **not** freshly establish remote unavailability, insufficient remote resources or a B02-specific remote incompatibility. Thus the recorded local suitability does not establish the preference's stated fallback condition: this was a local-preference deviation, not evidence that `wsl_4070` was unavailable, and not permission inherited from B01. I should have checked that preference explicitly before node selection. Preserve the accepted source, operation and observation; no migration, restart or scope change follows. Future selected work must apply the recorded remote-first preference with a concrete current fallback reason when one exists.

B02 observation checkpoint16:38 UTC: generation4 drained event`4790e5d9b9b99d5eebb3d346`, wake`9d97a840-cb2d-43e3-a151-e074aa6821cf`; accepted native identities remained running and records consistent. Native child queue delivery returned the already-known unsupported direct-app-server input error−32600; active DM received the deterministic local event, consumed it and rearmed generation5 against the same operation. No worker restart, scientific failure or outcome-prefix reading.

B02 second checkpoint17:03 UTC: generation5 event`9287472100b050314382ffe6`, wake`c3251bce-8d98-42d9-a8ac-36cd29239b8e` drained; same native process identities remained live/consistent, probe errors0. The same unsupported queue delivery was handled by the active DM. Operational counters only showed all48 worker episodes collected and35 reader episodes verified; no score/option outcome was inspected. Consumed checkpoint and rearmed generation6 on the unchanged handle.


### 2026-09-30 17:14 UTC — B02 full worker and reader collected; scientific review underway

The accepted operation exited0 at17:11:05 UTC with a valid native witness; both recorded runner and supervisor were absent and records consistent in [terminal status](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/launch-status.json). Worker status is complete:48 episodes,24,000 native transitions,0 fits/updates. The [full pure reader](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/reading.json) is complete for all48 episodes/24,048 native snapshots, every C/J/R candidate decision/digest, all metrics/counts, bound initial arrays and exact C/R prefix through t39. DM additionally verified all96 raw/decision file sizes+SHA256 and independently recomputed all48 complete native J/service means. No incomplete cell, duplicate launch, worker repair or new scope was needed.

Compact [summary](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/summary.json):191,509 bytes, SHA256`11d2a85260ac00b4c47846fb31268a3e9c00d9fabf716a8b76b5ec726d5d27bb`; reading111,805 bytes, SHA256`269fc6aca11d085d53375961ba031524af2964255ba3ea0acc3bf574cf3f15fd`. Worker1777.508580 wall/1776.094880 CPU seconds; reader1719.989952 wall/1718.653590 CPU; combined3497.517491 wall/3494.767428 CPU seconds. PeakRSS599,368KiB is the whole process lifetime, not a separately measured reader peak; process-lifetime CPU including imports is3497.870927 self seconds, child system.002832 seconds separately. This is58.25CPU minutes of computation, not a zero-cost study because it had no fits.

Observation generation6 READY event`09f13cd2bd7baeaffb8ccdfc`, wake`7db090a9-0a53-4a32-b7bb-06cbed21c94e` was drained with the terminal facts, consumed by rearm generation7, then observation stopped; drain confirmed stopped/no pending events or wake. The unsupported native child queue delivery did not lose collection because this turn remained active. Root received calculation release, explicitly distinguished from a scientific conclusion. Complete evidence is now with the isolated registered ResearchCritic; DM reads the full contrasts and adverse trajectories independently. All unique raw evidence stays available during that reading; final interpretation/publication and measured cleanup follow it.


<a id="b02-complete-reading"></a>
## 2026-09-30 — B02 complete reading: retain silent relocation–activation–resumed control

**Retain R as a conditional ordinary control capability and close this fixed comparison.**
The fresh complete N8 panel supports useful mean J and service beyond both unchanged C/E and
stronger immediate joint control J. The original blind-spot explanation is now strengthened
by realized reachable-placement value, with explicit adverse worlds, quality/tail losses and
extra travel. This is exploration, not confirmation, a learned method, or an option-necessity
claim. No new run, fitting, candidate expansion or repair is selected at this boundary.

Exact inputs were published at `9928d34b54628baaa542961debb65c5ce7ef0f23`; compact complete
[summary](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/summary.json),
[reader](../../../../runs/uav_fleet_transmission/b02_silent_repositioning_a01/reading.json) and
terminal evidence at `b7165f3294481c50335e43a5151f8b3b7d8f7459`. All48 episodes/24,000 native
transitions and24,048 saved snapshots passed the declared complete reader, including all
C/J/R candidate decisions, initial-array/source bindings, capacity identities and sixteen
exact C/R prefixes through t39. There were zero fits, optimizer updates or failed result cells.
The node-choice deviation and observer queue limitation remain recorded above; neither is
hidden by the successful scientific result.

### Complete outcomes and retained adverse worlds

Service is mean users served per native tick. All other means below first reduce each complete
H500 world, then average the sixteen equally weighted worlds. In this table `J score` denotes
the native objective; the middle program is the stronger joint controller named J.

| Program | J score | Service | Quality | Mean active | Path m/UAV | Service p05 | Episode minimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C | 0.615036072 | 39.049875 | 0.229656803 | 4.178750 | 260.115119 | 38.750000 | 34.437500 |
| J | 0.631313484 | 40.300750 | 0.223979923 | 4.488750 | 274.176743 | 40.375000 | 35.875000 |
| R | 0.648963246 | 41.853000 | 0.210589572 | 4.786250 | 450.673593 | 38.750000 | 34.437500 |

The fixed10,000-draw paired-world percentile bootstrap, seed26093024, gives the following
**descriptive** intervals. They condition on these deterministic programs and this host;
they are not training replication, simultaneous tests, equivalence or a universal guarantee.
Positive/negative/zero counts use the unrounded world differences.

| Contrast | Mean ΔJ [95%] | J +/−/0 worlds | Mean Δservice [95%] | Service +/−/0 worlds |
| --- | --- | --- | --- | --- |
| R-C | +0.033927174 [+0.021367181, +0.046673855] | 14/0/2 | +2.803125000 [+1.703246875, +3.857765625] | 11/1/4 |
| J-C | +0.016277412 [+0.003530419, +0.031960374] | 9/7/0 | +1.250875000 [+0.294625000, +2.275034375] | 12/4/0 |
| R-J | +0.017649762 [+0.004632463, +0.031449777] | 11/5/0 | +1.552250000 [+0.476487500, +2.732384375] | 9/7/0 |

Every world remains visible below; each cell is `J score / users per tick`. The raw and reader
retain all other requested outcomes and all three unfiltered comparisons. World IDs are not
selected for a new gate or a posthoc tuning panel.

| World | C | J | R | R−C | R−J |
| --- | --- | --- | --- | --- | --- |
| 29324000 | 0.637006213 / 39.990 | 0.637765475 / 39.994 | 0.637006213 / 39.990 | +0.000000000 / +0.000 | -0.000759262 / -0.004 |
| 29324001 | 0.632517317 / 39.980 | 0.632241193 / 40.000 | 0.684508495 / 45.244 | +0.051991178 / +5.264 | +0.052267302 / +5.244 |
| 29324002 | 0.684157529 / 44.724 | 0.685152491 / 44.864 | 0.684524389 / 44.724 | +0.000366860 / +0.000 | -0.000628102 / -0.140 |
| 29324003 | 0.584396502 / 35.986 | 0.613710244 / 38.982 | 0.636158552 / 40.382 | +0.051762050 / +4.396 | +0.022448309 / +1.400 |
| 29324004 | 0.607622777 / 37.972 | 0.648277400 / 41.980 | 0.650692470 / 42.464 | +0.043069693 / +4.492 | +0.002415070 / +0.484 |
| 29324005 | 0.605045402 / 37.934 | 0.624831460 / 40.830 | 0.661084917 / 43.176 | +0.056039515 / +5.242 | +0.036253457 / +2.346 |
| 29324006 | 0.538290760 / 34.894 | 0.637146736 / 39.946 | 0.622316118 / 40.176 | +0.084025358 / +5.282 | -0.014830618 / +0.230 |
| 29324007 | 0.571368788 / 36.992 | 0.564280526 / 36.000 | 0.618719490 / 39.612 | +0.047350702 / +2.620 | +0.054438964 / +3.612 |
| 29324008 | 0.615979382 / 37.996 | 0.612832343 / 37.994 | 0.685712474 / 44.252 | +0.069733092 / +6.256 | +0.072880131 / +6.258 |
| 29324009 | 0.612628491 / 38.014 | 0.601042257 / 36.886 | 0.630207368 / 39.772 | +0.017578878 / +1.758 | +0.029165112 / +2.886 |
| 29324010 | 0.625121682 / 39.898 | 0.624731404 / 39.912 | 0.625121682 / 39.898 | +0.000000000 / +0.000 | +0.000390278 / -0.014 |
| 29324011 | 0.587536971 / 38.562 | 0.619444189 / 39.756 | 0.602410134 / 38.544 | +0.014873163 / -0.018 | -0.017034055 / -1.212 |
| 29324012 | 0.629850541 / 39.990 | 0.619736113 / 39.008 | 0.673734052 / 44.272 | +0.043883511 / +4.282 | +0.053997940 / +5.264 |
| 29324013 | 0.613945647 / 39.984 | 0.610096308 / 39.998 | 0.614659028 / 39.984 | +0.000713381 / +0.000 | +0.004562720 / -0.014 |
| 29324014 | 0.699080507 / 44.896 | 0.717313201 / 46.848 | 0.719310319 / 46.652 | +0.020229812 / +1.756 | +0.001997118 / -0.196 |
| 29324015 | 0.596028640 / 36.986 | 0.652414400 / 41.814 | 0.637246237 / 40.506 | +0.041217598 / +3.520 | -0.015168162 / -1.308 |

R−C's service gain decomposes into1.421625 fewer SINR-ineligible users and1.381500 fewer
eligible-but-unserved users per tick; R−J's corresponding reductions are.949625/.602625.
These are identities along changed complete trajectories, not pure interference or capacity
causal shares. R−C quality falls.019067231 and R−J quality falls.013390351. The mean weighted
height charge in J is C .000559219, J .000090993 and R .000155625; all physical members count.
The fourteen selected silent members were already at50m, with zero descent ticks. The benefit
cannot be attributed to descending an otherwise unused silent member, although subsequent
ordinary control can change other members' heights.

All48 episodes have zero zero-service ticks and runs. R's service p05 and minimum equal C
**in every world**, preserving their common early-history tail; relative to J, the respective
world-mean differences are−1.625 and−1.4375users. R−J p05 improves in3worlds, worsens in8 and
ties in5. Thus higher mean service does not establish better startup or lower-tail service.
R's path rises190.558474m/UAV versus C and176.496850 versus J. Native J has no explicit path, battery or
delivery-reliability charge. Transit is included on the native movement clock, which alone
is not a physical deployment model.

Consequential witnesses from saved trajectories:

- **29324011:** the only R−C mean-service loss is−.018, nine user-ticks lost over seven ticks
  (64,72,73,74,75,76,80), with no positive service differences. C stays at39 users after t40;
  R transiently serves37/38, then settles to39 by t86. Its quality gain supports+.014873163J,
  despite the loss. The chosen arrival mask216→212 adds member2 and removes member3; the
  planner's small+.05462294 total-J improvement predicted no added service. R−J loses
  .017034055J/1.212users, and its p05 is35 versus J's40.
- **29324015:** R−J has the largest service loss,−1.308, alongside−.015168162J. Both finish
  with mask214, yet R settles at41served and J at42; R arrives at t60 and its last motion is at t68,
  while J last moved at t17. Their p05 values are37/42. Matching final masks is not matching
  geometry or trajectory value.
- **29324006:** R−J gains.230service but loses.014830618J because its quality is lower;
  J/service rankings cannot be interchanged. C's settled mean height57.5 versus R's50 also
  contributes to R−C J, precluding an exclusively service-capacity interpretation.
- **29324008:** R−J gains.072880131J/6.258users, the largest J and service gains. C and J
  finish with38served/mask51; activating member6 gives R mask115 and45served. Quality falls.
- **29324002/29324013:** the selected relocation paths are989.117/964.264m for tiny full-J
  gains.000366860/.000713381 over C and no extra service. This is a real cost of strict-J
  initiation when path is unpriced, not grounds to remove the worlds.
- **29324012:** R−C adds5299.04m of team travel, although the fixed option itself travels
  360m. Resumed ordinary movement accounts for much of the complete path consequence.

### Choice exposure, calibration and changed explanation

R initiates in14/16worlds. In29324000/29324010 the best modeled total-J gains are negative
(−.088018837/−.061723333); declining the option leaves the **entire** native C/R trajectories
exactly equal. All14 selected members activate at their legal arrival and remain active through
t499:6170 active member-ticks after arrival, no remuting. Durations are10ticks in3worlds,
20in9 and30in2. The program pays270 forced-transit ticks plus14 all-zero arrival transitions,
then resumes C/E from actual issued history. It makes759 normal mask calls and7716 ordinary
motion calls; the suppressed calls are part of the complete package, not omitted cost.

There are6100 considered member/site candidates, from61 muted members over16worlds, with
120240 model-propagation ticks. All actual arrival masks equal their predictions; native arrival
service matches, absolute J discrepancies are at most4.705e−9 and public-coordinate discrepancy
at most4.530e−5m. This validates the arrival approximation on observed options, not the complete
return of unchosen plans.

Every new C team stopped moving by t36, before the fixed t40 opportunity. Consequently all14
R transit trajectories have exactly C's service and reward components during transit: freezing
other vehicles incurs no foregone C motion in this panel. The stationary stay surrogate matches
actual remaining C return to within1.782e−6 total J, attributable here to public float32
coordinates. This removes an artificially weak stay comparator as an explanation of R−C on
these worlds; it does **not** establish no-cost transit for a moving host or for J's history.

Mean predicted option gain over stay, normalized by the full500steps and16worlds with zero
for no initiation, is+.017855987J; realized R−C is+.033927174. Twelve of fourteen initiated
worlds improve further after ordinary control resumes; only29324002/29324013 retain the
stationary destination prediction to numerical precision. The supported mechanism is the
**complete relocation–activation–resumed-control program**. Destination scoring alone is an
incomplete account of its realized value. R−J is a comparison of complete programs whose
pre-t40 trajectories differ; it does not identify the effect of adding an option to J.

Task opportunity is now established for this particular finite proposal on a fresh settled
N8 panel, beyond the old B01 proposal blind spot. J's own positive mean gains show that
immediate joint motion/mask coordination is also useful, but it does not absorb R's increment.
Lawful public coordinates, a known model, finite search and ordinary reoptimization suffice
for the observed capability. Learned representation, selector learnability and learning
necessity were not tested. Complete-package value is conditional on mean service/J use with
explicit path, quality and startup-tail tradeoffs. Earlier N4 harms and the B01 immediate-positive/
complete-negative witness remain unchanged; no policy-improvement theorem or host-general
recommendation follows.

### Measured cost and independent scientific diagnosis

Each row sums sixteen complete worker episode intervals, including its recording work.
No cross-program cache is credited; candidate counts distinguish requests from unique scored
state/mask pairs within decisions and geometry reuse.

| Program | Wall seconds | CPU seconds | Radio requests | Actually scored | Cache hits | Geometry computed | Geometry reused |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C | 81.562988 | 81.551673 | 1932000 | 1301320 | 630680 | 1158725 | 9251835 |
| J | 1590.266503 | 1589.091872 | 45619200 | 29229861 | 16389339 | 1154853 | 232684035 |
| R | 104.884154 | 104.681497 | 2642809 | 1904265 | 738544 | 1119179 | 14114941 |

Worker total is50,194,009radio requests, below the prospective50,918,864 bound, with5,122,656
ordinary position predictions and120,240option-model ticks. The reader independently repeats
candidate work and native reconstruction; it is additional scientific-verification computation.
R episode CPU is1.2836×C; J is15.1803×R in this implementation. Exact cross-decision memoization
was not implemented; these timings are neither algorithmic lower bounds nor deployment deadlines.
Worker1776.094880CPU seconds plus reader1718.653590 equals3494.767428CPU seconds; wall total
3497.517491seconds. Whole-process peak RSS is599368KiB. Import-inclusive lifetime CPU and
correctness costs remain separately recorded above. Engineering, review and publication labor
were not comprehensively metered and are not treated as zero.

Cumulative B01+B02 result exposure is208episodes/104,000native steps/zero new fits, with
5020.958056worker-plus-reader CPU seconds (83.68minutes); the two historical asset fits and
all earlier adverse/correctness/engineering costs remain incurred. B02 does not erase B01's
conditional asset findings or create a zero-cost learning dataset.

Independent `hmasd-research-critic` `/root/dm_fleet_transmission/result_diagnosis` reused its
separate-context B01 review and reconstructed B02 from the prospective contract, actual source
and native outputs before reading the complete archived Oracle proposal/Root decision. It
received no new DM explanation. It independently checked all96 artifact hashes, source/world
bindings against accepted snapshot and Git, exogenous arrays/seeds, all48 native metric reductions,
motion/mask/terminal constraints, capacity identities, all16exact C/R prefixes and all6primary
intervals; it reproduced all14 arrival-mask searches,70 native-physics snapshots and12 selected
J boundary scores. It read the full controller/option semantics. It did not repeat every
candidate enumeration of the complete reader; those verification scopes remain distinct.
No result-invalidating discrepancy emerged.

Its substantive recommendation is to **retain R and close the fixed B02 comparison without
automatic replication, fitting or expansion**. It specifically identifies resumed C as part of
the positive mechanism, rejects a destination-only attribution and a learned-necessity claim,
and retains the five R−J J losses, seven service losses, unchanged C tails, lower quality and
extra travel. It preserves a possible learned selector as a separately priced constructive
successor, not a required repair. I adopt these recommendations and limits. `MATERIAL_DISSENT:
no` for this actual conditional retention/closure; no distinct additional Pro question or
unresolved material scientific objection remains.

### DM disposition and next investment

Keep the complete R implementation, J and unchanged C/E as ordinary references, their tests
and reader, the canonical evidence and all positive/adverse world outcomes. Put this direction
in **reserve**, with no active producer, unread result/advice or selected next experiment. This
closes the bounded C/J/R study, not the broader question of developing useful fleet control.

The smallest useful complete experiment has discriminated the selected alternatives: J-only
success would have reduced the option's priority; sparse initiation would have limited exposure;
active aggregate harm would have rejected this package. The observed R mean gains beyond both
controls instead create a conditional capability worth retaining. Unchanged replication would
narrow its world uncertainty, but is not required to preserve that capability and does not itself
address deployment costs or selection learnability. No automatic sites/times/surrogate repair,
extra J pass, further N cell or attribution replay is selected.

A separately selected learned member/site proposal could build on R if it predicts either
better complete outcomes than unchanged R or comparable outcomes with lower **total** cost.
Such a comparison must charge teacher/data generation, fits, inference and increased travel,
retain competent R with the same added information, and state a break-even use count for any
amortization claim. Fourteen selected options supply no labels for complete unchosen-plan
returns; more representation or fitting is not an evidenced remedy. A physical travel-price or
moving-demand extension would change the use contract and needs its own substantive question.
These are candidate continuations, not new work or pending approvals. Root owns any next
cross-question selection at this assigned boundary; no owner decision is manufactured as a
current dependency. The relevant shared background is revised only for the supported ordinary
capability and its limits.

### Canonical evidence and completed cleanup

After full DM and independent readings, the unique96 raw/decision files were moved to
`local_linux:/home/fires/hmasd-artifacts/uav_fleet_transmission/b02_silent_repositioning_a01/raw/`
(16,101,141logical bytes). Every size/SHA256 in summary.json was verified before and after
moving. The SHA256 of sorted binding lines `path + NUL + decimal-bytes + NUL + sha256 + newline`
is `8f50ccf3a3669d4711a3d2ee4532af20ee14ef6085ad8134c7f9ea1aa99776e1`.
The local run's untracked `raw` symlink resolves to this one canonical copy. No required raw
was deleted. Nine exact compact files accompany it so that the canonical directory can be
consumed directly: summary, reader, config, launch manifest, admission preflight, terminal
status, exit witness and stdout/stderr. Their hashes match the published/local originals;
summary/reader identities remain those recorded above. No whole-tree backup or archive was made.

Useful code and machine readings were already published. CodeGraph followed by exact import/
entrypoint/reference inspection found the retained B02 implementation and its own tests as
consumers; all useful code is kept. All helpers completed. Native snapshot GC's privileged
read-only process scan found no live source consumer, and a separate privileged cwd/argv/open-file
scan found no consumer or permission error for the owned scratch/caches. The B02 observer's
terminal event was consumed and generation7 stopped, with no pending event or delivery.

The supported native collector previewed and removed exactly
`.git/hmasd-launch-sources/3c88e1ef6f92472294c00ae056408d00` and its matching
`.git/worktrees/3c88e1ef6f92472294c00ae056408d00` registration, after verifying the exited
operation and reachable published source. It retained claims, manifests and all results.
Also actually deleted were `temp/directions/uav_fleet_transmission/` (obsolete wait request),
`experiments/candidates/uav_fleet_transmission/b02/__pycache__/` and
`tests/experiments/candidates/uav_fleet_transmission/b02/__pycache__/`. All five targets are
absent. No other snapshot, B01 canonical evidence, original asset, shared cache or peer output
was touched, and there is no cleanup blocker.

Allocated-byte measurement covers those five targets plus the run and new canonical destination,
so relocation is not counted as freed space: **1,724,604,416 before →17,002,496 after;
net1,707,601,920bytes reclaimed**. Remaining measured evidence is344,064allocated bytes in
the local run plus16,658,432in the canonical directory. Broader Git object storage is outside
this scoped measurement. This deletion result is separate from the already-handled native-child
queue-delivery limitation and the recorded node-choice deviation.

<a id="b03-design-only"></a>
## 2026-09-30 — B03 design only: value the complete continuation of retained relocation options

Root assigned this new bounded preparation after the completed B02 closure at `f5f36d817`.
It does not reopen B02. Actual new exposure in this preparation is **zero fits, zero native
transitions, zero controller/radio/model/actor queries and no result implementation**. Work
consists of source/saved-record reading, literature reading, scalar cost arithmetic and this
prospective record. The existing independent Astra Max Oracle `/root/deep_report_review`
owns the selection recommendation; its complete original answer and later allocation update
are preserved below. Root owns the next result-investment choice. No result operation, trial
panel or engineering task is selected by publishing this design.

### Question, current explanation and investment preference

The question is whether accounting for the **complete resumed ordinary controller** changes
useful physical relocation choices beyond unchanged R. Its intended contribution is ordinary
control capability and empirical understanding, not a new learning method. B02 supports
relocation–activation–resumed control: R improves complete means beyond both C and J, and
twelve of fourteen initiated paths improve further after C resumes. The selected-option
forecast gain `.017856` versus realized `.033927` does **not** establish that unchosen plans
are misranked. The main competing prediction is that stationary scoring already chooses a
good representative and that better return estimates will leave physical choices unchanged.
All B02 quality, travel, startup-tail and adverse-world limits, and the earlier N4 active harms,
remain. In particular, a common C prefix through t39 cannot repair its own startup history.

Within this assigned question I prefer the proposed C/R/T comparison below to another
unchanged replication, fitting an unsupported selector, all-700-plan suffix search, or the
cheaper transit-mask alternative. It tests a persistent choice consequence of a demonstrated
capability with a finite complete observation. This preference is **not** evidence of unchosen-
option headroom. Retaining R without purchasing T is also a defensible cost choice. A negative
or inactive T need not produce a repair, larger shortlist, extra timing or next panel.

Relevant published background was read at `40caac61a66620da37f1c1ba5fff09a956e0473a`
and refreshed through `008487d84`: RESEARCH topics1/3 preserve the complete native objective
and conditional N8 capability; topic8 supplies information/action-order/cost reasoning without
requiring exhaustive headroom before a complete experiment. Topic2's local-peer forecast
result concretely requires this design to measure executed choices and native endpoints,
not credit forecast accuracy alone. Its N5 local interface supplies no transferable T effect
size. The newer topic4 S_I−Q_I capability is a competing constructive learning investment;
it supplies no N8 learned-selector claim or reason to substitute another controller here.
No new empirical finding from this design preparation changes a shared-background judgment.

### Proposed fixed comparison and lawful policy interface

The proposed panel is **16 fresh matched worlds × C/R/T × H500 = 48 complete episodes,
24,000 native transitions, zero fits/updates**. N8, capacity10, 0dB eligibility, 50 static
uniform users, deterministic free-space radio, clipping, and the native scalar objective stay
exactly as in B02. R and C are unchanged references from source
`9928d34b54628baaa542961debb65c5ce7ef0f23`; J is retained historical evidence, not a new
matched arm or a basis for a T−J/global-best claim. All programs start all-on. Cyclic world-index
arm order is C/R/T, R/T/C, T/C/R. All worlds, declines and technical failures remain recorded.

Proposed world identities are `29326000..29326015`, with
`SeedSequence([260930,26,world_id,stream,*suffix])`, streams1/2 for users/eight-UAV
initialization and stream3 with suffix8 for native runtime. Use the exact B02 member-major
RandomState uniform-coordinate generation with only this fresh address changed. No such
identity was found in the searched source/notebooks. These are prospective identities only:
no new arrays have been generated or outcomes inspected. If selected, commit the exact initial
arrays, little-endian-float64 hashes, stream seeds, source/configuration and reader bindings
before execution. The proposed descriptive bootstrap uses `RandomState(29326991)`, 10,000
common paired-world index resamples, percentile .025/.975 endpoints, with the sixteen worlds
as evaluation units. It does not create training replicates, equivalence or confirmation.

T executes C through t39. At t40 it enumerates exactly R's existing options: each currently
muted member and all100 fixed user/nearest-ten-user-centroid sites, original projection,
descent, aligned duration and stationary rank. Keep **one stationary-best champion per muted
member**, including champions with nonpositive stationary gain. At most seven champions are
possible because the entering mask is nonempty. Do not suppress the all-active/no-champion
case or any low-exposure world. The original global R physical champion is therefore included.

Add the C-stay continuation. For each of these at most eight complete programs, model all460
remaining transitions separately: the original silent transit with every other member held,
unchanged old mask, original required-member 128-mask arrival search and all-zero arrival
transition, then C/E through t499. The decline branch uses C/E immediately at t40. At arrival
`40+L`, the forced zero transition is still part of the option; ordinary C resumes at
`41+L`. No early stationary tail, cycle compression, new sites, new decision times, more
option opportunities, neural proposal or changed physical price is included.

Within each member retain original R's stationary rank. Across complete branches rank
`(remaining_J, remaining_service, -original_transit_path, -L, -member, -site)` and initiate
only if the winner's modeled J is strictly greater than the C-stay branch. Otherwise continue
C. Full resumed path is measured, not newly priced. Keep the model value of R's actual program
(C when R declines) distinct from its best physical candidate's model-only value when that
candidate is not executed. The chosen T option executes with the original R transition law
and subsequent C; no extra replan occurs within its commitment.

The actual interface is the existing 133-float public report only at ten-tick boundaries,
the entering mask and the controller's own issued-command/clock history. Motion selection
uses the old mask before E changes it; member order retains absolute `t mod8`. A model branch
must copy that history, not initialize a fresh C at arrival. The source permits a pure branch
without a native environment call: `Program.select` consumes these values, and `_Scores`
uses only the known analytic model with its existing within-decision cache.

The branch world starts from **decoded t40 public coordinates**, never hidden native doubles,
world identity/seed or future reports/actions. Maintain separate model-physical float64
positions and C's predicted float64 positions, with issued commands copied as float32.
At future legal reports reproduce CountAdapter's order: first cast physical coordinates to
float32, then perform the original float32 normalization; preserve the original static public
user-report bits. Between reports propagate C's estimate from its own issued commands. Score
the branch's actual model-physical post-action reward each tick, not C's selected candidate
estimate. Every branch has private controller/model state; only the selected actual action
updates the executing program. These details preserve the policy interface but do not make
decoded public coordinates equal to hidden native geometry.

For the finite set of represented complete programs, maximizing modeled remaining return
cannot score below the represented R program under that same model. This elementary inclusion
argument is the useful bridge to rollout. It is **not** a native improvement theorem: public
coordinate error can cross SINR thresholds, change a later argmax and alter subsequent C
behavior. The original shortlist also restricts which member/site trajectories can be selected.
Radio interference, assignment capacity and sequential team-control coupling remain inside
each complete branch; no independent-agent approximation removes them.

### Required reading and outcome implications if selected

Read paired complete T−R J/service first, then T−C and R−C, with all world differences and
the declared descriptive intervals. Retain quality, all-eight-vehicle height charge, path,
service p05/minimum/zero-service runs, eligibility/capacity accounting, transmitter counts,
arrival/remuting, timing and actual compute/storage costs. No mission threshold, energy price
or deployment deadline is invented. Record all candidate/champion identities, stationary and
complete forecasts, chosen/declined member/site/duration, actual command/mask/position changes,
and aliases between different indices. Verify exact C/R/T prefixes through t39 and identical
native suffixes when R and T execute the same physical program.

For C, the actual R program and chosen T, compare modeled versus observed remaining return
on their common-prefix world. Unexecuted branch forecasts are not native counterfactual labels.
The complete reader reconstructs every original shortlist ranking and every retained modeled
branch, not only the winner, then all48 complete native trajectories and artifact bindings.

- Changed physical choices with better complete J and service support a conditional finite-
  shortlist capability, subject to measured uncertainty, compute, quality/path and tail costs.
- Better forecasts with identical physical choices establish no T control benefit. End unchanged
  T investment and retain economical R; sparse changes imply narrow exposure, not a broad
  refutation of anticipation or all700-plan search.
- Changed choices with native harm reject this T package. A model/native reversal does not
  identify quantization, pruning or another specific cause, and does not prescribe a repair.
- Mixed means/tails or unresolved small differences remain conditional or unresolved; no
  equivalence, default adoption, extra seed panel or automatic replication follows.
- A technical failure preserves attempted cost and a missing comparison, not an imputed zero
  or a scientific adverse effect.

### Source-based full cost, feasibility and prospective L0

The bounds count state/mask requests before cache savings. Per world, C costs at most
`500*216 + 50*255 = 120750`; an R-style executing program is conservatively bounded by
`120750 + 1 + 7*100*128 + 128 = 210479`. This deliberately overcounts ordinary calls
suppressed during transit. The extra C-stay model branch costs
`460*216 + 46*255 + 460 = 111550`. At earliest arrival t50, an option branch costs at most
`449*216 + 44*255 + 128 + 460 = 108792`; later arrival reduces ordinary searches. Thus T adds
at most `111550 + 7*108792 = 873094` continuation requests per world, and all three programs
cost at most `16*(120750 + 210479 + 210479 + 873094) = 22636832` worker requests.

| Proposed cost | Bound or planning estimate |
| --- | ---: |
| New native episodes / transitions | 48 / 24,000 |
| Fits / updates / neural forwards / teacher acquisition | 0 / 0 / 0 / 0 |
| Worker state/mask requests | 22,636,832 |
| Additional T model-physical transitions | 58,880 |
| R+T original candidate-transit propagation | at most896,000 ticks |
| Ordinary actual+hypothetical candidate-position predictions | at most17,635,968 |
| Worker CPU | estimated15–30minutes |
| Full reader CPU | separately estimated15–30minutes |
| Implementation and focused checks | estimated4–6labor hours |
| Independent high-risk engineering review | estimated1–2labor hours |

The reader adds comparable candidate work plus full native reconstruction; it is not included
in the worker ceiling. Requests, actual scored states, cache hits and geometry work remain
separate. Model propagation is not counted as a native transition or free evidence. Estimates
use the already-paid B02 local implementation, not a new benchmark: per-episode complete CPU
was5.096980s for C,6.542594s for R and99.318242s for J. These are neither speed limits nor
guarantees on the eventual node. Source calculation found no hard interface gap. Peak memory,
bulk size, imports, new storage/transfer and support costs are unmeasured and not treated as
zero. Stream branch traces; no reason exists to retain all per-candidate geometry tensors.

If Root selects this purchase, the bounded L0 is a new owned
`experiments/candidates/uav_fleet_transmission/b03/` implementation and matching tests:
public-model C emulation, per-member original-R champions, T selection/execution, fixed input
binding and complete saved-data reader. Do not mutate the accepted B02 R/C source. Checks
must cover exact report encoding, old-mask/motion order, absolute clock and copied command
memory, branch isolation, nonpositive champions and all ties, model/native correspondence on
constructed correctness examples, initiated/declined complete serialization, and tampered or
incomplete evidence refusal. No such check or implementation has run in this design task.
Use the registered independent engineering Reviewer for this numerical/controller/reader
change; another scientific/Pro pass is not automatically required by unchanged implementation.
Publish exact inputs before one result launch and freshly admit the actual node. Apply the
owner's configured **wsl_4070-first** preference; prior local execution supplies no inherited
fallback permission. Preserve one canonical required evidence copy and retain failed attempts.

The genuinely cheaper candidate considered with the Oracle keeps R's exact chosen physical
path and adds either ordinary immediate E at transit boundaries or a ten-tick-total mask
choice, with the unchanged arrival reset. Source `uav_env.py` has no connection, handover,
battery or user-motion memory carrying these earlier masks into the common post-arrival C
state, so gains are confined to at most40 transit ticks; physical path and later control are
unchanged. R/R_E/R_10 would cost the same48 episodes/24,000steps, at most10,282,512 worker
requests, estimated10–30worker+reader CPUminutes and3–4engineering/review hours. Immediate
E need not improve a ten-tick held-mask total. We decline this alternative for the current
investment preference, not as an empirical refutation of timing; it is not appended as a sweep.

The complete B01+B02 sunk exposure remains208episodes/104,000result steps/zero new fits and
5,020.958056measured worker+reader CPUseconds, plus historical fits and incompletely metered
support. B02's own3,494.767428CPUseconds and completed cleanup are unchanged. This preparation
does not generate a new empirical insight, capability result, raw artifact or cleanup target.

### Primary-source check and independent recommendation

I read the Oracle's full original answer before adopting this design preference. Its scoped
three-library search and July/external-review reading are recorded in that answer. I directly
checked the load-bearing primary passages: Bertsekas `1910.00120v3` §1.1/Eqs1.2–1.3
([primary PDF](https://arxiv.org/pdf/1910.00120v3)); foundations B03, Oliehoek–Amato §8.2,
book pp100–102 ([local metadata](../../../new-libs/corpus/papers/B03/metadata.json),
[author PDF](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf)); Inst-sci
`MARL-0016`, *Models as Agents*, p3/Method/Theorem1
([primary JSON](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json),
[PDF](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0016.pdf)); and My-lib
`neurips-2024-2e8eaf43f20948ad878e6b8902797d1e`, *Policy Mirror Descent with Lookahead*,
§§3.2/4.2 and the inexact-value qualification in§5
([primary PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/neurips-2024/2e8eaf43f20948ad878e6b8902797d1e/arxiv-2403.14156.pdf)).

DIRECT: rollout uses base-policy continuation; macro-action value includes primitive-time
reward; model/policy interactions affect multistep return error; lookahead trades computation
for improvement under stated exact/inexact assumptions. INFERENCE here: price and test the
entire lawful C continuation, preserving public-state approximation and finite-shortlist limits.
None supplies a native UAV guarantee, a prediction that T wins, an exhaustive-oracle admission
gate or a novelty verdict. The Oracle's N8 `MATERIAL_DISSENT: no` is specific to this new
selection boundary. Its separate earlier inheritance-allocation dissent is not self-cleared
here. The later allocation addendum prompted by the newly completed parent B04 evidence is
preserved separately below; it does not silently rewrite the original advice.

<a id="b03-original-independent-recommendation"></a>
### Complete original independent Oracle recommendation

The following is the original native delivery from `/root/deep_report_review`, before its
separate B04 allocation update. The reviewer did not inherit the DM/Root conversation, but
explicitly records that its assignment supplied result facts/candidate axes; it is not called
a blind review. Its engineering feasibility/cost facts were supplied by this owning DM.

Recommend one bounded C/R/T comparison: use the ordinary controller’s complete modeled continuation to choose among a fixed shortlist of R’s existing relocation options. Retain R unchanged. Do not add sites, decision times, fits or a learned selector to this study. The question is whether accounting for resumed control changes useful physical choices, not whether it predicts R’s return more accurately.

This is a prospective investment recommendation, not authorization to execute. I reconstructed the new N8 premises from the source and saved outputs before reading the full B02 critic and the DM’s interpretation. I then obtained bounded implementation/cost facts from the owning DM. The assignment itself supplied result facts and candidate axes; this was not a blind review.

The empirical premise is strong enough for this finite question, but narrower than “the scorer needs repair.” B02 used source `9928d34b54628baaa542961debb65c5ce7ef0f23`, published results at `b7165f329`, and 16 fresh matched N8 worlds. Its complete means were:

| Program | Native J | Users served/tick | Path m/UAV | Worker CPU, 16 episodes |
|---|---:|---:|---:|---:|
| C | .615036 | 39.049875 | 260.115 | 81.55 s |
| J, immediate joint control | .631313 | 40.300750 | 274.177 | 1,589.09 s |
| R | .648963 | 41.853000 | 450.674 | 104.68 s |

R−J was +.017650 J and +1.552250 service, with the frozen descriptive paired-bootstrap intervals above zero. Nevertheless, five worlds lost J, seven lost service, quality fell, and R’s mean service-p05/minimum remained below J’s. R is already economical relative to J; neural amortization is not an established need. [Complete native summary](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b02_silent_repositioning_a01/summary.json), [complete reading and adverse worlds](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_transmission/NOTES.md:619).

The useful new observation is the full relocation–activation–resumed-control behavior. R initiated in 14/16 worlds; all selected members were already at 50 m, all activated and remained active, and transit service was invariant. C stopped moving by t36 in every world, so its stationary t40 stay forecast was accurate on this panel. Twelve initiated worlds improved further after C resumed. R’s forecast gain was .017856 J versus realized .033927 J. In the saved R trajectories I checked, resumed movement sometimes persisted substantially beyond arrival: world 29324012 continued moving through t101 after arriving at t60. A short fixed suffix would omit real behavior.

Those are observations. The conjecture is that continuation gains differ enough between candidate options to alter a useful choice. The strongest opposing explanation is that the stationary scorer already picks essentially the right representative: continued C improves its chosen destination without changing which destination should win. Selected-option underprediction does not reveal unchosen-option regret.

The lawful contract stays specific. There are eight physical UAVs, 50 static users, H500, capacity ten, a 0 dB eligibility threshold and deterministic free-space radio. The scalar objective is `.7 served/50 + .3 quality − .1(mean height−50)/100`; all eight heights count, including silent members. Commands are the 27 Cartesian ternary vectors, executed at 30 m per axis per tick with native clipping. Masks are nonempty integers 1…255, changed at ten-tick boundaries and held between them. C gets the existing 133-float public global report at those boundaries and otherwise propagates its own issued-command history. It selects motion under the old mask before E chooses the next mask; the rotating member order uses absolute `t mod 8`. This is the existing centralized public-model contract, not a new decentralized-information claim. [C/E source](/home/fires/hmasd-wsl/experiments/candidates/uav_fleet_transmission/control.py), [frozen state machine](/home/fires/hmasd-wsl/experiments/candidates/uav_fleet_transmission/b02/controller.py).

T should have the following complete meaning:

1. Execute exactly C through t39. At t40, enumerate the unchanged R member/site candidates: each currently muted member, the existing 100 user/centroid sites, original grid projection, descent, aligned duration and stationary scoring law. Retain the stationary-best candidate for each muted member, at most seven. Retain champions with nonpositive stationary gain. Thus R’s best physical candidate is included without screening on a new result.
2. Add declining relocation and continuing C/E. Evaluate each retained complete option in a separate public model: original silent transit with the other members held, the original 128-mask arrival search and all-zero arrival transition, then unchanged C/E through t499. For the decline branch, continue C/E immediately from t40. Preserve the actual pre-t40 issued commands, old mask and absolute clock.
3. Maintain separate modeled physical positions and controller estimates. Seed the model only from decoded public coordinates. At future legal report times, synthesize the exact float32 encoding from modeled physical positions; preserve the static public user-report bits. Score each modeled reward after the modeled physical action, rather than substituting C’s selected candidate score. Do not read future native reports, actual hidden coordinates or recorded future C commands.
4. Rank options by complete modeled remaining J, complete modeled service, shorter original transit path, shorter aligned duration, lower member and lower site. Initiate only for a strict modeled-J gain over the continued-C branch; otherwise decline. Full resumed path is measured, not newly priced. Keep R’s actual program value distinct from the model-only value of its best physical candidate when R declines.
5. Execute just that chosen original option, including its unchanged arrival reset and subsequent C/E. There is no additional option opportunity or replanning during the commitment. Exclude cycle compression and early stationary-tail truncation from this first study. Existing within-decision score/geometry caches remain legitimate.

The fixed shortlist is consequential: this tests continuation-aware selection among member representatives, not optimization over all 700 possible plans. It also updates the value of declining, so a benefit could arise by avoiding an option when C still has useful work on a new world. That is part of this complete selection rule, not isolated evidence about destination scoring alone.

Within its model, T cannot score below the actual R program, because that program’s continuation is represented by either its retained champion or C. That is a finite-candidate inclusion argument, not a native improvement theorem. The public-coordinate approximation remains real. Small coordinate errors can cross radio thresholds or change an argmax, causing different later C actions; B02’s accurate arrival predictions do not bound full-continuation error.

The smallest worthwhile complete observation is **16 new matched worlds × C/R/T, H500: 48 episodes, 24,000 native transitions, zero fits**. Freeze unused world/RNG addresses, initial-array hashes, source/configuration and the bootstrap seed before exposure. Use the same declared world generator, full final trajectories and all worlds; no favorable-world replacement or outcome-dependent extension. The sixteen worlds are the independent evaluation units. There are no independent training units.

R is the competent matched reference for the new selection question. Fresh C is worth its small marginal cost because it prices declining relocation and can reveal a T−R gain that still fails to repay the option versus ordinary control. J remains a retained alternative with better observed startup tails; this study makes no fresh T−J or globally-best-controller claim. Buying J’s much larger execution cost is unnecessary for this narrower comparison.

Read complete paired T−R J and service first, then T−C and R−C. Preserve the same descriptive 10,000-draw paired-world bootstrap style, all world differences, quality, all-vehicle height charge, p05/minimum/zero-service runs, capacity/eligibility accounting, complete path, boundary exposure, active transmitters and all costs. No physical energy price or deployment deadline is being invented.

Decision exposure must be part of that reading. Record the full candidate/champion identities and forecasts, declined/initiated choices, selected member/site/duration, changed requested options, and actual command/mask/position differences. Different indices can alias into the same physical behavior. For both the selected T program and the actual R program, compare modeled and realized remaining return on their common-prefix world. Do not call unexecuted candidate forecasts native counterfactual labels. Verify exact C/R/T prefixes through t39; when T and R choose the same physical program, their later native trajectories should agree under this deterministic host.

The plausible outcomes change different choices:

- **Changed physical choices, better complete J and service:** retain a conditional continuation-selection capability, with its measured compute, path and tail tradeoffs. This supports this finite shortlist, not all-option optimality, learning necessity or physical adoption.
- **Better forecasts but identical physical choices:** the model may be more accurate, but this correction has not supplied control value. End unchanged T investment; retain economical R. Sparse changes give a correspondingly narrow exposure result, not a broad null about anticipation.
- **Changed choices and adverse complete outcomes:** reject this T package. A model-versus-native ranking reversal is informative, but does not automatically identify quantization, shortlist restriction or any particular repair as its cause.
- **J/service/tail tradeoffs or unresolved small differences:** preserve the actual conditional findings. Neither equivalence nor a uniformly better controller follows, and another panel is not automatic.
- **Technical failure or broken bindings:** retain attempted cost and the missing comparison; do not impute zero or classify it as scientific harm.

Both T and R share the pre-t40 startup, so this proposal cannot repair that common early history. Higher complete means would not erase the observed quality/path/startup tradeoffs or the earlier N4 active harms.

The complete price is bounded but material. Source-based worst-case worker counts for the proposed 16-world panel are:

| Item | Bound or estimate |
|---|---:|
| Native episodes/transitions | 48 / 24,000 |
| Fits, optimizer updates, learned-model queries | 0 / 0 / 0 |
| Candidate-score requests, all three programs | 22,636,832 |
| Additional complete public-model transitions for T | 58,880 |
| Original option-transit propagation, R and T combined | at most 896,000 modeled ticks |
| Worker CPU | estimated 15–30 minutes |
| Full-reader CPU | separately estimated 15–30 minutes |
| Implementation/checks | estimated 4–6 labor hours |
| Focused engineering review | estimated 1–2 labor hours |

The score bound includes up to 873,094 extra continuation requests per T world: one 460-tick C branch and seven complete option branches, charging direct modeled reward at every tick. Counts distinguish model work from native transitions and requests from actual scored states/geometry reuse. The full reader must reconstruct every retained branch and champion, then all 48 native trajectories; checking only T’s winner would miss the selection claim. It adds comparable computation. Timing estimates use the completed local implementation as an anchor, not a cap or benchmark on the eventual admitted node. Native recording, imports, storage/RSS, preparation, transfer and review must be reported separately where measured; they are not zero.

For context, B02 itself cost 3,494.77 measured worker-plus-reader CPU seconds. B01+B02 already incurred 208 episodes/104,000 result steps and 5,020.96 worker-reader CPU seconds; historical asset fitting and incompletely metered support remain incurred. T requires no teacher-data acquisition or new trained asset. Its online public-model searches are the acquisition/computation bill, not free counterfactual evidence.

No known hard interface gap emerged. The bounded engineering work is a direction-owned public C-state emulator, member-champion collection, T selection/execution and complete reader. The high-risk checks are exact report encoding, correct old-mask/motion order, absolute clock and actual command state, branch isolation, nonpositive-champion/tie handling, complete failed/declined records and refusal of incomplete or altered evidence. These checks have not run. Root selection, source publication, engineering acceptance and actual-node admission remain future execution steps; this review authorizes none of them.

I considered a real cheaper alternative. Keep R’s chosen path fixed and compare R with immediate E during transit and with mask selection by the next ten transit-tick total J. All use legal ten-tick boundaries and the unchanged arrival reset. Source inspection establishes no native connection/battery/handover memory that would carry earlier masks into the common post-arrival C state. Thus benefits are confined to at most 40 transit ticks, with identical path and later control. The DM prices R/R_E/R_10 at the same 48 episodes/24,000 steps, at most 10,282,512 worker requests, roughly 10–30 worker-plus-reader CPU minutes and 3–4 engineering/review hours. Immediate E is needed there to distinguish ordinary activation access from ten-tick valuation. I decline this alternative for the present investment because T asks about persistent option consequences; this is an investment preference, not evidence that timing is useless or that T has headroom. Do not append it as another sweep.

The literature supports this construction as familiar rollout reasoning, with explicit limits:

- **DIRECT — Bertsekas, arXiv:1910.00120v3, §1.1:** standard rollout evaluates a candidate using the base policy’s cost-to-go; its improvement statement uses that correct evaluation. **INFERENCE here:** evaluate the actual C continuation instead of a stationary destination. The theorem does not transfer through our public-state approximation or restricted shortlist. [Primary paper](https://arxiv.org/pdf/1910.00120).
- **DIRECT — foundations B03, Oliehoek–Amato, §8.2, book pp.100–102:** macro-actions comprise primitive behavior and termination, and their value includes the primitive-time reward sequence. **INFERENCE here:** transit, arrival and resumed control all belong in the price/value. The local PDF/chunk body was absent, so I read the authors’ primary PDF directly; [local metadata](/home/fires/hmasd-wsl/docs/new-libs/corpus/papers/B03/metadata.json), [author PDF](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf).
- **DIRECT — Inst-sci MARL-0016, Wu et al., Method/Theorem 1:** multi-step model errors interact with the policies and affect predicted-versus-environment return. Its learned local-model setting differs from this analytic public model. **INFERENCE here:** accurate arrival geometry is insufficient to certify later choices. [Structured primary text](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json), [PDF](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0016.pdf).
- **DIRECT — My-lib `neurips-2024-2e8eaf43f20948ad878e6b8902797d1e`, Policy Mirror Descent with Lookahead, §§3.2/4.2:** lookahead changes policy improvement and incurs additional computation; its exact guarantees assume exact values/greedy operations in its MDP setting. **INFERENCE here:** price the full continuation and test native choice value, without borrowing a convergence guarantee. [Primary PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/neurips-2024/2e8eaf43f20948ad878e6b8902797d1e/arxiv-2403.14156.pdf).

All three library catalogs were searched; these are primary passages, not hint-based novelty claims. The proposed method is not new architecture. The July check also stays scoped: [G48’s record](/home/fires/hmasd-wsl/docs/research/cdc/EVIDENCE_NOTES/20260729_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_FORMAL_RESULT.md) and its [corrected external reading](/home/fires/hmasd-wsl/docs/external-review/rounds/20260729_g31_realized_successor_channel_attribution_g48_formal_result_evidence_boundary_correction/21_PRO_OPEN_RAW.md) concern removal of a particular post-anchor successor-credit channel, not a rejection of temporal control. The [July opportunity-contract review](/home/fires/hmasd-wsl/docs/external-review/rounds/20260720_supplied_executor_opportunity_contract/21_PRO_OPEN_RAW.md) correctly warns that filtering a myopic rule onto a different commitment clock does not create an opportunity-feasible upper bound. Neither old adviser opinion supplies today’s result or requires a preliminary oracle experiment. I did not re-audit those historical raw runs.

The recent local-peer forecast result supplies a directly relevant caution: large broad prediction improvements produced only nine changed physical R decisions and no demonstrated complete mean gain. Its published reading reinforces the need to observe actual choice exposure here; it is a different host/interface and does not predict T’s outcome. [Published exposure reading](/home/fires/hmasd-wsl/docs/research/candidates/uav_local_peer_forecast/NOTES.md:1058).

For cross-question allocation, I put this N8 comparison ahead of the new learned continuity-cost-to-go purchase. The latter is a plausible, distinct question: learn remaining M-continuation interruption cost and use it inside lawful command/mask search. Its current proposal buys 192 new acquisition episodes, two fits on one dataset, and 320 fresh evaluation episodes: 131,072 new native steps, about 8.56 million candidate requests and 0.94 million deployed value queries, plus the full reader. Its roughly .83 scheduler CPU hour + .70 reader CPU hour estimates still exclude unmeasured fit/feature/support cost. The serious uncertainty is transfer from observed M/one-intervention suffixes into planner-selected synthetic states. I checked the published waiting result directly: the prior A intervention changed 644 choices yet A−M’s primary mean-user-maximum-gap difference was +.62875 with an interval crossing zero. That is a reason to price this new extrapolation risk, not a proof that learning cannot help. [Underlying result](/home/fires/hmasd-wsl/runs/uav_user_waiting/b02_continuity_a03/result.json).

The inherited-policy reward/calibration proposal remains complementary and worthwhile in my earlier recommendation: two native reward continuations of the two retained assets, two explicitly paid calibration procedures, and at most 344,064 new native steps, with a 4–8-hour engineering estimate. It asks a broader learnability question than N8, at a different native/model-compute price. Its older PPO losses remain real risk. Calibration winner B* need not generalize above fixed Q or C, so improvements over S and B* alone cannot establish an ordinary-control increment; the already included matched R−Q/R−C readings retain that role. The pending inheritance allocation dissent remains separate. Current parent B04 stays frozen, with its original asset and coupling question.

These rankings are not prerequisites between studies. If Root can fund both distinct questions, N8 need not delay inheritance or become a positive gate for continuity learning. Conversely, the desire for four active DMs does not justify buying all three. With only one additional implementation investment available, I favor the bounded N8 C/R/T study for its demonstrated underlying capability, finite complete observation and lower acquisition uncertainty. Retaining R without a new study is also a defensible cost choice; it would be a declined investment, not a scientific exhaustion of the question.

My verification scope was source- and saved-data-only: I checked all 16 B02 source hashes against the accepted commit, config/summary/reader identities, all 48 recorded episode reductions, and the hashes and consequential positions/masks in all 16 R raw trajectories. I read the full original B02 critic and published positive/adverse reading. I did not repeat its full candidate/native-physics audit, run a controller/radio/model query, evaluate an unchosen option, fit anything, edit records or code, or launch an experiment. The proposed effect and runtime remain unmeasured.

MATERIAL_DISSENT: no — for this new N8 selection boundary. The supported correction is to retain R and test one explicitly priced continuation-aware choice rule; no conflicting N8 run or broader claim is currently selected. This does not dispose of the separate earlier inheritance-allocation dissent.

<a id="b03-allocation-addendum"></a>
### Complete Oracle allocation addendum and locator correction

Addendum to the full original N8 recommendation, 2026-09-30, after parent B04 publication c0a9ddc5 and the completed continuity design. Preserve the original text; this addendum replaces its cross-question priority statement and its continuity-reader timing estimate. The N8 C/R/T construction, 48-episode/24,000-step observation, query bounds, feasibility gaps and outcome rules are unchanged.

If Root can fund only one additional implementation, I now put the inherited-policy reward/calibration study first, N8 C/R/T second, and the learned continuity-cost-to-go study third. This is an investment preference under a shared resource constraint, not an execution authorization or a requirement that one study finish positively before another starts.

The changed premise is B04’s predeclared matched ordinary comparison. Its independent-decoder S_I−Q_I result was +0.0240748685 J, t95 [0.0081761524, 0.0399735846]; +1.7670288 served users/tick, [0.6480076, 2.8860500]; +3.546875 service-p10, [2.0252384, 5.0685116]; and −1,232.241 m/UAV path, [−1,674.902, −789.581]. There were 27/32 positive J worlds. World 29346004 remained a substantial adverse case: −0.100149 J, −7.037109 service and −9.25 p10. The primary coupling treatment S_A−S_I failed; this does not reopen A/B continuation.

This weakens the explanation that the useful inherited S behavior is entirely ordinary fixed-0.1 randomization. It does not establish superiority to the proposed paid calibration winner, improvement from native-reward training, a learned-information attribution, a second independently trained asset effect, or a universal gain. B04’s two action tapes are repeated evaluation within worlds, not independent acquisition or training replications. Its precise decoder is also part of its contract; the inheritance proposal should retain its declared original sampler rather than silently change it. Preserve the prior inheritance calibration-world clarification: the first 32 of each reward-continuation’s 256 training worlds are intentionally shared with calibration, while final worlds remain fresh and all lineage addresses are prebound.

At comparable quoted engineering ranges—inheritance 4–8 hours, N8 roughly 5–8 including engineering review—the stronger ordinary-comparator premise makes the unresolved reward-developability question my preferred next purchase. This does not follow from comparing the magnitudes of two different hosts’ scores. Native-step counts and score/model counts are unlike resources, and neither proposed complete runtime has been measured. The old adverse PPO evidence and calibration alternative remain essential. N8 retains the more direct model-based continuation question and its demonstrated economical R baseline; its usefulness has not decreased.

I read the full original B04 critic and the relevant published result reading, then bound source/config/summary/reader identities and recomputed the S_I−Q_I contrast from the saved episode reductions by first averaging the two tapes per world. I did not repeat the full raw-physics/actor audit or create another result-review round. Source e7225b0c7c428472b7349b6cce1f64fd42b97049; summary SHA256 1a17c21b90749b06f9495ec6e253e4a2b106da4ac0bce11f62261dfd2a2ec262; reading 90a2561139f3d96cfa320fd16e4374a2e92832a92c8ae60f005ba8a62da79fda; config be080840996f7e5e5de2f73f745b85f9f5e942f8d810428fe1842d1a12138833. Files are under runs/uav_parent_adaptation/b04_shared_decoders_a01/ only if that exact path is confirmed by the owning record; use the accepted identities and parent B04 NOTES rather than infer a new path from this message.

I have now read the complete Oracle continuity proposal. Its acquisition/two-fit/320-evaluation construction is distinct and testable, but selected-state extrapolation remains the central risk. Correct the earlier 0.70 reader-CPU-hour estimate to the DM’s conservative approximately 1.2 hours; the whole proposal is roughly 2–3 CPU hours with feature, fit and support overhead still unmeasured. Its deterministic reader also replays the ridge solve and 4,096 Adam updates. Those are charged reader computations, not independent training replications. The cheaper M/S/G0 comparison remains a real alternative to purchasing learning; it is not a mandatory positive gate.

The earlier inheritance-allocation dissent should remain historically visible. Completion of B04 with this useful predeclared ordinary comparison has overtaken the specific B04-first sequencing dispute; Root can close that item explicitly on the new evidence rather than a DM silently clearing it. No current N8 run has been selected in conflict with this recommendation.

MATERIAL_DISSENT: no — at the present N8/new-investment boundary. Recommend retaining the N8 C/R/T proposal, with inheritance first if only one implementation can be bought. Root owns allocation and disposition; no run is authorized.

**Oracle's immediately following source-locator correction (original delivery):**

Path correction to the addendum: the actual confirmed B04 directory is `runs/uav_parent_adaptation/b04_joint_sampling_a01/`, containing config.json, summary.json and reading.json. Disregard the conditional guessed-directory sentence in my preceding message; it was unnecessary and should not be used as a source locator. The stated file hashes and scientific interpretation are unchanged.

### DM response and completed design boundary

I read the complete addendum and correction. I accept the unchanged N8 C/R/T construction
and preserve the revised cross-question preference: under a one-implementation constraint,
the new matched ordinary-comparator evidence makes inherited-policy development the first
purchase, with N8 next. This does not reduce the scientific usefulness of T, compare score
magnitudes across hosts, or require a positive preceding study. Within this N8 question I
still prefer T over the priced transient timing alternative. There is no material N8 dissent
to resolve and no distinct additional Pro question at this boundary. I do not clear the
historical inheritance dispute or select another lead's work; Root owns that disposition.

The main explanation is deliberately still unresolved: complete C resumption adds observed
value to R's chosen paths, but the value of changing those choices has not been measured.
This design makes the necessary physical-choice/native-return comparison concrete and costed.
It establishes source feasibility, not a tested implementation or a result. The current task
returns the prospective design and recommendation to Root; **no result study or execution is
selected**. B02 remains closed, fully published and cleaned. No new worker, observer, fit,
query artifact, unconsumed advice or cleanup target was created by this preparation.

Publication self-check: all16 accepted B02 source-file byte counts/SHA256 still match the
current files. The corrected B04 directory's config/summary/reader hashes match all three
identities in the addendum. This notebook change is a pure append and passes `git diff --check`;
no B03 implementation/test directory or owned scratch directory exists. These are document,
binding and source checks, not an executed model or prospective-panel test.

The final publication refresh read `1ab42997a5a805764d5c54e3fdd810fcc2fdf514` on
published main. Its new Root allocation selects the separate inherited-policy and user-waiting
studies while N8 still awaits this complete design return. The relevant shared scientific
background and this direction's lead/paused scope are unchanged. I preserve those separate
decisions and make no N8 execution inference from them.

<a id="b03-selected-implementation"></a>
## 2026-09-30 — B03 selected; bounded implementation

Root selects the complete design at `9e2eabd278024c3cbbb525da0b2ed189b11899c8`
([published decision](../../RESEARCH.md#n8-continuation-root-decision-20260930)). The exact
16-world C/R/T panel, scopes, costs, outcome reading and exclusions above now apply to
implementation through complete reading/publication/cleanup. This is not an extension or
restart of B02. Current owner pause is lifted for this Root scope; this direction is exploring
with the existing `Codex DM (native child)` lead. The applicable full independent selection
review and allocation addendum are already read; no changed scientific premise calls for
another selection round. Actual node admission still precedes execution, with wsl_4070 first.

**L0.** Deliver the fixed continuation selector in new owned
`experiments/candidates/uav_fleet_transmission/b03/` with mirrored tests and a guarded
`run.py` entry, preserving every accepted B02 source. DM owns world bindings, champion/T
selection and execution, worker/reader, source and run records, this notebook and publication.
The registered Implementer is loaned only `b03/surrogate.py` and its mirrored
`test_surrogate.py`: one pure public-model continuation from the copied t40 C state, original
report bits and optional already-specified original R plan. It selects no candidates and
touches no environment, result launcher, notebook, shared file or Git index. Other writers
remain in the shared main checkout; helpers must preserve their edits and spawn no children.

The surrogate must leave its inputs unchanged; copy the actual issued-command, next-tick and
predicted-position state; use the actual t40 public report unchanged; and synthesize only later
reports with exact FP32 encoding and preserved static user bits. Separate model physical
positions from controller estimates. Reuse original forced-transit/arrival/C-resumption
semantics without re-enumerating R. Score each model-physical post-action state, accumulate
returns in tick order, and expose full positions/actions/masks/reports/estimates, decision
digests, direct reward scores, counts and complete-branch summary for independent readback.
Keep model calls separate from actual native steps and from original candidate propagation.

Checks cover codec equality, input purity/history/clock, old-mask order, branch isolation,
nonpositive champions/ties/global-R inclusion, complete selected/declined serialization,
native correspondence on constructed fixtures and refusal of altered/incomplete evidence.
Pure helper fixtures may use a shortened tail solely for correctness; production requires
t40/H500. Native correctness is prospectively bounded by **128 additional transitions** on
constructed/old-world fixtures, never on the sixteen new result identities; record actual
cost separately. No new-panel outcome pilot or exposure threshold is allowed. Independent
engineering review covers the complete changed numerical/controller/reader/entry path before
publication/launch. Stop on a consequential interface contradiction or material scope change
and return it to Root; otherwise complete this one selected panel with no automatic expansion.

### Implementation acceptance and prospective node correction, 18:45 UTC

The new B03 implementation now retains every original stationary candidate row, the exact
per-member champions, all complete model branch arrays/decisions and the executed C/R/T
trajectories. The reader reconstructs every retained branch and original candidate enumeration,
then all native physics, observations, control decisions and counts. Program identity includes
the arrival member and primitive commitment; separate modeled-execution and site-alias readings
do not assert that a model-only alias guarantees native equivalence. C and R call the unchanged
B02 worker/reader. All16 accepted B02 source bindings still match their recorded bytes/hash.

Generated and source-bound only the declared16 initial arrays at address `[260930,26]`, with
their little-endian-float64 hashes and runtime seeds. No policy, radio, model or native outcome
on those identities has been queried. The helper's pure surrogate implementation was read and
accepted with its six checks. The full local B03 suite passed21tests in5.38seconds, including
two13-step constructed native tails: **26actual native correctness transitions**, below the
prospective128 ceiling. After adding the required alias readings,13affected selector/reader
checks passed in4.59seconds, adding zero native transitions. All new Python files parse and
the owned sources have no trailing whitespace. Existing matplotlib deprecation warnings were
the only warnings; no fixture/test scratch was retained.

Independent engineering Reviewer `/root/dm_fleet_transmission/engineering_review` read the
new implementation and returned **no material finding** after checking original-R inclusion,
nonpositive champions, strict C-stay improvement, copied history/absolute clocks, FP32 reports,
separate physical/controller positions, complete replay, alias scope, costs, bindings, admission
order and incomplete-attempt refusal. It independently ran19zero-native tests (4.82seconds)
and confirmed the frozen B02/host/control diff is empty. It added zero native transitions.
The explicit coverage limit is retained: **no end-to-end T/H500 native worker-to-reader fixture
has run**. Checks combine short native/model tails with separate selector, serialization and
refusal tests; the selected complete operation must still pass its full reader. I accept the
implementation and review; this is engineering acceptance, not a scientific result.

Root initially reserved the next heavy `wsl_4070` window for the already-selected waiting
study. Before any N8 accepted operation, Root then prospectively **selects `local_linux` for
this complete N8 panel**, after verifying that `local_linux` (AMD8745H) and `wsl_4070`
(Intel13900H) are separate Windows physical hosts. N8 has no online wall-time deadline;
waiting/composition need the other node, while local fleet-adaptation currently owns its
producer/reader CPU window. This is the current explicit Root resource allocation, replacing
the preceding remote-first arrangement. It does not inherit the prior B02 local-preference
deviation or use an old interpreter failure as an automatic fallback. No accepted operation
has moved, stopped or restarted.

The selected local configuration is `/home/fires/.venvs/hmasd-linux-cpu/bin/python`, observed
Python3.10.20/NumPy1.26.3/Torch2.7.0+cpu, one Torch intra/inter-op thread. All worlds, masks,
commands, dtype/order laws, C/R/T branches, reader and prospective scientific cost bounds are
unchanged. Fresh actual-node pause/lead/source/memory admission still applies after publication.
The concrete execution dependency is the existing fleet-adaptation producer+reader's original
handle reaching terminal/resource release, coordinated by Root. No N8 result worker or full
reader will overlap that reserved local heavy-CPU window. The planned fresh output is
`runs/uav_fleet_transmission/b03_complete_continuation_a01/`; it does not yet exist.

### Published inputs and resource release, 18:51 UTC

Published exact B03 source, bound arrays and tests at
`837b7d2376d06131c13be66d17c9e5cf2f97fb6e`; origin/main publication verified. Before any
N8 acceptance, Root publishes `4e05c7d60` and releases the preceding local sequencing hold:
both fleet studies have no online wall deadline and use one computation thread on this
16-affinity-CPU host, while deadline-sensitive work uses the separate machine. They may
overlap when actual-node memory/occupancy permits. This supersedes the prior dependency;
it changes no scientific input or result scope and authorizes no second N8 chain.

The fresh18:51:20UTC local sample reports16affinity CPUs, load averages
`.3081/.4424/.3926`, MemAvailable6,845,812KiB and no observed live heavy Python worker;
two older Python processes report0.0%CPU. This is a point-in-time occupancy reading,
not admission or a promise of an idle host throughout execution. The launcher still checks
fresh effective/physical memory before release. Retain actual CPU/wall times; they are not
an interference-free speed benchmark. Owner pause is lifted, the direction remains exploring
under its unchanged lead, and the B03 executable/test paths are clean. Proceed with one
`local_linux` snapshot launch at the published source above and one continuous worker/reader.

### A01 accepted technical failure and narrow repair scope

A01 was accepted at18:52:17UTC from837b7d237 on `local_linux`; the kernel measured
7,161,356,288available/effective bytes against the4GiB floor. Preserve
[manifest](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a01/launch-manifest.json),
[preflight](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a01/admission-preflight.json)
and [exit witness](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a01/process-exit.json).
The same-handle observer immediately returned valid exit1 at18:52:19.729UTC, with both native
runner and supervisor absent and records consistent. The operation reference is
`.git/hmasd-admission/f0bf0c99e766f375d496f6a59ebbcd46b2649b640999f8c69ecc743f37bd5c5f.json`;
source snapshot8341f5d7c61343a3bf8d0898931b925a remains until verified reclamation.

The traceback reaches `study.run_study` configuration construction and reports
`KeyError: 'operation_id'`. No config, summary or raw directory was created. The code reaches
this before any episode/environment/model/controller query, after initial-array validation:
**zero result episodes, native transitions, fits or model/controller queries**. Import/support
cost was paid; no worker CPU/RSS telemetry was emitted, and it is not treated as zero. This
is missing execution, not an adverse C/R/T observation. The full panel remains unexposed.

Source inspection of the actual `require_admission` return shows schema_version, direction,
sha, command_sha256, parent_pid, child_pid and accepted_at_epoch; it has no operation_id.
The earlier mocked worker test supplied the nonexistent field, so neither it nor review
covered the real interface. Narrow L0 repair: reproduce this mismatch against the actual
guard's returned mapping in a zero-native fixture, consume its real command_sha256 in the
worker config, validate that binding against the accepted manifest in the complete reader,
and obtain focused independent engineering review. No controller, world, score, branch,
endpoint or budget changes. Preserve A01, publish the repair and justify one fresh A02 at
the repaired source after fresh admission; do not replay A01 or label its failure as data.

`hmasd_wait` generation1 delivered the terminal fact through manual same-state drain; native
App queue delivery is unsupported for this child, as already known. Its event was consumed
with generation2 and observation stopped without touching any worker. The same active-turn
deterministic observation discipline applies to a subsequent accepted operation.

The zero-native regression called the actual guard body with a mocked effect-free grant and
reproduced A01's exact KeyError before changing production code. The guard bytes also match
the failed immutable snapshot (SHA256
`0faa5d53fba5af9b1a2fc4979bde5bd50bcbcaac2dbef938e90a64680156cf4d`). The repaired worker
records `admission_command_sha256`; the reader validates its64hex form and agreement with
the accepted manifest's command/source/direction. Four focused reader tests pass in1.66s,
including the real-return fixture and a mismatched-manifest refusal. They add zero native
transitions; the cumulative native correctness count remains26.

The same independent engineering Reviewer inspected these three changed files, the actual
guard/launcher and A01 manifest, independently ran all four tests and found no material
remaining issue in the repair. Full native worker-to-reader completion remains to be tested
by the selected operation. I accept this narrow repair. Record A01's compact native/traceback
evidence and publish the three-file correction, then execute one outcome-blind
`b03_complete_continuation_a02` at that new published source with the same16worlds and all48
complete programs. A01 has no exposed trajectory to repeat, and a new source is needed to
correct the interface; this is not a same-source retry or a changed scientific study.

### A02 accepted and observed, 19:00 UTC

Repair/A01 evidence published at `02e8c1adc5a625037490facc6388e4b8bc9fd74e`. Fresh A02
was accepted from this source on `local_linux` at19:00:08UTC after actual-node admission
measured7,078,412,288available/effective bytes. The preceding18:59:39UTC occupancy sample
had16affinity CPUs, load `.6216/.5552/.4653`, MemAvailable6,926,108KiB and no observed heavy
Python process (an older small Python3 process showed1.7%CPU); this remains a snapshot only.

Keep [A02 manifest](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/launch-manifest.json),
[preflight](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/admission-preflight.json)
and immutable [config](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/config.json).
Exact operation reference:
`.git/hmasd-admission/5f5df023bf6fdb1a8f9bf41f47ebc2923e6d761400b66a820f2f408b62b6138f.json`;
source snapshot `b70bade3003946de9ca9f65580ebc865`. The first same-handle observer drain
confirmed native runner1152518 and supervisor1152517 running with matching start identities
and consistent records, and three completed episodes. Generation1 is armed under the owned
`b03_wait/state-a02` against that exact status handle. One accepted operation performs all48
episodes and the full reader. No collection/result conclusion is implied by acceptance; the
native child remains active through deterministic observation and complete reading.

### A02 complete collection, 19:23 UTC

The original operation exited0 at19:20:34UTC. Native status finds both recorded processes
absent, a valid exit witness and consistent claim/manifest/source records. Save the original
[terminal status](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/launch-status.json)
and [exit witness](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/process-exit.json).
The same observer reported READY at19:20:41UTC, event `b8ae5cfbb50d5fc259d2efd8`,
wake `d379d035-6623-4d88-8603-9cdb8b6c987f`, generation1. Native-child queue delivery again
returned the known unsupported multi-agent-input error; the still-active DM drained the
event at19:21:46UTC, consumed its exact generation/wake/event tuple through rearm1→2 and
stopped the observer. No worker restart or duplicated reading was used.

The worker and inline reader both completed all48episodes/24,000native steps. The reader
checked24,048native snapshots, all three decision streams, all16common prefixes, all5,800
original stationary candidates and all74retained complete modeled branches (34,040modeled
physical transitions). All25bound source files still match accepted/published source
`02e8c1adc5a625037490facc6388e4b8bc9fd74e`. The DM independently verified262artifact
bindings including config and reading, all48native endpoint reductions, all16prefixes and identical
R/T programs, the model-inclusion selection inequality, and15paired bootstrap intervals.
The independent path reduction used a different summation order and differed by at most
1.1368683772161603e-13m; J/service/quality/height reductions and prefixes matched exactly.
This check changed no production tolerance or result. It used saved arrays only, adding
zero native transitions or controller/model queries.

Complete [summary](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/summary.json)
SHA256 `df0d60b900d816bc93fed1855feca1afc9050dc2b719b017a7beb5d159a5cd7d`;
full [reading](../../../../runs/uav_fleet_transmission/b03_complete_continuation_a02/reading.json)
SHA256 `e3cbc277e478d4e17ac6c347d86c776376fd6a50bbe58994c7f125e5a47c97e9`;
config SHA256 `a945dcd2fda619d68d8c1a025e5ef2762e50e11fc023c683106434c3a94023be`.
The260unique native/model/candidate bulk files total44,795,108logical bytes. The independent
ResearchCritic first read the original design, Oracle advice, source and B02 adverse evidence
without partial A02 outcomes or new queries; after terminal collection it received the complete
evidence for substantive diagnosis. Scientific disposition and final retention/cleanup follow.

<a id="b03-complete-reading"></a>
## 2026-09-30 — B03 complete reading: useful continuation selection with a substantial compute premium

The fixed C/R/T comparison is complete at source `02e8c1adc5a625037490facc6388e4b8bc9fd74e`:
16fresh N8/c10/0dB/H500 worlds,48episodes/24,000native steps, zero fits or updates. The
published prospective comparison at `22c025c52` and full original independent advice remain
above. A01 failed before exposure and is retained separately; A02 is the single exposed
panel. The exact original B02 C/R programs remain unchanged. The complete machine reading
and all-world artifacts linked above, rather than rounded tables below, are the evidence.

### Complete levels and planned paired comparisons

| Complete H500 level, mean across16worlds | C | R | T |
| --- | ---: | ---: | ---: |
| Native J | .619011280 | .649481446 | .656881613 |
| Served users / step | 39.637000 | 42.204875 | 42.763500 |
| Connected-user quality | .213869165 | .195614720 | .194226840 |
| Height penalty | .000067470 | .000071220 | .000075439 |
| Ineligible users / step | 8.033125 | 6.604750 | 6.388875 |
| Eligible but unserved / step | 2.329875 | 1.190375 | .847625 |
| Active transmitters | 4.370000 | 4.861250 | 4.918750 |
| Complete path, metres / UAV | 226.832502 | 350.254372 | 372.740750 |
| Mean world service p05 | 39.687500 | 39.687500 | 39.687500 |
| Mean world minimum service | 35.125000 | 35.125000 | 35.125000 |
| Zero-service steps / longest zero-service run | 0 / 0 | 0 / 0 | 0 / 0 |

The fixed10,000draw paired-world percentile intervals are descriptive conditional intervals
for these three deterministic programs. Sixteen worlds are not sixteen training replications,
and positive lower endpoints are not a confirmation or deployment guarantee.

| Planned contrast | Mean J [95% world interval] | J positive / zero / negative worlds | Mean service [95% world interval] | Service positive / zero / negative worlds |
| --- | --- | --- | --- | --- |
| **T−R, primary** | **+.007400167 [.001879057,.014256967]** | **9 / 7 / 0** | **+.558625 [.148197,1.038134]** | **8 / 7 / 1** |
| T−C | +.037870334 [.023710045,.052083371] | 13 / 3 / 0 | +3.126500 [1.933403,4.309078] | 12 / 4 / 0 |
| R−C | +.030470166 [.017231835,.044409661] | 13 / 3 / 0 | +2.567875 [1.481369,3.706000] | 12 / 4 / 0 |

T−R quality is−.001387880 [−.006576469,+.003581172], with five negative, four positive
and seven zero worlds. Extra path is22.486378m/UAV [3.143785,45.808521], seven positive,
two negative and seven unchanged; extra height penalty is.000004219. Mean service gain
equals.215875fewer ineligible plus.342750fewer eligible-unserved users. Its J difference
equals+.007820750coverage contribution,−.000416364quality contribution and−.000004219height
contribution. These are endpoint accounting identities, not causal shares or a battery model.
R−C and T−C both reduce average connected-user quality and add travel. Native J does not
price physical path, battery, completion deadlines or planning CPU. Every world's service
p05/minimum is unchanged between arms; these tails supply no extra improvement claim.

All worlds are retained below. Member/site identifiers name the original stationary champion;
`stay` means unchanged C. The seven equal R/T programs have identical complete saved native
arrays, not merely rounded means. All nine changed programs alter actual commands, masks and
positions, with460different post-prefix position snapshots each; index aliases do not explain
the observed exposure.

| World suffix293260xx | C J / service | R J / service | T J / service | T−R J / service | R → T choice |
| --- | --- | --- | --- | --- | --- |
| 00 | .646122303 /41.984 | .646122303 /41.984 | .646122303 /41.984 | 0 /0 | stay → stay |
| 01 | .565681575 /35.992 | .628102167 /41.258 | .629041827 /41.260 | +.000939661 /+.002 | m7s8 → m6s8 |
| 02 | .622156537 /38.992 | .638771533 /41.644 | .684065114 /44.364 | +.045293582 /+2.720 | m4s33 → m3s34 |
| 03 | .616280804 /39.984 | .636541727 /41.700 | .666906332 /44.258 | +.030364605 /+2.558 | m6s36 → m2s94 |
| 04 | .682785724 /44.788 | .683250002 /44.788 | .683250002 /44.788 | 0 /0 | m1s47 → m1s47 |
| 05 | .595412717 /37.858 | .616326312 /40.558 | .629020535 /41.372 | +.012694223 /+.814 | m6s21 → m5s54 |
| 06 | .622118358 /39.992 | .622118358 /39.992 | .622118358 /39.992 | 0 /0 | stay → stay |
| 07 | .609425717 /37.902 | .661754078 /42.198 | .663059730 /42.296 | +.001305652 /+.098 | m5s83 → m0s33 |
| 08 | .646034065 /41.922 | .646034065 /41.922 | .646034065 /41.922 | 0 /0 | stay → stay |
| 09 | .634617465 /41.004 | .657056256 /42.762 | .657056256 /42.762 | 0 /0 | m0s33 → m0s33 |
| 10 | .601735319 /38.922 | .624233339 /39.820 | .624233339 /39.820 | 0 /0 | m6s24 → m6s24 |
| 11 | .609492996 /38.976 | .679523127 /44.238 | .679537980 /44.230 | +.000014853 /−.008 | m7s28 → m4s67 |
| 12 | .616491474 /38.992 | .625439305 /39.872 | .641862046 /41.622 | +.016422741 /+1.750 | m6s38 → m4s80 |
| 13 | .639554623 /40.980 | .671710001 /43.606 | .671710001 /43.606 | 0 /0 | m5s31 → m5s31 |
| 14 | .602858817 /37.918 | .680495396 /44.798 | .682312893 /44.948 | +.001817497 /+.150 | m7s34 → m6s52 |
| 15 | .593411980 /37.986 | .674225169 /44.138 | .683775033 /44.992 | +.009549863 /+.854 | m6s62 → m7s85 |

World11 is the explicit service adverse witness: T loses four user-steps over ticks65–67,
with no positive service tick relative to R, while quality rises. Both end at45served, but
T adds90.830478m/UAV for only+.000014853mean J. The model correctly predicts that service
loss; it is not a model/native ranking reversal. World12 gains1.75served and.016422741J,
but loses.026874196quality and adds145.640808m/UAV, the largest extra path. In contrast,
world03 gains2.558served with11.516504m/UAV less travel; world15 also shortens travel.
World02 supplies the largest J/service gain and ends at45served versus R's42. Two large
gains (02/03) account for much of the average; the complete table preserves the small gains.

### Physical exposure, prediction and changed explanation

R and T both initiate in13/16worlds and decline in00/06/08. The9changed choices are
rerankings among already-positive original stationary champions; no initiation/decline
decision changes. All58member champions are modeled, including10nonpositive stationary
champions, plus16C-stay branches. None of the10nonpositive champions is selected. The
5,800original member/site candidates contain681physical-alias groups, but no represented
champion branches alias in physical or complete modeled execution. All26initiated R/T
members remain transmitting from arrival to horizon with no remuting. Their arrival masks
equal their stationary predictions. The raw reader retains every champion, rank and branch.

All16C fleets cease actual motion by t32, before selection. The26initiated transit segments'
native reward components and service traces exactly match their C reference over the same
ticks. Thus this panel does not expose opportunity cost from freezing still-moving peers;
it does not establish that such cost is absent in another host. Selecting an option changes
the subsequent ordinary controller's coupled path, including other vehicles' later motion.

For the48C/actual-R/selected-T branches with matched native execution, saved modeled actions
and masks exactly equal the460native actions/masks. Full service sums match; the largest
absolute remaining-J-sum error is1.917972e-6. Model physical coordinates differ from native
coordinates by at most5.838207e-5m, consistent with the lawful decoded-public-state start.
These observations support faithful decision prediction for the executed branches on this
panel. The48native episodes correspond to38distinct represented programs:16C continuations,
13additional R programs and9additional T programs. The other36modeled branches remain
unexecuted forecasts. These observations do not turn those forecasts into native labels, prove every
shortlist branch correct, or establish a native improvement theorem. T's modeled J being
at least R's is guaranteed by finite candidate inclusion and is not the empirical result.

The evidence now supports **decision value from complete continuation ranking**, beyond
B02's selected-option underprediction: actual physical choices change and complete native
J/service means improve relative to unchanged R. It weakens the simpler prediction that
stationary champions' original global ranking is already sufficient on these worlds. The
gain applies only to one champion per muted member, not all700possible complete options,
new timing/sites, an optimal planner, or a learned selector.

The working explanation also needs a correction: resumed C is not uniformly a beneficial
addition to the selected destination. In world02, R's stationary forecast is297.221601J-sum
and19,700user-steps, but its native resumed continuation produces294.671176 and19,266.
Arrival initially serves43; later C motion drops to42 and finishes below the stationary
arrival J. The complete lawful model predicts that loss and chooses another member/site,
yielding317.317967J-sum and20,626user-steps. This is evidence about whole executed programs;
it does not identify a new controller repair or claim a universally harmful C tail.

### Measured cost and cumulative investment

| Worker cost | C | R | T, including all complete model branches |
| --- | ---: | ---: | ---: |
| State/mask requests | 1,932,000 | 2,604,752 | 10,525,608 |
| Actually scored candidates | 1,279,398 | 1,859,122 | 7,121,242 |
| Cached requests | 652,602 | 745,630 | 3,404,366 |
| Geometry rows computed | 1,137,798 | 1,107,823 | 6,035,685 |
| Geometry rows reused | 9,097,386 | 13,765,153 | 50,934,251 |
| Sum complete episode CPU seconds | 85.570255 | 108.556476 | 436.285998 |
| Sum complete episode wall seconds | 85.587733 | 108.569572 | 436.397294 |

T uses4.018977times R's measured episode CPU. Its controller-plus-branch-record CPU is
425.094114s; R controller CPU is97.459537s and C74.340997s. The branch-record term includes
serialization and cannot be relabeled isolated planning cost. Total worker requests are
15,062,360, of which7,916,026are complete-model requests including34,040physical-model reward
queries; original candidate-transit propagation is228,800ticks and ordinary candidate-position
prediction is12,121,056. All are below the prospective ceilings. The full reader separately
replays those requests/propagations and verifies native physics, observations and decisions.

Worker CPU/wall is631.790445/632.051672s, reader590.606499/591.212214s; the measured combined
study is1222.447506CPU-s/1223.314455wall-s. Whole-process lifetime CPU including imports is
1225.270095s, with.001948child CPU-s separately, and peak RSS354,964KiB. Bulk evidence is
44,795,108bytes across260files. This one-host cyclic comparison is not a deployment deadline
or a minimal-cost implementation result. The original30–60CPU-minute planning estimate was
conservative here; support, authoring/review labor, storage/transfer overhead and A01 CPU/RSS
were not metered and are not zero. A01's accepted-to-exit wall span is2.419563s, with zero
result episodes/transitions/controller or model queries. Twenty-six constructed correctness
native steps were used before launch, separately from the result panel; no new-world pilot.

B01+B02+B03 cumulative exposed result work is256episodes/128,000native steps/zero new fits,
with6243.405562measured worker-reader CPU-s, plus historical asset training and incompletely
metered support. A retained capability does not erase this cost or establish learning value.
Independent diagnosis, final disposition and canonical retention/cleanup are appended below.

### Canonical evidence collected before source cleanup

The independent reader released its raw/source consumers. A privileged read-only scan of
process cwd/argv/file descriptors found no live references and no permission errors for the
exact raw/scratch/cache targets. The260required raw/candidate/model files now have one
canonical copy at
`/home/fires/hmasd-artifacts/uav_fleet_transmission/b03_complete_continuation_a02/raw`.
Original `runs/uav_fleet_transmission/b03_complete_continuation_a02/raw` is an untracked
symlink to those same files, not another copy. All existing artifact bytes/hashes were
checked before and after the move:44,795,108logical bytes. SHA256 of the path-sorted existing
binding list encoded with sorted JSON keys and compact separators is
`b0005426adf89ab388647efb5225514611ef2d96479ee2fd19a7dc08455bf7cd`.

Nine small summary/reading/config/native-manifest/preflight/status/exit/stdout/stderr files
have byte-identical canonical copies so that the canonical run is independently readable.
An intentional full replay would use that canonical run root and accepted source, since
the reader's containment check correctly rejects resolving a local run's bulk outside that
root. No full replay is currently needed or selected. The failed A01 records remain in
their original run directory; B01/B02 canonical evidence and historical adverse worlds are
unchanged. Useful B03 implementation/tests remain published and required by the retained
capability. This collection is not itself a space-reclamation claim. Source/scratch deletion
and its net allocated-byte measurement follow publication of the complete compact reading.

### Complete original independent ResearchCritic diagnosis

The following is the original substantive response from the dedicated ResearchCritic in
its separate context. It independently reconstructed the original supporting/adverse evidence
before receiving a DM interpretation. No further native, controller, radio or model query
was used. The response is preserved in full:

**Retain T as a conditional continuation-selection capability, alongside cheaper R and C.** B03 answers the selected question positively: complete continuation scoring changed executed physical choices and improved mean native J and service over frozen R. The computation and travel premiums remain part of that result.

I reconstructed the evidence independently, before receiving a DM result interpretation. Accepted source is `02e8c1adc5a625037490facc6388e4b8bc9fd74e`; the supplied configuration, summary and reading hashes match. The operation completed all **48 episodes, 24,000 native transitions and 74 modeled continuations**, with zero fits or updates. [Native summary](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b03_complete_continuation_a02/summary.json), [complete reading](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b03_complete_continuation_a02/reading.json).

Mean J was **C 0.619011, R 0.649481, T 0.656882**; mean service was **39.6370, 42.2049, 42.7635 users/tick**, respectively.

| Complete contrast | Mean ΔJ [descriptive 95% interval] | Mean Δservice [descriptive 95% interval] |
|---|---:|---:|
| T−R | +0.007400 [+0.001879, +0.014257] | +0.558625 [+0.148197, +1.038134] |
| T−C | +0.037870 [+0.023710, +0.052083] | +3.126500 [+1.933403, +4.309078] |
| R−C | +0.030470 [+0.017232, +0.044410] | +2.567875 [+1.481369, +3.706000] |

These are the frozen paired-world bootstrap intervals over sixteen evaluation worlds. They establish conditional exploratory evidence, without training replication or a guarantee.

The choice exposure is substantial. **Nine worlds changed physical programs**, with different selected members and actual command, mask and position trajectories. All nine improved J; eight improved service and one lost service. The other seven complete R/T trajectories were exactly identical. Both programs initiated in thirteen worlds and declined in the same three. All initiated members remained active after arrival, without remuting.

Thus the observed increment comes from choosing different relocation–activation–resumed-C programs. It did not come from changing the initiation decision. Ten nonpositive stationary champions were represented, but none was selected. C had stopped moving by t32 in every world, so improving the value assigned to continuing C was also not the operative distinction on this panel.

This changes the working explanation beyond B02. B02 showed that ordinary resumption often added value to the selected relocation; it left unchosen-option ranking unresolved. B03 weakens the simpler prediction that complete continuation would merely improve return estimates while preserving R’s choices. A useful ranking difference now has direct native evidence.

World `29326002` is the strongest witness. Stationary scoring favored R’s `m4_s33` over T’s `m3_s34`: predicted gains over stay were approximately **0.021716 versus 0.016585 J**. Complete continuation reversed that ranking. The executed T program gained **0.045294 J and 2.720 users/tick over R**. World `29326003` supplies another useful positive: **+0.030365 J, +2.558 service and 11.52 m/UAV less travel**.

The model was accurate on the executed continuations. Across all 48 C/R/T suffixes, saved model outputs matched native **commands, masks and per-tick service exactly**. Maximum remaining-total-J error was **1.92×10⁻⁶**; maximum coordinate discrepancy was **5.84×10⁻⁵ m**. This supports the continuation model’s adequacy for these observed decisions. The 74 modeled branches contain only **38 distinct executed programs**; the other 36 remain model predictions without native counterfactual labels.

Ordinary known-model planning is therefore a sufficient explanation of the positive result. No new information rights or learned representation were involved. The supported capability remains selection among one stationary champion per muted member and C. It establishes neither all-site optimality nor a fresh T−J ranking.

The adverse and cost evidence prevents automatic adoption:

- **World `29326011`:** T gained only **0.000014853 J**, lost **0.008 users/tick** and added **90.83 m/UAV**. The service loss was four user-ticks at t65–67. The model predicted it correctly. This is an accurately valued objective tradeoff, not a forecast failure.
- **World `29326012`:** T gained **1.75 users/tick**, while quality fell **0.02687** and travel increased **145.64 m/UAV**.
- Across worlds, T−R quality was **−0.001388**, with an interval crossing zero; travel increased **22.486 m/UAV**, approximately **6.4%**, with interval **[3.144, 45.809]**. Seven worlds traveled farther, two less.
- Every world’s service fifth percentile and minimum were identical across C/R/T. All avoided zero-service ticks. Better complete means did not improve these service tails.
- T retained R’s marginal choice in world `29326004`: additional travel over C produced a small J gain and no additional service.

Native J prices height, not physical travel energy. These records do not establish battery savings, deployment suitability or a universal controller preference. Earlier B02 quality/startup tradeoffs and B01’s conditional findings remain intact.

Measured worker CPU across sixteen episodes was **85.57 s for C, 108.56 s for R and 436.29 s for T**. T therefore cost about **4.02 times R**, including its branch recording. Its worker used **10,525,608 score requests**, versus R’s **2,604,752**. These are measured implementation costs, rather than a deployment latency benchmark.

The entire worker used **15,062,360 requests**, **10,259,762 actually scored candidates**, **34,040 complete-model transitions** and **228,800 candidate-transit ticks**. Worker plus reader cost **1,222.45 CPU seconds / 1,223.31 wall seconds**, about 20.4 minutes; peak process RSS was **354,964 KiB**. Required raw evidence occupies **44.8 MB**. Reader reconstruction was additional paid computation. A01’s metadata failure occurred before any result/model/controller query; its import and support costs remain incurred and unmetered.

My checks covered all **25 source bindings** against Git, current files and the accepted snapshot; all **262 artifact bindings**; frozen initial arrays and RNG addresses; all 48 native metric reductions; exact prefixes and equivalent trajectories; and all 36 reported bootstrap intervals. I also reconstructed rankings and accounting from all **5,800 saved stationary candidates**, reductions and selection from all **74 saved branches**, and costs from all **122 saved decision traces**. I inspected lawful report encoding and saved motion semantics. I did not rerun candidate scoring, radio evaluation or the full reader. Those execution checks remain the completed reader’s evidence, distinct from my independent saved-data reconstruction. No material inconsistency emerged.

My recommendation is to **close this fixed B03 study and retain the measured C/R/T performance–cost choices**. I do not recommend an unchanged replication or broader option search merely because T succeeded. There is no material validity objection to the scoped capability claim; the strongest consequential qualification concerns its cost and objective tradeoffs.

This is also not scientific exhaustion. B03 makes a constructive learning question more concrete: can an inexpensive continuation-value estimate or ranker preserve useful physical choices while reducing full-suffix computation? If Root allocates further work within this question, I would prioritize that bounded approximation/amortization question over enlarging the search support. An ordinary planner using less computation remains a relevant alternative for an efficiency claim.

The smallest useful successor observation must retain complete fresh R/T/candidate trajectories and charge training-data generation, fitting, inference and travel. A learned candidate needs an explicitly declared exploratory fit; forecast accuracy alone would be insufficient. Preserved native gains with lower complete cost would support the approximation; unchanged choices without savings would supply little use value; adverse changed choices would reject that candidate while preserving B03. Data quantity, fit cost and ordinary-comparison details remain unpriced, so this is a candidate for Root’s next-question choice, not a launch-ready investment.

**MATERIAL_DISSENT: no — direct evidence supports the frozen finite-shortlist capability claim and retention of T with its costs. No expanded claim or additional result investment is endorsed automatically.**

### DM disposition and authorized next boundary

I accept the independent result recommendation and close the fixed B03 study. Retain T as a
constructive ordinary capability, and retain cheaper R/C and historical J as useful choices
with their original scopes. The empirical belief change is that complete continuation
ranking can improve executed relocation programs on this finite N8 host; merely correcting
selected-option forecasts is no longer the whole explanation. The accurate prediction of
world11's service/travel tradeoff prevents calling the score gain an unconditional mission
improvement. The first local draft's naive74−48unexecuted-branch count was corrected before
publication using the critic's de-duplication:38distinct programs are executed,36modeled
branches remain unexecuted. No raw result, policy or reader needed changing.

Task opportunity and this finite representation are supported; learnability and a lower-cost
or physically priced complete package remain open. No fresh J comparison, all-site optimality,
new information benefit or learned necessity follows. Model/native agreement does not grant
permission to replace unexecuted native outcomes with model values. The fixed study buys no
confirmation, unchanged replication, more worlds, repair, expanded option support or new fit.
The independent review adequately covers this unchanged claim; a second Pro result round
would duplicate its role without an identified distinct question.

Root has now assigned the original Astra Max Oracle and this existing DM **source-only next-
question discovery after B03 publication/cleanup**, including cheaper complete control,
potential learning objects, a different useful question or a justified stop. The critic's
preference for a costed approximation/amortization question remains an independent candidate,
not a resolved successor selection. The Oracle is also comparing a possible two-opportunity
anticipation question and a separate N5 learning branch; cross-question allocation and any
material direction disagreement return to Root. I will supply exact interfaces, hard gaps,
ordinary comparators and prospective total cost in this existing notebook, without new
result code, native/controller/model queries or fits. This is current authorized design
work with an actual Oracle producer, not idle waiting for invented approval. The B03 result
and its adverse evidence remain fixed while that next investment is considered.

<a id="b03-final-cleanup"></a>
### B03 publication and completed measured cleanup

Scientific reading, full original independent diagnosis, all compact native evidence, own
RESEARCH standing and the affected shared-background topic were published to main at
`0791f8a25460f6c841dc04ed779b63ccfb8a1090`. The substantively superseded prospective N8
index plan alone was retired under constitution section4 to
[2026-09-30 historical index material](../../archive/2026-09-30/RESEARCH.md), preserving its
published source and rebased evidence citations; the other current plans/controls were
preserved. No result code changed during reading, and no additional result was launched.

After publication, the maintained native snapshot collector previewed both exact terminal
sources as eligible, then rechecked and removed them under the serialized shared Git lock.
It verified terminal witnesses, absent processes, consistent claims, outputs outside the
snapshots, clean files and durable `main` reachability. Read-only privileged process scanning
had no reference or permission blocker. The critic and original Oracle explicitly released
their raw/snapshot consumers. Actual deleted targets are:

- `.git/hmasd-launch-sources/8341f5d7c61343a3bf8d0898931b925a` and its
  `.git/worktrees/8341f5d7c61343a3bf8d0898931b925a` registration (unexposed failed A01).
- `.git/hmasd-launch-sources/b70bade3003946de9ca9f65580ebc865` and its
  `.git/worktrees/b70bade3003946de9ca9f65580ebc865` registration (complete A02).
- `temp/directions/uav_fleet_transmission` (consumed/stopped observer scratch).
- `experiments/candidates/uav_fleet_transmission/__pycache__`.
- `experiments/candidates/uav_fleet_transmission/b02/__pycache__`.
- `experiments/candidates/uav_fleet_transmission/b03/__pycache__`.
- `tests/experiments/candidates/uav_fleet_transmission/b03/__pycache__`.

All nine filesystem targets and both Git worktree registrations are absent. Measured
allocated bytes across their union plus both B03 run directories and the canonical A02
store decreased from**3,478,691,840**to**48,267,264**, a **net3,430,424,576bytes reclaimed**.
This accounts for the raw relocation and necessary compact canonical copies; it does not
count moving raw data as savings. Remaining allocation is24,576bytes in A01,1,441,792in
the compact A02 run and46,800,896in canonical A02 evidence. All260required bulk hashes and
original run symlink identities were reverified after deletion. Useful code/tests, all
positive/adverse/failed evidence, operation claims and B01/B02 canonical evidence remain.
No cleanup target, tool blocker, active result producer, unread result or pending B03 review
remains. Root-authorized source-only next-design work is the next task, with no new
result-code/query/fit authorization.

<a id="post-b03-source-only-design"></a>
## 2026-09-30 — Source-only next-question construction after closed B03

Root assigned this continuing question work at19:28UTC to the same DM and original
independent Astra Max Oracle, `/root/deep_report_review`. B03 remains closed at scientific
publication `0791f8a25` and cleanup `a749fd6eb`. This entry records prospective source,
arithmetic and existing-evidence reasoning. It authorizes no new result implementation,
native/controller/model query, generated world, calibration or fit. Cross-question selection
remains Root's; a complete independent recommendation and DM disposition follow below.

### Consequential question and inherited constraints

B03 establishes useful selection among complete one-relocation programs. It leaves open
whether an early relocation can prepare a more valuable later relocation, beyond simply
allowing the same competent selector a second opportunity. This is an empirical-understanding
and ordinary-control capability question, not a learning-method claim. The contrasting
learning question is whether a cheaper learned continuation ranker can preserve complete
native value after paying for teacher data, fitting and inference. Neither is owed by B03.

I reread current published main `737a50333`, particularly RESEARCH topic3's B01/B02/B03
[fleet evidence](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构) and topic4's newly
published [two-lineage native-development losses](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)
from `711cc0f52`. Topic3 requires the matched ordinary two-opportunity comparator and full
native outcomes: a larger menu's model maximum is not empirical improvement. It also keeps
the N4 adverse, B02 startup/quality/path costs, B03 accurately predicted service loss and
unchanged service tails. Topic4 weakens the premise that a competent starting asset alone
justifies unrestricted reward continuation. Those N5 losses do not refute learning a new
N8 ranker; the information, representation and target differ. Conversely, N8's known-model
positive does not establish learned necessity. Root's separate N5 learning design retains
its own scope and is not duplicated here.

The original B03 ResearchCritic's complete response above favors a costed approximation/
amortization candidate, while explicitly calling its data and comparator contract unpriced.
The next independent review considers that recommendation alongside direct temporal planning,
exact ordinary reuse, a dynamic host, and a justified stop. No result validity dissent is
being silently cleared or turned into a mandate for a successor.

### Proposed complete comparison, still subject to Root selection

Keep N8/U50/c10/0dB, static users, free-space radio, H500 and the existing legal public
report, model and command-history rights. Consider16new common worlds and three complete
programs,48episodes/24,000native transitions, zero fits/updates, with cyclic arm order:

| Program | t40 decision | t120 decision |
| --- | --- | --- |
| T | Original B03 complete-continuation selection; at most one stationary champion per muted member plus C | Ordinary C continues |
| G2 | The same T choice, valuing each first option followed by C through499 | Recompute the same competent complete selector from the actual new lawful report/history, then C through499 |
| A2 | Rank the same first menu by its full continuation through a lawful T selection at120 and C thereafter | Recompute T from the actual new report/history, then C through499 |

G2 and A2 have identical two relocation opportunities, sites, commitment durations and
information rights. Primary A2−G2 asks whether anticipating the later opportunity changes
useful first choices; G2−T prices the added opportunity. A2−T alone would conflate those
questions. Nonpositive stationary first champions remain eligible. A2's decline comparator
is **C through119, then T at120 and C thereafter**, not C forever. Strict full-J improvement
over that comparator remains necessary to initiate the first option; deterministic service,
path/duration/member/site tie semantics must be explicit. First-option G2 is in A2's menu,
so modeled dominance over that finite G2 continuation is a construction property. It is
not a native improvement theorem.

At most8first candidates and8inner second candidates are priced. The latest first arrival
is80, leaving ordinary ticks81–119 before the120event:39ticks, not a promised full40ordinary
ticks or a settling guarantee. The choice of120is a fixed temporal separation, not a tuned
world-specific trigger. Every actual second decision is fresh, even if it differs from the
t40forecast. No timing sweep, early favorable-world stop or extra native counterfactual panel
is implied. Prospective world addresses29497000–29497015 and bootstrap seed29497991
(10,000paired draws) have no exact integer hits in a source-only text search of
`docs/research`, `experiments/candidates` and `runs`; no RNG or world was generated. These
remain provisional pending the complete fixed contract and Root's selection.

### Source feasibility and the nested-state distinction

This is feasible but not two calls to the frozen B03 object. Source inspection shows
`b03/option.py` embeds460remaining steps and40+L arrival; `b03/surrogate.py` requires a
controller at next_t40 and simulates from40; inherited `b02/controller.py` indexes committed
commands relative to40. A new direction-owned executor would parameterize start/remaining
horizon and relative command offsets while preserving frozen T. At120the expired first
plan is replaced; actual controller clock, issued commands and lawful state history survive.

For each t40first candidate, the outer model advances its physical coordinates and C history
through119. Its t120report must use the actual FP32 public codec. Inner T then starts from
that **decoded report**, with the lawful copied controller history, and selects its second
option. The outer model executes only that selected option from its own existing, unrounded
physical coordinates/history. It must not substitute inner decoded coordinates for its
physical state or expose hidden outer coordinates to inner scoring. Hence each first
candidate pays an outer post120suffix in addition to its inner candidate suffixes unless
exact identity reuse is separately established. Outer total-J/service/path accumulators
consume ticks in their original order; separately summed blocks cannot silently replace the
existing scalar accumulation. The full reader must verify this distinction and the actual
second replanning, not only the local maxima.

### Independently checked uncompressed cost

The following are source-derived conservative state/mask **request ceilings**, not measured
runtime or unique scored-candidate counts. All original menu/transit work is paid. Let
`B=1+7*100*128=89,601` be one original stationary bank. An ordinary full native episode
is bounded by`500*216+50*255=120,750`requests. Modeled reward adds one request per tick.

| Model component | Stay | Initiated option ceiling | Full8-candidate bank |
| --- | ---: | ---: | ---: |
| t40–499 |111,550|108,792|873,094|
| t120–499 |92,150|89,392|717,894|
| Outer t40–119 prefix |19,400|16,642|135,894|

The option ceiling uses the minimum10tick transit, its arrival query and the remaining
ordinary decisions; the full native bound deliberately does not subtract suppressed C work.

| Complete program | Requests/world |
| --- | ---: |
| T: `120750+B+128+873094` |1,083,573|
| G2: `120750+2*(B+128)+873094+717894` |1,891,196|
| A2: `120750+2*(B+128)+135894+8*(B+717894+92150)+717894` |8,351,156|

The16world total is**181,214,800requests**,**663,040physical-model transitions** and
**5,824,000original candidate-transit ticks**, plus the24,000native transitions and
native physics. Reader reconstruction pays additional work of comparable scope; native
physics, reports, serialization, imports/support and ordinary position-prediction work are
not erased by calling this zero-fit. Applying B03's combined worker/reader CPU per worker
request gives approximately**4.085CPU hours** for this ceiling, not a runtime guarantee.
Provisional implementation/checking is5–8hours plus2–3independent engineering-review hours,
**7–11labor hours**, unmetered estimates rather than a fitted timing model or a fit allowance.
Scientific reading/publication and support remain additional.

Existing B03 raw comprises22,315,248bytes of model arrays/traces for34,040ticks,
1,858,048bytes of5,800stationary candidate rows, and20,621,812bytes of native/other raw.
Scaling those components to this ceiling gives about502MB; scaling all44.8MB by the model
tick ratio gives873MB. Plan roughly**0.5–1.0GBcanonical raw**, with1–2GiBoutput/scratch
headroom plus one accepted source snapshot (about1.6GBin B03). These extrapolate existing
NPZ/gzip storage, without computational cycle reuse, and are not hard byte bounds. Stream
one outer prefix and one inner/selected outer suffix at a time, serializing completed
branches and retaining only summaries/plans/identities. With that explicit design, B03's
346.64MiBmeasured peak suggests roughly0.35–0.75GiBplanning peak and a1GiBadmission
allowance; actual implementation, fresh-node admission and measured RSS would decide.
Keeping the entire nested tree in RAM is outside this estimate. Worker and full reader
run sequentially. No fresh-node admission is needed for this source-only reasoning.

### Competing purchases and changed efficiency premise

The Oracle inspected all74**saved** B03 model traces, with no new controller/model/native
query. It reports exact full-state recurrence at period40after the last nonordinary event,
first witnessed at81–142, and matching saved actions/masks/positions/estimates/rewards in
every remaining repeat. Its avoidable-tail accounting is28,963/34,040model ticks and
7,006,621/7,916,026model requests. This is an existing-artifact reading, not an implemented
or measured speedup, and does not establish recurrence on a new second-option tail.

The source supports an exact-reuse route: key model physical positions, controller estimated
positions/users, previous issued commands, entering mask, phase modulo40and fixed user-report
bits/source. Use it only after a commitment ends and stop at the next scheduled selection;
t120is a barrier. Report time fields and next_t still advance. Per-tick scalar accumulation
order must be preserved rather than multiplying a cycle sum. Physical stationarity alone is
insufficient because issued commands and estimates remain state. A new reviewed certificate
could verify the preperiod and repeated full-state period, reconstructing logical trajectories
while separating logical from actually computed work. That engineering is estimated at an
additional4–7hours and is neither already done nor an obligatory precursor to the temporal
question. It is a substantive ordinary comparator for any later **efficiency** claim.

A learned ranker retaining the original champions still pays up to89,601online bank requests.
Lawful data may include the actual133FP32public-report values, entering mask, issued commands/
copied C history and original candidate descriptors; world IDs, hidden double coordinates
and future native labels are not inputs. Teacher labels are model predictions for complete
programs, not native counterfactuals. Acquisition alone costs at most972,355requests,
40native prefix transitions,3,680model transitions and28,000candidate-transit ticks/context.
At128contexts this is124,461,440requests/5,120native steps/471,040model steps/3,584,000transit
ticks, about2.806combined CPU hours at the same crude B03 rate, before learner fitting and
fresh complete evaluation. A source-only acquisition adaptation is estimated at4–7engineering/
review hours; architecture, fit count and evaluation cost remain unselected and unpriced.
This concrete bill and the exact-reuse alternative weaken learning-as-necessary-compression,
without empirically rejecting a learned ranker or requiring an ordinary-compression pilot.

The reused read-only Scout also mapped a different, already exercised host: native S7-S4
`energy_relay_availability` has N8/U30RPGM users at8m/s and clusters at10m/s, energy/failures,
30step replanning and pooled legal observations for H_local. I read its original B01
information contract and`configuration.py` directly. Hidden waypoints/velocities are not
granted by that local contract; mobility and faults share RNG, so equal seeds are not exact
counterfactual path replay. Original evidence is
`runs/energy_relay_availability/b01_s4_refs_a01/` and its direction notebook. S7-S2 is another
historical3m/s/H3000host with separate learned/adverse evidence. Both are closed/reserve
and historically owned, not permission to extend another direction. The existing
`uav_env.py`3gpp-36777sampler draws LOS/NLOS and optional4/8dBshadowing, with focused
cache/RNG tests; actual radio-policy studies used free-space. This bounded map establishes
neither a validated stochastic-radio actor contract, a calibrated learned transition model,
nor useful predictability from history. A dynamic/uncertain host would be a cross-question
proposal for Root and would need its own lawful information and complete comparator design.

<a id="b04-original-independent-recommendation"></a>
### Complete original independent Oracle recommendation

The following is the complete original final from `/root/deep_report_review`, received
through the native task tree. It preserves the allocation dissent rather than blending it
into the earlier result critic's different recommendation.

I recommend **one bounded T/G2/A2 study of anticipation across two relocation opportunities**, retaining B03’s T, R and C capabilities. Use the uncompressed evaluator for this first study: **48 fresh H500 episodes, 24,000 native steps, zero fits**, with an estimated **4.1 combined worker–reader CPU-hours and 7–11 engineering/check/review hours**.

The question is whether anticipating a later relocation changes the useful first relocation—not merely whether allowing another relocation improves performance. Exact tail reuse is feasible and now has strong saved-evidence support, but its additional engineering need not become a prerequisite. CAL/CONT’s separate selection does not determine this N8 investment.

This follow-up was conducted separately from the DM’s conversation, but was not blind: Root supplied result headlines, and I retain earlier advice. I reconstructed the new outputs before reading the DM’s interpretation, then read and reused the complete original B03 ResearchCritic. I made no controller, model, actor or native query, fit, implementation or launch.

**B03 establishes a useful finite capability, with clear limits.**

The source-bound [configuration](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b03_complete_continuation_a02/config.json), [summary](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b03_complete_continuation_a02/summary.json) and [reading](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b03_complete_continuation_a02/reading.json) support:

| Complete T−R contrast | Observation |
|---|---:|
| Mean J | +.007400167; descriptive interval [.001879057, .014256967] |
| Mean service | +.558625 users/tick; [.148197, 1.038134] |
| Mean path per UAV | +22.486 m; [3.144, 45.809] |
| Mean quality | −.001388; interval crosses zero |
| Changed physical programs | 9/16: nine positive J contrasts |
| Identical programs | 7/16 |
| Initiation decisions | Identical: 13 initiate, three decline |
| Service fifth percentile and minimum | Identical in every world |

The strongest positive is more than forecast improvement: continuation scoring changed executed choices and improved complete native outcomes. In world `29326002`, stationary scoring preferred R’s option, but complete scoring reversed the ranking; T subsequently gained .045294 J and 2.720 users/tick over R. Resumed C actually reduced R’s value relative to its stationary arrival forecast there. Thus “ordinary resumption adds value” is insufficient as a general explanation; its consequences depend on the selected program.

The adverse evidence is equally consequential. In world `29326011`, T gained only .000014853 J, lost .008 service and added 90.83 m/UAV. The model accurately predicted that tradeoff. World `29326012` gained service while losing .02687 quality and adding 145.64 m/UAV. Native J prices height, not travel energy.

All 48 executed C/R/T suffixes matched their model’s commands, masks and per-tick service; maximum remaining-total-J error was approximately \(1.92\times10^{-6}\). However, the 74 modeled branches contain **38 distinct executed programs and 36 unexecuted forecasts**. Those forecasts are not native counterfactual labels.

The measured study cost was 1,222.45 worker–reader CPU-seconds, 15,062,360 worker score requests and 44.8 MB of raw evidence. T’s measured episode CPU was 4.02 times R’s, including branch recording. A01 failed before result queries; its support costs remain incurred. Across B01–B03, the record contains 256 result episodes, 128,000 native steps and 6,243.41 measured worker–reader CPU-seconds, plus inherited and incompletely metered costs.

I agree with closing B03 and retaining its conditional capability. Neither unchanged replication nor automatic expansion follows from its positive result.

**A new saved-data finding changes the efficiency comparison.**

I inspected all 74 saved model trajectories and decision traces for exact recurrence after their last option event. The recurrence key included:

- Model-physical positions.
- C’s estimated positions and its static decoded users.
- Previously issued commands, including commands preserved by clipping.
- Entering transmission mask.
- The joint clock phase, \(t\bmod40\).
- Fixed public-user bits, source and completed-event conditions.

All 74 branches repeated at period 40, first certified between absolute ticks 81 and 142. I verified the remaining saved positions, estimates, actions, masks and rewards **bitwise**, including terminal physical and estimated positions.

The source explains why this matters. After option events finish, C uses time through its eight-member rotation and ten-tick report clock. It ignores the report’s time fraction. A repeated full state therefore permits exact reuse until a future scheduled event or the horizon.

On these existing traces, reuse could avoid:

| Saved logical work | Potentially avoidable after the first certified repeat |
|---|---:|
| Model-physical ticks | 28,963 / 34,040: **85.1%** |
| Model state/mask requests | 7,006,621 / 7,916,026: **88.5%** |

This would leave approximately 3.52 million T requests versus R’s 2.60 million, **not a measured runtime ratio**. Serialization, recurrence detection, reconstruction and other costs remain.

No optimized executable or new speed measurement exists. Recurrence on B03 does not guarantee recurrence equally early after newly coupled choices. Nevertheless, the ordinary alternative is now concrete. The measured 4.02× CPU premium cannot be treated as an irreducible economic argument for learning.

**The proposed scientific object is temporal complementarity between committed relocations.**

Suppose the fleet can schedule a relocation at t40 and another at t120. A first relocation may change which later relocation is useful through coverage, interference, assignment and the intervening C response.

Conceptually, the first-option comparison changes from

\[
Q_C(p)=\text{return through t119}+V_C(x_{120}^{p})
\]

to

\[
Q_T(p)=\text{return through t119}+V_{\text{T at120, then C}}(x_{120}^{p}).
\]

If the second opportunity contributes essentially the same increment across first options, ordinary greedy replanning should suffice. If that increment varies enough to reverse their ordering, anticipation can matter.

This is a familiar rollout construction, not a new planning theorem. Multiagent rollout and POMDP rollout provide the relevant bridge: evaluate current choices using a specified future policy, and distinguish exact-model improvement arguments from finite approximation. [Bertsekas](https://arxiv.org/html/1910.00120v3), [Bhattacharya et al.](https://arxiv.org/html/2011.04222).

The local sources reinforce its limits:

- Foundation **B03**, §8.2, treats macro behavior, termination and elapsed primitive rewards; it does not guarantee this UAV construction. I used its [catalog identity](/home/fires/hmasd-wsl/docs/new-libs/corpus/papers/B03/metadata.json) and the [author’s primary PDF](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf).
- **MARL-0016**, *Models as Agents*, connects model error and changed policies; its assumptions do not establish accuracy for these nested continuations. [Primary JSON](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json), [PDF](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0016.pdf).
- My-lib’s **iclr-2024-d74e6bfe9ce029526e69db14d2c281ec**, *Efficient Multi-agent Reinforcement Learning by Planning*, supplies a planning-and-learning antecedent, while explicitly confronting model generalization with depth. It supplies no reason to replace an adequate analytic model here. [Primary PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2024/d74e6bfe9ce029526e69db14d2c281ec/arxiv-2405.11778.pdf).

I checked all three library indexes and the relevant primary passages. The [July opportunity-contract review](/home/fires/hmasd-wsl/docs/external-review/rounds/20260720_supplied_executor_opportunity_contract/21_PRO_OPEN_RAW.md) also cautions against treating a restricted myopic frontier as an opportunity bound. The [G48 result](/home/fires/hmasd-wsl/docs/research/cdc/EVIDENCE_NOTES/20260729_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_FORMAL_RESULT.md) concerns its finite credit intervention, not a general rejection of temporal control. None establishes novelty or predicts a positive A2 result.

**The complete comparison should be:**

| Program | First decision at t40 | Second decision at t120 |
|---|---|---|
| **T** | Existing complete-continuation selector | Continue C |
| **G2** | Same choice as T, valuing continuation under C | Recompute the complete selector from the actual lawful report/history |
| **A2** | Value each first option under its resulting t120 selector and subsequent C | Recompute that same selector from the actual lawful report/history |

The primary contrast is **A2−G2**. Secondary contrasts are **G2−T** and **A2−T**. G2 receives the same additional opportunity as A2, separating its benefit from anticipation.

Freeze these details prospectively:

- Preserve N8/U50, H500, the existing radio/objective law, public reports every ten ticks, primitive commands, site construction and arrival-mask rule.
- At each decision retain C/stay and one stationary champion per currently muted member. At t120, stationary valuation uses the remaining **380** ticks. Retain nonpositive stationary champions.
- Commitments retain durations 10/20/30/40, hold other members’ commands at zero during transit, preserve the entering mask, perform the existing arrival choice and then resume C.
- A2’s **stay-first comparator includes T at120**. It is not C forever.
- Rank by complete modeled remaining J, service, then the existing first-option path/duration/member/site order. Require strict J improvement over stay-first; equal J declines.
- The latest first arrival is t80, leaving ordinary ticks **81–119** before the second opportunity. This is 39 ticks, with no settling assumption.
- Use 16 fresh paired worlds and cyclic T/G2/A2 execution order. Proposed addresses are `29497000–29497015`, with 10,000 paired bootstrap draws using `29497991`. Both repository checks found no exact existing integer use; no worlds or RNG values were drawn.

The numerical distinction inside A2 matters. At modeled t120, the inner selector receives the newly encoded FP32 report and begins its own search from decoded coordinates. After it chooses an option, **only that option** returns to the outer simulation. The outer simulation continues from its existing physical coordinates and controller history. It must not reset its physical state to the inner model’s coordinates or give those unrounded coordinates to the inner selector.

At actual t120, both G2 and A2 replan from their actual reports. Predicted and actual second choices may differ. Accumulate outer rewards in original tick order; do not add separately summarized prefix and suffix blocks.

G2’s first choice is present in A2’s menu. Consequently, modeled A2≥modeled G2 is a construction property under the specified evaluator. **Fresh complete native benefit remains the empirical question.**

**The exposure and reading must preserve that distinction.**

Record both opportunities, entering masks, eligibility, complete stationary candidate rows and physical aliases, retained champions, modeled rankings, strict-decline decisions, commitments and executed masks/commands. For A2, retain each first option’s predicted second selection and the actual second selection.

Read changed **first physical programs**, not merely different identifiers. G2 and T must agree through t119; all programs share the initial t0–39 history. Model errors should be checked against executed continuations, while unexecuted alternatives remain forecasts.

The endpoint is complete H500 native J over all 16 worlds. Read service, quality, service fifth percentile/minimum, zero-service behavior, travel and computation alongside it. The common startup remains charged; subsequent interventions can still worsen service tails.

| Outcome | Consequence |
|---|---|
| A2 improves over both G2 and T, with changed first choices and acceptable secondary costs | Retain conditional evidence for useful anticipation; no optimality, learning or automatic confirmation claim |
| G2 improves over T, while A2 adds little | Retain the cheaper two-opportunity program; decline deeper anticipation without a new reason |
| A2 beats G2 but does not improve T | Preserve the anticipation contrast, but do not adopt it as a mission upgrade |
| Choices mostly coincide | Record sparse exposure; neither opportunity exhaustion nor an automatic larger panel follows |
| Active A2 changes are adverse | Retain the supported reference and stop this finite package; no repair is owed |
| Technical invalidity | Preserve failure and cost; make no scientific negative claim |

Intervals remain descriptive conditional world intervals. No training replication is purchased because there are no fits.

**The full uncompressed bill is bounded at the request level, with runtime and engineering estimates kept separate.**

The DM independently checked the source arithmetic:

| Work | Prospective amount |
|---|---:|
| Complete native evaluation | **48 episodes / 24,000 steps** |
| Fits / parameter updates | **0 / 0** |
| T worker requests, all worlds | ≤17,337,168 |
| G2 worker requests, all worlds | ≤30,259,136 |
| A2 worker requests, all worlds | ≤133,618,496 |
| **Total worker state/mask requests** | **≤181,214,800** |
| Complete-model physical ticks | ≤663,040 |
| Separate stationary-candidate transit ticks | ≤5,824,000 |
| Stationary candidate rows | ≤145,600 |
| Worker plus full-reader CPU | **Approximately 4.085 hours** |
| Implementation, checks and independent review | **Approximately 7–11 hours** |
| Canonical raw evidence | Approximately 0.5–1.0 GB |
| Peak process RSS, assuming streamed branches | Approximately 0.35–0.75 GiB |

The CPU estimate extrapolates B03’s combined rate; it is not a runtime guarantee. Native physics, reconstruction, imports, storage and support remain charged. The reader separately reconstructs the complete branches and native outputs; its work is included in the CPU estimate, not hidden as free verification.

Storage estimates use B03’s measured model, candidate and native-record sizes. Allow 1–2 GiB for output/scratch plus one accepted source snapshot. Stream nested branches; retaining the whole tree in RAM falls outside the estimate. Actual node admission remains required.

The main implementation gap is real but bounded: frozen B03 embeds t40, 460 remaining ticks and `commands[t−40]`. A new owned executor must parameterize decision start, remaining horizon and plan-relative indexing while preserving T’s meaning. Both new programs must replace their expired first commitment before t120. No hard host-interface blocker was found.

Exact tail reuse could be incorporated prospectively into all three programs without changing their choices, provided it:

- Certifies the complete recurring state.
- Stops at scheduled selections and unfinished commitment/arrival barriers.
- Advances the absolute clock and regenerates report time fields.
- Preserves per-tick floating accumulation and tie semantics.
- Separately reports logical work, actually computed work and reuse.
- Preserves a complete, independently checked reader.

The DM estimates **another 4–7 engineering/review hours** for reuse and its certificate. For this single study, I do not recommend making that additional investment compulsory. The temporal question must justify its uncompressed bill. Reuse becomes a stronger practical purchase if subsequent repeated use warrants it.

**I considered the original critic’s approximation preference as a real alternative.**

Its strongest cheap version need not acquire 128 new teacher contexts. It could reuse the already-paid 74 model labels across **16 worlds**, fit a small residual predictor or ranker, and evaluate fresh R/T/learned trajectories. Those are 16 independent contexts, not 74 native labels.

For scale, a fresh 16-world R/T/one-candidate panel has a worker ceiling of **24,072,496 requests**, approximately **0.54 combined CPU-hours before fitting and support**. That is substantially cheaper than the temporal study. Learner features, fitting, optimization and their engineering cost remain unselected; this is not a launch-ready protocol.

If fresh acquisition were chosen, 128 C prefixes plus exact T labels would instead cost 5,120 native prefix steps, up to 124,461,440 requests and approximately 2.806 combined CPU-hours before final evaluation and fitting. That is an optional design choice, **not a minimum-data gate**. A champion ranker also continues paying up to 89,601 requests to construct its original menu at deployment.

Learning could still use experience to avoid computation on previously unseen transient states. Exact recurrence does not eliminate that possibility. But its efficiency reference must account for competent exact reuse; an additional identical native arm is unnecessary merely to compare implementation costs.

My preference for T/G2/A2 is therefore a choice of scientific object, not a claim that learning is too expensive or requires a deadline. B03 demonstrated that the value of future control can reverse present choices. The proposed study asks whether **the future decision opportunity itself** changes the correct first choice, with a matched ordinary comparator. Compressing the already-demonstrated single-opportunity decision is useful chiefly as an efficiency question whose ordinary cost reference has now improved substantially.

My direct checks covered the source bindings, compact contrasts, consequential positive/adverse model-versus-native evidence, selector/executor semantics and all 74 saved recurrence traces. I reused the original critic’s broader artifact, candidate and bootstrap reconstruction. I did not rerun physics, scores or training, and no prospective performance, timing or recurrence on the new tails has been measured.

**MATERIAL_DISSENT: yes — on the next N8 investment only.** I recommend the costed temporal-complementarity study over the original result critic’s conditional priority for approximation/amortization. The direct reasons are B03’s demonstrated decision reversals, the matched G2 comparison and the newly established ordinary exact-reuse opportunity. There is no dissent on B03 validity, closure or retention. Root should preserve and resolve this allocation difference; this recommendation does not authorize a run.

<a id="b04-temporal-design"></a>
### DM response, Root resolution and fixed B04 contract

I read the whole original recommendation and retain both advisers' allocation preferences.
I accept the temporal question's distinct knowledge purchase: whether making a later
decision part of the first option's value improves the actual first commitment under the
same two opportunities. The ordinary G2 comparison and full H500 outcomes are essential.
I do not infer a learning impossibility, an exhausted one-opportunity task or native
dominance from finite model maximization. My earlier128context acquisition price is only
one possible learning bill; it is not a minimum-data or deadline prerequisite. The cheaper
reuse of74paid model labels/16contexts remains a legitimate unselected alternative.

I independently read Bertsekas(1910.00120v3)§1.1/§2 and Bhattacharya et al.(2011.04222)§3–5
at their primary links above. They support the conceptual use of a specified base policy's
future return and acknowledge approximate rollout/policy approximation. Their state/belief,
evaluation and improvement assumptions are not automatically satisfied by nested rounded
reports and native execution here. This study is neither their improvement theorem nor a
new rollout-method claim. The Oracle's three-library and July readings remain attributed
to that independent review; no novelty verdict or new literature-driven admission gate is
introduced.

Root explicitly resolved the material allocation dissent in favor of **this one uncompressed
T/G2/A2 study**, preserving the original critic's approximation preference and the cheap
label-reuse alternative. Its accepted scope is48H500episodes/24,000native steps/0fits,
the181,214,800worker-request and663,040model-tick ceilings, approximately4.085combined
CPU hours and7–11implementation/check/review hours. Root excludes the optional4–7hour
cycle-reuse implementation. This selects B04 within the existing question; it does not
reopen B03 or authorize another result batch, fit, sweep, favorable-world stop or retry.
The independent scientific review and Root's explicit resolution cover this selection.
Another Pro or scientific selection round would add no identified distinct question.

Freeze the Oracle's complete comparison and readings above with first decision40, second120,
H500,16worlds29497000–29497015, and10,000paired bootstrap resamples using29497991.
World generation uses a distinct fixed SeedSequence namespace`[260930,97,world_id,stream,*suffix]`,
with user/UAV/runtime streams1/2/3and runtime suffix8, retaining the existing uniform
N8/U50initial-array construction. Committed initial arrays and hashes will bind the exact
panel before result execution; they are generated once without controller evaluation or
world selection. Arms cycle T/G2/A2 by world index. No additional holdout/confirmation is
selected. Primary is complete meanJ(A2−G2), with G2−T and A2−T secondary and all16paired
worlds retained. Report every native reward component, servicep05/minimum/zero-service
behavior and path/UAV, actual physical first/second choices, predictions, model/native errors,
candidate/query/transition work, CPU/wall/RSS and all adverse worlds. Descriptive intervals
do not become adoption thresholds. The prospective prediction is a changed first physical
commitment on at least one world and positive complete meanJ(A2−G2); each component can fail.
All fixed outcomes, including no changed choices, run to the same complete endpoint.

Rank each complete model candidate by total remaining J, total served, then the original
**first option's** stationary path, duration, member and site with their existing negative
tie keys; decline on J equality with the complete stay-first program even if service differs.
The second selector applies the original T convention to its own current menu and380tick
remaining horizon. No all-site complete search, altered candidate shortlist, new physical
information, cycle compression or learned model is included. Maintain original FP32 report
bits and issued commands, float64 model positions/reward reductions, scalar tick-order
accumulation and frozen native physics. A2 forecasts an actual lawful future selector and
then executes only its chosen option in the outer physical model; both native arms replan
at their actual120report regardless of the forecast.

Root preserves the accepted real-deadline resource windows. Its later explicit resource
message reports parent B05 worker plus full reader terminal/VERIFIED at20:06:39.448902UTC
with native processes absent, releasing configured local_linux; waiting still owns the
remote window. B04 may use local after source publication/review and fresh actual admission,
sharing with untimed single-thread CAL/CONT if actual resources allow. Prefer configured
remote if both windows are free and suitable at admission. This is a node-selection
constraint, not permission to disturb either accepted process or migrate a launch.

### L0 — bounded B04 implementation, checks, acceptance and stop

Deliver the selected fixed two-opportunity program and full worker/reader chain under
`experiments/candidates/uav_fleet_transmission/b04/`, with matching tests under
`tests/experiments/candidates/uav_fleet_transmission/b04/` and fixed run outputs under
`runs/uav_fleet_transmission/b04_temporal_complementarity_a01/`. Preserve all B01–B03
executables, sources, claims and evidence. Reuse frozen ordinary control/radio/physics,
public codec, candidate primitives and artifact conventions; only the parameterized
decision-time executor, nested selection, fixed host binding and complete new reading are
new. The runner entry is `python -m experiments.candidates.uav_fleet_transmission.b04.run`;
its standard source/seed/out arguments reject changes to this declared panel. It requires
runner-side admission before scientific effects, runs one worker then its full reader,
and preserves partial artifacts on failure. Use one CPU thread, no new learner or native
backend, and no result profiling/pilot/world screening.

The bounded Implementer task is the scientific state machine: new`option.py`,
`surrogate.py`and`controller.py`plus focused`test_temporal.py`under the B04paths. The DM
owns host/world bindings, runner, storage, reader, other tests and all records. The helper
has no Git index/commit/publication authority, no result launch, no notebook writes and
no children. Both write the existing shared main with disjoint paths; preserve all other
sessions' edits. Final acceptance remains the DM's after diff/check reading and independent
engineering review of the complete high-risk executable change.

Checks cover unchanged T, complete T/G2prefix through119, the scheduled40/120clocks,
expired-plan replacement, nonpositive champions, strict stay-first ties, empty eligible
sets, candidate/physical aliases, FP32 report versus outer-physical state separation, fresh
actual120replanning, all stage/branch identities and scalar accumulation. Synthetic small
fixtures and test doubles may check branch arithmetic without policy-quality evidence.
Separately declared real correctness exposure is capped at256constructed native transitions
and corresponding shortened ordinary/model checks; no prospective result worlds or complete
result-policy episode may be used as a prelaunch test. Account actual correctness work.
Reader tests must reject dropped/reordered/tampered inner/outer branches, candidates,
source bindings and native outputs. The complete result reader recomputes every charged
model branch and all native physics/observations/actions from saved inputs; unexecuted
branches remain forecasts. Preserve the original T reference independently in its arm and
verify G2first semantics against its same-world native prefix, without adding an undeclared
full shadow-result panel.

Stop and return a material source contradiction, impossible law/cost contract or unresolved
scientific objection to Root. Ordinary implementation defects are corrected within this
scope and receive relevant checks/review; no extra result exposure follows automatically.
Commit/publish exact inputs before fresh-node admission. After one accepted worker/reader
operation, arm deterministic same-handle observation and keep this native DM active through
collection, complete reading, independent result criticism, publication and measured cleanup.


<a id="b04-engineering-acceptance"></a>
### B04 implementation accepted; prelaunch checks — 2026-09-30 20:40 UTC

The bounded Implementer returned the four assigned files without scope deviation or Git
mutation. I read the complete controller/model changes and accept them with the new fixed
host, streamed evidence collector, admission entry and complete reader. T and the first
G2 choice delegate to the unchanged B03 implementation; all frozen B02/B03 dependencies
remain byte-identical to their accepted source. The new executor only parameterizes the
scheduled commitment clock. A2 stores every inner branch and the complete outer trajectory
once, retaining the physical/report separation and sequential tick reductions. The actual
second selection replaces the expired first plan even on decline. The single worker calls
its full reader after all48native episodes; failures preserve completed cells and live-cell
native prefixes/model artifacts, with no implicit resume or repeat.

Focused checks completed with the configured local scientific interpreter:

- Final temporal semantics:10passed in0.46s; final concatenation-copy refinement:1targeted
  pass in0.15s. The independent engineering reviewer also ran the final10checks. These
  include original T/G2 prefix delegation, t120pricing/nonpositive champions, strict J ties,
  empty eligible sets, physical aliases, nested stay-first reversal, fresh actual replanning,
  expired/malformed-plan refusal, hostile sink mutations and nonassociative scalar sums.
- Collector/reader/admission tests:7passed in2.28s. After expanding corruption coverage,
  the two integration checks passed in2.78s. The scripted formula-only fixture exercises
  actual collection/serialization and full episode reconstruction; missing/reordered branches
  and banks, rehashed branch/candidate/native corruption and partial-cell loss are rejected.
  It does not instantiate or transition a native environment or call the result planner.
- Constructed native t120correspondence:2passed in1.98s, exactly**26native transitions**
  total. Decline and a10tick commitment both match commands, masks, physical coordinates,
  all native reward components and H500-encoded reports through t132, including arrival and
  ordinary resumption. The remaining230transitions of the correctness cap are unused.
- CLI help and owned-file whitespace checks passed. No fit, optimizer update, scientific
  result world or full real policy episode was used for prelaunch checking. The pure
  temporal suite contains a three-tick constructed real model segment and three direct score
  checks per invocation; its1000candidate transit propagations use mocked radio. Repeated
  unit/review/import/support CPU is incurred but not formally metered.

Original engineering-review conclusion (`/root/dm_fleet_transmission/engineering_review`):

> No material finding remains in the stable B04 implementation; no repairs requested.
>
> Reviewed the full controller→model→collector→reader path. It preserves frozen T/G2 behavior through t119, prices the second menu over 380 ticks, separates decoded inner reports from outer physical state, replans at actual t120, declines equal-J choices, and counts each candidate bank once. Final plan validation and copying changes preserve those semantics.
>
> Checks:
>
> - Independently ran final temporal tests: **10 passed**.
> - Reviewed and reused DM evidence for **7 collector/reader checks**, including tampering and partial-failure preservation.
> - Reviewed the native correspondence tests and DM’s **2 passes / 26 constructed native transitions**; I performed no native transitions.
>
> Residual limit: no complete real T/G2/A2 H500 worker-reader panel was executed during review. Synthetic integration covers storage/reconstruction; bounded native checks cover t120 commitment, arrival, and resumption.
>
> No edits, Git mutations, launches, or additional result queries performed.

I accept that scoped engineering conclusion. The first complete scientific panel remains
this one selected result operation, with unchanged48H500/0fit exposure and all prospective
ceilings. No implementation check is counted as evidence for useful anticipation.

At20:40:21UTC the actual configured remote node still has the accepted user-waiting full
reader running; it retains its deadline window. Local_linux has the accepted untimed,
single-thread fleet CAL/CONT worker plus its observer. Root explicitly permits sharing that
released local window when fresh resources allow. Select local_linux for B04, with one CPU
thread and a separate admitted snapshot, subject to the launcher's fresh actual memory and
published pause/lead checks. Do not disturb, migrate or duplicate either accepted process.
The standing/routing rows are updated to this already-selected B04 contract; source publication
and successful admission, not this prospective note, establish the actual operation handle.


<a id="b04-accepted-operation"></a>
### B04 A01 accepted and observation adopted — 2026-09-30 20:44 UTC

Published exact source/tests, engineering acceptance and selected standing/routing in
`239360b03f5d7acf788bd9ae5d4dccbde4f9237e`. The single fixed worker/full-reader chain is
accepted on local_linux; its native identities, command, immutable snapshot and output
binding are in the [original launch manifest](../../../../runs/uav_fleet_transmission/b04_temporal_complementarity_a01/launch-manifest.json).
The [fresh actual-node preflight](../../../../runs/uav_fleet_transmission/b04_temporal_complementarity_a01/admission-preflight.json)
passed the4GiB physical/effective floor with6,734,266,368bytes available. The remote waiting
reader was still running when placement was checked. Root's subsequent placement refinement
explicitly keeps this B04 on suitable local capacity beside the untimed CAL/CONT work,
reserving remote for waiting's accepted reader and newly selected real-deadline successor.
No accepted process was displaced or changed.

The ordinary observer `arm` first refused because this same session's default state remained
stopped after B01/B02. `drain` exposed generation7, no pending events/wake and both old jobs
already ready; supported `rearm --generation7` advanced to8 without resuming an old worker
or probe. Adding the new exact B04 status request advanced to**generation9**. Its first
observed facts at20:44:15UTC show accepted admission, matching live runner/supervisor
identities and consistent records. Observation is adopted under job`launch-b04-temporal-a01`
in the session's existing default observer directory; task-local request is
`temp/directions/uav_fleet_transmission/b04/observer-request.json`. The25minute checkpoints
will drain/rearm this same operation. The initial observer refusal did not alter or repeat
the scientific launch. Native-child queue delivery is not presumed to work; this DM keeps
its turn active through complete collection and reading. No new result conclusion yet.

B04 observation checkpoint21:09UTC: generation9 CHECKPOINT `9b2962f1d11c25b5ccb0d4fe` / wake `ba6a9a48-2857-4996-bf74-754e0efaa361` was drained and consumed by supported rearm to10 against the same accepted operation. Native App queue returned explicit multi-agent-v2 rejection(-32600); the active DM read it through the deterministic observer-state wait. Latest native observation remains running/consistent, with23/48completed episodes,11,500recorded native steps,38,241,116recorded worker requests and1549.862672548completed-cell CPU seconds. stderr is empty; full reader remains pending. No score interpretation, source change, replay or added exposure.

B04 observation checkpoint21:34UTC: generation10 CHECKPOINT `03d91bd4a38c5d1fd628865a` / wake `1f712c1c-8dca-4c8c-8e03-dc0986286511` was drained and consumed by supported same-operation rearm to11. Queue again explicitly rejects native-child delivery(-32600); active deterministic waiting remains effective. Native identities are running/consistent,47/48episodes and23,500steps recorded,74,859,533worker requests and2970.952721717completed-cell CPU seconds. stderr remains empty; worker is finishing its fixed final cell and full reader is pending. No quality interpretation or change to exposure/inputs.

B04 observation checkpoint21:59UTC: generation11 CHECKPOINT `f02e8c2ad4ac6d3d2b4e583c` / wake `19f69cdd-991c-4d4c-812f-ddc8913bfad2` drained and consumed by same-operation rearm to12. Queue delivery again has the known explicit native-child rejection; active deterministic observation continues. Worker is complete at48episodes/24,000steps,78,066,287worker requests,3094.712765347CPU /3095.437050657wall seconds; peakRSS351,524KiB at worker boundary. Full reader has verified23/48episodes, native identities remain running/consistent and stderr is empty. This is technical collection, not a completed scientific reading. The original dedicated ResearchCritic now reconstructs the immutable saved worker evidence in parallel with remaining reader work, without new physics/control/model calls; current findings remain provisional until complete verification. No result or added investment is selected by this checkpoint.

B04 observation checkpoint 22:25 UTC: generation12 CHECKPOINT `b0e1297798d2ccf3479bf41c` / wake `fd0dd0bd-60cd-4343-ac23-b0b7e7faff58` was drained and consumed by same-operation rearm to13. Native identities remain running/consistent; full reader has verified47/48episodes and stderr remains empty. Native-child queue delivery again returned the known explicit rejection(-32600), handled by active deterministic waiting. Independent critic has completed all saved-data/source consumption and waits only for terminal reader identity and costs before final disposition. Root also assigned the existing Oracle a source-only successor allocation; no follow-on result execution or new queries are selected.

<a id="b04-complete-reading"></a>
### B04 complete reading: useful anticipation under matched opportunities, with material costs — 2026-09-30

**Disposition:** retain the conditional T/G2/A2 capabilities and close the fixed B04 study.
The primary anticipation comparison is positive and its predicted physical first-choice
reversals occur. It does not establish learning advantage, optimal relocation timing, overall
cost dominance or a default deployment choice. The complete original independent result
review and my response are preserved below; there is no material dissent on this disposition.

The single accepted source is `239360b03f5d7acf788bd9ae5d4dccbde4f9237e`. Its worker and
full reader completed 48 H500 episodes / 24,000 native steps / zero fits or updates on the
16 prospective worlds `29497000–29497015`. The native process exited successfully at
**22:27:05.153298 UTC**; the observed terminal facts at22:27:07.739815 show both runner and
supervisor absent, exit0 and consistent records. Generation13 READY
`5663f8e4f56ead1a366332e6` / wake `0c75df7d-5602-40f5-92e9-08b9f6fb64fb` was drained,
consumed by same-handle rearm to14, and observation explicitly stopped. Final state has no
wake or pending event. No launch, native episode or model query was repeated to recover the
unsupported native-child App queue delivery.

The [original summary](../../../../runs/uav_fleet_transmission/b04_temporal_complementarity_a01/summary.json)
SHA is `8bdf64a6bafd75864c10df6a2c5992fb668c393ce271b02adccd472fe4226aa2`.
The [compact complete reading](../../../../runs/uav_fleet_transmission/b04_temporal_complementarity_a01/reading-summary.json)
contains all 36 paired contrasts, all16world readings, all80 selected forecast comparisons,
cost ledgers and the saved native window witnesses. The unchanged full reading is
3,989,184bytes with SHA `c9eaac15e69d1195e73710e4b071b5c196402bc6811b3a0bac333c771fd39363`;
its larger nested-plan/alias detail is retained with the canonical raw rather than added to
Git. [Native terminal facts](../../../../runs/uav_fleet_transmission/b04_temporal_complementarity_a01/native-status.json)
and [process exit](../../../../runs/uav_fleet_transmission/b04_temporal_complementarity_a01/process-exit.json)
bind the completed operation. Configuration SHA remains
`3651cf713225bcd148297b7434b70270d35c592ecdfb9ca2240d1eb667a29c54`.

T makes one t40 relocation selection. G2 makes that same first selection and a fresh actual
t120 selection. A2 evaluates its t40 alternatives through a modeled t120 selector, then also
replans at actual t120. Its stay-first comparator includes the later selection. Consequently
A2−G2 tests anticipation under the same two opportunities; G2−T prices the additional
opportunity. All three share the complete native0–39prefix, and T/G2 share0–119 exactly.

| Complete native mean | T | G2 | A2 |
| --- | ---: | ---: | ---: |
| J | .658213347084 | .660257386639 | .661963463474 |
| Served users/tick |42.545500|42.725750|42.969625|
| Quality |.208918844430|.207330017946|.201678294898|
| Height penalty |.000099306245|.000102118745|.000114774995|
| Path, m/UAV |473.338235|558.918200|601.864789|
| Service fifth percentile |38.5625|38.5625|38.5625|
| Minimum service |32.8125|32.8125|32.8125|
| Zero-service steps |0|0|0|

| Paired contrast | Mean J [95% world-bootstrap interval] | Mean service [interval] | Mean path, m/UAV [interval] |
| --- | --- | --- | --- |
| **A2−G2** | **+.001706076836 [.000277842988,.003935420760]** | **+.243875 [.022625,.543378125]** |+42.946589 [−10.635655,130.320720]|
| G2−T |+.002044039555 [.000106455994,.004580958189]|+.180250 [−.000375,.408500]|+85.579965 [39.226349,145.208953]|
| A2−T |+.003750116391 [.001346704560,.006675754055]|+.424125 [.156750,.746262500]|+128.526554 [46.194194,232.397600]|

These are the fixed10,000-replicate percentile intervals, seed29497991, over16fresh worlds
for deterministic programs. They are descriptive world uncertainty, not learning replication.
A2−G2 has6positive /10zero /0negative J differences, and5positive /10zero /1negative service
differences. G2−T has12positive /4zero J differences; A2−T has14positive /2zero. Every
individual world's service fifth percentile and minimum are unchanged. These aggregate
service tails do not measure individual-user continuity.

The six changed A2 first choices are actual physical commitments, not merely different site
labels; the other ten complete A2/G2 native arrays are byte-for-byte equal. In all six changed
worlds, the selected A2 first option has a lower complete C-only modeled return than G2's
first option, but a higher return with the subsequent selector. Actual cumulative J before
t120 is also lower in all six and the later gain exceeds it. The earlier explanation that the
second opportunity adds approximately the same value regardless of the first choice is
weakened. The supported explanation is that anticipating later control can change the useful
present commitment. Full modeled/native correspondence supports this reading without
turning it into a general policy-improvement theorem.

| World | G2 first → second | A2 first → second | ΔJ | Δservice | Δpath m/UAV |
| --- | --- | --- | ---: | ---: | ---: |
| 29497000 | m7_s83@60 → m0_s9@140 | m7_s83@60 → m0_s9@140 | +0.000000000 | +0.000 | +0.000000 |
| 29497001 | m0_s60@60 → stay | m0_s60@60 → stay | +0.000000000 | +0.000 | +0.000000 |
| 29497002 | m6_s54@70 → stay | m6_s54@70 → stay | +0.000000000 | +0.000 | +0.000000 |
| 29497003 | m1_s29@50 → m3_s15@150 | m1_s29@50 → m3_s15@150 | +0.000000000 | +0.000 | +0.000000 |
| 29497004 | m1_s22@60 → m6_s43@130 | m2_s21@60 → m1_s54@130 | +0.000884368 | +0.002 | -25.073593 |
| 29497005 | m4_s55@70 → m0_s77@150 | m4_s55@70 → m0_s77@150 | +0.000000000 | +0.000 | +0.000000 |
| 29497006 | m2_s18@50 → m1_s38@140 | m2_s18@50 → m1_s38@140 | +0.000000000 | +0.000 | +0.000000 |
| 29497007 | stay → m2_s7@150 | m1_s2@60 → m0_s74@140 | +0.000491523 | +0.726 | +613.328109 |
| 29497008 | m5_s85@70 → m6_s85@130 | m5_s85@70 → m6_s85@130 | +0.000000000 | +0.000 | +0.000000 |
| 29497009 | m6_s23@50 → m1_s23@130 | m6_s23@50 → m1_s23@130 | +0.000000000 | +0.000 | +0.000000 |
| 29497010 | m7_s66@60 → m6_s71@130 | m4_s66@70 → m6_s37@140 | +0.004637319 | +0.356 | -87.432689 |
| 29497011 | m4_s56@60 → stay | m6_s58@60 → m7_s68@150 | +0.003007085 | +0.736 | -10.716991 |
| 29497012 | m5_s19@50 → m2_s9@140 | m7_s7@70 → m2_s37@150 | +0.016091706 | +2.086 | +135.110390 |
| 29497013 | m5_s60@60 → m1_s51@150 | m5_s60@60 → m1_s51@150 | +0.000000000 | +0.000 | +0.000000 |
| 29497014 | m6_s40@70 → stay | m1_s26@70 → m1_s26@130 | +0.002185229 | -0.004 | +61.930195 |
| 29497015 | m4_s47@70 → m1_s19@140 | m4_s47@70 → m1_s19@140 | +0.000000000 | +0.000 | +0.000000 |

Here `mXsY@Z` identifies the member, stationary site and actual arrival tick, with zero-based
member/site indices. No actual selected second commitment has zero physical path. Initiation
counts are T15; G2 first15 / second12; A2 first16 / second14. More initiations alone do not
explain the primary contrast because the selected first paths and downstream control differ.

The useful and adverse witnesses sharpen the result:

- **29497012:** A2 selects first member7/site7, whose original stationary gain over stay is
  **−.0428320218072 cumulative J**, and whose complete C-only gain over stay is
  **−.000909885235**. With the subsequent selector it exceeds G2's first-program value by
  **8.0458531365 cumulative modeled J**, and exceeds the full stay-first/later-selector
  branch by **8.0641530644**. This is not merely avoiding a poor first choice by waiting.
  Native J before120 falls .0095832102, while service is unchanged; afterward service gains
  1,043user-ticks, producing +2.086users/tick overall. The selected first member activates at70,
  remutes at80, briefly reactivates at150–159 and remutes again. It is active only20ticks after
  the first arrival. The second relocation is member2/site37 with arrival150. The complete
  +.016091706J gain supplies about59% of the aggregate J difference, alongside quality
  −.043682647 and135.110390m/UAV extra travel.
- **29497014:** A2 selects member1/site26 first despite stationary gain−.5912585415 and
  complete C-only gain−.00151501448 versus stay. That member activates at70, remutes at80,
  and is selected again at120 with arrival130; the repeated site identifier still denotes
  a nonzero second movement. Native J rises .002185229, but two user-ticks are lost
  (−.004users/tick), and travel rises61.930195m/UAV. The model predicts this objective tradeoff.
- **29497010:** the alternative first commitment loses128user-ticks before120 and another34
  at120–159, then gains340 at160–499. The complete result is +.004637319J /+.356users/tick
  with87.432689m/UAV less travel. An unchanged full-episode minimum or percentile does not
  erase that initial sacrifice.
- **29497007:** A2 starts a first relocation where G2 declines, then uses a different second
  relocation. Its +.000491523J /+.726users/tick comes with quality−.031591591 and
  **613.328109m/UAV** more travel. The independent reviewer found most of this extra travel
  in ordinary resumption before120. Native J contains no travel-distance charge.
- **29497013:** G2 and A2 coincide; both improve J over T while losing3user-ticks
  (−.006users/tick) and adding about288.07m/UAV. Additional opportunity is not service-safe.

Thus B03's particular “positive options reordered, then continuously active” pattern does
not extend to B04. Nonpositive stationary and C-only champions can become useful parts of a
later control program, and early selected members may be remuted. This supports sequential
control complementarity; it does not isolate remuting as the cause of benefit. No additional
native counterfactual was acquired to assign such a mechanism.

A2−G2 mean quality is−.005651723048 [−.013102479851,.000502444714]; height penalty rises
.00001265625. Service is accompanied by .264125 fewer eligible-unserved users and .020250
more ineligible users on average. Those are accounting differences along changed trajectories,
not causal shares. A2−T quality is−.007240549531 [−.014561713631,−.000942840467]. The retained
capability therefore includes service/quality/travel tradeoffs, not a claim of overall utility.

The accepted full reader reconstructed all34source bindings, 1,701bulk artifacts,
24,048native snapshots, all48episodes, all700modeled branches and all157stationary banks.
The DM independently checked source/artifact bindings, complete native reductions, prefixes,
all80 selected forecast comparisons and the displayed witnesses from saved arrays. The
ResearchCritic independently reconstructed all748decision traces, cost ledgers and36contrasts;
its full scope and distinction from scorer replay are in the original answer below.

All80 executed forecast comparisons reproduce commands, masks and per-tick service exactly.
Maximum remaining-total-J error is **3.265939596985845e−6** and maximum physical-coordinate
error **5.775788815753913e−5m**. The80comparisons consist of16T complete t40suffixes,
16G2first prefixes through119,16G2complete actual120suffixes,16A2complete outer t40forecasts,
and16A2complete actual120suffixes. They are not80new episodes. A2's predicted second choice
matches its fresh actual second choice in all16worlds. G2's original t40C-only forecast is
only tested before its additional120decision; it is not mislabeled as a complete forecast of
G2. The critic also checked the modeled A2 outer branch corresponding to G2's first option
against G2's actual complete continuation. Unexecuted modeled alternatives remain forecasts.

| Measured worker quantity,16worlds/arm | T | G2 | A2 |
| --- | ---: | ---: | ---: |
| State/mask requests |10,889,698|17,271,568|49,905,021|
| Model transitions |35,420|60,500|188,560|
| Candidate-transit ticks |119,290|218,790|733,620|
| Stationary rows |6,100|11,100|37,100|
| Modeled branches |77|143|480|
| Stationary banks |16|32|109|
| Episode CPU seconds |436.621932491|683.353064851|1,973.802400477|

The worker total is **78,066,287requests /284,480model transitions /1,071,700candidate-transit
ticks /54,300rows**, with63,414,360ordinary candidate-position predictions. All prospective
ceilings hold. The full reader repeats the corresponding search ledger, adding another
78,066,287requests (156,132,574across the two search ledgers), and reconstructs native physics.
No cycle reuse was implemented. A2 costs **2.888407914×G2** and **4.520621283×T** in measured
episode CPU, including evidence recording. These are the implemented packages, not isolated
planning latency, minimum algorithmic complexity or a physical deployment benchmark.

Worker CPU/wall is3094.712765347 /3095.437050657seconds; full-reader CPU/wall is
3128.531899457 /3131.787420640seconds. Total measured study CPU/wall is
**6223.404735426 /6227.384584262seconds** (about1.729CPU-hours), including final aggregation.
Peak process RSS is394,132KiB. Process-lifetime self CPU including imports is6226.029166seconds;
child CPU is separately.001736seconds. Preparation, engineering/review, saved-data inspection,
publication and cleanup are additional and not comprehensively metered. The26constructed
native correctness transitions remain separately charged; no result-world pilot was run.
Across B01–B04 the direction has **304result episodes /152,000native steps /0new scientific
fits** and approximately **12,466.810297worker/reader CPU seconds**. Earlier imported training
assets and failed-attempt/support costs remain in the earlier records; unmetered CPU is not zero.

Required evidence is now uniquely retained at
`/home/fires/hmasd-artifacts/uav_fleet_transmission/b04_temporal_complementarity_a01/` on
local_linux. Its `raw/` contains1,701files /225,118,040logical bytes; the sorted compact JSON
list of existing `{path,bytes,sha256}` bindings hashes to
`46192dd0f3c8f2479367e5d1ec19a09d29db6ef0e6ed82032d0a85c25319cf49`.
All hashes were rechecked after relocation. The original full `reading.json` is also there;
local `run/raw` and `run/reading.json` are symlinks. Small config/summary/status/read-summary
copies allow the canonical run root to remain self-contained. Any later complete reader
must use that canonical root, because its containment guard intentionally rejects raw paths
escaping a supplied local symlink root. No repeat reader is needed now. The critic and Root's
source-only Oracle released raw/snapshot consumption; accepted snapshot/scratch cleanup will
follow publication and is recorded separately below.

<a id="b04-original-result-critic"></a>
#### Complete original independent scientific review

Original final from `/root/dm_fleet_transmission/result_diagnosis`, read in full:

> I recommend **retaining B04’s conditional anticipation capability and closing the fixed study**. The predicted first-choice changes and complete native benefit occurred. Additional planning depth, unchanged replication or a learning experiment is not justified automatically.
>
> I reconstructed B04 in this dedicated reviewer context, retaining my earlier B01–B03 analysis, before reading the original next-design recommendation. The accepted source is `239360b03f5d7acf788bd9ae5d4dccbde4f9237e`. The [final reading](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b04_temporal_complementarity_a01/reading.json) and [summary](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b04_temporal_complementarity_a01/summary.json) are complete; the process exited successfully and the terminal records agree.
>
> T retains the single t40 decision. G2 adds a fresh t120 decision. A2 anticipates that same later decision when choosing at t40, then replans at actual t120. Thus **A2−G2 is the relevant anticipation comparison**.
>
> | Complete H500 contrast | Mean J difference, 95% world-bootstrap interval | Mean service difference, users/tick | Mean path difference, m/UAV |
> |---|---:|---:|---:|
> | **A2−G2** | **+0.001706 [0.000278, 0.003935]** | **+0.243875 [0.022625, 0.543378]** | **+42.947** |
> | G2−T | +0.002044 [0.000106, 0.004581] | +0.180250 [−0.000375, 0.408500] | +85.580 |
> | A2−T | +0.003750 [0.001347, 0.006676] | +0.424125 [0.156750, 0.746263] | +128.527 |
>
> These are descriptive intervals over sixteen fresh worlds for fixed deterministic programs. There were zero fits or updates.
>
> The consequential evidence is stronger than a positive aggregate score. A2 changes the **first physical commitment** in worlds `29497004`, `007`, `010`, `011`, `012` and `014`. All six improve native J; five improve service and world `014` slightly reduces it. The other ten produce exactly identical complete A2/G2 trajectories.
>
> In every changed world, A2’s chosen first option has **lower modeled one-opportunity return** than T’s choice, but higher modeled two-opportunity return. Actual A2 also loses J before t120 in all six, then gains more afterward. This weakens the explanation that the second opportunity merely supplies an approximately choice-independent increment. It supports the narrower explanation that anticipating future control changes a useful present commitment.
>
> The positive and adverse cases both matter:
>
> - **World `010`:** A2 gains 0.004637 J and 0.356 users/tick while reducing travel by **87.43 m/UAV**.
> - **World `012`:** the largest gain is 0.016092 J and 2.086 users/tick, accompanied by lower quality and **135.11 m/UAV** more travel. It supplies approximately 59% of the aggregate J gain.
> - **World `007`:** A2 gains only 0.000492 J despite adding **613.33 m/UAV**. Service rises by 0.726, while quality falls by 0.031592. Most additional travel occurs during ordinary resumption before t120, rather than in the committed transit itself.
> - **World `014`:** A2 gains 0.002185 J but loses two user-ticks, or 0.004 users/tick, and adds **61.93 m/UAV**. This is an accurately predicted objective tradeoff.
> - G2 also has an adverse service case: world `013` loses 0.006 users/tick while gaining J and adding 288.07 m/UAV over T.
>
> A2−G2’s mean quality change is −0.005652. Its path interval spans −10.64 to +130.32 m/UAV. Every world’s service fifth percentile and minimum remain unchanged across the three arms; no zero-service steps occur. Travel is not charged by native J, so these observations do not establish overall cost dominance or a practical adoption threshold.
>
> The activation interpretation also needs revision from B03. In A2 worlds `012` and `014`, the first selected member activates at t70 and is remuted at t80. World `014` selects that same member again at t120. The useful object is the complete evolving control program; “two persistently active additions” would misdescribe it.
>
> The strongest sufficient explanation remains **ordinary finite planning under the known host law**. The matched G2 control separates anticipation from simply granting another opportunity. The result establishes neither a learning advantage nor optimality over all relocation programs: the search still retains one stationary champion per muted member. Unexecuted branches remain model forecasts.
>
> Numerical and execution evidence supports that explanation. All eighty selected forecast comparisons reproduce native commands, masks and per-tick service exactly; maximum remaining-total-J error is approximately \(3.27\times10^{-6}\). Predicted and actual second physical choices agree for both G2 and A2 in all sixteen worlds. I additionally checked A2’s modeled outer branch corresponding to G2’s first choice against G2’s actual complete continuation. This avoids incorrectly using G2’s original one-opportunity forecast as its two-opportunity value.
>
> My independent checks covered:
>
> - All 34 source bindings against the accepted snapshot/current files; all sixteen fixture arrays, seed addresses and native initial conditions.
> - All 1,701 bulk-artifact bindings, plus configuration and final reading.
> - All 48 native metric reductions, objective arithmetic, public-state encoding, motion, mask clocks, assignment/capacity identities and required shared prefixes.
> - All 700 saved model-array summaries, 157 candidate-bank digests and champion rankings, eighty actual selection rankings and seventy-seven inner rankings.
> - The decoded inner report/history binding and preservation of the unrounded outer physical state.
> - All 748 saved decision traces and their cost counters, and all thirty-six final paired contrasts, including per-world values and bootstrap intervals.
>
> I made no new controller, radio, model-score or native-transition queries. I did not independently replay every scorer calculation; the completed accepted reader performed that reconstruction.
>
> The full measured study cost is **6,223.40 CPU seconds and 6,227.38 wall seconds**, approximately **1.73 CPU-hours**. This includes 3,094.71 worker CPU seconds and 3,128.53 reader CPU seconds. Peak process RSS was about 385 MiB; bulk evidence is 225.1 MB.
>
> T, G2 and A2 used respectively **436.62, 683.35 and 1,973.80 worker CPU seconds** across sixteen worlds. A2 therefore costs **2.89 times G2** in this implementation, including evidence recording. The worker made **78,066,287 state/mask requests**, with 284,480 complete-model transitions and 1,071,700 candidate-transit ticks; the reader repeated the corresponding search work and reconstructed native physics. No cycle reuse was implemented. Engineering, review and correctness-support costs remain additional and incompletely metered. Across B01–B04, the record now contains 304 result episodes, 152,000 native steps and approximately 12,466.81 measured worker–reader CPU seconds, preserving earlier failed-attempt costs.
>
> The six reversals strengthen the scientific premise of Root’s resolved temporal allocation. They do not retrospectively compare its investment value with the unrun approximation alternative. My earlier preference for amortization also cannot treat uncompressed rollout cost as irreducible: competent exact reuse remains an applicable ordinary alternative, although its B04 runtime has not been measured.
>
> **No new result run is recommended now.** Retain T, G2 and A2 with their demonstrated tradeoffs. Further depth needs a distinct prediction or use decision. If economical execution later becomes the selected question, a worthwhile complete observation would compare a prespecified cheaper selector against G2 and A2 on fresh complete missions, accounting for menu construction, teacher data, fitting and runtime, with competent ordinary reuse as a cost reference. Preserved native benefit at lower total cost would support that continuation; forecast improvement without useful executed choices would not; native harm would reject the candidate while preserving B04. Features, fitting budget and compressed-runtime costs remain unselected, so that continuation is not launch-ready.
>
> **MATERIAL_DISSENT: no — for retaining the bounded anticipation claim and closing B04. No additional experiment is currently selected.**

<a id="b04-independent-disposition"></a>
#### DM response and changed explanation

I accept this scoped independent recommendation. B04 establishes a useful within-host
anticipation capability: six actual first commitments sacrifice one-opportunity and early
native value to obtain a better complete outcome under the same two selection opportunities.
It improves on both G2 and T on this panel, while retaining all service, quality, travel and
computation costs. This is empirical understanding and a constructive ordinary-control asset;
it is not a new learning method or evidence that neural learning is necessary. Search remains
restricted to one original stationary champion per currently muted member and fixed40/120
selection times. Neither all-site/sequence optimality nor optimal selection timing is claimed.

The original review's statement about second-choice correspondence is read with its stated
comparison scopes: A2 has a t40 prediction of the actual120choice; G2 checks its choice and
execution from the actual120report, not a nonexistent anticipatory prediction at40. Native
correspondence and accurate adverse predictions support complete-program ranking, not a
claim that every modeled alternative has an independent native label.

The negative first-champion and early-remuting cases revise the local B03 explanation. They
show why first-destination positivity or permanent extra activation is too narrow a capability
model. They do not isolate the causal role of remuting. The finite known-model planner remains
a sufficient account of the observed gains, with no identified learning or representation
bottleneck. Native J also omits travel distance, and its quality/service weighting permits
small service sacrifices; the adverse cases are part of the result rather than prediction
repairs. A practical adoption decision needs a substantive use/cost contract, not merely the
positive aggregate J.

Close the fixed B04 allocation. No unchanged replication, deeper search, additional decision,
fit or teacher acquisition is selected. The parent temporal question is broader than this
fixed recipe and remains open. Root now owns a concrete source-only next-allocation review
with the existing Oracle; that is not a new result producer or a request for routine launch
approval. Parent B06 already owns its R/T_E/K2_E/L amortization comparison and is not silently
extended to the temporal target. The preserved B03 critic's earlier approximation preference
and Root's resolved allocation remain informative alternatives, not a retrospectively won
investment contest.

<a id="post-b04-source-only-design"></a>
### Source-only next-allocation facts: timing and ordinary exact reuse — 2026-09-30

Root assigned the existing `/root/deep_report_review` a source-only successor allocation
using the complete B04 evidence and original result critic. No new result study, controller
query, native/model transition, benchmark, fit or acquisition is selected. The following
answers the Oracle's concrete source/arithmetic questions; it neither changes B04 nor silently
extends parent B06. The Oracle has read the complete original B04 review above and released
its raw/snapshot consumer requirement. Its final next-allocation advice remains with Root.

The candidate ordinary timing rule is at most two selections: first at40; second at the
first actual arrival plus one public-report cadence, `t2=40+duration+10`, or50after first
decline. Thus initiated first options lead to60/70/80/90, and the stay-first branch to50.
A matched greedy G_E and anticipatory A_E must both use this rule; each modeled first candidate
carries its own second clock. A_E's stay-first comparator also uses the later opportunity.
Compared with fixed120 this changes the first member's chance to be remuted, the muted/eligible
candidate set and the absolute ordinary-control phase. It is not an equivalent menu with a
renamed timestamp. The original120clock ensured one full40phase cycle after the latest first
arrival, not optimal timing or a settling guarantee.

Source mapping, read through CodeGraph and the specific unshown gaps:

- B04 `option.enumerate_champions` and `surrogate.simulate_segment` deliberately reject starts
  outside40/120. Menu pricing otherwise uses`500−start_t`; plan validation and commitment
  indexing are already start-relative and ordinary control retains its absolute phase.
- B04 `TemporalProgram` fixes120in the G2 delegation boundary, dispatch, nested prefix stop,
  report encoding, inner/outer starts, branch/bank labels and80offset annotation. Reader
  correspondence also binds that clock. A new rule requires a new owned contract and full
  reading, not a launch-time parameter change to this accepted source.
- Arrival+10is report-aligned and gives the arrival mask an executed interval. Actual fresh
  reports/history, replacement of the expired first plan even on decline, and decoded inner
  versus unrounded outer physical state remain required. There is no identified physical
  interface obstruction, but no timing benefit has been measured.

For an **unselected fresh16world /four-arm G2,A2,G_E,A_E comparison**, there would be64H500
episodes /32,000native steps /0fits. The integer-only uncompressed ceiling follows the same
accounting as B04. Let`B=89,601`, native ordinary ceiling`C500=120,750`,
`S(t)=242.5(500−t)`, and full eight-branch continuation-bank ceiling
`F(t)=8S(t)−19,306`. An initiated suffix is bounded by`S(t)−2,758`, attained in this request
bound at the shortest10tick commitment. For an early first commitment of durationL, the outer
prefix through`t2−1` costs at most`L+2,082`; its stay-first prefix costs2,425.
The early nested stay context costs`2425+B+F(50)+S(50)=1,054,845`; each initiated context
costs`(L+2082)+B+F(50+L)+S(50+L)`, whose maximum is1,032,687 atL10.

| Unselected arm | Request ceiling/world |16world ceiling|Model-transition ceiling/world|
| --- | ---: | ---: | ---: |
| G2 |1,891,196|30,259,136|6,720|
| A2 |8,351,156|133,618,496|31,040|
| G_E |2,026,996|32,431,936|7,280|
| A_E |9,437,556|151,000,896|35,520|

For clarity, G_E is`C500+2(B+128)+F(40)+F(50)`. A_E is
`C500+2(B+128)+1054845+7*1032687+F(50)`; all actual second replanning is charged.
Each first outer trajectory still totals460ticks; its prefix and suffix are not counted as
independent500tick episodes. A_E inner work is bounded by`8*(450+7*440)`ticks, since an
initiated first option cannot lead to an earlier second selection than60.

The four-arm total is **347,310,464worker requests /1,288,960model transitions /384banks /
268,800stationary rows /10,752,000candidate-transit ticks**, plus32,000native transitions
and native physics. Scaling B04's measured worker and full-reader CPU/request ratios to this
uncompressed ceiling yields about **3.8245worker +3.8663reader =7.691combined CPU-hours**
including scaled aggregation overhead. This is a planning estimate for a conservative request
ceiling, not expected runtime, node timing or an optimized-runtime measurement. Approximate
implementation/checking is3–5hours plus1–2hours of independent engineering review, **4–7hours**;
scientific reading, publication and support are additional and not formally metered. A simple
B04 model-tick storage scaling gives1.02GB; allow roughly **1–1.5GBcanonical raw**,2–3GiB
output/scratch headroom plus about1.6GiB accepted-source snapshot, and streamed peak process
memory around0.4–0.8GiB. These are source-derived estimates, not a fresh node admission.

The Oracle separately asked about reusing B04's verified old controls. If those same16world
arrays, host law, interfaces and immutable G2/A2 programs are retained, **32new G_E/A_E
H500episodes /16,000new native steps /0fits**, paired with32reused G2/A2episodes, would be an
exposed exploratory development panel. New ceilings become **183,432,832requests /
684,800model transitions /192banks /134,400rows /5,376,000candidate-transit ticks**.
The corresponding uncompressed estimate is **2.0199worker +2.0420reader ≈4.062combined
CPU-hours**, assuming old controls need hash/metric readback and no repeated old scorer
reconstruction. New raw is roughly0.55–0.8GB. New-program implementation and complete reading
burdens remain essentially unchanged. Old-world/result-selection exposure and sunk costs must
remain explicit; this is neither fresh confirmation nor a clean newly timed four-arm benchmark.
No such panel is selected.

The B06 `cycle.py` implementation was also read for the specific reuse question. Its exact
byte key contains physical positions, C's estimated positions, FP32 issued commands, public
user bits, entering mask and`t%40`. Within a known-law ordinary segment, post-arrival transition
reuse remains conceptually compatible. The current callable is nevertheless tied to40:
`_copy_history`/`_copy_plan`, initial physical decoding, the loop origin and report normalization
are fixed; it also returns no terminal controller/mask. A bounded segment adapter would need
separate start/end/report-horizon fields, optional unrounded outer physical positions, copied
terminal history and a fresh cache at every decision barrier. It must advance absolute clocks,
regenerate lawful reports, preserve each floating addition and report actual versus logical
counts. Early first prefixes allow only ten post-arrival ticks, so no period40 saving is
promised there. Never reuse a transition across a later selection or its arrival event.

This is a compatible ordinary optimization with a **new core executable adapter and reader
obligation**, not a drop-in use of the already verified B06 callable. Estimate another2–4hours
of implementation/checks and1–2hours of independent engineering review (**3–6additional
hours**). B06's accepted source and result remain untouched. Until such a new implementation is
verified, retain the uncompressed ceilings; B04/early-rule speedup is unmeasured. An unchanged
uncompressed full reader still pays its complete reconstruction bill even if the worker later
reuses transitions. These facts support Root's comparison of timing, economy or no new
purchase; they do not turn an engineering possibility into a scientific investment decision.


<a id="b04-final-cleanup"></a>
### B04 publication and measured cleanup — 2026-09-30

Scientific reading, complete original critic/disposition, compact evidence, own standing/routing,
topic3 revision and retirement of the completed substantive allocation are published at
`8598d7f75efb98333979b5d07371aab6b5527a56`. After terminal process/observer reconciliation and
critic/Oracle consumer release, native snapshot GC preview accepted the exact B04 snapshot
against published main; supported apply removed it and its Git worktree registration.
The same operation handle was never restarted. Actual deleted targets:

- `.git/hmasd-launch-sources/08885e0b953e4b26a89380d0fa6ccc38`
- `temp/directions/uav_fleet_transmission`
- `experiments/candidates/uav_fleet_transmission/__pycache__`
- `experiments/candidates/uav_fleet_transmission/b02/__pycache__`
- `experiments/candidates/uav_fleet_transmission/b03/__pycache__`
- `experiments/candidates/uav_fleet_transmission/b04/__pycache__`
- `tests/experiments/candidates/uav_fleet_transmission/b04/__pycache__`

All seven targets are absent and the snapshot is unregistered. Across the explicit deletion
targets plus local run and canonical retained-output union, allocated usage fell from
**1,960,984,576bytes** to **236,662,784bytes**: net
**1,724,321,792allocated bytes reclaimed**. This includes the small canonical metadata
copy cost rather than reporting gross deleted sizes alone. The local run now occupies
524,288allocated bytes and its canonical evidence location
236,138,496bytes. All1,701raw hashes and the full original reader hash
were reverified after deletion; raw and full-reading symlinks resolve. Required unique evidence,
compact positive/adverse conclusions and published useful code/tests remain. There is no
remaining cleanup tool blocker. Other directions, their accepted snapshots, and the earlier
B01–B03 unique evidence were not deleted.

Root has read the complete B04 critique and declined the priced G_E/A_E timing extension for
now. It separately assigned a source-only possible next question about retained categorical S
versus competent ordinary stochastic choice from C scores. After this closure, I supply lawful
interface/coverage/cost facts in this existing notebook; no new study, fit, actor/controller/model
query or launch is selected. Parent B06 learning and fleet B06 count contracts remain their
original leads’ work. No active result producer, unread B04 result/review or cleanup dependency
remains.

<a id="ordinary-score-source-assessment"></a>
### Source-only successor assessment: retained S versus score-directed ordinary sampling — 2026-09-30

After closing B04, Root declined the priced early-timing extension and assigned its independent
Oracle a different allocation question: whether the retained N5/all-on categorical students have
useful package value beyond competent ordinary stochastic use of C's candidate scores. I own
the concrete interface, existing-control coverage and full-cost facts below. This is **not a
selected experiment**. No code, synthetic policy evaluation, outcome probe, actor/controller/
radio query, fit or native transition was performed for this assessment. Existing saved
calibration means and cost fields were read; only cost fields were aggregated. Fleet B06's
accepted count-development contract and the parent DM's separate learned-top2 work
remain their leads' work.

The current published background was read at main 8d8dbf16320631864587ac6fa0abb70002975090,
especially RESEARCH topic4's local-inheritance, joint-sampling and native-development evidence.
It changes the question in three concrete ways. Both original fitted S assets must be retained;
one cannot select the better exposed endpoint. Their repeated complete S−Q benefits justify a
capability worth comparing, while the failed PPO and static-consequence continuations do not
make another fit the default. Finally, Q's fixed uniform tail leaves a specific ordinary
alternative unresolved; the absence of that comparison is neither a novelty claim nor proof
that its cost is worthwhile. No new shared empirical judgment is being published here.

#### Actual lawful interface and decision exposure

The relevant C is **LocalController(history=False)** in
[the original N5 controller](../../../../experiments/candidates/uav_local_history/b01/controller.py),
not the separate N8 transmission controller. Its immutable source SHA256 is
b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2.
The [MemoC wrapper](../../../../experiments/candidates/uav_fleet_adaptation/b02/controllers.py)
is bound to that source and already returns all27 scores and predicted-service values.

- A decision receives one ordered104-value FP32 local row and private predecision navigation
  index0..9. The first103 values encode own position, up to20 decoded current users and up
  to4 visible peers. Absolute time is excluded from the memo key and learned features.
  The wrapper validates shape, finite first103 values, at most4 peers, integer navigation,
  and nonnegative four-tick decision boundaries. The collector separately validates the
  entire finite5×104 observation; no evaluator coordinates enter the policy.
- Commands are the27 Cartesian products of −1/0/+1 in three coordinates, sorted by squared
  norm then lexicographic tuple. Each is repeated for4 ticks, with30m increments and clipping
  to x/y0..1000m and z50..150m. Physical aliases arise at clipped boundaries. They remain
  distinct ordered categories: merging them would change the sampling law.
- C forecasts each own trajectory while visible peers remain fixed. Unknown interference
  is inferred from current observed SINR, visible-peer power and noise when fewer than4
  peers are visible, then held fixed. Each station stably ranks its eligible local links
  (SINR>=3dB) and keeps at most10. Its candidate score is the four-tick **mean** of
  0.7×served/50 +0.3×mean clipped((SINR−3)/30,0,1), with zero quality for no service.
  These are dimensionless local proxy values, not logits or horizon-summed values.
  [Native N5 reading](../../../../experiments/candidates/uav_local_history/b01/study.py)
  uses the same weights and no height/travel penalty. The mismatch is the censored local
  information/frozen-peer forecast versus simultaneous joint closed-loop motion, not
  different objective weights. The N8 height term must not be imported into this question.
- Ordinary selection uses the first score argmax in that command order. If **all27**
  candidates have zero predicted service, it instead chooses the endpoint nearest its
  current serpentine waypoint at height50; navigation advances cyclically when within60m.
  The original waypoint/tie rule and returned next_nav are preserved even if a stochastic
  wrapper samples a different category. On later ticks the collector holds the sampled
  command; it does not resample every primitive tick.
- Each agent has an episode-local exact memo keyed by the first103 ordered FP32 values
  plus one navigation byte:413bytes. A miss pays the full C ranking; a hit deep-copies the
  cached action, scores, service, features and next_nav. Neither a random draw nor the
  sampled category is cached. All27 score values are thus already paid for by a C query;
  a score-based wrapper adds a distribution calculation, not another radio-model request.
  New trajectories can still change cache misses, so equal request counts do not imply
  equal runtime. C stores900 ndarray bytes per entry, excluding key/container overhead.
- The unchanged student uses114 lawful features: first103 observation entries,10-way
  navigation one-hot and the full-support fallback bit. Its charged analytic helper
  establishes that bit with at most(1+p)n setup plus2n extreme links, rather than ranking27
  trajectories. One-row FP32 MLP logits are cached; probabilities/draws are not cached as
  actions. It remains an analytic-helper-plus-network package, not a purely neural policy.

The frozen fleet decoder in
[b02/policies.py](../../../../experiments/candidates/uav_fleet_adaptation/b02/policies.py)
forms FP64 probabilities, uses one private indexed uniform addressed by
(root,world,decision tick,agent), accumulates an ordered27-bin FP64 CDF, sets its final boundary
to1 and takes searchsorted(side="right"). It validates finite nonnegative mass and sum within
1e-12. Future two-tape pairing can use two distinct frozen roots shared across arms while
preserving each marginal kernel. This is **not** parent B04's two-draw finite departure/tail
decoder; silently substituting that decoder would change the implemented program.

#### Existing measured ordinary controls and calibrated packages

The bounded read-only coverage scout found no measured parent/fleet wrapper sampling from
C's full scores or score gaps. Parent Q uses0.9 on C's current choice and0.1/26 on each other
category. Parent B04 compared independent, shifted and shared-uniform coupling on32worlds
29346000..29346031 with2tapes; parent B05 retained that Q law. Coupling changes do not supply
a score-directed ordinary tail. Fleet B04 tested C departure rates0/.05/.10/.20 and S
greedy/temperatures.5/1/2. Those temperatures apply to **S logits**, not C scores.
This is coverage of the scanned relevant implementations, not a repository-wide or literature
novelty conclusion; the Oracle owns the broader historical/library comparison.

The authoritative saved fleet B04 calibration mean J values are:

| Calibration worlds | C0 | C.05 | C.10 | C.20 | Selected package |
| --- | ---: | ---: | ---: | ---: | --- |
| L0:29350000..29350031 |.3439236531|.3588182763|.3614211067|.3535949711|S_L0_T2:.3963116796|
| L1:29352000..29352031 |.3264835771|.3594455693|.3537689976|.3472814433|S_L1_T1:.3959505514|

Thus C.10 is the best ordinary calibration mean in L0 and C.05 in L1. The earlier conversational
shorthand that C.05 led both was corrected before selection; no candidate was newly selected
from these readings. Across all eight candidates the paid B* identities remain S_L0_T2 and
unchanged S_L1_T1. The former's historical uncertain J gain also incurred more path and lower
minimum service; it is a retained comparator, not an adopted temperature upgrade.
The [bound B04 reading](../../../../runs/uav_fleet_adaptation/b04_native_development_a01/reading.json)
SHA256 is93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50.
Its full run has1312episodes/335872steps; final panels were29351000..29351031 and
29353000..29353031. Calibration and final innovations were separately rooted; candidates
within each lineage shared the calibration worlds/innovations.

#### Oracle's exact unselected G and the question it could answer

For concrete pricing the Oracle supplied one fixed law, **G**, with c equal to lawful C's
current choice, including its fallback. Set p(c)=.9; distribute the remaining.1 over the other
26 categories in proportion to exp((score[a]−max_alt_score)/tau), with FP64 arithmetic and
**tau=.7/50=.014** in four-tick-mean proxy units. When all scores tie, reuse Q.10's exact
probability construction. Preserve original category order/aliases, navigation, private
actual-path memoization, four-tick holds and fleet flat-CDF decoder. This is one prospective
law, with no temperature grid, calibration or score/outcome probe.

Tau is the proxy increment from one additional served user throughout those four ticks when
quality is unchanged. It does not come from fitted student logits or observed new score gaps.
Increasing weight with alternative score raises the real-arithmetic conditional mean tail
proxy relative to Q.10, while retaining its nominal departure mass. That statement has a
floating-point/finite-grid tolerance in the implemented decoder: tiny tail probabilities may
have zero representable CDF width, and nominal.9 is not an exact real-number sampling theorem.
The all-equal branch preserves Q behavior on zero-service fallback instead of turning navigation
into uniform27-way movement. No synthetic evaluation of this law has yet occurred.

This supplies a specific discriminating comparison: **G−Q.10** tests score-directed choice
within the same nominal departure rate; C.05 retains the other useful paid ordinary perturbation;
both S assets and their B* identities answer the complete retained-package question. A local
proxy improvement does not guarantee native improvement because all five agents change their
own future information and each other's interference. Higher native S value after this
comparison could retain a narrower useful learned package; ordinary G matching or exceeding it
could remove a default reason to prefer that package on this host. Neither outcome proves
learned coordination, broad learning superiority/failure, or optimal ordinary control. A G loss
would reject this fixed tail law, not identify the missing information or exploration mechanism.
J, mean service, service-p10/minimum/zero ticks, path and full compute all matter because J
prices neither path nor computing and individual-user continuity remains unmeasured.

I do not recommend a free-running calibration sweep or comparing best historical means from
different world panels. Any selected experiment should make this complete-package/empirical
boundary consequential; merely obtaining a new leaderboard row is insufficient. The Oracle's
independent scientific recommendation and Root's cross-question choice remain separate from
this feasibility assessment.

#### Complete prospective bill, without a result launch

The priced panel uses32 **new common worlds**, two common private tapes for each stochastic
program, all-on N5/U50/H256 and the unchanged native objective. It includes C once/world;
S_L0_T1, S_L1_T1, B*0=S_L0_T2, Q.10, Q.05 and G twice/world. B*1 is exactly S_L1_T1 and reuses that
output rather than adding a duplicate episode. World/innovation seeds and a launch are not
selected. These are32 independent world clusters conditional on two fixed fitted assets;
neither64 tape observations nor two assets create additional training replications.

| New work | Exact configuration count or pre-cache ceiling |
| --- | ---: |
| Complete episodes / native team steps |416 /106496|
| All agent decision requests |133120|
| Full-C requests: C,Q.10,Q.05,G |71680|
| Student requests: S_L0,S_L1,B*0 |61440|
| Indexed categorical draws |122880|
| New fits / expert labels / calibrations / optimizer steps / native-model shadow branches |0 /0 /0 /0 /0|
| C candidate trajectories / modeled ticks |1935360 /7741440|
| C candidate links / setup links |154828800 /7168000|
| Student helper setup+extreme links / one-row actor forwards |<=8601600 /<=61440|
| Native dense power slots, if one constructor plus416 resets |29401075|

The link ceilings use n<=20,p<=4; observed cache misses and n/p determine actual work.
The last line is275 dense U2A/A2A slots per reset/step, including diagonal placeholders,
not275 extra native transitions. G's deterministic distribution can be cached by the same
sufficient input; every actual decision still consumes its current private draw. The reader
has zero added native episodes. For conservative pricing allow reconstruction of all ordinary
C scores and student helper state up to the same miss/link ceilings again, up to61440 one-row
student replays, all133120 probability/navigation/cache/decoder records, all106496 saved native
transitions and metric reductions. The reader can also derive Q.10's same-history/same-uniform
choice on the20,480 already saved G decisions, then compare at most81,920 four-tick agent
positions from saved geometry. This is elementary saved-data/kinematic work within the reader
range, with no new controller, radio, actor or native rollout and no counterfactual reward.
Record requested departures and physical aliases separately. With the original flat CDF,
redistributing alternative mass can shift the modal interval; a common uniform does not force
the same departure event despite identical nominal.9 modal mass. This diagnostic establishes
whether G changed physical commands on its own histories, not a causal mediation effect.
Numerical, law and alias correctness checks remain separate support work and must be declared
before performing them; none was run in this source task.

Existing recorded complete-episode CPU anchors are roughly C.189–.194s, Q.10 .293–.308s,
S .294–.297s and B*0 .330–.353s in fleet B04/B05; the paid C.05 calibration averages
.266/.271s by lineage. Scaling those fields suggests roughly120–140CPU-s of episode work
for this panel, **not a measurement of G**. Allow **2–6worker CPU-min plus1–6reader CPU-min,
3–12combined CPU-min**, including imports, construction, serialization and conservative
reconstruction overhead. Single-thread wall would be comparable absent contention; queue,
admission, support and publication are separate. Historical cache savings are not worst-case
guarantees, and these ranges are estimates rather than enforced runtime bounds.

A new bounded law adapter, own collector/reader contract, source/asset bindings, meaningful
synthetic/RNG/alias checks, independent engineering review and publication/cleanup are about
**4–8support hours**. Existing frozen implementations can be imported unchanged; they should
not be modified or copied wholesale, particularly while fleet B06 uses them. Scientific/source
assessment time already spent is additional and unmetered. Budget roughly **.15–.30GB** for
one canonical raw copy plus compact records, a temporary **1.6–1.9GB** launcher source snapshot,
and **.6–1.0GB** peak-process planning headroom. These are not current node admission facts.
Accepted-source lifecycle, durable evidence verification, live-consumer checks and supported
snapshot retirement still apply if Root selects the study.

The sunk bill is not zero just because the new comparison has no fit. Original S_L0/S_L1 each
cost one8000-update fit,256 acquisition episodes/65536steps,81920 expert-label requests and
4096000 optimizer presentations. Together their actual complete B02/B03 studies used
**2fits/832episodes/212992unique native steps/205.046058286worker+reader CPU-s**, including
their evaluations and reused-control accounting. The two paid eight-candidate B* calibrations
add512episodes/131072steps; their saved complete-episode timers sum139.828009008CPU-s and
139.921819053wall-s, with187724945raw bytes. Those timers exclude apportioned whole-run
imports/reader/support, so they are not a complete isolated calibration runtime.

The broader already incurred fleet B04 program also paid for two unsuccessful PPO continuation
fits: through B04 the lineage is4fits+2calibrations/548864steps/722.648864331measured CPU-s.
B05 then incurred4head fits/1138688steps/1620.467426957chain CPU-s. Through those studies
the accumulated context is **8fits+2calibrations/1687552steps/2343.116291288measured CPU-s**,
across differing timing scopes/hosts, before this potential comparison, earlier B01 costs,
other parent studies and incompletely metered engineering. Those adverse purchases remain
visible, but are not all charged as necessary acquisition of the unchanged S or G law.

Cost sources are the original B02/B03 summary+reader and B04/B05 complete reading/summary
fields. Their reader SHA256 identities respectively are
a3f76992ccb01aa90138eec2272dc2667b7283d32e86742e87bf77e43bd613e9,
b0c4943bb0b7fe8b7ac70d21f64a8d6805b086815789d35ba3992746aa6a5c20,
93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50, and
4b7f2d5512f0ef21d7ecde24744fe77b065e7dcc38213436ef7a0d7a383a5d5c.
The canonical retained S files are424487bytes each, SHA256
b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a and
cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d; original bindings are in
[the inherited contract](../../../../experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py).
No new copy, asset reconstruction or deletion was needed for this source-only assessment.

<a id="b05-original-selection-review"></a>
### B05 selection: complete original independent question and answer — 2026-09-30

Root's native question was sent2026-09-30 22:48:31UTC to its existing independent
deep_report_review context. The final original answer returned23:10:40UTC. Both are preserved
below in full, with their historical wording; later timing/allocation changes do not edit the
question. Root read the full answer and selected the fixed score-aware comparison after reading
the complete source assessment. This is the applicable independent selection review; no extra
consultation or Pro Send is pending.

#### Original Root question

I have read your FULL final timing recommendation and both original B04/B06 critics. I accept no further N8 timing/temporal-depth purchase now, while retaining the demonstrated anticipation and all tradeoffs; I will preserve the full recommendation and reasoned Root decision. Parent DM has a separate bounded source-only pricing task for the original critic's already-fitted learned-top2 shortlist, with no new fit/labels or selected run. Do not absorb or duplicate that task.
New candidate question for source-only independent innovation/selection assessment, potentially replacing the completed fleet-transmission allocation, not a fifth DM: do the retained categorical S assets still offer useful complete-package value against competent ordinary stochastic choice that uses C's actual candidate scores, rather than only the fixed uniform .10 perturbation Q? The existing positive S−Q result is substantial but Q ignores the modeled gaps among its26 alternatives. This may be an overlooked economically useful ordinary capability, or may already be covered/too close to repeated asset ranking to deserve purchase. Root is NOT asserting novelty, superiority, an identified cause of S's gains or that this candidate is promising enough to run. Please first check the original C-prior, fleet B02–B05 calibration, parent sampling/composition, July/external and shared records for actual coverage or stronger already-measured controls; do not simply invent a temperature sweep.
If still useful, develop the smallest complete FAIR ordinary-policy comparison that can change use or the learning reference: available local information/nav/holds/fallback, existing C scores and score units/aliases, stochastic law and paid prospective calibration if indispensable, unchangedS/bothlineages/paidB*/Q/C references, panel/tape identities and complete cost/tail/quality/path outcomes. Explain whether it answers worthwhile ordinary-control/use knowledge rather than progress on learning by itself. Keep inherited learning evidence and all adverse/calibration exposure intact; do not rewrite S's demonstrated construction if an ordinary alternative performs well. Your reasoned recommendation may be to decline or propose a materially better independent question instead. Use all3libraries and load-bearing primary sources as needed, reusing applicable reading rather than ritual rescan. Source-only, no controller/actor/model/native queries, outcome calculation/pilot, implementation, fit or launch. Fleet B06 count study's fixed inputs/comparators remain untouched; this assessment cannot add arms mid-study. Work with the SAME /root/dm_fleet_transmission for concrete source/feasibility/cost facts after its B04 closure; I am assigning that source task there. Return full evidence-led reasoning, outcome implications, incremental and cumulative cost, and material dissent for Root selection.

#### Complete original independent answer

**Recommend selecting one bounded N5 comparison against a fixed score-aware ordinary policy.** Its value is practical: it can reveal a useful ordinary controller and change the reference for future learning. The evidence does not justify another fit, a temperature search, or a claim that this explains S’s gains.

The question remains worthwhile alongside the separately selected waiting-allocation and L2_E studies. It does not depend on filling the completed DM’s slot.

I checked the original C and memoization/decoder sources, native N5 objective, saved B02–B05 results and costs, original C-prior, parent sampling/composition records, relevant historical coverage, and primary passages from all three libraries. I reconstructed the comparison before reading the DM’s completed feasibility assessment. This review calculated no candidate outcomes and performed no controller, actor, model or native queries. G’s activation, performance and runtime remain unmeasured.

The retained positive deserves this comparison. The saved fleet results report:

| Existing S−Q mean J | Fitted B02 lineage | Fitted B03 lineage |
|---|---:|---:|
| B04 | +.014836 [−.003726, +.033398] | +.021881 [+.007273, +.036490] |
| B05 | +.023534 [+.006811, +.040257] | +.027712 [+.009724, +.045700] |

These are descriptive paired-world intervals conditional on two retained fitted assets. Repeated evaluation panels do not create additional training replications. B05 also retained mean service gains of 1.656/2.030 users per tick, higher service p10 and shorter paths. This is useful complete behavior, beyond a training-loss improvement. [B04 saved results](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/summary.json), [B05 saved results](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b05_native_consequence_a01/summary.json)

The adverse evidence remains consequential. B04 world 29351009 gives S−Q −.110627 J and −7.429688 users per tick; world 29353015 also strongly favors Q. B05’s S in world 29483104 has **two zero-service ticks**, despite improving that world’s mean service over Q. Quality is not uniformly improved: B04’s first lineage loses mean SINR quality. The failed PPO and consequence-head increments remain active, finite-learning failures; an ordinary-control comparison neither repairs nor erases them.

The coverage gap is specific:

- Original C-prior used a nominal .90 C/.10 uniform-alternative initialization; its actor inputs did not include C’s complete score vector.
- Fleet B04 calibrated C departure rates 0/.05/.10/.20 and S temperatures. **C_.10 led the ordinary candidates in lineage 0; C_.05 led in lineage 1.** The overall paid winners remain S_L0 at T=2 and S_L1 at T=1.
- Parent B04 changed joint sampling while retaining the marginal probabilities. Parent B05 demonstrated valuable managed-radio alternatives, but their additional information/control rights do not answer this all-on local-motion comparison.
- C7 and history-based H supply useful existing ordinary controls, but neither establishes a stronger score-aware stochastic alternative. The inspected July/external records reinforce information-matched comparison; they do not supply this missing measured policy. This is bounded coverage, not a novelty claim.

The important correction is therefore to the **ordinary reference**, not to the established construction of S.

C already computes 27 candidate scores from lawful current local information and its private navigation state. Each score is a four-tick **mean** of `.7 × served/50 + .3 × quality`. These weights match native N5 J; neither objective includes height, travel or compute penalties. The approximation comes from truncated local observations, inferred frozen unknown interference and stationary peers while all five actual agents move jointly. [Controller](/home/fires/hmasd-wsl/experiments/candidates/uav_local_history/b01/controller.py), [native reading](/home/fires/hmasd-wsl/experiments/candidates/uav_local_history/b01/study.py:60)

I recommend one prospective law, G. Let \(c\) be C’s current lawful choice, including fallback, and \(s_a\) its candidate score:

\[
p_G(c)=0.9,\qquad
p_G(a\ne c)=0.1
\frac{\exp((s_a-m)/0.014)}
{\sum_{b\ne c}\exp((s_b-m)/0.014)},\quad
m=\max_{b\ne c}s_b.
\]

Here `.014 = .7/50` represents one additional modeled served user throughout the four-tick mean, holding quality fixed. It is a physically interpretable prospective scale, **not an estimated optimum**. No calibration is indispensable for testing this one specified ordinary capability.

Preserve the following semantics:

- Original ordered 27 categories, including clipped physical aliases; do not merge categories.
- C’s returned navigation transition on each policy’s actual trajectory, four-tick holds, and episode-private caches.
- Exact Q_.10 probability construction when all scores tie, including the zero-service waypoint fallback.
- The original fleet FP64, one-uniform, indexed flat-CDF decoder. Cache scores/logits, never sampled actions.
- Both **fitted** S_L0/S_L1 endpoints and their original helper semantics. These names must not be confused with the historical untrained `S0` arm.

Weighting by score increases the conditional tail’s expected C proxy in real arithmetic. That does **not** guarantee native improvement. Numerical interpretation must also respect FP64/53-bit sampling: tiny bins may have no representable width. Under the flat CDF, reweighting alternatives shifts the modal interval, so common uniforms do not preserve the realized departure event.

The strongest objection to this purchase is that a locally better tail might suppress productive departures from a misleading forecast. A negative G result would reject this fixed program, not establish an ordinary-control ceiling or identify a repair. That uncertainty is the experiment’s useful content.

The smallest complete comparison I consider worthwhile is:

| Program | Episodes per fresh world |
|---|---:|
| Deterministic C | 1 |
| Q_.10, Q_.05, G | 2 each |
| S_L0/T1, S_L1/T1, paid B*0 = S_L0/T2 | 2 each |
| Paid B*1 = S_L1/T1 | Reuse identical output |

Use **32 fresh common worlds**, two prospectively fixed private sampling roots, N5/U50/H256, all transmitters on, unchanged physics and native objective: **416 episodes and 106,496 native steps**. Bind source/assets, initial geometry, static users, configuration and indexed draws before execution. Fresh world identities prevent this becoming another ranking on repeatedly exposed panels. Fleet B06’s count-study inputs and comparators remain untouched.

Freeze the reading before outcome exposure:

- Primary retained-package contrasts: S_L0−G and S_L1−G separately.
- G−Q_.10 measures the new ordinary law; G versus Q_.05/C and paid B* supplies the practical reference.
- Average the two tapes within each world, then report all 32 paired differences and descriptive paired-world uncertainty. Shared controls remain correlated; neither tapes nor repeated panels enlarge the number of fitted lineages.
- Retain native J, mean service, p10, minima, zero-service ticks, quality, path, boundary/alias behavior, cache work and complete CPU/wall cost. Aggregate service does not establish individual-user continuity.

The saved G scores, C index and uniform also permit a reader-only comparison with Q_.10’s same-history categorical choice: 20,480 decisions and at most 81,920 four-tick geometry comparisons. This distinguishes weak exposure or aliases from physically active intervention without another rollout or counterfactual reward claim.

The outcomes would change decisions as follows:

- **G improves over Q and credibly surpasses retained S with acceptable service/path/cost tradeoffs:** adopt G as a useful ordinary reference for future N5 learning comparisons. Preserve S’s demonstrated construction.
- **G improves over Q while S retains additional value:** keep both capabilities; future learning must address the stronger ordinary reference.
- **G is actively adverse:** retain the existing packages and close this fixed score-tail proposal. No automatic temperature sweep follows.
- **Differences are uncertain or exposure is sparse:** report that boundary. An interval crossing zero is not equivalence, and uncertainty alone does not purchase more evaluation.

A J increase coupled to worse tails, travel or compute is a tradeoff, not an automatic deployment upgrade. No task-specific conversion among those costs has been supplied.

The complete prospective bill is modest in compute but meaningful in support work. The DM’s published source assessment prices **3–12 combined worker/reader CPU minutes**, **4–8 support hours**, approximately **.15–.30 GB** of canonical raw evidence, a temporary 1.6–1.9 GB launcher snapshot and .6–1.0 GB process-memory planning range. These are estimates, not benchmarks or node admission. The worker makes 71,680 full-C requests and 61,440 student requests; before cache savings, C alone permits 1,935,360 candidate trajectories/7,741,440 modeled ticks. Full reading and its reconstruction cost are included. [Published source assessment, commit 0fd639636](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_transmission/NOTES.md#ordinary-score-source-assessment)

Sunk cost remains explicit. The two original S acquisitions involved two fits, 163,840 expert labels and 16,000 optimizer updates; their complete B02/B03 studies consumed 212,992 native steps and 205.046 measured worker/reader CPU seconds. The paid B* calibrations added 512 episodes/131,072 steps within B04. Through B05, the broader chain totals **8 fits, 2 calibrations, 1,687,552 native steps and 2,343.116 measured CPU seconds**, with differing timer scopes/hosts. The proposed comparison raises that step total to **1,794,048**, with no additional fits or calibration. Earlier fleet B01’s separate two fits/576,000 steps/31,190.348 CPU seconds and technical failure remain incurred; parent studies and unmetered scientific/engineering labor also remain separate.

The literature supports familiarity and limits, not a performance promise. Foundations **P13**, §2.2, defines Boltzmann choice from marginalized utilities in static potential games. **MARL-0405/ADER** discusses reward scale and entropy tradeoffs. **MEHARL, arXiv:2306.10715v6**, §4, uses soft action values and sequential policy improvement. None turns C’s truncated four-tick forecast into those objects or justifies `.014` as optimal. [P13 metadata](/home/fires/hmasd-wsl/docs/new-libs/corpus/papers/P13/metadata.json), [P13 primary text](https://arxiv.org/pdf/2204.05466), [MARL-0405 primary extraction](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0405.json), [MEHARL primary PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2024/fe066022bab2a6c6a3c57032a1623c70/arxiv-2306.10715.pdf)

**MATERIAL_DISSENT: no.** I recommend this bounded ordinary-capability comparison on its own value/cost. The evidence supports neither a broader superiority claim nor further investment contingent only on obtaining a positive result.

<a id="b05-selected-contract"></a>
### DM response and fixed prospective B05 contract

I accept the recommendation without material dissent. The source assessment and current
published topic4 support this ordinary-capability/use question. Both inherited S endpoints
are worth preserving, and G tests one competent way to spend already lawful C scores, without
assuming that extra reward training, temperature search or a new architecture is needed.
The promising premise is limited: G improves the conditional local proxy in real arithmetic;
the native consequence remains uncertain because local censoring and simultaneous motion can
make that forecast misleading. A negative or unresolved result can close the fixed law. Neither
retained learned gains nor this ordinary proposal supplies a general learning or coordination
claim. All positive/adverse earlier evidence and the cost chain above remain binding context.

Root selected this scope and delegated execution, reading, publication and cleanup to the same
direction lead. The new owned implementation is b05_score_sampling, object
UAV-SCORE-SAMPLING-B05; intended initial run tag b05_score_sampling_a01. This revises the active
question to retained local categorical packages versus score-directed ordinary stochastic
control. It does not resume N8 timing/depth investment or alter any fleet-count/parent source.

The exact G law, fitted asset hashes, seven distinct programs and B*1 identity reuse are those
in the source assessment and complete answer above. Frozen production details:

- Native host N5/U50, all radios on, H256,4-tick holds; original ordered27 categories,
  original source C, original114-feature helpers and original FP32 student endpoints.
  Student temperatures1/1/2 are fixed by the retained S_L0/S_L1/B*0 identities.
- Worlds29630000..29630031, two private indexed sampling roots29630101 and29630102,
  actor-constructor-only seeds29630111/29630112, master identity29630100. Address search
  found no prior use of this exact seed block;29510000 was rejected because fleet B06 owns it.
  Constructor seeds do not fit or replace any loaded parameter.
- Each world contains C once and Q10,Q05,G,S_L0,S_L1,Bstar_L0 on both tapes:
 13episodes/world,416total/106496native transitions. Bstar_L1 reuses S_L1 exactly.
  Rotate the13-member episode order by the world index to avoid fixed timing position.
  Every arm/tape resets from the same world; static users/initial geometry must agree by digest.
- CPU, one Torch/inter-op/BLAS thread, deterministic algorithms, FP32 actor/command and FP64
  score/probability/native-coordinate arithmetic. Preferred executing node is the configured
  remote wsl_4070 with its current interpreter; fresh actual-node admission remains required.
  No trial, pilot, partial panel, adaptive stop or selected retry is authorized.
- Retain every episode and all unique21 signed paired contrasts between seven programs.
  Primary S_L0−G and S_L1−G remain separate; G−Q10 is the fixed ordinary-law contrast.
  G−Q05/C and both paid B* readings are required, with Bstar_L1 transparently aliasing S_L1.
  All other contrasts are descriptive references, not additional confirmation tests.
- Average each stochastic metric across its two tapes within a world; C has its single value.
  Compute descriptive paired-world percentile-bootstrap95% intervals with10000 resamples,
  root29630191, using the same resample indices across metrics/contrasts. Preserve all32
  differences and each episode/tape. No fitted-lineage pooling, multiplicity-adjusted
  confirmation, equivalence margin or deployment utility price is asserted.
- Read native J/return, mean service, service-p10/minimum/zero-service ticks, quality,
  mean path/UAV, boundaries/zero displacement, fallback, categorical/physical exposure,
  cache/query/model/helper work and complete CPU/wall. G's saved-only Q10 comparison uses
  20480 categorical checks and at most81920 geometric agent steps; no reward counterfactual
  or new model/native shadow rollout is permitted. Report both nominal and realized
  departures; preserve finite-grid effects and clipped aliases.
- The full worker/reader count envelope and estimates remain those priced above. Reader
  reconstructs all ordinary C scores on each episode's actual saved histories with exact
  episode-private memoization; student helper state is replayed, and every logged student
  decision receives a one-row actor check (61440rows). Reader policy work is explicitly
  additional; it performs no new native environment transition. Source hashes, immutable
  assets, all saved arrays/metrics/decoders/clocks and paired geometry are checked.
- Stop the fixed study after complete reading and independent scientific diagnosis. An
  adverse/null/inconclusive observation does not authorize a new epsilon/tau, extra worlds,
  another fit or duplicated operation. Technical missingness is preserved as such and any
  repair has its own prospective exposure decision. This is exploratory fixed-policy work,
  not confirmation or a new population-learning claim.

The declared new fit/label/calibration/optimizer counts are all zero. The priced106496steps
would raise the selected inherited-chain exposure to1794048steps, while earlier fleet B01,
parent work and support remain separate incurred costs. Target canonical evidence stays one
copy on the executing node; collection retains compact local readings and verified locators.
No change to the earlier B04 evidence/cleanup is required.

<a id="b05-score-sampling-l0"></a>
### L0 — fixed score-tail kernel and complete paired native study

Deliver one bounded B05 worker plus full reader with immutable-source/asset bindings, exact
per-world/tape identity, partial-failure records, raw arrays and a compact complete reading.
Owned code is experiments/candidates/uav_fleet_transmission/b05_score_sampling/;
tests mirror that path under tests/experiments/candidates/; records/scratch remain in this
direction's existing NOTES, runs and temp paths. Author on shared main; no other direction
or shared host/launcher file is assigned. Existing frozen code is imported unchanged.
One bounded Implementer at a time may own only the policy-kernel module and its focused
tests; the DM owns contract, collection, reading, runner, notebook and Git index/publication.

The kernel interface is FixedPolicy(arm, actor, world, agent, sampling_root). Query receives
one local row, decision tick and predecision navigation; it returns original feature/cache/
next_nav fields plus action index/command, probabilities, innovation, entropy and chosen
density. Ordinary arms retain c_index/full scores/service. Student arms retain original
one-row logits. G uses exactly tau.014 and .1 departure mass, all-score ties reuse exact Q10,
and no cache stores sampled choices. No model or policy accepts evaluator truth. The DM will
review the implementation and checks; the engineer does not acquire notebook/index ownership.

Checks cover synthetic unequal/tied scores, finite-grid/tiny bins and original Q identity;
fallback/nav and copied-cache behavior; indexed RNG independence and no global-RNG mutation;
original S/T2 behavior on synthetic fixed actors; commanded versus clipped physical paths;
and a small synthetic-environment collector→storage→reader fixture with deliberately corrupted
draw, score, source or metric evidence rejected. No extra native correctness episode is planned.
Fixture observations/actors are fabricated, cannot use production worlds or immutable fitted
assets, and cannot pass the production admission path. Record actual test requests/support
costs; do not treat these as native results. Reuse unchanged host checks. Independent numerical/
RNG/reader/launch review is required before result execution. The DM accepts that review and
the bounded change, then commits/pushes exact inputs and performs remote-first fresh admission.

<a id="b05-implementation-acceptance"></a>
### 2026-10-01 — B05 implementation accepted; no production exposure yet

The bounded Implementer supplied only policies.py and test_policies.py; I read both and
accept the unchanged source-C/navigation/cache and original-S bindings. The DM implemented
the fixed contract/assets, collector, saved-array metrics, full replay reader and admitted
entry in the owned b05_score_sampling package. There is no new learner or fixture CLI.
The complete collector saves all requested original observations, score/service vectors,
student logits, random draws, densities, navigation/cache state and native arrays; failures
retain partial arrays and actual attempted/completed work. The reader reconstructs each C
query on saved actual histories, every student one-row logit (including deployment cache
hits), native/feature/navigation reductions and the full paired-world reading. It records
partial replay work on failure. Runtime Python/NumPy/Torch and actual thread/determinism
settings are retained. The two original actor files remain canonical remote inputs.

Independent engineering Reviewer /root/dm_fleet_transmission/b05_engineering_review inspected
the actual source and original dependencies in a separate context. Its conclusion was
“no material finding remains”; it checked law/ties, source C/navigation/cache, S lineage/T1/
T1/T2, indexed RNG, precision, clipped exposure, complete reader, paired bootstrap, immutable
asset/calibration inputs, partial failure and admission-before-assets. The original paid
calibration is read from its pinned Git blob so sparse checkout omission cannot silently
change B*. All26 source identities and the exact calibration hash/choice were verified.
After the narrow runtime-metadata changes and the new actual-reader corruption regression,
the Reviewer explicitly retained that conclusion. I accept the implementation. These are
engineering checks, not scientific evidence or a changed selection review.

Synthetic checks and their scope:

- Kernel helper: final73passed/1.14s; one earlier assertion tolerance was corrected from
  less than one FP64 ulp to four epsilon, with no production-law change. Across its two
  invocations:169 FixedPolicy attempts/139 successes,128 MemoC calls and70 original-student
  calls, including nested/reference work.
- DM integration:3passed/2.44s, then4passed/2.03s, then final4passed/2.00s. The second added
  reader failure accounting/CLI checks; the last added actual mid-reader score-corruption
  counters and production-fixture refusal. All changes were then inspected independently.
- Reviewer: complete76passed/2.25s before the last additions; changed integration4passed/
  2.15s afterward. Its kernel counters were98attempts/83successes,78MemoC/35original-student.
  Its final narrow inspection repeated no tests.
- The five integration invocations each used26fabricated episodes/208synthetic transitions,
  260worker policy queries,120helper-replay requests and237actor rows including reader work.
  MemoC calls were294each except295in the final DM corruption check. Each invocation also
  ran one failing fixture with5ordinary queries,3fabricated step attempts/2completions.
  Thus the integration support used1050completed fabricated steps/1055attempts,1325worker
  query calls,1496MemoC calls including reader/corruption checks,600feature requests and
  1185actor rows. These counters overlap by construction; they are not independent episodes.
  Every policy row/actor/world was fabricated, with zero native transitions and zero fitted
  asset loads. Source inspection and checksum reads are additional support costs.

The tests exercise unequal/tied scores, tiny53-bit bins, copied caches/fresh draws, original
T1/T2 behavior and RNG isolation, all27 categories at clipped aliases, worker→raw→reader,
corrupt draws/scores/commands/features/navigation/probabilities/source/metrics, paired-panel
completeness, partial worker and reader costs, and admission-before-output. No native pilot
was inserted. The remaining production check is the selected complete run on the actual
remote node, subject to fresh admission. No seed, arm, horizon, stopping rule, output contract,
fit/calibration count or scientific interpretation changed.

<a id="b05-accepted-operation"></a>
### 2026-10-01 — B05 accepted remote worker and complete-reader chain

Published exact inputs are `54c57af8d2e3860f25a278850055a6aa020e5beb`. The fixed operation was
accepted at00:23:23UTC on wsl_4070. Its original command, source snapshot, node and native
identities are in the [launch manifest](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/launch-manifest.json);
[fresh actual-node preflight](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/admission-preflight.json)
passed both4GiB floors with14,673,215,488available bytes. This is the selected416episode/
106496step worker plus its full reader in one process, not a pilot or extra panel.

Remote preparation encountered an existing mixed canonical checkout: HEAD was older, while
compute/launcher overlays already matched current published main. A normal fast-forward
refused without overwriting those edits. I preserved that branch and all other edits, syncing
only this direction's stale remote table row from published main; current pause/lead matched.
Two non-login Git reads stalled on network/lazy object retrieval and their exact owned HTTP
helpers were stopped before any launch. The configured zsh login network environment resolved
retrieval. Git also reported an existing historical bad-tree/repack warning; no repository
repair or cleanup was attempted. These were source preparation facts, with zero native work.
The configured supervisor accepted one launch request; it then returned the native accepted
manifest. No duplicate scientific request was submitted.

The old completed observer was drained and rearmed from14to15. New observer registration
initially rejected the relative executable `ssh`; replacing it with existing absolute
`/usr/bin/ssh` registered **generation16**, job`launch-b05-score-sampling-a01`, against this
same output/status handle. First observed facts at00:24:39UTC confirm accepted admission,
live matching runner/supervisor identities and consistent records, with0probe errors. The
request remains under temp/directions/uav_fleet_transmission/b05/observer-request.json.
The native child stays active with deterministic waiting and same-handle drain/rearm through
complete reading; queue delivery is not assumed. No outcome prefix has been interpreted.

<a id="b05-complete-reading"></a>
### 2026-10-01 — B05 complete: conditional score-tail tradeoffs and retained S value

The one accepted worker/full-reader chain exited0 at00:25:44.891UTC; observation returned
READY at00:26:11UTC with absent original processes and consistent records. Generation16's
READY event`2f1bdc4477804205a25cca8b`/wake`30f79673-4a70-4ea9-b478-4a677e9547f3`
was drained, consumed by rearm17, and observation stopped. App queue again explicitly rejected
native-child delivery(-32600); active deterministic waiting supplied the terminal fact. There
was no rerun, replacement read, partial panel or additional fit. The unrelated same-node
waiting-study SIGSEGV reported later at00:27:41 does not change this run's observed exit0 and
full verification; this successful operation does not diagnose or clear that runtime problem.

[Original complete summary](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/summary.json),
[full reading](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/reading.json),
[configuration/source bindings](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/config.json),
and [native terminal status](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/launch-status.json)
are collected byte-identically. All416episodes/106496native transitions are present, with
0new fits, optimizer updates, training steps, labels or calibrations. Both immutable source
actors and the paid B* Git blob passed before/after checks. Every original C decision was
replayed on its actual saved local history; all61440student decision rows received fresh
one-row actor checks, including deployed cache hits. Full shapes, original scores/service,
features/navigation, caches, addresses/CDFs/densities, native reductions/motion/clocks,
paired geometry and all21contrasts passed. The reader added0native steps.

Each stochastic level below averages two tapes within each of32worlds; C has one episode per
world. Intervals below are the fixed10000-resample paired-world descriptive percentile95%
intervals, conditional on these two fitted assets. They are neither training replications nor
an equivalence/adoption rule. All per-tape/per-world observations, signed differences and
losses remain in the original JSON; no endpoint or metric was selected away.

| Fixed deployed program | Mean J | Service/tick | Service-p10 | Served-user quality | Path m/UAV | Policy-query CPU s/episode | Complete episode CPU s |
|---|---:|---:|---:|---:|---:|---:|---:|
| C | .341131 | 20.341431 | 19.078125 | .187836 | 2801.868 | .019046 | .163884 |
| Q10 | .357544 | 21.570068 | 17.117188 | .185210 | 4074.037 | .097916 | .255717 |
| Q05 | .360229 | 21.760925 | 17.578125 | .185254 | 3413.453 | .075797 | .227301 |
| G | .360972 | 21.666443 | 18.507812 | .192139 | 3688.557 | .085962 | .239732 |
| S_L0/T1 | .374588 | 22.936646 | 19.664062 | .178249 | 3272.185 | .088964 | .245271 |
| S_L1/T1 = Bstar_L1 | .384403 | 23.534424 | 20.023438 | .183071 | 3421.793 | .091756 | .247024 |
| Bstar_L0 = S_L0/T2 | .390959 | 24.117432 | 19.492188 | .177715 | 4351.792 | .121701 | .282497 |

**Primary retained-package comparisons.** S_L0−G is J+.013616[−.000949,+.027997],
21positive/11negative worlds; service+1.270203[+.203368,+2.304039] and p10+1.156250
[+.039063,+2.242383]. Path is416.372m shorter[−772.845,−53.614], but mean served-user
quality is−.013889[−.019642,−.008301]. Its mean J advantage over this stronger reference
remains unresolved, not equivalent. S_L1−G is J+.023431[+.012843,+.033524],27positive/
5negative; service+1.867981[+1.077617,+2.606001] and p10+1.515625[+.500000,+2.421875].
Its path point is266.765m shorter but interval[−695.938,+116.712] crosses zero; quality is
−.009068[−.013615,−.004719]. Both advantages in mean service coexist with quality losses;
this quality averages only served users and does not identify harm to the same fixed users.
S_L0/S_L1−Q10 J remains+.017044[+.001261,+.033260]/+.026859[+.015302,+.038930].
Against Q05, S_L0's J interval also crosses zero; S_L1 is+.024174[+.013635,+.034666].
These are separate fixed assets, not a pooled new learning result.

**Ordinary-law comparison.** G−Q10 gives J+.003428[−.007610,+.014797] and service+.096375
[−.715413,+.935858], with18/14J and16/16service signs. The intermediate score weighting
therefore did not establish a mean native J/service upgrade. It does supply a conditional
p10/path/quality tradeoff: p10+1.390625[+.648438,+2.156250], quality+.006928
[+.002847,+.011311], path−385.480m[−595.125,−180.430], and complete CPU−.015985s
[−.020649,−.011568]. G−Q05 remains unresolved in J(+.000743) and service(−.094482),
while p10+.929688[+.164063,+1.906250] and quality+.006884 accompany275.104m extra path
[+19.963,+534.345] and+.012431s complete CPU. Q05 remains a serious lower-path/lower-CPU
ordinary option. G−C J is+.019841[+.000287,+.039811], but service's interval crosses zero,
p10 is−.570313 and path+886.689m[+510.287,+1234.997]. There is no ordinary default winner
priced by J, which excludes travel/compute; deterministic C's much cheaper cache-heavy route
and every G/Q/C loss remain part of the complete comparison.

**Paid reference and adverse tails.** Bstar_L0−G is J+.029987[+.019919,+.040386],
service+2.450989[+1.725192,+3.201546], p10+.984375[+.171875,+1.797070], but quality
−.014424, path+663.235m[+364.725,+961.666] and CPU+.042765s. Bstar_L0−S_L0 improves
mean J+.016371[+.006474,+.027418] while adding1079.607m/UAV; p10's point is−.171875
and unresolved. Bstar_L0−S_L1 J+.006555[−.001612,+.015284] does not establish superiority
and adds930.000m/UAV. Bstar_L1 is exactly S_L1, not an extra episode/asset. Neither paid
calibration choice becomes a new default from this panel.

All ordinary arms have no total-service-zero tick here. At world29630013 the two S_L0 tapes
have8/1zero-service ticks, S_L1 has2/7, and Bstar_L0 has1/1. Thus both original students and
the paid temperature option retain a concrete outage counterexample against G/C/Q; aggregate
p10 improvement is not reliability or individual-user continuity. Worst world29630011 loses
.091119J/6.505859service/6.75p10 for S_L0−G, and.057153J/4.287109service/8.75p10 for S_L1−G.
S_L0−G has9service and10p10-loss worlds; S_L1−G has5service and6p10-loss worlds. G−Q10 has
14J/16service/5p10-loss worlds, including−.056547J at29630020 and−4.726563service at29630021.
All21pairwise signed series, extrema, boundaries, fallbacks and zero-displacement readings
were retained and read; these examples do not replace the complete adverse evidence.

**Intervention exposure and its limit.** On20480actual G decision histories, Q10's same-uniform
category differs1904times;1845produce different four-tick physical holds/endpoints,59are
physical aliases. There are350exact all-score ties;0positive float categories lose all53-bit
grid mass on this realized panel. Mean conditional expected score gain is+.002786660, its
minimum is0; grid-exact expectation agrees to floating precision. The realized same-history
score difference averages+.002665725. G departs from C2067times versus2054for the hypothetical
Q10 at those G histories, with163changed departure events. The actual independently visited
Q10 episodes have2047departures, a different object. This is genuine decision/physical
exposure and the predicted proxy improvement, not a sparse-activation failure. The81920saved
geometric agent ticks use no radio/controller/native shadow and supply no alternative reward.
Better conditional local scores plus uncertain complete native J/service cannot identify the
proxy error, joint interference, censoring or exploration mechanism; no causal mediation or
pure tail-content effect at fixed departure events is claimed.

**Actual cost.** The worker made71680ordinary and61440student requests,122880indexed draws,
20480score-tail evaluations,416explicit resets plus1constructor reset. Ordinary memo misses
were37692, charging1,017,684candidate trajectories/4,070,736model ticks,16,819,272candidate
and169,899setup links. Student misses/one-row forwards were41724; analytic helpers used
202923setup and378330extreme links. The full reader adds the same C/helper reconstruction
and61440actor rows, not free validation. Query CPU totals36.583563s, reset.286514s, native
steps49.541658s and raw compression/hash6.191928s; complete episodes total101.086969s.
Complete worker entry is103.247538CPU/104.186117wall seconds; reader36.723201CPU/36.697300wall;
enclosing entry-to-read chain140.041000CPU/140.954939wall seconds, including recorded gaps.
The shared-process high-water mark is434952KiB, not a sum of per-stage peaks. Native dense
power slots total29,401,075 including resets. No speed claim extrapolates beyond this host/
load; G's lower realized CPU than Q10 includes different visited histories and cache misses,
not a matched-input kernel benchmark. S query CPU is similar to G and remains much above C.
This study raises the selected B02–B05 inherited-chain exposure to1,794,048steps with8fits/
2paid calibrations unchanged, and the sum of previously scoped CPU readings to2483.157s;
other B01/count/parent branches and unmetered engineering/advice remain separate, not erased.

Canonical unique raw evidence stays at wsl_4070:/home/wu/projects/HMASD/runs/uav_fleet_transmission/
b05_score_sampling_a01/raw/:416files,179862927logical bytes/180719616allocated bytes. Every file
was rehashed against the original summary during collection. SHA256 of sorted lines
`relative_path<TAB>bytes<TAB>sha256<NEWLINE>` is
`2ad9e833a5a7d4772a99157af46ed999539d90ea7edd99e32340d85425c948cf`.
Local compact config/summary/reading/exit SHA256 values are respectively
`823f63c6d4581ea1e7d41f628c567a57a699eed3bc3eaf4c3713023c868ac658`,
`349a2ca0a1ea10924089ecd1482d3c1025367b1ddcc9dcd32e8e008292c4b70b`,
`91ed776d2234a20c44a6f660d6a7dcc5eaeaab77a0672a1e42ba7587c1897926`,
`f63bcb790b24dc3257fcd61a3ea1dbab919951abb16521f8b5f5c9b79981fc51`.
Both original logs are empty. No local raw duplicate was made.

My current reading strengthens the conditional S_L1 package capability beyond this competent
ordinary G and retains S_L0's service/path capability while weakening a uniform mean-J claim
for both assets against stronger ordinary controls. G adds a useful ordinary quality/tail/path
choice, not a clear mean-J/service replacement for Q10/Q05 and not an explanation that absorbs
all S value. The analytic proxy prediction materialized but did not establish its native mean
consequence. Representation and possible further learning remain untested by this0fit study;
prior failed learning increments remain adverse. Independent ResearchCritic is reconstructing
these original results and prior sources separately; final fixed-law disposition follows that
reading below. No next experiment, retuning or replication is selected meanwhile.

<a id="b05-independent-disposition"></a>
### 2026-10-01 — B05 independent diagnosis and fixed-study disposition

The dedicated ResearchCritic `/root/dm_fleet_transmission/b05_result_diagnosis`, created
with no inherited DM/Root conversation, returned the complete answer below at 00:37:43 UTC.
Its assignment supplied the actual fixed question, source/config/summary/reading, canonical
raw locations, original construction and failed-development evidence, and the original
selection answer. The critic reconstructed original evidence before reading my completed
interpretation; the fixed administrative stopping boundary was visible throughout. It ran
no new policy/model/native evaluation or fit. Its independent checks and their limits are
part of the answer, rather than an assertion that every source was independently replayed.

**Original scientific review, verbatim:**

> **Recommend stopping the fixed B05 study and retaining its conditional capabilities.** S_L1 retains useful native value beyond G; S_L0’s reward advantage remains unresolved. G adds useful ordinary service-tail, quality and cost tradeoffs without establishing a mean-reward improvement over Q10 or Q05. No automatic retuning, additional fit or confirmation is warranted.
>
> I received no inherited DM/Root conversation. I reconstructed the frozen comparison and native evidence before reading the original selection answer and DM’s completed interpretation. The assigned stopping boundary was visible from the outset.
>
> I checked source `54c57af8d2e3860f25a278850055a6aa020e5beb`, all 26 configuration source hashes against the committed and local files, both canonical actor-file hashes, the pinned calibration blob, and terminal records. I reconstructed all 21 paired contrast vectors for nine consequential metrics from the 416 episode records and exactly reproduced the declared bootstrap intervals for both primaries, G−Q10, G−Q05 and Bstar_L0−G. I directly read and hash-checked 39 canonical raw episodes: every arm/tape in worlds 29630011, 29630013 and 29630017. These include the strongest primary adverse world, all zero-service episodes and a strong positive world. Connections, service, SINR quality, reward, path, motion, all-on transmission and common initial geometry agreed.
>
> I did **not** independently repeat the complete controller/actor replay or inspect every raw episode. The original complete reader reports 71,680 ordinary-query replays, 61,440 student-row checks and zero new native steps. My raw checks also reproduced six G-versus-Q10 saved-history category/proxy comparisons. The compact local files matched their remote counterparts. [Configuration](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b05_score_sampling_a01/config.json), [summary](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b05_score_sampling_a01/summary.json), [complete reading](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b05_score_sampling_a01/reading.json).
>
> The primary evidence supports separate asset judgments:
>
> | Contrast | Mean J difference [descriptive 95% interval] | Other consequential differences |
> |---|---:|---|
> | S_L0−G | +.013616 [−.000949, +.027997] | Service +1.270/tick; within-episode service-p10 +1.156; path −416m/UAV; quality −.013889 |
> | S_L1−G | +.023431 [+.012843, +.033524] | Service +1.868/tick; p10 +1.516; path −267m, with its interval crossing zero; quality −.009068 |
> | Bstar_L0−G | +.029987 [+.019919, +.040386] | Service +2.451/tick; p10 +.984; path +663m/UAV; complete episode CPU +.042765s |
> | G−Q10 | +.003428 [−.007610, +.014797] | Unresolved mean service; p10 +1.391; quality +.006928; path −385m/UAV; CPU −.015985s |
> | G−Q05 | +.000743 [−.009557, +.010863] | Unresolved mean service; p10 +.930; quality +.006884; path +275m/UAV; CPU +.012431s |
>
> These intervals describe 32 paired world clusters after averaging the two stochastic tapes. They are conditional on the fixed assets, with no equivalence or multiplicity-adjusted confirmation claim.
>
> S_L1−G improves J in 27/32 worlds; S_L0−G improves it in 21/32. Both retain positive J intervals against Q10, while S_L0−Q05 remains unresolved. Bstar_L0’s positive reward increment over unchanged S_L0, +.016371, costs approximately 1,080 additional metres per UAV; its p10 improvement is not established. Bstar_L0−S_L1 remains unresolved in J and adds 930m/UAV. Bstar_L1 is exactly S_L1, so it supplies no additional replication.
>
> The strongest adverse evidence must remain beside those means. In world 29630013:
>
> | Retained program | Zero-service ticks, tape 0 / tape 1 |
> |---|---:|
> | S_L0 | 8 / 1 |
> | S_L1 | 2 / 7 |
> | Bstar_L0 | 1 / 1 |
>
> Every ordinary arm has zero such ticks on this panel. All six retained-policy outage episodes are genuine native observations. In world 29630011, S_L0−G loses .091119 J and S_L1−G loses .057153 J. Conversely, world 29630017 supplies a substantial S_L1 gain on both tapes. These cases prevent universal dominance or reliability claims without cancelling the complete positive comparison. Absence of ordinary outages here does not establish ordinary-policy safety. Average service-p10 also does not measure individual-user continuity. Quality averages different served-user sets, so its decrease does not identify harm to the same users.
>
> G was meaningfully active. Of 20,480 saved G decisions, only 350 had all scores tied. The hypothetical Q10 choice on those same histories differed in 1,904 categories and 1,845 physical holds. The conditional expected proxy gain averaged +.002786660, and the realized saved-history proxy difference averaged +.002665725. No positive category lost all finite-grid sampling mass on this panel. Nevertheless, the complete G−Q10 mean J/service difference remains unresolved.
>
> This is neither nonactivation nor evidence of an actively harmful native intervention. It is a realized proxy improvement with uncertain mean native benefit and useful secondary tradeoffs. The 163 changed departure events also matter: common uniforms and equal nominal departure probability do not isolate tail content while holding departure events fixed. Saved-history geometry supplies no counterfactual native reward.
>
> The strongest simpler explanation remains **useful state-dependent stochastic control inherited through imitation**, with its action distribution and resulting trajectories differing from C/Q/G. C’s local forecast freezes peers and approximates censored interference while actual agents move jointly. Reweighting its alternatives can improve that forecast without improving the complete coupled trajectory. G’s realized physical departures are also fewer than Q10’s despite the shared nominal .1 categorical departure probability. These observations make forecast limitations and physical aliasing plausible explanations; they do not identify either as the cause.
>
> The stronger ordinary comparison weakens the claim that any competent stochastic use of C would absorb the retained capability: the specified G does not absorb S_L1’s gain. It does not establish that learning is necessary, that S learned coordination, or that no better ordinary law exists. G is a competent, prospectively fixed comparator; an exhaustive tuning search is unnecessary for this conditional result.
>
> The resulting scientific update should distinguish three judgments:
>
> - **Representation:** this strengthens demonstrated capability of the existing lawful helper-plus-network representation, particularly S_L1, against a stronger ordinary comparator. I would narrow the DM’s statement that representation is “untested”: representational limits were not tested, but an implemented policy’s capability received new evidence.
> - **Learnability:** B05 adds zero fits and no new evidence of training-population reliability or useful further development. Original construction evidence survives. The earlier active PPO and consequence-head continuations remain adverse: B04 R−S was −.040278/−.005212 J; B05 CONT−S was −.005135/−.005498. Their physical interventions occurred, so inactivity does not explain those results. Repeated evaluation of the same assets does not add independent training units. [B04 evidence](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b04_native_development_a01/summary.json), [B05 consequence evidence](/home/fires/hmasd-wsl/runs/uav_fleet_adaptation/b05_native_consequence_a01/summary.json).
> - **Complete package value:** retain S_L1’s conditional reward/service capability, S_L0’s service/path capability, and the paid temperature option’s reward–travel tradeoff. Retain G alongside Q05/Q10 as an ordinary reference. No supplied utility prices travel, computation, quality and outages sufficiently to select a universal deployment winner.
>
> The original selection predictions were discriminating. A G improvement that displaced S would have changed the preferred ordinary reference; an additional S gain would preserve learned-package value; an active G loss would reject this fixed law; uncertainty alone would not purchase more evaluation. The observed result combines retained S_L1 value, ordinary secondary benefits and unresolved G mean improvement. It does not justify describing G as either a general replacement or a failed controller.
>
> The completed 416-episode panel is an adequate complete observation for that decision. There is no missing primary comparison requiring repair. I recommend no further native run now. More worlds would refine conditional asset means but would not resolve training variation or price the observed tradeoffs. A future replication is worthwhile only if its possible outcomes change a stated use or scientific decision. A future learning question needs independent training units and a constructive prediction beyond preserving competent starting assets; the present result does not automatically supply that prediction. Any richer information or control contract should give the ordinary comparator the same addition.
>
> Measured new cost is **106,496 native steps, zero fits, 103.248 worker CPU seconds and 36.723 reader CPU seconds**; enclosing totals are **140.041 CPU seconds and 140.955 wall seconds**. Peak process RSS is 434,952KiB; raw evidence occupies 179,862,927 logical bytes. G’s lower episode CPU than Q10 includes different trajectories and cache misses, rather than a matched-input kernel speedup. Support, admission, consultation and publication labor remain unmetered; the prospective 4–8 hours is not an actual measurement. The selected inherited chain now totals **8 fits, 2 calibrations, 1,794,048 native steps and 2,483.157 measured CPU seconds**, across differing timer scopes and hosts. Other historical branches remain separate incurred costs.
>
> I find no material objection to the DM’s substantive reading or to stopping this fixed study. The correction is to preserve the positive ordinary tradeoffs and demonstrated representational capability while withholding broader learning, reliability and adoption claims. Stopping this purchase does not close the parent scientific question.
>
> **MATERIAL_DISSENT: no — supported for stopping the fixed B05 study, retaining the conditional capabilities and selecting no automatic extension.**

**DM response and resolved choice.** I read and accept the complete independent answer.
It changes one phrase in my provisional reading: the existing helper/network representation's
demonstrated capability is strengthened, especially S_L1 beyond G; only its representational
limits and potential for reliable further learning remain untested here. This correction is
recorded without rewriting the earlier entry. The fixed study strengthens the original
learned-package capability and the usefulness of G's secondary tradeoffs. It does not supply
an explanation of S's benefit, a claim of learned coordination, a general learning advantage,
a training-population replication or a universally preferred deployed controller.

The actual categorical departures on each program's own histories are G 2,067 / Q10 2,047 /
Q05 1,049; their four-tick physical departures from C's corresponding command are 1,483 /
1,941 / 998. These are distinct from Q10's 2,054 hypothetical categorical departures on G histories. Equal nominal
.1 therefore does not match either realized departure events or physical intervention rates.
The saved-history score improvement and native mean uncertainty leave forecast error,
physical aliases and changed coupled trajectories unseparated. None is promoted to a causal
diagnosis or a reason for an automatic temperature/epsilon repair. Student departures relative
to their own modal category, if used, are a different comparison and are not C departures.

Stop the completed fixed B05 purchase and keep the capabilities with their adverse cases:
S_L1's conditional J/service gain; S_L0's useful service/path behavior and unresolved J gain;
paid Bstar_L0's reward–travel tradeoff; and G/Q05/Q10/C's different ordinary costs and tails.
The whole panel and reader are complete. No further world, fit, calibration, tau/epsilon
choice, confirmation or new question is selected. Additional fixed-asset evaluation would
mainly refine means without resolving training variation or the unpriced deployment tradeoffs.
A future learning allocation needs a substantive constructive prediction and independent
training units; a richer-contract comparison must give the ordinary controller the same new
rights/resources. That is a possible future question, not an active continuation or required
approval. Root owns cross-question allocation at this returned boundary. The parent question
remains open, with prior PPO/consequence/count adverse evidence and all N8 findings intact.

The original selection review and this separate-context result diagnosis cover this decision.
No unresolved disagreement or distinct Pro expertise was identified, so no duplicate Pro
consultation is added. This is a DM disposition with no material dissent and requires no
per-result Root acknowledgment. I directly update this direction's RESEARCH standing and topic 4 to
retain demonstrated capability, ordinary tradeoffs and the difference between an evaluated
asset and further learnability. Source is `54c57af8d2e3860f25a278850055a6aa020e5beb`; complete
compact evidence was published at `fbf908d9571268638f573e747edae0b9fffbedba` before cleanup.

<a id="b05-final-cleanup"></a>
### 2026-10-01 — B05 measured cleanup and final publication boundary

The source, full compact result, original terminal records and byte-verified raw locator were
published before removal. Both accepted native processes were absent with exit 0; the same
observer was drained and stopped, and the original result review is fully read above. There
is no live B05 worker, reader, observer, pending advice or selected successor. Read-only
consumer checks found the fleet-adaptation stochastic-target source assessment explicitly
using `b05_score_sampling/policies.py` and its contract. The compact kernel, harness, complete
reader and synthetic checks remain useful and are retained at their existing owned paths;
the reader's source bindings require the complete versioned implementation. Upstream actors,
other directions' live work and all required positive/adverse evidence remain intact.

The supported exact-snapshot collector initially could not inspect another process's cwd
(`EACCES`, pid 660). Its documented `--sudo-process-scan` read-only scan resolved that tool
limitation; preview and apply then proved terminal ownership, no live consumer, published
source and external durable outputs. It removed both the terminal source snapshot and Git
registration. No backup, relocation, archive chain or source rewrite was made.

| Actually deleted target | Allocated bytes before | After | Net reclaimed |
|---|---:|---:|---:|
| wsl_4070 `/home/wu/projects/HMASD/.git/hmasd-launch-sources/3c5fa3efbb72442c9b0325280bde2352` | 813826048 | 0 | 813826048 |
| wsl_4070 `/home/wu/projects/HMASD/.git/worktrees/3c5fa3efbb72442c9b0325280bde2352` | 3608576 | 0 | 3608576 |
| local `/home/fires/hmasd-wsl/temp/directions/uav_fleet_transmission/` — only the stopped B05 observer request remained | 12288 | 0 | 12288 |
| local `runs/uav_fleet_transmission/b05_score_sampling_a01/stdout.log` and `stderr.log` — empty redundant collection copies | 0 | 0 | 0 |

All exact targets were absent after deletion. Remote reduction is 817,434,624 allocated bytes;
local reduction is 12,288 bytes; **combined net reclamation is 817,446,912 allocated bytes**.
No owned Python cache existed to remove. The original empty logs remain with the canonical
remote run. Required raw evidence remains one canonical 416-file copy, 179,862,927 logical /
180,719,616 allocated bytes, at the locator and manifest digest in the complete-reading entry.
Those retained files are evidence, not a cleanup blocker. The unrelated remote Git autogc
warning did not prevent the supported snapshot removal and is not an outstanding B05 cleanup
dependency. No concrete cleanup blocker remains.

The direction returns to reserve with a completed, independently read result and no producer.
Re-entry requires a selected substantive question whose possible answers change a scientific
or use decision; it is not recurring polling or an owner approval fabricated from idle state.
The final publication updates only this notebook, this direction's standing/routing, directly
affected shared topic 4 and the completed selected-plan section. The superseded substantive
plan is retained once in the dated research archive; other directions and owner controls are
preserved.

<a id="post-b05-temporal-source-assessment"></a>
### 2026-10-01 — Source-only assessment of local hold termination; no study selected

Root read and adopted the completed B05 disposition at `175acdfd7`, then assigned one
substantive source-only successor assessment: can lawful observation-triggered early
termination of a four-tick local motion hold preserve useful retained S behavior while
avoiding harmful continued motion or aggregate outages? This is a temporal-control/use
question, not another score/temperature/epsilon fit and not a patch evaluated on world
29630013. No native, policy, model or target query, new outcome reduction, fit, code, fixture,
pilot, profile or launch is authorized or performed. The arithmetic below uses only source
dimensions and previously published cost facts. B05 remains closed. Fleet-adaptation's
separately selected S-prior T/H work is an actual consumer of the retained B05 kernels; its
controls and immutable assets stay untouched. Waiting's allocation replay and the parent's
N8 completion/redecision source question remain separate owned work.

I read current published RESEARCH at `4de05b0da41827cf945587003a2476584dac480e`, especially
topics 2/4 and the completed duration/roster allocation. Their concrete effects are to retain
competent ordinary fast feedback, distinguish native aggregate service from individual
continuity, and price changed control rights separately from learning. Root's independent
`/root/deep_report_review` owns the literature/innovation and selection judgment for this
source assessment; no duplicate B05 result critic or new learning round is opened.

**Actual observation and action interface.** The current native factory is
`experiments/candidates/ucope/uav_motion_prefix_b01/environment.py:8`: N5/U50, H256,
static uniform users, free-space radio, no shadowing, all transmitters on, non-FDMA,
30 metres per axis per one-second tick and clipping to x/y [0,1000], z [50,150].
`MultiUAVEnv.step` moves the five submitted commands, recomputes radio/assignments, computes
the reward, increments the clock and supplies five fresh local rows. There is no acceleration,
inertia, modeled communication delay or source-enforced four-tick command lock. The native
interface accepts changed commands on every primitive tick. A command chosen at time t
controls transition t→t+1; observation at time t reflects the preceding t transitions.
An off-boundary reaction at t=1 cannot prevent the first transition's outage.

Each existing row is 104 FP32 values: three own-position coordinates; 20 ordered user slots
of relative x/y and normalized own-link SINR; 10 ordered peer slots of relative x/y/z and
link SINR; and t/256. User/peer lists contain only links at or above native 3 dB, sorted by
descending SINR with stable index ties; unused slots are zero. User SINR is encoded as
clip((dB+10)/50,0,1), so a valid user slot has a strictly positive third field (at least .26).
Users and peers are anonymous in the row; global identities, team connections, complete
positions and per-user ages are not supplied. High SINR is clipped, and a full 20-user list
does not reveal all eligible users. The environment's `info` contains much richer per-agent
and global diagnostics, but B05's policy boundary passes only that agent's row, own nav,
absolute tick and private randomness. Diagnostic availability is not actor permission.

There is nevertheless a useful exact count deduction specific to this contract. Let P_i
be a UAV's received power at one user and let noise be positive. Eligibility requires
P_i ≥ r(sum of other powers + noise), with r=10^(3/10)>1. Two different UAVs cannot both
satisfy this inequality for the same user. The native all-on, non-FDMA eligible sets are
therefore disjoint; global greedy assignment reduces to each station's top ten eligible
users. The local view contains its top twenty, so

`own_served(t) = min(10, count_nonzero(row[3:63].reshape(20,3)[:,2] > 0))`.

This is a source/algebra deduction, not an evaluated trigger or a new outcome measurement.
It uses slot presence rather than reconstructing a rounded SINR threshold. It determines
the current own connection count, including exact own-zero service, despite censoring.
It neither identifies team service nor says whether a vanished link was handed to another
UAV. Stable user identity/continuous waiting cannot be inferred from this count. The deduction
must not be exported unchanged to FDMA, a different threshold/allocation rule, or a sensor
cap below capacity. The pure radio and assignment source, including its positive noise and
all-other-transmitter interference, was read directly.

**Where the four-tick restriction actually lives.** B05 `collect.py:51–72` receives and records
the intervening observations but invokes policies and replaces held commands/navigation only
at absolute t%4=0. Every episode starts with fresh private policy caches, nearest-waypoint
nav from its own reset row and a zero command before the t=0 query. There is one common
predecision observation snapshot; sequential agent queries cannot see other agents' new
commands before the joint native step.

The restriction is repeated in `b02/controllers._tick`, `FeatureMemo.query`,
`StudentPolicy.query` and `indexed_uniform`; merely changing the collector would fail.
The original `LocalController.act` also ingests a row but only calls `_decide` at t%4=0.
MemoC's `_miss` delegates to that act method. A new temporal wrapper would need an explicit
off-boundary decision entry, not a fictitious t'=4t, a rounded sampling address or a mutation
of these frozen modules. `history=False` C replaces its visible-user set at a query; it has
no persistent unseen-user map. Its model ranks all 27 clipped constant-command four-tick
trajectories using visible users, stationary visible peers and inferred unknown interference.

Both original S actors are feed-forward, with 114 inputs: row[:103], ten-way current nav,
and the original analytic fallback flag. They receive neither clock, held command, remaining
duration nor a recurrent hidden state. The feature/logit cache key is the exact first 103
FP32 bytes plus nav. Deterministic cached values may be reused, but every sampled decision
draws anew. Current `indexed_uniform(root,world,t,agent)` uses a private SeedSequence and
rejects off-grid t; a new version could admit every true integer tick while preserving the
old construction exactly at multiples of four. No new fit is needed to evaluate the immutable
actors, but earlier queries change their deployment/commitment distribution.

Nav changes only when an actual decision's fallback is true and the current waypoint is
within 60m, advancing one waypoint cyclically. The fallback is whether all modeled C commands
have zero service, not whether the current native own count is zero. S's cheaper analytic
helper reproduces that flag/nav transition; it is not a free full C score query. A count-only
gate need not run either helper or full C between decisions. Off-boundary redecision must
apply the existing nav transition once when it actually queries, keep nav unchanged on a
continued hold, and never reset navigation/history because of an interruption. The held
command remains private own state. These details also apply to C/Q/G under any new right.

A source-feasible query adapter can preserve the exact four-step score kernel: on a C miss,
set the private original controller's nav, parse the current row, call its history-false
`_ingest(xy, actual_t)`, then call `_decide` directly instead of the cadence-dispatching `act`.
Recover the original command/scores/served/fallback/next-nav and use the same exact memo key.
This creates no new physics or score law and avoids falsifying the clock. On a student miss,
call unchanged `analyze(row,nav)` and the same one-row FP32 actor; query-hit behavior retains
fresh draws. Synthetic boundary equivalence, private-state/cache restoration, exact nav and
draw addresses would need verification if implemented. This is a proposed adapter route,
not tested code or permission to edit the shared/frozen kernels.

**Prior evidence changes the proposal.** [UCOPE B10](../ucope/NOTES.md#2026-09-21-0554-utc--b10-complete-real-paired-credit-does-not-earn-a-retained-policy-gain)
already tested actual held-velocity KEEP/END choices, every-tick observations, ordinary fresh
feedback and paid real alternative suffix credit. Nine gate fits / 4,915,200 ticks gave mean
R_CF−ordinary G J −.0000731732 and failed its original investment rule; positive/negative
branch effects and deployment exceptions remained. This rules out presenting another adaptive
termination head or cleaner-credit repair as a new rationale. Its max-two-tick deterministic
recurrent foundations differ from these useful categorical four-tick S/C/G laws, so it does
not empirically settle this zero-fit cadence-use question. The distinction is the retained
capability and actual control contract, not an assertion that UCOPE lacked feedback.

The [completed duration/roster review](../../archive/2026-09-30/RESEARCH-duration-roster-allocation.md)
declined another purchase, retained ordinary feedback and required a substantive commitment
reason. Our own [N8 temporal comparison](#b04-complete-reading) and
[unselected completion-timing assessment](#post-b04-source-only-design) concerned long,
multi-agent relocation plans and report-aligned redecision; they provide neither an N5
effect size nor permission to extend those operations. Their local-positive/complete-negative
and anticipation evidence make full trajectory consequences essential here.

[Registered-service B02](../uav_registered_service/NOTES.md#b02-complete-reading) retained a
service/path gain while adding seven missed obligations and longer closed gaps; false model
completion alone did not explain all losses. [Service-age B01](../uav_service_age/NOTES.md#b01-complete-reading)
retained ordinary W/M and the learner's own-initialization gain, but lawful age was already
represented in a long adverse gap and L1 lost mean age to both references.
[Waiting B04](../uav_user_waiting/NOTES.md#b04-complete-reading) satisfied its modeled service
floor at every decision without establishing complete service preservation; useful U's
extreme-tail gains carried service/quality/compute costs. These used richer map/report/mask
contracts and cannot be transferred as N5 local policy scores. They directly weaken any
argument that an observed own-count drop, a local floor, or a higher p10 certifies continued
motion is harmful or protects individual users.

**Feasible candidate, with a narrower question.** The most coherent version to cost is
opportunistic same-policy redecision after a local service loss, compared with ordinary
every-tick feedback. Its intended contribution would be task use/empirical understanding:
does limited extra feedback preserve useful committed stochastic behavior at less query
cost than full feedback? It is not an outage shield or a learned termination method.
Source evidence establishes feasibility and a real local signal; it does not establish that
holding caused B05's outages or that this proposal will improve native value.

**Initial DM source proposal, preserved.** One possible extra query per agent per original
four-tick block: at b=0,4,…,252, query the parent and record s_i(b). At the first off-grid
t in that block with s_i(t)<s_i(b), query the SAME parent once from its actual row/nav and
actual-tick uniform; hold the replacement through b+3. Spend the extra query even on the
old category or a physical alias. Mandatory renewal remains b+4; no same-tick retry,
zero-motion rescue or threshold tuning. This initial proposal used a block-start count and
was source reasoning, not a tested or selected controller.

**Final prospective revision from the independent Oracle; still unselected.** Retain the
one-extra-query budget, but trigger on s_i(t)<s_i(t−1) from CONSECUTIVE fresh observations
at off-grid t, while the extra is unspent. I accept the source-based correction: a contact
first gained mid-hold and then lost is missed by a block-start/last-query-zero reference.
This reasoning uses no outage trace. Every agent stores one previous-count integer, updated
from the fresh row EVERY tick, including after the extra was spent and at mandatory boundaries.
Reset has no previous sample and performs the mandatory t=0 query. At t%4=0 query exactly
once, reset the per-block extra-used flag and do not add a second query for a simultaneous
count drop. On an off-grid event query the same parent once, apply its nav update once,
consume a fresh actual-tick uniform and spend the extra even when action/geometry is unchanged.
Hold that replacement until the next absolute boundary. There is no rolling deadline restart.

Thus the final E has at most one extra query per agent/block and at most one query per
agent/tick; an initially zero count can rise and then fall before expiry and trigger. The
Oracle briefly considered an uncapped event variant during the live source exchange, but
its final prospective recommendation retains this economy budget. The capped bill below
applies to the final consecutive-count rule. No version was implemented, queried or run,
and Root has not selected a result study.

H4 keeps the original four-tick program. H1 queries the same parent every primitive tick.
Both provide necessary comparisons: E−H4 tests added event feedback; E−H1 tests whether its
selectivity/commitment buys value or lower cost relative to ordinary fast renewal. More query
times also change stochastic persistence and nav opportunities, so this is the complete
cadence package, not pure causal value of observation content. H1 redraws the original law
on every actual query; its per-query epsilon/temperature is unchanged. Neither a new
exploration-hazard conversion nor repeated use of a block's uniform is silently substituted.

C/Q/G receive the same E and H1 rights, the same row-count gate and own memory, and pay their
full score queries when they redecide. Ordinary Q05 and Q10 both remain, alongside fixed G
and C. C/G keep their existing four-step local lookahead even when the issued replacement
lasts one to three ticks; H1 is receding four-step lookahead. S keeps its original four-step
trained law with the same changed execution duration. This explicitly separates forecast
horizon from execution commitment. Late H1/E queries would extrapolate four model ticks even
when fewer than four mission ticks remain, because the inherited time-free law ignores
that boundary; actual execution always stops at H256. A truncated-horizon ordinary law is
a different possible comparison, not an undocumented change to the fixed kernel.

A model-free brake-to-zero would have a lower query bill, but after a loss it can freeze a
poor position and suppress a useful handoff or recovery. A count-loss signal does not predict
which new velocity is better. Using C to override only S would instead add a teacher rescue
package. I would not prioritize either as a supposed safety repair. The original current-only
parents may also forget a just-lost user at requery; no new memory/map is smuggled into E.

**What could change a decision.** For each immutable S lineage, retain E−H4 and H1−H4,
and separately E−H1; compare retained S within E/H1 against matched G, Q05/Q10 and C,
without selecting a per-world best ordinary envelope. Keep the original paid Bstar_L0/T2
at H4 as a practical alternative; Bstar_L1/H4 is exactly S_L1/H4. An event rule that improves
native J/service or relevant outages while remaining economical beyond fast controls would
be a useful conditional package. If ordinary E/H1 captures the gain, retain that ordinary
capability. If H1 matches or improves on E's value at acceptable cost, event selectivity has
not earned a special role. If E changes motion but loses complete value, end the rule; an
observed count drop was not enough to choose a beneficial redecision. Inactive, rare-outage
or unresolved panels would remain valid boundaries without a sweep, extra worlds or a fit.

The intermediate prediction is actual before-expiry redecision with changed remaining motion
on some own-count losses, using at most twice H4's logical policy queries and at most half
H1's. Different visited states/cache misses mean that a corresponding CPU saving is not
established by the query bound and must be read in the complete comparison.
The native conjecture is better retention of service/J with shorter or fewer aggregate
outages, not simply a better local score. Each may fail independently. Complete outcomes
must retain all per-world/tape J, service/p10/minimum, zero-service count and longest zero
run, quality, path/boundary/zero-displacement, query/cache work and CPU/wall. The gate's
eligibility, requests, actual category and remaining-hold physical differences are separate.
No old-outage trajectory, single-step counterfactual or positive activation screen is needed.
Fresh complete trajectories are necessary because joint motion changes interference, later
observations, random redecisions and handoffs. Team outage improvement would still not be
individual continuity; any such additional outcome claim needs actual per-user gaps/ages
read from evaluator connections, never supplied to the gate.

**Complete prospective bill for that candidate; not a launch contract.** A complete exploratory
panel could use 32 fresh worlds, two private stochastic tapes, immutable S_L0/S_L1 and the
four ordinary C/Q10/Q05/G laws, each under H4/E/H1. Each deterministic C mode needs one
episode/world; the other five laws need two. That is 33 episodes/world, plus two Bstar_L0/H4
episodes: **1,120 H256 episodes / 286,720 native transitions / zero new fits, training labels,
optimizer calls or calibrations**. No seed range is reserved by this assessment. The original
29630000 panel is excluded as a new final panel; actual fresh seeds and fixed contrasts belong
to a later selection. Both inherited fit histories and paid calibration costs remain incurred.

| Work in the proposed complete worker | Source-derived count or ceiling |
|---|---:|
| Policy queries per H4 / E / H1 episode | 320 / at most 640 / 1280 |
| Ordinary C/Q/G queries, before memo savings | at most 501760 |
| Student queries including the paid H4 reference | at most 307200 |
| Total queries / indexed stochastic draws | at most 808960 / 737280 |
| G score-tail probability constructions | at most 143360 |
| Ordinary candidate trajectories / modeled ticks | at most 13547520 / 54190080 |
| Ordinary candidate / setup radio links | at most 1083801600 / 50176000 |
| Student analytic setup+extreme links / one-row forwards | at most 43008000 / 307200 |
| Potential off-boundary E gate checks | 337920 |
| E own-count decodes, including block starts | 450560 (9011200 slot-presence comparisons) |
| Native explicit resets plus factory reset | 1120 + 1 |
| Native dense radio power slots, including resets | 79156275 |

The radio ceilings deliberately assume every query is a miss with 20 users and four peers;
they are conservative and do not assert that all agents can simultaneously attain that
geometry. The gate itself uses no analytic helper, full C, actor or shadow rollout. All
1,433,600 scored observation rows already come from native steps; their 104-float payload
is 596,377,600 bytes before compression. This is an in-process data volume, not a claimed
radio transmission budget. There is no modeled sensor energy or physical processing delay;
additional gate/query CPU is measured and cannot be called free deployment sensing.

The full reader must reconstruct the variable decision/hold/nav state machine from every
saved row, independently recover own counts and actual native connections, replay every
ordinary decision on its actual history, reconstruct every S helper and one-row actor output
(including deployed cache hits), and check all distributions/absolute-tick addresses,
physical aliases, native metrics and paired contrasts. It adds the same worst-case ordinary
model work and up to 307,200 actor rows, plus all native-array reductions, with zero new
environment steps. The source count proof should receive focused synthetic checks and the
new scheduler/RNG/replay path independent engineering review if selected; none is run now.
All trigger bookkeeping, storage/compression, bootstrap/readback and asset/source verification
belong in the bill, not just neural inference.

B05's published 140.041 enclosing CPU seconds for 416 episodes supplies a scale, not a timing
prediction for new off-grid cache/geometry regimes. The new panel has 2.69 times its native
exposure, up to seven times its ordinary requests and five times its full-reader student rows;
full-C misses and link work can grow further. Allow roughly **5–20 worker plus 3–15 reader
CPU minutes (8–35 combined)**, **6–10 active support hours** for implementation/checks,
independent engineering review, scientific reading and publication, **0.7–1.3 GB canonical
raw**, **1–2 GB temporary accepted-source snapshot**, and **0.6–1.2 GiB process memory**.
These are uncalibrated planning estimates, not hard runtime bounds or resource admission.
No remote profiling/repair is needed for this source task; the known GCC recurrence remains
a separate actual-launch consideration. No backup or duplicate raw-retention chain is priced.

Selected inherited evidence through closed B05 has already incurred eight fits, two paid
calibrations, 1,794,048 native transitions and 2,483.157 measured CPU seconds under differing
timing scopes/hosts; older UCOPE/N8/parent/count branches and unmetered support remain
separate sunk costs. If this full candidate later completed, the selected inherited native
total would become 2,080,768 with the fit/calibration counts unchanged. A learning gate or new
actor fit is not justified by the source question and is not hidden in the estimate.

**Recommendation to the allocation review.** The interface supports a genuine, inexpensive
local service-loss trigger with no new observation field. It requires a new temporal control
and query contract, and a complete matched fast-feedback comparison. I recommend this
bounded zero-fit cadence-use formulation over an outage-shield claim, a brake-only repair or
another termination learner if Root chooses to buy the temporal question. I do not infer that
the added right is likely to help from the B05 outage witness, or recommend spending without
the ordinary H1 comparison. Declining this purchase is scientifically defensible given UCOPE's
negative development history, the lack of evidence that four-tick holding caused the losses,
and the support bill; it would not refute early feedback or close the retained-control question.
Root's ongoing independent allocation review compares that value with the separate N8 source
candidate. This note completes the authorized source answer and selects no result operation.

The load-bearing current code bytes are recoverable at the published revision above and the
unchanged B05 source `54c57af8d`. SHA256: native environment `fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e`;
pure radio `db3464803b1a5aa9c9504096810dc971266a6bd7eba1c31dfe79e7d8d903f3cc`;
adapter `8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40`;
original C `b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2`;
fleet helper/MemoC `a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522`;
fleet policies `fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd`;
B05 collector `d5b0fd092eab4ef10c617aee2622a97c14c6af178fedf22f277f27599478b044`;
B05 kernel `b6a018614df3ee4e32d41d6fd5550850deb8bfe0ec02cf53b6b5efd1291bb986`.
Only source/records and static count algebra were inspected in this assessment. No old raw
array was reduced and no policy/model/actor/environment was imported or queried.

<a id="b06-prospective-cadence"></a>
## 2026-10-01 — B06 selected: complete use of retained policies at H4, loss-triggered E and H1

Root selected this bounded comparison on 2026-10-01 01:20 UTC after reading the full source
assessment and independent Astra Max advice. This is the sole active result study in this
direction; B05 remains closed. The question is whether changing commitment/query timing
improves the complete native usefulness of retained categorical S assets, relative to equally
enabled competent ordinary policies and to every-tick feedback. It is a task-use and empirical
cadence question, not a new termination learner, an outage protection guarantee or a novelty claim.

I read the COMPLETE original independent answer from `/root/deep_report_review` before
implementation. Root preserves the complete original cross-question prompt, material correction
and full answer once in [the canonical temporal-use/planning-economy review](../../archive/2026-10-01/RESEARCH-temporal-use-and-planning-economy.md).
I adopt the N5 recommendation without material dissent. The consecutive-tick comparison corrects
my initial block-start signal because a contact can be acquired then lost inside one original
block. The one-extra-query bound retains the agreed fixed scope. The source proof establishes
own served-count truth under this host; it does not give the sign of a redecision's team effect.
S_L1's retained B05 gain makes useful policy deployment worth testing, while UCOPE's adverse
termination-learning history rules out treating interruption as a newly discovered learning
opportunity. The original B05 outage world establishes neither a cause nor a design panel.
The selected comparison pays for H1 and ordinary E/H1 so a useful ordinary or fast-feedback
result can change the practical choice. Sparse activation, unresolved effects or adverse
outcomes can end this purchase without a fit, threshold search or expanded world panel.

Relevant published-main background topics 2 and 4, the duration review, prior UCOPE/B02/
service-age/waiting evidence and their concrete implications are already read and linked in
[the source assessment](#post-b05-temporal-source-assessment). Those unchanged readings apply.
The latest topic-4 B05 revision retains conditional S capability beyond G, ordinary G tail/
quality/path tradeoffs and all outages without adding training units. This design changes lawful
temporal control/query opportunities; it adds no observation field, identity, global service,
future observation, training label or actor feature. Extra sampling/nav opportunities and changed
visitation remain competing explanations of any complete package effect.

**Fixed intervention.** Native N5/U50, all-on/non-FDMA, threshold 3 dB, capacity 10, H256.
At each E tick let `q_i=min(10,count(row[3:63].reshape(20,3)[:,2]>0))`. This equals own native
served count by the positive-noise/non-FDMA uniqueness and capacity argument already recorded.
At absolute `t=0,4,...`, query the same parent once, reset the extra-used flag, and never make a
second query for a simultaneous count loss. At `t=4k+1,4k+2,4k+3`, query once if the current
count is smaller than the preceding native-tick count and this block's extra is unused. Spend
the extra even if the selected category or physical remaining hold is unchanged. Update the
previous count EVERY tick, including block starts and after the allowance is used. Hold a
replacement only until the original next boundary; there is no rolling restart or rescue action.
H4 queries only on the original grid; H1 queries every tick. All laws reset private state at
episode start. The first loss can be observed only after its transition; no first-tick protection
is claimed. A local loss can be a useful handoff or can remove a contact from current-only input.

**Frozen panel and random addresses.** Object `UAV-CADENCE-USE-B06`, implementation directory
`experiments/candidates/uav_fleet_transmission/b06_cadence/`, intended run
`runs/uav_fleet_transmission/b06_cadence_a01/`. Fresh world seeds are the 32 integers
`29670000..29670031`; master seed `29670100`; private action-tape roots `29670101,29670102`;
actor-constructor seeds `29670111,29670112` (forked initialization only, overwritten by immutable
S tensors); paired bootstrap seed `29670191`, 10,000 resamples and percentile 95% intervals.
These addresses are fixed before any query or outcome. No old outage world is selected.
For each world, list parents `C,Q10,Q05,G,S_L0,S_L1` in that order, each mode `H4,E,H1`, each
stochastic tape `0,1` (C once with tape -1), then `Bstar_L0/H4` tapes `0,1`. Rotate this 35-cell
list left by world-index modulo 35. This deterministic cyclic ordering is fixed prospectively.
`Bstar_L1/H4` aliases `S_L1/H4`; no Bstar E/H1 episode is selected. C/Q/G scoring always forecasts
four ticks, even when executing only one to three remaining ticks. Late H1/E queries still
forecast past the native mission end; shortening that model horizon would change the parent law.

The complete purchase is EXACTLY **1120 H256 episodes / 286720 native transitions / zero new
fits, optimizer updates, training labels or calibrations**. Every parent/mode receives the same
lawful count memory and query rights. Fixed Q epsilon values .10/.05 and G tau .014 are inherited.
Original S/Bstar tensors and paid Bstar temperatures are immutable. Both stochastic tapes use
the actual address `(root,world,actual_tick,agent)` independently of cache hits; a new owned
uniform function extends the original SeedSequence law off-grid without pretending the tick is
another boundary. Actor computation remains one-row FP32; feature width/order stays 114 and
clock, held category, count history and remaining duration are not fed into S. Episode-private
caches store decisions/features/logits, never sampled actions. Original C/history=False is
ingested at the real tick and `_decide` is invoked directly by the owned adapter. Navigation
advances exactly once per actual query under the existing full-C fallback rule.

**Predictions and complete reading.** Primary within-lineage contrasts are `S_Lx/E−H4` and
`S_Lx/E−H1`; also read H1−H4 for each parent and every same-mode S versus C/Q10/Q05/G comparison.
Read paid Bstar_L0/H4 against S_L0/H4 and each S_L0 deployment as an available-use reference.
No per-world winning-ordinary selector is created. Average the two tapes within each world;
bootstrap paired WORLD clusters with the same indices across endpoints and contrasts. Intervals
are conditional/descriptive across 32 worlds, not training-population, individual continuity or
reliability inference. Read J, served count, served-user quality, service p10/minimum, total
zero-service ticks, longest zero run, path and complete query/CPU costs together. Inspect every
adverse world, not only mean or outage witnesses. Preserve all B05 and inherited adverse evidence.

Keep eligible off-grid count losses, allowed extra queries, changed categories and changed
remaining clipped physical holds as SEPARATE quantities. The physical counterfactual is only
an exact command-geometry comparison from the same starting position to the next original
boundary, not a native reward counterfactual. E's intermediate prediction is selective extra
queries with some changed remaining motion; its native consequence must still be measured.
If E retains useful complete value with favorable full cost relative to H1, retain that conditional
option. If ordinary E/H1 captures the value, retain the ordinary capability. If H1's tradeoff is
preferable, retain fast feedback. If E harms complete outcomes, stop this rule. Sparse or
unresolved findings authorize no automatic tuning or additional purchase.

**Full cost.** The accepted source-derived ceiling is 808960 worker queries: 501760 ordinary
and 307200 student, with 737280 indexed draws, 143360 G distributions, 13547520 ordinary
trajectories/54190080 modeled ticks, 1083801600 candidate and 50176000 setup links, at most
43008000 student helper links and 307200 one-row forwards. E adds 337920 off-boundary gate
checks and 450560 count decodes/9011200 slot tests. Native resets are 1120 explicit plus one
factory reset; dense native radio slots total 79156275. Full reading independently reconstructs
all actual ordinary queries, every helper and one-row S output INCLUDING deployed cache hits,
all gate/nav/hold/RNG/native arrays and reductions, with zero additional native steps. Its worst
ordinary/query work matches the worker ceiling. The source counts and costs are detailed in
the preceding assessment; logical saved queries are not assumed to imply measured CPU savings.
Planning estimates accepted by Root are 8–35 combined worker/reader CPU minutes, 6–10 active
support hours, .7–1.3 GB canonical raw, .6–1.2 GiB process RSS and 1–2 GB temporary source
snapshot. These are estimates, not admission or result cutoffs. Inherited selected-chain cost
is 8 fits, 2 calibrations, 1794048 native steps and 2483.157 scoped CPU-s; B06 completion would
raise native total to 2080768 with fits/calibration unchanged. Other branches and unmetered
support remain separate. Extra gate/query CPU and serialization/readback are measured; the
simulator has no physical sensing latency/energy bill to infer from them.

<a id="b06-l0"></a>
**L0 implementation scope.** Deliver a versioned off-grid adapter, the fixed three-mode
scheduler, exact complete panel collector and independently reconstructing reader under the
owned B06 directory and matching tests. Main checkout `/home/fires/hmasd-wsl`, branch `main`;
only the DM edits this notebook and shared standing. Frozen C/G/S/T-H source files stay unchanged.
One bounded Implementer at a time may own only `b06_cadence/policies.py` and its focused policy
tests: preserve full original query semantics while allowing actual off-grid ticks. The DM owns
the gate, contract, assets, collector, summaries, independent reader and runner, with no concurrent
writes to helper-owned paths. No helper index mutation, notebook write, child or result launch.

The adapter returns the B05 diagnostics and private counters using unchanged four-step scores,
one-row actor arithmetic and actual-clock addressed draws. Check old-grid equality on synthetic
contexts, off-grid decision/nav/fallback arithmetic, cache privacy/hit behavior, no sampled-action
caching, category ordering and RNG/global-stream invariance. DM checks count uniqueness/capacity/
truncation, consecutive-tick gate/reset/boundary/one-extra/spent-on-alias semantics, full panel
inventory, synthetic end-to-end saved-data reading and tamper rejection. Tests use managed
pytest scratch. **No native correctness fixture, pilot or profile is selected.** All numerical/
RNG/reader/identity/launch changes receive independent high-risk engineering review before the
DM accepts and publishes exact inputs. Source/asset identities bind old modules and all new
modules; local staging contains only the two exact required S files, digest checked against
their canonical originals. Asset location changes do not change tensors or policy arithmetic.

Execute one admitted worker followed by its complete reader on configured `local_linux`, as
Root selected because the remote GCC recurrence remains unresolved. Use the native launcher,
fresh actual-node memory admission, published exact input SHA and one immutable source snapshot.
Arm deterministic observation on the same accepted handle, keep this native child active, collect
and read without duplicate retry. Technical failure preserves partial exposures and stops that
attempt; it is not a negative scientific result. The full independent scientific diagnosis,
owned standing/background publication and measured exact-target cleanup complete the boundary.
No substantial implementation, result query, fit, model query or native transition has occurred
at the time of this prospective entry.

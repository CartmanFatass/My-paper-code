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

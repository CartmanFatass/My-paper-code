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

# UAV Radio Activation

## 2026-09-29 - B01 Prospective Complete Ordinary Comparison

Lead: native `hmasd-direction-manager` `/root/dm_radio_activation`, parent Root
`01a0e560-4333-7b03-8ff3-759a4add1d9a`, shared main at
`/home/fires/hmasd-wsl`. Selection/routing published at
`07912663779cd5a7604aedaa73d8f8a49e47f57c`; owner pause is lifted and the
direction is exploring. The full Oracle proposal, independent ResearchCritic
return and all four adopted corrections were read in the
[selection archive](../../archive/2026-09-29/RESEARCH-radio-actuation-selection.md).
That review covers this unchanged question and design. No confirmation or
learning claim is proposed, so this prospective notebook is the study contract.

### Question, Evidence and Prediction

Can joint transmitter activation improve complete native service under an
explicit registered static-site map, known propagation, and delayed low-rate
out-of-band telemetry, once retained competent motion responds to the changed
sensing? Does exhaustive search add useful service over greedy removal?
This is a complete ordinary resource-package comparison, not a new scheduling
algorithm, a learner, an optimal flight planner or a battery-saving claim.

Published RESEARCH at `079126637` sections 1, 2, 3, 6 and 8 inform this design:
native consequences and closed-loop value differ from instantaneous score;
current-only C remains a useful ordinary capability after the local-history
B01/B02 results; shared reward does not remove action externalities; and a
nested forecast action set does not imply native trajectory nondegradation.
The local-history B02 complete reading retains mean C J .361943, service
21.7383 and no zero-service ticks on its different 32-world panel, plus its
learning improvements and all losses. Neither C competence under radio silence
nor a general learning failure follows. Radio-placement's S7 ordinary gains and
tail costs are scope-different evidence, not an N5 performance comparison.

The native non-FDMA radio sums every active interferer. Removing one transmitter
can let other links cross the 3 dB threshold, but removes ten-user capacity and
user/peer discovery. The constructive prediction is that interference relief
outweighs these losses in complete J AND service. Serious alternatives are
capacity loss, blind-motion fallback and stale/extrapolated forecasts erasing
the gain, or greedy removal capturing the useful opportunity. Changes in
eligibility/connections/visibility are intermediate readings, not causal proof.
No primary-paper theorem is used as a premise and no novelty claim is made.

### Fixed Design and Cost

Reuse the N5/U50/H256 uniform-static-user factory from
`experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` and unchanged
`LocalController(history=False)` from `uav_local_history/b01/controller.py`:
free-space, no shadowing, non-FDMA, 3 dB, cap10, 27 velocity commands held four
ticks. Native motion, clipping, agent inventory, reward denominator and local
104-float observation layout remain. Each arm's trajectories are endogenous.

A is all-on. G starts all-on and repeatedly accepts the best strictly improving
single removal, stopping at no improvement or one active transmitter. E tests
all 31 nonempty masks. Score is horizon-average native J, tie by service, then
more active transmitters, then increasing integer mask (bit i is UAV i).
Strict G improvement uses that same lexicographic score; an exact J/service tie
cannot remove a transmitter because more-active wins. No score tolerance tunes
decisions. All three have the same resource rights; A leaves recurring traffic
unused. No training, tuning, learner or shadow scientific arm.

Fresh seeds 29305000 through 29305063, paired across A/G/E. Complete 192 episodes,
49,152 native steps, zero fits/optimizer updates. Arm order cycles through all
six permutations in lexicographic order by world index, giving counts differing
by at most one in each position and interleaving arms within every world.
E: 126,976 candidate plans / 505,920 mask-state reductions. G: at most61,440
plans /244,800 reductions. Combined at most750,720 reductions and32,640
predicted geometry snapshots. Retained C adds61,440 decisions,1,658,880 candidate
trajectories and6,635,520 model ticks. Counts are bounds, not runtime estimates.

Configured `local_linux` CPU, one compute thread and fresh4GiB memory-floor
admission. This avoids Claude's remote eight-thread SET-V-b reservation.
One CPU-hour hard batch ceiling (process user+system, including initialization,
rollout, search and output); preserve incomplete resource-limited evidence if
reached, with no scientific prefix conclusion, extension or automatic retry.
Runtime/memory unmeasured; Root's10-18 engineering-hour estimate is conjectural.
Checks/reading/support are separate costs, not unreported scientific fits.

### Public Information, Packets and Clock

Preinstallation is an actual400-byte codec:50 ordered sites, two little-endian
signed32-bit metre coordinates each, rounded nearest/even with `rint`. Equal
rounded positions remain distinct rows. It is a provisioned map, not online
channel truth or measured positioning accuracy. Known propagation/power/noise
parameters are a static application specification. Existing float32 own-position
observation error precedes rounding.

Every t=0,4,...252, after C commits its new command, each UAV encodes24 bytes:
version uint8, agent uint8, hold uint8, reserved uint8, sequence uint32,
report tick uint32, xyz signed16 metres, velocity command xyz signed8, three
reserved bytes. A mask command is16 bytes:version uint8, mask uint8,
hold uint8, reserved uint8, sequence uint32, effective tick uint32, reserved
uint32. Own position comes only from the observation and command only from the
chosen controller output. Decoders validate exact size/version/order/time/hold.
Five reports plus command:136bytes/round, at most8,704 recurring bytes/episode;
400-byte map provisioning is separate. Dedicated2kbit/s effective OOB link:
1,088bits take .544s in a one-second delivery round, leaving .456s computation.

The scheduler timer starts before report encoding/routing/decoding and covers
packet validation, predicted clipped positions, source-owned radio geometry,
every mask/association/score calculation, selection, command encoding and
destination command decoding. It excludes C's already committed motion choice,
static map provisioning, native transition and evidence writing. Check the
deadline before/after bounded geometry and candidate reductions and after
command decoding. An overdue result is discarded entirely: retain the prior
mask, no late queue, no partial-search winner. Record candidates/reductions,
wall/CPU latency and deadline outcomes. Results are conditional on actual host
timing; world intervals do not estimate execution-platform variability.

At state x_t the current mask governs transition t, whose native reward is after
movement at x_(t+1). A timely report's mask arrives only AFTER that reward and
its info arrays are copied, then observations are refreshed for state x_(t+1).
It governs transitions t+1..t+4. The predictor therefore scores positions
x_(t+2)..x_(t+5), native-clipped: first three use the known four-tick held
command, fourth extrapolates across C's next decision. Final t252 scores only
+2,+3,+4. First transition is all-on. Service silence removes interference,
serving/user discovery and peer discovery unless both ends are active. Own
position, motion and OOB reporting continue. Switching has zero EXTRA modeled
energy/guard time; flips/on-time do not establish hardware or battery savings.

### L0 Implementation Scope

Deliver B01 protocol, A/G/E scheduler, complete runner and offline reader under
`experiments/candidates/uav_radio_activation/b01/`, matching tests and runs.
DM owns these files and this notebook. Narrow shared exception: base
`envs/pettingzoo/uav_env.py`, source-owned pure `uav_radio.py`, and focused
`tests/experiments/candidates/uav_radio_activation/b01/test_radio.py`.
The bounded Implementer owns only those shared-radio files/test while assigned;
it has no Git index, commit, notebook, RESEARCH, launcher or scientific execution
ownership. No relay C++/G0/Claude changes. Preserve every unrelated edit.

Core API: opt-in `enable_transmitter_mask=False`, read-only-copy
`transmitter_mask` and `set_transmitter_mask(mask)` with all-on construction/reset.
Validate boolean shape. Both NumPy/reference paths remove muted interference
and eligibility; user discovery absent and peer endpoints both active. Refresh
radio/connections at mask-only changes without resampling a physical channel.
Keep default all-on reward/RNG/observations unchanged. Pure functions accept only
their explicit arrays/scalars, never a live environment: free-space path loss,
masked user SINR, native stable greedy assignment, and base non-paper service
metrics. The environment and scheduler use the same source-owned kernel;
independent tests use scalar source formulas/assignment rather than kernel output
as its own proof. Scalar reference remains independent for parity checks.

Verification: all-on/default/reset behavior, scalar/vector agreement, muted
interference, one-active SNR, capacity/eligibility, both-end peer discovery,
fixed-geometry refresh and preserved RNG; map/report round trips and collision
retention; no hidden information argument; exact +2..+5/final timing, reward
copy before mask arrival, deterministic ties/greedy/exhaustive correctness and
deadline discard including late decode. Test fixtures use separate seeds and
short correctness transitions, not the fresh result panel or a timing pilot.
Obtain independent registered engineering review of the full numerical and
execution changes, then accept the diff/checks as DM. Commit/push exact inputs
and use native launcher/runner admission. No result starts from dirty inputs.

### Reading and Decision

Keep per-world full J/service/quality and paired effects, every negative world,
zero-service counts/longest outages/minimum service, paths and boundary occupancy.
Retain masks, eligibility/connections, forecast errors by known/extrapolated
offset, visibility/fallback, bytes/ages, deadlines/flips/on-time, search work and
resource telemetry. Save compact per-world/paired readings in Git and raw arrays
once at a recorded durable location with hashes. Verify reconstruction offline
without new episodes. Descriptive paired t95 intervals across64 reset worlds
condition on this host and realized deadlines; no equivalence threshold is set.

G/E gains in complete J and service can retain an ordinary conditional capability.
E without a discernible useful increment favors G's simplicity but not equivalence.
Forecast improvement without complete native benefit rejects this package's
usefulness; mostly all-on indicates little opportunity under this package.
Mean gains with new service tails remain a tradeoff. Independently review the
material result/next investment, preserve dissent, and distinguish a tested
package result from the open parent question. No branch automatically purchases
a learner, repair, faster clock, new coefficient, second panel or propagation
variant. Cross-question pivots return to Root. Cleanup checks live consumers,
keeps necessary unique evidence/useful code and reports exact deletion/net bytes.

### Outcome-Blind Implementation Refinements

The first codec/clock test run used only fixture seed713 and8 native steps,
plus synthetic scheduling inputs. Six tests passed and the arm-order test caught
that lexicographic six-permutation cycling gives22/22/20 position counts on64
worlds. Before any result exposure, use two cyclic triples:
AGE, GEA, EAG, AEG, EGA, GAE. Each completed triple balances every position and
the64-world counts now differ by at most one. All six orders remain represented;
this corrects the prospective balanced/interleaved requirement.

For G/E, reports always cost120 recurring bytes; a timely command adds16.
A deadline miss sends no usable command and retains the old mask, so its round
cost is120, bounded by the declared136. Static map decode is one-time setup.
The deadline excludes recorder serialization and receiver radio recomputation
which belongs to the simulated environment arrival, as well as the previously
named exclusions. Candidate-plan counts require all their scored states complete;
partial overdue state reductions remain separately counted. No partial winner
is deployed. Independent correctness checking has no deadline-induced outcome.

### Engineering Acceptance Before Result Execution

The bounded registered Implementer `/root/dm_radio_activation/radio_kernel`
returned the shared base-mask/kernel diff and24 focused tests plus21 existing
path-loss tests. DM inspected the complete diff and source. Author testing of
the whole direction plus `tests/uav_path_loss_cache_test.py` passes54 tests in
1.93s; the final reader assertion refinement passes its five affected tests in
.88s. An earlier misspelled test path ran no tests and was corrected. Pytest
owns/cleans fixture scratch. No result-panel seed or timing pilot was used.

The frozen `tests/uav_env_channel_equivalence_test.py` setup fails its old
reference digest pin on this WSL interpreter: expected `cf389...`, observed
`efc5005140418f88f6d9e1b8f5a701763c2c37a60bf2c7528a8c1e2c0b3da546`.
The Implementer loaded published pre-change `079126637` env/scenario1 source
in memory and obtained exactly the same reference tape/digest as current
reference; current vector/reference tape SINR max difference2.85e-14,
connections/observations/state exact. This is a pre-existing harness limitation,
not a green harness result or a reason to change its frozen pin.

The registered independent Reviewer `/root/dm_radio_activation/engineering_review`
used `fork_turns=none` and the actual contract/source/checks. Full return:

> No material engineering finding remains in the assigned diff. No repair
> requested; acceptance remains with the DM.
>
> Reviewed the shared radio changes and complete protocol -> scheduler ->
> collector -> raw evidence -> reader path. The implementation preserves lawful
> scheduler inputs, delayed mask application, completed-transition evidence,
> deadline fallback, native service semantics, balanced arm order, and admission
> before collection.
>
> Independent checks passed:33 B01 tests, including physical silence,
> stochastic-channel/RNG preservation, codecs, search, deadlines, native arrival,
> observation reconstruction, and incomplete-resource evidence;21 existing
> path-loss tests; in-memory comparison against published079126637:both backends
> x five channel models, reset plus four transitions, with exact SINR,
> connections, reward, observations, state, and RNG equality.
>
> Residual limits: the historical equivalence harness's reported frozen-digest
> mismatch remains unresolved; it is not a passing check. My direct pre-change
> comparison provides narrower independent evidence. No complete scientific
> panel, real SIGXCPU teardown, or execution-platform deadline variability was
> exercised. No source edits, launches, or Git mutations performed.

DM accepts the reviewed diff and checks. The result panel remains unrun at this
acceptance. The actual1CPU-hour hard stop has a mocked incomplete-evidence test,
not a paid1hour signal test; native signal/OS exit facts will remain authoritative.
No scientific selection or comparison changed. Publish exact owned inputs,
then native admission on local_linux; keep this child active through same-handle
deterministic observation, collection and independent scientific interpretation.

### Accepted B01 Operation

Exact inputs published as `4d5ccefe6c90dbc6c132bcc71ffe6dd73535ae47`.
The original native launch was accepted2026-09-29T16:56:11.497004Z; see
[launch manifest](../../../../runs/uav_radio_activation/b01_delayed_masks_a01/launch-manifest.json)
for source snapshot, argv, process identities, output and recoverable handle.
Fresh local_linux admission observed9,006,141,440 effective/physical available
bytes against4,294,967,296 required, passed both floors. No node migration or
duplicate request. The prospective exposure and CPU ceiling are unchanged.

Detached `hmasd_wait` is armed for the original launch under this child's actual
runtime address `01a0ee05-355d-7282-a5b2-73969bc70d36`, using the direction's
private `temp/directions/uav_radio_activation/b01-wait.json`,30s observation
interval and1500s checkpoint window. This native child remains active; queue
registration is not assumed to guarantee a future wake. The scientific result
remains unread until full terminal evidence and reconstruction.

## 2026-09-29 - B01 Complete Reading

### Terminal Evidence and Native Outcomes

The single accepted operation completed with exit 0. Its native manifest,
admission, exit witness and compact summary remain together in
`runs/uav_radio_activation/b01_delayed_masks_a01/`; source is the published
`4d5ccefe6c90dbc6c132bcc71ffe6dd73535ae47`. All 192 episodes and 49,152 native
steps completed, with one constructor, 192 explicit resets, zero fits and zero
optimizer updates. No extension, resumed prefix or replacement launch occurred.

The original observer reached READY in generation 1, event
`4a3911c60d7f8a405e38e9a2`, wake `658750f6-d68a-4d33-bfa0-cf0bca4a45f5`.
Its queue call returned `direct app-server input is not allowed for unloaded
spawned sub-agents (code -32600)`, leaving delivery unknown. This active child
drained that same handle, consumed/rearmed generation 1 and stopped generation 2;
no worker restart or address rebinding. `observer-terminal.json` preserves the
terminal observation, delivery error, rearm and stopped state. The native
supervisor/runner and both observer process identities were absent afterward.

Native per-tick means over the fixed 64 paired reset worlds:

| Arm | J | Served Users | Quality |
|---|---:|---:|---:|
| A | .348125 | 20.820618 | .188787 |
| G | .463134 | 28.217224 | .226975 |
| E | .467518 | 28.601868 | .223640 |

Descriptive paired t95 intervals use reset worlds, conditional on this host and
realized deadline outcomes. They are not training-instance inference, physical
deployment guarantees or an equivalence test. Full precision and all 64 signed
differences for every declared paired endpoint remain in `summary.json`.

| Contrast | Mean J [t95] | Mean Users/Tick [t95] | J Positive/Negative/Tied | Service Positive/Negative/Tied |
|---|---|---|---|---|
| G-A | +.115009 [.099886, .130132] | +7.396606 [6.298708, 8.494505] | 62/2/0 | 61/3/0 |
| E-A | +.119393 [.104491, .134296] | +7.781250 [6.690212, 8.872288] | 62/2/0 | 61/3/0 |
| E-G | +.004385 [.001026, .007743] | +.384644 [.038274, .731013] | 33/13/18 | 31/14/19 |

Mean quality improves for G/E against A, but E-G is -.003335
[-.009771, +.003102], with 17 positive, 29 negative and 18 tied worlds.
Thus the exhaustive increment is not quality dominance. All arms have zero
zero-service ticks and no service outage; observed world minimum service never
falls below 2. G/E each increase mean world minimum by .640625 users
[.334314, .946936], with 21 improved and 43 unchanged worlds; E-G minima are
identical in all 64. These finite-panel facts do not establish safety.

Every world with a J or service loss against A is retained below:

| World | A J | G J | E J | A Service | G Service | E Service |
|---|---:|---:|---:|---:|---:|---:|
| 29305029 | .402082 | .430307 | .414672 | 23.703125 | 25.300781 | 23.167969 |
| 29305030 | .471988 | .461921 | .461921 | 29.742188 | 27.851563 | 27.851563 |
| 29305038 | .473931 | .418562 | .418562 | 30.687500 | 24.976563 | 24.976563 |
| 29305046 | .430941 | .436189 | .465126 | 26.539063 | 24.734375 | 28.218750 |

World 29305038 is the strongest common adverse witness: both schedulers lose
.055369 J and 5.710938 users/tick to A. Both lose J and service on 29305030.
G additionally loses service on 29305046 despite higher J; E loses service on
29305029 despite higher J. Within-episode service p10 falls below A on worlds
30, 38 and 46 by 2, 5 and 1 users respectively, for both schedulers. Keeping
minimum service therefore does not erase all service-tail costs.

E-G has a J or service loss on worlds ending 13, 20, 21, 24, 25, 29, 36, 42,
52, 53, 54, 55, 56, 57 and 61. The largest service loss is -3.613281 on
29305055 (J -.026365); the largest J loss is -.030655 on 29305052
(service -2.656250). E-G service p10 is one user lower on 42, 52 and 61.
These are costs of the actual complete package, not discarded outliers.

### Exposure and Measured Costs

All 4,096 G and 4,096 E rounds met the .456 s computation deadline. Maximum
observed round wall time was .015622 s for G and .039457 s for E. No result
was applied late and no fallback was caused by a deadline miss. Each G/E episode
used exactly 8,704 recurring bytes, 557,056 per arm; the separately provisioned
400-byte map is not recurring traffic. A used zero recurring bytes. Results
remain execution-platform conditional; this panel does not vary host load.

| Work/Behavior | A | G | E |
|---|---:|---:|---:|
| Candidate plans | 0 | 47,559 | 126,976 |
| Mask-state reductions | 0 | 189,525 | 505,920 |
| Geometry snapshots | 0 | 16,320 | 16,320 |
| Mean active transmitters | 5 | 3.445923 | 3.370544 |
| Transmitter-on ticks | 81,920 | 56,458 | 55,223 |
| All-on native ticks | 16,384 | 623 | 298 |
| Mask bit flips | 0 | 2,262 | 1,759 |
| Empty-discovery fallback decisions | 966 | 6,421 | 6,726 |
| Mean visible users/UAV | 4.191528 | 6.181421 | 6.251501 |
| Mean visible peers/UAV | .149390 | .078723 | .062842 |
| Scheduler CPU seconds | 0 | 34.156933 | 80.745294 |
| Episode CPU seconds, arm total | 21.099563 | 59.334796 | 105.577792 |

Actual combined search work is 174,535 plans, 695,445 reductions and 32,640
geometry snapshots, within the prospective bounds. E costs 46.242995 extra
episode CPU seconds over G across the entire 64-world panel, approximately
.72255 s per episode. Its scheduler CPU is 2.36 times G's, but both fit the
declared deadline on this node. More computation is a real cost; a small
absolute cost here is not a guarantee on a different deployment processor.

Mean paths are 2,896.49 / 3,094.24 / 2,773.03 m per UAV for A/G/E.
G-A is +197.75 m with a cross-zero interval; E-A is -123.46 m with a
cross-zero interval. E-G is -321.21 m [-582.39, -60.03], while retaining
20 path increases, 26 decreases and 18 ties. XY-boundary occupancy is
7,787 / 768 / 437 UAV-ticks. Path, boundary occupancy, on-time and switching
are behavioral/resource readings, not energy, battery-life or safety outcomes.

The entire scientific runner used 188.334892 s wall, 188.099280 s CPU
(.052250 CPU-hours), and 127,804 KiB peak RSS, with all configured compute
thread variables set to 1. This includes process imports, initialization,
rollout, search and output and is below the one-CPU-hour ceiling. It excludes
tests, offline reconstruction and independent review. Engineering/review labor
was not instrumented; the original 10-18 hour conjecture is not an observed
cost. The offline reader's measured cost and verified evidence are recorded
below when its same process completes, without new environment steps or fits.

### Complete Reconstruction and Intermediate Reading

The original offline reader completed with exit 0 and empty stderr:
`reading.json` is `VERIFIED_COMPLETE`, bound to the exact source above and
summary SHA256 `340748720f773f0dc79a91cd805f868f31139088bdfaba9b67d237a8b6c49363`.
It verified all 192 raw files, 20,661,922 bytes, exact fixed panel/arm order,
seeded geometry, map and packet bindings, native clipped motion, all masks and
their timing, candidate scores/selections, native connection/reward records,
observations and complete retained-C command/counter replay. Maximum reward
reconstruction error is 5.55e-17; SINR and observation errors are zero on this
reader. Shared-kernel agreement is not its own independent numerical proof:
the engineering reference/scalar checks and Scientific Reviewer's independent
scalar subset below provide that separate evidence.

Reconstruction cost was 984.845498 s wall / 984.608592 CPU-s, 731,000 KiB peak
RSS, with zero new environment steps or fits. Native collection plus this
reader is 1,172.707872 measured CPU-s (.325752 CPU-hours), excluding tests and
independent review. Reader time is support cost, not part of the prospectively
bounded native-result worker; it was not silently omitted from total investment.

On G/E's respective recorded forecasts, selected predicted J improves over
all-on by .098360/.113452 per round on average. At their respective actual
positions, the masked-minus-all-on J differences are .097522/.112979 per tick.
G gains 175,025 eligible UAV-user-time links and loses 38,213 relative to all-on
at those same positions; E gains 195,028 and loses 38,932. Connection-bit
changes number 173,920/193,797. These comparisons locate interference/capacity
exposure; they do not hold future sensing/motion fixed in a complete A-world
counterfactual and cannot decompose the observed complete treatment effect.

Mean Euclidean position prediction errors in metres, G/E respectively:

| Scored Offset | G | E |
|---|---:|---:|
| +2, first held-command state | .368796 | .370410 |
| +3 | .368215 | .369832 |
| +4 | .368031 | .369643 |
| +5, extrapolated across C's next decision | 18.614865 | 15.797691 |

There are 20,480 UAV forecasts per arm at each held-command offset and 20,160
at +5; maximum +5 error is 85.458831 m. Submetre held-command error is
consistent with the declared coordinate quantization, not measured positioning
accuracy. Mean signed actual-minus-predicted J is near zero at +2/+3/+4
(absolute mean at most .000143); the largest absolute individual error there
is .012649. At +5, signed mean errors are +.005169/+.003026, with maximum
absolute .099208/.051538. Signed means do not measure absolute accuracy.
The extrapolation limitation is therefore active even though it did not erase
the average complete benefit. Applied report ages are 1-4 ticks, mean 2.494118
over 16,320 affected transitions per arm; the final truncated round is retained.

The sole canonical bulk evidence is the 192 files under
`/home/fires/hmasd-wsl/runs/uav_radio_activation/b01_delayed_masks_a01/raw/`
on configured `local_linux`. Each path, byte size and SHA256 is in the compact
summary. This maintained shared-main output directory is not a disposable
authoring checkout; preserve this one necessary evidence copy, not another
archive or retention package. `reading.json` preserves per-world diagnostics
and all paired endpoints in Git alongside config/manifest/native status.

### Independent Scientific Diagnosis

Registered `hmasd-research-critic` `/root/dm_radio_activation/result_diagnosis`
ran in a separate context with no DM/Root conversation inheritance. It received
the actual question, original supporting/adverse records and completed evidence,
not a DM-preferred explanation. Its complete scientific return follows, with
formatting normalized:

> Recommend retain both G and E as conditional ordinary capabilities, with E
> the higher-service reference on this tested platform, and purchase no further
> study now. B01 supports the provisioned package; it does not establish
> universal nondegradation, hardware usefulness or a reason to add learning.
>
> I received the bounded assignment, governance and shared background, without
> the DM/Root conversation. I reconstructed the endpoints and raw evidence
> before reading the full Oracle/Root selection archive. No DM result
> interpretation was supplied.
>
> The complete native results support the prospective positive prediction:
> G-A J +.115009 [.099886, .130132], service +7.396606 [6.298708, 8.494505];
> E-A J +.119393 [.104491, .134296], service +7.781250 [6.690212, 8.872288];
> E-G J +.004385 [.001026, .007743], service +.384644 [.038274, .731013].
> These are paired reset-world descriptions conditional on this host and
> realized timing, not training replication or platform uncertainty.
>
> Both schedulers improve J in 62/64 worlds and service in 61/64. Preserve
> the adverse cases: both lose J/service on worlds 29305030 and 29305038;
> the latter loses .055369 J and 5.710938 users/step. G additionally loses
> service on 29305046; E on 29305029. E-G has 13 J losses, 14 service losses
> and 18 exactly matching complete trajectories. Its mean quality difference
> is -.003335, with an interval crossing zero.
>
> There are no zero-service ticks in any arm, and within-episode minimum
> service never worsens against A. That does not erase lower sustained
> service in the adverse worlds. G-A mean path length rises 197.75 m/UAV;
> E-A falls 123.46 m, both with intervals crossing zero. E-G falls 321.21 m
> [-582.39, -60.03]. Neither path nor transmitter-on time establishes
> battery savings.
>
> The intervention was extensively active: G/E selected non-all-on masks in
> 3,955/4,037 of 4,096 rounds. Mean active transmitters were 3.446/3.371.
> Fallback decisions increased sharply, mostly at muted UAVs, while mean
> visible users increased. Thus nonactivation cannot explain the result;
> silence changed both useful radio service and subsequent motion.
>
> The strongest supported explanation is ordinary control exploiting the
> declared map, known propagation and activation rights. This is a useful
> resource-package result, not an isolated value of information, a learning
> result or evidence that C is optimal. The predicted capacity/sensing/delay
> losses did not erase average benefit.
>
> Conversely, forecast containment supplies no trajectory guarantee. My
> independent reconstruction of world 29305038 finds masked radio improves J
> by .081003 and service by 5.007813 against all-on at its own recorded
> positions, yet its complete trajectory loses A. This demonstrates the
> consequential distinction; it does not isolate sensing loss, capacity or
> the controller objective as the unique cause.
>
> E's increment should not be dismissed as absent. On E's recorded forecast
> tables, exhaustive search exceeds reconstructed greedy J in 536/4,096
> decisions. E costs an additional .727943 CPU seconds per episode, about
> 11.37 ms per report round. No deadline was missed; maximum E latency was
> .039457 seconds against .456 allowed. Retain G as the cheaper alternative
> and E as the stronger conditional reference, without asserting a universal
> practical preference.
>
> I checked all 192 raw hashes, seeded initial geometry, map/report/command
> bindings, delayed masks, reward/components/path summaries and all 8,192
> scheduler selections. Ten consequential source files match the executed
> snapshot and 4d5ccefe exactly. Independent radio arithmetic and association
> matched 3,840 frames covering positive and adverse worlds. I did not repeat
> the full C/observation replay; the DM's ongoing reader must supply its
> eventual terminal witness and cost.
>
> Actual collection cost is 192 episodes, 49,152 native steps, zero fits;
> 188.335 s wall, 188.099 CPU seconds, 127,804 KiB peak RSS. Engineering/support
> costs remain incompletely metered. Hardware positioning, channel mismatch,
> link reliability and switching costs remain outside the evidence.
>
> No unchanged replication, faster clock, coefficient adjustment or learner
> presently answers a named unresolved investment choice. A concrete future
> comparison could test one initial report with a permanently held mask
> against rolling E, if recurring-link provisioning becomes consequential:
> 128 complete episodes/32,768 steps/zero fits at 64 fresh paired worlds.
> Preserved service would support cheaper provisioning; losses would support
> recurring feedback; mixed tails would retain a tradeoff. Its runtime and
> engineering cost are unmeasured, and E changes its initial mask in 58/64
> current worlds, so equivalence cannot be inferred. That comparison is
> unselected; the present recommendation is retention and no additional
> purchase.
>
> MATERIAL_DISSENT: no. The evidence supports conditional retention and
> stopping additional investment now; it does not support discarding E's
> observed increment or expanding the claim beyond the frozen package.

The review's .727943 s E-G cost is the scheduler-only mean, whereas the
.72255 s above is the complete-episode mean. These are different scopes, not
conflicting timing estimates. Its independent scalar subset had maximum SINR
error 3.55e-14 and J error 1.67e-16. The reader subsequently completed all
C/observation replay as documented above, satisfying its remaining technical
dependency. No material dissent or scientific correction remains unresolved.

### DM Interpretation and Investment Decision

Accept the independent recommendation. The constructive prediction survives a
complete endogenous-motion comparison: ordinary activation produces substantial
conditional mean J/service value, even with more empty-discovery fallback,
muted-user/peer discovery and fallible +5 forecasts. This establishes the
complete provisioned package's usefulness on the fixed free-space panel, not
an isolated interference mechanism, optimal motion, radio-only causality or
general value of information. Capacity/sensing/delay loss remains a real adverse
alternative in individual worlds, especially 29305038; it no longer explains
away the observed average benefit.

The simpler hypothesis that greedy removal captures all useful service is
weakened, not replaced with E dominance. E has a small positive declared
complete increment and low absolute observed latency, while losing to G in
13 J/14 service worlds and having lower mean quality. Retain E as the stronger
conditional J/service reference for this matched contract and G as a cheaper
ordinary alternative. Preserve both programs and the opt-in shared kernel;
future compatible method comparisons should not claim an ordinary-control
advance by beating only all-on. This is retention of demonstrated capabilities,
not deployment certification or a learner-selection argument.

The batch is exploratory, not confirmation. No new claim-wide confirmation,
unchanged replication, extra panel, faster clock, coefficient, channel variant
or learner is selected. A larger fresh panel would refine recurrence and the
small E-G effect but would not itself address unmodeled hardware/link costs.
The critic's one-report held-mask comparison is the clearest in-question
continuation: it could change an actual recurring-link provisioning choice,
with a cheaper matched ordinary comparator and complete native endpoint.
Its 128-episode/32,768-step/zero-fit cost is prospective, not authorized work;
engineering/runtime costs are unknown and recurring-link minimization is not
a currently requested decision. Do not run it merely because native collection
was inexpensive. Changing hardware/channel premises would require a concrete
deployment contract and renewed focused design review; cross-question choices
return to Root.

Accordingly the current study is complete, the direction becomes reserve with
no active producer, unread result or selected next batch. A concrete re-entry
condition is a use decision that values recurring-link cost enough to select
the held-versus-rolling comparison, or a separately specified deployment
contract that tests whether the retained capability survives its actual costs.
This is a justified stop in additional investment, not a refutation of the
broader radio-control question or an owner-approval dependency. Publish own
standing and directly affected shared background, then retire only unused
snapshot/scratch and redundant logs while keeping unique evidence and the
useful implementation.

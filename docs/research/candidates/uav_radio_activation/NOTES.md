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

### Publication and Measured Cleanup

Full compact results, reconstruction, scientific diagnosis and own RESEARCH
standing/background/routing were published at `46fa68117`. Subsequent peer
commits retain that result as an ancestor. The useful base-radio kernel and
opt-in mask remain shared; retained protocol/scheduler/collector/reader and
focused tests remain the executable definition of G/E and their evidence.
Import/test/entrypoint inspection found those live code relationships; no
unneeded replacement implementation or cross-direction file was removed.

After both native processes, both observer identities and the reader had
terminated, and after the independent Reviewer had finished its snapshot
inspection, the exact source snapshot was collected by the supported
`scripts/hmasd_snapshot_gc.py` preview/apply path. First unprivileged preview
refused because `/proc/383/cwd` was permission denied. The documented
`--sudo-process-scan` read-only process inspection then passed: terminal native
identities, clean source, no process references and durable `refs/heads/main`
reachability. Apply removed only
`.git/hmasd-launch-sources/ad114b6707d14961a2fcf76e33dd8cee`; operation claim,
manifest, exit witness, original source commit and all results remain.
The refusal was an inspection limit, resolved without bypassing the check.

Allocated bytes measured with `du -s -B1` before deletion:

| Exact Deleted Target | Allocated Bytes |
|---|---:|
| `.git/hmasd-launch-sources/ad114b6707d14961a2fcf76e33dd8cee` | 1,642,831,872 |
| `temp/directions/uav_radio_activation/`, containing only retired `b01-wait.json` | 8,192 |
| `experiments/candidates/uav_radio_activation/b01/__pycache__/` | 61,440 |
| `tests/experiments/candidates/uav_radio_activation/b01/__pycache__/` | 53,248 |
| `runs/uav_radio_activation/b01_delayed_masks_a01/stdout.log` | 24,576 |
| `runs/uav_radio_activation/b01_delayed_masks_a01/reader.log` | 12,288 |
| Same run's empty `stderr.log` and `reader-stderr.log` | 0 |

All eight targets are verified absent; the source is absent from registered
worktrees. Net allocated reduction over this exact cleanup target set is
**1,642,991,616 bytes**, from that sum to zero, with no copied retention tree,
tarball or backup chain. This is working-tree target reclamation, not a claim
about Git object storage or free space on a concurrently written filesystem.
The two nonempty logs only repeated row progress now preserved in complete
summary/reading records. Both stderr files were empty at verified completion.

Required raw evidence remains at the canonical path above: 20,661,922 content
bytes / 21,049,344 allocated bytes, with all 192 digests verified. The compact
native records preserve process and observer history after scratch deletion.
No cleanup blocker, active worker/observer, unread result or pending scientific
decision remains. No other direction's snapshots or caches were swept.

## 2026-09-29 - B02 Prospective Joint Motion and Activation

Lead: new native `hmasd-direction-manager` `/root/dm_radio_joint_control`, parent
Root `01a0e560-4333-7b03-8ff3-759a4add1d9a`, shared main. Selection, exploring
state and routing are published at `64eccccb24136ea5ea6fb3ca7df6a70b39203410`.
The former B01 child is fully complete; inherit this same direction, useful
C/G/E code, positive/adverse evidence and cost, with no adopted live operation.
Owner pause is lifted here; other direction pauses and accepted work are unchanged.
The complete [Pro question/answer, focused independent review and Root decision](../../archive/2026-09-29/RESEARCH-radio-capability-innovator.md)
have been read. Root resolved Pro's material dissent against no further purchase
by selecting this changed comparison with all four reviewer corrections. This
completed selection review applies without a new review or positive pilot.

### Question and Fixed Comparison

Can useful ordinary joint motion-and-transmitter activation extend retained
C+E beyond competent coordinated sequential control under explicit delayed
motion commitments? The target is conditional task usefulness and empirical
understanding, not learning, novelty, pure coordination causality or hardware use.
Published RESEARCH at `64eccccb2`, background sections1/2/6/8, concretely motivates
retaining C+E, giving S the same new rights as T, and reading complete native J
AND service rather than forecast containment. B01's E-A +.119393J/+7.781250users
and E-G +.004385/+.384644 remain capabilities; world29305038 and mixed ordinary
planning evidence prevent a trajectory guarantee. If a member is silent, its
movement has no current radio value at that fixed mask, while move+reactivate
may. Both sequential orders can miss that pair. Occurrence and full benefit
remain conjectural; stale proposals, limited support and short horizon can lose.

The full Root Decision linked above fixes the unchanged N5/U50/H256 host,
registered static50site map, native reward, retained C(history=False), pure
radio kernel, all27commands and31nonempty masks. R is original C+rolling E
with B01 timing. S tries both full-team sequential orders, motion at current
mask then mask, and mask at original C then motion, taking the better. T tests
all837pairs for fixed member `(tick // 4) % 5`; others keep their C proposals.
S/T rank J, served, preservation of selected member's C command, more active
transmitters, increasing mask integer, then increasing existing COMMANDS index.
No tolerance changes a decision. T-S is joint-search+compute; S/T-R is the
whole rights/information/clock package. Expose command aliases at boundaries
through actual executed displacement as well as command-index differences.

At t0, C is called once per member and reused as initial actual command and
first proposal. S/T call C only at reports0,4,...248 on actual refreshed local
observations, preserving its navigation updates even on misses. C suggestion,
commitment and actual command are distinct. Predict four ticks of current
actual commands then the candidate block; score positions+5..+8. Save preceding
transition reward before atomic arrival at t+4, refresh observations, then
generate the following proposal. First four all-on transitions remain; no
terminal t252 proposal. A late plan holds prior actual TEAM commands+mask,
without suggestion execution, state rollback, partial winner or queued work.

Version2 reports24bytes repurpose three reserved bytes for next C proposal;
the old velocity fields carry actual commands. Version2 commands16bytes bind
mask/member/COMMANDS index/sequence/effective tick/hold. Nominal136bytes/round,
63rounds=8,568recurring bytes per S/T episode, plus400byte map. Count actual
traffic on misses;8,568 is the upper bound. No hidden channel/connections/future
state. S/T's3.456s timer starts before C proposal generation and covers reports,
prediction/search and command encode/decode; .544s airtime completes the4s
window. Native transitions/radio refresh and evidence serialization remain
outside planner time. R retains.456s and its C cost is separately reported.
Timing is conditional on host/load, not a platform-replication result.

Fresh paired seeds29306000..29306063;192episodes/49,152native steps/0fits and
updates, no extra arm/pilot/panel. Orders cycle RST,STR,TRS,RTS,TSR,SRT, balanced
to within one per position. Upper work:3,969,472candidate scores,
15,875,904mask-state reductions,887,232scored geometries,32,256prefix ticks,
60,800Cdecisions/1,641,600Ctrajectories/6,566,400Cmodelticks. Cache geometry across
masks and repeated S queries; record actual work and request counts. T's matrix
supports same-input S shadow only at T's visited states, never S trajectories.

Configured local_linux/one thread/fresh4GiB floor, three-CPU-hour native-worker
ceiling including setup/collection/search/output. Preserve incomplete evidence
on ceiling, with no prefix inference/resumption/retry. Old ~42.1schedulerCPUmin
is sensitivity arithmetic, not runtime or a bound. Collection and reconstruction
are measured separately;12-24supporthours remain conjectural. B01's49,152steps
and.325752collection+readerCPUh remain inherited; complete B02 adds49,152steps.
Local NumPy CPU is suitable and avoids Claude's remote allocation; G0's accepted
local snapshot is untouched and admission still checks actual resources.

### L0 Implementation Scope

Deliver B02 codecs/search/runner/reader under direction-owned `b02/`, matching
tests, this notebook, runs and scratch. No edits to B01/C/kernel/shared launcher,
relay C++, G0 or Claude code. Registered Implementer owns only B02 `protocol.py`,
`scheduler.py` and `test_protocol_scheduler.py`; DM owns other files. Helper
uses shared main with no index/commit/NOTES/RESEARCH/launch ownership, spawns no
children and preserves all concurrent edits. Scheduler accepts only own-position
rows, actual commands, proposals, tick/mask and start clocks taken before C;
returns decoded commitment, packets, forecasts/scores, work and timing. Reuse
source-owned physics, cache geometry and S duplicate scores, derive S shadow
from T's existing matrix. No live environment enters search.

Focused checks: both-order choice, silent move+reactivate synthetic scores,
C-preserving ties/clipping aliases, codecs/rejects, four-step prefix/+5..+8,
single t0C/no t252, reward-before-arrival, distinct actual/suggestion state,
atomic late proposal/encoding/decoding fallback, unchanged R, full raw/endpoint
reconstruction, partial resource evidence and fixed admission/source binding.
Fixture seeds differ from panel; no scientific pilot. Independent registered
engineering review covers executable timing/numerical/identity risks; DM accepts
diff and checks. Exact inputs commit/push before native admitted detached launch.
Keep child active through deterministic same-handle observation and reading.

One canonical compressed raw per arm/world; compact results in Git. Reader
reconstructs every native motion/reward/service/observation/C suggestion and
commitment, validates search selection from recorded matrices, and checks a
prospectively fixed small candidate subset against physics. Recomputing every
candidate physics is not required; disclose coverage and reuse kernel checks.
Read full J/service/quality and every world, p10/minimum/zero outages, paths,
discovery/fallback, requested/executed changes, forecast errors, traffic and
compute/deadlines. Paired t95 uses reset worlds, not training instances or load
replication. T useful over S AND R retains capability; S>R without earned T
increment favors S without equivalence; T>S but not R earns no replacement.
Active choices/better forecasts without native benefit weaken this finite
package; tails remain costs. Independent diagnosis at material result boundary.
No automatic deeper search/learner/repair/panel; calibration/held-mask remain
unselected outside this task. Own publication/shared-background revision and
measured cleanup precede native return of evidence, changed judgment and next
action versus stop. Cross-question allocation belongs to Root.

### Outcome-Blind Implementation and Checks

Registered Implementer `/root/dm_radio_joint_control/commitment_search` returned
the version2 codec and S/T search, with eight focused checks. DM read the full
diff and integrated native collection and reconstruction. S caches duplicate
scores but counts116 algorithmic requests, excluding final ranking lookups;
T counts837 and reads its sequential shadow from the same completed matrix.
The fixed reader subset is Cq/all-on, Cq/current-mask, selected pair, sequential
pair, and `(round_index % 27, 1 + round_index % 31)`, wherever the S score exists;
all native transitions/C/commitments and matrix decisions are reconstructed.
R reuses the original complete reader and every retained E score check.

Two outcome-blind test corrections: duplicate B01/B02 test module names caused
collection failure, resolved by unique `test_b02_*` filenames (the attempted
package marker shadowed the source namespace and was removed). The atomic
pre-search deadline fixture caught empty pair-list assignment into a `(0,2)`
recorder slice; it now preserves the empty record and prior actual team command.
The synthetic silent-member fixture also now holds its radio score identical
across that member's commands, matching the declared structural conjecture.
Combined B01/B02 author checks pass48tests in2.89s, with only existing third-party
Pyparsing deprecation warnings. Fixtures use seeds811..815 and synthetic data,
not the result panel or a timing pilot. Final terminal-observation reconstruction
was then added. Required engineering review of the whole executable path is next.

### Engineering Acceptance

The final terminal-observation change passes all seven collector/reader tests
in2.47s. Registered independent Reviewer
`/root/dm_radio_joint_control/engineering_review`, separate context without
conversation inheritance, returned:

> No material engineering finding remains. No repair requested; acceptance
> remains with the DM. Reviewed the complete packet -> scheduler -> collector
> -> raw evidence -> reader path: single t0 C, separate actual/suggestion,
> reports through248, four actual prefix ticks and +5..+8 scoring; saved reward
> before arrival, refresh before proposal, atomic previous-actual-team fallback;
> both S orders,837 T pairs, ties/cache/displacement; unchanged R, admission,
> fixed exposure, partial-resource evidence and declared candidate subset.
> Independent verification:48tests passed in2.54s using configured scientific
> Python and pytest-owned scratch. Shared radio/environment, C and B01 sources
> match producing4d5ccefe6; inherited numerical evidence remains applicable.
> No full panel, actual SIGXCPU teardown or host-load deadline replication was
> exercised. Admission/publication remained prospective. No edits, Git
> mutations, launches or timing pilots performed.

DM accepts the diff and coverage. No scientific contract changed and no fresh
panel seed was exercised. Publish exact inputs then launch once through native
admission; any refusal/uncertain acceptance is reconciled at the same request.

### Accepted B02 Operation

Exact reviewed inputs published at `db5b9635850df204673871d4feb32e663ed8e5fd`.
Native launch accepted2026-09-29T18:31:10.167269Z on configured local_linux;
the [original manifest](../../../../runs/uav_radio_activation/b02_joint_commitment_a01/launch-manifest.json)
binds source snapshot, command, processes and output. Fresh actual-node
physical/effective available8,566,013,952bytes passed the4,294,967,296floor.
No node migration, extra arm or duplicate request. The fixed192episodes/0fits
and three-CPU-hour native-worker ceiling are unchanged.

Detached `hmasd_wait` uses this child's actual runtime
`01a0ee5c-3ec0-73c0-9937-a829cb1d4969`, private B02 request in direction scratch,
30s probes and1500s checkpoints against the original manifest/output handle.
Keep the child turn active through same-handle drain/rearm and full reading;
registration alone does not establish future queue delivery to a native child.

Generation1 checkpoint `ebe3f0c9d7397378618fb27c` (wake
`38b9a43c-ba6c-42d1-bd3b-4da1142db1fa`) observed the original runner and
supervisor still running. Latest printed exposure was112completeepisodes /
28,672steps /1498.196CPU-s. Queue delivery returned code-32600, `direct
app-server input is not allowed for unloaded spawned sub-agents`; the active
child drained and rearmed that same operation into generation2. The deterministic
in-turn wait reads only the existing observer's pending-event state. No worker
restart, address rebinding, outcome reading or scope/ceiling change occurred.

## 2026-09-29 - B02 Complete Reading

### Complete Native Exposure and Reconstruction

The original worker completed all192episodes /49,152native steps /0fits or
optimizer updates and exited0; both recorded native process identities were
absent at the19:14:08.497056Z terminal observation. Generation2 READY event
`bb8ec644c17892ad48474d16`, wake `691740ac-cc52-4a78-be9d-f7a91d23697f`, again
received the unloaded-native-child queue error. This still-active DM drained
the same operation, consumed the event through generation3, then stopped
observation. Both events are consumed, wake is null, stopped is true and the
observer PID is absent. No accepted work was restarted or rebound. The compact
[observer record](../../../../runs/uav_radio_activation/b02_joint_commitment_a01/observer-terminal.json)
preserves checkpoint, terminal facts, delivery failures and stop separately.

The [complete summary](../../../../runs/uav_radio_activation/b02_joint_commitment_a01/summary.json)
has SHA256 `9a630e63ccd00e3177f133aa759a44475e0a55729c707a9b4fd42eb3995022de`.
Its192per-arm/world rows retain every positive and adverse world, raw locator,
byte count and digest. One canonical evidence copy remains on local_linux at
`/home/fires/hmasd-wsl/runs/uav_radio_activation/b02_joint_commitment_a01/raw/`:
90,743,452content bytes /91,136,000allocated bytes. No extra scientific panel,
partial-prefix inference, outcome exclusion or seed replacement occurred.

The exact published source snapshot reader exited0 after all192rows and wrote
[VERIFIED_COMPLETE reading](../../../../runs/uav_radio_activation/b02_joint_commitment_a01/reading.json).
It verified all192raw hashes, complete paired initial worlds/maps, every native
motion/radio/reward/observation, C decisions and navigation updates, actual
commands, arrivals, commitments, deadlines/traffic and endpoint/paired metrics.
Maximum reconstructed native J error5.5511e-17; native SINR and observation
errors0. R's original complete candidate verification was retained. S/T matrix
choice was reconstructed for all rounds; the prospectively fixed physics
subset checked11,248S and15,305T candidate pairs. This does not claim exhaustive
independent physics recomputation of every T candidate or new environment
steps. All full endpoints include the initial four all-on S/T transitions.

### Complete Package Results

J is mean native reward, `.7 * served / 50 + .3 * quality`; service is users
served per step. Descriptive paired t95 intervals use64reset worlds, not
training seeds or independent host-load replications. This is exploratory,
without a new confirmation claim or a multiplicity-adjusted guarantee.

| Contrast | Mean Delta J [t95] | J Win/Loss | Mean Delta Service [t95] | Service Win/Loss |
|---|---:|---:|---:|---:|
| S-R | -.01350614 [-.02005700,-.00695529] |19/45| -.51043701 [-1.05729476,+.03642074] |23/41|
| T-R | -.00933808 [-.01650084,-.00217533] |17/47| -.15545654 [-.77228698,+.46137390] |26/38|
| T-S | +.00416806 [+.00045349,+.00788263] |42/22| +.35498047 [+.05005623,+.65990470] |44/20|

T has39worlds with both J and service higher than S and25with at least one
loss. All17T-R J gains also gain service; all47remaining worlds lose at least
J. S has19joint gains and45worlds with at least one loss against R. Service
intervals crossing zero do not establish equivalence; the declared positive
T-S increment does not establish T dominance or T-R replacement.

| Complete Mean/Endpoint | R | S | T |
|---|---:|---:|---:|
| Native J |.47066807|.45716193|.46132999|
| Served users/step |28.875000|28.364563|28.719543|
| Quality |.22139356|.20019348|.19752126|
| Mean within-world service p10 |27.546875|25.757813|26.250000|
| Mean within-world service minimum |12.125000|11.843750|11.828125|
| Absolute minimum service |2|1|1|
| Zero-service steps / longest outage |0/0|0/0|0/0|
| Path m/UAV |2466.960|7471.535|7479.787|
| XY-boundary UAV-ticks, total |559|7619|7451|
| Lower-altitude UAV-ticks, total |81539|81417|81352|

T-S quality -.00267223 [-.00586703,+.00052258],26wins/38losses. T-R quality
-.02387231 [-.03187583,-.01586879],15wins/49losses. By the exact reward identity,
T-R's service term contributes -.00217639 and quality term -.00716169 to the
J difference; this is an arithmetic partition, not a causal explanation.
S-R quality -.02120008 [-.02827071,-.01412945],13wins/51losses.

T-S p10 +.492188 [-.115410,+1.099785],21wins/11losses/32ties, while T-R p10
-1.296875 [-1.904565,-.689185],9wins/45losses/10ties. S-R p10 -1.789063
[-2.439302,-1.138823],8wins/45losses/11ties. T-R minimum service declines in
14worlds and S-R in13, with no improvements; T-S has one minimum loss in
29306057 and63ties. Zero outages do not establish safety. T-R path increases
5012.827m/UAV [4611.029,5414.625] in all64worlds; S-R increases5004.575 in63.
T-S's8.252m difference [-173.135,189.639] does not establish path equivalence.
The host has no energy model; these are motion costs, not battery conclusions.

All adverse worlds remain in the linked complete rows. Named witnesses:

| World | Contrast | Delta J | Delta Service | Delta p10 |
|---|---|---:|---:|---:|
|29306018|T-R|-.08950261|-6.261719|-4|
|29306020|T-R|-.05702710|-4.917969|-7|
|29306019|T-R|-.05481437|-4.523438|-3|
|29306018|T-S|-.02990433|-2.226563|-1|
|29306017|T-S|-.02391496|-1.945313|-3.5|
|29306021|T-S|-.02019395|-1.882813|-1|
|29306062|T-S|+.08188878|+6.949219|+17|
|29306062|T-R|+.08249951|+7.789063|+8|
|29306010|T-R|+.05999486|+5.199219|+3|
|29306017|T-R|+.04208386|+3.292969|0|

World62's large positive contribution is retained, not trimmed to change the
estimand. S-R worst J is29306018 (-.05959828/-4.035156service); worst service
is29306020 (-.05556977J/-4.726563service). Fresh29306038 is not the inherited
B01 world29305038. This study neither repeats nor repairs that earlier adverse
world; B01 positives and losses remain cumulative evidence under its own clock.

### Decisions, Forecasts and Feedback

S/T actually edited2,206/2,608selected-member C proposals; all of those edits
changed executed displacement, with0clipping aliases against the proposal.
Selected-member silent-to-active transitions were323/727. C empty-discovery
fallback decisions were6,694R /7,186S /6,798T, of20,480/20,160/20,160decisions;
S/T fallback here describes the internal C proposal, not automatic execution.
Mean visible-user rows were6.2891/6.2673/6.2863, peer rows.10007/.10144/.08953.
Mean active transmitters3.37506/3.24609/3.34277; total mask flips1,747/2,643/3,415.
Silence/discovery/flight feedback is active, not removed by the planning model.

On T's4,032visited report states, its recorded full matrix gives mean T-minus-S
shadow J +.001243340 and service +.126240079. The chosen pair differs in583rounds
and the selected member's executed displacement in566. In419rounds the selected
member is currently silent, the best sequential pair keeps it silent, while T
changes its C proposal and activates it with strictly higher predicted J. This
is active decision exposure for the constructive conjecture. The shadow is on
T's states and cannot be substituted for the complete S trajectories; the419
cases do not establish causal mediation of the complete T-S mean.

Committed-position prediction errors remain below.667214m. Mean errors at
offsets+5/+6/+7/+8 are S .240410/.239763/.238850/.237962m and
T .236992/.236283/.235328/.234348m; remaining packet quantization and threshold
effects are retained. R's corresponding declared offsets+2/+3/+4/+5 have
means.374359/.373790/.373545/14.450536m, maximum+5error85.527816m. Different
rights/clocks/horizons mean this is not a calibration-causality comparison.
Mean signed native-minus-predicted J at+5..8 is S
(-.00004068,-.00006706,-.00006441,-.00002616), T
(-.00005188,-.00001569,-.00002527,-.00008410); largest absolute errors are
.02530979S and.01302387T. Accurate blocks coexist with complete package losses.
Actual report ages average2.494ticks/max4 for R,5.5/max7 for S/T.

### Resource and Support Accounting

Native collection:2574.771866s wall,2571.774026user +1.851923system =
2573.625949CPU-s (.714896CPUh),132,408KiB worker-lifetime peak RSS. It remained
below the prospective3CPUh ceiling, on one configured thread, with no resource
truncation. There were0deadline misses in every arm. Maximum measured planner
wall times were.043384074R / .150891513S / .899728403T seconds, against
.456/3.456/3.456s windows. This is observed load-conditional feasibility, not
hardware certification, a latency guarantee, or a host replication.

| Actual Work or Cost | R | S | T |
|---|---:|---:|---:|
| Algorithmic candidate requests |126976|467712|3374784|
| Unique scored candidate pairs |126976|334389|3374784|
| Mask-state reductions |505920|1337556|13499136|
| Scored geometries |16320|435456|435456|
| Prefix prediction ticks |0|16128|16128|
| C decisions |20480|20160|20160|
| Planner CPU-s |84.558282|254.626336|2167.939028|
| C CPU-s, S/T already inside planner |9.766873|7.146803|7.054420|
| Sum complete-episode CPU-s |111.066612|272.852638|2187.392580|
| Recurring bytes/episode |8704|8568|8568|

Each episode also carries400static-map bytes. Total3,969,472candidate requests,
3,836,149unique scores,15,342,612mask-state reductions,887,232geometries,
32,256prefix ticks and60,800C decisions, with1,641,600C trajectories and
6,566,400C model ticks. Cached S duplicate requests explain reductions below
the15,875,904upper bound; there was no reduced native exposure. T-S adds about
29.915complete-episode CPU-s per world. No artificial compute penalty is added
to native J, and R's C cost is not hidden in its scheduler timing.

Complete reconstruction is separate support work: inner reader935.325617s wall /
935.064555CPU-s; whole reader process935.90s wall,915.27user +20.29system =
935.56CPU-s,102,800KiB lifetime peak RSS, exit0. Native-plus-whole-reader B02
cost is.974774CPUh. Including inherited B01's.325752 gives about1.300526CPUh
for the two batches' collection/readers,98,304native steps and0fits. This excludes
unmetered adviser/engineering work and is not a complete labor/compute bill.
The published registration18:11:38Z to exact-input publication18:30:25Z interval
is18m47s elapsed preparation/review wall time, with parallel helper work; it is
not additive agent-hours or human labor. Focused test times and independent
checks are recorded above. The prospective12-24supporthour conjecture was not
a measured quantity; aggregate other support remains incompletely metered.

### Independent Scientific Diagnosis

Registered ResearchCritic `/root/dm_radio_joint_control/result_diagnosis`
worked in a separate context without DM/Root conversation inheritance. It
received original source/config/manifest/results, B01 supporting/adverse records,
the complete adopted Pro/review archive and current background, with the actual
question rather than the DM's preferred interpretation. A condensed transcription
of its substantive final return follows, preserving the recommendation, evidence,
limits and dissent, including its change from its own provisional stop preference.

> Recommend revise through one prospective two-tick-delivery comparison.
> Retain R as the current complete-package reference and close frozen B02 with
> its adverse result intact. Preserve T's conditional increment over S. My
> earlier preference for no further purchase was provisional; the complete
> exposure and timing evidence support this specific continuation.
>
> I received no DM/Root conversation history. I reconstructed original outputs
> and consequential raw evidence before reading the full Pro answer, selection
> corrections and Root disposition. Complete B02 gives T-S J +.004168
> [.000453,.007883], service +.354980 [.050056,.659905]; T-R J -.009338
> [-.016501,-.002175], service -.155457 [-.772287,.461374]; S-R J -.013506
> [-.020057,-.006955], service -.510437 [-1.057295,.036421]. These are64paired
> reset-world comparisons, conditional on observed host/deadlines, with zero
> training inference. T-S improves J in42worlds and service in44. T-R loses J
> in47worlds. T's mean service p10 is1.297users below R, with45adverse worlds;
> mean path rises from approximately2467 to7480m/UAV. No arm has zero-service
> ticks. Paths are movement costs, not measured battery consumption.
>
> The selection hypothesis has a substantive positive. On T's4032visited report
> states, joint search has583strict predicted-J advantages over both-order S,
> occurring in every world. There are566displacement differences and419silent
> move/reactivate strict advantages. Shadows remain conditional on T's states.
>
> A direct native witness strengthens that interpretation. In29306018, S/T
> share the same prefix until transition36. At report32, S leaves member3
> silent; T changes its motion and activates it. The first affected native
> block gains.0022395J and.25users/tick, closely matching the predicted J
> increment. Nevertheless, complete T-S is-.0299043. Joint opportunity exists
> and is executed, while local improvement can lead to a worse trajectory.
>
> The strongest simpler explanation is ordinary finite optimization under a
> changed control contract. S already uses coordinated full-team scoring; T
> purchases larger search and about29.915additional episode CPU seconds.
> This establishes neither a special coordination mechanism, necessity of
> exhaustive search, nor learning value. S/T's approximately.24m block-position
> errors coexist with worse complete performance than R. Accurate committed-
> block prediction is insufficient. Stale proposals and later trajectory
> consequences remain plausible causes, but B02 does not separate them. My
> post hoc partition finds startup contributes only-.001736 of T-R's-.009338J
> difference; the loss persists afterward.
>
> The strongest consequential objection to stopping new investment now is
> concrete: the interaction is active, its complete matched-contract increment
> survives, and measured computation does not require four-tick delivery.
> T's maximum observed planner wall.899728s plus declared.544s airtime gives
> 1.443728s. This supports exploring two-tick delivery on the observed host,
> neither a deadline guarantee nor hardware replication.
>
> The smallest worthwhile continuation is R/S2/T2 on64fresh common worlds,
> retaining native H256. R keeps its original contract. S2/T2 share two-tick
> delivery, four-tick command holds, identical information and1.456s complete
> computation deadlines. Reports0,4,...252; predict two actual committed ticks,
> then score the following execution block. Report252 arrives254 and scores
> only the remaining transitions, at positions255and256. Preserve every
> startup/terminal transition. Retain both sequential orders, all837T pairs,
> atomic deadline fallback and complete J/service/tail/cost reading. This is
> new exploration, not a B02 retrofit or pure latency-causality inference.
>
> This changes a real judgment beyond repeating T-S: can demonstrated
> interaction become useful against R in a more responsive contract? Useful
> T2 gains over S2 and R support a new conditional capability. S2 beating R
> without earned T2 increment favors simpler composition. Continued R
> deficits, unacceptable tradeoffs or failed timely execution weaken this
> concrete continuation and support stopping it. Uncertainty establishes
> neither equivalence nor an automatic purchase of another clock.
>
> Proposed exposure192episodes/49152native steps/0fits; upper4030464candidate
> scores and15997888mask-state reductions. S2/T2 each8704recurring bytes plus
> separate400byte map. B02 collection-plus-reader approximately.975CPUh is an
> anchor, not forecast or bound. Collection2573.626CPU-s, reader approximately
> 935.56; inherited B01+B02 approximately1.301CPUh excludes incompletely
> metered support. New arrival ordering, terminal handling, reader changes
> and engineering checks require work whose labor cost remains unknown.
>
> I independently checked executed-source semantics, manifest/config bindings,
> twelve B02 raw files covering supportive/adverse/typical cases, six B01 raws,
> matched prefixes, reward components, tails and paths. I also checked all T
> recorded-score gaps and the post hoc reward partition. The completed reader
> verifies all192raw identities, native endpoints, observations, C proposals,
> commitments and selections; I verified its summary hash and bindings. Its
> physics coverage is the declared subset, not every candidate. Prior scalar/
> kernel checks remain applicable. Platform variability, physical positioning/
> link costs and learning generalization remain unverified.
>
> Return the proposed continuation to Root at this one-study boundary. This
> review authorizes no launch or source change. MATERIAL_DISSENT: yes,
> relative to provisional no-new-investment. The disagreement concerns
> purchasing the specified two-tick comparison, not retaining R, closing
> frozen B02, or publishing reserve status pending Root's choice.

### DM Interpretation and Next Investment

Accept the full B02 verdict and revise the provisional no-new-investment
preference in response to the complete independent reading. The constructive
silent-member opportunity is real and executed, and T earns a positive
complete J/service increment over the competent, already coordinated S. It
does not extend the retained R capability under this four-tick contract.
Neither a weak comparator nor unexpressed joint choices explain away that
split result. R remains the reference for complete native usefulness; the
new T/S asset is a retained conditional ordinary-control increment, not an
adopted replacement, learner result or proof of necessary joint search.

The native29306018 witness is especially discriminating: at report32/current
mask19, S chooses(q2,mask7), keeping member3 silent; T chooses(q7,mask13), moving
and reactivating it. Its first affected block36..39 gains.002239505J/.25users
(predicted J gap.002230090), yet later endogenous trajectories lose overall.
The post hoc full-panel arithmetic partition retains all256ticks: first4
contribute-.001735996 and remaining252 contribute-.007602088 to T-R J.
No startup omission, suffix re-estimand or causal latency attribution follows.
Better block accuracy and positive local choices are insufficient; feedback,
commitment timing and longer trajectory consequences remain coupled.

There is a more specific next question than a blind larger panel or deeper
search purchase. The observed .899728s planner maximum leaves room inside a
1.456s window plus the same.544s link, so the critic's two-tick complete
comparison has plausible decision value at roughly the measured B02 resource
scale, without assuming it will win or be timely under future load. Its native
prediction is that the more responsive package preserves useful T-over-S
choices while improving complete T2-versus-R J/service; that prediction can
fail even with accurate forecasts. The lower clock is not silently applied to
B02, and a point maximum is not a prospective runtime upper bound.

DM therefore returns the costed R/S2/T2 proposal to Root for the next allocation
at this assigned one-study boundary, explicitly retaining the critic's
MATERIAL_DISSENT against the earlier provisional stop preference. This accepts
the recommendation to consider the specified continuation, not an additional
launch or a scientific guarantee. Its final contract, fresh seeds, ceiling,
engineering review and source/admission would belong to that new selection.
No automatic tail repair, learner, deeper search, calibration/held-mask study
or extra B02 panel is selected here. Cross-question changes remain Root-owned.

B02 is now completely read with no active producer or unread result. The
direction is reserve at publication, with the positive T-S capability and all
R-relative costs retained. The actual next decision is Root's allocation of
the proposed clock comparison versus a justified stop or another question;
this is not a dependency for publishing or cleaning B02, nor a per-run approval
gate. Preserve useful code/tests and the sole evidence copy, publish the shared
background correction, and reclaim only reconciled snapshot/scratch/logs.

### Publication and Measured Cleanup

Full B02 compact evidence, reconstruction, independent diagnosis/dissent, DM
disposition and own RESEARCH standing/shared-background revision were published
and pushed at `ee19617e7ca6f6df2d16fccb78c4fbdcfe9f9ebf`. This includes the
complete native/observer records and every per-world result, not new bulk arrays.
Executed inputs remain recoverable at `db5b9635850df204673871d4feb32e663ed8e5fd`.

Import/test/entrypoint inspection retains useful B01/R and B02 S/T protocol,
search, collection/reconstruction and focused tests as executable definitions
of the conditional capabilities and their evidence. B02's reader consumes its
protocol/study helpers; tests bind those semantics. No unused replacement
implementation or other direction's code was removed. Retention is not a new
experiment selection. The shared pure radio kernel and C remain unchanged.

Both native identities, the whole reader, all bounded helpers and the stopped
observer had finished before deletion. Exact-target snapshot-GC preview and
apply both passed with the documented `--sudo-process-scan` read-only process
inspection: clean source, terminal native operation, no live process references
and durable `refs/heads/main` reachability. No new inspection refusal occurred.
The collector removed only the B02 launcher snapshot; original operation claim,
manifest, exit witness and source commit remain. The source is also absent
from registered worktrees. No other snapshot, G0 operation or Claude input was
touched, and no retention copy or archive was created.

Allocated bytes immediately before exact-target deletion (`du -s -B1`):

| Deleted Target | Allocated Bytes |
|---|---:|
| `.git/hmasd-launch-sources/4eeab042293b403b9a5aaeb2e2d89b52` |1645789184|
| `temp/directions/uav_radio_activation/`, containing only retired `b02-wait.json` |8192|
| `experiments/candidates/uav_radio_activation/b01/__pycache__/` |61440|
| `experiments/candidates/uav_radio_activation/b02/__pycache__/` |61440|
| `tests/experiments/candidates/uav_radio_activation/b01/__pycache__/` |53248|
| `tests/experiments/candidates/uav_radio_activation/b02/__pycache__/` |98304|
| `runs/uav_radio_activation/b02_joint_commitment_a01/stdout.log` |28672|
| Same run's empty `stderr.log` |0|

All eight targets are verified absent. Net allocated reduction over this exact
target set is **1,646,100,480bytes**, from that sum to zero. This measures
working-tree target reclamation, not Git-object shrinkage or whole-host free
space amid other writers. Stdout only repeated row progress retained in the
complete summary; stderr was empty. Rebuildable caches carried no unique result.

The canonical192raw files remain90,743,452content bytes /91,136,000allocated
bytes, with the complete reader's verified digests in the published summary.
No cleanup blocker, active worker/observer, unread result or unreturned helper
remains. The only future action proposed is the explicitly unselected clock
comparison already returned to Root; B02's collection and scientific reading
are complete independently of that allocation decision.

## 2026-09-29 - B03 Prospective Timely Joint Control

Lead: new native `hmasd-direction-manager` `/root/dm_radio_delivery`, parent
Root `01a0e560-4333-7b03-8ff3-759a4add1d9a`, shared main. Current selection,
exploring state and routing are published at `1afc7a68d`. Owner pause is lifted
for this direction. B01/B02 are fully read, with no active producer or unread
result adopted. This is cumulative question ownership, not reuse of old handles.
Read the complete B02 prospective/result/independent diagnosis/DM response,
the prior adoption archive's focused review and decision, and the complete
6 Pro answer at `d7c74268f` in RESEARCH's Joint Control Next Investment section.
The adequate B02 independent diagnosis supports this exact two-tick comparison;
reuse it without a duplicate selection review. Its material dissent against
the provisional stop preference and subsequent DM/Root adoption remain intact.

### Question, Prediction and Complete Comparison

Can the demonstrated motion/silence interaction extend complete native service
beyond original R under a supported, more timely delivery contract? Contribution
is conditional ordinary-control usefulness and empirical understanding, not
learning, novelty, pure latency causality or physical deployment. Published
RESEARCH `1afc7a68d`, background sections1/2 and the current selection, concretely
requires original R, matched S2 rights/information, and complete J AND service.
B01's activation capability and B02's T-S +.004168J/+.354980users coexist with
T-R -.009338J, service-p10 -1.296875 and about5013m/UAV additional path. Accurate
blocks and real local gains did not earn replacement; later motion/feedback and
stale proposals remain coupled alternatives, not uniquely diagnosed causes.

The constructive prediction is lower report age while preserving meaningful
joint choices, with useful complete T2-R J/service. The stronger ordinary
alternative is original R's timely feedback, or S2 if it earns the same useful
package without enough extra T2 value. This study does not demand a positive
activation count. Keep all worlds and complete startup/terminal exposure.

Fixed host: N5/U50/H256, uniform static users, registered400byte map with the
same quantization error, known free_space model, unchanged native reward and
opt-in radio mask semantics. Reuse C(history=False), all27 commands, all31
nonempty masks and deterministic J/service/C-preserving/mask/command tie order.
R is original C+rolling E with one-tick delivery and.456s planner window.
S2 tries both full-team sequential orders; T2 tests27commands x31masks for
member `(tick // 4) % 5`, other members retaining their C proposals. T2-S2 is
finite joint search plus computation; S2/T2-R is a whole-contract comparison.

S2/T2 reports are at0,4,...252. Actual team commands execute two prefix ticks;
arrival at t+2 atomically sets team commands and mask for transitions t+2..t+5,
with scoring on postmove positions t+3..t+6. Final report252 arrives254 and
scores only255/256. Initialize each C once at0, reuse that decision as actual
startup command and first proposal. Later C proposals occur only at report
clocks, with no extra C update on arrival. Save completed reward/radio/connection
data before atomic arrival and observation refresh. A complete missed plan
holds actual whole-team commands+mask, without partial winner, suggestion leak,
state rollback or an expired hold label preventing lawful continued execution.

Version3 packets retain24byte reports and16byte commands, binding two-tick
delivery separately from four-tick hold. Both new arms have1.456s full planning
time, including consequential C proposal/encoding/prediction/search/decode,
plus.544s airtime on the unchanged2kbit/s link. At most8704recurringbytes/episode
plus400map; record actual missed-round traffic. Nominal plan-controlled report
age is887/254=3.492126ticks (startup2ticks excluded only from this age metric,
never endpoints). Deadline failures and resulting older information are native
package outcomes. No future state/SINR, battery claim or physical-use guarantee.

Fresh common reset seeds29307000..29307063, fixed before result exposure;
192episodes/49152native steps/0fits or updates. Cycle orders R-S2-T2,
S2-T2-R,T2-R-S2,R-T2-S2,T2-S2-R,S2-R-T2, balanced within one per position.
Upper work:4030464candidate requests,15997888mask-state reductions,
894144scored geometries,16384prefix ticks,61440C decisions,
1658880C candidate trajectories and6635520C model ticks. Cache repeated
queries/geometry and report actual unique scores separately from requests.
T2 matrix S2 shadows describe T2 states only; they never replace S2 trajectories.

Configured local_linux, one CPU thread, fresh actual-node4GiB memory floor;
three-CPU-hour native-worker ceiling includes imports/init/native/C/search/output.
Local NumPy is suitable, preserves G0's same accepted operation, and uses none
of Claude's remote reservation. B02 native+reader.974774CPUh is an anchor, not a
new estimate. Reader and support are separately measured where available;
new engineering labor is unknown. Cumulative prior98304native steps/0fits and
about1.300526native+readerCPUh remain. Resource/technical incompleteness is not
a native negative, and permits no automatic extension, restart or prefix verdict.

### L0 Implementation Scope

Deliver new direction-owned `b03/{protocol,scheduler,study,run,read}.py`, tests
under matching `tests/experiments/candidates/uav_radio_activation/b03/`, this
notebook, `runs/uav_radio_activation/b03_two_tick_delivery_a01/` and direction
scratch. Preserve B01/B02/C/kernel/shared launchers, G0 and Claude sources.
Registered Implementer owns only B03 protocol/scheduler and their focused test
file: version3 two-tick forecast, terminal half-block, full timer and atomic
fallback. DM owns collector/reader/run and their tests. The helper writes on
shared main, spawns no children, launches no result and has no NOTES/RESEARCH/
index/commit ownership; preserve concurrent edits. Reuse existing helpers where
they retain semantics, without a gratuitous shared abstraction.

Checks cover version rejection and exact effective tick; two actual prefix
ticks/+3..+6 with252 terminal truncation; both S2 orders/T2 joint choices and
tie/cache counts; full deadline including proposal/encode/decode; repeated
misses beyond old hold expiration; separate report/arrival clocks; C-once
startup and report-only updates; saved transition before mask refresh; no new
proposal leaked on fallback; unchanged R; full endpoint reconstruction; partial
resource evidence and admitted fixed source/seed binding. Fixture seeds are
outside the scientific panel. Independent engineering review checks the new
timing/packet/collector/reader contract; DM accepts its diff/checks. Commit and
publish exact source before one native admitted detached launch and same-handle
observation, keeping the native child active through complete reading.

Keep one canonical compressed raw per arm/world and compact Git evidence.
Reconstruct all native transitions, C/actual/proposal/commitment states,
observations, rewards and choices; reuse complete R checks and the B02 fixed
candidate subset (Cq/all-on, Cq/current, selected, sequential, round-index
sentinel where evaluated), adapted to two-tick delivery and final half-block.
No claim to independently recompute every T2 candidate. Read full J/service/
quality, p10/min/zero counts/longest gaps, path/boundaries, discovery/fallback,
requested/executed choices, predictions, ages, traffic, deadlines and costs.
Paired descriptive t95 uses reset worlds, conditional on observed host/load,
not training-instance or platform replication. Independent result diagnosis
will confront all positive/adverse evidence at the complete study boundary.

Useful T2 gains over S2 and R retain a conditional capability; S2>R without
earned T2 increment favors simpler composition without equivalence. T2>S2
without developing R stops this clock-shortening route as current investment.
Proxy-only gains, tails or cost harms remain limitations; no automatic1tick,
deeper search, path penalty, learner, more worlds or retry. Publish own material
RESEARCH result/background and measured cleanup, then return changed knowledge,
remaining alternatives and a reasoned next-investment recommendation to Root.
Broader allocation is Root's question choice, not a routine launch ACK.

### Outcome-Blind Implementation and Checks

Registered Implementer `/root/dm_radio_delivery/two_tick_protocol` supplied the
version3 codec and two-tick S2/T2 scheduler plus nine focused checks; DM read
the full diff and accepted its interface. B03 imports B02's unchanged command
index/rank/two-order search helpers. New collector stores explicit pending
arrival time, with reports0..252, arrivals2..254, and NaN-only padding after the
terminal two-state forecast. C proposals, actual commands and commitments stay
distinct. The reader reconstructs both clocks, full native endpoints and the
declared candidate subset, including final half-block physics and report age.

Author configured-scientific pytest:18passed in3.06s, only existing third-party
Pyparsing deprecation warnings. Fixtures use nonpanel seeds811..816 plus
packet-only29306999/29307064, not scientific panel exposure or a timing pilot.
Checks establish two actual prefix ticks, final two-state scoring, single t0C,
report-only C thereafter, reward-before-arrival observation refresh, unchanged
R trajectory and candidate evidence, atomic encode/decode/partial-score misses,
repeated continued actual commands beyond four ticks, fixed seed/admission
order and preserved incomplete-resource evidence. Full-source upper arithmetic
matches4030464requests/15997888reductions/894144geometries/16384prefix ticks;
actual unique work remains to be measured. Independent engineering acceptance
of the complete path is next; no result-bearing operation has started.

Independent engineering review identified that first-round deadline failure
would leave the inherited age reader without an origin, omitting continued
startup commands until a timely plan. Corrected before any outcome exposure:
the age metric uses each actual command's source-observation tick, initializing
to the legal t0 C observation; only transitions0/1 are excluded. This initial
origin does not claim a delivered scheduler plan. An additional count exposes
startup-command hold transitions after the nominal first arrival until a timely
plan arrives. All-missed and first-missed-then-recovered fixtures protect the
complete denominator. No controller, objective, panel or execution rule changed.

### Engineering Acceptance

Independent registered Reviewer `/root/dm_radio_delivery/engineering_review`,
without DM/Root conversation inheritance, reviewed versioned packets, prefix/
arrival/final-block timing, full C-through-decode deadline, both sequential
orders/ties/cache, atomic actual-team fallback, native reset/RNG/radio/reward/
observation consumers, unchanged R, admission/source and incomplete-resource
paths. It identified the initial-miss age omission above, then reviewed the
repair and returned no remaining material engineering finding. Independent
configured-scientific pytest:20passed in3.65s; author20passed in3.53s.
Only existing third-party deprecation warnings. Inherited B01/B02/C/kernel/
environment files have no diff from executed B02 source `db5b9635850df204673871d4feb32e663ed8e5fd`.

DM accepts the implementation and checks. No scientific panel was exercised.
The CPU-ceiling check injects an exception; an actual three-hour/SIGXCPU
teardown was not run. Complete scientific reader execution awaits collected
evidence. Publish these exact inputs, then one launch under current admission;
no outstanding scientific selection issue or per-run Root approval remains.

### Accepted B03 Operation

Exact reviewed inputs published at `2bff85091f85f6d52fc0344d0329b4fc39fa6d5c`.
Native launch accepted2026-09-29T20:33:24.607559Z on configured local_linux;
the [original manifest](../../../../runs/uav_radio_activation/b03_two_tick_delivery_a01/launch-manifest.json)
binds source snapshot, command, process identities and canonical output.
Fresh actual-node physical/effective memory8828932096bytes passed the
4294967296byte floor. Fixed192episodes/49152steps/0fits, one CPU thread and
three-CPU-hour native-worker ceiling remain unchanged. No duplicate or
inherited process was launched, and no scientific outcome has been read.

Detached `hmasd_wait` is owned by this child's runtime
`01a0eed3-b984-7f62-aa36-c623d55c3612`, with private B03 request in direction
scratch,30s probes and1500s checkpoints on the same native operation. Keep this
child turn active, drain/rearm the same handle at checkpoints, and distinguish
queue-delivery facts from healthy observation. Registration is not proof that
an ended native child could be woken. Source publication precedes execution;
this start belongs in NOTES/runs, not another routine RESEARCH update.

Generation1 checkpoint `ebe3f0c9d7397378618fb27c`, wake
`65571785-91ac-4928-9e90-7931ed7030e8`, observed both original native identities
running at20:57:50Z. Latest progress102completeepisodes/26112steps/1482.090CPU-s.
Queue delivery returned code-32600, `direct app-server input is not allowed for
unloaded spawned sub-agents`. This active child drained and rearmed the same
operation into generation2. No worker restart, address change, scope/ceiling
extension or partial outcome interpretation occurred.

### Owner Pause and Handoff - 2026-09-29 21:31 UTC

The owner explicitly requested a workflow pause and written handoff. Root
relayed that instruction to this native DM; it takes precedence immediately,
including before any RESEARCH control publication. Scientific development,
new execution, further interpretation/review, cleanup and successor work are
stopped. Only this bounded reconciliation and evidence publication continue.
Root owns the global pause/control update, preserving launch-bound leads.
**B03 is technically complete, but its full independent reading and scientific
disposition are incomplete. No adopted result, route closure or next investment
is established by this pause entry. Owner resume is required.**

Published reviewed source is
`2bff85091f85f6d52fc0344d0329b4fc39fa6d5c`; accepted-operation publication is
`6b1fdd41f`. The sole native operation remains
`.git/hmasd-admission/c0e0f240ff4084e66fbf95f0700853600869e747fa182db01cf2bbaf2f4bc748.json`,
with accepted source snapshot
`.git/hmasd-launch-sources/3d9c57d229864a02a8679bdf903af92e` and canonical output
`runs/uav_radio_activation/b03_two_tick_delivery_a01/`. No duplicate operation,
native restart or batch extension occurred.

The native supervisor3910321 and worker3910322 terminated normally before the
pause. `process-exit.json` records exit0, `normal_process_exit`, finished epoch
1790716917.7261229; terminal status was observed at2026-09-29T21:22:20.857001Z.
Runner summary is COMPLETE with one constructor,192explicit resets,
192complete episodes/49152native and team steps,0fits/optimizer steps and no
failure. Whole-worker wall2912.68424427s, user2899.402799s plus system2.611851s
=2902.01465CPU-s, peakRSS131156KiB, one thread. These are technical collection
facts, not a completed independently read scientific conclusion. Summary
SHA256 is `554d27275b84c69479a1560c0ee9fa74be112fd933c6f60518c9b592bcb5edc1`.

Observer generation2 returned terminal READY event
`731f4862a4e8ed0767dfb596`, wake
`1071362f-5bd8-495d-bce3-985dbe3001a9`. Its queue attempt, like generation1,
returned code-32600 (`direct app-server input is not allowed for unloaded
spawned sub-agents`). The active DM drained that terminal event and consumed
it into stopped generation3 before this pause. Retained compact witness:
`observer-terminal.json`. Private request:
`temp/directions/uav_radio_activation/b03-wait.json`; private state:
`/home/fires/.local/state/hmasd-wait/01a0eed3-b984-7f62-aa36-c623d55c3612/state.json`.
State is stopped, wake null, both events consumed; final observer4008278 is
absent. There is no automatic wake to await or rearm. Do not restart/rearm it
under the pause.

The full reader had started from the exact accepted snapshot, in exec
session49205, with `/usr/bin/time -v` writing `reader-resources.txt`. On pause,
the DM identity-checked reader4008315 against the exact B03 snapshot command
and sent SIGTERM; its time parent was4008308. The session drained with exit143.
Last emitted completed verification was39/192, T2/reset seed29307012. The
reader has no resumable aggregate checkpoint and **`reading.json` is absent**.
The stopped reader cost is user248.21s/system5.45s, elapsed4:13.62,
peakRSS102072KiB. Its time witness says `Command terminated by signal 15`;
the footer's `Exit status: 0` does not supersede that signal or session exit143.
This is owner-paused partial verification, not reader success or a failed
native scientific package. No raw or summary artifact was overwritten.

At21:30:57Z, `ps` found none of native supervisor3910321, native worker3910322,
reader4008315, time parent4008308 or observer4008278. All owned exec waits are
drained. Helper states: `/root/dm_radio_delivery/two_tick_protocol` completed;
`/root/dm_radio_delivery/engineering_review` completed;
`/root/dm_radio_delivery/result_diagnosis` interrupted. The DM's explicit
interrupt found the critic already interrupted; no further review is assigned.
This DM remains active only to publish the handoff, then returns to Root.

The independent result critic's only received diagnostic message is retained
here as **provisional and unfinished**, not an adequate completed result
verdict. Before reading B02's prior critic/DM or Pro explanations, it reported
independent checks of192raw hashes, matched reset sites/initial positions/map
packets, and reconstruction of complete J/service/quality/p10/min/zero/path/
deadline/traffic endpoints matching summary. It reported S2-R
`+.016514J/+1.504150users`, T2-R `+.017367J/+1.667236users`, and T2-S2
`+.000853J/+.163086users`, with the last contrast's descriptive intervals
crossing zero and31/32J wins/losses. Its tentative preference was to retain
timely ordinary capability, favor S2 as the economical reference and not buy
exhaustive-search expansion on this increment; quality, path and adverse worlds
remained material. It explicitly had active-choice/block evidence and prior
interpretations still to check, with the full reader pending. That unfinished
message does not authorize a scientific disposition or further investment.
The runner's complete summary and192world artifacts remain available, including
positive/adverse outcomes; the DM has not completed the independent read or
answered the prior predictions at the study boundary.

At pause, the only unpublished owned changes were this notebook's checkpoint
and handoff entries plus compact `config.json`, `launch-status.json`,
`observer-terminal.json`, `process-exit.json`, `reader-resources.txt` and
`summary.json` in the canonical run directory. Publish these exact paths under
the shared-main writer lock, preserving all unrelated writers. Source/tests
are already clean and published. Existing tracked `launch-manifest.json` and
`admission-preflight.json` bind the launch. Ignored `raw/` contains the sole
canonical192compressed world records, declared content79442992bytes and
allocated79876096bytes at reconciliation. Retain stdout/stderr, private wait
request/state and the accepted source snapshot (allocated1649856512bytes);
direction scratch is8192allocatedbytes. No backup copy is created. No targets
were deleted and net reclaimed disk is0bytes: cleanup was stopped by the owner
pause, not a technical cleanup failure. Prior B01/B02 evidence stays unchanged.

Resume is conditional on an explicit owner lift, current lead/pause checks and
loading this handoff. Do not repeat the native192episode run. Inspect the same
terminal manifest/status/exit and source/raw identity, then rerun only the
read-only full reader on existing canonical artifacts from the accepted
snapshot using the configured CPU interpreter and `PYTHONDONTWRITEBYTECODE=1`.
Write any resumed reader timing to a new `reader-resources-resumed.txt`, keeping
the interrupted-reader witness and cost. The full reader must produce its
complete192/192 `reading.json`; do not splice a39-row prefix into a verdict.
Then resume the same independent critic, or transparently recover its unfinished
review with these exact sources if the helper cannot be resumed, preserving the
provisional message. Only after complete reading/review may the DM resolve
predictions, publish its material RESEARCH/background judgment, recommend the
next investment to Root and perform measured evidence-aware cleanup. Those
steps are all presently paused, not implicitly approved or automatically queued.

## 2026-09-29 - B03 Recovered Reading Responsibility

Owner explicitly resumed the Root workflow at21:59UTC with “阅读handoff 我们继续工作”.
Current Root `01a0ef2b-a391-7693-a748-60e24be246ae` recovered this unfinished
responsibility as native DM `/root/dm_radio_recovery`; this is not a resumed
old session or a newly selected study. Root's native follow-up could not find
the old child and the old Root was not loaded. The published resume/routing
commit `ecd5b2583` lifts only the authorized pause and preserves launch-bound
lead `Codex DM (native child)`, original source, operation and evidence. No
worker, observer or scientific episode is relaunched.

At22:00UTC the recovered DM found all named old native/reader/observer PIDs
absent. The accepted snapshot HEAD remains exactly
`2bff85091f85f6d52fc0344d0329b4fc39fa6d5c`; current direction source/tests have
no diff from it. Summary SHA256 matches the handoff, and all192raw digests and
sizes match their retained manifest entries:79,442,992content bytes. Neither
`reading.json` nor a resumed-reader timing file exists before recovery.

Rerun only the existing full read-only reader from that snapshot with the
configured local CPU interpreter and `PYTHONDONTWRITEBYTECODE=1`, retaining
the original interrupted timing and writing new cost to
`reader-resources-resumed.txt`. It reconstructs all192episodes/49,152saved
transitions, with zero new native steps, fits or optimizer updates. The old
39episode/253.66CPU-s verification remains paid interrupted work, not a prefix
checkpoint; the complete rerun is expected to be roughly20minutes from that
partial rate, with actual time recorded rather than a new scientific cutoff.
No changed source, comparator, outcome rule or repeated engineering review.

Recover the unfinished result diagnosis in a new registered ResearchCritic
with separate context and original evidence first. Preserve the old provisional
advice above, but do not call it a completed review or feed it as the desired
verdict. The critic will read the previous predictions and supporting/adverse
B01/B02 evidence after reconstructing B03, then confront the complete reader.
Resolve the fixed predictions and publish the material result/standing and any
useful background correction before measured cleanup. No successor launch is
assigned; the substantive recommendation returns to current Root.

The fresh22:01:42UTC local memory witness passed with10,251,472,896physical/
effective available bytes above4GiB; it is retained as
`reader-preflight-resumed.json`. Full reader runs in exec36521, PID4149209
under time parent4149208, with the same snapshot and output path. These are
reader identities only, not replacement native-run handles. The recovered
ResearchCritic is `/root/dm_radio_recovery/result_diagnosis_recovery` in a
separate context; no source or record write is delegated to it.

## 2026-09-29 - B03 Complete Reading

### Complete Evidence and Native Outcomes

The recovered full reader exited0 after192/192episodes and49,152saved native
transitions. `reading.json` is `VERIFIED_COMPLETE`, bound to original source
`2bff85091f85f6d52fc0344d0329b4fc39fa6d5c` and summary SHA256
`554d27275b84c69479a1560c0ee9fa74be112fd933c6f60518c9b592bcb5edc1`.
Its SHA256 is `765f4cffedbde6deb442b2b9139d701a9da2a8fb8aa158bae4de0bc1489a0d12`.
The complete config, original native/observer/exit records, all per-world
outcomes and paired differences remain in
`runs/uav_radio_activation/b03_two_tick_delivery_a01/`. Recovery added zero
native episodes, steps, fits or optimizer updates. The original192episodes/
49,152steps/0fits were neither restarted nor extended.

The reader verified all192raw identities and79,442,992content bytes, seeded
initial geometry and shared resets, native clipped motion, masks, radio and
reward, observations, C proposals/counters, actual team commands, both report
and arrival clocks, final half-block, candidate enumeration/selection, packet
identity and timing. Maximum native J reconstruction error is5.55e-17; SINR
and observation errors are zero. Candidate physics coverage is every retained
R mask score plus the predeclared S2/T2 subset:10,477/14,589candidate pairs.
It does not independently recompute every T2 matrix entry. Retained engineering
scalar/kernel checks supply their original separate coverage; shared-kernel
reconstruction alone is not an independent numerical proof.

World-average complete endpoints over64paired reset worlds are below. J,
served users and quality are per-tick means; p10/minimum are first computed
within each world, and path is per UAV.

| Arm | J | Served Users | Quality | Service p10 | Minimum Service | Path m/UAV |
|---|---:|---:|---:|---:|---:|---:|
| R |.466315|28.755127|.212478|27.132813|11.781250|2446.52|
| S2 |.482829|30.259277|.197330|27.687500|11.750000|4302.42|
| T2 |.483682|30.422363|.192562|27.851563|11.750000|4553.44|

The intervals below are descriptive paired t95 over reset worlds, conditional
on this host/load and realized deadlines. They are not training-instance or
hardware replication, physical safety, or equivalence tests. Full precision
and all signed world effects remain in the summary.

| Contrast | Mean J [t95] | Users/Tick [t95] | J + / - / = | Service + / - / = |
|---|---|---|---|---|
| S2-R |+.016514 [.010983,.022044]|+1.504150 [1.037317,1.970984]|48/16/0|53/11/0|
| T2-R |+.017367 [.012025,.022708]|+1.667236 [1.221056,2.113417]|53/11/0|54/9/1|
| T2-S2 |+.000853 [-.001805,.003510]|+.163086 [-.085845,.412016]|31/32/1|32/30/2|

Both two-tick packages improve complete mean J and service against original R.
The extra T2 increment over competent S2 is unresolved, not zero or equivalent.
Mean quality falls by.015148/.019916 for S2/T2 against R; both descriptive
intervals are below zero. T2-S2 quality is-.004768 [-.009032,-.000504].
The native J arithmetic weights service share.7 and quality.3, so larger mean
J coexists with this quality cost; that arithmetic does not identify a causal
failure mechanism or license changing the objective.

S2/T2 increase mean path by1855.89/2106.92m per UAV against R, with58path
increases each. These are measured movement costs, not battery consumption.
S2-R service p10 is+.554688 [-.076740,1.186115], with15adverse worlds;
T2-R is+.718750 [.127518,1.309982], with14adverse worlds. S2 loses7p10 users
on29307028; T2 loses5on29307062. All arms have zero zero-service ticks and
zero longest outages on this finite panel; this does not establish safety.
Minimum service is identical to R in63worlds and two users lower in29307020
for both new arms. Raw records locate that loss at startup transition1:
S2/T2 serve11while R's world minimum is13. It stays in the complete endpoint
despite preceding the first new-plan arrival; no startup trimming is used.

All adverse worlds are retained, including S2-R's largest J/service loss on
29307006 (-.029503J/-2.613281users), T2-R's largest J loss on29307042
(-.029652J/-1.117188users), and its largest service loss on29307062
(-.018825J/-1.996094users). The strongest common positive29307060 gives
S2-R +.075043J/+7.289063users and T2-R +.073347J/+7.230469users, while
adding3482.24/3306.01m per UAV. Mean gains do not erase these world tradeoffs.

### Executed Choices, Forecasts and Timing

The targeted intermediate change occurred. Each S2/T2 arm delivered all4096
rounds with mean actual-command report age887/254=3.492126ticks and maximum5;
the original B02 four-tick contract had mean5.5. R here remains younger at
2.494118(maximum4). Only the designed initial2ticks are excluded from S2/T2's
age metric, never from J/service. No startup command persisted beyond nominal
first delivery and no actual deadline fallback occurred.

At their own states S2/T2 changed1748/2031C proposal commands, and all those
changes altered executed displacement; none was only a clipping alias.
They reactivated121/377previously silent rotating members. On T2's4096visited
states, joint search selected330strictly better predicted-J pairs than its
both-order S2 shadow, in63worlds;324changed the member's executed displacement
and225were strict silent-move/reactivate advantages. Mean same-input matrix
gaps are+.000535J/+.062927users. These shadows are conditional on T2 states,
not another complete S2 rollout and not substitutes for T2-S2's native endpoint.

Post hoc inspection of supporting/adverse witnesses uses saved native paths,
not new counterfactual episodes. In29307011, S2/T2 have identical prefixes
until transition2; T2 chooses(q13,mask7), S2(q16,mask14). The first affected
block gains.009926J/.5users (predicted J gap.009937), and complete T2-S2 is
+.034239J/+3.613281users. In29307042, also first diverging at transition2,
T2(q6,mask21) versus S2(q2,mask19) gives a genuine first-block gain
.007375J/.75users, close to predicted.007468J. Complete T2-S2 is nevertheless
-.026838J/-1.703125users. Thus active useful joint choices can survive in a
full positive package without establishing the extra exhaustive program's
complete incremental value. The prior local-gain/later-loss constraint remains.

Selected commitment forecasts have mean position error approximately.325m
for S2 and.321m for T2 across offsets3..6, with maximum.714m. R's offset5
error is13.463m on average. Accurate blocks do not by themselves identify
complete usefulness; the actual native comparisons above answer that question.
This is a new-world complete contract comparison, not a paired B02-to-B03
latency intervention. Changed feedback/commitment, C proposal evolution and
later endogenous trajectories remain coupled; neither the sign change against
R nor lower report age identifies latency as the cause of B02's losses.

Each arm used8704recurring bytes per episode,557,056over64worlds, plus the
separate400byte registered map. All4096rounds per arm met their deadlines.
Maximum observed planner wall times are.045286s(R),.179326s(S2) and1.428485s(T2).
The latter, on29307004, leaves only.027515s below its1.456s computation window;
with.544s airtime it is1.972485s. This is successful measured execution, not a
deadline guarantee under different processors or load, nor a physical link or
switching-cost measurement.

### Cost and Exposure

| Work/Behavior | R | S2 | T2 |
|---|---:|---:|---:|
| Candidate requests |126976|475136|3428352|
| Unique candidate scores |126976|302953|3428352|
| Mask-state reductions |505920|1202360|13606272|
| Geometry snapshots |16320|438912|438912|
| Prefix model ticks |0|8192|8192|
| Transmitter-on ticks |55947|57814|58040|
| Mask bit flips |1281|1099|1708|
| Empty-discovery fallback decisions |6548|6111|6053|
| XY-boundary UAV-ticks |815|2334|2080|
| Scheduler CPU seconds |92.331728|257.177695|2479.113128|
| Complete episode CPU seconds |121.231970|277.046641|2501.254461|

Actual combined work is4,030,464requests,3,858,281unique scores,
15,314,552mask-state reductions,894,144scored geometries and16,384prefix ticks.
All arms together made61,440C decisions,1,658,880C candidate trajectories and
6,635,520C model ticks. The fixed upper work was respected; caching removes
repeat S2 queries but does not remove their request exposure. C's measured
CPU is included in S2/T2's full planning timer and reported separately in the
summary; R's C work is part of episode cost rather than its radio timer.

T2 uses9.64times S2's scheduler CPU and34.753247additional episode CPU seconds
per world. This is a real cost with no established additional complete J/service
increment on this panel; it is not an equivalence finding or a universal ban on
joint search. The useful S2 package costs2.434604additional episode CPU seconds
per world relative to R, alongside its movement/quality tradeoffs.

Original whole native worker:2912.684244s wall,2899.402799user+2.611851system
=2902.014650CPU-s,131,156KiB process-lifetime peak RSS, one compute thread.
The interrupted pre-pause reader remains253.62s elapsed/253.66CPU-s,
102,072KiB peak RSS, signal15/session exit143, no complete result. The recovered
reader is a full rerun, not prefix continuation: inner955.791655s wall/
955.369038CPU-s; whole process956.78s wall,936.32user+20.04system=
956.36CPU-s,102,600KiB peak RSS, exit0. Both timing witnesses are preserved.
Peak RSS values describe separate processes, not an additive simultaneous peak.

B03 native plus both reader attempts cost1.142232CPUh. Together with the
previous B01/B02 native/readers' approximately1.300526CPUh, this is about
2.442758CPUh across576native episodes/147,456steps/0fits. These phase costs
exclude incompletely metered adviser, engineering and other support; they are
neither total project cost nor elapsed time across the owner pause. Recovery
changed no executed scientific source and required no repeated engineering
review or test suite.

### Recovered Independent Scientific Diagnosis

Registered ResearchCritic
`/root/dm_radio_recovery/result_diagnosis_recovery` completed the interrupted
review's responsibility in a new separate context, without DM/Root conversation
inheritance. This does not pretend to resume the old critic. Navigation exposed
brief inherited-study standings; it reconstructed B03 before reading detailed
prospective reasoning, the preserved provisional advice and Pro explanations.
Its substantive return is condensed below, preserving scope and disposition.

> Retain the timely ordinary-control capability, prefer S2 as the economical
> conditional reference, and stop automatic clock or exhaustive-search
> expansion. B03 develops complete J/service performance beyond R, but does
> not establish that T2's extra search is worth selecting over S2. T2-S2's
> unresolved effect is not equivalence or proof of zero possible value.
>
> All complete gains and tradeoffs matter together: both new arms improve
> mean J/service, lose quality, add roughly1.86/2.11km per UAV and retain
> adverse service-tail worlds. Startup minimum loss29307020 stays in the
> complete endpoint; zero outage ticks establish no safety guarantee. Keep
> strong positives such as29307060 and adverse29307006/29307042.
>
> The intervention was active, not an unexecuted mechanism. The330strict
> T2 shadow advantages,324displacement differences and225silent-member
> move/reactivate opportunities are real, but describe T2 states rather
> than complete S2 trajectories. In29307042 a checked first-block native
> gain is followed by complete T2-S2 loss. Neither nonactivation nor wholly
> fictitious model gains explains the result; useful local choices do not
> determine subsequent trajectory value.
>
> The strongest ordinary explanation is competent finite planning under a
> revised control contract. S2 already scores the full team and tries both
> sequential orders. It obtains the established complete gain without T2's
> larger enumeration. This strengthens timely ordinary composition and
> weakens the case for exhaustive search in this contract; it establishes
> neither a learning benefit nor a special coordination mechanism.
>
> Prior predictions resolve differently: more timely execution occurred;
> committed choices were accurate and consequential; both new programs
> extended complete mean J/service beyond R; earned T2-over-S2 value remains
> unresolved. The frozen simpler-composition branch therefore applies.
> Different B02/B03 worlds, startup/terminal semantics and clocks preclude
> pure latency-causality attribution.
>
> T2's9.64fold scheduler CPU and34.753extra episode CPU seconds per world
> reinforce the allocation judgment without being subtracted from J. Its
> worst1.428485s round leaves only.027515s inside the declared window. This
> successful observed execution is not load robustness. Preserve both
> interrupted and completed reader costs: B03 native/readers1.142232CPUh,
> B01-B03 approximately2.442758CPUh, with other support incompletely metered.
>
> Recommend no additional radio run now. The smallest remaining observation
> required here was the complete saved-data reader, which has finished.
> More worlds could refine T2-S2, but no specified adoption choice presently
> requires that precision. Another clock, deeper search or learned program
> needs a substantive prediction and S2 as a competent comparator. This is
> not exhaustion of the parent question. Retain the capability and return
> allocation to Root's requested synthesis, without automatic expansion or
> relabeling the useful result as radio-control failure.
>
> Checked frozen configuration/manifest/exit and23source dependencies against
> accepted snapshot/commit; all192raw endpoints and64seeded common reset
> geometries; detailed radio/clock/block evidence in18B03 files spanning
> positives, adverses, startup and near-deadline cases; every recorded T2
> shadow gap; B01/B02 summary-reader bindings and15historical raws plus
> complete diagnoses; full next-investment Pro advice/decision and relevant
> background; final B03 reader hashes,192/192coverage and timing. The reader's
> candidate physics coverage remains the declared10477/14589S2/T2 pairs.
> I did not duplicate the full reader or recompute every candidate. Physical
> costs, different processor loads, longer missions and learning generality
> remain unverified. No edits, new episodes/fits, children or Pro sends.
>
> MATERIAL_DISSENT: no. Retain S2's conditional capability and decline an
> unearned exhaustive-search expansion, preserving R, T/T2 local capability
> and all adverse evidence.

### DM Interpretation and Next Investment

Accept this complete independent diagnosis. The prospective conditional
branch **S2 exceeds R without an earned extra T2 increment** is the supported
disposition. Retain S2 as the economical J/service reference for this explicit
two-tick-delivery/four-tick-hold contract, alongside R as a lower-travel,
higher-quality alternative. T2's demonstrated joint choices and individual
positive worlds remain capabilities, not a discarded failed architecture.
They do not establish an additional complete package benefit on this panel.
No default physical adoption, statistical equivalence or universal ordering
is asserted. One adequate independent result review covers this decision;
no distinct unresolved expertise question calls for another Pro round here.

The inherited shared-background judgment changes in a useful way. B02's
adverse R comparison was a property of that complete contract, not evidence
that motion/activation composition cannot develop R. B03 supplies a positive
ordinary composition and an applicable simpler comparator. The older lesson
that accurate prediction and local joint gains do not ensure trajectory value
survives, now within an overall useful package. Local opportunity is supported,
the lawful representation and control were exercised, finite learnability is
untested (zero fits), and complete conditional usefulness is strengthened for
S2/T2 versus R while extra exhaustive value is unresolved. This does not turn
the shared map, finite planning or longer travel into a learning contribution.

End the present clock/exhaustive-expansion investment and publish the useful
positive result. An unchanged larger panel would chiefly refine an increment
with no selected deployment threshold or consequential precision requirement;
another clock or deeper search has no tested new prediction here. Learning is
still an open different investment, not empirically refuted and not silently
authorized by this result. Retaining the demonstrated S2 capability is more
useful than an automatic repair or a renewed attempt to make T2 win. No new
study, tail penalty, clock, world panel or fit is selected.

At this assigned substantive boundary the direction becomes reserve/idle,
with no unread result, active producer or scientific-review dependency. Root's
already-requested round synthesis owns the next cross-question allocation;
that is not a blocker or an approval requirement for this publication/cleanup.
Return the evidence and recommendation through native child communication,
not App messaging. Preserve useful ordinary-control source/tests and the sole
required raw copy; remove reconciled snapshot, scratch and redundant logs only
after publication and live-consumer checks.

### Publication and Measured Cleanup

Complete compact evidence, recovered independent review, interpretation and
own RESEARCH standing/shared-background correction were committed and pushed
at `7e43ebc6c14bc825251daf88a75462f3d66f23e9`. Original executed source
remains recoverable at `2bff85091f85f6d52fc0344d0329b4fc39fa6d5c`; no code
semantics changed during recovery. This publication preceded deletion.

Import/test/entrypoint inspection retains useful B01/R, B02 and B03 protocol,
search, collection and reconstruction code and its focused tests. B03 consumes
B01's retained reader/metrics and B02's command/search helpers. These small
published definitions preserve the useful ordinary capability and its historical
comparison; no unused replacement implementation or other direction code was
removed. Shared C and the radio kernel remain unchanged.

Both old native identities, both old reader identities, the old observer and
the recovered reader/time parent were absent; the new ResearchCritic completed
its source reading and returned its final verdict. The original observer is
still stopped at generation3 with no wake. No active operation, accepted Send,
reader or helper consumes the snapshot. No new observer was armed in recovery.

Exact-target snapshot-GC preview and apply passed using the documented
`--sudo-process-scan` read-only process inspection. The collector verified
terminal native identity, clean source, no live process reference and durable
`refs/heads/main` reachability, then removed only the accepted B03 snapshot.
Original operation claim, manifest, exit witness, compact result and source
commit remain. Its registered worktree entry is also absent. No refusal or
cleanup blocker occurred, and no backup/archive/retention copy was created.

Allocated bytes immediately before deletion, measured with `du -s -B1`:

| Deleted Target | Allocated Bytes |
|---|---:|
| `.git/hmasd-launch-sources/3d9c57d229864a02a8679bdf903af92e` |1649856512|
| `temp/directions/uav_radio_activation/` (only retired `b03-wait.json`) |8192|
| `experiments/candidates/uav_radio_activation/b01/__pycache__/` |57344|
| `experiments/candidates/uav_radio_activation/b02/__pycache__/` |24576|
| `experiments/candidates/uav_radio_activation/b03/__pycache__/` |69632|
| `tests/experiments/candidates/uav_radio_activation/b03/__pycache__/` |57344|
| `runs/uav_radio_activation/b03_two_tick_delivery_a01/stdout.log` |28672|
| Same run's empty `stderr.log` |0|

All eight exact targets are verified absent, from1,650,102,272allocated bytes
to zero: **net reclaimed1,650,102,272bytes**. This is working-tree target
reclamation, not Git-object shrinkage or whole-host free-space change amid
other writers. Stdout contained exactly192progress rows already represented
in the complete summary; stderr was empty. Removed caches held only rebuildable
bytecode and scratch only the retired request. No required unique data moved.

The sole canonical192raw files remain at
`/home/fires/hmasd-wsl/runs/uav_radio_activation/b03_two_tick_delivery_a01/raw/`,
79,442,992content bytes /79,876,096allocated bytes, with per-file digests in
the summary and complete verification above. Both reader cost witnesses,
full positive/adverse/failed records and earlier B01/B02 evidence remain.
No deletion target is left over. B03 is fully read and published with no active
producer, unread review, new successor or unreturned helper; the recommendation
now returns to Root through the native parent channel.

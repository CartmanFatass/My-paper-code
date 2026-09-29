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

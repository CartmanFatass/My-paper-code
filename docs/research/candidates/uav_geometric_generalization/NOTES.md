# UAV geometric generalization

## 2026-09-28 - Assigned question and source-supported comparison

Root assigned this native DM `/root/dm_geometric_generalization`, parent `/root`
(chat `01a0e560-4333-7b03-8ff3-759a4add1d9a`), the question: does coordinate dependence
of the retained S7 SET constitute an actionable deployment limitation, and can a fixed
geometric deployment program improve complete native service/J? This is a conjecture,
not a conclusion from headings or boundary occupancy. The direction owns its five
standard directories on shared main. Claude retains `energy_relay_benchmark`, its
BS-only/cluster-only open-loop probe, and possible representation/decoder learning.
This study does not execute those probes or train a representation.

### Evidence and working explanation

Relevant published background read at `6dfbc9731e911de00d76d2b812063a741a4a0dfb`:
[native consequence](../../RESEARCH.md#1-rl-研究的是交互后果不是组件名称),
[complete deployment evidence](../../RESEARCH.md#6-实证研究是在具体条件下缩小解释空间),
and [symmetry and joint structure](../../RESEARCH.md#structural-research-background).
The effect on this design is concrete: native J, service, return cost and tails are
co-primary readings of usefulness; geometric proxies cannot stand in for them; symmetry
must bind the actual information and transition, including identities and initial law.

The original evidence is the
[Stage 1 result and subsequent independent corrections](../energy_relay_benchmark/NOTES.md#2026-09-27--stage-1-result-one-set-development-fit-at-fixed-exposure-read-by-the-pre-registered-readings-b02_s1_set_a01--b02_s1_set_a01r-final-model-c06-957001957032-read-once),
the retained development/holdout panels, and
`runs/energy_relay_benchmark/b04_deployment_reading_a01/{manifest,heading_stat,blob_stat}.json`.
The one retained c06 training lineage improved development QoS from .209/.243
deterministic/stochastic to .437/.438, with native J about 1276/1281; holdout was
.462/.440. These learning and mode facts remain. The two new independent SET endpoints
in `energy_relay_baselines` are technically missing, not negative learning outcomes.
The Stage 1 independent correction rejects the claim that post-charge service had
reached H_local: it compared unequal time windows. Native J already prices return cost.

The complete Pro answer published at `ee02de596` and the peer adoption at `6dfbc9731`
were read. R_map measures angle concentration, not geometry independence; near-zero
displacements and the first-service -1 sentinel qualify the old reader. The conclusions
of no useful per-agent reward signal and chain-feasible decoding were also withdrawn.
Those corrections rule out a mechanism claim based on the old heading table. A useful
closed-loop deployment program would be an empirical package result conditional on
this c06, not proof of a finite-training or representation bottleneck. A null or adverse
program result would not refute every geometric representation or the peer's probe.

### Feasibility: physical conjugacy is not initial-law invariance

Source mapping used an independent bounded read-only Scout, with the policy interface
traced by this DM. No new scientific fit, episode or result step has run.

- The actual host is `UAVEnergyAwareRelayEnv` in
  `envs/pettingzoo/relay/energy_aware.py`, subclassing `routed_core.py`; no separate
  `scenario7.py` implements this study. The B01 builder uses S7-S2, H3000, 8 UAVs,
  30 mobile users, one BS, two stations, square 8000 m bounds, dt=1 and 30 m/s.
- Horizontal actions are Cartesian normalized velocity, not headings. The first two
  components undergo a common radial speed cap; z and dock request are separate
  (`energy_aware.py:1619-1727`). Signed x/y permutations therefore preserve the action
  domain and this map. Arbitrary rotations do not preserve the square/action box;
  translations do not preserve the map boundary and are excluded.
- D4 matrices acting about the map center are candidates for conditional physical
  conjugacy: radio and visibility use distances; energy uses horizontal norm and
  vertical speed; shield/limp-home uses station displacement/distance; guard uses a
  geometric capacity test and an invariant dot product. RPGM angular draws, waypoint
  coordinates and station jitter must be transformed with the state for paired
  transition checks. Same integer seed alone does not provide that coupling.
- The actual reset law is not D4 invariant under fixed agent identities.
  `routed_core.py:1115-1198` places eight indexed UAVs on the first eight cells of a
  row-major 3x3 grid, in the same orientation in each random corner. Random corner
  selection is not reflection/rotation of that indexed grid. We do not permute IDs:
  nearest/connection/charging ties use stable index order. Any use of D4 below is a
  transformed-input deployment heuristic on the original world distribution, with
  possible out-of-training-distribution input, not a distribution-preserving theorem.
- The 365-field observation transforms own absolute xy and all relative xy pairs,
  including radius-gated/sorted users, peers, BS cache, overload and energy suffix.
  Zero padding remains zero. Entity identity/order stays fixed; distances and scalar
  fields stay fixed. The 306-field state transforms UAV/user/BS/station absolute xy
  and user xy velocities; all energy/connection/scalar fields stay fixed. The adapter
  casts to FP32 without clipping the state (`env_adapter.py:551-560`).
- The flat SET actor holds state, all eight observations and ego one-hot every k=10
  (`hmasd/agent.py:1294-1386`). Each transform needs its own recurrent state and held
  snapshot from episode start, following the actual common executed history. It is
  invalid to rotate only current local observation or reuse an identity-frame GRU.

### Provisional complete study for the Root scientific review

This is a proposal, not an accepted result launch. The Root is combining the independent
scientific selection review; this DM does not create a duplicate critic for the same
decision. We continue necessary correctness implementation while that review is open.

One retained c06, no optimization, on 16 fresh common worlds (IDs to be fixed before
publication of executable inputs), H3000 and the same production shield (entry 0,
exit .05), FP32 CPU, native environment/reset distribution unchanged:

1. P: original c06 deployment.
2. G: maintain one frozen recurrent stream per admitted D4 transform; transform the
   legal input history, inverse-transform each proposal, then take the arithmetic
   action mean. No frame is selected using a result.
3. V: a comparison for averaging-induced magnitude/scalar changes. At the same legal
   history compute P and G, use P's horizontal direction with G's horizontal norm,
   and G's z/dock values. Use zero horizontal action if P's norm is zero, and record
   that case. Thus G-V compares the full closed-loop direction rule with this fixed
   magnitude/scalar comparator; it is not a state-held causal mediation estimate.
4. H: frozen H_central@10 with its existing information and production shield, once
   per world, as a capable ordinary complete-task reference.

P/G/V each have deterministic and one stochastic mode. This is 7 programs x 16 worlds
= 112 episodes, at most 336000 native transitions, 0 fits and 0 optimizer updates.
Stochastic stream construction is still an implementation/design question: preserve
P's native marginal distribution, address common world/action draws prospectively,
and do not mislabel independent frame averaging as matched stochastic variance.
If a trustworthy coupling or any purported transform fails correctness, revise the
proposal before launch, do not silently weaken the input contract.

Primary readings: paired world-wise G-P and G-V native J and QoS/actual-step in each
mode, all world values and losses, native components and return-risk tails, cutoff/
depletion, minimum battery and reserve exposure, first-service censoring, fixed-clock
early service, actual horizontal speed/guard/shield use, and measured inference CPU/
wall/memory. H gaps are capability comparisons, not information-optimal bounds.
Exploratory conditional-world intervals do not add independent training instances.
Reduced wall occupancy alone cannot retain the program. A positive G-P but absent
G-V advantage would retain the simpler magnitude/scalar explanation; positive G-V
with complete value supports this direction rule, not a unique training mechanism.
Mixed or adverse outcomes terminate this exact package's automatic expansion; no
new seed, fit, frame selection, canonicalizer or repair is pre-authorized by scores.

Prospective cost: 0 fit/GPU time; 112 full episodes and 336k maximum environment
steps; the G/V policies require up to eight frozen recurrent forward streams per
step. Batched lanes can share weights, not recurrent memory. Tentative node CPU
wall is 1-3 h on wsl_4070, conditional on worker count and inference overhead;
historical 64-episode learned evaluations took about 13-29 min and are only a scale
reference. Approximately 1-2 h implementation/tests/engineering review and reading
is additional. These are estimates, not an exposure or wall stopping rule. Node
choice/admission and source publication are performed only for an actual launch.

### L0: bounded symmetry adapter preparation

Deliverable: a direction-owned S7-S2 D4 input/action adapter and focused correctness
tests, sufficient to determine whether this proposal can be implemented honestly.
Owned files: `experiments/candidates/uav_geometric_generalization/b01/symmetry.py`
and matching test module under `tests/experiments/candidates/uav_geometric_generalization/b01/`.
This task does not implement a result runner, evaluate a score panel, alter the shared
host/learner, or write any peer directory. Preserve native layout, entity/ego identity,
zero padding, scalar fields, z/dock, source arrays and dtype; transformations form D4
with explicit inverse/composition. Use the existing legal observation layout helper.
Checks should cover all coordinate blocks, round trips/group composition, source
immutability and physical/schema correspondence including distances, speed caps and
shield behavior. Tests create only pytest-managed scratch. A physical paired-step
fixture must transform exogenous mobility consistently, or identify its limitation;
it must not claim same-seed equivalence. Budget is bounded correctness work only;
stop and report a noninvertible encoding or reachable contradiction before adding
workarounds. The DM accepts the diff/checks and obtains independent engineering
review before any high-risk result executable is used.

### Pre-result design refinement: one-frame canonical deployment is the simpler candidate

The P/G/V proposal has a real drawback beyond computational cost: averaging valid
joint proposals can cancel a useful commitment, while stochastic frame averaging
changes variance. Before any result exposure, the DM recommends the simpler complete
candidate C for the combined scientific review to compare with G/V or a justified stop.
C chooses one x/y reflection at reset from the legally available team mean spawn xy,
mapping the spawn corner to the north-east (NE) quadrant; it keeps that same reflection
for the entire episode, transforms all actor inputs, and inversely transforms actions.
One original GRU and k10 snapshot evolve from reset; there is no action averaging,
frame switching, additional policy sample, action norm change, or replayed history.
P/C can use the unchanged native deterministic/sampled action paths and equal per-world
policy random seeds. Common noise is in policy coordinates, not a claim of identical
physical noise after reflection.

NE is explicitly chosen using already exposed c06 heading evidence (the eight mean
early headings were mostly south/west); it is not a neutral or outcome-blind discovery
of a privileged frame. The conjectured intermediate change is more useful initial
inward displacement on the original worlds, with complete service and J improvement
the required native consequence. The alternative is that learned geometric/index
dependencies are already useful, and this transformed input harms them or yields no
complete benefit. The fixed-ID reset-grid support mismatch remains and can explain
either result. C is a deployment heuristic, not a proof of a symmetry of the reset law.

This option costs 16 fresh worlds x (P-det, P-stoch, C-det, C-stoch, H_central@10)
= 80 H3000 episodes, at most 240000 native steps, 0 fits/updates, and no GPU.
Tentative CPU node wall is 40-100 min with two workers, plus engineering and readback;
actual inference and node resource use will be recorded. This supersedes no accepted
batch: neither version has run. The same transformation L0 serves either program.
The Root scientific review will resolve the first complete comparison; we will not
run G/V and C as an undeclared search over favorable deployment programs.

Neither option estimates the peer's withdrawn Block 2 contrast: the original policy
on a regenerated rotated physical world versus its original world (including its
specific agent rematching rule). P/G/V acts on unmodified original worlds; C chooses
a world-dependent reflection and likewise leaves the simulator/reset law untouched.
Conditional physical conjugacy can relate a single fixed reflected policy to a
fully reflected physical world with coupled exogenous randomness, but that is not
the peer's regenerated-grid estimand. This direction promises no replacement value
for peer decision row D and adds no pairing panel because the peer withdrew one.

### Independent scientific review and selected B01 contract

Root returned its independent Scientific Reviewer's substantive recommendation by
native message on 2026-09-28: choose P/C only, decline P/G/V and do not add the peer's
rotated-world Block 2. The reason was that one fixed legal coordinate transform for
the whole episode answers a narrow real deployment question while avoiding eight
lanes, cancellation of averaged actions and eight-sample stochastic denoising.
The review retained the objections that NE was chosen from exposed south/west
headings and that the indexed spawn law is not D4 invariant. Root adopted that
recommendation. No unresolved material disagreement remains for this comparison.
This is a pre-fixed c06 coordinate-canonicalization deployment package, not a symmetry
guarantee or a general geometric-generalization claim. A result does not substitute
for the peer probe or establish/refute representation learning. The substantive
recommendation is recorded here without waiting for the combined review's longer
publication; no duplicate scientific review was commissioned by this DM.

The final planned batch is `b01_pc_ne_a01`: fresh worlds **280928401-280928416**;
P-deterministic, P-stochastic, C-deterministic, C-stochastic, H_central@10; H3000;
80 episodes / at most 240000 native steps; 0 fits / 0 updates. World IDs had no match
in candidate notebooks at selection. Each arm rebuilds the native S7-S2 world with
the same integer world seed. P/C stochastic draw 0 uses the existing B01
`sample_seed(925031, world, 0)` implementation, seeded immediately before the first
policy call; the same native single-sample path is used in both arms. P/C therefore
share raw policy-coordinate random streams without claiming identical physical
innovations after reflection. The world has its own seeded native RNG. Numeric
contract: CPU FP32, two workers, one Torch/BLAS thread per worker.

C chooses `MIRROR_X` when the initial mean of the eight legal own-x observations is
below .5, `MIRROR_Y` for mean own-y below .5, their composition when both, and identity
otherwise. The chosen frame is fixed until episode end. It acts on all observations
and the complete state before the ordinary SET step and inversely on the four-action
proposal afterwards, leaving vertical and dock unchanged. The production shield and
native backhaul guard receive physical-frame actions and unmodified observations.
No identity remapping, new information, normalization fit, GRU reset mid-episode,
snapshot refresh change, action averaging, clipping change or policy update occurs.

Frozen model: c06, training seed 925031, 1.2M recorded transitions, agent.pt sha256
`41aa4ff0be5d55f924d8388af055fb087d76c1f517497e69c26d7962ce041bb3`, fingerprint
`a7c54b470441b8e742459e47a533a41c58534c36288ece0e9eb026a3b544c39c`.
The runner checks the recorded configuration and checkpoint identity. Existing c06
bulk is an input belonging to the peer; it is read-only and never moved or deleted.

L0 extension, owned by the DM: direction `run_b01.py` and `b01/study.py` plus
`test_study.py`. Implement the one-frame wrapper, native admission first, fixed
80-task batch, per-world compact result and retained raw traces, counts, RNG/model
identity, resource/inference timing and paired readout. Reuse the B01 production
evaluator, shield, model restore and H_central@10; change no shared file. Check
identity P against the original native evaluator on a short engineering fixture,
frame persistence/reset, transformed held snapshots/GRU continuity, unchanged
model/optimizer/normalizers, genuine first-service censoring, and admission order.
The independent engineering reviewer must inspect the executable transformation,
recurrent and execution boundaries before source publication and launch. There is
no automatic retry or extra panel if an attempt fails or a score disappoints.

The full combined scientific review and Root disposition are published at
`ee5799a2c` in
[the expanded native-DM review](../../archive/2026-09-28/RESEARCH-expanded-native-dm-review.md).
The selected P/C contract above is unchanged. The peer subsequently restored its
distinct paired rotated-physical-world Block 2 (`cef84927c`); this resolves the
publication dependency misunderstanding and adds no panel to this direction.

### Engineering acceptance before publication

The bounded Implementer returned the adapter and tests without Git mutations; the
DM read and accepted the diff. Twenty-nine distinct focused checks passed on the
configured local scientific interpreter: the 27-check suite in 14.22 s, then two
serialization/failure additions in 2.85 s. The earlier test-only attempt to deepcopy
an agent failed on its logger RLock (23 passed/1 failed); restoring a second frozen
agent independently fixed that fixture. No production method or scientific scope
was changed to make the check pass. P deterministic and stochastic each matched all
original evaluator arrays over a 24-step native fixture. C retained one frame across
12 steps and the k10 snapshot boundary with matching GRU state against an explicitly
transformed reference history. C-stochastic and H also completed 24-step worker
fixtures with native output serialization. These are engineering fixtures on old
test worlds, not an exposed study panel or new training.

Independent `hmasd-reviewer` returned no material engineering finding. It reconstructed
the coordinate fields, recurrent and held-snapshot route, action inversion before the
physical shield, native RNG seeding, model/normalizer/optimizer freeze, admission order
and incomplete-result accounting. It independently ran 14 symmetry tests (5.19 s),
inspected the other fixtures, and checked final `study.py` sha256
`3be8154254d4ccf51ae43c4ec3c5165bd8ffa160239b1173fd4a24f52d23dd54`.
Its metadata suggestion was adopted: information is labeled per program, and resource
sums explicitly cover observed workers, with missing measurement listed. DM accepts
the implementation. Limits retained: no complete H3000 batch or actual spawned-pool
crash was tested in review; physical fixtures validate schema/speed/guard snapshots,
not a coupled-world trajectory theorem. The selected heuristic does not need that
theorem. Null post-1000 readings after a native early termination are not imputed as
zero; each paired metric reports its eligible worlds.

Result node remains wsl_4070 CPU, with two single-thread workers. A read-only check
found about 12.2 GiB available RAM and the retained c06 input at
`/home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01r/checkpoints/c06/`.
This is not admission; the launcher must freshly admit the actual node. Its shared
canonical checkout is behind current main with unrelated modified/output paths,
so no pull, sparse change or output movement is performed. The result uses a
launcher-managed source snapshot at published main and only this direction's
current control-row projection is updated when needed.

### B01 accepted on the fixed native handle

Exact inputs were published as `52986d5b005202b3ec77f8f556ad2a790541d0d7`.
Only the published direction row was inserted into the remote canonical index under
its writer lock; the existing dirty records, accepted outputs and sparse selection
were preserved. A fetch outside the configured network shell stalled and its own
three read-only Git processes were terminated. The configured `zsh -lic` fetch
succeeded, with existing shell-startup diagnostics and an unrelated auto-GC bad-tree
warning retained as environment facts. Neither issue changed the accepted source.

Configured-supervisor request `ugg-b01-pc-ne-a01` invoked the native launcher once.
It accepted the fixed P/C/H batch at **2026-09-28 03:57:52.350409 UTC**, on wsl_4070
CPU with two single-thread workers. Fresh admission measured **12,267,339,776 bytes**
available against the **4,294,967,296-byte floor**, with no failure reasons.
[Manifest](../../../../runs/uav_geometric_generalization/b01_pc_ne_a01/launch-manifest.json),
[preflight](../../../../runs/uav_geometric_generalization/b01_pc_ne_a01/admission-preflight.json)
and [launch status](../../../../runs/uav_geometric_generalization/b01_pc_ne_a01/launch-status.json)
are retained. Output is `runs/uav_geometric_generalization/b01_pc_ne_a01` on the
original canonical node. The original operation reference is
`/home/wu/projects/HMASD/.git/hmasd-admission/eff8b251972b81009cee314b6317a18465524521dff214627f4b6ededda22fa3.json`;
its immutable source is `.git/hmasd-launch-sources/ecdf1ff8296545498cffbc6b85e16d05`.
At 03:58:33 UTC, runner 866084 and supervisor 866083 were both running with matching
Linux identities and consistent records. No terminal witness or scientific result
has been read. Outer supervisor exit zero only confirms launcher completion.

`tools/hmasd_wait.py` generation 1 observes that exact operation, with request at
`temp/directions/uav_geometric_generalization/b01-wait-request.json` and owning native
child UUID `01a0e5fe-ac1d-7281-a9f9-bb810a00ca77`. Its first drain verified the running
handle. Root reports an independently observed app-server refusal to queue an unloaded
spawned child; therefore this native turn stays open and uses long deterministic waits
with same-handle drain/rearm. It does not change the target session, use App messaging,
repeat submission or infer collection from observer registration. Checkpoints rearm
only observation. Collection, complete reading and publication remain this DM's work.

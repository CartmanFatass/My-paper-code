Scientific ruling — D7.S local-only successor provenance

Stage reviewed: 180980ab6a00b02596f2b3f2adaefe759450120a

1. RULING
Select a modified B3: locally certified seed replay, not bare seed provenance

Do not reinstate the manifest apparatus as the default successor route. Under the user’s binding local-only compute rule, the smallest provenance mechanism is:

A registered episode key generates one bit-identical, complete episode state under one frozen local execution class, demonstrated across fresh processes and enforced on every conclusion-bearing run.

This is materially stronger than “the same seed was applied.” It is a local replay certificate over the actual generated state and trajectory.

The previous Route-A manifest requirement was selected to remove an uncontrolled machine boundary. That boundary has now been removed by user authority. Reinstating a manifest store, inventory, capture mode, loader, replay gate, and random-tape escalation before testing direct local determinism would violate replacement-before-accumulation.

The route is therefore:

B3-L — LOCAL_CERTIFIED_SEED_REPLAY

not unrestricted B3.

The successor episode key

For each episode, the protected identity must contain at least:

successor contract / population namespace
repository stage commit or source-tree digest
complete configuration digest
topology seed
pinned topology-coordinate hash
block = PART_A_CONTROL | FOCAL_AUDIT
episode index
episode seed
energy-permutation seed
user-world seed
continuation-stream derivation version
fingerprint-definition version
dtype binding
certified local runtime ID
registered process topology

The current seed derivation already namespaces user-world and continuation streams by contract, topology, block, episode, limb, phase, candidate, and replicate. That machinery is retained.

Local certification gate

Before the successor population is instantiated, run a development-only local replay gate on TOPOLOGY_SEED_DEV = 20260725. It must use two fresh interpreter processes—not two constructions inside one process—and the same execution class intended for the formal run.

Call the passing outcome:

LOCAL_EPISODE_KEY_REPLAY_PASS

The gate must establish exact equality for all of the following:

Registered inputs

episode-key fields;

topology coordinates and coordinate hash;

all derived seeds;

repository/configuration/fingerprint versions;

certified runtime and process-topology identity.

Initial world

all nine WORLD_COMPONENT_ORDER arrays;

shapes and dtypes;

per-component digests;

environment RNG state after world generation.

Final pre-action state

the complete state defined in ASSERTION_6_SCOPE below, after all registered initialization inputs have been installed.

Prefix and event

post-prefix exogenous-world arrays;

qualifying-event presence or absence;

event-conformance record;

focal identities;

legal candidate identities;

duty map and event snapshot identity.

Full registered continuations

stable horizon H
stable
	​

=139;

flex horizon H
flex
	​

=550;

lossless per-step exogenous user/cluster trajectory digests;

primary-G component sequences;

selected candidates and evaluation units;

branch-relevant bounds or their deterministic pre-bootstrap units.

Dynamic-path liveness

at least one exercised development trajectory must trigger a post-initialization user-waypoint or cluster-target regeneration;

otherwise the gate has not tested the RPGM path that previously motivated A2.

Production process topology

the formal worker count, process start method, PYTHONHASHSEED, BLAS thread settings, and any other execution-affecting environment variables must either be frozen identically or included in the certified runtime identity.

The old same-process observation that two constructions agreed on the nine world arrays is supporting evidence, but it does not establish cross-process reproducibility, complete pre-action identity, or full-horizon equality.

Fail-closed decision tree
A. Initial world or final pre-action identity differs
   -> LOCAL_EPISODE_KEY_REPLAY_FAIL
   -> canonicalize the initialization path and rerun
   -> do not select the successor population

B. Initial and pre-action identity match, but exogenous trajectories
   diverge during H_stable or H_flex
   -> select B2 / A2
   -> persist the exogenous process or its complete random/event tape

C. Seed-generated initial world still differs after initialization
   canonicalization
   -> B1 becomes the retained fallback:
      local manifest-defined initial worlds plus the same complete-state gate

D. Complete initial, prefix, trajectory, unit, and branch-input equality
   -> LOCAL_EPISODE_KEY_REPLAY_PASS
   -> B3-L is certified
   -> manifests and random tapes remain unnecessary

This tree preserves B1 and B2 as live fallbacks rather than discarding them. It selects the least complex route first and escalates only on an observed failure surface. That is the correct ordering under the project’s information-gain and reversibility rules.

Runtime identity must become enforceable

The current runtime_identity() is descriptive and deliberately defensive—its documentation says it must never cause a run to fail. That is appropriate for historical metadata but insufficient as the successor’s certification gate.

Retain it as ordinary artifact metadata, but add a separate, strict object:

CERTIFIED_LOCAL_EXECUTION_CLASS

A formal successor run must refuse to start if its runtime/process identity differs from the one that earned LOCAL_EPISODE_KEY_REPLAY_PASS. At minimum, bind:

workstation identity
OS and architecture
Python
NumPy / SciPy
BLAS implementation and runtime CPU features
worker count and process start method
PYTHONHASHSEED
BLAS/OpenMP thread variables
source-tree digest
configuration digest

A later runtime update does not invalidate an already completed result. It requires recertification before a new run or formal rerun.

2. ASSERTION_6_SCOPE
Retain complete pre-step identity; move it to the actual first-action boundary

Do not scope assertion 6 down to:

the nine world arrays;

event identity;

or equality of the final U
\*
 units.

The valid assertion is:

Two executions of one registered episode key have the same complete continuation-sensitive environment state immediately before the first source-control action.

Temporal boundary

Compute assertion 6 only after this complete order:

1. construct/reset the environment
2. restore and verify the pinned topology
3. generate the registered user world from its dedicated seed
4. install the registered initial-energy permutation
5. run the canonical post-pin/post-world/post-energy initialization barrier
6. materialize observations and global state from those final inputs
7. fingerprint
8. execute the first action

The historical gate fingerprinted before the registered energy profile was installed; two of its reported differences subsequently converged. The correction is to move the assertion to the true first-action boundary, not to delete fields from it.

State surface

The exact identity must cover every field that can affect:

source-control actions;

transition dynamics;

event and candidate certification;

primary-G components;

legal SET alternatives;

observation or centralized state;

the later D7.3 decision-time predictor;

or continuation RNG.

That includes, at minimum:

topology coordinates
nine user/cluster world arrays
UAV positions
battery and charging state
station occupancy / queues / targets
return thresholds and margins
connection, SINR and routing state
lifecycle and event latches
current graph or other transition-consumed potentials
materialized observations and global state
source-controller assignment state
environment RNG state

Pure immutable configuration and inert rendering handles may remain reviewed exclusions. No live field may be excluded merely because it did not change the primary-G units in one development episode.

Construction-derived residue

The old six-field residue must not automatically be assumed present or absent at the current stage. The evidence note explicitly says its status after subsequent refactors is unmeasured.

Therefore:

first run the new complete local gate against the current stage;

if complete identity now passes, no environment repair is required;

if it fails, repair the canonical post-initialization barrier and rerun;

do not tolerate and disclose a differing state vector.

A public observation/state difference is inside the source claim even when the current scripted evaluator does not read it. The source is being qualified for a later learned decision-time mechanism; certifying only the scripted subset would produce another instrument that passes its current use while failing the next stage it exists to support.

3. DTYPE_BINDING
Pin user_cluster_assignments to np.int32; keep the existing width-sensitive digest

This modifies the choices offered in the question.

Use:

Python
Run
self.user_cluster_assignments = np.zeros(self.n_users, dtype=np.int32)

rather than dtype=int or dtype=np.int64.

Why np.int32

It preserves the only active local execution semantics.
The current workstation already creates this array as int32. Pinning np.int32 therefore changes no values and no bytes on the registered local route.

It preserves historical local fingerprint comparability.
The R3/R4 local artifacts used int32 bytes. Pinning int64 would gratuitously re-key them even though the observed divergence was representation width, not values.

It removes a hidden platform default.
dtype=int is a runtime-dependent implementation choice. An explicit dtype makes the state contract reviewable.

Its range is ample.
These are categorical cluster IDs for a small fixed number of clusters; int64 supplies no scientific benefit.

The evidence establishes 6/6 value equality and width-only divergence between int32 and int64 representations. The current source still creates the array using platform-dependent dtype=int.

Digest rule

Do not canonicalize only inside the digest. That would allow two executions holding different concrete array representations to receive the same fingerprint while the actual environment state differs.

Retain the existing width-sensitive component digest, but add an explicit provenance field:

component_dtype["user_cluster_assignments"] = "<i4"

and require the local replay gate to check it.

Because the actual bytes on the registered workstation remain unchanged, this does not require re-keying historical int32 fingerprints. Record the source-level dtype binding and a provenance-contract version change, but keep the existing fingerprint algorithm version unless another digest input changes.

The historical Linux int64 fingerprints remain representation-distinct and are never pooled into the successor result.

4. N_AND_O
Step N
Step N may proceed after LOCAL_EPISODE_KEY_REPLAY_PASS

Under B3-L, Step N is no longer “generate an immutable world-manifest inventory.” Replace it with:

GENERATE_AND_FREEZE_LOCAL_SUCCESSOR_INPUT_INVENTORY

The inventory must bind:

successor contract and namespace
exact topology list obtained from the frozen selection rule
topology coordinate records and hashes
all Part-A and focal-audit episode keys
episode / energy / user-world seed table
replicate and continuation seed derivation version
source-tree and configuration digests
certified local execution-class ID
fingerprint-definition version
dtype binding
episode count and complete inventory set hash

It does not pre-generate or store user-world arrays.

The formal runner must consume only inventory entries, and the pooler must prove:

exact episode-key coverage;

no duplicates;

no foreign topology;

no mixed namespace;

no mixed runtime certification;

no runtime or source-version drift.

Step O
Step O becomes scientifically eligible after Step N, but still requires separate compute authority

The formal successor run may start only when:

LOCAL_EPISODE_KEY_REPLAY_PASS is current
the complete input-inventory hash matches the frozen contract
the formal runtime equals CERTIFIED_LOCAL_EXECUTION_CLASS
the topology and episode key sets match exactly
the canonical pre-action assertion is live and fail-closed
all existing R4 realization, support and branch gates pass

Each formal episode must record:

runtime identity
episode-key identity
topology hash
world component digests and dtypes
complete final pre-action fingerprint
full fingerprint at t_e
event-snapshot fingerprint
actual derived seeds

A mismatch is:

LOCAL_PROVENANCE_NOT_CERTIFIED

and the run must refuse before conclusion-bearing computation where possible.

This scientific ruling does not itself authorize the formal compute. The user’s local-only rule identifies the allowed machine, but it does not erase the project’s separate conclusion-bearing compute-authority boundary.

Amendments to D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md
§5 — replace manifest authority

Delete the active requirement for:

schema-2 world manifests
one-machine manifest generation
manifest inventory set_hash

Replace it with:

local seed-replay certification
certified local execution class
immutable episode-key/input inventory
per-episode realized fingerprints

Keep D7_S_WORLD_MANIFEST_REPLAY.md as a historical design and fallback route, not the active successor mechanism.

§6 — close the open slot

Replace:

A1 versus A2 — OPEN

with:

SELECTED:
    B3-L — locally certified seed replay

FALLBACK:
    B1 — local fixed-world manifest replay
         if initial state cannot be regenerated locally

    B2/A2 — exogenous process or random-tape replay
            if initial state reproduces but the full horizon diverges
§7 — replace the invalidity branch

Replace:

MANIFEST_REPLAY_NOT_CERTIFIED

with:

LOCAL_PROVENANCE_NOT_CERTIFIED

Its reasons should distinguish:

LOCAL_RUNTIME_MISMATCH
EPISODE_KEY_INVENTORY_MISMATCH
INITIAL_WORLD_REPLAY_MISMATCH
PREACTION_STATE_REPLAY_MISMATCH
FULL_HORIZON_REPLAY_MISMATCH
DYNAMIC_PATH_NOT_EXERCISED
Preserve unchanged

deterministic topology rule;

K=8;

eight Part-A and eight focal-audit episodes per topology;

n_select=n_eval=2;

no expansion;

no support-based substitution;

no pooling with R3/R4;

the absolute five-G-unit R4 gates and result mapping.

5. CORRECTIONS
Correction 1 — “no unseeded np.random.* call remains” does not establish seed-complete construction

The current base environment executes:

Python
Run
self.np_random = np.random.RandomState(self.seed_val)

and seed_val defaults to None when the environment is constructed without a constructor seed. RandomState(None) is entropy-seeded even though it is not written as a module-level np.random.uniform(...) call.

The current build_pinned_env constructs the environment without a constructor seed and only subsequently calls reset(seed=episode_seed).

Therefore the moved source line and the absence of direct global np.random.* calls do not prove that construction-borne state has disappeared. The proposed local gate must measure it.

Correction 2 — same-process nine-array equality is not enough for B3

It establishes only:

same process
same current runtime
same nine generated arrays

It does not establish:

fresh-process equality;

complete pre-action identity;

deterministic event selection;

or full stable/flex continuation equality.

That measurement raises B3-L but does not close it.

Correction 3 — the historical manifest-replay result is not a current-stage certificate

The old local manifest exercise reproduced the registered world, event, and units while failing complete pre-step identity. Its instruments are deleted, and the question correctly reports that the stale residue’s status after later refactors is unmeasured.

It supplies the design of the new gate, not a grandfathered PASS.

Correction 4 — cancellation changes the required claim, not the historical observation

The unresolved cloud-versus-cloud divergence remains an honest historical observation. It no longer blocks the project because cross-machine transport is no longer inside the user-authorized execution scope. It should remain permanently open rather than be relabelled disproven.

Correction 5 — the deterministic selection rule already determines the numeric panel

Given:

candidate pool starts at 20260742
all earlier constructed seeds are excluded
K = 8
selection = ascending first K

the eventual seed list is mathematically determined even though the repository describes it as “not bound.” The scientifically important condition is:

precommitted but not instantiated, generated, inspected or filtered

not whether the numbers can be inferred from the rule.

This wording should be corrected without constructing the topologies.

Correction 6 — local-only does not mean single-process or numerically unconstrained

One workstation can still produce different execution paths through:

fresh interpreter construction;

process-spawn method;

worker count;

hash randomization;

BLAS/OpenMP threading;

dependency or code updates.

These must be part of the certified execution class. Otherwise B3 becomes “same machine” as an informal label rather than a reproducibility mechanism.

Correction 7 — seed_controls_generation cannot be promoted by renaming

The current audit explicitly documents that this flag proves only that the seed was applied and a topology was pinned; it does not prove reproducibility.

Under the successor route, use a new certification result earned by the local replay gate. Do not reinterpret the existing flag as satisfying B3.

Final disposition
ACTIVE ROUTE
    B3-L — locally certified seed replay

ASSERTION 6
    complete final pre-action state identity
    after topology + world + energy + canonical initialization

DTYPE
    pin user_cluster_assignments to np.int32
    retain width-sensitive digest
    record dtype explicitly

STEP N
    permitted after LOCAL_EPISODE_KEY_REPLAY_PASS
    generate immutable episode-key/input inventory, not manifests

STEP O
    scientifically eligible after N and all existing gates
    still requires separate conclusion-bearing compute authority

FALLBACKS
    B1 local manifest replay if initial regeneration fails
    B2/A2 exogenous tape if full-horizon dynamics diverge

No successor topology may be constructed or inspected before the complete local gate passes. D7.3 and D8 remain blocked pending a valid fresh-population successor result.
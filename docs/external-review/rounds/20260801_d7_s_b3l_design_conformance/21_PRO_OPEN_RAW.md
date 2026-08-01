Scientific ruling — D7.S B3-L design conformance

Stage reviewed: eac5b6d807e6aedb87352aefc51f60ffae0a4563

CONFORMANCE
DOES NOT YET CONFORM — FREEZE AFTER MODIFICATION

The design preserves the selected B3-L route, complete assertion-6 scope, explicit np.int32 binding, fresh-population rule, R4 estimand, fixed evidence volume, and fail-closed provenance principle. Those scientific choices are correctly transcribed.

Seven realization decisions remain incomplete or contradictory:

the certificate’s commit-based currency is self-invalidating once the certificate is committed;

the replay gate does not yet exercise the actual four-worker spawn process topology it purports to certify;

the gate covers only the focal-audit block and omits the conclusion-bearing Part-A control block;

the trajectory-digest encoding and completeness rules are underdefined;

the RPGM liveness counter can count initialization rather than post-initialization execution;

the formal per-episode paired-reconstruction protocol is not precisely defined;

the durable certificate does not contain enough evidence to audit the claimed PASS after its full worker records disappear.

The exact item dispositions follow.

D1 — assertion-6 relocation
CONFORMS

Calling the existing canonical barrier after the registered topology, user world, and energy profile are final, then computing the complete fingerprint before the first action, is the correct realization.

The environment barrier already:

rebuilds connection, channel, routing, energy-derived, observation, and global-state surfaces;

asserts that it consumes no RNG state;

is idempotent;

and is shared with reset() rather than being a second implementation.

The focused tests establish both sides needed by D1: two otherwise matched constructions can disagree before the barrier, and become complete-state identical after registered energy plus the barrier. They also test the named stale fields, no-RNG property, idempotence, and preservation of registered inputs.

One implementation postcondition should be explicit:

finalize_preaction_state(env)
    returns or records:
        observations materialized by this exact barrier invocation
        env.state materialized by this exact barrier invocation
        preaction_fingerprint computed afterward
        RNG-state token computed afterward

The formal path must not subsequently rematerialize observations or state before its first action.

D2 — barrier-repair scope
CONFORMS, WITH ONE CLARIFICATION

The gate-first policy is correct:

wiring the already accepted barrier at the final pre-action boundary is required now;

extending _post_pin_initialization_steps() is permitted only if the new replay gate identifies a remaining branch-A mismatch;

any extension must remain inside the shared barrier, not in a B3-L-only wrapper.

This preserves the single initialization code path and prevents speculative expansion.

A mismatch must first be localized by per-attribute complete-state digests. The repair target is the earliest stale derived surface, not whichever aggregate fingerprint happened to go red.

D3 — CERTIFIED_LOCAL_EXECUTION_CLASS
CHANGES REQUIRED

The field set is substantially correct, including explicit spawn, four workers, runtime libraries, CPU/BLAS state, thread settings, source identity, and resolved configuration.

Three amendments are mandatory.

D3.1 — thread settings must precede interpreter import

“Set by the parent before any NumPy work” cannot be realized by a function placed beside runtime_identity() in a module that has already imported NumPy.

Freeze a launcher-level rule:

Before starting either replay-gate process or any formal parent process:

PYTHONHASHSEED       = one explicit registered integer
OMP_NUM_THREADS      = 1
MKL_NUM_THREADS      = 1
OPENBLAS_NUM_THREADS = 1
NUMEXPR_NUM_THREADS  = 1

The launcher supplies these in the child-process environment before Python starts. Each parent and every pool worker independently verifies them after import.

Changing variables around ProcessPoolExecutor creation remains useful for spawned children, but does not retroactively constrain BLAS already initialized in the formal parent. The current orchestration imports NumPy at module load and only later wraps pool creation with thread-environment settings.

D3.2 — certify the actual parent and worker topology

The execution-class record must contain separately:

formal_parent_class_id
formal_worker_class_id
worker_count = 4
process_start_method = spawn

Every worker must report its own runtime record. A parent declaration that its children “should” have inherited the class is insufficient.

The formal implementation must explicitly pass:

Python
Run
mp_context=multiprocessing.get_context("spawn")

rather than merely recording "spawn" while using the platform default.

D3.3 — replace commit currency with a stable content identity

D3 and D12 currently create a contradiction:

the gate runs at commit C;

the certificate records source_tree=C;

committing that certificate creates commit C
′
;

the formal run at C
′
 sees that the certificate names C and declares it stale.

Trying to place C
′
 inside the certificate before creating C
′
 is self-referential.

Replace the currency field with:

source_code_id =
    SHA-256 over canonical sorted records:
        path
        git blob/content hash

for one frozen, explicit conclusion-bearing path set. The set must include:

the audit and pooling code;

the local replay gate and launcher;

Scenario 7 and its reachable environment/source-controller code;

the resolved configuration source and dependency lock;

the R4 and B3-L contracts;

seed, fingerprint, trajectory-digest, and inventory logic.

It must exclude:

the generated certificate itself;

the generated successor inventory;

logs and result artifacts.

The Git commit and clean-tree status remain recorded metadata. Currency is decided by source_code_id, configuration digest, execution-class ID, and provenance versions. A certificate-only or inventory-only commit then does not invalidate the certificate, while a conclusion-bearing code change does.

The “exact path set” mentioned in D3 must be enumerated in the ledger; it cannot remain a phrase.

D4 — local replay gate mechanism
CHANGES REQUIRED

Two fresh subprocess executions and exact comparison are correct, but the gate as described does not yet instantiate the same process topology as the formal run.

D4.1 — exercise the actual formal four-worker path

Each top-level gate execution must enter the same parent-plus-spawn-pool path intended for Step O. It is not enough for the worker record to state:

worker_count = 4
start_method = spawn

while the episode executes sequentially inside one subprocess.

The gate must prove that:

a four-worker spawn pool was actually created;

every worker reported the certified worker-class ID;

at least one task ran in every worker;

the conclusion-bearing episode computation passed through that orchestration;

result folding followed the same deterministic index order as the formal path.

A separate worker-liveness handshake is acceptable if the full development episode itself uses fewer than four tasks.

D4.2 — exercise both registered blocks

The prior ruling makes block = PART_A_CONTROL | FOCAL_AUDIT part of the protected episode identity. The formal result consumes both blocks.

The gate must therefore cover:

one development PART_A_CONTROL key, including the paired constructive_mixed and full_sync_SET continuations;

one development FOCAL_AUDIT key, including both limbs and the complete 2/2 candidate/evaluation set.

The same key may serve both only if the actual production driver does so. The current design explicitly places them in distinct block namespaces, so the safer binding is one key per block.

D4.3 — deterministic development-key selection

“Choose another dev index” is underdefined.

Freeze:

Search audit indices in ascending order over a finite registered range.
Select the first index satisfying:
    qualifying joint event exists
    complete stable/flex fork set exists

Record every rejected index and its reason.

Dynamic-path liveness may use a second, deterministically selected development key when the first qualifying focal key contains no post-initialization regeneration. Do not change the focal key merely to obtain a more convenient liveness path.

Failure to find a qualifying key in the registered range is:

LOCAL_EPISODE_KEY_REPLAY_UNTESTED:
    NO_DEVELOPMENT_EVENT_KEY

not a source result.

D4.4 — add the omitted initial-RNG witness

The B3-L ruling explicitly requires equality of the environment RNG state immediately after initial-world generation. R2 also lists it in the certification surface.

Each gate record must separately persist:

rng_after_world_generation
rng_after_energy_and_finalization
rng_at_t_e

The first distinguishes equal world arrays reached through different stream consumption. The second belongs to assertion 6. The third supports event identity.

D4.5 — no scientific bootstrap from the development gate

One development topology cannot carry the registered population bootstrap.

The gate should compare:

exact per-continuation component sequences;

candidate-selection and evaluation arrays;

D
A
	​

 and U
\*
 event units;

deterministic point-path inputs.

It must not emit or interpret R4 confidence bounds or a source branch. “Branch-relevant bounds or deterministic pre-bootstrap units” is resolved here in favor of the deterministic units.

D5 — trajectory digests
CONFORMS IN SCOPE; MODIFY THE ENCODING AND COMPLETENESS CONTRACT

Gate-only per-step trajectory identity is the correct interpretation. The formal result need not serialize every step after a current B3-L certificate has already established deterministic replay under the exact execution class.

The canonical per-step digest must be frozen as:

trajectory_digest_version
step index
for every component in WORLD_COMPONENT_ORDER:
    component name
    dtype
    shape
    contiguous bytes

Do not concatenate raw arrays plus a step number without delimiters, names, shapes, and dtypes. The initial world’s representation identity is part of the claim, especially after the dtype-width finding.

The gate must fail closed unless digest sequences are present and have exact registered lengths for:

the entire event-search prefix;

Part-A constructive_mixed;

Part-A full_sync_SET;

stable KEEP;

every stable SET selection and evaluation continuation;

flex KEEP;

every flex SET selection and evaluation continuation.

Missing sequences are UNTESTED, never equal by shared absence.

trajectory_digest_version may be represented through PROVENANCE_CONTRACT_VERSION, but the ledger must state that changing the D5 encoding bumps that version.

The formal run must still persist the endpoint evidence ordered in the prior ruling:

initial component digests and dtypes;

complete pre-action fingerprint;

complete event fingerprint;

event-snapshot fingerprint;

actual seed table.

D6 — dynamic-path liveness
CHANGES REQUIRED

Excluding a strictly diagnostic counter from the complete-state fingerprint is admissible, but the counter semantics are not yet precise enough.

The same waypoint and cluster-target generators are invoked during initial RPGM setup and later during stepping. The environment can regenerate:

an intra-cluster user waypoint;

an inter-cluster user waypoint;

a cluster migration target.

Freeze:

regen_count_at_preaction
regen_count_at_end
postinitialization_regen_delta =
    regen_count_at_end - regen_count_at_preaction

The gate requires the delta to be positive and equal on both executions. A counter value of one that came entirely from _initialize_user_waypoints_rpgm() does not exercise the risk B3-L is meant to test.

Prefer separate counters:

user_intra_waypoint_regenerations
user_inter_waypoint_regenerations
cluster_target_regenerations

At least one combined post-initialization delta must be positive. All three must be compared when present.

The fingerprint exclusion is valid only if:

no environment transition, observation, reward, source controller, or branch reads the counter;

changing the counter alone leaves actions and all registered outputs unchanged;

a paired negative proves the gate still reads the counter despite its fingerprint exclusion.

Record the exclusion and its causal justification alongside FINGERPRINT_EXCLUDED_ATTRS.

D7 — dtype binding
CONFORMS

Pinning:

Python
Run
user_cluster_assignments = np.zeros(n_users, dtype=np.int32)

while retaining the width-sensitive digest and adding explicit dtype provenance precisely follows the ruling. The current source still uses platform-dependent dtype=int, so this is a real source binding rather than a documentation-only change.

Require every initial and formal record to carry the complete nine-component dtype map—not only the <i4 assertion for this one array. The gate must compare the complete map exactly.

Historical local int32 fingerprints remain unchanged. Historical int64 fingerprints remain distinct and are not pooled.

D8 — versioning
CONFORMS

The split is correct:

fpalg-1 names the unchanged complete-state/world fingerprint algorithms;

prov-2 names the new B3-L provenance contract, dtype metadata, execution class, and replay certificate.

The two constants must appear in:

each gate worker record;

the PASS certificate;

the Step-N inventory;

every formal shard;

the pooled artifact.

Changing the canonical D5 trajectory encoding, source-code identity schema, or certificate equality matrix requires a provenance-version bump. It does not require an fpalg bump unless the underlying fingerprint byte encoding changes.

D9 — successor namespace and CLI
CONFORMS

A separate successor namespace, explicit --population successor, mandatory inventory, and hard refusal of ordinary topology overrides correctly prevent development and historical artifacts from earning successor identity.

The production rules must preserve the existing sharding distinction:

a strict subset may be a declared successor member shard;

only the exact inventory union, with every topology and episode key accounted for exactly once, may become the conclusion-bearing pooled result.

No unregistered CLI path may mint successor identity merely because its numeric seed happens to be in the panel.

D10 — Step N input inventory
CONFORMS WITH AMENDMENTS
Coordinate-generation timing

The flagged interpretation is accepted.

After LOCAL_EPISODE_KEY_REPLAY_PASS, Step N may mechanically instantiate the precommitted successor topologies, record their coordinates and hashes, and freeze them in the inventory. The prior prohibition is against constructing or inspecting them before the gate passes and against filtering or replacing them after construction. The inventory was expressly required to contain the coordinate records.

The following remain prohibited:

support probes;

user-world generation;

manual or programmatic filtering by geometry;

quadrant balancing;

replacement after a generation error;

substitution after support failure.

A coordinate-generation failure aborts Step N. It does not advance to the next candidate seed.

Required additions

The inventory must also bind:

topology-procedure version
source_code_id from amended D3
gate-certificate hash
trajectory-digest/provenance version
exact certified parent and worker class IDs
multiprocessing and thread-launch policy

Use the amended stable source_code_id, not a Git commit that changes when the inventory is committed.

D11 — provenance refusal chain
CHANGES REQUIRED

The gate-only/formal partition is basically right, but the formal paired-construction check is underspecified.

D11.1 — freeze the formal paired-construction protocol

The Step-N inventory deliberately contains no expected user-world arrays. Therefore:

INITIAL_WORLD_REPLAY_MISMATCH

cannot mean “different from a world stored in the inventory.”

For every formal episode key, freeze:

construct environment A;

construct environment B independently in the same certified worker;

compare:

all initial world arrays, dtypes, shapes, digests;

RNG state after world generation;

install the same energy profile and finalization barrier in both;

compare complete pre-action fingerprints and RNG state;

discard B;

continue the conclusion-bearing episode from A only.

Always choosing A prevents a mismatch check from selecting which realization becomes evidence.

This resolves:

INITIAL_WORLD_REPLAY_MISMATCH
PREACTION_STATE_REPLAY_MISMATCH

without smuggling user-world bytes into the input inventory.

D11.2 — gate-only reasons are accepted

The flagged partition is accepted:

FULL_HORIZON_REPLAY_MISMATCH
DYNAMIC_PATH_NOT_EXERCISED

belong to certification. A formal episode need not execute its entire trajectory twice after a current certificate has already bound the code, execution class, process topology, and trajectory algorithm.

A formal run still records its endpoint and event identities so drift or corruption remains observable.

D11.3 — this is an early operational refusal, not an R4 result branch

LOCAL_PROVENANCE_NOT_CERTIFIED must be emitted before scientific branch assembly wherever possible. It is not inserted into the R4 scientific precedence table and must not be interpreted as a population outcome.

The pooled runner must refuse to assemble a scientific branch when any shard contains this status.

D12 — PASS certificate
CHANGES REQUIRED
D12.1 — eliminate the commit self-reference

Use the amended source_code_id, not “certificate commit equals live commit,” as the currency test.

The certificate may additionally record:

gate_execution_commit
certificate_commit

for history. Neither field is the currency key.

D12.2 — make the committed certificate self-contained

Gitignored full worker records are acceptable only as temporary debugging material. The committed certificate must retain enough evidence for an independent reader to verify what passed.

At minimum it must contain:

both top-level process identities;

parent and all worker class IDs;

exact commands and registered environment-variable values;

selected Part-A, focal, and any separate liveness keys;

every rejected development index and reason;

both workers’ initial-world component digests, dtypes, and RNG tokens;

both pre-action fingerprints and RNG tokens;

prefix/event/focal/candidate/snapshot digests;

trajectory-sequence roots and lengths for every required continuation;

component-sequence and evaluation-unit digests;

liveness baselines, final counts, and deltas;

a field-by-field equality matrix;

hashes of both complete worker-record files.

Either commit the complete worker records as compact evidence or make the certificate itself carry the complete comparison surface. A single shared digest plus two PIDs is not enough to establish that every required field was independently produced and compared.

D12.3 — certificate currency

Freeze:

certificate is current iff:
    verdict == LOCAL_EPISODE_KEY_REPLAY_PASS
    source_code_id matches
    configuration_digest matches
    certified parent class ID matches
    certified worker class ID matches
    fingerprint/provenance versions match
    gate algorithm and required equality field set match

A timestamp is metadata, not identity.

Additional protected decisions omitted from D1–D12

The mandatory enumeration finds the following unasked choices.

O1 — source-code identity closure

The ledger refers to an “exact path set” but does not identify it. Reversing which imported file is included can allow changed dynamics to retain a current certificate. The path/import closure must be frozen under D3.

O2 — Part-A replay certification

The current gate covers only the focal-audit block. Part-A has a distinct block namespace, controller pair, and causal role. It must be certified under D4.

O3 — initial-world RNG equality

The initial RNG token is explicitly part of the B3-L ruling but has no named D1–D12 binding. Add it to D4 and the certificate.

O4 — deterministic development-key selection

“Choose another index” introduces a discretionary selection step. Freeze the ascending finite search and preserve its rejection log.

O5 — formal construction-pair ownership

D11 does not say which of the two matching formal constructions becomes evidence. Freeze “always continue from A; discard B.”

O6 — replay-gate process-topology liveness

Recording workers=4 is not proof that four spawned workers existed or executed. Add a worker-attestation requirement.

O7 — trajectory digest identity

The digest’s byte encoding, required path set, lengths, and missing-field semantics materially determine whether trajectory divergence is detectable. Freeze them and version them.

O8 — certificate evidence retention

The current design permits the load-bearing records to vanish under a gitignored path. The durable evidence surface must be explicit.

O9 — topology derivation version

Coordinate bytes alone do not say which procedure generated them. Step N must record and gate on the topology-procedure version.

O10 — resolved configuration surface

configuration_digest must cover the actual resolved environment and audit configuration—including Scenario-7 profile overrides—not merely the user-facing Config object.

INTERPRETATIONS
1. D10 coordinate generation after PASS
ACCEPTED

Step N may generate and hash the precommitted topology coordinates after the gate passes. No support, user-world, geometry-quality, or replacement decision may depend on their values.

2. D5 gate-only per-step trajectory digests
ACCEPTED, SUBJECT TO THE D5 ENCODING AND COMPLETENESS AMENDMENTS

Formal episodes need not persist full per-step sequences. They must preserve the registered endpoint, event, seed, component, and complete-state identities.

3. D11 gate-only full-horizon and liveness reasons
ACCEPTED

Those reasons belong to certificate production and currency. The formal run performs the paired initial/pre-action check and records the required realized fingerprints; it does not duplicate every full continuation.

4. D6 liveness counter excluded from the fingerprint
ACCEPTED CONDITIONALLY

The exclusion is correct only when the counter is:

purely diagnostic;

never read by environment or controller logic;

measured as a post-preaction delta;

independently compared by the gate;

covered by a negative test showing that changing it alone cannot alter a registered trajectory or quantity.

CONVERGENCE_DECISION
FREEZE AFTER MODIFICATION

The scientific route does not need another design round after the ledger and R2 contract incorporate the rulings above.

The modifications that must be frozen are:

D3   launch-time execution-class enforcement;
     actual parent/worker attestation;
     stable source_code_id rather than commit currency

D4   actual four-worker spawn route;
     Part-A plus focal block coverage;
     deterministic development-key selection;
     initial RNG witnesses;
     deterministic pre-bootstrap comparison only

D5   canonical, versioned, complete trajectory-digest surface

D6   post-preaction liveness deltas over all regeneration mechanisms

D10  topology-procedure version and amended source/certificate identity

D11  exact formal A/B paired-construction protocol;
     gate-only reason partition;
     early operational refusal semantics

D12  non-self-referential currency;
     self-contained durable PASS evidence

After those amendments are entered, the Project Manager may proceed to implementation under its ordinary authority without a third Pro design-conformance round, provided the implementation introduces no new protected choice. Actual realization must still undergo the project’s code-science conformance boundary; any newly discovered protected decision returns to Pro rather than being resolved as an implementation convenience.

The replay gate remains unrun, Step N remains held, and Step O remains held. This ruling authorizes neither the gate execution nor conclusion-bearing compute. D7.3 and D8 remain blocked pending a valid fresh-population successor result.
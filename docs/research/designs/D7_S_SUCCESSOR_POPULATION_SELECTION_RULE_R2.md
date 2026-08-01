# Successor population selection rule — R2 (local-only amendments)

Status: **frozen at the Pro ruling of round
`20260801_d7_s_local_only_successor_reruling`** (raw:
`21_PRO_OPEN_RAW.md`, stage commit `180980ab`). Supersedes the provenance
mechanism of `D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md` (R1); every R1
section not amended here is carried forward unchanged — the deterministic
topology rule, K=8, 8 Part-A + 8 focal-audit episodes per topology,
n_select=n_eval=2, no expansion, no support-based substitution, no pooling
with R3/R4, the R4 absolute five-G-unit gates and result mapping, and the
prohibition on reusing H, the re-run and their inspected worlds.

## Route (closes R1 §6's open slot)

```text
SELECTED   B3-L — LOCAL_CERTIFIED_SEED_REPLAY
           a registered episode key generates one bit-identical, complete
           episode state under one frozen local execution class, demonstrated
           across fresh interpreter processes and enforced on every
           conclusion-bearing run

FALLBACK   B1  — local fixed-world manifest replay,
                 if the initial state cannot be regenerated locally
           B2/A2 — exogenous process / random-tape replay,
                 if the initial state reproduces but the full horizon diverges
```

Fallbacks are selected only by the ruled fail-closed decision tree:

```text
A  initial world or final pre-action identity differs
   -> LOCAL_EPISODE_KEY_REPLAY_FAIL -> canonicalize initialization, rerun
B  pre-action identity matches, continuations diverge  -> select B2/A2
C  seed-generated initial world still differs after canonicalization -> B1
D  complete equality                                   -> PASS, B3-L certified
```

## Certification (replaces R1 §5's manifest authority)

```text
gate            development-only local replay gate, TOPOLOGY_SEED_DEV=20260725
processes       two FRESH interpreter processes (not two in-process builds)
execution class the same one intended for the formal run
pass            LOCAL_EPISODE_KEY_REPLAY_PASS
```

Equality surface (all required): registered episode-key inputs; initial world
(nine WORLD_COMPONENT_ORDER arrays, shapes, dtypes, per-component digests,
environment RNG state after world generation); complete final pre-action
state (see assertion 6 below); prefix and event identity (post-prefix
exogenous arrays, qualifying-event presence, event-conformance record, focal
and legal-candidate identities, duty map, event snapshot); full registered
continuations (H_stable=139, H_flex=550, lossless per-step exogenous
user/cluster trajectory digests, primary-G component sequences, selected
candidates and evaluation units, branch-relevant bounds); dynamic-path
liveness (at least one exercised post-initialization waypoint or
cluster-target regeneration); production process topology (worker count,
start method, PYTHONHASHSEED, BLAS thread settings frozen identically or
bound into the certified identity).

```text
CERTIFIED_LOCAL_EXECUTION_CLASS
  strict identity a formal run must match or refuse:
  workstation, OS/arch, Python, NumPy/SciPy, BLAS impl + CPU features,
  worker count, process start method, PYTHONHASHSEED, BLAS/OpenMP thread
  vars, source-tree digest, configuration digest.
  runtime_identity() remains descriptive metadata and never gates.
  A runtime update never invalidates a completed result; it requires
  recertification before any new run.
```

Assertion 6 (complete, relocated): two executions of one registered episode
key have the same complete continuation-sensitive environment state
immediately before the first source-control action — computed only after
construct/reset, topology restore + verify, registered user-world
generation, registered energy permutation, the canonical
post-pin/post-world/post-energy initialization barrier, and observation
materialization. No live field is excluded for having been inert in one
development episode; pure immutable configuration and inert rendering
handles may remain reviewed exclusions.

DTYPE binding: `user_cluster_assignments` is created
`np.zeros(n_users, dtype=np.int32)` (explicit, platform-independent); the
component digest stays width-sensitive; the artifact records
`component_dtype["user_cluster_assignments"] = "<i4"` and the gate checks
it. Historical int32 fingerprints are not re-keyed; historical Linux int64
fingerprints remain representation-distinct and are never pooled.

## Step N (replaces "generate immutable manifest inventory")

`GENERATE_AND_FREEZE_LOCAL_SUCCESSOR_INPUT_INVENTORY`, permitted only after
`LOCAL_EPISODE_KEY_REPLAY_PASS`. It binds: successor contract and namespace;
the exact topology list obtained from the frozen selection rule; topology
coordinate records and hashes; all Part-A and focal-audit episode keys; the
episode/energy/user-world seed table; replicate and continuation seed
derivation version; source-tree and configuration digests; certified local
execution-class ID; fingerprint-definition version; dtype binding; episode
count and the complete inventory set hash. It does **not** pre-generate or
store user-world arrays. The formal runner consumes only inventory entries;
the pooler proves exact episode-key coverage, no duplicates, no foreign
topology, no mixed namespace, no mixed runtime certification, no drift.

## Step O and invalidity (replaces R1 §7's added branch)

Step O is scientifically eligible when: the PASS is current; the inventory
hash matches the frozen contract; the formal runtime equals
`CERTIFIED_LOCAL_EXECUTION_CLASS`; topology and episode-key sets match
exactly; the canonical pre-action assertion is live and fail-closed; all
existing R4 realization, support and branch gates pass. Each formal episode
records runtime identity, episode-key identity, topology hash, world
component digests and dtypes, complete final pre-action fingerprint, full
fingerprint at t_e, event-snapshot fingerprint, and actual derived seeds.

```text
LOCAL_PROVENANCE_NOT_CERTIFIED   (replaces MANIFEST_REPLAY_NOT_CERTIFIED)
  reasons: LOCAL_RUNTIME_MISMATCH | EPISODE_KEY_INVENTORY_MISMATCH |
           INITIAL_WORLD_REPLAY_MISMATCH | PREACTION_STATE_REPLAY_MISMATCH |
           FULL_HORIZON_REPLAY_MISMATCH | DYNAMIC_PATH_NOT_EXERCISED
```

The ruling does not itself authorize the formal compute; conclusion-bearing
compute authority remains the user's separate boundary.

## Wording correction (ruling C5)

R1's "the exact confirmatory topology list — NOT BOUND" is corrected: the
ascending rule mathematically determines the panel. The binding condition is
**precommitted but not instantiated, generated, inspected or filtered**. No
topology in the candidate pool may be constructed for any reason before the
complete local gate passes — including a smoke test.

`D7_S_WORLD_MANIFEST_REPLAY.md` is retained as historical design and as the
B1 fallback route, not the active successor mechanism.
`seed_controls_generation` keeps its documented meaning (seed applied,
topology pinned) and is never reinterpreted as this certification (C7).

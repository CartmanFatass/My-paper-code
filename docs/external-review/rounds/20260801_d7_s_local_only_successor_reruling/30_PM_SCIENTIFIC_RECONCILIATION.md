# Reconciliation — 20260801_d7_s_local_only_successor_reruling

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `180980ab6a00b02596f2b3f2adaefe759450120a`.

## What was decided

1. **Route: B3-L — LOCAL_CERTIFIED_SEED_REPLAY** (a modified B3, not bare seed
   provenance, not manifest reinstatement). A registered episode key must
   generate one bit-identical complete episode state under one frozen local
   execution class, demonstrated across **fresh interpreter processes** and
   enforced on every conclusion-bearing run. B1 (local manifest replay) and
   B2/A2 (exogenous tape) survive as fallbacks selected only by the ruled
   fail-closed decision tree (A→canonicalize+rerun; B→A2; C→B1; D→PASS).
2. **Certification gate**: development-only local replay gate on
   `TOPOLOGY_SEED_DEV=20260725`, two fresh processes, same execution class as
   the formal run; pass = `LOCAL_EPISODE_KEY_REPLAY_PASS`. Equality surface:
   registered inputs; initial world (nine arrays, shapes, dtypes, digests,
   RNG state); complete final pre-action state; prefix/event identity; full
   registered continuations (H_stable=139, H_flex=550, lossless per-step
   exogenous trajectory digests, primary-G sequences, candidates, units);
   dynamic-path liveness (at least one exercised post-initialization
   waypoint/cluster regeneration); production process topology frozen or
   bound into the certified identity.
3. **CERTIFIED_LOCAL_EXECUTION_CLASS**: a new strict identity object
   (workstation, OS/arch, Python, NumPy/SciPy, BLAS + CPU features, worker
   count, start method, PYTHONHASHSEED, thread vars, source-tree digest,
   configuration digest). A formal run refuses on mismatch;
   `runtime_identity()` stays descriptive metadata.
4. **Assertion 6**: retain *complete* continuation-sensitive pre-action
   identity — not scoped to the nine arrays or units — and move it to the
   true first-action boundary (after topology restore, user-world
   generation, energy permutation, canonical initialization barrier, and
   observation materialization). If the gate fails there, repair the
   canonical barrier and rerun; tolerate-and-disclose is refused.
5. **DTYPE**: pin `user_cluster_assignments = np.zeros(n, dtype=np.int32)`;
   keep the width-sensitive component digest; add explicit provenance
   `component_dtype["user_cluster_assignments"] = "<i4"` checked by the gate;
   no re-keying of historical int32 fingerprints; provenance-contract version
   change only.
6. **Step N** becomes `GENERATE_AND_FREEZE_LOCAL_SUCCESSOR_INPUT_INVENTORY`
   (episode-key/seed/digest inventory with set hash; **no** pre-generated
   world arrays), permitted only after `LOCAL_EPISODE_KEY_REPLAY_PASS`.
   **Step O** is scientifically eligible after N plus all existing R4 gates,
   with per-episode recording duties and the new invalidity branch
   `LOCAL_PROVENANCE_NOT_CERTIFIED` (six distinguished reasons). The ruling
   does not itself authorize the compute.
7. **Selection-rule amendments** (§5 manifest authority → local certification
   stack; §6 open slot closed as SELECTED B3-L with B1/B2 fallbacks; §7
   `MANIFEST_REPLAY_NOT_CERTIFIED` → `LOCAL_PROVENANCE_NOT_CERTIFIED`),
   everything else preserved (K=8, 8+8 episodes, n_select=n_eval=2, no
   expansion, no substitution, no pooling, R4 absolute gates). Recorded by
   supersession in
   `docs/research/designs/D7_S_SUCCESSOR_POPULATION_SELECTION_RULE_R2.md`;
   `D7_S_WORLD_MANIFEST_REPLAY.md` is retained as historical design and
   fallback route.

## Where I was corrected

- **C1**: my claim "no unseeded `np.random.*` call remains (verified by
  grep)" does not establish seed-complete construction:
  `RandomState(seed_val)` with `seed_val=None` at construction is
  entropy-seeded, and `build_pinned_env` constructs without a constructor
  seed before `reset(seed=...)`. The gate must measure construction-borne
  state; the grep proved only the absence of one syntactic form.
- **C2**: same-process nine-array equality raises B3-L but closes nothing —
  fresh-process, complete pre-action, event, and full-horizon equality were
  never measured.
- **C3**: the historical manifest-replay result supplies the *design* of the
  new gate, never a grandfathered PASS.
- **C4**: the cloud-versus-cloud divergence stays permanently open, not
  disproven; it stopped blocking only because the claim scope changed.
- **C5**: "the exact confirmatory topology list NOT BOUND" is wrong wording —
  the ascending rule mathematically determines the panel; the real condition
  is *precommitted but not instantiated, generated, inspected or filtered*.
  Corrected in the superseding rule document without constructing anything.
- **C6**: local-only is not single-process or numerically unconstrained;
  spawn method, worker count, hash randomization and BLAS threading must be
  certified, or B3 is a label rather than a mechanism.
- **C7**: `seed_controls_generation` must not be renamed or reinterpreted as
  the certification; the gate earns a new result.

## Next action

Workflow 4 step 2: Project Manager code design for the B3-L stack (gate
script, certified execution class, assertion-6 relocation, dtype pin,
inventory generator, run refusal wiring), recorded as a decision ledger;
then touchpoint 2 asks conformance of that completed design to this ruling.
Zero experiments before touchpoint 2 closes.

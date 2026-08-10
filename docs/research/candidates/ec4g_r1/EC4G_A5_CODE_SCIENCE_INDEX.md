# EC4G-A5 code-science index

## Portable source-entry boundary

`EC4G-A5-PORTABLE-SOURCE-BOUND-TWO-PHASE-EXECUTION-CENSUS` has a fresh
implementation identity in
`experiments/candidates/ec4g_r1/portable_source_bound_two_phase_execution_census.py`
and a one-shot runner in
`scripts/run_ec4g_a5_portable_source_bound_two_phase_execution_census.py`.

Before C0/C1 is read and before any map or compiler call,
`admit_source_entry` records and requires all of the following:

- canonical process cwd equals the registered frozen source worktree root and
  that root is not the main checkout;
- the root is the actual Git toplevel at the exact declared HEAD commit;
- runner, A5 runtime core `__file__`, and the pure A4 algorithm dependency
  `__file__` resolve to their exact registered relative paths beneath that one
  root, with no symlink component or escape;
- each live file is either raw-byte-identical to its commit blob or has the
  same Git clean-filtered blob identity (the portable CRLF/LF case), with both
  live/blob SHA-256, relative/absolute path, committed and filtered Git blob
  identities, and the exact match mode recorded.

Any failure selects `A5_SOURCE_ENTRY_BINDING_INVALID`. The result retains one
technical entry record and one invocation record, while all scientific
counters remain zero. There is no corrected invocation.

The A4 module is an explicit source-bound pure-code dependency only. A5 never
reads an A4 run root, object, receipt, snapshot, manifest, result, equality
witness or D value. Its admitted execution always creates a fresh A5 Phase-1
artifact root.

## Frozen scientific mechanics

The implementation authenticates the accepted immutable C0 contract at
`c0beef960f5f731f0c994ecd2298a1e889210c7b` (blob
`6d37b33c933ee16f89186a507e67e1080b674ca0`, SHA-256
`0d0c9b6f24ae2bb96fc0a3f542c737557f1cd66be1edbdb72d809dfce9bb0183`)
and the accepted C1 binding record at
`ba9eae5cfc21c014f210e061561fe7b8f47f5592` (SHA-256
`495702d04188a929e62e1e8d178bde84ed156dc83beab10106c67e612a50baef`).

After source admission, Phase 1 calls `M_E` then `M_D` for each of
`k_join`, `k_leave`, `k_rejoin`, compiling and writing exactly six complete
objects and receipts in cell-major/map order. It closes them in one
content-addressed write-once snapshot and manifest before any comparison.
Prediction fields, expected output, peer equality and D are not inputs.

Phase 2 independently reopens the sealed file set, checks exact row/object/
receipt schemas, paths and digests, makes no map/compiler call or write,
compares all three pairs without early stop using exact canonical compared-
field bytes, and computes
`0.50 I[join differs] + 0.25 I[leave differs] + 0.25 I[rejoin differs]` only
after three complete witnesses. Hashes remain audit evidence, not equality.

Branch precedence is exactly:

1. `A5_SOURCE_ENTRY_BINDING_INVALID`
2. `A5_INPUT_OR_DESIGN_FREEZE_INVALID`
3. `A5_FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE`
4. `A5_MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS`
5. `A5_PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID`
6. `A5_PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL`
7. `A5_COMPLETE_PORTABLE_TWO_PHASE_EXECUTION_CENSUS`

The hard cap is one run, one entry record, one snapshot, six map calls, six
compiler calls, six objects, three comparisons, three witnesses and one D.
Environment, policy, learner, trainer, optimizer, evaluation, model-fit,
stochastic, retry, repair, corrected-invocation, rescan and reconstruction
activity is zero. Evidence complexity is constant, with `K_search=0` and zero
hypothetical transitions.

## Focused wrong-implementation evidence and authority

The focused test package checks accepted source binding and exact dependency
inventory; main/wrong cwd; runner, core and dependency blob tamper; other-root
runtime import; symlink escape; source failure before every scientific call;
fresh complete materialization; map/compiler-free Phase 2; post-seal tamper
before comparison/D; forbidden prediction flow; extra compiler fields; exact
canonical equality, D, branch order, counters and A5-only result identity.

Temporary test fixtures are not the registered A5 audit. The source package
does not run the unique treatment, publish a result, invoke readiness or
Operator transport, mutate Git, or technically accept the package. Those
actions remain CPM-owned. No branch establishes natural prevalence, causal or
reward value, learning, B/C/formal/Pro need, promotion, retirement or an
automatic successor.

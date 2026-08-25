# Semantic Graphon Shared Policy B1 r06-240

This isolated package binds exact science revision
`SGSP-B1-SCIENCE-20260814-06`. It is an isolated implementation of the
Pro-closed r05 treatment-definition base with only the frozen 240-update,
update-240-only checkpoint, fresh-seed, and `SGSP-B1-R06-240` namespace
replacements. It never loads a revision-05 checkpoint, seed packet, result, or
stochastic artifact. Source existence is not production authority.
The CLI has no default operation. Every stochastic or result-bearing path
requires both a passing exact-revision preactivity certificate and a Root-owned,
unexpired production authorization containing a nonempty lease token.

The authorization JSON is external owner state and cannot be created by this
package. It must contain the exact direction/revision, `production_authorized:
true`, the absolute `result_root`, `max_workers: 1`, a nonempty `lease_token`
and `stage_boundary`, timezone-aware `issued_at_utc` and future `not_after_utc`, a unique nonempty
`authorized_seeds` subset of the frozen registry, and
`cumulative_wall_clock_cap_hours` in `(0,8]`. The validity window from issuance
to expiry may not exceed that cap and is rechecked during formal execution.
Any continuation lease must retain the original stage boundary and remain
inside the first lease's continuous cumulative deadline. The production runner
fixes PyTorch intra-op and inter-op thread counts to one.
The registered generator, audit permutation, paired initializer, trainer, and
evaluator also require the validated `ProductionPermit` capability when called
as library functions; the CLI is not the only authorization boundary.

## Future commands

These commands are documentation only. Do not run them before the applicable
authority boundary.

Static preactivity certificate, after source review authority:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_r06 certificate --output C:/ABSOLUTE/PATH/sgsp-r06-240-preactivity.json
```

Static resource proposal:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_r06 resource-proposal --output C:/ABSOLUTE/PATH/sgsp-r06-240-resource-proposal.json
```

Only after Root issues the exact-revision production lease, initialize a fresh
result root:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_r06 init-result --result-root C:/ABSOLUTE/PATH/FRESH-SGSP-R06-240-RESULT --certificate C:/ABSOLUTE/PATH/sgsp-r06-240-preactivity.json --authorization C:/ABSOLUTE/PATH/root-sgsp-r06-240-lease.json
```

Run one authorized registered seed. Repeat only for the frozen seeds named by
the lease; an already installed seed cannot be replaced:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_r06 run-seed --result-root C:/ABSOLUTE/PATH/FRESH-SGSP-R06-240-RESULT --certificate C:/ABSOLUTE/PATH/sgsp-r06-240-preactivity.json --authorization C:/ABSOLUTE/PATH/root-sgsp-r06-240-lease.json --seed 14103
```

Analyze only after all 16 atomic four-arm packets exist:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_r06 analyze --result-root C:/ABSOLUTE/PATH/FRESH-SGSP-R06-240-RESULT --certificate C:/ABSOLUTE/PATH/sgsp-r06-240-preactivity.json --authorization C:/ABSOLUTE/PATH/root-sgsp-r06-240-lease.json --output C:/ABSOLUTE/PATH/FRESH-SGSP-R06-240-RESULT/analysis.json
```

No command performs checkpoint selection, seed replacement, held-out tuning,
automatic reruns, or cross-`N` tape nesting.

For a Root lease that names all 16 frozen seeds in exact order, the preferred
fresh all-seed production entry point performs initialization, every atomic
seed, and final analysis in one foreground process:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_r06 formal-run --result-root C:/ABSOLUTE/PATH/FRESH-SGSP-R06-240-RESULT --certificate C:/ABSOLUTE/PATH/sgsp-r06-240-preactivity.json --authorization C:/ABSOLUTE/PATH/root-sgsp-r06-240-lease.json
```

It refuses an existing result root. If the process terminates after one or more
complete atomic seed installs, no partial seed counts as evidence; continuation
uses only the separately gated `run-seed` commands under valid Root authority.

# SGSP RIDGEGATE-2Z r03 full panel

This isolated lifecycle package binds only `semantic_graphon_shared_policy`,
`SGSP-RG2Z-SCIENCE-20260815-03`, and the action
`SGSP-RG2Z-R03-FULL-PANEL`. It has no default action. `certificate` and
`resource-proposal` are static/preactivity-only commands. No training,
evaluation, result-root creation, seed packet, or analysis can proceed without
both a passing exact-revision certificate and a current Root authorization.

The authorization is external Root state. It must exactly bind the direction,
revision, action, absolute fresh result root, counter root, device,
Root-selected `max_workers` in `1..4` (one CPU thread/core per seed worker),
nonempty lease token and stage boundary, a timezone-aware
current validity interval, and an order-preserving nonempty subset of the
frozen 24 seeds. The package cannot mint or alter it. Continuation resource
slices may authorize different registered seed subsets, but cannot change the
frozen stage, coordinates, device, result root, or certificate.

Each seed is written only as a complete atomic packet containing the two learned
arms' update-512 checkpoint and packet metadata. Existing roots and seeds are
never replaced. `analyze` refuses anything short of all 24 verified `COMPLETE`
packets and writes one fresh complete analysis; it does not provide partial
scientific summaries. `formal-run` accepts only the full exact 24-seed lease.
The static proposal requests up to four independent CPU seed workers; concurrent
`run-seed` commands remain safe because every registered seed has a disjoint
atomic destination directory.

Future authorized static commands:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_rg2z_r03 certificate --output C:/ABSOLUTE/PATH/rg2z-r03-preactivity.json
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.semantic_graphon_shared_policy_rg2z_r03 resource-proposal --output C:/ABSOLUTE/PATH/rg2z-r03-resource-proposal.json
```

Production commands require an independently issued exact Root lease and are
intentionally not runnable from this README without that authority.

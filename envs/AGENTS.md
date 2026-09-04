# envs/ — shared environments and the native boundary

Core tier (`docs/project/ENGINEERING_SCOPE_SPEC.md` §2, §6): behaviour-preserving changes only,
each with the one focused test that would fail if the semantic changed. Environment
implementations own transition dynamics and environment RNG.

```
envs/pettingzoo/          UAV scenarios (scenario1–3, uav_env, adapters) + relay/ (routed relay core) + native/ (uav_geometry_backend.cpp)
envs/continuous_roster/   continuous-roster toy + native/ (continuous_roster_toy_backend.cpp)
envs/relay_corridor/      flexible_skill_duration host (exact references, margins); no imports from experiments/
envs/native/              cpp_extension_cache.py (source-keyed JIT loading), production_backend.py (capability registry)
envs/probe_environments.py
```

Native boundary, as it is rather than as older maps described it:

- `envs/native/cpp_extension_cache.py` compiles and caches extensions through PyTorch's JIT loader
  on first use, keyed by a SHA-256 of the source. There is no build step; the first test or run
  touching a native backend pays the compile. Two adapters use it (`continuous_roster/cpp_backend.py`,
  `pettingzoo/uav_cpp_backend.py`); most candidates ship their own loaders instead. There is no
  single native choke point.
- `envs/native/production_backend.py` is a fail-closed capability registry that lazily imports
  native loaders out of `experiments/candidates/*` inside function bodies (about ten). Those
  imports cross the core/research line and are recorded defects (`experiments/AGENTS.md` marks the
  directories `imported`); do not add another. `tests/production_backend_policy_test.py` exercises
  the registry.
- Device: CPU single thread is the right default at the measured model sizes (`torch.set_num_threads(1)`),
  but CPU is sometimes scientifically invalid rather than slower: `docs/project/PROBLEM_CACHE.md` P1b
  records a frozen contract where CPU fork reconstruction is not bitwise exact and CUDA is the
  registered backend. Neither declared conda environment has CUDA today. Check the contract before
  switching device.
- `.gitattributes` pins `eol=lf` on the two VNFC science cards a native loader byte-addresses; do
  not normalise them.

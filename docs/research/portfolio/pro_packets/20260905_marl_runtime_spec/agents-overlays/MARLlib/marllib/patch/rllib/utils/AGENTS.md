# MARLlib local research overlay

- Scope: patched RLlib utility subtree; only the exploration utility is present here.
- Provenance: local navigation authored for the fixed-source evidence pass on 2026-09-05.
- Fixed source: `80e9973a430271a93c781d7422133acb1198f84b`; repository URL: `https://github.com/Replicable-MARL/MARLlib`.
- Upstream state: no upstream `AGENTS.md` exists in this directory tree at the fixed commit. If a future checkout supplies one, preserve it and let the nearest upstream instruction take precedence.
- Source policy: source files are read-only for this pass. This file adds navigation only; it does not activate patches or install dependencies.
- Key paths: exploration/ornstein_uhlenbeck_noise.py; `marllib/patch/add_patch.py#L108-L110` is the link target declaration.
- Evidence reports: `C:\Projects\ref-lib\reports\MARLlib\CORE_EVIDENCE.md` and `ROOT_RETURN.md`.
- Boundary: this is a local RLlib snapshot; do not claim installed Ray imports it unless the link step is independently observed.
- License: MARLlib is MIT-licensed; cite and preserve notices without copying large source fragments.

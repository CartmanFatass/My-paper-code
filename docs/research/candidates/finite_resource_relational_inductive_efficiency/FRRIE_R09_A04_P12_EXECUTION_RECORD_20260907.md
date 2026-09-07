# FRRIE A04 P12 execution record — 2026-09-07

P12-FRRIE-A04-EXECUTE-01, committed Portfolio handoff at
`5eb4fa9e98048607300eb845373a5b47f2e71cbb`, allocates exactly one complete setup/T0 chain.
The Root assignment names this DM as launcher and `/root/cm_frrie_p12_a04_collect` as CM
collector; Root adopts observation after accepted-handle handoff. Existing card §§1–4 and
handoff §§1–2 at `6fb13f9a9ba7a655e07d168d09941a826decb7ec` retain their scientific meaning.
No new CM engineering spec, comparison enrollment, source change or Pro request is involved.

## Fixed execution and delivery

- Source SHA: `d6844bb25f6f1030aa7123467935861dcc719450`.
- Node: `wsl_4070`; exact detached cwd:
  `/home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f`.
- Prospective sole supervisor handle: `frrie-a04-system312-p11-d6844bb25f6f`.
  The `p11` component is the prepared name, not a second allocation.
- Dedicated environment: `/home/wu/.venvs/hmasd-frrie-system312-a04-20260907`, system
  `/usr/bin/python3.12`, NumPy1.26.3 binary only, no torch. Do not substitute another environment.
- Exact LF command: the sole bash block in the committed handoff, 1379 bytes, SHA256
  `959a43cefb989e823a8fe38cdccc30dc83914f13bc3218a8cdda635c691be885`.
  It is extracted without editing to local `temp/directions/finite_resource_relational_inductive_efficiency/exp/a04_p12_20260907/command.sh`
  and staged at `/home/wu/hmasd-inputs/frrie-a04-p12-command-20260907.sh`, then invoked by
  `/bin/bash` on that file. The digest records exact requested delivery, not a new runtime guard.
- Admission: cwd plus `temp/directions/finite_resource_relational_inductive_efficiency/technical/a04_system312_admission.json`.
  The on-node system-Python preflight is immediately joined by `&&` to T0.
- Result root: cwd plus `temp/directions/finite_resource_relational_inductive_efficiency/exp/a04_system312`.
- Exact chain: create venv, one NumPy acquisition/install, fresh admission, unchanged T0
  `--repeat 3 --updates 2` and publication; one CPU thread, FP32/int64; 384 tape constructions,
  128 distinct tape inputs; zero learner/optimizer/native/model exposure.
- Bound: one whole `timeout --signal=TERM --kill-after=5s 300s` chain, including setup through
  publication. No extra invocation, package version, arm, repetition, workload smoke or fallback.

## Prelaunch source staging (control-plane facts)

The accepted-name check returned `not_found`; the dedicated venv, detached worktree and staged
command paths were absent. The first plain-shell `git cat-file` lookup blocked in the partial
clone's Git/HTTP children before any A04 setup or handle acceptance. Root identified five
hanging same-SHA queries and explicitly instructed their termination, without duplicate queries.

At termination, PID 2747743 was already absent. Query roots 2747779, 2747829 (this DM's lookup),
2747896 and 2748003 and their 12 verified descendants received SIGTERM; none remained after
collection. No SIGKILL or experiment signal was needed. Raw termination receipt is in the local
runtime directory above as `source_query_termination.json`.

A 45 s bounded fetch via the configured `zsh -lic` network shell reached GitHub and populated
FETCH_HEAD from `codex/frrie`, but exited 1 because stale remote-tracking ref
`origin/codex/frrie/dirty-intake-20260904` prevented creation of `origin/codex/frrie`.
That ref was preserved. The fetched objects permitted the declared detached worktree directly:
`git worktree add --detach ... d6844...` completed exit 0 in approximately 3.45 s. Its HEAD
equals the bound SHA and its status is clean. This administrative staging does not run the
scientific/setup payload or change the fixed source. The ref collision is not a scientific result.

## Adoption and terminal return

At this prelaunch commit there is no accepted A04 handle and no setup/tape exposure. The next
authorized operation is exact file delivery and one invocation of the staged command. On
acceptance, send the actual supervisor receipt/log paths to Root and CM, retain observation until
Root ACK, then release this checkout to the CM for collection and technical acceptance.
Every terminal outcome returns to this DM for card §3, all-outcome intake and Chinese brief.
No A04 outcome identifies the old cause or authorizes R09.

scope: none

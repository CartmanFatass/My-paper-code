# The cloud / cross-device comparison line is retired (user ruling 2026-08-01)

**Status: the direction is CANCELLED, not disproven.** This note is its
scientific record; the code, workflow file, routing doctrine and manifests are
deleted and live only in git history (removal commit on `untied-k`, 2026-08-01).

## What was tried

A GitHub Actions vehicle (`d7s-audit.yml`: benchmark / audit / workers / replay
jobs), a compute-routing doctrine ("conclusion-bearing work goes to the cloud"),
and a cross-machine reproducibility apparatus: world digest probe/diff,
world-conformance gate, clone-conformance check, prelaunch cost bound, and the
Route A world-manifest + replay probe/gate ordered as the A1 precondition by the
ruling in round `20260730_d7_s_manifest_replay_gate_result`.

## What it returned

- Hosted runner ~1.4x slower than local; the 6 h job ceiling binds at |Z|=8
  with ~14 minutes of headroom (run 30245735762).
- Same seeds, different machines -> different OS-entropy user worlds
  (pre-repair, local t_e=708 vs runner t_e=921).
- Two cloud runs disagreed on 3 of 8 topologies' world fingerprints while both
  reported `all_seed_controlled=true`. **UNRESOLVED**; it did not reproduce on
  the re-downloaded round-2 artifacts. The dtype-width half is closed 6/6
  (`20260731_USER_CLUSTER_ASSIGNMENTS_DIVERGENCE_IS_DTYPE_WIDTH_NOT_VALUES.md`).
- Local manifest replay reproduced every registered quantity except assertion 6
  (`20260730_MANIFEST_REPLAY_GATE_FIRST_RESULT.md`) — a cross-process PASS only.
- The ruling's cross-machine two-job gate never ran; its escalation is
  withdrawn with this retirement.

## Why it is dead

User ruling 2026-08-01: the line is over-engineering. All compute now runs on
the single local workstation, so cross-machine reproducibility is no longer a
property any claim of this project needs, and the apparatus was consuming the
research loop it existed to serve.

## What survives

- The population-provenance requirement stands **on one machine**: a registered
  episode key must still identify one reproducible world (Pro ruling, round
  `20260730_d7_s_provenance_correction_result`).
- `runtime_identity` stays in every audit artifact; the scenario7 canonical
  post-pin initialization barrier and its tests stay; all evidence notes and
  round records stay at their original paths.

## Owed to Pro at the next touchpoint

Disclose the cancellation and local-only execution, and ask Pro to re-rule the
successor-population route: the A1 selection precondition (a cross-machine
`MANIFEST_REPLAY_PASS`) is unsatisfiable by design now that only one machine
exists.

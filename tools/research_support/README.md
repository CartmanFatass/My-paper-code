# Research support and UAV/UE visualization suite

Diagnostic tooling for the HMASD research work: a live and offline viewer for the UAV / UE /
base-station scenes, algorithm capability reports, run and configuration inspection, and
locally generated bundles. It is a **reading** layer. It starts no research.

```
python -m tools.research_support --help
```

The current host's scientific (3.10 + torch) and control-plane (3.11+) interpreters are
configured in `.codex/hmasd-compute.toml`. From the checkout root, use
`python3 -c 'from tools.research_support.interpreters import scientific_interpreter; print(scientific_interpreter())'`
on POSIX, or `py -3.11 -c 'from tools.research_support.interpreters import scientific_interpreter; print(scientific_interpreter())'`
in PowerShell; substitute `control_plane_interpreter` for the other role. See
`tests/AGENTS.md` for ready-to-run test commands on both hosts.

`interpreters.py` resolves these for the running host, so `recommend-tests` and
`inspect-env --probe` emit a command that is runnable where it is read. Override with
`HMASD_SCIENTIFIC_PYTHON` / `HMASD_CONTROL_PLANE_PYTHON`. Never point a Linux checkout at
`/mnt/c/.../python.exe`: that runs a Windows torch build against Linux paths and nothing
in the record would say the run crossed an OS boundary.

On Linux, put the venv's `bin` on `PATH` (or activate it) for anything that builds the
native C++ geometry backend — `ninja` lives in the venv, and `torch.utils.cpp_extension`
looks for it on `PATH`, not in `sys.prefix`.

Nothing here needs a new dependency; GIF and MP4 export use an encoder only if one is
already installed and refuse with an actionable message if not.

## What it will not do

These are contract, not defaults, and the tests in `tests/tools/research_support/` are what
hold them:

- **Zero training.** No command in this suite starts a fit or a hyperparameter search.
  Every executing command prints its scope first, including `optimizer updates: 0` and
  `formal training fits: 0`. `record-eval` is the only command that runs a trained
  checkpoint, and only when you name that checkpoint on the command line.
- **No recomputation for display.** Frames carry values the simulation already computed.
  The viewer never asks for another SINR evaluation, another routing solve or another
  policy forward pass in order to draw something.
- **Closing the browser cannot affect a run.** The viewer is a separate read-only process.
  It exposes no endpoint that can start, stop, step or reset anything, and it serves only
  `GET` and `HEAD` on loopback behind a session token and an `Origin` check.
- **Missing evidence stays missing.** A value that was not recorded is rendered as *not
  recorded*, never as `0`, never as a passed check, never as a current default. `Measured`
  in `records.py` keeps a measured zero distinct from unknown, unsupported, not-applicable,
  missing-artifact, invalid and not-recorded.
- **No privileged data reaches the policy.** The viewer's "policy-visible" mode reads the
  frame's `observation_view` and nothing else; anything drawn from simulator truth appears
  under its own heading. Unknown policy-visible fields are never filled in from truth.
- **No fallbacks.** A missing dataset, config, checkpoint or episode list is refused by
  name. Nothing silently substitutes a fixture, a synthetic stand-in or a second loader.
- **Aggregate demand points are labelled as aggregates.** In the service-restoration scene a
  ground marker stands for one source grid cell, not a person, a subscriber or a device.
  Movement is demonstrated on the legacy relay route, which has genuinely mobile UEs; no
  moving UE is invented for the service-restoration scene.

## Capture profiles

`capture/profiles.py` implements the efficiency contract. Four profiles:

| profile | what it is for | default |
|---|---|---|
| `off` | every existing training and evaluation run | yes |
| `live_preview` | an operator is watching right now | opt-in |
| `record_eval` | an explicitly requested evaluation recording | opt-in |
| `replay_only` | reading something already on disk | opt-in |

On the `off` path the shared environment costs one attribute load and one `is not None` test
per decision step and per substep. `CaptureGate.admit()` checks, in this order: profile,
lane, then the **completed-step** gate — all before it reads a clock at all — then a single
clock read, then circuit breaker, wall interval, viewer lease, session bound and byte budget.
Every gate is evaluated before any array is copied. The producer reads the viewer lease as a
pre-armed 8-byte double in shared memory; there is no socket, file scan or RPC on that path.

Measure it yourself:

```
python -m tools.research_support efficiency-check \
  --config configs/uav_service_restoration/smoke_fixture.json --output <new dir>
```

## Common tasks

**Watch a rule-controller rollout live.** Opens a loopback viewer and holds it after the
rollout finishes. Nothing is captured until the browser actually holds the lease.

```
python -m tools.research_support demo --route service-restoration \
  --config configs/uav_service_restoration/smoke_fixture.json \
  --controller backhaul_aware_greedy --episodes 1 --live
```

**Record a trace, then read it offline.** The trace is the scientific artifact; the display
is not.

```
python -m tools.research_support demo --route legacy-mobile-relay \
  --config configs/research_support/legacy_mobile_relay_demo.json \
  --episodes 1 --trace-output temp/research_support/legacy-trace

python -m tools.research_support replay --trace temp/research_support/legacy-trace
```

**Serve traces already on disk.** This command runs no simulator and cannot attach to an
uninstrumented process.

```
python -m tools.research_support serve \
  --trace "relay=temp/research_support/sr-trace" \
  --trace "static=temp/research_support/sr-trace-static"
```

**Compare two policies on the same world.** The viewer verifies both traces carry the same
world identity before it will align them, and aligns by simulated time, never by frame index
or wall clock. It invents no frame beyond the shorter trace's recorded coverage.

**Inspect a route's effective configuration.** Static by default; `--probe` constructs the
environment in a child process and promotes the values it actually observed to
`verified_runtime`.

```
python -m tools.research_support inspect-env --route service-restoration \
  --config configs/uav_service_restoration/smoke_fixture.json --probe
```

**Export a trace.** `html` is a self-contained page with no external request; `json` is the
frames; `png` is one figure; `gif` and `mp4` need an encoder you already have.

```
python -m tools.research_support export --trace <dir> --format html --output <file>
```

## The viewer

Loopback only, `GET`/`HEAD` only, session token on every data route, `Origin` and `Host`
validated, static files served through a resolved-path containment check, and no external
URL anywhere in the page — no CDN, no web font, no remote image.

Reading the scene:

- Marker **area** is proportional to offered demand, so doubling demand doubles the quantity
  the eye integrates.
- Every status pairs a **colour with a marker shape**; colour is never the only difference.
- A **solid** link is carrying traffic. A **dotted** link is geometrically available and
  carrying nothing. A feasible link with zero flow must never look like service.
- The status bar separates `sim` (interval end), `geometry` (the quadrature point the solve
  and the drawn positions belong to) and `measured` (the window the interval totals cover).
- `drops` and `gated` count frames the display never received. Display frames may be
  decimated; scientific metric and event evidence in the trace may not.

## Layout

```
capture/         the efficiency contract, transports, trace store, per-route observers
viewer/          loopback server and the browser client
plots/           C01-C14 capability charts and the figure contract
readers/         run artifact readers, one per producing family
records.py       the frozen shared data model; everything imports it
cli.py           every subcommand
```

`records.py` is the contract between every other module: `Measured`, `Validity`,
`EntityId`/`LifetimeRegistry` (a reused array slot is a new lifetime, never the same entity),
and `canonical_link_key()` (link identity from endpoints, link class and resource domain —
never from a solver's per-solve integer index).

## The one shared-core change

`envs/uav_service_restoration/env.py` gained four optional observer seams and
`set_capture_observer()`. `tests/tools/research_support/test_off_path_noninterference.py`
loads the pre-change revision of that file out of git, runs the same rollout against both,
and asserts identical trajectories, identical episode boundaries, identical RNG stream state
and an identical number of scheduler solves. The legacy relay route needed no shared edit at
all: its observer reads what the adapter already builds.

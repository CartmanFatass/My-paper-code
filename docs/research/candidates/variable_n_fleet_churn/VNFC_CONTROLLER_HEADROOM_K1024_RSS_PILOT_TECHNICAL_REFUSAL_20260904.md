# VNFC controller-headroom K=1024 RSS pilot — technical refusal

- Direction: `variable_n_fleet_churn`
- Prospective predecessor: accepted `VNFC-CONTROLLER-HEADROOM-A-RECON-R01`, branch
  `CH-D / HEADROOM_BRACKET_UNRESOLVED`
- Pilot class: result-blind engineering resource disposition; **not a scientific object or result**
- Git SHA: `f6101bdb4db900fbefd9253a271068de17a2b9d0`
- Date: 2026-09-04
- Disposition: **`TECHNICAL_REFUSAL / RSS_ENVELOPE_NOT_SUPPORTED`**

## 1. Question and protected boundary

The accepted R01 intake selected one possible `K=1024` successor only if a result-blind pilot could
conservatively support the existing expected peak-RSS envelope below 2 GiB. This pilot asks only
whether the current native materialization and available measurement support that engineering
claim.

It does not ask whether `K=1024` finds headroom. It generated no R02 target world, used no R02 RNG
or world coordinate, read and reported no endpoint, command, policy, lower bound, upper bound, or
branch input, and created no science card, result root, preflight receipt, model, optimizer, or
checkpoint.

## 2. Exact one-run pilot

Working directory:

```text
C:\Projects\HMASD-worktrees\codex-vnfc-controller-headroom-20260904
```

PowerShell invocation:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c $pilotCode
```

Exact `$pilotCode`:

```python
import json
import time
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import deterministic_general_episode
from experiments.candidates.variable_n_fleet_churn_headroom.native_backend import build_analysis_backend, run_headroom_fixture
from scripts.run_vnfc_controller_headroom import peak_rss_bytes
build_analysis_backend()
fixture = deterministic_general_episode(1)
started = time.perf_counter()
row = run_headroom_fixture(fixture, 1024)
wall = time.perf_counter() - started
print(json.dumps({
    "fixture": "deterministic_general_episode(failed_zone=1)",
    "beam_width": 1024,
    "wall_seconds": wall,
    "peak_rss_bytes": peak_rss_bytes(),
    "beam_depths": [
        {
            "depth": item["depth"],
            "states_before": item["states_before"],
            "legal_commands": item["legal_commands"],
            "expansions": item["expansions"],
            "states_retained": item["states_retained"],
            "native_ticks": item["native_ticks"],
        }
        for item in row["beam_depths"]
    ],
}, sort_keys=True))
```

Exactly one fresh Python process ran the synthetic fixture. No retry or second pilot was attempted.
The prebuilt analysis DLL was created outside any scientific root at
`temp/directions/variable_n_fleet_churn/build/controller_headroom/headroom_analysis.dll`.

## 3. Direct engineering observations

The exact stdout JSON, followed by `CRLF`, was:

```json
{"beam_depths": [{"depth": 0, "expansions": 1164, "legal_commands": 1164, "native_ticks": 23280, "states_before": 1, "states_retained": 1024}, {"depth": 1, "expansions": 68625, "legal_commands": 68625, "native_ticks": 1372500, "states_before": 1024, "states_retained": 1024}, {"depth": 2, "expansions": 173364, "legal_commands": 173364, "native_ticks": 3467280, "states_before": 1024, "states_retained": 1}], "beam_width": 1024, "fixture": "deterministic_general_episode(failed_zone=1)", "peak_rss_bytes": 0, "wall_seconds": 1.9359753000026103}
```

The process completed 243,153 beam expansions and 4,863,060 native ticks in 1.9359753 seconds. It
filled both retained layers to `K=1024`.

The current C++ implementation materializes the complete depth-1 `expanded` vector before
selection. The relevant declared upper bound is `1961*K = 2,008,064` materialized nodes. This
synthetic fixture materialized 68,625 nodes, only about 3.42 percent of that bound. It therefore
neither reaches nor upper-bounds the allocation that controls the expected RSS envelope.

The Windows memory call returned sentinel `peak_rss_bytes=0`. That is unavailable telemetry, not
zero memory use. A pilot that exercises only 3.42 percent of the controlling node bound and has no
RSS measurement cannot conservatively support an expected peak below 2 GiB.

## 4. Disposition and scientific boundary

The resource disposition is **technical refusal**. The favorable wall projection for `K=1024`
(`723.80 s` for the worst-case sixteen-world arm under the recorded result-blind calibration) does
not substitute for RSS evidence. No successor card is frozen, no CM implementation objective is
opened, and no target result may launch from this pilot.

This refusal has no scientific polarity. It does not say that headroom is absent, that BCRH is
sufficient, that `K=1024` would fail to improve the lower bound, or that a learner budget ladder is
or is not warranted. R01 remains the controlling scientific observation: valid complete `CH-D`,
with aggregate `L/U=7/960 / 3299/4800` and the optimum unidentified.

## 5. Object-tier decision

Options:

- (a) accept the technical refusal, do not freeze or launch `K=1024`, and return the next family
  choice to the persistent convergence node;
- (b) treat the sentinel RSS value as zero and proceed;
- (c) treat 3.42-percent allocation coverage as sufficient or run another uncarded pilot.

Recommendation: **(a)**. Options (b) and (c) would invent resource evidence or repeat an
underpowered probe without a prospectively different bound.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This is reversible and changes no scientific meaning. The prospective
`K=1024` successor remains unregistered.

## 6. Direction-tier boundary

The next choice is no longer object-local. The persistent
`em:variable_n_fleet_churn:convergence` node must decide among at least:

- open a memory-bounded `K=1024` implementation route that preserves the exact beam order and
  comparator semantics while obtaining a conservative result-blind allocation/RSS disposition;
- recast the host/population/headroom discriminator instead of widening this beam;
- park the controller-headroom family with `CH-D` unresolved; or
- close this family without turning the technical refusal into scientific polarity.

Recommendation to the direction node: first consider the memory-bounded `K=1024` route, because
the blocker is current vector materialization/measurement rather than a scientific result. The
strongest alternative is a host/headroom recast if preserving the exact search requires machinery
or cost outside the research-code budget. This document does not select among those options.

Exposure remains `not applicable (A/RECON, no learner)`: zero parameters, initialisations,
optimizer steps, training transitions, or checkpoints. Any future sweep must retain the recorded
per-arm wall projections and establish its own memory admission before a result invocation.

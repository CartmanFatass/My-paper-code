# Restart handoff

Updated: 2026-07-25. Branch `untied-k`. Everything is committed and pushed.

Read `AGENTS.md`, then this file, then `docs/project/RESEARCH_GOAL.md`.

## Paused on compute, 2026-07-26

**Part B is blocked on episode budget, not on any decision.** The user ruled the
local CPU insufficient and will run the deciding job elsewhere. The instrument is
repaired and verified; what remains is arithmetic.

Read **`docs/project/REMOTE_COMPUTE_HANDOFF.md`** — it carries the exact command,
the read order, and why 64 episodes. Do not start a local H=1500 run; that is the
job that was killed.

At four episodes `B_H` is statistically indistinguishable from zero at both short
horizons (`H=139`: −1.514, CI −3.76..+1.79; `H=450`: +10.149, CI −26.6..+46.9), so
every normalized margin there is uninformative. Back-solved, `H=450` needs ~52
episodes for `B_H` alone to exclude zero.

No loop driver is attached: the user cancelled it and the session-only cron has
expired.

## Next action, exactly

**D7.S part B — re-run the horizon sweep on the repaired instrument, then one
Pro round.** Do not compute or report a margin before the reproducibility check
below passes; the margins measured on 2026-07-25 are all invalid.

```text
harness  scripts/audit_d7_s_persistence_margin.py   (build_env, --topology-seed)
tests    tests/audit_d7_s_persistence_margin_test.py
check    two processes, identical args -> byte-identical arm_means
sweep    H = 139 (exchange window), 450 (energy window), 1500 (registered episode)
         all three at the SAME --topology-seed, or they are not comparable
```

The Pro round carries four coupled items, batched deliberately:

1. `set_flex` is defined by the frozen design as "re-decides each check", which is
   what `constructive` already does, so `U*_flex = constructive - keep_flex` while
   `B_H = constructive - null` -- treatment and normalizer share a term, which D0
   forbids. Correcting the arm is protected semantics.
2. `Delta` is absent from the instrument: D0 freezes it at one check interval, the
   keep arms hold for the whole window.
3. No `H` yet found where the margin and its own normalizer are both well behaved.
   At `H = 139` the exchange margin is large but `B_H` is 0.932; at `H = 1500`
   `B_H` is healthy but the exchange margin inverts.
4. The environment ignores its seed for topology. That is wider than this audit.

### The superseded instruction, kept because part B is still frozen

```text
design   docs/research/designs/D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md
source   envs/pettingzoo/scenario7_energy_aware.py   (UAVEnergyAwareRelayEnv)
         envs/pettingzoo/uav_env.py                  (base motion, positions)
estimand docs/research/designs/D0_CARRIER_AND_ESTIMAND.md  -- U*_{i,src}
```

Part B is **already frozen** in the design file — mixed-urgency history class, `H`
from the registered scenario-7 config (**read it, do not choose it**), best legal
joint continuation in both terms, constructive versus full-sync controls that pay
the real motion cost, the margin thresholds, and the branch meanings. Do not
renegotiate any of those after seeing output.

```text
U*_stable,src / B_H  <=  -0.10        U*_flex,src / B_H  >=  +0.10
```

Route, cheapest first per `AGENTS.md` *Result interpretation*: derivation, then
constructive/exhaustive control on a **small registered instance**. **Not** a
training run. `B_H` is the constructive-minus-null gap measured before the
comparison, averaged over windows starting at check boundaries — never a step-0
window, which on the toy collapsed `B_5` to exactly zero.

Only two branches remain open; part A already ruled out the third:

```text
PERSISTENCE_NECESSARY_SOURCE   -> proceed to D7.3, replacement toy unnecessary
SOURCE_NECESSITY_UNRESOLVED    -> tenure control advances carrier capacity only
```

**D8 is blocked in every branch** until part B resolves.

## What is settled — do not re-derive or re-litigate

- **D7.2B is closed.** The toy admits an optimal full-sync swap, so persistence was
  optional and its null carried no information. Ruled `ACCEPT` by Pro. Registered
  audit: `A = 1.0/1.0`, `U~_flex 0.43006` against `U~_stable 0.25186`, difference
  `0.17820` short of its `0.20` floor, `P(KEEP|stable) = 0.0`, full-sync SET `1.0`.
  In 384 ledger rows `token_kind` took one value, `SET`, and `skill_age` was
  exactly 5 at every check past the first.
- **D7.S part A is complete** and is a repository fact, not an estimand: a full-sync
  role permutation preserves **none** of return, position, energy, queue state or
  topology. `uav_positions` is written per agent from its own action
  (`uav_env.py:250`); `uav_battery_ratios` depletes with that UAV's own motion;
  return depends on position via SINR (`scenario7:1147`) and backhaul (`:1156`).
  So `ZERO_COST_ROLE_EXCHANGE_SOURCE` is structurally absent here.
- **Lossy exchange is necessary, not sufficient.** Do not upgrade part A into
  `PERSISTENCE_NECESSARY_SOURCE` without the margin. That inference — structure to
  margin without computing the margin — is what cost D7.2B a run.
- **`U_opp` is renamed `U_max_pi`** and is policy-conditional; the source-level
  quantity is `U*_{i,src}`, which reoptimizes or oracle-supplies the joint
  continuation in **both** terms. The archived result JSON keeps the old key
  `u_opp_flex_split_sample` so it stays readable against its own schema.
- **The broad class claim is dead.** Permutation-invariant reward alone does *not*
  imply free role exchange. Use the narrow statement in `AGENTS.md`, *A positive
  control must make its target behaviour necessary*.
- **Competence budget is not a free lever.** The D7.2B escalation was accepted for
  that narrow result only. Any replacement needs a pre-registered finite competence
  ladder that reports no-access at its maximum stage rather than raising budget
  until A passes.
- **Parked:** `R30_ALL_SET_BASIN_INDUCTIVE_BIAS` — a retained hypothesis needing
  multi-seed pre-registration. Explicitly not worth runs on an equal-optimum source.

## Traps that already bit, and will again

- **`keep_head.weight` is zero-initialized**, so `keep_logit` starts
  state-independent and both agents deterministically KEEP at entry. Comparing
  realized *tokens* across conditions therefore shows no difference even when the
  wiring is correct. Probe the **skill logits**.
- **Nonzero gradients are not behaviour.** The first two D7.2B runs sat at chance
  with `high_grad_norm` 0.26–0.48 because one epoch at `lr 1e-4` for 200 updates is
  200 optimizer steps. Count optimizer steps and check the policy left its
  initialization (entropy, marginals) before reading anything scientific into a
  flat result.
- **Historical results may be a tenth of your budget.** The prior toy record read as
  a settled credit failure; its archived contract showed 20 outer updates and
  12,800 timesteps. Open the archived contract before citing any past conclusion.
- **`check_compute_free.ps1` cannot tell your own run from another line's.** Read
  the reported `heavy_pids` first: if the load is ours, wait on the completion
  notification and do documentation-only work; do not sleep an hour beside a job
  that reports itself.
- **This environment ignores its seed for topology.** `ground_bs_positions` and
  `charging_station_positions` are drawn at *construction* from `np_random`
  before any seed exists, and `reset(seed=)` never regenerates them. Two
  constructions differ by kilometres; the same arm on three fresh envs spread
  17 %. Seeding the global RNG first does **not** help — the draw is off
  `np_random`. Any comparison across processes is invalid unless the topology is
  pinned, as `build_env` now does. This silently destroyed a three-point horizon
  sweep before anyone looked.
- **`reset(seed=)` does not clear everything.** Eight attributes survive it,
  including `user_pause_times` and `last_global_sync_step`. The first run on an
  env is pristine and every later one is used, so whichever arm runs first is
  privileged — and it was always `constructive`, the arm `B_H` is built from.
  Build a fresh env per arm.
- **An impossible pair of diagnostics is a bug, not a finding.** `charge_steps`
  of 647.5 alongside `dock_events` of 0.0 was numpy aliasing: `np.asarray` on a
  matching dtype returns the *same object*, so the rising-edge test compared a
  buffer with itself. Check arithmetic consistency between diagnostics before
  reading any of them.

## Transport, if a round is needed

`$hmasd-review-round`, then `claude-in-chrome`. Registered conversation for this
branch is `open_divergent`, `6a63979e-35d8-83e8-8da7-10de59a5fdeb`.

- `preflight_review_round.ps1` must print `ROUND_PREFLIGHT_READY`. The allow-list
  must include `docs/project/ALGORITHM_PRINCIPLES.md` and
  `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`, or it fails.
- Compose the fence as `10_FENCE.txt` and **paste** it — a newline submits in that
  composer. ASCII only.
- Prove fence absence by counting user turns; verify the send by measuring
  (composer empty **and** user turns +1).
- Capture only with `Copy response` against a **clipboard sentinel**. Three clicks
  silently wrote nothing on 2026-07-25 and only the sentinel caught it; a tab
  replacement cleared it. Transcription and `get_page_text` are prohibited archive
  paths.
- The tab wedges on this conversation. Reload-and-wait twice, then close and
  recreate, ending with exactly one tab.

## Authorization

Full and unattended. Never return to the user for resource, compute or continue
permission. Compute is authorized; only its timing is gated. `AGENTS.md`,
*Implementing a ruling is not making one* — a blocker this conversation wrote is
not authority over this conversation.

`iterations_remaining=19` of the user's 20-iteration grant.
`iterations_since_last_compaction=1`, so this seam is a compaction point.

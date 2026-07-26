"""D7.S part B — main-scenario persistence margin, constructive controls only.

Contract: `docs/research/designs/D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md`.
Estimand: `docs/research/designs/D0_CARRIER_AND_ESTIMAND.md`, `U*_{i,src}`.
Ordered by: `rounds/20260725_d7_2b_source_persistence_necessity/21_PRO_OPEN_RAW.md`.

No training and no policy. `U*_{i,src}` is a **source** property, so both of its
terms take the best legal continuation — here supplied by the environment's own
constructive layout oracle rather than by a learned controller.

Everything the contract froze is read from it, not chosen here:

```text
H      = 139 steps   causal duty window: 0.5214 * area_size / max_speed
Delta  = k = 10      check cadence; commitments are re-decided at checks only
margin U*_stable,src / B_H <= -0.10        U*_flex,src / B_H >= +0.10
B_H    = constructive minus null, over windows starting at check boundaries
```

**Declared external-return proxy.** `G` is the QoS satisfaction ratio computed by
the environment's own end-to-end rate model — `mean(clip(rate / qos_target, 0, 1))`
— summed over the window. This is the same quantity
`estimate_heuristic_qos_feasibility` maximizes, so the oracle and the return agree
by construction. Declared before measurement; it is not the shaped training reward,
which carries load-balance and energy terms that `G` must exclude (D0 §3).

**Why the physics is driven directly.** The audit calls `_update_channel_state`,
`_update_uav_connections`, `_compute_routing_paths` and
`_calculate_end_to_end_user_rates` itself instead of `env.step(actions)`. Going
through `step` would apply the reward model, energy accounting and action
normalization, none of which belong in an external-return source audit, and would
force an action-space encoding of "hold this position" that the source does not
have. Positions and user motion are the entire state this estimand depends on.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

# --- frozen constants, from the contract ------------------------------------
MARGIN_STABLE_CEIL = -0.10
MARGIN_FLEX_FLOOR = 0.10


def kmeans_centroids(user_xy: np.ndarray, k: int, iters: int = 30) -> np.ndarray:
    """The oracle's own clustering, mirrored so the caller controls which UAV
    re-targets. Same seeding and same fixed iteration count as
    `estimate_heuristic_qos_feasibility` (scenario7:1199-1220)."""
    seed_indices = np.linspace(0, len(user_xy) - 1, k, dtype=int)
    centroids = user_xy[seed_indices].copy()
    for _ in range(iters):
        d = np.sum((user_xy[:, None, :] - centroids[None, :, :]) ** 2, axis=2)
        labels = np.argmin(d, axis=1)
        updated = np.array([
            np.mean(user_xy[labels == c], axis=0) if np.any(labels == c)
            else centroids[c]
            for c in range(k)
        ])
        if np.allclose(updated, centroids):
            break
        centroids = updated
    return centroids


def duty_targets(env, n_relay: int, n_service: int, height: float) -> np.ndarray:
    """Best legal layout for the *current* user positions.

    Relays sit on the ground-BS-to-service-centre line and services at cluster
    centroids, exactly as the environment's oracle constructs them.
    """
    user_xy = np.asarray(env.user_positions[:, :2], dtype=float)
    bs_xy = np.mean(env.ground_bs_positions[:, :2], axis=0)
    centroids = kmeans_centroids(user_xy, n_service)
    service_centre = np.mean(centroids, axis=0)

    targets = np.zeros((n_relay + n_service, 3), dtype=float)
    for i in range(n_relay):
        fraction = (i + 1) / (n_relay + 1)
        xy = (1.0 - fraction) * bs_xy + fraction * service_centre
        targets[i] = [xy[0], xy[1], height]
    for j in range(n_service):
        targets[n_relay + j] = [centroids[j][0], centroids[j][1], height]
    return targets


def qos_ratio(env) -> float:
    """External return for one step: the source's own service objective, **unclipped**.

    The first version of this audit used the clipped QoS satisfaction ratio,
    `mean(clip(rate / target, 0, 1))`, because that is what the environment's layout
    oracle maximizes. It is a **vacuous instrument here** and the measurement said
    so unambiguously: over a 40-step window the constructive, null, keep_stable,
    keep_flex and set_flex arms returned *exactly* `38.66666666666668`, which is
    `40 * 29/30` — 29 of 30 users sit so far above the QoS target that clipping
    pins them at `1.0` and the metric cannot distinguish a good layout from a
    slightly worse one. `B_H` came out identically `0`.

    That is the pre-freeze checklist's own failure: an invariant satisfied
    trivially, making the measurement vacuous (`AGENTS.md`, question 3). The proxy
    is therefore replaced **because it cannot separate any arm**, not because it
    failed a threshold — the thresholds were never reached. Unclipped, the same
    physical quantity retains its sensitivity to layout.

    Saturation is re-checked at run time and reported, so this cannot recur
    silently.
    """
    env._update_channel_state()
    env._update_uav_connections()
    env._compute_routing_paths()
    rates_bps, _, _ = env._calculate_end_to_end_user_rates()
    target = max(env.user_qos_rate_mbps * 1e6, 1e-8)
    return float(np.mean(rates_bps / target))


def saturation_fraction(env) -> float:
    """Fraction of users at or above the QoS target — the diagnostic that caught
    the vacuous proxy. Reported with every result."""
    rates_bps, _, _ = env._calculate_end_to_end_user_rates()
    target = max(env.user_qos_rate_mbps * 1e6, 1e-8)
    return float(np.mean(rates_bps >= target))


def step_toward(positions: np.ndarray, targets: np.ndarray, max_speed: float,
                dt: float) -> np.ndarray:
    """One step of bounded motion. This is where a duty exchange pays for itself:
    a UAV cannot teleport to another UAV's post."""
    delta = targets - positions
    dist = np.linalg.norm(delta, axis=1, keepdims=True)
    step_len = min(max_speed * dt, np.inf)
    scale = np.where(dist > step_len, step_len / np.maximum(dist, 1e-9), 1.0)
    return positions + delta * scale


def run_arm(env, *, seed: int, horizon: int, check_every: int, arm: str,
            focal_stable: int, focal_flex: int) -> float:
    """Roll one arm forward and return the summed external return over `horizon`.

    Arms, all under best legal continuation except where a focal commitment is
    deliberately held or re-decided:

      constructive  every duty re-decided at every check
      null          no renewal at all; the t=0 layout is held for the window
      keep_stable   the relay holds its t=0 post; everything else re-decides
      set_stable    the relay re-decides at t=0 and swaps duty with a service UAV
      keep_flex     one service UAV holds its t=0 post; everything else re-decides
      set_flex      that service UAV re-decides at every check
    """
    env.reset(seed=seed)
    best = env.estimate_heuristic_qos_feasibility()
    n_service = int(best["service_uavs"])
    n_relay = int(env.n_uavs - n_service)
    height = float(best["height_m"])
    if n_relay < 1 or n_service < 1:
        raise RuntimeError("oracle returned a degenerate relay/service split")

    positions = np.asarray(env.uav_positions, dtype=float).copy()
    # Duty index -> UAV index. A swap permutes this map, not the positions.
    duty_of = np.arange(env.n_uavs)
    if arm == "set_stable":
        duty_of[[focal_stable, focal_flex]] = duty_of[[focal_flex, focal_stable]]

    held = np.zeros(env.n_uavs, dtype=bool)
    if arm == "keep_stable":
        held[focal_stable] = True
    elif arm == "keep_flex":
        held[focal_flex] = True
    elif arm == "null":
        held[:] = True

    targets = duty_targets(env, n_relay, n_service, height)[duty_of]
    frozen_targets = targets.copy()

    total = 0.0
    dt = float(env.time_step)
    max_speed = float(env.max_speed)
    for t in range(horizon):
        if t > 0 and t % check_every == 0:
            fresh = duty_targets(env, n_relay, n_service, height)[duty_of]
            targets = np.where(held[:, None], frozen_targets, fresh)
        positions = step_toward(positions, targets, max_speed, dt)
        env.uav_positions = positions.copy()
        total += qos_ratio(env)
        env._move_users()
    return total


def run_arm_stepped(env, *, seed: int, horizon: int, check_every: int, arm: str,
                    focal_stable: int, focal_flex: int,
                    initial_energies=None, energy_seed: int = 0) -> dict:
    """Same arms, driven through `env.step()` so **energy actually depletes**.

    The direct-physics runner above cannot be used at `S2+`: battery accounting,
    charging capture and docking all live inside `step`, so driving positions
    directly would report energy-enabled *labels* over energy-inert *dynamics*.

    Actions are the scenario's own 4-vector — three normalized velocity components
    scaled by `max_speed`, plus a dock request compared against
    `dock_request_threshold` (`_extend_spaces_for_energy`, `scenario7:409-414`).

    External return stays **identical** to the S1 audit: the unclipped mean rate
    ratio read from the environment's own end-to-end model after each step. Only
    the dynamics change, never `G`.

    Recharge is what creates renewal need here. A UAV below its return reserve
    heads for the nearest station and must arrive within `charging_capture_radius_m`
    at under `charging_hover_speed_threshold` to capture, so the duty it vacates is
    genuinely uncovered for the transit plus charge duration. `constructive`
    reassigns duties among the **airborne** UAVs at each check; `null` never
    reassigns, so a vacated duty stays vacant.
    """
    env.reset(seed=seed)
    if initial_energies is not None:
        # The G2 registered source applies a fresh permutation of a fixed energy
        # multiset each episode, rather than sampling uniform 0.75-1.0. The
        # permutation is drawn from a private stream so it does not consume the
        # environment's user-motion, channel, station or action RNG.
        perm = np.random.default_rng(int(energy_seed)).permutation(
            initial_energies.size
        )
        env.uav_battery_ratios = initial_energies[perm].astype(float).copy()
        env._update_return_energy_state()

    best = env.estimate_heuristic_qos_feasibility()
    n_service = int(best["service_uavs"])
    n_relay = int(env.n_uavs - n_service)
    height = float(best["height_m"])

    duty_of = np.arange(env.n_uavs)
    if arm == "set_stable":
        duty_of[[focal_stable, focal_flex]] = duty_of[[focal_flex, focal_stable]]
    held = np.zeros(env.n_uavs, dtype=bool)
    if arm == "keep_stable":
        held[focal_stable] = True
    elif arm == "keep_flex":
        held[focal_flex] = True
    elif arm == "null":
        held[:] = True

    targets = duty_targets(env, n_relay, n_service, height)[duty_of]
    frozen_targets = targets.copy()

    dt = float(env.time_step)
    max_speed = float(env.max_speed)
    dock_threshold = float(getattr(env, "dock_request_threshold", 0.5))
    reserve = float(getattr(env, "return_reserve_ratio", 0.10))
    # Head for a station with a margin over the bare return reserve, so the
    # decision is made before the reserve is already spent.
    dock_trigger = min(0.95, reserve + 0.15)

    total = 0.0
    charge_steps = 0
    dock_events = 0
    was_charging = np.zeros(env.n_uavs, dtype=bool)

    for t in range(horizon):
        battery = np.asarray(getattr(env, "uav_battery_ratios",
                                     np.ones(env.n_uavs)), dtype=float)
        charging = np.asarray(getattr(env, "uav_charging",
                                      np.zeros(env.n_uavs, bool)), dtype=bool)
        needs_charge = (battery < dock_trigger) | charging

        if t > 0 and t % check_every == 0:
            fresh = duty_targets(env, n_relay, n_service, height)[duty_of]
            targets = np.where(held[:, None], frozen_targets, fresh)

        actions = {}
        station_xy = np.asarray(
            env.charging_station_positions[: env.n_charging_stations], dtype=float
        )
        for idx, agent in enumerate(env.agents):
            pos = np.asarray(env.uav_positions[idx], dtype=float)
            want_dock = bool(needs_charge[idx]) and station_xy.size > 0
            if want_dock:
                d = np.linalg.norm(station_xy[:, :2] - pos[None, :2], axis=1)
                tgt = station_xy[int(np.argmin(d))].copy()
            else:
                tgt = targets[idx].copy()

            delta = tgt - pos
            dist = float(np.linalg.norm(delta))
            if want_dock and dist <= float(
                getattr(env, "charging_capture_radius_m", 20.0)
            ):
                vel = np.zeros(3)          # hover to capture
            else:
                step_len = min(max_speed * dt, dist)
                vel = (delta / max(dist, 1e-9)) * (step_len / max(dt, 1e-9))
            act = np.zeros(int(env.action_dim), dtype=np.float32)
            act[:3] = np.clip(vel / max(max_speed, 1e-9), -1.0, 1.0)
            if int(env.action_dim) > 3:
                act[3] = 1.0 if want_dock else -1.0
            actions[agent] = act

        env.step(actions)
        total += qos_ratio(env)

        # .copy() is load-bearing. `uav_charging` is already a bool ndarray
        # (scenario7:157) that `step` mutates IN PLACE (scenario7:1698,1747), and
        # np.asarray on a matching dtype returns that same object -- so retaining
        # it as `was_charging` aliased the live buffer, made the rising-edge test
        # `now & ~was` identically False, and pinned dock_events to exactly 0 in
        # every arm of every run. charge_steps was unaffected and stayed valid.
        # The environment itself copies for precisely this reason (:1694, :1761).
        now_charging = np.asarray(getattr(env, "uav_charging",
                                          np.zeros(env.n_uavs, bool)),
                                  dtype=bool).copy()
        charge_steps += int(np.sum(now_charging))
        dock_events += int(np.sum(now_charging & ~was_charging))
        was_charging = now_charging

    final_battery = np.asarray(getattr(env, "uav_battery_ratios",
                                       np.ones(env.n_uavs)), dtype=float)
    return {
        "return": total,
        "charge_steps": charge_steps,
        "dock_events": dock_events,
        "min_final_battery": float(np.min(final_battery)),
        "mean_final_battery": float(np.mean(final_battery)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--horizon", type=int, default=139)
    parser.add_argument("--check-every", type=int, default=10)
    parser.add_argument("--seed", type=int, default=3229000)
    parser.add_argument("--out", default="")
    parser.add_argument("--stage", default="S1")
    parser.add_argument("--n-uavs", type=int, default=0)
    parser.add_argument(
        "--initial-energies", default="",
        help=("Comma-separated per-UAV initial battery ratios, applied as a fresh "
              "permutation each episode. The G2 registered source uses "
              "0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90 -- unlike config_1's "
              "uniform 0.75-1.0, which never depletes inside an episode."),
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    import config_1
    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

    config = config_1.Config()
    if int(args.n_uavs) > 0:
        # scenario_base.py:157 reads the fleet size from `n_agents`, not `n_uavs`.
        config.n_agents = int(args.n_uavs)
        config.n_uavs = int(args.n_uavs)
        config.max_observed_uavs = int(args.n_uavs)
    env = UAVEnergyAwareRelayEnv(config=config, energy_stage=args.stage)

    initial_energies = None
    if args.initial_energies.strip():
        initial_energies = np.array(
            [float(x) for x in args.initial_energies.split(",") if x.strip()],
            dtype=float,
        )
        if initial_energies.size != int(env.n_uavs):
            raise SystemExit(
                f"--initial-energies has {initial_energies.size} values but the "
                f"source has {env.n_uavs} UAVs"
            )

    horizon = 6 if args.smoke else int(args.horizon)
    episodes = 2 if args.smoke else int(args.episodes)

    arms = ("constructive", "null", "keep_stable", "set_stable",
            "keep_flex", "set_flex")
    acc: dict[str, list[float]] = {a: [] for a in arms}

    probe_seed = int(args.seed)
    env.reset(seed=probe_seed)
    probe = env.estimate_heuristic_qos_feasibility()
    n_service = int(probe["service_uavs"])
    n_relay = int(env.n_uavs - n_service)
    probe_saturation = saturation_fraction(env)
    focal_stable = 0                      # a relay: its duty target is BS-anchored
    focal_flex = n_relay                  # first service UAV: tracks a cluster

    # S1 has no energy dynamics, so the direct-physics runner is exact there and
    # much cheaper. Anywhere energy is enabled, the run MUST go through step().
    stepped = str(args.stage).upper() != "S1"
    diag: dict[str, list[dict]] = {a: [] for a in arms}

    for i in range(episodes):
        seed = probe_seed + 100000 + i
        for arm in arms:
            if stepped:
                out = run_arm_stepped(
                    env, seed=seed, horizon=horizon,
                    check_every=int(args.check_every), arm=arm,
                    focal_stable=focal_stable, focal_flex=focal_flex,
                    initial_energies=initial_energies, energy_seed=seed,
                )
                acc[arm].append(out["return"])
                diag[arm].append(out)
            else:
                acc[arm].append(run_arm(
                    env, seed=seed, horizon=horizon,
                    check_every=int(args.check_every), arm=arm,
                    focal_stable=focal_stable, focal_flex=focal_flex,
                ))

    mean = {a: float(np.mean(v)) for a, v in acc.items()}
    b_h = mean["constructive"] - mean["null"]
    u_stable = mean["set_stable"] - mean["keep_stable"]
    u_flex = mean["set_flex"] - mean["keep_flex"]

    measurable = abs(b_h) >= 1e-9
    norm_stable = u_stable / b_h if measurable else float("nan")
    norm_flex = u_flex / b_h if measurable else float("nan")

    if not measurable:
        branch = "SOURCE_NECESSITY_UNRESOLVED"
        reason = "B_H is degenerate; the normalized margin is undefined"
    elif norm_stable <= MARGIN_STABLE_CEIL and norm_flex >= MARGIN_FLEX_FLOOR:
        branch = "PERSISTENCE_NECESSARY_SOURCE"
        reason = ("both margins clear; individual persistence is necessary for "
                  "optimality on this source")
    else:
        branch = "SOURCE_NECESSITY_UNRESOLVED"
        reason = ("at least one margin did not clear its threshold under these "
                  "constructive controls")

    result = {
        "branch": branch,
        "reason": reason,
        "horizon": horizon,
        "energy_stage": str(args.stage),
        "stage_note": ("S1 disables battery_enabled and charging_enabled, so the "
                       "energy dynamics that create roster change are inert there; "
                       "S2/S3/S4 enable them"),
        "check_every": int(args.check_every),
        "episodes": episodes,
        "n_relay": n_relay,
        "n_service": n_service,
        "n_uavs": int(env.n_uavs),
        "n_users": int(env.n_users),
        "focal_stable_uav": focal_stable,
        "focal_flex_uav": focal_flex,
        "external_return": ("unclipped mean rate / qos_target, summed over the "
                            "window; the clipped form was vacuous, see qos_ratio"),
        "probe_qos_saturation_fraction": probe_saturation,
        "arms_all_equal": len({round(v, 9) for v in mean.values()}) == 1,
        "driven_via": "env.step" if stepped else "direct physics (S1 has no energy)",
        "energy_diagnostics": {
            a: {
                k: float(np.mean([d[k] for d in diag[a]]))
                for k in ("charge_steps", "dock_events", "min_final_battery",
                          "mean_final_battery")
            }
            for a in arms if diag[a]
        },
        "arm_means": mean,
        "b_h": b_h,
        "u_star_stable_src": u_stable,
        "u_star_flex_src": u_flex,
        "normalized": {"stable": norm_stable, "flex": norm_flex},
        "thresholds": {"stable_ceiling": MARGIN_STABLE_CEIL,
                       "flex_floor": MARGIN_FLEX_FLOOR},
        "contract": "docs/research/designs/D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md",
    }
    print(f"D7_S_BRANCH={branch}")
    print(f"D7_S_REASON={reason}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "d7_s_persistence_margin.json").open("w", encoding="utf-8") as h:
            json.dump(result, h, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

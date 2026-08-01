"""Pool sharded D7.S part B audit results into the JSON one monolithic run writes.

Episodes are independent and seeded `seed + 100000 + i`, so shards whose `--seed`
values tile one contiguous block reproduce exactly the episode set of a single
`--episodes N` run. Pooling is therefore loss-free: concatenate `per_episode`,
recompute the means, `B_H`, both margins and the bootstrap from the concatenation
— never average the normalized margins across shards, since a ratio of means is
not the mean of ratios.

Every scientific field is recomputed with the audit module's own functions and
frozen constants, with `ci_seed = seed_0 + 7717` — the value the monolithic run
would have used — so the pooled JSON matches what `--episodes N` at `seed_0`
would have written, field for field.

Refuses to pool anything whose identity is not proven: every shard must carry
the provenance echo (`seed`, `topology_seed`, ...), agree on every
configuration field, and tile seeds contiguously with no gap or overlap.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "audit_d7_s_persistence_margin", _HERE / "audit_d7_s_persistence_margin.py")
audit = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault(_SPEC.name, audit)
_SPEC.loader.exec_module(audit)

ARMS = ("constructive", "null", "keep_stable", "set_stable",
        "keep_flex", "set_flex")

# Everything that must be byte-equal across shards for the episodes to belong to
# one instrument on one topology. `seed` and `episodes` are deliberately absent:
# they are what varies between shards, and they are checked by the contiguity
# rule instead.
IDENTITY_FIELDS = (
    "horizon", "energy_stage", "check_every", "n_uavs", "n_users", "n_relay",
    "n_service", "focal_stable_uav", "focal_flex_uav", "topology_seed",
    "initial_energies", "thresholds", "driven_via", "external_return",
    "contract",
)

PROVENANCE_FIELDS = ("seed", "topology_seed")


def pool(shards: list[dict], *, paths: list[str] | None = None) -> dict:
    """Pool shard result dicts. Raises SystemExit on any identity violation."""
    if len(shards) < 2:
        raise SystemExit("pooling needs at least two shards")
    paths = paths if paths is not None else [f"<shard {i}>" for i in range(len(shards))]

    for p, s in zip(paths, shards):
        for f in PROVENANCE_FIELDS:
            if f not in s:
                raise SystemExit(
                    f"{p} lacks provenance field '{f}': it predates the "
                    "provenance echo and its shard identity cannot be proven. "
                    "Re-run it with the current instrument.")

    ref_path, ref = paths[0], shards[0]
    for p, s in zip(paths[1:], shards[1:]):
        for f in IDENTITY_FIELDS:
            if s.get(f) != ref.get(f):
                raise SystemExit(
                    f"identity mismatch on '{f}': {ref_path} has "
                    f"{ref.get(f)!r}, {p} has {s.get(f)!r}. These shards do "
                    "not measure the same instrument on the same topology.")

    order = sorted(range(len(shards)), key=lambda i: int(shards[i]["seed"]))
    shards = [shards[i] for i in order]
    paths = [paths[i] for i in order]

    seed0 = int(shards[0]["seed"])
    expected = seed0
    for p, s in zip(paths, shards):
        if int(s["seed"]) != expected:
            raise SystemExit(
                f"seed tiling broken at {p}: expected seed {expected}, found "
                f"{int(s['seed'])}. Shards must tile one contiguous episode "
                "block with no gap or overlap, or they are not the monolithic "
                "run's episode set.")
        n = int(s["episodes"])
        for a in ARMS:
            got = len(s["per_episode"][a])
            if got != n:
                raise SystemExit(
                    f"{p}: per_episode['{a}'] has {got} entries but the shard "
                    f"declares {n} episodes")
        expected += n

    per_ep = {a: np.concatenate([np.asarray(s["per_episode"][a], dtype=float)
                                 for s in shards]) for a in ARMS}
    episodes = int(sum(int(s["episodes"]) for s in shards))

    mean = {a: float(np.mean(v)) for a, v in per_ep.items()}
    b_h = mean["constructive"] - mean["null"]
    u_stable = mean["set_stable"] - mean["keep_stable"]
    u_flex = mean["set_flex"] - mean["keep_flex"]

    measurable = abs(b_h) >= 1e-9
    norm_stable = u_stable / b_h if measurable else float("nan")
    norm_flex = u_flex / b_h if measurable else float("nan")

    ci_seed = seed0 + 7717
    b_h_ep = per_ep["constructive"] - per_ep["null"]
    intervals = {
        "b_h": audit.bootstrap_mean_ci(b_h_ep, seed=ci_seed),
        "u_star_stable_src": audit.bootstrap_mean_ci(
            per_ep["set_stable"] - per_ep["keep_stable"], seed=ci_seed + 1),
        "u_star_flex_src": audit.bootstrap_mean_ci(
            per_ep["set_flex"] - per_ep["keep_flex"], seed=ci_seed + 2),
        "normalized_stable": audit.bootstrap_ratio_ci(
            per_ep["set_stable"] - per_ep["keep_stable"], b_h_ep,
            seed=ci_seed + 3),
        "normalized_flex": audit.bootstrap_ratio_ci(
            per_ep["set_flex"] - per_ep["keep_flex"], b_h_ep,
            seed=ci_seed + 4),
    }

    if not measurable:
        branch = "SOURCE_NECESSITY_UNRESOLVED"
        reason = "B_H is degenerate; the normalized margin is undefined"
    elif (norm_stable <= audit.MARGIN_STABLE_CEIL
          and norm_flex >= audit.MARGIN_FLEX_FLOOR):
        branch = "PERSISTENCE_NECESSARY_SOURCE"
        reason = ("both margins clear; individual persistence is necessary for "
                  "optimality on this source")
    else:
        branch = "SOURCE_NECESSITY_UNRESOLVED"
        reason = ("at least one margin did not clear its threshold under these "
                  "constructive controls")

    # Episode-weighted recombination of per-shard means; only if every shard
    # carries them (S1 runs do not).
    energy_diagnostics = {}
    if all(s.get("energy_diagnostics") for s in shards):
        w = np.array([int(s["episodes"]) for s in shards], dtype=float)
        for a in ARMS:
            keys = shards[0]["energy_diagnostics"][a].keys()
            energy_diagnostics[a] = {
                k: float(np.average(
                    [s["energy_diagnostics"][a][k] for s in shards], weights=w))
                for k in keys
            }

    # Required-n back-solve for B_H, the quantity whose interval straddling zero
    # forced the episode-budget escalation. Diagnostic only; the gate stays on
    # point estimates.
    sd = float(np.std(b_h_ep, ddof=1)) if episodes > 1 else float("nan")
    required_n = (int(np.ceil((1.96 * sd / b_h) ** 2))
                  if measurable and np.isfinite(sd) and sd > 0 else None)

    result = dict(shards[0])
    result.update({
        "branch": branch,
        "reason": reason,
        "episodes": episodes,
        "seed": seed0,
        "episode_seed_base": seed0 + 100000,
        "probe_qos_saturation_fraction": shards[0][
            "probe_qos_saturation_fraction"],
        "probe_qos_saturation_fraction_per_shard": [
            s["probe_qos_saturation_fraction"] for s in shards],
        "arms_all_equal": len({round(v, 9) for v in mean.values()}) == 1,
        "arm_means": mean,
        "b_h": b_h,
        "u_star_stable_src": u_stable,
        "u_star_flex_src": u_flex,
        "normalized": {"stable": norm_stable, "flex": norm_flex},
        "intervals": intervals,
        "per_episode": {a: [float(x) for x in v] for a, v in per_ep.items()},
        "required_n_b_h_excludes_zero": required_n,
        "pooled_from": [
            {"path": p, "seed": int(s["seed"]), "episodes": int(s["episodes"])}
            for p, s in zip(paths, shards)
        ],
        "pooling_note": (
            "Pooled by concatenating per_episode across seed-contiguous shards "
            "and recomputing every statistic from the concatenation with the "
            "audit module's own functions at ci_seed = seed_0 + 7717 — the "
            "output a monolithic run at seed_0 would have written. Normalized "
            "margins are never averaged across shards."),
    })
    if energy_diagnostics:
        result["energy_diagnostics"] = energy_diagnostics
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shards", nargs="+", required=True,
                        help="paths to the shard d7_s_persistence_margin.json files")
    parser.add_argument("--out", default="",
                        help="directory for the pooled d7_s_persistence_margin.json")
    args = parser.parse_args()

    shards = []
    for p in args.shards:
        with open(p, encoding="utf-8") as h:
            shards.append(json.load(h))

    result = pool(shards, paths=list(args.shards))
    print(f"D7_S_BRANCH={result['branch']}")
    print(f"D7_S_REASON={result['reason']}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "d7_s_persistence_margin.json").open(
                "w", encoding="utf-8") as h:
            json.dump(result, h, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

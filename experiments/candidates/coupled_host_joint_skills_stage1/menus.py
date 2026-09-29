"""Planner menus and anchors for the macro-step contracts (coupled_host_joint_skills_stage1, T-W).

A *menu* is the world's ``P_relay`` layout exactly as ``run_gate.py`` computes it for the sealed
closed-loop reference ``P_relay^on``:

* ``initial`` = the host's reset positions, copied **before** any search (``static_evaluate``
  mutates the env's positions);
* ``P_flat`` = ``search_placement(env, False, budget, default_rng(world))``;
* ``P_relay`` = ``search_placement(env, True, budget, default_rng(world),
  extra_candidates=[P_flat], extra_kind="flat_result_incumbent")`` (fresh rng instance);
* ``m_permutation`` = ``assign_targets(initial, P_relay)`` (UAV ``i`` -> slot ``perm[i]``, the
  min-makespan assignment ``closed_loop_execute`` uses), ``anchors`` = ``P_relay[perm]`` (the
  offset contract's per-UAV centre).

Role tags come from the generator of the candidate the winning descent started from (T-W
default, returned to the DM as an open question): ``subset_*`` candidates carry
``service:c`` / ``relay:c:m`` / ``extra_service:c`` / ``above_bs`` directly; a ``kmeans_plain``
start tags its first ``k`` rows ``service:c`` and the midpoint rows ``relay:c:r`` (``relay_targets``);
a ``flat_result_incumbent`` start inherits the tags of the flat search's own winning start by
the same rule.  ``role_source`` records which rule applied.  A routing-derived role (relay =
interior node of some routing path; service = has connected users; otherwise idle) of the
static layout is stored as a diagnostic only; it never enters an observation.

Cache: ``<menu_dir>/<area>/<world>.json`` (compact, key-sorted JSON; written atomically).
``load_or_build_menu`` returns the menu, its file sha256 and whether it was loaded or computed.
numpy only (no torch at import).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

MENU_SCHEMA = 1
N_SLOTS = 6
ROLE_TYPES = ("service", "relay", "above_bs")
#: Width of one menu row in the observation/state: x/area, y/area, (z - 50)/100 + role one-hot.
MENU_ROW_WIDTH = 3 + len(ROLE_TYPES)
MENU_WIDTH = N_SLOTS * MENU_ROW_WIDTH  # 36
PLANNER_BUDGET = 3000


class MenuError(RuntimeError):
    """A cached or computed menu violates the menu contract."""


def role_type(tag: str) -> str:
    """Map a generator role tag to its role type (extra_service counts as service)."""
    head = str(tag).split(":", 1)[0]
    if head in ("service", "extra_service"):
        return "service"
    if head == "relay":
        return "relay"
    if head == "above_bs":
        return "above_bs"
    raise MenuError(f"unknown role tag {tag!r}")


def _plain_roles(candidate: dict[str, Any], n_uavs: int) -> list[str]:
    k = int(candidate["k"])
    targets = list(candidate["relay_targets"])
    roles = [f"service:{c}" for c in range(k)]
    roles += [f"relay:{int(targets[r])}:{r // k}" for r in range(n_uavs - k)]
    return roles


def _start_roles(result, n_uavs: int, flat=None) -> tuple[list[str], str]:
    candidate = result.candidates[int(result.best_start["candidate_index"])]
    kind = str(candidate["kind"])
    if candidate.get("roles") is not None:
        return list(candidate["roles"]), f"generator:{kind}"
    if kind == "kmeans_plain":
        return _plain_roles(candidate, n_uavs), "generator:kmeans_plain(relay_targets)"
    if kind == "flat_result_incumbent" and flat is not None:
        roles, source = _start_roles(flat, n_uavs)
        return roles, f"flat_result_incumbent<-flat {source}"
    raise MenuError(f"no role rule for a {kind!r} start")


def _routing_roles(env) -> list[str]:
    relays = {int(node) for path in env.routing_paths.values() for kind, node in path[1:-1]
              if kind == "uav"}
    connected = np.asarray(env.connections, dtype=bool).any(axis=1)
    out = []
    for i in range(env.n_uavs):
        if i in relays:
            out.append("relay")
        elif connected[i]:
            out.append("service")
        else:
            out.append("idle")
    return out


def compute_menu(world: int, area_size: int = 5000, budget: int = PLANNER_BUDGET) -> dict[str, Any]:
    """Run the gate's two searches for ``world`` and return the menu record (see module doc)."""
    from .host import make_host, static_evaluate
    from .planner import assign_targets, search_placement

    env = make_host(int(world), area_size=int(area_size))
    initial = np.array(env.uav_positions, dtype=float, copy=True)
    flat = search_placement(env, False, int(budget), np.random.default_rng(int(world)))
    relay = search_placement(env, True, int(budget), np.random.default_rng(int(world)),
                             extra_candidates=[flat.positions_xyz],
                             extra_kind="flat_result_incumbent")
    positions = np.asarray(relay.positions_xyz, dtype=float)
    roles, source = _start_roles(relay, env.n_uavs, flat)
    perm = assign_targets(initial, positions)
    static_evaluate(env, positions, allow_a2a=True)
    routing = _routing_roles(env)
    menu = {
        "schema": MENU_SCHEMA,
        "world": int(world),
        "area_size": int(area_size),
        "budget": int(budget),
        "planner_rng": "numpy.random.default_rng(world), fresh instance per search (run_gate.py rule)",
        "positions_xyz": positions.tolist(),
        "roles": roles,
        "role_types": [role_type(tag) for tag in roles],
        "role_source": source,
        "routing_roles_diagnostic": routing,
        "initial_positions_xyz": initial.tolist(),
        "m_permutation": [int(p) for p in perm],
        "anchors_xyz": positions[np.asarray(perm, dtype=int)].tolist(),
        "static": {"P_relay_contract_reward": float(relay.contract_reward),
                   "P_relay_coverage_backhauled": float(relay.coverage_backhauled),
                   "P_flat_contract_reward": float(flat.contract_reward),
                   "P_flat_coverage_backhauled": float(flat.coverage_backhauled),
                   "evaluations": [int(flat.evaluations), int(relay.evaluations)],
                   "best_start_kind": str(relay.best_start["kind"])},
    }
    check_menu(menu, int(world), int(area_size))
    return menu


def check_menu(menu: dict[str, Any], world: int, area_size: int) -> None:
    if int(menu.get("schema", -1)) != MENU_SCHEMA:
        raise MenuError("menu schema mismatch")
    if int(menu["world"]) != int(world) or int(menu["area_size"]) != int(area_size):
        raise MenuError(f"menu is for world {menu['world']} / area {menu['area_size']}, "
                        f"not {world} / {area_size}")
    positions = np.asarray(menu["positions_xyz"], dtype=float)
    if positions.shape != (N_SLOTS, 3) or not np.all(np.isfinite(positions)):
        raise MenuError("menu positions must be a finite 6 x 3 array")
    if (np.any(positions[:, :2] < 0) or np.any(positions[:, :2] > area_size)
            or np.any(positions[:, 2] < 50.0) or np.any(positions[:, 2] > 150.0)):
        raise MenuError("menu position outside the arena box")
    if len(menu["roles"]) != N_SLOTS or [role_type(t) for t in menu["roles"]] != list(menu["role_types"]):
        raise MenuError("menu roles inconsistent")
    perm = [int(p) for p in menu["m_permutation"]]
    if sorted(perm) != list(range(N_SLOTS)):
        raise MenuError("m_permutation is not a permutation")
    if not np.array_equal(np.asarray(menu["anchors_xyz"], dtype=float), positions[perm]):
        raise MenuError("anchors differ from positions[m_permutation]")


def encode_json(menu: dict[str, Any]) -> bytes:
    return (json.dumps(menu, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def menu_path(menu_dir: Path | str, world: int, area_size: int) -> Path:
    return Path(menu_dir) / str(int(area_size)) / f"{int(world)}.json"


def load_or_build_menu(world: int, area_size: int, menu_dir: Path | str,
                       budget: int = PLANNER_BUDGET) -> tuple[dict[str, Any], str, str]:
    """Return ``(menu, sha256 of the cache file bytes, "loaded" | "computed")``."""
    path = menu_path(menu_dir, world, area_size)
    if path.exists():
        data = path.read_bytes()
        menu = json.loads(data)
        check_menu(menu, world, area_size)
        if int(menu["budget"]) != int(budget):
            raise MenuError(f"cached menu {path} has budget {menu['budget']}, expected {budget}")
        return menu, hashlib.sha256(data).hexdigest(), "loaded"
    menu = compute_menu(world, area_size, budget)
    data = encode_json(menu)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(f".json.{os.getpid()}.partial")
    partial.write_bytes(data)
    os.replace(partial, path)
    # Re-read through the loader rule so the in-memory menu equals what the cache now holds.
    return json.loads(data), hashlib.sha256(data).hexdigest(), "computed"


def menu_features(menu: dict[str, Any], area_size: float, height_low: float = 50.0,
                  height_span: float = 100.0) -> np.ndarray:
    """Flat float32 menu block (6 rows x [x/area, y/area, (z - 50)/100, one-hot role type])."""
    positions = np.asarray(menu["positions_xyz"], dtype=np.float64)
    rows = np.zeros((N_SLOTS, MENU_ROW_WIDTH), dtype=np.float32)
    rows[:, 0] = positions[:, 0] / float(area_size)
    rows[:, 1] = positions[:, 1] / float(area_size)
    rows[:, 2] = (positions[:, 2] - float(height_low)) / float(height_span)
    for slot, kind in enumerate(menu["role_types"]):
        rows[slot, 3 + ROLE_TYPES.index(kind)] = 1.0
    return rows.reshape(-1)


class MenuProvider:
    """Cache-backed menus by world; records (sha256, source) per world for the run summary."""

    def __init__(self, menu_dir: Path | str, area_size: int, budget: int = PLANNER_BUDGET):
        self.menu_dir = Path(menu_dir)
        self.area_size = int(area_size)
        self.budget = int(budget)
        self._menus: dict[int, dict[str, Any]] = {}
        self.records: dict[int, dict[str, str]] = {}
        #: Wall seconds spent loading or computing menus (the runner excludes it from env time).
        self.seconds = 0.0

    def __call__(self, world: int) -> dict[str, Any]:
        world = int(world)
        if world not in self._menus:
            started = time.perf_counter()
            menu, digest, source = load_or_build_menu(world, self.area_size, self.menu_dir, self.budget)
            self.seconds += time.perf_counter() - started
            self._menus[world] = menu
            self.records[world] = {"sha256": digest, "source": source,
                                   "path": str(menu_path(self.menu_dir, world, self.area_size))}
        return self._menus[world]

    def summary(self) -> dict[str, Any]:
        return {"menu_dir": str(self.menu_dir), "area_size": self.area_size, "budget": self.budget,
                "worlds": {str(w): r for w, r in sorted(self.records.items())},
                "computed": sum(r["source"] == "computed" for r in self.records.values()),
                "loaded": sum(r["source"] == "loaded" for r in self.records.values()),
                "seconds": self.seconds}


def precompute_menus(worlds, area_size: int, menu_dir: Path | str,
                     budget: int = PLANNER_BUDGET) -> dict[str, Any]:
    """Fill the cache for ``worlds`` (e.g. the 736 macro training worlds); returns the summary."""
    provider = MenuProvider(menu_dir, area_size, budget)
    for world in worlds:
        provider(int(world))
    return provider.summary()

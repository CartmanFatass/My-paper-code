"""3D topology capture and visualization for standalone HA-CTSE eval runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib import animation
except Exception:  # pragma: no cover - optional plotting dependency.
    plt = None
    animation = None


TOPOLOGY_KEYS = (
    "uav_positions",
    "user_positions",
    "ground_bs_positions",
    "charging_station_positions",
    "connections",
    "uav_connections",
    "uav_bs_connections",
    "routing_paths",
    "uav_battery_ratios",
    "uav_charging",
    "uav_failed",
    "charging_station_occupancy",
    "charging_station_queue_lengths",
    "area_size",
    "current_step",
    "max_steps",
)


def _sanitize(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _sanitize(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    return value


def _array3(value: Any) -> np.ndarray:
    arr = np.asarray(value if value is not None else [], dtype=np.float32)
    if arr.size == 0:
        return np.zeros((0, 3), dtype=np.float32)
    arr = arr.reshape((-1, arr.shape[-1]))
    if arr.shape[1] >= 3:
        return arr[:, :3]
    if arr.shape[1] == 2:
        return np.concatenate([arr, np.zeros((arr.shape[0], 1), dtype=arr.dtype)], axis=1)
    return np.pad(arr, ((0, 0), (0, 3 - arr.shape[1])), mode="constant")


def _field_from_info(info: dict[str, Any] | None, key: str) -> Any:
    if not isinstance(info, dict):
        return None
    if key in info:
        return info[key]
    for source_key in ("state_info", "reward_info", "reward_components"):
        source = info.get(source_key)
        if isinstance(source, dict):
            if key in source:
                return source[key]
            nested = source.get("reward_info")
            if isinstance(nested, dict) and key in nested:
                return nested[key]
    return None


def capture_topology_frame(
    env: Any,
    info: dict[str, Any] | None,
    agent: Any,
    episode: int,
    step: int,
    reward: float,
    metrics: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Capture one eval frame without mutating the environment or agent."""

    state_info = {}
    if hasattr(env, "get_current_state"):
        try:
            state_info = env.get_current_state() or {}
        except Exception:
            state_info = {}

    frame: dict[str, Any] = {
        "episode": int(episode),
        "step": int(step),
        "reward": float(reward),
        "metrics": {key: float(value) for key, value in (metrics or {}).items()},
    }
    for key in TOPOLOGY_KEYS:
        value = state_info.get(key)
        if value is None:
            value = _field_from_info(info, key)
        if value is not None:
            frame[key] = _sanitize(value)

    if agent is not None:
        try:
            frame["active_skills"] = _sanitize(agent.active_skills[0].copy())
            frame["duration_remaining"] = _sanitize(agent.duration_remaining[0].copy())
            frame["skill_age"] = _sanitize(agent.skill_age[0].copy())
        except Exception:
            pass
    return frame


def _node_position(node: Any, uavs: np.ndarray, base_stations: np.ndarray) -> np.ndarray | None:
    if not isinstance(node, (list, tuple)) or len(node) < 2:
        return None
    node_type = str(node[0])
    try:
        idx = int(node[1])
    except (TypeError, ValueError):
        return None
    if node_type == "uav" and 0 <= idx < len(uavs):
        return uavs[idx]
    if node_type in ("ground_bs", "bs", "base_station") and 0 <= idx < len(base_stations):
        return base_stations[idx]
    return None


def _routing_path(record: Any) -> list[Any]:
    if isinstance(record, dict):
        path = record.get("path")
        return path if isinstance(path, list) else []
    if isinstance(record, list):
        if record and isinstance(record[0], list) and record[0] and isinstance(record[0][0], (list, tuple)):
            return record[0]
        if record and isinstance(record[0], (list, tuple)) and len(record[0]) >= 2:
            return record
    return []


def _plot_topology(ax: Any, frames: list[dict[str, Any]]) -> None:
    current = frames[-1]
    uavs = _array3(current.get("uav_positions"))
    users = _array3(current.get("user_positions"))
    base_stations = _array3(current.get("ground_bs_positions"))
    chargers = _array3(current.get("charging_station_positions"))
    connections = np.asarray(current.get("connections", []), dtype=bool)
    uav_connections = np.asarray(current.get("uav_connections", []), dtype=bool)
    uav_bs_connections = np.asarray(current.get("uav_bs_connections", []), dtype=bool)
    area_size = float(current.get("area_size") or 0.0)
    if area_size <= 0.0:
        xy_points = [arr[:, :2] for arr in (uavs, users, base_stations, chargers) if len(arr)]
        area_size = float(np.max(np.concatenate(xy_points))) if xy_points else 1.0
        area_size = max(area_size, 1.0)

    ax.set_xlim(0, area_size)
    ax.set_ylim(0, area_size)
    z_max = max(250.0, float(np.max(uavs[:, 2])) * 1.2 if len(uavs) else 250.0)
    ax.set_zlim(0, z_max)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.view_init(elev=28, azim=42)

    title_bits = [
        f"episode={current.get('episode', 0)}",
        f"step={current.get('step', 0)}",
        f"reward={float(current.get('reward', 0.0)):.2f}",
    ]
    metrics = current.get("metrics") or {}
    if isinstance(metrics, dict):
        for key in ("coverage", "qos", "throughput"):
            if key in metrics:
                title_bits.append(f"{key}={float(metrics[key]):.3f}")
    ax.set_title("HA-CTSE 3D topology  " + "  ".join(title_bits), fontsize=10)

    if len(users):
        connected_users = set()
        if connections.ndim == 2:
            for user_idx in np.where(np.any(connections, axis=0))[0]:
                connected_users.add(int(user_idx))
        user_colors = ["#1f77b4" if idx in connected_users else "#a6cee3" for idx in range(len(users))]
        user_sizes = [18 if idx in connected_users else 8 for idx in range(len(users))]
        ax.scatter(users[:, 0], users[:, 1], users[:, 2], c=user_colors, s=user_sizes, marker="o", alpha=0.65, label="users")

    if len(base_stations):
        ax.scatter(
            base_stations[:, 0],
            base_stations[:, 1],
            base_stations[:, 2],
            c="black",
            s=120,
            marker="s",
            edgecolors="white",
            linewidth=0.8,
            label="base stations",
        )

    if len(chargers):
        ax.scatter(
            chargers[:, 0],
            chargers[:, 1],
            chargers[:, 2],
            c="#2ca02c",
            s=90,
            marker="D",
            edgecolors="white",
            linewidth=0.8,
            label="charging stations",
        )

    colors = plt.cm.tab10(np.linspace(0, 1, max(len(uavs), 1)))
    for uav_idx, color in enumerate(colors[: len(uavs)]):
        history = []
        for frame in frames:
            frame_uavs = _array3(frame.get("uav_positions"))
            if uav_idx < len(frame_uavs):
                history.append(frame_uavs[uav_idx])
        if len(history) >= 2:
            hist = np.asarray(history, dtype=np.float32)
            ax.plot(hist[:, 0], hist[:, 1], hist[:, 2], color=color, alpha=0.45, linewidth=1.1)

    skills = current.get("active_skills") or []
    durations = current.get("duration_remaining") or []
    batteries = current.get("uav_battery_ratios") or []
    charging = current.get("uav_charging") or []
    failed = current.get("uav_failed") or []
    status_lines = []
    for uav_idx, uav_pos in enumerate(uavs):
        has_users = bool(connections.ndim == 2 and uav_idx < connections.shape[0] and np.any(connections[uav_idx]))
        marker_color = colors[uav_idx]
        if uav_idx < len(failed) and bool(failed[uav_idx]):
            marker_color = "#7f7f7f"
        elif uav_idx < len(charging) and bool(charging[uav_idx]):
            marker_color = "#2ca02c"
        elif has_users:
            marker_color = "#d62728"
        ax.scatter(
            [uav_pos[0]],
            [uav_pos[1]],
            [uav_pos[2]],
            c=[marker_color],
            s=95,
            marker="^",
            edgecolors="white",
            linewidth=0.8,
        )
        ax.text(uav_pos[0], uav_pos[1], uav_pos[2] + 18.0, f"U{uav_idx}", fontsize=7, ha="center")
        suffix = f"U{uav_idx}:"
        if uav_idx < len(skills):
            suffix += f" z={int(skills[uav_idx])}"
        if uav_idx < len(durations):
            suffix += f" d={int(durations[uav_idx])}"
        if uav_idx < len(batteries):
            suffix += f" b={float(batteries[uav_idx]):.2f}"
        if uav_idx < len(charging) and bool(charging[uav_idx]):
            suffix += " charging"
        if uav_idx < len(failed) and bool(failed[uav_idx]):
            suffix += " failed"
        status_lines.append(suffix)

    if connections.ndim == 2 and len(uavs) and len(users):
        for uav_idx in range(min(connections.shape[0], len(uavs))):
            for user_idx in np.where(connections[uav_idx])[0]:
                if user_idx >= len(users):
                    continue
                ax.plot(
                    [uavs[uav_idx, 0], users[user_idx, 0]],
                    [uavs[uav_idx, 1], users[user_idx, 1]],
                    [uavs[uav_idx, 2], users[user_idx, 2]],
                    color="#2ca02c",
                    alpha=0.18,
                    linewidth=0.6,
                )

    if uav_connections.ndim == 2 and len(uavs):
        for src_idx in range(min(uav_connections.shape[0], len(uavs))):
            for dst_idx in np.where(uav_connections[src_idx])[0]:
                if dst_idx <= src_idx or dst_idx >= len(uavs):
                    continue
                ax.plot(
                    [uavs[src_idx, 0], uavs[dst_idx, 0]],
                    [uavs[src_idx, 1], uavs[dst_idx, 1]],
                    [uavs[src_idx, 2], uavs[dst_idx, 2]],
                    color="#999999",
                    alpha=0.22,
                    linewidth=0.7,
                    linestyle=":",
                )

    if uav_bs_connections.ndim == 2 and len(uavs) and len(base_stations):
        for uav_idx in range(min(uav_bs_connections.shape[0], len(uavs))):
            for bs_idx in np.where(uav_bs_connections[uav_idx])[0]:
                if bs_idx >= len(base_stations):
                    continue
                ax.plot(
                    [uavs[uav_idx, 0], base_stations[bs_idx, 0]],
                    [uavs[uav_idx, 1], base_stations[bs_idx, 1]],
                    [uavs[uav_idx, 2], base_stations[bs_idx, 2]],
                    color="#666666",
                    alpha=0.28,
                    linewidth=0.8,
                    linestyle=":",
                )

    routing = current.get("routing_paths") or {}
    if isinstance(routing, dict):
        for record in routing.values():
            path = _routing_path(record)
            for left, right in zip(path, path[1:]):
                left_pos = _node_position(left, uavs, base_stations)
                right_pos = _node_position(right, uavs, base_stations)
                if left_pos is None or right_pos is None:
                    continue
                ax.plot(
                    [left_pos[0], right_pos[0]],
                    [left_pos[1], right_pos[1]],
                    [left_pos[2], right_pos[2]],
                    color="#ff7f0e",
                    alpha=0.75,
                    linewidth=1.6,
                )

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        unique = dict(zip(labels, handles))
        ax.legend(unique.values(), unique.keys(), loc="upper left", fontsize=7)
    if status_lines:
        ax.text2D(
            0.72,
            0.97,
            "\n".join(status_lines),
            transform=ax.transAxes,
            fontsize=7,
            va="top",
            ha="left",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.78, "edgecolor": "#cccccc"},
        )


def save_topology_artifacts(
    frames: list[dict[str, Any]],
    log_dir: str | Path,
    total_steps: int,
    episode: int,
    checkpoint_name: str = "",
) -> dict[str, str]:
    """Save topology JSON plus static and animated 3D artifacts."""

    output: dict[str, str] = {}
    if not frames:
        return output
    topology_dir = Path(log_dir) / "topology"
    topology_dir.mkdir(parents=True, exist_ok=True)
    stem_bits = [f"steps_{int(total_steps):09d}", f"ep_{int(episode):02d}"]
    if checkpoint_name:
        safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in checkpoint_name)
        stem_bits.append(safe_name)
    stem = "_".join(stem_bits)

    json_path = topology_dir / f"{stem}.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(_sanitize(frames), handle, ensure_ascii=False, indent=2)
    output["json"] = str(json_path)

    if plt is None:
        return output

    final_png = topology_dir / f"{stem}_final.png"
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")
    _plot_topology(ax, frames)
    fig.tight_layout()
    fig.savefig(final_png, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    output["final_png"] = str(final_png)

    if animation is None or len(frames) < 2:
        return output
    gif_path = topology_dir / f"{stem}.gif"
    try:
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection="3d")

        def draw(frame_idx: int) -> list[Any]:
            ax.cla()
            _plot_topology(ax, frames[: frame_idx + 1])
            return []

        ani = animation.FuncAnimation(fig, draw, frames=len(frames), interval=220, blit=False)
        writer = animation.PillowWriter(fps=5)
        ani.save(gif_path, writer=writer, dpi=120)
        plt.close(fig)
        output["gif"] = str(gif_path)
    except Exception:
        keyframe_dir = topology_dir / f"{stem}_frames"
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        for idx, frame in enumerate(frames):
            fig = plt.figure(figsize=(12, 9))
            ax = fig.add_subplot(111, projection="3d")
            _plot_topology(ax, frames[: idx + 1])
            fig.tight_layout()
            frame_path = keyframe_dir / f"frame_{idx:04d}.png"
            fig.savefig(frame_path, dpi=140, bbox_inches="tight", facecolor="white")
            plt.close(fig)
        output["frames_dir"] = str(keyframe_dir)
    return output

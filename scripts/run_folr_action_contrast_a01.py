"""Run the zero-fit frozen-action contrast diagnostic on both A01 final panels."""

import time

START_WALL = time.monotonic()
START_CPU = time.process_time()

import argparse
import json
import math
from numbers import Real
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hmasd_admission import require_admission


def _resource_snapshot(summary):
    summary["runner_wall_seconds"] = time.monotonic() - START_WALL
    summary["aggregate_cpu_seconds"] = time.process_time() - START_CPU
    summary["aggregate_cpu_scope"] = "single diagnostic process, user plus system CPU"
    try:
        import resource

        summary["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        summary["peak_rss_kib"] = None
        summary["resources_unmeasured"] = ["peak_rss_kib on local Windows check"]


def _write_summary(out, summary):
    encoded = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    path = out / "summary.json"
    path.write_text(encoded)
    if json.loads(path.read_text()) != summary:
        raise IOError("summary publication/readback mismatch")


def _publish(out, summary):
    _resource_snapshot(summary)
    _write_summary(out, summary)


def _sanitize_failure(value, path, invalid_paths):
    if isinstance(value, dict):
        return {
            key: _sanitize_failure(item, f"{path}.{key}", invalid_paths)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _sanitize_failure(item, f"{path}[{index}]", invalid_paths)
            for index, item in enumerate(value)
        ]
    if isinstance(value, Real) and not isinstance(value, (bool, int)):
        number = float(value)
        if not math.isfinite(number):
            invalid_paths.append(path)
            return None
        return number
    return value


def _publish_failure(out, summary):
    _resource_snapshot(summary)
    invalid_paths = []
    safe = _sanitize_failure(summary, "$", invalid_paths)
    safe["invalid_nonfinite_paths"] = invalid_paths
    _write_summary(out, safe)


def _source_hashes(file_sha256):
    root = Path(__file__).resolve().parents[1]
    paths = (
        Path(__file__).resolve(),
        root / "experiments/candidates/vap_folr_core/action_contrast_a01/diagnostic.py",
    )
    return {
        str(path.relative_to(root)): file_sha256(path)
        for path in paths
    }


def _input_paths(input_root, bindings):
    return {
        arm: {
            "checkpoint": input_root / binding["tag"] / "final.pt",
            "panel": input_root / binding["tag"] / "final-panel.npz",
            "summary": input_root / binding["tag"] / "summary.json",
        }
        for arm, binding in bindings.items()
    }


def _hash_inputs(paths, file_sha256):
    return {
        arm: {
            name + "_sha256": file_sha256(path)
            for name, path in arm_paths.items()
        }
        for arm, arm_paths in paths.items()
    }


def _validate_summary(source_summary, arm, binding):
    if (
        source_summary.get("status"),
        source_summary.get("arm"),
        source_summary.get("evaluation_seed"),
        source_summary.get("final_episodes"),
        source_summary.get("final_transitions"),
    ) != ("complete", arm, 1783101, 128, 2560):
        raise ValueError(f"{arm} source summary has foreign or incomplete exposure")
    if source_summary.get("final_checkpoint_sha256") != binding["checkpoint_sha256"]:
        raise ValueError(f"{arm} source summary checkpoint binding mismatch")
    if source_summary.get("final_panel", {}).get("artifact_sha256") != binding["panel_sha256"]:
        raise ValueError(f"{arm} source summary panel binding mismatch")
    returns = source_summary.get("final_returns")
    if not isinstance(returns, list) or len(returns) != 128:
        raise ValueError(f"{arm} source summary has no complete final returns")
    return returns


def _activity():
    return {
        "actor_forward_calls": 0,
        "full_forward_calls": 0,
        "reset_forward_calls": 0,
        "factual_transition_calls": 0,
        "counterfactual_transition_calls": 0,
        "observation_boundaries_verified": 0,
        "active_action_checks": 0,
        "factual_reward_checks": 0,
        "native_return_checks": 0,
        "replayed_episodes": 0,
        "selected_rows": 0,
        "rows_written": 0,
    }


def _refresh_total_activity(summary):
    total = _activity()
    for panel in summary["panels"].values():
        for key, value in panel.get("activity", {}).items():
            total[key] += int(value)
    summary["activity"] = total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seed != 1783101:
        parser.error("--seed must match the selected frozen final-panel seed")

    admission = require_admission(__file__, direction="vap_folr_core")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    from experiments.candidates.vap_folr_core.action_contrast_a01.diagnostic import (
        INPUTS,
        PANEL_SEED,
        actor_state_sha256,
        file_sha256,
        replay_panel,
        summarize_rows,
    )

    args.out.mkdir(parents=True, exist_ok=True)
    summary = {
        "object": "FOLR_ACTION_CONTRAST_A01_1783101",
        "status": "incomplete",
        "launch_sha": args.launch_sha,
        "seed": args.seed,
        "fits": 0,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "predictor_forward_calls": 0,
        "mixer_forward_calls": 0,
        "activity": _activity(),
        "panels": {},
        "input_bindings": INPUTS,
        "source_hashes": _source_hashes(file_sha256),
        "scope": (
            "Frozen factual one-step action consequence on prespecified geometry rows. "
            "Zero incoming hidden state is an out-of-distribution sensitivity, not a "
            "memoryless baseline or a representation-capacity test."
        ),
    }
    _publish(args.out, summary)
    input_paths = None
    try:
        import numpy as np
        import torch

        from experiments.candidates.vap_folr_core.entity_history_b01.environment import (
            EntityHistoryEnv,
        )
        from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor

        input_root = args.input_root.resolve(strict=True)
        summary["input_root"] = str(input_root)
        input_paths = _input_paths(input_root, INPUTS)
        before_hashes = _hash_inputs(input_paths, file_sha256)
        summary["input_hashes_before"] = before_hashes
        for arm, binding in INPUTS.items():
            if before_hashes[arm]["checkpoint_sha256"] != binding["checkpoint_sha256"]:
                raise ValueError(f"{arm} checkpoint SHA256 does not match the frozen binding")
            if before_hashes[arm]["panel_sha256"] != binding["panel_sha256"]:
                raise ValueError(f"{arm} final panel SHA256 does not match the frozen binding")

        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        row_path = args.out / "selected-rows.jsonl"
        panel_rows = {arm: [] for arm in INPUTS}
        with row_path.open("w", encoding="utf-8", newline="\n") as row_stream:
            for arm, binding in INPUTS.items():
                paths = input_paths[arm]
                source_summary = json.loads(paths["summary"].read_text())
                expected_returns = _validate_summary(source_summary, arm, binding)
                with np.load(paths["panel"], allow_pickle=False) as archive:
                    panel = {key: archive[key].copy() for key in archive.files}
                checkpoint = torch.load(paths["checkpoint"], map_location="cpu", weights_only=True)
                if checkpoint.get("arm") != arm or checkpoint.get("native_actor_arm") != "GENERIC_RETAIN":
                    raise ValueError(f"{arm} checkpoint has foreign actor identity")
                actor = Actor("GENERIC_RETAIN")
                actor.load_state_dict(checkpoint["actor"], strict=True)
                actor.eval()
                if any(
                    value.device.type != "cpu" or value.dtype != torch.float32
                    for value in actor.state_dict().values()
                ):
                    raise ValueError(f"{arm} actor is not CPU FP32")
                state_before = actor_state_sha256(actor)
                activity = _activity()
                panel_record = {
                    "activity": activity,
                    "actor_state_sha256_before": state_before,
                    "actor_state_sha256_after": None,
                    "reading": None,
                }
                summary["panels"][arm] = panel_record

                def emit_row(row, *, arm=arm):
                    encoded = json.dumps(row, allow_nan=False)
                    row_stream.write(encoded + "\n")
                    panel_rows[arm].append(row)

                np.random.seed(PANEL_SEED)
                env = EntityHistoryEnv(difficulty="easy", vision=1, seed=PANEL_SEED)
                replay_panel(
                    env,
                    actor,
                    panel,
                    expected_returns,
                    arm,
                    emit_row,
                    activity,
                )
                state_after = actor_state_sha256(actor)
                if state_after != state_before:
                    raise RuntimeError(f"{arm} frozen actor parameters changed during diagnostic")
                if activity["selected_rows"] != binding["selected_rows"]:
                    raise RuntimeError(f"{arm} selected geometry-row count drifted")
                if activity["active_action_checks"] != binding["active_action_checks"]:
                    raise RuntimeError(f"{arm} active action-check count drifted")
                expected_counterfactual = binding["selected_rows"] * 4
                if (
                    activity["actor_forward_calls"] != 128 * 21 * 2
                    or activity["factual_transition_calls"] != 128 * 20
                    or activity["counterfactual_transition_calls"] != expected_counterfactual
                    or activity["rows_written"] != binding["selected_rows"]
                ):
                    raise RuntimeError(f"{arm} diagnostic activity count drifted")
                panel_record["actor_state_sha256_after"] = state_after
                panel_record["reading"] = summarize_rows(panel_rows[arm])
                _refresh_total_activity(summary)
                row_stream.flush()
                _publish(args.out, summary)

        summary["row_artifact"] = {
            "path": str(row_path),
            "sha256": file_sha256(row_path),
            "rows": sum(len(rows) for rows in panel_rows.values()),
        }
        after_hashes = _hash_inputs(input_paths, file_sha256)
        summary["input_hashes_after"] = after_hashes
        if after_hashes != before_hashes:
            raise RuntimeError("frozen diagnostic inputs changed during execution")
        if (
            summary["activity"]["actor_forward_calls"] != 10752
            or summary["activity"]["factual_transition_calls"] != 5120
            or summary["activity"]["counterfactual_transition_calls"] != 3592
            or summary["activity"]["rows_written"] != 898
        ):
            raise RuntimeError("two-panel diagnostic total count drifted")
        summary["native_transition_calls"] = (
            summary["activity"]["factual_transition_calls"]
            + summary["activity"]["counterfactual_transition_calls"]
        )
        if summary["native_transition_calls"] != 8712:
            raise RuntimeError("two-panel native transition total drifted")
        summary["torch_version"] = torch.__version__
        summary["numpy_version"] = np.__version__
        summary["torch_threads"] = [torch.get_num_threads(), torch.get_num_interop_threads()]
        summary["status"] = "complete"
        _publish(args.out, summary)
    except BaseException as exc:
        _refresh_total_activity(summary)
        partial_row_path = locals().get("row_path")
        if partial_row_path is not None and partial_row_path.exists():
            summary["row_artifact"] = {
                "path": str(partial_row_path),
                "sha256": file_sha256(partial_row_path),
                "rows": summary["activity"]["rows_written"],
            }
        if input_paths is not None:
            try:
                summary["input_hashes_after"] = _hash_inputs(input_paths, file_sha256)
            except BaseException as hash_exc:
                summary["input_hashes_after_error"] = type(hash_exc).__name__ + ": " + str(hash_exc)
        summary["status"] = "incomplete"
        summary["error"] = type(exc).__name__ + ": " + str(exc)
        summary["failure_count_scope"] = "Only successfully issued calls and written rows are counted."
        _publish_failure(args.out, summary)
        raise
    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_rows": summary["activity"]["rows_written"],
                "native_transition_calls": summary["native_transition_calls"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()

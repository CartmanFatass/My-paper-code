"""Run the read-only supplied-executor opportunity authority/use audit."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.dynamic_roster_opportunity_audit import (  # noqa: E402
    FORMAL_EVAL_EPISODES,
    run_read_only_opportunity_authority_and_use_audit,
)


DEFAULT_ROUND = (
    PROJECT_ROOT
    / "docs"
    / "external-review"
    / "rounds"
    / "20260720_supplied_executor_opportunity_contract"
)
DEFAULT_RUN = (
    PROJECT_ROOT / "logs" / "clean_supplied_executor_high_path_g0_20260720_054300"
)
DEFAULT_SOURCE_RESULT = DEFAULT_ROUND / "03_SUPPLIED_EXECUTOR_RESULT.json"
DEFAULT_UPDATE_ZERO = DEFAULT_RUN / "checkpoints" / "update_000_high.pt"
DEFAULT_LATEST = DEFAULT_RUN / "checkpoints" / "latest_high_only.pt"


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_text(
        path,
        json.dumps(dict(value), ensure_ascii=False, indent=2, allow_nan=False),
    )


def _write_status(path: Path, **fields: Any) -> None:
    payload = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _atomic_text(path, "".join(f"{key}={value}\n" for key, value in payload.items()))


def run_opportunity_authority_audit(
    *,
    output_root: Path,
    source_result: Path = DEFAULT_SOURCE_RESULT,
    update_zero: Path = DEFAULT_UPDATE_ZERO,
    latest: Path = DEFAULT_LATEST,
    device: str = "cuda",
    batch_size: int = 16,
    smoke: bool = False,
    smoke_episodes: int = 2,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    result_path = (
        output_root
        / "result"
        / "clean_supplied_executor_opportunity_authority_audit.json"
    )
    status_path = output_root / "runner_status.txt"
    started = time.perf_counter()
    episode_ids = (
        tuple(range(int(smoke_episodes)))
        if smoke
        else tuple(range(FORMAL_EVAL_EPISODES))
    )
    if smoke and (int(smoke_episodes) <= 0 or int(smoke_episodes) > 8):
        raise ValueError("smoke audit episode count must lie in 1..8")
    if not smoke and (
        source_result.resolve() != DEFAULT_SOURCE_RESULT.resolve()
        or update_zero.resolve() != DEFAULT_UPDATE_ZERO.resolve()
        or latest.resolve() != DEFAULT_LATEST.resolve()
    ):
        raise ValueError("formal audit requires the registered result/checkpoint paths")
    _write_status(
        status_path,
        state="running",
        phase="focused_smoke" if smoke else "read_only_authority_and_use",
        formal_evidence=not smoke,
        episode_count=len(episode_ids),
        optimizer_steps=0,
        result=result_path,
    )
    result = run_read_only_opportunity_authority_and_use_audit(
        source_result_path=source_result,
        update_zero_path=update_zero,
        latest_path=latest,
        device=device,
        episode_ids=episode_ids,
        batch_size=int(batch_size),
        solve_hindsight=not smoke,
        formal=not smoke,
    )
    result["source_result_path"] = str(source_result.resolve())
    result["result_path"] = str(result_path)
    result["authoritative_status_source"] = str(status_path)
    result["wall_seconds"] = time.perf_counter() - started
    _write_json(result_path, result)
    _write_status(
        status_path,
        state="complete",
        phase="terminal",
        status=result["status"],
        formal_evidence=result["formal_evidence"],
        implementation_valid=result["implementation_valid"],
        episode_count=len(episode_ids),
        high_optimizer_steps=0,
        low_optimizer_steps=0,
        result=result_path,
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-result", type=Path, default=DEFAULT_SOURCE_RESULT)
    parser.add_argument("--update-zero", type=Path, default=DEFAULT_UPDATE_ZERO)
    parser.add_argument("--latest", type=Path, default=DEFAULT_LATEST)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--smoke-episodes", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status_path = args.output_root.resolve() / "runner_status.txt"
    error_path = args.output_root.resolve() / "runner_stderr.log"
    try:
        result = run_opportunity_authority_audit(
            output_root=args.output_root,
            source_result=args.source_result,
            update_zero=args.update_zero,
            latest=args.latest,
            device=args.device,
            batch_size=args.batch_size,
            smoke=args.smoke,
            smoke_episodes=args.smoke_episodes,
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "formal_evidence": result["formal_evidence"],
                    "implementation_valid": result["implementation_valid"],
                    "result": result["result_path"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        _atomic_text(error_path, traceback.format_exc())
        _write_status(
            status_path,
            state="failed",
            phase="runner",
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


if __name__ == "__main__":
    sys.exit(main())

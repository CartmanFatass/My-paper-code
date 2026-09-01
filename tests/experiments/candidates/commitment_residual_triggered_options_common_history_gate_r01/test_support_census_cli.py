from __future__ import annotations

from pathlib import Path

import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import (
    run as run_module,
    support_census_worker as worker_module,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    SUPPORT_CENSUS_TOMBSTONE_REASON,
    SupportCensusConsumedError,
)


class _Unreadable:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"tombstoned entry inspected argument attribute {name}")

    def __iter__(self):
        raise AssertionError("tombstoned entry iterated an argument")

    def __len__(self) -> int:
        raise AssertionError("tombstoned entry measured an argument")

    def __getitem__(self, key: object) -> object:
        raise AssertionError(f"tombstoned entry indexed an argument at {key!r}")


def test_public_cli_rejects_support_token_before_parser_or_path_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        run_module, "build_parser",
        lambda: pytest.fail("support CLI reached parser construction"),
    )
    monkeypatch.setattr(
        run_module, "_launch_support_census_worker",
        lambda **_kwargs: pytest.fail("support CLI reached launcher"),
    )
    before = list(tmp_path.iterdir())
    with pytest.raises(SupportCensusConsumedError) as captured:
        run_module.main([
            "support-census",
            "--output-root", str(tmp_path / "direction"),
            "--result", str(tmp_path / "result.json"),
            "--resource-receipt", str(tmp_path / "memory.json"),
        ])
    assert str(captured.value) == SUPPORT_CENSUS_TOMBSTONE_REASON
    assert list(tmp_path.iterdir()) == before


def test_parser_exposes_only_a_terminal_token_without_fresh_parameters() -> None:
    parser = run_module.build_parser()
    assert parser.parse_args(["support-census"]).action == "support-census"
    with pytest.raises(SystemExit):
        parser.parse_args(["support-census", "--output-root", "forbidden"])


def test_launcher_worker_main_direct_run_and_ledger_all_reject_without_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        run_module, "source_check", lambda: pytest.fail("launcher reached source check"),
    )
    monkeypatch.setattr(
        run_module.subprocess, "run", lambda *_args, **_kwargs: pytest.fail(
            "launcher started a process"
        ),
    )
    poison = _Unreadable()
    before = list(tmp_path.iterdir())
    invocations = (
        lambda: run_module._launch_support_census_worker(
            output_root=poison, result_path=poison,
            resource_receipt_path=poison, run_resource_receipt_path=poison,
        ),
        lambda: worker_module.main(poison),
        lambda: worker_module._run_registered_support_census(
            output_root=poison, result_path=poison,
            resource_receipt_path=poison, run_resource_receipt_path=poison,
        ),
        worker_module.SupportCensusWorkLedger,
    )
    for invoke in invocations:
        with pytest.raises(SupportCensusConsumedError) as captured:
            invoke()
        assert str(captured.value) == SUPPORT_CENSUS_TOMBSTONE_REASON
        assert list(tmp_path.iterdir()) == before


def test_worker_exports_only_the_terminal_entry_surface() -> None:
    assert worker_module.__all__ == ["SupportCensusConsumedError", "main"]

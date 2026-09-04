"""Permanent tombstone for the consumed CRTO K8 support census worker."""

from __future__ import annotations

from typing import Mapping, Sequence

from .config import SupportCensusConsumedError, refuse_consumed_support_census


WORKER_ENV = "HMASD_CRTO_SUPPORT_CENSUS_WORKER"


class SupportCensusWorkLedger:
    """Disabled ledger surface retained only to reject stale callers consistently."""

    def __init__(self) -> None:
        refuse_consumed_support_census()


def _run_registered_support_census(
    *,
    output_root: object,
    result_path: object,
    resource_receipt_path: object,
    run_resource_receipt_path: object,
) -> Mapping[str, object]:
    """Reject the consumed object before inspecting any supplied target."""

    refuse_consumed_support_census()


def main(argv: Sequence[str] | None = None) -> int:
    """Reject before parser construction or argument inspection."""

    refuse_consumed_support_census()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["SupportCensusConsumedError", "main"]

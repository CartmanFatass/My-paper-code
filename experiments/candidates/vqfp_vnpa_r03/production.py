"""Future production command boundary; construction may prepare but not run it."""

from __future__ import annotations

import argparse
import json

from envs.native.production_backend import VQFP_VNPA_R03_FULL_CHAIN, require_cpp_batched_production
from .contract import EXACT_REVISION, FROZEN_COUNTS, QUESTION_RELEVANT_ACTIVITY, SCIENCE_CARD_SHA256
from .lifecycle import COMPETENCE_FIELDS, FROZEN_STAGE_STOPS
from .native_backend import production_execute_guard


def prepared_manifest() -> dict[str, object]:
    return {"schema":"VQFP_VNPA_R03_FUTURE_MANIFEST_V1","revision":EXACT_REVISION,
            "science_card_sha256":SCIENCE_CARD_SHA256,
            "component":VQFP_VNPA_R03_FULL_CHAIN,"backend":"cpp","batch_width":32,
            "workers":8,"frozen_counts":FROZEN_COUNTS,
            "frozen_stage_stops":FROZEN_STAGE_STOPS,"competence_fields":COMPETENCE_FIELDS,
            "scientific_activity_criterion":QUESTION_RELEVANT_ACTIVITY,
            "no_partial_release":True,"lease_required":True,"coordinate_bound":False}


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--print-prepared-manifest",action="store_true"); parser.add_argument("--execute",action="store_true")
    args=parser.parse_args(argv)
    if args.print_prepared_manifest:
        print(json.dumps(prepared_manifest(),sort_keys=True)); return 0
    if args.execute:
        require_cpp_batched_production(VQFP_VNPA_R03_FULL_CHAIN,backend="cpp",batch_width=32)
        production_execute_guard()
    parser.error("construction boundary permits only --print-prepared-manifest")
    return 2


if __name__ == "__main__": raise SystemExit(main())

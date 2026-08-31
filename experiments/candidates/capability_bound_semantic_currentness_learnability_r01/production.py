"""Sole competence-first production orchestration for CBSC-LR01."""

from __future__ import annotations

import time
from pathlib import Path

import torch

from .analysis import reduce_finite_panel, select_branch
from .artifact import publish_complete_result, to_jsonable
from .codecs import CodecArm
from .codecs import CODEC_SCHEDULES
from .contract import RESOURCE_CAPS, SCHEMA_ID
from .addressing import block_id, ordered_batch_ids
from .host import panel
from .initialization import initialized_learner
from .metrics import block_auc, competence_passes, paired_estimands, struct_endpoint_gate, toggle_counts
from .preflight import run_preflight
from .resource import peak_rss_bytes
from .support import Purpose, Split
from .training import BlockTrainingResult, train_competence_block, train_main_block


def _rss_bytes() -> int:
    return peak_rss_bytes()


def _resource_guard(started: float) -> tuple[float, int]:
    wall = time.monotonic() - started
    rss = _rss_bytes()
    if wall > RESOURCE_CAPS["wall_seconds"] or rss > RESOURCE_CAPS["rss_bytes"]:
        raise RuntimeError("CBSC-LR01 resource bound exceeded; no result may be released")
    return wall, rss


def _evaluation_projection(result: BlockTrainingResult) -> dict[str, object]:
    return {
        "purpose": result.purpose.value,
        "block": result.block,
        "arm": result.arm.value,
        "updates": result.updates,
        "optimizer_steps": result.optimizer_steps,
        "examples": result.examples,
        "finite_losses": result.finite_losses,
        "work_receipt": dict(result.work_receipt),
        "checkpoints": [{
            "update": item.update,
            "finite": item.finite,
            "state_unchanged": item.state_unchanged,
            "mean_regret": item.mean_regret,
            "gated_regret": item.gated_regret,
            "open_regret": item.open_regret,
            "correct": sum(item.correct),
            "strict": sum(item.strict),
            "zero_regret": sum(regret == 0 for regret in item.regrets),
        } for item in result.checkpoints],
    }


def _direct_pair_parity(block: int) -> bool:
    models = [initialized_learner(Purpose.MAIN, block) for _ in CodecArm]
    parameter_equal = all(
        torch.equal(left, right)
        for peer in models[1:]
        for left, right in zip(models[0].parameters(), peer.parameters())
    )
    panels = [
        (panel(Purpose.MAIN, block, Split.TRAIN), panel(Purpose.MAIN, block, Split.EVAL))
        for _ in CodecArm
    ]
    direct_values = [
        tuple((row.canonical, row.target_q) for split in pair for row in split)
        for pair in panels
    ]
    identity = block_id(Purpose.MAIN, block)
    orders = [
        tuple(ordered_batch_ids(Purpose.MAIN.value, identity, epoch) for epoch in range(8))
        for _ in CodecArm
    ]
    return parameter_equal and direct_values[0] == direct_values[1] == direct_values[2] and orders[0] == orders[1] == orders[2]


def run_registered(manifest: Path) -> Path:
    started = time.monotonic()
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError as error:
            raise RuntimeError("CBSC-LR01 requires one interop thread before production starts") from error
    peak_rss = _rss_bytes()
    try:
        def guard() -> None:
            nonlocal peak_rss
            _wall, current = _resource_guard(started)
            peak_rss = max(peak_rss, current)

        preflight = run_preflight()
        if not preflight["valid"] or not preflight["ready_for_production"]:
            raise RuntimeError("CBSC-LR01 preflight did not admit production")
        competence: list[BlockTrainingResult] = []
        for block in range(4):
            competence.append(train_competence_block(block, resource_guard=guard))
            _wall, rss = _resource_guard(started)
            peak_rss = max(peak_rss, rss)
        raw_competent = all(competence_passes(result) for result in competence)
        audit_order = (
            "preflight_valid", "complete_competence_panel", "competence_numeric_health",
            "complete_main_panel", "main_numeric_health", "update_zero_common",
            "direct_pair_parity", "paired_work_parity",
        )
        if not raw_competent:
            branch = "RAW_INCOMPETENT"
            main_projection: list[object] = []
            decision_projection = None
            audits = {
                "preflight_valid": True,
                "complete_competence_panel": len(competence) == 4,
                "competence_numeric_health": all(
                    result.finite_losses and result.checkpoints[-1].finite
                    and result.checkpoints[-1].state_unchanged for result in competence
                ),
                "complete_main_panel": None, "main_numeric_health": None,
                "update_zero_common": None, "direct_pair_parity": None,
                "paired_work_parity": None,
            }
            if any(value is False for value in audits.values()):
                branch = "INVALID"
        else:
            main: dict[int, dict[CodecArm, BlockTrainingResult]] = {}
            direct_parity: dict[int, bool] = {}
            for block in range(24):
                direct_parity[block] = _direct_pair_parity(block)
                main[block] = {}
                for arm in CodecArm:
                    main[block][arm] = train_main_block(block, arm, resource_guard=guard)
                    _wall, rss = _resource_guard(started)
                    peak_rss = max(peak_rss, rss)
            valid = all(
                result.finite_losses and all(item.finite and item.state_unchanged for item in result.checkpoints)
                for arms in main.values() for result in arms.values()
            )
            common_zero = all(
                main[block][arm].checkpoints[0].choices == main[block][CodecArm.STRUCT].checkpoints[0].choices
                and main[block][arm].checkpoints[0].regrets == main[block][CodecArm.STRUCT].checkpoints[0].regrets
                for block in range(24) for arm in CodecArm
            )
            common_zero_by_block = {
                block: all(
                    main[block][arm].checkpoints[0].choices == main[block][CodecArm.STRUCT].checkpoints[0].choices
                    and main[block][arm].checkpoints[0].regrets == main[block][CodecArm.STRUCT].checkpoints[0].regrets
                    and main[block][arm].work_receipt["initial_logits_zero"] is True
                    for arm in CodecArm
                ) for block in range(24)
            }
            parity_keys = {
                "initial_logits_zero", "codec_context_materializations",
                "codec_xor_operations", "active_parameters", "parameter_bytes",
                "dense_macs_per_context", "training_forward_contexts", "backward_calls",
                "adam_calls", "scalar_target_exposures", "checkpoint_evaluations",
                "evaluation_contexts", "workers", "threads", "dtype",
            }
            parity = all(
                {key: main[block][arm].work_receipt[key] for key in parity_keys}
                == {key: main[block][CodecArm.STRUCT].work_receipt[key] for key in parity_keys}
                for block in range(24) for arm in CodecArm
            )
            parity_by_block = {
                block: all(
                    {key: main[block][arm].work_receipt[key] for key in parity_keys}
                    == {key: main[block][CodecArm.STRUCT].work_receipt[key] for key in parity_keys}
                    for arm in CodecArm
                ) for block in range(24)
            }
            audits = {
                "preflight_valid": True,
                "complete_competence_panel": len(competence) == 4,
                "competence_numeric_health": all(
                    result.finite_losses and result.checkpoints[-1].finite
                    and result.checkpoints[-1].state_unchanged for result in competence
                ),
                "complete_main_panel": len(main) == 24 and all(len(arms) == 3 for arms in main.values()),
                "main_numeric_health": valid,
                "update_zero_common": common_zero and all(common_zero_by_block.values()),
                "direct_pair_parity": all(direct_parity.values()),
                "paired_work_parity": parity and all(parity_by_block.values()),
            }
            valid = all(value is True for value in audits.values())
            no_headroom = all(
                all(regret == 0 for regret in main[block][arm].checkpoints[1].regrets)
                for block in range(24) for arm in CodecArm
            )
            endpoint = all(
                struct_endpoint_gate(
                    main[block][CodecArm.STRUCT], panel(Purpose.MAIN, block, Split.EVAL)
                ) for block in range(24)
            )
            vectors = [paired_estimands(main[block]) for block in range(24)]
            decision = reduce_finite_panel(vectors)
            branch = select_branch(
                decision, valid=valid, raw_competent=True,
                no_resolvable_headroom=no_headroom, structured_endpoint_gate=endpoint,
            )
            main_projection = [{
                "block": block,
                "arms": [_evaluation_projection(main[block][arm]) for arm in CodecArm],
                "estimand": vectors[block],
                "direct_pair_parity": direct_parity[block],
                "update_zero_common": common_zero_by_block[block],
                "paired_work_parity": parity_by_block[block],
                "structured_u64_correct_by_cell": [
                    sum(main[block][CodecArm.STRUCT].checkpoints[-1].correct[cell * 16:(cell + 1) * 16])
                    for cell in range(48)
                ],
                "structured_toggle_counts": toggle_counts(
                    main[block][CodecArm.STRUCT].checkpoints[-1], panel(Purpose.MAIN, block, Split.EVAL),
                ),
                "structured_endpoint_gate": struct_endpoint_gate(
                    main[block][CodecArm.STRUCT], panel(Purpose.MAIN, block, Split.EVAL),
                ),
            } for block in range(24)]
            decision_projection = decision
        wall, rss = _resource_guard(started)
        peak_rss = max(peak_rss, rss)
        result = {
            "schema": SCHEMA_ID,
            "complete": True,
            "protocol_id": "CBSC-LR01",
            "codec_schedules": {
                arm.value: [list(pair) for pair in CODEC_SCHEDULES[arm]] for arm in CodecArm
            },
            "branch": branch,
            "audits": audits,
            "first_failing_witness": next(
                (name for name in audit_order if audits[name] is False), None,
            ),
            "preflight": preflight,
            "competence": [_evaluation_projection(item) for item in competence],
            "main": main_projection,
            "decision": decision_projection,
            "work": {
                "competence_optimizer_steps": sum(item.optimizer_steps for item in competence),
                "main_optimizer_steps": sum(
                    arm["optimizer_steps"] for block in main_projection for arm in block["arms"]
                ) if main_projection else 0,
                "threads": 1,
            },
            "resource": {"wall_seconds": wall, "peak_rss_bytes": peak_rss},
        }
        payload = to_jsonable(result)
        return publish_complete_result(manifest, payload)
    finally:
        torch.set_num_threads(prior_threads)


__all__ = ["run_registered"]

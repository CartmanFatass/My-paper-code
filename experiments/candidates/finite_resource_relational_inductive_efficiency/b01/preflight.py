"""Direct source/runtime verification of the B01 algorithm contract."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

from ..arms import PROJECTION_BOXES
from ..state_codec import encode_optimizer_state
from ..training import (
    CRITIC_COEFFICIENT, ENTROPY_COEFFICIENT, GRADIENT_CLIP_NORM,
    RSCFTrainer, TRAIN_EPISODES_PER_UPDATE, make_optimizer, rscf_batch_loss,
)
from .constants import LEARNED_ARMS, MODEL_PARAMETERS
from .contract import B01ContractError, exact_algorithm_contract


def static_algorithm_receipt() -> dict[str, Any]:
    from .trainer import ProjectionObservedTrainer

    update_source = inspect.getsource(RSCFTrainer.update)
    b01_update_source = inspect.getsource(ProjectionObservedTrainer.update)
    batch_source = inspect.getsource(rscf_batch_loss)
    optimizer_source = inspect.getsource(make_optimizer)
    adam_position = update_source.find("self.optimizer.step()")
    projection_position = update_source.find("self.model.project_beta()")
    if adam_position < 0 or projection_position <= adam_position:
        raise B01ContractError("actual trainer source does not project strictly after Adam")
    required_source = (
        "terms.loss.backward()", "clip_grad_norm_", "foreach=False",
        "sum(term.loss for term in terms) / divisor",
    )
    combined = update_source + b01_update_source + batch_source + optimizer_source
    if any(fragment not in combined for fragment in required_source):
        raise B01ContractError("actual trainer source differs from the full-batch algorithm")
    ordered_fragments = (
        "zero_grad(set_to_none=True)", "rscf_batch_loss(episodes)",
        "terms.loss.backward()", "clip_grad_norm_", "self.optimizer.step()",
        "self.model.project_beta()",
    )
    positions = [b01_update_source.find(fragment) for fragment in ordered_fragments]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise B01ContractError("actual B01 update order differs")
    for primitive in (
        "terms.score", "terms.entropy", "terms.critic", "preprojection_beta",
        "postprojection_beta", "optimizer_moments_unchanged_by_projection",
    ):
        if primitive not in b01_update_source:
            raise B01ContractError("actual B01 trainer omits required primitive receipts")
    receipt = exact_algorithm_contract()
    if (
        ENTROPY_COEFFICIENT != receipt["loss"]["entropy_coefficient"]
        or CRITIC_COEFFICIENT != receipt["loss"]["critic_coefficient"]
        or GRADIENT_CLIP_NORM != receipt["loss"]["gradient_clip_l2"]
        or TRAIN_EPISODES_PER_UPDATE != receipt["loss"]["episodes_per_update"]
        or {arm: list(PROJECTION_BOXES[arm]) for arm in LEARNED_ARMS}
        != {arm: receipt["projection_boxes"][arm] for arm in LEARNED_ARMS}
    ):
        raise B01ContractError("actual runtime constants differ from algorithm contract")
    return {
        "schema": "FRRIE_B01_STATIC_ALGORITHM_PREFLIGHT_V1",
        "algorithm_contract": receipt,
        "adam_before_projection": True,
        "full_batch_source_verified": True,
        "runtime_constants_verified": True,
    }


def runtime_algorithm_receipt(
    models: Mapping[str, Any], optimizers: Mapping[str, Any],
) -> dict[str, Any]:
    if set(models) != set(LEARNED_ARMS) or set(optimizers) != set(LEARNED_ARMS):
        raise B01ContractError("runtime preflight requires exactly both learned arms")
    static = static_algorithm_receipt()
    rows: dict[str, Any] = {}
    for arm in LEARNED_ARMS:
        model = models[arm]
        optimizer = optimizers[arm]
        if model.arm_id != arm or sum(parameter.numel() for parameter in model.parameters()) != MODEL_PARAMETERS:
            raise B01ContractError("runtime model identity/parameter count differs")
        if any(parameter.dtype.__str__() != "torch.float32" or parameter.device.type != "cpu"
               for parameter in model.parameters()):
            raise B01ContractError("runtime model is not CPU FP32")
        # This validates exact optimizer class, order, state shapes, and finite values.
        optimizer_bytes = encode_optimizer_state(model, optimizer)
        group = optimizer.param_groups[0]
        expected = exact_algorithm_contract()["optimizer"]
        if not (
            group["lr"] == expected["learning_rate"]
            and group["betas"] == tuple(expected["betas"])
            and group["eps"] == expected["epsilon"]
            and group["weight_decay"] == expected["weight_decay"]
            and group["amsgrad"] is expected["amsgrad"]
            and group.get("maximize") is expected["maximize"]
            and group.get("capturable") is expected["capturable"]
            and group.get("differentiable") is expected["differentiable"]
            and group.get("foreach") is expected["foreach"]
            and group.get("fused") is expected["fused"]
            and expected["zero_grad_set_to_none"] is True
        ):
            raise B01ContractError("actual optimizer runtime differs from algorithm contract")
        rows[arm] = {
            "parameter_count": MODEL_PARAMETERS,
            "parameter_dtype": "float32", "device": "cpu",
            "projection_box": list(PROJECTION_BOXES[arm]),
            "optimizer_state_bytes": len(optimizer_bytes),
        }
    paired_parameters_equal = (
        models[LEARNED_ARMS[0]].parameter_bytes()
        == models[LEARNED_ARMS[1]].parameter_bytes()
    )
    paired_optimizers_equal = (
        encode_optimizer_state(models[LEARNED_ARMS[0]], optimizers[LEARNED_ARMS[0]])
        == encode_optimizer_state(models[LEARNED_ARMS[1]], optimizers[LEARNED_ARMS[1]])
    )
    if not paired_parameters_equal or not paired_optimizers_equal:
        raise B01ContractError("runtime paired initial model/optimizer bytes differ")
    return {
        "schema": "FRRIE_B01_RUNTIME_ALGORITHM_PREFLIGHT_V1",
        "static": static,
        "arms": rows,
        "paired_parameter_bytes_equal": paired_parameters_equal,
        "paired_optimizer_bytes_equal": paired_optimizers_equal,
        "complete": True,
    }

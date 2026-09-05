"""Projection-observing paired RSCF update primitive for B01."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..state_codec import (
    decode_optimizer_state, encode_optimizer_state, load_actor_and_optimizer_state,
)
from ..training import (
    GRADIENT_CLIP_NORM, LossReductionReceipt, RSCFEpisode,
    _rscf_batch_loss_with_receipt, exact_loss_reduction_contract, make_optimizer,
    validate_loss_reduction_receipt, validate_update_batch,
)
from ..contracts.core import ContractError
from .constants import (
    LEARNED_ARMS, TRAIN_FACTUAL_WORK_PER_ARM_SEED,
    TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED, TRAIN_AUDIT_WORK_PER_ARM_SEED,
    TRAIN_TOTAL_WORK_PER_ARM_SEED, UPDATES, MODEL_PARAMETERS,
    PARAMETER_DISTANCE_RAW_SCHEMA, PARAMETER_DISTANCE_STATE_SCHEMA,
    PARAMETER_DISTANCE_LAYOUT_SCHEMA, PARAMETER_DISTANCE_BETA_FLAT_START,
    PARAMETER_DISTANCE_BETA_FLAT_END, PARAMETER_DISTANCE_BETA_BYTE_START,
    PARAMETER_DISTANCE_BETA_BYTE_END,
    CHECKPOINTS,
)
from .contract import B01ContractError
from .contract import canonical_json_bytes
from .native_batch import BatchWorkLedger


class _ParameterDistanceNonfinite(B01ContractError):
    pass


@dataclass(frozen=True, slots=True)
class ArmUpdateReceipt:
    arm: str
    update: int
    loss: float
    score: float
    entropy: float
    critic: float
    loss_reduction_receipt: LossReductionReceipt
    preclip_global_norm: float
    backward_calls: int
    adam_steps: int
    projection_changed_indices: tuple[int, ...]
    box_contact: bool
    maximum_box_overshoot: float
    projection_displacement: float
    preprojection_beta: tuple[float, ...]
    postprojection_beta: tuple[float, ...]
    optimizer_moments_unchanged_by_projection: bool
    model_pre_bytes: bytes
    optimizer_pre_bytes: bytes
    model_post_adam_bytes: bytes
    optimizer_post_adam_bytes: bytes
    model_post_projection_bytes: bytes
    optimizer_post_projection_bytes: bytes


def _tensor_direct_equal(left: Any, right: Any) -> bool:
    import torch
    return (
        isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor)
        and left.dtype == right.dtype and left.shape == right.shape
        and torch.equal(left.detach(), right.detach())
    )


def _q_targets_direct_equal(
    left_targets: Any, right_targets: Any, left_masks: Any, right_masks: Any,
) -> bool:
    """Bit-exact paired Q targets with the frozen illegal-action NaN sentinel.

    ``training._validate_episode`` intentionally requires finiteness only on
    ``targets[legal]``.  The collector therefore initializes the whole target
    matrix with the canonical CPU FP32 quiet-NaN and fills only legal columns.
    Comparing these tensors with ``torch.equal`` is incorrect because equal
    NaN payloads still compare unequal.
    """

    import torch

    if not all(isinstance(value, torch.Tensor) for value in (
        left_targets, right_targets, left_masks, right_masks,
    )):
        return False
    if (
        left_targets.device.type != "cpu" or right_targets.device.type != "cpu"
        or left_masks.device.type != "cpu" or right_masks.device.type != "cpu"
        or left_targets.dtype != torch.float32 or right_targets.dtype != torch.float32
        or left_targets.shape != (3, 6) or right_targets.shape != (3, 6)
        or left_masks.dtype != torch.bool or right_masks.dtype != torch.bool
        or left_masks.shape != (3, 6) or right_masks.shape != (3, 6)
        or not torch.equal(left_masks.detach(), right_masks.detach())
    ):
        return False
    legal = left_masks.detach()
    left = left_targets.detach().contiguous()
    right = right_targets.detach().contiguous()
    if (
        not bool(torch.isfinite(left[legal]).all().item())
        or not bool(torch.isfinite(right[legal]).all().item())
        or not torch.equal(left.view(torch.int32)[legal], right.view(torch.int32)[legal])
    ):
        return False
    illegal = ~legal
    if (
        not bool(torch.isnan(left[illegal]).all().item())
        or not bool(torch.isnan(right[illegal]).all().item())
    ):
        return False
    canonical_nan_bits = torch.full(
        (3, 6), float("nan"), dtype=torch.float32,
    ).view(torch.int32)[illegal]
    return bool(
        torch.equal(left.view(torch.int32)[illegal], canonical_nan_bits)
        and torch.equal(right.view(torch.int32)[illegal], canonical_nan_bits)
    )


_EXOGENOUS_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class DirectExogenousEpisode:
    update: int
    position: int
    roster: int
    tape_bytes: bytes
    tape_coordinate: tuple[str, str, int, int, int]
    law_revisions: tuple[str, ...]
    observations_bytes: bytes
    observations_shape: tuple[int, ...]
    observations_dtype: str
    relations_bytes: bytes
    relations_shape: tuple[int, ...]
    relations_dtype: str
    masks_bytes: bytes
    masks_shape: tuple[int, ...]
    masks_dtype: str
    origin_coordinates: tuple[tuple[int, int, int], ...]
    origin_addresses: tuple[bytes, ...]

    def __init__(
        self, token: object, *, update: int, position: int, roster: int,
        tape_bytes: bytes, tape_coordinate: tuple[str, str, int, int, int],
        law_revisions: tuple[str, ...],
        observations_bytes: bytes, observations_shape: tuple[int, ...], observations_dtype: str,
        relations_bytes: bytes, relations_shape: tuple[int, ...], relations_dtype: str,
        masks_bytes: bytes, masks_shape: tuple[int, ...], masks_dtype: str,
        origin_coordinates: tuple[tuple[int, int, int], ...],
        origin_addresses: tuple[bytes, ...],
    ) -> None:
        if token is not _EXOGENOUS_TOKEN:
            raise B01ContractError("exogenous episode must be captured from direct arrays/tape")
        for field, value in (
            ("tape", tape_bytes), ("observations", observations_bytes),
            ("relations", relations_bytes), ("masks", masks_bytes),
        ):
            if type(value) is not bytes or not value:
                raise B01ContractError(f"direct {field} bytes are absent")
        object.__setattr__(self, "update", update)
        object.__setattr__(self, "position", position)
        object.__setattr__(self, "roster", roster)
        object.__setattr__(self, "tape_bytes", tape_bytes)
        object.__setattr__(self, "tape_coordinate", tape_coordinate)
        object.__setattr__(self, "law_revisions", law_revisions)
        object.__setattr__(self, "observations_bytes", observations_bytes)
        object.__setattr__(self, "observations_shape", observations_shape)
        object.__setattr__(self, "observations_dtype", observations_dtype)
        object.__setattr__(self, "relations_bytes", relations_bytes)
        object.__setattr__(self, "relations_shape", relations_shape)
        object.__setattr__(self, "relations_dtype", relations_dtype)
        object.__setattr__(self, "masks_bytes", masks_bytes)
        object.__setattr__(self, "masks_shape", masks_shape)
        object.__setattr__(self, "masks_dtype", masks_dtype)
        object.__setattr__(self, "origin_coordinates", origin_coordinates)
        object.__setattr__(self, "origin_addresses", origin_addresses)


def capture_exogenous_episode(
    *, update: int, position: int, roster: int, tape: Any,
    observations: Any, relations: Any, masks: Any,
    origin_coordinates: Sequence[tuple[int, int, int]],
) -> DirectExogenousEpisode:
    import numpy as np
    from ..policy import LEGAL_ACTION_INDICES
    from ..tapes import EpisodeTape

    expected_episode = position // 2
    if (
        type(tape) is not EpisodeTape or tape.purpose != "TRAIN"
        or tape.roster != roster or tape.update != update or tape.episode != expected_episode
        or not tape.seed_block.startswith("FRRIE-B01-")
    ):
        raise B01ContractError("direct TRAIN tape coordinate differs from batch position")
    fields = ("event_times", "detection_uniform", "uplink_uniform", "base_uniform", "action_uniform")
    tape_bytes = b"".join(getattr(tape, field).tobytes(order="C") for field in fields)
    observation_array = np.asarray(observations)
    role_array = np.asarray(relations)
    mask_array = np.asarray(masks)
    expected_roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
    expected_masks = np.zeros((12, roster, 6), dtype=np.bool_)
    for entity, role in enumerate(expected_roles):
        expected_masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
    if (
        observation_array.dtype != np.dtype(np.float32)
        or observation_array.shape != (12, roster, 22)
        or not observation_array.flags.c_contiguous
        or not np.isfinite(observation_array).all()
    ):
        raise B01ContractError("direct observations must be finite C-order FP32 [12,N,22]")
    if (
        role_array.dtype != np.dtype(np.int64) or role_array.shape != (roster,)
        or not role_array.flags.c_contiguous or not np.array_equal(role_array, expected_roles)
    ):
        raise B01ContractError("direct roles must be fixed contiguous int64 thirds 0/1/2")
    if (
        mask_array.dtype != np.dtype(np.bool_) or mask_array.shape != (12, roster, 6)
        or not mask_array.flags.c_contiguous or not np.array_equal(mask_array, expected_masks)
    ):
        raise B01ContractError("direct masks must equal the exact per-role legal support")
    origins = tuple(tuple(map(int, value)) for value in origin_coordinates)
    if (
        len(origins) != 3 or tuple(value[0] for value in origins) != (0, 1, 2)
        or any(
            len(value) != 3 or not 0 <= value[1] < 12 or not 0 <= value[2] < roster
            or int(role_array[value[2]]) != value[0]
            for value in origins
        )
    ):
        raise B01ContractError("origin coordinates must be one valid entity/slot per role")
    origin_addresses = tuple(canonical_json_bytes({
        "schema": "FRRIE_B01_ORIGIN_ADDRESS_V1", "seed_block": tape.seed_block,
        "update": update, "batch_position": position, "roster": roster,
        "role": role, "slot": slot, "entity": entity,
    }) for role, slot, entity in origins)
    return DirectExogenousEpisode(
        _EXOGENOUS_TOKEN, update=update, position=position, roster=roster,
        tape_bytes=tape_bytes,
        tape_coordinate=(tape.seed_block, tape.purpose, tape.roster, tape.update, tape.episode),
        law_revisions=(
            "RIDGEGATE_2Z_NATIVE_STEP_ABI_V2", "OBSERVATION_22_V1",
            "K0_RELATION_FUNCTION_V1", "ROLE_LEGAL_MASK_FUNCTION_V1",
        ),
        observations_bytes=observation_array.tobytes(order="C"),
        observations_shape=tuple(observation_array.shape), observations_dtype=str(observation_array.dtype),
        relations_bytes=role_array.tobytes(order="C"), relations_shape=tuple(role_array.shape),
        relations_dtype=str(role_array.dtype), masks_bytes=mask_array.tobytes(order="C"),
        masks_shape=tuple(mask_array.shape), masks_dtype=str(mask_array.dtype),
        origin_coordinates=origins, origin_addresses=origin_addresses,
    )


@dataclass(frozen=True, slots=True)
class B01ArmBatch:
    episodes: tuple[RSCFEpisode, ...]
    exogenous_receipts: tuple[DirectExogenousEpisode, ...]
    collection_ledgers: tuple[BatchWorkLedger, ...]

    def validate(self, *, update: int) -> "B01ArmBatch":
        if len(self.episodes) != 64 or len(self.exogenous_receipts) != 64:
            raise B01ContractError("B01 arm batch requires 64 episodes/receipts")
        for position, receipt in enumerate(self.exogenous_receipts):
            if (
                type(receipt) is not DirectExogenousEpisode
                or receipt.update != update or receipt.position != position
                or receipt.roster != (9 if position % 2 == 0 else 15)
            ):
                raise B01ContractError("B01 exogenous receipt coordinate differs")
        if len({receipt.tape_coordinate[0] for receipt in self.exogenous_receipts}) != 1:
            raise B01ContractError("B01 update mixes seed-block identities")
        if not self.collection_ledgers or any(type(item) is not BatchWorkLedger for item in self.collection_ledgers):
            raise B01ContractError("B01 collection requires direct native ledgers")
        if sum(item.environment_slots for item in self.collection_ledgers) != 4_928:
            raise B01ContractError("actual native collection work differs from 4928 slots")
        return self


def assert_paired_episode_information(
    left: Sequence[RSCFEpisode], right: Sequence[RSCFEpisode],
) -> None:
    if len(left) != len(right):
        raise B01ContractError("paired arm episode counts differ")
    fields = (
        "selected_probabilities", "factual_actions",
        "all_probabilities", "critic_values", "terminal_return",
    )
    for left_episode, right_episode in zip(left, right):
        if (
            left_episode.roster_size != right_episode.roster_size
            or not _q_targets_direct_equal(
                left_episode.q_targets, right_episode.q_targets,
                left_episode.legal_masks, right_episode.legal_masks,
            )
            or any(
            not _tensor_direct_equal(getattr(left_episode, field), getattr(right_episode, field))
            for field in fields
            )
        ):
            raise B01ContractError("paired arms received different information or targets")


def assert_common_exogenous_and_work(left: B01ArmBatch, right: B01ArmBatch) -> None:
    if left.collection_ledgers != right.collection_ledgers:
        raise B01ContractError("paired arms received different exogenous coordinates or work")
    for left_row, right_row in zip(left.exogenous_receipts, right.exogenous_receipts):
        # Actual observation values are action/history endogenous after
        # contact.  Common pairing binds only exogenous tapes, law revisions,
        # fixed roles/masks, origin addresses, and batch coordinates.
        common_left = (
            left_row.update, left_row.position, left_row.roster,
            left_row.tape_bytes, left_row.tape_coordinate, left_row.law_revisions,
            left_row.relations_bytes, left_row.relations_shape, left_row.relations_dtype,
            left_row.masks_bytes, left_row.masks_shape, left_row.masks_dtype,
            left_row.origin_coordinates, left_row.origin_addresses,
        )
        common_right = (
            right_row.update, right_row.position, right_row.roster,
            right_row.tape_bytes, right_row.tape_coordinate, right_row.law_revisions,
            right_row.relations_bytes, right_row.relations_shape, right_row.relations_dtype,
            right_row.masks_bytes, right_row.masks_shape, right_row.masks_dtype,
            right_row.origin_coordinates, right_row.origin_addresses,
        )
        if common_left != common_right:
            raise B01ContractError("paired arms received different exogenous coordinates or work")


def assert_precontact_observation_equality(left: B01ArmBatch, right: B01ArmBatch) -> None:
    if any(
        (
            lrow.observations_bytes, lrow.observations_shape, lrow.observations_dtype,
        ) != (
            rrow.observations_bytes, rrow.observations_shape, rrow.observations_dtype,
        )
        for lrow, rrow in zip(left.exogenous_receipts, right.exogenous_receipts)
    ):
        raise B01ContractError("pre-contact actual observation traces differ")


class ProjectionObservedTrainer:
    """Exact full-batch Adam update with direct pre-projection observation."""

    def __init__(self, model: Any, optimizer: Any | None = None) -> None:
        self.model = model
        self.optimizer = make_optimizer(model) if optimizer is None else optimizer

    def update(self, episodes: Sequence[RSCFEpisode], *, update: int) -> ArmUpdateReceipt:
        import torch

        if type(update) is not int or not 1 <= update <= 512:
            raise B01ContractError("B01 update must lie in [1,512]")
        validate_update_batch(episodes)
        model_pre_bytes = self.model.parameter_bytes()
        optimizer_pre_bytes = encode_optimizer_state(self.model, self.optimizer)
        self.optimizer.zero_grad(set_to_none=True)
        terms, loss_reduction_receipt = _rscf_batch_loss_with_receipt(episodes)
        if not bool(torch.isfinite(terms.loss).item()) or not terms.loss.requires_grad:
            raise B01ContractError("B01 full-batch loss is not finite/differentiable")
        terms.loss.backward()
        parameters = self.model.ordered_parameters()
        if any(parameter.grad is None or not bool(torch.isfinite(parameter.grad).all().item())
               for parameter in parameters):
            raise B01ContractError("B01 full backward has missing/nonfinite gradients")
        preclip = torch.nn.utils.clip_grad_norm_(
            parameters, GRADIENT_CLIP_NORM, norm_type=2.0,
            error_if_nonfinite=True, foreach=False,
        )
        self.optimizer.step()
        model_post_adam_bytes = self.model.parameter_bytes()
        optimizer_post_adam_bytes = encode_optimizer_state(self.model, self.optimizer)
        beta_before_projection = self.model.beta.detach().clone()
        low, high = self.model.projection_box if hasattr(self.model, "projection_box") else (
            (-0.15, 0.15) if self.model.arm_id == "PHY_TRUST" else (-1.5, 1.5)
        )
        projected = beta_before_projection.clamp(low, high)
        changed = int((projected != beta_before_projection).sum().item())
        changed_indices = tuple(
            int(index) for index in torch.nonzero(
                (projected != beta_before_projection).reshape(-1), as_tuple=False,
            ).reshape(-1).tolist()
        )
        overshoot = float(torch.maximum(
            (torch.tensor(low) - beta_before_projection).clamp_min(0).max(),
            (beta_before_projection - torch.tensor(high)).clamp_min(0).max(),
        ).item())
        displacement = float((projected - beta_before_projection).abs().sum().item())
        optimizer_before_projection = encode_optimizer_state(self.model, self.optimizer)
        self.model.project_beta()
        optimizer_after_projection = encode_optimizer_state(self.model, self.optimizer)
        if not torch.equal(self.model.beta.detach(), projected):
            raise B01ContractError("actual projection differs from direct clipped beta")
        if optimizer_before_projection != optimizer_after_projection:
            raise B01ContractError("projection changed Adam moments")
        return ArmUpdateReceipt(
            arm=self.model.arm_id, update=update, loss=float(terms.loss.detach().item()),
            score=float(terms.score.detach().item()),
            entropy=float(terms.entropy.detach().item()),
            critic=float(terms.critic.detach().item()),
            loss_reduction_receipt=loss_reduction_receipt,
            preclip_global_norm=float(preclip.detach().item()), backward_calls=1,
            adam_steps=1, projection_changed_indices=changed_indices,
            box_contact=bool(changed),
            maximum_box_overshoot=overshoot, projection_displacement=displacement,
            preprojection_beta=tuple(float(value) for value in beta_before_projection.reshape(-1)),
            postprojection_beta=tuple(float(value) for value in projected.reshape(-1)),
            optimizer_moments_unchanged_by_projection=True,
            model_pre_bytes=model_pre_bytes,
            optimizer_pre_bytes=optimizer_pre_bytes,
            model_post_adam_bytes=model_post_adam_bytes,
            optimizer_post_adam_bytes=optimizer_post_adam_bytes,
            model_post_projection_bytes=self.model.parameter_bytes(),
            optimizer_post_projection_bytes=optimizer_after_projection,
        )


class PairedB01Trainer:
    def __init__(self, models: Mapping[str, Any], optimizers: Mapping[str, Any]) -> None:
        if set(models) != set(LEARNED_ARMS) or set(optimizers) != set(LEARNED_ARMS):
            raise B01ContractError("paired trainer requires both learned arms")
        self.models = dict(models)
        self.trainers = {
            arm: ProjectionObservedTrainer(models[arm], optimizers[arm]) for arm in LEARNED_ARMS
        }
        self.first_tight_contact_update: int | None = None
        self.precontact_full_state_equal = True
        self.changed_coordinates: set[int] = set()
        self.maximum_tight_overshoot = 0.0
        self.cumulative_tight_displacement = 0.0
        self.wide_boundary_contact = False
        self._continuation_seed_label: str | None = None
        self._continuation_update = 0
        self._continuation_work: Mapping[str, Any] | None = None
        self._continuation_frontier: Mapping[str, Any] | None = None

    def _state_equal(self) -> bool:
        left, right = LEARNED_ARMS
        return (
            self.models[left].parameter_bytes() == self.models[right].parameter_bytes()
            and encode_optimizer_state(self.models[left], self.trainers[left].optimizer)
            == encode_optimizer_state(self.models[right], self.trainers[right].optimizer)
        )

    def update(
        self, batches: Mapping[str, B01ArmBatch], *, update: int,
    ) -> dict[str, ArmUpdateReceipt]:
        if set(batches) != set(LEARNED_ARMS):
            raise B01ContractError("paired update requires both arm batches")
        precontact = self.first_tight_contact_update is None
        if precontact and not self._state_equal():
            self.precontact_full_state_equal = False
            raise B01ContractError("paired full state diverged before tight contact")
        left = batches[LEARNED_ARMS[0]].validate(update=update)
        right = batches[LEARNED_ARMS[1]].validate(update=update)
        assert_common_exogenous_and_work(left, right)
        # Before contact the models, policies, native paths, and all derived
        # episode tensors must be identical.  After contact only exogenous
        # provenance/work stays common; requiring targets or probabilities to
        # remain equal would delete the treatment effect.
        if precontact:
            assert_precontact_observation_equality(left, right)
            assert_paired_episode_information(left.episodes, right.episodes)
        backups = {
            arm: (
                self.models[arm].parameter_bytes(),
                encode_optimizer_state(self.models[arm], self.trainers[arm].optimizer),
            )
            for arm in LEARNED_ARMS
        }
        try:
            receipts = {
                arm: self.trainers[arm].update(batches[arm].episodes, update=update)
                for arm in LEARNED_ARMS
            }
            tight = receipts["PHY_TRUST"]
            wide = receipts["EDGE_FLEX"]
            proposed_first = self.first_tight_contact_update
            proposed_coordinates = set(self.changed_coordinates)
            proposed_maximum = self.maximum_tight_overshoot
            proposed_displacement = self.cumulative_tight_displacement
            proposed_wide = self.wide_boundary_contact
            if tight.box_contact:
                if proposed_first is None:
                    proposed_first = update
                proposed_coordinates.update(tight.projection_changed_indices)
                proposed_maximum = max(proposed_maximum, tight.maximum_box_overshoot)
                proposed_displacement += tight.projection_displacement
            if wide.box_contact:
                proposed_wide = True
            if proposed_first is None and not self._state_equal():
                raise B01ContractError("paired full state diverged on a no-contact update")
        except Exception as exc:
            for arm in LEARNED_ARMS:
                model_bytes, optimizer_bytes = backups[arm]
                prior_step = decode_optimizer_state(optimizer_bytes).step
                load_actor_and_optimizer_state(
                    self.models[arm], self.trainers[arm].optimizer,
                    model_bytes, optimizer_bytes, expected_update=prior_step,
                )
            if any(
                self.models[arm].parameter_bytes() != backups[arm][0]
                or encode_optimizer_state(self.models[arm], self.trainers[arm].optimizer)
                != backups[arm][1]
                for arm in LEARNED_ARMS
            ):
                raise RuntimeError("B01 paired update rollback did not restore direct bytes") from exc
            raise B01ContractError("B01 paired update failed; both arms rolled back") from exc
        self.first_tight_contact_update = proposed_first
        self.changed_coordinates = proposed_coordinates
        self.maximum_tight_overshoot = proposed_maximum
        self.cumulative_tight_displacement = proposed_displacement
        self.wide_boundary_contact = proposed_wide
        return receipts

    def update_with_direct_rows(
        self, batches: Mapping[str, B01ArmBatch], *,
        collection_audits: Mapping[str, Any], update: int,
        expected_seed_label: str,
        expected_root: bytes,
    ) -> dict[str, Any]:
        """Atomically update, validate direct rows, and advance continuation state.

        This is the B01 induction transaction.  Model/Adam, projection audit,
        cumulative work, and the publication frontier either all advance from
        ``update-1`` to ``update`` or all return to their direct prestates.
        """

        from .training_shards import (
            actual_direct_training_row, validate_actual_direct_row_chain_step,
            validate_actual_paired_direct_rows,
        )

        if set(batches) != set(LEARNED_ARMS) or set(collection_audits) != set(LEARNED_ARMS):
            raise B01ContractError("paired direct transaction inventory differs")
        if self._continuation_update != update - 1:
            raise B01ContractError("paired direct transaction continuation frontier differs")
        prior_continuation = self.checkpoint_continuation_state()
        prior_audit = self.projection_audit()
        prior_states = {
            arm: (
                self.models[arm].parameter_bytes(),
                encode_optimizer_state(self.models[arm], self.trainers[arm].optimizer),
            )
            for arm in LEARNED_ARMS
        }
        try:
            receipts = self.update(batches, update=update)
            rows = {
                arm: actual_direct_training_row(
                    receipt=receipts[arm], batch=batches[arm],
                    collection_audit=collection_audits[arm],
                )
                for arm in LEARNED_ARMS
            }
            paired = validate_actual_paired_direct_rows(
                rows, expected_update=update,
                expected_seed_label=expected_seed_label,
                expected_root=expected_root,
            )
            chains = {
                arm: validate_actual_direct_row_chain_step(
                    rows[arm], expected_update=update,
                    previous_model_post_projection=prior_states[arm][0],
                    previous_optimizer_post_projection=prior_states[arm][1],
                )
                for arm in LEARNED_ARMS
            }
            work = deepcopy(prior_continuation["work"])
            for arm in LEARNED_ARMS:
                ledgers = batches[arm].collection_ledgers
                reset = sum(item.native_reset_calls for item in ledgers)
                observe = sum(item.native_observe_calls for item in ledgers)
                step = sum(item.native_step_calls for item in ledgers)
                row = work[arm]
                ledger = row["native_batch_ledger"]
                row.update({
                    "training_update": update,
                    "episodes": row["episodes"] + 64,
                    "environment_slots": row["environment_slots"] + 4_928,
                    "backward_calls": row["backward_calls"] + 1,
                    "adam_steps": row["adam_steps"] + 1,
                    "native_batch_calls": row["native_batch_calls"] + reset + observe + step,
                })
                ledger.update({
                    "reset_calls": ledger["reset_calls"] + reset,
                    "observe_calls": ledger["observe_calls"] + observe,
                    "step_calls": ledger["step_calls"] + step,
                    "environment_slots": ledger["environment_slots"] + 4_928,
                })
            if work[LEARNED_ARMS[0]] != work[LEARNED_ARMS[1]]:
                raise B01ContractError("paired direct transaction cumulative work differs")
            completed = list(prior_continuation["frontier"]["completed_checkpoints"])
            if update in CHECKPOINTS and update not in completed:
                completed.append(update)
            self._continuation_update = update
            self._continuation_work = work
            self._continuation_frontier = {
                "training_update": update,
                "training_episode_cursor": update * 64,
                "evaluation_checkpoint_cursor": prior_continuation["frontier"][
                    "evaluation_checkpoint_cursor"
                ],
                "completed_checkpoints": completed,
            }
            continuation = self.checkpoint_continuation_state()
            if continuation["update"] != update or continuation["work"] != work:
                raise B01ContractError("paired direct transaction continuation readback differs")
            return {
                "schema": "FRRIE_B01_COMMITTED_DIRECT_UPDATE_V1",
                "receipts": receipts, "rows": rows, "paired": paired,
                "chains": chains, "continuation": continuation,
            }
        except Exception as exc:
            for arm in LEARNED_ARMS:
                model_bytes, optimizer_bytes = prior_states[arm]
                load_actor_and_optimizer_state(
                    self.models[arm], self.trainers[arm].optimizer,
                    model_bytes, optimizer_bytes, expected_update=update - 1,
                )
            self.first_tight_contact_update = prior_continuation[
                "first_tight_contact_update"
            ]
            self.precontact_full_state_equal = prior_continuation[
                "precontact_full_state_equal"
            ]
            self.changed_coordinates = set(
                prior_continuation["tight_projection_changed_indices"]
            )
            self.wide_boundary_contact = prior_continuation["wide_boundary_contact"]
            self.maximum_tight_overshoot = prior_continuation[
                "maximum_tight_overshoot"
            ]
            self.cumulative_tight_displacement = prior_continuation[
                "cumulative_tight_displacement"
            ]
            self._continuation_seed_label = prior_continuation["seed_label"]
            self._continuation_update = prior_continuation["update"]
            self._continuation_work = deepcopy(prior_continuation["work"])
            self._continuation_frontier = deepcopy(prior_continuation["frontier"])
            if (
                self.projection_audit() != prior_audit
                or self.checkpoint_continuation_state() != prior_continuation
                or any(
                    self.models[arm].parameter_bytes() != prior_states[arm][0]
                    or encode_optimizer_state(
                        self.models[arm], self.trainers[arm].optimizer,
                    ) != prior_states[arm][1]
                    for arm in LEARNED_ARMS
                )
            ):
                raise RuntimeError("B01 direct transaction rollback failed") from exc
            raise B01ContractError(
                "B01 direct transaction failed; state/work/frontier rolled back"
            ) from exc

    def projection_audit(self) -> dict[str, Any]:
        return {
            "first_tight_contact_update": self.first_tight_contact_update,
            "precontact_full_state_equal": self.precontact_full_state_equal,
            "tight_projection_changed_coordinates": len(self.changed_coordinates),
            "tight_projection_changed_indices": sorted(self.changed_coordinates),
            "wide_boundary_contact": self.wide_boundary_contact,
            "maximum_tight_overshoot": self.maximum_tight_overshoot,
            "cumulative_tight_displacement": self.cumulative_tight_displacement,
        }

    def restore_checkpoint_continuation_state(self, state: Mapping[str, Any]) -> None:
        """Explicitly restore every non-model field used by continued training."""

        fields = {
            "schema", "seed_label", "update", "first_tight_contact_update",
            "precontact_full_state_equal", "tight_projection_changed_indices",
            "wide_boundary_contact", "maximum_tight_overshoot",
            "cumulative_tight_displacement", "work", "frontier",
        }
        if not isinstance(state, Mapping) or set(state) != fields or state.get(
            "schema"
        ) != "FRRIE_B01_TRAINER_CONTINUATION_STATE_V1":
            raise B01ContractError("trainer continuation state fields differ")
        update = state["update"]
        contact = state["first_tight_contact_update"]
        indices = state["tight_projection_changed_indices"]
        if (
            update not in CHECKPOINTS
            or (contact is not None and (type(contact) is not int or not 1 <= contact <= update))
            or not isinstance(indices, list)
            or indices != sorted(set(indices))
            or any(type(item) is not int or not 0 <= item < 18 for item in indices)
            or type(state["precontact_full_state_equal"]) is not bool
            or type(state["wide_boundary_contact"]) is not bool
            or state["precontact_full_state_equal"] is not True
        ):
            raise B01ContractError("trainer continuation audit values differ")
        for field in ("maximum_tight_overshoot", "cumulative_tight_displacement"):
            value = state[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise B01ContractError("trainer continuation movement values differ")
        if contact is None and (
            indices or state["maximum_tight_overshoot"] != 0
            or state["cumulative_tight_displacement"] != 0
        ):
            raise B01ContractError("trainer no-contact continuation audit differs")
        if contact is not None and (
            not indices or state["maximum_tight_overshoot"] <= 0
            or state["cumulative_tight_displacement"] <= 0
        ):
            raise B01ContractError("trainer contact continuation audit differs")
        frontier = state["frontier"]
        if not isinstance(frontier, Mapping) or frontier.get("training_update") != update:
            raise B01ContractError("trainer continuation frontier differs")
        if not isinstance(state["work"], Mapping) or set(state["work"]) != set(LEARNED_ARMS):
            raise B01ContractError("trainer continuation work inventory differs")
        self.first_tight_contact_update = contact
        self.precontact_full_state_equal = state["precontact_full_state_equal"]
        self.changed_coordinates = set(indices)
        self.wide_boundary_contact = state["wide_boundary_contact"]
        self.maximum_tight_overshoot = float(state["maximum_tight_overshoot"])
        self.cumulative_tight_displacement = float(state["cumulative_tight_displacement"])
        self._continuation_seed_label = state["seed_label"]
        self._continuation_update = update
        self._continuation_work = deepcopy(state["work"])
        self._continuation_frontier = deepcopy(state["frontier"])

    def checkpoint_continuation_state(self) -> dict[str, Any]:
        """Read back the exact audit/work/frontier continuation state."""

        return {
            "schema": "FRRIE_B01_TRAINER_CONTINUATION_STATE_V1",
            "seed_label": self._continuation_seed_label,
            "update": self._continuation_update,
            "first_tight_contact_update": self.first_tight_contact_update,
            "precontact_full_state_equal": self.precontact_full_state_equal,
            "tight_projection_changed_indices": sorted(self.changed_coordinates),
            "wide_boundary_contact": self.wide_boundary_contact,
            "maximum_tight_overshoot": self.maximum_tight_overshoot,
            "cumulative_tight_displacement": self.cumulative_tight_displacement,
            "work": deepcopy(self._continuation_work),
            "frontier": deepcopy(self._continuation_frontier),
        }

    def checkpoint_boundary_state_inventory(self) -> dict[str, Any]:
        """Prove this trainer retains no live rollout/native/RNG iterator state."""

        expected = {
            "models", "trainers", "first_tight_contact_update",
            "precontact_full_state_equal", "changed_coordinates",
            "maximum_tight_overshoot", "cumulative_tight_displacement",
            "wide_boundary_contact", "_continuation_seed_label",
            "_continuation_update", "_continuation_work", "_continuation_frontier",
        }
        if set(vars(self)) != expected or any(
            set(vars(self.trainers[arm])) != {"model", "optimizer"}
            for arm in LEARNED_ARMS
        ):
            raise B01ContractError("trainer checkpoint boundary owns unexpected live state")
        return {
            "schema": "FRRIE_B01_TRAINER_CHECKPOINT_BOUNDARY_STATE_V1",
            "owned_fields": sorted(expected),
            "no_live_episode_state": True, "no_live_native_state": True,
            "no_live_iterator_state": True, "no_mutable_rng_cursor_state": True,
            "addressed_rng_is_stateless_external_input": True,
            "complete": True,
        }


@dataclass(frozen=True, slots=True)
class SeedWorkerTask:
    seed_label: str
    invocation_binding: Mapping[str, Any]
    output_root: str
    checkpoint_root: str
    scratch_root: str


@dataclass(frozen=True, slots=True)
class PlannedFormalSeedWorkerTask:
    seed_label: str
    planned_invocation_id: str
    planned_receipt_path: str
    output_root: str
    checkpoint_root: str
    scratch_root: str


def formal_seed_worker_plan_from_manifest(
    manifest: Mapping[str, Any], planned_invocations: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    """Plan isolated formal workers without pre-creating stale admission receipts.

    This is deliberately not a launch seam.  A non-injectable formal worker
    must execute its own admit-memory command at task start and bind the fresh
    receipt before creating its output transaction, RNG, model or optimizer.
    """

    from pathlib import Path
    from .contract import validate_manifest

    manifest0 = validate_manifest(manifest)
    labels = tuple(manifest0["execution_labels"])
    if set(planned_invocations) != set(labels):
        raise B01ContractError("formal seed worker plan differs from manifest labels")
    expected_count = 3 if manifest0["phase"] == "INITIAL_001_003" else 2
    if len(labels) != expected_count:
        raise B01ContractError("seed worker phase task count differs")
    tasks = []
    invocation_ids = set()
    receipt_paths = set()
    all_roots = set()
    for label in labels:
        planned = planned_invocations[label]
        if not isinstance(planned, Mapping) or set(planned) != {
            "invocation_id", "receipt_path",
        } or not isinstance(planned["invocation_id"], str) or not planned["invocation_id"].strip():
            raise B01ContractError("formal seed planned invocation fields differ")
        receipt_path = Path(planned["receipt_path"])
        if not receipt_path.is_absolute() or receipt_path.exists():
            raise B01ContractError("formal seed receipt locator must be absolute and not yet created")
        receipt = str(receipt_path.resolve(strict=False))
        if planned["invocation_id"] in invocation_ids or receipt in receipt_paths:
            raise B01ContractError("formal seed plans require unique invocation IDs/receipt locators")
        invocation_ids.add(planned["invocation_id"])
        receipt_paths.add(receipt)
        roots = {
            name: str((Path(manifest0["roots"][name]) / label).resolve(strict=False))
            for name in ("output", "checkpoint", "scratch")
        }
        if any(path in all_roots for path in roots.values()) or len(set(roots.values())) != 3:
            raise B01ContractError("seed worker roots must be isolated")
        all_roots.update(roots.values())
        tasks.append(PlannedFormalSeedWorkerTask(
            seed_label=label, planned_invocation_id=planned["invocation_id"],
            planned_receipt_path=receipt,
            output_root=roots["output"], checkpoint_root=roots["checkpoint"],
            scratch_root=roots["scratch"],
        ))
    return {
        "schema": "FRRIE_B01_FORMAL_SEED_WORKER_PLAN_V1",
        "phase": manifest0["phase"], "capacity": 4,
        "actual_seed_task_count": expected_count, "seed_order": list(labels),
        "tasks": tuple(tasks),
        "worker_runtime_contract": {
            "admission": "WORKER_LOCAL_FRESH_ADMIT_MEMORY_BEFORE_ANY_RUNTIME_CONSTRUCTION",
            "model_optimizer": "WORKER_LOCAL_RETAINED_UNTIL_WAVE_VALIDATION",
            "torch_threads": 1, "native_width": 32,
            "output_transaction": "SEED_LOCAL_CREATE_ONCE",
            "parent_reduction": "MANIFEST_ORDER_NOT_COMPLETION_ORDER",
        },
        "launch_capable": False,
        "reason": "NONINJECTABLE_FORMAL_WORKER_RUNTIME_REQUIRED",
    }


def make_test_only_seed_worker_tasks(
    *, seed_labels: Sequence[str], invocation_bindings: Mapping[str, Any],
    roots: Mapping[str, str],
) -> tuple[SeedWorkerTask, ...]:
    """Build fixed-root TEST-only tasks for static 1/2/4 orchestration tests."""

    from pathlib import Path
    from .constants import TEST_SEED_LABELS
    from .contract import validate_invocation_binding

    labels = tuple(seed_labels)
    if len(labels) not in (2, 3) or labels != TEST_SEED_LABELS[:len(labels)]:
        raise B01ContractError("TEST seed workers require the canonical first two/three TEST labels")
    if set(invocation_bindings) != set(labels) or set(roots) != {"output", "checkpoint", "scratch"}:
        raise B01ContractError("TEST seed worker inventory/roots differ")
    tasks = []
    receipt_paths = set()
    invocation_ids = set()
    for label in labels:
        binding = validate_invocation_binding(invocation_bindings[label], require_test_only=True)
        if binding["operation"] != "TEST_SMOKE":
            raise B01ContractError("TEST seed worker invocation must be TEST_SMOKE")
        receipt = str(Path(binding["receipt_path"]).resolve(strict=True))
        if binding["invocation_id"] in invocation_ids or receipt in receipt_paths:
            raise B01ContractError("TEST seed workers require unique receipts/invocations")
        invocation_ids.add(binding["invocation_id"])
        receipt_paths.add(receipt)
        task_roots = {
            name: str((Path(roots[name]) / label).resolve(strict=False)) for name in roots
        }
        tasks.append(SeedWorkerTask(
            seed_label=label, invocation_binding=binding,
            output_root=task_roots["output"], checkpoint_root=task_roots["checkpoint"],
            scratch_root=task_roots["scratch"],
        ))
    return tuple(tasks)


def bounded_test_seed_worker_map(
    tasks: Sequence[SeedWorkerTask], *, workers: int, worker_fn: Any,
) -> dict[str, Any]:
    """Exercise TEST-only scheduling/order/failure isolation with capacity four.

    The callable seam is an internal orchestration/test seam.  Actual B01 seed
    Runtime object IDs and reported effect paths are diagnostics only; this
    injected mapper is never a formal launch authority and cannot prove object
    ownership, native topology, fresh admission, or external-effect isolation.
    """

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from pathlib import Path
    import threading

    if type(workers) is not int or workers not in (1, 2, 4):
        raise B01ContractError("seed worker equivalence topology must be 1, 2, or 4")
    rows = tuple(tasks)
    from .constants import TEST_SEED_LABELS
    if not rows or len(rows) not in (2, 3) or any(type(row) is not SeedWorkerTask for row in rows):
        raise B01ContractError("seed wave must contain exactly extension-2 or initial-3 tasks")
    labels = tuple(row.seed_label for row in rows)
    if labels != TEST_SEED_LABELS[:len(labels)]:
        raise B01ContractError("injected seed mapper is restricted to fixed TEST labels")
    active = peak = 0
    lock = threading.Lock()

    def invoke(index: int, task: SeedWorkerTask):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            return index, worker_fn(task)
        finally:
            with lock:
                active -= 1

    completed: dict[int, dict[str, Any]] = {}
    failures: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(rows)), thread_name_prefix="frrie-b01-seed") as pool:
        future_by_index = {pool.submit(invoke, index, task): index for index, task in enumerate(rows)}
        for future in as_completed(future_by_index):
            index = future_by_index[future]
            try:
                _, result = future.result()
                if not isinstance(result, Mapping) or set(result) != {
                    "seed_label", "invocation_id", "effect_paths", "runtime_identity", "payload",
                }:
                    raise B01ContractError("seed worker direct result fields differ")
                task = rows[index]
                if (
                    result["seed_label"] != task.seed_label
                    or result["invocation_id"] != task.invocation_binding["invocation_id"]
                    or not isinstance(result["effect_paths"], list)
                    or not isinstance(result["runtime_identity"], Mapping)
                    or set(result["runtime_identity"]) != {
                        "model_object_id", "optimizer_object_id", "torch_threads", "native_width",
                    }
                    or type(result["runtime_identity"]["model_object_id"]) is not int
                    or type(result["runtime_identity"]["optimizer_object_id"]) is not int
                    or result["runtime_identity"]["torch_threads"] != 1
                    or result["runtime_identity"]["native_width"] != 32
                ):
                    raise B01ContractError("seed worker identity/runtime contract differs")
                allowed = tuple(Path(path).resolve(strict=False) for path in (
                    task.output_root, task.checkpoint_root, task.scratch_root,
                ))
                for effect in result["effect_paths"]:
                    path = Path(effect).resolve(strict=False)
                    if not path.is_absolute() or not any(path == root or path.is_relative_to(root) for root in allowed):
                        raise B01ContractError("seed worker effect escaped its isolated roots")
                completed[index] = dict(result)
            except Exception as error:
                failures[index] = f"{type(error).__name__}: {error}"
    ordered = []
    for index, task in enumerate(rows):
        if index in completed:
            ordered.append({"seed_label": task.seed_label, "status": "COMPLETE", **completed[index]})
        else:
            ordered.append({
                "seed_label": task.seed_label, "invocation_id": task.invocation_binding["invocation_id"],
                "status": "INCOMPLETE_QUARANTINE_REQUIRED", "error": failures[index],
            })
    return {
        "schema": "FRRIE_B01_TEST_ONLY_BOUNDED_SEED_WORKER_MAP_V1",
        "capacity": 4, "requested_workers": workers,
        "actual_worker_ceiling": min(workers, len(rows)), "observed_peak_active_workers": peak,
        "seed_order": list(labels), "rows": ordered,
        "completed_seed_count": len(completed), "failed_seed_count": len(failures),
        "duplicate_launches": 0, "manifest_order_preserved": True,
        "per_seed_torch_threads": 1, "per_seed_native_width": 32,
        "runtime_object_ids_authoritative": False,
        "effect_path_reports_authoritative": False,
        "formal_launch_capable": False,
        "performance_readiness_from_static_orchestration": False,
    }


def manifest_bound_paired_update_component(
    *, paired_trainer: PairedB01Trainer, adapter: object,
    tapes: Sequence[Any], origins: Sequence[Sequence[Any]], update: int,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Collect and atomically update both arms through the formal collector API.

    This is the manifest-bound semantic component used *inside* the formal
    runner after source/admission and canonical native-loader gates.  It is not
    itself a public launch seam: the adapter and live trainer are accepted only
    from that enclosing runner, and this function never mints a panel token.
    In particular it calls the public production collector with the complete
    validated manifest; it never calls the TEST-only label wrapper or supplies
    a caller-chosen allowed-label list.
    """

    from .batch_collector import collect_b01_arm_update
    from .contract import validate_manifest

    manifest0 = validate_manifest(manifest)
    if type(paired_trainer) is not PairedB01Trainer:
        raise B01ContractError("formal paired component requires PairedB01Trainer")
    if type(update) is not int or not 1 <= update <= UPDATES:
        raise B01ContractError("formal paired component update lies outside [1,512]")
    collections = {
        arm: collect_b01_arm_update(
            model=paired_trainer.models[arm], adapter=adapter,
            tapes=tapes, origins=origins, update=update, manifest=manifest0,
        )
        for arm in LEARNED_ARMS
    }
    receipts = paired_trainer.update(
        {arm: row.batch for arm, row in collections.items()}, update=update,
    )
    audits = {arm: row.audit for arm, row in collections.items()}
    if any(
        audit.total_environment_slots != 4_928
        or audit.factual_slots != 768
        or audit.factual_suffix_audit_slots != 1_248
        or audit.nonfactual_suffix_slots != 2_912
        for audit in audits.values()
    ):
        raise B01ContractError("formal paired component direct work partition differs")
    return {
        "schema": "FRRIE_B01_MANIFEST_BOUND_PAIRED_UPDATE_COMPONENT_V1",
        "seed_label": tapes[0].seed_block if tapes else None,
        "update": update, "arm_audits": audits, "arm_update_receipts": receipts,
        "scientific_training_work_per_arm": 4_928,
        "manifest_execution_labels": list(manifest0["execution_labels"]),
        "formal_top_gates_required": [
            "ACTUAL_SOURCE_GATE", "FRESH_INVOCATION_ADMISSION",
            "CANONICAL_PACKAGE_NATIVE_LOADER", "PROCESS_TREE_TELEMETRY",
            "CHECKPOINT_AND_PANEL_TRANSACTION",
        ],
        "production_token_minted": False,
    }


def direct_training_loss_reduction_array_contract() -> dict[str, tuple[str, tuple[int, ...]]]:
    """Production 512-update storage axes for exact loss reduction provenance."""

    return {
        "loss_episode_component_bits": ("<u4", (UPDATES, 64, 4)),
        "loss_aggregate_bits": ("<u4", (UPDATES, 4)),
    }


def validate_direct_training_shard(value: Any) -> dict[str, Any]:
    """Stream the exact 512-update model/Adam/projection receipt for one arm/seed."""

    import math
    from pathlib import Path
    import numpy as np
    from ..arms import LAYER_SHAPES, PARAMETER_BYTE_COUNT, PROJECTION_BOXES, LearnedArm
    from ..state_codec import OPTIMIZER_STATE_BYTE_COUNT, decode_optimizer_state

    descriptor_fields = {"path", "dtype", "shape", "order", "byte_count"}

    def mmap(descriptor: Any, *, dtype: str, shape: tuple[int, ...], name: str):
        if not isinstance(descriptor, Mapping) or set(descriptor) != descriptor_fields:
            raise B01ContractError(f"training {name} descriptor fields differ")
        path = Path(descriptor["path"])
        expected = math.prod(shape) * np.dtype(dtype).itemsize
        if (
            not path.is_absolute() or descriptor["dtype"] != dtype
            or descriptor["shape"] != list(shape) or descriptor["order"] != "C"
            or descriptor["byte_count"] != expected
        ):
            raise B01ContractError(f"training {name} dtype/shape/byte contract differs")
        try:
            if path.stat().st_size != expected:
                raise B01ContractError(f"training {name} persisted byte length differs")
            return np.memmap(path, dtype=dtype, mode="r", shape=shape, order="C")
        except OSError as error:
            raise B01ContractError(f"training {name} raw bytes are unreadable") from error

    fields = {
        "schema", "seed_label", "arm", "coordinate_order", "array_shards",
        "state_blobs", "work_contract", "loss_reduction_contract", "complete",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("direct training shard fields differ")
    shard = dict(value)
    arm = shard["arm"]
    if (
        shard["schema"] != "FRRIE_B01_DIRECT_TRAINING_SHARD_V1"
        or not isinstance(shard["seed_label"], str) or not shard["seed_label"]
        or arm not in LEARNED_ARMS or shard["coordinate_order"] != ["update_1_512"]
        or shard["loss_reduction_contract"] != exact_loss_reduction_contract()
        or shard["complete"] is not True
    ):
        raise B01ContractError("direct training shard identity differs")
    expected_work = {
        "per_update": {
            "factual": TRAIN_FACTUAL_WORK_PER_ARM_SEED // UPDATES,
            "seven_nonfactual_alternatives": TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED // UPDATES,
            "three_audits": TRAIN_AUDIT_WORK_PER_ARM_SEED // UPDATES,
            "total": TRAIN_TOTAL_WORK_PER_ARM_SEED // UPDATES,
        },
        "per_arm_seed": {
            "factual": TRAIN_FACTUAL_WORK_PER_ARM_SEED,
            "seven_nonfactual_alternatives": TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED,
            "three_audits": TRAIN_AUDIT_WORK_PER_ARM_SEED,
            "total": TRAIN_TOTAL_WORK_PER_ARM_SEED,
        },
        "raw_native_call_counts": "RECORDED_NOT_FROZEN",
    }
    if shard["work_contract"] != expected_work:
        raise B01ContractError("direct training work contract differs")
    array_contract = {
        "beta_pre_bits": ("<u4", (UPDATES, 18)),
        "beta_post_adam_bits": ("<u4", (UPDATES, 18)),
        "beta_post_projection_bits": ("<u4", (UPDATES, 18)),
        "loss_terms": ("<f4", (UPDATES, 5)),
        **direct_training_loss_reduction_array_contract(),
        "changed_mask": ("|u1", (UPDATES, 18)),
        "box_contact": ("|u1", (UPDATES,)),
        "maximum_box_overshoot": ("<f8", (UPDATES,)),
        "projection_l1_displacement": ("<f8", (UPDATES,)),
        "optimizer_moments_unchanged": ("|u1", (UPDATES,)),
        "work": ("<u4", (UPDATES, 4)),
        "raw_native_calls": ("<u4", (UPDATES, 3)),
    }
    blob_contract = {
        "model_pre": ("|u1", (UPDATES, PARAMETER_BYTE_COUNT)),
        "model_post_adam": ("|u1", (UPDATES, PARAMETER_BYTE_COUNT)),
        "model_post_projection": ("|u1", (UPDATES, PARAMETER_BYTE_COUNT)),
        "optimizer_pre": ("|u1", (UPDATES, OPTIMIZER_STATE_BYTE_COUNT)),
        "optimizer_post_adam": ("|u1", (UPDATES, OPTIMIZER_STATE_BYTE_COUNT)),
        "optimizer_post_projection": ("|u1", (UPDATES, OPTIMIZER_STATE_BYTE_COUNT)),
    }
    if not isinstance(shard["array_shards"], Mapping) or set(shard["array_shards"]) != set(array_contract):
        raise B01ContractError("direct training scalar array inventory differs")
    if not isinstance(shard["state_blobs"], Mapping) or set(shard["state_blobs"]) != set(blob_contract):
        raise B01ContractError("direct training state blob inventory differs")
    arrays = {
        name: mmap(shard["array_shards"][name], dtype=dtype, shape=shape, name=name)
        for name, (dtype, shape) in array_contract.items()
    }
    blobs = {
        name: mmap(shard["state_blobs"][name], dtype=dtype, shape=shape, name=name)
        for name, (dtype, shape) in blob_contract.items()
    }
    beta_offset = 4 * sum(math.prod(shape) for name, shape in LAYER_SHAPES if name != "beta")
    # beta is interleaved before critic; calculate its actual prefix, not total non-beta size.
    beta_offset = 0
    for name, shape in LAYER_SHAPES:
        if name == "beta":
            break
        beta_offset += 4 * math.prod(shape)
    beta_stop = beta_offset + 18 * 4
    low, high = PROJECTION_BOXES[arm]
    first_contact = None
    displacements: list[float] = []
    maximum_overshoot = 0.0
    previous_model = previous_optimizer = None
    for index in range(UPDATES):
        update = index + 1
        state_bytes = {
            name: bytes(blobs[name][index]) for name in blob_contract
        }
        for name in ("model_pre", "model_post_adam", "model_post_projection"):
            LearnedArm.from_parameter_bytes(arm, state_bytes[name])
        if previous_model is not None and (
            state_bytes["model_pre"] != previous_model
            or state_bytes["optimizer_pre"] != previous_optimizer
        ):
            raise B01ContractError("direct training consecutive state chain differs")
        if decode_optimizer_state(state_bytes["optimizer_pre"]).step != update - 1 or (
            decode_optimizer_state(state_bytes["optimizer_post_adam"]).step != update
            or decode_optimizer_state(state_bytes["optimizer_post_projection"]).step != update
        ):
            raise B01ContractError("direct training Adam step frontier differs")
        if state_bytes["optimizer_post_adam"] != state_bytes["optimizer_post_projection"] or int(
            arrays["optimizer_moments_unchanged"][index]
        ) != 1:
            raise B01ContractError("projection changed Adam moment bytes")
        pre_bits = np.frombuffer(
            state_bytes["model_pre"][beta_offset:beta_stop], dtype="<u4",
        )
        adam_bits = np.frombuffer(
            state_bytes["model_post_adam"][beta_offset:beta_stop], dtype="<u4",
        )
        projected_bits = np.frombuffer(
            state_bytes["model_post_projection"][beta_offset:beta_stop], dtype="<u4",
        )
        if not np.array_equal(pre_bits, arrays["beta_pre_bits"][index]) or not np.array_equal(
            adam_bits, arrays["beta_post_adam_bits"][index],
        ) or not np.array_equal(projected_bits, arrays["beta_post_projection_bits"][index]):
            raise B01ContractError("direct training beta literal bits differ from model bytes")
        before = adam_bits.view("<f4")
        after = projected_bits.view("<f4")
        wanted = np.clip(before, np.float32(low), np.float32(high)).astype("<f4")
        if wanted.tobytes() != after.tobytes():
            raise B01ContractError("direct training projection differs from exact box clip")
        if (
            state_bytes["model_post_adam"][:beta_offset]
            + state_bytes["model_post_adam"][beta_stop:]
            != state_bytes["model_post_projection"][:beta_offset]
            + state_bytes["model_post_projection"][beta_stop:]
        ):
            raise B01ContractError("projection changed non-beta model bytes")
        changed = adam_bits != projected_bits
        if not np.array_equal(changed.astype(np.uint8), arrays["changed_mask"][index]) or int(
            arrays["box_contact"][index]
        ) != int(changed.any()):
            raise B01ContractError("direct training projection contact mask differs")
        overshoot = max(
            max((float(low) - float(item) for item in before), default=0.0),
            max((float(item) - float(high) for item in before), default=0.0),
            0.0,
        )
        displacement = math.fsum(abs(float(a) - float(b)) for a, b in zip(after, before))
        if float(arrays["maximum_box_overshoot"][index]).hex() != float(overshoot).hex() or float(
            arrays["projection_l1_displacement"][index]
        ).hex() != float(displacement).hex():
            raise B01ContractError("direct training projection movement scalars differ")
        if changed.any() and first_contact is None:
            first_contact = update
        maximum_overshoot = max(maximum_overshoot, overshoot)
        displacements.append(displacement)
        terms = arrays["loss_terms"][index]
        if not np.isfinite(terms).all():
            raise B01ContractError("direct training loss scalars are nonfinite")
        reduction = {
            "schema": "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
            "component_order": ["loss", "score", "entropy", "critic"],
            "roster_order": exact_loss_reduction_contract()["roster_order"],
            "per_episode_u32_bits": arrays[
                "loss_episode_component_bits"
            ][index].astype("<u4", copy=False).tolist(),
            "reduction_law": exact_loss_reduction_contract()["reduction_law"],
            "divisor": 64, "dtype": "CPU_FP32",
            "aggregate_u32_bits": arrays["loss_aggregate_bits"][index].tolist(),
        }
        try:
            validate_loss_reduction_receipt(
                reduction,
                aggregate_scalars={
                    name: float(terms[position])
                    for position, name in enumerate(("loss", "score", "entropy", "critic"))
                },
            )
        except ContractError as error:
            raise B01ContractError("direct training loss reduction provenance differs") from error
        if not np.array_equal(
            arrays["work"][index],
            np.asarray([768, 2_912, 1_248, 4_928], dtype="<u4"),
        ):
            raise B01ContractError("direct training per-update work partition differs")
        previous_model = state_bytes["model_post_projection"]
        previous_optimizer = state_bytes["optimizer_post_projection"]
    return {
        "schema": "FRRIE_B01_VALIDATED_TRAINING_COMPONENT_V1",
        "seed_label": shard["seed_label"], "arm": arm,
        "updates": UPDATES, "first_box_contact_update": first_contact,
        "maximum_box_overshoot": maximum_overshoot,
        "cumulative_projection_l1": math.fsum(displacements),
        "work": expected_work, "raw_native_calls_recorded_not_frozen": True,
        "raw_native_call_ledger": {
            "reset_calls": int(arrays["raw_native_calls"][:, 0].sum(dtype=np.uint64)),
            "observe_calls": int(arrays["raw_native_calls"][:, 1].sum(dtype=np.uint64)),
            "step_calls": int(arrays["raw_native_calls"][:, 2].sum(dtype=np.uint64)),
        },
        "state_chain_revalidated": True, "production_token_minted": False,
    }


def validate_paired_training_shards(value: Mapping[str, Any]) -> dict[str, Any]:
    """Cross-arm direct state/contact/distance component; replay remains separate."""

    import math
    from pathlib import Path
    import numpy as np
    from ..arms import PARAMETER_BYTE_COUNT
    from ..state_codec import OPTIMIZER_STATE_BYTE_COUNT

    if not isinstance(value, Mapping) or set(value) != set(LEARNED_ARMS):
        raise B01ContractError("paired training component requires both arm shards")
    components = {arm: validate_direct_training_shard(value[arm]) for arm in LEARNED_ARMS}
    if components["PHY_TRUST"]["seed_label"] != components["EDGE_FLEX"]["seed_label"]:
        raise B01ContractError("paired training seed identities differ")

    def mapped(arm: str, group: str, name: str, dtype: str, shape: tuple[int, ...]):
        descriptor = value[arm][group][name]
        path = Path(descriptor["path"])
        return np.memmap(path, dtype=dtype, mode="r", shape=shape, order="C")

    model_stages = {
        name: {
            arm: mapped(arm, "state_blobs", name, "|u1", (UPDATES, PARAMETER_BYTE_COUNT))
            for arm in LEARNED_ARMS
        }
        for name in ("model_pre", "model_post_adam", "model_post_projection")
    }
    optimizer_stages = {
        name: {
            arm: mapped(
                arm, "state_blobs", name, "|u1", (UPDATES, OPTIMIZER_STATE_BYTE_COUNT),
            )
            for arm in LEARNED_ARMS
        }
        for name in ("optimizer_pre", "optimizer_post_adam", "optimizer_post_projection")
    }
    changed = mapped("PHY_TRUST", "array_shards", "changed_mask", "|u1", (UPDATES, 18))
    edge_contact = mapped("EDGE_FLEX", "array_shards", "box_contact", "|u1", (UPDATES,))
    kappa = components["PHY_TRUST"]["first_box_contact_update"]
    beta_offset = 0
    from ..arms import LAYER_SHAPES
    for name, shape in LAYER_SHAPES:
        if name == "beta":
            break
        beta_offset += 4 * math.prod(shape)
    beta_stop = beta_offset + 18 * 4
    _validate_paired_stage_equality(
        model_stages=model_stages, optimizer_stages=optimizer_stages,
        kappa=kappa, beta_offset=beta_offset, beta_stop=beta_stop, updates=UPDATES,
    )
    contacted = tuple(int(index) for index in np.flatnonzero(changed.any(axis=0)))
    return {
        "schema": "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1",
        "seed_label": components["PHY_TRUST"]["seed_label"], "kappa": kappa,
        "phy_contacted_coordinate_indices": list(contacted),
        "phy_contacted_coordinate_count": len(contacted),
        "edge_wide_contact": bool(edge_contact.any()),
        "parameter_distance_contract_status": "PRO_FINAL_RAW_RECORDS_REQUIRED",
        "parameter_distance_state_stage": "POSTPROJECTION",
        "parameter_distance_required_updates": (
            [] if kappa is None else list(range(kappa, UPDATES + 1))
        ),
        "parameter_distance_raw_records": None,
        "raw_native_call_ledger_by_arm": {
            arm: components[arm]["raw_native_call_ledger"] for arm in LEARNED_ARMS
        },
        "precontact_and_contact_prestate_equal": True,
        "training_validation_replay_complete": False,
        "production_token_minted": False,
    }


def exact_parameter_layout() -> dict[str, Any]:
    """Return the Pro-frozen canonical little-endian FP32 parameter layout."""

    import math
    from ..arms import LAYER_SHAPES, PARAMETER_BYTE_COUNT

    tensor_order = [
        {"name": name, "shape": list(shape)} for name, shape in LAYER_SHAPES
    ]
    if (
        sum(math.prod(row["shape"]) for row in tensor_order) != MODEL_PARAMETERS
        or PARAMETER_BYTE_COUNT != 142_052
    ):
        raise B01ContractError("actual learned-arm layout differs from Pro parameter contract")
    return {
        "schema": PARAMETER_DISTANCE_LAYOUT_SCHEMA,
        "parameter_count": MODEL_PARAMETERS,
        "parameter_byte_count": PARAMETER_BYTE_COUNT,
        "dtype": "IEEE754_BINARY32", "byte_order": "LITTLE_ENDIAN",
        "tensor_flattening": "C_ORDER", "tensor_order": tensor_order,
        "beta_flat_start": PARAMETER_DISTANCE_BETA_FLAT_START,
        "beta_flat_end_exclusive": PARAMETER_DISTANCE_BETA_FLAT_END,
        "beta_byte_start": PARAMETER_DISTANCE_BETA_BYTE_START,
        "beta_byte_end_exclusive": PARAMETER_DISTANCE_BETA_BYTE_END,
    }


def _u64_bits(value: float) -> int:
    import struct
    return struct.unpack("<Q", struct.pack("<d", float(value)))[0]


def _parameter_distance_from_state_pair(
    phy_bytes: bytes, edge_bytes: bytes,
) -> dict[str, Any]:
    """Direct Pro-frozen signed-f64/L-infinity decomposition for one update."""

    import numpy as np
    from ..arms import PARAMETER_BYTE_COUNT

    if (
        type(phy_bytes) is not bytes or type(edge_bytes) is not bytes
        or len(phy_bytes) != PARAMETER_BYTE_COUNT
        or len(edge_bytes) != PARAMETER_BYTE_COUNT
    ):
        raise B01ContractError("parameter-distance arm state must be exactly 142052 bytes")
    phy = np.frombuffer(phy_bytes, dtype="<f4")
    edge = np.frombuffer(edge_bytes, dtype="<f4")
    if not np.isfinite(phy).all() or not np.isfinite(edge).all():
        return {
            "available": False,
            "availability_reason": "PARAMETER_DISTANCE_NONFINITE_RECORD",
        }
    # Conversion from binary32 to binary64 is exact; NumPy's binary64
    # subtraction uses the host IEEE-754 round-to-nearest-even operation.
    signed = phy.astype("<f8") - edge.astype("<f8")
    if not np.isfinite(signed).all():
        return {
            "available": False,
            "availability_reason": "PARAMETER_DISTANCE_NONFINITE_RECORD",
        }
    absolute = np.abs(signed)
    beta = absolute[
        PARAMETER_DISTANCE_BETA_FLAT_START:PARAMETER_DISTANCE_BETA_FLAT_END
    ]
    nonbeta = np.concatenate((
        absolute[:PARAMETER_DISTANCE_BETA_FLAT_START],
        absolute[PARAMETER_DISTANCE_BETA_FLAT_END:],
    ))
    full_index = int(np.argmax(absolute))
    beta_relative = int(np.argmax(beta))
    nonbeta_relative = int(np.argmax(nonbeta))
    nonbeta_index = (
        nonbeta_relative
        if nonbeta_relative < PARAMETER_DISTANCE_BETA_FLAT_START
        else nonbeta_relative + (
            PARAMETER_DISTANCE_BETA_FLAT_END - PARAMETER_DISTANCE_BETA_FLAT_START
        )
    )
    full = float(absolute[full_index])
    beta_max = float(beta[beta_relative])
    nonbeta_max = float(nonbeta[nonbeta_relative])
    return {
        "available": True, "availability_reason": None,
        "signed_difference_f64_le_bytes": signed.astype("<f8", copy=False).tobytes(order="C"),
        "derived": {
            "linf_full_binary64_bits_u64": _u64_bits(full),
            "linf_beta_binary64_bits_u64": _u64_bits(beta_max),
            "linf_nonbeta_binary64_bits_u64": _u64_bits(nonbeta_max),
            "full_parameter_bytes_equal": phy_bytes == edge_bytes,
            "first_argmax_full_flat_index": full_index,
            "first_argmax_beta_flat_index": (
                PARAMETER_DISTANCE_BETA_FLAT_START + beta_relative
            ),
            "first_argmax_nonbeta_flat_index": nonbeta_index,
        },
    }


def _resolve_parameter_state_binding(
    binding: Any, *, seed_label: str, update: int, arm: str,
    manifest: Mapping[str, Any] | None,
) -> bytes:
    import base64
    import binascii
    import json
    from pathlib import Path
    import numpy as np
    from ..arms import LearnedArm, PARAMETER_BYTE_COUNT
    from ..contracts.core import ContractError
    from .constants import CHECKPOINT_SCHEMA, TEST_CHECKPOINT_SCHEMA

    common = {
        "binding_kind", "seed_block", "training_update", "arm_id",
        "decoded_parameter_byte_count", "state_stage",
    }
    if not isinstance(binding, Mapping) or not common.issubset(binding):
        raise B01ContractError("parameter-distance state binding fields differ")
    if (
        binding["seed_block"] != seed_label or binding["training_update"] != update
        or binding["arm_id"] != arm
        or binding["decoded_parameter_byte_count"] != PARAMETER_BYTE_COUNT
        or binding["state_stage"] != "POSTPROJECTION"
    ):
        raise B01ContractError("parameter-distance state binding coordinate differs")
    if binding["binding_kind"] == "INLINE_PARAMETER_BYTES":
        if set(binding) != common | {"parameter_bytes_b64"}:
            raise B01ContractError("inline parameter-distance binding fields differ")
        try:
            state = base64.b64decode(binding["parameter_bytes_b64"], validate=True)
        except (TypeError, ValueError, binascii.Error) as error:
            raise B01ContractError("inline parameter-distance bytes are malformed") from error
    elif binding["binding_kind"] == "IMMUTABLE_STATE_REF":
        required = common | {"container_schema", "container_path", "field"}
        if set(binding) != required or binding["field"] != "arm_state_bytes":
            raise B01ContractError("immutable parameter-distance binding fields differ")
        path = Path(binding["container_path"])
        if not path.is_absolute():
            raise B01ContractError("parameter-distance container path must be absolute")
        if binding["container_schema"] == PARAMETER_DISTANCE_STATE_SCHEMA:
            try:
                index = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise B01ContractError("parameter-distance state container is unreadable") from error
            expected_fields = {
                "schema", "seed_block", "training_update", "state_stage",
                "arm_files", "decoded_parameter_byte_count", "resume_or_evaluation_capable",
                "complete",
            }
            if (
                not isinstance(index, Mapping) or set(index) != expected_fields
                or index["schema"] != PARAMETER_DISTANCE_STATE_SCHEMA
                or index["seed_block"] != seed_label or index["training_update"] != update
                or index["state_stage"] != "POSTPROJECTION"
                or index["decoded_parameter_byte_count"] != PARAMETER_BYTE_COUNT
                or index["resume_or_evaluation_capable"] is not False
                or index["complete"] is not True
                or index["arm_files"] != {
                    "PHY_TRUST": "PHY_TRUST.f32", "EDGE_FLEX": "EDGE_FLEX.f32",
                }
            ):
                raise B01ContractError("parameter-distance state container identity differs")
            state_path = path.parent / index["arm_files"][arm]
            if state_path.parent.resolve(strict=False) != path.parent.resolve(strict=False):
                raise B01ContractError("parameter-distance state file escaped its container")
            try:
                state = state_path.read_bytes()
            except OSError as error:
                raise B01ContractError("parameter-distance state bytes are unreadable") from error
        elif binding["container_schema"] in {CHECKPOINT_SCHEMA, TEST_CHECKPOINT_SCHEMA}:
            if manifest is None:
                raise B01ContractError("checkpoint parameter binding requires its exact manifest")
            from .checkpoint import decode_checkpoint
            try:
                data = path.read_bytes()
            except OSError as error:
                raise B01ContractError("parameter-distance checkpoint is unreadable") from error
            decoded = decode_checkpoint(
                data, manifest=manifest, expected_seed_label=seed_label,
                expected_update=update,
                expected_test_only=(binding["container_schema"] == TEST_CHECKPOINT_SCHEMA),
            )
            state = decoded["arm_state_bytes"][arm]
        else:
            raise B01ContractError("parameter-distance state container schema differs")
    else:
        raise B01ContractError("parameter-distance binding kind differs")
    if len(state) != PARAMETER_BYTE_COUNT:
        raise B01ContractError("parameter-distance state byte count differs")
    if not np.isfinite(np.frombuffer(state, dtype="<f4")).all():
        raise _ParameterDistanceNonfinite("parameter-distance source contains NaN or infinity")
    try:
        LearnedArm.from_parameter_bytes(arm, state)
    except ContractError as error:
        raise B01ContractError("parameter-distance source is not the canonical model layout") from error
    return state


def _validate_parameter_distance_raw_record_core(
    value: Any, *, manifest: Mapping[str, Any] | None = None,
    test_only_component: bool = False, expected_kappa: int | None = None,
) -> dict[str, Any]:
    """Recompute one post-contact parameter diagnostic from authoritative states."""

    fields = {
        "schema", "seed_block", "training_update", "first_tight_contact_update",
        "available", "state_stage", "capture_boundary", "parameter_layout",
        "phy_state_binding", "edge_state_binding", "derived",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("parameter-distance raw record fields differ")
    row = dict(value)
    update = row["training_update"]
    kappa = row["first_tight_contact_update"]
    if manifest is None:
        from .constants import TEST_SEED_LABELS
        if test_only_component is not True or row["seed_block"] not in TEST_SEED_LABELS:
            raise B01ContractError(
                "parameter-distance record without manifest is restricted to explicit TEST labels"
            )
    else:
        from .contract import validate_manifest
        manifest0 = validate_manifest(manifest)
        if row["seed_block"] not in manifest0["execution_labels"]:
            raise B01ContractError("parameter-distance seed is outside manifest execution labels")
    if (
        row["schema"] != PARAMETER_DISTANCE_RAW_SCHEMA
        or not isinstance(row["seed_block"], str) or not row["seed_block"]
        or type(update) is not int or not 1 <= update <= UPDATES
        or type(kappa) is not int or not 1 <= kappa <= update
        or row["available"] is not True or row["state_stage"] != "POSTPROJECTION"
        or row["capture_boundary"]
        != "AFTER_ADAM_AND_ARM_PROJECTION_BEFORE_NEXT_MODEL_MUTATION"
        or row["parameter_layout"] != exact_parameter_layout()
    ):
        raise B01ContractError("parameter-distance raw record identity differs")
    if expected_kappa is not None and kappa != expected_kappa:
        raise B01ContractError("parameter-distance raw κ differs from derived paired training κ")
    expected_derived_fields = {
        "linf_full_binary64_bits_u64", "linf_beta_binary64_bits_u64",
        "linf_nonbeta_binary64_bits_u64", "full_parameter_bytes_equal",
        "first_argmax_full_flat_index", "first_argmax_beta_flat_index",
        "first_argmax_nonbeta_flat_index",
    }
    if not isinstance(row["derived"], Mapping) or set(row["derived"]) != expected_derived_fields:
        raise B01ContractError("parameter-distance derived fields differ")
    try:
        phy = _resolve_parameter_state_binding(
            row["phy_state_binding"], seed_label=row["seed_block"], update=update,
            arm="PHY_TRUST", manifest=manifest,
        )
        edge = _resolve_parameter_state_binding(
            row["edge_state_binding"], seed_label=row["seed_block"], update=update,
            arm="EDGE_FLEX", manifest=manifest,
        )
    except _ParameterDistanceNonfinite as error:
        return {
            "schema": "FRRIE_B01_VALIDATED_PARAMETER_DISTANCE_RECORD_V1",
            "seed_block": row["seed_block"], "training_update": update,
            "first_tight_contact_update": kappa, "available": False,
            "availability_reason": "PARAMETER_DISTANCE_NONFINITE_RECORD",
            "diagnostic_error": str(error), "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
            "included_in_ordered_28": False, "production_gate": False,
        }
    except B01ContractError as error:
        return {
            "schema": "FRRIE_B01_VALIDATED_PARAMETER_DISTANCE_RECORD_V1",
            "seed_block": row["seed_block"], "training_update": update,
            "first_tight_contact_update": kappa, "available": False,
            "availability_reason": "PARAMETER_DISTANCE_MEASUREMENT_DEFECT",
            "diagnostic_error": str(error), "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
            "included_in_ordered_28": False, "production_gate": False,
        }
    direct = _parameter_distance_from_state_pair(phy, edge)
    if not direct["available"]:
        return {
            "schema": "FRRIE_B01_VALIDATED_PARAMETER_DISTANCE_RECORD_V1",
            "seed_block": row["seed_block"], "training_update": update,
            "first_tight_contact_update": kappa, "available": False,
            "availability_reason": direct["availability_reason"],
            "diagnostic_error": "nonfinite source or derived binary64 value",
            "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
            "included_in_ordered_28": False, "production_gate": False,
        }
    if dict(row["derived"]) != direct["derived"]:
        return {
            "schema": "FRRIE_B01_VALIDATED_PARAMETER_DISTANCE_RECORD_V1",
            "seed_block": row["seed_block"], "training_update": update,
            "first_tight_contact_update": kappa, "available": False,
            "availability_reason": "PARAMETER_DISTANCE_MEASUREMENT_DEFECT",
            "diagnostic_error": "stored derived bits differ from direct state recomputation",
            "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
            "included_in_ordered_28": False, "production_gate": False,
        }
    return {
        "schema": "FRRIE_B01_VALIDATED_PARAMETER_DISTANCE_RECORD_V1",
        "seed_block": row["seed_block"], "training_update": update,
        "first_tight_contact_update": kappa, "available": True,
        "availability_reason": None, "derived": direct["derived"],
        "signed_difference_f64_le_bytes": direct["signed_difference_f64_le_bytes"],
        "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
        "included_in_ordered_28": False, "production_gate": False,
    }


def validate_parameter_distance_raw_record(
    value: Any, *, manifest: Mapping[str, Any] | None = None,
    test_only_component: bool = False,
) -> dict[str, Any]:
    """Explicit TEST/component raw validator; caller κ is never formal authority."""

    if manifest is not None:
        raise B01ContractError(
            "formal parameter-distance raw validation requires paired-shard-derived κ"
        )
    return _validate_parameter_distance_raw_record_core(
        value, manifest=None, test_only_component=test_only_component,
        expected_kappa=None,
    )


def create_paired_parameter_state_container_once(
    root: str | Any, *, seed_label: str, update: int,
    phy_state_bytes: bytes, edge_state_bytes: bytes,
    manifest: Mapping[str, Any] | None = None, test_only_component: bool = False,
) -> dict[str, Any]:
    """Atomically retain symmetric non-checkpoint diagnostic state blobs."""

    import json
    import os
    from pathlib import Path
    from ..arms import LearnedArm, PARAMETER_BYTE_COUNT

    if manifest is None:
        from .constants import TEST_SEED_LABELS
        if test_only_component is not True or seed_label not in TEST_SEED_LABELS:
            raise B01ContractError(
                "parameter-distance state write without manifest is restricted to TEST labels"
            )
    else:
        from .contract import validate_manifest
        manifest0 = validate_manifest(manifest)
        if seed_label not in manifest0["execution_labels"]:
            raise B01ContractError("parameter-distance state seed is outside manifest labels")
    target = Path(root).resolve(strict=False)
    staging = target.with_name(target.name + ".creating")
    incomplete = target.with_name(target.name + ".incomplete")
    if not target.is_absolute() or target.exists() or staging.exists() or incomplete.exists():
        raise B01ContractError("parameter-distance state container root is not fresh")
    if type(update) is not int or not 1 <= update <= UPDATES:
        raise B01ContractError("parameter-distance state update lies outside [1,512]")
    states = {"PHY_TRUST": phy_state_bytes, "EDGE_FLEX": edge_state_bytes}
    for arm, state in states.items():
        if type(state) is not bytes or len(state) != PARAMETER_BYTE_COUNT:
            raise B01ContractError("parameter-distance state blob byte count differs")
        LearnedArm.from_parameter_bytes(arm, state)
    staging.mkdir(parents=True, exist_ok=False)
    published_by_this_transaction = False
    try:
        files = {}
        for arm, state in states.items():
            name = f"{arm}.f32"
            path = staging / name
            with path.open("xb") as stream:
                stream.write(state)
                stream.flush()
                os.fsync(stream.fileno())
            files[arm] = name
        index = {
            "schema": PARAMETER_DISTANCE_STATE_SCHEMA,
            "seed_block": seed_label, "training_update": update,
            "state_stage": "POSTPROJECTION", "arm_files": files,
            "decoded_parameter_byte_count": PARAMETER_BYTE_COUNT,
            "resume_or_evaluation_capable": False, "complete": True,
        }
        with (staging / "index.json").open("xb") as stream:
            stream.write(canonical_json_bytes(index))
            stream.flush()
            os.fsync(stream.fileno())
        staging.replace(target)
        published_by_this_transaction = True
        import json
        literal = json.loads((target / "index.json").read_text(encoding="utf-8"))
        if literal != index:
            raise B01ContractError("parameter-distance state literal index readback differs")
        container_path = str((target / "index.json").resolve(strict=True))
        for arm in LEARNED_ARMS:
            _resolve_parameter_state_binding({
                "binding_kind": "IMMUTABLE_STATE_REF",
                "container_schema": PARAMETER_DISTANCE_STATE_SCHEMA,
                "container_path": container_path, "seed_block": seed_label,
                "training_update": update, "arm_id": arm, "field": "arm_state_bytes",
                "decoded_parameter_byte_count": PARAMETER_BYTE_COUNT,
                "state_stage": "POSTPROJECTION",
            }, seed_label=seed_label, update=update, arm=arm, manifest=None)
    except BaseException:
        if staging.exists() and not incomplete.exists():
            staging.replace(incomplete)
        elif published_by_this_transaction and target.exists() and not incomplete.exists():
            target.replace(incomplete)
        raise
    container_path = str((target / "index.json").resolve(strict=True))
    bindings = {
        arm: {
            "binding_kind": "IMMUTABLE_STATE_REF",
            "container_schema": PARAMETER_DISTANCE_STATE_SCHEMA,
            "container_path": container_path, "seed_block": seed_label,
            "training_update": update, "arm_id": arm, "field": "arm_state_bytes",
            "decoded_parameter_byte_count": PARAMETER_BYTE_COUNT,
            "state_stage": "POSTPROJECTION",
        }
        for arm in LEARNED_ARMS
    }
    return {
        "schema": PARAMETER_DISTANCE_STATE_SCHEMA,
        "container_path": container_path, "bindings": bindings,
        "complete": True, "scientific_work_added": 0,
        "resume_or_evaluation_capable": False,
    }


def parameter_distance_raw_record_from_bindings(
    *, seed_label: str, update: int, first_tight_contact_update: int,
    phy_state_binding: Mapping[str, Any], edge_state_binding: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None, test_only_component: bool = False,
) -> dict[str, Any]:
    """Construct one exact raw record from two already-immutable state bindings."""

    if manifest is not None:
        raise B01ContractError(
            "formal parameter-distance raw creation requires paired-shard-derived κ"
        )

    try:
        phy = _resolve_parameter_state_binding(
            phy_state_binding, seed_label=seed_label, update=update,
            arm="PHY_TRUST", manifest=manifest,
        )
        edge = _resolve_parameter_state_binding(
            edge_state_binding, seed_label=seed_label, update=update,
            arm="EDGE_FLEX", manifest=manifest,
        )
    except _ParameterDistanceNonfinite as error:
        return {
            "schema": "FRRIE_B01_PARAMETER_DISTANCE_UNAVAILABLE_V1",
            "seed_block": seed_label, "training_update": update,
            "first_tight_contact_update": first_tight_contact_update,
            "available": False,
            "availability_reason": "PARAMETER_DISTANCE_NONFINITE_RECORD",
            "diagnostic_error": str(error),
            "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
        }
    direct = _parameter_distance_from_state_pair(phy, edge)
    if not direct["available"]:
        return {
            "schema": "FRRIE_B01_PARAMETER_DISTANCE_UNAVAILABLE_V1",
            "seed_block": seed_label, "training_update": update,
            "first_tight_contact_update": first_tight_contact_update,
            "available": False, "availability_reason": direct["availability_reason"],
            "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
        }
    row = {
        "schema": PARAMETER_DISTANCE_RAW_SCHEMA,
        "seed_block": seed_label, "training_update": update,
        "first_tight_contact_update": first_tight_contact_update,
        "available": True, "state_stage": "POSTPROJECTION",
        "capture_boundary": "AFTER_ADAM_AND_ARM_PROJECTION_BEFORE_NEXT_MODEL_MUTATION",
        "parameter_layout": exact_parameter_layout(),
        "phy_state_binding": dict(phy_state_binding),
        "edge_state_binding": dict(edge_state_binding),
        "derived": direct["derived"],
    }
    validated = validate_parameter_distance_raw_record(
        row, manifest=manifest, test_only_component=test_only_component,
    )
    if not validated["available"]:
        raise B01ContractError("new parameter-distance raw record failed direct validation")
    return row


def write_parameter_distance_raw_record_once(
    path: str | Any, row: Mapping[str, Any], *, manifest: Mapping[str, Any] | None = None,
    test_only_component: bool = False,
) -> dict[str, Any]:
    """Create one canonical raw-record locator without duplicating state bytes."""

    import os
    from pathlib import Path

    if manifest is not None:
        raise B01ContractError(
            "formal parameter-distance raw publication requires paired-shard-derived κ"
        )
    target = Path(path).resolve(strict=False)
    staging = target.with_name(target.name + ".creating")
    incomplete = target.with_name(target.name + ".incomplete")
    if (
        target.exists() or staging.exists() or incomplete.exists()
        or not target.is_absolute()
    ):
        raise B01ContractError("parameter-distance raw record path is not fresh")
    validated = validate_parameter_distance_raw_record(
        row, manifest=manifest, test_only_component=test_only_component,
    )
    if not validated["available"]:
        raise B01ContractError("unavailable parameter-distance record cannot be published as raw")
    target.parent.mkdir(parents=True, exist_ok=True)
    published_by_this_transaction = False
    try:
        with staging.open("xb") as stream:
            stream.write(canonical_json_bytes(row))
            stream.flush()
            os.fsync(stream.fileno())
        _atomic_parameter_record_publish(staging, target)
        published_by_this_transaction = True
        import json
        literal = json.loads(target.read_text(encoding="utf-8"))
        readback = validate_parameter_distance_raw_record(
            literal, manifest=manifest, test_only_component=test_only_component,
        )
        if not readback["available"]:
            raise B01ContractError("published parameter-distance record failed literal readback")
        return readback
    except BaseException:
        if staging.exists() and not incomplete.exists():
            staging.replace(incomplete)
        elif published_by_this_transaction and target.exists() and not incomplete.exists():
            target.replace(incomplete)
        raise


def _atomic_parameter_record_publish(staging: Any, target: Any) -> None:
    """Tiny TEST seam around same-directory atomic create-only publication."""

    staging.replace(target)


def _validate_parameter_distance_availability_index_core(
    rows: Any, *, seed_label: str, first_tight_contact_update: int | None,
    manifest: Mapping[str, Any] | None = None, test_only_component: bool = False,
    formal_expected_kappa: int | None = None,
) -> dict[str, Any]:
    """Derive the exact 512-update availability trace without zero imputation."""

    import json
    from pathlib import Path

    if first_tight_contact_update is not None and (
        type(first_tight_contact_update) is not int
        or not 1 <= first_tight_contact_update <= UPDATES
    ):
        raise B01ContractError("parameter-distance κ lies outside [1,512]")
    if not isinstance(rows, list) or len(rows) != UPDATES:
        raise B01ContractError("parameter-distance availability index requires 512 updates")
    records = []
    for update, locator in enumerate(rows, start=1):
        if not isinstance(locator, Mapping) or set(locator) != {
            "seed_block", "training_update", "raw_record_path",
        } or locator["seed_block"] != seed_label or locator["training_update"] != update:
            raise B01ContractError("parameter-distance availability index order differs")
        required = first_tight_contact_update is not None and update >= first_tight_contact_update
        if not required:
            if locator["raw_record_path"] is not None:
                raise B01ContractError("pre/no-contact update must not emit a distance raw record")
            records.append({
                "seed_block": seed_label, "training_update": update, "available": False,
                "availability_reason": (
                    "PRE_TIGHT_CONTACT" if first_tight_contact_update is not None
                    else "NO_TIGHT_CONTACT_BY_512"
                ),
            })
            continue
        if locator["raw_record_path"] is None:
            records.append({
                "seed_block": seed_label, "training_update": update, "available": False,
                "availability_reason": "PARAMETER_DISTANCE_MEASUREMENT_DEFECT",
                "diagnostic_error": "required raw record locator is absent",
            })
            continue
        path = Path(locator["raw_record_path"])
        try:
            if not path.is_absolute():
                raise OSError("locator is not absolute")
            raw = json.loads(path.read_text(encoding="utf-8"))
            validated = (
                _validate_parameter_distance_raw_record_core(
                    raw, manifest=manifest, test_only_component=False,
                    expected_kappa=formal_expected_kappa,
                )
                if manifest is not None
                else validate_parameter_distance_raw_record(
                    raw, manifest=None, test_only_component=test_only_component,
                )
            )
            if (
                validated["seed_block"] != seed_label
                or validated["training_update"] != update
                or validated["first_tight_contact_update"] != first_tight_contact_update
            ):
                raise B01ContractError("raw record coordinate differs from availability index")
            records.append(validated)
        except (OSError, json.JSONDecodeError, B01ContractError) as error:
            records.append({
                "seed_block": seed_label, "training_update": update, "available": False,
                "availability_reason": "PARAMETER_DISTANCE_MEASUREMENT_DEFECT",
                "diagnostic_error": str(error),
            })
    return {
        "schema": "FRRIE_B01_PARAMETER_DISTANCE_AVAILABILITY_INDEX_V1",
        "seed_block": seed_label,
        "first_tight_contact_update": first_tight_contact_update,
        "records": records, "record_count": UPDATES,
        "available_count": sum(row["available"] for row in records),
        "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
        "temporal_reducer": None, "included_in_ordered_28": False,
        "production_gate": False,
    }


def validate_parameter_distance_availability_index(
    rows: Any, *, seed_label: str, first_tight_contact_update: int | None,
    manifest: Mapping[str, Any] | None = None, test_only_component: bool = False,
) -> dict[str, Any]:
    """Explicit TEST/component index; caller-supplied κ is never formal authority."""

    from .constants import TEST_SEED_LABELS

    if manifest is not None:
        raise B01ContractError(
            "formal parameter-distance inventory must derive κ from paired 512-update shards"
        )
    if test_only_component is not True or seed_label not in TEST_SEED_LABELS:
        raise B01ContractError(
            "caller-supplied parameter-distance κ is restricted to explicit TEST/component labels"
        )
    return _validate_parameter_distance_availability_index_core(
        rows, seed_label=seed_label,
        first_tight_contact_update=first_tight_contact_update,
        manifest=None, test_only_component=True,
        formal_expected_kappa=None,
    )


def validate_formal_parameter_distance_inventory(
    rows: Any, *, seed_label: str, manifest: Mapping[str, Any],
    paired_training_shards: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive formal κ/coverage only from revalidated full paired training shards."""

    from .contract import validate_manifest

    manifest0 = validate_manifest(manifest)
    if seed_label not in manifest0["execution_labels"]:
        raise B01ContractError("formal parameter-distance seed is outside manifest execution labels")
    paired = validate_paired_training_shards(paired_training_shards)
    if (
        paired.get("schema") != "FRRIE_B01_VALIDATED_PAIRED_TRAINING_COMPONENT_V1"
        or paired.get("seed_label") != seed_label
        or type(paired.get("training_validation_replay_complete")) is not bool
    ):
        raise B01ContractError("formal parameter-distance paired training component differs")
    kappa = paired["kappa"]
    result = _validate_parameter_distance_availability_index_core(
        rows, seed_label=seed_label, first_tight_contact_update=kappa,
        manifest=manifest0, test_only_component=False,
        formal_expected_kappa=kappa,
    )
    expected_required = [] if kappa is None else list(range(kappa, UPDATES + 1))
    observed_required = [
        row["training_update"] for row in result["records"]
        if row["training_update"] >= (kappa or UPDATES + 1)
    ]
    if observed_required != expected_required:
        raise B01ContractError("formal parameter-distance post-contact coverage differs")
    return {
        **result,
        "schema": "FRRIE_B01_FORMAL_PARAMETER_DISTANCE_INVENTORY_V1",
        "kappa_source": "REVALIDATED_COMPLETE_PAIRED_512_UPDATE_TRAINING_SHARDS",
        "paired_training_schema": paired["schema"],
        "paired_training_state_chain_revalidated": True,
        "required_postcontact_updates": expected_required,
        "caller_supplied_kappa_accepted": False,
    }


def _validate_paired_stage_equality(
    *, model_stages: Mapping[str, Mapping[str, Any]],
    optimizer_stages: Mapping[str, Mapping[str, Any]], kappa: int | None,
    beta_offset: int, beta_stop: int, updates: int,
) -> None:
    """Shared direct-byte law; small synthetic tests are explicitly non-production."""

    def row_bytes(value: Any) -> bytes:
        return value.tobytes() if hasattr(value, "tobytes") else bytes(value)

    fully_equal_updates = updates if kappa is None else kappa - 1
    for index in range(fully_equal_updates):
        if any(
            row_bytes(stages["PHY_TRUST"][index])
            != row_bytes(stages["EDGE_FLEX"][index])
            for stages in (*model_stages.values(), *optimizer_stages.values())
        ):
            raise B01ContractError("paired training stage bytes differ before κ")
    if kappa is None:
        return
    index = kappa - 1
    if any(
        row_bytes(model_stages[name]["PHY_TRUST"][index])
        != row_bytes(model_stages[name]["EDGE_FLEX"][index])
        for name in ("model_pre", "model_post_adam")
    ) or any(
        row_bytes(optimizer_stages[name]["PHY_TRUST"][index])
        != row_bytes(optimizer_stages[name]["EDGE_FLEX"][index])
        for name in optimizer_stages
    ):
        raise B01ContractError("paired training pre/postAdam bytes differ at κ")
    left = row_bytes(model_stages["model_post_projection"]["PHY_TRUST"][index])
    right = row_bytes(model_stages["model_post_projection"]["EDGE_FLEX"][index])
    if left[:beta_offset] + left[beta_stop:] != right[:beta_offset] + right[beta_stop:]:
        raise B01ContractError("paired training non-beta projection bytes differ at κ")

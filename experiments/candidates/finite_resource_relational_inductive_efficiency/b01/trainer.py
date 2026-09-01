"""Projection-observing paired RSCF update primitive for B01."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..state_codec import (
    decode_optimizer_state, encode_optimizer_state, load_actor_and_optimizer_state,
)
from ..training import (
    GRADIENT_CLIP_NORM, RSCFEpisode, make_optimizer, rscf_batch_loss,
    validate_update_batch,
)
from .constants import LEARNED_ARMS
from .contract import B01ContractError
from .contract import canonical_json_bytes
from .native_batch import BatchWorkLedger


@dataclass(frozen=True, slots=True)
class ArmUpdateReceipt:
    arm: str
    update: int
    loss: float
    score: float
    entropy: float
    critic: float
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


def _tensor_direct_equal(left: Any, right: Any) -> bool:
    import torch
    return (
        isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor)
        and left.dtype == right.dtype and left.shape == right.shape
        and torch.equal(left.detach(), right.detach())
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
        "selected_probabilities", "q_targets", "legal_masks", "factual_actions",
        "all_probabilities", "critic_values", "terminal_return",
    )
    for left_episode, right_episode in zip(left, right):
        if left_episode.roster_size != right_episode.roster_size or any(
            not _tensor_direct_equal(getattr(left_episode, field), getattr(right_episode, field))
            for field in fields
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
        self.optimizer.zero_grad(set_to_none=True)
        terms = rscf_batch_loss(episodes)
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
            preclip_global_norm=float(preclip.detach().item()), backward_calls=1,
            adam_steps=1, projection_changed_indices=changed_indices,
            box_contact=bool(changed),
            maximum_box_overshoot=overshoot, projection_displacement=displacement,
            preprojection_beta=tuple(float(value) for value in beta_before_projection.reshape(-1)),
            postprojection_beta=tuple(float(value) for value in projected.reshape(-1)),
            optimizer_moments_unchanged_by_projection=True,
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

    def projection_audit(self) -> dict[str, Any]:
        return {
            "first_tight_contact_update": self.first_tight_contact_update,
            "precontact_full_state_equal": self.precontact_full_state_equal,
            "tight_projection_changed_coordinates": len(self.changed_coordinates),
            "wide_boundary_contact": self.wide_boundary_contact,
            "maximum_tight_overshoot": self.maximum_tight_overshoot,
            "cumulative_tight_displacement": self.cumulative_tight_displacement,
        }

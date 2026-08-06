"""FOLR prospective registration: the precommitted readout-sensitive cell.

Sequence 01, first half of component 7 of the object graph External Pro required
in ruling ``FOLR_S03_BINDING_SELECTED``.

THE RULE THIS MODULE EXISTS TO ENFORCE
--------------------------------------
    No cell may be selected, replaced or modified after observing any of the
    main, reset or wrong-owner kernels.

So the cell is built analytically, frozen with a digest, and sent to Pro for
approval *before* execution.  Development and debugging of the branch harness
run against ``development_registration()``, which is marked ``DEVELOPMENT_ONLY``
and uses different owner keys and payloads; debugging on the registered cell
would itself be an observation before registration.

WHY OPPOSITE HEAD WEIGHTS ARE NOT ENOUGH
----------------------------------------
Pro rejected the naive prototype:

    Setting skill_head.weight[0,0] and [1,0] to opposite signs does not, by
    itself, guarantee an S03 effect. The payload must first alter decoder
    coordinate zero through the GRU and decoder path. […] The actual actor path
    is: pre_hidden -> GRU new hidden -> decoder hidden -> skill head.

So the cell fixes the whole path, and the guarantee is a derivation rather than
a hope.  Writing ``H`` for ``high_hidden_dim`` and ``h`` for the installed
payload, the surgery is:

1. ``high_rnn.weight_hh[:, 0] = 0``
   No gate reads ``h[0]``.  In the GRU update
   ``new = (1 - z) * n + z * h``, both ``z`` and ``n`` therefore become
   constants with respect to ``h[0]``.

2. ``weight_ih[H, :] = 0``, ``bias_ih[H] = +20``, ``bias_hh[H] = 0``
   The update gate's coordinate 0 is pinned at ``z0 = sigmoid(20)``, which is
   within ``2.1e-9`` of 1.  Hence
   ``new_hidden[0] = z0 * h[0] + (1 - z0) * n0``, an affine function of
   ``h[0]`` with slope ``z0 > 0.999999997``.

3. ``decoder_hidden[0].weight[:, 0] = 0`` then row 0 set to ``e_0`` with zero
   bias.  So ``hidden[0] = GELU(new_hidden[0])`` and **no other** decoder
   coordinate depends on ``h[0]`` at all.

4. ``skill_head.weight[:, 0] = 0``, then ``[0, 0] = +1`` and ``[1, 0] = -1``.
   So ``logit_0 - logit_1 = 2 * GELU(new_hidden[0])`` plus terms independent of
   ``h[0]``.

The registered payloads put ``h[0]`` at ``0.0`` and ``2.0``.  GELU is strictly
increasing on ``[0, inf)`` -- its only non-monotone stretch is near ``-0.75``,
which the registered values avoid -- so

    (logit_0 - logit_1) moves by 2 * (GELU(2) - GELU(0)) = 3.909...

and the softmax must move.  That is the analytic guarantee; it is not read off a
kernel.

WHAT THAT COSTS IN INTERPRETATION, VERBATIM
-------------------------------------------
Pro was explicit that building the sensitivity in changes what may be claimed:

    The runtime correctly transports and reads a registered owner-private
    recurrent payload in a constructed sensitivity cell.

    It may not be reported as evidence that: a naturally trained policy
    discovered S03 use; the environment creates a need for the mechanism; the
    mechanism improves behavior; typical cells are S03-sensitive.

``outcome.py`` carries those exclusions into every terminal.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import torch

from ha_ctse_process import variable_roster_event as vre

from experiments.candidates.folr_core import branch_snapshot as bs
from experiments.candidates.folr_core import reset_manifest as rm
from experiments.candidates.folr_core import s03_binding as sb

RAW_OUTPUT_BINDING = "folr_core.registration.v1"

#: The registered payload coordinate and its two values.  Coordinate 0 is the
#: one the cell's surgery routes; every other coordinate is held identical
#: across h0, h1 and h_neutral so no complementary coordinate is uncontrolled.
FOCAL_COORDINATE = 0
PAYLOAD_ZERO_VALUE = 0.0
PAYLOAD_ONE_VALUE = 2.0
NEUTRAL_VALUE = 1.0

#: The update-gate bias that pins z0. sigmoid(20) = 1 - 2.06e-9.
UPDATE_GATE_BIAS = 20.0


def _gelu(x: float) -> float:
    """The exact erf-based GELU torch uses by default."""
    return 0.5 * x * (1.0 + math.erf(x / math.sqrt(2.0)))


#: The analytic witness: how far the registered payloads move logit_0 - logit_1,
#: computed in closed form and never from an observed kernel.
ANALYTIC_LOGIT_SEPARATION = 2.0 * (
    _gelu(PAYLOAD_ONE_VALUE) - _gelu(PAYLOAD_ZERO_VALUE)
)


def install_readout_sensitive_cell(policy: Any, *, high_hidden_dim: int) -> None:
    """Apply the four-step surgery described in the module docstring."""
    with torch.no_grad():
        gru = policy.high_rnn
        # 1. no gate reads the focal hidden coordinate
        gru.weight_hh[:, FOCAL_COORDINATE] = 0.0
        # 2. pin the update gate's focal coordinate at sigmoid(UPDATE_GATE_BIAS)
        update_row = high_hidden_dim + FOCAL_COORDINATE
        gru.weight_ih[update_row, :] = 0.0
        gru.bias_ih[update_row] = UPDATE_GATE_BIAS
        gru.bias_hh[update_row] = 0.0
        # 3. only decoder coordinate 0 reads new_hidden[0], and reads it alone
        decoder = policy.decoder_hidden[0]
        decoder.weight[:, FOCAL_COORDINATE] = 0.0
        decoder.weight[FOCAL_COORDINATE, :] = 0.0
        decoder.weight[FOCAL_COORDINATE, FOCAL_COORDINATE] = 1.0
        decoder.bias[FOCAL_COORDINATE] = 0.0
        # 4. opposite signs on the two skills the focal coordinate drives
        head = policy.skill_head
        head.weight[:, FOCAL_COORDINATE] = 0.0
        head.weight[0, FOCAL_COORDINATE] = 1.0
        head.weight[1, FOCAL_COORDINATE] = -1.0


def payload_vectors(high_hidden_dim: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """h0, h1, h_neutral -- identical apart from the focal coordinate.

    The non-focal coordinates carry a fixed nonzero pattern rather than zeros,
    so h0 is distinguishable from a freshly initialized record and the
    "uncontrolled complementary coordinate" failure Pro warned about cannot hide
    in a default value.
    """
    base = (0.1 * np.arange(high_hidden_dim, dtype=np.float32)).astype(np.float32)
    vectors = []
    for value in (PAYLOAD_ZERO_VALUE, PAYLOAD_ONE_VALUE, NEUTRAL_VALUE):
        vector = base.copy()
        vector[FOCAL_COORDINATE] = np.float32(value)
        vectors.append(vector)
    return tuple(vectors)  # type: ignore[return-value]


@dataclass(frozen=True)
class Registration:
    """Pro's §7 freeze list, complete, with one digest over all of it."""

    cell_identifier: str
    binding: sb.S03Binding
    manifest: rm.ResetManifest
    normalization_profile: str
    canonical_provenance_branch: int
    teacher_actions: Mapping[str, int]
    #: The positive gate. Pro: "Do not use mere != as the formal positive gate;
    #: register either an integer-ULP margin or a probability-space margin
    #: before execution."  The VALUE is a scientific parameter and goes to Pro
    #: with this registration; it is not chosen here on the strength of any
    #: observed kernel.
    delta_cell: float
    analytic_logit_separation: float
    weight_witness: Mapping[str, Any]
    development_only: bool = False

    def __post_init__(self) -> None:
        if self.normalization_profile not in rm.NORMALIZATION_PROFILES:
            raise ValueError("unregistered normalization profile")
        if self.canonical_provenance_branch not in (0, 1):
            raise ValueError("the canonical provenance branch must be 0 or 1")
        if self.delta_cell <= 0.0:
            raise ValueError("delta_cell must be a positive margin, not !=")
        if set(self.teacher_actions) != set(self.manifest.frontier):
            raise ValueError("teacher actions must cover exactly the frontier")
        if self.binding.target_lifecycle_key != self.manifest.target_lifecycle_key:
            raise ValueError("binding and manifest name different targets")

    def registration_digest(self) -> str:
        hasher = hashlib.sha256()
        hasher.update(RAW_OUTPUT_BINDING.encode("utf-8"))
        hasher.update(
            bs.digest_of(
                {
                    "cell_identifier": self.cell_identifier,
                    "binding": self.binding.manifest_digest(),
                    "manifest": self.manifest.digest(),
                    "normalization_profile": self.normalization_profile,
                    "canonical_provenance_branch": self.canonical_provenance_branch,
                    "teacher_actions": dict(self.teacher_actions),
                    "delta_cell": self.delta_cell,
                    "analytic_logit_separation": self.analytic_logit_separation,
                    "weight_witness": dict(self.weight_witness),
                    "development_only": self.development_only,
                }
            ).encode("utf-8")
        )
        return hasher.hexdigest()

    def frozen_record(self) -> dict[str, object]:
        """The human-readable freeze, for the pre-execution dispatch to Pro."""
        return {
            "raw_output_binding": RAW_OUTPUT_BINDING,
            "cell_identifier": self.cell_identifier,
            "development_only": self.development_only,
            "registration_digest": self.registration_digest(),
            "s03_registry": self.binding.registry(),
            "reset_manifest_digest": self.manifest.digest(),
            "target": [
                self.manifest.target_lifecycle_key,
                self.binding.target_membership_epoch,
            ],
            "shadow": [
                self.binding.shadow_lifecycle_key,
                self.binding.shadow_membership_epoch,
            ],
            "frontier": list(self.manifest.frontier),
            "target_token_order": list(self.manifest.target_token_order),
            "legal_action_support": self.manifest.legal_action_support.tolist(),
            "teacher_actions": dict(self.teacher_actions),
            "normalization_profile": self.normalization_profile,
            "canonical_provenance_branch": self.canonical_provenance_branch,
            "delta_cell": self.delta_cell,
            "analytic_logit_separation": self.analytic_logit_separation,
            "weight_witness": dict(self.weight_witness),
        }


def _weight_witness(policy: Any, *, high_hidden_dim: int) -> dict[str, Any]:
    """The exact weight witness Pro's §7 freeze list requires."""
    update_row = high_hidden_dim + FOCAL_COORDINATE
    with torch.no_grad():
        z0 = float(
            torch.sigmoid(
                policy.high_rnn.bias_ih[update_row] + policy.high_rnn.bias_hh[update_row]
            )
        )
        return {
            "focal_coordinate": FOCAL_COORDINATE,
            "update_gate_z0": z0,
            "update_gate_slope_shortfall": 1.0 - z0,
            "gate_reads_focal_hidden": bool(
                torch.any(policy.high_rnn.weight_hh[:, FOCAL_COORDINATE] != 0.0)
            ),
            "decoder_rows_reading_focal": int(
                torch.count_nonzero(
                    policy.decoder_hidden[0].weight[:, FOCAL_COORDINATE]
                )
            ),
            "skill_head_focal_column": policy.skill_head.weight[
                :, FOCAL_COORDINATE
            ].tolist(),
            "model_state_digest": sb.model_state_digest(policy),
        }


def build_registration(
    *,
    cell_identifier: str,
    target: str,
    shadow: str,
    other_owners: tuple[str, ...] = (),
    architecture_mode: str = "f1",
    high_hidden_dim: int = 10,
    obs_dim: int = 3,
    critic_member_dim: int = 2,
    critic_global_dim: int = 2,
    n_skills: int = 3,
    action_dim: int = 2,
    member_hidden_dim: int = 12,
    skill_embedding_dim: int = 5,
    model_seed: int = 20_260_806,
    normalization_profile: str = rm.PROVENANCE_LABEL,
    canonical_provenance_branch: int = 0,
    delta_cell: float = 1e-3,
    development_only: bool = False,
) -> Registration:
    """Construct the frozen registration.  Observes no kernel."""
    keys = (target, shadow) + tuple(other_owners)
    if len(set(keys)) != len(keys):
        raise ValueError("registration owner keys must be distinct")

    torch.manual_seed(int(model_seed))
    core = vre.VariableRosterEventCore(
        architecture_mode=architecture_mode,
        runtime_mode="supplied_executor",
        obs_dim=obs_dim,
        critic_member_dim=critic_member_dim,
        critic_global_dim=critic_global_dim,
        n_skills=n_skills,
        action_dim=action_dim,
        member_hidden_dim=member_hidden_dim,
        high_hidden_dim=high_hidden_dim,
        skill_embedding_dim=skill_embedding_dim,
        gamma=0.9,
        gae_lambda=0.8,
        opportunity_seed=142,
        frontier_seed=51,
        action_seed=61,
    )
    install_readout_sensitive_cell(core.commitment_model, high_hidden_dim=high_hidden_dim)

    h0, h1, neutral = payload_vectors(high_hidden_dim)
    binding = sb.S03Binding.build(
        target_lifecycle_key=target,
        target_membership_epoch=0,
        shadow_lifecycle_key=shadow,
        shadow_membership_epoch=0,
        h0=h0,
        h1=h1,
        h_neutral=neutral,
    )

    # A canonical starting state, built from the registration rather than from
    # any history: every owner ACTIVE, no open trace, opportunity gap expired so
    # the whole active set is due at the frontier, target first.
    non_s03_hidden = (0.05 * np.arange(high_hidden_dim, dtype=np.float32)).astype(
        np.float32
    )
    owners = tuple(
        rm.OwnerManifest(
            lifecycle_key=key,
            membership_epoch=0,
            status=vre.ACTIVE,
            active_skill=index % n_skills,
            skill_active_age=index,
            active_gap_remaining=0,
            is_genuine_join=False,
            is_rejoin=False,
            high_hidden=(neutral.copy() if key == target else non_s03_hidden.copy()),
            observation=np.asarray(
                [0.1 * (index + 1) + 0.01 * axis for axis in range(obs_dim)],
                dtype=np.float32,
            ),
            critic_member_features=np.asarray(
                [0.2 * (index + 1) - 0.03 * axis for axis in range(critic_member_dim)],
                dtype=np.float32,
            ),
        )
        for index, key in enumerate(keys)
    )
    manifest = rm.ResetManifest(
        architecture={name: getattr(core, name) for name in bs.ARCHITECTURE_FIELDS},
        model_states={
            name: {
                key: value.clone()
                for key, value in getattr(core, name).state_dict().items()
            }
            for name in bs.MODEL_FIELDS
        },
        rng_identity={
            name: int(getattr(core, name))
            for name in (
                "rng_episode_id",
                "opportunity_master_seed",
                "frontier_master_seed",
                "action_master_seed",
                "opportunity_stream_id",
                "frontier_stream_id",
                "action_stream_id",
            )
        },
        rng_states={
            "opportunity_rng_state": dict(core.opportunity_rng.bit_generator.state),
            "frontier_order_rng_state": dict(core.frontier_rng.bit_generator.state),
            "policy_action_rng_state": dict(core.action_rng.bit_generator.state),
        },
        physical_time=0,
        policy_version=0,
        owners=owners,
        critic_global_features=np.asarray([0.0, -0.25], dtype=np.float32)[
            :critic_global_dim
        ],
        target_lifecycle_key=target,
        frontier=keys,
        target_token_order=keys,
        legal_action_support=np.ones(n_skills, dtype=np.bool_),
    )
    return Registration(
        cell_identifier=cell_identifier,
        binding=binding,
        manifest=manifest,
        normalization_profile=normalization_profile,
        canonical_provenance_branch=canonical_provenance_branch,
        teacher_actions={key: 0 for key in keys},
        delta_cell=float(delta_cell),
        analytic_logit_separation=ANALYTIC_LOGIT_SEPARATION,
        weight_witness=_weight_witness(
            core.commitment_model, high_hidden_dim=high_hidden_dim
        ),
        development_only=bool(development_only),
    )


def development_registration() -> Registration:
    """A decoy cell for building and debugging the harness.

    Different owner keys, different model seed and a marked identifier, so no
    part of the harness can be developed by looking at the registered cell's
    kernels -- which would violate Pro's prospective-registration rule.
    """
    return build_registration(
        cell_identifier="DEVELOPMENT_ONLY_decoy_v1",
        target="dev_target",
        shadow="dev_shadow",
        model_seed=1_234_567,
        development_only=True,
    )


def registered_cell() -> Registration:
    """The prospectively frozen cell.  Not to be executed before approval."""
    return build_registration(
        cell_identifier="folr_s03_constructed_sensitivity_v1",
        target="owner_t",
        shadow="owner_q",
        development_only=False,
    )

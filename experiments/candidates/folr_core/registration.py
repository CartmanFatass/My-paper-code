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
   The update gate's coordinate 0 is pinned at ``z0 = sigmoid(20)``.  In the
   registered numerical context -- CPU, float32 -- that rounds to **exactly**
   1.0, so ``new_hidden[0] = h[0]`` exactly rather than approximately.  Pro
   accepted the construction on that basis: *"the focal carry is exact for the
   registered realization rather than merely having slope close to one"*.  In
   exact real arithmetic the same expression is affine in ``h[0]`` with slope
   ``z0 > 0.999999997``.

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

WHAT THAT DOES AND DOES NOT PROVE
---------------------------------
Pro corrected an overreach here, and the correction matters:

    That proves logit-level functional dependence. It does not by itself prove
    ||K_1 - K_0||_inf > 10^-3. For example, if the unchanged third logit
    dominates both focal logits by a sufficiently large amount, both
    probability vectors can concentrate arbitrarily closely on action 2 even
    while logit_0 - logit_1 moves by 3.909.

So ``ANALYTIC_LOGIT_SEPARATION`` is a **logit-space** witness only.  No
probability-space lower bound is registered, and ``outcome.py`` must not infer
one: a sub-margin contrast is routed to interface/instance insufficiency
because the probability bound was never established, not because the logit
derivation was contradicted.

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
import pathlib
import subprocess
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

#: Pro's §3 disposition.  The reset manifest rebuilds a ``VariableRosterEventCore``
#: and nothing environment-side, so rather than add an environment merely to
#: satisfy an overbroad label, the scope is registered explicitly and travels in
#: the registration digest:
#:
#:     Do not add an environment merely to satisfy an overbroad label. Instead,
#:     amend the registration with an explicit, digest-bearing scope.
#:
#: The admissible positive sentence names the core for the same reason: a run of
#: this graph cannot say that ``DynamicRosterEventEnv`` has been exercised.
OBJECT_GRAPH_SCOPE: dict[str, Any] = {
    "includes": (
        "VariableRosterEventCore",
        "registered synthetic BoundarySnapshot",
        "registered MembershipTransaction",
        "constructed sensitivity model",
    ),
    "excludes": (
        "DynamicRosterEventEnv",
        "environment return",
        "environment task dynamics",
    ),
    "admissible_positive_sentence": (
        "VariableRosterEventCore correctly transports and reads the registered "
        "owner-private recurrent payload at the registered synthetic boundary "
        "in the constructed sensitivity cell."
    ),
    "must_not_say": (
        "that DynamicRosterEventEnv has been exercised"
    ),
}

#: The source files that implement the registered actor path
#: ``pre_hidden -> GRUCell -> decoder -> skill head`` and the row types that
#: carry its witnesses.
#:
#: ``variable_roster_event_support`` is here because Pro found the dependency
#: the first pass missed: *"EventCommitmentPolicy.encode_members calls
#: variable_roster_event_support.normalized_log_age. A change in that helper can
#: change the target member embedding, set summary, logits, and probability
#: kernel without changing any of the three fingerprinted files."*
ACTOR_PATH_SOURCES = (
    "ha_ctse_process/variable_roster_event.py",
    "ha_ctse_process/variable_roster_event_models.py",
    "ha_ctse_process/variable_roster_event_types.py",
    "ha_ctse_process/variable_roster_event_support.py",
)

#: The candidate-side modules that install the intervention, clone and reset
#: branch state, capture and digest the actor preimage, certify placement and
#: freshness, construct the contrasts and route the terminal.
#:
#: Pro's §4.2, which is the sharper half of the objection: *"A later change to
#: branches.py, certificates.py, or outcome.py could leave the registration data
#: and three-file actor fingerprint unchanged while changing the executable
#: scientific proposition."*  Freezing the model but not the harness freezes the
#: wrong half.
HARNESS_SOURCES = (
    "experiments/candidates/folr_core/s03_binding.py",
    "experiments/candidates/folr_core/branch_snapshot.py",
    "experiments/candidates/folr_core/reset_manifest.py",
    "experiments/candidates/folr_core/branches.py",
    "experiments/candidates/folr_core/certificates.py",
    "experiments/candidates/folr_core/registration.py",
    "experiments/candidates/folr_core/outcome.py",
)

#: Everything the registered scientific proposition executes.
SCIENTIFIC_GRAPH_SOURCES = tuple(sorted(HARNESS_SOURCES + ACTOR_PATH_SOURCES))


def _repository_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _fingerprint(digests: Mapping[str, str], names: tuple[str, ...]) -> str:
    hasher = hashlib.sha256()
    for relative in names:
        hasher.update(relative.encode("utf-8"))
        hasher.update(digests[relative].encode("utf-8"))
    return hasher.hexdigest()


def actor_path_source_identity() -> dict[str, Any]:
    """Commit, worktree cleanliness and per-file digests of the whole graph.

    The digests are the durable half.  A commit hash taken from a dirty tree
    authenticates nothing, so the record says which case it is instead of
    implying the stronger one.

    The cleanliness flag is named for what it actually measures.  Pro:
    *"The field named source_tree_dirty is also computed from
    `git status --porcelain -- <ACTOR_PATH_SOURCES>` so it means 'the three
    selected actor-path files are clean,' not 'the source tree is clean.'"*
    It is now ``registered_sources_dirty`` and covers the complete graph.
    """
    root = _repository_root()

    def _git(*arguments: str) -> str | None:
        try:
            return subprocess.run(
                ["git", *arguments],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return None

    head = _git("rev-parse", "HEAD")
    commit = head.strip() if head is not None else "UNAVAILABLE"
    status = _git("status", "--porcelain", "--", *SCIENTIFIC_GRAPH_SOURCES)
    dirty = None if status is None else bool(status.strip())

    digests = {}
    for relative in SCIENTIFIC_GRAPH_SOURCES:
        # LF-normalized: this worktree runs core.autocrlf=true, so raw bytes
        # would fingerprint differently on a fresh clone.
        digests[relative] = hashlib.sha256(
            (root / relative).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()

    return {
        "source_commit": commit,
        "registered_sources_dirty": dirty,
        "commit_authenticates_the_registration": commit != "UNAVAILABLE" and dirty is False,
        "registered_sources": digests,
        "actor_path_fingerprint": _fingerprint(digests, ACTOR_PATH_SOURCES),
        "harness_fingerprint": _fingerprint(digests, HARNESS_SOURCES),
        # This, not the commit, is what the execution-time gate compares. Pro:
        # "The fingerprint must enter the registration digest and be recomputed
        # at execution."
        "scientific_graph_fingerprint": _fingerprint(
            digests, SCIENTIFIC_GRAPH_SOURCES
        ),
        # Pro: the registered construction makes finite-precision claims about
        # GRUCell, GELU, sigmoid and softmax, so the libraries are part of the
        # identity of what was proved.
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
    }


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


def _scope_record(scope: Mapping[str, Any]) -> dict[str, Any]:
    """Plain JSON-shaped view of the scope, for digesting and reporting."""
    return {
        key: (list(value) if isinstance(value, (tuple, list)) else value)
        for key, value in sorted(scope.items())
    }


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
    #: Pro §3/§6G: the digest-bearing object-graph scope.  Frozen here so the
    #: emitted outcome cannot quietly widen the claim to the environment.
    object_graph_scope: Mapping[str, Any]
    #: Pro §6C: the approved source identity, carried by the registration itself
    #: rather than pinned only in the dispatch message.
    source_identity: Mapping[str, Any]
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
        """The frozen identity of the registration.

        ``source_identity`` enters through the **scientific-graph fingerprint**
        and the library versions, never through the commit hash or the dirty
        flag.  Those two move whenever HEAD moves for any unrelated reason, and
        Pro asks for two separate gates: the current registration digest must
        equal the precommitted expected digest (so it has to be stable), *and*
        the execution source identity must equal the approved one (which the
        content-addressed fingerprint answers exactly).  Pro accepted that
        split: *"the content fingerprint belongs inside the registration digest;
        a human-readable commit identity may travel alongside it."*

        The fingerprint covers the actor path **and** the harness.  Freezing the
        model while leaving ``branches.py`` / ``certificates.py`` /
        ``outcome.py`` free would freeze the wrong half: the executable
        scientific proposition could change with the registration data intact.
        """
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
                    "object_graph_scope": _scope_record(self.object_graph_scope),
                    "scientific_graph_fingerprint": str(
                        self.source_identity["scientific_graph_fingerprint"]
                    ),
                    "torch_version": str(self.source_identity["torch_version"]),
                    "numpy_version": str(self.source_identity["numpy_version"]),
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
            "delta_cell_status": (
                "a prospectively registered minimum effect size (materiality "
                "threshold), NOT a numerical-error tolerance: direct kernels are "
                "compared as exact float32 outputs and replay is their exact "
                "float64 widening, so numerical reproduction is handled "
                "separately"
            ),
            "analytic_logit_separation": self.analytic_logit_separation,
            "analytic_witness_status": (
                "proves logit-level functional dependence only. It does NOT "
                "imply ||K_1 - K_0||_inf > delta_cell: if the unchanged third "
                "logit dominates both focal logits, both probability vectors "
                "can concentrate arbitrarily closely on action 2 while "
                "logit_0 - logit_1 still moves by "
                f"{self.analytic_logit_separation:.6f}. No probability-space "
                "lower bound is registered."
            ),
            "weight_witness": dict(self.weight_witness),
            "object_graph_scope": _scope_record(self.object_graph_scope),
            "source_identity": dict(self.source_identity),
        }


class ExactCarryNotEstablished(RuntimeError):
    """The focal update gate is not bitwise 1.0 at the registered boundary."""


def _sigmoid_one_threshold() -> float:
    """Smallest float32 preactivation whose float32 sigmoid is exactly 1.0.

    Reported as headroom rather than assumed: the whole exact-carry claim rests
    on the preactivation clearing this line, so how far it clears it by is part
    of the witness.
    """
    low, high = 0.0, 64.0
    for _ in range(200):
        middle = 0.5 * (low + high)
        value = torch.sigmoid(torch.tensor(middle, dtype=torch.float32))
        if value.item() == 1.0:
            high = middle
        else:
            low = middle
    return high


def focal_update_gate_witness(
    policy: Any, *, high_hidden_dim: int, payloads: Mapping[str, np.ndarray]
) -> dict[str, Any]:
    """The registered-boundary finite-precision gate witness Pro's §1 requires.

    The previous witness reported ``sigmoid(bias_ih + bias_hh)`` and called it
    ``update_gate_z0``.  Pro caught that this is a **bias-only** quantity, not
    the gate:

        Zeroing weight_hh[:, 0] establishes that the focal hidden coordinate h_0
        does not influence any GRU gate or candidate. It does not zero the
        remainder of the focal update-gate row. […] The nonfocal payload
        coordinates are deliberately nonzero, so the recurrent term is not
        identically absent. […] It shows that the registration has not proved it.

    Correct, and the repair is a witness rather than a weight change.  The
    preactivation of the focal update gate is

        a_z0 = bias_ih[r] + bias_hh[r] + (W_ih[r,:] @ x) + (W_hh[r,:] @ h)

    and the cell zeroes ``W_ih[r,:]``, so the member embedding ``x`` drops out
    entirely.  What remains depends only on the registered model weights and the
    registered payload's NONFOCAL coordinates -- both frozen in this
    registration.  So the gate is computable here exactly, with no runtime, no
    actor input and no probability kernel observed.

    ``W_hh[r,0]`` is zero (from the focal-column surgery) and h_1..h_9 are
    identical across h0, h1 and h_neutral, so the three preactivations must
    coincide.  That coincidence is asserted, not assumed: if the payloads ever
    differ outside the focal coordinate, this is where it surfaces.
    """
    update_row = high_hidden_dim + FOCAL_COORDINATE
    with torch.no_grad():
        gru = policy.high_rnn
        recurrent_row = gru.weight_hh[update_row, :]
        input_row_is_zero = bool(torch.all(gru.weight_ih[update_row, :] == 0.0))
        bias = gru.bias_ih[update_row] + gru.bias_hh[update_row]

        gates: dict[str, dict[str, Any]] = {}
        for slot, vector in payloads.items():
            hidden = torch.as_tensor(np.asarray(vector), dtype=torch.float32)
            recurrent = torch.dot(recurrent_row, hidden)
            preactivation = bias + recurrent
            z0 = torch.sigmoid(preactivation)
            gates[slot] = {
                "recurrent_contribution": float(recurrent),
                "preactivation": float(preactivation),
                "z0": float(z0),
                "z0_is_bitwise_one": z0.item() == 1.0,
            }

        preactivations = {row["preactivation"] for row in gates.values()}
        equal_across_payloads = len(preactivations) == 1
        exact_carry = all(row["z0_is_bitwise_one"] for row in gates.values())
        threshold = _sigmoid_one_threshold()
        reference = next(iter(gates.values()))["preactivation"]

        nonfocal = {
            slot: np.asarray(vector, dtype=np.float32)[
                FOCAL_COORDINATE + 1 :
            ].tolist()
            for slot, vector in payloads.items()
        }
        return {
            "focal_coordinate": FOCAL_COORDINATE,
            "focal_update_gate_row": update_row,
            # Load-bearing: with a nonzero input row the preactivation would
            # depend on the member embedding and could not be certified here.
            "update_gate_input_row_is_zero": input_row_is_zero,
            "update_gate_bias_sum": float(bias),
            "focal_update_gate_recurrent_row": recurrent_row.tolist(),
            "registered_nonfocal_payload_coordinates": nonfocal,
            "per_payload": gates,
            "preactivation_equal_across_payloads": equal_across_payloads,
            "float32_sigmoid_saturation_threshold": threshold,
            "preactivation_headroom_over_threshold": reference - threshold,
            "exact_carry_established": bool(
                exact_carry and equal_across_payloads and input_row_is_zero
            ),
        }


def _weight_witness(
    policy: Any, *, high_hidden_dim: int, payloads: Mapping[str, np.ndarray]
) -> dict[str, Any]:
    """The exact weight witness Pro's §7 freeze list requires."""
    with torch.no_grad():
        return {
            "focal_coordinate": FOCAL_COORDINATE,
            "focal_update_gate": focal_update_gate_witness(
                policy, high_hidden_dim=high_hidden_dim, payloads=payloads
            ),
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


def analytic_logit_separation(witness: Mapping[str, Any]) -> float:
    """The logit displacement, derived from the gate that actually evaluates.

    Only valid under exact carry.  If the gate is not bitwise 1.0 the correct
    object is the frozen affine map ``h'_0 = (1 - z0) * n0 + z0 * h_0`` and the
    corresponding GELU displacement, which needs the candidate ``n0`` and hence
    the registered member embedding.  That case is refused rather than silently
    approximated -- reporting the exact-carry number under a gate that does not
    carry exactly is the defect Pro just caught, and it should fail closed.
    """
    gate = witness["focal_update_gate"]
    if not gate["exact_carry_established"]:
        raise ExactCarryNotEstablished(
            "the focal update gate is not bitwise 1.0 across all registered "
            "payloads at the registered boundary; the analytic witness must be "
            "re-derived from h'_0 = (1 - z0) * n0 + z0 * h_0 using the frozen "
            f"z0 values {gate['per_payload']}"
        )
    return ANALYTIC_LOGIT_SEPARATION


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
    witness = _weight_witness(
        core.commitment_model,
        high_hidden_dim=high_hidden_dim,
        payloads={slot: binding.payload(slot) for slot in sb.PAYLOAD_SLOTS},
    )
    return Registration(
        cell_identifier=cell_identifier,
        binding=binding,
        manifest=manifest,
        normalization_profile=normalization_profile,
        canonical_provenance_branch=canonical_provenance_branch,
        teacher_actions={key: 0 for key in keys},
        delta_cell=float(delta_cell),
        # Derived FROM the witness, so a cell whose gate does not carry exactly
        # cannot silently inherit the exact-carry number.
        analytic_logit_separation=analytic_logit_separation(witness),
        weight_witness=witness,
        object_graph_scope=OBJECT_GRAPH_SCOPE,
        source_identity=actor_path_source_identity(),
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

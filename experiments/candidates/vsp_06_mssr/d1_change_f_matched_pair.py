"""MSSR-D1 CHANGE_F post-commit matched-pair harness (zero training, structural).

External Pro reserved, for the D1 unit, the STRONGER claim that loop-3's
history-reconvergence search (``history_reconvergence_search.py``) could not
reach: a matched non-P actor preimage captured at the REAL target token INSIDE
``_process_frontier`` AFTER membership commit (a POST-commit direct preimage,
repairing loop-3's PRE-commit digest), established by the MSSR candidate's OWN
selective-renewal operation CHANGE_F rather than by an accidental collision.

This module proves, on ONE exposure-positive matched pair sourced from the
loop-3 registered search, that:

* the candidate's CHANGE_F operation (reset the fast recurrent state F = owner
  ``high_hidden`` to its registered zeros initializer, while preserving the slow
  obs-context S and the retained partner-interaction value P) yields a
  BYTE-IDENTICAL post-reset non-P actor preimage across the two controlled arms
  (``Z_not_P,post-CHANGE_F(-) == Z_not_P,post-CHANGE_F(+)``);
* the retained partner-interaction value nevertheless DIFFERS
  (``current_p(-) != current_p(+)``);
* the pre-recurrence action head ``first_logits`` would consume that retained P
  difference, and a P-null ablation (``partner_p=0`` on both arms) removes the
  two-arm logit difference EXACTLY;
* WITHOUT CHANGE_F the same two arms captured at the same post-commit token
  yield DIFFERENT preimages, and the difference is confined to F
  (``high_hidden``) with P per arm unchanged -- the causal control showing the
  match is established BY the CHANGE_F reset, not already present without it.

The S/P/F partition and the CHANGE_F mask are GROUNDED in the abstract D0
contract (``preaction_closure_certificate.py``: ``STATE_ORDER``, ``LEGAL_MASKS``,
``EvaluationTrace``/``validate_trace``).  This module wires ``first_logits`` ONLY
in this harness; production execution and replay still call ``.logits()``.  It
reads the frozen runtime and installs only the already-registered PUBLIC hooks
``install_kernel_capture`` / ``install_preframe_intervention``; it never modifies,
monkeypatches, or replaces any ``ha_ctse_process`` symbol.  It licenses no
scientific or value claim.

Materiality (Pro's false-closure caution): the retained ``|dP|`` and the
``first_logits`` sensitivity ``dLogit/dP`` are SMALL at untrained initialization
(``|dP| ~ 0.043`` gives a logit L2 ~ 2.6e-4).  The claim is the INTERFACE (P
reaches the pre-recurrence head at the matched preimage), not a large or trained
effect.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

import numpy as np
import torch

from experiments.candidates.vsp_06_mssr.history_reconvergence_search import (
    DELTA,
    Design,
    Tape,
    BASE_FAMILY_BY_NAME,
    make_core,
    make_environment,
    registered_designs,
    run_search,
    _partner_flip_primitive,
)

# The abstract D0 contract we ground against (import; never edit).
from experiments.candidates.vsp_06_mssr.preaction_closure_certificate import (
    STATE_ORDER,
    LEGAL_MASKS,
    EvaluationTrace,
    validate_mask,
    validate_trace,
)

# Determinism: loop-3's ``make_core`` already sets this; pin it at import too so
# the harness is thread-count reproducible even before a core is built.
torch.set_num_threads(1)

RAW_OUTPUT_BINDING = "vsp_06_mssr.d1_change_f_matched_pair.v1"

ACTIVE = "ACTIVE"

# --- Terminals ---------------------------------------------------------------
TERMINAL_PRESENT = "MSSR_D1_CHANGE_F_POSTCOMMIT_MATCHED_PAIR_PRESENT"
TERMINAL_NO_EXPOSURE = "MSSR_D1_NO_EXPOSURE_POSITIVE_PAIR_IN_REGISTERED_BUDGET"
TERMINAL_NO_POSTCOMMIT = "MSSR_D1_NO_POSTCOMMIT_MATCH_IN_REGISTERED_BUDGET"

# --- The CHANGE_F mask, grounded in D0 --------------------------------------
#: D0's CHANGE_F mask over ``STATE_ORDER = ("F", "S", "P")``: reset F (bit 0 = 0),
#: preserve S (bit 1 = 1), preserve P (bit 2 = 1).
CHANGE_F_MASK = LEGAL_MASKS["CHANGE_F"]


@dataclass(frozen=True)
class SourcedPair:
    """One frozen exposure-positive matched pair from the loop-3 search."""

    base_family: str
    target_key: str
    partner_key: str
    window: tuple[int, ...]
    physical_time: int
    membership_epoch: int
    delta_p: float

    def design(self) -> Design:
        flip = _partner_flip_primitive(
            BASE_FAMILY_BY_NAME[self.base_family], self.partner_key
        )
        return Design(
            target_key=str(self.target_key),
            partner_key=str(self.partner_key),
            window=tuple(int(step) for step in self.window),
            base_family=str(self.base_family),
            perturb_primitive=int(flip),
        )

    def base_tape(self) -> Tape:
        return Tape.make(0, self.target_key, {}, base_family=self.base_family)

    def perturbed_tape(self) -> Tape:
        return Tape.make(
            0, self.target_key, self.design().perturbation(),
            base_family=self.base_family,
        )


#: The frozen record of the pair the registered search selects first (highest
#: retained ``|dP|`` among exposure-positive, post-commit-matched candidates).
#: ``source_exposure_positive_candidates`` rediscovers it from the search; this
#: constant is the provenance-frozen result and the fast path for the tests.
FROZEN_SOURCED_PAIR = SourcedPair(
    base_family="asym_parity_short",
    target_key="0",
    partner_key="2",
    window=(14,),
    physical_time=40,
    membership_epoch=0,
    delta_p=0.042735756321491264,
)


# ---------------------------------------------------------------------------
# Byte-stable serialization (mirrors loop-3's ``_feed`` / ``_f32_bytes``).
# ---------------------------------------------------------------------------
def _f32_bytes(array) -> bytes:
    return np.ascontiguousarray(np.asarray(array, dtype=np.float32)).tobytes()


def _feed(hasher: "hashlib._Hash", label: bytes, payload: bytes) -> None:
    hasher.update(b"\x1e")
    hasher.update(label)
    hasher.update(b"\x1f")
    hasher.update(payload)


def _f32_copy(tensor_or_array) -> np.ndarray:
    if isinstance(tensor_or_array, torch.Tensor):
        tensor_or_array = tensor_or_array.detach().cpu().numpy()
    return np.ascontiguousarray(np.asarray(tensor_or_array, dtype=np.float32)).copy()


def _int_array_copy(tensor_or_array) -> np.ndarray:
    if isinstance(tensor_or_array, torch.Tensor):
        tensor_or_array = tensor_or_array.detach().cpu().numpy()
    return np.asarray(tensor_or_array).copy()


# ---------------------------------------------------------------------------
# CHANGE_F operation (a preframe hook) and the post-commit capture sink.
# ---------------------------------------------------------------------------
def make_change_f_preframe(target_key: str, physical_time: int):
    """The candidate's CHANGE_F op as a registered preframe intervention.

    Fires (via ``install_preframe_intervention``) once per ``apply_transaction``
    AFTER membership commit, BEFORE the frontier loop.  It resets ONLY the
    target's fast recurrent state F (``high_hidden``) to its registered zeros
    initializer, and ONLY at the single registered application point
    (``core.physical_time == physical_time`` and the target ACTIVE).  It does not
    touch ``partner_interaction_history`` (P preserved), and it touches no other
    record (S and non-descendants preserved) -- exactly D0's CHANGE_F mask
    ``(F=0, S=1, P=1)``.
    """

    target = str(target_key)
    phys = int(physical_time)

    def fn(c) -> None:
        if int(c.physical_time) != phys:
            return
        record = c.records.get(target)
        if record is None or record.status != ACTIVE:
            return
        # Reset F to the registered zeros initializer (production ``_new_record``
        # uses exactly ``np.zeros(high_hidden_dim, np.float32)``).
        record.high_hidden = np.zeros(c.high_hidden_dim, dtype=np.float32)

    return fn


class TargetTokenSink:
    """A kernel-capture sink that records the target's post-commit preimage.

    Installed via ``install_kernel_capture``; ``capture(**kwargs)`` fires INSIDE
    ``_process_frontier`` at every token after ``masked_logits``/softmax and
    before action selection.  This sink filters to the target owner AND the
    frozen physical time, deep-copies the preimage tensors for byte stability,
    and reads the historical (pre-write) ``current_p`` from the record.  It
    returns ``None`` (the runtime interprets nothing), so it perturbs no state.
    """

    def __init__(self, core, target_key: str, physical_time: int) -> None:
        self._core = core
        self._target = str(target_key)
        self._phys = int(physical_time)
        self.captured: dict | None = None

    def capture(self, **kwargs) -> None:
        if str(kwargs["owner_lifecycle_key"]) != self._target:
            return None
        if int(self._core.physical_time) != self._phys:
            return None
        if self.captured is not None:
            return None
        preimage = kwargs["preimage"]
        record = self._core.records[self._target]
        history = record.partner_interaction_history
        current_p = 0.0 if history is None else float(history.current_p)
        self.captured = {
            "owner_lifecycle_key": str(kwargs["owner_lifecycle_key"]),
            "membership_epoch": int(kwargs["membership_epoch"]),
            "token_position": int(kwargs["token_position"]),
            "masked_logits": _f32_copy(kwargs["masked_logits"]),
            "observations": _f32_copy(preimage["observations"]),
            "event_flags": _int_array_copy(preimage["event_flags"]),
            "initial_skills": _int_array_copy(preimage["initial_skills"]),
            "initial_ages": _int_array_copy(preimage["initial_ages"]),
            "pre_token_working_skills": _int_array_copy(
                preimage["pre_token_working_skills"]
            ),
            "pre_token_working_ages": _int_array_copy(
                preimage["pre_token_working_ages"]
            ),
            "pre_token_high_hidden": _f32_copy(preimage["pre_token_high_hidden"]),
            "legal_mask": _int_array_copy(preimage["legal_mask"]),
            "sampled_order": tuple(str(x) for x in preimage["sampled_order"]),
            "active_lifecycle_keys": tuple(
                str(x) for x in preimage["active_lifecycle_keys"]
            ),
            "active_membership_epochs": tuple(
                int(x) for x in preimage["active_membership_epochs"]
            ),
            "architecture_mode": str(preimage["architecture_mode"]),
            "current_p": current_p,
            # Pro's D1 Step-1 field list names the model digest among the
            # materialized preimage: attest the exact parameters this arm's
            # actor ran with (both arms build from the registered seed 57057,
            # so the digests still match -- now provably, not by construction).
            "model_param_checksum": _param_checksum(self._core.commitment_model),
        }
        return None


# ---------------------------------------------------------------------------
# Rollout driver (mirrors loop-3's teacher-forced ``rollout``).
# ---------------------------------------------------------------------------
def _drive(core, env, tape: Tape, *, preframe=None, sink=None) -> None:
    """Replay one legally supported history with optional hooks installed."""
    if sink is not None:
        core.install_kernel_capture(sink)
    if preframe is not None:
        core.install_preframe_intervention(preframe)
    base = tape.base_script()
    perturbation = tape.perturbation_map()

    def handle(bound) -> None:
        post = bound.post_membership_pre_policy_snapshot
        frontier = tuple(post.frontier)
        order = tuple(sorted((str(key) for key in frontier), key=int))
        core.apply_transaction(
            bound,
            teacher_actions={str(key): base.token(str(key)) for key in frontier},
            teacher_order=order,
            deterministic_policy=True,
        )

    transaction = env.reset_event_runtime(tape.episode_id)
    handle(core.bind_due_frontier(transaction))
    while True:
        active = tuple(env.environment.active_keys)
        actions = {int(key): base.primitive(int(key)) for key in active}
        for (step, key), value in perturbation.items():
            if int(step) == int(core.physical_time) and int(key) in actions:
                actions[int(key)] = int(value)
        step_result = env.step_event_runtime(actions)
        core.complete_primitive_transition(float(step_result.reward))
        if step_result.terminated:
            core.close_terminal()
            break
        handle(core.bind_due_frontier(step_result.next_transaction))


def capture_post_change_f(
    tape: Tape, target_key: str, physical_time: int, *, change_f: bool = True
) -> dict:
    """Run one arm with capture (CHANGE_F applied by default); return the
    target's post-commit preimage.

    ``change_f=False`` runs the WITHOUT-CHANGE_F causal-control arm: the SAME
    tape, the SAME post-commit capture point inside ``_process_frontier``, but
    no preframe installed -- the raw preimage CHANGE_F would otherwise have
    reset.  Raises ``RuntimeError`` if the target token at ``physical_time`` is
    never captured (should not happen for a sourced pair; both arms remain
    teacher forced onto the same frontier skeleton).
    """
    core = make_core(0)
    env = make_environment()
    sink = TargetTokenSink(core, target_key, physical_time)
    preframe = (
        make_change_f_preframe(target_key, physical_time) if change_f else None
    )
    _drive(core, env, tape, preframe=preframe, sink=sink)
    if sink.captured is None:
        raise RuntimeError(
            f"target {target_key} produced no token at physical_time {physical_time}"
        )
    return sink.captured


def read_partner_rows(
    tape: Tape, target_key: str, physical_time: int
) -> tuple[tuple[int, str, float], ...]:
    """Read the target's accumulated partner-interaction rows AT ``physical_time``,
    pre-token, in a PLAIN rollout (no CHANGE_F).

    The reader is a preframe that only READS record fields (it mutates nothing),
    so determinism is untouched.  Returns ``(event_index, partner_lifecycle_key,
    payload)`` per row, in append order.
    """
    core = make_core(0)
    env = make_environment()
    target = str(target_key)
    phys = int(physical_time)
    box: dict[str, tuple] = {}

    def reader(c) -> None:
        if int(c.physical_time) != phys or "rows" in box:
            return
        record = c.records.get(target)
        if record is None or record.status != ACTIVE:
            return
        history = record.partner_interaction_history
        if history is None:
            return
        box["rows"] = tuple(
            (int(row.event_index), str(row.partner_lifecycle_key), float(row.payload))
            for row in history.rows
        )

    _drive(core, env, tape, preframe=reader, sink=None)
    return box.get("rows", ())


def exposure_positive(
    base_rows: Sequence[tuple[int, str, float]],
    perturbed_rows: Sequence[tuple[int, str, float]],
) -> bool:
    """True iff a prior differing partner payload actually reached both owners'
    histories.

    ``event_index`` is a token position within an event and repeats across
    events, so the two append-only histories are aligned POSITIONALLY (they share
    the same scripted frontier skeleton, hence the same partner sequence); a
    length mismatch is itself exposure.  Exposure-positive iff some aligned pair
    differs in ``payload`` or ``partner_lifecycle_key``.
    """
    if len(base_rows) != len(perturbed_rows):
        return True
    for base_row, pert_row in zip(base_rows, perturbed_rows):
        if base_row[1] != pert_row[1] or base_row[2] != pert_row[2]:
            return True
    return False


# ---------------------------------------------------------------------------
# The Z_not_P post-CHANGE_F digest (canonical, EXCLUDING P).
# ---------------------------------------------------------------------------
def znp_post_change_f_digest(captured: dict, *, include_high_hidden: bool = True) -> str:
    """Canonical sha256 over the captured post-CHANGE_F preimage, EXCLUDING P.

    Serializes every actor-read field materialized at the target token except the
    partner-interaction value P: byte-stable float32 for arrays, ``repr`` for
    integer arrays / tuples / scalars (mirrors loop-3's ``_feed``/``_f32_bytes``),
    plus the arm's model parameter checksum (Pro's Step-1 "model digest": the
    actor identity is attested inside the digest, not assumed identical by
    construction).  ``pre_token_high_hidden`` is the zeros initializer after
    CHANGE_F.

    ``include_high_hidden=False`` omits ``pre_token_high_hidden`` (feeding a
    constant marker in its slot).  This yields the Z_not_P-minus-F digest used by
    the without-CHANGE_F causal control: it lets the control show that the two
    arms' post-commit preimages differ ONLY in F (``high_hidden``) -- the residual
    CHANGE_F resets -- and in nothing else.
    """
    hasher = hashlib.sha256()
    _feed(hasher, b"binding", RAW_OUTPUT_BINDING.encode())
    _feed(hasher, b"observations", _f32_bytes(captured["observations"]))
    _feed(hasher, b"event_flags", repr(captured["event_flags"].tolist()).encode())
    _feed(hasher, b"initial_skills", repr(captured["initial_skills"].tolist()).encode())
    _feed(hasher, b"initial_ages", repr(captured["initial_ages"].tolist()).encode())
    _feed(
        hasher,
        b"pre_token_working_skills",
        repr(captured["pre_token_working_skills"].tolist()).encode(),
    )
    _feed(
        hasher,
        b"pre_token_working_ages",
        repr(captured["pre_token_working_ages"].tolist()).encode(),
    )
    _feed(
        hasher,
        b"pre_token_high_hidden",
        _f32_bytes(captured["pre_token_high_hidden"])
        if include_high_hidden
        else b"EXCLUDED",
    )
    _feed(hasher, b"legal_mask", repr(captured["legal_mask"].tolist()).encode())
    _feed(hasher, b"sampled_order", repr(captured["sampled_order"]).encode())
    _feed(
        hasher,
        b"active_lifecycle_keys",
        repr(captured["active_lifecycle_keys"]).encode(),
    )
    _feed(
        hasher,
        b"active_membership_epochs",
        repr(captured["active_membership_epochs"]).encode(),
    )
    _feed(hasher, b"architecture_mode", captured["architecture_mode"].encode())
    _feed(hasher, b"token_position", repr(captured["token_position"]).encode())
    _feed(hasher, b"membership_epoch", repr(captured["membership_epoch"]).encode())
    _feed(hasher, b"owner_lifecycle_key", captured["owner_lifecycle_key"].encode())
    _feed(
        hasher,
        b"model_param_checksum",
        captured["model_param_checksum"].encode(),
    )
    # P is DELIBERATELY excluded -- Z_not_P is the registered quotient over P.
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Faithful reconstruction of the target token's actor inputs.
# ---------------------------------------------------------------------------
def reconstruct_actor_inputs(
    model, captured: dict
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Recompute ``(member_embedding, selected_summary, pre_hidden)`` exactly as
    ``_process_frontier`` produces them at the target token (mode ``f1``).

    For ``f1`` the selected summary is the WORKING summary, updated incrementally
    per earlier token; this replays those exact incremental updates from the
    captured preimage (``working_summary[:-1] += new_embedding - old_embedding``),
    so the reconstruction is byte-faithful (verified by matching the captured
    ``masked_logits`` via ``model.logits`` -- see ``faithfulness_ok``).  Because
    every input here is part of the byte-identical Z_not_P preimage, the result
    is identical across the two arms BY CONSTRUCTION; the only cross-arm input to
    ``first_logits`` that differs is ``partner_p``.
    """
    if str(captured["architecture_mode"]) != "f1":
        raise ValueError("reconstruction is registered for architecture_mode='f1'")
    device = torch.device("cpu")
    observations = torch.as_tensor(
        captured["observations"], dtype=torch.float32, device=device
    )
    event_flags = torch.as_tensor(captured["event_flags"], device=device)
    initial_skills = torch.as_tensor(captured["initial_skills"], device=device)
    initial_ages = torch.as_tensor(captured["initial_ages"], device=device)
    pre_skills = torch.as_tensor(captured["pre_token_working_skills"], device=device)
    pre_ages = torch.as_tensor(captured["pre_token_working_ages"], device=device)
    pre_hidden = torch.as_tensor(
        captured["pre_token_high_hidden"], dtype=torch.float32, device=device
    )
    active_keys = list(captured["active_lifecycle_keys"])
    key_to_row = {key: index for index, key in enumerate(active_keys)}
    order = list(captured["sampled_order"])
    target = str(captured["owner_lifecycle_key"])
    target_position = order.index(target)

    with torch.no_grad():
        member_embeddings = model.encode_members(
            observations, initial_skills, initial_ages, event_flags
        )
        working_embeddings = member_embeddings.clone()
        working_summary = model.set_summary(member_embeddings).clone()
        for position in range(target_position):
            row = key_to_row[order[position]]
            new_embedding = model.encode_members(
                observations[row : row + 1],
                pre_skills[row : row + 1],
                pre_ages[row : row + 1],
                event_flags[row : row + 1],
            )[0]
            working_summary = working_summary.clone()
            working_summary[:-1] += new_embedding - working_embeddings[row]
            working_embeddings = working_embeddings.clone()
            working_embeddings[row] = new_embedding
        member_embedding = working_embeddings[key_to_row[target]]
        selected_summary = working_summary
    return member_embedding, selected_summary, pre_hidden


# ---------------------------------------------------------------------------
# Purity helpers (RNG + parameter checksum).
# ---------------------------------------------------------------------------
def _rng_checksum(core) -> str:
    hasher = hashlib.sha256()
    for name in ("opportunity_rng", "frontier_rng", "action_rng"):
        state = getattr(core, name).bit_generator.state
        _feed(hasher, name.encode(), repr(state).encode())
    return hasher.hexdigest()


def _param_checksum(model) -> str:
    hasher = hashlib.sha256()
    for name, parameter in sorted(model.state_dict().items()):
        _feed(hasher, name.encode(), _f32_bytes(parameter.detach().cpu().numpy()))
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# first_logits binding + P-null ablation + purity + trace.
# ---------------------------------------------------------------------------
def first_logits_report(cap_minus: dict, cap_plus: dict) -> dict:
    """Bind ``first_logits`` to the byte-matched preimage and report the P read.

    Uses a FRESH core's model (untrained init, seed 57057).  ``first_logits`` is
    wired ONLY here; production execution and replay still call ``.logits()``.
    """
    core = make_core(0)
    model = core.commitment_model
    if not model.partner_first_action:
        raise RuntimeError("commitment model was not built with partner_first_action")

    member_embedding, selected_summary, pre_hidden = reconstruct_actor_inputs(
        model, cap_minus
    )
    member_embedding_plus, selected_summary_plus, pre_hidden_plus = (
        reconstruct_actor_inputs(model, cap_plus)
    )

    # By construction (byte-identical Z_not_P preimage) the non-P actor inputs
    # coincide across arms; assert it so the first_logits difference is P-only.
    inputs_match = (
        member_embedding.numpy().tobytes() == member_embedding_plus.numpy().tobytes()
        and selected_summary.numpy().tobytes()
        == selected_summary_plus.numpy().tobytes()
        and pre_hidden.numpy().tobytes() == pre_hidden_plus.numpy().tobytes()
    )

    p_minus = float(cap_minus["current_p"])
    p_plus = float(cap_plus["current_p"])

    rng_before = _rng_checksum(core)
    param_before = _param_checksum(model)

    with torch.no_grad():
        # Faithfulness: production ``.logits`` on the reconstructed inputs must
        # reproduce the captured ``masked_logits`` byte-for-byte (legal_mask is
        # all-ones, so masked_logits == logits).
        recon_logits, _ = model.logits(
            member_embedding, selected_summary, pre_hidden
        )
        captured_logits = torch.as_tensor(
            cap_minus["masked_logits"], dtype=torch.float32
        )
        faithfulness_ok = (
            recon_logits.numpy().tobytes() == captured_logits.numpy().tobytes()
        )

        first_minus, _ = model.first_logits(
            member_embedding, selected_summary, pre_hidden, partner_p=p_minus
        )
        first_plus, _ = model.first_logits(
            member_embedding_plus, selected_summary_plus, pre_hidden_plus,
            partner_p=p_plus,
        )
        arm_l2 = float(torch.linalg.norm(first_minus - first_plus))

        # Replay: identical inputs -> byte-identical logits.
        first_minus_replay, _ = model.first_logits(
            member_embedding, selected_summary, pre_hidden, partner_p=p_minus
        )
        replay_identical = (
            first_minus.numpy().tobytes() == first_minus_replay.numpy().tobytes()
        )

        # P-null ablation: partner_p=0 on both arms -> logit difference exactly 0.
        ablate_minus, _ = model.first_logits(
            member_embedding, selected_summary, pre_hidden, partner_p=0.0
        )
        ablate_plus, _ = model.first_logits(
            member_embedding_plus, selected_summary_plus, pre_hidden_plus,
            partner_p=0.0,
        )
        ablation_l2 = float(torch.linalg.norm(ablate_minus - ablate_plus))

        # dLogit/dP by central finite difference at the retained P(-).
        eps = 1e-3
        low, _ = model.first_logits(
            member_embedding, selected_summary, pre_hidden, partner_p=p_minus - eps
        )
        high, _ = model.first_logits(
            member_embedding, selected_summary, pre_hidden, partner_p=p_minus + eps
        )
        d_logit_d_p = ((high - low) / (2.0 * eps)).numpy().tolist()

    rng_after = _rng_checksum(core)
    param_after = _param_checksum(model)

    # SYMBOLIC re-assertion of the D0 ordering contract (first_logits precedes
    # the recurrent update), NOT an empirical measurement of this invocation --
    # the empirical purity of the actual call is rng_unchanged/param_unchanged
    # above, and the structural ground is first_head-before-high_rnn in the
    # model source.
    trace = EvaluationTrace(first_logits_tick=0, recurrent_update_tick=1)
    validate_trace(trace)  # raises if the symbolic ordering is violated

    return {
        "faithfulness_ok": bool(faithfulness_ok),
        "non_p_inputs_match_across_arms": bool(inputs_match),
        "p_minus": p_minus,
        "p_plus": p_plus,
        "arm_l2": arm_l2,
        "ablation_l2": ablation_l2,
        "replay_identical": bool(replay_identical),
        "rng_unchanged": bool(rng_before == rng_after),
        "param_unchanged": bool(param_before == param_after),
        "d_logit_d_p": d_logit_d_p,
        "d_logit_d_p_small": bool(max(abs(v) for v in d_logit_d_p) < 1e-2),
        "first_logits_minus": first_minus.numpy().tolist(),
        "first_logits_plus": first_plus.numpy().tolist(),
        "d0_trace_contract": {
            "first_logits_tick": trace.first_logits_tick,
            "recurrent_update_tick": trace.recurrent_update_tick,
            "symbolic_contract_validated": True,
            "note": (
                "symbolic re-assertion of the D0 ordering contract, not an "
                "empirical measurement of this run; empirical purity is "
                "rng_unchanged/param_unchanged"
            ),
        },
    }


# ---------------------------------------------------------------------------
# Sourcing: exposure-positive candidates from the loop-3 registered search.
# ---------------------------------------------------------------------------
def source_exposure_positive_candidates(
    designs: Sequence[Design] | None = None,
) -> tuple[list[SourcedPair], dict]:
    """Run the loop-3 registered search, keep reconverged P-different comparisons,
    and return those that are ALSO exposure-positive (sorted by descending |dP|).

    Returns ``(candidates, counts)``.  ``counts`` is machine-visible: n
    reconverged (znp_minus_hidden), n reconverged-and-P-different, n
    exposure-positive.
    """
    resolved = registered_designs() if designs is None else tuple(designs)
    result = run_search(resolved)
    reconverged = [c for c in result.comparisons if c.znp_minus_hidden_match]
    p_different = [
        c
        for c in reconverged
        if c.high_hidden_l2_gap > 0.0 and c.delta_p > 0.0
    ]
    p_different.sort(key=lambda c: -c.delta_p)

    candidates: list[SourcedPair] = []
    for comparison in p_different:
        pair = SourcedPair(
            base_family=comparison.base_family,
            target_key=comparison.target_key,
            partner_key=comparison.partner_key,
            window=tuple(comparison.window),
            physical_time=int(comparison.physical_time),
            membership_epoch=int(comparison.membership_epoch),
            delta_p=float(comparison.delta_p),
        )
        base_rows = read_partner_rows(
            pair.base_tape(), pair.target_key, pair.physical_time
        )
        perturbed_rows = read_partner_rows(
            pair.perturbed_tape(), pair.target_key, pair.physical_time
        )
        if exposure_positive(base_rows, perturbed_rows):
            candidates.append(pair)

    counts = {
        "target_opportunities": len(result.comparisons),
        "znp_minus_hidden_reconverged": len(reconverged),
        "reconverged_and_p_different": len(p_different),
        "exposure_positive": len(candidates),
    }
    return candidates, counts


# ---------------------------------------------------------------------------
# The proof entry point.
# ---------------------------------------------------------------------------
def evaluate_pair(pair: SourcedPair) -> dict:
    """CHANGE_F both arms, digest Z_not_P, and run the without-CHANGE_F control.

    The WITHOUT-CHANGE_F causal control re-runs BOTH arms with the identical
    post-commit capture point but no CHANGE_F preframe, and establishes that
    (a) the two raw preimages DIFFER (so the CHANGE_F match is not an accidental
    collision already present without the op), (b) the difference is confined to
    F (their Z_not_P-minus-F digests match), and (c) the retained P is
    CHANGE_F-invariant (identical ``current_p`` per arm with and without the op
    -- the preserved bit P=1 of the mask, observed rather than assumed).
    """
    cap_minus = capture_post_change_f(
        pair.base_tape(), pair.target_key, pair.physical_time
    )
    cap_plus = capture_post_change_f(
        pair.perturbed_tape(), pair.target_key, pair.physical_time
    )
    digest_minus = znp_post_change_f_digest(cap_minus)
    digest_plus = znp_post_change_f_digest(cap_plus)

    nocf_minus = capture_post_change_f(
        pair.base_tape(), pair.target_key, pair.physical_time, change_f=False
    )
    nocf_plus = capture_post_change_f(
        pair.perturbed_tape(), pair.target_key, pair.physical_time, change_f=False
    )
    nocf_digest_minus = znp_post_change_f_digest(nocf_minus)
    nocf_digest_plus = znp_post_change_f_digest(nocf_plus)
    nocf_digests_differ = nocf_digest_minus != nocf_digest_plus
    nocf_minus_hidden_match = znp_post_change_f_digest(
        nocf_minus, include_high_hidden=False
    ) == znp_post_change_f_digest(nocf_plus, include_high_hidden=False)

    return {
        "cap_minus": cap_minus,
        "cap_plus": cap_plus,
        "digest_minus": digest_minus,
        "digest_plus": digest_plus,
        "digest_match": digest_minus == digest_plus,
        "current_p_minus": float(cap_minus["current_p"]),
        "current_p_plus": float(cap_plus["current_p"]),
        "abs_delta_p": abs(
            float(cap_minus["current_p"]) - float(cap_plus["current_p"])
        ),
        "pre_high_hidden_is_initializer": bool(
            np.array_equal(
                cap_minus["pre_token_high_hidden"],
                np.zeros_like(cap_minus["pre_token_high_hidden"]),
            )
            and np.array_equal(
                cap_plus["pre_token_high_hidden"],
                np.zeros_like(cap_plus["pre_token_high_hidden"]),
            )
        ),
        "without_change_f_digests_differ": bool(nocf_digests_differ),
        "without_change_f_only_high_hidden_differs": bool(
            nocf_digests_differ and nocf_minus_hidden_match
        ),
        "without_change_f_high_hidden_l2_gap": float(
            np.linalg.norm(
                np.asarray(nocf_minus["pre_token_high_hidden"], dtype=np.float64)
                - np.asarray(nocf_plus["pre_token_high_hidden"], dtype=np.float64)
            )
        ),
        "without_change_f_p_preserved": bool(
            float(nocf_minus["current_p"]) == float(cap_minus["current_p"])
            and float(nocf_plus["current_p"]) == float(cap_plus["current_p"])
        ),
    }


SCOPE = (
    "Zero-training STRUCTURAL harness. On ONE exposure-positive matched pair "
    "sourced from the loop-3 registered search, the MSSR candidate's OWN CHANGE_F "
    "selective-renewal op (reset F=high_hidden to its registered zeros "
    "initializer, preserve S and P) yields a byte-identical POST-COMMIT DIRECT "
    "target-token preimage Z_not_P across two arms while the retained P differs. "
    "SCOPE / honesty clauses: "
    "(1) POST-COMMIT DIRECT target-token preimage -- captured INSIDE "
    "_process_frontier at the real target token after membership commit and after "
    "earlier tokens (repairs loop-3's PRE-commit digest). "
    "(2) CONTROLLED legal arms -- the two primitive tapes are legal-reachability "
    "controls (high-level event actions have positive model probability, but no "
    "stochastic PRIMITIVE behavior law is registered); sufficient for a "
    "capability search, NOT an observational support/overlap claim. "
    "(3) Z_not_P is a registered QUOTIENT over P grounded in D0's S/P/F partition "
    "(preaction_closure_certificate.py STATE_ORDER/LEGAL_MASKS; CHANGE_F mask "
    "(F=0,S=1,P=1)); it excludes P by construction and is not literally all non-P "
    "runtime state. "
    "(4) The matched support is established by the candidate's OWN CHANGE_F (a "
    "registered reset of F to its initializer), NOT an accidental collision. "
    "(5) The retained |dP| (~0.043) and the first_logits sensitivity dLogit/dP "
    "are SMALL at untrained init (logit L2 ~ 2.6e-4); this is a MATERIALITY fact, "
    "not a trained or large effect. The claim is the INTERFACE (P reaches the "
    "pre-recurrence head at the matched preimage), not an effect size. "
    "(6) first_logits is wired ONLY in this harness; production execution and "
    "replay still call .logits(). "
    "(7) NO claim that P_t = f(high_hidden_t), NO GRU-injectivity claim, and NO "
    "production policy effect of P. A bounded terminal claims only the absence of "
    "a qualifying pair in the registered budget, never impossibility or nullity. "
    "(8) WITHOUT-CHANGE_F CAUSAL CONTROL -- the same two arms captured at the "
    "same post-commit token WITHOUT CHANGE_F yield DIFFERENT Z_not_P digests, "
    "the difference is confined to F (their Z_not_P-minus-F digests match), and "
    "the retained P per arm is identical with and without the op. The "
    "byte-identical matched support is therefore established BY the CHANGE_F "
    "reset (necessary for the match), not already present without it, and "
    "CHANGE_F's observed effect at the capture point is exactly the F reset with "
    "P preserved."
)


def proof() -> dict:
    """Source, CHANGE_F-match, and first_logits-bind one exposure-positive pair."""
    candidates, counts = source_exposure_positive_candidates()
    report: dict = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "scope": SCOPE,
        "delta_materiality_threshold": DELTA,
        "change_f_mask": {
            "state_order": list(STATE_ORDER),
            "mask": list(CHANGE_F_MASK),
            "name": validate_mask(CHANGE_F_MASK),
        },
        "sourcing_counts": counts,
    }

    if not candidates:
        report["terminal"] = TERMINAL_NO_EXPOSURE
        return report

    rejected: list[dict] = []
    for pair in candidates:
        evaluation = evaluate_pair(pair)
        # PAIR-level gate: matched digest, P difference, and the full
        # without-CHANGE_F causal control (including P preservation under the op).
        pair_ok = bool(
            evaluation["digest_match"]
            and evaluation["abs_delta_p"] > 0.0
            and evaluation["without_change_f_digests_differ"]
            and evaluation["without_change_f_only_high_hidden_differs"]
            and evaluation["without_change_f_p_preserved"]
        )
        # BINDING-validity gate: a degenerate first_logits binding (unfaithful
        # reconstruction, cross-arm non-P input mismatch, non-replayable or
        # impure read) may not emit the PRESENT terminal.  The head's arm_l2 /
        # ablation_l2 / dLogit/dP MAGNITUDES stay reported facts, not gates.
        head = (
            first_logits_report(evaluation["cap_minus"], evaluation["cap_plus"])
            if pair_ok
            else None
        )
        binding_ok = pair_ok and bool(
            head["faithfulness_ok"]
            and head["non_p_inputs_match_across_arms"]
            and head["replay_identical"]
            and head["rng_unchanged"]
            and head["param_unchanged"]
        )
        if not binding_ok:
            rejected.append(
                {
                    "base_family": pair.base_family,
                    "target_key": pair.target_key,
                    "partner_key": pair.partner_key,
                    "window": list(pair.window),
                    "physical_time": pair.physical_time,
                    "digest_match": evaluation["digest_match"],
                    "abs_delta_p": evaluation["abs_delta_p"],
                    "without_change_f_digests_differ": evaluation[
                        "without_change_f_digests_differ"
                    ],
                    "without_change_f_only_high_hidden_differs": evaluation[
                        "without_change_f_only_high_hidden_differs"
                    ],
                    "without_change_f_p_preserved": evaluation[
                        "without_change_f_p_preserved"
                    ],
                    "pair_ok": pair_ok,
                    "binding_ok": binding_ok,
                }
            )
            continue

        report["terminal"] = TERMINAL_PRESENT
        report["sourced_pair"] = {
            "base_family": pair.base_family,
            "target_key": pair.target_key,
            "partner_key": pair.partner_key,
            "window": list(pair.window),
            "physical_time": pair.physical_time,
            "membership_epoch": pair.membership_epoch,
        }
        report["post_change_f"] = {
            "digest_minus": evaluation["digest_minus"],
            "digest_plus": evaluation["digest_plus"],
            "digest_match": evaluation["digest_match"],
            "pre_high_hidden_is_initializer": evaluation[
                "pre_high_hidden_is_initializer"
            ],
            "current_p_minus": evaluation["current_p_minus"],
            "current_p_plus": evaluation["current_p_plus"],
            "abs_delta_p": evaluation["abs_delta_p"],
            "without_change_f_digests_differ": evaluation[
                "without_change_f_digests_differ"
            ],
            "without_change_f_only_high_hidden_differs": evaluation[
                "without_change_f_only_high_hidden_differs"
            ],
            "without_change_f_high_hidden_l2_gap": evaluation[
                "without_change_f_high_hidden_l2_gap"
            ],
            "without_change_f_p_preserved": evaluation[
                "without_change_f_p_preserved"
            ],
        }
        report["first_logits"] = head
        report["rejected_before_match"] = rejected
        return report

    # Exposure-positive pairs existed but none reconverged post-commit.
    report["terminal"] = TERMINAL_NO_POSTCOMMIT
    report["rejected_before_match"] = rejected
    return report


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2, default=str))

"""MSSR passive-carrier history-reconvergence search (zero training, structural).

External Pro ruling ``MSSR_MATCHED_SUPPORT_HISTORY_RECONVERGENCE_REQUIRED``
directed the successor to the current-source coupling witness
(``matched_support_reachability``).  That sibling established only that varying
the CURRENT partner observation moves both the current write payload and the
current actor context; Pro reserved the STRONGER matched-support claim for a
LEGAL-HISTORY RECONVERGENCE search under the production 15-dim dynamic-roster
law: two legally supported histories ``H-`` and ``H+`` that reach, at ONE target
owner opportunity, a BYTE-IDENTICAL canonical non-P pre-action state ``Z_not_P``
but a DIFFERENT retained partner-interaction value ``P``.

This module runs exactly that bounded, registered search over the FROZEN
behavior law and the production model (seed 57057, mode ``f1``, the 15-dim law --
NOT the 3-dim fixture).  It licenses no scientific or value claim and wires no
model head.  A positive EXACT replayable witness would be sufficient; when none
is found in the registered budget the ONLY terminal it may assert is
``MSSR_MATCHED_HISTORY_NO_WITNESS_IN_REGISTERED_BUDGET`` -- never structural
nullity or unreachability.  The residual ``high_hidden`` gap reported on a
bounded failure is a MEASURED property of the finite search, not a nullity.

Design (passive carrier)
------------------------
Two arms share the SAME ``episode_id`` and therefore the SAME scripted
membership / wave / frontier / opportunity-gap skeleton and the SAME three RNG
streams (teacher-forced order and actions never draw the frontier or action
streams; the opportunity stream is consumed identically).  The BASE arm runs a
fixed legal script -- every event token ``PERSIST`` and every primitive ``IDLE``.
The PERTURBED arm is identical EXCEPT that one partner ``j``'s PRIMITIVE actions
are set to ``SHORT`` inside an early window; the owner ``i``'s own tokens and
primitives are byte-identical across arms (``i`` is a passive carrier).  The
``IDLE`` base keeps global wave completion and persistent duty matched across
arms, so the only divergence is ``j``'s private observation (its ``previous_action``
and, under an active wave, ``short_streak``), which the environment forgets a
step or two after the window.  ``i``'s retained ``P`` and ``high_hidden`` pick up
the transient only if ``i`` has an opportunity while ``j``'s observation is still
divergent, and both then carry it forward (``P`` through its 0.8-retention EMA,
``high_hidden`` through the GRU carry).

At every physical time where owner ``i`` is in the frontier of BOTH arms (a
target opportunity) we read, BEFORE that opportunity's token is processed, the
canonical non-P pre-action digest ``Z_not_P`` (which INCLUDES ``i``'s
``high_hidden`` and EXCLUDES only ``i``'s ``partner_interaction_history``) and the
historical scalar ``P`` the owner's head would consume at that opportunity.

Terminal
--------
* POSITIVE witness iff some target opportunity has byte-identical full
  ``Z_not_P`` across arms AND ``|P_base - P_perturbed| >= DELTA``.
* ELSE ``MSSR_MATCHED_HISTORY_NO_WITNESS_IN_REGISTERED_BUDGET`` with a
  machine-visible obstruction residual: among target opportunities where
  ``Z_not_P``-MINUS-``high_hidden`` reconverged (env + every active member's
  skills/ages/flags + the three RNG states all byte-identical) AND
  ``|dP| >= DELTA``, the minimum L2 ``high_hidden`` gap and the ``dP`` there.  If
  that set is empty the counts say so explicitly, and the reconverged set's
  maximum observed ``|dP|`` and minimum ``high_hidden`` gap are reported so the
  residual is not vacuous.

False-closure guards (Pro's list)
---------------------------------
* temporal-index: the target ``P`` is read BEFORE the target-time token, so the
  historical ``P_t`` a head would consume is compared, never the current write
  ``P_{t+1}``.
* fixture-to-environment: the production 15-dim law and the production model are
  used, not the 3-dim fixture.
* downstream-state: ``Z_not_P`` carries the owner's PRE-token ``high_hidden`` (the
  ``pre_hidden`` the actor reads), which is exactly what ``_process_frontier``
  consumes before the write.
* local-to-global / aggregate-alias: the digest includes every active member's
  observation (the source of the set summary) and the target's own pre-token
  state, so a reconvergence is of the whole actor-visible pre-action state, not a
  local slice.
* unwired-head: no model head is added, invoked, or trained; the search only
  reads the frozen runtime's records.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_testbed import (
    IDLE,
    MAX_LIFECYCLES,
    PERSIST,
    SHORT,
    TRAIN_LEDGER_SEED,
)
from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEventEnv,
)
from ha_ctse_process.variable_roster_event import (
    SUPPLIED_EXECUTOR_RUNTIME,
    VariableRosterEventCore,
)

RAW_OUTPUT_BINDING = "vsp_06_mssr.history_reconvergence_search.v1"

# --- Verified wiring constants (a CPU spike reproduced these exactly). --------
MODEL_SEED = 57_057
OPPORTUNITY_SEED = 77_057
FRONTIER_SEED = 77_057
ACTION_SEED = 87_057
OBSERVATION_DIM = 15
ACTION_COUNT = 3
N_SKILLS = 3
HIGH_HIDDEN_DIM = 64
MEMBER_HIDDEN_DIM = 64
LOW_HIDDEN_DIM = 64
SKILL_EMBEDDING_DIM = 16
CRITIC_GLOBAL_DIM = 8

# Fixed legal script: every event token PERSIST, every primitive IDLE.  IDLE
# leaves global wave completion and persistent duty untouched, so a partner's
# windowed SHORT perturbation stays private to that partner's observation and the
# environment forgets it.
BASE_TOKEN = PERSIST
BASE_PRIMITIVE = IDLE
PERTURBATION_PRIMITIVE = SHORT

# --- Precommitted decision threshold (documented, frozen). -------------------
#: A witness (or a qualifying residual opportunity) requires the retained partner
#: interaction values to differ by at least this much.  Precommitted, not tuned
#: to any observed number.
DELTA = 0.05


class BaseScript:
    """A per-lifecycle legal script: a name, a primitive rule and a token rule.

    Applied IDENTICALLY across the base and perturbed arms; the two arms differ
    only in the single perturbation override.  ``primitive(key)`` returns an
    environment primitive in ``{IDLE, PERSIST, SHORT}``; ``token(key)`` returns an
    event token in ``[0, ACTION_COUNT)``.
    """

    def __init__(self, name, primitive_rule, token_rule):
        self.name = str(name)
        self._primitive_rule = primitive_rule
        self._token_rule = token_rule

    def primitive(self, key: int) -> int:
        return int(self._primitive_rule(int(key)))

    def token(self, key: str) -> int:
        return int(self._token_rule(str(key)))


#: Registered base families.  ``sym_persist_idle`` is the symmetric control
#: (payload-degenerate, ΔP capped low); the two asymmetric families break the
#: observation symmetry so a partner perturbation can move the owner's retained
#: payload, giving the retained ΔP its best shot.
SYM_PERSIST_IDLE = BaseScript(
    "sym_persist_idle", lambda key: IDLE, lambda key: PERSIST
)
ASYM_PARITY_SHORT = BaseScript(
    "asym_parity_short",
    lambda key: SHORT if key % 2 == 0 else IDLE,
    lambda key: PERSIST,
)
ASYM_THIRDS = BaseScript(
    "asym_thirds",
    lambda key: (SHORT, IDLE, PERSIST)[key % 3],
    lambda key: int(key) % 3,
)
BASE_FAMILIES: tuple[BaseScript, ...] = (
    SYM_PERSIST_IDLE,
    ASYM_PARITY_SHORT,
    ASYM_THIRDS,
)
BASE_FAMILY_BY_NAME: dict[str, BaseScript] = {b.name: b for b in BASE_FAMILIES}

#: Symmetric default script names (kept so unqualified rollouts stay symmetric).
DEFAULT_BASE_FAMILY = SYM_PERSIST_IDLE.name


@dataclass(frozen=True)
class Design:
    """One resolved perturbation design: a base family + a single-step flip.

    The perturbation flips ``partner_key``'s primitive at each step in ``window``
    (a single near-target step in the registered budget) to ``perturb_primitive``,
    which is ``SHORT`` unless the base family already drives that partner ``SHORT``,
    in which case it is ``IDLE`` (so the flip is always a genuine change).
    """

    target_key: str
    partner_key: str
    window: tuple[int, ...]
    base_family: str = DEFAULT_BASE_FAMILY
    perturb_primitive: int = PERTURBATION_PRIMITIVE
    target_opportunity: int = -1
    lead: int = -1

    def perturbation(self) -> dict[tuple[int, str], int]:
        return {
            (int(step), str(self.partner_key)): int(self.perturb_primitive)
            for step in self.window
        }


# --- Registered budget spec (episode ids, base families, design shape). -------
EPISODE_IDS: tuple[int, ...] = (0,)

#: The handful of (target, partner) pairs probed under every base family, chosen
#: (locally) to surface the largest retained P difference the passive-carrier
#: design admits, so the anti-correlation with the high_hidden gap is visible.
DESIGN_TARGET_PARTNERS: tuple[tuple[str, str], ...] = (
    ("0", "2"),
    ("0", "3"),
    ("2", "1"),
)
#: Perturb the partner this many steps before a target opportunity.
LEADS: tuple[int, ...] = (1, 2, 3)
#: Place perturbations before the target's last this-many opportunities.
LAST_N_OPPORTUNITIES: int = 3


def _partner_flip_primitive(base: BaseScript, partner_key: str) -> int:
    """The genuine flip: SHORT unless the base already drives the partner SHORT."""
    return IDLE if base.primitive(int(partner_key)) == SHORT else SHORT


# ---------------------------------------------------------------------------
# Deterministic CPU harness (verified recipe).
# ---------------------------------------------------------------------------
def make_core(episode_id: int, *, partner_interaction_enabled: bool = True) -> VariableRosterEventCore:
    """Build the production supplied-executor event core exactly per the recipe."""
    torch.set_num_threads(1)
    torch.manual_seed(MODEL_SEED)
    return VariableRosterEventCore(
        architecture_mode="f1",
        obs_dim=OBSERVATION_DIM,
        critic_member_dim=OBSERVATION_DIM,
        critic_global_dim=CRITIC_GLOBAL_DIM,
        n_skills=N_SKILLS,
        action_dim=ACTION_COUNT,
        member_hidden_dim=MEMBER_HIDDEN_DIM,
        high_hidden_dim=HIGH_HIDDEN_DIM,
        low_hidden_dim=LOW_HIDDEN_DIM,
        skill_embedding_dim=SKILL_EMBEDDING_DIM,
        gamma=0.99,
        gae_lambda=0.95,
        environment_index=0,
        opportunity_seed=OPPORTUNITY_SEED,
        frontier_seed=FRONTIER_SEED,
        action_seed=ACTION_SEED,
        rng_episode_id=int(episode_id),
        opportunity_stream_id=0,
        frontier_stream_id=1,
        action_stream_id=0,
        device=torch.device("cpu"),
        partner_interaction_enabled=bool(partner_interaction_enabled),
        runtime_mode=SUPPLIED_EXECUTOR_RUNTIME,
    )


def make_environment() -> CleanProcessDynamicRosterEventEnv:
    return CleanProcessDynamicRosterEventEnv(task_master_seed=TRAIN_LEDGER_SEED)


# ---------------------------------------------------------------------------
# Canonical serialization primitives.
# ---------------------------------------------------------------------------
def _f32_bytes(array) -> bytes:
    return np.ascontiguousarray(np.asarray(array, dtype=np.float32)).tobytes()


def _feed(hasher: "hashlib._Hash", label: bytes, payload: bytes) -> None:
    hasher.update(b"\x1e")
    hasher.update(label)
    hasher.update(b"\x1f")
    hasher.update(payload)


def _environment_bytes(env: CleanProcessDynamicRosterEventEnv) -> bytes:
    """A deterministic primitive serialization of the actor-visible env state.

    This encodes exactly the content of ``env.environment.snapshot_state()`` that
    the 15-dim dynamic-roster law exposes -- the global schedule scalars, the
    active wave, every active member's full 15-dim observation, and every
    lifecycle's raw integer state -- in a byte-stable primitive form.  The
    audit-only clean-process actuator trace is deliberately excluded: it is not an
    actor or critic input and never changes reward or task dynamics.
    """
    world = env.environment
    hasher = hashlib.sha256()
    _feed(hasher, b"time", repr(int(world.time)).encode())
    _feed(hasher, b"persistent_owner", repr(world.persistent_owner).encode())
    _feed(hasher, b"persistent_units", repr(int(world.persistent_units)).encode())
    _feed(hasher, b"short_required", repr(int(world.short_required_total)).encode())
    _feed(hasher, b"short_completed", repr(int(world.short_completed_total)).encode())
    wave = world.current_wave
    if wave is None:
        _feed(hasher, b"wave", b"None")
    else:
        _feed(
            hasher,
            b"wave",
            repr(
                (
                    int(wave.index),
                    int(wave.arrival_time),
                    int(wave.required_work),
                    int(wave.deadline_exclusive),
                    int(wave.completed_work),
                )
            ).encode(),
        )
    view = world.observe()
    for key, observation in sorted(
        zip(view.active_keys, view.observations), key=lambda pair: int(pair[0])
    ):
        _feed(hasher, b"obs:" + repr(int(key)).encode(), _f32_bytes(observation))
    for key in range(MAX_LIFECYCLES):
        state = world.lifecycles[int(key)]
        _feed(
            hasher,
            b"life:" + repr(int(key)).encode(),
            repr(
                (
                    str(state.status),
                    int(state.previous_action),
                    int(state.active_steps),
                    int(state.short_streak),
                    bool(state.contributed_current_wave),
                    int(state.membership_epoch),
                )
            ).encode(),
        )
    return hasher.digest()


def _active_member_core_bytes(
    core: VariableRosterEventCore, active_keys: Sequence[object]
) -> bytes:
    """Every active member's CORE skills/ages/event-flag fields and status.

    These feed ``pack_active`` -> ``set_summary``, which drives the owner's
    ``high_hidden``.  Members joining THIS event have no record yet (records are
    created inside ``apply_transaction``); they are byte-identical fresh defaults
    across arms, so they are encoded with a canonical ``FRESH`` marker.
    """
    hasher = hashlib.sha256()
    for key in sorted((str(item) for item in active_keys), key=int):
        record = core.records.get(key)
        if record is None:
            _feed(hasher, key.encode(), b"FRESH")
            continue
        _feed(
            hasher,
            key.encode(),
            repr(
                (
                    None if record.active_skill is None else int(record.active_skill),
                    int(record.skill_active_age),
                    bool(record.is_genuine_join),
                    bool(record.is_rejoin),
                    str(record.status),
                )
            ).encode(),
        )
    return hasher.digest()


def _rng_bytes(core: VariableRosterEventCore) -> bytes:
    hasher = hashlib.sha256()
    for name in ("opportunity_rng", "frontier_rng", "action_rng"):
        state = getattr(core, name).bit_generator.state
        _feed(hasher, name.encode(), repr(state).encode())
    return hasher.digest()


def canonical_non_p_digest(
    core: VariableRosterEventCore,
    env: CleanProcessDynamicRosterEventEnv,
    target_key: str,
    *,
    frontier: Sequence[object],
    teacher_order: Sequence[object] | None = None,
    include_target_high_hidden: bool = True,
) -> str:
    """SHA-256 of the canonical non-P pre-action state ``Z_not_P``.

    Computed AT a target owner opportunity, BEFORE that owner's token is
    processed.  Serializes EXACTLY (excluding only the target owner's
    ``partner_interaction_history``):

    * the environment state at this physical time (the full 15-dim observation of
      every active member plus the global schedule scalars and wave);
    * physical time, the target key and its membership epoch;
    * every active member's core skills/ages/event-flag fields and status;
    * the target owner's non-P record fields -- ``high_hidden`` (byte-exact,
      when ``include_target_high_hidden``), active skill, skill age, gap, join /
      rejoin flags, status and policy version;
    * the frontier tuple and the target owner's token position in
      ``teacher_order``;
    * the three RNG states (opportunity / frontier / action).

    ``include_target_high_hidden=False`` yields the ``Z_not_P``-minus-``high_hidden``
    digest the search uses to detect environment/skill/RNG reconvergence
    independently of the residual ``high_hidden`` gap.
    """
    order = (
        tuple(str(item) for item in sorted((str(k) for k in frontier), key=int))
        if teacher_order is None
        else tuple(str(item) for item in teacher_order)
    )
    record = core.records[str(target_key)]
    hasher = hashlib.sha256()
    _feed(hasher, b"binding", RAW_OUTPUT_BINDING.encode())
    _feed(hasher, b"env", _environment_bytes(env))
    _feed(hasher, b"physical_time", repr(int(core.physical_time)).encode())
    active_keys = tuple(env.environment.active_keys)
    _feed(hasher, b"members", _active_member_core_bytes(core, active_keys))
    _feed(
        hasher,
        b"target",
        repr(
            (
                str(target_key),
                int(record.membership_epoch),
                None if record.active_skill is None else int(record.active_skill),
                int(record.skill_active_age),
                int(record.active_gap_remaining or 0),
                bool(record.is_genuine_join),
                bool(record.is_rejoin),
                str(record.status),
                int(record.policy_version),
            )
        ).encode(),
    )
    if include_target_high_hidden:
        _feed(hasher, b"target_high_hidden", _f32_bytes(record.high_hidden))
    _feed(
        hasher,
        b"frontier",
        repr(tuple(str(item) for item in frontier)).encode(),
    )
    _feed(hasher, b"teacher_order", repr(order).encode())
    _feed(hasher, b"token_position", repr(order.index(str(target_key))).encode())
    _feed(hasher, b"rng", _rng_bytes(core))
    return hasher.hexdigest()


def high_hidden_bytes(core: VariableRosterEventCore, target_key: str) -> bytes:
    """The owner's pre-action ``high_hidden`` (64,) float32, byte-exact."""
    return _f32_bytes(core.records[str(target_key)].high_hidden)


def current_p(core: VariableRosterEventCore, target_key: str) -> float:
    """The historical retained ``P`` the owner's head would consume (0.0 if none)."""
    record = core.records.get(str(target_key))
    if record is None:
        return 0.0
    history = record.partner_interaction_history
    return 0.0 if history is None else float(history.current_p)


# ---------------------------------------------------------------------------
# Rollout of one legally supported history.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Opportunity:
    """One target owner opportunity, read BEFORE that opportunity's token."""

    physical_time: int
    membership_epoch: int
    znp_digest: str
    znp_minus_hidden_digest: str
    p_value: float
    high_hidden: bytes


@dataclass(frozen=True)
class Tape:
    """A replayable history: episode id, base family, target owner, perturbation."""

    episode_id: int
    target_key: str
    perturbation: tuple[tuple[int, str, int], ...]
    base_family: str = DEFAULT_BASE_FAMILY

    @classmethod
    def make(
        cls,
        episode_id: int,
        target_key: str,
        perturbation: Mapping[tuple[int, str], int],
        *,
        base_family: str = DEFAULT_BASE_FAMILY,
    ) -> "Tape":
        items = tuple(
            (int(step), str(key), int(value))
            for (step, key), value in sorted(perturbation.items())
        )
        return cls(int(episode_id), str(target_key), items, str(base_family))

    def perturbation_map(self) -> dict[tuple[int, str], int]:
        return {(step, key): value for step, key, value in self.perturbation}

    def base_script(self) -> BaseScript:
        return BASE_FAMILY_BY_NAME[self.base_family]


def rollout(tape: Tape) -> dict[int, Opportunity]:
    """Replay one legally supported history and read every target opportunity.

    Returns ``{physical_time: Opportunity}`` for every physical time at which the
    target owner is in the (post-membership) frontier and already has a record --
    i.e. every LATER opportunity, never the owner's own genuine-join boundary
    (records are created inside ``apply_transaction``, so the join event has no
    pre-token record and no accumulated history to read).
    """
    core = make_core(tape.episode_id)
    env = make_environment()
    base = tape.base_script()
    perturbation = tape.perturbation_map()
    target = str(tape.target_key)
    opportunities: dict[int, Opportunity] = {}

    def handle(bound) -> None:
        post = bound.post_membership_pre_policy_snapshot
        frontier = tuple(post.frontier)
        order = tuple(sorted((str(key) for key in frontier), key=int))
        frontier_keys = {str(key) for key in frontier}
        record = core.records.get(target)
        if target in frontier_keys and record is not None:
            opportunities[int(core.physical_time)] = Opportunity(
                physical_time=int(core.physical_time),
                membership_epoch=int(record.membership_epoch),
                znp_digest=canonical_non_p_digest(
                    core, env, target, frontier=frontier, teacher_order=order,
                    include_target_high_hidden=True,
                ),
                znp_minus_hidden_digest=canonical_non_p_digest(
                    core, env, target, frontier=frontier, teacher_order=order,
                    include_target_high_hidden=False,
                ),
                p_value=current_p(core, target),
                high_hidden=high_hidden_bytes(core, target),
            )
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
    return opportunities


@dataclass
class OpportunityState:
    """A live pre-apply snapshot at a target opportunity (for structural probes)."""

    core: VariableRosterEventCore
    env: CleanProcessDynamicRosterEventEnv
    target_key: str
    frontier: tuple[str, ...]
    teacher_order: tuple[str, ...]

    def digest(self, *, include_target_high_hidden: bool = True) -> str:
        return canonical_non_p_digest(
            self.core,
            self.env,
            self.target_key,
            frontier=self.frontier,
            teacher_order=self.teacher_order,
            include_target_high_hidden=include_target_high_hidden,
        )


def capture_opportunity_state(tape: Tape) -> OpportunityState:
    """Drive the history to the target's FIRST opportunity, before its token.

    Returns the live ``core``/``env`` positioned exactly where
    ``canonical_non_p_digest`` is read, without applying that opportunity's
    transaction -- so a test can perturb one field and observe the digest move.
    """
    core = make_core(tape.episode_id)
    env = make_environment()
    base = tape.base_script()
    perturbation = tape.perturbation_map()
    target = str(tape.target_key)

    def at_opportunity(bound) -> OpportunityState | None:
        post = bound.post_membership_pre_policy_snapshot
        frontier = tuple(str(key) for key in post.frontier)
        order = tuple(sorted(frontier, key=int))
        if target in frontier and core.records.get(target) is not None:
            return OpportunityState(core, env, target, frontier, order)
        return None

    def apply(bound) -> None:
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
    bound = core.bind_due_frontier(transaction)
    state = at_opportunity(bound)
    if state is not None:
        return state
    apply(bound)
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
            raise RuntimeError("target never reached an opportunity in this history")
        bound = core.bind_due_frontier(step_result.next_transaction)
        state = at_opportunity(bound)
        if state is not None:
            return state
        apply(bound)


# ---------------------------------------------------------------------------
# The bounded search.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OpportunityComparison:
    episode_id: int
    base_family: str
    target_key: str
    partner_key: str
    window: tuple[int, ...]
    physical_time: int
    membership_epoch: int
    znp_full_match: bool
    znp_minus_hidden_match: bool
    delta_p: float
    high_hidden_l2_gap: float


@dataclass
class SearchResult:
    comparisons: list[OpportunityComparison] = field(default_factory=list)
    witnesses: list[dict[str, object]] = field(default_factory=list)


def _high_hidden_l2_gap(left: bytes, right: bytes) -> float:
    a = np.frombuffer(left, dtype=np.float32)
    b = np.frombuffer(right, dtype=np.float32)
    return float(np.linalg.norm(a - b))


def registered_designs() -> tuple[Design, ...]:
    """The strengthened budget: for every base family and (target, partner) pair,
    a single-step partner flip placed ``lead`` steps before each of the target's
    last ``LAST_N_OPPORTUNITIES`` opportunities.

    The target's opportunity physical times are read from that family's own base
    rollout, so the concrete steps are a DETERMINISTIC function of the registered
    spec (base families, target/partner pairs, leads, last-N) and the frozen law.
    """
    designs: list[Design] = []
    opportunity_cache: dict[tuple[int, str, str], list[int]] = {}
    for episode_id in EPISODE_IDS:
        for base in BASE_FAMILIES:
            for target_key, partner_key in DESIGN_TARGET_PARTNERS:
                cache_key = (int(episode_id), base.name, str(target_key))
                if cache_key not in opportunity_cache:
                    opportunity_cache[cache_key] = sorted(
                        rollout(
                            Tape.make(
                                episode_id, target_key, {}, base_family=base.name
                            )
                        )
                    )
                opportunities = opportunity_cache[cache_key]
                flip = _partner_flip_primitive(base, partner_key)
                for opportunity in opportunities[-LAST_N_OPPORTUNITIES:]:
                    for lead in LEADS:
                        step = int(opportunity) - int(lead)
                        if step < 0:
                            continue
                        designs.append(
                            Design(
                                target_key=str(target_key),
                                partner_key=str(partner_key),
                                window=(step,),
                                base_family=base.name,
                                perturb_primitive=int(flip),
                                target_opportunity=int(opportunity),
                                lead=int(lead),
                            )
                        )
    return tuple(designs)


def _compare_arms(
    episode_id: int,
    design: Design,
    base: dict[int, Opportunity],
    perturbed: dict[int, Opportunity],
) -> list[OpportunityComparison]:
    comparisons: list[OpportunityComparison] = []
    for physical_time in sorted(set(base) & set(perturbed)):
        base_opp = base[physical_time]
        pert_opp = perturbed[physical_time]
        comparisons.append(
            OpportunityComparison(
                episode_id=int(episode_id),
                base_family=design.base_family,
                target_key=design.target_key,
                partner_key=design.partner_key,
                window=tuple(design.window),
                physical_time=int(physical_time),
                membership_epoch=int(base_opp.membership_epoch),
                znp_full_match=(base_opp.znp_digest == pert_opp.znp_digest),
                znp_minus_hidden_match=(
                    base_opp.znp_minus_hidden_digest
                    == pert_opp.znp_minus_hidden_digest
                ),
                delta_p=abs(base_opp.p_value - pert_opp.p_value),
                high_hidden_l2_gap=_high_hidden_l2_gap(
                    base_opp.high_hidden, pert_opp.high_hidden
                ),
            )
        )
    return comparisons


def run_search(designs: Sequence[Design] | None = None) -> SearchResult:
    """Roll out both arms of every registered design and compare each opportunity."""
    resolved = tuple(registered_designs() if designs is None else designs)
    result = SearchResult()
    base_cache: dict[tuple[int, str, str], dict[int, Opportunity]] = {}
    for episode_id in EPISODE_IDS:
        for design in resolved:
            key = (int(episode_id), design.base_family, design.target_key)
            if key not in base_cache:
                base_cache[key] = rollout(
                    Tape.make(
                        episode_id, design.target_key, {},
                        base_family=design.base_family,
                    )
                )
            base = base_cache[key]
            perturbed = rollout(
                Tape.make(
                    episode_id, design.target_key, design.perturbation(),
                    base_family=design.base_family,
                )
            )
            for comparison in _compare_arms(episode_id, design, base, perturbed):
                result.comparisons.append(comparison)
                if comparison.znp_full_match and comparison.delta_p >= DELTA:
                    result.witnesses.append(
                        {
                            "episode_id": int(episode_id),
                            "base_family": design.base_family,
                            "target_key": design.target_key,
                            "partner_key": design.partner_key,
                            "window": list(design.window),
                            "physical_time": comparison.physical_time,
                            "membership_epoch": comparison.membership_epoch,
                            "delta_p": comparison.delta_p,
                        }
                    )
    return result


def verify_witness_replay(design: Design, episode_id: int, physical_time: int) -> dict[str, object]:
    """Re-run both arms of a witness and confirm the exact replay at the target."""
    base = rollout(
        Tape.make(episode_id, design.target_key, {}, base_family=design.base_family)
    )
    perturbed = rollout(
        Tape.make(
            episode_id, design.target_key, design.perturbation(),
            base_family=design.base_family,
        )
    )
    base_opp = base[int(physical_time)]
    pert_opp = perturbed[int(physical_time)]
    return {
        "znp_digest": base_opp.znp_digest,
        "znp_byte_identical": base_opp.znp_digest == pert_opp.znp_digest,
        "p_base": base_opp.p_value,
        "p_perturbed": pert_opp.p_value,
        "delta_p": abs(base_opp.p_value - pert_opp.p_value),
    }


def _obstruction_residual(result: SearchResult) -> dict[str, object]:
    comparisons = result.comparisons
    reconverged = [c for c in comparisons if c.znp_minus_hidden_match]
    reconverged_delta = [c for c in reconverged if c.delta_p >= DELTA]
    reconverged_hidden_residual = [
        c for c in reconverged if c.high_hidden_l2_gap > 0.0
    ]
    full_match = [c for c in comparisons if c.znp_full_match]

    residual: dict[str, object] = {
        "note": (
            "MEASURED property of the FINITE registered search. It is NOT a claim "
            "that the matched state is impossible to reach and NOT a claim that the "
            "underlying structure is empty. Reports the retained high_hidden "
            "obstruction at opportunities where the environment, every active "
            "member's skills/ages/flags, and the three RNG states reconverged "
            "byte-identically."
        ),
        "delta": DELTA,
        "counts": {
            "target_opportunities": len(comparisons),
            "znp_minus_hidden_reconverged": len(reconverged),
            "reconverged_and_delta_p_ge_delta": len(reconverged_delta),
            # The meaningful obstruction: env + skills/ages/flags + RNG all
            # reconverged byte-identically, yet the owner's high_hidden retained a
            # nonzero L2 gap (the GRU carry did not forget what the env did).
            "reconverged_with_high_hidden_residual": len(reconverged_hidden_residual),
            # Opportunities where the FULL Z_not_P (high_hidden included) was byte
            # identical; a witness would additionally require |dP| >= DELTA there.
            "znp_full_byte_identical": len(full_match),
        },
    }

    # --- Anti-correlation, measured over ALL comparisons (all base families). --
    full_match_delta_ps = [c.delta_p for c in full_match]
    residual["full_match_max_delta_p"] = (
        max(full_match_delta_ps) if full_match_delta_ps else 0.0
    )
    residual["full_match_with_delta_p_gt_zero_count"] = sum(
        1 for c in full_match if c.delta_p > 0.0
    )
    if reconverged:
        rc_max_dp = max(reconverged, key=lambda c: c.delta_p)
        rc_min_gap = min(reconverged, key=lambda c: c.high_hidden_l2_gap)
        residual["reconverged_minus_hidden_max_delta_p"] = rc_max_dp.delta_p
        residual["reconverged_minus_hidden_max_delta_p_high_hidden_l2_gap"] = (
            rc_max_dp.high_hidden_l2_gap
        )
        residual["reconverged_minus_hidden_min_high_hidden_l2_gap"] = (
            rc_min_gap.high_hidden_l2_gap
        )
        residual["reconverged_minus_hidden_min_gap_delta_p"] = rc_min_gap.delta_p
    else:
        residual["reconverged_minus_hidden_max_delta_p"] = 0.0
        residual["reconverged_minus_hidden_max_delta_p_high_hidden_l2_gap"] = 0.0
        residual["reconverged_minus_hidden_min_high_hidden_l2_gap"] = None
        residual["reconverged_minus_hidden_min_gap_delta_p"] = None
    residual["anti_correlation_note"] = (
        "MEASURED over ALL comparisons across the sym+asym base families: when the "
        "FULL Z_not_P (high_hidden included) reconverges byte-identically the "
        "retained |dP| is 0 (P has reconverged too), and among opportunities where "
        "only Z_not_P-minus-high_hidden reconverges the retained |dP| and the "
        "high_hidden L2 gap CO-VARY (a larger dP goes with a larger gap). This is a "
        "property of the FINITE search, NOT a claim that the matched state is "
        "impossible to reach, NOT a claim of structural emptiness, and NOT a claim "
        "that the GRU carry is globally injective."
    )

    if not reconverged:
        residual["reconverged_any"] = False
        residual["reconverged_and_delta_present"] = False
        residual["min_high_hidden_l2_gap_over_reconverged_and_delta"] = None
        return residual

    residual["reconverged_any"] = True
    max_dp = max(reconverged, key=lambda c: c.delta_p)
    min_gap = min(reconverged, key=lambda c: c.high_hidden_l2_gap)
    residual["reconverged_summary"] = {
        "max_delta_p": max_dp.delta_p,
        "high_hidden_l2_gap_at_max_delta_p": max_dp.high_hidden_l2_gap,
        "physical_time_at_max_delta_p": max_dp.physical_time,
        "min_high_hidden_l2_gap": min_gap.high_hidden_l2_gap,
        "delta_p_at_min_high_hidden_l2_gap": min_gap.delta_p,
    }

    if reconverged_delta:
        best = min(reconverged_delta, key=lambda c: c.high_hidden_l2_gap)
        residual["reconverged_and_delta_present"] = True
        residual["min_high_hidden_l2_gap_over_reconverged_and_delta"] = (
            best.high_hidden_l2_gap
        )
        residual["obstruction_at"] = {
            "episode_id": best.episode_id,
            "target_key": best.target_key,
            "partner_key": best.partner_key,
            "window": list(best.window),
            "physical_time": best.physical_time,
            "delta_p": best.delta_p,
            "high_hidden_l2_gap": best.high_hidden_l2_gap,
        }
    else:
        residual["reconverged_and_delta_present"] = False
        residual["min_high_hidden_l2_gap_over_reconverged_and_delta"] = None
        residual["empty_qualifying_set_note"] = (
            "No target opportunity in the registered budget both reconverged "
            "Z_not_P-minus-high_hidden AND retained |dP| >= DELTA; the reconverged "
            "set's maximum retained |dP| stayed below DELTA (see reconverged_summary)."
        )
    return residual


SCOPE = (
    "Zero-training STRUCTURAL search over the FROZEN behavior law for two legally "
    "supported histories reaching a byte-identical canonical non-P pre-action "
    "state Z_not_P at one target owner opportunity with a different retained "
    "partner-interaction value P. Uses the PRODUCTION 15-dim dynamic-roster law "
    "and the PRODUCTION model (seed 57057, mode f1) -- NOT the 3-dim fixture. The "
    "registered budget runs the search under three per-lifecycle base families -- "
    "one symmetric control (sym_persist_idle) and two asymmetric families "
    "(asym_parity_short, asym_thirds) that break the observation symmetry so a "
    "partner perturbation can move the owner's retained payload -- with "
    "perturbations placed near the target's last opportunities. The "
    "anti-correlation between the retained P difference and the high_hidden gap is "
    "MEASURED across those families, not proven impossible. A "
    "bounded failure claims ONLY that there is no witness in the registered "
    "budget: it makes no claim that the matched state is impossible to reach and "
    "no claim that the underlying structure is empty. The residual high_hidden "
    "gap is a MEASURED fact about the finite search, not a structural claim. This "
    "does NOT conflate the current-write P_{t+1} with the historical P_t consumed "
    "at the target: the target owner's P is read BEFORE its target-time token, so "
    "the historical retained value a head would consume is the one compared. "
    "Guards against Pro's false closures -- temporal-index (P read pre-token), "
    "local-to-global and aggregate-alias (Z_not_P includes every active member's "
    "observation and the owner's own pre-token state), fixture-to-environment "
    "(production law and model), downstream-state (Z_not_P carries the pre-token "
    "high_hidden the actor reads as pre_hidden), and unwired-head (no model head "
    "is added, invoked or trained). Licenses no scientific or value claim and "
    "wires no model head."
)

TERMINAL_WITNESS = "MSSR_MATCHED_HISTORY_WITNESS_PRESENT"
TERMINAL_NO_WITNESS = "MSSR_MATCHED_HISTORY_NO_WITNESS_IN_REGISTERED_BUDGET"


def _budget(designs: Sequence[Design]) -> dict[str, object]:
    return {
        "episode_ids": list(EPISODE_IDS),
        "base_families": [family.name for family in BASE_FAMILIES],
        "design_target_partners": [list(pair) for pair in DESIGN_TARGET_PARTNERS],
        "leads": list(LEADS),
        "last_n_opportunities": LAST_N_OPPORTUNITIES,
        "delta": DELTA,
        "design_count": len(designs),
        "designs": [
            {
                "base_family": design.base_family,
                "target_key": design.target_key,
                "partner_key": design.partner_key,
                "perturb_step": design.window[0],
                "perturb_primitive": design.perturb_primitive,
                "target_opportunity": design.target_opportunity,
                "lead": design.lead,
            }
            for design in designs
        ],
    }


def proof() -> dict[str, object]:
    """Run the registered search and return its terminal, budget and residual."""
    designs = registered_designs()
    result = run_search(designs)
    report: dict[str, object] = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "budget": _budget(designs),
        "scope": SCOPE,
    }
    if result.witnesses:
        witness = result.witnesses[0]
        design = next(
            d
            for d in designs
            if d.base_family == witness["base_family"]
            and d.target_key == witness["target_key"]
            and d.partner_key == witness["partner_key"]
            and list(d.window) == witness["window"]
        )
        replay = verify_witness_replay(
            design, int(witness["episode_id"]), int(witness["physical_time"])
        )
        report["terminal"] = TERMINAL_WITNESS
        report["witness"] = {**witness, "replay": replay}
    else:
        report["terminal"] = TERMINAL_NO_WITNESS
        report["obstruction_residual"] = _obstruction_residual(result)
    return report


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2, default=str))

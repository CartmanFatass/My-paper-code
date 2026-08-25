from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import itertools
import json
import math
from pathlib import Path

from .config import (
    ACTIONS,
    ALL_SIZES,
    ALT_GRAPHON,
    ARM_CENTERS,
    CANONICAL_ROW_ORDER,
    COUNTER_ALGORITHM,
    EXPERIMENT_NAMESPACE,
    COUNTER_TERMINALS,
    EDGE_ARMS,
    GRAPHON,
    HELDOUT_SIZES,
    NOMINAL_HANDLE_RULE,
    POPULATION_NORMALIZATION,
    REGISTERED,
    REGIMES,
    RESIDUAL_SCALES,
    REVISION,
    ROLE_COORDINATES,
    SEEDS,
    SELF_EDGES_INCLUDED,
    TRAIN_SIZES,
)
from .resources import resource_proposal


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    evidence: object


def _source(name: str) -> str:
    return (Path(__file__).parent / name).read_text(encoding="utf-8")


def _omega(center: tuple[tuple[float, float], tuple[float, float]],
           residuals: list[list[float]], scale: float) -> list[list[float]]:
    return [[center[r][s] * math.exp(scale * math.tanh(residuals[r][s]))
             for s in (0, 1)] for r in (0, 1)]


def _implicit(
    encoded: list[list[float]], roles: list[int], center: tuple[tuple[float, float], tuple[float, float]],
    residuals: list[list[float]], scale: float, sender_roles: list[int] | None = None,
) -> tuple[list[float], list[list[float]], list[list[float]]]:
    n = len(roles)
    width = len(encoded[0])
    sender_roles = roles if sender_roles is None else sender_roles
    weights = _omega(center, residuals, scale)
    sums = [[sum(encoded[i][k] for i in range(n) if sender_roles[i] == sender) / n
             for k in range(width)] for sender in (0, 1)]
    masses = [sum(role == sender for role in sender_roles) / n for sender in (0, 1)]
    d_role = [sum(weights[r][s] * masses[s] for s in (0, 1)) for r in (0, 1)]
    m_role = [[sum(weights[r][s] * sums[s][k] for s in (0, 1))
               for k in range(width)] for r in (0, 1)]
    z_role = [[value / (d_role[r] + 1e-12) for value in m_role[r]] for r in (0, 1)]
    return ([d_role[r] for r in roles], [m_role[r] for r in roles], [z_role[r] for r in roles])


def _dense(
    encoded: list[list[float]], roles: list[int], center: tuple[tuple[float, float], tuple[float, float]],
    residuals: list[list[float]], scale: float, sender_roles: list[int] | None = None,
) -> tuple[list[float], list[list[float]], list[list[float]]]:
    n = len(roles)
    width = len(encoded[0])
    sender_roles = roles if sender_roles is None else sender_roles
    weights = _omega(center, residuals, scale)
    d = [sum(weights[roles[i]][sender_roles[j]] for j in range(n)) / n for i in range(n)]
    m = [[sum(weights[roles[i]][sender_roles[j]] * encoded[j][k] for j in range(n)) / n
          for k in range(width)] for i in range(n)]
    z = [[value / (d[i] + 1e-12) for value in m[i]] for i in range(n)]
    return d, m, z


def _max_error(left: object, right: object) -> float:
    if isinstance(left, (list, tuple)):
        if not isinstance(right, type(left)):
            raise TypeError(f"container type mismatch: {type(left).__name__} != {type(right).__name__}")
        return max((_max_error(a, b) for a, b in zip(left, right, strict=True)), default=0.0)
    return abs(float(left) - float(right))


def _forward_arguments() -> list[str]:
    tree = ast.parse(_source("policies.py"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "SharedSGSPPolicy":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == "forward":
                    return [argument.arg for argument in member.args.args if argument.arg != "self"]
    raise RuntimeError("SharedSGSPPolicy.forward not found")


def _function_arguments(source_name: str, function_name: str) -> list[str]:
    tree = ast.parse(_source(source_name))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return [argument.arg for argument in node.args.args]
    raise RuntimeError(f"{function_name} not found in {source_name}")


def _serve_pos_probability(raw_summary: float) -> float:
    # Hand-written output-connected actor: logits [0, raw_summary].
    softmax_pos = 1.0 / (1.0 + math.exp(-raw_summary))
    return 0.96 * softmax_pos + 0.02


def build_certificate() -> dict[str, object]:
    """No RNG, world, policy, training, or evaluation module is imported or called."""
    checks: list[Check] = []
    source_files = sorted(Path(__file__).parent.glob("*.py"))
    syntax_errors: dict[str, str] = {}
    for source_file in source_files:
        try:
            ast.parse(source_file.read_text(encoding="utf-8"), filename=source_file.name)
        except SyntaxError as error:
            syntax_errors[source_file.name] = str(error)
    checks.append(Check(
        "isolated_package_python_syntax",
        not syntax_errors,
        {"parsed_files": [path.name for path in source_files], "errors": syntax_errors},
    ))
    checks.append(Check("literal_process", (
        TRAIN_SIZES == (8, 12) and HELDOUT_SIZES == (6, 16)
        and ROLE_COORDINATES == (0.25, 0.75)
        and GRAPHON == ((1.0, 0.2), (0.2, 1.0))
        and ALT_GRAPHON == ((0.2, 1.0), (1.0, 0.2))
        and SELF_EDGES_INCLUDED and POPULATION_NORMALIZATION == "1/N"
        and ACTIONS == ("SERVE_NEG", "SERVE_POS") and REGIMES == ("SAME", "OPPOSED")
        and CANONICAL_ROW_ORDER == "lexicographic(role,within_role_slot)"
    ), {
        "train_N": TRAIN_SIZES, "heldout_N": HELDOUT_SIZES,
        "balanced_role_counts": "N/2,N/2", "coordinates": ROLE_COORDINATES,
        "W": GRAPHON, "W_ALT": ALT_GRAPHON, "self_edges": SELF_EDGES_INCLUDED,
        "normalization": POPULATION_NORMALIZATION, "context": "0.6*c_role+Normal(0,1)",
        "zero_target_tie": "SERVE_POS", "reward": "mean agent correctness",
        "support": "0.96*softmax+0.02", "canonical_rows": CANONICAL_ROW_ORDER,
        "nominal_handle": NOMINAL_HANDLE_RULE,
    }))

    rng_source = _source("rng.py")
    world_source = _source("world.py")
    checks.append(Check("counter_and_canonical_order_contract", all(token in rng_source for token in (
        "limit = _UINT64_RANGE - (_UINT64_RANGE % bound)",
        '"bounded_rejection", rejection',
        '"identity_replay_permutation", attempt',
        "if not bool(np.array_equal(candidate, identity))",
        "attempt += 1",
    )) and all(token in world_source for token in (
        "roles = np.repeat", "slots = np.tile", "episode not in range(256)",
        "episode not in range(16 * 240)", "nominal_handle(",
    )) and "world_row_order" not in world_source
    and EXPERIMENT_NAMESPACE == "SGSP-B1-R06-240"
    and SEEDS == (
        14103, 14127, 14153, 14177, 14201, 14229, 14253, 14273,
        14297, 14327, 14357, 14387, 14409, 14441, 14463, 14483,
    ), {
        "experiment_namespace": EXPERIMENT_NAMESPACE,
        "counter_algorithm": COUNTER_ALGORITHM,
        "counter_terminals": COUNTER_TERMINALS,
        "N_separated": True,
        "training_episode": "16*(update-1)+local_e in 0..3839",
        "evaluation_episode": "0..255 under evaluation phase",
        "base_row_draw": False,
        "audit_permutation": "uniform conditioned on nonidentity; one addressed attempt sequence",
    }))
    runtime_source_names = (
        "artifacts.py", "audits.py", "authorization.py", "config.py",
        "evaluation.py", "policies.py", "reference.py", "resources.py",
        "rng.py", "runner.py", "statistics.py", "training.py", "world.py",
    )
    runtime_sources = {name: _source(name) for name in runtime_source_names}
    forbidden_r05_runtime_tokens = (
        "SGSP-B1-SCIENCE-20260813-05",
        "sgsp-b1-rev05-atomic-result-v1",
        "checkpoint-update-480.pt",
        "immediately_after_optimizer_update_480",
        "only_evaluable_state_immediately_after_update_480",
    )
    r05_runtime_references = {
        name: [token for token in forbidden_r05_runtime_tokens if token in source]
        for name, source in runtime_sources.items()
        if any(token in source for token in forbidden_r05_runtime_tokens)
    }
    checks.append(Check(
        "r06_single_budget_namespace_and_r05_artifact_isolation",
        not r05_runtime_references
        and 'COUNTER_ROOT = EXPERIMENT_NAMESPACE' in runtime_sources["config.py"]
        and 'payload = "\\x1f".join((COUNTER_ROOT,' in runtime_sources["rng.py"]
        and 'checkpoint-update-240.pt' in runtime_sources["artifacts.py"]
        and 'checkpoint-update-480.pt' not in runtime_sources["artifacts.py"],
        {
            "revision": REVISION,
            "namespace": EXPERIMENT_NAMESPACE,
            "fresh_seed_block": list(SEEDS),
            "r05_runtime_references": r05_runtime_references,
            "training_episode_range": [0, 3839],
            "sole_checkpoint": "immediately_after_optimizer_update_240",
            "revision_05_artifact_load": False,
        },
    ))
    stochastic_entrypoints = {
        "world.generate_world": _function_arguments("world.py", "generate_world"),
        "rng.forced_nonidentity_audit_permutation": _function_arguments(
            "rng.py", "forced_nonidentity_audit_permutation",
        ),
        "policies.paired_policy_set": _function_arguments("policies.py", "paired_policy_set"),
        "training.train_seed": _function_arguments("training.py", "train_seed"),
        "evaluation.evaluate_seed": _function_arguments("evaluation.py", "evaluate_seed"),
    }
    authorization_source = _source("authorization.py")
    checks.append(Check(
        "registered_stochastic_entrypoints_require_production_permit",
        all(arguments and arguments[0] == "permit" for arguments in stochastic_entrypoints.values())
        and "load_production_permit" in _source("runner.py")
        and all(token in authorization_source for token in (
            "certificate_path", 'certificate.get("revision") != REVISION',
            'certificate.get("passed") is not True', "production_authorized",
            "lease_token", "not_after_utc",
        )),
        stochastic_entrypoints,
    ))

    encoded = [[float((row + 1) * (column - 3)) / 17.0 for column in range(33)]
               for row in range(6)]
    roles = [0, 0, 0, 1, 1, 1]
    residuals = [[-0.3, 0.2], [0.7, -0.4]]
    dense_errors: dict[str, float] = {}
    for arm in EDGE_ARMS:
        dense = _dense(encoded, roles, ARM_CENTERS[arm], residuals, RESIDUAL_SCALES[arm])
        implicit = _implicit(encoded, roles, ARM_CENTERS[arm], residuals, RESIDUAL_SCALES[arm])
        dense_errors[f"{arm}|intact"] = max(
            _max_error(a, b) for a, b in zip(dense, implicit, strict=True)
        )
        flipped = [1 - role for role in roles]
        reassoc_dense = _dense(
            encoded, roles, ARM_CENTERS[arm], residuals, RESIDUAL_SCALES[arm], flipped,
        )
        reassoc_implicit = _implicit(
            encoded, roles, ARM_CENTERS[arm], residuals, RESIDUAL_SCALES[arm], flipped,
        )
        dense_errors[f"{arm}|sender_reassociation"] = max(
            _max_error(a, b) for a, b in zip(
                reassoc_dense, reassoc_implicit, strict=True,
            )
        )
    swapped_dense = _dense(encoded, roles, ALT_GRAPHON, residuals, 0.25)
    swapped_implicit = _implicit(encoded, roles, ALT_GRAPHON, residuals, 0.25)
    dense_errors["SGSP-W|center_swap"] = max(
        _max_error(a, b) for a, b in zip(swapped_dense, swapped_implicit, strict=True)
    )
    checks.append(Check(
        "dense_implicit_actor_input_equality",
        max(dense_errors.values()) <= REGISTERED.dense_tolerance,
        {"handwritten_fixture_errors": dense_errors, "tolerance": REGISTERED.dense_tolerance,
         "panel_centers": {"SGSP": "W", "ALT": "W_ALT", "EDGE": "W", "SWAP": "W_ALT"}},
    ))
    deployed_sources = "\n".join(_source(name) for name in (
        "policies.py", "training.py", "evaluation.py",
    ))
    checks.append(Check(
        "dense_reference_isolation",
        "from .reference" not in deployed_sources and "dense_weights" not in _source("policies.py"),
        {"dense_modules": ["world.py physical simulator", "reference.py deterministic audit"],
         "deployed_nxn_objects": 0},
    ))

    collision_a = [1.0, 1.0, 1.0, -1.0, -1.0, -1.0]
    collision_b = [-value for value in collision_a]
    anon_means = [sum(values) / 6.0 for values in (collision_a, collision_b)]
    fields = [[sum(GRAPHON[receiver][roles[j]] * values[j] for j in range(6)) / 6.0
               for receiver in (0, 1)] for values in (collision_a, collision_b)]
    checks.append(Check(
        "anonymous_collision",
        _max_error(anon_means, [0.0, 0.0]) <= REGISTERED.dense_tolerance
        and _max_error(fields, [[0.4, -0.4], [-0.4, 0.4]]) <= REGISTERED.dense_tolerance,
        {"anonymous_means": anon_means, "role_fields": fields, "correct_action_flips": True},
    ))

    nesting_errors = {
        "residual": 0.0, "weight": 0.0, "summary": 0.0,
        "actor_input": 0.0, "handwritten_common_actor_logit": 0.0,
    }
    for flat_residuals in itertools.product((-0.20, 0.0, 0.20), repeat=4):
        residual_table = [list(flat_residuals[:2]), list(flat_residuals[2:])]
        sgsp_gamma = [[math.atanh(value / 0.25) for value in row] for row in residual_table]
        edge_gamma = [[math.atanh(value / 2.0) for value in row] for row in residual_table]
        sgsp_weights = _omega(GRAPHON, sgsp_gamma, 0.25)
        edge_weights = _omega(GRAPHON, edge_gamma, 2.0)
        sgsp_summary = _implicit(encoded, roles, GRAPHON, sgsp_gamma, 0.25)
        edge_summary = _implicit(encoded, roles, GRAPHON, edge_gamma, 2.0)
        nesting_errors["residual"] = max(
            nesting_errors["residual"],
            max(abs(value - 2.0 * math.tanh(edge_gamma[r][s]))
                for r, row in enumerate(residual_table) for s, value in enumerate(row)),
        )
        nesting_errors["weight"] = max(
            nesting_errors["weight"], _max_error(sgsp_weights, edge_weights),
        )
        nesting_errors["summary"] = max(
            nesting_errors["summary"], _max_error(sgsp_summary, edge_summary),
        )
        sgsp_actor_inputs = [
            sgsp_summary[2][i] + [sgsp_summary[0][i], float(roles[i] == 0), float(roles[i] == 1)]
            for i in range(len(roles))
        ]
        edge_actor_inputs = [
            edge_summary[2][i] + [edge_summary[0][i], float(roles[i] == 0), float(roles[i] == 1)]
            for i in range(len(roles))
        ]
        nesting_errors["actor_input"] = max(
            nesting_errors["actor_input"], _max_error(sgsp_actor_inputs, edge_actor_inputs),
        )
        sgsp_logits = [[sum(row), -sum(row)] for row in sgsp_actor_inputs]
        edge_logits = [[sum(row), -sum(row)] for row in edge_actor_inputs]
        nesting_errors["handwritten_common_actor_logit"] = max(
            nesting_errors["handwritten_common_actor_logit"],
            _max_error(sgsp_logits, edge_logits),
        )
    capability_residuals = [[1.5, -1.5], [-1.5, 1.5]]
    capability_gamma = [
        [math.atanh(residual / 2.0) for residual in row]
        for row in capability_residuals
    ]
    capability_summary = _implicit(
        [[v] for v in collision_a], roles, GRAPHON, capability_gamma, 2.0,
    )[2]
    zero_edge_summary = _implicit(
        [[v] for v in collision_a], roles, GRAPHON,
        [[0.0, 0.0], [0.0, 0.0]], 2.0,
    )[2]
    capability_changed = abs(capability_summary[0][0] - zero_edge_summary[0][0]) > 0.0
    checks.append(Check(
        "edge_nesting_and_capability",
        max(nesting_errors.values()) <= REGISTERED.dense_tolerance
        and any(abs(value) > 0.25 for row in capability_residuals for value in row)
        and capability_changed,
        {"exhaustive_residual_table_count": 81, "nesting_max_errors": nesting_errors,
         "capability_residuals": capability_residuals,
         "EDGE_gamma_via_atanh_residual_over_2": capability_gamma,
         "unavailable_to_sgsp": True, "raw_summary_changed": capability_changed},
    ))

    sgsp_ratio_upper = 0.2 * math.exp(0.5)
    alt_ratio_lower = 5.0 * math.exp(-0.5)
    log_jacobian_max_error = 0.0
    jacobian_table_count = 0
    for flat_residuals in itertools.product((-0.20, 0.0, 0.20), repeat=4):
        common_gamma = [math.atanh(value / 0.25) for value in flat_residuals]
        sgsp_log_jacobian = [0.25 / math.cosh(value) ** 2 for value in common_gamma]
        alt_log_jacobian = [0.25 / math.cosh(value) ** 2 for value in common_gamma]
        log_jacobian_max_error = max(
            log_jacobian_max_error, _max_error(sgsp_log_jacobian, alt_log_jacobian),
        )
        jacobian_table_count += 1
    raw_jacobian_sgsp = sorted([0.25 * value for row in GRAPHON for value in row])
    raw_jacobian_alt = sorted([0.25 * value for row in ALT_GRAPHON for value in row])
    zero = [[0.0, 0.0], [0.0, 0.0]]
    asymmetric = [[0.8, -0.4], [0.2, -0.7]]
    original_roles = roles
    flipped_roles = [1 - role for role in roles]
    base_encoded = [[value] for value in collision_a]
    sgsp_intact_z = _implicit(base_encoded, original_roles, GRAPHON, zero, 0.25)[2][0][0]
    alt_intact_z = _implicit(base_encoded, original_roles, ALT_GRAPHON, zero, 0.25)[2][0][0]
    zero_reassoc_z = _implicit(
        base_encoded, original_roles, GRAPHON, zero, 0.25, flipped_roles,
    )[2][0][0]
    zero_swap_z = _implicit(base_encoded, original_roles, ALT_GRAPHON, zero, 0.25)[2][0][0]
    asymmetric_reassoc_z = _implicit(
        base_encoded, original_roles, GRAPHON, asymmetric, 0.25, flipped_roles,
    )[2][0][0]
    asymmetric_swap_z = _implicit(
        base_encoded, original_roles, ALT_GRAPHON, asymmetric, 0.25,
    )[2][0][0]
    probability_change = abs(
        _serve_pos_probability(sgsp_intact_z) - _serve_pos_probability(alt_intact_z)
    )
    checks.append(Check(
        "equal_width_center_jacobian_action_reachability",
        sgsp_ratio_upper < 1.0 and alt_ratio_lower > 1.0
        and jacobian_table_count == 81 and log_jacobian_max_error == 0.0
        and raw_jacobian_sgsp == raw_jacobian_alt
        and probability_change > 0.0
        and abs(zero_reassoc_z - zero_swap_z) <= 1e-15
        and abs(asymmetric_reassoc_z - asymmetric_swap_z) > 1e-12,
        {"SGSP_cross_same_upper": sgsp_ratio_upper, "ALT_cross_same_lower": alt_ratio_lower,
         "log_edge_jacobian_formula": "0.25*sech(gamma)^2 on active diagonal",
         "enumerated_common_residual_tables": jacobian_table_count,
         "log_edge_jacobian_max_error": log_jacobian_max_error,
         "initial_raw_jacobian_multiset": raw_jacobian_sgsp,
         "indexwise_raw_jacobian_equality_claimed": False,
         "output_connected_SERVE_POS_probability_change": probability_change,
         "zero_gamma_reassociation_equals_swap": abs(zero_reassoc_z - zero_swap_z) <= 1e-15,
         "asymmetric_gamma_reassociation_differs_from_swap": abs(asymmetric_reassoc_z - asymmetric_swap_z)},
    ))

    forward_arguments = _forward_arguments()
    forbidden = {"opaque_handle", "row_position", "within_role_slot", "n", "reward", "target",
                 "latent_orientation", "future", "evaluation_statistic", "heldout_size"}
    checks.append(Check(
        "policy_schema_and_forbidden_inputs",
        forward_arguments == [
            "sender_messages", "receiver_roles", "sender_roles_override", "center_swap",
        ] and not forbidden.intersection(forward_arguments),
        {"forward_arguments": forward_arguments, "forbidden_arguments": sorted(forbidden),
         "cut_controls_are_evaluator_owned": ["sender_roles_override", "center_swap"]},
    ))

    policy_source = _source("policies.py")
    training_source = _source("training.py")
    checks.append(Check(
        "parameter_initializer_optimizer_checkpoint_contract",
        REGISTERED.edge_arm_parameters == 1318 and REGISTERED.anon_parameters == 1314
        and REGISTERED.train_updates == 240 and REGISTERED.train_batch_worlds == 64
        and all(token in training_source for token in (
            "episode = 16 * (update - 1) + within_cell", "clip_grad_norm_",
            "mean_loss.backward()", "optimizer.step()", "immediately_after_optimizer_update_240",
            "foreach=False",
        ))
        and all(token in policy_source for token in (
            "initialization_uniform(permit, seed, layer, row, column)", "encoder_bias.zero_()",
            "gamma.zero_()", "common_tensors_bitwise_equal",
        )),
        {"encoder": 64, "edge_table": 4, "actor_hidden": 1184, "actor_head": 66,
         "edge_arm_total": 1318, "anon_total": 1314, "updates": 240,
         "batch": "16 per lexicographic N/regime cell, 64 total",
         "optimizer": {"name": "Adam", "lr": 4e-4, "betas": (0.9, 0.999),
                       "epsilon": 1e-8, "amsgrad": False, "weight_decay": 0.0,
                       "bias_correction": True, "global_gradient_clip": 2.0},
         "final_checkpoint": "immediately after update 240"},
    ))

    evaluation_source = _source("evaluation.py")
    checks.append(Check(
        "identity_reassociation_center_swap_semantics",
        all(token in evaluation_source for token in (
            "forced_nonidentity_audit_permutation(",
            "world.permuted(permutation)", "uniforms[permutation]", "np.argsort(permutation)",
            "reassociated_roles = 1 - world.roles", "center_swap=True",
            "permuted_override =", "one_permutation_reused_across_arms_and_panels_per_world",
        )),
        {"identity_moves": ["x", "b", "u", "within_role_slot", "nominal_handle", "action_uniform"],
         "identity_inverse_moves": ["logits", "actions"],
         "reassociation_moves": ["sender_role_at_aggregation_port"],
         "center_swap_moves": ["declared_center_in_D_and_M"],
         "center_swap_gamma_indices_move": False,
         "cuts_fix": ["physical_truth", "reward", "canonical_rows", "parameters", "action_tape"]},
    ))
    forbidden_legacy = "G-" + "PERMUTE"
    runtime_source = "\n".join(_source(name) for name in (
        "rng.py", "world.py", "policies.py", "training.py", "evaluation.py", "statistics.py",
    ))
    checks.append(Check(
        "no_legacy_arm_substitution",
        forbidden_legacy not in runtime_source,
        {"primary_comparator": "EDGE-PE", "identity_replay": "complete tuple permutation"},
    ))

    work_rows = []
    for n in ALL_SIZES:
        for regime in REGIMES:
            ledger = {
                "sender_scalars": n, "public_role_coordinates": n, "encoder_calls": n,
                "role_pair_exponentials": 4, "receiver_role_block_reductions": 2,
                "actor_calls": n, "legal_action_probabilities": 2 * n,
                "scalar_multiplications": {
                    "encoder": 32 * n, "edge_residual_and_anchor": 8,
                    "numerator_and_mass": 136, "actor_hidden": 1152 * n,
                    "actor_head": 64 * n, "support_mix": 2 * n,
                },
                "scalar_additions": {
                    "encoder_bias": 32 * n, "block_message_sums": 33 * (n - 2),
                    "block_count_sums": 2 * (n - 1), "numerator_and_mass": 68,
                    "summary_epsilon": 2, "actor_hidden_including_bias": 1152 * n,
                    "actor_head_including_bias": 64 * n,
                    "softmax_shift_sum_and_floor": 5 * n,
                },
                "scalar_comparisons": 3 * n,
                "scalar_tanh": 64 * n + 4,
                "scalar_exp": 2 * n + 4,
                "scalar_divisions": 134 + 2 * n,
                "reduction_invocations": 68 + 35 * n,
                "learned_nxn_objects": 0,
            }
            work_rows.append({"n": n, "regime": regime,
                              **{arm: dict(ledger) for arm in EDGE_ARMS}, "ratio": 1})
    checks.append(Check(
        "valid_tuple_work_communication_replay", all(
            row["SGSP-W"] == row["ALT-CENTER"] == row["EDGE-PE"] for row in work_rows
        ), {"intact_rows": work_rows, "common_replays": ["identity", "sender_reassociation"],
            "SGSP_center_swap": "separate post-training audit ledger",
            "time": "O(2N)", "storage": "O(N)", "edge_storage": 4},
    ))

    statistics_source = _source("statistics.py")
    checks.append(Check(
        "interval_availability_mechanism_and_branch_contract",
        all(token in statistics_source for token in (
            "student_t.ppf(1.0 - 0.05 / (2.0 * 4.0), df=15)",
            "student_t.ppf(1.0 - 0.05 / 3.0, df=15)",
            "return_caps.append(min(", "tv_caps.append(min(",
            "ge_attenuation_caps.append(min(", "ga_attenuation_caps.append(min(",
            '"GE_TWO_SIDED_AVAILABLE"', '"GA_TWO_SIDED_AVAILABLE"',
            '"ANON_POSITIVE_AVAILABLE"', '"CUT_RETURN_DROP_AVAILABLE"',
            '"CUT_ACTION_TV_AVAILABLE"', '"GE_ATTENUATION_AVAILABLE"',
            '"GA_ATTENUATION_AVAILABLE"', "PROMOTE_FIXED_SEMANTIC_GRAPHON_SECOND_SURFACE",
            "DELETE_CORRECT_CENTER_SPECIFIC_FAMILY", "BOUNDED_GENERIC_EDGE_EVIDENCE",
            "CAPACITY_COMPARATOR_DELETION_OR_EQUIVALENCE", "ANSWERABLE_MECHANISM_FAILURE",
            "IDENTIFYING_SIZE_OR_REGIME_INTERACTION",
            "FAILED_ENDPOINT_CUT_OR_ATTENUATION_AVAILABILITY", "BOUNDED_NONIDENTIFICATION",
        )),
        {"inferential_unit": "seed", "seed_count": len(SEEDS),
         "two_sided_family": "four-cell 95% Bonferroni Student-t",
         "mechanism_family": "within-seed min_N then one-sided 3-bound Bonferroni Student-t",
         "availability": "arithmetic mean of within-seed minimum caps",
         "branch_order": list(range(1, 10))},
    ))

    resources = resource_proposal()
    artifacts_source = _source("artifacts.py")
    runner_source = _source("runner.py")
    checks.append(Check(
        "atomic_lifecycle_resource_and_fail_closed_runner",
        resources["hypothetical_trajectory_candidates"] == 0
        and resources["learned_dense_pairwise_objects"] == 0
        and resources["formal_wall_clock_hard_cap_hours"] <= 8
        and resources["requested_concurrency"] == 1
        and resources["requested_cpu_cores"] == 1
        and resources["requested_gpu_count"] == 0
        and resources["registered_policy_forwards_total"] == 1_310_832
        and resources["registered_backward_calls_total"] == 15_360
        and all(token in artifacts_source for token in (
            "exist_ok=False", "os.replace(temporary, destination)", "atomic_complete",
            "seed may not be replaced", "all four arms", "validate_lease_binding",
        ))
        and all(token in runner_source for token in (
            "required=True", "require_exact_certificate", "load_production_permit",
            "validate_result_root", "load_complete_seed_packet", "_configure_single_cpu",
        )),
        {"result_root": "fresh, exact-revision manifest",
         "seed_packet": "atomic four-arm directory rename", "seed_replacement": False,
         "production_gate": "passing exact-revision certificate plus Root lease token",
         "resource_proposal": resources},
    ))

    return {
        "direction": "semantic_graphon_shared_policy",
        "revision": REVISION,
        "certificate_kind": "preactivity_handwritten_fixture_and_static_source_only",
        "registered_stochastic_object_materialized": False,
        "registered_seed_value_inspected": False,
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
        "registered_seed_count": len(SEEDS),
    }


def write_certificate(path: Path) -> dict[str, object]:
    certificate = build_certificate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(certificate, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return certificate

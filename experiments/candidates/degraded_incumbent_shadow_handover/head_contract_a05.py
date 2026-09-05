"""Genuine synthetic policy mapping, two graph probes and nine native consumer calls."""

import ctypes
import math
from pathlib import Path
import subprocess

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState,
)


def mapping_rule(raw_exact, sigmoid_match, raw_difference, sigmoid_difference):
    if raw_exact and sigmoid_difference > 1e-6:
        return "RAW_LOGIT_PASS_THROUGH"
    if sigmoid_match and raw_difference > 1e-6:
        return "LINKED_PROBABILITY_MAPPING"
    return "OTHER_MAPPING_READOUT"


def graph_rule(training, control, outputs_finite):
    names = ("prediction_cholesky.weight", "prediction_cholesky.bias")
    omitted = all(training[name]["grad_none"] for name in names)
    connected = all(not control[name]["grad_none"] and control[name]["finite"]
                    and control[name]["l1"] > 0 for name in names)
    return ("CHOLESKY_OMITTED_FROM_TRAINING_HEAD_GRAPH" if outputs_finite and omitted and connected
            else "OTHER_TRAINING_HEAD_CONNECTION")


def consumer_rule(cases):
    if not all(case["q95"]["raw"] == case["q95"]["clipped"] for case in cases):
        return "OTHER_NATIVE_CONSUMER_READOUT"
    return ("NATIVE_CLIP_CONTRAST_REPRODUCED" if any(
        abs(case["q95"]["raw"] - case["q95"]["sigmoid"]) >= 0.05 - 1e-12 for case in cases
    ) else "NO_DISCRIMINATING_CONSUMER_CONTRAST")


def gradient(value):
    grad = value.grad
    return {"shape": list(value.shape), "requires_grad": value.requires_grad,
            "grad_none": grad is None, "finite": bool(torch.isfinite(grad).all()) if grad is not None else None,
            "l1": float(grad.detach().double().abs().sum()) if grad is not None else None}


def native_helper(output):
    translation = Path(__file__).with_suffix(".cpp")
    toolchain = backend._production_toolchain()
    target = output / "head_contract_a05.so"
    subprocess.run([toolchain["compiler"], *toolchain["flags"], str(translation), "-o", str(target)],
                   check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(target))
    helper = library.dish_a05_predictive_q95
    helper.argtypes = [ctypes.POINTER(ctypes.c_double)]
    helper.restype = ctypes.c_double
    return library, helper


def probe(seed, levels, output):
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    state = RecurrentRolloutState.fresh("STRUCTURED", width=2)
    policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=None, state=state)
    model = policy.model
    before = {name: value.detach().double().clone() for name, value in model.named_parameters()}
    actor = np.empty((2, 4, 54), dtype=np.float32)
    for lane in range(2):
        for copy in range(4):
            actor[lane, copy] = 0.01 * (1 + 4 * lane + copy)
    observation = {"actor": actor, "owner": np.array([0, 1], dtype=np.int64),
                   "renew": np.ones(2, dtype=bool), "snapshot_payload": np.zeros((2, 18), dtype=np.float32),
                   "snapshot_delivery_mask": np.zeros(2, dtype=bool)}
    rows = policy.step_rows(observation, sampler=None, global_tick=0, deterministic=True)
    with torch.no_grad():
        raw_q = model.service_q(state.hidden)
        sigmoid = torch.sigmoid(raw_q)
    mappings = []
    for lane, selected in enumerate((3, 1)):
        raw = raw_q[lane, selected].double().numpy()
        linked = sigmoid[lane, selected].double().numpy()
        returned = rows["service_q"][lane]
        raw_difference = float(np.max(np.abs(returned - raw)))
        linked_difference = float(np.max(np.abs(returned - linked)))
        exact = bool(np.array_equal(returned, raw))
        linked_match = linked_difference <= 1e-7
        mappings.append({"lane": lane, "owner": lane, "owner_active_copy": (0, 2)[lane],
                         "standby_shadow_copy": selected, "native_row": returned.tolist(),
                         "selected_raw_float64": raw.tolist(), "sigmoid_fp32_expanded": linked.tolist(),
                         "native_minus_raw": (returned - raw).tolist(), "native_minus_sigmoid": (returned - linked).tolist(),
                         "raw_exact": exact, "sigmoid_match_atol_1e7": linked_match,
                         "max_raw_difference": raw_difference, "max_sigmoid_difference": linked_difference,
                         "result": mapping_rule(exact, linked_match, raw_difference, linked_difference)})
    with torch.enable_grad():
        hidden = torch.full((2, 4, 128), 0.125, dtype=torch.float32, requires_grad=True)
        training_heads = model.training_heads(hidden)
        sum(value.sum() for value in training_heads.values()).backward()
        training = {name: gradient(value) for name, value in model.named_parameters()}
        training_hidden = gradient(hidden)
        model.zero_grad(set_to_none=True)
        hidden.grad = None
        full_heads = model.heads(hidden)
        full_heads["prediction_cholesky"].sum().backward()
        control = {name: gradient(value) for name, value in model.named_parameters()
                   if name.startswith("prediction_cholesky.")}
        control_hidden = gradient(hidden)
    outputs_finite = bool(torch.isfinite(raw_q).all() and torch.isfinite(sigmoid).all()
                          and all(torch.isfinite(value).all() for value in training_heads.values())
                          and all(torch.isfinite(value).all() for value in full_heads.values())
                          and np.isfinite(rows["service_q"]).all())
    initial_norm = math.sqrt(sum(float(value.square().sum()) for value in before.values()))
    final_norm = math.sqrt(sum(float(value.detach().double().square().sum()) for value in model.parameters()))
    displacement = math.sqrt(sum(float((value.detach().double() - before[name]).square().sum())
                                 for name, value in model.named_parameters()))
    library, helper = native_helper(output)
    cases = []
    for level in levels:
        raw = np.full(20, level, dtype=np.float64)
        vectors = {"raw": raw, "clipped": np.clip(raw, 1e-6, 1.0 - 1e-6),
                   "sigmoid": np.array([1.0 / (1.0 + math.exp(-float(x))) for x in raw], dtype=np.float64)}
        q95 = {name: float(helper(vector.ctypes.data_as(ctypes.POINTER(ctypes.c_double))))
               for name, vector in vectors.items()}
        cases.append({"level": level, "vectors": {name: value.tolist() for name, value in vectors.items()}, "q95": q95})
    graph_result = graph_rule(training, control, outputs_finite)
    consumer_result = consumer_rule(cases)
    finite_gradients = all(row["grad_none"] or row["finite"] for row in
                           [*training.values(), *control.values(), training_hidden, control_hidden])
    if not (outputs_finite and finite_gradients and math.isfinite(final_norm)
            and all(math.isfinite(v) for case in cases for v in case["q95"].values()) and displacement == 0):
        raise RuntimeError("incomplete A05: nonfinite measurement or changed parameters")
    reproduced = (all(row["result"] == "RAW_LOGIT_PASS_THROUGH" for row in mappings)
                  and graph_result == "CHOLESKY_OMITTED_FROM_TRAINING_HEAD_GRAPH"
                  and consumer_result == "NATIVE_CLIP_CONTRAST_REPRODUCED")
    return {"object": "DISH-PREDICTION-HEAD-CONTRACT-A05", "synthetic_seed": seed,
            "result": "A05-SYNTHETIC-BOUNDARY-REPRODUCED" if reproduced else "A05-ALTERNATE-SYNTHETIC-READOUT",
            "model_training_mode": model.training, "actor": actor.tolist(), "raw_service_q_fp32": raw_q.tolist(),
            "mapping_rows": mappings, "training_head_keys": list(training_heads), "training_parameter_gradients": training,
            "training_hidden_gradient": training_hidden, "control_cholesky_gradients": control,
            "control_hidden_gradient": control_hidden, "graph_result": graph_result,
            "connected_training_parameter_tensors": sum(not row["grad_none"] for row in training.values()),
            "outputs_finite": outputs_finite, "native_cases": cases, "native_result": consumer_result,
            "parameter_change": {"initial_norm": initial_norm, "final_norm": final_norm,
                                 "l2_displacement": displacement, "relative_displacement": displacement / initial_norm},
            "exposure": {"model_policy_initializations": 1, "policy_recurrent_forwards": 1,
                         "extra_service_q_calls": 1, "training_heads_calls": 1, "full_heads_control_calls": 1,
                         "backward_passes": 2, "native_compile_load_calls": 1, "native_helper_calls": 9,
                         "policy_rows": 2, "native_helper_cases": 3, "nested_heads_calls": 2,
                         "nested_service_q_calls": 4, "nested_cholesky_calls": 2,
                         "optimizer_initializations": 0, "optimizer_steps": 0, "checkpoint_reads": 0,
                         "training_master_initializations": 0, "trace_reads": 0, "training_transitions": 0,
                         "learner_updates": 0, "native_state_initializations": 0, "native_resets": 0,
                         "native_prepares": 0, "native_completions": 0, "native_episodes": 0}}

"""B13 retained-byte intake, adapted from B12; no model, rollout, RNG or update."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import torch


p = argparse.ArgumentParser()
p.add_argument("--root", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--launch-sha", required=True)
args = p.parse_args()
assert re.fullmatch(r"[0-9a-f]{40}", args.launch_sha)
root = args.root
run = root / "b13_seed33"
summary = json.loads((run / "summary.json").read_text())
curves = [json.loads(line) for line in (run / "curves.jsonl").read_text().splitlines()]
roles = ("initialization", "final1024", "greedy", "nearest", "modal")
panels = {role: json.loads((run / (role + ".json")).read_text()) for role in roles}
primary = ("8_to_12.ACTIVE_CONTINUATION", "12_to_8.ACTIVE_CONTINUATION")
cells = {f"{path}.{mode}" for path in ("8_to_8", "12_to_12", "8_to_12", "12_to_8")
         for mode in ("ACTIVE_CONTINUATION", "NEW_EPOCH")}


def close(a, b):
    assert math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12), (a, b)


assert summary["status"] == "COMPLETE" and summary["seed"] == 33
assert len(curves) == 1024 and [c["update"] for c in curves] == list(range(1, 1025))
assert sum(c["training_episodes"] for c in curves) == summary["training_episodes"] == 65536
assert sum(c["native_ticks"] for c in curves) == 4194304
for key in ("backward_calls", "optimizer_calls"):
    assert sum(c[key] for c in curves) == summary[key] == 1024
assert summary["training_updates"] == 1024 and summary["independent_fits"] == 1
assert summary["native_ticks"] == 4358144
assert summary["phase_draws_training"] == 1048576
assert summary["phase_draws_evaluation"] == 16384 and summary["modal_team_decisions"] == 8192
assert summary["evaluation_episodes"] == {role: 512 for role in roles}
assert summary["evaluation_parameter_displacement"] == 0.0
checks = {}
for role, rows in panels.items():
    assert len(rows) == len({(r["cell"], r["scenario"]) for r in rows}) == 512
    assert {r["cell"] for r in rows} == cells
    assert all(math.isfinite(r[k]) for r in rows for k in ("U", "F", "tau", "Y", "unmet_ticks"))
    assert all(0 <= r["U"] <= 1 and 0 <= r["F"] <= 1 and 0 <= r["Y"] <= 1
               and 0 <= r["tau"] <= 40 for r in rows)
    for row in rows:
        close(row["unmet_ticks"], 40 * row["U"])
    if role != "nearest":
        assert all(r["F"] == 0 for r in rows)
    for cell in cells:
        selected = [r for r in rows if r["cell"] == cell]
        assert sorted(r["scenario"] for r in selected) == list(range(64))
        for key in ("U", "F", "tau", "Y", "unmet_ticks"):
            close(np.mean([r[key] for r in selected]), summary["endpoint_means"][role][cell][key])
        assert sum(r["tau"] == 40 for r in selected) == summary["endpoint_means"][role][cell]["tau40"]
    checks[role] = dict(rows=512, cells=8, agent_ticks=sum(r["agent_ticks"] for r in rows),
                       agent_claims=sum(r["agent_claims"] for r in rows))

comparisons = {}
for target, names, published in (("final1024", ("D_g", "D_n", "G_U"), summary["comparison"]),
                                 ("modal", ("D_g", "D_n"), summary["modal_comparison"])):
    comparisons[target] = {}
    for name in names:
        reference = {"D_g": "greedy", "D_n": "nearest", "G_U": "initialization"}[name]
        paths = {}
        for cell in primary:
            left = {r["scenario"]: r for r in panels[reference] if r["cell"] == cell}
            right = {r["scenario"]: r for r in panels[target] if r["cell"] == cell}
            delta = np.array([left[i]["U"] - right[i]["U"] for i in range(64)])
            paths[cell] = dict(mean=float(delta.mean()), conditional_se=float(delta.std(ddof=1) / 8),
                               positive=int((delta > 0).sum()), adverse=int((delta < 0).sum()), ties=int((delta == 0).sum()))
            assert np.allclose(delta, published[name]["paths"][cell]["differences"], rtol=0, atol=1e-14)
        mean = float(np.mean([d["mean"] for d in paths.values()]))
        se = math.sqrt(sum(d["conditional_se"] ** 2 for d in paths.values())) / 2
        close(mean, published[name]["mean"])
        close(se, published[name]["conditional_se"])
        comparisons[target][name] = dict(mean=mean, conditional_se=se,
                                         conditional_normal95=[mean - 1.96 * se, mean + 1.96 * se], paths=paths)

init = torch.load(run / "initialization.pt", map_location="cpu", weights_only=True)
final = torch.load(run / "final1024.pt", map_location="cpu", weights_only=True)
expected = {"log_prior_strength", *(f"{layer}.{field}" for layer in ("row1", "row2", "head", "score") for field in ("weight", "bias"))}
assert init.keys() == final["model"].keys() == expected
assert next(iter(init)) == "log_prior_strength"
for state in (init, final["model"]):
    assert all(t.dtype == torch.float64 and bool(torch.isfinite(t).all()) for t in state.values())
iv = torch.cat([init[name].reshape(-1) for name in init])
fv = torch.cat([final["model"][name].reshape(-1) for name in init])
assert iv.numel() == fv.numel() == summary["parameters"] == 2562
assert init["log_prior_strength"].shape == final["model"]["log_prior_strength"].shape == torch.Size([])
assert float(init["log_prior_strength"]) == 0.0
assert torch.count_nonzero(init["score.weight"]) == torch.count_nonzero(init["score.bias"]) == 0
assert final["updates"] == 1024 and final["seed"] == 33
assert final["launch_sha"] == summary["launch_sha"] == args.launch_sha
assert final["object_id"] == summary["object_id"] == "RCLE-TBCFV-B13-LEARNED-PRIOR-STRENGTH-1024"
assert final["action_law"] == summary["action_law"] == "softmax(exp(eta)*log(q)+z); eta0=0; q=.9*exact_greedy+.1/N"
assert final["learned_prior_strength"] is summary["learned_prior_strength"] is True
assert final["baselines"].shape == (8,) and bool(torch.isfinite(final["baselines"]).all())
group, = final["optimizer"]["param_groups"]
assert group["lr"] == 3e-4 and tuple(group["betas"]) == (.9, .999)
assert group["eps"] == 1e-8 and group["weight_decay"] == 0 and group["foreach"] is False
assert len(group["params"]) == len(final["optimizer"]["state"]) == len(init) == 9
steps = []
for name, identifier in zip(init, group["params"]):
    state = final["optimizer"]["state"][identifier]
    steps.append(float(state["step"]))
    for key in ("exp_avg", "exp_avg_sq"):
        assert state[key].shape == init[name].shape and state[key].dtype == torch.float64
        assert bool(torch.isfinite(state[key]).all())
assert all(step == 1024 for step in steps)
displacement = float(torch.linalg.vector_norm(fv - iv))
close(displacement, summary["displacement"])
close(torch.linalg.vector_norm(iv), summary["initial_norm"])
for curve in curves:
    assert all(math.isfinite(curve[key]) for key in ("loss", "gradient_norm", "parameter_step_norm", "log_prior_strength", "prior_strength"))
    close(math.exp(curve["log_prior_strength"]), curve["prior_strength"])
eta = float(final["model"]["log_prior_strength"])
close(eta, curves[-1]["log_prior_strength"])
close(eta, summary["prior_strength"]["final_log"])
close(math.exp(eta), summary["prior_strength"]["final"])
assert summary["prior_strength"]["initial_log"] == 0 and summary["prior_strength"]["initial"] == 1
primary_means = {role: {key: float(np.mean([summary["endpoint_means"][role][cell][key] for cell in primary]))
                        for key in ("U", "F", "tau", "Y", "unmet_ticks")} for role in roles}
for role in roles:
    primary_means[role]["tau40_count_of128"] = sum(summary["endpoint_means"][role][cell]["tau40"] for cell in primary)
native = {key: float(value) for key, value in (line.split("=", 1) for line in (root / "b13_control/native.time").read_text().splitlines())}
assert native["exit_code"] == 0  # Ordinary wall plans are estimates, not validity gates.
files = [dict(path=file.relative_to(root).as_posix(), bytes=file.stat().st_size,
              sha256=hashlib.sha256(file.read_bytes()).hexdigest()) for file in sorted(root.rglob("*")) if file.is_file()]
result = dict(object_id=summary["object_id"], source_sha_canonical=args.launch_sha,
              independent_fits=1, training_episodes=65536, evaluation_episodes=2560, updates=1024,
              native_ticks=4358144, native32_batches=2128, evaluation=checks,
              checkpoint=dict(parameters=2562, dtype="float64", displacement=displacement,
                              changed_parameters=int((iv != fv).sum()), optimizer_steps=steps,
                              initial_eta=0.0, final_eta=eta, final_prior_strength=math.exp(eta)),
              observed_curve=dict(first32_mean_training_Y=float(np.mean([v["Y"] for c in curves[:32] for v in c["per_cell"].values()])),
                                  last32_mean_training_Y=float(np.mean([v["Y"] for c in curves[-32:] for v in c["per_cell"].values()])),
                                  nonzero_parameter_updates=sum(c["parameter_step_norm"] > 0 for c in curves),
                                  minimum_eta=min(c["log_prior_strength"] for c in curves), maximum_eta=max(c["log_prior_strength"] for c in curves)),
              primary_means=primary_means, comparison=comparisons, all_eight_cell_means=summary["endpoint_means"],
              sampled_reading_flags=summary["reading_flags"], native_receipt=native,
              nested_study_body_wall_s=summary["study_body_wall_s"], files=files,
              evaluation_displacement=dict(value=summary["evaluation_parameter_displacement"], source="runner measurement; saved final checkpoint precedes evaluation, not an independent after-evaluation checkpoint"),
              scope="Retained bytes and conditional paired scenarios of one fit; no model/rollout/RNG/update. Modal contrasts separate from sampled learning. No training-population variance or eta causal effect.")
args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf8")
print(json.dumps({key: result[key] for key in ("checkpoint", "observed_curve", "primary_means", "comparison", "native_receipt")}, indent=2))

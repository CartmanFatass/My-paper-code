"""E01 retained-output checks and paired arithmetic only; no model or native calls."""
import argparse, hashlib, json, math, statistics
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--root", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
a = p.parse_args()
s = json.loads((a.root / "modal_e01/summary.json").read_text())
assert s["status"] == "COMPLETE" and s["object_id"] == "RCLE_FIXED_MODAL_REUSE_E01"
assert s["launch_sha"] == "5c3ab7b074f185902078452811774e6a8d727a9d"
assert s["retained_completed_fits"] == 2
assert all(s[k] == 0 for k in ("new_fits", "new_training_episodes", "new_backward_calls", "new_optimizer_calls"))
assert s["new_evaluation_episodes"] == 1024 and s["native_ticks"] == 65536
assert s["native_source_sha256"] == "18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819"
cells = {f"{path}.{mode}" for path in ("8_to_8", "12_to_12", "8_to_12", "12_to_8") for mode in ("ACTIVE_CONTINUATION", "NEW_EPOCH")}
primary = ("8_to_12.ACTIVE_CONTINUATION", "12_to_8.ACTIVE_CONTINUATION")
metrics = ("U", "F", "tau", "tau40", "unmet_ticks", "Y")
expected = {(c, i) for c in cells for i in range(64)}
result = {}; assignments = claims = episodes = 0
for name in ("b10", "b12"):
    base = s["bases"][name]
    assert base["evaluation_episodes"] == 512 and base["native_ticks"] == 32768
    assert base["parameter_displacement"] == base["new_optimizer_calls"] == 0
    panels = {r: json.loads((a.root / f"modal_e01/{name}/{r}.json").read_text()) for r in ("modal", "greedy")}
    means = {}; indexed = {}
    for role, rows in panels.items():
        assert len(rows) == 512 and {(r["cell"], r["scenario"]) for r in rows} == expected
        indexed[role] = {(r["cell"], r["scenario"]): r for r in rows}
        assert all(math.isfinite(r[k]) for r in rows for k in ("U", "F", "tau", "unmet_ticks", "Y"))
        assert all(0 <= r["U"] <= 1 and r["F"] == 0 and 0 <= r["tau"] <= 40 and 0 <= r["Y"] <= 1 for r in rows)
        assert all(math.isclose(r["unmet_ticks"], 40*r["U"], abs_tol=1e-12) for r in rows)
        means[role] = {}
        for cell in sorted(cells):
            v = [indexed[role][(cell, i)] for i in range(64)]
            means[role][cell] = {k: (sum(r["tau"] == 40 for r in v) if k == "tau40" else statistics.mean([r[k] for r in v])) for k in metrics}
            for k in metrics:
                assert math.isclose(means[role][cell][k], base["comparison"]["all_eight_cell_means"][role][cell][k], abs_tol=1e-14)
    paths = {}
    for cell in primary:
        delta = [indexed["greedy"][(cell, i)]["U"] - indexed["modal"][(cell, i)]["U"] for i in range(64)]
        old = base["comparison"]["D_mode_g"]["paths"][cell]
        assert all(math.isclose(x, y, abs_tol=1e-14) for x, y in zip(delta, old["differences"]))
        paths[cell] = dict(mean=statistics.mean(delta), conditional_se=statistics.stdev(delta)/8,
            favorable=sum(d > 0 for d in delta), adverse=sum(d < 0 for d in delta), ties=sum(d == 0 for d in delta))
        for k, v in paths[cell].items(): assert math.isclose(v, old[k], abs_tol=1e-14)
    mean = statistics.mean([r["mean"] for r in paths.values()])
    se = math.sqrt(sum(r["conditional_se"]**2 for r in paths.values()))/2
    assert math.isclose(mean, base["comparison"]["D_mode_g"]["mean"], abs_tol=1e-14)
    assert math.isclose(se, base["comparison"]["D_mode_g"]["conditional_se"], abs_tol=1e-14)
    diffs = {cell: {k: means["greedy"][cell][k] - means["modal"][cell][k] for k in metrics} for cell in sorted(cells)}
    for cell in cells:
        for k in metrics: assert math.isclose(diffs[cell][k], base["comparison"]["greedy_minus_modal_cell_differences"][cell][k], abs_tol=1e-14)
    counts = {k: dict(modal_favorable=sum((v[k] < 0 if k == "Y" else v[k] > 0) for v in diffs.values()),
        modal_adverse=sum((v[k] > 0 if k == "Y" else v[k] < 0) for v in diffs.values()), tied=sum(v[k] == 0 for v in diffs.values())) for k in metrics}
    rows = panels["modal"]
    assert sum(r["agent_claims"] for r in rows) == base["native_agent_claims"]
    assert sum(r["agent_ticks"] for r in rows) == base["native_agent_ticks"]
    for r in rows:
        n0, n1 = map(int, r["cell"].split(".")[0].split("_to_"))
        assert r["agent_claims"] == 6*n0 + 10*n1 and r["agent_ticks"] == 4*r["agent_claims"]
        claims += r["agent_claims"]; assignments += 6*n0*n0 + 10*n1*n1; episodes += 1
    row_equal = {k: sum(indexed["modal"][key][k] == indexed["greedy"][key][k] for key in expected) for k in ("U", "F", "tau", "unmet_ticks", "Y")}
    result[name] = dict(paired_row_equal_out_of512=row_equal, D_mode_g=dict(mean=mean, conditional_se=se, conditional_normal95=[mean-1.96*se, mean+1.96*se], paths=paths),
        all_eight_cell_means=means, greedy_minus_modal_cell_differences=diffs, cell_sign_counts=counts)
assert episodes == 1024 and claims == 163840 and assignments == 1703936
exposure = dict(new_fits=0, new_training_episodes=0, new_backward_calls=0, new_optimizer_calls=0,
    new_evaluation_episodes=episodes, native_ticks=episodes*64, native_batch32_calls=episodes//32,
    modal_team_decisions=episodes*16, phase_heads=claims, assignment_rows=assignments,
    accounting_basis="Complete per-row native counters plus reviewed two32-row-per-cell evaluator partition and roster schedule; historical fits and greedy rows add no new exposure")
report = dict(status="RECORDED_BYTES_CHECKED", source_sha=s["launch_sha"], summary_sha256=hashlib.sha256((a.root/"modal_e01/summary.json").read_bytes()).hexdigest(),
    exposure=exposure, parameter_displacement={b:s["bases"][b]["parameter_displacement"] for b in result}, bases=result,
    interpretation_limit="Conditional post-outcome two-retained-base observations on seen panels; no new learning or equivalence claim; B11 missing endpoint retained")
a.out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf8")
print(json.dumps({"exposure":exposure,"bases":{b:r["D_mode_g"] for b,r in result.items()}},indent=2))

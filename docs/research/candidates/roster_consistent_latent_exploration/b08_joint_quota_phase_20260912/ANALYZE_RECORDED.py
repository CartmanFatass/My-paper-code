"""B08 read-only intake analysis over retained bytes; no model construction or rollout."""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import torch

p=argparse.ArgumentParser()
p.add_argument("--root", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
args=p.parse_args()
root=args.root
summary=json.loads((root/"b08_seed28/summary.json").read_text())
curves=[json.loads(x) for x in (root/"b08_seed28/curves.jsonl").read_text().splitlines()]
roles=("initialization","final256","greedy","nearest")
panels={r:json.loads((root/f"b08_seed28/{r}.json").read_text()) for r in roles}
primary=("8_to_12.ACTIVE_CONTINUATION","12_to_8.ACTIVE_CONTINUATION")
expected_cells=set(summary["endpoint_means"]["final256"])
assert len(curves)==256 and [x["update"] for x in curves]==list(range(1,257))
assert sum(x["training_episodes"] for x in curves)==16384
assert sum(x["backward_calls"] for x in curves)==sum(x["optimizer_calls"] for x in curves)==256
assert sum(x["native_ticks"] for x in curves)==1048576
checks={}
for role,rows in panels.items():
    assert len(rows)==512 and len({(r["cell"],r["scenario"]) for r in rows})==512
    assert {r["cell"] for r in rows}==expected_cells
    for cell in expected_cells:
        selected=[r for r in rows if r["cell"]==cell]
        assert sorted(r["scenario"] for r in selected)==list(range(64))
        for key in ("U","F","tau","Y","unmet_ticks"):
            assert math.isclose(float(np.mean([r[key] for r in selected])),summary["endpoint_means"][role][cell][key],abs_tol=1e-14)
    assert all(math.isfinite(r[k]) for r in rows for k in ("U","F","tau","Y","unmet_ticks"))
    assert all(0<=r["U"]<=1 and 0<=r["F"]<=1 and 0<=r["Y"]<=1 and 0<=r["tau"]<=40 for r in rows)
    assert all(math.isclose(r["unmet_ticks"],40*r["U"],abs_tol=1e-12) for r in rows)
    if role!="nearest": assert all(r["F"]==0 for r in rows)
    checks[role]=dict(rows=len(rows),cells=len(expected_cells),agent_ticks=sum(r["agent_ticks"] for r in rows),agent_claims=sum(r["agent_claims"] for r in rows))
comparisons={}
for name,role in (("D_g","greedy"),("D_n","nearest"),("G_U","initialization")):
    paths={}
    for cell in primary:
        left={r["scenario"]:r for r in panels[role] if r["cell"]==cell}
        right={r["scenario"]:r for r in panels["final256"] if r["cell"]==cell}
        delta=np.array([left[i]["U"]-right[i]["U"] for i in range(64)])
        paths[cell]=dict(mean=float(delta.mean()),conditional_se=float(delta.std(ddof=1)/8),positive=int((delta>0).sum()),adverse=int((delta<0).sum()),ties=int((delta==0).sum()))
        assert np.allclose(delta,summary["comparison"][name]["paths"][cell]["differences"],rtol=0,atol=1e-14)
    mean=float(np.mean([d["mean"] for d in paths.values()]))
    se=math.sqrt(sum(d["conditional_se"]**2 for d in paths.values()))/2
    assert math.isclose(mean,summary["comparison"][name]["mean"],abs_tol=1e-14)
    assert math.isclose(se,summary["comparison"][name]["conditional_se"],abs_tol=1e-14)
    comparisons[name]=dict(mean=mean,conditional_se=se,conditional_normal95=[mean-1.96*se,mean+1.96*se],paths=paths)
init=torch.load(root/"b08_seed28/initialization.pt",map_location="cpu",weights_only=True)
final=torch.load(root/"b08_seed28/final256.pt",map_location="cpu",weights_only=True)
assert init.keys()==final["model"].keys()
assert all(t.dtype==torch.float64 and bool(torch.isfinite(t).all()) for t in final["model"].values())
iv=torch.cat([t.reshape(-1) for t in init.values()])
fv=torch.cat([t.reshape(-1) for t in final["model"].values()])
assert iv.numel()==fv.numel()==2561
steps=[float(x["step"]) for x in final["optimizer"]["state"].values()]
assert steps and all(s==256 for s in steps)
assert final["updates"]==256 and final["seed"]==28
assert final["launch_sha"]==summary["launch_sha"]
assert summary["launch_sha"].rstrip("\r")=="012a8bce2c90cbe54459437dba01d3f171c9e063"
displacement=float(torch.linalg.vector_norm(fv-iv))
assert math.isclose(displacement,summary["displacement"],abs_tol=1e-12)
assert all(math.isfinite(c[k]) for c in curves for k in ("loss","gradient_norm","parameter_step_norm"))
first32=float(np.mean([v["Y"] for c in curves[:32] for v in c["per_cell"].values()]))
last32=float(np.mean([v["Y"] for c in curves[-32:] for v in c["per_cell"].values()]))
primary_means={r:{k:float(np.mean([summary["endpoint_means"][r][c][k] for c in primary])) for k in ("U","F","tau","Y","unmet_ticks","tau40")} for r in roles}
native={k:float(v) for k,v in (l.split("=",1) for l in (root/"b08_control/native.time").read_text().splitlines())}
assert native["exit_code"]==0 and native["whole_native_wall_s"]<=900
files=[dict(path=str(p.relative_to(root)).replace("\\","/"),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(root.rglob("*")) if p.is_file()]
result=dict(object_id=summary["object_id"],source_sha_canonical="012a8bce2c90cbe54459437dba01d3f171c9e063",source_metadata_literal=summary["launch_sha"],source_metadata_deviation="one terminal CR from PowerShell-to-bash payload; canonical remote HEAD independently verified; metadata only, raw output retained",
   independent_fits=1,training_episodes=16384,updates=256,evaluation=checks,native_ticks=1179648,training_agent_ticks=sum(c["agent_ticks"] for c in curves),training_agent_claims=sum(c["agent_claims"] for c in curves),
   checkpoint=dict(parameters=iv.numel(),dtype="float64",initial_norm=float(torch.linalg.vector_norm(iv)),displacement=displacement,changed_parameters=int((iv!=fv).sum()),optimizer_steps=steps,baseline_shape=list(final["baselines"].shape)),
   observed_curve=dict(first32_mean_training_Y=first32,last32_mean_training_Y=last32,nonzero_parameter_updates=sum(c["parameter_step_norm"]>0 for c in curves),minimum_gradient_norm=min(c["gradient_norm"] for c in curves),maximum_gradient_norm=max(c["gradient_norm"] for c in curves)),
   primary_means=primary_means,comparison=comparisons,reading_flags=summary["reading_flags"],native_receipt=native,all_eight_cell_means=summary["endpoint_means"],files=files,
   scope="read-only checks and arithmetic over retained bytes; zero new fitting, rollout, screening or seed independence")
args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf8")
print(json.dumps({k:result[k] for k in ("checkpoint","observed_curve","primary_means","comparison","native_receipt")},indent=2))


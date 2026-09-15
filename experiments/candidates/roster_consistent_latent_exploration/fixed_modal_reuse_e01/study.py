"""Fixed modal E01: original worlds, new modal trajectories, no new training."""
import hashlib
import io
import json
import math
from pathlib import Path
import time

import numpy as np
import torch

from ..joint_quota_phase import study as phase_study
from ..joint_quota_phase.policy import PhasePolicy, flat_parameters

OBJECT = "RCLE_FIXED_MODAL_REUSE_E01"
LAW = "softmax(log(q)+z); q=.9*exact_greedy+.1/N"
BASES = {
    "b10": dict(seed=30, object_id="RCLE-TBCFV-B10-GREEDY-ANCHORED-1024",
        source_sha="e5fd439735bcc52d7f4cba9943b8c5c5138e21c2",
        checkpoint_sha256="c0e0a5385d190460c289c5ab1e43b1ef13628e4b5ec5df23188dbe3aae9793cf",
        greedy_sha256="00804e6f141379ca240a526b362e425a9c112a67f3da48c92ef5ce913e667ed1"),
    "b12": dict(seed=32, object_id="RCLE-TBCFV-B12-GREEDY-ANCHORED-1024-INDEPENDENT",
        source_sha="15eaa7ea655a0f42a0ec3986927487892bdce212",
        checkpoint_sha256="0bece0f2db200e4589c84e7624f21f77a6aee31a51f55d81df90280622b4d3eb",
        greedy_sha256="90857130ebb8f7cc1f80f5a1c8b03ac7787658026122966c4c9710382eabb936"),
}


def validate_panel(rows):
    expected = {(cell, i) for cell in phase_study.HELDOUT_CELLS for i in range(64)}
    if len(rows) != 512 or {(r["cell"], r["scenario"]) for r in rows} != expected:
        raise ValueError("panel must contain each original cell/scenario exactly once")
    for r in rows:
        if not all(math.isfinite(r[k]) for k in ("U", "F", "tau", "Y", "unmet_ticks")):
            raise ValueError("nonfinite native outcome")
        if not (0 <= r["U"] <= 1 and r["F"] == 0 and 0 <= r["Y"] <= 1 and 0 <= r["tau"] <= 40):
            raise ValueError("native quota outcome outside its declared range")
        if not math.isclose(r["unmet_ticks"], 40 * r["U"], abs_tol=1e-12):
            raise ValueError("unmet ticks do not match the direct U endpoint")


def load_base(inputs, name):
    """Hash and load the card's exact bytes, not a mutable checkpoint glob."""
    spec = BASES[name]
    data = {}
    for filename, digest in (("final1024.pt", spec["checkpoint_sha256"]), ("greedy.json", spec["greedy_sha256"])):
        payload = (Path(inputs) / name / filename).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"{name}/{filename} differs from the frozen input")
        data[filename] = payload
    checkpoint = torch.load(io.BytesIO(data["final1024.pt"]), map_location="cpu", weights_only=True)
    for field, expected in (("object_id", spec["object_id"]), ("seed", spec["seed"]),
                            ("launch_sha", spec["source_sha"]), ("updates", 1024), ("action_law", LAW)):
        if checkpoint[field] != expected:
            raise ValueError(f"checkpoint {name} has wrong {field}")
    tensors = checkpoint["model"]
    if sum(p.numel() for p in tensors.values()) != 2561 or not all(
            p.dtype == torch.float64 and bool(torch.isfinite(p).all()) for p in tensors.values()):
        raise ValueError("checkpoint is not the finite2561-parameter FP64 model")
    model = PhasePolicy(greedy_anchored=True)  # This non-state_dict attribute is essential.
    model.load_state_dict(tensors, strict=True)
    model.eval()
    model.requires_grad_(False)
    greedy = json.loads(data["greedy.json"])
    validate_panel(greedy)
    key = hashlib.sha256(f"{spec['object_id']}/seed/{spec['seed']}".encode("ascii")).digest()
    return model, greedy, key


def compare(modal, greedy):
    paths = {}
    left = {(r["cell"], r["scenario"]): r for r in greedy}
    right = {(r["cell"], r["scenario"]): r for r in modal}
    for cell in phase_study.PRIMARY:
        delta = np.asarray([left[(cell, i)]["U"] - right[(cell, i)]["U"] for i in range(64)])
        paths[cell] = dict(mean=float(delta.mean()), conditional_se=float(delta.std(ddof=1) / 8),
            favorable=int((delta > 0).sum()), adverse=int((delta < 0).sum()), ties=int((delta == 0).sum()),
            differences=delta.tolist())
    mean = float(np.mean([p["mean"] for p in paths.values()]))
    se = math.sqrt(sum(p["conditional_se"] ** 2 for p in paths.values())) / 2
    means = {"modal": phase_study.cell_means(modal), "greedy": phase_study.cell_means(greedy)}
    differences = {c: {k: means["greedy"][c][k] - means["modal"][c][k]
        for k in ("U", "F", "tau", "tau40", "Y", "unmet_ticks")} for c in phase_study.HELDOUT_CELLS}
    return dict(D_mode_g=dict(mean=mean, conditional_se=se, conditional_normal95=[mean-1.96*se, mean+1.96*se], paths=paths),
        all_eight_cell_means=means, greedy_minus_modal_cell_differences=differences,
        difference_signs="positive favors modal for U/tau/tau40/unmet_ticks; negative favors modal for Y; F is structural")


def run(inputs, out, launch_sha):
    if len(launch_sha) != 40 or any(c not in "0123456789abcdef" for c in launch_sha):
        raise ValueError("full exact launch SHA required")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    # Load and verify both fixed inputs before constructing any empirical native state.
    loaded = {name: load_base(inputs, name) for name in BASES}
    binding = phase_study.bind_native_backend(build_root=out / "native_build")
    if binding.source_sha256 != "18d45b95a29c1ca8d17b4d192a9328ddc9c56a821a2690f118de44dbf0054819":
        raise ValueError("native source changed; original comparator reuse needs reassessment")
    results = {}
    for name, (model, greedy, key) in loaded.items():
        dest = out / name
        dest.mkdir()
        before = flat_parameters(model).clone()
        modal = phase_study.evaluate(model, "modal", key, binding, dest)
        validate_panel(modal)
        after = flat_parameters(model)
        if not torch.equal(before, after):
            raise ValueError("fixed policy parameters changed during evaluation")
        phase_study.write_json(dest / "greedy.json", greedy)
        results[name] = dict(input=BASES[name], evaluation_episodes=len(modal), native_ticks=64*len(modal),
            parameter_displacement=float(torch.linalg.vector_norm(after-before)), new_optimizer_calls=0,
            native_agent_ticks=sum(r["agent_ticks"] for r in modal), native_agent_claims=sum(r["agent_claims"] for r in modal),
            comparison=compare(modal, greedy))
        phase_study.write_json(dest / "result.json", results[name])
    summary = dict(status="COMPLETE", object_id=OBJECT, launch_sha=launch_sha, retained_completed_fits=2,
        new_fits=0, new_training_episodes=0, new_backward_calls=0, new_optimizer_calls=0,
        new_evaluation_episodes=sum(r["evaluation_episodes"] for r in results.values()),
        native_ticks=sum(r["native_ticks"] for r in results.values()), bases=results,
        execution_law="lowest-index argmax of actual combined log(q)+z; whole-team quota targets",
        inference_ceiling="post-outcome conditional measurement on two retained completed fits and reused seen panels; B11 missing endpoint retained",
        native_source_sha256=binding.source_sha256, body_wall_s=time.monotonic()-started)
    phase_study.write_json(out / "summary.json", summary)
    if json.loads((out / "summary.json").read_text(encoding="utf8"))["status"] != "COMPLETE":
        raise ValueError("summary publication failed")
    return summary

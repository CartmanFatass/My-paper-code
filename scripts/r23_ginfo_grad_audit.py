"""R23 g-info gradient audit (diagnostic-only, single-batch backward, no training).

Answers: does the g-info loss actually move Z-embedding / assignment-head params, and
how large is that gradient vs a PPO-style policy-loss gradient on the same batch?
Classifies: wiring (grad~0) / scale (grad << PPO) / form (grad present but MI can't move).

Usage:
  PYTHONPATH=. python scripts/r23_ginfo_grad_audit.py --checkpoint random --gain 0.5 --coef-skill 0.02
"""
from __future__ import annotations
import argparse, sys, numpy as np, torch


def _build_high_batch(agent, states_np, jobs_np):
    """Reproduce the g-info high_obs/prev/ages/compact/omega/relevance batch (per-agent rows)."""
    dev = agent.device
    na = int(agent.n_agents)
    R = states_np.shape[0]
    st = torch.as_tensor(states_np, dtype=torch.float32, device=dev)
    jo = torch.as_tensor(jobs_np, dtype=torch.float32, device=dev)
    compact, _cd, _cmi, weights, _ent, agent_rel = agent.compact(st, jo)
    B = R * na
    comp_b = compact.repeat_interleave(na, dim=0)
    obs_b = jo.reshape(B, agent.obs_dim)
    agent_ids = torch.arange(na, device=dev).repeat(R)
    prev_skills = torch.zeros(B, dtype=torch.long, device=dev)
    ages = torch.zeros(B, dtype=torch.float32, device=dev)
    omega_b = weights.repeat_interleave(na, dim=0) if agent.high_condition_on_omega else None
    rel_b = None
    if agent.use_agent_prototype_relevance:
        rel_b = agent_rel[torch.arange(R, device=dev).repeat_interleave(na), agent_ids]
    return obs_b, prev_skills, ages, comp_b, omega_b, rel_b


def _grad_norm(loss, params):
    ps = [p for p in params if p is not None and p.requires_grad]
    if not ps:
        return 0.0
    grads = torch.autograd.grad(loss, ps, retain_graph=True, allow_unused=True)
    tot = 0.0
    for g in grads:
        if g is not None:
            tot += float(g.detach().pow(2).sum().cpu())
    return tot ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="random")
    ap.add_argument("--structure-from", default="")
    ap.add_argument("--n-resets", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--gain", type=float, default=0.5)
    ap.add_argument("--coef-skill", type=float, default=0.02)
    a = ap.parse_args()

    struct_path = a.structure_from or (a.checkpoint if a.checkpoint != "random" else "")
    extra = f"--z_assignment_residual_gain {a.gain} --enable_g_info_objective --g_info_coef_skill {a.coef_skill}"
    base = ["train", "--config", "ha_ctse_process.config", "--scenario", "energy",
            "--preset", "S7-S1", "--n_agents", "6", "--num_envs", "1", "--device", "cpu",
            "--skill_lifetime_candidates", "1,2,3,4", "--skill_interval", "10",
            "--opt_num_prototypes", "4", "--prototype_skill_extra_codes", "0",
            "--team_bridge_type", "stochastic", "--enable_situation_diagnostics",
            "--enable_prototype_response_skills", "--enable_high_omega_conditioning",
            "--enable_agent_prototype_relevance", "--enable_per_agent_kappa",
            "--enable_prototype_disc_probe", "--prototype_disc_condition", "kappa",
            "--enable_team_intent", "--enable_team_disc_probe", "--team_intent_k", "8",
            "--seed", str(a.seed)] + extra.split()
    sys.argv = base
    from ha_ctse_process import train
    from ha_ctse_process.train import (load_config, normalize_scenario, apply_standalone_overrides,
                                        apply_checkpoint_structure, create_env, create_agent,
                                        load_checkpoint, load_checkpoint_metadata)
    args = train.parse_args()
    cfg = load_config(args.config, args.preset or None)
    cfg.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(cfg, args)
    if struct_path:
        apply_checkpoint_structure(cfg, args, load_checkpoint_metadata(struct_path))
    env = create_env(cfg, cfg.scenario, int(args.seed), rank=0, scale_mode="eval")
    try:
        _o, info = env.reset(seed=int(args.seed))
        sd = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size)
        agent = create_agent(cfg, args, env, num_envs=1, state_dim=sd)
    finally:
        env.close()
    if a.checkpoint != "random":
        load_checkpoint(a.checkpoint, agent, load_optimizers=False)

    env = create_env(cfg, cfg.scenario, 1234, rank=0, scale_mode="eval")
    states, jobs = [], []
    try:
        for r in range(a.n_resets):
            obs, info = env.reset(seed=1000 + r)
            states.append(np.asarray(info.get("state"), dtype=np.float32).reshape(-1))
            jobs.append(np.asarray(obs, dtype=np.float32).reshape(agent.n_agents, agent.obs_dim))
    finally:
        env.close()

    obs_b, prev, ages, comp_b, omega_b, rel_b = _build_high_batch(agent, np.stack(states), np.stack(jobs))
    high = agent.high

    g_loss, g_metrics = agent.g_info_objective(
        high_policy=high, bridge=agent.bridge, high_obs=obs_b, prev_skills=prev,
        ages=ages, compact=comp_b, omega=omega_b, agent_relevance=rel_b, total_steps=10 ** 9)

    def head_params(mod):
        return list(mod.parameters()) if mod is not None else []

    groups = {
        "code_embedding(Z)": list(agent.bridge.code_embedding.parameters()),
        "z_skill_residual(W_Z)": head_params(high.z_skill_residual),
        "z_duration_residual(U_Z)": head_params(high.z_duration_residual),
        "skill_head": list(high.skill_head.parameters()),
        "duration_head": list(high.duration_head.parameters()),
        "shared_input_trunk": list(high.input.parameters()),
    }
    g_norms = {k: _grad_norm(g_loss, v) for k, v in groups.items()}

    codes = torch.zeros(obs_b.shape[0], dtype=torch.long, device=agent.device)
    _c, tvec, *_ = agent.bridge(comp_b, forced_team_code=codes)
    sl, dl, _v = high.logits(obs_b, prev, ages, comp_b, tvec, omega=omega_b, agent_relevance=rel_b)
    ppo_like = torch.nn.functional.log_softmax(sl, -1).mean() + torch.nn.functional.log_softmax(dl, -1).mean()
    ppo_norms = {k: _grad_norm(ppo_like, v) for k, v in groups.items()}

    print(f"R23 g-info GRADIENT AUDIT  ckpt={a.checkpoint} gain={a.gain} coef_skill={a.coef_skill}  "
          f"g_info_skill_mi={g_metrics['g_info_skill_mi']:.5f} loss={g_metrics['g_info_loss']:.6e}")
    print(f"{'param group':26s} {'grad|g_info|':>14s} {'grad|ppo-ref|':>14s} {'ratio':>10s}")
    for k in groups:
        r = g_norms[k] / ppo_norms[k] if ppo_norms[k] > 0 else float('nan')
        print(f"{k:26s} {g_norms[k]:14.3e} {ppo_norms[k]:14.3e} {r:10.2e}")

    key = g_norms["z_skill_residual(W_Z)"] + g_norms["code_embedding(Z)"]
    ref = ppo_norms["z_skill_residual(W_Z)"] + ppo_norms["code_embedding(Z)"] + 1e-12
    if key < 1e-9:
        verdict = "WIRING: g-info grad ~0 to Z path -> detach/enumeration bug; fix before any sweep."
    elif key / ref < 1e-2:
        verdict = ("SCALE/FORM: g-info grad present but <<1% of ref; MI near-flat -> self-stalling "
                   "MI form; move to q_A residual (cross-entropy, first-order).")
    else:
        verdict = ("FORM/OTHER: g-info grad non-trivial; if MI still won't move it is cancelled by "
                   "PPO/entropy/clipping -> q_A residual.")
    print("VERDICT:", verdict)


if __name__ == "__main__":
    main()

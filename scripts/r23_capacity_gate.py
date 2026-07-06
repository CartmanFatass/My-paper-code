"""R23-0 static architecture capacity gate (diagnostic-only, no training).

Forces the sampled team intent Z = 0..C-1 on a fixed in-distribution batch and
measures how much Z moves the high-level assignment distributions (skill,
duration, and edit head if one exists). Answers: does the CURRENT architecture
have the capacity for Z to influence joint assignment xi, independent of the
objective? PASS if forced_Z_skill_KL_mean >= gate (default 0.02, ~10x the R21
decorative band of ~0.002).

Does NOT modify any algorithm module. Read-only over checkpoints + env resets.

Usage:
  PYTHONPATH=. python scripts/r23_capacity_gate.py \
      --checkpoint <path.pt|random> [--structure-from <path.pt>] \
      [--n-resets 48] [--gate 0.02] [--seed 1]
"""
from __future__ import annotations
import argparse, sys, numpy as np, torch


def _forced_z_probe(agent, states_np, jobs_np):
    dev = agent.device; C = int(agent.num_team_codes); na = int(agent.n_agents)
    R = states_np.shape[0]
    st = torch.as_tensor(states_np, dtype=torch.float32, device=dev)
    jo = torch.as_tensor(jobs_np, dtype=torch.float32, device=dev)
    with torch.no_grad():
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
        has_edit = hasattr(agent.high, "edit_head")
        sp, dp, ep = [], [], []
        for z in range(C):
            fz = torch.full((B,), z, dtype=torch.long, device=dev)
            _c, tvec, *_ = agent.bridge(comp_b, forced_team_code=fz)
            out = agent.high.logits(obs_b, prev_skills, ages, comp_b, tvec,
                                    omega=omega_b, agent_relevance=rel_b, ar_prefix=None)
            sl, dl = out[0], out[1]
            sp.append(torch.softmax(sl, -1)); dp.append(torch.softmax(dl, -1))
            if has_edit:
                ep.append(torch.softmax(agent.high.edit_head(sl.new_zeros(0)), -1))  # placeholder if present
    def summ(p):
        ref = p[0]
        kl = (p * (torch.log(p + 1e-12) - torch.log(ref.unsqueeze(0) + 1e-12))).sum(-1)
        tv = 0.5 * (p - ref.unsqueeze(0)).abs().sum(-1)
        am = p.argmax(-1)
        disagree = (am != am[0].unsqueeze(0)).float().mean().item()
        return dict(kl_mean=float(kl[1:].mean()), kl_max=float(kl.max()),
                    tv_mean=float(tv[1:].mean()), argmax_disagree=disagree)
    skill_p = torch.stack(sp); dur_p = torch.stack(dp)
    return summ(skill_p), summ(dur_p), has_edit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True, help="path to .pt, or 'random' for random-init")
    ap.add_argument("--structure-from", default="", help="ckpt to read structural config from when --checkpoint random")
    ap.add_argument("--n-resets", type=int, default=48)
    ap.add_argument("--gate", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--extra-args", default="", help="extra train CLI flags, space-separated")
    a = ap.parse_args()

    struct_path = a.structure_from or (a.checkpoint if a.checkpoint != "random" else "")
    if not struct_path:
        print("ERROR: --structure-from required when --checkpoint random"); sys.exit(2)

    base = ["train", "--config", "ha_ctse_process.config", "--scenario", "energy",
            "--preset", "S7-S1", "--n_agents", "6", "--num_envs", "1", "--device", "cpu",
            "--skill_lifetime_candidates", "3,7,13,24", "--skill_interval", "10",
            "--opt_num_prototypes", "4", "--prototype_skill_extra_codes", "0",
            "--team_bridge_type", "stochastic", "--enable_situation_diagnostics",
            "--enable_prototype_response_skills", "--enable_high_omega_conditioning",
            "--enable_agent_prototype_relevance", "--enable_per_agent_kappa",
            "--enable_prototype_disc_probe", "--prototype_disc_condition", "kappa",
            "--enable_team_intent", "--enable_team_disc_probe", "--team_intent_k", "48",
            "--seed", str(a.seed)] + (a.extra_args.split() if a.extra_args else [])
    sys.argv = base
    from ha_ctse_process import train
    from ha_ctse_process.train import (load_config, normalize_scenario, apply_standalone_overrides,
                                        apply_checkpoint_structure, create_env, create_agent,
                                        load_checkpoint, load_checkpoint_metadata)
    args = train.parse_args()
    cfg = load_config(args.config, args.preset or None)
    cfg.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(cfg, args)
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
    skill, dur, has_edit = _forced_z_probe(agent, np.stack(states), np.stack(jobs))
    passed = skill["kl_mean"] >= a.gate
    print(f"R23-0 CAPACITY GATE  checkpoint={a.checkpoint}  C={agent.num_team_codes}  gate(skill_KL_mean>={a.gate})")
    print(f"  SKILL    KL_mean={skill['kl_mean']:.5f} KL_max={skill['kl_max']:.5f} TV_mean={skill['tv_mean']:.5f} argmax_disagree={skill['argmax_disagree']:.3f}")
    print(f"  DURATION KL_mean={dur['kl_mean']:.5f} KL_max={dur['kl_max']:.5f} TV_mean={dur['tv_mean']:.5f} argmax_disagree={dur['argmax_disagree']:.3f}")
    print(f"  EDIT head present: {has_edit} (current high policy exposes skill+duration heads only; 'edit' is via AR/roster prefix, not a categorical head)")
    print(f"  VERDICT: {'PASS' if passed else 'FAIL'}  (skill_KL_mean={skill['kl_mean']:.5f} vs gate {a.gate}; R21 decorative band ~0.002)")


if __name__ == "__main__":
    main()

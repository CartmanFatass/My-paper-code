"""Standalone evaluation-loop owner for HA-CTSE process-core."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from ha_ctse_process import standalone_manifest
from ha_ctse_process.standalone_evaluation import evaluate
from ha_ctse_process.standalone_metrics import emit, log_eval_metrics
from ha_ctse_process.checkpoint_io import load_checkpoint
from ha_ctse_process.standalone_cli import create_agent, create_env
from ha_ctse_process.standalone_contracts import (
    dispatch_variable_roster_event_boundary,
    is_variable_roster_event,
)


def eval_loop(config, args: argparse.Namespace, writer) -> None:
    if is_variable_roster_event(config):
        dispatch_variable_roster_event_boundary(config)
    if not args.resume_from:
        raise ValueError("--mode eval requires --resume_from pointing to a standalone checkpoint")
    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="eval")
    try:
        _obs, info = env.reset(seed=args.seed)
        state_dim = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size) if info.get("state") is not None else None
        agent = create_agent(config, args, env, num_envs=1, state_dim=state_dim)
    finally:
        env.close()
    total_steps, update_idx = load_checkpoint(args.resume_from, agent, load_optimizers=False)
    standalone_manifest.export_run_manifest(
        args,
        config,
        env=env,
        agent=agent,
        total_steps=total_steps,
        update_idx=update_idx,
        mode="eval",
    )
    emit(
        args,
        "standalone_eval_start "
        f"path={args.resume_from} total_steps={total_steps} update_idx={update_idx} "
        f"action_mode={getattr(args, 'eval_action_mode', 'deterministic')} "
        f"duration_candidates={tuple(getattr(config, 'skill_lifetime_candidates', ())) }"
    )
    args.eval_checkpoint_name = Path(args.resume_from).name
    metrics = evaluate(
        agent,
        config,
        args,
        episodes=int(args.eval_episodes),
        total_steps=total_steps,
    )
    log_eval_metrics(writer, total_steps, metrics)

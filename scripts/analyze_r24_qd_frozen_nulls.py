from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from ha_ctse_process.r24_qd_dataset import FIELDS, QDWindowBatch, read_qd_window_shards, sample_qd_rows
from ha_ctse_process.team_conditioned_qd import TeamConditionedQDProbe


VARIANTS = (
    "real",
    "shuffled",
    "fake_marginal",
    "duration_matched",
    "agent_matched",
    "behavior_only",
    "pre_only",
    "action_only",
    "effect_only",
)


def _take(batch: QDWindowBatch, idx: np.ndarray) -> QDWindowBatch:
    return QDWindowBatch(**{field: getattr(batch, field)[idx] for field in FIELDS})


def _split_indices(batch: QDWindowBatch, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(int(seed))
    envs = np.unique(batch.env_id)
    if envs.size >= 2:
        shuffled_envs = envs.copy()
        rng.shuffle(shuffled_envs)
        n_eval_envs = max(1, int(np.ceil(0.2 * shuffled_envs.size)))
        eval_envs = set(int(v) for v in shuffled_envs[:n_eval_envs])
        eval_idx = np.asarray([i for i, env_id in enumerate(batch.env_id) if int(env_id) in eval_envs], dtype=np.int64)
        train_idx = np.asarray([i for i, env_id in enumerate(batch.env_id) if int(env_id) not in eval_envs], dtype=np.int64)
        if train_idx.size > 0 and eval_idx.size > 0:
            return train_idx, eval_idx

    idx = np.arange(batch.labels.shape[0], dtype=np.int64)
    rng.shuffle(idx)
    n_eval = max(1, int(round(0.2 * idx.size)))
    return np.sort(idx[n_eval:]), np.sort(idx[:n_eval])


def _shuffle_within(labels: np.ndarray, groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    out = labels.copy()
    for group in np.unique(groups):
        idx = np.flatnonzero(groups == group)
        if idx.size > 1:
            out[idx] = out[idx[rng.permutation(idx.size)]]
    return out.astype(np.int64, copy=False)


def _variant_batch(batch: QDWindowBatch, variant: str, seed: int, num_skills: int) -> QDWindowBatch:
    rng = np.random.default_rng(int(seed))
    labels = batch.labels.astype(np.int64, copy=True)
    action = batch.action.astype(np.float32, copy=True)
    effect = batch.effect.astype(np.float32, copy=True)
    condition = batch.condition.astype(np.float32, copy=True)
    pre_action = batch.pre_action.astype(np.float32, copy=True)
    pre_effect = batch.pre_effect.astype(np.float32, copy=True)

    if variant == "shuffled":
        labels = labels[rng.permutation(labels.shape[0])]
    elif variant == "fake_marginal":
        counts = np.bincount(labels.clip(0, num_skills - 1), minlength=num_skills).astype(np.float64)
        probs = counts / max(float(counts.sum()), 1.0)
        labels = rng.choice(np.arange(num_skills, dtype=np.int64), size=labels.shape[0], p=probs)
    elif variant == "duration_matched":
        labels = _shuffle_within(labels, batch.duration_idx, rng)
    elif variant == "agent_matched":
        labels = _shuffle_within(labels, batch.agent_id, rng)
    elif variant == "behavior_only":
        condition = np.zeros_like(condition, dtype=np.float32)
    elif variant == "pre_only":
        action = pre_action.copy()
        effect = pre_effect.copy()
    elif variant == "action_only":
        effect = np.zeros_like(effect, dtype=np.float32)
        pre_effect = np.zeros_like(pre_effect, dtype=np.float32)
    elif variant == "effect_only":
        action = np.zeros_like(action, dtype=np.float32)
        pre_action = np.zeros_like(pre_action, dtype=np.float32)
    elif variant != "real":
        raise ValueError(f"unknown frozen q_d variant: {variant}")

    return replace(
        batch,
        action=action,
        effect=effect,
        condition=condition,
        labels=labels,
        pre_action=pre_action,
        pre_effect=pre_effect,
    )


def _tensor(values: np.ndarray, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    return torch.as_tensor(values, dtype=dtype)


def _losses(probe: TeamConditionedQDProbe, batch: QDWindowBatch) -> dict[str, torch.Tensor]:
    return probe.losses(
        _tensor(batch.action),
        _tensor(batch.effect),
        _tensor(batch.condition),
        _tensor(batch.labels, torch.long),
        pre_action=_tensor(batch.pre_action),
        pre_effect=_tensor(batch.pre_effect),
        pre_mask=_tensor(batch.pre_valid) > 0.5,
    )


def _train_probe(
    train: QDWindowBatch,
    eval_batch: QDWindowBatch,
    *,
    num_skills: int,
    hidden_dim: int,
    steps: int,
    lr: float,
    seed: int,
) -> dict[str, float]:
    torch.manual_seed(int(seed))
    probe = TeamConditionedQDProbe(
        action_dim=int(train.action.shape[1]),
        effect_dim=int(train.effect.shape[1]),
        condition_dim=int(train.condition.shape[1]),
        num_skills=int(num_skills),
        hidden_dim=int(hidden_dim),
    )
    optimizer = torch.optim.Adam(probe.parameters(), lr=float(lr))
    for _ in range(int(max(steps, 0))):
        optimizer.zero_grad()
        losses = _losses(probe, train)
        losses["loss"].backward()
        optimizer.step()

    with torch.no_grad():
        train_terms = _losses(probe, train)
        terms = _losses(probe, eval_batch)

    def scalar(name: str) -> float:
        return float(terms[name].detach().cpu().item())

    return {
        "rows_train": float(train.labels.shape[0]),
        "rows_eval": float(eval_batch.labels.shape[0]),
        "loss_full": scalar("loss_full"),
        "loss_prior": scalar("loss_prior"),
        "acc_full": scalar("acc_full"),
        "acc_prior": scalar("acc_prior"),
        "acc_behavior": scalar("acc_behavior"),
        "acc_pre": scalar("acc_pre"),
        "acc_majority": scalar("acc_majority"),
        "residual_gain": scalar("residual_gain"),
        "residual_mean": scalar("residual_mean"),
        "positive_frac": scalar("positive_frac"),
        "behavior_gain_over_prior": scalar("behavior_gain_over_prior"),
        "pre_gain_over_prior": scalar("pre_gain_over_prior"),
        "full_minus_behavior_acc": scalar("full_minus_behavior_acc"),
        "full_minus_pre_acc": scalar("full_minus_pre_acc"),
        "label_entropy": scalar("label_entropy"),
        "label_max_frac": scalar("label_max_frac"),
        "train_acc_full": float(train_terms["acc_full"].detach().cpu().item()),
    }


def _write_reports(output_dir: Path, results: dict[str, dict[str, float]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "r24_qd_frozen_nulls.json"
    md_path = output_dir / "r24_qd_frozen_nulls.md"
    json_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# R24 Frozen q_d Null Probes",
        "",
        "| variant | residual_gain | positive_frac | acc_full | acc_prior | acc_behavior | acc_pre | rows_eval |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant in VARIANTS:
        row = results.get(variant, {})
        lines.append(
            "| {variant} | {residual_gain:.6f} | {positive_frac:.6f} | {acc_full:.6f} | "
            "{acc_prior:.6f} | {acc_behavior:.6f} | {acc_pre:.6f} | {rows_eval:.0f} |".format(
                variant=variant,
                residual_gain=float(row.get("residual_gain", 0.0)),
                positive_frac=float(row.get("positive_frac", 0.0)),
                acc_full=float(row.get("acc_full", 0.0)),
                acc_prior=float(row.get("acc_prior", 0.0)),
                acc_behavior=float(row.get("acc_behavior", 0.0)),
                acc_pre=float(row.get("acc_pre", 0.0)),
                rows_eval=float(row.get("rows_eval", 0.0)),
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_frozen_null_analysis(
    input_dir: Path,
    output_dir: Path,
    *,
    num_skills: int,
    steps: int,
    seed: int,
    hidden_dim: int = 128,
    lr: float = 3e-3,
    max_rows: int = 0,
) -> dict[str, dict[str, float]]:
    torch.set_num_threads(1)
    batch = read_qd_window_shards(Path(input_dir))
    if int(max_rows) > 0:
        batch = sample_qd_rows(batch, max_rows=int(max_rows), seed=int(seed))
    if batch.labels.shape[0] < 2:
        raise ValueError("frozen q_d analysis requires at least two rows")

    train_idx, eval_idx = _split_indices(batch, seed=int(seed))
    results: dict[str, dict[str, float]] = {}
    for offset, variant in enumerate(VARIANTS):
        variant_batch = _variant_batch(
            batch,
            variant,
            seed=int(seed) + 1009 * (offset + 1),
            num_skills=int(num_skills),
        )
        results[variant] = _train_probe(
            _take(variant_batch, train_idx),
            _take(variant_batch, eval_idx),
            num_skills=int(num_skills),
            hidden_dim=int(hidden_dim),
            steps=int(steps),
            lr=float(lr),
            seed=int(seed) + offset,
        )

    _write_reports(Path(output_dir), results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze frozen R24 q_d window null probes.")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--num_skills", type=int, required=True)
    parser.add_argument("--hidden_dim", type=int, default=128)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--max_rows", type=int, default=0)
    args = parser.parse_args()
    run_frozen_null_analysis(
        Path(args.input_dir),
        Path(args.output_dir),
        num_skills=int(args.num_skills),
        hidden_dim=int(args.hidden_dim),
        steps=int(args.steps),
        lr=float(args.lr),
        seed=int(args.seed),
        max_rows=int(args.max_rows),
    )


if __name__ == "__main__":
    main()

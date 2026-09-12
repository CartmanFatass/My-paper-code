"""One fresh B07 equal-unit fit on the unchanged .99-prior native service path."""
import torch

from experiments.candidates.roster_consistent_latent_exploration.b04_nearest_prior import study as b04
from experiments.candidates.roster_consistent_latent_exploration.b06_nearest99_prior1000.study import LAW
from .update import step_from_losses

host = b04.host
b03 = b04.b03
OBJECT_ID = "RCLE-TBCFV-B07-EQUAL-UNIT"
SEED = 27
UPDATES = 1000


def training_update(model, rng, update, baselines, progress=None):
    progress = {} if progress is None else progress
    results, cells = [], []
    for start in range(0, 8, 4):
        coordinates = tuple(
            b03.EpisodeCoordinate(rng.block_index, cell, update, row)
            for cell in host.TRAINING_CELLS[start:start + 4] for row in range(8))
        results.extend(b03.execute_learned_batch(model, b03.FLEX, rng, coordinates, training=True))
        progress["returned_training_episodes"] = len(results)
        cells.extend(cell for cell in range(start, start + 4) for _ in range(8))
    returns = torch.tensor([r.Y for r in results], dtype=torch.float64)
    indices = torch.tensor(cells, dtype=torch.int64)
    means = [b03.averaged_episode_score(torch.stack(r.plan_scores), torch.stack(r.claim_scores))
             for r in results]
    advantage = returns.detach() - baselines.detach()[indices]
    manager_loss = -(advantage * torch.stack([mean[0] for mean in means])).mean()
    claim_loss = -(advantage * torch.stack([mean[1] for mean in means])).mean()
    model.zero_grad(set_to_none=True)
    step = step_from_losses(tuple(model.parameters()), manager_loss, claim_loss, progress)
    # Both derivatives and the single parameter step precede this baseline change.
    cell_means = torch.stack([returns[indices == cell].mean() for cell in range(8)])
    updated_baselines = (.95 * baselines + (1.0 - .95) * cell_means).detach()
    progress["baseline_updates_completed"] = 1
    curve = {
        "update": update, **step, "event_order": ["parameter_update", "baseline_update"],
        "per_cell": [dict(cell=cell, episodes=8, **{
            f"{key}_mean": host._mean([float(getattr(results[i], key)) for i in range(64) if cells[i] == c])
            for key in ("Y", "U", "tau", "F")}) for c, cell in enumerate(host.TRAINING_CELLS)],
        "training_episodes": len(results), "environment_ticks": 64 * len(results),
        "agent_ticks": sum(r.agent_ticks for r in results),
        "agent_claim_decisions": sum(r.claim_decisions for r in results),
    }
    return updated_baselines, curve


def run(arm, out, launch_sha, admission_receipt, started, wall_cap, learned_summary=None, seed=SEED):
    return b04.run(arm, out, launch_sha, admission_receipt, started, wall_cap,
                   learned_summary, seed, updates=UPDATES, object_id=OBJECT_ID,
                   panel_label="B07", action_law=LAW, equal_unit_update=training_update)

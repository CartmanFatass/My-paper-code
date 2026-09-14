"""One synthetic training-lifetime diagnostic; never a scientific B11 endpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase import study
from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase.policy import (
    PhasePolicy, adam_update,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    key = hashlib.sha256(b"SYNTHETIC-RCLE-B11-FAULT-D1/seed/1").digest()
    binding = study.bind_native_backend(build_root=out / "native_build")
    model = PhasePolicy(greedy_anchored=True)

    def entries(name, count):
        return study.uniforms(key, binding, [
            study._address(0, parameter_entry=name,
                           draw_kind="common-initial-parameter", draw_index=i)
            for i in range(count)
        ])

    model.initialize(entries)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4, betas=(.9, .999),
                                 eps=1e-8, weight_decay=0, foreach=False)
    baselines = torch.zeros(8, dtype=torch.float64)
    for update in range(1, 193):
        episodes, batch_scores = [], []
        for start in (0, 4):
            coords = tuple(study.EpisodeCoordinate(0, cell, update, row)
                           for cell in study.TRAINING_CELLS[start:start + 4]
                           for row in range(8))
            results, scores = study.rollout(model, "learned", key, binding,
                                            coords, training=True)
            episodes.extend(results)
            batch_scores.append(scores)
        returns = torch.tensor([r["Y"] for r in episodes], dtype=torch.float64)
        indices = torch.arange(8).repeat_interleave(8)
        baselines, _ = adam_update(model, optimizer, returns, torch.cat(batch_scores),
                                  indices, baselines)
        print(json.dumps({"diagnostic": "SYNTHETIC-D1", "completed_update": update}),
              flush=True)
    (out / "diagnostic.json").write_text(json.dumps({
        "diagnostic": "SYNTHETIC-D1", "status": "COMPLETED_WITHOUT_REPRODUCTION",
        "updates": 192, "training_episodes": 12288, "native_ticks": 786432,
        "scientific_results": False,
        "limitation": "One synthetic diagnostic does not establish B11 validity or runtime safety.",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

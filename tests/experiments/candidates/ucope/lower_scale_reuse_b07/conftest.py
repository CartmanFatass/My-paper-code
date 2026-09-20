import hashlib
import json
import math

import pytest
import torch

from experiments.candidates.ucope.lower_scale_reuse_b07 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import arm_copy, templates


@pytest.fixture
def admission():
    return {
        "schema_version": 1,
        "direction": "ucope",
        "sha": "admitted-b07-sha",
        "command_sha256": "command-digest",
        "parent_pid": 41,
        "child_pid": 42,
        "accepted_at_epoch": 123.5,
    }


@pytest.fixture
def inherited_files(tmp_path):
    config = study.Config.engineering()
    common = templates(config.master)
    actor, critic = arm_copy(common, False)
    common_digest = study._model_digest(actor, critic, common_only=True)
    with torch.no_grad():
        actor.log_std.fill_(math.log(0.5))
        actor.mean.bias.add_(0.05)
    checkpoint = tmp_path / "B06_Ghalf_final.pt"
    torch.save(
        {
            "object": study.SOURCE_OBJECT,
            "actor": actor.state_dict(),
            "critic": critic.state_dict(),
            "arm": "Ghalf",
            "seed": config.master,
            "train_episodes": config.train_episodes,
            "optimizer_steps": 2 * config.train_episodes,
            "initial_log_std": [math.log(0.5)] * 3,
        },
        checkpoint,
    )
    checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    summary = tmp_path / "B06_summary.json"
    summary.write_text(
        json.dumps(
            {
                "object": study.SOURCE_OBJECT,
                "master": config.master,
                "launch_sha": study.SOURCE_SHA,
                "status": "COMPLETE",
                "configuration": {
                    "master": config.master,
                    "horizon": config.horizon,
                    "train_episodes": config.train_episodes,
                    "eval_episodes": config.eval_episodes,
                    "chunk": config.chunk,
                    "watchdog_seconds": config.watchdog_seconds,
                    "fixture": True,
                },
                "paired_common_initial_sha256": common_digest,
                "arms": {
                    "Ghalf": {
                        "train_complete": True,
                        "common_initial_sha256": common_digest,
                        "initial_log_std": [math.log(0.5)] * 3,
                        "checkpoint": {
                            "bytes": checkpoint.stat().st_size,
                            "sha256": checkpoint_sha,
                        },
                        "counts": {
                            "train_episodes": config.train_episodes,
                            "train_team_steps": config.train_episodes * config.horizon,
                            "optimizer_steps": 2 * config.train_episodes,
                        },
                        "evaluation_immutability": {
                            "optimizer_steps": 0,
                            "parameter_exposure": {
                                "total": {"displacement": 0.0}
                            },
                        },
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    source = tmp_path / "B06_source.json"
    source.write_text(
        json.dumps(
            {
                "object": study.SOURCE_OBJECT,
                "launch_sha": study.SOURCE_SHA,
                "shared_collector": {
                    "present": True,
                    "sha256": study.EXPECTED_SHARED_SHA256["ordinary_learner"],
                },
                "shared_policy": {
                    "present": True,
                    "sha256": study.EXPECTED_SHARED_SHA256["ordinary_policy"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    return study.InheritedFiles(
        checkpoint=checkpoint,
        summary=summary,
        source=source,
        checkpoint_sha256=digest(checkpoint),
        summary_sha256=digest(summary),
        source_sha256=digest(source),
    )

import hashlib
import io
import tarfile

import pytest
import torch

from experiments.candidates.ucope.mean_agreement_deployment_b05 import study
from experiments.candidates.ucope.reactive_rate_b03.scalar import scalar_actor
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import arm_copy, templates


@pytest.fixture
def admission():
    return {
        "schema_version": 1,
        "direction": "ucope",
        "sha": "admitted-b05-sha",
        "command_sha256": "command-digest",
        "parent_pid": 41,
        "child_pid": 42,
        "accepted_at_epoch": 123.5,
    }


@pytest.fixture
def archive_factory(tmp_path):
    def make(*, overrides=None, omit=()):
        overrides = overrides or {}
        config = study.Config.engineering()
        common = templates(config.master)
        b_actor, b_critic = scalar_actor(common)
        g_actor, g_critic = arm_copy(common, False)
        models = {"B": (b_actor, b_critic), "G": (g_actor, g_critic)}
        path = tmp_path / f"checkpoints-{len(list(tmp_path.glob('checkpoints-*.tar.gz')))}.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for arm, (actor, critic) in models.items():
                name = f"{arm}_final.pt"
                if name in omit:
                    continue
                payload = {
                    "object": study.SOURCE_OBJECT,
                    "actor": actor.state_dict(),
                    "critic": critic.state_dict(),
                    "arm": arm,
                    "seed": config.master,
                    "train_episodes": 2048,
                    "optimizer_steps": 4096,
                }
                payload.update(overrides.get(arm, {}))
                buffer = io.BytesIO()
                torch.save(payload, buffer)
                data = buffer.getvalue()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
            log = b"fixture only\n"
            member = tarfile.TarInfo("stdout.log")
            member.size = len(log)
            archive.addfile(member, io.BytesIO(log))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, digest

    return make

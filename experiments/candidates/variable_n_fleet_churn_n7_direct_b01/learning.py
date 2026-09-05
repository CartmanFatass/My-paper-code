"""Fresh N7 worlds, canonical actors and the unchanged terminal GAE/PPO objective."""

import hashlib
import math
from dataclasses import replace
from types import SimpleNamespace
from time import perf_counter

import torch

from scripts import run_vnfc_bpcr_b_explore as r01
from scripts.run_vnfc_bpcr_r02 import build_canonical_model_classes
from ..variable_n_fleet_churn_bpcr_r09.empirical_training import _model_inputs, make_optimizer, _normal_source_shape
from ..variable_n_fleet_churn_bpcr_r09.torch_models import materialize_external_initialization, mapr_parameter_shapes, direct_parameter_shapes
from ..variable_n_fleet_churn_bpcr_r09.training import gae_terminal, normalize_advantages, ppo_loss
from ..variable_n_fleet_churn_bpcr_r09.rng import address
from ..variable_n_fleet_churn_bpcr_r09.services import _shuffle
from .native import Batch

MAPR, CanonicalDirect = build_canonical_model_classes(r01)


class Direct(CanonicalDirect):
    """Observe actual residual logits without changing values or autograd."""

    def prefix_adjustment(self, summary, hidden, prefix_sum, prefix_max):
        value = super().prefix_adjustment(summary, hidden, prefix_sum, prefix_max)
        if self.residual_observation is not None:
            detached = value.detach()
            self.residual_observation[0] += float(detached.square().sum())
            self.residual_observation[1] += detached.numel()
            self.residual_observation[2] = max(self.residual_observation[2], float(detached.abs().max()))
        return value


def rng(seed, namespace, stream):
    material = f"HMASD/VNFC-N7-DIRECT-B01/{namespace}/{seed}/{stream}".encode()
    return r01._SeedRNG(hashlib.sha256(material).digest())


def coordinate(namespace, domain, purpose, round_index=0, episode=0, zone=1, time=0, draw=0):
    return address(replicate_role="BPCR-REP-00", domain=domain, purpose=f"{namespace}/{purpose}",
                   roster_size=7, failed_zone=zone, update_or_panel_row=round_index,
                   episode_row=episode, physical_time=time, draw=draw)


def initialize(seed, namespace):
    source = rng(seed, namespace, "initialization")
    base, residual = {}, {}
    for target, shapes, domain in (
        (base, mapr_parameter_shapes(), "model-initialization/base"),
        (residual, {key: direct_parameter_shapes()[key] for key in
                    ("residual.0.weight", "residual.1.weight")}, "model-initialization/direct-residual"),
    ):
        for name, shape in shapes.items():
            if len(shape) != 2 or name == "null.embedding":
                continue
            builder = lambda draw, name=name, domain=domain: coordinate(namespace, domain, name, draw=draw)
            target[name] = (domain, source.normal_array(_normal_source_shape(shape), builder, now=None))
    mapr, direct = materialize_external_initialization(base, residual)
    models = {"MAPR": MAPR(mapr), "DIRECT": Direct(direct)}
    models["DIRECT"].residual_observation = None
    return models, {arm: make_optimizer(model) for arm, model in models.items()}


def worlds(seed, namespace, purpose, count, round_index=0):
    source = rng(seed, namespace, "exogenous-worlds")
    config = SimpleNamespace(namespace=namespace)
    return tuple(r01._build_world(source, config, purpose=purpose, roster_size=7,
                  failed_zone=1 + index // (count // 2), row=round_index * count + index, now=None)
                 for index in range(count))


def parameter_state(model, initial=None):
    parameters = dict(model.named_parameters())
    squared = sum(float(p.detach().square().sum()) for p in parameters.values())
    result = dict(count=sum(p.numel() for p in parameters.values()), norm=math.sqrt(squared),
                  max_abs=max(float(p.detach().abs().max()) for p in parameters.values()))
    result["rms"] = math.sqrt(squared / result["count"])
    if initial is not None:
        delta = sum(float((p.detach() - initial[name]).square().sum()) for name, p in parameters.items())
        initial_norm = math.sqrt(sum(float(p.square().sum()) for p in initial.values()))
        result.update(displacement_norm=math.sqrt(delta), relative_displacement=math.sqrt(delta) / initial_norm)
    residual = [p for name, p in parameters.items() if "residual" in name]
    if residual:
        result["residual_parameter_norm"] = math.sqrt(sum(float(p.detach().square().sum()) for p in residual))
        output = [p for name, p in parameters.items() if "residual__out" in name]
        result["residual_output_parameter_norm"] = math.sqrt(sum(float(p.detach().square().sum()) for p in output))
    return result


def terminal_metrics(row):
    if not row["terminal"] or row["integrated_ticks"] != 240 or row["epoch"] != 6:
        raise AssertionError("N7 episode did not complete its native 120-second terminal")
    result = r01._endpoint_values(row)
    result.update({name: list(row[name]) for name in ("fail_endpoint", "total_endpoint", "intact_endpoint")})
    result.update({name: row[name] for name in ("safety_violation", "exclusivity_violation", "event_count", "integrated_ticks")})
    return result


def rollout(library, fixtures, model, arm, namespace, action_source, round_index, training, check_presentation=False):
    started = perf_counter()
    count = len(fixtures)
    episodes = [[] for _ in fixtures]
    public_context = [[] for _ in fixtures]
    checks = dict(physical_commands=0, null_choices=0, fixed_choices=0, zone2_commands=0, presentation_checks=0)
    if arm == "DIRECT":
        model.residual_observation = [0.0, 0, 0.0]
    with Batch(library, fixtures) as batch:
        rows = batch.initial
        failed = [row["failed_rank"] for row in rows]
        for epoch in range(6):
            traces = [row["next_observation"] for row in rows]
            inputs = [_model_inputs(trace, fixture, lost) for trace, fixture, lost in zip(traces, fixtures, failed)]
            stacked = tuple(torch.cat([row[column] for row in inputs], 0) for column in range(6))
            if stacked[0].shape[1] != 7:
                raise AssertionError("expected seven surviving entity rows")
            uniforms = None
            if training:
                uniforms = torch.tensor([[(action_source.word(coordinate(namespace, "training/action", arm,
                    round_index, index, fixture.failed_zone, 20 * epoch, token), now=None) + .5) / float(1 << 64)
                    for token in range(4)] for index, fixture in enumerate(fixtures)], dtype=torch.float64)
            with torch.no_grad():
                output = model(*stacked, uniforms)
            relative = output["command"]
            commands = [r01._physical_command(relative[index], fixture, failed[index], epoch)
                        for index, fixture in enumerate(fixtures)]
            if check_presentation and epoch == 0:
                # One changed-presentation consequence check on an actual zone2
                # initial-evaluation state, without another episode or rollout.
                index = count // 2
                permutation = tuple(reversed(range(7)))
                permuted = r01._permuted_inputs(inputs[index], permutation)
                changed_batch = tuple(value.clone() for value in stacked)
                for column, value in enumerate(permuted):
                    changed_batch[column][index:index + 1] = value
                with torch.no_grad():
                    permuted_output = model(*changed_batch, None)
                presentations = list(fixtures[index].post_presentations)
                presentations[epoch] = tuple(reversed(presentations[epoch]))
                changed = replace(fixtures[index], post_presentations=tuple(presentations))
                physical = r01._physical_command(permuted_output["command"][index], changed, failed[index], epoch)
                if physical != commands[index]:
                    raise AssertionError("changed presentation changed the actual zone2 physical action")
                checks["presentation_checks"] += 1
            for index, trace in enumerate(traces):
                episodes[index].append(dict(inputs=tuple(value[index:index + 1] for value in stacked),
                    command=relative[index:index + 1], old_logp=output["log_probability"][index],
                    old_value=output["value"][index], variable=(stacked[4][index] < 0).double()))
                failed_zone = fixtures[index].failed_zone - 1
                zones = trace["zone_rows"]
                public_context[index].append(dict(time=20 * epoch,
                    failed_zone_delivery_observed=2 * zones[failed_zone * 15 + 11],
                    failed_executor_state=trace["token_state"][failed_zone * 2]))
            rows = batch.step(commands)
            for index, row in enumerate(rows):
                if tuple(row["applied_decision"]["command"]) != commands[index]:
                    raise AssertionError("presented command did not reach its physical native entity/token")
                checks["physical_commands"] += 1
                checks["null_choices"] += int((relative[index] == 7).sum())
                checks["fixed_choices"] += int((stacked[4][index] >= 0).sum())
                checks["zone2_commands"] += int(fixtures[index].failed_zone == 2)
        metrics = [dict(terminal_metrics(row), zone=fixture.failed_zone, world=index,
                        recovery_observations_20s=public_context[index])
                   for index, (row, fixture) in enumerate(zip(rows, fixtures))]
    residual = None
    if arm == "DIRECT":
        squared, elements, maximum = model.residual_observation
        residual = dict(logit_rms=math.sqrt(squared / elements), logit_max_abs=maximum, observed_elements=elements)
        model.residual_observation = None
    return dict(records=[item for episode in episodes for item in episode], episodes=metrics,
                checks=checks, residual=residual, seconds=perf_counter() - started,
                model_forward_calls=6 + checks["presentation_checks"],
                model_forward_decisions=count * (6 + checks["presentation_checks"]))


def update(model, optimizer, rollout_data, seed, namespace, arm, round_index):
    started = perf_counter()
    records = rollout_data["records"]
    values = torch.stack([row["old_value"] for row in records]).reshape(-1, 6)
    objectives = torch.tensor([row["J_ext"] for row in rollout_data["episodes"]], dtype=torch.float64)
    advantages, returns = gae_terminal(values, objectives)
    advantages, returns = normalize_advantages(advantages).reshape(-1), returns.reshape(-1)
    old_logp = torch.stack([row["old_logp"] for row in records])
    all_inputs = tuple(torch.cat([row["inputs"][column] for row in records]) for column in range(6))
    commands = torch.cat([row["command"] for row in records])
    variable = torch.stack([row["variable"] for row in records])
    source = rng(seed, namespace, f"minibatches/{arm}")
    losses, gradients, residual_gradients = [], [], []
    for epoch in range(4):
        base = dict(replicate_role="BPCR-REP-00", domain="training/minibatch-permutation",
                    purpose=f"{namespace}/{arm}", roster_size=7, failed_zone=1,
                    update_or_panel_row=round_index, episode_row=epoch, physical_time=0)
        permutation = _shuffle(tuple(range(len(records))), source, base, None)
        for start in range(0, len(records), 24):
            ix = torch.tensor(permutation[start:start + 24], dtype=torch.int64)
            output = model(*(value[ix] for value in all_inputs), None, commands[ix])
            if not torch.equal(output["command"], commands[ix]):
                raise AssertionError("PPO forced command changed presented survivor coordinates")
            if epoch == 0 and start == 0 and not torch.allclose(output["log_probability"].detach(), old_logp[ix], atol=1e-8, rtol=1e-8):
                raise AssertionError("first PPO replay does not match collected action likelihood")
            loss = ppo_loss(output["log_probability"], old_logp[ix], advantages[ix], output["value"],
                            returns[ix], output["token_entropies"], variable[ix])
            optimizer.zero_grad(set_to_none=True)
            loss["total"].backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), .5)
            if not torch.isfinite(norm) or not torch.isfinite(loss["total"]):
                raise AssertionError("nonfinite real PPO loss or gradient")
            residual_gradients.append(math.sqrt(sum(float(p.grad.square().sum()) for name, p in
                model.named_parameters() if "residual" in name and p.grad is not None)))
            optimizer.step()
            gradients.append(float(norm))
            losses.append({name: float(value.detach()) for name, value in loss.items()})
    return dict(seconds=perf_counter() - started, optimizer_steps=len(losses), backward_calls=len(losses),
                optimizer_forward_calls=len(losses), optimizer_forward_decisions=len(losses) * 24,
                mean_losses={name: sum(row[name] for row in losses) / len(losses) for name in losses[0]},
                mean_preclip_gradient_norm=sum(gradients) / len(gradients),
                mean_postclip_residual_gradient_norm=sum(residual_gradients) / len(residual_gradients))

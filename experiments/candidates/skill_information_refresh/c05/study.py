"""One prospective policy-gradient fit against the exact same-information value rule."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import resource
import time

import numpy as np
import torch
from torch import nn
from torch.distributions import Bernoulli

from .host import FixedHost, HORIZON, RESTRICTED, RULES, Worlds, rule


@dataclass(frozen=True)
class Config:
    seed: int = 73160
    train_cycles: int = 16384
    batch: int = 128
    epochs: int = 4
    final_cycles: int = 4096

    def __post_init__(self):
        if (self.seed < 0 or min(self.train_cycles, self.batch, self.epochs, self.final_cycles) < 1
                or self.train_cycles % self.batch):
            raise ValueError("invalid fixed-horizon training configuration")


class Scheduler(nn.Module):
    def __init__(self):
        super().__init__()
        self.actor = nn.Sequential(nn.Linear(3, 16), nn.Tanh(), nn.Linear(16, 1))
        self.value = nn.Sequential(nn.Linear(3, 16), nn.Tanh(), nn.Linear(16, 1))

    def forward(self, features):
        return self.actor(features).squeeze(-1), self.value(features).squeeze(-1)


def parameters(model):
    return torch.cat([p.detach().flatten().clone() for p in model.parameters()])


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def choose(name, view, model):
    if name == "LEARNED":
        with torch.no_grad():
            logits, _ = model(torch.from_numpy(view.features()))
        probability = torch.sigmoid(logits).numpy()
        return probability >= .5, probability
    early = rule(name, view)
    return early, early.astype(np.float32)


def reading(trace):
    return dict(cycles=len(trace["utility"]), native_utility=float(trace["utility"].mean()),
        first_correct=float(trace["correct"][:, 0].mean()),
        second_correct=float(trace["correct"][:, 1].mean()),
        early_fraction=float(trace["early"].mean()), packets=int(trace["packets"].sum()),
        bytes=int(trace["bytes"].sum()))


def run_study(out, launch_sha, config=Config()):
    out = Path(out)
    if (out / "summary.json").exists() or (out / "updates.jsonl").exists():
        raise FileExistsError("C05 never overwrites or resumes scientific output")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.manual_seed(config.seed)
    model = Scheduler()
    original = parameters(model)
    optimizer = torch.optim.Adam(model.parameters(), lr=.003)
    counts = dict(started_fits=0, train_cycles=0, train_transitions=0, optimizer_steps=0,
        eval_cycles=0, eval_transitions=0, evaluation_optimizer_steps=0)
    summary = dict(object="SIR-C05", direction="skill_information_refresh", status="RUNNING",
        launch_sha=launch_sha, config=asdict(config), counts=counts, limits=[],
        device="cpu", dtype="float32", native_threads=1, arms=["LEARNED", *RULES],
        primary_reference="VOI", selection="none; all four restricted mappings reported",
        information="current sender X/q plus the paid receiver context already delivered at t=1",
        channel=dict(packets_per_cycle=2, bytes_per_cycle=11, context_bytes=7, data_bytes=4,
            delay=1, sender_slots=[1, 3], receiver_slot=0, binary_timing_choices=1),
        claim_scope="fixed scripted commitments; exact opportunity is not learned package value",
        phases_seconds={})
    started = time.monotonic()
    write_json(out / "config.json", asdict(config))
    write_json(out / "summary.json", summary)
    traces = {}
    with (out / "episodes.jsonl").open("x") as episodes, (out / "updates.jsonl").open("x") as updates:
        def evaluate(phase, name, worlds):
            host = FixedHost(worlds)
            view = host.prepare()
            early, probability = choose(name, view, model)
            _, trace = host.rollout(early)
            trace["early_probability"] = probability
            trace["delta_tenths"] = view.delta_tenths()
            if not ((trace["packets"] == 2).all() and (trace["bytes"] == 11).all()):
                raise RuntimeError("fixed communication cost changed")
            for i in range(len(worlds.ids)):
                episodes.write(json.dumps(dict(phase=phase, arm=name, world_id=int(worlds.ids[i]),
                    utility=int(trace["utility"][i]), early=bool(early[i]),
                    first_correct=bool(trace["correct"][i, 0]),
                    second_correct=bool(trace["correct"][i, 1]), packets=2, bytes=11)) + "\n")
            episodes.flush()
            np.savez_compressed(out / f"{phase}_{name}.npz", **trace)
            traces[phase, name] = trace
            counts["eval_cycles"] += len(worlds.ids)
            counts["eval_transitions"] += len(worlds.ids) * HORIZON
            return reading(trace)

        try:
            summary["initial_exact"] = evaluate("initial_exact", "LEARNED", Worlds.exact())
            counts["started_fits"] = 1
            train_start = time.monotonic()
            worlds = Worlds.make(config.seed, 0, config.train_cycles)
            training_traces = []
            for start in range(0, config.train_cycles, config.batch):
                host = FixedHost(worlds.take(start, start + config.batch))
                view = host.prepare()
                features = torch.from_numpy(view.features())
                with torch.no_grad():
                    old_logits, old_values = model(features)
                    old_distribution = Bernoulli(logits=old_logits)
                    actions = old_distribution.sample()
                    old_logp = old_distribution.log_prob(actions)
                reward, train_trace = host.rollout(actions.numpy().astype(bool))
                train_trace["early_probability"] = old_distribution.probs.numpy()
                train_trace["delta_tenths"] = view.delta_tenths()
                training_traces.append(train_trace)
                target = torch.tensor(reward / 7., dtype=torch.float32)
                advantage = target - old_values
                # One terminal decision: no GAE, hidden future observation or analytic target.
                for epoch in range(config.epochs):
                    logits, values = model(features)
                    distribution = Bernoulli(logits=logits)
                    ratio = (distribution.log_prob(actions) - old_logp).exp()
                    surrogate = torch.minimum(ratio * advantage,
                        ratio.clamp(.8, 1.2) * advantage)
                    policy_loss = -surrogate.mean()
                    value_loss = .5 * (values - target).square().mean()
                    entropy = distribution.entropy().mean()
                    loss = policy_loss + .5 * value_loss - .01 * entropy
                    optimizer.zero_grad()
                    loss.backward()
                    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), .5)
                    if not torch.isfinite(loss) or not torch.isfinite(grad_norm):
                        raise RuntimeError("nonfinite learning update")
                    optimizer.step()
                    counts["optimizer_steps"] += 1
                    updates.write(json.dumps(dict(step=counts["optimizer_steps"],
                        cycle_stop=start + config.batch, epoch=epoch, loss=float(loss.detach()),
                        policy_loss=float(policy_loss.detach()), value_loss=float(value_loss.detach()),
                        entropy=float(entropy.detach()), gradient_norm=float(grad_norm),
                        batch_native_utility=float(reward.mean())), allow_nan=False) + "\n")
                updates.flush()
                counts["train_cycles"] += config.batch
                counts["train_transitions"] += config.batch * HORIZON
            np.savez_compressed(out / "training_LEARNED.npz", **{
                key: np.concatenate([trace[key] for trace in training_traces])
                for key in training_traces[0]})
            summary["phases_seconds"]["training"] = time.monotonic() - train_start
            frozen = parameters(model)
            torch.save(dict(model=model.state_dict(), config=asdict(config), launch_sha=launch_sha),
                out / "final.pt")
            eval_start = time.monotonic()
            model.eval()
            panels = {"final": Worlds.make(config.seed, 2, config.final_cycles),
                "final_exact": Worlds.exact(), "zero_risk_exact": Worlds.exact(zero_risk=True)}
            for phase, panel in panels.items():
                summary[phase] = {name: evaluate(phase, name, panel) for name in summary["arms"]}
            summary["phases_seconds"]["evaluation"] = time.monotonic() - eval_start
            comparisons = {}
            for phase in panels:
                learned = traces[phase, "LEARNED"]["utility"]
                voi = traces[phase, "VOI"]["utility"]
                restricted_best = max(summary[phase][name]["native_utility"] for name in RESTRICTED)
                comparisons[phase] = dict(learned_minus_voi=float((learned - voi).mean()),
                    learned_minus_voi_total=int((learned - voi).sum()),
                    best_restricted_value=restricted_best,
                    voi_minus_best_restricted=summary[phase]["VOI"]["native_utility"] - restricted_best,
                    learned_minus_best_restricted=float(learned.mean()) - restricted_best,
                    learned_positive_worlds=int((learned > voi).sum()),
                    learned_negative_worlds=int((learned < voi).sum()),
                    learned_tied_worlds=int((learned == voi).sum()))
            summary["comparisons"] = comparisons
            contexts = []
            exact = traces["final_exact", "LEARNED"]
            for i in range(0, len(exact["world_ids"]), 10):
                contexts.append(dict(condition=int(exact["initial_condition"][i]),
                    received_weight=int(exact["weight"][i]), risk_tenths=int(exact["risk_tenths"][i]),
                    delta=float(exact["delta_tenths"][i]) / 10,
                    learned_early=bool(exact["early"][i]),
                    learned_probability=float(exact["early_probability"][i]),
                    voi_early=bool(exact["delta_tenths"][i] > 0)))
            summary["contexts"] = contexts
            summary["strict_context_errors"] = sum(r["learned_early"] != r["voi_early"]
                for r in contexts if r["delta"] != 0)
            if not torch.equal(parameters(model), frozen):
                raise RuntimeError("evaluation changed model parameters")
            if not all(torch.isfinite(p).all() for p in model.parameters()):
                raise RuntimeError("nonfinite final model")
            summary["parameters"] = dict(count=len(original),
                displacement=float((frozen - original).norm()), evaluation_displacement=0., finite=True)
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["status"] = "TECHNICAL_FAILURE"
            summary["limits"].append(f"{type(error).__name__}: {error}")
            raise
        finally:
            summary["wall_seconds"] = time.monotonic() - started
            usage = resource.getrusage(resource.RUSAGE_SELF)
            summary["resources"] = dict(peak_rss_kib=usage.ru_maxrss,
                rss_scope="one Linux scientific child, not aggregate node occupancy",
                user_cpu_seconds=usage.ru_utime, system_cpu_seconds=usage.ru_stime)
            write_json(out / "summary.json", summary)
    if json.loads((out / "summary.json").read_text())["counts"] != counts:
        raise RuntimeError("summary readback failed")
    return summary

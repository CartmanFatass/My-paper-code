"""B04 reward learning on the unchanged B3 host; no result-selection policy.

Models run in batches. Each row still executes the real host's three transitions.
RNG namespaces are independent of arm and evaluation update for paired routing.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch

from experiments.candidates.folr_core.partner_writer_stale_load_routing import (
    MatchedRoutedActor, OrdinaryPartnerWriter,
)
from experiments.candidates.folr_core.partner_writer_stale_load_routing_host import (
    COMPLETE_RESET, ISOMORPHIC_GENERIC_UPDATE, TYPED_OWNER_EPOCH_ROUTING,
    HostDimensions, PartnerWriteDTO, PartnerWriterStaleLoadHost,
)

ARMS = ("TYPED", "GENERIC", "RESET")
REGIMES = ("CLEAN", "STALE_LOAD")
MASKS = dict(zip(ARMS, (TYPED_OWNER_EPOCH_ROUTING, ISOMORPHIC_GENERIC_UPDATE, COMPLETE_RESET)))


def derive_seed(seed, namespace):
    data = f"N3-FOLR-B04\0{seed}\0{namespace}".encode()
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "little") % (2**31 - 1)


def episode_rows(seed, phase, count, *, update=None, regime=None):
    """Balanced legal cues, shuffled afresh; independent data and action tapes.

    Writer counts are multiples of two, routing training of sixteen, and routing
    evaluation of eight. The runner owns the full/toy sizes satisfying this law.
    CLEAN uses n_old=0, whose encoded state the host and learner both zero.
    """
    suffix = "evaluation" if update is None else f"train/{update}"
    namespace = f"{phase}/{suffix}/{regime or 'mixed'}"
    if phase == "writer":
        support = [("CALIBRATION", 0, 0, bit) for bit in (0, 1)]
    else:
        clean = [("CLEAN", s, 0, new) for s, new in product((0, 1), repeat=2)]
        stale = [("STALE_LOAD", s, old, new) for s, old, new in product((0, 1), repeat=3)]
        support = clean if regime == "CLEAN" else stale if regime == "STALE_LOAD" else clean * 2 + stale
    tuples = support * (count // len(support))
    data_rng = np.random.default_rng(derive_seed(seed, namespace + "/data"))
    data_rng.shuffle(tuples)
    roots = data_rng.integers(0, 2**31 - 1, size=count)
    uniforms = np.random.default_rng(derive_seed(seed, namespace + "/actions")).random(count)
    return [dict(regime=r, s=s, n_old=old, n_new=new, root=int(root),
                 action_uniform=float(u), episode=i)
            for i, ((r, s, old, new), root, u) in enumerate(zip(tuples, roots, uniforms))]


def bits(rows, name):
    return torch.tensor([[2.0 * row[name] - 1.0] for row in rows], dtype=torch.float32)


def sample_actions(probabilities, rows):
    uniforms = torch.tensor([r["action_uniform"] for r in rows], dtype=torch.float32)
    return (uniforms[:, None] > probabilities.cumsum(-1)).sum(-1).clamp_max(probabilities.shape[-1] - 1)


def start_hosts(rows, owner, obsolete, payloads):
    hosts, delivered_owner, delivered_partner = [], [], []
    for row, own, old, payload in zip(rows, owner, obsolete, payloads):
        host = PartnerWriterStaleLoadHost(root=row["root"], regime=row["regime"], dimensions=HostDimensions())
        host.transition_one(owner_state=own, obsolete_partner_state=old)
        host.apply_replacement(host.replacement_transaction())
        host.transition_two(PartnerWriteDTO.make(
            writer_call_identity=f"B04/{row['root']}/{row['episode']}",
            source_bit=row["n_new"], payload=payload))
        host_owner, _, host_partner = host.routed_inputs()
        hosts.append(host)
        delivered_owner.append(host_owner)
        delivered_partner.append(host_partner)
    return hosts, torch.stack(delivered_owner), torch.stack(delivered_partner)


def reward_from_hosts(hosts, rows, actions, *, writer=False):
    return torch.tensor([
        host.terminal_transition(action=int(action),
                                 target=row["n_new"] if writer else 2 * row["s"] + row["n_new"],
                                 action_count=2 if writer else 4)["reward"]
        for host, row, action in zip(hosts, rows, actions.tolist())
    ], dtype=torch.float32)


def writer_episode_batch(model, rows):
    payloads = model.write(bits(rows, "n_new"))
    zero = torch.zeros(len(rows), 2, dtype=torch.float32)
    hosts, _, delivered = start_hosts(rows, zero, zero, payloads)
    # The host record is detached. Retain the existing writer's differentiable
    # candidate during training; evaluation reads exactly the delivered payload.
    logits = model.readout(payloads if torch.is_grad_enabled() else delivered)
    probabilities = logits.softmax(-1)
    actions = sample_actions(probabilities, rows)
    rewards = reward_from_hosts(hosts, rows, actions, writer=True)
    return logits, probabilities, actions, rewards, None


def routing_episode_batch(actor, arm, rows, *, flip=False, timing=None):
    owner, obsolete = actor.pre_event(bits(rows, "s"), bits(rows, "n_old"))
    clean = torch.tensor([row["regime"] == "CLEAN" for row in rows])[:, None]
    obsolete = obsolete.masked_fill(clean, 0.0)
    with torch.no_grad():
        payloads = actor.partner_write(bits(rows, "n_new"))
    hosts, delivered_owner, delivered_partner = start_hosts(rows, owner, obsolete, payloads)
    # Host records detach on purpose; preserve B3's actor-owned gradient path.
    owner_input = owner if torch.is_grad_enabled() else delivered_owner
    logits = actor.action_head(actor.routed_state(
        arm=MASKS[arm], owner_state=owner_input, obsolete_state=obsolete,
        partner_state=delivered_partner.detach()))
    probabilities = logits.softmax(-1)
    actions = sample_actions(probabilities, rows)
    rewards = reward_from_hosts(hosts, rows, actions)
    tv = None
    if flip:
        start = perf_counter()
        _, flipped = actor.pre_event(bits(rows, "s"), -bits(rows, "n_old"))
        flipped = flipped.masked_fill(clean, 0.0)
        other = actor.action_head(actor.routed_state(
            arm=MASKS[arm], owner_state=owner_input, obsolete_state=flipped,
            partner_state=delivered_partner)).softmax(-1)
        tv = (probabilities - other).abs().sum(-1) * 0.5
        if timing is not None:
            timing["diagnostic"] += perf_counter() - start
    return logits, probabilities, actions, rewards, tv


def latch_episode_batch(writer, rows):
    # Only this initial write reads s. Terminal control recovers surviving state.
    stored = torch.tensor([[1.0 - row["s"], float(row["s"])] for row in rows])
    payloads = writer.write(bits(rows, "n_new"))
    hosts, owner_state, delivered = start_hosts(rows, stored, torch.zeros_like(stored), payloads)
    binary = writer.readout(delivered).softmax(-1)
    retained_bit = owner_state.argmax(-1)
    # Four-action kernel carries the binary readout on the retained owner's half.
    probabilities = torch.zeros(len(rows), 4, dtype=torch.float32)
    probabilities.scatter_(1, 2 * retained_bit[:, None] + torch.arange(2)[None, :], binary)
    actions = 2 * retained_bit + sample_actions(binary, rows)
    rewards = reward_from_hosts(hosts, rows, actions)
    return None, probabilities, actions, rewards, None


def reinforce(logits, actions, rewards, optimizer):
    # Only the host's external reward supplies the learning signal.
    loss = -(rewards * logits.log_softmax(-1).gather(1, actions[:, None]).squeeze(1)).mean()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
    return float(loss.detach())


def metrics(rows, probabilities, actions, rewards, *, writer=False, tv=None):
    target = torch.tensor([r["n_new"] if writer else 2 * r["s"] + r["n_new"] for r in rows])
    result = {"episodes": len(rows), "return": float(rewards.mean()),
              "expected_reward_probability": float(probabilities.gather(1, target[:, None]).mean()),
              "owner_accuracy": None if writer else float((actions // 2 == target // 2).float().mean()),
              "new_bit_accuracy": float((actions % 2 == target % 2).float().mean())}
    if tv is not None:
        result["n_old_flip_tv"] = float(tv.mean())
    return result


def final_rows(rows, probabilities, actions, rewards, tv):
    return [{**row, "probabilities": p, "action": int(a), "host_reward": float(r),
             **({"n_old_flip_tv": float(t)} if t is not None else {})}
            for row, p, a, r, t in zip(rows, probabilities.tolist(), actions.tolist(), rewards.tolist(),
                                       [None] * len(rows) if tv is None else tv.tolist())]


def parameter_vector(model):
    return torch.cat([p.detach().flatten().to(torch.float64) for p in model.parameters() if p.requires_grad])


def parameter_metrics(model, initial, updates):
    final = parameter_vector(model)
    norm = float(initial.norm())
    displacement = float((final - initial).norm())
    return {"initial_norm": norm, "final_norm": float(final.norm()),
            "displacement_norm": displacement, "relative_displacement": displacement / norm,
            "updates": updates}


def new_phase():
    return {"training_curve": [], "evaluation_curve": [], "final": {}, "auc": {},
            "counts": {"train_episodes": 0, "eval_episodes": 0, "updates": 0,
                       "primitive_transitions": 0,
                       "policy_calls": {"train": {}, "evaluation": {}, "diagnostic": {}},
                       "terminal_decisions": {"train": 0, "evaluation": 0}},
            "wall_seconds": {"train": 0.0, "evaluation": 0.0, "diagnostic": 0.0}}


def count_batch(phase, mode, size, *, writer=False, latch=False, flip=False):
    counts = phase["counts"]
    counts["train_episodes" if mode == "train" else "eval_episodes"] += size
    counts["primitive_transitions"] += 3 * size
    counts["terminal_decisions"][mode] += size
    # These are actual batched forward calls, not episode-equivalent forwards.
    roles = ("new_partner_writer", "writer_readout") if writer or latch else (
        "owner_encoder", "obsolete_partner_encoder", "new_partner_writer", "event_updater", "owner_action_head")
    for role in roles:
        calls = counts["policy_calls"][mode]
        calls[role] = calls.get(role, 0) + 1
    if flip:
        for role in ("owner_encoder", "obsolete_partner_encoder", "event_updater", "owner_action_head"):
            calls = counts["policy_calls"]["diagnostic"]
            calls[role] = calls.get(role, 0) + 1
        counts["counterfactual_kernel_rows"] = counts.get("counterfactual_kernel_rows", 0) + size


def finish_phase(phase, model, optimizer, initial, updates, directory, rows):
    phase["parameters"] = parameter_metrics(model, initial, updates)
    phase["checkpoint"] = str(directory / "final.pt")
    torch.save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(),
                "updates": updates}, phase["checkpoint"])
    write_rows(phase, directory, rows)
    for regime in phase["final"]:
        curve = [point for point in phase["evaluation_curve"] if point["regime"] == regime]
        phase["auc"][regime] = sum(
            (right["update"] - left["update"]) * (left["return"] + right["return"]) * 0.5
            for left, right in zip(curve, curve[1:])) / updates


def write_rows(phase, directory, rows):
    phase["final_rows"] = str(directory / "final_evaluation.jsonl")
    with Path(phase["final_rows"]).open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")


def run_seed(seed, *, updates=128, batch_size=64, eval_episodes=256, eval_every=16, output_root):
    """Return plain seed metrics; save final checkpoints and inspectable rows only."""
    directory = Path(output_root) / f"seed_{seed}"
    points = set(range(0, updates + 1, eval_every)) | {updates}
    writer_phase = new_phase()
    with torch.random.fork_rng(devices=[]):
        writer = OrdinaryPartnerWriter(initialization_seed=derive_seed(seed, "writer/initialization"))
    optimizer = torch.optim.Adam(writer.parameters(), lr=0.025, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
    initial = parameter_vector(writer)
    writer_eval = episode_rows(seed, "writer", eval_episodes)
    writer_directory = directory / "writer"
    writer_directory.mkdir(parents=True, exist_ok=True)
    for update in range(updates + 1):
        if update:
            start = perf_counter()
            rows = episode_rows(seed, "writer", batch_size, update=update)
            logits, probabilities, actions, rewards, _ = writer_episode_batch(writer, rows)
            loss = reinforce(logits, actions, rewards, optimizer)
            writer_phase["wall_seconds"]["train"] += perf_counter() - start
            writer_phase["training_curve"].append({"update": update, "reward": float(rewards.mean()), "loss": loss})
            count_batch(writer_phase, "train", len(rows), writer=True)
            writer_phase["counts"]["updates"] += 1
        if update in points:
            start = perf_counter()
            with torch.no_grad():
                _, probabilities, actions, rewards, _ = writer_episode_batch(writer, writer_eval)
                metric = metrics(writer_eval, probabilities, actions, rewards, writer=True)
            writer_phase["wall_seconds"]["evaluation"] += perf_counter() - start
            writer_phase["evaluation_curve"].append({"update": update, "regime": "CALIBRATION", **metric})
            count_batch(writer_phase, "evaluation", len(writer_eval), writer=True)
    writer_phase["final"]["CALIBRATION"] = metric
    finish_phase(writer_phase, writer, optimizer, initial, updates, writer_directory,
                 final_rows(writer_eval, probabilities, actions, rewards, None))
    frozen_writer = deepcopy(writer.state_dict())
    routing_eval = {regime: episode_rows(seed, "routing", eval_episodes, regime=regime) for regime in REGIMES}
    arms = {}
    for arm in ARMS:
        phase = new_phase()
        with torch.random.fork_rng(devices=[]):
            actor = MatchedRoutedActor(frozen_writer_state=frozen_writer,
                                      initialization_seed=derive_seed(seed, "routing/initialization"))
        optimizer = torch.optim.Adam([p for p in actor.parameters() if p.requires_grad],
                                     lr=0.025, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
        initial = parameter_vector(actor)
        arm_directory = directory / arm
        arm_directory.mkdir(parents=True, exist_ok=True)
        saved_rows = []
        for update in range(updates + 1):
            if update:
                start = perf_counter()
                rows = episode_rows(seed, "routing", batch_size, update=update)
                logits, probabilities, actions, rewards, _ = routing_episode_batch(actor, arm, rows)
                loss = reinforce(logits, actions, rewards, optimizer)
                phase["wall_seconds"]["train"] += perf_counter() - start
                phase["training_curve"].append({"update": update, "reward": float(rewards.mean()), "loss": loss})
                count_batch(phase, "train", len(rows))
                phase["counts"]["updates"] += 1
            if update in points:
                for regime, rows in routing_eval.items():
                    start = perf_counter()
                    with torch.no_grad():
                        _, probabilities, actions, rewards, tv = routing_episode_batch(
                            actor, arm, rows, flip=update == updates, timing=phase["wall_seconds"])
                        metric = metrics(rows, probabilities, actions, rewards, tv=tv)
                    phase["wall_seconds"]["evaluation"] += perf_counter() - start
                    phase["evaluation_curve"].append({"update": update, "regime": regime, **metric})
                    count_batch(phase, "evaluation", len(rows), flip=update == updates)
                    if update == updates:
                        phase["final"][regime] = metric
                        saved_rows.extend(final_rows(rows, probabilities, actions, rewards, tv))
        finish_phase(phase, actor, optimizer, initial, updates, arm_directory, saved_rows)
        arms[arm] = phase
    latch = new_phase()
    latch["optimization_cost"] = "Zero extra updates; full shared writer exposure already paid."
    latch_directory = directory / "LATCH"
    latch_directory.mkdir(parents=True, exist_ok=True)
    saved_rows = []
    with torch.no_grad():
        for regime, rows in routing_eval.items():
            start = perf_counter()
            _, probabilities, actions, rewards, _ = latch_episode_batch(writer, rows)
            metric = metrics(rows, probabilities, actions, rewards)
            latch["wall_seconds"]["evaluation"] += perf_counter() - start
            latch["evaluation_curve"].append({"update": updates, "regime": regime, **metric})
            latch["final"][regime] = metric
            count_batch(latch, "evaluation", len(rows), latch=True)
            saved_rows.extend(final_rows(rows, probabilities, actions, rewards, None))
    write_rows(latch, latch_directory, saved_rows)
    return {"seed": seed, "writer": writer_phase, "arms": arms, "latch": latch}

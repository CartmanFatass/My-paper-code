"""One fit and four full native endpoints for the selected quota-phase B08."""
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_runner import (
    EpisodeCoordinate, _address, _compact_coordinate_columns,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import TRAINING_CELLS, HELDOUT_CELLS
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.native_backend import (
    StepInput, bind_native_backend, native_materialize_fixtures_compact,
    native_semantic_uniform_words, reset_native_batch,
)
from .policy import PhasePolicy, adam_update, flat_parameters, greedy_phase, sampled_phase

OBJECT = "RCLE-TBCFV-B08-JOINT-QUOTA-PHASE"
SEED = 28
PRIMARY = ("8_to_12.ACTIVE_CONTINUATION", "12_to_8.ACTIVE_CONTINUATION")
ROLES = ("initialization", "final256", "greedy", "nearest")


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf8")


def uniforms(key, binding, addresses):
    words = native_semantic_uniform_words(key, addresses, binding=binding)
    return [(word + .5) / float(1 << 64) for word in words]


def phase_uniforms(key, binding, coordinates, tick):
    return uniforms(key, binding, [
        _address(0, cell=c.cell, update_or_scenario=c.update_or_scenario,
                 physical_tick=tick, physical_agent=c.episode_row,
                 draw_kind="joint-quota-phase", draw_index=0)
        for c in coordinates])


def rollout(model, role, key, binding, coordinates, training=False, observe=None):
    cells, updates, rows = _compact_coordinate_columns(coordinates)
    fixtures = native_materialize_fixtures_compact(key, 0, cells, updates, rows, binding=binding)
    score_terms = [[] for _ in coordinates]
    agent_ticks = [0] * len(coordinates)
    claim_counts = [0] * len(coordinates)
    with reset_native_batch(fixtures, packed_views=False, binding=binding) as batch:
        for tick in range(64):
            snapshots = batch.snapshots
            if snapshots[0].event_input_required:
                events = batch.materialize_events_compact(key, 0, cells, updates, rows, fixtures)
                snapshots = batch.apply_event(events)
            if snapshots[0].claim_required:
                if role == "nearest":
                    # Eager row columns are materialized from this post-event roster.
                    sizes = [len(s.positions) for s in snapshots]
                    actions = batch.scripted_actions(2, [(-1,) * n for n in sizes],
                        [(False,) * n for n in sizes], [s.tick == 0 or s.new_epoch for s in snapshots],
                        [False] * len(sizes), [(tick - 24) // 4] * len(sizes))
                else:
                    actions = [None] * len(snapshots)
                    phase_u = (phase_uniforms(key, binding, coordinates, tick)
                               if role != "greedy" else None)
                    for n in sorted({len(s.positions) for s in snapshots}):
                        lanes = [i for i, s in enumerate(snapshots) if len(s.positions) == n]
                        public = [snapshots[i].public_observation() for i in lanes]
                        if role == "greedy":
                            choices = greedy_phase(public)
                        else:
                            choices, scores, _ = sampled_phase(model, public, [phase_u[i] for i in lanes])
                            if training:
                                for row, lane in enumerate(lanes):
                                    score_terms[lane].append(scores[row])
                        for row, lane in enumerate(lanes):
                            actions[lane] = StepInput(tuple(int(a) for a in choices[row]))
                if observe is not None:
                    observe(tick, snapshots, actions)
                for lane, action in enumerate(actions):
                    claim_counts[lane] += len(action.claims)
            else:
                actions = [StepInput.no_claims() for _ in snapshots]
            for lane, snapshot in enumerate(snapshots):
                agent_ticks[lane] += len(snapshot.positions)
            batch.step(actions)
        results = []
        for i, snapshot in enumerate(batch.snapshots):
            results.append(dict(U=float(snapshot.U), F=float(snapshot.F), tau=int(snapshot.tau),
                                Y=float(snapshot.Y), unmet_ticks=40 * float(snapshot.U),
                                agent_ticks=agent_ticks[i], agent_claims=claim_counts[i]))
    scores = torch.stack([torch.stack(s).sum() for s in score_terms]) if training else None
    return results, scores


def cell_means(rows):
    return {cell: dict(episodes=len(part), **{
        name: float(np.mean([r[name] for r in part])) for name in ("U", "F", "tau", "Y", "unmet_ticks")},
        tau40=sum(r["tau"] == 40 for r in part))
        for cell in HELDOUT_CELLS if (part := [r for r in rows if r["cell"] == cell])}


def contrasts(panels):
    result = {}
    for name, comparator in (("D_g", "greedy"), ("D_n", "nearest"), ("G_U", "initialization")):
        paths = {}
        for cell in PRIMARY:
            base = {(r["cell"], r["scenario"]): r for r in panels[comparator]}
            final = {(r["cell"], r["scenario"]): r for r in panels["final256"]}
            differences = np.asarray([base[(cell, i)]["U"] - final[(cell, i)]["U"] for i in range(64)])
            paths[cell] = dict(mean=float(differences.mean()), sd=float(differences.std(ddof=1)),
                              conditional_se=float(differences.std(ddof=1) / 8),
                              positive=int((differences > 0).sum()), adverse=int((differences < 0).sum()),
                              ties=int((differences == 0).sum()), differences=differences.tolist())
        mean = float(np.mean([p["mean"] for p in paths.values()]))
        se = math.sqrt(sum(p["conditional_se"] ** 2 for p in paths.values())) / 2
        result[name] = dict(mean=mean, conditional_se=se, conditional_normal95=[mean - 1.96 * se, mean + 1.96 * se],
                            paths=paths)
    return result


def reading(dg, dn, gu):
    flags = []
    if dg >= .025 and dn >= .025 and gu > 0:
        flags.append("useful_one_fit_signal")
    if dg > 0 and dn > 0 and (dg < .025 or dn < .025):
        flags.append("small_positive_benefits")
    if dn > 0 and dg <= 0:
        flags.append("no_increment_over_greedy")
    if dg > 0 and dn <= 0:
        flags.append("local_increment_nearest_deficit")
    if dg <= 0 and dn <= 0:
        flags.append("no_endpoint_advantage")
    if gu <= 0:
        flags.append("no_positive_own_initialization_learning")
    return flags


def evaluate(model, role, key, binding, out):
    rows = []
    for cell in HELDOUT_CELLS:
        for start in (0, 32):
            coords = tuple(EpisodeCoordinate(0, cell, 0, i) for i in range(start, start + 32))
            with torch.no_grad():
                results, _ = rollout(model, role, key, binding, coords)
            rows.extend(dict(cell=cell, scenario=c.episode_row, **r) for c, r in zip(coords, results))
            write_json(out / (role + ".json"), rows)
    return rows


def run(out, launch_sha, seed=SEED):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    key = hashlib.sha256(f"{OBJECT}/seed/{seed}".encode("ascii")).digest()
    binding = bind_native_backend(build_root=out / "native_build")
    model = PhasePolicy()
    def parameter_uniforms(name, count):
        return uniforms(key, binding, [_address(0, parameter_entry=name,
            draw_kind="common-initial-parameter", draw_index=i) for i in range(count)])
    model.initialize(parameter_uniforms)
    initial = flat_parameters(model).clone()
    torch.save(model.state_dict(), out / "initialization.pt")
    panels = {"initialization": evaluate(model, "initialization", key, binding, out)}
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4, betas=(.9, .999), eps=1e-8,
                                 weight_decay=0, foreach=False)
    baselines = torch.zeros(8, dtype=torch.float64)
    curves = []
    for update in range(1, 257):
        episodes, batch_scores = [], []
        for cell_start in (0, 4):
            coords = tuple(EpisodeCoordinate(0, cell, update, row)
                           for cell in TRAINING_CELLS[cell_start:cell_start + 4] for row in range(8))
            results, scores = rollout(model, "learned", key, binding, coords, training=True)
            episodes.extend(results)
            batch_scores.append(scores)
        returns = torch.tensor([r["Y"] for r in episodes], dtype=torch.float64)
        indices = torch.arange(8).repeat_interleave(8)
        baselines, step = adam_update(model, optimizer, returns, torch.cat(batch_scores), indices, baselines)
        curve = dict(update=update, **step, training_episodes=64, native_ticks=4096,
            agent_ticks=sum(r["agent_ticks"] for r in episodes),
            agent_claims=sum(r["agent_claims"] for r in episodes),
            per_cell={c: {k: float(np.mean([r[k] for r in episodes[i*8:(i+1)*8]]))
                         for k in ("Y", "U", "F", "tau")} for i, c in enumerate(TRAINING_CELLS)})
        curves.append(curve)
        with (out / "curves.jsonl").open("a", encoding="utf8") as f:
            f.write(json.dumps(curve, allow_nan=False) + "\n")
        if update % 32 == 0:
            print(f"update {update}/256", flush=True)
    torch.save(dict(model=model.state_dict(), optimizer=optimizer.state_dict(), baselines=baselines,
                    updates=256, seed=seed, object_id=OBJECT, launch_sha=launch_sha), out / "final256.pt")
    for role in ROLES[1:]:
        panels[role] = evaluate(model, role, key, binding, out)
    comparison = contrasts(panels)
    summary = dict(status="COMPLETE", object_id=OBJECT, seed=seed, launch_sha=launch_sha,
        parameters=sum(p.numel() for p in model.parameters()), independent_fits=1,
        training_episodes=sum(c["training_episodes"] for c in curves), training_updates=len(curves),
        backward_calls=sum(c["backward_calls"] for c in curves),
        optimizer_calls=sum(c["optimizer_calls"] for c in curves),
        evaluation_episodes={r: len(panels[r]) for r in ROLES},
        native_ticks=64 * (sum(c["training_episodes"] for c in curves) + sum(map(len, panels.values()))),
        initial_norm=float(torch.linalg.vector_norm(initial)),
        displacement=float(torch.linalg.vector_norm(flat_parameters(model) - initial)),
        nonzero_parameter_updates=sum(c["parameter_step_norm"] > 0 for c in curves),
        phase_draws_training=16 * sum(c["training_episodes"] for c in curves),
        phase_draws_evaluation=16 * (len(panels["initialization"]) + len(panels["final256"])),
        endpoint_means={role: cell_means(rows) for role, rows in panels.items()}, comparison=comparison,
        reading_flags=reading(*(comparison[n]["mean"] for n in ("D_g", "D_n", "G_U"))),
        native_Y_source="direct native terminal endpoint for all roles; never inferred from post-event U",
        uncertainty="paired scenario uncertainty conditional on one fit; contrasts share final panel",
        native_source_sha256=binding.source_sha256, study_body_wall_s=time.monotonic() - started)
    write_json(out / "summary.json", summary)
    # The required publication path is exercised inside this invocation.
    published = json.loads((out / "summary.json").read_text(encoding="utf8"))
    return published

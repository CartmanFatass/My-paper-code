"""Fixed fits and their native endpoints for quota-phase B08 through B13."""
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
    StepInput, bind_native_backend, materialize_fixtures_compact as native_materialize_fixtures_compact,
    semantic_uniform_words as native_semantic_uniform_words, reset_native_batch,
)
from .policy import PhasePolicy, adam_update, flat_parameters, greedy_phase, modal_phase, sampled_phase

OBJECT = "RCLE-TBCFV-B08-JOINT-QUOTA-PHASE"
SEED = 28
B09_OBJECT = "RCLE-TBCFV-B09-GREEDY-ANCHORED-PHASE"
B10_OBJECT = "RCLE-TBCFV-B10-GREEDY-ANCHORED-1024"
B11_OBJECT = "RCLE-TBCFV-B11-GREEDY-ANCHORED-1024-REPLICATION"
B12_OBJECT = "RCLE-TBCFV-B12-GREEDY-ANCHORED-1024-INDEPENDENT"
B13_OBJECT = "RCLE-TBCFV-B13-LEARNED-PRIOR-STRENGTH-1024"
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
    if role == "modal" and training:
        raise ValueError("fixed-modal evaluation has no training likelihood or update")
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
                               if role not in ("greedy", "modal") else None)
                    for n in sorted({len(s.positions) for s in snapshots}):
                        lanes = [i for i, s in enumerate(snapshots) if len(s.positions) == n]
                        public = [snapshots[i].public_observation() for i in lanes]
                        if role == "greedy":
                            choices = greedy_phase(public)
                        elif role == "modal":
                            choices, _ = modal_phase(model, public)
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


def contrasts(panels, final_role="final256"):
    result = {}
    for name, comparator in (("D_g", "greedy"), ("D_n", "nearest"), ("G_U", "initialization")):
        paths = {}
        for cell in PRIMARY:
            base = {(r["cell"], r["scenario"]): r for r in panels[comparator]}
            final = {(r["cell"], r["scenario"]): r for r in panels[final_role]}
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


def run(out, launch_sha, seed=SEED, *, greedy_anchored=False):
    object_id = B09_OBJECT if greedy_anchored else OBJECT
    if seed != (29 if greedy_anchored else SEED):
        raise ValueError("seed must match the selected fixed B08/B09 object")
    return _run(out, launch_sha, seed, object_id, 256, greedy_anchored)


def run_exposure1024(out, launch_sha, seed=30):
    if seed != 30:
        raise ValueError("seed must match the selected fixed B10 object")
    return _run(out, launch_sha, seed, B10_OBJECT, 1024, True)


def run_replication1024(out, launch_sha, seed=31):
    if seed != 31:
        raise ValueError("seed must match the selected fixed B11 object")
    return _run(out, launch_sha, seed, B11_OBJECT, 1024, True)


def run_b12_exposure1024(out, launch_sha, seed=32):
    if seed != 32:
        raise ValueError("seed must match the selected fixed B12 object")
    return _run(out, launch_sha, seed, B12_OBJECT, 1024, True)


def run_b13_learned_prior1024(out, launch_sha, seed=33):
    if seed != 33:
        raise ValueError("seed must match the selected fixed B13 object")
    return _run(out, launch_sha, seed, B13_OBJECT, 1024, True, learned_prior_strength=True)


def _run(out, launch_sha, seed, object_id, updates, greedy_anchored, *, learned_prior_strength=False):
    final_role = f"final{updates}"
    roles = ("initialization", final_role, "greedy", "nearest")
    action_law = "softmax(log(q)+z); q=.9*exact_greedy+.1/N" if greedy_anchored else "softmax(z)"
    if learned_prior_strength:
        roles += ("modal",)
        action_law = "softmax(exp(eta)*log(q)+z); eta0=0; q=.9*exact_greedy+.1/N"
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    key = hashlib.sha256(f"{object_id}/seed/{seed}".encode("ascii")).digest()
    binding = bind_native_backend(build_root=out / "native_build")
    model = PhasePolicy(greedy_anchored=greedy_anchored, learned_prior_strength=learned_prior_strength)
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
    for update in range(1, updates + 1):
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
        if learned_prior_strength:
            curve.update(log_prior_strength=float(model.log_prior_strength.detach()),
                         prior_strength=float(model.log_prior_strength.detach().exp()))
        curves.append(curve)
        with (out / "curves.jsonl").open("a", encoding="utf8") as f:
            f.write(json.dumps(curve, allow_nan=False) + "\n")
        if update % 32 == 0:
            print(f"update {update}/{updates}", flush=True)
    torch.save(dict(model=model.state_dict(), optimizer=optimizer.state_dict(), baselines=baselines,
                    updates=updates, seed=seed, object_id=object_id, action_law=action_law, launch_sha=launch_sha,
                    **({"learned_prior_strength": True} if learned_prior_strength else {})), out / (final_role + ".pt"))
    before_evaluation = flat_parameters(model).clone() if learned_prior_strength else None
    for role in roles[1:]:
        panels[role] = evaluate(model, role, key, binding, out)
    comparison = contrasts(panels, final_role)
    summary = dict(status="COMPLETE", object_id=object_id, seed=seed, launch_sha=launch_sha,
        action_law=action_law,
        parameters=sum(p.numel() for p in model.parameters()), independent_fits=1,
        training_episodes=sum(c["training_episodes"] for c in curves), training_updates=len(curves),
        backward_calls=sum(c["backward_calls"] for c in curves),
        optimizer_calls=sum(c["optimizer_calls"] for c in curves),
        evaluation_episodes={r: len(panels[r]) for r in roles},
        native_ticks=64 * (sum(c["training_episodes"] for c in curves) + sum(map(len, panels.values()))),
        initial_norm=float(torch.linalg.vector_norm(initial)),
        displacement=float(torch.linalg.vector_norm(flat_parameters(model) - initial)),
        nonzero_parameter_updates=sum(c["parameter_step_norm"] > 0 for c in curves),
        phase_draws_training=16 * sum(c["training_episodes"] for c in curves),
        phase_draws_evaluation=16 * (len(panels["initialization"]) + len(panels[final_role])),
        endpoint_means={role: cell_means(rows) for role, rows in panels.items()}, comparison=comparison,
        reading_flags=reading(*(comparison[n]["mean"] for n in ("D_g", "D_n", "G_U"))),
        native_Y_source="direct native terminal endpoint for all roles; never inferred from post-event U",
        uncertainty="paired scenario uncertainty conditional on one fit; contrasts share final panel",
        native_source_sha256=binding.source_sha256, study_body_wall_s=time.monotonic() - started)
    if learned_prior_strength:
        modal = contrasts(panels, "modal")
        summary.update(learned_prior_strength=True,
            prior_strength=dict(initial_log=0.0, initial=1.0,
                final_log=float(model.log_prior_strength.detach()),
                final=float(model.log_prior_strength.detach().exp())),
            modal_comparison={name: modal[name] for name in ("D_g", "D_n")},
            modal_team_decisions=16 * len(panels["modal"]),
            evaluation_parameter_displacement=float(torch.linalg.vector_norm(
                flat_parameters(model) - before_evaluation)))
    write_json(out / "summary.json", summary)
    # The required publication path is exercised inside this invocation.
    published = json.loads((out / "summary.json").read_text(encoding="utf8"))
    return published

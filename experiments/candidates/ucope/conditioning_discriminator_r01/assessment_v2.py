"""Authoritative decomposed assessment-02 workload and timer ledger."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from fractions import Fraction
import time

from .checkpoint import save_snapshot_transaction
from .contract import ARM_IDS, CONTEXTS, K_EVAL, K_TRAIN, WorkloadConfig
from .host import execute_episode, generate_population, ordered_rows
from .model import basis_for_record, build_arm, raw_initialization
from .oracle import posterior_short
from .resources import _tree_sample, directory_bytes
from .training import ArmInitialization, _activity, _candidate_features, _cyclic_indices, _step, _tail_targets, feature_matrix, load_checkpoint_models_read_only, materialize_root_targets
from .conditioning import build_gram_design, factor_gram_design, pair_initial_coefficients
from .topology import configure_torch_topology_once

TIMER_SPECS = {
    "entry_fixed": (1, 1, 1),
    "environment_rows": (320, 122_880, 384),
    "feature_row_assembly": (480, 184_320, 384),
    "gram_design_binding_rows": (480, 184_320, 384),
    "cholesky_factorization": (4, 12, 3),
    "learner_optimizer_setup": (8, 24, 3),
    "initialization_parity_training_rows": (960, 368_640, 384),
    "initialization_parity_candidate_rows": (2_336, 7_008, 3),
    "tail_update_steps": (8, 1_920, 240),
    "root_target_rows": (640, 245_760, 384),
    "root_update_steps": (16, 3_840, 240),
    "snapshot_full_binding_rows": (1_280, 983_040, 768),
    "evaluation_projection_reload": (8, 48, 6),
    "candidate_evaluation": (4_736, 28_416, 6),
    "sampled_episode_work": (128, 24_576, 192),
    "sanitized_assembly": (8, 48, 6),
}
MEASURE_FIELDS = ("wall_seconds", "cpu_seconds", "io_read_bytes", "io_write_bytes", "scratch_bytes_created", "durable_bytes_created")


class StageLedger:
    def __init__(self, scratch: Path, durable: Path):
        self.scratch, self.durable = scratch, durable
        self.values = {key: {field: 0.0 if field.endswith("seconds") else 0 for field in MEASURE_FIELDS} for key in TIMER_SPECS if key != "entry_fixed"}

    @contextmanager
    def measure(self, key: str):
        if key == "entry_fixed" or key not in self.values: raise ValueError("invalid classified timer")
        before_tree = _tree_sample(); before_wall = time.perf_counter(); before_scratch = directory_bytes(self.scratch); before_durable = directory_bytes(self.durable)
        yield
        after_tree = _tree_sample(); row = self.values[key]
        row["wall_seconds"] += time.perf_counter() - before_wall
        row["cpu_seconds"] += max(0, after_tree["cpu_milliseconds"] - before_tree["cpu_milliseconds"]) / 1000
        row["io_read_bytes"] += max(0, after_tree["io_read_bytes"] - before_tree["io_read_bytes"])
        row["io_write_bytes"] += max(0, after_tree["io_write_bytes"] - before_tree["io_write_bytes"])
        row["scratch_bytes_created"] += max(0, directory_bytes(self.scratch) - before_scratch)
        row["durable_bytes_created"] += max(0, directory_bytes(self.durable) - before_durable)

    def rows_without_entry(self) -> list[dict[str, object]]:
        rows = []
        for key in TIMER_SPECS:
            if key == "entry_fixed": continue
            assessment_units, science_units, multiplier = TIMER_SPECS[key]
            rows.append({"timer_key": key, **self.values[key], "assessment_work_units": assessment_units, "science_work_units": science_units, "multiplier": multiplier})
        return rows


def reload_snapshots_once(paths):
    loaded = []
    for path in paths:
        payload, root, tail = load_checkpoint_models_read_only(path)
        loaded.append((payload, SimpleNamespace(root=root, tail=tail)))
    return loaded


def run_assessment_workload(*, binding: str, scratch_root: str | Path, durable_root: str | Path):
    """Execute the exact V2 technical workload without learned-choice evaluation."""
    topology_record = configure_torch_topology_once()
    import torch
    config = WorkloadConfig.assess(); scratch, durable = Path(scratch_root), Path(durable_root); scratch.mkdir(parents=True, exist_ok=False); durable.mkdir(parents=True, exist_ok=True)
    ledger = StageLedger(scratch, durable); seed = config.seed_ids[0]
    with ledger.measure("environment_rows"): population = generate_population(config, seed)
    matrices = {}; row_sets = {}
    with ledger.measure("feature_row_assembly"):
        for fold in (0, 1):
            row_sets[(fold, "tail")] = ordered_rows(population, fold_id=fold, stage="tail"); row_sets[(fold, "root")] = ordered_rows(population, fold_id=fold, stage="root")
            matrices[(fold, "tail")] = feature_matrix(row_sets[(fold, "tail")], stage="tail"); matrices[(fold, "root")] = feature_matrix(row_sets[(fold, "root")], stage="root")
    grams = {}
    with ledger.measure("gram_design_binding_rows"):
        for fold in (0, 1): grams[fold] = {stage: build_gram_design(stage, matrices[(fold, stage)]) for stage in ("tail", "root")}
    transforms = {}
    with ledger.measure("cholesky_factorization"):
        for fold in (0, 1): transforms[fold] = {stage: factor_gram_design(grams[fold][stage]) for stage in ("tail", "root")}
    training_parity, candidate_parity, candidates = {}, {}, {}
    with ledger.measure("initialization_parity_training_rows"):
        for arm in ARM_IDS:
            for fold in (0, 1):
                training_parity[(arm, fold)] = {stage: pair_initial_coefficients(transforms[fold][stage], raw_initialization(stage, seed, fold), matrices[(fold, stage)]) for stage in ("root", "tail")}
    with ledger.measure("initialization_parity_candidate_rows"):
        for fold in (0, 1): candidates[fold] = {stage: _candidate_features(stage) for stage in ("root", "tail")}
        for arm in ARM_IDS:
            for fold in (0, 1): candidate_parity[(arm, fold)] = {stage: pair_initial_coefficients(transforms[fold][stage], raw_initialization(stage, seed, fold), candidates[fold][stage]) for stage in ("root", "tail")}
    bundles = {}; activities = {}
    with ledger.measure("learner_optimizer_setup"):
        for arm in ARM_IDS:
            for fold in (0, 1):
                initials = {stage: training_parity[(arm, fold)][stage].raw_beta0 if arm == ARM_IDS[0] else training_parity[(arm, fold)][stage].whitened_beta0 for stage in ("root", "tail")}
                bundles[(arm, fold)] = build_arm(arm, seed, fold, root_transform=transforms[fold]["root"], tail_transform=transforms[fold]["tail"], root_initial=initials["root"], tail_initial=initials["tail"])
                activities[(arm, fold)] = _activity(len(row_sets[(fold, "root")]), len(row_sets[(fold, "tail")]))
    with ledger.measure("tail_update_steps"):
        for arm in ARM_IDS:
            for fold in (0, 1):
                bundle, activity = bundles[(arm, fold)], activities[(arm, fold)]; targets = _tail_targets(row_sets[(fold, "tail")])
                for update in range(config.tail_updates):
                    indices = _cyclic_indices(len(targets), update, config.batch_size); norm, clipped = _step(bundle.tail, bundle.tail_optimizer, matrices[(fold, "tail")][indices], targets[indices])
                    activity["tail_optimizer_updates"] += 1; activity["tail_example_exposures"] += config.batch_size; activity["tail_gradient_norm_sum"] += norm; activity["tail_gradient_norm_max"] = max(activity["tail_gradient_norm_max"], norm); activity["tail_clip_events"] += int(clipped)
    frozen_targets = {}
    with ledger.measure("root_target_rows"):
        for arm in ARM_IDS:
            for fold in (0, 1):
                rows = row_sets[(fold, "root")]; frozen_targets[(arm, fold)] = materialize_root_targets(rows, bundles[(arm, fold)].tail, transforms[fold]["tail"]); activities[(arm, fold)]["target_materialization_events"] = 1; activities[(arm, fold)]["target_materialization_rows"] = len(rows)
    checkpoint_paths = []
    for update in range(1, config.root_updates + 1):
        with ledger.measure("root_update_steps"):
            for arm in ARM_IDS:
                for fold in (0, 1):
                    bundle, activity = bundles[(arm, fold)], activities[(arm, fold)]; indices = _cyclic_indices(len(frozen_targets[(arm, fold)]), update - 1, config.batch_size); norm, clipped = _step(bundle.root, bundle.root_optimizer, matrices[(fold, "root")][indices], frozen_targets[(arm, fold)][indices])
                    activity["root_optimizer_updates"] += 1; activity["root_example_exposures"] += config.batch_size; activity["root_gradient_norm_sum"] += norm; activity["root_gradient_norm_max"] = max(activity["root_gradient_norm_max"], norm); activity["root_clip_events"] += int(clipped)
        if update in config.checkpoint_root_updates:
            with ledger.measure("snapshot_full_binding_rows"):
                for arm in ARM_IDS:
                    for fold in (0, 1):
                        bundle = bundles[(arm, fold)]; base = scratch / "snapshots" / arm / f"fold-{fold}" / f"root-{update:04d}"
                        checkpoint_paths.append(save_snapshot_transaction(base, config=config, binding=binding, arm_id=arm, seed_id=seed, fold_id=fold, root_update=update, tail_updates=config.tail_updates, root=bundle.root, tail=bundle.tail, root_optimizer=bundle.root_optimizer, tail_optimizer=bundle.tail_optimizer, frozen_root_targets=frozen_targets[(arm, fold)], transforms={stage: transforms[fold][stage].to_bytes() for stage in ("root", "tail")}, activity=activities[(arm, fold)]))
    loaded = []
    with ledger.measure("evaluation_projection_reload"):
        loaded = reload_snapshots_once([record["projection_path"] for record in checkpoint_paths])
    candidate_counts = []
    with ledger.measure("candidate_evaluation"):
        for payload, bundle in loaded:
            count = 0
            with torch.no_grad():
                for link, reliability, cost in CONTEXTS:
                    root_record = SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=Fraction(1, 2))
                    for periods in (K_TRAIN, K_EVAL):
                        values = bundle.root(torch.stack([basis_for_record(root_record, stage="root", period=0, action_probe=True), *[basis_for_record(root_record, stage="root", period=period, action_probe=False) for period in periods]])); count += values.numel()
                        if not torch.isfinite(values).all().item(): raise ValueError("technical candidate values nonfinite")
                    for displayed in range(7):
                        tail_record = SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=posterior_short(link, reliability, displayed))
                        for periods in (K_TRAIN, K_EVAL):
                            values = bundle.tail(torch.stack([basis_for_record(tail_record, stage="tail", period=period) for period in periods])); count += values.numel()
                            if not torch.isfinite(values).all().item(): raise ValueError("technical candidate values nonfinite")
            if count != 592: raise ValueError("technical candidate value count drift")
            candidate_counts.append(count)
    sampled_counts = []
    with ledger.measure("sampled_episode_work"):
        for payload, _bundle in loaded:
            count = 0
            for context in CONTEXTS:
                for index in range(2):
                    execute_episode(context, ancestry=(config.run_id, payload["arm_id"], payload["fold_id"], payload["root_update"]), episode_index=index, root_action="PROBE", support=K_EVAL, tail_selector=lambda displayed: K_EVAL[displayed % len(K_EVAL)], evaluation=True); count += 1
            sampled_counts.append(count)
    with ledger.measure("sanitized_assembly"):
        structural = [{"snapshot_index": index, "candidate_value_count": candidate_counts[index], "fixed_technical_episode_count": sampled_counts[index]} for index in range(len(loaded))]
    if len(structural) != 8 or sum(candidate_counts) != 4_736 or sum(sampled_counts) != 128: raise ValueError("assessment structural work reconciliation failed")
    return {"timer_rows": ledger.rows_without_entry(), "structural_records": structural, "snapshot_count": len(checkpoint_paths), "scratch_root": str(scratch), "durable_root": str(durable), "topology": topology_record}

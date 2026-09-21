"""Fixed-program C07 confirmation built on the frozen C06 evaluator."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import resource
import time

import numpy as np

from ..c01.host import FRAME, PACKET_BYTES, CrossingHost, Worlds
from ..c06.study import MODEL_COUNT_KEYS, _contrast, _reading, _run_batch


ARMS = ("NEAR_COMMIT", "LONG", "ACTIVE_FIRST")
COMPARISONS = (
    ("NEAR_COMMIT-ACTIVE_FIRST", "NEAR_COMMIT", "ACTIVE_FIRST"),
    ("LONG-NEAR_COMMIT", "LONG", "NEAR_COMMIT"),
    ("LONG-ACTIVE_FIRST", "LONG", "ACTIVE_FIRST"),
)
NATIVE_CONTROL_FILES = {
    "launch-manifest.json",
    "admission-preflight.json",
    "launch-status.json",
    "stdout.log",
    "stderr.log",
}
NORMAL_95_Z = 1.96
TASK_MARGIN_JOBS = 0.05


@dataclass(frozen=True)
class Config:
    world_seeds: tuple[int, ...] = (73180, 73181, 73182, 73183, 73184)
    model_seeds: tuple[int, ...] = (973180, 973181, 973182, 973183, 973184)
    phase: int = 30
    worlds_per_block: int = 256
    horizon: int = 96
    batch: int = 16
    particles: int = 32

    def __post_init__(self):
        world_seeds = tuple(int(seed) for seed in self.world_seeds)
        model_seeds = tuple(int(seed) for seed in self.model_seeds)
        object.__setattr__(self, "world_seeds", world_seeds)
        object.__setattr__(self, "model_seeds", model_seeds)
        if not world_seeds or len(world_seeds) != len(model_seeds):
            raise ValueError("world and model seed tuples must be nonempty and equally sized")
        if min(world_seeds + model_seeds) < 0 or self.phase < 0:
            raise ValueError("seeds and phase must be nonnegative")
        if len(set(world_seeds)) != len(world_seeds):
            raise ValueError("world master seeds must be unique across confirmation blocks")
        if len(set(model_seeds)) != len(model_seeds):
            raise ValueError("model master seeds must be unique across confirmation blocks")
        if self.horizon <= 0 or self.horizon % 48:
            raise ValueError("horizon must be a positive multiple of 48")
        if min(self.worlds_per_block, self.batch) < 1:
            raise ValueError("world and batch counts must be positive")
        if self.particles < 2:
            raise ValueError("at least two particles are required for a finite model SE")
        if len(world_seeds) * self.worlds_per_block < 2:
            raise ValueError("at least two paired worlds are required for the pooled interval")


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _validate_clean_output(out):
    out = Path(out)
    if not out.exists():
        return
    if not out.is_dir():
        raise FileExistsError("C07 output path already exists and is not a directory")
    unexpected = [
        path.name for path in out.iterdir()
        if path.name not in NATIVE_CONTROL_FILES
        and not (path.name.startswith(".hmasd-launch-") and path.name.endswith(".tmp"))
    ]
    if unexpected:
        raise FileExistsError(
            "C07 never overwrites or resumes scientific output: "
            + ", ".join(sorted(unexpected)))


def _resource_snapshot():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return dict(
        ru_maxrss_child_kib=int(usage.ru_maxrss),
        user_cpu_child_seconds=float(usage.ru_utime),
        system_cpu_child_seconds=float(usage.ru_stime),
    )


def _resource_delta(before, after):
    return dict(
        ru_maxrss_child_kib=after["ru_maxrss_child_kib"],
        ru_maxrss_increase_kib=max(
            0, after["ru_maxrss_child_kib"] - before["ru_maxrss_child_kib"]),
        user_cpu_child_seconds=(
            after["user_cpu_child_seconds"] - before["user_cpu_child_seconds"]),
        system_cpu_child_seconds=(
            after["system_cpu_child_seconds"] - before["system_cpu_child_seconds"]),
        rss_scope="scientific process peak observed through panel end; Linux ru_maxrss KiB",
        cpu_scope="scientific process CPU consumed during panel",
    )


def _paired_units(left, right):
    fields = ("block", "world_id", "world_seed", "model_seed")
    left_keys = [tuple(row[field] for field in fields) for row in left]
    right_keys = [tuple(row[field] for field in fields) for row in right]
    if not left_keys or left_keys != right_keys:
        raise ValueError("paired confirmation panels must have the same ordered block/world units")
    return [dict(zip(fields, key)) for key in left_keys]


def _add_normal_interval(metric):
    differences = np.asarray(metric["per_world_difference"], dtype=np.float64)
    if differences.size < 2:
        raise ValueError("normal intervals require at least two paired worlds")
    mean = float(differences.mean())
    se = float(differences.std(ddof=1) / np.sqrt(differences.size))
    metric["conditional_world_se"] = se
    metric["normal_95"] = dict(
        z=NORMAL_95_Z,
        lower=float(mean - NORMAL_95_Z * se),
        upper=float(mean + NORMAL_95_Z * se),
        formula="mean +/- 1.96 * sample_sd(paired world differences) / sqrt(n)",
    )


def _paired_contrast(left, right):
    units = _paired_units(left, right)
    contrast = _contrast(left, right)
    contrast["paired_units"] = units
    for metric in contrast.values():
        if isinstance(metric, dict) and "per_world_difference" in metric:
            _add_normal_interval(metric)
    return contrast


def _fixed_reading(block_contrasts, pooled_contrasts):
    primary_blocks = [
        block["NEAR_COMMIT-ACTIVE_FIRST"]["completed_jobs"]
        for block in block_contrasts
    ]
    primary_pooled = pooled_contrasts["NEAR_COMMIT-ACTIVE_FIRST"]["completed_jobs"]
    secondary_pooled = pooled_contrasts["LONG-NEAR_COMMIT"]["completed_jobs"]
    all_block_means_positive = all(metric["mean"] > 0.0 for metric in primary_blocks)
    pooled_lower_exceeds_margin = (
        primary_pooled["normal_95"]["lower"] > TASK_MARGIN_JOBS)
    secondary_upper_below_margin = (
        secondary_pooled["normal_95"]["upper"] < TASK_MARGIN_JOBS)
    return dict(
        primary=dict(
            comparison="NEAR_COMMIT-ACTIVE_FIRST",
            margin_jobs_per_episode=TASK_MARGIN_JOBS,
            all_block_means_positive=all_block_means_positive,
            pooled_normal_95_lower=primary_pooled["normal_95"]["lower"],
            pooled_lower_exceeds_margin=pooled_lower_exceeds_margin,
            retained=all_block_means_positive and pooled_lower_exceeds_margin,
            rule=("all block mean paired differences > 0 and pooled normal 95% lower "
                "bound > 0.05 jobs per 96-tick episode"),
        ),
        secondary=dict(
            comparison="LONG-NEAR_COMMIT",
            margin_jobs_per_episode=TASK_MARGIN_JOBS,
            pooled_normal_95_upper=secondary_pooled["normal_95"]["upper"],
            extra_gain_bounded_below_margin=secondary_upper_below_margin,
            rule="pooled normal 95% upper bound < 0.05 jobs per 96-tick episode",
            scope="descriptive bound only; no identity, equivalence, or joint-coverage claim",
        ),
        interval_units="independently addressed paired worlds pooled across fixed seed blocks",
        multiplicity="no multiplicity-adjusted joint-coverage assertion",
    )


def _initial_counts(config):
    counts = dict(
        started_fits=0,
        train_episodes=0,
        train_transitions=0,
        optimizer_steps=0,
        evaluation_optimizer_steps=0,
        parameter_updates=0,
        selection_episodes=0,
        rule_search_arms=0,
        rule_search_exposure_episodes=0,
        confirmation_episodes=0,
        confirmation_native_episodes=0,
        actual_transitions=0,
        belief_observation_record_calls=0,
        belief_observation_rows=0,
        belief_packet_update_rows=0,
        belief_contradiction_rows=0,
    )
    for key in MODEL_COUNT_KEYS:
        counts[key] = 0
    for block, (world_seed, model_seed) in enumerate(
            zip(config.world_seeds, config.model_seeds)):
        stage = _stage_name(block, world_seed, model_seed)
        counts[f"{stage}_episodes"] = 0
        counts[f"{stage}_transitions"] = 0
        for key in MODEL_COUNT_KEYS:
            counts[f"{stage}_{key}"] = 0
        for key in (
            "belief_observation_record_calls",
            "belief_observation_rows",
            "belief_packet_update_rows",
            "belief_contradiction_rows",
        ):
            counts[f"{stage}_{key}"] = 0
    return counts


def _stage_name(block, world_seed, model_seed):
    return f"block{block}_s{world_seed}_m{model_seed}"


def run_confirmation(out, launch_sha, config=Config()):
    """Run a configurable engineering instance of the fixed C07 program."""
    out = Path(out)
    _validate_clean_output(out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    initial_resource = _resource_snapshot()
    counts = _initial_counts(config)
    expected = dict(
        jobs_per_world=config.horizon // 12 + config.horizon // 16,
        packets_per_world=2 * config.horizon // FRAME,
        bytes_per_world=2 * config.horizon // FRAME * PACKET_BYTES,
    )
    modeled_episodes = (
        len(config.world_seeds) * 2 * config.worlds_per_block)
    planned = dict(
        blocks=len(config.world_seeds),
        arms=len(ARMS),
        episodes=len(config.world_seeds) * len(ARMS) * config.worlds_per_block,
        actual_transitions=(
            len(config.world_seeds) * len(ARMS)
            * config.worlds_per_block * config.horizon),
        modeled_episodes=modeled_episodes,
        maximum_model_branch_transitions=(
            modeled_episodes * (config.horizon * 3 // 4) * config.particles
            * 2 * min(32, config.horizon)),
        fits=0,
        parameter_updates=0,
    )
    summary = dict(
        object="SIR-C07",
        direction="skill_information_refresh",
        status="RUNNING",
        launch_sha=launch_sha,
        source_sha=launch_sha,
        config=asdict(config),
        program=dict(
            arms=list(ARMS),
            modeled_threshold=0.0,
            development_selection="none",
            root_diagnostics="none",
            continuation="ACTIVE_FIRST after the paired root intervention",
        ),
        counts=counts,
        expected_accounting=expected,
        planned_accounting=planned,
        panels=[],
        blocks=[],
        contrasts_by_block=[],
        pooled_contrasts={},
        fixed_reading={},
        trace_files=[],
        phases_seconds={},
        resources_unmeasured=False,
        limits=[],
    )

    def refresh_runtime():
        current = _resource_snapshot()
        summary["wall_seconds"] = time.monotonic() - started
        summary["resources"] = _resource_delta(initial_resource, current)
        summary["resources"]["confirmation_user_cpu_seconds"] = (
            current["user_cpu_child_seconds"] - initial_resource["user_cpu_child_seconds"])
        summary["resources"]["confirmation_system_cpu_seconds"] = (
            current["system_cpu_child_seconds"] - initial_resource["system_cpu_child_seconds"])
        summary["resources"].update(current)
        summary["resources"]["cpu_scope"] = (
            "process lifetime child CPU including imports; confirmation_* excludes pre-function CPU")
        summary["wall_scope"] = (
            "run_confirmation function; complete native process timing is in launch and exit records")

    def flush_summary():
        refresh_runtime()
        _write_json(out / "summary.json", summary)

    _write_json(out / "config.json", dict(
        source_sha=launch_sha,
        fixed_program=True,
        threshold=0.0,
        arms=list(ARMS),
        **asdict(config),
    ))
    (out / "updates.jsonl").open("x", encoding="utf-8").close()
    summary["phases_seconds"]["setup"] = time.monotonic() - started
    flush_summary()

    rows_by_block = []
    phase_started = time.monotonic()
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episodes:

        def evaluate(block, world_seed, model_seed, arm):
            stage = _stage_name(block, world_seed, model_seed)
            rows, traces = [], []
            panel_started = time.monotonic()
            panel_resource = _resource_snapshot()
            panel_before = counts.copy()
            trace_start = len(summary["trace_files"])
            complete = False
            try:
                for start in range(0, config.worlds_per_block, config.batch):
                    stop = min(start + config.batch, config.worlds_per_block)
                    ids = tuple(range(start, stop))
                    host = CrossingHost(
                        Worlds.make(world_seed, config.phase, ids, config.horizon))
                    try:
                        batch_rows, trace_name = _run_batch(
                            host, arm, 0.0 if arm != "ACTIVE_FIRST" else None,
                            ids, model_seed, config.phase, config.particles, counts,
                            stage, True, out, start, summary["trace_files"], None)
                    finally:
                        for record in summary["trace_files"][trace_start:]:
                            record.update(
                                block=block, world_seed=world_seed, model_seed=model_seed,
                                world_phase=config.phase)
                    if not all(
                        row["jobs_started"] == expected["jobs_per_world"]
                        and row["packets"] == expected["packets_per_world"]
                        and row["bytes"] == expected["bytes_per_world"]
                        for row in batch_rows
                    ):
                        raise RuntimeError("fixed host job or communication accounting changed")
                    enriched = [dict(
                        phase="confirmation",
                        world_phase=config.phase,
                        stage=stage,
                        block=block,
                        world_seed=world_seed,
                        model_seed=model_seed,
                        arm=arm,
                        threshold=0.0 if arm != "ACTIVE_FIRST" else None,
                        **row,
                    ) for row in batch_rows]
                    for row in enriched:
                        episodes.write(json.dumps(row, allow_nan=False) + "\n")
                    episodes.flush()
                    rows.extend(enriched)
                    if trace_name is not None:
                        traces.append(trace_name)
                    counts[f"{stage}_episodes"] += len(enriched)
                    counts["confirmation_episodes"] += len(enriched)
                    counts["confirmation_native_episodes"] += len(enriched)
                    flush_summary()
                    print(json.dumps(dict(
                        status="PROGRESS",
                        block=block,
                        arm=arm,
                        completed_native_episodes=counts["confirmation_native_episodes"],
                    )), flush=True)
                complete = True
                return rows, traces
            finally:
                panel = dict(
                    block=block,
                    world_seed=world_seed,
                    model_seed=model_seed,
                    phase="confirmation",
                    world_phase=config.phase,
                    stage=stage,
                    arm=arm,
                    threshold=0.0 if arm != "ACTIVE_FIRST" else None,
                    complete=complete,
                    completed_episodes=len(rows),
                    wall_seconds=time.monotonic() - panel_started,
                    counts={
                        key: value - panel_before.get(key, 0)
                        for key, value in counts.items()
                    },
                    resources=_resource_delta(panel_resource, _resource_snapshot()),
                    traces=[record["file"] for record in summary["trace_files"][trace_start:]],
                )
                summary["panels"].append(panel)

        try:
            for block, (world_seed, model_seed) in enumerate(
                    zip(config.world_seeds, config.model_seeds)):
                arm_rows = {}
                block_started = time.monotonic()
                block_resource = _resource_snapshot()
                block_before = counts.copy()
                for arm in ARMS:
                    arm_rows[arm], traces = evaluate(block, world_seed, model_seed, arm)
                rows_by_block.append(arm_rows)
                block_contrasts = {
                    name: _paired_contrast(arm_rows[left], arm_rows[right])
                    for name, left, right in COMPARISONS
                }
                summary["contrasts_by_block"].append(dict(
                    block=block,
                    world_seed=world_seed,
                    model_seed=model_seed,
                    world_phase=config.phase,
                    contrasts=block_contrasts,
                ))
                summary["blocks"].append(dict(
                    block=block,
                    world_seed=world_seed,
                    model_seed=model_seed,
                    world_phase=config.phase,
                    readings={arm: _reading(arm_rows[arm]) for arm in ARMS},
                    wall_seconds=time.monotonic() - block_started,
                    counts={
                        key: value - block_before.get(key, 0)
                        for key, value in counts.items()
                    },
                    resources=_resource_delta(block_resource, _resource_snapshot()),
                ))
                flush_summary()

            pooled_rows = {
                arm: [row for block_rows in rows_by_block for row in block_rows[arm]]
                for arm in ARMS
            }
            summary["pooled_contrasts"] = {
                name: _paired_contrast(pooled_rows[left], pooled_rows[right])
                for name, left, right in COMPARISONS
            }
            block_contrast_values = [item["contrasts"]
                for item in summary["contrasts_by_block"]]
            summary["fixed_reading"] = _fixed_reading(
                block_contrast_values, summary["pooled_contrasts"])
            summary["phases_seconds"]["confirmation"] = time.monotonic() - phase_started
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["status"] = "TECHNICAL_FAILURE"
            summary["error"] = {"type": type(error).__name__, "message": str(error)}
            summary["limits"].append(f"{type(error).__name__}: {error}")
            summary["phases_seconds"]["confirmation"] = time.monotonic() - phase_started
            raise
        finally:
            summary["phases_seconds"]["total"] = time.monotonic() - started
            flush_summary()

    published = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    if published["status"] != "COMPLETE" or published["counts"] != counts:
        raise RuntimeError("C07 summary readback failed")
    return summary

"""Thin B02 binding and publication adapter around reactive-renewal B01."""

from pathlib import Path

from ..reactive_renewal_b01 import study as b01
from ..uav_motion_prefix_b01.study import write_summary


OBJECT = "UCOPE_REACTIVE_RENEWAL_B02"
NOTEBOOK = "docs/research/candidates/ucope/NOTES.md"
NOTEBOOK_SECTION = "2026-09-19 — owner-selected parallel feedback-renewal branch"
SOURCE_OBJECT = b01.OBJECT
EXECUTION_NODE = "local_linux"
ALLOWED_MASTERS = (8911, 8912)
FITTED_ARMS = ("R", "F", "G")
HORIZON = 256
TRAIN_EPISODES = 2048
EVAL_EPISODES = 64
CHUNK = 32
WATCHDOG_SECONDS = 6000


def config_for(master):
    if master not in ALLOWED_MASTERS:
        raise ValueError("master must be one of the two prospectively selected B02 blocks")
    return b01.Config(
        seed=master,
        horizon=HORIZON,
        train_episodes=TRAIN_EPISODES,
        eval_episodes=EVAL_EPISODES,
        chunk=CHUNK,
        watchdog_seconds=WATCHDOG_SECONDS,
        fixture=False,
    )


def _activity_record(arm, record):
    counts = record.get("counts", {}) if isinstance(record, dict) else {}
    activity = {
        key: int(counts.get(key, 0))
        for key in (
            "constructors",
            "train_episodes",
            "train_team_steps",
            "optimizer_steps",
            "eval_episodes",
            "eval_team_steps",
        )
    }
    observed_training = any(
        activity[key] > 0
        for key in ("train_episodes", "train_team_steps", "optimizer_steps")
    )
    return {
        "arm": arm,
        "record_present": isinstance(record, dict),
        "scientific_constructor_observed": activity["constructors"] > 0,
        "training_activity_observed": observed_training,
        "train_complete": bool(record.get("train_complete", False))
        if isinstance(record, dict)
        else False,
        "eval_complete": bool(record.get("eval_complete", False))
        if isinstance(record, dict)
        else False,
        "activity": activity,
    }


def _fit_accounting(summary):
    arms = summary.get("arms", {})
    records = {
        arm: _activity_record(arm, arms.get(arm)) for arm in FITTED_ARMS
    }
    activity_arms = [
        arm for arm, record in records.items() if record["training_activity_observed"]
    ]
    constructor_arms = [
        arm
        for arm, record in records.items()
        if record["scientific_constructor_observed"]
    ]
    completed = [arm for arm, record in records.items() if record["train_complete"]]
    invocation_complete = summary.get("status") == "COMPLETE"
    return {
        "allocated_fit_arms": list(FITTED_ARMS),
        "allocated_fits_this_invocation": 3,
        "allocated_fits_complete_batch": 6,
        "observed_training_activity_arms": activity_arms,
        "observed_training_activity_fit_lower_bound": len(activity_arms),
        "scientific_constructor_arms": constructor_arms,
        "completed_training_arms": completed,
        "completed_training_fits": len(completed),
        "exact_started_fits": 3 if invocation_complete else None,
        "per_arm": records,
        "qualification": (
            "On an incomplete invocation, inherited counters prove completed activity and "
            "scientific construction but cannot prove the exact number of allocated fits "
            "that crossed every possible start boundary. No unused arm authorizes an "
            "automatic replacement."
        ),
    }


def _artifact_record(path):
    path = Path(path)
    return {"path": str(path), "present": path.is_file()}


def _telemetry(summary):
    peak_rss_kib = None
    unmeasured = []
    try:
        import resource

        peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        unmeasured.append("single-process peak RSS")
    return {
        "wall_seconds": summary.get("elapsed_wall_seconds"),
        "wall_scope": (
            "runner main entry through the inherited scientific loop and its first "
            "summary preparation; excludes final B02 rewrite, print and process exit"
        ),
        "process_cpu_seconds": summary.get("aggregate_process_cpu_seconds"),
        "process_cpu_scope": (
            "single process from inherited B01 run entry through its scientific loop; "
            "excludes parser, admission and Torch import startup"
        ),
        "peak_rss_kib": peak_rss_kib,
        "peak_rss_scope": (
            "single process ru_maxrss through B02 adaptation"
            if peak_rss_kib is not None
            else "unavailable in the runner"
        ),
        "complete_process_exit_wall": None,
        "external_scope": (
            "the native launch manifest is authoritative for actual node and complete "
            "process wall/resource telemetry"
        ),
        "resources_unmeasured": unmeasured,
    }


def adapt_summary(summary, out, admission, expected_master=None):
    """Relabel one inherited invocation without changing its scientific records."""
    admitted_sha = admission.get("sha")
    if not isinstance(admitted_sha, str) or not admitted_sha:
        raise ValueError("B02 requires an admitted source SHA")

    inherited_object = summary.get("object")
    inherited_card = summary.get("card")
    inherited_launch_sha = summary.get("launch_sha")
    if inherited_object != SOURCE_OBJECT:
        raise ValueError("B02 adapter received a foreign source study")
    configuration = summary.get("configuration", {})
    master = summary.get("seed")
    if master not in ALLOWED_MASTERS or (
        expected_master is not None and master != expected_master
    ):
        raise ValueError("inherited study has the wrong B02 master")
    expected_scope = {
        "seed": master,
        "horizon": HORIZON,
        "train_episodes": TRAIN_EPISODES,
        "eval_episodes": EVAL_EPISODES,
        "chunk": CHUNK,
        "watchdog_seconds": WATCHDOG_SECONDS,
        "fixture": False,
    }
    if any(configuration.get(key) != value for key, value in expected_scope.items()):
        raise ValueError("inherited study has the wrong B02 scientific scope")

    summary["object"] = OBJECT
    summary["source_object"] = inherited_object
    summary["source_card"] = inherited_card
    summary["card"] = NOTEBOOK
    summary["notebook"] = NOTEBOOK
    summary["notebook_section"] = NOTEBOOK_SECTION
    summary["selected_masters"] = list(ALLOWED_MASTERS)
    summary["declared_execution_node"] = EXECUTION_NODE
    summary["node_evidence_scope"] = (
        "local_linux is the prospective object binding; the native launch manifest "
        "is authoritative for the actual execution node"
    )
    # Preserve only facts returned by require_admission; it does not attest a node.
    summary["admission"] = dict(admission)
    summary["inherited_launch_sha"] = inherited_launch_sha
    summary["launch_sha"] = admitted_sha
    summary.pop("new_fits", None)
    summary["fit_accounting"] = _fit_accounting(summary)
    summary["evaluation_optimizer_steps"] = 0
    summary["source_resource_note"] = summary.get("resource_note")
    summary["telemetry"] = _telemetry(summary)
    summary["resource_note"] = (
        "Runner telemetry has the explicit scopes in telemetry; missing complete-process "
        "telemetry limits only resource claims and does not invalidate the scientific result."
    )

    panel = summary.get("panel")
    if not isinstance(panel, dict):
        raise ValueError("inherited study did not publish a panel")
    inherited_reading = panel.pop("reading", None)
    panel["selected_contrast"] = "R_minus_G"
    invocation_complete = summary.get("status") == "COMPLETE"
    panel["complete"] = bool(invocation_complete and panel.get("all_panels_complete"))
    contrast_names = (
        "R_minus_F",
        "R_minus_G",
        "R_minus_H",
        "F_minus_H",
        "G_minus_H",
        "F_minus_G",
    )
    for name in contrast_names:
        contrast = panel.get(name)
        if not isinstance(contrast, dict):
            raise ValueError(f"inherited panel has no {name} contrast")
        contrast["panel_complete"] = bool(contrast.get("complete"))
        contrast["complete"] = bool(panel["complete"] and contrast["panel_complete"])
    panel["primary"] = panel["R_minus_G"]
    panel["secondary"] = {
        "R_minus_F": panel["R_minus_F"],
        "F_minus_G": panel["F_minus_G"],
    }
    panel["interpretation"] = (
        "Exploratory descriptive contrasts only; the historical categorical reading "
        "does not apply to B02."
    )
    if inherited_reading is not None:
        summary["omitted_source_categorical_reading"] = True

    if inherited_launch_sha not in (None, admitted_sha):
        summary["status"] = "INCOMPLETE"
        panel["complete"] = False
        for name in contrast_names:
            panel[name]["complete"] = False
        summary.setdefault("limits", []).append(
            "inherited launch SHA did not match the admitted source SHA"
        )

    out = Path(out)
    summary["artifacts"] = {
        "episodes": _artifact_record(out / "episodes.jsonl"),
        "updates": _artifact_record(out / "updates.jsonl"),
        "checkpoints": {
            arm: _artifact_record(out / f"{arm}_final.pt") for arm in FITTED_ARMS
        },
    }
    return summary


def run(master, out, admission, start=None):
    """Execute the unchanged B01 study once, then publish only B02 semantics."""
    config = config_for(master)
    summary = b01.run(config, out, start=start)
    summary = adapt_summary(summary, out, admission, expected_master=master)
    write_summary(Path(out) / "summary.json", summary)
    return summary

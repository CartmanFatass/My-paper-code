"""Complete only the fixed missing B06 evaluation slots, preserving original evidence."""

import hashlib
import io
import json
from pathlib import Path
import resource
import time

import torch

from . import study
from .collector import collect_episode
from .model import SOURCE_SHA256, build_arm, parameter_snapshot
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator

SOURCE_ROOT = Path(__file__).resolve().parents[4]
ORIGINAL_SOURCE = "f288de6416dff6f8b73ea634995bbe163ad9b5fd"
ORIGINAL_INVENTORY = "74d949fefdb07bed87a8eec0479002c326aaf01adb4874e6e1313a7dbe9fe15b"
ORIGINAL_FILES = 207
ORIGINAL_SUMMARY_SHA = "2cf1c6884a9584e0005e62f8284582dadc43d82cf6ebb24ea70e7ed32bd88b7f"
D_SUMMARY_SHA = "327cde4412772d01f5bbb9ca3bff5d96d901b0f44c55c7634b33283735674458"
D_CHECKPOINT_SHA = "140aee1b9fdbd2708fc787d788d25466bec8f46d9cbbdaaf8f099d0c1d415e13"
HORIZON, TRAIN, EVALUATION = 256, 512, 32
D_EPISODES = tuple(range(9, 32))
B40_EPISODES = tuple(range(32))
CPU_LIMIT_SECONDS = 600
FROZEN_SOURCE_HASHES = {
    'experiments/candidates/uav_message_content/b06/study.py': '2a7d6fdfeb0aea59be55d3fa75d1fa482171812eaacba476ea87c6019cf2ee24',
    'experiments/candidates/uav_message_content/b06/collector.py': 'e0b002961a65eddbb225964f8e0f8cccefb89ef6bef39f93c288bbbc184e5f01',
    'experiments/candidates/uav_message_content/b06/model.py': '804ce5a41125e7eba48097c23a1420178504a6ebecd64ec9e9ff1f29510a7f71',
    'experiments/candidates/uav_message_content/b06/update.py': 'a0727aacd560bd14a1c867f06f19c4e0e99c7069b0f6ce8fe2e966878b2fe6a2',
    'experiments/candidates/uav_message_content/b05/model.py': 'eced84dcdb99df0a100957e4c1ab51c7c0bbfec50acde3127c957d9437b4029f',
    'experiments/candidates/uav_message_content/b05/collector.py': '38917bc814800d7e4824ad6bd847db4c2bbe7d63abd15b1b6cb5a75b6f00f578',
    'experiments/candidates/uav_message_content/b05/channel.py': 'ad48afa619a7dbc43899ac1489469c02236081c4dbdeee5c2b69927d7239eb6e',
    'experiments/candidates/uav_message_content/b05/update.py': 'be7d4f016d5783566832ebdeef9754a905b9669670865283f8069cfa6851dd23',
    'experiments/candidates/contention_aware_decentralized_communication/cadc_b01/model.py': '46ed96aeeb6c13640bd4105d283ebf3e12f9660844ee9456b65d60eb0d143633',
    'experiments/candidates/contention_aware_decentralized_communication/cadc_b01/channel.py': 'f28cdd2e452646169653daabdad963c1a0cdf00f9388454e7de7a0710145bf91',
    'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py': 'fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6',
    'experiments/candidates/ucope/uav_motion_prefix_b01/policy.py': 'e324640251d0d025549705ff7541b765e7b96733f422c48ee9c2f5bd07709614',
    'envs/pettingzoo/uav_env.py': 'fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e',
    'envs/pettingzoo/env_adapter.py': '8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40',
    'envs/pettingzoo/uav_radio.py': 'db3464803b1a5aa9c9504096810dc971266a6bd7eba1c31dfe79e7d8d903f3cc',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory(root):
    """Handoff inventory: sorted relative path NUL size NUL SHA256 LF."""
    root = Path(root)
    digest, count, size = hashlib.sha256(), 0, 0
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        require(not path.is_symlink(), "evidence inventory contains symlink")
        if path.is_file():
            n = path.stat().st_size
            record = f"{path.relative_to(root).as_posix()}\0{n}\0{study.sha256(path)}\n"
            digest.update(record.encode("utf-8"))
            count += 1
            size += n
    return dict(sha256=digest.hexdigest(), files=count, bytes=size)


def verify_frozen_source():
    for name, expected in FROZEN_SOURCE_HASHES.items():
        require(study.sha256(SOURCE_ROOT / name) == expected, f"frozen source mismatch: {name}")
    return dict(FROZEN_SOURCE_HASHES)


def identity(row):
    return row["master"], row["arm"], row["phase"], row["episode"]


def validate_rows(rows, master, arm, episodes):
    require([identity(r) for r in rows] == [(master, arm, "final_eval", e) for e in episodes],
            "evaluation coverage/identity mismatch")
    for row in rows:
        e = row["episode"]
        require((row["reset_seed"], row["channel_seed"], row["motion_seed"], row["steps"]) ==
                (study.EVAL_BASE + 2000 + e, study.EVAL_BASE + 7000 + e,
                 study.EVAL_BASE + 3000 + e, HORIZON), "evaluation input binding mismatch")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_original_bindings(original, checkpoint, checkpoint_sha256=SOURCE_SHA256):
    """Read/validate metadata and identities only; no policy, environment or metric reduction."""
    original, checkpoint = Path(original), Path(checkpoint)
    require(original.is_absolute() and checkpoint.is_absolute(), "input paths must be absolute")
    require(original.is_dir(), "original evidence missing")
    frozen = verify_frozen_source()
    inv = inventory(original)
    require(inv["sha256"] == ORIGINAL_INVENTORY and inv["files"] == ORIGINAL_FILES,
            "original inventory mismatch")
    require(study.sha256(original / "summary.json") == ORIGINAL_SUMMARY_SHA,
            "original summary digest mismatch")
    require(study.sha256(original / "19703/D/summary.json") == D_SUMMARY_SHA,
            "unfinished D summary digest mismatch")
    require(checkpoint_sha256 == SOURCE_SHA256 and study.sha256(checkpoint) == SOURCE_SHA256,
            "parent checkpoint digest mismatch")
    batch = read_json(original / "summary.json")
    exit_record = read_json(original / "process-exit.json")
    manifest = read_json(original / "launch-manifest.json")
    require(exit_record.get("status") == "exited" and exit_record.get("exit_code") == -15
            and exit_record.get("termination") == "signal", "original terminal exit mismatch")
    require(manifest.get("sha") == ORIGINAL_SOURCE and manifest.get("node") == "local_linux",
            "original source/node mismatch")
    require(batch.get("launch_sha") == batch.get("source_sha") == ORIGINAL_SOURCE
            and batch.get("status") == "INCOMPLETE" and batch.get("active_cell") == "19703/D"
            and batch.get("b40") is None and not (original / "B40").exists(),
            "original interruption binding mismatch")
    pairs = [(m, a) for m in study.MASTERS for a in study.ARMS]
    require([(c["master"], c["arm"]) for c in batch["cells"]] == pairs[:-1],
            "original returned cell identities mismatch")
    cells = []
    for master, arm in pairs:
        directory = original / str(master) / arm
        cell = read_json(directory / "summary.json")
        require((cell["master"], cell["arm"], cell["launch_sha"], Path(cell["directory"])) ==
                (master, arm, ORIGINAL_SOURCE, directory), "original cell/source/path mismatch")
        n = len(range(EVALUATION)) if (master, arm) != (19703, "D") else D_EPISODES[0]
        require(cell["status"] == ("COMPLETE" if n == EVALUATION else "INCOMPLETE"),
                "original cell status mismatch")
        expected = study.expected_counts(arm, HORIZON, TRAIN, n)
        require(all(cell["counts"].get(k) == v for k, v in expected.items()),
                "original cell count mismatch")
        validate_rows(cell["rows"], master, arm, range(n))
        records = [json.loads(line) for line in (directory / "episodes.jsonl").read_text().splitlines()]
        require([identity(r) for r in records] ==
                [(master, arm, "train", e) for e in range(TRAIN)] +
                [(master, arm, "final_eval", e) for e in range(n)], "original stream coverage mismatch")
        require(records[TRAIN:] == cell["rows"], "original row/stream mismatch")
        for label in ("initial", "final"):
            record = cell[f"{label}_checkpoint"]
            p = directory / f"{label}.pt"
            require(Path(record["path"]) == p and study.sha256(p) == record["sha256"]
                    and p.stat().st_size == record["bytes"], "original checkpoint binding mismatch")
        cells.append(cell)
    require(cells[:-1] == batch["cells"], "original batch/cell metadata mismatch")
    require(cells[-1]["final_checkpoint"]["sha256"] == D_CHECKPOINT_SHA,
            "D final checkpoint digest mismatch")
    binding = dict(directory=str(original), source_sha=ORIGINAL_SOURCE, inventory=inv,
                   summary_sha256=ORIGINAL_SUMMARY_SHA, unfinished_d_summary_sha256=D_SUMMARY_SHA,
                   exit=exit_record, exit_sha256=study.sha256(original / "process-exit.json"),
                   source_paths_sha256=frozen, original_status="INCOMPLETE",
                   manifest_sha256=study.sha256(original / "launch-manifest.json"),
                   saved_evaluation_episodes=sum(len(c["rows"]) for c in cells),
                   unpersisted_native_steps_range=[0, HORIZON], resources_missing=["batch", "19703/D"])
    return dict(original=binding, batch=batch, cells=cells, unfinished_d=cells[-1],
                checkpoint_input=study.source_binding(checkpoint, checkpoint_sha256))


def parameter_hashes(actor, critic):
    return {key: study.tensor_hash(value) for key, value in parameter_snapshot(actor, critic).items()}


def load_final_d(checkpoint_bytes, cell):
    require(hashlib.sha256(checkpoint_bytes).hexdigest() == D_CHECKPOINT_SHA,
            "D final checkpoint digest mismatch")
    state = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    fields = dict(arm="D", master=19703, input_size=186, critic_size=526,
                  inherited_sha256=SOURCE_SHA256, correction_bound=.10, source_sha=ORIGINAL_SOURCE)
    require(isinstance(state, dict) and all(state.get(k) == v for k, v in fields.items()),
            "D final checkpoint metadata mismatch")
    actor, critic = build_arm(19703, "D")
    for name, network in (("actor", actor), ("critic", critic)):
        values = state.get(name)
        require(isinstance(values, dict) and set(values) == set(network.state_dict()),
                "D checkpoint parameter keys mismatch")
        for key, target in network.state_dict().items():
            value = values[key]
            require(isinstance(value, torch.Tensor) and value.dtype == torch.float32
                    and value.device.type == "cpu" and value.shape == target.shape
                    and bool(torch.isfinite(value).all()), "D checkpoint tensor contract mismatch")
        network.load_state_dict(values, strict=True)
    require(parameter_hashes(actor, critic) == cell["final_tensor_sha256"],
            "D final parameter witness mismatch")
    return actor, critic


def eval_counts(episodes):
    counts = study.expected_counts("B40", HORIZON, 0, episodes)
    return counts


def validate_recovery(summary, bindings):
    """Validate completion, exact disjoint slots, frozen parameters and zero fitting."""
    require(summary["original"] == bindings["original"], "recovery original binding mismatch")
    require(summary["status"] == "COMPLETE" and not summary["limits"], "recovery incomplete")
    d, b = summary["recovered_d"], summary["b40"]
    require(d["checkpoint_input"] == bindings["unfinished_d"]["final_checkpoint"],
            "recovery D checkpoint input mismatch")
    require(b["warm_start"] == bindings["checkpoint_input"], "recovery parent input mismatch")
    require(d["initial_tensor_sha256"] == bindings["unfinished_d"]["final_tensor_sha256"],
            "recovery trained D witness mismatch")
    for cell, master, arm, slots in ((d, 19703, "D", D_EPISODES), (b, 19451, "B40", B40_EPISODES)):
        require((cell["master"], cell["arm"], cell["status"]) == (master, arm, "COMPLETE")
                and not cell["limits"], "recovery cell identity/status mismatch")
        require(cell["launch_sha"] == summary["launch_sha"], "recovery cell source mismatch")
        validate_rows(cell["rows"], master, arm, slots)
        expected = eval_counts(len(slots))
        require(all(cell["counts"].get(k) == v for k, v in expected.items()),
                "recovery evaluation count mismatch")
        require(cell["counts"]["delivered_packets"] + cell["counts"]["censored_packets"] ==
                expected["team_steps"], "recovery transport count mismatch")
        require(cell["initial_tensor_sha256"] == cell["final_tensor_sha256"] ==
                cell["after_eval_tensor_sha256"], "recovery evaluation changed parameters")
        directory = Path(cell["directory"])
        require(sorted(p.name for p in (directory / "raw").iterdir()) ==
                [f"final_{e:02d}.npz" for e in slots], "recovery raw coverage mismatch")
        for row in cell["rows"]:
            path = directory / "raw" / f"final_{row['episode']:02d}.npz"
            require(Path(row["raw"]) == path and not path.is_symlink()
                    and study.sha256(path) == row["raw_sha256"], "recovery raw binding mismatch")
        records = [json.loads(line) for line in (directory / "episodes.jsonl").read_text().splitlines()]
        require(records == cell["rows"] and study.sha256(directory / "episodes.jsonl") ==
                cell["episode_stream_sha256"], "recovery row/stream binding mismatch")
        require((directory / "updates.jsonl").stat().st_size == 0 and
                study.sha256(directory / "updates.jsonl") == cell["update_stream_sha256"],
                "recovery update stream is not empty")
    saved = {identity(r) for c in bindings["cells"] for r in c["rows"]}
    recovered = {identity(r) for c in (d, b) for r in c["rows"]}
    require(not saved & recovered, "original/recovery coverage overlaps")
    require(sorted(r["episode"] for r in bindings["unfinished_d"]["rows"] + d["rows"]) ==
            list(range(EVALUATION)), "combined D coverage mismatch")
    actual = {k: d["counts"][k] + b["counts"][k] for k in study.new_counts()}
    require(summary["actual"] == actual, "recovery aggregate counts mismatch")
    if "original_inventory_after" in summary:
        require(summary["original_inventory_after"] == bindings["original"]["inventory"],
                "original evidence changed during recovery")
    return dict(original_evaluation_episodes=len(saved), recovery_evaluation_episodes=len(recovered),
                combined_evaluation_episodes=len(saved | recovered), overlaps=0,
                fits=0, optimizer_updates=0, native_team_steps=actual["team_steps"])


def run_d(out, launch_sha, checkpoint_bytes, original_cell, check):
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts, rows = study.new_counts(), []
    start = resource.getrusage(resource.RUSAGE_SELF)
    cell = dict(object="UAV-MESSAGE-CONTENT-B06-RECOVERED-D", directory=str(out), master=19703,
                arm="D", launch_sha=launch_sha, status="INCOMPLETE", limits=[], rows=rows, counts=counts,
                checkpoint_input=original_cell["final_checkpoint"], started_wall=time.time())
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        (out / "updates.jsonl").touch(exist_ok=False)

        def emit(row):
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            rows.append(row)
            study.write_json(out / "summary.json", cell)

        try:
            check()
            actor, critic = load_final_d(checkpoint_bytes, original_cell)
            cell["initial_tensor_sha256"] = parameter_hashes(actor, critic)
            cell["final_tensor_sha256"] = dict(cell["initial_tensor_sha256"])
            # Same constructor address as the interrupted trained cell; each reset is independently seeded.
            env = study.make_real(100000 * 19703 + 1000)
            counts["constructors"] += 1
            for e in D_EPISODES:
                collect_episode(env, actor, critic, "D", HORIZON, study.EVAL_BASE + 2000 + e,
                                study.EVAL_BASE + 7000 + e, generator(study.EVAL_BASE + 3000 + e),
                                dict(master=19703, arm="D", phase="final_eval", episode=e,
                                     motion_seed=study.EVAL_BASE + 3000 + e), counts, emit, check,
                                raw_path=out / "raw" / f"final_{e:02d}.npz")
            cell["after_eval_tensor_sha256"] = parameter_hashes(actor, critic)
            require(cell["after_eval_tensor_sha256"] == cell["initial_tensor_sha256"],
                    "recovery evaluation changed D parameters")
            cell["status"] = "COMPLETE"
        except Exception as error:
            cell["limits"].append(f"{type(error).__name__}: {error}")
        finally:
            cell["finished_wall"] = time.time()
            cell["resources"] = study.resources_since(start)
            cell["episode_stream_sha256"] = study.sha256(out / "episodes.jsonl")
            cell["update_stream_sha256"] = study.sha256(out / "updates.jsonl")
            study.write_json(out / "summary.json", cell)
    return cell


def run_recovery(out, launch_sha, original, checkpoint, checkpoint_sha256=SOURCE_SHA256,
                 seed=19701, *, start_usage=None):
    require(seed == 19701, "fixed recovery seed19701")
    start = start_usage or resource.getrusage(resource.RUSAGE_SELF)
    cpu_start = start.ru_utime + start.ru_stime

    def check():
        if time.process_time() - cpu_start >= CPU_LIMIT_SECONDS:
            raise TimeoutError("600 CPU-second recovery worker ceiling; no automatic extension/retry")

    check()
    bindings = load_original_bindings(original, checkpoint, checkpoint_sha256)
    check()
    out = Path(out).absolute()
    original = Path(original).resolve()
    require(out.resolve() != original and original not in out.resolve().parents,
            "recovery output must be separate from original evidence")
    controls = {"admission-preflight.json", "launch-manifest.json", "launch-status.json", "stdout.log", "stderr.log"}
    if out.exists() and any(p.name not in controls for p in out.iterdir()):
        raise FileExistsError("recovery scientific output already exists; no retry")
    out.mkdir(parents=True, exist_ok=True)
    batch = dict(object="UAV-MESSAGE-CONTENT-B06-EVAL-RECOVERY", launch_sha=launch_sha,
                 source_sha=launch_sha, original=bindings["original"], status="INCOMPLETE", limits=[],
                 recovered_d=None, b40=None, actual=study.new_counts(), started_wall=time.time(),
                 cpu_limit_seconds=CPU_LIMIT_SECONDS,
                 expected=dict(evaluation_episodes=len(D_EPISODES) + len(B40_EPISODES), fits=0,
                               optimizer_updates=0, constructors=2,
                               native_team_steps=(len(D_EPISODES) + len(B40_EPISODES)) * HORIZON))
    config = dict(seed=seed, launch_sha=launch_sha, horizon=HORIZON, dtype="float32", device="cpu",
                  node="local_linux", torch_threads=1, torch_interop_threads=1, blas_threads=1,
                  deployment="sampled_composed_policy", eval_world_base=study.EVAL_BASE + 2000,
                  eval_channel_base=study.EVAL_BASE + 7000, eval_motion_base=study.EVAL_BASE + 3000,
                  d_episodes=list(D_EPISODES), b40_episodes=list(B40_EPISODES),
                  parent_checkpoint=bindings["checkpoint_input"],
                  d_checkpoint=bindings["unfinished_d"]["final_checkpoint"],
                  original=bindings["original"], cpu_limit_seconds=CPU_LIMIT_SECONDS,
                  optimizer_constructed=False, automatic_retry=False)
    study.write_json(out / "config.json", config)
    batch["config_sha256"] = study.sha256(out / "config.json")
    study.write_json(out / "summary.json", batch)
    try:
        check()
        require(torch.get_num_threads() == torch.get_num_interop_threads() == 1,
                "recovery requires one Torch/interop thread")
        require(torch.get_default_dtype() == torch.float32, "recovery requires CPU float32")
        dpath = Path(bindings["unfinished_d"]["final_checkpoint"]["path"])
        batch["recovered_d"] = run_d(out / "19703/D", launch_sha, dpath.read_bytes(),
                                       bindings["unfinished_d"], check)
        if batch["recovered_d"]["status"] != "COMPLETE":
            raise RuntimeError("D recovery incomplete; B40 not started")
        check()
        batch["b40"] = study.run_cell(19451, "B40", out / "B40", Path(checkpoint).read_bytes(),
                                      checkpoint_sha256, factory=study.make_real, horizon=HORIZON,
                                      train=0, evaluation=len(B40_EPISODES), check=check,
                                      launch_sha=launch_sha, checkpoint_path=checkpoint)
        check()
        batch["status"] = "COMPLETE"
        batch["actual"] = {k: sum(c["counts"][k] for c in (batch["recovered_d"], batch["b40"]))
                           for k in study.new_counts()}
        batch["coverage"] = validate_recovery(batch, bindings)
    except Exception as error:
        batch["status"] = "INCOMPLETE"
        batch["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        cells = [c for c in (batch["recovered_d"], batch["b40"]) if c is not None]
        batch["actual"] = {k: sum(c["counts"][k] for c in cells) for k in study.new_counts()}
        batch["original_inventory_after"] = inventory(original)
        if batch["original_inventory_after"] != bindings["original"]["inventory"]:
            batch["status"] = "INCOMPLETE"
            batch["limits"].append("original evidence changed during recovery")
        batch["finished_wall"] = time.time()
        batch["resources"] = dict(study.resources_since(start),
                                  wall_seconds=batch["finished_wall"] - batch["started_wall"])
        files = [p for p in out.rglob("*") if p.is_file()]
        batch["resources"]["output_logical_bytes_before_final_summary"] = sum(p.stat().st_size for p in files)
        batch["resources"]["output_allocated_bytes_before_final_summary"] = sum(p.stat().st_blocks * 512 for p in files)
        batch["resources"]["output_size_scope"] = "recovery output tree, including launcher logs; before final summary rewrite"
        if time.process_time() - cpu_start >= CPU_LIMIT_SECONDS:
            batch["status"] = "INCOMPLETE"
            batch["limits"].append("600 CPU-second recovery worker ceiling reached during finalization")
        study.write_json(out / "summary.json", batch)
    return batch

"""One non-resumable complete selected package; durable failure frontier and costs."""

import json
from pathlib import Path
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from .codec import fit_ordinary, metric_scales, validate_book
from .collect import collect_episode
from .contract import EXPECTED, FIELDS, METRICS, PROGRAMS, SEEDS, artifact, increment, require, verify_artifact, write_json
from .inputs import load_inputs
from .offline import binding_replay, fit_learned, score
from .reader import full_read
from .receiver import load_receiver, parameter_hash
from .transport import ByteCodec


def save_book(path, book, scales, initial, history, method, seed, metric, dev_kl):
    validate_book(book, scales)
    import numpy as np
    np.savez_compressed(path, book=book.numpy(), scales=scales.numpy(), initial_book=initial.numpy())
    return dict(method=method, seed=seed, metric=metric, dev_kl=dev_kl, history=history,
                dictionary=artifact(path), installed_bytes=6168,
                dictionary_displacement=float((book - initial).norm()),
                dictionary_initial_norm=float(initial.norm()), dictionary_final_norm=float(book.norm()))


def load_book(record):
    import numpy as np
    with np.load(verify_artifact(record["dictionary"]), allow_pickle=False) as archive:
        book, scales = torch.from_numpy(archive["book"].copy()), torch.from_numpy(archive["scales"].copy())
    validate_book(book, scales)
    return book, scales


def choose_candidate(candidates):
    require([c["metric"] for c in candidates] == list(METRICS), "selection candidate order")
    return min(candidates, key=lambda c: (c["dev_kl"], METRICS.index(c["metric"])))


def resources(out, start_wall, start_cpu, include_bytes=True):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(wall_seconds=time.monotonic() - start_wall, process_cpu_seconds=time.process_time() - start_cpu,
                process_lifetime_cpu_seconds=usage.ru_utime + usage.ru_stime,
                process_lifetime_peak_rss_kib_linux=usage.ru_maxrss,
                child_lifetime_cpu_seconds=children.ru_utime + children.ru_stime,
                completed_children_peak_rss_kib_linux=children.ru_maxrss,
                child_cpu_scope="RUSAGE_CHILDREN lifetime user+system, waited-for descendants",
                child_rss_scope="RUSAGE_CHILDREN Linux maximum child high-water mark; not simultaneous total RSS",
                child_wall_seconds="unmeasured; external supervisor measures worker lifetime",
                output_bytes=sum(p.stat().st_size for p in Path(out).rglob("*") if p.is_file()) if include_bytes else None,
                torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                cpu_scope="RUSAGE_SELF since main entry, including admission and cold scientific imports; interpreter startup excluded",
                rss_scope="Linux RUSAGE_SELF lifetime high-water mark; not incremental by phase", gpu_seconds=0)


def run_batch(args, *, start_wall, start_cpu):
    out = args.out
    # The native launcher owns its already-created records. Refuse scientific reuse.
    require(all(not (out / name).exists() for name in
                ("summary.json", "progress.json", "reading.json", "fit-updates.jsonl", "raw", "dictionaries")),
            "B07 scientific output already exists; resume/retry is forbidden")
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    (out / "dictionaries").mkdir()
    counts = dict.fromkeys(EXPECTED, 0)
    summary = dict(object="UAV-MESSAGE-CONTENT-B07", schema_version=1, status="INCOMPLETE",
                   launch_sha=args.launch_sha, counts=counts, expected_counts=EXPECTED,
                   frontier=dict(phase="inputs"), fits=[], selection={}, native={}, limits=[],
                   configuration=dict(seeds=list(SEEDS), metrics=list(METRICS), horizon=256, old_fit=list(range(24)),
                                      old_dev=list(range(24, 32)), native_worlds=list(range(32)),
                                      dtype="float32", device="cpu", threads=1, lloyd_updates=25,
                                      learned_epochs=20, full_episodes_per_minibatch=4, adam_updates_per_fit=120,
                                      temperature=".25*(.025/.25)**(epoch/19)", source_fields=list(FIELDS),
                                      ties="lowest index; unit candidate on exact dev tie", sender="RR t%5",
                                      delays=[1, 5], channel_flip_probability=.05, fee=.001,
                                      pending="send-time public deterministic deadline, no ACK",
                                      compressed_packet_bytes=3, lossless_packet_bytes=26, beacon_bytes=2,
                                      native_seed_bases=[1981002000, 1981007000, 1981003000],
                                      policy_receiver_critic_updates=0, target_bank="fixed stored means",
                                      offline_minibatch_rows_per_tick=20, native_binding_dev_reader_rows_per_tick=5),
                   input_manifest=artifact(args.input_manifest),
                   inherited_cost=dict(policy_fits=33, predictor_fits=3, persisted_native_steps=4751360,
                                       interrupted_native_steps_range=[0, 256],
                                       separate_correction_compression_native_steps=57344,
                                       missing_original_b06_cpu="unknown", support_cpu="unknown"))
    actors, initial_hashes = {}, {}

    def progress():
        write_json(out / "progress.json", dict(status=summary["status"], frontier=summary["frontier"],
                                              counts=counts, resources=resources(out, start_wall, start_cpu, False)))

    def checkpoint():
        summary["resources"] = resources(out, start_wall, start_cpu)
        write_json(out / "summary.json", summary)
        progress()

    checkpoint()
    try:
        manifest, episodes = load_inputs(args.input_manifest, args.input_manifest_sha256,
                                         args.d_checkpoint, args.d_checkpoint_sha256,
                                         args.b_checkpoint, args.b_checkpoint_sha256)
        summary["inputs"] = manifest
        summary["frontier"] = dict(phase="load_receivers")
        checkpoint()
        started = time.process_time()
        actors = {kind: load_receiver(path, kind) for kind, path in (("D", args.d_checkpoint), ("B", args.b_checkpoint))}
        summary["cold_receiver_load_cpu_seconds"] = time.process_time() - started
        initial_hashes = {kind: parameter_hash(actor) for kind, actor in actors.items()}
        summary["frozen_initial_hashes"] = initial_hashes
        summary["deployment"] = dict(d_actor_parameters=sum(p.numel() for p in actors["D"].parameters()),
                                     d_actor_bytes=sum(p.numel() * p.element_size() for p in actors["D"].parameters()),
                                     installed_codec_bytes_per_device=6168, installed_codec_team_bytes=30840,
                                     lossless_bytes_per_episode=7168, compressed_bytes_per_episode=1280,
                                     amortization_ticks_broadcast=269, amortization_ticks_five_unicasts=1341)
        summary["frontier"] = dict(phase="binding_replay")
        checkpoint()
        summary["binding_replay"] = binding_replay(actors["D"], episodes, counts)
        checkpoint()
        samples = torch.cat([torch.from_numpy(e["packet"][:, list(FIELDS)]) for e in episodes[:24]])
        selected = {}
        for r, seed in enumerate(SEEDS, 1):
            ordinary, learned = [], []
            for metric in METRICS:
                scales = metric_scales(samples, metric)
                summary["frontier"] = dict(phase="fit", method="O", seed=seed, metric=metric)
                increment(counts, "fits_started")
                checkpoint()

                partial_book = out / "dictionaries" / f"active_{seed}_{metric}.npz"

                def preserve_fit(row, current_book, method):
                    import numpy as np
                    np.savez_compressed(partial_book, book=current_book.numpy(), scales=scales.numpy())
                    with (out / "fit-updates.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(dict(method=method, seed=seed, metric=metric, **row), allow_nan=False) + "\n")

                def ordinary_progress(row, current_book):
                    summary["frontier"]["lloyd_iteration"] = row["iteration"]
                    preserve_fit(row, current_book, "O")
                    progress()

                book, initial_book, history, distortion = fit_ordinary(samples, scales, seed, counts, ordinary_progress)
                increment(counts, "fits_completed")
                summary["frontier"] = dict(phase="dev", method="O", seed=seed, metric=metric)
                progress()
                dev = score(actors["D"], episodes[24:], book, scales, counts)
                candidate = save_book(out / "dictionaries" / f"O_{seed}_{metric}.npz", book, scales, initial_book,
                                      history, "O", seed, metric, dev)
                candidate["final_source_distortion"] = distortion
                ordinary.append(candidate)
                summary["fits"].append(candidate)
                partial_book.unlink()
                checkpoint()
                summary["frontier"] = dict(phase="fit", method="L", seed=seed, metric=metric)
                increment(counts, "fits_started")
                checkpoint()

                def learned_progress(row, current_book):
                    summary["frontier"].update(epoch=row["epoch"], batch=row["batch"])
                    # Persist every completed update/history; no automatic resume or retry.
                    preserve_fit(row, current_book, "L")
                    progress()

                learned_book, history = fit_learned(actors["D"], episodes[:24], book, scales, seed, counts, learned_progress)
                increment(counts, "fits_completed")
                summary["frontier"] = dict(phase="dev", method="L", seed=seed, metric=metric)
                progress()
                dev = score(actors["D"], episodes[24:], learned_book, scales, counts)
                candidate = save_book(out / "dictionaries" / f"L_{seed}_{metric}.npz", learned_book, scales, book,
                                      history, "L", seed, metric, dev)
                learned.append(candidate)
                summary["fits"].append(candidate)
                partial_book.unlink()
                checkpoint()
            for method, candidates in (("O", ordinary), ("L", learned)):
                program = f"{method}{r}"
                summary["selection"][program] = choose_candidate(candidates)
                selected[program] = load_book(summary["selection"][program])
            require(parameter_hash(actors["D"]) == initial_hashes["D"], "offline receiver mutation")
            checkpoint()
        for program in PROGRAMS:
            kind = "B" if program == "fullB" else "D"
            summary["native"][program] = []
            summary["frontier"] = dict(phase="native_constructor", program=program)
            checkpoint()
            started = time.process_time()
            env = make_real(1981002000)
            increment(counts, "constructors")
            summary.setdefault("constructor_cpu_seconds", {})[program] = time.process_time() - started
            try:
                for world in range(32):
                    summary["frontier"] = dict(phase="native", program=program, world=world)
                    checkpoint()
                    book, scales = selected.get(program, (None, None))
                    codec = ByteCodec(book, scales, counts)
                    row = collect_episode(env, actors[kind], kind, codec, world,
                                          out / "raw" / f"{program}_{world:02d}.npz", counts, progress)
                    summary["native"][program].append(row)
                    checkpoint()
            finally:
                env.close()
        summary["frontier"] = dict(phase="reader")
        checkpoint()
        reading = full_read(summary["native"], actors, selected, counts, progress)
        write_json(out / "reading.json", reading)
        summary["reading"] = artifact(out / "reading.json")
        summary["frozen_final_hashes"] = {kind: parameter_hash(actor) for kind, actor in actors.items()}
        require(summary["frozen_final_hashes"] == initial_hashes, "frozen receiver movement")
        require(all(counts.get(key) == value for key, value in EXPECTED.items()), "complete exposure/count mismatch")
        summary["total_actor_rows"] = sum(counts[k] for k in ("fit_actor_rows", "dev_actor_rows", "binding_actor_rows", "native_actor_rows", "reader_actor_rows"))
        require(summary["total_actor_rows"] == 4505600, "total forward rows")
        summary["status"] = "COMPLETE"
        summary["frontier"] = dict(phase="complete")
    except Exception as error:
        summary["limits"].append(f"{type(error).__name__}: {error}")
        summary["failure_frontier"] = dict(summary["frontier"])
    finally:
        if actors:
            summary["frozen_after_exit_hashes"] = {kind: parameter_hash(actor) for kind, actor in actors.items()}
        if (out / "fit-updates.jsonl").exists():
            summary["fit_update_stream"] = artifact(out / "fit-updates.jsonl")
        summary["partial_artifacts"] = [artifact(path) for path in
            [*sorted((out / "dictionaries").glob("active_*.npz")), *sorted((out / "raw").glob("*.partial.npz"))]]
        checkpoint()
    return summary

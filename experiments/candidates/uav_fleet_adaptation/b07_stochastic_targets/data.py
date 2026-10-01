"""Generate both frozen targets once from the paid, unchanged F0 row order."""
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_probabilities
from experiments.candidates.uav_local_history.b01.study import file_identity
from .assets import checked_path
from .contract import INPUT_ROOT, OLD_REL, array_digest
from .targets import build_targets


STAT_NAMES = ("tv_T_P", "tv_H_P", "entropy_P", "entropy_T", "entropy_H",
              "proxy_P", "proxy_T", "proxy_H", "flat_scores", "zeros_P", "zeros_T", "zeros_H",
              "mode_P", "mode_T", "mode_H", "c_index", "fallback", "parent_C_mass")


def target_statistics(parent, t, h, scores, c_index, fallback):
    entropies = [float(-np.sum(q[q > 0] * np.log(q[q > 0]))) for q in (parent, t, h)]
    return np.asarray([.5 * np.abs(t - parent).sum(), .5 * np.abs(h - parent).sum(), *entropies,
                       *(float(q @ scores) for q in (parent, t, h)), float(np.all(scores == scores[0])),
                       *(int(np.count_nonzero(q == 0)) for q in (parent, t, h)),
                       *(int(np.argmax(q)) for q in (parent, t, h)), c_index, fallback, parent[c_index]],
                      dtype=np.float64)


def statistics_summary(stats):
    if stats.ndim != 2 or stats.shape[1] != len(STAT_NAMES) or not np.isfinite(stats).all():
        raise ValueError("invalid complete target diagnostics")
    values = {name: stats[:, i] for i, name in enumerate(STAT_NAMES)}
    return dict(rows=len(stats), columns=list(STAT_NAMES),
                by_metric={k: dict(mean=float(v.mean()), min=float(v.min()), max=float(v.max()),
                                   quantiles=np.quantile(v, [0, .1, .5, .9, 1]).tolist())
                           for k, v in values.items()},
                flat_score_rows=int(values["flat_scores"].sum()),
                fallback_rows=int(values["fallback"].sum()),
                changed_T_modes=int(np.count_nonzero(values["mode_T"] != values["mode_P"])),
                changed_H_modes=int(np.count_nonzero(values["mode_H"] != values["mode_P"])),
                positive_T_TV_rows=int(np.count_nonzero(values["tv_T_P"] > 0)),
                positive_H_TV_rows=int(np.count_nonzero(values["tv_H_P"] > 0)),
                T_entropy_change_mean=float((values["entropy_T"] - values["entropy_P"]).mean()),
                H_entropy_change_mean=float((values["entropy_H"] - values["entropy_P"]).mean()),
                T_proxy_change_mean=float((values["proxy_T"] - values["proxy_P"]).mean()),
                H_proxy_change_mean=float((values["proxy_H"] - values["proxy_P"]).mean()),
                H_minus_T_proxy_min=float((values["proxy_H"] - values["proxy_T"]).min()),
                scope="All fixed F0 rows; target distributions/local proxy only, no sampled counterfactual or native-value claim")


def prepare_targets(parent, manifest, dataset, out, counts, *, root=INPUT_ROOT, progress=None):
    wall, cpu = time.perf_counter(), time.process_time()
    x, y, n = dataset
    total = len(x)
    arrays = dict(parent_logits=np.empty((total, 27), dtype=np.float32),
                  parent_probabilities=np.empty((total, 27), dtype=np.float64),
                  T=np.empty((total, 27), dtype=np.float64), H=np.empty((total, 27), dtype=np.float64),
                  statistics=np.empty((total, len(STAT_NAMES)), dtype=np.float64))
    count = torch.tensor([5], dtype=torch.int64)
    offset, mapping = 0, []
    for episode in manifest["rows"]:
        path = checked_path(root, OLD_REL / episode["raw"]["path"], episode["raw"])
        with np.load(path, allow_pickle=False) as archive:
            features = archive["features"].reshape(-1, 114)
            labels = archive["expert_action_index"].reshape(-1)
            scores = archive["expert_scores"].reshape(-1, 27)
            fallback = archive["expert_fallback"].reshape(-1)
        stop = offset + len(features)
        if (features.shape != (320, 114) or features.dtype != np.float32
                or labels.shape != (320,) or labels.dtype != np.int64
                or scores.shape != (320, 27) or scores.dtype != np.float64
                or not np.array_equal(features, x[offset:stop]) or not np.array_equal(labels, y[offset:stop])
                or not np.all(n[offset:stop] == 5)):
            raise ValueError("raw-to-paid-dataset identity mismatch")
        for local in range(len(features)):
            index = offset + local
            counts["parent_target_forward_calls"] += 1
            with torch.inference_mode():
                logits = parent(torch.from_numpy(features[local]).reshape(1, 114), count)[0].numpy().copy()
            counts["parent_target_forwards"] += 1
            p = categorical_probabilities(logits.astype(np.float64))
            counts["target_vector_calls"] += 2
            t, h = build_targets(p, scores[local], labels[local])
            counts["target_rows"] += 2
            arrays["parent_logits"][index], arrays["parent_probabilities"][index] = logits, p
            arrays["T"][index], arrays["H"][index] = t, h
            arrays["statistics"][index] = target_statistics(p, t, h, scores[local], int(labels[local]), bool(fallback[local]))
        mapping.append(dict(id=episode["id"], first=offset, stop=stop, phase=episode["phase"]))
        offset = stop
        if progress is not None:
            progress(dict(kind="targets", source_episode=episode["id"], archive_rows=offset))
    if offset != 81920:
        raise ValueError("target archive extent changed")
    path = out / "data" / "targets.npz"
    if path.exists():
        raise FileExistsError("target artifact already exists")
    np.savez_compressed(path, **arrays)
    identity = file_identity(path)
    identity["path"] = str(path.relative_to(out))
    record = dict(artifact=identity, mapping=mapping, rows=offset, statistics=statistics_summary(arrays["statistics"]),
                  array_sha256={k: array_digest(v) for k, v in arrays.items()},
                  source_data_sha256=array_digest(x, y, n), cpu_seconds=time.process_time() - cpu,
                  wall_seconds=time.perf_counter() - wall,
                  scope="one frozen one-row P0 forward per paid row; both FP64 targets, no C/native query")
    return arrays, record

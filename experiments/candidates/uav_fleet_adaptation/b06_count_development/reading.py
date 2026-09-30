"""Fixed world-clustered summaries, all native components and actual exposure."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.reading import (
    METRICS as BASE_METRICS, episode_metrics as base_metrics, numeric_summary, sum_counts,
)
from .contract import FINAL_COUNTS

METRICS = (*BASE_METRICS, "longest_zero_service_streak")


def episode_metrics(raw):
    result = base_metrics(raw)
    longest = current = 0
    for value in raw["served"]:
        current = current + 1 if value == 0 else 0
        longest = max(longest, current)
    result["longest_zero_service_streak"] = longest
    peers = np.asarray(raw["n_peers"])
    result["visible_peer_counts"] = np.bincount(peers.reshape(-1), minlength=7).tolist()
    result["more_than_four_peer_decisions"] = int(np.count_nonzero(peers > 4))
    result["no_visible_peer_decisions"] = int(np.count_nonzero(peers == 0))
    result["mean_visible_peers"] = float(peers.mean())
    result["zero_service_ticks"] = np.flatnonzero(np.asarray(raw["served"]) == 0).tolist()
    if "entropy" in raw:
        result["mean_entropy"] = float(np.asarray(raw["entropy"]).mean())
    return result


def cost_totals(rows, *, inflight=None):
    if inflight:
        partial = {key: inflight[key] for key in ("kind", "arm", "neural")}
        partial.update({name + "_counts": sum_counts(inflight[name + "_agents"])
                        for name in ("policy", "expert", "feature")})
        rows = [*rows, partial]
    full_c, helpers, neural, requests = [], [], [], []
    for row in rows:
        if row["kind"] == "acquisition":
            full_c.append(row["expert_counts"])
        elif row["arm"] in ("C", "Q"):
            full_c.append(row["policy_counts"])
        if row["neural"]:
            requests.append({"requests": row["policy_counts"]["requests"]})
        for c in (row["policy_counts"], row["feature_counts"]):
            helpers.append({k: v for k, v in c.items() if k.startswith("helper_")})
            neural.append({k: v for k, v in c.items() if k in ("neural_rows", "sampled_draws")})
    c, h = sum_counts(full_c), sum_counts(helpers)
    return dict(full_C=c, helper=h, neural=sum_counts(neural), student_requests=sum_counts(requests).get("requests", 0),
                controller_power_links=c.get("candidate_links", 0) + c.get("setup_links", 0)
                + h.get("helper_setup_links", 0) + h.get("helper_extreme_links", 0),
                scope=(("recorded complete and partial-episode counters; interrupted-call internals may be unmeasured; "
                        if inflight else "actual cache-miss work; ")
                       + "phase0 C execution supplies its one teacher label; includes separately declared H8 fixture"))


def validate_counts(counts, costs, protocol):
    expected = protocol.expected()
    keys = ("acquisition_episodes", "evaluation_episodes", "complete_episodes", "fixture_trajectories",
            "acquisition_native_steps", "evaluation_native_steps", "fixture_native_steps", "native_steps",
            "native_uav_ticks", "expert_labels", "optimizer_steps", "sample_presentations",
            "constructor_resets", "explicit_resets", "layout_refreshes", "native_dense_slots", "new_calibrations")
    for key in keys:
        if counts[key] != expected[key]:
            raise AssertionError(f"actual count mismatch {key}: {counts[key]} != {expected[key]}")
    for calls, completed in (("constructor_calls", "constructors"), ("explicit_reset_calls", "explicit_resets"),
                             ("layout_refresh_calls", "layout_refreshes"), ("native_step_calls", "native_steps")):
        if counts[calls] != counts[completed]:
            raise AssertionError("incomplete native call: " + calls)
    if counts["fits_started"] != 4 or counts["fits_completed"] != 4:
        raise AssertionError("four complete fits are required")
    if costs["full_C"]["requests"] != expected["full_C_requests"] or costs["student_requests"] != expected["student_requests"]:
        raise AssertionError("controller/actor request exposure changed")
    return True


def comparisons(rows, protocol):
    final = [r for r in rows if r["kind"] == "evaluation"]
    by_key = {(r["lineage"], r["arm"], r["n"], r["world"], r["tape"]): r for r in final}
    if len(by_key) != len(final) or len(final) != protocol.expected()["evaluation_episodes"]:
        raise ValueError("incomplete/duplicated final panel")

    def metric_value(lineage, arm, n, world, metric):
        if arm == "C":
            return float(by_key[None, "C", n, world, None][metric])
        actual_lineage = None if arm == "Q" else lineage
        actual_arm = "P" if arm == "Bstar" and lineage == 1 else arm
        return float(np.mean([by_key[actual_lineage, actual_arm, n, world, tape][metric] for tape in (0, 1)]))

    def summarize(a):
        a = np.asarray(a, dtype=np.float64)
        return dict(numeric_summary(a), differences=a.tolist(), positive=int(np.count_nonzero(a > 0)),
                    negative=int(np.count_nonzero(a < 0)), zero=int(np.count_nonzero(a == 0)))

    pairs = [("M", "F"), ("M", "P"), ("F", "P"), ("M", "Bstar"), ("F", "Bstar"), ("Bstar", "P")]
    pairs += [(a, b) for a in ("M", "F", "P", "Bstar") for b in ("C", "Q")]
    result = dict(worlds=list(protocol.evaluation_worlds), counts=list(FINAL_COUNTS), by_lineage={},
                  primary_equal_N4_N6_both_lineages={}, lineage_targets={},
                  scope="32 shared world clusters; average two tapes first; two fixed inherited lineage blocks and equal N4/N6 target, not training-population confirmation")
    targets = {}
    for lineage in (0, 1):
        result["by_lineage"][str(lineage)] = {}
        for n in FINAL_COUNTS:
            item = dict(means={}, paired={})
            for arm in ("P", "F", "M", "Bstar", "C", "Q"):
                item["means"][arm] = {metric: numeric_summary([
                    metric_value(lineage, arm, n, w, metric) for w in protocol.evaluation_worlds]) for metric in METRICS}
            for a, b in pairs:
                item["paired"][a + "-" + b] = {metric: summarize([
                    metric_value(lineage, a, n, w, metric) - metric_value(lineage, b, n, w, metric)
                    for w in protocol.evaluation_worlds]) for metric in METRICS}
            result["by_lineage"][str(lineage)][str(n)] = item
        targets[lineage] = {metric: np.asarray([
            np.mean([metric_value(lineage, "M", n, w, metric) - metric_value(lineage, "F", n, w, metric)
                     for n in (4, 6)]) for w in protocol.evaluation_worlds]) for metric in METRICS}
        result["lineage_targets"][str(lineage)] = {m: summarize(a) for m, a in targets[lineage].items()}
    result["primary_equal_N4_N6_both_lineages"] = {
        m: summarize((targets[0][m] + targets[1][m]) / 2.) for m in METRICS}
    result["zero_service_episodes"] = [{k: r[k] for k in
                                        ("id", "lineage", "arm", "n", "world", "tape", "zero_service_steps", "zero_service_ticks")}
                                       for r in final if r["zero_service_steps"]]
    result["identity_reuse"] = dict(Bstar1="P1 at each N/world/tape", ordinary="C and Q shared across lineages within identical N/world/tape")
    return result

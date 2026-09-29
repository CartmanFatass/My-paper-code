"""T4: P3 interaction reader and commitment collector (disposition item 5).

Synthetic acceptance on tables with the collector's schema (256 episodes x 50 commitments =
12,800 rows, the declared geometry) plus a tiny-spec collection smoke on a technical fit
(hidden 32, 2 lanes, 1 rollout; worlds from the training-world law, never a panel world).
"""
from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.coupled_host_joint_skills_stage1 import interaction_reader as reader

@pytest.fixture(scope="module", autouse=True)
def single_thread_blas():
    """Pin numpy's OpenBLAS to one thread for this module (the reader's own entry point sets
    OPENBLAS_NUM_THREADS=1 before importing numpy; inside pytest numpy is already loaded, and on
    a loaded node multi-threaded BLAS made one reading ~13x slower).  Restored afterwards."""
    import ctypes

    setter = getter = None
    try:
        with open("/proc/self/maps", encoding="utf-8") as maps:
            paths = {line.split()[-1] for line in maps if "openblas" in line.lower() and "/" in line}
        for path in paths:
            lib = ctypes.CDLL(path)
            for suffix in ("64_", ""):
                setter = getattr(lib, "openblas_set_num_threads" + suffix, None)
                getter = getattr(lib, "openblas_get_num_threads" + suffix, None)
                if setter is not None and getter is not None:
                    break
            if setter is not None and getter is not None:
                break
    except OSError:
        setter = getter = None
    previous = getter() if getter is not None else None
    if setter is not None:
        setter(1)
    yield
    if setter is not None and previous is not None:
        setter(int(previous))


N_SEEDS = 40
SYNTH_BOOT = 1000

#: Declared synthetic generator (report these with the pass rates).
SYNTH = {
    "lanes": 16, "episodes": 16, "per_episode": 50,
    "state_ar": 0.8,              # latent pre-commitment state, AR(1) across commitments
    "noise_ar": 0.6,              # within-episode AR(1) noise of segment_mean_r
    "noise_sd": 0.04,             # marginal SD of the AR(1) noise
    "episode_sd": 0.03,           # episode random effect
    "additive_label_sd": 0.05,    # agent-index-specific label effects g_i(z) ~ N(0, sd)
    "label_state_slope": 1.5,     # state-dependence of the label logits
    "relay_prob": 0.35,           # a routed UAV's path goes through another routed UAV
    "pair_effect": 0.03,          # positive case: +.03 when the team holds labels 1 and 2
}


def synthetic_table(seed, *, effect=0.0, scale=1.0, drop_label=None, relay_effect=0.0):
    rng = np.random.default_rng(seed)
    lanes, episodes, per = SYNTH["lanes"], SYNTH["episodes"], SYNTH["per_episode"]
    n = lanes * episodes * per
    lane = np.repeat(np.arange(lanes), episodes * per)
    episode = np.tile(np.repeat(46 + np.arange(episodes), per), lanes)
    t0 = np.tile(np.arange(per) * 10, lanes * episodes)
    # latent state per commitment, AR(1) within episode
    state = np.zeros(n)
    noise = np.zeros(n)
    innovation = np.sqrt(1 - SYNTH["noise_ar"] ** 2) * SYNTH["noise_sd"]
    for start in range(0, n, per):
        s = rng.normal()
        e = rng.normal(0, SYNTH["noise_sd"])
        for k in range(per):
            s = SYNTH["state_ar"] * s + np.sqrt(1 - SYNTH["state_ar"] ** 2) * rng.normal()
            e = SYNTH["noise_ar"] * e + innovation * rng.normal()
            state[start + k], noise[start + k] = s, e
    episode_effect = np.repeat(rng.normal(0, SYNTH["episode_sd"], lanes * episodes), per)
    routed = rng.random((n, 6)) < 1 / (1 + np.exp(-(0.5 + 0.8 * state[:, None])))
    relay_matrix = np.zeros((n, 6, 6), dtype=bool)
    for row in range(n):
        members = np.flatnonzero(routed[row])
        for j in members:
            if members.size > 1 and rng.random() < SYNTH["relay_prob"]:
                i = rng.choice(members[members != j])
                relay_matrix[row, i, j] = True
    relay = relay_matrix.any(axis=2)
    serving = rng.poisson(4 + 2 * (state[:, None] > 0), size=(n, 6)).astype(np.int16)
    c_bh = np.clip(0.4 + 0.1 * state + 0.05 * rng.normal(size=n), 0, 1)
    sd = np.clip(0.25 + 0.05 * state + 0.03 * rng.normal(size=n), 0, 1.0186)
    # state- and role-dependent labels
    base = rng.normal(0, 1, (6, 6))
    slope = rng.normal(0, SYNTH["label_state_slope"], (6, 6))
    role = rng.normal(0, 1, (6, 6))
    logits = base[None] + slope[None] * state[:, None, None] + role[None] * relay[:, :, None]
    for label in np.atleast_1d(drop_label if drop_label is not None else []):
        logits[..., int(label)] = -np.inf
    prob = np.exp(logits - logits.max(axis=2, keepdims=True))
    prob /= prob.sum(axis=2, keepdims=True)
    labels = (prob.cumsum(axis=2) > rng.random((n, 6, 1))).argmax(axis=2)
    team_logits = rng.normal(0, 1, 6)[None] + rng.normal(0, 1, 6)[None] * state[:, None]
    team_prob = np.exp(team_logits - team_logits.max(axis=1, keepdims=True))
    team_prob /= team_prob.sum(axis=1, keepdims=True)
    team = (team_prob.cumsum(axis=1) > rng.random((n, 1))).argmax(axis=1)
    g = rng.normal(0, SYNTH["additive_label_sd"], (6, 6))
    y = (0.2 + 0.3 * c_bh + 0.4 * sd + 0.02 * t0 / 500 + relay @ rng.normal(0, .01, 6)
         + routed @ rng.normal(0, .01, 6) + serving @ rng.normal(0, .002, 6)
         + g[np.arange(6)[None, :], labels].sum(axis=1) + episode_effect + noise)
    counts = np.stack([(labels == z).sum(axis=1) for z in range(6)], axis=1)
    y = y + effect * ((counts[:, 1] >= 1) & (counts[:, 2] >= 1))
    if relay_effect:
        pair = np.einsum("nij,ni,nj->n", relay_matrix.astype(float), (labels == 1).astype(float),
                         (labels == 2).astype(float))
        y = y + relay_effect * (pair > 0)
    return {"lane": lane, "episode": episode, "t0": t0, "c_bh_t0": c_bh, "sd_t0": sd,
            "routed": routed, "relay": relay, "serving": serving, "agent_labels": labels.astype(np.int8),
            "team_label": team.astype(np.int8), "relay_matrix": relay_matrix,
            "segment_mean_r": scale * y}


# ------------------------------------------------------------------------------ design facts


def test_count_basis_squares_are_spanned_and_products_are_full_rank():
    table = synthetic_table(11)
    x_r = reader.reduced_block(table)
    counts = np.stack([(table["agent_labels"] == z).sum(axis=1) for z in range(6)], axis=1).astype(float)
    products = np.column_stack([counts[:, z] * counts[:, w] for z, w in reader.COUNT_PAIRS])
    squares = counts ** 2
    rank = np.linalg.matrix_rank
    assert rank(np.column_stack([x_r, products])) - rank(x_r) == 15
    assert rank(np.column_stack([x_r, products, squares])) - rank(x_r) == 15
    routed_total = table["routed"].sum(axis=1).astype(float)
    assert rank(np.column_stack([x_r, routed_total])) == rank(x_r)  # n_routed is in R's span


def test_added_block_definitions_on_a_hand_example():
    table = {key: value[:1].copy() for key, value in synthetic_table(3).items()}
    table["agent_labels"][0] = [1, 2, 2, 0, 5, 1]
    matrix = np.zeros((1, 6, 6), dtype=bool)
    matrix[0, 1, 0] = True   # UAV1 (label 2) relays for UAV0 (label 1)
    matrix[0, 4, 3] = True   # UAV4 (label 5) relays for UAV3 (label 0)
    matrix[0, 1, 5] = True   # UAV1 (label 2) relays for UAV5 (label 1)
    table["relay_matrix"] = matrix
    table["relay"] = matrix.any(axis=2)
    block = dict(zip(reader.ADDED_NAMES, reader.added_block(table)[0]))
    assert block["n1*n2"] == 4 and block["n0*n5"] == 1 and block["n3*n4"] == 0
    assert block["rs_2to1"] == 2 and block["rs_5to0"] == 1 and block["rs_1to2"] == 0
    assert block["rp_2_5"] == 1 and block["rp_2_2"] == 0 and sum(v for k, v in block.items() if k.startswith("rp_")) == 1
    assert len(reader.ADDED_NAMES) == 72 and len(set(reader.ADDED_NAMES)) == 72


def test_gram_route_equals_direct_refits_for_bootstrap_draws():
    table = synthetic_table(5, effect=0.01)
    reading = reader.read_table(table, n_boot=20)
    assert reading["decision"] in ("supported", "unsupported")
    # Direct refits of a few draws, the slow way.
    n = table["segment_mean_r"].size
    group, fold, keys, _, _ = reader.groups_and_folds(table)
    r_std, r_zero = reader.standardise(reader.reduced_block(table)[:, 1:])
    x_r = np.column_stack([np.ones(n), r_std[:, ~r_zero]])
    added = reader.added_block(table)
    _, supported = reader.block_support(added, reader.ADDED_NAMES, group, n)
    x_f = np.column_stack([x_r, reader.standardise(added)[0][:, supported]])
    y = table["segment_mean_r"].astype(float)
    fitted = x_r @ np.linalg.lstsq(x_r, y, rcond=None)[0]
    weights = reader.rademacher(len(keys), 20)
    # Recompute the reading's null the slow way for draws 1, 7 and 20.
    null = []
    for b in (1, 7, 20):
        y_star = fitted + (y - fitted) * weights[b - 1][group]
        null.append(reader.direct_cv_delta(x_r, x_f, y_star, fold, reader.K_FOLDS)[0])
    fast = reader.read_table(table, n_boot=20)  # deterministic: same draws
    assert fast["omnibus"]["delta"] == pytest.approx(fast["omnibus"]["direct_refit_delta"], rel=1e-9)
    grams_r = reader.fold_grams(x_r, _basis(x_r, y, group, len(keys)), fold, reader.K_FOLDS)
    grams_f = reader.fold_grams(x_f, _basis(x_r, y, group, len(keys)), fold, reader.K_FOLDS)
    assert set(grams_f[3]) == {"normal_equations"}
    for value, b in zip(null, (1, 7, 20)):
        v = np.concatenate([[1.0], weights[b - 1]])[:, None]
        delta = (reader.fold_mse(grams_r[0], grams_r[1], v) - reader.fold_mse(grams_f[0], grams_f[1], v)).mean()
        assert delta == pytest.approx(value, rel=1e-8, abs=1e-14)


def _basis(x_r, y, group, n_groups):
    fitted = x_r @ np.linalg.lstsq(x_r, y, rcond=None)[0]
    basis = np.zeros((y.size, 1 + n_groups))
    basis[:, 0] = fitted
    basis[np.arange(y.size), 1 + group] = y - fitted
    return basis


def test_fold_assignment_is_fixed_and_hash_based():
    table = synthetic_table(1)
    _, fold, keys, fold_of_group, digest = reader.groups_and_folds(table)
    again = reader.groups_and_folds(synthetic_table(2))
    assert digest == again[4] and np.array_equal(fold_of_group, again[3])
    assert len(keys) == 256 and set(fold_of_group.tolist()) == set(range(8))
    for g, (lane, episode) in enumerate(keys):
        rows = (table["lane"] == lane) & (table["episode"] == episode)
        assert np.all(fold[rows] == fold_of_group[g])


# ------------------------------------------------------------------------------ acceptance


@pytest.fixture(scope="module")
def null_readings():
    return [reader.read_table(synthetic_table(1000 + s), n_boot=SYNTH_BOOT, direct_check=False)
            for s in range(N_SEEDS)]


@pytest.fixture(scope="module")
def positive_readings():
    return [reader.read_table(synthetic_table(2000 + s, effect=SYNTH["pair_effect"]), n_boot=SYNTH_BOOT,
                              direct_check=False) for s in range(N_SEEDS)]


def test_additive_null_pass_rate_at_most_ten_percent(null_readings):
    assert all(r["decision"] in ("supported", "unsupported") for r in null_readings)
    rate = np.mean([r["decision"] == "supported" for r in null_readings])
    print(f"\nadditive-null pass rate {rate:.3f} over {N_SEEDS} seeds")
    assert rate <= 0.10


def test_additive_null_products_only_pass_rate_within_five_percent(null_readings):
    assert all(r["decision_products_only"] in ("supported", "unsupported") for r in null_readings)
    rate = np.mean([r["decision_products_only"] == "supported" for r in null_readings])
    print(f"\nadditive-null products-only pass rate {rate:.3f} over {N_SEEDS} seeds")
    assert rate <= 0.05


def test_known_pair_interaction_passes_at_least_eighty_percent(positive_readings):
    rate = np.mean([r["decision"] == "supported" for r in positive_readings])
    print(f"\npair-interaction (+{SYNTH['pair_effect']}) pass rate {rate:.3f} over {N_SEEDS} seeds")
    assert rate >= 0.80


def test_known_pair_interaction_products_only_passes(positive_readings):
    rate = np.mean([r["decision_products_only"] == "supported" for r in positive_readings])
    print(f"\npair-interaction products-only pass rate {rate:.3f} over {N_SEEDS} seeds")
    assert rate >= 0.80


def test_one_label_never_used_is_listed_unsupported_not_zero():
    reading = reader.read_table(synthetic_table(7, drop_label=4), n_boot=50)
    assert reading["decision"] in ("supported", "unsupported") and reading["omnibus"] is not None
    unsupported = reading["design"]["missing_support"]["unsupported"]
    assert {"n0*n4", "n4*n5", "rs_4to1", "rp_4_4"} <= set(unsupported)
    assert unsupported["n0*n4"] == {"nonzero_rows": 0, "nonzero_episodes": 0, "supported": False}
    assert not set(unsupported) & set(reading["design"]["full_columns_used"])
    rank = reading["design"]["rank"]
    assert rank["products_supported"] == 10 and rank["added_increment"] == rank["added_supported_columns"]
    assert reading["decision_products_only"] in ("supported", "unsupported")
    assert "agent0_label4" in reading["design"]["reduced_columns_dropped_zero_variance"]


def test_fewer_than_ten_supported_products_is_unreadable():
    reading = reader.read_table(synthetic_table(7, drop_label=[3, 4]), n_boot=50)
    assert reading["design"]["rank"]["products_supported"] == 6
    assert reading["decision"] == "unreadable" and reading["omnibus"] is None
    assert reading["decision_products_only"] == "unreadable" and reading["omnibus_products_only"] is None
    assert "label-count products supported" in reading["reason"]


def test_support_rule_is_fixed_on_the_design():
    assert reader.support_threshold_rows(12_800) == 128
    assert reader.support_threshold_rows(100) == 8 and reader.support_threshold_rows(1_000) == 10
    table = synthetic_table(3015, relay_effect=0.03)
    shifted = dict(table, segment_mean_r=table["segment_mean_r"] * -3.0 + 1.0)
    a = reader.read_table(table, n_boot=20, direct_check=False)["design"]
    b = reader.read_table(shifted, n_boot=20, direct_check=False)["design"]
    assert a["added_support"] == b["added_support"] and a["full_columns_used"] == b["full_columns_used"]


def test_seed_3015_rp_5_5_is_unsupported_not_unreadable():
    reading = reader.read_table(synthetic_table(3015, relay_effect=0.03), n_boot=200)
    assert reading["decision"] in ("supported", "unsupported")
    unsupported = reading["design"]["missing_support"]["unsupported"]
    assert unsupported["rp_5_5"]["nonzero_rows"] == 0 and "rs_5to5" in unsupported
    assert reading["design"]["rank"]["added_increment"] == len(reading["design"]["full_columns_used"]) - \
        len(reading["design"]["reduced_columns_used"])


def test_reward_scaling_leaves_the_decision_unchanged():
    for seed, effect in ((21, 0.0), (22, SYNTH["pair_effect"]), (23, 0.01)):
        base = reader.read_table(synthetic_table(seed, effect=effect), n_boot=200)
        scaled = reader.read_table(synthetic_table(seed, effect=effect, scale=10.0), n_boot=200)
        assert base["decision"] == scaled["decision"]
        assert base["decision_products_only"] == scaled["decision_products_only"]
        assert base["design"]["full_columns_used"] == scaled["design"]["full_columns_used"]
        assert scaled["omnibus"]["delta"] == pytest.approx(100 * base["omnibus"]["delta"], rel=1e-7)
        assert scaled["omnibus"]["null_quantile_95"] == pytest.approx(
            100 * base["omnibus"]["null_quantile_95"], rel=1e-7)
        assert scaled["omnibus"]["null_fraction_below_observed"] == base["omnibus"]["null_fraction_below_observed"]


def test_reading_json_fields_and_placebo(tmp_path):
    reading = reader.read_table(synthetic_table(31), n_boot=100)
    assert reading["reading_wording"] == reader.READING_WORDING
    for key in ("delta", "delta_per_fold", "null_quantile_95", "null_summary", "passed"):
        assert key in reading["omnibus"], key
    assert reading["placebo"]["readable"] and "delta" in reading["placebo"]
    assert reading["folds"]["assignment_sha256"] and reading["bootstrap"]["draws"] == 100
    rank = reading["design"]["rank"]
    assert rank["added_increment"] == rank["added_supported_columns"] and rank["products_supported"] >= 10
    assert reading["omnibus_products_only"]["decision"] == reading["decision_products_only"]
    assert reading["design"]["support_rule"] == reader.SUPPORT_RULE_TEXT
    assert np.isfinite(reading["design"]["condition_number"]["full"])
    reader.write_json(tmp_path / "r.json", reading)
    assert json.loads((tmp_path / "r.json").read_text())["decision"] == reading["decision"]


# ------------------------------------------------------------------------------ CLI guards


def _admission_calls(module_path):
    source = Path(module_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    inside = [node for node in ast.walk(main) if isinstance(node, ast.Call)
              and getattr(node.func, "id", None) == "require_admission"]
    everywhere = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                  and getattr(node.func, "id", None) == "require_admission"]
    return source, inside, everywhere


def test_require_admission_exactly_once_inside_main_of_both_entry_points():
    from experiments.candidates.coupled_host_joint_skills_stage1 import collect_commitments as collector

    for module in (reader, collector):
        source, inside, everywhere = _admission_calls(module.__file__)
        assert source.count('require_admission(__file__, direction="coupled_host_joint_skills_stage1")') == 1
        assert len(inside) == 1 and len(everywhere) == 1


def test_reader_cli_admission_and_smoke_guard(tmp_path, monkeypatch):
    calls = []

    def refuse(*args, **kwargs):
        calls.append(kwargs)
        raise RuntimeError("not admitted")

    monkeypatch.setattr(reader, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="not admitted"):
        reader.main(["--table", "x.npz", "--out", str(tmp_path / "o"), "--launch-sha", "abc"])
    assert calls == [{"direction": "coupled_host_joint_skills_stage1"}] and not (tmp_path / "o").exists()
    assert reader.main(["--table", "x.npz", "--out", "/tmp/elsewhere", "--smoke-no-admission"]) == 2


def test_snapshot_paths_map_back_to_the_checkout():
    snap = Path("/home/u/repo/.git/hmasd-launch-sources/abc123")
    assert reader._data_root(snap) == Path("/home/u/repo")
    assert reader.resolve_input(snap / "runs/d/t/commitments.npz") == Path("/home/u/repo/runs/d/t/commitments.npz")


# ------------------------------------------------------------------------------ collector smoke


def test_collect_commitments_on_a_tiny_checkpoint(tmp_path):
    import torch

    from experiments.candidates.coupled_host_joint_skills_stage1 import collect_commitments as collector
    from experiments.candidates.coupled_host_joint_skills_stage1 import runner
    from experiments.candidates.coupled_host_joint_skills_stage1.adapter import PANEL_WORLD_SET, training_world_seed
    from experiments.candidates.coupled_host_joint_skills_stage1.configuration import DEFAULT_SPEC, SEEDS

    tiny = replace(DEFAULT_SPEC, train_lanes=2, eval_lanes=1, rollouts=1, panels=(1,), hidden_size=32,
                   n_heads=2, n_layers=1, ppo_epochs=1, sequence_batch_size=64, coordinator_batch_size=64,
                   torch_threads=1, dev_worlds=(9201,), holdout_worlds=(9202,), probe_panel_worlds=(9203,),
                   probe_rollouts=1)
    seed = SEEDS["H"][0]
    fit = tmp_path / "fit"
    assert runner.run_fit(fit, "H", seed, "technical-fixture", {"sha": "technical-fixture"}, tiny) == 0
    checkpoint = fit / "checkpoint_01.pt"
    before = collector.file_sha256(checkpoint)
    out = tmp_path / "collect"
    code = collector.run_collection(checkpoint, seed, tiny, out, rollouts=1, lanes=2, launch_sha="t", smoke=True)
    assert code == 0, (out / "error.txt").read_text() if (out / "error.txt").exists() else ""
    assert collector.file_sha256(checkpoint) == before
    meta = json.loads((out / "meta.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["checkpoint_matches_fit_summary"] is True
    assert meta["rows"] == 100 and meta["counters"]["team_steps"] == 1000
    assert meta["worlds"] == [[training_world_seed(seed, lane, 2) for lane in range(2)]]
    assert not set(meta["worlds"][0]) & PANEL_WORLD_SET
    assert meta["frozen"]["digest_before"] == meta["frozen"]["digest_after"]
    assert not any(meta["frozen"]["optimizer_calls"].values())
    assert meta["frozen"]["rng_digest_before"] == meta["frozen"]["rng_digest_after"]
    assert meta["load"]["faithful_load"]["tensors_bitwise_equal"]
    check = meta["structural_zero_check"]
    assert check["passed"] and check["rows"] == 100
    assert check["max_abs_action_difference"] == {"deterministic": 0.0, "sampled": 0.0}
    assert check["control_individual_label_change_max_abs_difference"] > 0
    with np.load(out / "commitments.npz") as data:
        table = {key: data[key] for key in data.files}
    assert table["state"].shape == (100, 133) and table["observations"].shape == (100, 6, 90)
    assert table["actions"].shape == (100, 10, 6, 3) and table["rewards"].shape == (100, 10)
    assert table["structural_actor_hidden"].shape == (100, 6, 32)
    for lane in range(2):
        rows = table["lane"] == lane
        assert rows.sum() == 50 and np.array_equal(table["t0"][rows], np.arange(0, 500, 10))
    assert np.all(table["episode"] == 2) and set(table["world"].tolist()) == set(meta["worlds"][0])
    assert np.allclose(table["segment_mean_r"], table["rewards"].mean(axis=1))
    assert np.all((table["agent_labels"] >= 0) & (table["agent_labels"] < 6))
    assert np.array_equal(table["relay"], table["relay_matrix"].any(axis=2))
    assert np.all(table["n_routed"] == table["routed"].sum(axis=1))
    assert np.all(~table["relay"] | table["routed"])
    norms = np.linalg.norm(table["executed_actions"], axis=-1)
    assert np.all(norms <= 1 + 1e-5)
    # the reader accepts the table's schema (too few episodes for K = 8 folds: unreadable)
    reading = reader.read_table(reader.load_table(out / "commitments.npz"), n_boot=10)
    assert reading["decision"] == "unreadable"
    # a second attempt into the same --out is refused before any collection
    with pytest.raises(ValueError, match="existing summary"):
        collector.run_collection(checkpoint, seed, tiny, out, rollouts=1, lanes=2, smoke=True)
    # wrong seed / non-final checkpoint are refused at load
    bad = tmp_path / "bad"
    assert collector.run_collection(checkpoint, SEEDS["H"][1], tiny, bad, rollouts=1, lanes=2, smoke=True) == 1
    assert "seed" in json.loads((bad / "summary.json").read_text())["failure"]


def test_collector_cli_guards(tmp_path, monkeypatch):
    from experiments.candidates.coupled_host_joint_skills_stage1 import collect_commitments as collector
    from experiments.candidates.coupled_host_joint_skills_stage1.configuration import SEEDS

    calls = []

    def refuse(*args, **kwargs):
        calls.append(kwargs)
        raise RuntimeError("not admitted")

    monkeypatch.setattr(collector, "require_admission", refuse)
    monkeypatch.setattr(collector, "run_collection", lambda *a, **k: calls.append("effects"))
    with pytest.raises(RuntimeError, match="not admitted"):
        collector.main(["--checkpoint", "runs/x/checkpoint_45.pt", "--seed", str(SEEDS["H"][0]),
                        "--area-size", "5000", "--out", str(tmp_path / "o"), "--launch-sha", "abc"])
    assert calls == [{"direction": "coupled_host_joint_skills_stage1"}]
    for argv in (["--seed", str(SEEDS["SET"][0]), "--launch-sha", "abc"],
                 ["--seed", str(SEEDS["H"][0])],
                 ["--seed", str(SEEDS["H"][0]), "--launch-sha", "abc", "--rollouts", "2"]):
        with pytest.raises(SystemExit):
            collector.main(["--checkpoint", "c.pt", "--area-size", "5000", "--out", str(tmp_path / "p"), *argv])
    assert len(calls) == 1
    worlds = collector.collection_worlds(SEEDS["H"][0], collector.DEFAULT_SPEC, 16, 16)
    assert worlds[0][0] == 300000 + 201 * 100 + 46 * 10000 and len({w for row in worlds for w in row}) == 256
    assert collector.smoke_refusal(worlds, "/tmp/elsewhere") is not None
    assert collector.smoke_refusal(worlds, collector.ROOT / "temp" / "x") is None
    assert collector.smoke_refusal([[1000]], collector.ROOT / "temp" / "x") is not None

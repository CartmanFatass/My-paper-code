"""Focused acceptance of the ACVC_MATCHED_PACKAGE_COMPARISON_B01 binding and paired publication: the block
identities (MASTER 28731 / namespace 38731), object, card and plans reach the protocol on the C route and the
transfer runner on the M route before any recipe import or seed parsing; the M binder never touches the C
route; the paired reducer computes P = mean64[J(F(C)) - J(F(M))] with the fixed labels, exactly the six
supports, the rowwise identity, exact boundaries and dependency-specific INCOMPLETE. Synthetic only; no
native environment, fit or profiling."""
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

PATTERNS = ("cluster_mappo_comparison_b0", "m_deployment_transfer_b0", "matched_package_comparison_b0")


def _names():
    return [n for n in list(sys.modules) if any(s in n for s in PATTERNS)]


@pytest.fixture
def fresh_modules():
    saved = {n: sys.modules.pop(n) for n in _names()}
    yield
    for n in _names():
        sys.modules.pop(n)
    sys.modules.update(saved)


def _entry():
    return importlib.import_module("run_acvc_matched_package_comparison_b01")


def make_summary(arm, scores, master=28731, namespace=38731, obj="ACVC_MATCHED_PACKAGE_COMPARISON_B01"):
    panels = {key: dict(complete=True, available_episodes=64, scores_J=list(map(float, s)), mean_J=float(np.mean(s)))
              for key, s in scores.items()}
    counts = dict(train_episodes=4096, train_team_steps=4096 * 256, rollouts=2048, final_checkpoints=1)
    if arm == "C":
        counts["optimizer_steps"] = 8192
    else:
        counts.update(actor_optimizer_steps=8192, critic_optimizer_steps=8192)
    return dict(object=obj, arm=arm, master=master, evaluation_namespace=namespace, fit_complete=True,
                launch_sha=f"sha-{arm}", counts=counts, panels=panels,
                interventions={k: {"opportunities": 1} for k in scores})


def pair(base):
    c = make_summary("C", {"C": base, "F": base + .05, "dwell": base + .01})
    m = make_summary("M", {"M": base + .02, "F(M)": base + .03, "dwell(M)": base + .025})
    return c, m


def test_c_route_binds_the_protocol_and_keeps_the_recipe_and_arms(fresh_modules):
    e = _entry()
    p, t = e.p, e.t
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28331, 38331)  # importing leaves the modules as recorded
    assert (t.MASTER, t.EVALUATION_NAMESPACE) == (28531, 38531)
    frozen = {name: getattr(p, name) for name in e.FROZEN}
    arms_before = dict(p.ARMS)
    e.bind_c()
    assert (p.MASTER, p.EVALUATION_NAMESPACE, p.OBJECT, p.CARD) == (28731, 38731, e.OBJECT, e.CARD)
    assert p.CARD.endswith("ACVC_MATCHED_PACKAGE_COMPARISON_B01_PROSPECTIVE_CARD_20260915.md")
    assert p.PLANS == {"C": 2600, "M": 1200}
    assert p.ARMS == arms_before and p.ARMS["C"] == ("C", "F", "dwell")  # the transfer binder was not applied
    assert (t.MASTER, t.EVALUATION_NAMESPACE) == (28531, 38531)  # the M route's globals are untouched
    for name, value in frozen.items():
        assert getattr(p, name) is value
    assert frozen["TRAIN_EPISODES"] == 4096 and frozen["EVAL_EPISODES"] == 64 and frozen["HORIZON"] == 256
    assert frozen["UPSTREAM_SHA"] == "de66d7a4b23fac2513f56f96f73b3f5cb96695ac"
    span = range(0, 50000)
    new = {100000 * 28731 + k for k in span} | {100000 * 38731 + k for k in span}
    for master, namespace in e.PRIOR_IDENTITIES:
        old = {100000 * master + k for k in span} | {100000 * namespace + k for k in span}
        assert not (old & new)
    e.bind_c()  # idempotent
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28731, 38731)


def test_m_route_binds_the_transfer_runner_and_its_binder_carries_the_protocol(fresh_modules):
    e = _entry()
    p, t = e.p, e.t
    e.bind_m()
    assert (t.MASTER, t.EVALUATION_NAMESPACE, t.OBJECT, t.CARD) == (28731, 38731, e.OBJECT, e.CARD)
    assert t.ORDINARY_PLAN_SECONDS == 1200
    t.bind_object()
    assert (p.MASTER, p.EVALUATION_NAMESPACE, p.OBJECT) == (28731, 38731, e.OBJECT)
    assert p.ARMS == {"M": ("M", "F(M)", "dwell(M)")} and p.PLANS == {"M": 1200}
    assert t.b01.execute_m is t.execute_m_with_panels
    assert set(t.CONSTRUCTOR_OFFSETS.values()) == {65, 66, 67}
    e.bind_m()  # idempotent after the first binding
    assert (t.MASTER, t.EVALUATION_NAMESPACE) == (28731, 38731)


def test_dispatch_reaches_the_runners_with_bound_identities(fresh_modules, monkeypatch):
    e = _entry()
    p = e.p
    seen = []

    def fake_run(output, arm, launch_sha, upstream_root=None):
        seen.append(dict(arm=arm, master=p.MASTER, namespace=p.EVALUATION_NAMESPACE, object=p.OBJECT,
                         plans=dict(p.PLANS), arms=dict(p.ARMS), upstream=upstream_root, launch_sha=launch_sha))
        return 0

    monkeypatch.setattr(e.b01, "run", fake_run)
    assert e.main(["--arm", "C", "--seed", "28731", "--output", "outc", "--launch-sha", "abc"]) == 0
    assert seen[-1]["arm"] == "C" and seen[-1]["master"] == 28731 and seen[-1]["namespace"] == 38731
    assert seen[-1]["object"] == e.OBJECT and seen[-1]["plans"] == {"C": 2600, "M": 1200}
    assert seen[-1]["arms"]["C"] == ("C", "F", "dwell") and seen[-1]["upstream"] is None
    assert e.main(["--arm", "M", "--seed", "28731", "--output", "outm", "--launch-sha", "abc",
                   "--on-policy-root", "up"]) == 0
    assert seen[-1]["arm"] == "M" and seen[-1]["master"] == 28731 and seen[-1]["namespace"] == 38731
    assert seen[-1]["object"] == e.OBJECT and seen[-1]["plans"] == {"M": 1200}
    assert seen[-1]["arms"] == {"M": ("M", "F(M)", "dwell(M)")} and str(seen[-1]["upstream"]) == "up"


def test_wrong_seed_missing_inputs_and_early_import_are_refused(fresh_modules):
    e = _entry()
    for argv in (["--arm", "C", "--seed", "28331", "--output", "x", "--launch-sha", "a"],
                 ["--arm", "M", "--seed", "28631", "--output", "x", "--launch-sha", "a", "--on-policy-root", "u"],
                 ["--arm", "M", "--seed", "28731", "--output", "x", "--launch-sha", "a"],  # no on-policy root
                 ["--seed", "28731", "--output", "x", "--launch-sha", "a"],  # no arm
                 ["--arm", "C", "--seed", "28731", "--output", "x"],  # no launch sha
                 ["--arm", "C", "--seed", "28731", "--output", "x", "--launch-sha", "a", "--on-policy-root", "u"],
                 ["--mode", "reduce", "--output", "x", "--c-summary", "c"],  # no m summary
                 ["--mode", "reduce", "--output", "x", "--c-summary", "c", "--m-summary", "m", "--arm", "C"]):
        with pytest.raises(SystemExit):
            e.main(argv)
    sys.modules["experiments.candidates.acvc.cluster_mappo_comparison_b01.c_fit"] = object()
    with pytest.raises(RuntimeError):
        e.bind_c()
    with pytest.raises(RuntimeError):
        e.bind_m()


def test_reducer_primary_supports_identity_and_boundaries(fresh_modules):
    e = _entry()
    base = np.linspace(.2, .5, 64)
    c, m = pair(base)
    out = e.reduce_matched(c, m)
    assert out["complete"] and out["eligible_fits"] == {"C": True, "M": True}
    assert out["primary"] == "P" and out["training_instances"] == 2
    assert out["P"]["reading"] == "F_C_ABOVE_MEI" and out["P"]["mean_J"] == pytest.approx(.02)
    assert (out["P"]["left"], out["P"]["right"]) == ("F(C)", "F(M)")
    assert set(out["supports"]) == {"C-M", "F(C)-C", "F(M)-M", "F(C)-own-dwell(C)", "F(M)-own-dwell(M)",
                                    "own-dwell(C)-own-dwell(M)"}
    s = out["supports"]
    assert s["C-M"]["reading"] == "DOWN" and s["C-M"]["mean_J"] == pytest.approx(-.02)
    assert s["F(C)-C"]["reading"] == "UP" and s["F(C)-C"]["mean_J"] == pytest.approx(.05)
    assert s["F(M)-M"]["reading"] == "WITHIN_MEI" and s["F(M)-M"]["mean_J"] == pytest.approx(.01)
    assert s["F(C)-own-dwell(C)"]["mean_J"] == pytest.approx(.04)
    assert s["F(M)-own-dwell(M)"]["reading"] == "WITHIN_MEI"
    assert s["own-dwell(C)-own-dwell(M)"]["reading"] == "DOWN"
    assert out["decomposition_identity"]["max_abs_residual_J"] < 1e-12
    assert out["panels"]["F(C)"]["source_key"] == "F" and out["panels"]["own-dwell(M)"]["source_key"] == "dwell(M)"
    assert all(v["eligible_for_bound_comparison"] for v in out["panels"].values())
    # Signed orientation and the exact boundaries of the primary (zero-based vectors so the mean difference is
    # exactly delta in float64; the rule is strict outside the inclusive +-.01 band on the unrounded mean).
    zero = np.zeros(64)
    for delta, label in ((.01, "WITHIN_MEI"), (-.01, "WITHIN_MEI"), (.01 + 1e-9, "F_C_ABOVE_MEI"),
                         (-.01 - 1e-9, "F_M_ABOVE_MEI"), (-.03, "F_M_ABOVE_MEI"), (0.0, "WITHIN_MEI")):
        c2 = make_summary("C", {"C": zero, "F": zero + delta, "dwell": zero})
        m2 = make_summary("M", {"M": zero, "F(M)": zero, "dwell(M)": zero})
        out2 = e.reduce_matched(c2, m2)
        assert out2["P"]["mean_J"] == delta and out2["P"]["reading"] == label, delta
    assert out2["P"]["conditional_SE_J"] == pytest.approx(0.0) and out2["P"]["zero"] == 64


def test_reducer_is_incomplete_per_dependency_without_imputation(fresh_modules):
    e = _entry()
    base = np.linspace(.2, .5, 64)
    # A missing dwell panel does not erase P; only the dwell supports are incomplete.
    c, m = pair(base)
    del m["panels"]["dwell(M)"]
    out = e.reduce_matched(c, m)
    assert out["complete"] and out["P"]["reading"] == "F_C_ABOVE_MEI"
    assert out["supports"]["F(M)-own-dwell(M)"]["reading"] == "INCOMPLETE"
    assert out["supports"]["own-dwell(C)-own-dwell(M)"]["reading"] == "INCOMPLETE"
    assert out["supports"]["C-M"]["complete"] and out["decomposition_identity"] is not None
    # A missing F(M) makes P incomplete without erasing the within-arm C supports.
    c, m = pair(base)
    m["panels"]["F(M)"]["scores_J"][3] = float("nan")
    out = e.reduce_matched(c, m)
    assert not out["complete"] and out["P"]["reading"] == "INCOMPLETE" and out["P"]["mean_J"] is None
    assert out["supports"]["F(C)-C"]["complete"] and out["supports"]["C-M"]["complete"]
    assert out["supports"]["F(M)-M"]["reading"] == "INCOMPLETE" and out["decomposition_identity"] is None
    # A short panel is not a panel.
    c, m = pair(base)
    c["panels"]["F"]["scores_J"] = c["panels"]["F"]["scores_J"][:63]
    assert e.reduce_matched(c, m)["P"]["reading"] == "INCOMPLETE"
    # Mismatched identities make the whole fit ineligible.
    c, m = pair(base)
    stale = make_summary("M", {"M": base, "F(M)": base, "dwell(M)": base}, master=28631, namespace=38631,
                         obj="ACVC_M_DEPLOYMENT_TRANSFER_B02")
    out = e.reduce_matched(c, stale)
    assert out["eligible_fits"] == {"C": True, "M": False} and out["P"]["reading"] == "INCOMPLETE"
    assert out["supports"]["F(C)-C"]["complete"] and not out["supports"]["C-M"]["complete"]
    out = e.reduce_matched(None, None)
    assert out["eligible_fits"] == {"C": False, "M": False} and not out["complete"]


def test_reduce_cli_writes_the_paired_summary(fresh_modules, tmp_path):
    e = _entry()
    base = np.linspace(.2, .5, 64)
    c, m = pair(base)
    (tmp_path / "c.json").write_text(json.dumps(c), encoding="utf-8")
    (tmp_path / "m.json").write_text(json.dumps(m), encoding="utf-8")
    assert e.main(["--mode", "reduce", "--c-summary", str(tmp_path / "c.json"), "--m-summary",
                   str(tmp_path / "m.json"), "--output", str(tmp_path / "out")]) == 0
    out = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert (out["object"], out["master"], out["evaluation_namespace"]) == (e.OBJECT, 28731, 38731)
    assert out["card"] == e.CARD and out["P"]["reading"] == "F_C_ABOVE_MEI" and out["MEI_J"] == .01
    assert out["plans_seconds"] == {"C": 2600, "M": 1200} and out["plan_is_cap"] is False
    assert out["inputs"]["C"]["launch_sha"] == "sha-C" and out["inputs"]["M"]["arm"] == "M"
    assert out["inputs"]["C"]["summary_path"].endswith("c.json") and out["inputs"]["M"]["summary_path"].endswith("m.json")


def test_launch_scripts_name_the_runner_arm_and_seed():
    d = ROOT / "experiments/candidates/acvc/matched_package_comparison_b01"
    c = (d / "launch_c.sh").read_text(encoding="utf-8")
    m = (d / "launch_m.sh").read_text(encoding="utf-8")
    for text in (c, m):
        assert "scripts/run_acvc_matched_package_comparison_b01.py" in text and "--seed 28731" in text
        assert 'admit-memory --out "$output/admission.json" &&' in text
        for old in ("28331", "28431", "28531", "28631"):
            assert old not in text
    assert "--arm C" in c and '[ "$#" -eq 2 ]' in c and "on-policy-root" not in c
    assert "--arm M" in m and '[ "$#" -eq 3 ]' in m and '--on-policy-root "$upstream"' in m

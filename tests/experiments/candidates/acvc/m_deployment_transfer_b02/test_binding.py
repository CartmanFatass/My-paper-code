"""Focused acceptance of the ACVC_M_DEPLOYMENT_TRANSFER_B02 binding change: the new identities (MASTER
28631 / namespace 38631) reach the protocol, the B01 transfer runner's parser, the panel constructors and
the wrapped evaluator's namespace argument, and the reducer before use; B01's frozen recipe values and its
own module are untouched. Synthetic only; no native environment, fit or profiling."""
import importlib
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

PATTERNS = ("cluster_mappo_comparison_b0", "m_deployment_transfer_b0")


def _names():
    return [n for n in list(sys.modules) if any(s in n for s in PATTERNS)]


@pytest.fixture
def fresh_modules():
    saved = {n: sys.modules.pop(n) for n in _names()}
    yield
    for n in _names():
        sys.modules.pop(n)
    sys.modules.update(saved)


def make_summary(scores, master=28631, namespace=38631, obj="ACVC_M_DEPLOYMENT_TRANSFER_B02"):
    panels = {arm: dict(complete=True, available_episodes=64, scores_J=list(s), mean_J=float(np.mean(s)))
              for arm, s in scores.items()}
    counts = dict(train_episodes=4096, train_team_steps=4096 * 256, rollouts=2048, final_checkpoints=1,
                  actor_optimizer_steps=8192, critic_optimizer_steps=8192)
    return dict(object=obj, arm="M", master=master, evaluation_namespace=namespace, fit_complete=True,
                counts=counts, panels=panels, interventions={"F(M)": {"opportunities": 3}})


def test_b02_binding_reaches_the_protocol_and_keeps_the_frozen_recipe(fresh_modules):
    b02 = importlib.import_module("run_acvc_m_deployment_transfer_b02")
    t, p = b02.t, b02.t.p
    assert (t.MASTER, t.EVALUATION_NAMESPACE) == (28531, 38531)  # importing B02 leaves B01's module as recorded
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28331, 38331)
    frozen = {name: getattr(p, name) for name in t.FROZEN}
    b02.bind_b02()
    assert (t.MASTER, t.EVALUATION_NAMESPACE, t.OBJECT, t.CARD) == (28631, 38631, b02.OBJECT, b02.CARD)
    t.bind_object()
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28631, 38631)
    assert p.OBJECT == "ACVC_M_DEPLOYMENT_TRANSFER_B02" and p.CARD.endswith("B02_PROSPECTIVE_CARD_20260915.md")
    assert p.ARMS == {"M": ("M", "F(M)", "dwell(M)")} and p.PLANS == {"M": 1200}
    for name, value in frozen.items():
        assert getattr(p, name) is value
    assert frozen["TRAIN_EPISODES"] == 4096 and frozen["EVAL_EPISODES"] == 64 and frozen["HORIZON"] == 256
    assert frozen["UPSTREAM_SHA"] == "de66d7a4b23fac2513f56f96f73b3f5cb96695ac"
    assert t.b01.execute_m is t.execute_m_with_panels
    assert set(t.CONSTRUCTOR_OFFSETS.values()) == {65, 66, 67}
    span = range(0, 50000)
    new = {100000 * 28631 + k for k in span} | {100000 * 38631 + k for k in span}
    for master, namespace in b02.PRIOR_IDENTITIES:
        old = {100000 * master + k for k in span} | {100000 * namespace + k for k in span}
        assert not (old & new)
    b02.bind_b02()  # idempotent
    assert (t.MASTER, t.EVALUATION_NAMESPACE) == (28631, 38631)


def test_early_recipe_import_and_wrong_seed_are_refused(fresh_modules):
    b02 = importlib.import_module("run_acvc_m_deployment_transfer_b02")
    with pytest.raises(SystemExit):  # the B01 seed is not admitted once B02 is bound
        b02.main(["--seed", "28531", "--output", "x", "--launch-sha", "abc", "--on-policy-root", "y"])
    with pytest.raises(SystemExit):
        b02.main(["--seed", "28631", "--output", "x", "--launch-sha", "abc"])  # no on-policy root
    sys.modules["experiments.candidates.acvc.cluster_mappo_comparison_b01.mappo"] = object()
    with pytest.raises(RuntimeError):
        b02.bind_b02()


def test_panels_are_constructed_and_evaluated_under_the_bound_namespace(fresh_modules, monkeypatch):
    """The two wrapped panels take their constructor seeds and evaluator namespace from the bound protocol."""
    b02 = importlib.import_module("run_acvc_m_deployment_transfer_b02")
    t, p = b02.t, b02.t.p
    b02.bind_b02()
    t.bind_object()
    seen = dict(constructors=[], namespaces=set(), arms=[], episodes=0, trained=0)

    class Actor:
        def load_state_dict(self, state):
            assert state == {"actor": "weights"}

    fake_m = types.SimpleNamespace(
        MASTER=p.MASTER, EVALUATION_NAMESPACE=p.EVALUATION_NAMESPACE,
        configuration=lambda: ("args", None),
        make_policy=lambda args: (types.SimpleNamespace(actor=Actor()), None),
        torch=types.SimpleNamespace(load=lambda *a, **k: {"actor": {"actor": "weights"}}),
    )
    sys.modules["experiments.candidates.acvc.cluster_mappo_comparison_b01.mappo"] = fake_m
    monkeypatch.setattr(t, "_B01_EXECUTE_M", lambda *a: seen.__setitem__("trained", seen["trained"] + 1))
    monkeypatch.setattr(p, "make_cluster", lambda seed: seen["constructors"].append(seed) or "env")
    monkeypatch.setattr(p, "EVAL_EPISODES", 2)

    def fake_eval(policy, env, episode, counts, emit, arm, namespace, horizon):
        seen["namespaces"].add(namespace)
        seen["arms"].append(arm)
        seen["episodes"] += 1
        assert horizon == p.HORIZON and env == "env"

    monkeypatch.setattr(t, "evaluate_wrapped", fake_eval)
    summary = dict(checkpoint="final.pt", counts=dict(post_fit_loads=1, environment_constructors=3,
                                                     unscored_constructor_resets=3))
    t.execute_m_with_panels("out", summary, lambda row: None, lambda row: None, lambda: None)
    assert seen["trained"] == 1
    assert seen["constructors"] == [100000 * 38631 + 66, 100000 * 38631 + 67]
    assert seen["namespaces"] == {38631} and seen["episodes"] == 4
    assert seen["arms"] == ["F(M)", "F(M)", "dwell(M)", "dwell(M)"]
    assert summary["counts"]["post_fit_loads"] == 3 and summary["counts"]["environment_constructors"] == 5
    assert "deployment_laws" in summary
    # A recipe module that did not receive the bound identities is refused.
    fake_m.MASTER = 28531
    with pytest.raises(RuntimeError):
        t.execute_m_with_panels("out", summary, lambda row: None, lambda row: None, lambda: None)


def test_reduce_cli_reads_a_b02_summary_and_refuses_the_b01_identities(fresh_modules, tmp_path):
    b02 = importlib.import_module("run_acvc_m_deployment_transfer_b02")
    base = np.linspace(.2, .5, 64)
    good = make_summary({"M": base, "F(M)": base + .05, "dwell(M)": base + .01})
    (tmp_path / "b02.json").write_text(json.dumps(good), encoding="utf-8")
    assert b02.main(["--mode", "reduce", "--m-summary", str(tmp_path / "b02.json"),
                     "--output", str(tmp_path / "out")]) == 0
    out = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert (out["object"], out["master"], out["evaluation_namespace"]) == ("ACVC_M_DEPLOYMENT_TRANSFER_B02", 28631, 38631)
    assert out["card"] == b02.CARD and out["training_instances"] == 1 and out["primary"] == "T_F"
    assert out["eligible_fit"] and out["complete"]
    assert out["contrasts"]["T_F"]["reading"] == "TRANSFERS" and out["contrasts"]["T_F"]["mean_J"] == pytest.approx(.05)
    assert out["contrasts"]["U"]["mean_J"] == pytest.approx(.04)
    stale = make_summary({"M": base, "F(M)": base + .05, "dwell(M)": base + .01}, master=28531, namespace=38531,
                         obj="ACVC_M_DEPLOYMENT_TRANSFER_B01")
    (tmp_path / "b01.json").write_text(json.dumps(stale), encoding="utf-8")
    assert b02.main(["--mode", "reduce", "--m-summary", str(tmp_path / "b01.json"),
                     "--output", str(tmp_path / "out_stale")]) == 0
    stale_out = json.loads((tmp_path / "out_stale" / "summary.json").read_text(encoding="utf-8"))
    assert not stale_out["eligible_fit"]
    assert all(v["reading"] == "INCOMPLETE" for v in stale_out["contrasts"].values())


def test_launch_script_names_the_b02_runner_and_seed():
    text = (ROOT / "experiments/candidates/acvc/m_deployment_transfer_b02/launch.sh").read_text(encoding="utf-8")
    assert "scripts/run_acvc_m_deployment_transfer_b02.py" in text and "--seed 28631" in text
    assert 'admit-memory --out "$output/admission.json" &&' in text and '[ "$#" -eq 3 ]' in text
    assert "28531" not in text

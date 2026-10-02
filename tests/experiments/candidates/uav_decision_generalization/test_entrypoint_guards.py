"""Pure launcher/admission checks; run under the configured control-plane Python."""
import ast
import json
from pathlib import Path
import sys
import pytest

pytestmark=pytest.mark.skipif(sys.version_info<(3,11),reason='launcher uses tomllib; configured control-plane interpreter required')


def test_actual_launcher_guard_contract():
    from scripts.hmasd_launch import _validate_guard_contract
    root=Path.cwd()/'experiments/candidates/uav_decision_generalization'
    for name in ('run_b01_learning.py','run_b01_native.py','read_b01.py'):
        _validate_guard_contract(root/name,'uav_decision_generalization')


@pytest.mark.parametrize('name',['run_b01_learning','run_b01_native','read_b01'])
def test_admission_refused_before_input_effects(name,monkeypatch):
    import importlib
    from scripts import hmasd_admission
    runner=importlib.import_module('experiments.candidates.uav_decision_generalization.'+name)
    calls=[]
    def refused(*args,**kw):
        calls.append('admission')
        raise hmasd_admission.AdmissionRefused('fixture refusal')
    def unexpected(*args,**kw):
        raise AssertionError('scientific/external input reached before admission')
    monkeypatch.setattr(hmasd_admission,'require_admission',refused)
    from experiments.candidates.uav_decision_generalization import phases
    monkeypatch.setattr(phases,'accepted_store',unexpected)
    inputs={'run_b01_learning':['dataset-input'],'run_b01_native':['fit-input','dataset-input','learning-input'],
            'read_b01':['fit-input','fresh-input','dataset-input','learning-input']}[name]
    argv=['--seed','0','--launch-sha','a'*40,'--out-dir','/unused/out']
    for option in ['budget-ledger',*inputs]:
        argv.extend(['--'+option,'/unused/'+option,'--'+option+'-sha256','b'*64])
    with pytest.raises(hmasd_admission.AdmissionRefused,match='fixture refusal'):
        runner.main(argv)
    assert calls==['admission']

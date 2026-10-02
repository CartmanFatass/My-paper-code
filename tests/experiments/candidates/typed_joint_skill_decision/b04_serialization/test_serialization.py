"""One bounded pass: six synthetic attempts/five target calls; no original replay."""
import ast
import contextlib
import hashlib
import json
import os
from pathlib import Path
import resource
import sys

import pytest
from experiments.candidates.typed_joint_skill_decision.b04_serialization import records as r,run

ROOT=Path(__file__).resolve().parents[5]
PACKAGE=ROOT/'experiments/candidates/typed_joint_skill_decision/b04_serialization'
CALLS={'synthetic_attempts':0,'actual_target_calls':0}


@pytest.fixture(scope='module',autouse=True)
def finite_test_allocation():
    yield
    used=resource.getrusage(resource.RUSAGE_SELF)
    cpu=used.ru_utime+used.ru_stime
    print(f"synthetic_attempts={CALLS['synthetic_attempts']} actual_target_calls={CALLS['actual_target_calls']} original_calls=0 process_cpu={cpu:.6f}s")
    assert CALLS['actual_target_calls']<=CALLS['synthetic_attempts']<=8
    assert cpu<=5


@pytest.fixture(autouse=True)
def no_live_signal_changes(monkeypatch):
    monkeypatch.setattr(run,'protected',contextlib.nullcontext)


@pytest.fixture(scope='module')
def encoder():
    original=r.target(ROOT,r.TARGET)
    def call(value):
        CALLS['synthetic_attempts']+=1;CALLS['actual_target_calls']+=1
        assert CALLS['synthetic_attempts']<=8
        return original(value)
    return call


def state():
    return {'attempted':0,'completed':0,'encoded_bytes':0,'rolling':hashlib.sha256()}


def after(n):
    calls=[0]
    def guard():
        if calls[0]>=n:raise run.Stop('synthetic_cap')
        calls[0]+=1
    return guard


def invoke(tmp_path,lines,encoder,guard,s):
    with (tmp_path/'attempts.bin').open('xb',buffering=0) as attempts,\
         (tmp_path/'checkpoints.jsonl').open('xb',buffering=0) as checkpoints:
        return run.replay(lines,encoder,attempts,checkpoints,guard,s)


def test_fresh_decode_every_cycle(tmp_path,encoder):
    seen=[];line=b'{"a":[1]}\n';s=state()
    def mutating(value):
        seen.append(value);result=encoder(value);value['a'].append(9);return result
    with pytest.raises(run.Stop,match='synthetic_cap'):
        invoke(tmp_path,[line],mutating,after(2),s)
    assert len(seen)==2 and seen[0] is not seen[1] and seen[1]['a']==[1,9]
    assert s['completed']==2 and s['rolling'].hexdigest()==hashlib.sha256(line*2).hexdigest()


def test_original_order_ordinals_and_newline_digest(tmp_path,encoder):
    seen=[];lines=[b'{"x":1}\n',b'{"x":2}\n'];s=state()
    def observing(value):seen.append(value['x']);return encoder(value)
    with pytest.raises(run.Stop):invoke(tmp_path,lines,observing,after(2),s)
    assert seen==[1,2] and s['completed']==s['attempted']==2
    assert (tmp_path/'attempts.bin').read_bytes()==r.ORDINAL.pack(1)+r.ORDINAL.pack(2)
    assert s['rolling'].hexdigest()==hashlib.sha256(b''.join(lines)).hexdigest()
    checkpoint=json.loads((tmp_path/'checkpoints.jsonl').read_bytes())
    assert checkpoint['completed']==2 and checkpoint['cycles_complete']==1


def test_exact_mismatch_stops_at_first_attempt(tmp_path,encoder):
    s=state();line=b'{"x":1}\n'
    with pytest.raises(run.ByteMismatch):
        invoke(tmp_path,[line],lambda value:encoder(value).rstrip(b'\n'),after(2),s)
    assert s['attempted']==1 and s['completed']==0
    assert s['mismatch']['actual_bytes']==len(line)-1
    assert s['mismatch']['expected_sha256']==hashlib.sha256(line).hexdigest()
    assert (tmp_path/'attempts.bin').stat().st_size==8


def test_exception_retains_attempt_without_claiming_completion(tmp_path):
    s=state()
    def failing(value):
        CALLS['synthetic_attempts']+=1
        raise RuntimeError('synthetic original failure')
    with pytest.raises(RuntimeError,match='original failure'):
        invoke(tmp_path,[b'{"x":1}\n'],failing,after(2),s)
    assert s['attempted']==1 and s['completed']==0 and s['encoded_bytes']==0
    assert s['rolling'].hexdigest()==hashlib.sha256().hexdigest()


def test_fixed_manifest_and_source_rejection(tmp_path):
    path=ROOT/'docs/research/candidates/typed_joint_skill_decision/b04_serialization/INPUT.json'
    value=r.manifest(path,r.sha(path));assert value['input']==r.INPUT and value['limits']==r.LIMITS
    with pytest.raises(ValueError,match='SHA256'):r.manifest(path,'0'*64)
    bad={**value,'limits':{**value['limits'],'cycles':1001}};copy=tmp_path/'bad.json'
    copy.write_bytes(r.json_bytes(bad))
    with pytest.raises(ValueError,match='contract'):r.manifest(copy,r.sha(copy))
    with pytest.raises(ValueError,match='target source'):
        r.target(ROOT,{**r.TARGET,'sha256':'0'*64})
    with pytest.raises(ValueError,match='contained'):r.contained(ROOT,'../escape')


def test_admission_precedes_target_limits_and_output(tmp_path,monkeypatch):
    from scripts import hmasd_admission,hmasd_launch
    hmasd_launch._validate_guard_contract(PACKAGE/'run.py','typed_joint_skill_decision')
    def reject(*a,**kw):raise RuntimeError('pure admission refusal')
    monkeypatch.setattr(hmasd_admission,'require_admission',reject)
    monkeypatch.setattr(r,'target',lambda *a:pytest.fail('encoder import before admission'))
    monkeypatch.setattr(run,'arm_limits',lambda *a:pytest.fail('limits before admission'))
    with pytest.raises(RuntimeError,match='admission refusal'):
        run.main(['--out',str(tmp_path/'not-created'),'--launch-sha','a'*40,'--seed','0',
                  '--node','local_linux','--input-manifest',str(tmp_path/'absent'),'--input-manifest-sha256','b'*64])
    assert not (tmp_path/'not-created').exists()
    assert '--out' in hmasd_launch.OUTPUT_ARGUMENTS
    for path in PACKAGE.glob('*.py'):
        tree=ast.parse(path.read_bytes())
        imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        assert not any((getattr(n,'module','') or '').startswith(('numpy','torch','envs')) for n in imports)
        assert not any(a.name.split('.')[0] in ('numpy','torch','envs') for n in imports for a in n.names)
    assert 'numpy' not in sys.modules and 'torch' not in sys.modules


def test_caps_stop_before_attempt_and_keep_core_setting(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'allocated',lambda *a,**kw:100)
    budget=run.Budget(tmp_path,tmp_path/'out')
    monkeypatch.setattr(run.time,'process_time',lambda:291.)
    with pytest.raises(run.Stop,match='cpu_cap'):budget.check()
    source=(PACKAGE/'run.py').read_text()
    assert 'resource.setrlimit(resource.RLIMIT_CORE' not in source
    assert 'resource.setrlimit(resource.RLIMIT_CPU,(290,300))' in source
    assert "resource.setrlimit(resource.RLIMIT_AS,(r.LIMITS['address_space_bytes']" in source
    assert 'exit=True' in source and 'buffering=0' in source
    destinations={a.dest for a in run.parser()._actions}
    assert destinations=={'help','out','launch_sha','seed','node','input_manifest','input_manifest_sha256'}


def reader_fixture(tmp_path,monkeypatch):
    value=json.loads((ROOT/'docs/research/candidates/typed_joint_skill_decision/b04_serialization/INPUT.json').read_bytes())
    lines=[b'{"x":1}\n',b'{"x":2}\n'];monkeypatch.setattr(r,'input_lines',lambda *a:lines)
    launch={'sha':'a'*40,'command_sha256':'b'*64,'node':'local_linux','host_identity':'Jacob',
            'direction':'typed_joint_skill_decision','source_root':str(ROOT),'output_root':str(tmp_path),
            'runner_process':{'identity':{'pid':123}},'process':{'identity':{'pid':122}}}
    config={'manifest':value,'manifest_sha256':'c'*64,'launch_sha':'a'*40,'command_sha256':'b'*64,
            'node':'local_linux','runtime':value['nodes']['local_linux'],
            'admission':{'sha':'a'*40,'command_sha256':'b'*64,'child_pid':123},
            'source_root':str(ROOT),'output_root':str(tmp_path)}
    witness={'status':'exited','exit_code':-11,'process_identity':{'pid':123},'supervisor_identity':{'pid':122}}
    for name,data in [('config.json',config),('launch-manifest.json',launch),('process-exit.json',witness)]:
        (tmp_path/name).write_bytes(r.json_bytes(data))
    (tmp_path/'attempts.bin').write_bytes(r.ORDINAL.pack(1)+r.ORDINAL.pack(2))
    cp={'completed':1,'attempted':1,'encoded_bytes':len(lines[0]),
        'rolling_sha256':hashlib.sha256(lines[0]).hexdigest(),'cycles_complete':0}
    (tmp_path/'checkpoints.jsonl').write_bytes(r.json_bytes(cp))
    return value,cp


def test_reader_negative_witness_keeps_uncertain_tail(tmp_path,monkeypatch):
    value,cp=reader_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(r,'target',lambda *a:pytest.fail('reader encoder replay'))
    read=r.read_records(tmp_path,value,ROOT,'c'*64)
    assert read['status']=='partial_or_failed' and read['terminal_exit_code']==-11
    assert read['attempted_ordinals']==2 and read['completed_lower_bound']==1 and read['completed_upper_bound']==2
    assert read['last_attempted_ordinal']==2
    changed={**cp,'rolling_sha256':'0'*64}
    (tmp_path/'checkpoints.jsonl').write_bytes(r.json_bytes(changed))
    with pytest.raises(ValueError,match='digest'):r.read_records(tmp_path,value,ROOT,'c'*64)


def test_reader_refuses_order_manifest_and_terminal_tamper(tmp_path,monkeypatch):
    value,cp=reader_fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='binding'):r.read_records(tmp_path,value,ROOT,'d'*64)
    (tmp_path/'attempts.bin').write_bytes(r.ORDINAL.pack(2)+r.ORDINAL.pack(1))
    with pytest.raises(ValueError,match='reordered'):r.read_records(tmp_path,value,ROOT,'c'*64)
    (tmp_path/'attempts.bin').write_bytes(r.ORDINAL.pack(1)+r.ORDINAL.pack(2))
    witness=json.loads((tmp_path/'process-exit.json').read_bytes());witness['process_identity']['pid']=999
    (tmp_path/'process-exit.json').write_bytes(r.json_bytes(witness))
    with pytest.raises(ValueError,match='witness'):r.read_records(tmp_path,value,ROOT,'c'*64)


def test_reader_setup_absence_does_not_hide_invalid_terminal(tmp_path,monkeypatch):
    value,_=reader_fixture(tmp_path,monkeypatch);(tmp_path/'config.json').unlink()
    reading=r.read_records(tmp_path,value,ROOT,'c'*64)
    assert reading['status']=='setup_record_missing' and reading['terminal_exit_code']==-11
    assert reading['completed_upper_bound'] is None and reading['attempted_ordinals'] is None
    bad=json.loads((tmp_path/'process-exit.json').read_bytes());bad['exit_code']=True
    (tmp_path/'process-exit.json').write_bytes(r.json_bytes(bad))
    with pytest.raises(ValueError,match='witness'):r.read_records(tmp_path,value,ROOT,'c'*64)


def test_reader_soft_stop_summary_keeps_uncommitted_completion_uncertain(tmp_path,monkeypatch):
    value,cp=reader_fixture(tmp_path,monkeypatch)
    cp['attempted']=2
    (tmp_path/'checkpoints.jsonl').write_bytes(r.json_bytes(cp))
    (tmp_path/'summary.json').write_bytes(r.json_bytes({**cp,'stop':'signal_SIGALRM','budget':{}}))
    witness=json.loads((tmp_path/'process-exit.json').read_bytes());witness['exit_code']=0
    (tmp_path/'process-exit.json').write_bytes(r.json_bytes(witness))
    reading=r.read_records(tmp_path,value,ROOT,'c'*64)
    assert reading['status']=='partial_or_failed'
    assert reading['completed_lower_bound']==1 and reading['completed_upper_bound']==2
    assert 'durably recorded' in reading['completion_scope']


@pytest.mark.parametrize('prohibited_at',[None,'before','after'])
def test_mock_main_consumed_admission_watchdog_and_runtime_import_guard(tmp_path,monkeypatch,prohibited_at):
    """Zero encoder calls; no input replay, real admission, clocks, limits or watchdog."""
    from scripts import hmasd_admission
    value=json.loads((ROOT/'docs/research/candidates/typed_joint_skill_decision/b04_serialization/INPUT.json').read_bytes())
    runtime={'executable_realpath':str(Path(sys.executable).resolve()),'executable_sha256':'d'*64,
             'python_version':'mock-version','hostname':'mock-node'}
    value['nodes']['local_linux']=runtime
    launch={'sha':'a'*40,'command_sha256':'b'*64,'source_root':str(ROOT),'output_root':str(tmp_path),
            'node':'local_linux','direction':'typed_joint_skill_decision','host_identity':'mock-node'}
    (tmp_path/'launch-manifest.json').write_bytes(r.json_bytes(launch))
    monkeypatch.setenv('HMASD_ADMISSION_V1','consumed by real admission')
    def admit(*a,**kw):
        os.environ.pop('HMASD_ADMISSION_V1')
        return {'sha':'a'*40,'command_sha256':'b'*64}
    monkeypatch.setattr(hmasd_admission,'require_admission',admit)
    monkeypatch.setattr(r,'manifest',lambda *a:value)
    monkeypatch.setattr(r,'sha',lambda *a:'d'*64)
    monkeypatch.setattr(run.platform,'python_version',lambda:'mock-version')
    monkeypatch.setattr(run.platform,'node',lambda:'mock-node')
    monkeypatch.setattr(r,'cpu',lambda:{'mock':True})
    monkeypatch.setattr(r,'process_wall',lambda:0.)
    class MockBudget:
        def __init__(self,*a):pass
        def check(self):pass
        def snapshot(self):return {'mock':True}
    monkeypatch.setattr(run,'Budget',MockBudget)
    monkeypatch.setattr(run,'arm_limits',lambda *a:{'address_space':[536870912]*2,'cpu':[290,300]})
    monkeypatch.setattr(run.signal,'setitimer',lambda *a:None)
    monkeypatch.setattr(run.signal,'signal',lambda *a:None)
    imported=[];replayed=[];streams=[];cancelled=[]
    original_open=Path.open
    def tracking_open(path,*a,**kw):
        stream=original_open(path,*a,**kw)
        if path.parent==tmp_path and path.name in ('fatal.log','attempts.bin','checkpoints.jsonl'):
            streams.append(stream)
        return stream
    monkeypatch.setattr(Path,'open',tracking_open)
    def cancel():
        assert (tmp_path/'summary.json').exists()
        assert len(streams)==3 and all(stream.closed for stream in streams)
        cancelled.append(True)
    monkeypatch.setattr(run.faulthandler,'cancel_dump_traceback_later',cancel)
    def literal_input(*a):
        if prohibited_at=='before':monkeypatch.setitem(sys.modules,'envs.forbidden_fixture',object())
        return [b'{"literal":1}\n']
    monkeypatch.setattr(r,'input_lines',literal_input)
    def mock_target(*a):imported.append(True);return object()
    monkeypatch.setattr(r,'target',mock_target)
    def mock_replay(*a):
        replayed.append(True)
        if prohibited_at=='after':monkeypatch.setitem(sys.modules,'torch.forbidden_fixture',object())
        return 'cycles'
    monkeypatch.setattr(run,'replay',mock_replay)
    result=run.main(['--out',str(tmp_path),'--launch-sha','a'*40,'--seed','0','--node','local_linux',
                     '--input-manifest',str(tmp_path/'unused'),'--input-manifest-sha256','c'*64])
    assert 'HMASD_ADMISSION_V1' not in os.environ and cancelled==[True]
    summary=json.loads((tmp_path/'summary.json').read_bytes())
    assert summary['completed']==summary['attempted']==0
    if prohibited_at:
        assert result==2 and summary['stop']=='prohibited_import'
        assert summary['modules_after_last_call']['prohibited_modules']
        assert bool(imported)==bool(replayed)==(prohibited_at=='after')
    else:
        assert result==0 and imported==replayed==[True]
        assert summary['modules_before_target_import']['prohibited_modules']==[]
        assert summary['modules_after_last_call']['prohibited_modules']==[]

"""One saved predecision reconstruction; no environment instance or step."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
parser=argparse.ArgumentParser()
parser.add_argument('--source-root',type=Path,required=True)
parser.add_argument('--raw',type=Path,required=True)
parser.add_argument('--config',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
a=parser.parse_args()
sys.path.insert(0,str(a.source_root))
import numpy as np
from experiments.candidates.uav_user_waiting.b02 import scheduler as s
from experiments.candidates.uav_user_waiting.b01.history import ServiceHistory
from experiments.candidates.uav_user_waiting.b02 import protocol as p
config=json.loads(a.config.read_text())
for row in config['source_identities']:
    assert hashlib.sha256((a.source_root/row['path']).read_bytes()).hexdigest()==row['sha256']
with np.load(a.raw,allow_pickle=False) as f:
    raw={k:f[k].copy() for k in f.files}
steps=int(raw['completed_steps'])
assert str(raw['program'])=='R' and int(raw['world_seed'])==29322001 and steps==112
assert int(raw['terminal_history_reductions'])==0
actor=s.Scheduler('R',raw['map_packet'].tobytes(),lambda:0.,lambda:0.,horizon=256)
for tick in range(steps):
    actor.executed(tick,raw['commands'][tick],int(raw['mask'][tick]))
actor.execution.start_tick=int(raw['terminal_history_start'])
actor.execution.next_unsettled=steps
actor.execution.history=ServiceHistory(actor.execution.start_tick,raw['terminal_last'].copy(),raw['terminal_windows'].copy(),raw['terminal_burden'].copy())
actor.execution.predicted={tick:raw['model_contacts'][tick].copy() for tick in range(steps)}
actor.execution.position=np.rint(raw['observations'][steps,:,:3].astype(float)*(1000.,1000.,100.)+(0.,0.,50.))
checks=dict(calls=0,non_integer_positions=0,non_integer_derived_indices=0,shapes=set(),sinr_dtypes=set(),assignment_digest=hashlib.sha256())
original=s.greedy_connection_assignment

def checked(sinr,*args,**kwargs):
    values=np.asarray(sinr)
    assert values.ndim==2
    n_users=values.shape[1]
    flat=values.reshape(-1)
    eligible=np.flatnonzero(flat>=3.)
    order=eligible[np.argsort(-flat[eligible],kind='stable')]
    positions=order.tolist()
    checks['calls']+=1
    checks['shapes'].add(tuple(values.shape))
    checks['sinr_dtypes'].add(values.dtype.str)
    checks['non_integer_positions']+=sum(type(pos) is not int for pos in positions)
    checks['non_integer_derived_indices']+=sum(type(pos//n_users) is not int or type(pos-(pos//n_users)*n_users) is not int for pos in positions)
    result=original(sinr,*args,**kwargs)
    checks['assignment_digest'].update(result.tobytes())
    return result

s.greedy_connection_assignment=checked
start=time.perf_counter()
result=actor.decide(raw['observations'][steps,:,:3],raw['commands'][steps],raw['proposals'][steps],steps,int(raw['mask'][steps]),raw['post_c_nav'][steps//4])
assert result['timely']
checks['assignment_digest']=checks['assignment_digest'].hexdigest()
checks['shapes']=sorted(checks['shapes'])
checks['sinr_dtypes']=sorted(checks['sinr_dtypes'])
r=result['record']['current']
out=dict(status='RECONSTRUCTION_COMPLETED',scope='one frozen-R saved-input decision, zero native environment calls/fits; traceback lacks original frame operands',launch_sha=config['launch_sha'],host=platform.node(),python=platform.python_version(),numpy=np.__version__,raw_sha256=hashlib.sha256(a.raw.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seed=29322001,tick=steps,candidate_requests=result['candidate_requests'],candidate_plans=result['candidate_plans'],state_reductions=result['state_reductions'],selected_q=result['selected_q'],selected_mask=result['selected_mask'],key_digest=hashlib.sha256(r['keys']['R'].tobytes()).hexdigest(),contacts_digest=hashlib.sha256(r['contacts'].tobytes()).hexdigest(),checks=checks,wall_seconds=time.perf_counter()-start)
a.out.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out),flush=True)

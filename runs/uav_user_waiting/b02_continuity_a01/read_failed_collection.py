"""Read accepted complete episodes and the observed partial prefix only."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
sys.path.insert(0,str(Path.cwd()))
import numpy as np
from experiments.candidates.uav_user_waiting.b02.read import verify_episode,verify_stage,advance,check_history
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.study import source_identities
from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_service_age.b01.read import verify_native
from experiments.candidates.uav_radio_activation.b01.read import observed_rows,radio,assert_close
from experiments.candidates.uav_registered_service.b01.read import load_episode
root=Path('runs/uav_user_waiting/b02_continuity_a01')
summary=json.loads((root/'summary.json').read_text())
config=json.loads((root/'config.json').read_text())
assert summary['status']=='INCOMPLETE_TECHNICAL_FAILURE' and summary['config']==config
assert config['source_identities']==source_identities()
rawdir=Path('temp/directions/uav_user_waiting/b02_failure_raw')
started=time.perf_counter()
reading=dict(status='READ_INCOMPLETE_TECHNICAL_COLLECTION',complete_rows=[],partial={},native_steps_added=0,fits_added=0,summary_sha256=hashlib.sha256((root/'summary.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='No complete fixed panel or paired scientific conclusion; all accepted saved native transitions checked')
for row in summary['rows']:
    path=rawdir/Path(row['raw']['path']).name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['raw']['sha256']
    reading['complete_rows'].append(verify_episode(row,load_episode(path)))
    print(json.dumps(dict(verified=row['arm'],seed=row['seed'])),flush=True)
raw=load_episode(rawdir/'R_29322001.npz')
steps=int(raw['completed_steps'])
assert steps==112 and int(raw['round_count'])==28
records=unpack_records(raw)
assert len(records)==28 and raw['episode_failure_type']=='TypeError'
# C at failed report112 completed before scheduler failure. Verify and distinguish
# its counters from the112 actual transitions accepted by the native prefix reader.
controllers=[LocalController(history=False) for _ in range(5)]
for tick in range(0,steps+1,4):
    if tick==steps:
        prefix_counts={k:sum(c.counters[k] for c in controllers) for k in controllers[0].counters}
    for member,controller in enumerate(controllers):
        command,diag=controller.act(raw['observations'][tick,member],tick)
        np.testing.assert_array_equal(command,raw['proposals'][tick,member])
        assert controller._nav_index==raw['post_c_nav'][tick//4,member]
all_counts={k:sum(c.counters[k] for c in controllers) for k in controllers[0].counters}
np.testing.assert_array_equal(raw['controller_counts'],[all_counts[str(k)] for k in raw['controller_counter_keys']])
view=dict(raw)
for key in ('positions','observations'):
    view[key]=raw[key][:steps+1]
for key in ('commands','proposals','c_called','c_decision','c_wall','c_cpu','mask','reward','served','quality','sinr','connections','fallback','n_current','n_visible_peers','selected_index'):
    view[key]=raw[key][:steps]
for key in ('round_tick','commitments','applied_mask'):
    view[key]=raw[key][:steps//4]
view['controller_counts']=np.array([prefix_counts[str(k)] for k in raw['controller_counter_keys']])
row=dict(arm='R',seed=29322001,steps=steps,controller_counts=prefix_counts)
verified=verify_native(row,view,verify_observations=False)
maximum_observation_error=0.
for tick in range(steps+1):
    mask=int(raw['mask'][tick])
    expected=observed_rows(raw['positions'][tick],raw['true_sites'],mask,tick)
    expected[:,-1]=tick/256.
    assert_close(raw['observations'][tick],expected,1e-6)
    maximum_observation_error=max(maximum_observation_error,float(np.abs(raw['observations'][tick]-expected).max()))
verified['max_observation_error']=maximum_observation_error
contacts=raw['connections'][:steps].any(axis=1)
ages=np.zeros((steps,50),dtype=np.int64)
last=np.full(50,-1,dtype=np.int64)
for tick,served in enumerate(contacts):
    last[served]=tick
    ages[tick]=tick-last
np.testing.assert_array_equal(raw['actual_ages'],ages)
# Independently reconstruct lawful actual-history settlements/anchors and every
# completed R candidate through the last returned report108.
sites=p.decode_map(raw['map_packet'].tobytes())
last=np.full(50,-1,dtype=np.int64)
windows=np.zeros((4,50),dtype=bool)
burden=np.zeros(50,dtype=np.int64)
position=None
cursor=0
anchors={record['tick']:record['decoded_positions'] for record in records if record['decoded_anchor']}
# Failed report112 was decoded/settled before its candidate exception; it has no
# executed transition and cannot change the already reconstructed history.
physics=0
for index,record in enumerate(records):
    tick=index*4
    assert record['history_before']==cursor and record['history_after']==tick
    while cursor<tick:
        origin=anchors.get(cursor,position)
        position=np.clip(origin+30*raw['commands'][cursor],p.LOW,p.HIGH)
        _,connected,_=radio(position,sites,int(raw['mask'][cursor]))
        served=connected.any(axis=0)
        np.testing.assert_array_equal(raw['model_contacts'][cursor],served)
        advance(last,windows,burden,cursor,served)
        cursor+=1
    if tick in anchors:
        position=anchors[tick].copy()
    for name,value in (('last',last),('windows',windows),('burden',burden)):
        np.testing.assert_array_equal(record['history_'+name],value)
    packets=tuple(packet.tobytes() for packet in record['report_packets'])
    assert packets==p.encode_reports(raw['observations'][tick,:,:3],raw['commands'][tick],raw['proposals'][tick],tick,raw['post_c_nav'][index])
    decoded,committed,proposed,nav=p.decode_reports(packets,tick)
    for key,value in (('positions',decoded),('actual',committed),('proposals',proposed),('nav',nav)):
        np.testing.assert_array_equal(record['decoded_'+key],value)
        np.testing.assert_array_equal(record['current'][key],value)
    check_history(record['current']['input_history'],0,last,windows,burden)
    result=verify_stage(record['current'],sites,full_physics=tick in (0,60,124,248))
    physics+=result['candidate_physics_pairs']
    assert record['timely']
    selected=record['current']['searches']['R']['selected_pair']
    np.testing.assert_array_equal(record['requested_pair'],selected)
    assert raw['selected_q'][index]==selected[0] and raw['selected_mask'][index]==selected[1]
    mask,member,q=p.decode_command(record['delivered_command_packet'].tobytes(),tick)
    assert (q,mask)==tuple(selected) and mask==raw['applied_mask'][index]
    expected_commands=proposed.copy()
    from experiments.candidates.uav_local_history.b01.controller import COMMANDS
    expected_commands[member]=COMMANDS[q]
    np.testing.assert_array_equal(record['returned_commands'],expected_commands)
    np.testing.assert_array_equal(raw['commitments'][index],expected_commands)
while cursor<steps:
    origin=anchors.get(cursor,position)
    position=np.clip(origin+30*raw['commands'][cursor],p.LOW,p.HIGH)
    _,connected,_=radio(position,sites,int(raw['mask'][cursor]))
    served=connected.any(axis=0)
    np.testing.assert_array_equal(raw['model_contacts'][cursor],served)
    advance(last,windows,burden,cursor,served)
    cursor+=1
for name,value in (('last',last),('windows',windows),('burden',burden)):
    np.testing.assert_array_equal(raw['terminal_'+name],value)
assert raw['model_valid'][:steps].all() and not raw['model_valid'][steps:].any()
reading['partial']=dict(**verified,arm='R',seed=29322001,failed_report=112,verified_prior_decisions=len(records),candidate_physics_pairs=physics,observed_ages_verified=True,model_history_verified=True,extra_current_C_calls_before_failed_decision=5,original_failing_candidate_frame='not saved; deterministic reconstruction is not original frame recovery')
reading['verified_native_steps']=sum(row['verified_steps'] for row in reading['complete_rows'])+steps
assert reading['verified_native_steps']==summary['counts']['team_steps']==1648
reading['wall_seconds']=time.perf_counter()-started
(root/'failure-reading.json').write_text(json.dumps(reading,indent=2)+'\n')
print(json.dumps({k:v for k,v in reading.items() if k not in ('complete_rows','partial')},indent=2))

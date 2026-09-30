#!/usr/bin/env python3
"""Full causal/physical/value reconstruction and deterministic same-data fit replay."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_radio_activation.b01.study import file_identity,write_json
from experiments.candidates.uav_radio_activation.b01.read import assert_close
from experiments.candidates.uav_registered_service.b01.read import load_episode
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b03.read_core import verify_episode,reference_features
from experiments.candidates.uav_user_waiting.b03.learner import load_model,fit_ridge,fit_neural
from experiments.candidates.uav_user_waiting.b03.study import PURE_SEEDS,PERTURBED_SEEDS,EVAL_SEEDS,ARMS,ARM_ORDERS,perturbations,frozen_config,paired_reading


def verified_load(identity):
    path=Path(identity['path'])
    if file_identity(path)!=identity: raise ValueError('raw/checkpoint binding changed: '+str(path))
    return load_episode(path)


def verify_training(data,sources):
    """Independent loops for actual targets and causal maximum reconstruction."""
    checked=missing=0
    rows=[]
    for episode,source in enumerate(sources):
        raw=verified_load(source['raw'])
        assert str(raw['program'])=='M' and int(raw['completed_steps'])==256
        assert int(raw['world_seed'])==source['seed']
        records=unpack_records(raw)
        sites=p.decode_map(raw['map_packet'].tobytes())
        actual=np.zeros(50,np.int64);actual_max=np.zeros((257,50),np.int64)
        last=np.full(50,-1,np.int64);maxima=np.zeros((257,50),np.int64)
        lasts=np.empty((257,50),np.int64);lasts[0]=last
        windows=np.zeros((257,4,50),bool)
        for tick in range(256):
            actual+=1;actual[raw['connections'][tick].any(axis=0)]=0
            np.testing.assert_array_equal(actual,raw['actual_ages'][tick])
            actual_max[tick+1]=np.maximum(actual_max[tick],actual)
            contact=raw['model_contacts'][tick];last[contact]=tick
            lasts[tick+1]=last
            maxima[tick+1]=np.maximum(maxima[tick],tick-last)
            windows[tick+1]=windows[tick];windows[tick+1,tick//64]|=contact
        eligible=[]
        for index,record in enumerate(records):
            tick=4*index
            if tick<max(4,source['perturbation_tick']+4): continue
            good=(record['decoded_anchor'] and record['history_start']==0 and record['history_after']==tick and raw['model_valid'][:tick].all())
            if good: eligible.append(tick)
            else: missing+=1
        selected=np.flatnonzero(data['episode_ids']==episode)
        np.testing.assert_array_equal(data['ticks'][selected],eligible)
        for number,tick in zip(selected,eligible):
            index=tick//4;record=records[index]
            positions,commands,_,_=p.decode_reports(tuple(packet.tobytes() for packet in record['report_packets']),tick)
            np.testing.assert_array_equal(record['history_last'],lasts[tick])
            np.testing.assert_array_equal(record['history_windows'],windows[tick])
            x=reference_features(sites=sites,positions=positions,commands=commands,mask=int(raw['mask'][tick]),
                previous_nav=raw['post_c_nav'][index-1],last=lasts[tick],maximum=maxima[tick],windows=windows[tick],tick=tick)
            np.testing.assert_array_equal(data['X'][number],x)
            target=float((actual_max[-1]-actual_max[tick]).sum())/50.
            assert data['y'][number]==target and 0<=target<=256-tick
            assert all(r['arm']=='M' and not r.get('perturbation_applied',False) for r in records[index:])
            checked+=1
        rows.append(dict(seed=source['seed'],episode=episode,labels=len(selected)))
    assert checked==len(data['y'])<=13182 and len(sources)==256
    assert set(map(int,np.unique(data['episode_ids'])))<=set(range(256))
    return dict(labels=checked,excluded_missing_rows=missing,episodes=256,rows=rows,
                scope='all new derived rows and canonical source hashes; reused64 prior physical verification retained by reference')


def compare_fit(arm,model,fit_record,data):
    original_trace=verified_load(fit_record['trace'])
    fn=fit_ridge if arm=='LR' else fit_neural
    replay,stats,trace=fn(data['X'],data['y'],data['episode_ids'])
    assert set(trace)==set(original_trace)
    for key,array in trace.items():
        # Timing remains in stats, never in deterministic numerical traces.
        np.testing.assert_array_equal(array,original_trace[key],err_msg='fit trace '+arm+'/'+key)
    left,right=model.arrays(),replay.arrays()
    assert set(left)==set(right)
    for key in left:
        np.testing.assert_array_equal(left[key],right[key],err_msg='fit parameters '+arm+'/'+key)
    predicted=np.asarray(trace['final_prediction'],np.float64)*256.
    episodes=np.unique(data['episode_ids'])
    weighted_mse=float(np.mean([np.mean((predicted[data['episode_ids']==e]-data['y'][data['episode_ids']==e])**2) for e in episodes]))
    return dict(status='BITWISE_REPLAYED',fit_stats=stats,training_rows=len(predicted),
                weighted_training_mse_ticks=weighted_mse,
                scope='same node/data/seeds/software numerical verification; not another independent scientific training replicate')


def read_result(out,*,reading_out,admission,expected_summary_sha256,expected_launch_sha):
    out=Path(out).resolve();destination=Path(reading_out).resolve()
    if out==destination: raise ValueError('reader output must preserve the canonical worker records')
    if (destination/'reading.json').exists() or (destination/'reading-progress.json').exists():
        raise FileExistsError('no implicit verification optimization replay')
    if file_identity(out/'summary.json')['sha256']!=expected_summary_sha256:
        raise ValueError('worker summary changed before admitted reading')
    destination.mkdir(parents=True,exist_ok=True)
    start,cpu=time.perf_counter(),time.process_time()
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    result=dict(status='READING',phase='bindings',rows=[],fits={},admission=admission,
        worker_output=str(out),counts=dict(native_steps=0,scientific_fits=0,
        verification_ridge_solves=0,verification_adam_updates=0,value_replays=0,calibration_queries=0,training_predictions=0))
    try:
        summary=json.loads((out/'summary.json').read_text())
        assert summary['status']=='COMPLETE' and summary['scientific_invocation']
        assert summary['launch_sha']==expected_launch_sha
        assert json.loads((out/'process-exit.json').read_text())['exit_code']==0
        config=json.loads((out/'config.json').read_text())
        assert config==summary['config']==frozen_config(summary['launch_sha'])
        assert summary['counts']==dict(constructors=1,explicit_resets=512,native_step_calls=131072,
            team_steps=131072,complete_episodes=512,fit_started=2,optimizer_steps=4096)
        assert summary['fixed_policy_evaluation_counts']==dict(episodes=320,transitions=81920,optimizer_updates=0,parameter_updates=0)
        assert [(r['arm'],r['seed']) for r in summary['acquisition_rows']]==[('M',s) for s in PURE_SEEDS+PERTURBED_SEEDS]
        assert [(r['arm'],r['seed']) for r in summary['evaluation_rows']]==[(a,s) for i,s in enumerate(EVAL_SEEDS) for a in ARM_ORDERS[i%10]]
        result.update(launch_sha=summary['launch_sha'],summary=file_identity(out/'summary.json'))
        models={}
        for arm,record in summary['fits'].items():
            verified_load(record['model'])
            models[arm]=load_model(record['model']['path'])
        reference=json.loads((Path(__file__).parent/'reused_m.json').read_text())
        # The selected proof is in the source-bound manifest. Launcher snapshots
        # intentionally omit runs/, so do not require a second historical copy.
        assert reference['prior_verification']['status']=='VERIFIED_COMPLETE'
        assert reference['prior_verification']['verified_raw_files']==256
        assert [r['seed'] for r in reference['sources']]==list(range(29322000,29322064))
        assert all(r['prior_verified_steps']==256 for r in reference['sources'])
        sources=reference['sources']+[dict(seed=r['seed'],raw=r['raw'],perturbation_tick=r['perturbation_tick']) for r in summary['acquisition_rows']]
        data=verified_load(summary['training']['raw'])
        result['phase']='training_data'
        result['training']=verify_training(data,sources)
        assert summary['training']['labels']==len(data['y'])
        assert summary['training']['eligible_episodes']==len(np.unique(data['episode_ids']))
        for arm in ('LR','LN'):
            result['phase']='fit_replay_'+arm
            if arm=='LR': result['counts']['verification_ridge_solves']+=1
            else: result['counts']['verification_adam_updates']=None
            write_json(destination/'reading-progress.json',result)
            result['fits'][arm]=compare_fit(arm,models[arm],summary['fits'][arm],data)
            result['counts']['training_predictions']+=len(data['y'])
            if arm=='LN': result['counts']['verification_adam_updates']=4096
        world_bindings={};calibration={arm:dict(raw=[],clipped=[],target=[],seed=[],tick=[]) for arm in ('LR','LN')}
        tape={r['seed']:r for r in perturbations()}
        for row in summary['acquisition_rows']+summary['evaluation_rows']:
            result['phase']='episode_reading'
            raw=verified_load(row['raw'])
            if row['seed'] in tape:
                assert raw['perturbation_tick']==tape[row['seed']]['tick']
                np.testing.assert_array_equal(raw['perturbation_pair'],tape[row['seed']]['pair'])
            else:
                assert raw['perturbation_tick']==-1
            checked=verify_episode(row,raw,value=models.get(row['arm']))
            result['counts']['value_replays']+=checked['value_replays']
            result['rows'].append(checked)
            world=raw['true_sites'],raw['positions'][0]
            if row['seed'] in world_bindings:
                for left,right in zip(world,world_bindings[row['seed']]): np.testing.assert_array_equal(left,right)
            else: world_bindings[row['seed']]=tuple(x.copy() for x in world)
            if row['arm']=='M' and row['seed'] in EVAL_SEEDS:
                from experiments.candidates.uav_user_waiting.b03.data import episode_rows
                fresh=episode_rows(raw)
                for arm,model in models.items():
                    predicted=np.asarray(model.raw_ticks(fresh['X']))
                    clipped=np.clip(predicted,0,256-fresh['ticks'])
                    for key,values in (('raw',predicted),('clipped',clipped),('target',fresh['y']),('tick',fresh['ticks'])):
                        calibration[arm][key].extend(values.tolist())
                    calibration[arm]['seed'].extend([row['seed']]*len(predicted))
                    result['counts']['calibration_queries']+=len(predicted)
            if len(result['rows'])%8==0: write_json(destination/'reading-progress.json',result)
            print(json.dumps(dict(verified=len(result['rows']),arm=row['arm'],seed=row['seed'])),flush=True)
        for arm,rows in calibration.items():
            pred,target=np.array(rows['clipped']),np.array(rows['target'])
            rows.update(mse_ticks=float(np.mean((pred-target)**2)),mae_ticks=float(np.mean(np.abs(pred-target))),
                        bias_ticks=float(np.mean(pred-target)))
        result['fresh_m_calibration']=calibration
        result['calibration_scope']='real held-out M suffixes only; no claim about LN-selected counterfactual M states'
        result['paired']=paired_reading(summary['evaluation_rows'])
        assert result['paired']==summary['paired']
        assert summary['evaluation_parameter_sha256']=={arm:model.parameter_sha256() for arm,model in models.items()}
        result['verified_artifacts']=[file_identity(Path(r['path'])) for r in summary['artifacts']]
        assert result['verified_artifacts']==summary['artifacts']
        result['status'],result['phase']='VERIFIED_COMPLETE','complete'
        result['physics_scope']='all native/C/executed histories; all selected evaluated plans and all visited candidates at0/60/124/248; all other costs/values/keys from contacts; same radio kernel'
        result['reader_c_calls']=512*64*5*2
    except Exception as exc:
        result['status']='READ_FAILED'
        result['error']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        result['resources']=dict(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,
            process_user_seconds=usage.ru_utime,process_system_seconds=usage.ru_stime,peak_rss_kib=usage.ru_maxrss,
            scope='reader lifetime Linux KiB; verification optimization and physical/model calls separately from new native exposure')
        write_json(destination/'reading.json',result)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--worker-out',type=Path,required=True)
    parser.add_argument('--worker-summary-sha256',required=True)
    parser.add_argument('--launch-sha',required=True)
    parser.add_argument('--seed',type=int,required=True)
    args=parser.parse_args(argv)
    if args.seed!=29423000: parser.error('fixed B03 verification identity required')
    if len(args.worker_summary_sha256)!=64 or any(c not in '0123456789abcdef' for c in args.worker_summary_sha256):
        parser.error('complete lowercase worker summary SHA256 required')
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction='uav_user_waiting')
    if admission['sha']!=args.launch_sha: raise RuntimeError('reader admission/source mismatch')
    return read_result(args.worker_out,reading_out=args.out,admission=dict(admission),
        expected_summary_sha256=args.worker_summary_sha256,expected_launch_sha=args.launch_sha)


if __name__=='__main__':
    if main()['status']!='VERIFIED_COMPLETE': raise SystemExit(1)

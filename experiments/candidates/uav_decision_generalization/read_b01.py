"""Admitted independent reading of all fixed A/R/N endpoints, updates and fresh traces."""
from __future__ import annotations
import json
import math
from pathlib import Path
import sys
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments.candidates.uav_decision_generalization import contract as c,models,phases,reading,independent


def soft_ce(logits,q):
    import numpy as np
    x=np.asarray(logits,dtype=np.float64)
    shifted=x-x.max();logprob=shifted-np.log(np.exp(shifted).sum())
    return float(-np.dot(reading.independent_soft_target(q),logprob))


def endpoint_read(store,records,state,arm,stage,endpoint,worlds=None):
    predictions=endpoint['predictions']
    if len(predictions)!=len(records) or {p['world'] for p in predictions}!={r['address']['world'] for r in records}:
        raise ValueError('endpoint world set changed')
    saved={p['world']:p for p in predictions};rows=[]
    for record in records:
        wid=record['address']['world'];features=record['features'];actual=saved[wid]
        if actual['feature_sha256']!=c.digest(features) or actual['slots']!=features['display_order']:
            raise ValueError('endpoint feature/display identity mismatch')
        slots=actual['slots'];gpu=actual['logits']
        if len(gpu)!=len(slots) or not all(math.isfinite(v) for v in gpu):
            raise ValueError('invalid endpoint logits')
        executed=slots[max(range(len(slots)),key=lambda i:gpu[i])]
        if actual['selected_slot']!=executed:
            raise ValueError('GPU endpoint logit-to-slot mapping changed')
        store.bill.enter('reader_'+arm+'_contexts')
        x,ind_slots=independent.fields(features,arm)
        cpu=independent.logits(state,x,arm)
        if ind_slots!=slots:
            raise ValueError('independent slot mapping mismatch')
        chosen=slots[max(range(len(slots)),key=lambda i:cpu[i])]
        labels=record['labels'];qmap=dict(zip(labels['slot_order'],labels['Q']))
        q=[qmap[s] for s in slots]
        flags=independent.comparison(cpu,gpu)
        row={'world':wid,'split':record['address']['split'],'stage':stage,'arm':arm,'slots':slots,
             'feature_sha256':actual['feature_sha256'],'GPU_logits':gpu,'CPU_logits':cpu,
             'executed_slot':executed,'independent_slot':chosen,'choice_mismatch':chosen!=executed,
             'float_comparison':flags,'executed_Q':qmap[executed],'independent_Q':qmap[chosen],
             'independent_minus_executed_Q':qmap[chosen]-qmap[executed],
             'soft_CE':soft_ce(gpu,q),'independent_soft_CE':soft_ce(cpu,q),'regret':max(q)-qmap[executed]}
        if worlds is not None:
            result=worlds[wid]['scores'][executed]
            row['native_means']=result['native_means'];row['service_tail']=result['service_tail']
            reading.close_numbers(result['Q'],qmap[executed])
        rows.append(row)
        store.bill.check()
    return rows


def aggregate(rows):
    output={k:reading.uncertainty([r[k] for r in rows]) for k in ('soft_CE','regret','executed_Q')}
    output['selected_slot_counts']={str(i):sum(r['executed_slot']==i for r in rows) for i in range(8)}
    output['choice_mismatches']=sum(r['choice_mismatch'] for r in rows)
    output['component_tolerance_flags']=[{'world':r['world'],'flags':r['float_comparison']['component_within_tolerance']}
                                          for r in rows if not r['float_comparison']['all_within_tolerance']]
    if 'native_means' in rows[0]:
        output['native_means']={k:reading.uncertainty([r['native_means'][k] for r in rows]) for k in rows[0]['native_means']}
        output['service_tail']={k:tail_distribution([r['service_tail'][k] for r in rows]) for k in rows[0]['service_tail']}
    return output


def tail_distribution(values):
    import numpy as np
    return {**reading.uncertainty(values),'cross_world_minimum':min(values),
            'cross_world_p10':float(np.quantile(values,.1)),'cross_world_maximum':max(values)}


def check_fit_config(config,block,arm,train_locator):
    expected={'block':block,'arm':arm,'model_seed':c.BASES[block-1]+(41001 if arm=='A' else 42001),
              'order_seed':c.BASES[block-1]+20002,'epochs':64,'batch_size':32,'lr':.001,'weight_decay':.0001,
              'adam_betas':[.9,.999],'adam_eps':1e-8,'dtype':'float32','parameters':c.PARAMETERS[arm],
              'dataset_manifest_sha256':train_locator['manifest_sha256']}
    if any(config.get(k)!=v for k,v in expected.items()):
        raise ValueError('frozen fit configuration mismatch')


def read_blocks(store,train,fresh,fit_root,fit_files,fresh_root,fresh_files,old_root,old_files,worlds):
    import torch
    blocks={}
    for block in (1,2,3):
        training=train.split(block,'train');evaluation=fresh.split(block,'fresh')
        fits={};fresh_rows={r['address']['world']:{} for r in evaluation}
        for arm in ('A','R','N'):
            if arm!='N':
                prefix=f'fits/b{block}/{arm}'
                for name in ('config.json','summary.json','initial.pt','final.pt','optimizer.pt','updates.jsonl'):
                    phases.require_file(fit_files,prefix+'/'+name)
                config=json.loads((fit_root/(prefix+'/config.json')).read_bytes())
                check_fit_config(config,block,arm,train.locator)
                initial=torch.load(fit_root/(prefix+'/initial.pt'),map_location='cpu',weights_only=True)
                final=torch.load(fit_root/(prefix+'/final.pt'),map_location='cpu',weights_only=True)
                fits[arm]=reading.read_update_chain(fit_root,prefix,config,initial,final,training,store.bill)
                states={'initial':initial,'final':final}
            else:
                states={'final':phases.load_old_n(old_root,old_files,block)};fits[arm]={'new_updates':0,'final_sha256':c.N_FINAL_DIGESTS[block]}
            metrics={}
            for stage,state in states.items():
                for split,records,root,files in ([('train',training,fit_root,fit_files),('fresh',evaluation,fresh_root,fresh_files)] if arm!='N'
                                                 else [('fresh',evaluation,fresh_root,fresh_files)]):
                    relative=f'fits/b{block}/{arm}/{stage}-{split}.json';phases.require_file(files,relative)
                    endpoint=json.loads((root/relative).read_bytes())
                    rows=endpoint_read(store,records,state,arm,stage,endpoint,worlds if split=='fresh' else None)
                    metrics[stage+'-'+split]=aggregate(rows)
                    store.write_json(f'raw/scorers/b{block}/{arm}/{stage}-{split}.json',{'readings':rows,'aggregate':metrics[stage+'-'+split],
                                     'input_wall_seconds':endpoint['input_wall_seconds'],'scorer_wall_seconds':endpoint['scorer_wall_seconds']},kind='independent_scorer_read')
                    if split=='fresh':
                        for row in rows:
                            fresh_rows[row['world']][arm+'_'+stage]=row
                    store.status('reading_scorers')
            fits[arm]['endpoint_metrics']=metrics
        # Original requested fixed slot 3 is frozen; no new fixed-policy selection.
        for record in evaluation:
            wid=record['address']['world'];world=worlds[wid];row=fresh_rows[wid]
            ordinary=world['ordinary'];fixed_slot=ordinary['fixed_executed_slots']['3']
            selections={'fixed':fixed_slot,'static':ordinary['static'],'travel':ordinary['travel']}
            row['ordinary']={name:world['scores'][slot] for name,slot in selections.items()}
            row['ordinary']['planner']=world['planner']
            row['menu_best_Q']=ordinary['menu_best_Q']
            row['uniform_Q']=ordinary['uniform_Q']
            row['world']=wid
        rows=list(fresh_rows.values());contrasts={}
        for left,right in (('R','A'),('A','N'),('R','N')):
            contrasts[left+'_minus_'+right]=[r[left+'_final']['executed_Q']-r[right+'_final']['executed_Q'] for r in rows]
        for arm in ('A','R','N'):
            contrasts[arm+'_regret']=[r['menu_best_Q']-r[arm+'_final']['executed_Q'] for r in rows]
            for reference in ('fixed','static','travel','planner'):
                contrasts[arm+'_minus_'+reference]=[r[arm+'_final']['executed_Q']-r['ordinary'][reference]['Q'] for r in rows]
            contrasts[arm+'_minus_uniform']=[r[arm+'_final']['executed_Q']-r['uniform_Q'] for r in rows]
            if arm!='N':
                contrasts[arm+'_learning_delta']=[r[arm+'_final']['executed_Q']-r[arm+'_initial']['executed_Q'] for r in rows]
        # All native tradeoffs retain complete paired world differences and tails.
        native_differences={}
        for left,right in (('R','A'),('A','N'),('R','N')):
            name=left+'_minus_'+right
            native_differences[name]={field:[r[left+'_final']['native_means'][field]-r[right+'_final']['native_means'][field] for r in rows]
                                      for field in rows[0][left+'_final']['native_means']}
            native_differences[name].update({'service_'+field:[r[left+'_final']['service_tail'][field]-r[right+'_final']['service_tail'][field] for r in rows]
                                            for field in rows[0][left+'_final']['service_tail']})
        references={name:{'native_means':{field:reading.uncertainty([r['ordinary'][name]['native_means'][field] for r in rows])
                                        for field in rows[0]['ordinary'][name]['native_means']},
                          'service_tail':{field:tail_distribution([r['ordinary'][name]['service_tail'][field] for r in rows])
                                          for field in rows[0]['ordinary'][name]['service_tail']}}
                    for name in ('fixed','static','travel','planner')}
        compact={'block':block,'fits':fits,'metrics':{name:reading.uncertainty(v) for name,v in contrasts.items()},
                 'native_contrast_metrics':{name:{field:reading.uncertainty(v) for field,v in fields.items()} for name,fields in native_differences.items()},
                 'ordinary_native_readings':references,'world_count':len(rows)}
        store.write_json(f'raw/blocks/b{block}.json',{'worlds':rows,'paired_world_differences':contrasts,
                         'paired_native_differences':native_differences},kind='complete_block_world_read')
        store.write_json(f'blocks/b{block}.json',compact,kind='compact_block_read')
        blocks[block]=compact
    return blocks


def main(argv=None):
    args=phases.parser(__doc__,('dataset-input','learning-input','fit-input','fresh-input')).parse_args(argv)
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    import os
    paths=json.loads(os.environ.get(ENVIRONMENT_KEY,'{}'))
    admission=require_admission(__file__,direction='uav_decision_generalization')
    store,admission,prior,root=phases.accepted_store(__file__,args,admission,paths)
    try:
        threads=models.cpu_thread_environment()
        train,native_locator=phases.bound_dataset(args.dataset_input,args.dataset_input_sha256,old=True,training_only=True)
        old_root,old_locator,old_files=phases.verify_old_learning(args.learning_input,args.learning_input_sha256,native_locator)
        fit_root,fit_locator,fit_files,fit_summary,fit_config=phases.phase_input(args.fit_input,args.fit_input_sha256)
        fresh_root,fresh_locator,fresh_files,fresh_summary,fresh_config=phases.phase_input(args.fresh_input,args.fresh_input_sha256,prior)
        phases.verify_phase_source(fit_config,root)
        phases.verify_phase_source(fresh_config,root)
        phases.register_external_roots(store,train.root,old_root)
        phases.register_external_roots(store,fit_root,fresh_root,category="sequential_study_evidence")
        if (fit_config['dataset_locator']!=native_locator or fresh_config['fit_locator']!=fit_locator
                or fresh_config['learning_locator']!=old_locator or fresh_config['dataset_locator']!=native_locator):
            raise ValueError('sequential external input identity mismatch')
        fresh=phases.Dataset(fresh_root,fresh_locator)
        versions=phases.verify_numerical_versions()
        import torch
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.set_default_dtype(torch.float32)
        store.write_json('config.json',{'admission':admission,'contract':c.frozen_contract(),'direction_source_sha256':phases.source_identity(root),'native_locator':native_locator,
            'learning_locator':old_locator,'fit_locator':fit_locator,'fresh_locator':fresh_locator,'threads':threads,
            'prior_bill_sha256':args.budget_ledger_sha256,'device':'cpu','versions':versions,'tolerance':models.FLOAT_TOLERANCE},kind='reader_config')
        worlds=reading.reconstruct_native(store,fresh)
        blocks=read_blocks(store,train,fresh,fit_root,fit_files,fresh_root,fresh_files,old_root,old_files,worlds)
        if (sum(store.bill.delta['reader_'+arm+'_contexts'] for arm in ('A','R','N'))!=4992
                or store.bill.delta['reader_updates_read']!=3072):
            raise AssertionError('fixed complete reader scorer/update bill mismatch')
        expected_episodes=sum(len(r['features']['plans'])+1 for r in fresh.records)
        expected_aliases=sum(len(r['labels']['correctness_audit']) for r in fresh.records)
        if store.bill.delta['reader_episode_reads']!=expected_episodes or store.bill.delta['reader_alias_reads']!=expected_aliases:
            raise AssertionError('complete native trace/audit reading mismatch')
        effects=[blocks[b]['metrics']['R_minus_A']['mean'] for b in (1,2,3)]
        effect=reading.uncertainty(effects);se=effect['standard_error'];mean=effect['mean']
        primary={'mean':mean,'block_effects':effects,'independent_blocks':3,'df':2,
                 'descriptive_t95_interval':[mean-4.302652729911275*se,mean+4.302652729911275*se]}
        status=store.status('complete')
        store.write_json('summary.json',{**status,'launch_sha':args.launch_sha,'contract_sha256':c.digest(c.frozen_contract()),
            'primary_R_minus_A':primary,'blocks':blocks,'endpoint_contexts':4992,'reader_contexts':4992,'total_scorer_contexts':9984,
            'native_episode_reads':expected_episodes,'audit_alias_reads':expected_aliases,
            'fit_locator':fit_locator,'fresh_locator':fresh_locator,
            'reliance':['all fresh native traces read independently; old train Q uses verified original dataset',
                        'saved optimizer/gradient/hash chains read; optimizer not replayed',
                        'native static queries trusted at bound five-source digests; no extra native query',
                        'GPU endpoint choices remain reported policies; CPU numerical flags preserved'],
            'inference_scope':'three independent training/data blocks; world intervals conditional on fits; package comparisons',
            'cost_limits':['segmented endpoint input/scorer timings; complete online deployment costs not measured',
                           'allocated storage includes declared external input roots/source snapshots separately from new evidence']},kind='reader_summary')
        return 0
    except BaseException as exc:
        phases.failure(store,exc);raise
    finally:
        store.close()


if __name__=='__main__':
    raise SystemExit(main())

"""Independent rebuild; each finite vector owns its exact lower-index winner."""
from __future__ import annotations
import math
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import data as old,evidence as e
from . import contract as c


def vector(record):
    infos=record['infos'];best=old.teacher(infos)
    if 'best' in record and (type(record['best']) is not int or best!=record['best']):
        raise AssertionError('stored winner must equal exact self argmax')
    values=[[r[k] for k in ('contract_reward','coverage_backhauled','frontend_capacity_with_path_mbps')] for r in infos]
    if not all(type(v) in (float,int) and math.isfinite(v) for row in values for v in row):
        raise ValueError('finite complete J/C/frontend vectors required')
    js=[r[0] for r in values];maximum=js[best]
    maxima=[i for i,j in enumerate(js) if j==maximum]
    ordered=sorted(js,reverse=True)
    return {'best':best,'exact_max_indices':maxima,'margin_to_second':maximum-ordered[1] if len(js)>1 else None,
            'J_C_frontend':values}


def winner_difference(a,b):
    av,bv=vector(a),vector(b);ai,bi=av['best'],bv['best']
    aj=[v[0] for v in av['J_C_frontend']];bj=[v[0] for v in bv['J_C_frontend']]
    if len(aj)!=len(bj):raise ValueError('full cross-vector denominator')
    delta=max(abs(x-y) for x,y in zip(aj,bj))
    return {'left':av,'right':bv,'winner_differs':ai!=bi,'maximum_J_abs_difference':delta,
            'cross_selected_J':{'left_at_left':aj[ai],'left_at_right':aj[bi],
                                'right_at_left':bj[ai],'right_at_right':bj[bi]},
            'left_cross_selected_regret':aj[ai]-aj[bi],'right_cross_selected_regret':bj[bi]-bj[ai],
            'algebraic_regret_bound_2delta':2*delta}


def compare_world(actual,saved,bank_module,diagnostics,label,count_compatibility=False):
    old.exact(actual['identity'],saved['identity'],label+' world identity',diagnostics)
    old.exact(bank_module.features(actual),bank_module.features(saved),label+' ordered outcome-free features',diagnostics)
    old.exact(actual['construction'],saved['construction'],label+' raw metadata/RNG',diagnostics)
    old.exact(len(actual['infos']),len(saved['infos']),label+' complete candidate count',diagnostics)
    for i,(a,b) in enumerate(zip(actual['infos'],saved['infos'])):
        if count_compatibility:diagnostics.bill.charge('compatibility_label_attempts')
        old.physical(a,b,f'{label}/{i} physical fields',diagnostics)
        if count_compatibility:diagnostics.bill.charge('compatibility_labels')
    reading=winner_difference(actual,saved)
    diagnostics.write({'check':label+' exact self winners; cross winner difference observed','passed':True,**reading})
    return reading


def rebuild(store,native,bank_module,saved,value,root):
    import numpy as np
    from experiments.candidates.typed_joint_skill_decision.b04 import evidence as original
    split,local,worlds=c.shard(store.index)
    diagnostic_name=store.data_prefix+'-checks.jsonl.gz';diagnostics=e.Trace(store.allowed(diagnostic_name),store.bill,diagnostics=True)
    journal_name=store.data_prefix+'-full.jsonl.gz';journal=e.Trace(store.allowed(journal_name),store.bill)
    rebuilt=[];checks=[];compatibility=[];excluded=None
    reference=value['b05_contract']['reference']
    try:
        if store.index<39:
            name=f'raw/bank/train/{local:04d}.npz'
            compatibility=old.load_shard(c.relative(reference['root'],name),reference['files'][name],worlds.start,reference['old_source_sha'],reference['old_input_sha256'])
        elif store.index==39:
            compatibility,excluded=old.partial_records(old.c.partial_path(root,value['b05_contract']),reference['partial'],reference['old_source_sha'],reference['old_input_sha256'])
        old.exact([r['identity']['world'] for r in saved],list(worlds),'complete chronological producer addresses',diagnostics)
        for n,world in enumerate(worlds):
            store.bill.check();store.bill.shared.locate('reader',store.index,world);store.bill.charge('reader_worlds_attempted')
            env,identity,raw,f,construction,_=bank_module.prepare(native,world)
            current={'identity':identity,'features':f,'layouts_xyz':f['layouts_xyz'],'construction':construction,'infos':[]}
            record=saved[n];vector(record)
            old.exact(identity,record['identity'],f'{world} independent reset/RNG/geometry',diagnostics)
            old.exact(f,bank_module.features(record),f'{world} ordered raw features',diagnostics)
            old.exact(construction,record['construction'],f'{world} construction',diagnostics)
            old.exact(len(raw),len(record['infos']),f'{world} complete menu denominator',diagnostics)
            for i,r in enumerate(raw):
                store.bill.shared.locate('reader',store.index,world,i)
                info=original.plain(native.host.static_evaluate(env,r['positions_xyz'],allow_a2a=True));current['infos'].append(info)
                journal.write({'world':world,'raw_index':i,'positions_xyz':r['positions_xyz'].tolist(),'info':info})
                old.physical(info,record['infos'][i],f'{world}/{i} independent physical fields',diagnostics)
                rebuilt.append([info[k] for k in ('contract_reward','coverage_backhauled','frontend_capacity_with_path_mbps')])
            pairs={'rebuild_vs_producer':winner_difference(current,record)}
            diagnostics.write({'check':f'{world} exact self winners','passed':True,**pairs['rebuild_vs_producer']})
            if n<len(compatibility):
                store.bill.charge('compatibility_attempts')
                pairs['rebuild_vs_original']=compare_world(current,compatibility[n],bank_module,diagnostics,f'{world} rebuild vs original',True)
                pairs['producer_vs_original']=compare_world(record,compatibility[n],bank_module,diagnostics,f'{world} producer vs original')
                store.bill.charge('compatibility_worlds')
            checks.append({'world':world,'M':len(raw),'teacher':old.teacher(current['infos']),
                           'attempts':len(raw),'completed':len(raw),'winner_comparisons':pairs})
            store.bill.charge('reader_worlds_completed');store.bill.shared.flush()
        original.npz_write(store,store.data_prefix+'.npz',{'J_C_frontend':np.asarray(rebuilt,dtype=np.float64),
            'records':np.asarray(c.encoded(checks).decode('ascii'))})
    finally:
        journal.close();diagnostics.close()
        store.register(journal_name,content_format='gzip-jsonl',record_count=journal.rows)
        store.register(diagnostic_name,content_format='gzip-jsonl',record_count=diagnostics.rows)
    store.bill.charge('reader_shards_completed')
    return {'split':split,'shard':local,'worlds':64,'labels':len(rebuilt),
        'world_candidate_counts':[[r['world'],r['M'],r['teacher']] for r in checks],
        'compatibility_worlds':len(compatibility),'compatibility_labels':sum(len(r['infos']) for r in compatibility),
        'excluded_old_partial':excluded,'checks':diagnostics.rows,
        'winner_difference_counts':{pair:sum(row['winner_comparisons'].get(pair,{}).get('winner_differs',False) for row in checks)
             for pair in ('rebuild_vs_producer','rebuild_vs_original','producer_vs_original')},
        'journal_instrumentation':journal.timing(),'diagnostic_instrumentation':diagnostics.timing(),
        'trust':'independent reconstruction with pinned radio, not independent physical laws; original exit2 unchanged'}

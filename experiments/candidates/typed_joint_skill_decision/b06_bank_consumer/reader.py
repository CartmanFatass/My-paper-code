"""B06 complete B04 reader composition with paid ordinary-query authority only.

The complete body below preserves B04's sampling, endpoints, CPU functional flags,
frames, audits, P cache replay and aggregates. Only ordinary verification and static
score reporting differ. Frozen B04 reader/exact/labels are never replaced.
"""
from __future__ import annotations
import itertools
import json
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import data as fixed_data


class PhysicalDiagnostics:
    def __init__(self,diagnostics):self.diagnostics=diagnostics
    def write(self,value):self.diagnostics.append(value)


def ordinary_paid(decision,queries,raw,selected,reference,diagnostics):
    """Exact paid self-argmax, original query chronology/layouts, frozen physics."""
    sink=PhysicalDiagnostics(diagnostics)
    selected=sorted(selected)
    if len(queries)!=len(selected) or not selected:raise AssertionError('ordinary complete paid query count')
    if decision['selection_counts']['static_calls']!=len(selected):raise AssertionError('ordinary actual paid-query count')
    actual_scores={}
    for query,i in zip(queries,selected):
        if set(query)!={'positions_xyz','allow_a2a','info','state'} or query['allow_a2a'] is not True:
            raise AssertionError('ordinary original paid-query schema/physics identity')
        fixed_data.exact(query['state']['current_step'],0,'ordinary paid query at t0',sink)
        fixed_data.exact(query['state']['positions_xyz'],raw[i]['positions_xyz'],'ordinary paid-query state ordered row',sink)
        state_info=query['state']['reward_info']
        if set(query['info'])!=set(state_info)|{'uav_connection_count'}:
            raise AssertionError('ordinary original reward-info/static extension keys')
        fixed_data.exact({k:query['info'][k] for k in state_info},state_info,'ordinary paid-query reward response/state identity',sink)
        links=query['state']['uav_connections']
        if len(links)!=6 or any(len(row)!=6 for row in links):raise AssertionError('ordinary complete six-agent link state')
        link_count=int(sum(links[i][j] for i in range(6) for j in range(i+1,6)))
        fixed_data.exact(query['info']['uav_connection_count'],link_count,'ordinary original static link-count extension',sink)
        fixed_data.exact(query['positions_xyz'],raw[i]['positions_xyz'],'ordinary original raw query row',sink)
        fixed_data.physical(query['info'],reference['infos'][i],'ordinary paid physical fields',sink)
        actual_scores[str(i)]=query['info']
    fixed_data.exact(decision['scores'],actual_scores,'ordinary recorded decision.scores equal actual paid responses',sink)
    paid_best=max(selected,key=lambda i:(actual_scores[str(i)]['contract_reward'],-i))
    fixed_data.exact(decision['chosen_raw_index'],paid_best,'ordinary exact own paid-response argmax',sink)
    bank_best=max(selected,key=lambda i:(reference['infos'][i]['contract_reward'],-i))
    paid=[actual_scores[str(i)]['contract_reward'] for i in selected]
    bank=[reference['infos'][i]['contract_reward'] for i in selected]
    if decision['arm']=='Raw8J':
        fixed_data.exact(decision['shortlist']['source_indices'],selected,'ordinary outcome-free shortlist addresses',sink)
    return {'paid_winner':paid_best,'bank_winner_on_paid_indices':bank_best,'winner_differs':paid_best!=bank_best,
            'paid_indices':selected,'paid_J':paid,'bank_J':bank,
            'paid_exact_max_indices':[i for i,j in zip(selected,paid) if j==max(paid)],
            'bank_exact_max_indices':[i for i,j in zip(selected,bank) if j==max(bank)],
            'paid_margin_to_second':sorted(paid,reverse=True)[0]-sorted(paid,reverse=True)[1] if len(paid)>1 else None,
            'bank_margin_to_second':sorted(bank,reverse=True)[0]-sorted(bank,reverse=True)[1] if len(bank)>1 else None,
            'bank_at_paid_winner_J':reference['infos'][paid_best]['contract_reward'],
            'online_paid_at_chosen_J':actual_scores[str(paid_best)]['contract_reward']}


def static_values(arm,decision,reference,matched,ordinary=None):
    bank_j=reference['infos'][decision['chosen_raw_index']]['contract_reward'] if arm!='P' else None
    paid_j=(ordinary['online_paid_at_chosen_J'] if ordinary is not None else
            decision['P_menu']['static']['P_relay_contract_reward'] if arm=='P' else None)
    matched_j=matched['contract_reward']
    return {'bank_at_chosen_J':bank_j,'online_paid_at_chosen_J':paid_j,'matched_static_J':matched_j,
            'matched_minus_bank_J':None if bank_j is None else matched_j-bank_j,
            'matched_minus_online_J':None if paid_j is None else matched_j-paid_j,
            'online_minus_bank_J':None if bank_j is None or paid_j is None else paid_j-bank_j,
            'ordinary_paid_reading':ordinary}


def complete(store,train_view,training_view,fresh_view,assets,cases,diagnostics):
    import numpy as np
    from experiments.candidates.typed_joint_skill_decision.b04 import reader as original
    from experiments.candidates.typed_joint_skill_decision.b04 import contract as c,evidence as e,bank,model
    from experiments.candidates.typed_joint_skill_decision.b04.shortlist import select_menu
    SERIES=original.SERIES
    exact=original.exact;world_gate=original.world_gate;frame_reader=original.frame_reader
    original_audit=original.original_audit;statistic=original.statistic
    read_updates=original.read_updates;read_endpoint=original.read_endpoint;learner_movement=original.learner_movement
    from experiments.candidates.typed_joint_skill_decision.b04.native import Native
    from experiments.candidates.typed_joint_skill_decision.b04.planner_reader import replay
    e.verify_outputs(store.root,store.files)
    endpoint_readings=[];fits=[];initials={}
    for asset in assets:
        fit=asset['fit'];path=e.relative_path(store.root,asset['path'])
        if asset['path'] not in store.files or store.files[asset['path']]['sha256']!=asset['sha256']:
            raise ValueError('unbound final model')
        checkpoint=e.checked_torch(path,asset['sha256'])
        if checkpoint['launch_sha']!=store.launch_sha or checkpoint['input_sha256']!=store.input_sha256 or checkpoint['fit']!=fit:
            raise ValueError('functional-reader model source identity')
        exact(model.digest(checkpoint['state']),checkpoint['final_sha256'],'final whole parameter bytes',diagnostics)
        initial_path=f'raw/initial/stream{fit["stream"]}.pt'
        if initial_path not in store.files:
            raise ValueError('unbound initial state')
        initial=e.checked_torch(e.relative_path(store.root,initial_path),store.files[initial_path]['sha256'])
        exact(model.digest(initial['state']),checkpoint['initial_sha256'],'saved actual initial weights',diagnostics)
        if fit['stream'] in initials:
            exact(initials[fit['stream']],checkpoint['initial_sha256'],'same-stream initializer equality',diagnostics)
        initials[fit['stream']]=checkpoint['initial_sha256']
        final_movement=learner_movement(checkpoint['state'],initial['state'])
        exposure,reading=read_updates(store,training_view,fit,checkpoint,final_movement,diagnostics);fits.append(reading)
        endpoint_readings.append(read_endpoint(store,training_view,fit,'train',checkpoint['state'],exposure,diagnostics))
        endpoint_readings.append(read_endpoint(store,fresh_view,fit,'fresh',checkpoint['state'],None,diagnostics))
    per_world=[];main_read=[];audits=[]
    with Native(store.bill) as native:
        for offset,world in enumerate(range(c.FRESH_START,c.FRESH_START+128)):
            row={'world':world,'arms':{}}
            reference=fresh_view.load(world)
            raw=[{**meta,'positions_xyz':xyz} for meta,xyz in zip(reference['construction']['raw_metadata'],reference['layouts_xyz'])]
            shortlist,_=select_menu(raw);short_ids=[p['source_index'] for p in shortlist]
            for arm in c.ARMS:
                case=cases[(world,arm)]
                decision=e.load_output(store.root,store.files,case['decision'])
                result=e.load_output(store.root,store.files,case['native'])
                world_gate(decision,reference,diagnostics)
                path=e.relative_path(store.root,case['trace'])
                reading=frame_reader(native,path,decision,result,diagnostics)
                store.write_gzip(f'raw/native-reader/{world}/{arm}.json.gz',reading)
                planner=None;ordinary=None
                if arm=='P':
                    env=native.host.make_host(world,area_size=5000)
                    exact(bank.identity(env),reference['identity'],'P cache replay fresh world',diagnostics)
                    planner=replay(env,native.p,e.relative_path(store.root,case['queries']),decision,store.bill)
                elif arm in ('Raw8J','RawJ'):
                    queries=list(e.read_trace(e.relative_path(store.root,case['queries'])))
                    selected=short_ids if arm=='Raw8J' else list(range(len(raw)))
                    ordinary=ordinary_paid(decision,queries,raw,selected,reference,diagnostics)
                audit=(offset in (0,1) and arm not in ('Raw8J','RawJ')) or (offset==0 and arm in ('Raw8J','RawJ'))
                if audit:
                    audit_reading=original_audit(store,native,decision,path,diagnostics)
                    audits.append({'world':world,'arm':arm,'reading':audit_reading})
                matched=case['matched_endpoint']
                statics=static_values(arm,decision,reference,matched,ordinary)
                metrics={k:reading[k] for k in SERIES}
                metrics.update(association_change_count=reading['association_change_count'],backhaul_loss_events=reading['backhaul_loss_events'],
                               all_team_outage_count=reading['service']['all_team_outage_count'],never_served_count=len(reading['service']['never_served_users']),
                               longest_user_gap=reading['service']['longest_user_gap'],arrival_step=reading['arrival_step'],
                               cold_selection_seconds=decision['parent_cold_selection_seconds'],
                               selection_child_cpu_seconds=decision['selection_child_cpu']['total_seconds'],
                               selection_parent_cpu_seconds=decision['selection_parent_cpu_seconds'],
                               selection_counts=decision['selection_counts'],timing=decision['timing'],
                               **statics,
                               planner_reading=planner,native_wall_seconds=result['native_wall_seconds_including_trace'],chosen_raw_index=decision['chosen_raw_index'])
                metrics['native_trace_instrumentation']=result['trace_instrumentation']
                row['arms'][arm]=metrics;main_read.append({'world':world,'arm':arm,'metrics':metrics})
            per_world.append(row);store.progress('native_reader',completed_worlds=len(per_world),total_worlds=128)
    store.write_gzip('reading/native-per-world.json.gz',per_world)
    pairs={}
    for left,right in itertools.combinations(c.ARMS,2):
        label=left+'_minus_'+right
        native_metrics={k:statistic([r['arms'][left][k]['mean_all']-r['arms'][right][k]['mean_all'] for r in per_world]) for k in SERIES}
        native_metrics.update({k:statistic([r['arms'][left][k]-r['arms'][right][k] for r in per_world])
                               for k in ('cold_selection_seconds','selection_child_cpu_seconds','selection_parent_cpu_seconds',
                                         'association_change_count','backhaul_loss_events','all_team_outage_count','never_served_count',
                                         'longest_user_gap','matched_static_J')})
        for metric in ('bank_at_chosen_J','online_paid_at_chosen_J','matched_minus_bank_J','matched_minus_online_J','online_minus_bank_J'):
            observed=[r['arms'][left][metric]-r['arms'][right][metric] for r in per_world
                      if r['arms'][left][metric] is not None and r['arms'][right][metric] is not None]
            native_metrics[metric]=statistic(observed) if observed else {'n':0,'status':'unavailable_no_paid_or_bank_value'}
        pairs[label]=native_metrics
    raw8_fresh=[]
    for world in range(c.FRESH_START,c.FRESH_START+512):
        r=fresh_view.load(world);raw=[{**m,'positions_xyz':x} for m,x in zip(r['construction']['raw_metadata'],r['layouts_xyz'])]
        short,_=select_menu(raw);ids=[v['source_index'] for v in short]
        best=max(ids,key=lambda i:(r['infos'][i]['contract_reward'],-i))
        raw8_fresh.append({'world':world,'choice':best,'raw8_J':r['infos'][best]['contract_reward'],
                           'RawJ_J':r['infos'][r['best']]['contract_reward'],
                           'regret':r['infos'][r['best']]['contract_reward']-r['infos'][best]['contract_reward']})
    store.write_gzip('reading/Raw8J-fresh512.json.gz',raw8_fresh)
    curves={}
    for stream in (0,1):
        curves[str(stream)]=[r for r in endpoint_readings if next(f for f in c.FITS if f['id']==r['fit'])['stream']==stream]
    curve_pairs={}
    for stream in (0,1):
        ids=[f['id'] for f in sorted(c.FITS,key=lambda f:f['n']) if f['stream']==stream]
        for split in ('train','fresh'):
            readings={}
            for fit_id in ids:
                with np.load(e.relative_path(store.root,f'raw/endpoints/{fit_id}/{split}.npz'),allow_pickle=False) as z:
                    readings[fit_id]=json.loads(str(z['records']))
            for left,right in itertools.combinations(ids,2):
                paired=[{'world':a['world'],'left_regret':a['regret'],'right_regret':b['regret'],
                         'delta_regret':a['regret']-b['regret'],'delta_J':a['J']-b['J']}
                        for a,b in zip(readings[left],readings[right])]
                if any(a['world']!=b['world'] for a,b in zip(readings[left],readings[right])):
                    raise AssertionError('paired nested curve world identities')
                label=f'{split}/{left}_minus_{right}'
                curve_pairs[label]={'delta_regret':statistic([r['delta_regret'] for r in paired]),
                                    'delta_J':statistic([r['delta_J'] for r in paired])}
                store.write_gzip('reading/curve-pairs/'+label+'.json.gz',paired)
    return {'status':'complete','fits':fits,'endpoint_readings':endpoint_readings,'curves_by_fixed_stream':curves,
            'paired_nested_curves':curve_pairs,
            'native_worlds':128,'native_arms':list(c.ARMS),'native_comparisons':pairs,
            'native_absolute':{a:{k:statistic([r['arms'][a][k]['mean_all'] for r in per_world]) for k in SERIES} for a in c.ARMS},
            'audits':len(audits),'Raw8J_fresh_static_regret':statistic([r['regret'] for r in raw8_fresh]),
            'matched_row_differences':'bank-at-chosen, actual online-paid and matched values distinct; both differences retained',
            'ordinary_winner_differences':sum(bool(r['metrics']['ordinary_paid_reading'] and r['metrics']['ordinary_paid_reading']['winner_differs']) for r in main_read),
            'Raw8J_fresh512_scope':'offline fixed-bank reference; only128 actual online deployments',
            'uncertainty':'two optimization streams on one nested bank; world comparisons conditional on each fixed asset; no data-only causal or scaling-law inference',
            'trust':'independent labels/native refresh use pinned radio; functional CPU scorer has no production forward; no optimizer replay; P control uses paid cached responses',
            'cold_scope':'fresh child through immutable selection-ready, includes matching/reset/serialization; segmented compute is not an independently measured uninstrumented latency',
            'host_clock':'planning wall delay does not advance H500; no high-level service-history adaptation',
            'support':'unmetered support remains unknown; phase resource bill measures this actual operation'}

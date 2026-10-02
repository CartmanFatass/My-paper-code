"""Fixed outcome-free interface checks; four C calls, seven count decodes, no actor/native."""
import numpy as np
from . import metrics,policy,read
from experiments.candidates.uav_fleet_adaptation.b02 import controllers as original
from experiments.candidates.uav_fleet_transmission.b05_score_sampling import policies as laws


def bounded(budget):
    def row(q):
        result=np.zeros(104,dtype=np.float32);result[:3]=(.5,.5,.5)
        result[3:3+3*q].reshape(q,3)[:,2]=.26
        return result
    for observation in (row(0),row(1)):
        nav=original.initial_nav(observation)
        budget.pay('original_C_calls');a=original.MemoC().query(observation,0,nav)
        budget.pay('original_C_calls');b=read.source_c(original.original.LocalController(False),observation,0,nav)
        for key in ('command','scores','served','features','action_index','next_nav','fallback'):read.equal(a[key],b[key],'bounded original C '+key)
        read.equal(read.probabilities('G',a),laws.score_tail_probabilities(a['scores'],a['action_index']),'bounded original G law')
        if a['n_current']==0:
            read.equal(a['scores'],np.zeros(27),'empty full C scores');read.equal(a['served'],np.zeros(27),'empty full C service')
    switch=policy.Switch('ZG');answers=[]
    for tick,q in enumerate((1,0,0,0,0)):
        budget.pay('count_decodes');answers.append(switch.observe(row(q),tick))
    read.equal(answers[0]['source'],'G','bounded initial parent');read.equal(answers[4]['source'],'C','bounded t1..t4 gate')
    for count,expected in ((1,1),(20,10)):
        budget.pay('count_decodes');read.equal(policy.own_count(row(count)),expected,'bounded lawful count cap')
    read.equal(read.clipped_path((1000,1000,50),(1,1,-1)),read.clipped_path((1000,1000,50),(0,0,0)),'bounded entire clipped path')
    service=metrics.user_service(np.zeros((8,50),dtype=bool))
    if service['never_served_users']!=50 or any(u['zero_runs']!=[{'start':0,'stop':8,'length':8,'left_censored':True,'right_censored':True}] for u in service['users']):raise AssertionError('bounded all50 censored gaps')
    return {'status':'VERIFIED','checks':['original empty/nonempty C and G law','t1..t4 alignment','capacity cap','four-step clipped paths','all50 censored never-served users'],
            'actual_usage':{'original_C_calls':4,'frozen_actor_rows':0,'count_decodes':7},'new_native_steps':0,'fake_actor_rows':0,'fake_native_steps':0}

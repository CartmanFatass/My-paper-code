"""Lawful fresh-process selectors; no label-bank or endpoint inputs."""
from __future__ import annotations
import hashlib
import time
from . import contract as c, evidence as e, bank, model
from .native import reset_identity
from .shortlist import select_menu


def checkpoint_model(path,digest,fit,launch_sha,input_sha):
    data=e.checked_torch(path,digest)
    if (data['fit']!=fit or data['launch_sha']!=launch_sha or data['input_sha256']!=input_sha
        or data['updates']!=4096 or data['world_presentations']!=131072 or model.digest(data['state'])!=data['final_sha256']):
        raise ValueError('exact final checkpoint/source/fit identity required')
    network=model.build(fit['model_seed'])
    network.load_state_dict(data['state'],strict=True)
    return network.to('cuda:0').eval()


def select(native,world,arm,context,bill):
    import numpy as np
    timing={};scores=None;shortlist=None;menu=None
    if arm=='P':
        t=time.perf_counter()
        from experiments.candidates.coupled_host_joint_skills_stage1.menus import compute_menu
        menu=compute_menu(world,area_size=5000,budget=3000)
        timing['compute_menu_seconds']=time.perf_counter()-t
        env=native.last_host;original=native.last_host_identity
        positions=np.asarray(menu['positions_xyz'],dtype=float)
        permutation=np.asarray(menu['m_permutation'],dtype=int)
        feature_hash,construction_hash=None,None
        chosen=None
    else:
        env,original,raw,f,construction,seconds=bank.prepare(native,world)
        timing['host_and_raw_generation_seconds']=seconds
        feature_hash=hashlib.sha256(e.encoded(f)).hexdigest()
        construction_hash=hashlib.sha256(e.encoded(construction)).hexdigest()
        t=time.perf_counter()
        if arm in ('Raw8J','RawJ'):
            indices=list(range(len(raw)))
            if arm=='Raw8J':
                selected,provenance=select_menu(raw)
                indices=sorted(p['source_index'] for p in selected)
                shortlist={'source_indices':indices,'selected_slots':selected,'provenance':provenance,
                           'execution':'original raw[source_index]; canonical shortlist coordinates not executed'}
            scores={i:e.plain(native.host.static_evaluate(env,raw[i]['positions_xyz'],allow_a2a=True)) for i in indices}
            chosen=max(indices,key=lambda i:(scores[i]['contract_reward'],-i))
            timing['ordinary_static_scoring_seconds']=time.perf_counter()-t
        else:
            fit=next(fit for fit in c.FITS if fit['id']==arm)
            with bill.gpu():
                t=time.perf_counter()
                timing['effective_runtime']=c.configure(cuda=True,expected=context['runtime'])
                network=checkpoint_model(context['checkpoint_path'],context['checkpoint_sha256'],fit,context['launch_sha'],context['input_sha256'])
                timing['cuda_configuration_and_checkpoint_load_seconds']=time.perf_counter()-t
                t=time.perf_counter()
                logits,segment=model.score(network,f,bill,'cold')
                chosen=model.choose(logits)
                timing['resident_feature_scorer_seconds']=time.perf_counter()-t
                timing['scorer']=segment
                scores=logits
                bill.charge('cold_contexts')
                del network
                import torch
                torch.cuda.empty_cache()
        positions=np.asarray(raw[chosen]['positions_xyz'],dtype=float)
        t=time.perf_counter()
        permutation=native.p.assign_targets(original['initial_positions_xyz'],positions)
        timing['chosen_layout_matching_seconds']=time.perf_counter()-t
    decision={'world':world,'arm':arm,'initial_positions_xyz':original['initial_positions_xyz'],
              'user_positions_xy':original['user_positions_xy'],'bs_xyz':original['bs_xyz'],
              'construction_identity':original,'feature_sha256':feature_hash,'construction_sha256':construction_hash,
              'chosen_raw_index':chosen,'positions_xyz':positions.tolist(),'target_permutation':permutation.tolist(),
              'assigned_targets_xyz':positions[permutation].tolist(),'scores':scores,'shortlist':shortlist,'P_menu':menu,
              'source_sha':context['launch_sha'],'input_sha256':context['input_sha256'],'timing':timing}
    t=time.perf_counter()
    decision['reset_identity']=reset_identity(env,decision)
    timing['execution_identity_reset_seconds']=time.perf_counter()-t
    return env,decision

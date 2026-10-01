"""Checkpoint chain, target arithmetic and update exposure without optimizer replay."""
import json
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.read import identity
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import equal, require
from .assets import load_head_checkpoint
from .contract import HEADS
from .learning import COUNT_KEYS, fresh_critic


def _movement(first, second):
    require(set(first) == set(second), 'parameter movement state keys')
    value = 0.
    for key in first:
        a, b = first[key].detach().cpu().numpy(), second[key].detach().cpu().numpy()
        require(a.shape == b.shape and a.dtype == b.dtype == np.float32, 'parameter shape/dtype')
        require(np.isfinite(a).all() and np.isfinite(b).all(), 'nonfinite checkpoint parameter')
        delta = b.astype(np.float64) - a.astype(np.float64)
        value += float(np.sum(delta * delta, dtype=np.float64))
    return float(np.sqrt(value))


def _optimizer(optimizer, state, steps):
    require(len(optimizer['param_groups']) == 1, 'one optimizer parameter group')
    group = optimizer['param_groups'][0]
    for key, value in dict(lr=3e-4, eps=1e-8, betas=(.9, .999), weight_decay=0,
                           amsgrad=False, foreach=False, fused=False, maximize=False).items():
        require(group[key] == value, 'fixed Adam option ' + key)
    require(len(group['params']) == len(state), 'optimizer/model parameter count')
    if steps == 0:
        require(not optimizer['state'], 'fresh optimizer has inherited state')
        return
    require(set(group['params']) == set(optimizer['state']), 'complete Adam moments')
    for index, tensor in zip(group['params'], state.values()):
        item = optimizer['state'][index]
        require(float(item['step']) == steps, 'continuing Adam step count')
        for key in ('exp_avg', 'exp_avg_sq'):
            value = item[key]
            require(value.shape == tensor.shape and value.dtype == torch.float32
                    and bool(torch.isfinite(value).all()), 'finite Adam moment ' + key)
        require(bool((item['exp_avg_sq'] >= 0).all()), 'nonnegative Adam second moments')


class LearningAudit:
    def __init__(self, out, summary, protocol, calls):
        self.out, self.summary, self.protocol, self.calls = Path(out), summary, protocol, calls
        self.records, self.heads, self.payloads, self.rollouts = {}, {}, {}, {}
        scheduled = list(protocol.training_schedule())
        require(len(summary['group_heads']) == len(scheduled), 'all immutable rollout-group heads')
        all_records = list(summary['initial_checkpoints'].values()) + summary['group_heads'] + list(summary['final_checkpoints'].values())
        for record in all_records:
            relative = record['path']
            require(relative not in self.records, 'duplicate checkpoint path')
            head, payload = load_head_checkpoint(identity(out, record), record)
            self.records[relative], self.heads[relative], self.payloads[relative] = record, head, payload
            calls['checkpoint_files'] += 1
        for record, (group, kind, worlds) in zip(summary['group_heads'], scheduled):
            require(record['kind'] == kind and record['path'] == f'assets/{kind}_group{group:03d}.pt', 'ordered group identity')
            require(record['metadata'] == dict(launch_sha=summary['launch_sha'], group=group, worlds=list(worlds),
                original_student_sha256=summary['inputs']['S']['state_sha256'],
                critic_sha256=record['metadata']['critic_sha256'], optimizer_steps_per_network=4 * group),
                'group source/rollout metadata')
        initial_critic = fresh_critic(protocol.critic_seed)
        calls['critic_initialization_reconstructions'] += 1
        initial_critic_sha = state_digest(initial_critic.state_dict())
        for kind in HEADS:
            for stage in ('initial', 'final'):
                record = summary[stage + '_checkpoints'][kind]
                require(record['path'] == f'assets/{kind}_{stage}.pt' and record['kind'] == kind, 'endpoint identity')
                meta = dict(launch_sha=summary['launch_sha'], stage=stage, critic_seed=protocol.critic_seed,
                            original_student_sha256=summary['inputs']['S']['state_sha256'])
                if stage == 'final':
                    meta['optimizer_steps_per_network'] = len(protocol.train_worlds) * 2
                require(record['metadata'] == meta, 'endpoint metadata')
                payload = self.payloads[record['path']]
                require(len(payload['optimizers']) == 2, 'actor and critic optimizers')
                step = 0 if stage == 'initial' else len(protocol.train_worlds) * 2
                _optimizer(payload['optimizers'][0], payload['head_state'], step)
                _optimizer(payload['optimizers'][1], payload['critic_state'], step)
                if stage == 'initial':
                    require(record['critic_sha256'] == initial_critic_sha, 'fresh matched critic seed/parameters')
                    require(all(bool((v == 0).all()) for v in payload['head_state'].values()), 'zero-initialized head')
        self.scheduled = scheduled

    def head_for(self, row, transfers):
        program = row['arm'].rsplit('_', 1)[0]
        if program in ('CAL', 'CONT'):
            if row['phase'] == 'training':
                path = f"assets/{program}_group{row['group']:03d}.pt"
            else:
                path = f'assets/{program}_final.pt'
            require(row['head_checkpoint'] == path, 'row immutable head checkpoint')
            require(row['head_sha256'] == self.records[path]['head_sha256'], 'row head state identity')
            if row['phase'] == 'training':
                require(row['critic_sha256'] == self.records[path]['metadata']['critic_sha256'], 'row baseline state provenance')
            return self.heads[path]
        require(row['head_checkpoint'] is None, 'fixed program acquired fitted checkpoint')
        if program in transfers:
            require(row['head_sha256'] == self.summary['inputs'][program]['state_sha256'], 'paid transfer identity')
            return transfers[program]
        require(row['head_sha256'] is None, 'unchanged policy acquired a head')
        return None

    def retain_targets(self, raw, row):
        if row['phase'] != 'training':
            require(row['critic_sha256'] is None and row['group'] is None
                    and row['critic_cpu_seconds'] == row['critic_wall_seconds'] == 0, 'training-only final leakage')
            return
        kind = row['arm'].rsplit('_', 1)[0]
        self.rollouts.setdefault((kind, row['group']), []).append(dict(world=row['world'], tape=row['tape'],
             rewards=raw['macro_rewards'].copy(), values=raw['values'].copy(), head_sha256=row['head_sha256'],
             critic_sha256=row['critic_sha256']))

    def finish(self):
        p, s = self.protocol, self.summary
        require(len(s['updates']) == len(self.scheduled), 'complete ordered update groups')
        before = {key: 0 for key in COUNT_KEYS}
        previous_head = {kind: s['initial_checkpoints'][kind]['head_sha256'] for kind in HEADS}
        previous_critic = {kind: s['initial_checkpoints'][kind]['critic_sha256'] for kind in HEADS}
        groups_by_kind = {kind: [] for kind in HEADS}
        updates = {}
        for record, (group, kind, worlds) in zip(s['updates'], self.scheduled):
            require(record['kind'] == kind and record['group'] == group and record['status'] == 'COMPLETE'
                    and record['path'] == f'updates/{kind}_group{group:03d}.json', 'ordered update record')
            update = json.loads(identity(self.out, record).read_text())
            require(update['status'] == 'COMPLETE' and update['kind'] == kind and update['group'] == group
                    and update['worlds'] == list(worlds), 'complete update provenance')
            path = f'assets/{kind}_group{group:03d}.pt'
            require(update['head_checkpoint'] == path, 'update/group checkpoint binding')
            require(update['initial_actor_sha256'] == previous_head[kind] == self.records[path]['head_sha256'], 'head update chain')
            require(update['initial_critic_sha256'] == previous_critic[kind] == self.records[path]['metadata']['critic_sha256'],
                    'baseline update chain')
            data = self.rollouts[kind, group]
            require([r['world'] for r in data] == list(worlds) and all(r['tape'] == 0 for r in data), 'two on-policy episodes')
            require(all(r['head_sha256'] == previous_head[kind] and r['critic_sha256'] == previous_critic[kind] for r in data),
                    'same held head/critic within group')
            rewards = np.stack([r['rewards'] for r in data]).astype(np.float32)
            # Independent higher-precision accumulation of FP32 macro rewards;
            # stored targets retain the actual source FP32 cumsum and division.
            target64 = np.cumsum(rewards[:, ::-1].astype(np.float64), axis=1)[:, ::-1] / p.horizon
            targets = np.asarray(update['targets'], dtype=np.float32)
            require(targets.shape == target64.shape and np.isfinite(targets).all(), 'target array shape')
            target_tolerance = 4 * np.finfo(np.float32).eps * max(1., float(np.max(np.abs(target64))))
            equal(targets, target64, 'whole native suffix-return target', target_tolerance)
            values = np.stack([r['values'] for r in data])
            residual = (targets - values).astype(np.float32)
            center = residual.astype(np.float64).mean()
            spread = residual.astype(np.float64).std(ddof=0)
            expected_advantage = (residual.astype(np.float64) - center) / (spread + 1e-8)
            advantages = np.asarray(update['advantages'], dtype=np.float32)
            # Mean/std accumulation in the finite source is FP32. Expose its
            # conditioning instead of asserting a universal bitwise reduction.
            advantage_tolerance = 32 * np.finfo(np.float32).eps * max(1., float(np.max(np.abs(residual)))) / (spread + 1e-8)
            equal(advantages, expected_advantage, 'normalized two-episode team advantage', advantage_tolerance)
            d = p.horizon // 4
            delta = dict(actor_optimizer_steps=4, actor_replay_rows=40 * d,
                         critic_optimizer_steps=4, critic_replay_rows=8 * d,
                         density_identity_rows=10 * d, target_rows=2 * d,
                         actor_optimizer_attempts=4, critic_optimizer_attempts=4)
            require(update['counts_before'] == before and update['counts_delta'] == delta, 'exact update work exposure')
            before = {key: before[key] + delta[key] for key in COUNT_KEYS}
            require(update['counts_after'] == before, 'update counter continuation')
            ident = update['initial_identity']
            require(ident['logits_exact'] and ident['rows'] == 10 * d
                    and 0 <= ident['max_probability_abs'] <= 5e-14
                    and 0 <= ident['max_chosen_logp_abs'] <= 1e-10
                    and 0 <= ident['max_ratio_from_one'] <= 1e-10, 'first-epoch recorded density identity')
            require(len(update['epochs']) == 4, 'four full epochs only')
            for epoch, item in enumerate(update['epochs']):
                step = 4 * group + epoch + 1
                require(item['epoch'] == epoch and item['actor_step_completed'] and item['critic_step_completed'], 'complete epoch')
                require(item['actor_optimizer_step_values'] == [step] * 2
                        and item['critic_optimizer_step_values'] == [step] * 6, 'continuing Adam step values')
                for key in ('actor_loss', 'critic_loss', 'actor_grad_norm', 'critic_grad_norm',
                            'actor_movement_l2', 'critic_movement_l2', 'ratio_min', 'ratio_max', 'ratio_mean', 'clip_fraction'):
                    require(np.isfinite(item[key]), 'finite update diagnostic ' + key)
                require(0 < item['ratio_min'] <= item['ratio_mean'] <= item['ratio_max']
                        and 0 <= item['clip_fraction'] <= 1, 'ratio/clip diagnostic range')
            require(update['actor_optimizer_step_values'] == [4 * group + 4] * 2
                    and update['critic_optimizer_step_values'] == [4 * group + 4] * 6, 'terminal group Adam counts')
            require(update['final_actor_sha256'] == update['epochs'][-1]['actor_sha256']
                    and update['final_critic_sha256'] == update['epochs'][-1]['critic_sha256'], 'update terminal hash')
            previous_head[kind], previous_critic[kind] = update['final_actor_sha256'], update['final_critic_sha256']
            updates[kind, group] = update
            groups_by_kind[kind].append(path)
            self.calls['target_formula_rows'] += targets.size
            self.calls['update_records'] += 1
        result = {}
        for kind in HEADS:
            end = s['final_checkpoints'][kind]
            require(end['head_sha256'] == previous_head[kind] and end['critic_sha256'] == previous_critic[kind], 'final endpoint update chain')
            paths = groups_by_kind[kind] + [end['path']]
            for group in range(len(paths) - 1):
                a, b = self.payloads[paths[group]]['head_state'], self.payloads[paths[group + 1]]['head_state']
                movement = _movement(a, b)
                # The worker diagnostic uses an FP32 vector norm; the reader
                # accumulates squared differences in FP64. Bound the source
                # reduction/subtraction roundoff by its actual vector length.
                n = sum(value.numel() for value in a.values())
                gamma = (n + 8) * np.finfo(np.float32).eps
                tolerance = 2 * gamma / (1 - gamma) * max(movement, np.finfo(np.float32).tiny)
                equal(updates[kind, group]['actor_movement_l2'], movement,
                      'head movement from immutable states', tolerance)
                require(updates[kind, group]['final_actor_sha256'] == self.records[paths[group + 1]]['head_sha256'], 'next-group head identity')
            initial = self.payloads[s['initial_checkpoints'][kind]['path']]
            final = self.payloads[end['path']]
            result[kind] = dict(head_movement_l2=_movement(initial['head_state'], final['head_state']),
                                critic_movement_l2=_movement(initial['critic_state'], final['critic_state']),
                                optimizer_steps_per_network=len(p.train_worlds) * 2,
                                immutable_group_heads=len(groups_by_kind[kind]))
        require(all(s['actual'][key] == value for key, value in before.items()), 'worker/update total counts')
        return result

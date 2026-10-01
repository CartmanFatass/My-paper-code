"""Two fixed on-policy fits followed by the complete final S2/T2 panel."""
from datetime import datetime, timezone
import copy
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import Head
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import make_bundle
from .assets import load_inputs, preflight_inputs, save_checkpoint
from .collection import collect_episode
from .contract import ASSETS, BASE_PINS, FROZEN, HEADS, OBJECT, arm_parts, new_counts, source_identities, validate_counts
from .learning import fresh_critic, make_optimizers, update_group
from .reading import cost_totals, read_comparisons

ROOT = Path(__file__).resolve().parents[4]


def run_batch(out, launch_sha, *, input_dir, admission=None, protocol=FROZEN,
              scientific_invocation=False, factory=None, fixture_bindings=None,
              entry_wall=None, entry_cpu=None, collector=collect_episode, check=lambda: None):
    protocol.validate()
    production = factory is None
    if production:
        if (not scientific_invocation or not admission or admission.get('sha') != launch_sha
                or protocol != FROZEN or fixture_bindings is not None or collector is not collect_episode):
            raise ValueError('production requires the admitted complete fixed B09 contract')
        if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
            raise ValueError('production CPU thread contract')
        from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
        factory = make_real
        bindings = ASSETS
    else:
        if scientific_invocation or protocol == FROZEN or fixture_bindings is None:
            raise ValueError('synthetic fixtures must be explicit and nonproduction')
        bindings = fixture_bindings
        for name in ASSETS:
            if any(bindings[name][key] == ASSETS[name][key] for key in ('sha256', 'state_sha256')):
                raise ValueError('synthetic fixture may not use production asset bytes/tensors')
    start_wall = time.perf_counter() if entry_wall is None else entry_wall
    start_cpu = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {'launch-status.json', 'launch-manifest.json', 'admission-preflight.json', 'stdout.log', 'stderr.log'}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError('existing B09 scientific output: reconcile, never repeat')
    for name in ('raw', 'assets', 'updates'):
        (out / name).mkdir()
    counts = new_counts()
    batch = dict(object=OBJECT, status='INCOMPLETE', launch_sha=launch_sha,
                 scientific_invocation=scientific_invocation, protocol=protocol.to_dict(), expected=protocol.expected(),
                 actual=counts, rows=[], updates=[], group_heads=[], initial_checkpoints={}, final_checkpoints={},
                 start_utc=datetime.now(timezone.utc).isoformat(), admission=dict(admission or {}),
                 runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                              host=platform.node(), device='cpu', actor_dtype='float32', density_dtype='float64',
                              torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                              thread_environment={name: os.environ.get(name) for name in
                                                  ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}),
                 timing_scope='entry through final summary preparation including imports via run.py, all input checks/load, '
                 'constructor/reset/tapes, training-only critic outside local deadline, collection, immutable caches, '
                 'updates/checkpoints/serialization/close; final self-write and separately metered full reader excluded',
                 worker_cpu_estimate_seconds=[4200, 7200], reader_cpu_estimate_seconds=[900, 2400],
                 exposure_stop='fixed groups/four epochs/full final panel, no performance-dependent continuation')
    inflight, env, systems, live_update = {}, None, {}, None

    def publish():
        counts['optimizer_steps'] = counts['actor_optimizer_steps'] + counts['critic_optimizer_steps']
        batch.update(worker_wall_seconds=time.perf_counter() - start_wall,
                     worker_cpu_seconds=time.process_time() - start_cpu,
                     worker_process_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if batch['rows']:
            batch['costs'] = cost_totals(batch['rows'])
        write_json(out / 'summary.json', batch)

    def actor_unchanged():
        if state_digest(actor.state_dict()) != batch['inputs']['S']['state_sha256']:
            raise AssertionError('frozen backbone mutated')

    def collect(arm, world, tape, *, phase, head=None, critic=None, checkpoint=None, group=None):
        program, _ = arm_parts(arm)
        before = None if head is None else state_digest(head.state_dict())
        critic_before = None if critic is None else state_digest(critic.state_dict())
        row, rollout = collector(env, arm=arm, world=world, tape=tape, bundle=bundles.get((world, tape)),
                                 out=out, protocol=protocol, counts=counts, actor=actor,
                                 policy_sha=batch['inputs']['S']['state_sha256'] if program not in ('C', 'Q_I')
                                 else BASE_PINS['experiments/candidates/uav_local_history/b01/controller.py'],
                                 inflight=inflight, check=check, head=head, critic=critic)
        if head is not None and state_digest(head.state_dict()) != before:
            raise AssertionError('episode collection mutated its immutable group head')
        if critic is not None and state_digest(critic.state_dict()) != critic_before:
            raise AssertionError('episode collection mutated its baseline')
        row.update(phase=phase, group=group, head_sha256=before, critic_sha256=critic_before,
                   head_checkpoint=None if checkpoint is None else checkpoint['path'],
                   temperature=2. if program == 'Bstar' else 1.)
        batch['rows'].append(row)
        batch['progress'] = dict(completed=len(batch['rows']), total=batch['expected']['complete_episodes'],
                                 phase=phase, arm=arm, world=world, tape=tape, group=group)
        return rollout

    try:
        check()
        # Importing native factory above does not construct or query a host. This
        # preflight verifies accepted-snapshot/external input presence, not merely
        # availability in the author's shared checkout.
        batch['input_preflight'] = preflight_inputs(input_dir, bindings)
        batch['source_sha256'] = source_identities(ROOT)
        actor, transfers, batch['inputs'] = load_inputs(input_dir, bindings)
        bundles = {}
        for worlds, tapes in ((protocol.train_worlds, (0,)), (protocol.worlds, protocol.tapes)):
            for world in worlds:
                for tape in tapes:
                    bundles[world, tape] = make_bundle(world, tape, horizon=protocol.horizon,
                        public_root=protocol.public_root, departure_root=protocol.departure_root, tail_root=protocol.tail_root)
        batch['tape_provision'] = dict(unique_bundles=len(bundles),
            unique_integers=sum(a.size for b in bundles.values() for a in b.values()),
            unique_bytes=sum(a.nbytes for b in bundles.values() for a in b.values()),
            public_stream_used=False, policy_has_future_entries_or_roots=False, online_payload_bytes=0)
        for kind in HEADS:
            head = Head(kind)
            critic = fresh_critic(protocol.critic_seed)
            counts['critics'] += 1
            opts = make_optimizers(head, critic)
            systems[kind] = head, critic, opts
            batch['initial_checkpoints'][kind] = save_checkpoint(out, f'assets/{kind}_initial.pt', kind=kind,
                head=head, critic=critic, optimizers=opts,
                metadata=dict(launch_sha=launch_sha, stage='initial', critic_seed=protocol.critic_seed,
                              original_student_sha256=batch['inputs']['S']['state_sha256']))
        if len({record['critic_sha256'] for record in batch['initial_checkpoints'].values()}) != 1:
            raise AssertionError('fresh critic initialization is not matched')
        write_json(out / 'config.json', {key: batch[key] for key in
                   ('object', 'launch_sha', 'scientific_invocation', 'protocol', 'expected', 'inputs', 'source_sha256')})
        publish()
        inflight['phase'] = 'constructor'
        counts['constructor_calls'] += 1
        env = factory(protocol.train_worlds[0])
        counts['constructors'] += 1
        counts['constructor_resets'] += 1
        inflight.clear()
        for group, kind, worlds in protocol.training_schedule():
            check()
            if group == 0:
                counts['fits'] += 1
            head, critic, opts = systems[kind]
            actor_unchanged()
            checkpoint = save_checkpoint(out, f'assets/{kind}_group{group:03d}.pt', kind=kind, head=head,
                metadata=dict(launch_sha=launch_sha, group=group, worlds=list(worlds),
                              original_student_sha256=batch['inputs']['S']['state_sha256'],
                              critic_sha256=state_digest(critic.state_dict()),
                              optimizer_steps_per_network=group * 4))
            batch['group_heads'].append(checkpoint)
            counts['rollout_group_heads'] += 1
            rollouts = [collect(kind + '_S2', world, 0, phase='training', head=head, critic=critic,
                                checkpoint=checkpoint, group=group) for world in worlds]
            live_update = {}
            update_started_wall, update_started_cpu = time.perf_counter(), time.process_time()
            try:
                update_group(head, critic, *opts, rollouts, counts, horizon=protocol.horizon, live_record=live_update)
            finally:
                live_update.update(kind=kind, group=group, worlds=list(worlds), head_checkpoint=checkpoint['path'],
                                   wall_seconds=time.perf_counter() - update_started_wall,
                                   cpu_seconds=time.process_time() - update_started_cpu)
                path = out / 'updates' / f'{kind}_group{group:03d}.json'
                write_json(path, live_update)
                batch['updates'].append(dict(file_identity(path), path=str(path.relative_to(out)), kind=kind,
                                             group=group, status=live_update.get('status'),
                                             cpu_seconds=live_update['cpu_seconds'], wall_seconds=live_update['wall_seconds']))
            live_update = None
            actor_unchanged()
            del rollouts
            publish()
            if (group + 1) % 8 == 0:
                print('B09_TRAIN', kind, group + 1, 'of', len(protocol.train_worlds) // 2, flush=True)
        for kind, (head, critic, opts) in systems.items():
            batch['final_checkpoints'][kind] = save_checkpoint(out, f'assets/{kind}_final.pt', kind=kind,
                head=head, critic=critic, optimizers=opts,
                metadata=dict(launch_sha=launch_sha, stage='final', critic_seed=protocol.critic_seed,
                              optimizer_steps_per_network=len(protocol.train_worlds) * 2,
                              original_student_sha256=batch['inputs']['S']['state_sha256']))
        for index, (arm, world, tape) in enumerate(protocol.schedule()):
            check()
            program, _ = arm_parts(arm)
            checkpoint = batch['final_checkpoints'].get(program)
            head = systems[program][0] if program in HEADS else transfers.get(program)
            collect(arm, world, tape, phase='final', head=head, checkpoint=checkpoint)
            if (index + 1) % 16 == 0:
                actor_unchanged()
                publish()
                print('B09_FINAL', index + 1, 'of', batch['expected']['final_episodes'], flush=True)
        actor_unchanged()
        batch['asset_after_state_sha256'] = state_digest(actor.state_dict())
        if preflight_inputs(input_dir, bindings) != batch['input_preflight']:
            raise AssertionError('bound input files changed during execution')
        if source_identities(ROOT) != batch['source_sha256']:
            raise AssertionError('source changed during execution')
        validate_counts(batch)
        batch['comparisons'] = read_comparisons(batch['rows'], protocol)
        batch['bulk'] = dict(canonical_root=str(out), raw_files=len(batch['rows']),
                             raw_bytes=sum(row['raw']['bytes'] for row in batch['rows']),
                             identity_scope='one canonical raw copy; source/file/state identities in rows and checkpoints')
        batch['status'] = 'COMPLETE'
        batch['finish_utc'] = datetime.now(timezone.utc).isoformat()
    except BaseException as error:
        batch['status'] = 'INCOMPLETE'
        batch['failure'] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        batch['inflight'] = copy.deepcopy(inflight)
        if live_update is not None:
            batch['inflight_update'] = copy.deepcopy(live_update)
        # Preserve partially changed models and optimizer state as failure evidence;
        # this is not a resume/retry interface.
        for kind, (head, critic, opts) in systems.items():
            if not (out / 'assets' / (kind + '_failed.pt')).exists():
                batch.setdefault('failed_checkpoints', {})[kind] = save_checkpoint(out,
                    f'assets/{kind}_failed.pt', kind=kind, head=head, critic=critic, optimizers=opts,
                    metadata=dict(launch_sha=launch_sha, stage='failed', actual=copy.deepcopy(counts)))
        publish()
        raise
    finally:
        if env is not None and hasattr(env, 'close'):
            env.close()
    publish()
    return batch

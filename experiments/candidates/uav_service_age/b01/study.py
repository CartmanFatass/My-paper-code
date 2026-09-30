"""The fixed512-episode fit and seven-program complete native comparison."""

import json
import os
import platform
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_radio_activation.b01.protocol import ALL_ON, HORIZON, N, U, encode_map, mask_array
from experiments.candidates.uav_radio_activation.b01.study import factory, file_identity, write_json
from experiments.candidates.uav_radio_activation.b03.protocol import DELIVERY, HOLD
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler as NativeScheduler
from experiments.candidates.uav_registered_service.b01.scheduler import Scheduler as OldestScheduler
from experiments.candidates.uav_registered_service.b01.metrics import add_contact_raw
from experiments.candidates.uav_registered_service.b02.scheduler import Scheduler as GateScheduler
from experiments.candidates.uav_registered_service.b02.metrics import add_gate_raw
from experiments.candidates.uav_registered_service.b02 import study as retained
from .learner import Learner, innovations, parameter_digest, INIT_SEED, TRAIN_CHOICE_KEY, EVAL_CHOICE_KEY
from .metrics import add_age_raw, age_metrics, paired_reading

ROOT = Path(__file__).resolve().parents[4]
TRAIN_SEED, TRAIN_EPISODES = 29311000, 512
EVAL_SEED, WORLDS = 29312000, 64
ARMS = ('L0', 'L1', 'M', 'W', 'O', 'G', 'S2')
ARM_ORDERS = tuple(tuple(order[i:] + order[:i]) for order in (ARMS, tuple(reversed(ARMS))) for i in range(7))
NEW_ARMS = ('L', 'L0', 'L1', 'M', 'W')


def source_identities():
    existing = {row['path']: row for row in retained.source_identities()}
    for path in (ROOT / 'experiments/candidates/uav_service_age/b01').glob('*.py'):
        relative = str(path.relative_to(ROOT))
        existing[relative] = dict(file_identity(path), path=relative)
    return [existing[key] for key in sorted(existing)]


def frozen_config(launch_sha):
    from .features import FEATURE_SPEC
    return dict(object='UAV-SERVICE-AGE-B01', launch_sha=launch_sha,
                train_seeds=list(range(TRAIN_SEED, TRAIN_SEED + TRAIN_EPISODES)),
                evaluation_seeds=list(range(EVAL_SEED, EVAL_SEED + WORLDS)), arms=list(ARMS),
                arm_orders=[list(order) for order in ARM_ORDERS], horizon=HORIZON,
                initialization_seed=INIT_SEED, train_choice_key=TRAIN_CHOICE_KEY,
                evaluation_choice_key=EVAL_CHOICE_KEY,
                rng='NumPy PCG64 SeedSequence([choice_key,world_seed]),64 clock-indexed uniforms',
                planned_fits=1, planned_training_episodes=512, planned_evaluation_episodes=448,
                planned_episodes=960, planned_steps=245760,
                delivery_ticks=2, hold_ticks=4, deadline_seconds=1.456, transmission_seconds=.544,
                objective='sum actual postmove service age / (50*256); served resets0; unserved +1; initial0',
                reward='negative actual age over report[t,t+3]/12800; gamma1; zero terminal bootstrap',
                learner=dict(hidden=64, activation='tanh', dtype='float32', device='cpu',
                             hidden_initializer='orthogonal gain sqrt2, zero bias',
                             actor_head='all zero', critic_head='orthogonal gain1, zero bias',
                             epochs=4, rows=64, adam_lr=.0003, adam_betas=[.9,.999], adam_eps=1e-5,
                             weight_decay=0, ppo_clip=.2, gradient_norm=.5, entropy=.01,
                             actor_denominator=64, critic_loss='.5 mean squared finite RTG error',
                             advantages='RTG minus fixed pre-update legal critic; unnormalized',
                             evaluation='sampled L0/L1; final endpoint only; no evaluation updates'),
                feature_spec=FEATURE_SPEC,
                upper_work=dict(candidate_requests=12353536, candidate_state_reductions=49028096,
                                scoring_geometry_snapshots=6583680, history_prefix_terminal_reductions=344064),
                source_identities=source_identities(),
                candidate_physics_read='all selected O/W plans and all evaluated pairs at reports0/60/124/252; all keys/contacts/history checked; shared physical kernels',
                cpu_limit_seconds=None)


def allocate_raw(horizon, arm, sites, map_packet):
    storage_arm = 'O' if arm in NEW_ARMS else arm
    raw = retained.allocate_raw(horizon, storage_arm, sites, map_packet)
    raw['program'] = np.array(arm)
    return raw


def record_round(raw, arrival, tick, arm):
    """Common frozen record plus all newly named causal decision arrays."""
    index = int(raw['round_count'])
    retained.record_round(raw, arrival, tick, 'O' if arm in NEW_ARMS else arm)
    if arm in NEW_ARMS:
        # The scheduler advertises exactly the extra stable-shape fields. The last
        # candidate block is padded only in the common recorder, never scored padded.
        for key in arrival['extra_record_fields']:
            value = np.asarray(arrival[key])
            target = 'age_' + key
            if target not in raw:
                raw[target] = np.zeros((len(raw['round_tick']),) + value.shape, dtype=value.dtype)
            if raw[target].shape[1:] != value.shape:
                raise ValueError(f'nonstationary decision field shape: {key}')
            raw[target][index] = value


def episode_metrics(raw, steps, arm):
    result = retained.episode_metrics(raw, steps, 'O' if arm in NEW_ARMS else arm)
    result.update(age_metrics(raw, steps))
    if arm in NEW_ARMS:
        # Detailed choices remain in raw; complete exposure counts cannot remove worlds.
        for name in ('alias', 'sampled', 'sampled_late', 'forced_before_sampling'):
            if 'age_' + name in raw:
                result[name + '_slots'] = int(raw['age_' + name].sum())
    return result


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON,
                    selector=None, training=False, scheduler_type=None,
                    controller_type=LocalController):
    """No parameters change here. Actual service is confined to reward and recording."""
    if arm not in ARMS + ('L',) or not 8 <= horizon <= HORIZON or horizon % 4:
        raise ValueError('complete four-tick episode horizon required')
    from .scheduler import Scheduler
    started, cpu_started = time.perf_counter(), time.process_time()
    obs, reset_info = env.reset(seed=seed)
    counts['explicit_resets'] += 1
    if obs.shape != (N, 104) or not env.env.transmitter_mask.all():
        raise RuntimeError('incorrect native observation or reset mask')
    sites = np.array(reset_info['state_info']['user_positions'], copy=True)
    map_packet = encode_map(sites)
    scheduler_arm = 'L' if arm in ('L', 'L0', 'L1') else arm
    chosen = scheduler_type or {'O': OldestScheduler, 'G': GateScheduler, 'S2': NativeScheduler}.get(arm, Scheduler)
    scheduler = chosen(scheduler_arm, map_packet, horizon=horizon)
    controllers = [controller_type(history=False) for _ in range(N)]
    raw = allocate_raw(horizon, arm, sites, map_packet)
    raw['world_seed'] = np.array(seed)
    raw['training_episode'] = np.array(training)
    raw['choice_innovations'] = innovations(seed, training=training)[:horizon // HOLD]
    raw['positions'][0] = np.array(reset_info['state_info']['uav_positions'], copy=True)
    raw['observations'][0] = obs
    actual = np.zeros((N, 3), dtype=np.float32)
    proposals = actual.copy()
    current_mask, pending, pending_at, pairs = ALL_ON, None, None, None
    failure = None
    try:
        for tick in range(horizon):
            reporting = tick % HOLD == 0
            c_start, c_cpu = time.perf_counter(), time.process_time()
            if reporting:
                pairs = [controller.act(obs[i].copy(), tick) for i, controller in enumerate(controllers)]
                proposals = np.array([pair[0] for pair in pairs], dtype=np.float32)
                raw['c_called'][tick] = raw['c_decision'][tick] = True
                raw['c_wall'][tick], raw['c_cpu'][tick] = time.perf_counter() - c_start, time.process_time() - c_cpu
            if tick == 0:
                actual = proposals.copy()
            raw['commands'][tick], raw['proposals'][tick], raw['mask'][tick] = actual, proposals, current_mask
            for key in ('fallback', 'selected_index'):
                raw[key][tick] = [pair[1][key] for pair in pairs]
            raw['n_current'][tick] = (obs[:, 3:63].reshape(N, 20, 3)[:, :, 2] > 0).sum(axis=1)
            raw['n_visible_peers'][tick] = (obs[:, 63:103].reshape(N, 10, 4)[:, :, 3] > 0).sum(axis=1)
            if reporting:
                optional = dict(selector=selector, innovation=float(raw['choice_innovations'][tick // HOLD])) if arm in NEW_ARMS else {}
                pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), proposals.copy(), tick,
                                           current_mask, started=c_start, cpu_started=c_cpu, **optional)
                pending_at = tick + DELIVERY
                record_round(raw, pending, tick, arm)
            counts['native_step_calls'] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts['team_steps'] += 1
            if arm != 'S2':
                scheduler.executed(tick, actual.copy(), int(current_mask))
            global_info = info['infos_dict']['uav_0']['global']
            # Arriving masks mutate radio arrays. Preserve actual postmove service first.
            sinr = np.array(global_info['sinr_matrix'], dtype=np.float64, copy=True)
            connected = np.array(global_info['connections'], dtype=bool, copy=True)
            served = int(connected.sum())
            quality = float(np.clip((sinr[connected] - 3) / 30, 0, 1).sum() / max(served, 1))
            reward = sum(float(value) for value in info['rewards_dict'].values())
            if not np.isclose(reward, .7 * served / U + .3 * quality, atol=1e-12, rtol=0):
                raise RuntimeError('preserved actual transition disagrees with native reward')
            raw['sinr'][tick], raw['connections'][tick] = sinr, connected
            raw['served'][tick], raw['quality'][tick], raw['reward'][tick] = served, quality, reward
            raw['positions'][tick + 1] = np.array(info['state_info']['uav_positions'], copy=True)
            raw['completed_steps'][...] = tick + 1
            if bool(terminated or truncated) != (tick + 1 == horizon):
                raise RuntimeError('unexpected native terminal boundary')
            if pending is not None and tick + 1 == pending_at:
                current_mask = pending['mask']
                actual = np.array(pending['commands'], dtype=np.float32, copy=True)
                env.env.set_transmitter_mask(mask_array(current_mask))
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
                pending, pending_at = None, None
            obs = next_obs
            raw['observations'][tick + 1] = obs
    except Exception as exc:
        failure = exc
    finally:
        if arm != 'S2':
            wall, cpu = time.perf_counter(), time.process_time()
            before = scheduler.execution.next_unsettled
            ready = False
            try:
                _, ready = scheduler.execution.settle(int(raw['completed_steps']))
            except Exception as support_failure:
                raw['terminal_support_failure_type'] = np.array(type(support_failure).__name__)
                raw['terminal_support_failure_message'] = np.array(str(support_failure))
                if failure is None:
                    failure = support_failure
            settled, start_tick = scheduler.execution.next_unsettled, scheduler.execution.start_tick
            raw['terminal_history_start'] = np.array(-1 if start_tick is None else start_tick)
            if start_tick is not None:
                raw['model_valid'][start_tick:settled] = True
            for tick, served in scheduler.execution.predicted.items():
                raw['model_contacts'][tick] = served
            raw['terminal_history_complete'][...] = ready
            raw['terminal_history_reductions'][...] = settled - before
            raw['terminal_history_wall'][...] = time.perf_counter() - wall
            raw['terminal_history_cpu'][...] = time.process_time() - cpu
            raw['terminal_last'] = scheduler.execution.history.last.copy()
            raw['terminal_windows'] = scheduler.execution.history.windows.copy()
        raw['episode_failure_type'] = np.array('' if failure is None else type(failure).__name__)
        raw['episode_failure_message'] = np.array('' if failure is None else str(failure))
        steps = int(raw['completed_steps'])
        add_contact_raw(raw, steps)
        add_age_raw(raw, steps)
        if arm == 'G':
            add_gate_raw(raw, steps)
        keys = tuple(controllers[0].counters)
        raw['controller_counter_keys'] = np.array(keys)
        raw['controller_counts'] = np.array([sum(c.counters[key] for c in controllers) for key in keys])
        if failure is not None:
            np.savez_compressed(Path(out) / 'raw' / f'{arm}_{seed}.npz', **raw)
    if failure is not None:
        raise failure
    counts['complete_episodes'] += 1
    row = dict(arm=arm, seed=seed, steps=horizon, **episode_metrics(raw, horizon, arm),
               controller_counts=dict(zip(keys, raw['controller_counts'].tolist())),
               wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started)
    return row, raw


def save_episode(out, row, raw):
    path = Path(out) / 'raw' / f"{row['arm']}_{row['seed']}.npz"
    wall, cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **raw)
    row['raw'] = file_identity(path)
    row['storage_wall_seconds'] = time.perf_counter() - wall
    row['storage_cpu_seconds'] = time.process_time() - cpu


def run_batch(out, launch_sha, *, entry_start=None, admission=None):
    from .features import FEATURE_DIM
    out = Path(out).resolve()
    if (out / 'config.json').exists() or (out / 'summary.json').exists():
        raise FileExistsError('result output already has scientific records; no implicit resume')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'raw').mkdir(exist_ok=True)
    started = time.perf_counter() if entry_start is None else entry_start
    cpu_started = time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    config = frozen_config(launch_sha)
    write_json(out / 'config.json', config)
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0,
                  complete_episodes=0, fit_started=0, fit_completed=0,
                  actor_updates=0, critic_updates=0, training_episodes=0, evaluation_episodes=0)
    summary = dict(object='UAV-SERVICE-AGE-B01', status='RUNNING', launch_sha=launch_sha,
                   scientific_invocation=True, config=config, counts=counts, training=[], rows=[],
                   admission=admission,
                   runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                                host=platform.node(), platform=platform.platform()))
    env = learner = None
    try:
        env = factory(TRAIN_SEED)
        counts['constructors'] += 1
        env.env.max_steps = HORIZON
        counts['fit_started'] += 1
        learner = Learner(FEATURE_DIM)
        initial = Learner(FEATURE_DIM)
        torch.save(learner.state(), out / 'raw' / 'initial.pt')
        summary['initial_checkpoint'] = file_identity(out / 'raw' / 'initial.pt')
        for episode, seed in enumerate(config['train_seeds']):
            actor_before = parameter_digest(learner.actor)
            critic_before = parameter_digest(learner.critic)
            row, raw = collect_episode(env, 'L', seed, out, counts, selector=learner.probabilities, training=True)
            if parameter_digest(learner.actor) != actor_before or parameter_digest(learner.critic) != critic_before:
                raise AssertionError('policy changed inside an episode')
            raw['actor_before_sha256'] = np.array(actor_before)
            raw['critic_before_sha256'] = np.array(critic_before)
            raw['episode_index'] = np.array(episode)
            update_wall, update_cpu = time.perf_counter(), time.process_time()
            try:
                update, arrays = learner.update(raw['age_features'], raw['age_sampled_choice'],
                                                raw['age_logp'], raw['age_sampled'], raw['report_rewards'])
            except Exception as update_failure:
                raw['learner_failure_type'] = np.array(type(update_failure).__name__)
                raw['learner_failure_message'] = np.array(str(update_failure))
                row['learner_wall_seconds'] = time.perf_counter() - update_wall
                row['learner_cpu_seconds'] = time.process_time() - update_cpu
                save_episode(out, row, raw)
                summary['failed_training_episode'] = row
                raise
            row['learner_wall_seconds'] = time.perf_counter() - update_wall
            row['learner_cpu_seconds'] = time.process_time() - update_cpu
            row['update'] = update
            raw.update({f'learning_{key}': value for key, value in arrays.items()})
            save_episode(out, row, raw)
            counts['training_episodes'] += 1
            counts['actor_updates'], counts['critic_updates'] = learner.actor_updates, learner.critic_updates
            summary['training'].append(row)
            write_json(out / 'summary.json', summary)
            print(json.dumps(dict(stage='training', episode=episode + 1, completed=counts['complete_episodes'],
                                  steps=counts['team_steps'], A=row['A'], sampled=update['sampled_slots'])), flush=True)
        counts['fit_completed'] += 1
        torch.save(learner.state(), out / 'raw' / 'final.pt')
        summary['final_checkpoint'] = file_identity(out / 'raw' / 'final.pt')
        final_actor, final_critic = parameter_digest(learner.actor), parameter_digest(learner.critic)
        summary['learner'] = dict(actor_updates=learner.actor_updates, critic_updates=learner.critic_updates,
                                  episodes_updated=learner.episodes_updated, actor_sha256=final_actor,
                                  critic_sha256=final_critic,
                                  actor_displacement=summary['training'][-1]['update']['actor_displacement'],
                                  critic_displacement=summary['training'][-1]['update']['critic_displacement'])
        for index, seed in enumerate(config['evaluation_seeds']):
            for arm in ARM_ORDERS[index % len(ARM_ORDERS)]:
                selector = initial.probabilities if arm == 'L0' else learner.probabilities if arm == 'L1' else None
                row, raw = collect_episode(env, arm, seed, out, counts, selector=selector)
                save_episode(out, row, raw)
                counts['evaluation_episodes'] += 1
                summary['rows'].append(row)
                write_json(out / 'summary.json', summary)
                print(json.dumps(dict(stage='evaluation', arm=arm, seed=seed,
                                      completed=counts['complete_episodes'], steps=counts['team_steps'], A=row['A'])), flush=True)
        if parameter_digest(learner.actor) != final_actor or parameter_digest(learner.critic) != final_critic:
            raise AssertionError('evaluation changed final learner')
        if parameter_digest(initial.actor) != summary['training'][0]['update']['before_actor_sha256']:
            raise AssertionError('initial policy changed')
        summary['paired'] = paired_reading(summary['rows'], config['evaluation_seeds'], ARMS)
        summary['status'] = 'COMPLETE'
        summary['fixed_policy_evaluation_counts'] = dict(episodes=448, transitions=114688,
                                                        optimizer_updates=0, parameter_updates=0)
    except Exception as exc:
        summary['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        summary['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        if learner is not None:
            torch.save(learner.state(), out / 'raw' / 'failed_endpoint.pt')
            summary['failed_checkpoint'] = file_identity(out / 'raw' / 'failed_endpoint.pt')
    finally:
        if env is not None:
            env.close()
        if learner is not None:
            counts['actor_updates'], counts['critic_updates'] = learner.actor_updates, learner.critic_updates
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary['resources'] = dict(wall_seconds=time.perf_counter() - started,
                                    measured_cpu_seconds=time.process_time() - cpu_started,
                                    process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
                                    peak_rss_kib=usage.ru_maxrss, rss_scope='worker lifetime peak; Linux KiB',
                                    scope='entry wall includes imports; measured_cpu starts after study import; process CPU includes import/init',
                                    torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                                    thread_environment={key:os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})
        summary['artifacts'] = [file_identity(path) for path in sorted((out / 'raw').iterdir()) if path.is_file()]
        write_json(out / 'summary.json', summary)
    return summary

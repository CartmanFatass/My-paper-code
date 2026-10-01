"""H8 synthetic integration: no native host or production policy asset queries."""
import copy
import json
from pathlib import Path
import shutil

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers, model
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import Head
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_radio_activation.b01 import protocol as ep
from experiments.candidates.uav_radio_activation.b01.read import observed_rows, radio
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import make_bundle
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_coordinator import coordinator_counts, verify_coordinator
from experiments.candidates.uav_parent_adaptation.b09_managed_development import assets, collection, policies, read, study, verify_local
from experiments.candidates.uav_parent_adaptation.b09_managed_development.contract import ASSETS, FROZEN, Protocol, base_arm, new_counts
from experiments.candidates.uav_parent_adaptation.b09_managed_development.learning import fresh_critic
from experiments.candidates.uav_parent_adaptation.b09_managed_development.verify_learning import LearningAudit

SMALL = Protocol(train_worlds=(71701, 71702, 71703, 71704), worlds=(71721, 71722),
                 public_root=71811, departure_root=71812, tail_root=71813, critic_seed=71801, horizon=8)


class SyntheticHost:
    def __init__(self, seed):
        self.env = self
        self.agents = [f'uav_{i}' for i in range(5)]
        self.transmitter_mask = np.ones(5, bool)
        self.sinr = np.empty((5, 50))
        self.connections = np.zeros((5, 50), bool)
        self.reset(seed)

    def reset(self, seed):
        rng = np.random.RandomState(seed)
        self.positions = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)] for _ in range(5)])
        self.users = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
        self.tick = 0
        self.transmitter_mask[:] = True
        self.refresh()
        return self.observations.copy(), self.info()

    def refresh(self):
        mask = sum(int(active) << i for i, active in enumerate(self.transmitter_mask))
        sinr, connections, self.metrics = radio(self.positions, self.users, mask)
        self.sinr[:], self.connections[:] = sinr, connections
        self.observations = observed_rows(self.positions, self.users, mask, self.tick)
        self.observations[:, -1] = self.tick / SMALL.horizon

    def set_transmitter_mask(self, mask):
        self.transmitter_mask[:] = mask
        self.refresh()

    def _get_observation(self, agent):
        return self.observations[int(agent.split('_')[-1])].copy()

    def _dict_to_array(self, values):
        return np.asarray([values[agent] for agent in self.agents], np.float32)

    def info(self):
        state = np.concatenate((self.positions.ravel(), self.users.ravel(), [self.tick / SMALL.horizon])).astype(np.float32)
        return dict(state=state.copy(), next_state=state.copy(),
                    state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={'uav_0': {'global': dict(sinr_matrix=self.sinr, connections=self.connections)}},
                    rewards_dict={agent: self.metrics['J'] / 5 for agent in self.agents})

    def step(self, commands):
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30., ep.LOW, ep.HIGH)
        self.tick += 1
        self.refresh()
        return self.observations.copy(), 0., False, self.tick == SMALL.horizon, self.info()


def synthetic_inputs(root):
    root.mkdir(parents=True)
    actor = model.make_student(71901)
    state = actor.state_dict()
    digest = model.state_digest(state)
    torch.save(dict(architecture=[114, 128, 128, 27], dtype='float32', activation='relu',
                    state_dict=state, state_sha256=digest), root / 'S.pt')
    bindings = {'S': dict(file_identity(root / 'S.pt'), state_sha256=digest)}
    for kind in ('CAL', 'CONT'):
        head = Head(kind)
        with torch.no_grad():
            head.b.copy_(torch.linspace(-.2, .2, 27))
            if kind == 'CONT':
                head.W.copy_(torch.linspace(-.03, .03, 27 * 128).reshape(27, 128))
            else:
                head.alpha.fill_(.1)
        state = head.state_dict()
        path = root / (kind + '_all.pt')
        torch.save(dict(schema='uav_fleet_adaptation.b05.head.v1', endpoint=kind, lineage=0,
                        dtype='float32', hidden_size=128, output_size=27,
                        original_student_sha256=digest, state_dict=state, state_sha256=model.state_digest(state)), path)
        bindings[kind + '_all'] = dict(file_identity(path), state_sha256=model.state_digest(state))
    return bindings


@pytest.fixture(scope='module')
def batch(tmp_path_factory):
    old_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp('b09-synthetic-complete')
    bindings = synthetic_inputs(root / 'inputs')
    out = root / 'result'
    try:
        result = study.run_batch(out, 'synthetic-only', protocol=SMALL, input_dir=root / 'inputs',
                                 factory=SyntheticHost, fixture_bindings=bindings)
        yield out, result, root / 'inputs', bindings
    finally:
        torch.set_num_threads(old_threads)


def load_raw(out, row):
    with np.load(out / row['raw']['path'], allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def counts():
    return dict(read.local_counts(), **read.coordinator_counts(), new_head_attempts=0, new_head_completed=0,
                transfer_head_attempts=0, transfer_head_completed=0, bstar_applications=0, critic_input_rows=0,
                checkpoint_files=0, critic_initialization_reconstructions=0, target_formula_rows=0, update_records=0)


def test_exact_selected_exposure_and_order():
    e = FROZEN.expected()
    assert e['complete_episodes'] == 1024 and e['native_steps'] == 262144
    assert e['fits'] == e['critics'] == 2 and e['target_rows'] == 32768
    assert e['actor_optimizer_steps'] == e['critic_optimizer_steps'] == 1024
    assert e['optimizer_steps'] == 2048 and e['actor_replay_rows'] == 655360
    assert e['density_identity_rows'] == 163840 and e['critic_replay_rows'] == 131072
    assert e['controller_requests'] == 327680 and e['c_requests'] == 40960 and e['s_requests'] == 286720
    assert e['new_head_rows_ceiling'] == 204800 and e['transfer_head_rows_ceiling'] == 40960 and e['bstar_rows_ceiling'] == 20480
    assert e['s2_candidate_requests_ceiling'] == 7364608 and e['s2_candidate_plans_ceiling'] == 7110656
    assert e['s2_state_reductions_ceiling'] == 28220416 and e['t2_candidate_requests_ceiling'] == 1714176
    assert e['t2_state_reductions_ceiling'] == 6803136 and e['coordinator_geometry_ceiling'] == 7022592
    assert e['coordinator_user_links_ceiling'] == 1755648000
    assert e['recurring_bytes_ceiling'] == 8912896 and e['map_bytes_provisioned'] == 409600
    assert e['sampling_decisions'] == 307200 and e['private_integer_reads'] == 614400
    assert e['unique_tape_bundles'] == 320 and e['unique_tape_integers'] == 225280 and e['unique_maps'] == 288
    assert e['reader_native_observation_formula_checks'] == 328704
    assert e['reader_candidate_state_reductions_ceiling'] == 1300480
    groups = list(FROZEN.training_schedule())
    assert groups[:4] == [(0, 'CAL', (29841000, 29841001)), (0, 'CONT', (29841000, 29841001)),
                          (1, 'CONT', (29841002, 29841003)), (1, 'CAL', (29841002, 29841003))]
    final = list(FROZEN.schedule())
    assert len(final) == len(set(final)) == 512 and len(groups) == 256
    assert final[:4] == [('C_S2', 29843000, -1), ('C_T2', 29843000, -1), ('Q_I_S2', 29843000, 0), ('Q_I_S2', 29843000, 1)]
    assert not set(FROZEN.train_worlds) & set(FROZEN.worlds)


def test_admission_and_fixture_guards_precede_queries(tmp_path, monkeypatch):
    from experiments.candidates.uav_parent_adaptation.b09_managed_development import run
    from scripts import hmasd_admission
    called = []
    monkeypatch.setattr(study, 'load_inputs', lambda *args: called.append('load'))
    with pytest.raises(ValueError, match='admitted'):
        study.run_batch(tmp_path / 'native', 'bad', input_dir=tmp_path)
    with pytest.raises(ValueError, match='nonproduction'):
        study.run_batch(tmp_path / 'fixture', 'bad', input_dir=tmp_path, factory=SyntheticHost)
    wrong = {name: dict(sha256='synthetic', state_sha256='synthetic') for name in ASSETS}
    wrong['CAL_all']['state_sha256'] = ASSETS['CAL_all']['state_sha256']
    with pytest.raises(ValueError, match='production asset'):
        study.run_batch(tmp_path / 'alias', 'bad', input_dir=tmp_path, protocol=SMALL,
                        factory=SyntheticHost, fixture_bindings=wrong)
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic admission refusal')
    monkeypatch.setattr(hmasd_admission, 'require_admission', refuse)
    with pytest.raises(RuntimeError, match='admission refusal'):
        run.main(['--out', str(tmp_path / 'b09_managed_development_a01'), '--seed', '29840911',
                  '--launch-sha', 'bad', '--input-dir', str(tmp_path)])
    assert not called and not list(tmp_path.iterdir())


def test_all_assets_present_before_any_model_load(tmp_path, monkeypatch):
    bindings = synthetic_inputs(tmp_path / 'inputs')
    (tmp_path / 'inputs' / 'CONT_all.pt').unlink()
    called = []
    monkeypatch.setattr(assets, 'load_asset', lambda *args: called.append('load'))
    with pytest.raises(FileNotFoundError, match='required staged'):
        study.run_batch(tmp_path / 'result', 'synthetic-only', protocol=SMALL, input_dir=tmp_path / 'inputs',
                        factory=lambda seed: called.append('construct'), fixture_bindings=bindings)
    summary = json.loads((tmp_path / 'result' / 'summary.json').read_text())
    assert not called and summary['actual']['native_steps'] == summary['actual']['critics'] == summary['actual']['fits'] == 0


def test_complete_group_training_final_panel_and_reader(batch, monkeypatch):
    out, summary, inputs, bindings = batch
    assert summary['status'] == 'COMPLETE'
    assert summary['actual']['complete_episodes'] == 40 and summary['actual']['native_steps'] == 320
    assert summary['actual']['fits'] == summary['actual']['critics'] == 2
    assert len(summary['group_heads']) == len(summary['updates']) == 4
    assert summary['asset_after_state_sha256'] == summary['inputs']['S']['state_sha256']
    def forbidden(*args, **kwargs):
        raise AssertionError('reader acquired an undeclared query')
    monkeypatch.setattr(SyntheticHost, 'step', forbidden)
    monkeypatch.setattr(controllers.MemoC, 'query', forbidden)
    monkeypatch.setattr(torch.optim, 'Adam', forbidden)
    monkeypatch.setattr(study, 'update_group', forbidden)
    result = read.read_batch(out, permit_fixture=True)
    assert result['status'] == 'VERIFIED'
    assert result['reader_calls']['S_forward_completed'] == 320
    assert result['reader_calls']['new_head_completed'] == 160
    assert result['reader_calls']['transfer_head_completed'] == 80
    assert result['reader_calls']['bstar_applications'] == 40
    assert result['reader_calls']['critic_input_rows'] == result['reader_calls']['target_formula_rows'] == 16
    assert result['reader_calls']['critic_forward_rows'] == result['reader_calls']['optimizer_steps'] == 0
    assert result['reader_calls']['native_formula_completed'] == 440
    assert len(result['comparisons']['paired']) == 36
    for kind in ('CAL', 'CONT'):
        assert result['learning'][kind]['head_movement_l2'] > 0
        assert result['learning'][kind]['critic_movement_l2'] > 0
    with pytest.raises(FileExistsError, match='reconcile paid work'):
        read.read_batch(out, permit_fixture=True)
    with pytest.raises(FileExistsError, match='never repeat'):
        study.run_batch(out, 'synthetic-only', protocol=SMALL, input_dir=inputs, factory=SyntheticHost, fixture_bindings=bindings)


def test_training_baseline_is_before_startup_and_later_proposals(batch):
    out, summary, _, _ = batch
    for row in summary['rows']:
        raw = load_raw(out, row)
        if row['phase'] != 'training':
            assert not any(key.startswith('critic_') for key in raw)
            continue
        np.testing.assert_array_equal(raw['critic_actual'][0], np.zeros((5, 3), np.float32))
        np.testing.assert_array_equal(raw['coord_actual'][0], raw['proposals'][0])
        np.testing.assert_array_equal(raw['critic_actual'][1], raw['commands'][3])
        np.testing.assert_array_equal(raw['critic_nav'], raw['nav_pre'])
        verify_local.verify_critic_inputs(raw, row, SMALL, counts())


@pytest.mark.parametrize('field', ['hidden', 'base_logits', 'logits', 'logp', 'critic_features', 'critic_actual', 'critic_nav', 'macro_rewards'])
def test_saved_learning_context_tampering_rejected(batch, field):
    out, summary, inputs, bindings = batch
    row = summary['rows'][0]
    raw = load_raw(out, row)
    raw[field].flat[0] += 1
    actor, transfers, _ = assets.load_inputs(inputs, bindings)
    audit = LearningAudit(out, summary, SMALL, counts())
    head = audit.head_for(row, transfers)
    bundle = make_bundle(row['world'], 0, horizon=8, public_root=SMALL.public_root,
                         departure_root=SMALL.departure_root, tail_root=SMALL.tail_root)
    with pytest.raises(AssertionError):
        verify_local.verify_local(raw, row, SMALL, actor, head, bundle, counts(), lambda: None)
        verify_local.verify_critic_inputs(raw, row, SMALL, counts())


@pytest.mark.parametrize('after', [0, 120])
def test_late_search_retains_actual_commands_mask_and_readable_training(tmp_path, after):
    inputs = tmp_path / 'inputs'
    bindings = synthetic_inputs(inputs)
    actor, _, _ = assets.load_inputs(inputs, bindings)
    head, critic = Head('CAL'), fresh_critic(SMALL.critic_seed)
    out = tmp_path / 'late'
    (out / 'raw').mkdir(parents=True)
    def factory(kind, packet, horizon):
        scheduler = Scheduler(kind, packet, horizon=horizon)
        original = scheduler.decide
        def decide(*args, **kwargs):
            start, count = kwargs['started'], [0]
            def clock():
                count[0] += 1
                return start + (10. if count[0] > after else 0.)
            scheduler.clock = clock
            return original(*args, **kwargs)
        scheduler.decide = decide
        return scheduler
    world = 71741
    bundle = make_bundle(world, 0, horizon=8, public_root=SMALL.public_root,
                         departure_root=SMALL.departure_root, tail_root=SMALL.tail_root)
    row, raw = collection.collect_episode(SyntheticHost(world), arm='CAL_S2', world=world, tape=0,
        bundle=bundle, out=out, protocol=SMALL, counts=new_counts(), actor=actor, policy_sha='synthetic',
        inflight={}, check=lambda: None, head=head, critic=critic, coordinator_factory=factory)
    row.update(phase='training')
    assert not raw['coord_timely'].any() and raw['transmitter_mask'].all()
    np.testing.assert_array_equal(raw['commands'], np.broadcast_to(raw['proposals'][0], (8, 5, 3)))
    verify_local.verify_critic_inputs(raw, row, SMALL, counts())
    verify_coordinator(raw, {**row, 'arm': base_arm(row['arm'])}, SMALL, coordinator_counts(), lambda: None)
    if after:
        assert raw['coord_state_reductions'].sum() > 0


def test_innovations_follow_all_five_queries_and_cache_context_is_immutable(monkeypatch):
    host = SyntheticHost(71751)
    actor = model.make_student(71902)
    team = policies.ManagedTeam('S_I', host.observations.copy(), actor, head=Head('CONT'))
    calls, saved = [], {}
    original = policies.frozen_forward
    def forward(*args):
        calls.append('query')
        return original(*args)
    monkeypatch.setattr(policies, 'frozen_forward', forward)
    def coins():
        assert calls == ['query'] * 5
        saved['hidden'] = np.stack([p.latest['hidden'] for p in team.policies]).copy()
        for p in team.policies:
            p.latest['hidden'][:] = 999  # Cannot change the pre-coin learning context.
        calls.append('coins')
        return dict(private_depart=np.arange(5, dtype=np.uint64), private_tail=np.arange(5, dtype=np.uint64))
    decision = team.decide(host.observations.copy(), 0, coins)
    assert calls == ['query'] * 5 + ['coins']
    np.testing.assert_array_equal(decision['record']['hidden'], saved['hidden'])
    assert decision['sampling_decisions'] == 5


def test_failed_transition_retains_partial_costs_raw_and_models(batch, tmp_path):
    class Failing(SyntheticHost):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError('synthetic transition failure')
            return super().step(commands)
    out = tmp_path / 'failed'
    with pytest.raises(RuntimeError, match='synthetic transition failure'):
        study.run_batch(out, 'synthetic-only', protocol=SMALL, input_dir=batch[2], factory=Failing, fixture_bindings=batch[3])
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['actual']['native_step_calls'] == 3 and summary['actual']['native_steps'] == 2
    assert summary['actual']['actor_optimizer_steps'] == 0 and len(summary['failed_checkpoints']) == 2
    assert summary['inflight']['raw']['sha256']
    raw = load_raw(out, dict(raw=summary['inflight']['raw']))
    assert not raw['episode_complete'] and raw['completed_steps'] == 2

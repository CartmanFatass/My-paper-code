"""Frozen B09 comparison, identities and complete work exposure."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.contract import ASSET
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.contract import (
    PINS as BASE_PINS, Protocol as BaseProtocol, new_counts as base_counts,
)

OBJECT = 'UAV-PARENT-MANAGED-DEVELOPMENT-B09'
ARMS = ('C_S2', 'C_T2', 'Q_I_S2', 'S_I_S2', 'CAL_S2', 'CONT_S2',
        'CAL_all_S2', 'CONT_all_S2', 'Bstar_S2')
HEADS = ('CAL', 'CONT')
ASSETS = {
    'S': dict(ASSET),
    'CAL_all': dict(bytes=15395, sha256='5b4a91a483239ac97e0dfa44cd1edbeb8b2c2e2050a58bf5587d383e0f4c026f',
                    state_sha256='f57a8824576cd8be9c993c18129e49fc8bbfa04c577752b595e07f5a2a605810'),
    'CONT_all': dict(bytes=56753, sha256='f179c83a9f07e78eaea0fbd78b3ec3895d79f5cd4669f22dab15569e23c65eb5',
                     state_sha256='ba75b800025725ef1db0b94ca2ebbe83a3addde70b194696cf133f882bf6e38d'),
}
# Additional inherited source identities are inserted before source publication.
ADDITIONAL_PINS = {'experiments/candidates/uav_fleet_adaptation/b04_native_development/__init__.py': '1b895cb24c21a2ae44f93beb580c78f247d81fde8bbbd4fc75947ff583818bdc',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/assets.py': 'c7941d73f1cfcbf3f054a70129d9149e6f1723768d5a8e8e60372ddbdbd0459c',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/collect.py': '8085697e1c4572ea18f4e6eb49073d299670336683d7e9bd216972ae7229eb5d',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py': '55155fbc690fc7030978849e3c6e8052745ad9f2bd0efe4fe188c4852ea9de36',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/learning.py': '93dccde51527c9bc25718530500b764ddc0d9ff84ab34446a9a50b584a535aa7',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/policies.py': '3dde95d7a21d8f54e67fbd2e2c5ae72f8322d5aa24d94974446cd9fb6343559f',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/read.py': '77750845b658ae72b7e0bd8e486e82235f770ed9632a96d3cf9bc373bd5b69a7',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/reading.py': '7cacf84f962cd6cff118268df06e0f891289d5db74ca147b2ac045a6c88955c1',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/run.py': '5b8c24ca07d836d7fea54383bee878a736462aa427da7cceab0ba6d9380e672b',
 'experiments/candidates/uav_fleet_adaptation/b04_native_development/study.py': '5c7df36ec1f0a3a7ce550d21eb769bb31d90fd8312a61627cbb5be80cb62c5d5',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/__init__.py': '60c6ca76c7ce20cf1ab55206a6e0b9361c4de68b4c45ed6c288b55fc908aa5cd',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/assets.py': 'bc3394b66493126b2e71bf86cb17850ed3d506356b3fb22b5f498bbca79c7917',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/collect.py': 'b16f26c8c7a70927ce5f9ed7f6262275ca890883e8976437baa26d658ffaa22f',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/contract.py': 'c76d5a1b196ceace4c4d59d81f43a10608e135d88502a9c29ce5a67f8ef1e543',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/learning.py': '37247b67c95a9956e8cc610dc2f43b509d081b866f4ea2c1d8c12b313f9f7a96',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/policies.py': 'cf06f2299bf6b378643a2a3adf01c08c55d5387dfb733144441db43660a1d4b9',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/read.py': 'd02d617f06461285d7a58c2a6335ced960a38e2ad8feebdfd9116849253d01fc',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/reading.py': 'cd090d06737f0d14e21cef0d0d258f1a02605d182a8cd328a33ab8fc10f0b6ea',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/run.py': 'c2f3e5ec44d4d9b6002d8b394b235f20e3780d6b8194c614ea11006b72383fa4',
 'experiments/candidates/uav_fleet_adaptation/b05_native_consequence/study.py': '1fbf3da37309dd3dff5cc9a6f7f2d1d113f02fcb544d1beaa3dbeb61dc5dfec9',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/read.py': 'a33b66013b85ce7e3bf757566c5e9304458e15e540ee8c54e336e46364aa3560',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/sampling.py': '0c4319269711627670a76ca0f020dafd5672b411b0c015df68f45116eb78f9a5',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/study.py': '7a5c11b8e8897a8991cba62c2bb96fb8727aadafa3319eb3d1d293a3d5f9e89a',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/__init__.py': '9612d2c495dce06769639be1e8c14b8fed9ab78d7806ddb8f4b554c39781f654',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/collection.py': '80166fb69a3afcc721e52e2387f17f4d1cdec373baa94796070aac67f4d8fefc',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/contract.py': 'e43b6006e3a2589912861972ae7fee5e70053b706c171b63af2685fc362c86b0',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/policies.py': '3a91939a9418bc925224944f1ce10cefc29c976681126cb1fd2658be8b7afc99',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/read.py': '7aa56b79a628dff0484acc850385b4bb7f28f79075be40233d8da763e05fad32',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/reading.py': 'ae659cbecf7ccba5bb3873d0a466d49d5c64616dc661f1e2fe16ebbc108a23eb',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/run.py': 'bdef533f2a337dd2e6b37a41a1fd461543706de26ffc8bdbf2f4f5e51ecd1d20',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/study.py': '3b7e7fb98e6276998ffcc2f857bc24a5814e0d61701f621efb1288894cd79037',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/verify_coordinator.py': '76a16d842b0627df1c640fcd7b8397a10739640ccf36639aaff99690712c587a',
 'experiments/candidates/uav_parent_adaptation/b05_radio_composition/verify_local.py': 'dbbd5aa1effdfd09a6430fcef14fc3972047ed4535169da5beafbe3bb5aaf075'}


def arm_parts(arm):
    if arm not in ARMS:
        raise ValueError('unknown B09 arm')
    return arm.rsplit('_', 1)


def base_arm(arm):
    family, coordinator = arm_parts(arm)
    return f'{family if family in ("C", "Q_I") else "S_I"}_{coordinator}'


@dataclass(frozen=True)
class Protocol(BaseProtocol):
    train_worlds: tuple[int, ...] = tuple(range(29841000, 29841256))
    worlds: tuple[int, ...] = tuple(range(29843000, 29843032))
    public_root: int = 29840911
    departure_root: int = 29840912
    tail_root: int = 29840913
    critic_seed: int = 29840901

    def validate(self):
        super().validate()
        w = self.train_worlds
        if (not w or len(w) % 2 or len(set(w)) != len(w)
                or any(type(v) is not int or v < 0 for v in w)
                or set(w) & set(self.worlds) or type(self.critic_seed) is not int or self.critic_seed < 0):
            raise ValueError('disjoint even complete training worlds and fresh critic seed required')
        return self

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        for key in ('worlds', 'train_worlds', 'tapes'):
            value[key] = tuple(value[key])
        return cls(**value).validate()

    def training_schedule(self):
        for group in range(len(self.train_worlds) // 2):
            worlds = self.train_worlds[2 * group:2 * group + 2]
            for kind in HEADS if group % 2 == 0 else HEADS[::-1]:
                yield group, kind, worlds

    def schedule(self):
        order = tuple((arm, tape) for arm in ARMS
                      for tape in ((-1,) if arm.startswith('C_') else self.tapes))
        for index, world in enumerate(self.worlds):
            shift = index % len(order)
            rotated = order[shift:] + order[:shift]
            for arm, tape in rotated[::-1] if index % 2 else rotated:
                yield arm, world, tape

    def expected(self):
        self.validate()
        n, m, h = len(self.train_worlds), len(self.worlds), self.horizon
        d = h // 4
        train, final, total = 2 * n, 16 * m, 2 * n + 16 * m
        s2, t2 = total - m, m
        joint_states = h - 2
        c, s = 4 * m * d * 5, (total - 4 * m) * d * 5
        stochastic = total - 2 * m
        tapes = n + 2 * m
        return dict(fits=2, critics=2, expert_labels=0, optimizer_steps=8 * n,
                    training_episodes=train, final_episodes=final, complete_episodes=total,
                    native_steps=total * h, constructor_resets=1, explicit_resets=total,
                    rollout_group_heads=n, actor_optimizer_steps=4 * n,
                    critic_optimizer_steps=4 * n, actor_replay_rows=train * d * 5 * 4,
                    density_identity_rows=train * d * 5, critic_replay_rows=train * d * 4,
                    collected_critic_rows=train * d, target_rows=train * d,
                    policy_blocks=total * d, controller_requests=total * d * 5,
                    c_requests=c, s_requests=s,
                    c_candidate_paths_ceiling=c * 27, c_model_ticks_ceiling=c * 108,
                    c_candidate_power_ceiling=c * 108 * 20, c_setup_power_ceiling=c * 100,
                    s_forward_rows_ceiling=s, s_helper_calls_ceiling=s,
                    s_helper_power_ceiling=s * 140,
                    new_head_rows_ceiling=(train + 4 * m) * d * 5,
                    transfer_head_rows_ceiling=4 * m * d * 5, bstar_rows_ceiling=2 * m * d * 5,
                    sampling_decisions=stochastic * d * 5, private_integer_reads=stochastic * d * 10,
                    unique_tape_bundles=tapes, unique_tape_integers=tapes * d * 11,
                    unique_tape_bytes=tapes * d * 11 * 8,
                    s2_episodes=s2, t2_episodes=t2, coordinator_rounds=total * d,
                    s2_candidate_requests_ceiling=s2 * d * 116,
                    s2_candidate_plans_ceiling=s2 * d * 112,
                    s2_state_reductions_ceiling=s2 * joint_states * 112,
                    t2_candidate_requests_ceiling=t2 * d * 837,
                    t2_state_reductions_ceiling=t2 * joint_states * 837,
                    coordinator_geometry_ceiling=total * joint_states * 27,
                    coordinator_user_links_ceiling=total * joint_states * 27 * 250,
                    recurring_bytes_ceiling=total * d * 136, map_bytes_provisioned=total * 400,
                    unique_maps=n + m, reader_s_forward_rows=s, reader_s_helper_calls=s,
                    reader_c_ranking_queries=0,
                    reader_candidate_state_reductions_ceiling=total * joint_states * 5,
                    reader_native_observation_formula_checks=total * (h + d + 1),
                    reader_native_steps=0)


FROZEN = Protocol().validate()


def new_counts():
    result = base_counts()
    result.update(critics=0, actor_optimizer_steps=0, critic_optimizer_steps=0,
                  actor_replay_rows=0, critic_replay_rows=0, density_identity_rows=0,
                  target_rows=0, collected_critic_rows=0, rollout_group_heads=0)
    return result


def source_identities(repo):
    repo = Path(repo)
    result = {}
    for relative, expected in {**BASE_PINS, **ADDITIONAL_PINS}.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('frozen inherited source drift: ' + relative)
        result[relative] = actual
    for path in sorted(Path(__file__).parent.glob('*.py')):
        result[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def validate_counts(batch):
    actual, expected = batch['actual'], batch['expected']
    for key in ('fits', 'critics', 'expert_labels', 'optimizer_steps', 'complete_episodes', 'native_steps',
                'constructor_resets', 'explicit_resets', 'rollout_group_heads',
                'actor_optimizer_steps', 'critic_optimizer_steps', 'actor_replay_rows',
                'critic_replay_rows', 'density_identity_rows', 'target_rows',
                'collected_critic_rows', 'policy_blocks', 'sampling_decisions', 'private_integer_reads'):
        if actual[key] != expected[key]:
            raise AssertionError((key, actual[key], expected[key]))
    for key in ('coordinator_round_calls', 'coordinator_round_returns', 'mask_setter_calls', 'mask_setter_returns'):
        if actual[key] != expected['coordinator_rounds']:
            raise AssertionError((key, actual[key], expected['coordinator_rounds']))
    for key, target in (('constructor_calls', 1), ('constructors', 1),
                        ('explicit_reset_calls', expected['explicit_resets']),
                        ('native_step_calls', expected['native_steps']),
                        ('policy_block_calls', expected['policy_blocks']),
                        ('collected_critic_attempts', expected['collected_critic_rows']),
                        ('actor_optimizer_attempts', expected['actor_optimizer_steps']),
                        ('critic_optimizer_attempts', expected['critic_optimizer_steps'])):
        if actual[key] != target:
            raise AssertionError((key, actual[key], target))
    costs = batch['costs']
    if costs['C']['requests'] != expected['c_requests'] or costs['S']['requests'] != expected['s_requests']:
        raise AssertionError('complete local query count')
    for observed, limit in ((costs['C']['model_ticks'], expected['c_model_ticks_ceiling']),
                            (costs['S']['neural_rows'], expected['s_forward_rows_ceiling']),
                            (costs['S']['helper_calls'], expected['s_helper_calls_ceiling'])):
        if observed > limit:
            raise AssertionError('local work exceeds selected exposure')
    for name in ('S2', 'T2'):
        for field in ('candidate_requests', 'state_reductions'):
            if costs[name][field] > expected[name.lower() + '_' + field + '_ceiling']:
                raise AssertionError('coordinator work exceeds selected exposure')

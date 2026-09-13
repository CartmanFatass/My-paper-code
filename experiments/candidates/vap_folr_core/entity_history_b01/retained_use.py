"""One outcome-informed fixed-reference use, with one fresh Generic realization."""
from .publication import arm_result


USE_OBJECT = 'FOLR_RETAINED_REFERENCE_USE_B01_781301'
GENERIC_SEED, GENERIC_EVALUATION_SEED = 781301, 1781301
BANK_TRAINING_SEED, BANK_EVALUATION_SEED = 781201, 2781301


def load_retained_bank(path):
    import torch
    from .model import Actor

    saved = torch.load(path, map_location='cpu', weights_only=True)
    if saved['arm'] != 'BANK' or saved['updates'] != 4969:
        raise ValueError('retained input must be the accepted final BANK checkpoint')
    actor = Actor('BANK')
    actor.load_state_dict(saved['actor'], strict=True)
    return actor.eval().requires_grad_(False)


def require_generic_endpoint(generic):
    expected = dict(object=USE_OBJECT, arm='GENERIC_RETAIN', status='complete',
                    training_seed=GENERIC_SEED, evaluation_seed=GENERIC_EVALUATION_SEED,
                    training_episodes=5000, training_ticks=100000, optimizer_steps=4969,
                    evaluation_episodes=128, evaluation_ticks=2560)
    if any(generic.get(key) != value for key, value in expected.items()):
        raise ValueError('the new selected Generic full endpoint is required before BANK')
    return arm_result(generic['evaluation_returns'])


def reference_use_result(generic, bank):
    g = require_generic_endpoint(generic)
    expected = dict(object=USE_OBJECT, arm='BANK', status='complete', training_seed=None,
                    retained_training_seed=BANK_TRAINING_SEED,
                    evaluation_seed=BANK_EVALUATION_SEED, training_episodes=0,
                    training_ticks=0, optimizer_steps=0, evaluation_episodes=128,
                    evaluation_ticks=2560)
    if any(bank.get(key) != value for key, value in expected.items()):
        raise ValueError('the fixed BANK new panel with zero new learning is required')
    b = arm_result(bank['evaluation_returns'])
    difference = b['mean'] - g['mean']
    rule = ('OPTIONAL_BANK_REFERENCE' if difference > 1 else
            'GENERIC_ONLY_BANK_WORSE' if difference < -1 else 'GENERIC_ONLY_WITHIN_MEI')
    return dict(generic=g, fixed_bank=b, d_use=difference, rule=rule, mei=1.0,
                fresh_generic_training_instances=1, retained_bank_policies=1,
                new_bank_training_instances=0, training_pairs=0, paired_difference_se=None,
                uncertainty='Episode dispersion conditional on one fresh Generic and one outcome-informed, completion-conditioned historical BANK; separate streams, no pairing or training-population uncertainty.',
                claim='Optional executable-reference inclusion on this exact public-information host only.')

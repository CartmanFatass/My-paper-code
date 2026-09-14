"""Identity and collected-Generic binding for the B02 fresh-learning pair."""

OBJECT = 'FOLR_ENTITY_HISTORY_B02_781401'
TRAINING_SEED = 781401
EVALUATION_SEED = 1781401
COMPLETE_EXPOSURE = (5000, 100000, 4969, 128, 2560)


def require_generic(summary):
    """Accept only this object's technically collected Generic arm."""
    if (summary.get('object'), summary.get('arm'), summary.get('status')) not in (
            (OBJECT, 'GENERIC_RETAIN', 'complete'),
            (OBJECT, 'GENERIC_RETAIN', 'incomplete')):
        raise ValueError('BANK requires the technically collected B02 Generic arm')
    if (summary.get('training_seed'), summary.get('evaluation_seed')) != (
            TRAINING_SEED, EVALUATION_SEED):
        raise ValueError('BANK requires the selected B02 Generic seed binding')
    return summary


def complete_exposure(summary):
    return tuple(summary.get(key) for key in (
        'training_episodes', 'training_ticks', 'optimizer_steps',
        'evaluation_episodes', 'evaluation_ticks')) == COMPLETE_EXPOSURE

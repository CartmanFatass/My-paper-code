"""Finite native endpoint and whole-package reading; no episode pairing claim."""
import math
import statistics


def arm_result(values):
    if len(values) != 128 or not all(math.isfinite(x) for x in values):
        raise ValueError('the final native panel must contain 128 finite returns')
    sd = statistics.stdev(values)
    return dict(mean=statistics.mean(values), sample_sd=sd,
                conditional_episode_se=sd / math.sqrt(len(values)),
                minimum=min(values), maximum=max(values), n=len(values))


def pair_result(generic, bank):
    for summary, arm in ((generic, 'GENERIC_RETAIN'), (bank, 'BANK')):
        if summary['status'] != 'complete' or summary['arm'] != arm:
            raise ValueError('both selected arms require complete technical output')
        if (summary['training_episodes'], summary['optimizer_steps'],
                summary['evaluation_episodes']) != (5000, 4969, 128):
            raise ValueError('the selected whole-arm exposure is incomplete')
    if (generic['training_seed'], generic['evaluation_seed']) != (bank['training_seed'], bank['evaluation_seed']):
        raise ValueError('different selected seed binding')
    g, b = arm_result(generic['evaluation_returns']), arm_result(bank['evaluation_returns'])
    difference = b['mean'] - g['mean']
    rule = 'BANK_ABOVE_MEI' if difference > 1 else 'GENERIC_ABOVE_MEI' if difference < -1 else 'WITHIN_MEI'
    return dict(generic=g, bank=b, bank_minus_generic=difference, rule=rule,
                mei=1.0, training_pairs=1, paired_difference_se=None,
                uncertainty='Per-arm episode dispersion conditional on each fitted policy; shared seed labels do not establish exogenous episode coupling or training-population uncertainty.',
                claim='Exploratory whole-package native comparison on the selected public-information host.')

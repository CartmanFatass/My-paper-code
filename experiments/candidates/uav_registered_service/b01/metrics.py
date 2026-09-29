"""Evaluation-only periodic endpoints and continuous task-censored unserved gaps."""

import numpy as np


def contact_gaps(contacts):
    contacts = np.asarray(contacts, dtype=bool)
    if contacts.ndim != 2 or contacts.shape[1] != 50:
        raise ValueError('expected transition by registered-user contacts')
    horizon = len(contacts)
    gap_rows, contact_rows = [], []
    for user in range(50):
        contact_rows.extend((user, int(tick)) for tick in np.flatnonzero(contacts[:, user]))
        start = None
        for tick in range(horizon + 1):
            absent = tick < horizon and not contacts[tick, user]
            if absent and start is None:
                start = tick
            if not absent and start is not None:
                gap_rows.append((user, start, tick, tick - start, int(start == 0), int(tick == horizon)))
                start = None
    return (np.asarray(contact_rows, dtype=int).reshape(-1, 2),
            np.asarray(gap_rows, dtype=int).reshape(-1, 6))


def window_bits(contacts):
    return np.array([contacts[start:min(start + 64, len(contacts))].any(axis=0)
                     for start in range(0, len(contacts), 64)], dtype=bool)


def periodic_metrics(contacts):
    contacts = np.asarray(contacts, dtype=bool)
    bits = window_bits(contacts)
    _, gaps = contact_gaps(contacts)
    lengths = gaps[:, 3]
    closed = gaps[(gaps[:, 4] == 0) & (gaps[:, 5] == 0), 3]
    ever = contacts.any(axis=0)
    maxima = np.array([max(gaps[gaps[:, 0] == u, 3], default=0) for u in range(50)])
    def aggregate(values):
        return dict(count=len(values), mean=float(np.mean(values)) if len(values) else None,
                    maximum=int(max(values)) if len(values) else None)
    return dict(F=int(bits.sum()), per_window_coverage=bits.sum(axis=1).tolist(),
                satisfied_window_histogram=np.bincount(bits.sum(axis=0), minlength=5).tolist(),
                ever_served=int(ever.sum()), never_served=int((~ever).sum()),
                unserved_gaps=aggregate(lengths), closed_unserved_gaps=aggregate(closed),
                left_censored_gaps=int(gaps[:, 4].sum()), right_censored_gaps=int(gaps[:, 5].sum()),
                mean_user_max_unserved_gap=float(maxima.mean()), max_unserved_gap=int(maxima.max()))


def add_contact_raw(raw, steps):
    contacts = raw['connections'][:steps].any(axis=1)
    events, gaps = contact_gaps(contacts)
    raw.update(actual_contacts=contacts, actual_window_bits=window_bits(contacts),
               contact_events=events, unserved_gap_rows=gaps,
               gap_columns=np.array(['user','start_inclusive','end_exclusive','unserved_ticks','left_censored','right_censored']))


def estimate_metrics(raw, steps):
    valid = raw['model_valid'][:steps]
    predicted = raw['model_contacts'][:steps]
    actual = raw['connections'][:steps].any(axis=1)
    valid_windows = np.array([valid[start:min(start+64,steps)].all() for start in range(0,steps,64)])
    pbits, abits = window_bits(predicted), window_bits(actual)
    return dict(model_verified_transitions=int(valid.sum()),
                model_service_false_positive=int(((predicted & ~actual) & valid[:,None]).sum()),
                model_service_false_negative=int(((~predicted & actual) & valid[:,None]).sum()),
                model_complete_windows=int(valid_windows.sum()),
                model_window_false_positive=int(((pbits & ~abits) & valid_windows[:,None]).sum()),
                model_window_false_negative=int(((~pbits & abits) & valid_windows[:,None]).sum()))

"""Bounded native correctness only: one 30-step S/R prefix, never a result panel."""

import json

import numpy as np

from experiments.candidates.uav_persistent_service.b03.episode import LongMissionEpisode
from experiments.candidates.uav_persistent_service.b05.episode import ServiceShiftEpisode


def test_native_prefix_rng_and_saved_scheduler_contract(tmp_path):
    import torch

    torch.set_num_threads(1)
    episodes = []
    try:
        candidate = ServiceShiftEpisode(52292801)
        episodes.append(candidate)
        candidate.macro_step(candidate.controller.ordinary_action())
        reference = LongMissionEpisode(52292801, "R")
        episodes.append(reference)
        reference.macro_step(reference.controller.ordinary_action())
        left, right = candidate.arrays(), reference.arrays()
        assert np.array_equal(left["user_xy_m"], right["user_xy_m"])
        assert np.array_equal(left["rng_state_sha256_by_step"], right["rng_state_sha256_by_step"])
        assert np.array_equal(left["initial_native_battery"], right["initial_native_battery"])
        assert left["native_station_input_wh"].shape == (30, 2)
        scheduler = candidate.macros[0]["choice"]["scheduler"]
        assert scheduler["fallback"] is None
        assert scheduler["scheduler_snapshot_calls"] == 9
        assert scheduler["chosen_forecast"]["grid_bins"] == 40
        assert 0 in scheduler["candidate_actions"]
        result = candidate.save(tmp_path/"partial.npz", complete=False)
        saved = json.loads((tmp_path/"partial.decisions.json").read_text())
        assert saved["complete"] is False
        assert saved["macros"][0]["choice"]["scheduler"] == scheduler
        assert result["raw_bytes"] > 0
    finally:
        for episode in reversed(episodes):
            episode.close()

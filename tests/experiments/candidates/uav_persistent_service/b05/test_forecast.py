from dataclasses import replace

import numpy as np

from experiments.candidates.uav_persistent_service.b05.forecast import (
    ForecastInput, ForecastOption, _station_advance, forecast,
)


def view(*, battery=None, slots=(8, 8), options=(), modes=None, remaining=1200,
         charging=None, waiting=None, weights=None, draw_w=None):
    xyz = np.c_[np.zeros(8), np.zeros(8), np.full(8, 100.0)]
    return ForecastInput(
        xyz=xyz, stations=np.array([[0., 0., 100.], [500., 0., 100.]]),
        targets_xy=np.c_[np.full(8, 300.), np.zeros(8)],
        battery=np.asarray(battery if battery is not None else np.full(8, .6)),
        available=np.ones(8, dtype=bool),
        modes=np.asarray(modes if modes is not None else np.zeros(8, dtype=bool)),
        charging=np.asarray(charging if charging is not None else np.zeros(8, dtype=bool)),
        waiting=np.asarray(waiting if waiting is not None else np.zeros(8)),
        draw_w=np.asarray(draw_w if draw_w is not None else np.full(8, 168.49)),
        slots=np.asarray(slots), weights=np.asarray(weights if weights is not None else np.ones(8)/8),
        q0=.8, options=tuple(options), remaining=remaining,
        limp_power_w=168.49, max_power_w=350.,
    )


def test_charger_priority_is_post_consumption_then_wait_then_index():
    options = tuple(ForecastOption(i, 0, 600, 0, 0) for i in range(3))
    batteries = [.5, .5, .499] + [.8]*5
    # One slot. Member 2 has the lowest post-consumption battery, then waits.
    result = forecast(view(battery=batteries, slots=(1, 0), options=options,
                           charging=[True]*3+[False]*5, remaining=30,
                           waiting=[0, 100, 100]+[0]*5,
                           draw_w=[168.49, 168.49, 350.0]+[168.49]*5), None)
    assert result["grid_bins"] == 1
    assert result["battery_end"][2] > result["battery_end"][1]
    batteries = [.5]*3+[.8]*5
    equal_draw = [168.49]*8
    wait_first = forecast(view(battery=batteries, slots=(1, 0), options=options,
                               charging=[True]*3+[False]*5, remaining=30,
                               waiting=[0, 100, 0]+[0]*5, draw_w=equal_draw), None)
    assert wait_first["battery_end"][1] > wait_first["battery_end"][0]
    index_first = forecast(view(battery=batteries, slots=(1, 0), options=options,
                                charging=[True]*3+[False]*5, remaining=30,
                                draw_w=equal_draw), None)
    assert index_first["battery_end"][0] > index_first["battery_end"][1]
    # The aggregate six-member case has a signed deficit even when every dock is selected.
    six = tuple(ForecastOption(i, 0, 600, 0, 0) for i in range(6))
    six_result = forecast(view(battery=[.5]*8, slots=(1, 0), options=six,
                               charging=[True]*6+[False]*2, remaining=30,
                               draw_w=[1010.94/6]*8), None)
    assert sum(six_result["battery_end"][:6]) < 3.0


def test_docked_signed_stock_and_recharge_below_service_cutoff():
    option = ForecastOption(0, 0, 600, 0, 0)
    state = replace(view(battery=[0.0]+[.8]*7, slots=(1, 0), options=(option,),
                         remaining=30, draw_w=[350.]*8),
                    available=np.array([False]+[True]*7))
    result = forecast(state, None)
    assert np.isclose(result["battery_end"][0], (1000.-168.49)*30/(160*3600))
    assert result["depletion_ticks"] == 0
    assert result["member_bin_updates"] == 8
    away = replace(state, xyz=np.c_[np.full(8, 250.), np.zeros(8), np.full(8, 100.)],
                   options=(), remaining=1200)
    stranded = forecast(away, None)
    assert stranded["battery_end"][0] == 0
    assert stranded["depletion_ticks"] == 40
    assert stranded["readiness"][0] is None
    queued_f = replace(state, options=(), modes=np.array([True]+[False]*7),
                       charging=np.zeros(8, dtype=bool), waiting=np.array([10.]+[0.]*7))
    recovered = forecast(queued_f, None)
    assert np.isclose(recovered["battery_end"][0], (1000.-168.49)*30/(160*3600))


def test_no_invented_arrival_and_timeout_for_existing_charging_mismatch():
    missing = ForecastOption(0, 0, 120, 0, None, True)
    result = forecast(view(options=(missing,), slots=(0, 0), charging=[True]+[False]*7,
                           battery=[.2]+[.8]*7), None)
    assert result["release"][0] == 900
    assert result["readiness"][0] is None


def test_dwell_full_and_f_precedence_are_separate():
    dwelling = ForecastOption(0, 0, 120, 0, 0)
    result = forecast(view(options=(dwelling,), charging=[True]+[False]*7,
                           remaining=300), None)
    assert result["release"][0] == 120
    full = forecast(view(options=(dwelling,), charging=[True]+[False]*7,
                         battery=[.99]+[.8]*7, remaining=120), None)
    assert full["release"][0] == 30
    f_result = forecast(view(modes=[True]+[False]*7, weights=[.2]+[0.]*7,
                             battery=[.1]+[.8]*7, remaining=30), None)
    assert f_result["qhat"][0] < .8
    assert f_result["member_bin_updates"] == 8
    redirected = forecast(view(options=(ForecastOption(0, 1, 600, 0, None,
                                                        transfer=True),),
                               modes=[True]+[False]*7,
                               battery=[.1]+[.8]*7, remaining=30), None)
    assert redirected["release"][0] == 0
    inbound_timeout = forecast(view(options=(ForecastOption(0, 1, 600, 890, None,
                                                            transfer=True),),
                                    remaining=120), None)
    assert inbound_timeout["release"][0] == 30
    assert inbound_timeout["readiness"][0] == 60


def test_f_uses_normal_caps_until_actual_emergency_limp():
    start = np.array([0., 0., 100.])
    station = np.array([500., 0., 100.])
    normal_position, normal_arrived = _station_advance(start, station, 30, False)
    limp_position, limp_arrived = _station_advance(start, station, 30, True)
    assert normal_position[0] > 340  # 30 m/s outside 160 m, then 3 m/s docking.
    assert limp_position[0] == 90
    assert not normal_arrived and not limp_arrived
    far = ForecastOption(0, 1, 600, 0, None, transfer=True)
    normal = forecast(view(options=(far,), modes=[True]+[False]*7,
                           battery=[.1]+[.8]*7, remaining=30), None)
    limp = forecast(view(options=(far,), modes=[True]+[False]*7,
                         battery=[.04]+[.8]*7, remaining=30), None)
    assert normal["release"][0] == 0  # F takes the nearer station.
    assert limp["release"][0] == 0
    moving = np.c_[np.full(8, 250.), np.zeros(8), np.full(8, 100.)]
    direct_normal = forecast(replace(view(modes=[True]+[False]*7,
                                          battery=[.13]+[.8]*7, remaining=30), xyz=moving), None)
    direct_limp = forecast(replace(view(modes=[True]+[False]*7,
                                        battery=[.04]+[.8]*7, remaining=30), xyz=moving), None)
    assert .13-direct_normal["battery_end"][0] > .04-direct_limp["battery_end"][0]

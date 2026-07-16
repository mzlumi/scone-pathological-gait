import numpy as np
import pytest

from conftest import make_storage, square_contact
from scone_gait.cycles import extract_gait_cycles


def test_regular_walk_gives_alternating_cycles(walking_storage):
    cycles = extract_gait_cycles(walking_storage)
    assert [c.side for c in cycles[:4]] == ["l", "r", "l", "r"]
    # left is in swing at t=0 and touches down at 0.1 s; right is in stance at
    # t=0, so its first counted contact is at 0.7 s
    assert cycles[0].begin == pytest.approx(0.1, abs=0.006)
    assert cycles[1].begin == pytest.approx(0.7, abs=0.006)
    for c in cycles:
        assert c.duration == pytest.approx(1.2, abs=0.006)
        assert c.stance_fraction == pytest.approx(0.6, abs=0.01)
        assert c.length == pytest.approx(1.2, abs=0.006)
        assert c.velocity == pytest.approx(1.0, abs=0.01)


def test_cycles_are_sorted_by_start_time(walking_storage):
    begins = [c.begin for c in extract_gait_cycles(walking_storage)]
    assert begins == sorted(begins)


def test_incomplete_cycles_at_the_end_are_dropped(walking_storage):
    cycles = extract_gait_cycles(walking_storage)
    assert all(c.end <= walking_storage.time[-1] for c in cycles)
    # 6 s of data: left contacts at 0.1, 1.3, 2.5, 3.7, 4.9 give 4 complete
    # cycles; the next contact (6.1 s) is outside the data
    assert sum(c.side == "l" for c in cycles) == 4


def test_short_contact_is_merged_into_the_previous_cycle():
    dt = 0.01
    time = np.arange(0.0, 5.0, dt)
    # contacts at 0.5, 1.5, 2.5, 3.5, 4.5 s, each lasting 0.6 s
    grf = square_contact(time, 1.0, 0.6, phase=0.5)
    # a 0.05 s bump in the middle of the swing that starts at 2.1 s
    bump = (time >= 2.2) & (time < 2.25)
    grf = np.where(bump, 0.2, grf)
    sto = make_storage(
        time,
        {"leg0_l.grf_norm_y": grf, "leg0_l.cop_x": time, "leg0_l.cop_y": 0 * time, "leg0_l.cop_z": 0 * time},
    )
    cycles = extract_gait_cycles(sto)
    starts = [round(float(c.begin), 2) for c in cycles]
    assert starts == [0.5, 1.5, 2.5, 3.5]
    # the cycle cut short by the bump is extended to the next real contact
    assert cycles[1].end == pytest.approx(2.5)


def test_threshold_controls_contact_detection():
    time = np.arange(0.0, 4.0, 0.01)
    grf = square_contact(time, 1.0, 0.6, phase=0.5) * 0.5 + 0.01
    sto = make_storage(
        time,
        {"leg1_r.grf_norm_y": grf, "leg1_r.cop_x": time, "leg1_r.cop_y": 0 * time, "leg1_r.cop_z": 0 * time},
    )
    # the force never drops below 0.01 BW, so a 0.001 BW threshold sees no flight
    assert extract_gait_cycles(sto, force_threshold=0.001) == []
    # contacts at 0.5, 1.5, 2.5, 3.5 s; the flight after 3.5 s (at 4.1 s) is outside the data
    assert len(extract_gait_cycles(sto, force_threshold=0.1)) == 3


def test_missing_channels_give_no_cycles():
    sto = make_storage([0.0, 1.0], {"pelvis_tilt": [0.0, 0.0]})
    assert extract_gait_cycles(sto) == []

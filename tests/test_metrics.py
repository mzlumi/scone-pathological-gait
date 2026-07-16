import numpy as np
import pytest

from conftest import PERIOD, synthetic_walk
from scone_gait.analysis import analyze_gait
from scone_gait.metrics import foot_contact_index, gait_metrics


def test_metrics_of_a_synthetic_walk():
    sto = synthetic_walk()
    m = gait_metrics(sto, analyze_gait(sto))
    assert m.speed == pytest.approx(1.0, abs=0.02)
    assert m.stride_length == pytest.approx(1.2, abs=0.01)
    assert m.stride_duration == pytest.approx(1.2, abs=0.01)
    assert m.cadence == pytest.approx(100.0, abs=1.0)
    assert m.stance_percent == pytest.approx(60.0, abs=1.0)
    # contact values are sampled one 5 ms frame before the detected contact
    shift = 0.005 / PERIOD
    assert m.ankle_at_contact == pytest.approx(10 * np.sin(-2 * np.pi * shift) - 5, abs=0.01)
    assert m.ankle_peak_dorsiflexion_stance == pytest.approx(5.0, abs=0.1)
    assert m.ankle_peak_plantarflexion == pytest.approx(-15.0, abs=0.1)
    assert m.ankle_range == pytest.approx(20.0, abs=0.2)
    assert m.knee_at_contact == pytest.approx(35 - 25 * np.cos(2 * np.pi * (-shift - 0.3)), abs=0.01)
    assert m.knee_min_stance == pytest.approx(10.0, abs=0.1)
    assert m.knee_peak_swing == pytest.approx(60.0, abs=0.1)
    assert m.hip_peak_extension == pytest.approx(-20.0, abs=0.1)
    assert m.foot_contact_index == pytest.approx(0.25, abs=0.01)
    assert 0.0 <= m.fit_score <= 100.0


@pytest.mark.parametrize(
    "heel_offset, toe_offset, expected",
    [(0.0, 0.2, 0.0), (0.2, 0.0, 1.0), (0.1, 0.1, 0.5)],
)
def test_foot_contact_index_from_heel_to_toe(heel_offset, toe_offset, expected):
    sto = synthetic_walk(heel_offset, toe_offset)
    ga = analyze_gait(sto)
    assert foot_contact_index(sto, ga.cycles[0]) == pytest.approx(expected, abs=1e-9)


def test_metrics_as_dict_is_json_friendly():
    sto = synthetic_walk()
    d = gait_metrics(sto, analyze_gait(sto)).as_dict()
    assert set(d) >= {"speed", "ankle_at_contact", "foot_contact_index", "fit_score"}
    assert all(isinstance(v, float) for v in d.values())

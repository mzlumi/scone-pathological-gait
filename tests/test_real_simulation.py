"""Checks on a real SCONE result: the Deliverable 1 healthy gait.

tests/data/healthy_excerpt.sto keeps the channels the analysis uses from
results/healthy/0035_1.021_0.780.par.sto, and healthy_excerpt.par.txt is the
objective breakdown that sconecmd printed for the same solution.
"""

from pathlib import Path

import pytest

from scone_gait.analysis import analyze_gait
from scone_gait.metrics import gait_metrics
from scone_gait.results import read_report
from scone_gait.storage import read_sto

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def healthy():
    sto = read_sto(DATA / "healthy_excerpt.sto")
    return sto, analyze_gait(sto)


def test_speed_agrees_with_scone_gait_measure(healthy):
    sto, ga = healthy
    report = read_report(DATA / "healthy_excerpt.par.txt")
    scone_speed = report["Gait"]["step_velocity"].value
    # SCONE averages step length over step time from foot positions, this
    # package uses centre of pressure stride lengths: they agree within 3 %
    assert ga.speed == pytest.approx(scone_speed, rel=0.03)


def test_cycles_alternate_and_have_physiological_timing(healthy):
    _, ga = healthy
    assert len(ga.cycles) == 11
    sides = [c.side for c in ga.cycles]
    assert all(a != b for a, b in zip(sides, sides[1:]))
    for c in ga.cycles:
        assert 1.0 < c.duration < 1.5
        assert 0.55 < c.stance_fraction < 0.75


def test_healthy_gait_is_a_heel_strike_gait(healthy):
    sto, ga = healthy
    m = gait_metrics(sto, ga)
    assert abs(m.foot_contact_index) < 0.1
    assert m.ankle_at_contact > 0  # dorsiflexed at contact
    assert m.knee_peak_swing > 55


def test_fit_score_is_stable(healthy):
    _, ga = healthy
    assert ga.score == pytest.approx(72.11, abs=0.01)
    assert ga["Pelvic tilt"].fit == pytest.approx(100.0)

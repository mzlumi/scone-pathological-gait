import numpy as np
import pytest

from scone_gait.analysis import (
    PERCENT,
    GaitPlotSpec,
    analyze_gait,
    fit_percentage,
    load_template,
    parse_template,
)


def test_default_template_has_the_five_scone_plots():
    specs = load_template()
    assert [s.title for s in specs] == ["Pelvic tilt", "Hip angle", "Knee angle", "Ankle angle", "GRF"]
    assert all(s.has_norm and len(s.norm_lower) == 101 for s in specs)
    knee = specs[2]
    assert knee.channel_multiply == pytest.approx(-57.3)
    assert knee.left_channel.startswith("knee_angle_l;")


def test_norm_offset_is_added_to_the_band():
    ankle = load_template()[3]
    # the template stores ankle norms 20 degrees low and corrects them with norm_offset
    assert ankle.norm_lower[0] == pytest.approx(-25.1 + 20)
    assert ankle.norm_upper[0] == pytest.approx(-19.6 + 20)


def test_mean_and_std_norms():
    specs = parse_template(
        "GaitPlot { title = x left_channel = a right_channel = b row = 0 column = 0 "
        "norm_mean = [ 1 2 ] norm_std = [ 0.5 1 ] norm_offset = 1 }"
    )
    np.testing.assert_allclose(specs[0].norm_lower, [1.5, 2.0])
    np.testing.assert_allclose(specs[0].norm_upper, [2.5, 4.0])


def test_fit_is_100_inside_the_band_and_drops_outside():
    lower, upper = np.zeros(101), np.full(101, 2.0)
    assert fit_percentage(np.ones_like(PERCENT), lower, upper) == pytest.approx(100.0)
    # one band width above everywhere: error 1, fit 0
    assert fit_percentage(np.full_like(PERCENT, 4.0), lower, upper) == pytest.approx(0.0)
    # half a band width below everywhere: fit 50
    assert fit_percentage(np.full_like(PERCENT, -1.0), lower, upper) == pytest.approx(50.0)


def test_fit_uses_a_minimum_band_width():
    lower = upper = np.zeros(101)
    # zero-width band: the width is taken as 0.01, so an excess of 0.001 costs 10%
    assert fit_percentage(np.full_like(PERCENT, 0.001), lower, upper) == pytest.approx(90.0)


def test_channel_patterns_match_alternatives_and_wildcards(walking_storage):
    spec = GaitPlotSpec("k", "knee_angle_l;/jointset/knee_l/value", "knee_*_r")
    assert spec.channels(walking_storage, "l") == ["knee_angle_l"]
    assert spec.channels(walking_storage, "r") == ["knee_angle_r"]


def test_analysis_of_a_synthetic_walk(walking_storage):
    spec = GaitPlotSpec(
        "Knee", "knee_angle_l", "knee_angle_r", channel_multiply=2.0,
        norm_lower=np.full(101, -3.0), norm_upper=np.full(101, 3.0),
    )
    ga = analyze_gait(walking_storage, template=[spec])
    # 4 left cycles (contacts 0.1 ... 4.9 s) and 4 right cycles (0.7 ... 5.5 s),
    # minus the first 2 and the last one
    assert len(ga.cycles) == 5
    assert [c.side for c in ga.cycles] == ["l", "r", "l", "r", "l"]
    assert ga.stride_duration == pytest.approx(1.2, abs=0.01)
    assert ga.stride_length == pytest.approx(1.2, abs=0.01)
    assert ga.speed == pytest.approx(1.0, abs=0.02)
    assert ga.stance_fraction == pytest.approx(0.6, abs=0.01)

    knee = ga["Knee"]
    assert knee.curves.shape == (5, len(PERCENT))
    # the synthetic knee angle is sin(2 pi (t - phase) / 1.2), times 2 for
    # channel_multiply; sampling is shifted back by one 5 ms frame
    phase = {"l": 0.1, "r": 0.7}
    for row, cycle in zip(knee.curves, ga.cycles):
        t = cycle.begin + PERCENT * cycle.duration / 100.0 - 0.005
        expected = 2.0 * np.sin(2 * np.pi * (t - phase[cycle.side]) / 1.2)
        # linear interpolation of a 5 ms sampled sine: error below 2e-4
        np.testing.assert_allclose(row, expected, atol=2e-4)
    assert knee.fit == pytest.approx(100.0)
    assert ga.score == pytest.approx(100.0)
    assert set(knee.sides) == {"l", "r"}
    assert knee.side_curves("l").shape[0] == 3


def test_analysis_needs_enough_cycles(walking_storage):
    # 8 cycles in total; skipping 8 leaves nothing
    with pytest.raises(ValueError, match="gait cycles"):
        analyze_gait(walking_storage, skip_first=6, skip_last=2)


def test_plots_without_matching_channels_are_skipped(walking_storage):
    ga = analyze_gait(walking_storage)
    # the synthetic storage has knee angles and GRFs, but no pelvis, hip or ankle
    assert [p.spec.title for p in ga.plots] == ["Knee angle", "GRF"]
    with pytest.raises(KeyError):
        ga["Hip angle"]

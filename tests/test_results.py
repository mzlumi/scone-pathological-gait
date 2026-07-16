import pytest

from scone_gait.results import (
    best_result,
    parse_report,
    parse_result_name,
    read_par,
)

REPORT = """\
06:05:25 SCONE version 2.4.5-RC-2
06:05:25 Evaluating /work/results/runs/x/0012_18.754_13.052.par
06:06:08 Results written to /work/results/runs/x/0012_18.754_13.052.par.sto
06:06:08 result                    = 13.0521
06:06:08   Gait                    = 11.8542 <- 100 * (0.118542 > 0.05)
06:06:08     step_velocity         = 0.881458
06:06:08     step_count            = 15
06:06:08   Effort                  = 0.851042 <- 0.1 * 8.51042
06:06:08     effort                = 5802.97
06:06:08     distance              = 9.07164
06:06:08   DofLimits               = 0.205405
06:06:08     ankle_angle_l         = 0 <- 0.1 * 0
06:06:08     knee_angle_l          = 0.105793 <- 0.01 * (10.5793 > 5)
06:06:08   HeadStabilityY          = 0.0346006 <- 0.25 * 0.138402
06:06:08 simulation time           = 10
06:06:08 performance (x real-time) = 0.24146
"""


def test_read_par(tmp_path):
    f = tmp_path / "a.par"
    f.write_text(
        "pelvis_tilt.offset              \t-0.029105207\t-0.027006059\t0.0023249588\t\n"
        "S00111.soleus.KF                \t0.36811988\t0.415179\t0.018899608\t\n"
    )
    params = read_par(f)
    assert list(params) == ["pelvis_tilt.offset", "S00111.soleus.KF"]
    assert params["S00111.soleus.KF"].value == pytest.approx(0.36811988)
    assert params["S00111.soleus.KF"].mean == pytest.approx(0.415179)
    assert params["S00111.soleus.KF"].std == pytest.approx(0.018899608)


def test_read_par_rejects_malformed_lines(tmp_path):
    f = tmp_path / "b.par"
    f.write_text("only_two 1.0\n")
    with pytest.raises(ValueError, match="b.par:1"):
        read_par(f)


def test_parse_result_name():
    name = parse_result_name("results/x/0013_14.602_8.802.par")
    assert (name.generation, name.average, name.best) == (13, 14.602, 8.802)
    assert parse_result_name("InitParameters.par") is None
    assert parse_result_name("0013_14.602_8.802.par.sto") is None


def test_best_result_picks_lowest_objective(tmp_path):
    for n in ["0000_96.300_95.636.par", "0013_14.602_8.802.par", "0012_18.754_13.052.par",
              "InitParameters.par", "0013_14.602_8.802.par.sto"]:
        (tmp_path / n).write_text("")
    assert best_result(tmp_path).name == "0013_14.602_8.802.par"


def test_best_result_on_empty_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        best_result(tmp_path)


def test_parse_report_builds_the_measure_tree():
    result = parse_report(REPORT)
    assert result.value == pytest.approx(13.0521)
    assert [c.name for c in result.children] == ["Gait", "Effort", "DofLimits", "HeadStabilityY"]
    gait = result["Gait"]
    assert gait.value == pytest.approx(11.8542)
    assert gait.detail == "100 * (0.118542 > 0.05)"
    assert gait["step_velocity"].value == pytest.approx(0.881458)
    assert gait["step_count"].value == 15
    assert result["DofLimits"]["knee_angle_l"].detail == "0.01 * (10.5793 > 5)"
    with pytest.raises(KeyError):
        result["Missing"]


def test_parse_report_ignores_lines_after_the_tree():
    result = parse_report(REPORT)
    assert "simulation time" not in [c.name for c in result.children]


def test_parse_report_without_result_line():
    with pytest.raises(ValueError, match="result"):
        parse_report("15:00:00 nothing here\n")

import numpy as np
import pytest

from scone_gait.results import (
    best_result,
    init_file_name,
    parse_report,
    parse_result_name,
    read_history,
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


def test_best_result_ignores_a_warm_start_init_file(tmp_path):
    (tmp_path / "config.scone").write_text(
        'CmaOptimizer {\n\tinit_file = "../../results/healthy/0035_1.021_0.780.par"\n'
        "\tuse_init_file = true\n\tSimulationObjective { max_duration = 10 }\n}\n"
    )
    for n in ["0035_1.021_0.780.par", "0000_98.461_85.929.par", "0112_0.964_0.880.par"]:
        (tmp_path / n).write_text("")
    assert init_file_name(tmp_path) == "0035_1.021_0.780.par"
    assert best_result(tmp_path).name == "0112_0.964_0.880.par"


def test_init_file_name_without_config(tmp_path):
    assert init_file_name(tmp_path) is None


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


def test_read_history(tmp_path):
    f = tmp_path / "history.txt"
    f.write_text(
        "generation\tbest_fitness\tmedian_fitness\tpredicted_fitness\tfitness_progress\n"
        "0\t95.6\t96.3\t0\t0\n"
        "1\t95.4\t95.9\t8.3\t0.0018\n"
        "2\t96.0\t95.5\t-198\t0.006\n"
        "3\t64.8\t94.5\t-405\t0.01\n"
    )
    h = read_history(f)
    np.testing.assert_array_equal(h.generation, [0, 1, 2, 3])
    np.testing.assert_allclose(h.best, [95.6, 95.4, 96.0, 64.8])
    np.testing.assert_allclose(h.median, [96.3, 95.9, 95.5, 94.5])
    np.testing.assert_allclose(h.best_so_far, [95.6, 95.4, 95.4, 64.8])


def test_read_history_rejects_other_files(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("not a history\n")
    with pytest.raises(ValueError, match="history"):
        read_history(f)


def test_parse_report_without_result_line():
    with pytest.raises(ValueError, match="result"):
        parse_report("15:00:00 nothing here\n")

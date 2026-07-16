import json

import matplotlib.pyplot as plt
import numpy as np

from conftest import synthetic_walk
from scone_gait.analysis import analyze_gait, load_template
from scone_gait.cli import main
from scone_gait.plots import plot_comparison, plot_convergence, plot_gait, y_label
from scone_gait.results import History
from scone_gait.storage import write_sto

REPORT = """\
06:06:08 result                    = 0.81
06:06:08   Gait                    = 0 <- 100 * (0.01 > 0.05)
06:06:08     step_velocity         = 1.2
06:06:08   Effort                  = 0.6 <- 0.1 * 6
"""


def test_y_labels_carry_units_and_sign_convention():
    labels = {s.title: y_label(s) for s in load_template()}
    assert labels["Knee angle"] == "Knee angle (deg)\n- ext / + flex"
    assert labels["Ankle angle"] == "Ankle angle (deg)\n- plantar / + dorsi"
    assert labels["GRF"] == "Vertical GRF (BW)"


def test_plot_gait_labels_every_axis(tmp_path):
    ga = analyze_gait(synthetic_walk())
    fig = plot_gait(ga, title="synthetic")
    for ax in fig.axes:
        assert ax.get_xlabel() == "Gait cycle (%)"
        assert "(deg)" in ax.get_ylabel() or "(BW)" in ax.get_ylabel()
    plt.close(fig)
    plot_gait(ga, path=tmp_path / "g.png")
    assert (tmp_path / "g.png").stat().st_size > 0


def test_plot_comparison_draws_one_line_per_simulation(tmp_path):
    ga = analyze_gait(synthetic_walk())
    fig = plot_comparison({"A": ga, "B": ga}, titles=("Knee angle", "Ankle angle"))
    assert len(fig.axes) == 2
    assert [line.get_label() for line in fig.axes[0].get_lines()] == ["A", "B"]
    plt.close(fig)


def test_cli_analyze_writes_figure_and_summary(tmp_path, capsys):
    sto = tmp_path / "0050_1.0_0.81.par.sto"
    write_sto(synthetic_walk(), sto)
    (tmp_path / "0050_1.0_0.81.par.txt").write_text(REPORT)

    assert main(["analyze", str(sto), "--out", str(tmp_path / "out"), "--name", "walk"]) == 0
    assert (tmp_path / "out" / "walk_gait.png").exists()
    summary = json.loads((tmp_path / "out" / "walk_summary.json").read_text())
    assert summary["cycles"] == 5
    assert abs(summary["metrics"]["speed"] - 1.0) < 0.02
    assert summary["objective"]["value"] == 0.81
    assert summary["objective"]["children"]["Gait"]["children"]["step_velocity"]["value"] == 1.2
    assert "5 cycles" in capsys.readouterr().out


def test_cli_convergence(tmp_path):
    hist = tmp_path / "history.txt"
    hist.write_text("generation\tbest_fitness\tmedian_fitness\n0\t95\t96\n1\t1.2\t50\n2\t0.8\t2\n")
    out = tmp_path / "conv.png"
    assert main(["convergence", str(hist), "--labels", "Healthy", "--out", str(out)]) == 0
    assert out.exists()


def test_convergence_axes_are_labelled():
    h = History(np.arange(3), np.array([95.0, 1.2, 0.8]), np.array([96.0, 50.0, 2.0]))
    fig = plot_convergence({"A": h})
    ax = fig.axes[0]
    assert ax.get_xlabel() == "Generation (-)"
    assert ax.get_ylabel() == "Best objective so far (-)"
    assert ax.get_yscale() == "log"
    plt.close(fig)


def test_cli_compare(tmp_path):
    a, b = tmp_path / "a.sto", tmp_path / "b.sto"
    write_sto(synthetic_walk(), a)
    write_sto(synthetic_walk(), b)
    out = tmp_path / "figs" / "cmp.png"
    assert main(["compare", str(a), str(b), "--labels", "A", "B", "--out", str(out)]) == 0
    assert out.exists()

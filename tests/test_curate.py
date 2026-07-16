import pytest

from scone_gait.curate import curate_run

RUN_FILES = [
    "config.scone", "Human0914.osim", "InitStateGait.sto", "InitParameters.par",
    "history.txt", "optimization.log",
    "0000_96.300_95.636.par", "0012_18.754_13.052.par", "0012_18.754_13.052.par.sto",
    "0050_0.900_0.790.par", "0050_0.900_0.790.par.sto", "0050_0.900_0.790.par.txt",
]


@pytest.fixture
def run_dir(tmp_path):
    d = tmp_path / "260716.055822.f0914m.GH2010v8.S10W.D10.I"
    d.mkdir()
    for name in RUN_FILES:
        (d / name).write_text(name)
    return d


def test_keeps_setup_files_and_only_the_best_solution(run_dir, tmp_path):
    dest = tmp_path / "curated"
    best = curate_run(run_dir, dest)
    assert best == dest / "0050_0.900_0.790.par"
    assert sorted(p.name for p in dest.iterdir()) == sorted([
        "config.scone", "Human0914.osim", "InitStateGait.sto", "InitParameters.par",
        "history.txt", "optimization.log",
        "0050_0.900_0.790.par", "0050_0.900_0.790.par.sto", "0050_0.900_0.790.par.txt",
        "SOURCE.txt",
    ])
    assert "best: 0050_0.900_0.790.par" in (dest / "SOURCE.txt").read_text()


def test_explicit_best_solution(run_dir, tmp_path):
    dest = tmp_path / "curated"
    curate_run(run_dir, dest, best="0012_18.754_13.052.par")
    names = {p.name for p in dest.iterdir()}
    assert {"0012_18.754_13.052.par", "0012_18.754_13.052.par.sto"} <= names
    assert "0050_0.900_0.790.par" not in names


def test_missing_best_solution(run_dir, tmp_path):
    with pytest.raises(FileNotFoundError):
        curate_run(run_dir, tmp_path / "x", best="9999_1.000_1.000.par")

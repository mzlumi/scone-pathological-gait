import numpy as np
import pytest

from scone_gait.storage import Storage, StorageFormatError, read_sto, write_sto


def write_raw_sto(path, labels, rows, header=None, name="run/0001_1.000_0.900"):
    header = header or {"version": "1", "inDegrees": "no"}
    lines = [name]
    lines += [f"{k}={v}" for k, v in header.items()]
    lines += ["endheader", "\t".join(labels)]
    lines += ["\t".join(f"{v:g}" for v in row) for row in rows]
    path.write_text("\n".join(lines) + "\n")
    return path


def test_reads_header_labels_and_data(tmp_path):
    f = write_raw_sto(
        tmp_path / "a.sto",
        ["time", "pelvis_tilt", "leg0_l.grf_norm_y"],
        [[0.0, -0.1, 0.0], [0.01, -0.2, 0.5], [0.02, -0.3, 1.0]],
        header={"version": "1", "nRows": "3", "nColumns": "3", "inDegrees": "no"},
    )
    sto = read_sto(f)
    assert sto.name == "run/0001_1.000_0.900"
    assert sto.header["nRows"] == "3"
    assert sto.labels == ("pelvis_tilt", "leg0_l.grf_norm_y")
    np.testing.assert_allclose(sto.time, [0.0, 0.01, 0.02])
    np.testing.assert_allclose(sto["pelvis_tilt"], [-0.1, -0.2, -0.3])
    assert sto.frame_count == 3
    assert sto.average_frame_duration == pytest.approx(0.01)


def test_tolerates_trailing_tabs_and_blank_lines(tmp_path):
    f = tmp_path / "b.sto"
    f.write_text("name\nversion=1\nendheader\ntime\tx\t\n0\t1\t\n\n0.5\t2\t\n")
    sto = read_sto(f)
    assert sto.labels == ("x",)
    np.testing.assert_allclose(sto["x"], [1.0, 2.0])


def test_interpolates_linearly_and_clamps(tmp_path):
    f = write_raw_sto(tmp_path / "c.sto", ["time", "x"], [[0.0, 0.0], [1.0, 10.0], [2.0, 30.0]])
    sto = read_sto(f)
    assert sto.interpolate(0.5, "x") == pytest.approx(5.0)
    assert sto.interpolate(1.5, "x") == pytest.approx(20.0)
    np.testing.assert_allclose(sto.interpolate(np.array([-1.0, 3.0]), "x"), [0.0, 30.0])


def test_unknown_channel_raises_key_error(tmp_path):
    sto = read_sto(write_raw_sto(tmp_path / "d.sto", ["time", "x"], [[0.0, 1.0]]))
    assert sto.has("x") and not sto.has("y")
    with pytest.raises(KeyError, match="y"):
        sto["y"]


def test_missing_endheader_is_an_error(tmp_path):
    f = tmp_path / "e.sto"
    f.write_text("time\tx\n0\t1\n")
    with pytest.raises(StorageFormatError, match="endheader"):
        read_sto(f)


def test_row_length_mismatch_is_an_error(tmp_path):
    f = tmp_path / "f.sto"
    f.write_text("n\nendheader\ntime\tx\ty\n0\t1\n")
    with pytest.raises(StorageFormatError, match="labels"):
        read_sto(f)


def test_first_column_must_be_time(tmp_path):
    f = tmp_path / "g.sto"
    f.write_text("n\nendheader\nt\tx\n0\t1\n")
    with pytest.raises(StorageFormatError, match="time"):
        read_sto(f)


def test_degrees_are_rejected(tmp_path):
    f = write_raw_sto(tmp_path / "h.sto", ["time", "x"], [[0.0, 1.0]], header={"inDegrees": "yes"})
    with pytest.raises(StorageFormatError, match="inDegrees"):
        read_sto(f)


def test_write_then_read_round_trips(tmp_path):
    original = Storage(
        labels=("a", "b.c"),
        time=np.array([0.0, 0.01, 0.02]),
        data=np.array([[1.0, -2.5], [1e-9, 3.0], [0.1 + 0.2, 4.0]]),
        name="run/x",
    )
    write_sto(original, tmp_path / "x.sto")
    copy = read_sto(tmp_path / "x.sto")
    assert copy.name == "run/x"
    assert copy.labels == original.labels
    assert copy.header["nRows"] == "3" and copy.header["nColumns"] == "3"
    np.testing.assert_array_equal(copy.time, original.time)
    np.testing.assert_array_equal(copy.data, original.data)


def test_storage_validates_shape_and_time():
    with pytest.raises(ValueError, match="shape"):
        Storage(labels=("a",), time=np.array([0.0, 1.0]), data=np.zeros((2, 2)))
    with pytest.raises(ValueError, match="increasing"):
        Storage(labels=("a",), time=np.array([0.0, 0.0]), data=np.zeros((2, 1)))
    with pytest.raises(ValueError, match="unique"):
        Storage(labels=("a", "a"), time=np.array([0.0]), data=np.zeros((1, 2)))

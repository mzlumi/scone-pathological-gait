import numpy as np
import pytest

from scone_gait.storage import Storage


def make_storage(time, channels):
    labels = tuple(channels)
    data = np.column_stack([np.asarray(channels[k], dtype=float) for k in labels])
    return Storage(labels=labels, time=np.asarray(time, dtype=float), data=data)


def square_contact(time, period, stance_fraction, phase=0.0, amplitude=1.0):
    """Vertical force that is `amplitude` during stance and 0 during swing."""
    t = (np.asarray(time) - phase) % period
    return np.where(t < stance_fraction * period, amplitude, 0.0)


@pytest.fixture
def walking_storage():
    """Synthetic 1 m/s walk: 1.2 s stride, 60% stance, legs half a stride apart.

    The centre of pressure of each foot moves forward with the body, so the
    distance between consecutive contacts of one foot is 1.2 m.
    """
    dt = 0.005
    time = np.arange(0.0, 6.0 + dt / 2, dt)
    period, stance = 1.2, 0.6
    grf_l = square_contact(time, period, stance, phase=0.1)
    grf_r = square_contact(time, period, stance, phase=0.7)
    return make_storage(
        time,
        {
            "leg0_l.grf_norm_y": grf_l,
            "leg0_l.cop_x": time * 1.0,
            "leg0_l.cop_y": np.zeros_like(time),
            "leg0_l.cop_z": np.zeros_like(time),
            "leg1_r.grf_norm_y": grf_r,
            "leg1_r.cop_x": time * 1.0,
            "leg1_r.cop_y": np.zeros_like(time),
            "leg1_r.cop_z": np.zeros_like(time),
            "knee_angle_l": np.sin(2 * np.pi * (time - 0.1) / period),
            "knee_angle_r": np.sin(2 * np.pi * (time - 0.7) / period),
        },
    )

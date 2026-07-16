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


DEG = 57.3  # SCONE's radians to degrees factor in the gait template
PERIOD, STANCE = 1.2, 0.6


def synthetic_walk(heel_offset=0.05, toe_offset=0.15):
    """1 m/s walk with analytic joint angles, as functions of the cycle phase.

    ankle = 10 sin(2 pi phase) - 5      (deg, dorsiflexion positive)
    knee  = 35 - 25 cos(2 pi (phase - 0.3))   (deg, flexion positive)
    hip   = 20 cos(2 pi phase)          (deg, flexion positive)
    """
    time = np.arange(0.0, 6.0 + 0.0025, 0.005)
    channels = {"pelvis_tilt": np.zeros_like(time)}
    for side, leg, phase0 in [("l", "leg0_l", 0.1), ("r", "leg1_r", 0.7)]:
        phase = ((time - phase0) % PERIOD) / PERIOD
        channels[f"ankle_angle_{side}"] = (10 * np.sin(2 * np.pi * phase) - 5) / DEG
        # the model's knee angle is negative in flexion; the template multiplies by -57.3
        channels[f"knee_angle_{side}"] = -(35 - 25 * np.cos(2 * np.pi * (phase - 0.3))) / DEG
        channels[f"hip_flexion_{side}"] = 20 * np.cos(2 * np.pi * phase) / DEG
        channels[f"{leg}.grf_norm_y"] = square_contact(time, PERIOD, STANCE, phase=phase0)
        channels[f"{leg}.cop_x"] = time.copy()
        channels[f"{leg}.cop_y"] = np.zeros_like(time)
        channels[f"{leg}.cop_z"] = np.zeros_like(time)
        channels[f"calcn_{side}.pos_x"] = time - heel_offset
        channels[f"toes_{side}.pos_x"] = time + toe_offset
    return make_storage(time, channels)


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

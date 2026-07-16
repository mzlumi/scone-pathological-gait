"""Gait cycle extraction from simulated ground reaction forces.

This follows ``ExtractGaitCycles`` in scone-core (``scone/core/GaitCycle.cpp``)
so that cycle boundaries match those of the SCONE Studio gait analysis. A cycle
runs from one foot contact to the next contact of the same foot. A foot is in
contact while its vertical ground reaction force, in body weights, is above
``force_threshold``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scone_gait.storage import Storage

LEGS = {"l": "leg0_l", "r": "leg1_r"}


@dataclass(frozen=True)
class GaitCycle:
    side: str
    begin: float
    swing: float
    end: float
    begin_pos: np.ndarray
    end_pos: np.ndarray

    @property
    def duration(self) -> float:
        return self.end - self.begin

    @property
    def stance_duration(self) -> float:
        return self.swing - self.begin

    @property
    def swing_duration(self) -> float:
        return self.end - self.swing

    @property
    def stance_fraction(self) -> float:
        return self.stance_duration / self.duration

    @property
    def length(self) -> float:
        """Stride length: distance between centres of pressure at the two contacts."""
        return float(np.linalg.norm(self.end_pos - self.begin_pos))

    @property
    def velocity(self) -> float:
        return self.length / self.duration


def _next_touch(force: np.ndarray, idx: int | None, threshold: float) -> int | None:
    if idx is None:
        return None
    above = np.nonzero(force[idx:] > threshold)[0]
    return idx + int(above[0]) if above.size else None


def _next_flight(force: np.ndarray, idx: int | None, threshold: float) -> int | None:
    if idx is None:
        return None
    below = np.nonzero(force[idx:] <= threshold)[0]
    return idx + int(below[0]) if below.size else None


def _cop(sto: Storage, leg: str, idx: int) -> np.ndarray:
    return np.array([sto[f"{leg}.cop_{axis}"][idx] for axis in "xyz"])


def extract_gait_cycles(
    sto: Storage,
    force_threshold: float = 0.001,
    min_stance_duration: float = 0.1,
) -> list[GaitCycle]:
    """All complete gait cycles of both legs, sorted by start time.

    The defaults are the SCONE Studio defaults. A contact shorter than
    ``min_stance_duration`` is treated as a bump: it does not start a new cycle
    and extends the previous cycle of the same leg instead.
    """
    cycles: list[GaitCycle] = []
    for side, leg in LEGS.items():
        grf = f"{leg}.grf_norm_y"
        if not (sto.has(grf) and sto.has(f"{leg}.cop_x")):
            continue
        force = sto[grf]
        time = sto.time

        # skip to the first touch down that follows a flight phase
        flight = _next_flight(force, 0, force_threshold)
        touch = _next_touch(force, flight, force_threshold)

        while touch is not None:
            begin, begin_pos = time[touch], _cop(sto, leg, touch)
            flight = _next_flight(force, touch, force_threshold)
            if flight is None:
                break
            swing = time[flight]
            touch = _next_touch(force, flight, force_threshold)
            if touch is None:
                break
            end, end_pos = time[touch], _cop(sto, leg, touch)

            if swing - begin < min_stance_duration:
                if cycles and cycles[-1].side == side:
                    prev = cycles[-1]
                    cycles[-1] = GaitCycle(side, prev.begin, prev.swing, end, prev.begin_pos, end_pos)
            else:
                cycles.append(GaitCycle(side, begin, swing, end, begin_pos, end_pos))

    cycles.sort(key=lambda c: c.begin)
    return cycles

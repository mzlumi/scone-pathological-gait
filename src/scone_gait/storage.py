"""Reader for SCONE / OpenSim storage (.sto) files.

A SCONE result file looks like this::

    <name>
    version=1
    nRows=1001
    nColumns=505
    inDegrees=no
    endheader
    time    pelvis_tilt    ...
    0       -0.0590659     ...

Columns are tab separated. The first column is always time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


class StorageFormatError(ValueError):
    """Raised when a file does not follow the storage format."""


@dataclass(frozen=True)
class Storage:
    """Time series of named channels sampled at the same instants."""

    labels: tuple[str, ...]
    time: np.ndarray
    data: np.ndarray
    header: dict[str, str] = field(default_factory=dict)
    name: str = ""

    def __post_init__(self) -> None:
        if self.data.ndim != 2:
            raise ValueError("data must be a 2D array (frames x channels)")
        if self.data.shape != (len(self.time), len(self.labels)):
            raise ValueError(
                f"data shape {self.data.shape} does not match "
                f"{len(self.time)} frames and {len(self.labels)} labels"
            )
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("channel labels must be unique")
        if len(self.time) > 1 and np.any(np.diff(self.time) <= 0):
            raise ValueError("time must be strictly increasing")

    @property
    def frame_count(self) -> int:
        return len(self.time)

    @property
    def average_frame_duration(self) -> float:
        if self.frame_count < 2:
            return 0.0
        return float((self.time[-1] - self.time[0]) / (self.frame_count - 1))

    def has(self, label: str) -> bool:
        return label in self.labels

    def index(self, label: str) -> int:
        try:
            return self.labels.index(label)
        except ValueError:
            raise KeyError(f"no channel named {label!r}") from None

    def __getitem__(self, label: str) -> np.ndarray:
        return self.data[:, self.index(label)]

    def interpolate(self, t: float | np.ndarray, label: str) -> np.ndarray:
        """Linearly interpolate one channel at time(s) t, clamped at both ends."""
        return np.interp(t, self.time, self[label])


def read_sto(path: str | Path) -> Storage:
    """Read a .sto file written by SCONE or OpenSim."""
    path = Path(path)
    lines = path.read_text().splitlines()

    try:
        end = next(i for i, line in enumerate(lines) if line.strip() == "endheader")
    except StopIteration:
        raise StorageFormatError(f"{path}: no 'endheader' line") from None

    name = ""
    header: dict[str, str] = {}
    for line in lines[:end]:
        if "=" in line:
            key, value = line.split("=", 1)
            header[key.strip()] = value.strip()
        elif line.strip() and not name:
            name = line.strip()

    if end + 1 >= len(lines):
        raise StorageFormatError(f"{path}: no column labels after 'endheader'")
    labels = lines[end + 1].strip().split("\t")
    if not labels or labels[0] != "time":
        raise StorageFormatError(f"{path}: first column must be 'time'")

    rows = [line for line in lines[end + 2 :] if line.strip()]
    if rows:
        values = np.array([row.split() for row in rows], dtype=float)
    else:
        values = np.empty((0, len(labels)))
    if values.shape[1] != len(labels):
        raise StorageFormatError(
            f"{path}: {values.shape[1]} values per row but {len(labels)} labels"
        )

    if header.get("inDegrees", "no").lower() == "yes":
        raise StorageFormatError(f"{path}: files with inDegrees=yes are not supported")

    return Storage(
        labels=tuple(labels[1:]),
        time=values[:, 0].copy(),
        data=values[:, 1:].copy(),
        header=header,
        name=name,
    )

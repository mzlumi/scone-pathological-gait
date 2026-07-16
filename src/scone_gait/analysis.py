"""Gait analysis against normative data, as in the SCONE Studio Gait Analysis window.

For every plot in a template (pelvic tilt, hip, knee and ankle angle, vertical
ground reaction force) each gait cycle is sampled at 0, 0.5, ..., 99.5 percent,
the cycles are averaged, and the average is compared with a normative band.
The fit of one plot is

    fit = 100 * clamp(1 - mean_i(excess_i / width_i), 0, 1)

where ``excess_i`` is how far the average curve lies outside the band at the
i-th normative sample and ``width_i`` is the band width there. A curve that
stays inside the band scores 100 percent. The overall score is the mean fit
over all plots. This mirrors ``GaitAnalysis.cpp`` and ``GaitPlot.cpp`` in
scone-studio, including its defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from importlib import resources
from pathlib import Path

import numpy as np

from scone_gait.cycles import GaitCycle, extract_gait_cycles
from scone_gait.storage import Storage
from scone_gait.zml import get, parse_zml

PERCENT = np.arange(0.0, 100.0, 0.5)


@dataclass(frozen=True)
class GaitPlotSpec:
    title: str
    left_channel: str
    right_channel: str
    y_label: str = ""
    channel_multiply: float = 1.0
    channel_offset: float = 0.0
    norm_lower: np.ndarray | None = None
    norm_upper: np.ndarray | None = None

    @property
    def has_norm(self) -> bool:
        return self.norm_lower is not None

    def channels(self, sto: Storage, side: str) -> list[str]:
        """Labels in sto that match the channel pattern ('a;b' means a or b)."""
        pattern = self.left_channel if side == "l" else self.right_channel
        alternatives = pattern.split(";")
        return [lab for lab in sto.labels if any(fnmatchcase(lab, p) for p in alternatives)]

    def transform(self, value: np.ndarray) -> np.ndarray:
        return self.channel_offset + self.channel_multiply * value


def _floats(values: object) -> np.ndarray:
    return np.array([float(v) for v in values])  # type: ignore[union-attr]


def parse_template(text: str) -> list[GaitPlotSpec]:
    specs = []
    for key, block in parse_zml(text):
        if key != "GaitPlot":
            continue
        offset = float(get(block, "norm_offset", 0.0))
        lower = upper = None
        if get(block, "norm_min") is not None:
            lower = _floats(get(block, "norm_min")) + offset
            upper = _floats(get(block, "norm_max")) + offset
        elif get(block, "norm_mean") is not None and get(block, "norm_std") is not None:
            mean = _floats(get(block, "norm_mean")) + offset
            std = _floats(get(block, "norm_std"))
            lower, upper = mean - std, mean + std
        if lower is not None and len(lower) != len(upper):
            raise ValueError(f"norm arrays of {get(block, 'title')!r} differ in length")
        specs.append(
            GaitPlotSpec(
                title=str(get(block, "title", "")),
                left_channel=str(get(block, "left_channel")),
                right_channel=str(get(block, "right_channel")),
                y_label=str(get(block, "y_label", "")),
                channel_multiply=float(get(block, "channel_multiply", 1.0)),
                channel_offset=float(get(block, "channel_offset", 0.0)),
                norm_lower=lower,
                norm_upper=upper,
            )
        )
    return specs


def load_template(path: str | Path | None = None) -> list[GaitPlotSpec]:
    """Load a gait analysis template; by default the one shipped with SCONE Studio."""
    if path is None:
        text = resources.files("scone_gait").joinpath("data/gait_analysis_default.zml").read_text()
    else:
        text = Path(path).read_text()
    return parse_template(text)


def fit_percentage(mean: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Fit of an average curve sampled at PERCENT to a normative band."""
    x = np.linspace(0.0, 100.0, len(lower))
    v = np.interp(x, PERCENT, mean)
    excess = np.where(v < lower, v - lower, np.where(v > upper, v - upper, 0.0))
    error = np.mean(np.abs(excess) / np.maximum(0.01, upper - lower))
    return float(100.0 * np.clip(1.0 - error, 0.0, 1.0))


@dataclass(frozen=True)
class PlotResult:
    spec: GaitPlotSpec
    sides: tuple[str, ...]
    curves: np.ndarray  # one row per cycle, sampled at PERCENT
    fit: float | None

    @property
    def mean(self) -> np.ndarray:
        return self.curves.mean(axis=0)

    def side_curves(self, side: str) -> np.ndarray:
        return self.curves[[s == side for s in self.sides]]


@dataclass(frozen=True)
class GaitAnalysis:
    cycles: tuple[GaitCycle, ...]
    plots: tuple[PlotResult, ...]

    def __getitem__(self, title: str) -> PlotResult:
        for p in self.plots:
            if p.spec.title == title:
                return p
        raise KeyError(title)

    @property
    def stride_length(self) -> float:
        return float(np.mean([c.length for c in self.cycles]))

    @property
    def stride_duration(self) -> float:
        return float(np.mean([c.duration for c in self.cycles]))

    @property
    def speed(self) -> float:
        return self.stride_length / self.stride_duration

    @property
    def stance_fraction(self) -> float:
        return float(np.mean([c.stance_fraction for c in self.cycles]))

    @property
    def score(self) -> float:
        fits = [p.fit for p in self.plots if p.fit is not None]
        return float(np.mean(fits)) if fits else float("nan")


def analyze_gait(
    sto: Storage,
    template: list[GaitPlotSpec] | None = None,
    force_threshold: float = 0.001,
    min_stance_duration: float = 0.1,
    skip_first: int = 2,
    skip_last: int = 1,
    contact_timing_offset: float = 1.0,
) -> GaitAnalysis:
    """Average gait cycles of a simulation and compare them with normative data.

    ``skip_first`` and ``skip_last`` drop the first and last cycles (both legs
    together, in time order), which are dominated by the initial state and by
    the end of the simulation.
    """
    if template is None:
        template = load_template()
    cycles = extract_gait_cycles(sto, force_threshold, min_stance_duration)
    if len(cycles) <= skip_first + skip_last:
        raise ValueError(
            f"only {len(cycles)} gait cycles found; at least {skip_first + skip_last + 1} are needed"
        )
    cycles = cycles[skip_first : len(cycles) - skip_last]

    # the contact is detected one sample late; shift sampling back by that much
    lookahead = sto.average_frame_duration * contact_timing_offset

    plots = []
    for spec in template:
        rows, sides = [], []
        for c in cycles:
            channels = spec.channels(sto, c.side)
            if not channels:
                continue
            t = c.begin + PERCENT * c.duration / 100.0 - lookahead
            raw = np.mean([sto.interpolate(t, ch) for ch in channels], axis=0)
            rows.append(spec.transform(raw))
            sides.append(c.side)
        if not rows:
            continue
        curves = np.vstack(rows)
        fit = fit_percentage(curves.mean(axis=0), spec.norm_lower, spec.norm_upper) if spec.has_norm else None
        plots.append(PlotResult(spec, tuple(sides), curves, fit))

    return GaitAnalysis(tuple(cycles), tuple(plots))

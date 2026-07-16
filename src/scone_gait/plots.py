"""Figures for gait analyses: joint angles and ground reaction force over the gait cycle."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from scone_gait.analysis import PERCENT, GaitAnalysis, GaitPlotSpec  # noqa: E402
from scone_gait.results import History  # noqa: E402

SIDE_COLORS = {"l": "tab:blue", "r": "tab:red"}
X_LABEL = "Gait cycle (%)"


def y_label(spec: GaitPlotSpec) -> str:
    """Axis label with units and the sign convention from the template."""
    unit = "BW" if spec.title == "GRF" else "deg"
    name = "Vertical GRF" if spec.title == "GRF" else spec.title
    direction = spec.y_label.replace("<-", "").replace("->", "").strip()
    if spec.title != "GRF" and direction:
        parts = [p.strip() for p in direction.split("/")]
        if len(parts) == 2:
            return f"{name} ({unit})\n- {parts[0]} / + {parts[1]}"
    return f"{name} ({unit})"


def _draw_norm(ax, spec: GaitPlotSpec) -> None:
    if spec.has_norm:
        x = np.linspace(0, 100, len(spec.norm_lower))
        ax.fill_between(x, spec.norm_lower, spec.norm_upper, color="0.85", lw=0, label="Normal range")


def plot_gait(ga: GaitAnalysis, title: str = "", path: str | Path | None = None):
    """One panel per template plot: normal band, every cycle, and the mean."""
    fig, axes = plt.subplots(1, len(ga.plots), figsize=(3.2 * len(ga.plots), 3.2), squeeze=False)
    for ax, result in zip(axes[0], ga.plots):
        spec = result.spec
        _draw_norm(ax, spec)
        for row, side in zip(result.curves, result.sides):
            ax.plot(PERCENT, row, color=SIDE_COLORS[side], lw=0.6, alpha=0.5)
        ax.plot(PERCENT, result.mean, color="k", lw=1.8, label="Mean")
        fit = f" (fit {result.fit:.0f}%)" if result.fit is not None else ""
        ax.set_title(f"{spec.title}{fit}", fontsize=10)
        ax.set_xlabel(X_LABEL)
        ax.set_ylabel(y_label(spec))
        ax.set_xlim(0, 100)
    axes[0][0].plot([], [], color=SIDE_COLORS["l"], lw=0.8, label="Left cycles")
    axes[0][0].plot([], [], color=SIDE_COLORS["r"], lw=0.8, label="Right cycles")
    axes[0][0].legend(fontsize=7, loc="best")
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, dpi=150)
        plt.close(fig)
    return fig


def plot_convergence(histories: Mapping[str, History], path: str | Path | None = None):
    """Best objective so far against generation, on a log scale."""
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for label, h in histories.items():
        ax.semilogy(h.generation, h.best_so_far, lw=1.6, label=label)
    ax.axhline(0.9, color="0.5", ls="--", lw=1, label="Handout target (0.9)")
    ax.set_xlabel("Generation (-)")
    ax.set_ylabel("Best objective so far (-)")
    ax.legend(fontsize=7)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, dpi=150)
        plt.close(fig)
    return fig


def plot_comparison(
    analyses: Mapping[str, GaitAnalysis],
    path: str | Path | None = None,
    titles: tuple[str, ...] | None = None,
):
    """Mean curves of several simulations on shared axes, with the normal band."""
    first = next(iter(analyses.values()))
    specs = [p.spec for p in first.plots if titles is None or p.spec.title in titles]
    fig, axes = plt.subplots(1, len(specs), figsize=(3.2 * len(specs), 3.2), squeeze=False)
    for ax, spec in zip(axes[0], specs):
        _draw_norm(ax, spec)
        for label, ga in analyses.items():
            try:
                result = ga[spec.title]
            except KeyError:
                continue
            ax.plot(PERCENT, result.mean, lw=1.6, label=label)
        ax.set_title(spec.title, fontsize=10)
        ax.set_xlabel(X_LABEL)
        ax.set_ylabel(y_label(spec))
        ax.set_xlim(0, 100)
    axes[0][-1].legend(fontsize=7, loc="best")
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, dpi=150)
        plt.close(fig)
    return fig

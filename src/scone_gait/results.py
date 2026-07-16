"""Readers for SCONE optimization results.

An optimization folder contains one ``.par`` file per improving generation,
named ``<generation>_<average>_<best>.par``. Evaluating a ``.par`` file with
``sconecmd -e`` prints the objective broken down into its measures, which
``scripts/scone.sh`` saves as ``<name>.par.txt``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_RESULT_NAME = re.compile(r"^(\d+)_(-?[\d.]+)_(-?[\d.]+)\.par$")
_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2} ")


@dataclass(frozen=True)
class Parameter:
    value: float
    mean: float
    std: float


def read_par(path: str | Path) -> dict[str, Parameter]:
    """Read a SCONE parameter file: one 'name value mean std' line per parameter."""
    params: dict[str, Parameter] = {}
    for n, line in enumerate(Path(path).read_text().splitlines(), start=1):
        fields = line.split()
        if not fields:
            continue
        if len(fields) != 4:
            raise ValueError(f"{path}:{n}: expected 'name value mean std', got {line!r}")
        name, value, mean, std = fields
        params[name] = Parameter(float(value), float(mean), float(std))
    return params


@dataclass(frozen=True)
class ResultName:
    generation: int
    average: float
    best: float


def parse_result_name(path: str | Path) -> ResultName | None:
    """Split '0013_14.602_8.802.par' into generation, average and best objective."""
    m = _RESULT_NAME.match(Path(path).name)
    if not m:
        return None
    return ResultName(int(m.group(1)), float(m.group(2)), float(m.group(3)))


def init_file_name(folder: str | Path) -> str | None:
    """File name of the init_file in the config.scone that SCONE wrote to the folder.

    SCONE copies the init file into the results folder. When an optimization is
    warm started from an earlier solution, that copy has a result-style name
    (for example 0035_1.021_0.780.par) but is not a result of this run.
    """
    config = Path(folder) / "config.scone"
    if not config.exists():
        return None
    from scone_gait.zml import ZmlError, get, parse_zml

    try:
        blocks = parse_zml(config.read_text())
    except ZmlError:
        return None
    for _, block in blocks:
        value = get(block, "init_file") if isinstance(block, list) else None
        if value:
            return Path(str(value)).name
    return None


def best_result(folder: str | Path) -> Path:
    """The .par file with the lowest objective among the results of a run.

    The copy of a warm start init file is not a result and is ignored.
    """
    init = init_file_name(folder)
    candidates = []
    for p in Path(folder).glob("*.par"):
        name = parse_result_name(p)
        if name is not None and p.name != init:
            candidates.append((name.best, -name.generation, p))
    if not candidates:
        raise FileNotFoundError(f"no optimization results in {folder}")
    return min(candidates)[2]


@dataclass(frozen=True)
class History:
    generation: np.ndarray
    best: np.ndarray  # best objective of each generation
    median: np.ndarray

    @property
    def best_so_far(self) -> np.ndarray:
        return np.minimum.accumulate(self.best)


def read_history(path: str | Path) -> History:
    """Read the per-generation history.txt that SCONE writes in a results folder."""
    lines = [line for line in Path(path).read_text().splitlines() if line.strip()]
    if not lines or not lines[0].startswith("generation"):
        raise ValueError(f"{path}: not a SCONE history file")
    header = lines[0].split("\t")
    rows = np.array([line.split("\t")[: len(header)] for line in lines[1:]], dtype=float).reshape(-1, len(header))
    col = {name: i for i, name in enumerate(header)}
    return History(
        generation=rows[:, col["generation"]].astype(int),
        best=rows[:, col["best_fitness"]],
        median=rows[:, col["median_fitness"]],
    )


@dataclass
class ReportEntry:
    name: str
    value: float
    detail: str = ""
    children: list["ReportEntry"] = field(default_factory=list)

    def __getitem__(self, name: str) -> "ReportEntry":
        for child in self.children:
            if child.name == name:
                return child
        raise KeyError(name)


def parse_report(text: str) -> ReportEntry:
    """Parse the objective breakdown printed by 'sconecmd -e'.

    The breakdown is indented by two spaces per level::

        result                    = 13.0521
          Gait                    = 11.8542 <- 100 * (0.118542 > 0.05)
            step_velocity         = 0.881458

    Returns the 'result' entry, with the measures as its children.
    """
    root: ReportEntry | None = None
    stack: list[tuple[int, ReportEntry]] = []
    for raw in text.splitlines():
        line = _TIMESTAMP.sub("", raw.rstrip())
        if " = " not in line:
            continue
        stripped = line.lstrip(" ")
        depth = (len(line) - len(stripped)) // 2
        name, rest = stripped.split(" = ", 1)
        value_text, _, detail = rest.partition(" <- ")
        try:
            value = float(value_text.split()[0])
        except (ValueError, IndexError):
            continue
        entry = ReportEntry(name.strip(), value, detail.strip())

        if name.strip() == "result" and depth == 0:
            root = entry
            stack = [(0, entry)]
            continue
        if root is None or depth == 0:
            continue
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if not stack:
            continue
        stack[-1][1].children.append(entry)
        stack.append((depth, entry))

    if root is None:
        raise ValueError("no 'result = ...' line in the evaluation report")
    return root


def read_report(path: str | Path) -> ReportEntry:
    return parse_report(Path(path).read_text())

"""Copy an optimization folder into the layout the handout asks for.

The submission must contain the optimization results "removing intermediate
solutions", but with the setup files SCONE copies into the folder and the best
solution, so the simulation can be replayed without optimizing again.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from scone_gait.results import best_result, init_file_name, parse_result_name

SETUP_PATTERNS = ("config.scone", "*.osim", "*.sto", "*.par", "history.txt", "optimization.log")


def _is_setup_file(path: Path) -> bool:
    if parse_result_name(path) is not None:
        return False  # an intermediate or best solution, handled separately
    if path.name.endswith(".par.sto") or path.name.endswith(".par.txt"):
        return False
    return any(path.match(p) for p in SETUP_PATTERNS)


def curate_run(run_dir: str | Path, dest: str | Path, best: str | Path | None = None) -> Path:
    """Copy setup files and the best solution (with its evaluation) to dest.

    Returns the path of the copied best .par file.
    """
    run_dir, dest = Path(run_dir), Path(dest)
    best = Path(best) if best is not None else best_result(run_dir)
    if best.parent.resolve() != run_dir.resolve():
        best = run_dir / best.name
    if not best.exists():
        raise FileNotFoundError(best)

    init = init_file_name(run_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(run_dir.iterdir()):
        if f.is_file() and (_is_setup_file(f) or f.name == init):
            shutil.copy2(f, dest / f.name)
    for f in (best, best.with_name(best.name + ".sto"), best.with_name(best.name + ".txt")):
        if f.exists():
            shutil.copy2(f, dest / f.name)
    source = f"run: {run_dir.name}\nbest: {best.name}\n"
    if init and (run_dir / init).exists():
        source += f"init: {init} (warm start init file copied by SCONE, not a result of this run)\n"
    (dest / "SOURCE.txt").write_text(source)
    return dest / best.name

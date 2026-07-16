"""Command line tool: analyze and compare SCONE simulation results.

    scone-gait analyze results/healthy/0050_x_y.par.sto --out figures --name healthy
    scone-gait compare healthy.par.sto weak.par.sto --labels Healthy Weak --out cmp.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scone_gait.analysis import analyze_gait
from scone_gait.metrics import gait_metrics
from scone_gait.plots import plot_comparison, plot_gait
from scone_gait.results import ReportEntry, read_report
from scone_gait.storage import read_sto


def _report_dict(entry: ReportEntry) -> dict:
    return {
        "value": entry.value,
        "detail": entry.detail,
        "children": {c.name: _report_dict(c) for c in entry.children},
    }


def analyze(sto_path: Path, out: Path, name: str) -> dict:
    sto = read_sto(sto_path)
    ga = analyze_gait(sto)
    summary: dict = {
        "source": sto_path.name,
        "cycles": len(ga.cycles),
        "metrics": gait_metrics(sto, ga).as_dict(),
        "fit": {p.spec.title: p.fit for p in ga.plots},
    }
    # 'x.par.sto' was evaluated from 'x.par', whose report is 'x.par.txt'
    report = sto_path.with_suffix(".txt")
    if report.exists():
        summary["objective"] = _report_dict(read_report(report))

    out.mkdir(parents=True, exist_ok=True)
    plot_gait(ga, title=name, path=out / f"{name}_gait.png")
    (out / f"{name}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scone-gait", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("analyze", help="gait figure and metrics for one simulation")
    p.add_argument("sto", type=Path)
    p.add_argument("--out", type=Path, default=Path("."))
    p.add_argument("--name", default=None)

    c = sub.add_parser("compare", help="overlay the mean gait of several simulations")
    c.add_argument("sto", type=Path, nargs="+")
    c.add_argument("--labels", nargs="+", required=True)
    c.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "analyze":
        summary = analyze(args.sto, args.out, args.name or args.sto.name.split(".")[0])
        m = summary["metrics"]
        print(
            f"{summary['cycles']} cycles, speed {m['speed']:.2f} m/s, "
            f"fit {m['fit_score']:.1f}%, ankle at contact {m['ankle_at_contact']:.1f} deg, "
            f"foot contact index {m['foot_contact_index']:.2f}"
        )
    else:
        if len(args.labels) != len(args.sto):
            parser.error("give one label per file")
        analyses = {label: analyze_gait(read_sto(f)) for label, f in zip(args.labels, args.sto)}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        plot_comparison(analyses, path=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

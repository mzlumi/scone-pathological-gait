"""Clinical gait metrics used to recognise heel walking, toe walking and crouch gait.

Joint angles follow the SCONE gait analysis conventions, in degrees: hip
flexion positive, knee flexion positive, ankle dorsiflexion positive and
plantarflexion negative.

The foot contact index locates the centre of pressure at initial contact along
the foot, from the heel (calcaneus origin, 0) to the metatarsophalangeal joint
(toes origin, 1). Heel strikers land near 0; toe walkers land near or beyond 1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from scone_gait.analysis import PERCENT, GaitAnalysis
from scone_gait.cycles import LEGS, GaitCycle
from scone_gait.storage import Storage

# load above which the centre of pressure is considered reliable
COP_FORCE_THRESHOLD = 0.05


@dataclass(frozen=True)
class GaitMetrics:
    speed: float  # m/s
    stride_length: float  # m
    stride_duration: float  # s
    cadence: float  # steps/min
    stance_percent: float  # % of the gait cycle
    ankle_at_contact: float  # deg
    ankle_peak_dorsiflexion_stance: float  # deg
    ankle_peak_plantarflexion: float  # deg, around push-off and early swing
    ankle_range: float  # deg
    knee_at_contact: float  # deg
    knee_min_stance: float  # deg, least flexed point of stance
    knee_peak_swing: float  # deg
    hip_peak_extension: float  # deg, negative means extension
    foot_contact_index: float  # 0 heel, 1 metatarsal heads
    fit_score: float  # % SCONE gait analysis score

    def as_dict(self) -> dict[str, float]:
        return {k: float(v) for k, v in asdict(self).items()}


def foot_contact_index(sto: Storage, cycle: GaitCycle) -> float:
    """Centre of pressure position along the foot at initial contact."""
    leg = LEGS[cycle.side]
    side = cycle.side
    force = sto[f"{leg}.grf_norm_y"]
    in_stance = (sto.time >= cycle.begin) & (sto.time < cycle.swing)
    loaded = np.nonzero(in_stance & (force > COP_FORCE_THRESHOLD))[0]
    if loaded.size == 0:
        return float("nan")
    i = loaded[0]
    heel = sto[f"calcn_{side}.pos_x"][i]
    toe = sto[f"toes_{side}.pos_x"][i]
    cop = sto[f"{leg}.cop_x"][i]
    return float((cop - heel) / (toe - heel))


def _stance_mask(ga: GaitAnalysis) -> np.ndarray:
    """Per cycle, which samples of PERCENT fall in stance."""
    return np.vstack([PERCENT < 100.0 * c.stance_fraction for c in ga.cycles])


def _masked_extreme(curves: np.ndarray, mask: np.ndarray, fn) -> float:
    return float(np.mean([fn(row[m]) for row, m in zip(curves, mask) if m.any()]))


def gait_metrics(sto: Storage, ga: GaitAnalysis) -> GaitMetrics:
    """Summarise a gait analysis with clinical metrics, averaged over cycles."""
    stance = _stance_mask(ga)
    swing = ~stance

    ankle = ga["Ankle angle"].curves
    knee = ga["Knee angle"].curves
    hip = ga["Hip angle"].curves

    contact_index = [foot_contact_index(sto, c) for c in ga.cycles]

    return GaitMetrics(
        speed=ga.speed,
        stride_length=ga.stride_length,
        stride_duration=ga.stride_duration,
        cadence=2 * 60.0 / ga.stride_duration,
        stance_percent=100.0 * ga.stance_fraction,
        ankle_at_contact=float(np.mean(ankle[:, 0])),
        ankle_peak_dorsiflexion_stance=_masked_extreme(ankle, stance, np.max),
        ankle_peak_plantarflexion=float(np.mean(ankle.min(axis=1))),
        ankle_range=float(np.mean(ankle.max(axis=1) - ankle.min(axis=1))),
        knee_at_contact=float(np.mean(knee[:, 0])),
        knee_min_stance=_masked_extreme(knee, stance, np.min),
        knee_peak_swing=_masked_extreme(knee, swing, np.max),
        hip_peak_extension=float(np.mean(hip.min(axis=1))),
        foot_contact_index=float(np.nanmean(contact_index)) if not np.all(np.isnan(contact_index)) else float("nan"),
        fit_score=ga.score,
    )

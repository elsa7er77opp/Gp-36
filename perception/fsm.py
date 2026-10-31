"""SAFE / WARNING / STOP decision from the unified detection list.

Until the range sensor and IMU are connected, nearness is estimated from the
image only: a box that reaches low in the frame (large `bottom`) and overlaps
the driving corridor is treated as close. All thresholds are PLACEHOLDERS until
they are calibrated on the pod's own camera; they live in perception/config.yaml.

Range thresholds follow Strasser et al. (2024): normal speed above 2 m, slow
down between 2 m and 0.5 m, stop below 0.5 m.

Hysteresis: the state goes up (towards STOP) quickly and comes down slowly, so
one missed detection does not release a STOP. If no frame arrives for
`stale_timeout_s`, the output is STOP (fail-safe).
"""
from dataclasses import dataclass, fields

SAFE, WARNING, STOP = "SAFE", "WARNING", "STOP"
LEVEL = {SAFE: 0, WARNING: 1, STOP: 2}


@dataclass
class FsmConfig:
    corridor_x: tuple = (0.25, 0.75)
    obstacle_labels: tuple = ("coco:person", "coco:bicycle", "coco:car", "coco:motorcycle",
                              "coco:bus", "coco:truck", "coco:dog")
    obstacle_min_conf: float = 0.40
    obstacle_warn_bottom: float = 0.55
    obstacle_stop_bottom: float = 0.85
    obstacle_stop_height: float = 0.45
    hazard_labels: tuple = ("hazard:pothole", "hazard:speed_bump")
    hazard_min_conf: float = 0.35
    hazard_warn_bottom: float = 0.50
    range_warn_m: float = 2.0
    range_stop_m: float = 0.5
    escalate_frames: int = 2
    release_frames: int = 10
    stale_timeout_s: float = 1.0

    @classmethod
    def from_dict(cls, d):
        known = {f.name for f in fields(cls)}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown fsm config keys: {sorted(unknown)}")
        kw = {k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items()}
        return cls(**kw)


def in_corridor(det, cfg):
    lo, hi = cfg.corridor_x
    return det.x1n < hi and det.x2n > lo


def instant_state(dets, cfg, range_m=None):
    """State for this frame alone. Returns (state, reasons)."""
    state, reasons = SAFE, []

    def raise_to(s, why):
        nonlocal state
        reasons.append(f"{s}: {why}")
        if LEVEL[s] > LEVEL[state]:
            state = s

    for d in dets:
        if not in_corridor(d, cfg):
            continue
        if d.label in cfg.obstacle_labels and d.conf >= cfg.obstacle_min_conf:
            if d.bottom >= cfg.obstacle_stop_bottom or d.h_ratio >= cfg.obstacle_stop_height:
                raise_to(STOP, f"{d.label} near ({d.conf:.2f})")
            elif d.bottom >= cfg.obstacle_warn_bottom:
                raise_to(WARNING, f"{d.label} ahead ({d.conf:.2f})")
        elif d.label in cfg.hazard_labels and d.conf >= cfg.hazard_min_conf:
            # A surface hazard means "slow down", not "stop": it is driven over or around.
            if d.bottom >= cfg.hazard_warn_bottom:
                raise_to(WARNING, f"{d.label} ahead ({d.conf:.2f})")

    if range_m is not None:
        if range_m < cfg.range_stop_m:
            raise_to(STOP, f"range {range_m:.2f} m")
        elif range_m < cfg.range_warn_m:
            raise_to(WARNING, f"range {range_m:.2f} m")
    return state, reasons


class PerceptionFSM:
    def __init__(self, cfg=None):
        self.cfg = cfg or FsmConfig()
        self.state = SAFE
        self.reasons = []
        self._up = 0
        self._down = 0
        self._last_t = None

    def update(self, dets, t, range_m=None):
        """Feed one frame (t in seconds, monotonic). Returns (state, reasons)."""
        self._last_t = t
        inst, reasons = instant_state(dets, self.cfg, range_m)
        range_stop = range_m is not None and range_m < self.cfg.range_stop_m
        if LEVEL[inst] > LEVEL[self.state]:
            self._down = 0
            self._up += 1
            if range_stop or self._up >= self.cfg.escalate_frames:
                self.state, self._up = inst, 0
        elif LEVEL[inst] < LEVEL[self.state]:
            self._up = 0
            self._down += 1
            if self._down >= self.cfg.release_frames:
                self.state, self._down = inst, 0
        else:
            self._up = self._down = 0
        self.reasons = reasons
        return self.state, reasons

    def tick(self, t):
        """Call when no frame arrived. Forces STOP once input is older than stale_timeout_s."""
        if self._last_t is None or t - self._last_t > self.cfg.stale_timeout_s:
            self.state, self.reasons = STOP, ["STOP: stale input"]
            self._up = self._down = 0
        return self.state, self.reasons

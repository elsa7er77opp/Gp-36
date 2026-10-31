"""Unified detection record shared by both detectors.

Class ids are only unique inside one model (hazard 0 = pothole, COCO 0 = person),
so every detection carries its namespace and is referred to by `label`
("hazard:pothole", "coco:person"), never by the bare class id.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

HAZARD_NS = "hazard"
COCO_NS = "coco"
NAMESPACES = (HAZARD_NS, COCO_NS)


@dataclass(frozen=True)
class Detection:
    ns: str                                   # "hazard" or "coco"
    cls_id: int                               # class id inside its own model
    name: str                                 # class name inside its own model
    conf: float
    xyxy: Tuple[float, float, float, float]   # pixel box
    frame_wh: Tuple[int, int]                 # (width, height) of the frame
    track_id: Optional[int] = None

    def __post_init__(self):
        if self.ns not in NAMESPACES:
            raise ValueError(f"unknown namespace {self.ns!r}, expected one of {NAMESPACES}")
        w, h = self.frame_wh
        if w <= 0 or h <= 0:
            raise ValueError("frame_wh must be positive")

    @property
    def label(self) -> str:
        return f"{self.ns}:{self.name}"

    @property
    def uid(self) -> str:
        return f"{self.ns}:{self.cls_id}"

    # Geometry normalised by the frame size (0..1)
    @property
    def x1n(self) -> float:
        return self.xyxy[0] / self.frame_wh[0]

    @property
    def x2n(self) -> float:
        return self.xyxy[2] / self.frame_wh[0]

    @property
    def bottom(self) -> float:
        """Bottom edge of the box. Closer objects on the ground sit lower in the frame."""
        return self.xyxy[3] / self.frame_wh[1]

    @property
    def h_ratio(self) -> float:
        return (self.xyxy[3] - self.xyxy[1]) / self.frame_wh[1]

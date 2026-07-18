"""
AirCanvas – General-purpose utility functions.
"""
from __future__ import annotations

import math
import os
import time
from datetime import datetime
from typing import Sequence

import cv2
import numpy as np

from utils.constants import SAVE_DIR, SAVE_PREFIX


# ── Geometry ──────────────────────────────────────────────────────────────────

def distance(p1: Sequence[float], p2: Sequence[float]) -> float:
    """Euclidean distance between two 2-D points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between *a* and *b* by factor *t* ∈ [0, 1]."""
    return a + (b - a) * t


def lerp_point(
    p1: Sequence[float], p2: Sequence[float], t: float
) -> tuple[int, int]:
    """Interpolate between two 2-D points and return integer pixel coords."""
    return (int(lerp(p1[0], p2[0], t)), int(lerp(p1[1], p2[1], t)))


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, value))


def point_in_rect(
    point: Sequence[float],
    x: int, y: int, w: int, h: int,
) -> bool:
    """Return True if *point* is inside the axis-aligned rectangle."""
    px, py = point[0], point[1]
    return x <= px <= x + w and y <= py <= y + h


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_rounded_rect(
    img: np.ndarray,
    x: int, y: int, w: int, h: int,
    radius: int,
    color: tuple,
    thickness: int = -1,  # -1 = filled
    alpha: float = 1.0,
) -> None:
    """
    Draw a filled (or outlined) rounded rectangle on *img*.

    When *alpha* < 1 a temporary overlay is blended for transparency.
    """
    if alpha < 1.0:
        overlay = img.copy()
        _draw_rounded_rect_solid(overlay, x, y, w, h, radius, color, thickness)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    else:
        _draw_rounded_rect_solid(img, x, y, w, h, radius, color, thickness)


def _draw_rounded_rect_solid(
    img: np.ndarray,
    x: int, y: int, w: int, h: int,
    radius: int,
    color: tuple,
    thickness: int,
) -> None:
    r = min(radius, w // 2, h // 2)
    # Four corner circles
    for cx, cy in [
        (x + r, y + r),
        (x + w - r, y + r),
        (x + r, y + h - r),
        (x + w - r, y + h - r),
    ]:
        cv2.circle(img, (cx, cy), r, color, thickness, cv2.LINE_AA)
    # Three rectangles to fill the interior
    if thickness == -1:
        cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, -1)
        cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, -1)


def alpha_blend(
    background: np.ndarray,
    overlay: np.ndarray,
    alpha: float,
    region: tuple[int, int, int, int] | None = None,
) -> None:
    """
    In-place alpha blend *overlay* onto *background*.

    *region* is (x, y, w, h). If None the full frame is used.
    """
    if region is None:
        cv2.addWeighted(overlay, alpha, background, 1 - alpha, 0, background)
    else:
        x, y, w, h = region
        roi = background[y : y + h, x : x + w]
        ov_roi = overlay[y : y + h, x : x + w]
        blended = cv2.addWeighted(ov_roi, alpha, roi, 1 - alpha, 0)
        background[y : y + h, x : x + w] = blended


def apply_blur_glass(img: np.ndarray, x: int, y: int, w: int, h: int, ksize: int = 21) -> None:
    """Blur a rectangular region to simulate frosted-glass."""
    roi = img[y : y + h, x : x + w]
    blurred = cv2.GaussianBlur(roi, (ksize, ksize), 0)
    img[y : y + h, x : x + w] = blurred


# ── File I/O ──────────────────────────────────────────────────────────────────

def ensure_save_dir() -> str:
    """Create the save directory if it does not exist; return its path."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    return SAVE_DIR


def next_save_path() -> str:
    """Generate a unique timestamped file path for saving a drawing."""
    ensure_save_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(SAVE_DIR, f"{SAVE_PREFIX}_{ts}.png")


def save_canvas(canvas_bgr: np.ndarray) -> str:
    """
    Save *canvas_bgr* (a BGR image) onto a white background as a PNG.

    Returns the file path on success, or an empty string on failure.
    """
    try:
        path = next_save_path()
        # Composite on white
        h, w = canvas_bgr.shape[:2]
        white = np.full((h, w, 3), 255, dtype=np.uint8)
        # Wherever the canvas is non-white, keep the artwork
        # (canvas background is already white, so this is a direct copy)
        cv2.imwrite(path, canvas_bgr)
        return path
    except Exception as exc:  # noqa: BLE001
        print(f"[AirCanvas] Save failed: {exc}")
        return ""


# ── Text rendering ────────────────────────────────────────────────────────────

def put_text_centered(
    img: np.ndarray,
    text: str,
    cx: int, cy: int,
    font_scale: float,
    color: tuple,
    thickness: int = 1,
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
) -> None:
    """Draw *text* horizontally and vertically centered at (cx, cy)."""
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    cv2.putText(
        img, text,
        (cx - tw // 2, cy + th // 2),
        font, font_scale, color, thickness, cv2.LINE_AA,
    )


def fps_string(elapsed_seconds: float) -> str:
    """Convert elapsed frame time in seconds to a formatted FPS string."""
    if elapsed_seconds <= 0:
        return "-- FPS"
    return f"{1.0 / elapsed_seconds:.0f} FPS"


# ── Misc ──────────────────────────────────────────────────────────────────────

def now_ms() -> float:
    """Monotonic timestamp in milliseconds."""
    return time.monotonic() * 1000.0

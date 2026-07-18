"""
AirCanvas – Cursor renderer.
Draws a crosshair + brush-preview circle at the smoothed fingertip position, plus a pinch-state indicator.
"""
from __future__ import annotations
import cv2
import numpy as np
from core.drawing import DrawingEngine, Tool
from utils.colors import UI
from utils.constants import PINCH_THRESHOLD_PX

class CursorRenderer:
    """
    Renders the virtual cursor and brush preview circle.
    Parameters
    ----------
    engine : DrawingEngine
        Needed to read current tool, color, and brush size.
    """

    def __init__(self, engine: DrawingEngine) -> None:
        self._engine = engine

    def draw(
        self,
        img: np.ndarray,
        cursor: tuple[int, int],
        is_pinching: bool,
        pinch_distance: float,
    ) -> None:
        """
        Paint the cursor onto *img*.

        Parameters
        ----------
        img : np.ndarray
            The composited display frame (modified in place).
        cursor : (int, int)
            Smoothed cursor position in pixels.
        is_pinching : bool
            Current pinch state (for indicator colour).
        pinch_distance : float
            Raw distance between thumb and index in pixels.
        """
        cx, cy = cursor
        engine = self._engine
        radius = engine.effective_radius

        # ── Brush preview circle ────
        if engine.tool == Tool.BRUSH:
            preview_color = engine.color.bgr()
        else:
            preview_color = UI.ERASER_PREVIEW.bgr()

        # Outer ring (white for contrast)
        cv2.circle(img, (cx, cy), radius + 2, UI.CURSOR_OUTER.bgr(), 1, cv2.LINE_AA)
        # Inner ring (tool color / eraser grey)
        cv2.circle(img, (cx, cy), radius, preview_color, 1, cv2.LINE_AA)

        # ── Crosshair ────
        arm = max(radius + 8, 14)
        gap = radius + 3

        cross_color = UI.CURSOR_CROSSHAIR.bgr()
        # Horizontal arms
        cv2.line(img, (cx - arm, cy), (cx - gap, cy), cross_color, 1, cv2.LINE_AA)
        cv2.line(img, (cx + gap, cy), (cx + arm, cy), cross_color, 1, cv2.LINE_AA)
        # Vertical arms
        cv2.line(img, (cx, cy - arm), (cx, cy - gap), cross_color, 1, cv2.LINE_AA)
        cv2.line(img, (cx, cy + gap), (cx, cy + arm), cross_color, 1, cv2.LINE_AA)

        # ── Pinch indicator dot ─────
        indicator_color = (
            UI.PINCH_ACTIVE.bgr() if is_pinching else UI.PINCH_IDLE.bgr()
        )
        dot_x = cx + radius + 8
        dot_y = cy - radius - 8
        cv2.circle(img, (dot_x, dot_y), 4, indicator_color, -1, cv2.LINE_AA)
        cv2.circle(img, (dot_x, dot_y), 4, UI.CURSOR_OUTER.bgr(), 1, cv2.LINE_AA)

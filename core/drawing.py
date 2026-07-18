"""
AirCanvas – Drawing engine.

Handles all stroke rendering onto the Canvas layer with anti-aliasing,
rounded caps, and dense interpolation so fast hand movements never leave
gaps in strokes.
"""
from __future__ import annotations

import math
from enum import Enum, auto

import cv2
import numpy as np

from utils.constants import (
    DEFAULT_BRUSH_SIZE,
    ERASER_SIZE_MULTIPLIER,
    MAX_BRUSH_SIZE,
    MAX_INTERPOLATION_DISTANCE,
    MIN_BRUSH_SIZE,
    BRUSH_SIZE_STEP,
)
from utils.colors import Color, WHITE


class Tool(Enum):
    BRUSH = auto()
    ERASER = auto()


class DrawingEngine:
    """
    Manages the current drawing state and renders strokes.

    Parameters
    ----------
    canvas : Canvas
        The :class:`~core.canvas.Canvas` instance to paint on.
    """

    def __init__(self, canvas: "Canvas") -> None:  # type: ignore[name-defined]
        self._canvas = canvas
        self._tool = Tool.BRUSH
        self._brush_size = DEFAULT_BRUSH_SIZE
        self._color: Color = Color(30, 30, 30, "Charcoal")  # BGR charcoal

        # Drawing state
        self._is_drawing = False
        self._prev_point: tuple[int, int] | None = None

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def tool(self) -> Tool:
        return self._tool

    @tool.setter
    def tool(self, value: Tool) -> None:
        self._tool = value

    @property
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, value: Color) -> None:
        self._color = value
        self._tool = Tool.BRUSH  # Selecting a color switches back to brush

    @property
    def brush_size(self) -> int:
        return self._brush_size

    @property
    def effective_radius(self) -> int:
        """Radius actually used for rendering (accounts for eraser multiplier)."""
        if self._tool == Tool.ERASER:
            return self._brush_size * ERASER_SIZE_MULTIPLIER // 2
        return self._brush_size // 2

    @property
    def is_drawing(self) -> bool:
        return self._is_drawing

    # ── Brush size control ─────────────────────────────────────────────────

    def increase_brush(self) -> None:
        self._brush_size = min(self._brush_size + BRUSH_SIZE_STEP, MAX_BRUSH_SIZE)

    def decrease_brush(self) -> None:
        self._brush_size = max(self._brush_size - BRUSH_SIZE_STEP, MIN_BRUSH_SIZE)

    # ── Stroke lifecycle ───────────────────────────────────────────────────

    def begin_stroke(self, point: tuple[int, int]) -> None:
        """Start a new stroke at *point*."""
        if not self._is_drawing:
            self._is_drawing = True
            self._prev_point = point
            # Paint a single dot at the starting point
            self._paint_segment(point, point)

    def continue_stroke(self, point: tuple[int, int]) -> None:
        """Extend the current stroke to *point*."""
        if not self._is_drawing:
            return
        if self._prev_point is None:
            self._prev_point = point
            return
        self._paint_segment(self._prev_point, point)
        self._prev_point = point

    def end_stroke(self) -> None:
        """Finish the current stroke and push an undo snapshot."""
        if self._is_drawing:
            self._is_drawing = False
            self._prev_point = None
            self._canvas.push_snapshot()

    # ── Rendering ─────────────────────────────────────────────────────────

    def _paint_segment(
        self,
        p1: tuple[int, int],
        p2: tuple[int, int],
    ) -> None:
        """
        Paint one segment from *p1* to *p2* with interpolation.

        Interpolates intermediate points so that gaps never appear even
        when the cursor moves faster than the frame rate can track.
        """
        layer = self._canvas.layer
        mask = self._canvas.mask

        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        steps = max(1, int(dist / MAX_INTERPOLATION_DISTANCE))

        # Draw each sub-segment
        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0.0
            ix = int(p1[0] + (p2[0] - p1[0]) * t)
            iy = int(p1[1] + (p2[1] - p1[1]) * t)

            if self._tool == Tool.ERASER:
                self._erase_at(layer, mask, ix, iy)
            else:
                self._paint_at(layer, mask, ix, iy)

        # For brush: also draw the full line for smooth anti-aliasing
        if self._tool == Tool.BRUSH:
            cv2.line(
                layer, p1, p2,
                self._color.bgr(),
                self._brush_size,
                cv2.LINE_AA,
            )
            # Update mask along the line
            cv2.line(
                mask, p1, p2,
                255,
                self._brush_size,
                cv2.LINE_AA,
            )

    def _paint_at(
        self,
        layer: np.ndarray,
        mask: np.ndarray,
        x: int, y: int,
    ) -> None:
        """Paint a filled anti-aliased circle (rounded cap) at (x, y)."""
        r = self._brush_size // 2
        cv2.circle(layer, (x, y), r, self._color.bgr(), -1, cv2.LINE_AA)
        cv2.circle(mask,  (x, y), r, 255,                -1, cv2.LINE_AA)

    def _erase_at(
        self,
        layer: np.ndarray,
        mask: np.ndarray,
        x: int, y: int,
    ) -> None:
        """Erase a circle at (x, y) by restoring white on layer and 0 on mask."""
        r = self._brush_size * ERASER_SIZE_MULTIPLIER // 2
        cv2.circle(layer, (x, y), r, WHITE.bgr(), -1, cv2.LINE_AA)
        cv2.circle(mask,  (x, y), r, 0,            -1, cv2.LINE_AA)

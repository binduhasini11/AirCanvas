"""
AirCanvas – Bottom status bar renderer.

Displays FPS, current tool, brush size, and color swatch in a slim
glassmorphism strip along the bottom of the frame.
"""
from __future__ import annotations

import cv2
import numpy as np

from core.drawing import DrawingEngine, Tool
from utils.colors import UI
from utils.constants import (
    STATUS_BAR_ALPHA,
    STATUS_BAR_HEIGHT,
    STATUS_FONT_SCALE,
    STATUS_FONT_THICKNESS,
)
from utils.helpers import apply_blur_glass, draw_rounded_rect


class StatusBar:
    """
    Renders the bottom status bar.

    Parameters
    ----------
    frame_width : int
        Width of the display frame.
    frame_height : int
        Height of the display frame.
    engine : DrawingEngine
        The active drawing engine (for reading tool/color/brush state).
    """

    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        engine: DrawingEngine,
    ) -> None:
        self._w = frame_width
        self._h = frame_height
        self._engine = engine

        self._bar_y = frame_height - STATUS_BAR_HEIGHT
        self._bar_h = STATUS_BAR_HEIGHT

        self._fps_str = "-- FPS"
        self._extra_msg = ""     # Transient message (e.g. "Saved!")
        self._msg_frames = 0     # How many frames to display extra_msg

    # ── Public API ─────────────────────────────────────────────────────────

    def set_fps(self, fps_str: str) -> None:
        self._fps_str = fps_str

    def show_message(self, msg: str, duration_frames: int = 60) -> None:
        """Display a transient status message for *duration_frames* frames."""
        self._extra_msg = msg
        self._msg_frames = duration_frames

    # ── Rendering ──────────────────────────────────────────────────────────

    def draw(self, img: np.ndarray, hovered_tooltip: str = "") -> None:
        """Draw the status bar onto *img* (modified in place)."""
        bx, by, bw, bh = 0, self._bar_y, self._w, self._bar_h

        # Frosted glass
        apply_blur_glass(img, bx, by, bw, bh, ksize=15)

        # Background fill
        draw_rounded_rect(
            img, bx, by, bw, bh,
            radius=0,
            color=UI.STATUS_BG.bgr(),
            thickness=-1,
            alpha=STATUS_BAR_ALPHA,
        )
        # Top separator line
        cv2.line(img, (bx, by), (bx + bw, by), UI.TOOLBAR_BORDER.bgr(), 1)

        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = STATUS_FONT_SCALE
        ft = STATUS_FONT_THICKNESS
        text_color = UI.STATUS_TEXT.bgr()
        accent_color = UI.STATUS_ACCENT.bgr()
        cy = by + bh // 2

        x = 12

        # FPS
        self._put(img, self._fps_str, x, cy, fs, accent_color, ft, font)
        x += 90

        # Separator
        cv2.line(img, (x, by + 6), (x, by + bh - 6), UI.TOOLBAR_BORDER.bgr(), 1)
        x += 10

        # Tool indicator
        tool_str = "Brush" if self._engine.tool == Tool.BRUSH else "Eraser"
        self._put(img, f"Tool: {tool_str}", x, cy, fs, text_color, ft, font)
        x += 120

        # Separator
        cv2.line(img, (x, by + 6), (x, by + bh - 6), UI.TOOLBAR_BORDER.bgr(), 1)
        x += 10

        # Brush size
        sz = self._engine.brush_size
        self._put(img, f"Size: {sz}px", x, cy, fs, text_color, ft, font)
        x += 100

        # Separator
        cv2.line(img, (x, by + 6), (x, by + bh - 6), UI.TOOLBAR_BORDER.bgr(), 1)
        x += 10

        # Color swatch
        if self._engine.tool == Tool.BRUSH:
            swatch_r = bh // 2 - 5
            cv2.circle(img, (x + swatch_r, cy), swatch_r, self._engine.color.bgr(), -1, cv2.LINE_AA)
            cv2.circle(img, (x + swatch_r, cy), swatch_r, (120, 120, 120), 1, cv2.LINE_AA)
            x += swatch_r * 2 + 8
            self._put(img, self._engine.color.name, x, cy, fs, text_color, ft, font)
            x += 90
        else:
            self._put(img, "Eraser", x, cy, fs, text_color, ft, font)
            x += 80

        # Tooltip (right-aligned area, centered in remaining space)
        if hovered_tooltip:
            self._put(img, f"[ {hovered_tooltip} ]", x + 20, cy, fs, accent_color, ft, font)

        # Transient message (far right)
            # Transient message (far right)
        if self._msg_frames > 0:
            msg = self._extra_msg
            self._msg_frames -= 1
            (tw, th), baseline = cv2.getTextSize(msg,font,fs,ft)
            mx = self._w - tw - 15
            self._put(img, msg, mx, cy, fs, accent_color, ft, font)


    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _put(
        img: np.ndarray,
        text: str,
        x: int, cy: int,
        fs: float,
        color: tuple,
        thickness: int,
        font: int,
    ) -> None:
        _, th = cv2.getTextSize(text, font, fs, thickness)[0:2]
        cv2.putText(img, text, (x, cy + th // 2), font, fs, color, thickness, cv2.LINE_AA)

"""
AirCanvas – Floating glassmorphism toolbar.
Arranges all toolbar buttons in a horizontal strip, renders the glass background, and handles pinch-based button activation with a cooldown to prevent unintended clicks while the user is drawing nearby.
"""
from __future__ import annotations

from typing import Callable

import cv2
import numpy as np
from core.drawing import DrawingEngine, Tool
from ui.buttons import (
    BrushButton,
    ClearButton,
    ColorButton,
    EraserButton,
    IconButton,
    SaveButton,
    SizeButton,
    ToolbarButton,
)
from utils.colors import PALETTE, UI
from utils.constants import (
    TOOLBAR_ALPHA,
    TOOLBAR_BUTTON_GAP,
    TOOLBAR_BUTTON_SIZE,
    TOOLBAR_CORNER_RADIUS,
    TOOLBAR_HEIGHT,
    TOOLBAR_PADDING,
    TOOLBAR_PINCH_COOLDOWN_FRAMES,
)
from utils.helpers import apply_blur_glass, draw_rounded_rect, point_in_rect


class Toolbar:
    """
    Horizontal floating toolbar drawn near the top of the frame.

    Parameters
    ----------
    frame_width : int
        Width of the camera / canvas frame.
    engine : DrawingEngine
        The drawing engine; toolbar buttons mutate it directly.
    on_clear : callable
        Called when the user activates the Clear button.
    on_save : callable
        Called when the user activates the Save button.
    on_undo : callable
        Called when the user activates the Undo button.
    on_redo : callable
        Called when the user activates the Redo button.
    """

    def __init__(
        self,
        frame_width: int,
        engine: DrawingEngine,
        on_clear: Callable[[], None],
        on_save: Callable[[], None],
        on_undo: Callable[[], None],
        on_redo: Callable[[], None],
    ) -> None:
        self._engine = engine
        self._on_clear = on_clear
        self._on_save = on_save

        # Build button list
        self._buttons: list[ToolbarButton] = []
        self._build_buttons(frame_width, on_clear, on_save, on_undo, on_redo)

        # Precompute toolbar background rect
        self._compute_bg_rect(frame_width)

        # Pinch interaction state
        self._cooldown_remaining = 0   # frames until next click is allowed
        self._last_hovered: ToolbarButton | None = None
        self._hovered_tooltip: str = ""

    # ── Construction ───────────────────────────────────────────────────────

    def _compute_bg_rect(self, frame_width: int) -> None:
        """Calculate the background rectangle that fits all buttons."""
        if not self._buttons:
            self._bg_x = 0
            self._bg_y = 0
            self._bg_w = 0
            self._bg_h = TOOLBAR_HEIGHT
            return

        leftmost = min(b.x for b in self._buttons)
        rightmost = max(b.x + b.size for b in self._buttons)
        topy = min(b.y for b in self._buttons)
        boty = max(b.y + b.size for b in self._buttons)

        self._bg_x = leftmost - TOOLBAR_PADDING
        self._bg_y = topy - TOOLBAR_PADDING
        self._bg_w = rightmost - leftmost + TOOLBAR_PADDING * 2
        self._bg_h = boty - topy + TOOLBAR_PADDING * 2

    def _build_buttons(
        self,
        frame_width: int,
        on_clear: Callable[[], None],
        on_save: Callable[[], None],
        on_undo: Callable[[], None],
        on_redo: Callable[[], None],
    ) -> None:
        """Instantiate and lay out all buttons."""
        s = TOOLBAR_BUTTON_SIZE
        gap = TOOLBAR_BUTTON_GAP
        y = TOOLBAR_PADDING + 5  # top padding from frame edge

        # Starting x so the toolbar is centred
        # Layout order: [Colors…] | [Brush] [Eraser] [Size-] [Size+] | [Undo] [Redo] | [Clear] [Save]
        n_colors = len(PALETTE)
        n_tools  = 4   # brush, eraser, size-, size+
        n_hist   = 2   # undo, redo
        n_act    = 2   # clear, save
        n_sep    = 3   # visual separators (gaps between groups)
        sep_gap  = gap * 2

        total_buttons = n_colors + n_tools + n_hist + n_act
        total_width = (
            total_buttons * s
            + (total_buttons - 1) * gap
            + n_sep * sep_gap
        )
        start_x = (frame_width - total_width) // 2

        x = start_x

        # ── Color swatches ───────────────────────────────────────────────
        for color in PALETTE:
            c = color  # capture loop variable
            btn = ColorButton(
                x, y, s, c,
                on_click=lambda col=c: self._select_color(col),
            )
            self._buttons.append(btn)
            x += s + gap
        x += sep_gap

        # ── Brush / Eraser ───────────────────────────────────────────────
        brush_btn = BrushButton(
            x, y, s,
            on_click=lambda: self._select_tool(Tool.BRUSH),
            tooltip="Brush",
        )
        self._buttons.append(brush_btn)
        x += s + gap

        eraser_btn = EraserButton(
            x, y, s,
            on_click=lambda: self._select_tool(Tool.ERASER),
            tooltip="Eraser",
        )
        self._buttons.append(eraser_btn)
        x += s + gap + sep_gap

        # ── Brush size ───────────────────────────────────────────────────
        self._buttons.append(SizeButton(
            x, y, s, increase=False,
            on_click=self._engine.decrease_brush,
        ))
        x += s + gap
        self._buttons.append(SizeButton(
            x, y, s, increase=True,
            on_click=self._engine.increase_brush,
        ))
        x += s + gap + sep_gap

        # ── Undo / Redo ──────────────────────────────────────────────────
        self._buttons.append(IconButton(
            x, y, s, label="↩",
            on_click=on_undo,
            tooltip="Undo (Z)",
        ))
        x += s + gap
        self._buttons.append(IconButton(
            x, y, s, label="↪",
            on_click=on_redo,
            tooltip="Redo (Y)",
        ))
        x += s + gap + sep_gap

        # ── Clear / Save ─────────────────────────────────────────────────
        self._buttons.append(ClearButton(
            x, y, s,
            on_click=on_clear,
            tooltip="Clear canvas (C)",
        ))
        x += s + gap
        self._buttons.append(SaveButton(
            x, y, s,
            on_click=on_save,
            tooltip="Save drawing (S)",
        ))

        # Store refs for active-state tracking
        self._brush_btn = brush_btn
        self._eraser_btn = eraser_btn

    # ── Update ─────────────────────────────────────────────────────────────

    def update(
        self,
        cursor: tuple[int, int],
        is_pinching: bool,
    ) -> bool:
        """
        Update hover/active states and handle button activation.

        Parameters
        ----------
        cursor : (int, int)
            Smoothed cursor position.
        is_pinching : bool
            Whether the pinch gesture is active.

        Returns
        -------
        bool
            True if the cursor is over the toolbar (blocks drawing).
        """
        cx, cy = cursor

        # Determine if cursor is within toolbar bounds
        over_toolbar = point_in_rect(
            cursor,
            self._bg_x, self._bg_y, self._bg_w, self._bg_h,
        )

        # Clear stale hover flags
        self._hovered_tooltip = ""
        for btn in self._buttons:
            btn.is_hovered = False

        # Update hover states and detect pinch activation
        if over_toolbar:
            for btn in self._buttons:
                if btn.contains(cx, cy):
                    btn.is_hovered = True
                    self._hovered_tooltip = btn.tooltip

                    if is_pinching and self._cooldown_remaining == 0:
                        btn.on_click()
                        self._cooldown_remaining = TOOLBAR_PINCH_COOLDOWN_FRAMES
                    break

        # Tick cooldown
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1

        # Sync active states
        self._sync_active_states()

        return over_toolbar

    def _sync_active_states(self) -> None:
        """Keep active flags consistent with engine state."""
        current_tool = self._engine.tool
        current_color = self._engine.color

        for btn in self._buttons:
            if isinstance(btn, ColorButton):
                btn.is_active = (
                    current_tool == Tool.BRUSH
                    and btn.color.bgr() == current_color.bgr()
                )
            elif isinstance(btn, BrushButton):
                btn.is_active = current_tool == Tool.BRUSH
            elif isinstance(btn, EraserButton):
                btn.is_active = current_tool == Tool.ERASER
            else:
                btn.is_active = False

    # ── Helpers ────────────────────────────────────────────────────────────

    def _select_color(self, color: "Color") -> None:  # noqa: F821
        self._engine.color = color

    def _select_tool(self, tool: Tool) -> None:
        self._engine.tool = tool

    # ── Rendering ──────────────────────────────────────────────────────────

    def draw(self, img: np.ndarray) -> None:
        """Render the toolbar (glass background + buttons) onto *img*."""
        bx, by, bw, bh = self._bg_x, self._bg_y, self._bg_w, self._bg_h

        # Clamp to image bounds
        h, w = img.shape[:2]
        bx = max(0, bx)
        by = max(0, by)
        bw = min(bw, w - bx)
        bh = min(bh, h - by)

        # Frosted-glass blur
        apply_blur_glass(img, bx, by, bw, bh, ksize=25)

        # Semi-transparent dark fill
        draw_rounded_rect(
            img,
            bx, by, bw, bh,
            radius=TOOLBAR_CORNER_RADIUS,
            color=UI.TOOLBAR_BG.bgr(),
            thickness=-1,
            alpha=TOOLBAR_ALPHA,
        )

        # Subtle border
        draw_rounded_rect(
            img,
            bx, by, bw, bh,
            radius=TOOLBAR_CORNER_RADIUS,
            color=UI.TOOLBAR_BORDER.bgr(),
            thickness=1,
            alpha=0.9,
        )

        # Buttons
        for btn in self._buttons:
            btn.draw(img)

    # ── Public accessors ───────────────────────────────────────────────────

    @property
    def hovered_tooltip(self) -> str:
        return self._hovered_tooltip

    @property
    def bg_rect(self) -> tuple[int, int, int, int]:
        """(x, y, w, h) of the toolbar background."""
        return (self._bg_x, self._bg_y, self._bg_w, self._bg_h)

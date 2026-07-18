"""
AirCanvas – Button widgets for the floating toolbar.
Each button is self-contained: it knows its bounding box, how to render itself, and whether the cursor is hovering over it.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable
import cv2
import numpy as np
from utils.colors import Color, UI
from utils.helpers import draw_rounded_rect, put_text_centered


# ── Base class ───

class ToolbarButton(ABC):
    """
    Abstract base for all toolbar buttons.

    Parameters
    ----------
    x, y : int
        Top-left corner of the button bounding box.
    size : int
        Side length of the (square) button.
    on_click : callable
        Zero-argument callback invoked when the button is triggered.
    tooltip : str
        Short label shown in the status bar on hover.
    """

    def __init__(
        self,
        x: int, y: int, size: int,
        on_click: Callable[[], None],
        tooltip: str = "",
    ) -> None:
        self.x = x
        self.y = y
        self.size = size
        self.on_click = on_click
        self.tooltip = tooltip

        self.is_hovered = False
        self.is_active = False       # "selected" state (e.g. active color)

    # ── Geometry helpers ───
    def contains(self, px: int, py: int) -> bool:
        """Return True if pixel (px, py) is inside this button."""
        return (
            self.x <= px <= self.x + self.size
            and self.y <= py <= self.y + self.size
        )

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.size // 2, self.y + self.size // 2)

    # ── Rendering ───

    def draw(self, img: np.ndarray) -> None:
        """Render the button onto *img*."""
        bg_color = self._background_color()
        radius = self.size // 4

        draw_rounded_rect(
            img,
            self.x, self.y, self.size, self.size,
            radius=radius,
            color=bg_color.bgr(),
            thickness=-1,
        )

        # Active border highlight
        if self.is_active:
            draw_rounded_rect(
                img,
                self.x, self.y, self.size, self.size,
                radius=radius,
                color=UI.BUTTON_ACTIVE.bgr(),
                thickness=2,
            )
        elif self.is_hovered:
            draw_rounded_rect(
                img,
                self.x, self.y, self.size, self.size,
                radius=radius,
                color=UI.TOOLBAR_HIGHLIGHT.bgr(),
                thickness=1,
            )

        self._draw_icon(img)

    def _background_color(self) -> Color:
        if self.is_active:
            return UI.BUTTON_HOVER
        if self.is_hovered:
            return UI.BUTTON_HOVER
        return UI.BUTTON_NORMAL

    @abstractmethod
    def _draw_icon(self, img: np.ndarray) -> None:
        """Subclasses draw their specific icon here."""


# ── Concrete button types ─────────────────────────────────────────────────────

class ColorButton(ToolbarButton):
    """A swatch button that selects a brush color."""

    def __init__(self, x: int, y: int, size: int, color: Color, on_click: Callable[[], None]) -> None:
        super().__init__(x, y, size, on_click, tooltip=f"{color.name}")
        self.color = color

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        r = self.size // 2 - 6
        # Filled color circle
        cv2.circle(img, (cx, cy), r, self.color.bgr(), -1, cv2.LINE_AA)
        # White border for dark colors / visibility
        cv2.circle(img, (cx, cy), r, (180, 180, 180), 1, cv2.LINE_AA)


class IconButton(ToolbarButton):
    """A button that renders a text-based icon (letter or symbol)."""

    def __init__(
        self,
        x: int, y: int, size: int,
        label: str,
        on_click: Callable[[], None],
        tooltip: str = "",
    ) -> None:
        super().__init__(x, y, size, on_click, tooltip=tooltip)
        self.label = label

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        color = UI.BUTTON_ACTIVE.bgr() if self.is_active else UI.BUTTON_ICON.bgr()
        put_text_centered(
            img, self.label, cx, cy,
            font_scale=0.60,
            color=color,
            thickness=1,
        )


class BrushButton(ToolbarButton):
    """Renders a small brush icon (thick dot + handle line)."""

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        color = UI.BUTTON_ACTIVE.bgr() if self.is_active else UI.BUTTON_ICON.bgr()
        # Handle
        cv2.line(img, (cx - 4, cy + 6), (cx + 4, cy - 6), color, 2, cv2.LINE_AA)
        # Tip
        cv2.circle(img, (cx - 5, cy + 7), 3, color, -1, cv2.LINE_AA)


class EraserButton(ToolbarButton):
    """Renders a small eraser icon (rounded rectangle)."""

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        color = UI.BUTTON_ACTIVE.bgr() if self.is_active else UI.BUTTON_ICON.bgr()
        cv2.rectangle(img, (cx - 8, cy - 5), (cx + 8, cy + 5), color, -1)
        cv2.rectangle(img, (cx - 8, cy - 5), (cx + 8, cy + 5), (80, 80, 80), 1)
        # Pink accent bar
        cv2.rectangle(img, (cx + 4, cy - 5), (cx + 8, cy + 5), (140, 140, 220), -1)


class SizeButton(ToolbarButton):
    """Renders +/- size control icon."""

    def __init__(
        self,
        x: int, y: int, size: int,
        increase: bool,
        on_click: Callable[[], None],
    ) -> None:
        label = "+" if increase else "–"
        tip = "Increase brush size" if increase else "Decrease brush size"
        super().__init__(x, y, size, on_click, tooltip=tip)
        self._increase = increase

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        color = UI.BUTTON_ICON.bgr()
        # Horizontal bar (always)
        cv2.line(img, (cx - 7, cy), (cx + 7, cy), color, 2, cv2.LINE_AA)
        # Vertical bar for "+"
        if self._increase:
            cv2.line(img, (cx, cy - 7), (cx, cy + 7), color, 2, cv2.LINE_AA)


class ClearButton(ToolbarButton):
    """Renders a trash / clear icon."""

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        color = UI.BUTTON_ICON.bgr()
        # Can body
        cv2.rectangle(img, (cx - 7, cy - 4), (cx + 7, cy + 8), color, 1, cv2.LINE_AA)
        # Lid
        cv2.line(img, (cx - 9, cy - 5), (cx + 9, cy - 5), color, 2, cv2.LINE_AA)
        # Handle
        cv2.rectangle(img, (cx - 4, cy - 8), (cx + 4, cy - 5), color, 1, cv2.LINE_AA)
        # Lines inside can
        for dx in (-3, 0, 3):
            cv2.line(img, (cx + dx, cy - 2), (cx + dx, cy + 6), color, 1, cv2.LINE_AA)


class SaveButton(ToolbarButton):
    """Renders a save / floppy-disk icon."""

    def _draw_icon(self, img: np.ndarray) -> None:
        cx, cy = self.center
        color = UI.BUTTON_ICON.bgr()
        # Outer square
        cv2.rectangle(img, (cx - 8, cy - 8), (cx + 8, cy + 8), color, 1, cv2.LINE_AA)
        # Label window
        cv2.rectangle(img, (cx - 5, cy - 8), (cx + 5, cy - 2), color, -1)
        # Bottom notch
        cv2.rectangle(img, (cx - 6, cy + 1), (cx + 6, cy + 7), color, 1, cv2.LINE_AA)

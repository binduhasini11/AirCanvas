"""
AirCanvas – Color definitions and palette utilities.
All colors are in BGR order (OpenCV convention).
"""
from __future__ import annotations
from typing import NamedTuple


class Color(NamedTuple):
    """A BGR color tuple with an optional display name."""
    b: int
    g: int
    r: int
    name: str = ""

    def bgr(self) -> tuple[int, int, int]:
        return (self.b, self.g, self.r)

    def rgb(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def with_alpha(self, alpha: int) -> tuple[int, int, int, int]:
        """Return BGRA tuple."""
        return (self.b, self.g, self.r, alpha)

    def lerp(self, other: "Color", t: float) -> "Color":
        """Linearly interpolate between this color and another."""
        return Color(
            b=int(self.b + (other.b - self.b) * t),
            g=int(self.g + (other.g - self.g) * t),
            r=int(self.r + (other.r - self.r) * t),
        )


# ── Neutral palette ───────────────────────────────────────────────────────────
WHITE = Color(255, 255, 255, "White")
BLACK = Color(0, 0, 0, "Black")
TRANSPARENT = Color(0, 0, 0, "Transparent")

# ── Drawing brush palette ─────────────────────────────────────────────────────
PALETTE: list[Color] = [
    Color(30,  30,  30,  "Charcoal"),
    Color(20,  80,  220, "Crimson"),
    Color(40,  200, 255, "Amber"),
    Color(50,  200, 50,  "Emerald"),
    Color(255, 100, 30,  "Ocean"),
    Color(200, 60,  200, "Violet"),
    Color(20,  200, 200, "Teal"),
    Color(255, 255, 255, "White"),
]

# ── UI chrome colors (BGR) ────────────────────────────────────────────────────
class UI:
    """Color constants for UI elements."""

    # Toolbar glass
    TOOLBAR_BG        = Color(40,  40,  40,  "ToolbarBg")
    TOOLBAR_BORDER    = Color(90,  90,  90,  "ToolbarBorder")
    TOOLBAR_HIGHLIGHT = Color(255, 255, 255, "ToolbarHighlight")

    # Button states
    BUTTON_NORMAL     = Color(55,  55,  55,  "ButtonNormal")
    BUTTON_HOVER      = Color(80,  80,  80,  "ButtonHover")
    BUTTON_ACTIVE     = Color(255, 160, 50,  "ButtonActive")   # accent (BGR: orange)
    BUTTON_ICON       = Color(230, 230, 230, "ButtonIcon")

    # Cursor
    CURSOR_OUTER      = Color(255, 255, 255, "CursorOuter")
    CURSOR_INNER      = Color(30,  30,  30,  "CursorInner")
    CURSOR_CROSSHAIR  = Color(200, 200, 200, "CursorCrosshair")

    # Status bar
    STATUS_BG         = Color(20,  20,  20,  "StatusBg")
    STATUS_TEXT       = Color(200, 200, 200, "StatusText")
    STATUS_ACCENT     = Color(255, 160, 50,  "StatusAccent")   # same orange

    # Pinch indicator
    PINCH_ACTIVE      = Color(80,  220, 100, "PinchActive")
    PINCH_IDLE        = Color(100, 100, 100, "PinchIdle")

    # Flash overlay (save animation)
    FLASH             = Color(255, 255, 255, "Flash")

    # Eraser tool visual
    ERASER_PREVIEW    = Color(180, 180, 180, "EraserPreview")

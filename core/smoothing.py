"""
AirCanvas – Cursor position smoothing.
Uses an exponential moving average (EMA) filter to reduce hand-tracking jitter while keeping latency minimal.
A separate velocity-based adaptive alpha adjusts smoothing dynamically: fast movements get less smoothing so the cursor stays responsive; slow, deliberate movements get more smoothing for fine control.
"""
from __future__ import annotations

import math
from utils.constants import SMOOTHING_FACTOR


class PositionSmoother:
    """
    EMA-based 2-D position smoother with adaptive alpha.

    Parameters
    ----------
    alpha : float
        Base smoothing strength, 0 < alpha < 1.
        Higher = more smoothing (more lag).
        Lower  = less smoothing (more responsive).
    """

    def __init__(self, alpha: float = SMOOTHING_FACTOR) -> None:
        self._alpha = alpha
        self._x: float | None = None
        self._y: float | None = None

        # Adaptive parameters
        self._prev_raw_x: float | None = None
        self._prev_raw_y: float | None = None
        # Velocity threshold (px/frame) above which alpha is reduced
        self._velocity_threshold: float = 30.0
        # How aggressively to reduce alpha under fast movement
        self._adaptive_strength: float = 0.40

    # ── Public API ─────────────────────────────────────────────────────────

    def update(self, raw_x: float, raw_y: float) -> tuple[int, int]:
        """
        Feed a new raw position and return the smoothed position.

        Parameters
        ----------
        raw_x, raw_y : float
            Raw fingertip pixel coordinates.

        Returns
        -------
        (smooth_x, smooth_y) : tuple[int, int]
            Filtered coordinates ready for use in drawing/UI.
        """
        if self._x is None:
            # Bootstrap on the first sample
            self._x = float(raw_x)
            self._y = float(raw_y)
            self._prev_raw_x = raw_x
            self._prev_raw_y = raw_y
            return (int(self._x), int(self._y))

        # Compute raw velocity
        vx = raw_x - (self._prev_raw_x or raw_x)
        vy = raw_y - (self._prev_raw_y or raw_y)
        velocity = math.hypot(vx, vy)

        # Adaptive alpha: reduce smoothing proportionally to velocity
        if velocity > self._velocity_threshold:
            ratio = min(1.0, (velocity - self._velocity_threshold) / 60.0)
            effective_alpha = self._alpha * (1.0 - ratio * self._adaptive_strength)
        else:
            effective_alpha = self._alpha

        # EMA update  (output = alpha * previous + (1-alpha) * new_input)
        self._x = effective_alpha * self._x + (1.0 - effective_alpha) * raw_x
        self._y = effective_alpha * self._y + (1.0 - effective_alpha) * raw_y

        self._prev_raw_x = raw_x
        self._prev_raw_y = raw_y

        return (int(self._x), int(self._y))

    def reset(self) -> None:
        """Forget state; next call to :meth:`update` bootstraps again."""
        self._x = None
        self._y = None
        self._prev_raw_x = None
        self._prev_raw_y = None

    @property
    def position(self) -> tuple[int, int] | None:
        """Last smoothed position, or None before first update."""
        if self._x is None:
            return None
        return (int(self._x), int(self._y))

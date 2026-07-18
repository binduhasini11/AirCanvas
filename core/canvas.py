"""
AirCanvas – Canvas buffer management.

Maintains the persistent drawing surface as a white BGR image, composites
it over the live camera frame, and manages undo/redo history.
"""
from __future__ import annotations

import copy

import cv2
import numpy as np

from utils.constants import CANVAS_ALPHA, MAX_UNDO_STEPS


class Canvas:
    """
    Persistent drawing surface.

    Internally stores two numpy arrays:
    - ``_layer``   – The artwork layer (white background, BGR).
    - ``_mask``    – Binary mask: 255 where a stroke has been painted,
                     0 elsewhere.  Used to composite over the camera.

    Undo/Redo is implemented by storing copies of ``(_layer, _mask)``
    at snapshot points (typically end of each stroke).

    Parameters
    ----------
    width, height : int
        Canvas dimensions in pixels (should match camera resolution).
    """

    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height

        self._layer = self._make_white()
        self._mask = np.zeros((height, width), dtype=np.uint8)

        # Undo stack: list of (layer, mask) snapshots
        self._undo_stack: list[tuple[np.ndarray, np.ndarray]] = []
        # Redo stack: list of (layer, mask) snapshots
        self._redo_stack: list[tuple[np.ndarray, np.ndarray]] = []

    # ── Internal helpers ───────────────────────────────────────────────────

    def _make_white(self) -> np.ndarray:
        return np.full(
            (self._height, self._width, 3), 255, dtype=np.uint8
        )

    # ── Drawing surface access ─────────────────────────────────────────────

    @property
    def layer(self) -> np.ndarray:
        """The BGR artwork layer (white background)."""
        return self._layer

    @property
    def mask(self) -> np.ndarray:
        """Binary mask where paint has been applied."""
        return self._mask

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    # ── Clear ──────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Clear the canvas to white and record an undo snapshot."""
        self._push_undo()
        self._layer = self._make_white()
        self._mask = np.zeros((self._height, self._width), dtype=np.uint8)

    def _reset_no_history(self) -> None:
        """Clear without modifying history (used by undo/redo)."""
        self._layer = self._make_white()
        self._mask = np.zeros((self._height, self._width), dtype=np.uint8)

    # ── Undo / Redo ────────────────────────────────────────────────────────

    def push_snapshot(self) -> None:
        """
        Save the current state so it can be restored with :meth:`undo`.

        Call this at the *end* of a stroke (when the user releases the pinch).
        """
        self._push_undo()
        self._redo_stack.clear()

    def _push_undo(self) -> None:
        self._undo_stack.append(
            (self._layer.copy(), self._mask.copy())
        )
        if len(self._undo_stack) > MAX_UNDO_STEPS:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        """
        Restore the previous state.

        Returns
        -------
        bool
            True if undo was possible, False if history is empty.
        """
        if not self._undo_stack:
            return False
        # Save current state to redo before popping
        self._redo_stack.append(
            (self._layer.copy(), self._mask.copy())
        )
        layer, mask = self._undo_stack.pop()
        self._layer = layer
        self._mask = mask
        return True

    def redo(self) -> bool:
        """
        Re-apply an undone action.

        Returns
        -------
        bool
            True if redo was possible, False if redo stack is empty.
        """
        if not self._redo_stack:
            return False
        self._undo_stack.append(
            (self._layer.copy(), self._mask.copy())
        )
        layer, mask = self._redo_stack.pop()
        self._layer = layer
        self._mask = mask
        return True

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    # ── Compositing ────────────────────────────────────────────────────────

    def composite_onto(self, frame: np.ndarray) -> np.ndarray:
        """
        Blend the drawing layer onto *frame* and return the result.

        Pixels that have never been painted show the raw camera feed.
        Painted pixels blend the artwork over the feed at ``CANVAS_ALPHA``
        opacity, giving a watercolour-over-video feel.

        Parameters
        ----------
        frame : np.ndarray
            BGR camera frame (same resolution as the canvas).

        Returns
        -------
        np.ndarray
            New BGR image ready for display.
        """
        out = frame.copy()

        # Only composite where strokes exist
        stroke_mask = self._mask.astype(bool)

        if stroke_mask.any():
            # Blend artwork into camera feed where mask is set
            blended = cv2.addWeighted(
                self._layer, CANVAS_ALPHA,
                frame,        1.0 - CANVAS_ALPHA,
                0,
            )
            out[stroke_mask] = blended[stroke_mask]

        return out

    def as_png_array(self) -> np.ndarray:
        """Return the artwork composited on a pure white background (for saving)."""
        white = np.full(
            (self._height, self._width, 3), 255, dtype=np.uint8
        )
        # Where mask is set, use the artwork; elsewhere keep white
        out = white.copy()
        stroke_mask = self._mask.astype(bool)
        out[stroke_mask] = self._layer[stroke_mask]
        return out

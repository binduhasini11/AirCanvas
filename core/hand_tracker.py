"""
AirCanvas – Hand tracking module.
Wraps cvzone HandDetector (MediaPipe backend) and exposes a clean, application-level interface for fingertip positions and pinch detection.
"""
from __future__ import annotations
from dataclasses import dataclass
import cv2
import numpy as np

from utils.constants import (
    HAND_DETECTION_CONFIDENCE,
    HAND_TRACKING_CONFIDENCE,
    INDEX_MCP,
    INDEX_TIP,
    MAX_HANDS,
    PINCH_RELEASE_THRESHOLD_PX,
    PINCH_THRESHOLD_PX,
    THUMB_TIP,
)
from utils.helpers import distance

# Import cvzone lazily so import errors surface as a helpful message
try:
    from cvzone.HandTrackingModule import HandDetector as _HandDetector  # type: ignore[import]
except ImportError as exc:
    raise ImportError(
        "[HandTracker] cvzone is not installed. "
        "Run: pip install cvzone mediapipe"
    ) from exc


@dataclass
class HandState:
    """Snapshot of one hand's state for a single frame."""

    detected: bool = False
    index_tip: tuple[int, int] = (0, 0)     # Index fingertip pixel coords
    thumb_tip: tuple[int, int] = (0, 0)     # Thumb tip pixel coords
    pinch_distance: float = 999.0
    is_pinching: bool = False                # Hysteresis-gated pinch flag
    landmarks: list[list[int]] | None = None # All 21 landmarks (x, y, z)


class HandTracker:
    """
    Real-time hand tracker for one hand.

    Detects the index fingertip cursor position and a pinch gesture
    (thumb + index finger close together).

    Parameters
    ----------
    detection_con : float
        Minimum detection confidence (0–1).
    tracking_con : float
        Minimum tracking confidence (0–1).
    """

    def __init__(
        self,
        detection_con: float = HAND_DETECTION_CONFIDENCE,
        tracking_con: float = HAND_TRACKING_CONFIDENCE,
    ) -> None:
        self._detector = _HandDetector(
            detectionCon=detection_con,
            minTrackCon=tracking_con,
            maxHands=MAX_HANDS,
        )
        self._was_pinching = False
        self._state = HandState()

    # ── Public API ─────────────────────────────────────────────────────────

    def process(self, frame: np.ndarray) -> HandState:
        """
        Run hand detection on *frame* and return the updated :class:`HandState`.

        The detector may draw debug overlays on *frame* if it is configured
        to do so – this is disabled here to keep the frame clean.

        Parameters
        ----------
        frame : np.ndarray
            BGR camera frame (will not be modified).

        Returns
        -------
        HandState
            Current hand state.
        """
        hands, _ = self._detector.findHands(frame, draw=False, flipType=False)

        if not hands:
            self._state = HandState(detected=False)
            self._was_pinching = False
            return self._state

        hand = hands[0]
        lm = hand["lmList"]          # shape: (21, 3)  –  x, y, z per landmark

        thumb_tip = (int(lm[THUMB_TIP][0]), int(lm[THUMB_TIP][1]))
        index_tip = (int(lm[INDEX_TIP][0]), int(lm[INDEX_TIP][1]))

        pinch_dist = distance(thumb_tip, index_tip)

        # Hysteresis: enter pinch when dist < THRESHOLD, leave when > RELEASE
        if self._was_pinching:
            is_pinching = pinch_dist < PINCH_RELEASE_THRESHOLD_PX
        else:
            is_pinching = pinch_dist < PINCH_THRESHOLD_PX
        self._was_pinching = is_pinching

        self._state = HandState(
            detected=True,
            index_tip=index_tip,
            thumb_tip=thumb_tip,
            pinch_distance=pinch_dist,
            is_pinching=is_pinching,
            landmarks=lm,
        )
        return self._state

    @property
    def state(self) -> HandState:
        """Most recent hand state (from the last :meth:`process` call)."""
        return self._state

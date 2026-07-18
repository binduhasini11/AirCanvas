"""
AirCanvas – Camera capture abstraction.

Wraps OpenCV VideoCapture with resolution configuration and graceful
fallback when the requested resolution is not supported by the hardware.
"""
from __future__ import annotations

import cv2
import numpy as np

from utils.constants import (
    CAMERA_FLIP,
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
)


class Camera:
    """
    Manages a single webcam capture session.

    Usage
    -----
    ::

        cam = Camera()
        cam.open()
        while running:
            frame = cam.read()
            ...
        cam.release()

    Or use as a context manager::

        with Camera() as cam:
            frame = cam.read()
    """

    def __init__(
        self,
        index: int = CAMERA_INDEX,
        width: int = CAMERA_WIDTH,
        height: int = CAMERA_HEIGHT,
        flip: bool = CAMERA_FLIP,
    ) -> None:
        self._index = index
        self._requested_width = width
        self._requested_height = height
        self._flip = flip

        self._cap: cv2.VideoCapture | None = None
        self._actual_width: int = width
        self._actual_height: int = height

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def open(self) -> None:
        """Open the camera device and configure resolution."""
        self._cap = cv2.VideoCapture(self._index)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"[Camera] Cannot open camera at index {self._index}. "
                "Check that a webcam is connected and not in use by another app."
            )

        # Request resolution (hardware may silently ignore unsupported values)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._requested_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._requested_height)

        # Read back the actual resolution the driver chose
        self._actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(
            f"[Camera] Opened index={self._index} "
            f"({self._actual_width}×{self._actual_height})"
        )

    def release(self) -> None:
        """Release the camera device."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    # ── Context manager ────────────────────────────────────────────────────

    def __enter__(self) -> "Camera":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()

    # ── Frame acquisition ──────────────────────────────────────────────────

    def read(self) -> np.ndarray | None:
        """
        Capture and return one frame.

        Returns
        -------
        np.ndarray or None
            BGR frame, or None if the capture failed.
        """
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        if self._flip:
            frame = cv2.flip(frame, 1)
        return frame

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def width(self) -> int:
        """Actual capture width in pixels."""
        return self._actual_width

    @property
    def height(self) -> int:
        """Actual capture height in pixels."""
        return self._actual_height

    @property
    def is_open(self) -> bool:
        """True while the capture device is open."""
        return self._cap is not None and self._cap.isOpened()

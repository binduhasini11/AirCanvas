"""
AirCanvas – Entry point.
Wires together the camera, hand tracker, drawing engine, and UI elements into the main application loop.

Run with:
    python main.py
"""
from __future__ import annotations

import sys
import time
import cv2
import numpy as np

# ── Local imports ───
from core.camera import Camera
from core.canvas import Canvas
from core.drawing import DrawingEngine, Tool
from core.hand_tracker import HandTracker
from core.smoothing import PositionSmoother
from ui.cursor import CursorRenderer
from ui.statusbar import StatusBar
from ui.toolbar import Toolbar
from utils.constants import (
    FLASH_DURATION_FRAMES,
    KEY_CLEAR,
    KEY_FULLSCREEN,
    KEY_QUIT,
    KEY_REDO,
    KEY_SAVE,
    KEY_UNDO,
    STATUS_BAR_HEIGHT,
    TOOLBAR_HEIGHT,
    WINDOW_TITLE,
)
from utils.helpers import fps_string, save_canvas


class AirCanvasApp:
    """
    Top-level application controller.

    Manages the event loop, coordinates all subsystems, and handles
    keyboard shortcuts and flash animation.
    """

    def __init__(self) -> None:
        # Camera
        self._camera = Camera()

        # These are initialised in setup() once the actual frame size is known
        self._canvas: Canvas | None = None
        self._engine: DrawingEngine | None = None
        self._smoother = PositionSmoother()
        self._tracker = HandTracker()
        self._toolbar: Toolbar | None = None
        self._cursor_renderer: CursorRenderer | None = None
        self._status_bar: StatusBar | None = None

        # State flags
        self._running = False
        self._fullscreen = False

        # Flash animation (save feedback)
        self._flash_frames = 0

        # FPS tracking
        self._prev_time = time.monotonic()
        self._fps_str = "-- FPS"

    # ── Lifecycle ────

    def setup(self, width: int, height: int) -> None:
        """Initialise subsystems once the actual frame resolution is known."""
        self._canvas = Canvas(width, height)
        self._engine = DrawingEngine(self._canvas)

        self._toolbar = Toolbar(
            frame_width=width,
            engine=self._engine,
            on_clear=self._do_clear,
            on_save=self._do_save,
            on_undo=self._do_undo,
            on_redo=self._do_redo,
        )
        self._cursor_renderer = CursorRenderer(self._engine)
        self._status_bar = StatusBar(width, height, self._engine)

    def run(self) -> None:
        """Open the camera and enter the main loop."""
        with self._camera:
            # Read a test frame to get the actual resolution
            test_frame = self._camera.read()
            if test_frame is None:
                print("[AirCanvas] Failed to read from camera. Exiting.")
                sys.exit(1)

            self.setup(self._camera.width, self._camera.height)

            cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(
                WINDOW_TITLE, self._camera.width, self._camera.height
            )

            self._running = True
            print("[AirCanvas] Running. Press Q to quit, S to save, C to clear.")

            while self._running:
                frame = self._camera.read()
                if frame is None:
                    print("[AirCanvas] Camera read failed; exiting.")
                    break

                display = self._process_frame(frame)
                cv2.imshow(WINDOW_TITLE, display)

                key = cv2.waitKey(1) & 0xFF
                self._handle_key(key)

                # Window close button
                if cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
                    self._running = False

        cv2.destroyAllWindows()
        print("[AirCanvas] Goodbye.")

    # ── Frame processing ───

    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Run one frame of the pipeline and return the display image."""
        assert self._canvas is not None
        assert self._engine is not None
        assert self._toolbar is not None
        assert self._cursor_renderer is not None
        assert self._status_bar is not None

        # ── FPS ───
        now = time.monotonic()
        elapsed = now - self._prev_time
        self._prev_time = now
        self._fps_str = fps_string(elapsed)
        self._status_bar.set_fps(self._fps_str)

        # ── Hand tracking ───
        hand = self._tracker.process(frame)

        if hand.detected:
            sx, sy = self._smoother.update(*hand.index_tip)
            cursor = (sx, sy)
        else:
            self._smoother.reset()
            self._engine.end_stroke()
            cursor = None

        # ── Toolbar update (must happen before drawing logic) ──────────
        over_toolbar = False
        if cursor is not None:
            over_toolbar = self._toolbar.update(cursor, hand.is_pinching)

        # ── Drawing logic ──
        if cursor is not None and not over_toolbar:
            if hand.is_pinching:
                if not self._engine.is_drawing:
                    self._engine.begin_stroke(cursor)
                else:
                    self._engine.continue_stroke(cursor)
            else:
                if self._engine.is_drawing:
                    self._engine.end_stroke()

        # ── Compositing ───
        # 1. Blend canvas onto camera feed
        display = self._canvas.composite_onto(frame)

        # 2. Toolbar
        self._toolbar.draw(display)

        # 3. Cursor
        if cursor is not None:
            self._cursor_renderer.draw(
                display,
                cursor,
                hand.is_pinching,
                hand.pinch_distance,
            )

        # 4. Status bar
        tooltip = self._toolbar.hovered_tooltip if cursor is not None else ""
        self._status_bar.draw(display, tooltip)

        # 5. Flash overlay (save animation)
        if self._flash_frames > 0:
            alpha = self._flash_frames / FLASH_DURATION_FRAMES
            white = np.full_like(display, 255)
            cv2.addWeighted(white, alpha * 0.6, display, 1.0 - alpha * 0.6, 0, display)
            self._flash_frames -= 1

        return display

    # ── Actions ───
    def _do_clear(self) -> None:
        assert self._canvas is not None
        self._canvas.clear()
        assert self._status_bar is not None
        self._status_bar.show_message("Canvas cleared", duration_frames=60)

    def _do_save(self) -> None:
        assert self._canvas is not None
        artwork = self._canvas.as_png_array()
        path = save_canvas(artwork)
        self._flash_frames = FLASH_DURATION_FRAMES
        assert self._status_bar is not None
        if path:
            self._status_bar.show_message(f"Saved → {path}", duration_frames=90)
            print(f"[AirCanvas] Saved to {path}")
        else:
            self._status_bar.show_message("Save failed!", duration_frames=90)

    def _do_undo(self) -> None:
        assert self._canvas is not None
        assert self._status_bar is not None
        if self._canvas.undo():
            self._status_bar.show_message("Undo", duration_frames=45)
        else:
            self._status_bar.show_message("Nothing to undo", duration_frames=45)

    def _do_redo(self) -> None:
        assert self._canvas is not None
        assert self._status_bar is not None
        if self._canvas.redo():
            self._status_bar.show_message("Redo", duration_frames=45)
        else:
            self._status_bar.show_message("Nothing to redo", duration_frames=45)

    def _toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        flag = cv2.WINDOW_FULLSCREEN if self._fullscreen else cv2.WINDOW_NORMAL
        cv2.setWindowProperty(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, flag)

    # ── Keyboard handling ────
    def _handle_key(self, key: int) -> None:
        if key == 255 or key == -1:   # No key pressed (waitKey returns 255/−1)
            return
        if key == KEY_QUIT:
            self._running = False
        elif key == KEY_CLEAR:
            self._do_clear()
        elif key == KEY_SAVE:
            self._do_save()
        elif key == KEY_UNDO:
            self._do_undo()
        elif key == KEY_REDO:
            self._do_redo()
        elif key == KEY_FULLSCREEN:
            self._toggle_fullscreen()


# ── Entry point ───

def main() -> None:
    """Bootstrap and run AirCanvas."""
    import os
    from utils.constants import SAVE_DIR
    os.makedirs(SAVE_DIR, exist_ok=True)

    app = AirCanvasApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[AirCanvas] Interrupted by user.")
    except Exception as exc:
        print(f"[AirCanvas] Fatal error: {exc}")
        raise


if __name__ == "__main__":
    main()

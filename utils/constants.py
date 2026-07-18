"""
AirCanvas – Application-wide configuration constants.
All tunable values live here; no magic numbers elsewhere.
"""

# ── Window ───
WINDOW_TITLE = "AirCanvas"
WINDOW_FLAGS_NORMAL = 0          # cv2.WINDOW_NORMAL equivalent (0)
TARGET_FPS = 30

# ── Camera ───
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FLIP = True               # Mirror the frame (more natural for drawing)

# ── Hand Tracking ───
HAND_DETECTION_CONFIDENCE = 0.75
HAND_TRACKING_CONFIDENCE = 0.75
MAX_HANDS = 1

# Landmark indices (MediaPipe)
THUMB_TIP = 4
INDEX_TIP = 8
INDEX_MCP = 5                    # Index finger knuckle (for hand-open detection)

# Pinch gesture
PINCH_THRESHOLD_PX = 45          # Distance (px) below which a pinch is registered
PINCH_RELEASE_THRESHOLD_PX = 60  # Hysteresis to prevent flicker on release

# ── Cursor Smoothing ──
SMOOTHING_FACTOR = 0.55          # 0 = no smoothing, 1 = frozen; EMA alpha

# ── Drawing ──
DEFAULT_BRUSH_SIZE = 8
MIN_BRUSH_SIZE = 2
MAX_BRUSH_SIZE = 60
BRUSH_SIZE_STEP = 2
ERASER_SIZE_MULTIPLIER = 3       # Eraser is this many times the brush size
MAX_INTERPOLATION_DISTANCE = 6   # Max gap to interpolate between (px)

# ── Undo / Redo ─────
MAX_UNDO_STEPS = 25

# ── Toolbar ───
TOOLBAR_HEIGHT = 70
TOOLBAR_PADDING = 10
TOOLBAR_BUTTON_SIZE = 44         # Square button side length
TOOLBAR_BUTTON_GAP = 8
TOOLBAR_CORNER_RADIUS = 16
TOOLBAR_ALPHA = 0.82             # Glassmorphism fill opacity

# Hover detection requires the cursor to dwell for this many frames
# before triggering a button action (prevents accidental clicks during drawing)
TOOLBAR_PINCH_COOLDOWN_FRAMES = 18

# ── Status Bar ────
STATUS_BAR_HEIGHT = 32
STATUS_BAR_ALPHA = 0.70
STATUS_FONT_SCALE = 0.48
STATUS_FONT_THICKNESS = 1

# ── Canvas Compositing ────
CANVAS_ALPHA = 0.92              # How opaque the drawing layer is over the feed

# ── Saved Drawings ─────
SAVE_DIR = "saved_drawings"
SAVE_PREFIX = "aircanvas"

# ── Keyboard shortcuts ────
KEY_QUIT = ord("q")
KEY_CLEAR = ord("c")
KEY_SAVE = ord("s")
KEY_UNDO = ord("z")
KEY_REDO = ord("y")
KEY_FULLSCREEN = ord("f")

# ── Flash animation (save feedback) ─────
FLASH_DURATION_FRAMES = 12       # White-flash frames on save

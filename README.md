# AirCanvas ✋🎨

A gesture-controlled virtual painting application.
Draw naturally in the air using only your webcam ; no mouse or touchscreen needed.

---

## Features

- **Real-time hand tracking** via MediaPipe through cvzone
- **Pinch gesture** : pinch thumb + index to draw; release to lift the pen
- **Adaptive cursor smoothing** : jitter-free strokes while staying responsive
- **Anti-aliased strokes** with rounded caps and dense interpolation
- **Glassmorphism toolbar** with frosted-glass blur effect
- **8-color palette**, brush tool, and eraser
- **Adjustable brush size** (2 - 60 px)
- **Undo / Redo** (up to 25 levels)
- **Clear canvas** with undo support
- **Save drawing** as PNG on a white background
- **Flash animation** on save
- **FPS counter** and status bar
- **Fullscreen mode**

---

## Installation

```bash
pip install -r requirements.txt
```

> **Note:** `mediapipe` requires Python 3.8–3.11. It does not currently support Python 3.12+.

---

## Running

```bash
python main.py
```

Run from the `AirCanvas/` directory (or adjust your `PYTHONPATH` accordingly).

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `C` | Clear canvas |
| `S` | Save drawing |
| `Z` | Undo |
| `Y` | Redo |
| `F` | Toggle fullscreen |

---

## Gesture Controls

| Gesture | Action |
|---------|--------|
| Index finger in air | Move cursor |
| Pinch (thumb + index) | Draw / select toolbar button |
| Release pinch | Lift pen / confirm selection |

---

## Project Structure

```
AirCanvas/
├── main.py                 ← Entry point; application loop
├── requirements.txt
├── README.md
│
├── core/
│   ├── camera.py           ← Camera capture abstraction
│   ├── hand_tracker.py     ← cvzone/MediaPipe wrapper + pinch detection
│   ├── canvas.py           ← Drawing surface + undo/redo history
│   ├── drawing.py          ← Stroke engine (anti-aliasing, interpolation)
│   └── smoothing.py        ← Adaptive EMA cursor filter
│
├── ui/
│   ├── toolbar.py          ← Glassmorphism floating toolbar
│   ├── buttons.py          ← Button widget classes
│   ├── cursor.py           ← Crosshair + brush-preview renderer
│   └── statusbar.py        ← Bottom status strip
│
├── utils/
│   ├── constants.py        ← All configuration values
│   ├── colors.py           ← Color definitions + palette
│   └── helpers.py          ← Geometry, file I/O, text rendering utilities
│
├── assets/
│   └── icons/
│
└── saved_drawings/         ← Output PNGs land here
```

---

## Saved Drawings

Artworks are saved inside `saved_drawings/` as timestamped PNGs:

```
saved_drawings/aircanvas_20240718_143022.png
```

Each file contains only the artwork on a clean white background.

---

## Configuration

All tunable values live in `utils/constants.py`:

- `SMOOTHING_FACTOR` — cursor EMA strength (0 = none, 1 = frozen)
- `PINCH_THRESHOLD_PX` — distance (px) for pinch detection
- `DEFAULT_BRUSH_SIZE`, `MIN_BRUSH_SIZE`, `MAX_BRUSH_SIZE`
- `MAX_UNDO_STEPS` — undo history depth
- `CAMERA_INDEX` — change if your webcam is not device 0

---

## Requirements

- Python 3.8 – 3.11
- Webcam
- OpenCV, cvzone, MediaPipe, NumPy (see `requirements.txt`)

---

## 🤝 Contributing

Contributions are welcome!

If you'd like to improve AirCanvas, feel free to:

- Report bugs or suggest new features by opening an Issue.
- Submit improvements through Pull Requests.
- Enhance gesture recognition, UI/UX, or drawing capabilities.

Please ensure your changes are well-tested and follow the existing project structure and coding style.

---

## 👩‍💻 Author

**Bindu Hasini**

B.Tech CSE @ VIT Vellore • AI & Computer Vision Enthusiast

- 🐙 GitHub: https://github.com/binduhasini11
- 💼 LinkedIn: linkedin.com/in/bindu-hasini-b-5a38bb225/

If you found this project interesting, consider ⭐ starring the repository!

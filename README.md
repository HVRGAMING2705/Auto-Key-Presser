# Macro Recorder

The original repo pressed one key on a loop. This is a full macro
system: **record** keyboard/mouse input with timing, save it as editable
JSON, then **replay** it with loop counts and speed control.

## Legitimate uses

- **UI testing**: replay exact input sequences against your own apps
- **Accessibility**: one-key replay of complex input chains
- **Productivity**: automate repetitive form-filling on your own machine
- **Demos**: scripted walkthroughs with precise timing

## Responsible use

Only record and replay input on machines and applications you own or
have explicit permission to automate. Do not use macros to spam,
cheat in games where automation is prohibited, or evade rate limits.
Playback can always be stopped instantly with Esc.

## Features

- `recorder.py` — captures key down/up, mouse moves (throttled),
  clicks with timestamps; Esc stops recording and the Esc press
  itself is stripped from the saved macro
- `macro.py` — `Macro` model: strict JSON save/load (unknown event
  types, missing keys, negative/NaN times are rejected with a clear
  `ValueError`, never a traceback), `filter_type`, `trim`,
  `drop_mouse_moves`, `with_speed`, `remap_keys` editing
- `player.py` — faithful-timing replay; `--loops`, `--speed`,
  `--drop-moves`; Esc aborts mid-playback; `DryRunPlayer` for
  headless simulation (imports no `pynput`, so it can never emit
  real input) with `plan()` — the exact timed step list the web
  simulator mirrors
- `cli.py` — `record`, `play`, `info`, `validate` subcommands
- `test_macro.py` — headless test suite (45 checks: model, editing,
  serialization, playback, schema rejection, speed/loop edge cases)
- `index.html` — honest web companion: this page **cannot** record
  your keyboard or mouse (browsers can't). It really does edit and
  validate macro JSON against the same schema, simulate playback
  with true timestamps ÷ speed, preview dry-run step counts/times,
  remap keys, and download a runnable `.json`. Edited macros save
  only to your browser's localStorage — nothing is uploaded.

## How to run

```bash
pip install -r requirements.txt   # pynput (record/live-play only)
python cli.py record --out demo.json
python cli.py validate demo.json
python cli.py info demo.json
python cli.py play demo.json --loops 2 --speed 1.5
python cli.py play demo.json --dry-run      # simulate, touch nothing
python test_macro.py                       # headless tests
```

## Macro file format

```json
{
  "name": "demo",
  "events": [
    {"type": "key_down", "t": 0.0, "key": "a"},
    {"type": "key_up", "t": 0.1, "key": "a"},
    {"type": "mouse_move", "t": 0.2, "x": 100, "y": 200}
  ]
}
```

Events are plain JSON — hand-edit timings, delete steps, or generate
macros programmatically.

## Requirements

Recording and live playback need a display and `pynput`.
Tests, `--dry-run`, and macro editing need only the standard library.

"""Macro recorder: captures keyboard/mouse input into a Macro.

Requires the `pynput` package and a display. Recording is fully
optional — everything else (editing, replay, tests) works headless.
"""
import time

from macro import Macro


class Recorder:
    def __init__(self):
        self.macro = Macro()
        self._t0 = None

    def _now(self):
        return time.time() - self._t0

    def start(self, name="recording"):
        try:
            from pynput import keyboard, mouse
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"recording needs pynput and a display: {exc}")
        self.macro = Macro(name)
        self._t0 = time.time()
        self._stop = False

        def on_press(key):
            self.macro.add("key_down", self._now(), key=_key_name(key))
            if key == keyboard.Key.esc:
                self._stop = True
                return False  # Esc stops recording

        def on_release(key):
            self.macro.add("key_up", self._now(), key=_key_name(key))

        def on_move(x, y):
            # throttle: record moves at most every 50 ms
            if not self.macro.events or self._now() - self.macro.events[-1]["t"] > 0.05:
                self.macro.add("mouse_move", self._now(), x=x, y=y)

        def on_click(x, y, button, pressed):
            self.macro.add("mouse_down" if pressed else "mouse_up",
                           self._now(), x=x, y=y, button=str(button))

        kl = keyboard.Listener(on_press=on_press, on_release=on_release)
        ml = mouse.Listener(on_move=on_move, on_click=on_click)
        kl.start()
        ml.start()
        print("Recording... press Esc to stop.")
        while not self._stop:
            time.sleep(0.05)
        kl.stop()
        ml.stop()
        # drop the Esc key_up that stopped us (usually noise)
        self.macro.events = [e for e in self.macro.events
                             if not (e["type"] == "key_up" and e.get("key") == "Key.esc")]
        print(f"Recorded {len(self.macro.events)} events "
              f"({self.macro.duration:.1f}s).")
        return self.macro


def _key_name(key):
    try:
        return key.char
    except AttributeError:
        return str(key)

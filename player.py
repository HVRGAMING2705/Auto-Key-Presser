"""Macro player: replays a Macro with loop counts, speed control, and
dry-run mode. Live playback needs pynput + display; dry-run is headless.
"""
import time


class DryRunPlayer:
    """Replays into a recorded action list instead of the real inputs."""

    def __init__(self):
        self.played = []  # (loop, event) tuples

    def play(self, macro, loops=1, speed=1.0):
        if loops < 1:
            raise ValueError("loops must be >= 1")
        if speed <= 0:
            raise ValueError("speed must be > 0")
        scaled = macro.with_speed(speed)
        for loop in range(loops):
            for e in scaled.events:
                self.played.append((loop, dict(e)))
        return len(self.played)


class LivePlayer:
    """Replays through pynput with faithful timing."""

    def __init__(self):
        try:
            from pynput.keyboard import Controller as KController, Key
            from pynput.mouse import Controller as MController, Button
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"live playback needs pynput and a display: {exc}")
        self.kb = KController()
        self.ms = MController()
        self.Key = Key
        self.Button = Button

    def play(self, macro, loops=1, speed=1.0, stop_key="esc"):
        from pynput import keyboard
        if loops < 1:
            raise ValueError("loops must be >= 1")
        stopped = {"v": False}

        def on_press(key):
            if key == keyboard.Key.esc:
                stopped["v"] = True
                return False

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        try:
            scaled = macro.with_speed(speed)
            for _ in range(loops):
                prev_t = 0.0
                for e in scaled.events:
                    if stopped["v"]:
                        print("stopped by Esc")
                        return
                    time.sleep(max(0.0, e["t"] - prev_t))
                    prev_t = e["t"]
                    self._fire(e)
        finally:
            listener.stop()

    def _fire(self, e):
        t = e["type"]
        if t == "key_down":
            self.kb.press(self._key(e["key"]))
        elif t == "key_up":
            self.kb.release(self._key(e["key"]))
        elif t == "mouse_move":
            self.ms.position = (e["x"], e["y"])
        elif t == "mouse_down":
            self.ms.press(self._button(e.get("button", "Button.left")))
        elif t == "mouse_up":
            self.ms.release(self._button(e.get("button", "Button.left")))

    def _key(self, name):
        if len(name or "") == 1:
            return name
        return getattr(self.Key, name.split(".")[-1], name)

    def _button(self, name):
        return getattr(self.Button, name.split(".")[-1], self.Button.left)

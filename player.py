"""Macro player: replays a Macro with loop counts, speed control, and
dry-run mode. Live playback needs pynput + display; dry-run is headless
and never imports pynput, so it can never emit real input.
"""
import time


class DryRunPlayer:
    """Replays into a recorded action list instead of the real inputs."""

    def __init__(self):
        self.played = []  # (loop, event) tuples, across all play() calls

    def plan(self, macro, loops=1, speed=1.0):
        """Timed preview of a replay: one step per event per loop.

        Each step: {"loop", "t" (scaled timestamp), "delay" (seconds
        after the previous step in the same loop), "event"}. The web
        timeline simulator mirrors this exact plan, so what you preview
        in the browser is what --dry-run reports on the desktop.
        """
        if loops < 1:
            raise ValueError("loops must be >= 1")
        if speed <= 0:
            raise ValueError("speed must be > 0")
        scaled = macro.with_speed(speed)
        steps = []
        for loop in range(loops):
            prev_t = 0.0
            for e in scaled.events:
                steps.append({"loop": loop, "t": e["t"],
                              "delay": round(e["t"] - prev_t, 4),
                              "event": dict(e)})
                prev_t = e["t"]
        return steps

    def play(self, macro, loops=1, speed=1.0):
        """Dry-run a replay. Returns the number of events THIS call
        played (not the cumulative total across calls — that was a bug:
        a second play() call used to report the running total)."""
        steps = self.plan(macro, loops=loops, speed=speed)
        for s in steps:
            self.played.append((s["loop"], s["event"]))
        return len(steps)


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
        if speed <= 0:
            raise ValueError("speed must be > 0")
        stop_target = self._stop_target(stop_key)
        stopped = {"v": False}

        def on_press(key):
            if key == stop_target or getattr(key, "char", None) == stop_key:
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

    def _stop_target(self, stop_key):
        if stop_key == "esc":
            return self.Key.esc
        if len(stop_key or "") == 1:
            return stop_key  # matched via key.char in on_press
        return getattr(self.Key, stop_key.split(".")[-1], stop_key)

    def _fire(self, e):
        t = e["type"]
        if t == "key_down":
            self.kb.press(self._key(e.get("key")))
        elif t == "key_up":
            self.kb.release(self._key(e.get("key")))
        elif t == "mouse_move":
            if e.get("x") is None or e.get("y") is None:
                raise ValueError(f"mouse_move event needs x and y: {e!r}")
            self.ms.position = (e["x"], e["y"])
        elif t == "mouse_down":
            self.ms.press(self._button(e.get("button", "Button.left")))
        elif t == "mouse_up":
            self.ms.release(self._button(e.get("button", "Button.left")))
        else:
            raise ValueError(f"unknown event type {t!r}")

    def _key(self, name):
        if not name:
            raise ValueError("key event needs a non-empty 'key'")
        if len(name) == 1:
            return name
        return getattr(self.Key, name.split(".")[-1], name)

    def _button(self, name):
        return getattr(self.Button, (name or "").split(".")[-1], self.Button.left)

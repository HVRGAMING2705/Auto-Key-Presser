"""Macro data model: timed keyboard/mouse events, JSON-serializable,
editable, replayable.
"""
import json
import time

EVENT_TYPES = ("key_down", "key_up", "mouse_move", "mouse_down", "mouse_up")


class Macro:
    """An ordered list of timestamped events. t=0 is the first event."""

    def __init__(self, name="untitled", events=None):
        self.name = name
        self.events = list(events or [])

    def add(self, etype, t, **kwargs):
        if etype not in EVENT_TYPES:
            raise ValueError(f"unknown event type {etype!r}")
        if t < 0:
            raise ValueError("event time must be >= 0")
        self.events.append({"type": etype, "t": round(t, 4), **kwargs})
        self.events.sort(key=lambda e: e["t"])

    @property
    def duration(self):
        return self.events[-1]["t"] if self.events else 0.0

    def to_dict(self):
        return {"name": self.name, "events": self.events}

    @classmethod
    def from_dict(cls, d):
        m = cls(d.get("name", "untitled"))
        for e in d.get("events", []):
            m.add(e["type"], e["t"],
                  **{k: v for k, v in e.items() if k not in ("type", "t")})
        return m

    def save(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    # ---- editing helpers ----

    def filter_type(self, etype):
        """Return a new macro with only events of the given type."""
        m = Macro(self.name + f"_{etype}")
        m.events = [e for e in self.events if e["type"] == etype]
        return m

    def trim(self, start, end):
        """Keep events in [start, end), re-based so t=0 is `start`."""
        m = Macro(self.name + "_trimmed")
        for e in self.events:
            if start <= e["t"] < end:
                e2 = dict(e)
                e2["t"] = round(e["t"] - start, 4)
                m.events.append(e2)
        return m

    def drop_mouse_moves(self):
        """Remove noisy mouse_move events (keeps clicks)."""
        m = Macro(self.name + "_nocursor")
        m.events = [e for e in self.events if e["type"] != "mouse_move"]
        return m

    def with_speed(self, factor):
        """Return a new macro with all timings scaled by 1/factor."""
        if factor <= 0:
            raise ValueError("speed factor must be > 0")
        m = Macro(self.name + f"_{factor}x")
        for e in self.events:
            e2 = dict(e)
            e2["t"] = round(e["t"] / factor, 4)
            m.events.append(e2)
        return m

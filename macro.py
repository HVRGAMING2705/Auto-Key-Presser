"""Macro data model: timed keyboard/mouse events, JSON-serializable,
editable, replayable.
"""
import json
import math

EVENT_TYPES = ("key_down", "key_up", "mouse_move", "mouse_down", "mouse_up")


def _validate_event_dict(e):
    """Validate one raw event dict; raise ValueError (never KeyError)."""
    if not isinstance(e, dict):
        raise ValueError(f"event must be an object, got {e!r}")
    etype = e.get("type")
    if etype not in EVENT_TYPES:
        raise ValueError(f"unknown event type {etype!r}")
    t = e.get("t")
    if isinstance(t, bool) or not isinstance(t, (int, float)) \
            or not math.isfinite(t) or t < 0:
        raise ValueError(f"event time must be a finite number >= 0, got {t!r}")
    if etype in ("key_down", "key_up") and not e.get("key"):
        raise ValueError(f"{etype} event needs a non-empty 'key'")
    if etype in ("mouse_move", "mouse_down", "mouse_up"):
        for axis in ("x", "y"):
            v = e.get(axis)
            if isinstance(v, bool) or not isinstance(v, (int, float)) \
                    or not math.isfinite(v):
                raise ValueError(f"{etype} event needs a finite '{axis}', got {v!r}")


class Macro:
    """An ordered list of timestamped events. t=0 is the first event."""

    def __init__(self, name="untitled", events=None):
        self.name = name
        self.events = list(events or [])

    def add(self, etype, t, **kwargs):
        if etype not in EVENT_TYPES:
            raise ValueError(f"unknown event type {etype!r}")
        if isinstance(t, bool) or not isinstance(t, (int, float)) \
                or not math.isfinite(t) or t < 0:
            raise ValueError(f"event time must be a finite number >= 0, got {t!r}")
        self.events.append({"type": etype, "t": round(t, 4), **kwargs})
        self.events.sort(key=lambda e: e["t"])

    @property
    def duration(self):
        return self.events[-1]["t"] if self.events else 0.0

    def to_dict(self):
        return {"name": self.name, "events": self.events}

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise ValueError(f"macro must be an object, got {type(d).__name__}")
        events = d.get("events", [])
        if not isinstance(events, list):
            raise ValueError("'events' must be a list")
        for e in events:
            _validate_event_dict(e)
        m = cls(d.get("name", "untitled"))
        for e in events:
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
        if etype not in EVENT_TYPES:
            raise ValueError(f"unknown event type {etype!r}")
        m = Macro(self.name + f"_{etype}")
        m.events = [e for e in self.events if e["type"] == etype]
        return m

    def trim(self, start, end):
        """Keep events in [start, end), re-based so t=0 is `start`."""
        if start < 0 or end <= start:
            raise ValueError(f"trim needs 0 <= start < end, got {start}, {end}")
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

    def remap_keys(self, mapping):
        """Return a new macro with key_down/key_up keys remapped.

        mapping: {old_key: new_key}. Keys not in the mapping are unchanged.
        This is what backs the web editor's remap box and makes the
        site's "remap keys" claim real.
        """
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError("remap mapping must be a non-empty object")
        m = Macro(self.name + "_remapped")
        for e in self.events:
            e2 = dict(e)
            if e2["type"] in ("key_down", "key_up") and e2.get("key") in mapping:
                e2["key"] = mapping[e2["key"]]
            m.events.append(e2)
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

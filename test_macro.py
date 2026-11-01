"""Headless tests for the Macro Recorder: model, editing, serialization,
and dry-run playback. No display needed.
"""
import json
import os
import tempfile

from macro import Macro
from player import DryRunPlayer

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name}")


def sample_macro():
    m = Macro("demo")
    m.add("key_down", 0.0, key="a")
    m.add("key_up", 0.1, key="a")
    m.add("mouse_move", 0.2, x=100, y=200)
    m.add("mouse_down", 0.3, x=100, y=200, button="Button.left")
    m.add("mouse_up", 0.35, x=100, y=200, button="Button.left")
    return m


def main():
    global PASS, FAIL
    m = sample_macro()
    check("duration", m.duration == 0.35)
    check("event count", len(m.events) == 5)

    # JSON round-trip
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    m.save(path)
    m2 = Macro.load(path)
    os.unlink(path)
    check("round-trip name", m2.name == "demo")
    check("round-trip events", m2.events == m.events)

    # editing
    keys_only = m.filter_type("key_down")
    check("filter_type", len(keys_only.events) == 1)
    trimmed = m.trim(0.15, 0.4)
    check("trim keeps range", len(trimmed.events) == 3)
    check("trim re-bases t=0", trimmed.events[0]["t"] == 0.05)
    no_moves = m.drop_mouse_moves()
    check("drop_mouse_moves", len(no_moves.events) == 4)
    fast = m.with_speed(2.0)
    check("speed scaling", fast.duration == 0.175)
    try:
        m.with_speed(0)
        check("rejects zero speed", False)
    except ValueError:
        check("rejects zero speed", True)
    try:
        m.add("bogus", 1.0)
        check("rejects bad event type", False)
    except ValueError:
        check("rejects bad event type", True)

    # dry-run playback
    player = DryRunPlayer()
    n = player.play(m, loops=3, speed=2.0)
    check("loop count", n == 15)
    check("loops tagged", player.played[5][0] == 1 and player.played[10][0] == 2)
    check("speed applied", player.played[0][1]["t"] == 0.0
          and player.played[4][1]["t"] == 0.175)
    try:
        player.play(m, loops=0)
        check("rejects zero loops", False)
    except ValueError:
        check("rejects zero loops", True)

    # CLI dry-run end to end
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    m.save(path)
    from cli import main as cli_main
    rc = cli_main(["play", path, "--loops", "2", "--dry-run"])
    check("cli dry-run exits 0", rc == 0)
    rc = cli_main(["info", path])
    check("cli info exits 0", rc == 0)
    rc = cli_main(["validate", path])
    check("cli validate exits 0", rc == 0)
    os.unlink(path)

    # --- v2.0 fixes & edge cases ---
    # speed math: 2x halves, 0.25x quadruples, empty macro is safe
    check("2x halves delays", m.with_speed(2.0).events[1]["t"] == 0.05)
    check("0.25x quadruples", m.with_speed(0.25).duration == 1.4)
    empty = Macro("empty")
    check("empty duration 0", empty.duration == 0.0)
    check("empty with_speed ok", empty.with_speed(2.0).events == [])
    check("empty dry-run 0", DryRunPlayer().play(empty, loops=3) == 0)
    for bad_speed in (0, -1.0):
        for fn in (lambda s=bad_speed: m.with_speed(s),
                   lambda s=bad_speed: DryRunPlayer().play(m, speed=s)):
            try:
                fn()
                check(f"rejects speed {bad_speed}", False)
            except ValueError:
                check(f"rejects speed {bad_speed}", True)
    try:
        DryRunPlayer().play(m, loops=-1)
        check("rejects negative loops", False)
    except ValueError:
        check("rejects negative loops", True)
    # dry-run per-call count (old bug: cumulative total on 2nd call)
    p2 = DryRunPlayer()
    check("dry-run 1st call count", p2.play(m, loops=1) == 5)
    check("dry-run 2nd call count", p2.play(m, loops=1) == 5)
    check("dry-run cumulative played", len(p2.played) == 10)
    # plan(): delays are true inter-event gaps, scaled by speed
    steps = DryRunPlayer().plan(m, loops=1, speed=2.0)
    check("plan delays", [s["delay"] for s in steps] == [0.0, 0.05, 0.05, 0.05, 0.025])
    check("plan total time", steps[-1]["t"] == 0.175)
    # strict schema: old web example used "key"/"type"/"wait" — must fail
    for bad in ({"name": "x", "events": [{"type": "key", "t": 0.0, "key": "a"}]},
                {"name": "x", "events": [{"type": "key_down", "key": "a"}]},
                {"name": "x", "events": [{"type": "key_down", "t": -1, "key": "a"}]},
                {"name": "x", "events": [{"type": "key_down", "t": 0.0}]},
                {"name": "x", "events": [{"type": "mouse_move", "t": 0.0, "x": 1}]},
                {"name": "x", "events": "nope"},
                {"name": "x", "events": [{"type": "key_down", "t": float("nan"), "key": "a"}]}):
        try:
            Macro.from_dict(bad)
            check(f"rejects bad schema {bad['events'] if isinstance(bad.get('events'), list) else bad['events']}", False)
        except ValueError:
            check("rejects bad schema", True)
    # editing guards + remap
    try:
        m.filter_type("bogus")
        check("filter rejects bad type", False)
    except ValueError:
        check("filter rejects bad type", True)
    try:
        m.trim(0.4, 0.15)
        check("trim rejects inverted range", False)
    except ValueError:
        check("trim rejects inverted range", True)
    remapped = m.remap_keys({"a": "b"})
    check("remap keys", remapped.events[0]["key"] == "b"
          and remapped.events[1]["key"] == "b"
          and remapped.events[2].get("key") is None)
    check("remap leaves original", m.events[0]["key"] == "a")
    # dry-run never touches pynput
    import sys as _sys
    check("dry-run imports no pynput", "pynput" not in _sys.modules)

    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

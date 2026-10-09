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
    os.unlink(path)

    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

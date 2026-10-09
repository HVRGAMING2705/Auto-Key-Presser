"""CLI: record / play / inspect macros."""
import argparse
import sys

from macro import Macro
from player import DryRunPlayer, LivePlayer
from recorder import Recorder


def cmd_record(args):
    rec = Recorder()
    macro = rec.start(args.name)
    macro.save(args.out)
    print(f"saved to {args.out}")


def cmd_play(args):
    macro = Macro.load(args.macro)
    if args.drop_moves:
        macro = macro.drop_mouse_moves()
    if args.dry_run:
        player = DryRunPlayer()
        n = player.play(macro, loops=args.loops, speed=args.speed)
        print(f"DRY RUN: would replay {n} events "
              f"({len(macro.events)} per loop x {args.loops}, {args.speed}x speed)")
        return
    player = LivePlayer()
    print(f"Playing {args.macro}: {len(macro.events)} events, "
          f"{args.loops} loop(s) at {args.speed}x. Esc stops.")
    player.play(macro, loops=args.loops, speed=args.speed)


def cmd_info(args):
    macro = Macro.load(args.macro)
    print(f"name:     {macro.name}")
    print(f"events:   {len(macro.events)}")
    print(f"duration: {macro.duration:.2f}s")
    kinds = {}
    for e in macro.events:
        kinds[e["type"]] = kinds.get(e["type"], 0) + 1
    for k in sorted(kinds):
        print(f"  {k:12s} {kinds[k]}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Macro Recorder — record and replay input macros.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="record a new macro (needs display)")
    r.add_argument("--name", default="recording")
    r.add_argument("--out", default="macro.json")
    r.set_defaults(fn=cmd_record)

    p = sub.add_parser("play", help="replay a macro file")
    p.add_argument("macro")
    p.add_argument("--loops", type=int, default=1)
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--drop-moves", action="store_true",
                   help="skip mouse_move events on replay")
    p.add_argument("--dry-run", action="store_true",
                   help="simulate replay without touching inputs")
    p.set_defaults(fn=cmd_play)

    i = sub.add_parser("info", help="summarize a macro file")
    i.add_argument("macro")
    i.set_defaults(fn=cmd_info)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

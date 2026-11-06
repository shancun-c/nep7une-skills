#!/usr/bin/env python3
"""Read-only structural/color check using the same policy as the repair tool."""
import argparse
import sys
from canvas_safety import CanvasError, parse_canvas, resolve_path, snapshot, validate


def verify(canvas_path):
    try:
        raw, _ = snapshot(canvas_path)
        errors = validate(parse_canvas(raw))
    except (CanvasError, OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("Canvas passes structural and color checks (not a layout or full-schema audit).")
    return not errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canvas_path", nargs="?")
    args = parser.parse_args()
    try:
        path = resolve_path(args.canvas_path)
    except CanvasError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0 if verify(path) else 1)

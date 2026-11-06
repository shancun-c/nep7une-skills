#!/usr/bin/env python3
"""Preview or repair canvas colors. Close Obsidian and pause sync before writing.

Only groups and explicitly supplied STALE_YELLOW_IDS are repaired. This tool
cannot infer node age or semantic role; review stale IDs before using them.
"""
import argparse
import copy
import os
import sys
from canvas_safety import CanvasError, parse_canvas, resolve_path, save_canvas, snapshot, validate


def fix_and_verify(canvas_path, dry_run=False):
    result = {"fixes": [], "errors": [], "stats": {}, "dry_run": dry_run, "saved": False}
    try:
        original, original_stat = snapshot(canvas_path)
        canvas = parse_canvas(original)
        result["errors"] = validate(canvas, colors=False)
        if result["errors"]:
            return result
        candidate = copy.deepcopy(canvas)
        texts = [n for n in candidate["nodes"] if n["type"] == "text"]
        groups = [n for n in candidate["nodes"] if n["type"] == "group"]
        for group in groups:
            if group.get("color") != "4":
                result["fixes"].append(f"Group {group['id']}: color -> 4")
                group["color"] = "4"
        stale_ids = {s.strip() for s in os.environ.get("STALE_YELLOW_IDS", "").split(",") if s.strip()}
        changed_ids = set()
        for node in texts:
            if node["id"] in stale_ids and node.get("color") == "3":
                node["color"] = "5"
                changed_ids.add(node["id"])
                result["fixes"].append(f"Node {node['id']}: 3 -> 5 (explicit stale ID)")
        for edge in candidate["edges"]:
            if edge.get("color") == "3" and edge["fromNode"] in changed_ids:
                edge["color"] = "5"
                result["fixes"].append(f"Edge {edge['id']}: 3 -> 5")
        result["errors"] = validate(candidate)
        result["stats"] = {"groups": len(groups), "text_nodes": len(texts), "edges": len(candidate["edges"])}
        if result["fixes"] and not result["errors"] and not dry_run:
            result["backup"] = save_canvas(candidate, canvas_path, original, original_stat)
            result["saved"] = True
    except (CanvasError, OSError, ValueError) as exc:
        result["errors"].append(str(exc))
    return result


def print_report(result):
    print("=== Canvas Color Report ===")
    label = "SAVED" if result["saved"] else "PREVIEW" if result["dry_run"] else "NOT SAVED"
    for fix in result["fixes"]:
        print(f"{label}: {fix}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    if result.get("backup"):
        print(f"Original-byte backup: {result['backup']}")
    if not result["errors"]:
        print("Candidate passes structural and color checks (not a layout or full-schema audit).")
    return 1 if result["errors"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("canvas_path", nargs="?")
    args = parser.parse_args()
    try:
        path = resolve_path(args.canvas_path)
    except CanvasError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return print_report(fix_and_verify(path, args.dry_run))


if __name__ == "__main__":
    sys.exit(main())

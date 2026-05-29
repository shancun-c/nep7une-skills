#!/usr/bin/env python3
"""Fix and verify Knowledge Canvas color conventions.

Usage:
    python3 fix-canvas-colors.py [--dry-run] [canvas_path]

Fixes:
    1. All group colors → "4" (green)
    2. Stale yellow nodes (>24h) → "5" (cyan)
    3. Stale yellow edges (from stale nodes) → "5" (cyan)

Verification:
    - Groups: all must be "4"
    - Text nodes: only "3", "5", "6" allowed
    - Edges: only "3", "5", or unset allowed
    - JSON validity + edge reference integrity

By default writes changes to the file. Use --dry-run to preview only.
"""
import json, sys, os
from datetime import datetime, timedelta

# --- Config ---
VAULT = os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    os.path.expanduser(
        "~/Library/CloudStorage/GoogleDrive-wenweikun@gmail.com/其他计算机/我的计算机/the_ai_obsidian"
    )
)
DEFAULT_CANVAS = f"{VAULT}/99 System/Knowledge Canvas.canvas"


def load_canvas(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def save_canvas(canvas: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(canvas, f, ensure_ascii=False, indent="\t")
    f = open(path, "a")
    f.write("\n")
    f.close()


def fix_and_verify(canvas_path: str, dry_run: bool = False) -> dict:
    canvas = load_canvas(canvas_path)
    fixes = []
    errors = []

    texts = [n for n in canvas["nodes"] if n["type"] == "text"]
    groups = [n for n in canvas["nodes"] if n["type"] == "group"]

    # --- Fix 1: Group colors must be "4" ---
    for g in groups:
        if g.get("color") != "4":
            fixes.append(f"Group '{g['label']}': '{g.get('color')}' → '4'")
            if not dry_run:
                g["color"] = "4"

    # --- Fix 2: Stale yellow nodes → "5" ---
    # Nodes with color "3" that are >24h old cannot be detected from canvas alone.
    # This relies on tracking which IDs were new yesterday (from canvas-state.md).
    # If you have stale yellow IDs, pass them via STALE_YELLOW_IDS env var (comma-separated).
    stale_ids_raw = os.environ.get("STALE_YELLOW_IDS", "")
    stale_ids = set(stale_ids_raw.split(",")) if stale_ids_raw else set()

    if stale_ids:
        for node in texts:
            if node["id"] in stale_ids and node.get("color") == "3":
                title = node["text"].split("\n")[0].replace("**", "")[:50]
                fixes.append(f"Node '{title}': '3' → '5' (stale)")
                if not dry_run:
                    node["color"] = "5"

        for edge in canvas["edges"]:
            if edge.get("color") == "3" and edge["fromNode"] in stale_ids:
                fixes.append(f"Edge {edge['id']}: '3' → '5' (stale)")
                if not dry_run:
                    edge["color"] = "5"

    # --- Verification ---
    # Groups
    for g in groups:
        if g.get("color") != "4":
            errors.append(f"Group '{g['label']}': color '{g.get('color')}', must be '4'")

    # Text nodes
    for t in texts:
        title = t["text"].split("\n")[0].replace("**", "")[:50]
        if t.get("color") not in {"3", "5", "6", None}:
            errors.append(f"Node '{title}': unexpected color '{t.get('color')}'")

    # Edges
    for e in canvas["edges"]:
        if e.get("color") not in {"3", "5", None}:
            errors.append(f"Edge {e['id']}: unexpected color '{e.get('color')}'")

    # Edge integrity
    node_ids = {n["id"] for n in canvas["nodes"]}
    for e in canvas["edges"]:
        if e["fromNode"] not in node_ids:
            errors.append(f"Edge {e['id']}: fromNode '{e['fromNode']}' not found")
        if e["toNode"] not in node_ids:
            errors.append(f"Edge {e['id']}: toNode '{e['toNode']}' not found")

    # --- Summary ---
    yellow = sum(1 for t in texts if t.get("color") == "3")
    cyan = sum(1 for t in texts if t.get("color") == "5")
    purple = sum(1 for t in texts if t.get("color") == "6")

    result = {
        "fixes": fixes,
        "errors": errors,
        "stats": {
            "groups": len(groups),
            "groups_green": sum(1 for g in groups if g.get("color") == "4"),
            "text_nodes": len(texts),
            "yellow": yellow,
            "cyan": cyan,
            "purple": purple,
            "edges": len(canvas["edges"]),
        },
        "dry_run": dry_run,
    }

    if fixes and not dry_run:
        save_canvas(canvas, canvas_path)
        result["saved"] = True

    return result


def print_report(result: dict) -> None:
    s = result["stats"]
    print("=== Canvas Color Report ===")
    if result["fixes"]:
        print(f"\nFixes applied ({'DRY RUN' if result['dry_run'] else 'SAVED'}):")
        for f in result["fixes"]:
            print(f"  ✓ {f}")
    else:
        print("\n✓ No fixes needed")

    print(f"\nGroups: {s['groups']} (all green: {s['groups_green'] == s['groups']})")
    print(f"Text nodes: {s['text_nodes']} — yellow={s['yellow']}, cyan={s['cyan']}, purple={s['purple']}")
    print(f"Edges: {s['edges']}")

    if result["errors"]:
        print(f"\n⚠ {len(result['errors'])} COLOR VIOLATIONS:")
        for e in result["errors"]:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("\n✅ All color conventions satisfied")
        print("✅ JSON valid, edge references intact")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    path = args[0] if args else DEFAULT_CANVAS

    if not os.path.exists(path):
        print(f"Canvas not found: {path}")
        print(f"Set OBSIDIAN_VAULT_PATH or pass path as argument.")
        sys.exit(1)

    result = fix_and_verify(path, dry_run=dry_run)
    print_report(result)

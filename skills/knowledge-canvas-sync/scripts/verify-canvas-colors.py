"""Verify Knowledge Canvas colors match skill conventions.
Run after any canvas write to catch color errors early.
"""
import json, sys

RULES = {
    "groups": "4",       # All groups must be green
    "principles": "6",   # Foundational principle nodes
    "established": "5",  # Established knowledge nodes
    "new_today": "3",    # New knowledge added today
}

def verify(canvas_path: str) -> bool:
    with open(canvas_path) as f:
        canvas = json.load(f)

    errors = []
    texts = [n for n in canvas["nodes"] if n["type"] == "text"]
    groups = [n for n in canvas["nodes"] if n["type"] == "group"]

    # 1. All groups must be color "4" (green)
    for g in groups:
        if g["color"] != "4":
            errors.append(f"Group '{g['label']}' has color '{g['color']}', must be '4'")

    # 2. Check node colors (non-exhaustive; flags suspicious combos)
    for t in texts:
        title = t["text"].split("\n")[0].replace("**", "")[:50]
        if t["color"] not in {"3", "5", "6"}:
            errors.append(f"Node '{title}' has unexpected color '{t['color']}'")

    if errors:
        print("COLOR ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
        return False
    else:
        print(f"✓ {len(groups)} groups all green")
        print(f"✓ {len(texts)} text nodes — colors: 3/5/6 only")
        return True

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "99 System/Knowledge Canvas.canvas"
    ok = verify(path)
    sys.exit(0 if ok else 1)

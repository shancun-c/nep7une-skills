# Canvas Layout Repair

When the canvas layout breaks (overlapping rows, wrong group sizes, nodes outside groups), use this programmatic approach. Do NOT attempt to fix layout with `patch` — it will fail with escape-drift on JSON canvas files.

## When to use

Signals of layout breakage:
- Groups in different rows overlap (e.g., Row 0 max height extends past Row 1 start Y)
- Text nodes fall outside their group's bounding box
- Group height doesn't match actual node count
- Nodes overlap each other

## Repair script pattern

Write a Python script to `/tmp/fix_canvas.py` and run it via `terminal`. The script template:

```python
#!/usr/bin/env python3
import json
from pathlib import Path

CANVAS_PATH = Path("<vault-path>") / "99 System/Knowledge Canvas.canvas"

# Layout constants (from knowledge-canvas-sync)
NODE_W = 360
NODE_H = 170
GROUP_PAD = 50
GAP_X = 50  # between nodes horizontally
GAP_Y = 40  # between nodes vertically
GROUP_GAP = 80  # between rows
GROUP_W = 970

# Color constants
COLOR_GREEN = "4"
COLOR_YELLOW = "3"
COLOR_CYAN = "5"
COLOR_PURPLE = "6"

def load_canvas():
    with open(CANVAS_PATH, encoding='utf-8') as f:
        return json.load(f)

def save_canvas(data):
    with open(CANVAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent='\t', ensure_ascii=False)

def assign_nodes_to_groups(nodes):
    """Assign text nodes to groups by bounding-box containment."""
    groups = {}
    for n in nodes:
        if n.get('type') == 'group':
            groups[n['id']] = {'node': n, 'text_nodes': [], 'label': n.get('label', '')}
        elif n.get('type') == 'text':
            text_nodes = n  # will be assigned below
    
    for tn in [n for n in nodes if n.get('type') == 'text']:
        tx, ty = tn['x'] + NODE_W/2, tn['y'] + NODE_H/2
        for gid, gdata in groups.items():
            g = gdata['node']
            if g['x'] <= tx <= g['x']+g['width'] and g['y'] <= ty <= g['y']+g['height']:
                gdata['text_nodes'].append(tn)
                break
    return groups

def group_height(num_nodes):
    """Calculate correct group height for node count."""
    if num_nodes == 0:
        return 200
    cols = 2
    rows = (num_nodes + cols - 1) // cols
    return rows * NODE_H + (rows - 1) * GAP_Y + 2 * GROUP_PAD

def reflow_groups(groups_data, group_order):
    """Reflow: row-based 3-col layout, dynamic heights, no overlaps."""
    COLS = 3
    current_y = -50
    col = 0
    row_heights = {}
    
    # First pass: calculate row heights
    row_idx = 0
    for label in group_order:
        gdata = groups_data.get(label)
        if not gdata:
            continue
        gh = max(group_height(len(gdata['text_nodes'])), 300)
        row_heights[row_idx] = max(row_heights.get(row_idx, 0), gh)
        col += 1
        if col >= COLS:
            col = 0
            row_idx += 1
    
    # Second pass: position
    col = 0
    current_row = 0
    y_pos = -50
    for label in group_order:
        gdata = groups_data.get(label)
        if not gdata:
            continue
        gh = max(group_height(len(gdata['text_nodes'])), 300)
        x_pos = -50 + col * (GROUP_W + GAP_X)
        
        g = gdata['node']
        g['x'], g['y'] = x_pos, y_pos
        g['width'], g['height'] = GROUP_W, gh
        g['color'] = COLOR_GREEN
        
        # 2-col grid within group
        for j, tn in enumerate(gdata['text_nodes']):
            tn['x'] = x_pos + GROUP_PAD + (j % 2) * (NODE_W + GAP_X)
            tn['y'] = y_pos + GROUP_PAD + (j // 2) * (NODE_H + GAP_Y)
            tn['width'], tn['height'] = NODE_W, NODE_H
        
        col += 1
        if col >= COLS:
            col = 0
            current_row += 1
            if current_row < len(row_heights):
                y_pos = y_pos + row_heights[current_row - 1] + GROUP_GAP

def verify_layout(nodes):
    """Check 0 overlaps across all text node pairs."""
    texts = [n for n in nodes if n.get('type') == 'text']
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            a, b = texts[i], texts[j]
            if a['id'] == b['id']:
                continue
            if (a['x'] < b['x']+b['width'] and a['x']+a['width'] > b['x'] and
                a['y'] < b['y']+b['height'] and a['y']+a['height'] > b['y']):
                return False
    return True
```

## Key invariants

1. **Group height must reflect actual node count.** 420 height for 1 node is wrong — `group_height(1)` = 270.
2. **Row position = previous row's end + GROUP_GAP.** Never hardcode Y. Calculate from max group height in the row above.
3. **All groups are green (4).** Period. No exceptions in this vault.
4. **Principle nodes (工程原则) are purple (6).** Apply after layout.
5. **Verify 0 overlaps after every write** — check all text node bounding-box pairs.

## Color repair (post-layout)

After fixing layout, run color repairs:

```python
# Fix principle-level nodes to purple
for gid, gdata in groups.items():
    if '工程原则' in gdata['label']:
        g = gdata['node']
        for tn in gdata['text_nodes']:
            if g['x'] <= tn['x']+tn['width']/2 <= g['x']+g['width']:
                tn['color'] = COLOR_PURPLE
```

For comprehensive color fixes (stale yellows, edge colors, group verification), prefer running the existing `scripts/fix-canvas-colors.py`.

## Pitfalls

- **Don't use `patch`.** The JSON canvas format triggers escape-drift 100% of the time. Python script → `terminal` is the only reliable path.
- **Don't hand-edit JSON.** Even minor whitespace changes can break Obsidian's canvas parser. Always go through `json.load` → modify → `json.dump`.
- **Don't forget to re-sort nodes.** Groups must come before text nodes in the `nodes` array. After layout: `canvas['nodes'] = group_nodes + text_nodes`.
- **Don't skip overlap verification.** A single missed overlap creates visual chaos in Obsidian.

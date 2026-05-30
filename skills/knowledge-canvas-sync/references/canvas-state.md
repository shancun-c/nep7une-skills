# Knowledge Canvas State (as of 2026-05-30)

## Layout

Two-row grid with new third row, all groups green ("4"):

```yaml
Row 1 (y=-50):
  [工程原则]      x=-50,  w=970, h=900  (7 nodes, 4 rows)
  [工具与执行]    x=970,  w=970, h=690  (5 nodes, 3 rows)
  [交互与自动化]  x=1990, w=970, h=480  (3 nodes, 2 rows)

Row 2 (y=930):
  [记忆与知识]    x=-50,  w=970, h=900  (7 nodes, 4 rows)
  [领域实践]      x=970,  w=970, h=480  (4 nodes, 2 rows)
  [AI产业与经济]  x=1990, w=970, h=300  (2 nodes) ← fixed height (was 690), row gap=80 ✓
```

## Color Scheme (STRICT)

| Color | Meaning | Applies To |
|-------|---------|-----------|
| "4" (green) | Group background | ALL groups, no exceptions |
| "6" (purple) | Foundational principles | 工程原则 group text nodes only |
| "5" (cyan) | Established knowledge | All other text nodes |
| "3" (yellow) | New today (24h only) | Nodes added today, revert to "5" tomorrow |

## Stats

- 6 groups, 28 text nodes, 45 edges
- All groups: color "4" (green) ✓
- 1 yellow node (new today): 09354575066f9622
- 20 cyan nodes (established) ✓
- 7 purple nodes (工程原则) ✓

## Today's New Nodes (revert to "5" on 2026-05-31)

- `09354575066f9622` — AI产业竞争正在从模型对决升级为企业操作系统之争 (AI产业与经济)

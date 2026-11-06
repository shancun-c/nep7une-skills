# Isolated examples

Run these examples from the repository root in **Bash**. They use new temporary
folders, no real runtime home, vault, SSH host, or network service. Keep the
printed paths for inspection; there is no automatic cleanup command here.
Linux is the tested environment. These examples do not certify native
Windows/macOS, real runtime discovery, or Obsidian integration.

## 1. Preview and install a disposable package

This deliberately bypasses external companion checks to demonstrate packaging
only. The resulting install is **not ready for runtime use** until its actual
required companions are installed and verified.

```bash
set -euo pipefail
DEMO="$(mktemp -d)"
SKILLS_ROOT="$DEMO/skills"
printf 'Disposable example: %s\n' "$DEMO"
bash installers/install-codex.sh --skills-dir "$SKILLS_ROOT" --skill obsidian-wiki-skill --skip-deps --dry-run
test ! -e "$SKILLS_ROOT"
bash installers/install-codex.sh --skills-dir "$SKILLS_ROOT" --skill obsidian-wiki-skill --skip-deps
INSTALLED="$SKILLS_ROOT/nep7une-skills/obsidian-wiki-skill"
test -f "$INSTALLED/SKILL.md"
test -f "$INSTALLED/.nep7une-install.json"
```

## 2. Repeat an update while preserving unrelated local data

Continue in the same Bash session after example 1. Use only this disposable
installation, not a personal runtime directory.

```bash
printf 'Synthetic local state\n' > "$INSTALLED/example-local-state.txt"
bash installers/install-codex.sh --skills-dir "$SKILLS_ROOT" --skill obsidian-wiki-skill --skip-deps --dry-run
bash installers/install-codex.sh --skills-dir "$SKILLS_ROOT" --skill obsidian-wiki-skill --skip-deps
grep -Fx 'Synthetic local state' "$INSTALLED/example-local-state.txt"
test -f "$INSTALLED/.nep7une-install.json"
```

This tests preservation of an unrelated file, not migration of every possible
runtime state. See [maintenance](maintenance.md) before updating a real install.

## 3. Preview and verify a Canvas repair on synthetic data

This creates an invalid group color on purpose. The first verifier must fail;
preview must leave the original bytes unchanged. Repair then creates a backup
and writes the valid candidate. The helper cannot infer knowledge age or role.

```bash
set -euo pipefail
CANVAS_DEMO="$(mktemp -d)"
CANVAS="$CANVAS_DEMO/example.canvas"
printf '%s\n' '{"nodes":[{"id":"g1","type":"group","x":0,"y":0,"width":400,"height":200,"label":"Example","color":"3"}],"edges":[]}' > "$CANVAS"
cp "$CANVAS" "$CANVAS_DEMO/before.canvas"
if python3 skills/knowledge-canvas-sync/scripts/verify-canvas-colors.py "$CANVAS"; then
  echo 'Expected the intentionally invalid example to fail' >&2
  exit 1
fi
python3 skills/knowledge-canvas-sync/scripts/fix-canvas-colors.py --dry-run "$CANVAS"
cmp "$CANVAS" "$CANVAS_DEMO/before.canvas"
python3 skills/knowledge-canvas-sync/scripts/fix-canvas-colors.py "$CANVAS"
python3 skills/knowledge-canvas-sync/scripts/verify-canvas-colors.py "$CANVAS"
python3 - "$CANVAS" <<'PYTHON'
import json
import pathlib
import sys
p = pathlib.Path(sys.argv[1])
assert json.loads(p.read_text(encoding="utf-8"))["nodes"][0]["color"] == "4"
backups = list(p.parent.glob(p.name + ".backup-*"))
assert len(backups) == 1
assert backups[0].read_bytes() == (p.parent / "before.canvas").read_bytes()
print("Preview preserved bytes; repair and original-byte backup verified.")
PYTHON
```

Color `4` is the helper's required group color. Passing this check verifies its
structural/color policy, not visual layout or the entire JSON Canvas schema.

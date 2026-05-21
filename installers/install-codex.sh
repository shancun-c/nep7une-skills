#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/lib.sh"

SKILL_NAME="obsidian-wiki-skill"
COLLECTION_NAME="nep7une-skills"
TARGET_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
TARGET_PATH=""
DRY_RUN=0
CHECK_DEPS=1

usage() {
  cat <<'USAGE'
Usage: installers/install-codex.sh [options]

Options:
  --skill NAME       Skill slug to install. Default: obsidian-wiki-skill
  --collection NAME  Collection namespace. Default: nep7une-skills
  --skills-dir DIR   Codex skills directory. Default: ${CODEX_HOME:-$HOME/.codex}/skills
  --target DIR       Full target skill directory. Overrides --skills-dir.
  --check-deps       Check required/recommended/optional dependencies before install. Default.
  --skip-deps        Skip dependency checks.
  --dry-run          Print and validate without writing files.
  -h, --help         Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      SKILL_NAME="${2:?Missing value for --skill}"
      shift 2
      ;;
    --collection)
      COLLECTION_NAME="${2:?Missing value for --collection}"
      shift 2
      ;;
    --skills-dir)
      TARGET_ROOT="${2:?Missing value for --skills-dir}"
      shift 2
      ;;
    --target)
      TARGET_PATH="${2:?Missing value for --target}"
      shift 2
      ;;
    --check-deps)
      CHECK_DEPS=1
      shift
      ;;
    --skip-deps)
      CHECK_DEPS=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

SOURCE="$REPO_ROOT/skills/$SKILL_NAME"
if [[ -z "$TARGET_PATH" ]]; then
  TARGET_PATH="$TARGET_ROOT/$COLLECTION_NAME/$SKILL_NAME"
fi

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "Skill not found: $SOURCE/SKILL.md" >&2
  exit 1
fi

echo "Runtime: Codex"
echo "Collection: $COLLECTION_NAME"
echo "Skill:   $SKILL_NAME"
echo "Source:  $SOURCE"
echo "Target:  $TARGET_PATH"

if [[ "$CHECK_DEPS" -eq 1 ]]; then
  check_skill_dependencies codex "$TARGET_ROOT" "$SKILL_NAME"
else
  echo "Dependency check: skipped"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: no files written."
  rsync -an --delete --exclude '.DS_Store' "$SOURCE"/ "$TARGET_PATH"/
  exit 0
fi

mkdir -p "$TARGET_PATH"
rsync -a --delete --exclude '.DS_Store' "$SOURCE"/ "$TARGET_PATH"/
echo "Installed $SKILL_NAME to $TARGET_PATH"

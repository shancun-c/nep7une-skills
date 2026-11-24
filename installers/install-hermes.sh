#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/lib.sh"

SKILL_NAME="obsidian-wiki-skill"
COLLECTION_NAME="nep7une-skills"
TARGET_ROOT="${HERMES_HOME:-$HOME/.hermes}/skills"
TARGET_PATH=""
DRY_RUN=0
CHECK_DEPS=1

usage() {
  cat <<'USAGE'
Usage: installers/install-hermes.sh [options]

Options:
  --skill NAME       Skill slug to install. Default: obsidian-wiki-skill
  --collection NAME  Collection namespace. Default: nep7une-skills
  --skills-dir DIR   Hermes skills root. Default: ${HERMES_HOME:-$HOME/.hermes}/skills
  --target DIR       Full target skill directory. Overrides --collection and --skills-dir.
  --check-deps       Check required/recommended/optional dependencies before install. Default.
  --skip-deps        Skip dependency checks.
  --dry-run          Print and validate without writing files.
  -h, --help         Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      require_installer_value "$1" "${2-}"
      SKILL_NAME="$2"
      shift 2
      ;;
    --collection)
      require_installer_value "$1" "${2-}"
      COLLECTION_NAME="$2"
      shift 2
      ;;
    --skills-dir)
      require_installer_value "$1" "${2-}"
      TARGET_ROOT="$2"
      shift 2
      ;;
    --target)
      require_installer_value "$1" "${2-}"
      TARGET_PATH="$2"
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

echo "Runtime: Hermes"
echo "Collection: $COLLECTION_NAME"
echo "Skill:   $SKILL_NAME"
echo "Source:  $SOURCE"
echo "Target:  $TARGET_PATH"

if [[ "$CHECK_DEPS" -eq 1 ]]; then
  check_skill_dependencies hermes "$TARGET_ROOT" "$SKILL_NAME"
else
  echo "Dependency check: skipped"
fi

# Python 3 provides path checks, ownership tracking and a recoverable update.
command -v python3 >/dev/null || { echo "Python 3 is required." >&2; exit 1; }
INSTALL_ARGS=(--repo "$REPO_ROOT" --source "$SOURCE" --target "$TARGET_PATH"
  --root "$TARGET_ROOT" --skill "$SKILL_NAME" --collection "$COLLECTION_NAME")
if [[ "$DRY_RUN" -eq 1 ]]; then
  INSTALL_ARGS+=(--dry-run)
fi
python3 "$SCRIPT_DIR/safe-install.py" "${INSTALL_ARGS[@]}"

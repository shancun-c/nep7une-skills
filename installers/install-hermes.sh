#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILL_NAME="obsidian-wiki-skill"
CATEGORY="research"
TARGET_ROOT="${HERMES_HOME:-$HOME/.hermes}/skills"
TARGET_PATH=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage: installers/install-hermes.sh [options]

Options:
  --skill NAME       Skill slug to install. Default: obsidian-wiki-skill
  --category NAME    Hermes category directory. Default: research
  --skills-dir DIR   Hermes skills root. Default: ${HERMES_HOME:-$HOME/.hermes}/skills
  --target DIR       Full target skill directory. Overrides --category and --skills-dir.
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
    --category)
      CATEGORY="${2:?Missing value for --category}"
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
  TARGET_PATH="$TARGET_ROOT/$CATEGORY/$SKILL_NAME"
fi

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "Skill not found: $SOURCE/SKILL.md" >&2
  exit 1
fi

echo "Runtime: Hermes"
echo "Skill:   $SKILL_NAME"
echo "Source:  $SOURCE"
echo "Target:  $TARGET_PATH"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: no files written."
  rsync -an --delete --exclude '.DS_Store' "$SOURCE"/ "$TARGET_PATH"/
  exit 0
fi

mkdir -p "$TARGET_PATH"
rsync -a --delete --exclude '.DS_Store' "$SOURCE"/ "$TARGET_PATH"/
echo "Installed $SKILL_NAME to $TARGET_PATH"

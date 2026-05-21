#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/lib.sh"

SKILL_NAME="obsidian-wiki-skill"
COLLECTION_NAME="nep7une-skills"
WORKSPACE=""
SKILLS_DIR=""
DRY_RUN=0
CHECK_DEPS=1

usage() {
  cat <<'USAGE'
Usage: installers/install-openclaw.sh --target WORKSPACE [options]
       installers/install-openclaw.sh --skills-dir DIR [options]

Options:
  --skill NAME       Skill slug to install. Default: obsidian-wiki-skill
  --collection NAME  Collection namespace. Default: nep7une-skills
  --target DIR       OpenClaw workspace directory. Installs into DIR/skills/COLLECTION/NAME.
  --skills-dir DIR   Exact skills root. Installs into DIR/COLLECTION/NAME.
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
    --target)
      WORKSPACE="${2:?Missing value for --target}"
      shift 2
      ;;
    --skills-dir)
      SKILLS_DIR="${2:?Missing value for --skills-dir}"
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

if [[ -n "$WORKSPACE" && -n "$SKILLS_DIR" ]]; then
  echo "Use either --target or --skills-dir, not both." >&2
  exit 2
fi

if [[ -z "$WORKSPACE" && -z "$SKILLS_DIR" ]]; then
  echo "OpenClaw install requires --target WORKSPACE or --skills-dir DIR." >&2
  usage >&2
  exit 2
fi

SOURCE="$REPO_ROOT/skills/$SKILL_NAME"
if [[ -n "$WORKSPACE" ]]; then
  TARGET_ROOT="$WORKSPACE/skills"
  TARGET_PATH="$WORKSPACE/skills/$COLLECTION_NAME/$SKILL_NAME"
else
  TARGET_ROOT="$SKILLS_DIR"
  TARGET_PATH="$SKILLS_DIR/$COLLECTION_NAME/$SKILL_NAME"
fi

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "Skill not found: $SOURCE/SKILL.md" >&2
  exit 1
fi

echo "Runtime: OpenClaw"
echo "Collection: $COLLECTION_NAME"
echo "Skill:   $SKILL_NAME"
echo "Source:  $SOURCE"
echo "Target:  $TARGET_PATH"

if [[ "$CHECK_DEPS" -eq 1 ]]; then
  check_skill_dependencies openclaw "$TARGET_ROOT" "$SKILL_NAME"
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

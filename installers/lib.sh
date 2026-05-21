#!/usr/bin/env bash

skill_dependencies() {
  local runtime="$1"
  local skill_name="$2"
  local level="$3"

  case "$runtime:$skill_name:$level" in
    codex:obsidian-wiki-skill:required)
      printf '%s\n' obsidian-markdown obsidian-cli obsidian-bases json-canvas
      ;;
    codex:obsidian-wiki-skill:recommended)
      printf '%s\n' defuddle
      ;;
    codex:obsidian-wiki-skill:optional)
      printf '%s\n' anysearch
      ;;
    hermes:obsidian-wiki-skill:required)
      printf '%s\n' obsidian
      ;;
    hermes:obsidian-wiki-skill:recommended)
      printf '%s\n' obsidian-markdown obsidian-cli obsidian-bases json-canvas defuddle
      ;;
    hermes:obsidian-wiki-skill:optional)
      printf '%s\n' anysearch
      ;;
    openclaw:obsidian-wiki-skill:required)
      printf '%s\n' obsidian
      ;;
    openclaw:obsidian-wiki-skill:recommended)
      printf '%s\n' defuddle
      ;;
    openclaw:obsidian-wiki-skill:optional)
      printf '%s\n' obsidian-markdown obsidian-cli obsidian-bases json-canvas anysearch
      ;;
  esac
}

skill_installed() {
  local skills_root="$1"
  local dependency_name="$2"
  local skill_file
  local skill_dir
  local dir_name
  local metadata_name

  if [[ ! -d "$skills_root" ]]; then
    return 1
  fi

  while IFS= read -r skill_file; do
    skill_dir="$(dirname "$skill_file")"
    dir_name="$(basename "$skill_dir")"

    if [[ "$dir_name" == "$dependency_name" ]]; then
      return 0
    fi

    metadata_name="$(awk '
      NR == 1 && $0 == "---" { in_frontmatter = 1; next }
      in_frontmatter && $0 == "---" { exit }
      in_frontmatter && $1 == "name:" {
        sub(/^name:[[:space:]]*/, "")
        print
        exit
      }
    ' "$skill_file")"

    if [[ "$metadata_name" == "$dependency_name" ]]; then
      return 0
    fi
  done < <(find "$skills_root" -maxdepth 8 -type f -name SKILL.md 2>/dev/null)

  return 1
}

check_skill_dependencies() {
  local runtime="$1"
  local skills_root="$2"
  local skill_name="$3"
  local missing_required=0
  local dependency

  echo "Dependency check: $runtime skills root $skills_root"

  for dependency in $(skill_dependencies "$runtime" "$skill_name" required); do
    if skill_installed "$skills_root" "$dependency"; then
      echo "  required ok: $dependency"
    else
      echo "  required missing: $dependency" >&2
      missing_required=1
    fi
  done

  for dependency in $(skill_dependencies "$runtime" "$skill_name" recommended); do
    if skill_installed "$skills_root" "$dependency"; then
      echo "  recommended ok: $dependency"
    else
      echo "  recommended missing: $dependency" >&2
    fi
  done

  for dependency in $(skill_dependencies "$runtime" "$skill_name" optional); do
    if skill_installed "$skills_root" "$dependency"; then
      echo "  optional ok: $dependency"
    else
      echo "  optional missing: $dependency" >&2
    fi
  done

  if [[ "$missing_required" -ne 0 ]]; then
    echo "Missing required skill dependencies. Install them first or rerun with --skip-deps." >&2
    return 1
  fi
}

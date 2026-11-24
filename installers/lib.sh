#!/usr/bin/env bash

require_installer_value() {
  local option="$1" value="$2"
  # An option token must not be consumed as a value, especially --dry-run.
  # Dash-prefixed relative paths can be supplied as ./-name.
  if [[ -z "$value" || "$value" == -* ]]; then
    printf 'Missing value for %s (use ./ for paths starting with a dash).\n' "$option" >&2
    exit 2
  fi
}

skill_dependencies() {
  local runtime="$1"
  local skill_name="$2"
  local level="$3"

  case "$runtime:$skill_name:$level" in
    codex:knowledge-canvas-sync:required)
      printf '%s\n' obsidian-canvas-creator obsidian-markdown
      ;;
    hermes:knowledge-canvas-sync:required)
      printf '%s\n' obsidian-canvas-creator obsidian
      ;;
    openclaw:knowledge-canvas-sync:required)
      printf '%s\n' obsidian-canvas-creator
      ;;
    codex:knowledge-canvas-sync:recommended)
      printf '%s\n' obsidian-wiki-skill
      ;;
    hermes:knowledge-canvas-sync:recommended)
      printf '%s\n' obsidian-markdown obsidian-wiki-skill
      ;;
    openclaw:knowledge-canvas-sync:recommended)
      printf '%s\n' obsidian-markdown obsidian
      ;;
    *:knowledge-canvas-sync:optional)
      printf '%s\n' defuddle anysearch
      ;;
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

    # Read only a simple top-level name scalar from closed frontmatter.
    metadata_name="$(awk -v sq="'" '
      BEGIN { dq = sprintf("%c", 34) }
      { sub(/\r$/, "") } # Normalize CRLF before checking frontmatter delimiters.
      NR == 1 { in_frontmatter = ($0 == "---"); next }
      !in_frontmatter { exit }
      $0 == "---" { closed = 1; exit }
      /^[[:space:]]*($|#)/ { next }
      { if (after_name && $0 ~ /^[[:space:]]/) candidate = ""; after_name = 0 }
      $0 ~ "^(" dq "name" dq "|" sq "name" sq ")[[:space:]]*:" { names++; next }
      /^name[[:space:]]*:/ {
        names++
        after_name = 1
        if ($0 !~ /^name[[:space:]]*:[[:space:]]+/) next
        sub(/^name[[:space:]]*:[[:space:]]*/, "")
        sub(/[[:space:]]*$/, "")
        quote = substr($0, 1, 1)
        if (length($0) >= 2 && (quote == sq || quote == dq) &&
            substr($0, length($0), 1) == quote) {
          $0 = substr($0, 2, length($0) - 2)
        }
        if ($0 ~ /^[a-z0-9]+(-[a-z0-9]+)*$/) candidate = $0
      }
      END { if (closed && names == 1 && candidate != "") print candidate }
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

"""Offline package identity checks, not runtime discovery certification."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def identity_errors(registry, source_names):
    """Inspect the repository's constrained registry/frontmatter format only."""
    slugs = []
    entries = []
    for line in registry.splitlines():
        if line.startswith("  - "):
            entry = re.fullmatch(r"  - slug: ([a-z0-9-]+)", line)
            entries.append((entry[1] if entry else None, []))
        elif entries and line.startswith("    path: "):
            entries[-1][1].append(line[len("    path: "):])
    errors = []
    for slug, paths in entries:
        if slug is None:
            errors.append("unrecognized registry entry")
            continue
        slugs.append(slug)
        if len(paths) != 1:
            errors.append("entry must have exactly one path: " + slug)
        elif paths[0] != "skills/" + slug:
            errors.append("source path differs from slug: " + slug)
        if source_names.get(slug) != [slug]:
            errors.append("frontmatter name differs from slug: " + slug)
    if not slugs or len(slugs) != len(set(slugs)):
        errors.append("missing or duplicate slug")
    if set(slugs) != set(source_names):
        errors.append("registry and source inventory differ")
    return errors


def source_names():
    result = {}
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            result[path.parent.name] = []
            continue
        frontmatter = "\n".join(lines[1:lines.index("---", 1)])
        result[path.parent.name] = re.findall(r"^name: ([a-z0-9-]+)$", frontmatter, re.M)
    return result


class PackageIdentityTests(unittest.TestCase):
    def setUp(self):
        self.registry = (ROOT / "registry.yaml").read_text(encoding="utf-8")
        self.names = source_names()

    def test_registry_paths_and_frontmatter_names_agree(self):
        self.assertEqual(identity_errors(self.registry, self.names), [])

    def test_renamed_frontmatter_is_detected(self):
        self.names["obsidian-wiki-skill"] = ["renamed-wiki"]
        self.assertIn("frontmatter name differs from slug: obsidian-wiki-skill",
                      identity_errors(self.registry, self.names))

    def test_wrong_registry_path_is_detected(self):
        registry = self.registry.replace("path: skills/obsidian-wiki-skill",
                                         "path: skills/knowledge-canvas-sync")
        self.assertIn("source path differs from slug: obsidian-wiki-skill",
                      identity_errors(registry, self.names))

    def test_balanced_wrong_path_counts_cannot_shift_into_next_entry(self):
        registry = self.registry.replace(
            "    path: skills/knowledge-canvas-sync\n",
            "",
        ).replace(
            "    path: skills/obsidian-wiki-skill\n",
            "    path: skills/obsidian-wiki-skill\n"
            "    path: skills/knowledge-canvas-sync\n",
        )
        errors = identity_errors(registry, self.names)
        self.assertIn("entry must have exactly one path: obsidian-wiki-skill", errors)
        self.assertIn("entry must have exactly one path: knowledge-canvas-sync", errors)

    def test_unregistered_package_is_detected(self):
        self.names["new-skill"] = ["new-skill"]
        self.assertIn("registry and source inventory differ",
                      identity_errors(self.registry, self.names))

    def test_duplicate_slug_and_name_are_detected(self):
        registry = self.registry + "\n  - slug: obsidian-wiki-skill\n"
        self.assertIn("missing or duplicate slug", identity_errors(registry, self.names))
        self.names["obsidian-wiki-skill"] *= 2
        self.assertIn("frontmatter name differs from slug: obsidian-wiki-skill",
                      identity_errors(self.registry, self.names))


if __name__ == "__main__":
    unittest.main()

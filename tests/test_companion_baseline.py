"""Offline documentation contracts, not live CLI or installed-skill certification."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "skills/obsidian-wiki-skill/references"


class CompanionBaselineTests(unittest.TestCase):
    def test_baseline_is_explicit_and_complete(self):
        data = json.loads((REF / "kepano-baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["repository"], "https://github.com/kepano/obsidian-skills")
        self.assertRegex(data["reviewed_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(data["license"]["spdx"], "MIT")
        names = [entry["name"] for entry in data["skills"]]
        self.assertEqual(set(names), {
            "obsidian-markdown", "obsidian-cli", "obsidian-bases", "json-canvas", "defuddle"})
        self.assertEqual(len(names), len(set(names)))
        for entry in data["skills"]:
            self.assertEqual(entry["path"], f'skills/{entry["name"]}/SKILL.md')
            self.assertRegex(entry["blob_sha"], r"^[0-9a-f]{40}$")
        self.assertRegex(data["license"]["blob_sha"], r"^[0-9a-f]{40}$")

    def test_preflight_is_reachable_and_links_exist(self):
        skill = REF.parent / "SKILL.md"
        self.assertIn("references/companion-preflight.md", skill.read_text(encoding="utf-8"))
        self.assertIn("companion-preflight.md", (REF / "companion-skill-routing.md").read_text(encoding="utf-8"))
        for path in (REF / "companion-preflight.md", REF / "companion-skill-routing.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if not target.startswith(("https:", "http:", "#")):
                    self.assertTrue((path.parent / target.split("#")[0]).is_file(), target)

    def test_file_level_cli_requires_explicit_unambiguous_path(self):
        text = (REF / "companion-preflight.md").read_text(encoding="utf-8")
        for boundary in (
            "path=<vault-relative-path>", "confirm the resolved file",
            "Never omit the file selector", "the active file",
            "ambiguous `file=<name>`", "stop that operation",
        ):
            self.assertIn(boundary, text)

    def test_preflight_does_not_claim_runtime_enforcement(self):
        text = (REF / "companion-preflight.md").read_text(encoding="utf-8")
        for boundary in (
            "not provenance", "every command", "most recently focused vault",
            "symlink escapes", "does not replace", "temporary synthetic vaults",
            "not proof of real-app compatibility",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()

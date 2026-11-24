"""Offline documentation contracts, not live CLI or installed-skill certification."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "skills/obsidian-wiki-skill/references"


class CompanionBaselineTests(unittest.TestCase):
    def assert_baseline_contract(self, data):
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["repository"], "https://github.com/obsidianmd/obsidian-skills")
        self.assertEqual(data["reviewed_tag"], "1.2.1")
        self.assertEqual(data["reviewed_commit"], "b110b2f8e9eb1f287892f937050dfd40af862cbb")
        self.assertEqual(data["reviewed_on"], "2026-11-24")
        self.assertEqual(data["license"]["spdx"], "MIT")
        self.assertEqual(data["license"]["path"], "LICENSE")
        self.assertEqual(data["license"]["blob_sha"], "33d692ee84f4464f575f2d1e927f19cf1c8ccc57")
        expected = {
            "obsidian-markdown": "13e3041536ac2b2e27509d7f4aff357995f0d090",
            "obsidian-cli": "a72787f713b0a9051c8597d11fa91c7981db811f",
            "obsidian-bases": "a6a84a5fd3387c9820985e056a2555d2277ce34b",
            "json-canvas": "7a60b5dd74415cc4a2a7c27a06760ea90e91caaf",
            "defuddle": "81f6ee03344ae517c45055b9c789eae530d47c43",
        }
        self.assertEqual(len(data["skills"]), len(expected))
        self.assertEqual({entry["name"] for entry in data["skills"]}, set(expected))
        for entry in data["skills"]:
            self.assertEqual(entry["path"], f'plugins/obsidian/skills/{entry["name"]}/SKILL.md')
            self.assertEqual(entry["blob_sha"], expected[entry["name"]])
        self.assertEqual(data["reviewed_references"], [{
            "path": "plugins/obsidian/skills/obsidian-markdown/references/PROPERTIES.md",
            "blob_sha": "244534b8b1d9258c266f80c58727cf24e502aaa3",
        }])
        self.assertEqual(len(data["history"]), 1)
        historical = data["history"][0]
        self.assertEqual(historical["repository"], "https://github.com/kepano/obsidian-skills")
        self.assertEqual(historical["reviewed_commit"], "3ccff5338ea700537839b21900aa5358a0402c98")
        self.assertEqual(historical["reviewed_on"], "2026-11-06")
        self.assertEqual(historical["license"], data["license"])
        self.assertEqual(data["scope"], historical["scope"])
        self.assertIn("not an installer lock or certification", data["scope"])

    def test_baseline_is_explicit_and_complete(self):
        data = json.loads((REF / "kepano-baseline.json").read_text(encoding="utf-8"))
        self.assert_baseline_contract(data)

    def test_contract_rejects_mixed_revision_path_blob_and_scope(self):
        data = json.loads((REF / "kepano-baseline.json").read_text(encoding="utf-8"))
        mutations = (
            lambda d: d.update(reviewed_commit=d["history"][0]["reviewed_commit"]),
            lambda d: d.update(reviewed_tag="1.2.0"),
            lambda d: d["skills"][0].update(path="skills/obsidian-markdown/SKILL.md"),
            lambda d: d["skills"][0].update(blob_sha=d["skills"][1]["blob_sha"]),
            lambda d: d["skills"].append(dict(d["skills"][0])),
            lambda d: d["skills"].pop(),
            lambda d: d["reviewed_references"][0].update(blob_sha="0" * 40),
            lambda d: d["license"].update(blob_sha="0" * 40),
            lambda d: d["history"][0].update(reviewed_on="2026-11-24"),
            lambda d: d.update(scope="Runtime compatibility certified"),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = copy.deepcopy(data)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    self.assert_baseline_contract(changed)

    def test_current_source_text_matches_review_record(self):
        for path in (ROOT / "README.md", REF / "companion-preflight.md",
                     REF / "companion-skill-routing.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("obsidianmd/obsidian-skills", text)
            self.assertIn("1.2.1", text)
            self.assertIn("kepano-baseline.json", text)

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

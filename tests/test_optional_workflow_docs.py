"""Structural documentation contracts, not external-tool integration tests."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "skills" / "obsidian-wiki-skill"


class OptionalWorkflowDocsTests(unittest.TestCase):
    def test_upstream_snapshot_is_dated_and_pinned(self):
        data = json.loads((ROOT / "docs/upstream-projects.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "research_baseline_not_runtime_lock")
        self.assertRegex(data["checked_at"], r"^\d{4}-\d{2}-\d{2}$")
        projects = data["projects"]
        self.assertEqual(len(projects), len({p["repository"] for p in projects}))
        for project in projects:
            with self.subTest(project=project["repository"]):
                self.assertRegex(project["reviewed_head"], r"^[0-9a-f]{40}$")
                self.assertRegex(project["license_blob_sha"], r"^[0-9a-f]{40}$")
                self.assertGreater(project["stars"], 0)
                self.assertFalse(project["archived"])
                prefix = "https://github.com/" + project["repository"] + "/blob/" + project["reviewed_head"] + "/"
                self.assertTrue(project["license_url"].startswith(prefix))
                self.assertTrue(project["readme_url"].startswith(prefix))

    def test_license_split_is_not_lost(self):
        data = json.loads((ROOT / "docs/upstream-projects.json").read_text(encoding="utf-8"))
        projects = {p["repository"]: p for p in data["projects"]}
        self.assertEqual(projects["lycheeverse/lychee"]["license"], "MIT OR Apache-2.0")
        self.assertIn("CC-BY-4.0", projects["agentskills/agentskills"]["license"])
        roadmap = (ROOT / "docs/open-source-roadmap.md").read_text(encoding="utf-8")
        self.assertIn("model licenses are separate", roadmap)
        self.assertIn("demonstration-only", roadmap)

    def test_new_local_links_resolve(self):
        files = [ROOT / "docs/open-source-roadmap.md", WIKI / "references/local-document-ingest.md",
                 WIKI / "references/publication-secret-scan.md"]
        for path in files:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(file=str(path), target=target):
                    self.assertTrue((path.parent / target.split("#", 1)[0]).is_file())

    def test_workflows_are_routed_but_not_required_dependencies(self):
        skill = (WIKI / "SKILL.md").read_text(encoding="utf-8")
        git_policy = (WIKI / "references/git-sync-pitfalls.md").read_text(encoding="utf-8")
        self.assertIn("references/local-document-ingest.md", skill)
        self.assertIn("](publication-secret-scan.md)", git_policy)
        registry = (ROOT / "registry.yaml").read_text(encoding="utf-8").lower()
        for optional_tool in ("markitdown", "docling", "gitleaks", "lychee", "trivy", "skills-ref"):
            self.assertNotIn(optional_tool, registry)

    def test_conversion_boundary_remains_explicit(self):
        text = (WIKI / "references/local-document-ingest.md").read_text(encoding="utf-8")
        for required in ("not an implemented adapter", "No real-vault access", "convert_stream()",
                         "enable_plugins=False", "not a network sandbox", "QMD", "synthetic",
                         "Documentation tests are not these tests"):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_secret_scan_is_not_publication_or_safety_proof(self):
        text = (WIKI / "references/publication-secret-scan.md").read_text(encoding="utf-8")
        for required in ("grant permission to publish", "--redact=100", "not verified",
                         "findings and errors", "private", "false positive", "manual staged diff",
                         "No Gitleaks integration run", "pause before step 6"):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()

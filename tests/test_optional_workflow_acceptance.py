"""Synthetic contract tests only: no MarkItDown or Gitleaks is executed."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "optional_acceptance", ROOT / "tools/optional_workflow_acceptance.py")
ACCEPTANCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACCEPTANCE)


def markdown():
    return ("\n\n".join(ACCEPTANCE.REQUIRED_TEXT) + "\n\n"
            "| Year | Revenue | Unit |\n| --- | --- | --- |\n"
            "| 2025 | 12.50 | USD million |\n| 2026 | 13.75 | USD million |\n").encode("utf-8")


def finding():
    return {"RuleID": ACCEPTANCE.RULE_ID, "File": "canary.txt",
            "StartLine": 2, "EndLine": 2, "Secret": "REDACTED", "Match": "REDACTED"}


def check(value, returncode=10, case="canary", **kwargs):
    return ACCEPTANCE.check_gitleaks(json.dumps(value).encode("utf-8"),
                                    returncode=returncode, case=case, **kwargs)


class OptionalWorkflowAcceptanceTests(unittest.TestCase):
    def assert_pass(self, result):
        self.assertEqual(result["status"], "synthetic_contract_passed")
        self.assertEqual(result["tool_execution"], "not_verified")
        self.assertEqual(result["network_isolation"], "not_verified")
        self.assertEqual(result["real_data_readiness"], "not_verified")

    def assert_unverified(self, result):
        self.assertEqual(result["status"], "not_verified")

    def test_markdown_preserves_text_and_table(self):
        self.assert_pass(ACCEPTANCE.check_markdown(markdown()))

    def test_missing_unicode_source_text(self):
        self.assert_unverified(ACCEPTANCE.check_markdown(markdown().replace(
            ACCEPTANCE.REQUIRED_TEXT[1].encode("utf-8"), b"")))

    def test_table_row_value_swap_requires_review(self):
        content = markdown().replace(b"2025 | 12.50", b"2025 | 13.75").replace(
            b"2026 | 13.75", b"2026 | 12.50")
        self.assert_unverified(ACCEPTANCE.check_markdown(content))

    def test_missing_units_and_flattened_table_require_review(self):
        for content in (markdown().replace(b"USD million", b"USD"),
                        markdown().replace(b"|", b" ")):
            self.assert_unverified(ACCEPTANCE.check_markdown(content))

    def test_duplicate_or_extended_tables_require_review(self):
        for content in (markdown() + markdown(), markdown() + b"| 2027 | 42 | USD million |\n",
                        markdown() + b"\n| Year | Revenue | Unit |\n"):
            self.assert_unverified(ACCEPTANCE.check_markdown(content))

    def test_payload_encoding_and_size_limits(self):
        for content in (b"\xff", b"\x00", b"x" * (ACCEPTANCE.MAX_BYTES + 1), "not bytes"):
            self.assert_unverified(ACCEPTANCE.check_markdown(content))
            self.assert_unverified(ACCEPTANCE.check_gitleaks(content, returncode=0, case="clean"))

    def test_clean_report_contract(self):
        self.assert_pass(check([], returncode=0, case="clean"))

    def test_redacted_canary_contract(self):
        self.assert_pass(check([finding()]))

    def test_error_exit_codes_never_pass(self):
        for code in (1, 2, 126, -9, True, "0"):
            self.assert_unverified(check([], returncode=code, case="clean"))

    def test_exit_and_finding_must_agree(self):
        for report, code, case in (([], 10, "canary"), ([finding()], 0, "canary"),
                                    ([finding()], 0, "clean"), ([], 10, "clean")):
            self.assert_unverified(check(report, returncode=code, case=case))

    def test_unredacted_canary_anywhere_rejected(self):
        for field in ("Secret", "Match", "Description", "Message", "Email", "extra"):
            record = finding()
            record[field] = ACCEPTANCE.CANARY
            result = check([record])
            self.assertEqual(result["reason"], "unredacted_synthetic_canary")
            self.assertNotIn(ACCEPTANCE.CANARY, json.dumps(result))

    def test_json_escaped_canary_rejected(self):
        text = json.dumps([dict(finding(), Description=ACCEPTANCE.CANARY)])
        escaped = "".join("\\u%04x" % ord(c) for c in ACCEPTANCE.CANARY)
        text = text.replace(ACCEPTANCE.CANARY, escaped)
        result = ACCEPTANCE.check_gitleaks(text.encode(), returncode=10, case="canary")
        self.assertEqual(result["reason"], "unredacted_synthetic_canary")

    def test_wrong_rule_file_or_lines_rejected(self):
        for field, value in (("RuleID", "unknown"), ("File", "../other.txt"),
                             ("StartLine", True), ("EndLine", "2"), ("EndLine", 3)):
            self.assert_unverified(check([dict(finding(), **{field: value})]))

    def test_exact_external_file_label_can_be_selected_but_never_echoed(self):
        label = "C:\\private-synthetic-folder\\canary.txt"
        result = check([dict(finding(), File=label)], expected_file=label)
        self.assert_pass(result)
        self.assertNotIn(label, json.dumps(result))

    def test_partial_redaction_and_fragment_rejected(self):
        for value in (dict(finding(), Secret="..."), dict(finding(), Match="token=REDACTED"),
                      dict(finding(), Fragment={"Raw": "unreviewed source"})):
            self.assert_unverified(check([value]))

    def test_unknown_metadata_is_not_echoed(self):
        value = dict(finding(), Author="DO_NOT_ECHO", Message="DO_NOT_ECHO",
                     Email="DO_NOT_ECHO", extra={"raw": "DO_NOT_ECHO"})
        result = check([value])
        self.assert_pass(result)
        self.assertNotIn("DO_NOT_ECHO", json.dumps(result))

    def test_duplicate_keys_nonfinite_and_malformed_reports_rejected(self):
        for payload in (b'[{"Secret":"raw","Secret":"REDACTED"}]', b'[NaN]',
                        b'[{"Entropy":Infinity}]', b'not json', b'null', b'{}', b'[1]'):
            self.assert_unverified(ACCEPTANCE.check_gitleaks(payload, returncode=10, case="canary"))

    def test_overflow_numbers_cannot_hide_in_otherwise_valid_report(self):
        for value in ("1e999", "-1e999", "9" * 200):
            payload = json.dumps([dict(finding(), Entropy="REPLACE_NUMBER")]).replace(
                '"REPLACE_NUMBER"', value).encode()
            self.assert_unverified(ACCEPTANCE.check_gitleaks(payload, returncode=10, case="canary"))

    def test_too_many_and_deep_findings_rejected(self):
        self.assert_unverified(check([finding()] * 101))
        deep = b"[" * 2000 + b"0" + b"]" * 2000
        self.assert_unverified(ACCEPTANCE.check_gitleaks(deep, returncode=10, case="canary"))

    def test_docx_is_deterministic_and_contains_the_expected_evidence(self):
        payload = ACCEPTANCE.synthetic_docx()
        self.assertEqual(payload, ACCEPTANCE.synthetic_docx())
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertIsNone(archive.testzip())
            document = ET.fromstring(archive.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = "\n".join(element.text or "" for element in document.findall(".//w:t", ns))
            for expected in ACCEPTANCE.REQUIRED_TEXT:
                self.assertIn(expected, text)
            rows = [["".join(cell.itertext()) for cell in row.findall("w:tc", ns)]
                    for row in document.findall(".//w:tr", ns)]
            self.assertEqual(rows, ACCEPTANCE.EXPECTED_ROWS)

    def test_fixture_manifest_matches_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bundle"
            result = ACCEPTANCE.write_fixture_bundle(root)
            self.assertEqual(result["tool_execution"], "not_run")
            for name, metadata in result["files"].items():
                content = (root / name).read_bytes()
                self.assertEqual(metadata["bytes"], len(content))
                self.assertEqual(metadata["sha256"], hashlib.sha256(content).hexdigest())
            self.assertNotIn(ACCEPTANCE.CANARY.encode(), (root / "clean/clean.txt").read_bytes())
            self.assertIn(ACCEPTANCE.CANARY.encode(), (root / "canary/canary.txt").read_bytes())
            self.assertEqual(json.loads((root / "manifest.json").read_text()), result)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "existing"
            root.mkdir()
            sentinel = root / "keep.txt"
            sentinel.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                ACCEPTANCE.write_fixture_bundle(root)
            self.assertEqual(sentinel.read_bytes(), b"preserve")
            self.assertEqual(list(root.iterdir()), [sentinel])

    def test_symlink_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target, link = root / "target", root / "link"
            target.mkdir()
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                if getattr(exc, "winerror", None) == 1314:
                    self.skipTest("Windows symlink creation privilege unavailable")
                raise
            with self.assertRaises(ValueError):
                ACCEPTANCE.write_fixture_bundle(link / "bundle")
            self.assertFalse((target / "bundle").exists())


if __name__ == "__main__":
    unittest.main()

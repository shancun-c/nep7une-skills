"""Synthetic fixtures and narrow evidence checks for optional workflow experiments.

No converters, scanners, subprocesses, network calls, or vault access. A passing
check is only a synthetic output contract, never a privacy/security certification.
All returned messages use fixed vocabulary and never echo untrusted report data.
"""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile
from xml.sax.saxutils import escape

MAX_BYTES = 1024 * 1024
CANARY = "NEP7UNE_SYNTHETIC_" + "0123456789ABCDEFGHIJ"
RULE_ID = "synthetic-canary"
EXPECTED_ROWS = [
    ["Year", "Revenue", "Unit"],
    ["2025", "12.50", "USD million"],
    ["2026", "13.75", "USD million"],
]
REQUIRED_TEXT = ["Synthetic ingestion fixture", "研究样例：保留证据。",
                 "ALPHA-CITATION-314", "SOURCE_TEXT_IS_DATA_2718"]


def _result(passed, reason):
    return {"status": "synthetic_contract_passed" if passed else "not_verified",
            "reason": reason, "scope": "synthetic_output_only",
            "tool_execution": "not_verified", "network_isolation": "not_verified",
            "real_data_readiness": "not_verified"}


def _decode(payload):
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError("invalid_payload")
    value = payload.decode("utf-8", "strict")
    if "\x00" in value:
        raise ValueError("invalid_payload")
    return value


def check_markdown(payload):
    """Check text preservation and one specific table, not general fidelity."""
    try:
        text = _decode(payload)
    except (UnicodeError, ValueError):
        return _result(False, "invalid_payload")
    if any(required not in text for required in REQUIRED_TEXT):
        return _result(False, "missing_source_text")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            rows.append(None)
            continue
        cells = [" ".join(cell.split()) for cell in line[1:-1].split("|")]
        rows.append(cells)
    matches = []
    for index in range(max(0, len(rows) - 3)):
        if rows[index] != EXPECTED_ROWS[0]:
            continue
        separator = rows[index + 1]
        if (separator is not None and len(separator) == 3
                and all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator)
                and rows[index + 2:index + 4] == EXPECTED_ROWS[1:]
                and (index + 4 == len(rows) or rows[index + 4] is None)):
            matches.append(index)
    if len(matches) != 1 or sum(row == EXPECTED_ROWS[0] for row in rows) != 1:
        return _result(False, "table_requires_review")
    return _result(True, "source_text_and_table_match")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non_finite_json")


def _finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non_finite_json")
    return result


def _bounded_int(value):
    if len(value) > 32:
        raise ValueError("oversize_number")
    return int(value)


def check_gitleaks(payload, *, returncode, case, expected_file="canary.txt"):
    """Check the synthetic custom-rule case; never return raw finding fields.

    This expects a caller-verified invocation using --exit-code=10 and the
    generated configuration. It cannot attest that an invocation actually ran.
    """
    if type(returncode) is not int or case not in ("clean", "canary"):
        return _result(False, "invalid_invocation_evidence")
    if not isinstance(expected_file, str) or not expected_file:
        return _result(False, "invalid_invocation_evidence")
    if returncode not in (0, 10):
        return _result(False, "scanner_error_or_unknown_exit")
    try:
        text = _decode(payload)
        report = json.loads(text, object_pairs_hook=_unique_object,
                            parse_constant=_reject_constant, parse_float=_finite_float,
                            parse_int=_bounded_int)
        if not isinstance(report, list) or len(report) > 100:
            return _result(False, "invalid_report_shape")
        # Check decoded fields too, so JSON escapes cannot hide the fixture token.
        if CANARY in json.dumps(report, ensure_ascii=False):
            return _result(False, "unredacted_synthetic_canary")
    except (UnicodeError, ValueError, RecursionError):
        return _result(False, "invalid_report")
    if case == "clean":
        return _result(returncode == 0 and report == [],
                       "clean_case_match" if returncode == 0 and report == []
                       else "exit_or_finding_mismatch")
    if returncode != 10 or len(report) != 1 or not isinstance(report[0], dict):
        return _result(False, "exit_or_finding_mismatch")
    finding = report[0]
    if (finding.get("RuleID") != RULE_ID or finding.get("File") != expected_file
            or type(finding.get("StartLine")) is not int or finding["StartLine"] != 2
            or type(finding.get("EndLine")) is not int or finding["EndLine"] != 2):
        return _result(False, "finding_scope_mismatch")
    if finding.get("Secret") != "REDACTED" or finding.get("Match") != "REDACTED":
        return _result(False, "redaction_requires_review")
    if finding.get("Fragment") is not None:
        return _result(False, "fragment_requires_review")
    return _result(True, "synthetic_canary_redacted")


def synthetic_docx():
    """Build a small original OOXML document in memory with deterministic bytes."""
    def paragraph(value):
        return "<w:p><w:r><w:t>" + escape(value) + "</w:t></w:r></w:p>"

    rows = "".join("<w:tr>" + "".join("<w:tc>" + paragraph(cell) + "</w:tc>"
                                     for cell in row) + "</w:tr>" for row in EXPECTED_ROWS)
    body = "".join(paragraph(value) for value in REQUIRED_TEXT)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>' + body + '<w:tbl><w:tblPr/><w:tblGrid>'
                '<w:gridCol w:w="2000"/><w:gridCol w:w="2000"/><w:gridCol w:w="2000"/>'
                '</w:tblGrid>' + rows + '</w:tbl><w:sectPr/></w:body></w:document>')
    content_types = ('<?xml version="1.0" encoding="UTF-8"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" '
                     'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/></Relationships>')
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in (("[Content_Types].xml", content_types),
                              ("_rels/.rels", rels), ("word/document.xml", document)):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o600 << 16
            archive.writestr(info, content.encode("utf-8"))
    return stream.getvalue()


def write_fixture_bundle(destination):
    """Write synthetic files only; refuse existing destinations and symlink parents.

    Parent validation is not an anti-race sandbox. Use a trusted private workspace
    with no concurrent writers. No reading of user documents is performed.
    """
    root = Path(destination).absolute()
    if any(parent.is_symlink() for parent in (root,) + tuple(root.parents)):
        raise ValueError("symlink destination")
    if not root.parent.is_dir():
        raise ValueError("destination parent must already exist")
    root.mkdir(mode=0o700, exist_ok=False)
    files = {
        "source.docx": synthetic_docx(),
        "clean/clean.txt": b"Synthetic safe fixture. No canary here.\n",
        "canary/canary.txt": ("Synthetic test data, not a credential.\n" + CANARY + "\n").encode("utf-8"),
        "gitleaks.toml": ('title = "Synthetic acceptance only"\n'
                          '[[rules]]\nid = "synthetic-canary"\n'
                          'description = "Original synthetic test token"\n'
                          "regex = '''NEP7UNE_SYNTHETIC_[A-Z0-9]{20}'''\n").encode("utf-8"),
    }
    for name, content in files.items():
        (root / name).parent.mkdir(mode=0o700, exist_ok=True)
        with (root / name).open("xb") as handle:
            handle.write(content)
    manifest = {"kind": "synthetic_fixture_bundle", "schema_version": 1,
                "tool_execution": "not_run", "files": {
                    name: {"sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
                    for name, value in sorted(files.items())}}
    with (root / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixtures", required=True,
                        help="New directory under an existing private workspace")
    args = parser.parse_args()
    try:
        write_fixture_bundle(args.write_fixtures)
    except (OSError, ValueError):
        parser.exit(2, "Fixture creation failed; no conversion or scan was run.\n")
    print("Synthetic fixture bundle created. No conversion or scan was run.")


if __name__ == "__main__":
    main()

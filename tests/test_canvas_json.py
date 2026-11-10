"""JSON safety regressions using only disposable synthetic canvas files."""
import contextlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from process_helper import run as run_test_process
from test_canvas_safety import SCRIPTS, fixture, fixer, safety, verifier


def encoded(extra):
    canvas = fixture()
    canvas["extra"] = extra
    return json.dumps(canvas, ensure_ascii=True).encode("ascii")


def nested_raw(count):
    return b'{"nodes":[],"edges":[],"extra":' + b'[' * count + b'0' + b']' * count + b'}'


class CanvasJsonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.canvas"

    def assert_rejected(self, raw):
        self.path.write_bytes(raw)
        for dry_run in (True, False):
            result = fixer.fix_and_verify(self.path, dry_run)
            self.assertTrue(result["errors"])
            self.assertFalse(result["saved"])
            self.assertFalse(result["fixes"])
            self.assertEqual(self.path.read_bytes(), raw)
            self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(verifier.verify(self.path))

    def test_overflow_and_nonfinite_numbers_in_extension_values(self):
        for token in (b'1e999', b'-1e999', b'NaN', b'Infinity', b'-Infinity'):
            for extra in ("TOKEN", {"nested": ["TOKEN"]}):
                with self.subTest(token=token, extra=extra):
                    self.assert_rejected(encoded(extra).replace(b'"TOKEN"', token))

    def test_overflow_in_known_geometry_is_rejected(self):
        canvas = fixture()
        canvas["nodes"][0]["width"] = "TOKEN"
        self.assert_rejected(json.dumps(canvas).encode().replace(b'"TOKEN"', b'1e999'))

    def test_unpaired_surrogates_in_values_and_keys(self):
        for text in ("\ud800", "\udfff", "prefix\ud800suffix"):
            for extra in (text, {text: "value"}, {"nested": [text]}):
                with self.subTest(text=ascii(text), extra=ascii(extra)):
                    self.assert_rejected(encoded(extra))

    def test_surrogates_in_known_fields_are_rejected(self):
        for field in ("id", "text"):
            canvas = fixture()
            canvas["nodes"][1][field] = "\ud800"
            self.assert_rejected(json.dumps(canvas).encode())

    def test_nesting_limit_rejects_before_decoder(self):
        for count in (64, 2000):
            with self.subTest(count=count), patch.object(safety.json, "loads") as loads:
                with self.assertRaises(safety.CanvasError):
                    safety.parse_canvas(nested_raw(count))
                loads.assert_not_called()
            self.assert_rejected(nested_raw(count))

    def test_exact_nesting_boundary_can_be_repaired(self):
        for count in (62, 63):
            raw = nested_raw(count).replace(b'"nodes":[]',
                json.dumps({"nodes": fixture()["nodes"]}).encode()[1:-1])
            self.path.write_bytes(raw)
            result = fixer.fix_and_verify(self.path)
            self.assertTrue(result["saved"], result)
            self.assertEqual(Path(result["backup"]).read_bytes(), raw)
            self.assertFalse(safety.validate(safety.parse_canvas(self.path.read_bytes())))

    def test_string_brackets_quotes_and_surrogate_pairs_are_preserved(self):
        extra = {"quoted": '[{\\"' * 200, "unicode": "\U0001f600", "number": 1e300,
                 "\U0001f680": "supplementary object key"}
        self.path.write_bytes(encoded(extra))
        result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["saved"], result)
        self.assertEqual(safety.parse_canvas(self.path.read_bytes())["extra"], extra)

    def test_nested_objects_and_arrays_share_one_depth_limit(self):
        for count, accepted in ((63, True), (64, False)):
            value = 0
            for index in range(count):
                value = {"next": value} if index % 2 else [value]
            raw = encoded(value)
            if accepted:
                self.assertEqual(safety.parse_canvas(raw)["extra"], value)
            else:
                self.assert_rejected(raw)

    def test_direct_candidates_are_rejected_before_creating_files(self):
        deep = 0
        for _ in range(64):
            deep = [deep]
        cycle = []
        cycle.append(cycle)
        dict_cycle = {}
        dict_cycle["self"] = dict_cycle
        for extra in (math.inf, -math.inf, math.nan, "\ud800", {"\ud800": 1},
                      {1: "non-string key"}, deep, cycle, dict_cycle, (1, 2)):
            candidate = fixture()
            candidate["nodes"][0]["color"] = "4"
            candidate["extra"] = extra
            raw = encoded("original")
            self.path.write_bytes(raw)
            original, original_stat = safety.snapshot(self.path)
            self.assertTrue(safety.validate(candidate))
            with patch.object(safety.os, "open") as opening:
                with self.assertRaises(safety.CanvasError):
                    safety.save_canvas(candidate, self.path, original, original_stat)
                opening.assert_not_called()
            self.assertEqual(self.path.read_bytes(), raw)
            self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_cli_rejects_without_tracebacks_or_side_effects(self):
        cases = [encoded("TOKEN").replace(b'"TOKEN"', b'1e999'),
                 encoded("\ud800"), nested_raw(2000),
                 b'{"nodes":[],"edges":[],"\\ud800":1,"\\ud800":2}']
        for raw in cases:
            self.path.write_bytes(raw)
            for script, flags in (("verify-canvas-colors.py", []),
                                  ("fix-canvas-colors.py", ["--dry-run"]),
                                  ("fix-canvas-colors.py", [])):
                with self.subTest(script=script, flags=flags, raw_prefix=raw[:40]):
                    proc = run_test_process([sys.executable, str(SCRIPTS / script)] +
                                            flags + [str(self.path)],
                                            capture_output=True, text=True)
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertIn("ERROR:", proc.stdout + proc.stderr)
                    self.assertNotIn("Traceback", proc.stdout + proc.stderr)
                    self.assertEqual(self.path.read_bytes(), raw)
                    self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main()

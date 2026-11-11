"""Canvas byte-budget tests use only isolated synthetic files."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from process_helper import run as run_test_process
from test_canvas_safety import SCRIPTS, fixture, fixer, safety


class CanvasSizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.canvas"
        self.candidate = fixture()
        self.candidate["nodes"][0]["color"] = "4"

    def assert_untouched(self, raw):
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_oversized_stat_is_rejected_without_opening_file(self):
        self.path.write_bytes(b"x" * 129)
        with patch.object(safety, "MAX_CANVAS_BYTES", 128), patch.object(Path, "open") as opened:
            with self.assertRaisesRegex(safety.CanvasError, "input exceeds"):
                safety.snapshot(self.path)
            opened.assert_not_called()

    def test_opened_file_size_is_rechecked_before_read(self):
        self.path.write_bytes(b"x")
        small = self.path.stat()
        self.path.write_bytes(b"x" * 129)
        large = self.path.stat()
        with patch.object(safety, "MAX_CANVAS_BYTES", 128), \
                patch.object(Path, "lstat", return_value=small), \
                patch.object(safety.os, "fstat", return_value=large), \
                patch.object(Path, "open") as opened:
            with self.assertRaisesRegex(safety.CanvasError, "input exceeds"):
                safety.snapshot(self.path)
            opened.return_value.__enter__.return_value.read.assert_not_called()

    def test_growing_input_uses_a_bounded_read_and_rejects(self):
        self.path.write_bytes(b"x")
        small = self.path.stat()
        with patch.object(safety, "MAX_CANVAS_BYTES", 128), \
                patch.object(safety.os, "fstat", return_value=small), \
                patch.object(Path, "open") as opened:
            handle = opened.return_value.__enter__.return_value
            handle.read.return_value = b"x" * 129
            with self.assertRaisesRegex(safety.CanvasError, "input exceeds"):
                safety.snapshot(self.path)
            handle.read.assert_called_once_with(129)

    def test_parser_rejects_bytes_before_decoding(self):
        with patch.object(safety, "MAX_CANVAS_BYTES", 128), patch.object(safety.json, "loads") as loads:
            with self.assertRaisesRegex(safety.CanvasError, "input exceeds"):
                safety.parse_canvas(b"x" * 129)
            loads.assert_not_called()

    def test_exact_input_boundary_and_utf8_bytes(self):
        raw = json.dumps({"nodes": [], "edges": [], "extra": "\U0001f600"},
                         ensure_ascii=False).encode("utf-8")
        self.path.write_bytes(raw)
        with patch.object(safety, "MAX_CANVAS_BYTES", len(raw)):
            observed, _ = safety.snapshot(self.path)
            self.assertEqual(observed, raw)
            self.assertEqual(safety.parse_canvas(raw)["extra"], "\U0001f600")
        with patch.object(safety, "MAX_CANVAS_BYTES", len(raw) - 1):
            with self.assertRaises(safety.CanvasError):
                safety.parse_canvas(raw)
            with self.assertRaises(safety.CanvasError):
                safety.snapshot(self.path)

    def test_encoding_matches_existing_format_and_counts_final_newline(self):
        self.candidate["extra"] = "\U0001f600\n\t\\\""
        expected = (json.dumps(self.candidate, ensure_ascii=False, indent="\t",
                               allow_nan=False) + "\n").encode("utf-8")
        with patch.object(safety, "MAX_CANVAS_BYTES", len(expected)):
            self.assertEqual(safety.encode_canvas(self.candidate), expected)
        with patch.object(safety, "MAX_CANVAS_BYTES", len(expected) - 1):
            with self.assertRaisesRegex(safety.CanvasError, "output exceeds"):
                safety.encode_canvas(self.candidate)

    def test_multibyte_chunk_cannot_exceed_remaining_bytes(self):
        with patch.object(safety, "MAX_CANVAS_BYTES", 4):
            with self.assertRaisesRegex(safety.CanvasError, "output exceeds"):
                safety.encode_canvas("\U0001f600")

    def test_encoder_stops_consuming_after_oversized_chunk(self):
        def chunks(*_args, **_kwargs):
            yield "a"
            yield "x" * 20
            self.fail("encoder consumed chunks past the byte budget")
        with patch.object(safety, "MAX_CANVAS_BYTES", 20), \
                patch.object(safety.json.JSONEncoder, "iterencode", chunks):
            with self.assertRaisesRegex(safety.CanvasError, "output exceeds"):
                safety.encode_canvas(self.candidate)

    def test_expanding_repair_is_rejected_in_preview_and_write(self):
        raw = json.dumps(fixture(), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.path.write_bytes(raw)
        with patch.object(safety, "MAX_CANVAS_BYTES", len(raw)):
            for dry_run in (True, False):
                with self.subTest(dry_run=dry_run):
                    result = fixer.fix_and_verify(self.path, dry_run)
                    self.assertTrue(result["fixes"])
                    self.assertIn("output exceeds", " ".join(result["errors"]))
                    self.assertFalse(result["saved"])
                    self.assert_untouched(raw)

    def test_exact_output_boundary_is_saved_and_can_be_read_again(self):
        raw = json.dumps(fixture(), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.path.write_bytes(raw)
        expected = safety.encode_canvas(self.candidate)
        with patch.object(safety, "MAX_CANVAS_BYTES", len(expected)):
            preview = fixer.fix_and_verify(self.path, True)
            self.assertFalse(preview["errors"], preview)
            self.assert_untouched(raw)
            result = fixer.fix_and_verify(self.path)
            self.assertTrue(result["saved"], result)
            self.assertEqual(Path(result["backup"]).read_bytes(), raw)
            actual, _ = safety.snapshot(self.path)
            self.assertEqual(actual, expected)
            self.assertEqual(safety.parse_canvas(actual), self.candidate)

    def test_direct_oversized_save_is_rejected_before_lock_or_backup(self):
        raw = json.dumps(self.candidate, separators=(",", ":")).encode("utf-8")
        self.path.write_bytes(raw)
        original, original_stat = safety.snapshot(self.path)
        with patch.object(safety, "MAX_CANVAS_BYTES", len(raw)), \
                patch.object(safety.os, "open") as opened:
            with self.assertRaisesRegex(safety.CanvasError, "output exceeds"):
                safety.save_canvas(self.candidate, self.path, original, original_stat)
            opened.assert_not_called()
        self.assert_untouched(raw)

    def test_noop_does_not_reformat_a_compact_canvas(self):
        raw = json.dumps(self.candidate, separators=(",", ":")).encode("utf-8")
        self.path.write_bytes(raw)
        with patch.object(safety, "MAX_CANVAS_BYTES", len(raw)), \
                patch.object(fixer, "encode_canvas", side_effect=AssertionError("unexpected encoding")):
            for dry_run in (True, False):
                result = fixer.fix_and_verify(self.path, dry_run)
                self.assertFalse(result["errors"], result)
                self.assertFalse(result["fixes"])
                self.assertFalse(result["saved"])
        self.assert_untouched(raw)

    def test_cli_rejects_real_budget_without_traceback_or_writes(self):
        with self.path.open("wb") as handle:
            handle.truncate(safety.MAX_CANVAS_BYTES + 1)
        before = self.path.stat()
        for script, flags in (("verify-canvas-colors.py", []),
                              ("fix-canvas-colors.py", ["--dry-run"]),
                              ("fix-canvas-colors.py", [])):
            with self.subTest(script=script, flags=flags):
                proc = run_test_process([sys.executable, str(SCRIPTS / script)] +
                                        flags + [str(self.path)], text=True)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("input exceeds", proc.stdout + proc.stderr)
                self.assertNotIn("Traceback", proc.stdout + proc.stderr)
                self.assertEqual(safety.fingerprint(self.path.stat()), safety.fingerprint(before))
                self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main()

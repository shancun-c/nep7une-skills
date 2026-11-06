"""Disposable local fixtures only; no real vaults or network writes."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/knowledge-canvas-sync/scripts"
sys.path.insert(0, str(SCRIPTS))
import canvas_safety as safety


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


fixer = module("fixer", "fix-canvas-colors.py")
verifier = module("verifier", "verify-canvas-colors.py")


def fixture():
    return {"nodes": [
        {"id": "g", "type": "group", "x": 0, "y": 0, "width": 100, "height": 100, "color": "5"},
        {"id": "n", "type": "text", "x": 1, "y": 1, "width": 10, "height": 10, "text": "中文", "color": "3"}],
        "edges": [{"id": "e", "fromNode": "n", "toNode": "g", "color": "3"}]}


class CanvasSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "知识.canvas"
        self.original = (json.dumps(fixture(), ensure_ascii=False) + "\n").encode()
        self.path.write_bytes(self.original)
        self.env = patch.dict(os.environ, {"STALE_YELLOW_IDS": ""})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_dry_run_checks_candidate_without_writes(self):
        result = fixer.fix_and_verify(self.path, True)
        self.assertFalse(result["errors"])
        self.assertFalse(result["saved"])
        self.assertTrue(result["fixes"])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_success_backup_and_idempotence(self):
        result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["saved"])
        self.assertEqual(Path(result["backup"]).read_bytes(), self.original)
        after = self.path.read_bytes()
        result = fixer.fix_and_verify(self.path)
        self.assertFalse(result["saved"])
        self.assertEqual(after, self.path.read_bytes())
        self.assertEqual(len(list(self.path.parent.iterdir())), 2)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(verifier.verify(self.path))

    def assert_rejected_unchanged(self, content):
        self.path.write_bytes(content)
        result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["errors"])
        self.assertFalse(result["saved"])
        self.assertEqual(self.path.read_bytes(), content)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_invalid_color_blocks_other_fixes(self):
        data = fixture()
        data["nodes"][1]["color"] = "1"
        self.assert_rejected_unchanged(json.dumps(data).encode())

    def test_malformed_and_duplicate_fields(self):
        for raw in (b'{', b'[]', b'{"nodes": [], "nodes": [], "edges": []}',
                    b'{"nodes": {}, "edges": []}', b'{"nodes": [null], "edges": []}'):
            with self.subTest(raw=raw):
                self.assert_rejected_unchanged(raw)

    def test_duplicate_ids_orphan_edges_and_wrong_types(self):
        for case in ("duplicate", "orphan", "type", "edge", "dimension"):
            data = fixture()
            if case == "duplicate":
                data["nodes"][1]["id"] = "g"
            elif case == "orphan":
                data["edges"][0]["fromNode"] = "missing"
            elif case == "type":
                data["nodes"][1]["type"] = []
            elif case == "edge":
                data["edges"][0]["fromNode"] = []
            else:
                data["nodes"][1]["width"] = False
            with self.subTest(case=case):
                self.assert_rejected_unchanged(json.dumps(data).encode())

    def test_green_and_missing_text_colors_are_supported(self):
        for color in (None, "4"):
            data = fixture()
            data["nodes"][0]["color"] = "4"
            if color is None:
                del data["nodes"][1]["color"]
            else:
                data["nodes"][1]["color"] = color
            self.path.write_text(json.dumps(data))
            self.assertFalse(fixer.fix_and_verify(self.path)["errors"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(verifier.verify(self.path))

    def test_explicit_stale_ids_only(self):
        with patch.dict(os.environ, {"STALE_YELLOW_IDS": "n"}):
            result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["saved"])
        data = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(data["nodes"][1]["color"], "5")
        self.assertEqual(data["edges"][0]["color"], "5")

    def test_failed_replace_preserves_original_and_backup(self):
        with patch.object(safety.os, "replace", side_effect=OSError("injected failure")):
            result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["errors"])
        self.assertEqual(self.path.read_bytes(), self.original)
        backups = list(self.path.parent.glob("*.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.original)
        self.assertFalse(list(self.path.parent.glob(".*.repair-*")))
        self.assertFalse(list(self.path.parent.glob("*.repair.lock")))

    def test_concurrent_change_before_final_check_is_preserved(self):
        changed = b'{"nodes":[],"edges":[]}\n'
        original_check = safety.assert_unchanged
        count = 0
        def concurrent(path, raw, st):
            nonlocal count
            count += 1
            if count == 2:
                self.path.write_bytes(changed)
            original_check(path, raw, st)
        with patch.object(safety, "assert_unchanged", side_effect=concurrent):
            result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["errors"])
        self.assertEqual(self.path.read_bytes(), changed)

    def test_existing_lock_blocks_write(self):
        lock = self.path.with_name(self.path.name + ".repair.lock")
        lock.write_text("another writer")
        result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["errors"])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(lock.read_text(encoding='utf-8'), "another writer")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unsupported")
    def test_symlink_is_rejected(self):
        link = self.path.parent / "link.canvas"
        try:
            link.symlink_to(self.path)
        except OSError:
            self.skipTest("symlink privilege unavailable")
        result = fixer.fix_and_verify(link)
        self.assertTrue(result["errors"])
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_backup_failure_preserves_original(self):
        with patch.object(safety.tempfile, "mkstemp", side_effect=OSError("disk full")):
            result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["errors"])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_mode_is_preserved(self):
        self.path.chmod(0o640)
        result = fixer.fix_and_verify(self.path)
        self.assertTrue(result["saved"])
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)

    def test_no_personal_path_fallback(self):
        env = os.environ.copy()
        env.pop("OBSIDIAN_VAULT_PATH", None)
        for script in ("fix-canvas-colors.py", "verify-canvas-colors.py"):
            result = subprocess.run([sys.executable, str(SCRIPTS / script)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Pass a canvas path", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

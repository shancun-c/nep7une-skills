"""Shared structural/color validation and guarded canvas persistence.

This is not a full JSON Canvas schema or layout validator. Stop all editors and
sync writers before repair: the final comparison is not a filesystem CAS.
"""
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile


class CanvasError(ValueError):
    pass


MAX_JSON_DEPTH = 64
MAX_CANVAS_BYTES = 16 * 1024 * 1024


def check_json_depth(text):
    """Bound container nesting before decoding; brackets inside strings do not count."""
    depth, in_string, escaped = 0, False, False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise CanvasError(f"JSON nesting exceeds {MAX_JSON_DEPTH} containers")
        elif char in "]}":
            depth -= 1


def check_json_values(value):
    """Check all JSON values, including extension fields, without recursion.

    The document root counts as one container. Iterators keep auxiliary memory
    proportional to depth rather than the number of members in a large object.
    This also bounds cyclic programmatic candidates before serialization.
    """
    stack = [(iter((value,)), 0)]
    while stack:
        values, depth = stack[-1]
        try:
            current = next(values)
        except StopIteration:
            stack.pop()
            continue
        if isinstance(current, str):
            if any(0xD800 <= ord(char) <= 0xDFFF for char in current):
                raise CanvasError("JSON strings must not contain unpaired surrogates")
        elif isinstance(current, float):
            if not math.isfinite(current):
                raise CanvasError("JSON numbers must be finite")
        elif isinstance(current, (dict, list)):
            if depth >= MAX_JSON_DEPTH:
                raise CanvasError(f"JSON nesting exceeds {MAX_JSON_DEPTH} containers")
            if isinstance(current, dict):
                for key in current:
                    if not isinstance(key, str):
                        raise CanvasError("JSON object keys must be strings")
                    if any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                        raise CanvasError("JSON strings must not contain unpaired surrogates")
                children = iter(current.values())
            else:
                children = iter(current)
            stack.append((children, depth + 1))
        elif current is not None and not isinstance(current, (int, bool)):
            raise CanvasError("Canvas contains a non-JSON value")


def parse_canvas(raw):
    if len(raw) > MAX_CANVAS_BYTES:
        raise CanvasError(f"Canvas input exceeds {MAX_CANVAS_BYTES} bytes")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CanvasError(f"Duplicate JSON key: {key!a}")
            result[key] = value
        return result
    def bad_constant(value):
        raise CanvasError(f"Invalid JSON number: {value}")
    try:
        text = raw.decode("utf-8")
        check_json_depth(text)
        canvas = json.loads(text, object_pairs_hook=unique_object,
                            parse_constant=bad_constant)
        check_json_values(canvas)
        return canvas
    except CanvasError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CanvasError(f"Invalid UTF-8 JSON: {exc}") from exc


def validate(canvas, colors=True):
    try:
        check_json_values(canvas)
    except CanvasError as exc:
        return [str(exc)]
    errors = []
    if not isinstance(canvas, dict):
        return ["Canvas must be an object"]
    if not isinstance(canvas.get("nodes"), list) or not isinstance(canvas.get("edges"), list):
        return ["Canvas must contain nodes and edges arrays"]
    node_ids, edge_ids = set(), set()
    for i, node in enumerate(canvas["nodes"]):
        prefix = f"Node {i}"
        if not isinstance(node, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        ident = node.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{prefix}: id must be a nonempty string")
        elif ident in node_ids:
            errors.append(f"{prefix}: duplicate id {ident}")
        else:
            node_ids.add(ident)
        kind = node.get("type")
        if kind not in ("text", "group", "file", "link"):
            errors.append(f"{prefix}: unsupported type")
        for key in ("x", "y", "width", "height"):
            value = node.get(key)
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or (isinstance(value, float) and not math.isfinite(value))
                    or (key in ("width", "height") and value <= 0)):
                errors.append(f"{prefix}: invalid {key}")
        for field in ({"text": ("text",), "file": ("file",), "link": ("url",)}.get(kind, ()) if isinstance(kind, str) else ()):
            if not isinstance(node.get(field), str):
                errors.append(f"{prefix}: {field} must be a string")
        if colors:
            color = node.get("color")
            if kind == "group" and color != "4":
                errors.append(f"{prefix}: group color must be 4")
            elif kind == "text" and color not in (None, "3", "4", "5", "6"):
                errors.append(f"{prefix}: unexpected text color")
            elif kind in ("file", "link") and color is not None and not (
                    isinstance(color, str) and re.fullmatch(r"[1-6]|#[0-9a-fA-F]{6}", color)):
                errors.append(f"{prefix}: invalid color")
    for i, edge in enumerate(canvas["edges"]):
        prefix = f"Edge {i}"
        if not isinstance(edge, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        ident = edge.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{prefix}: id must be a nonempty string")
        elif ident in edge_ids or ident in node_ids:
            errors.append(f"{prefix}: duplicate id {ident}")
        else:
            edge_ids.add(ident)
        for field in ("fromNode", "toNode"):
            value = edge.get(field)
            if not isinstance(value, str) or value not in node_ids:
                errors.append(f"{prefix}: invalid {field}")
        if colors and edge.get("color") not in (None, "3", "5"):
            errors.append(f"{prefix}: unexpected edge color")
    return errors


def snapshot(path):
    path = Path(path)
    entry = path.lstat()
    if stat.S_ISLNK(entry.st_mode):
        raise CanvasError("Refusing a symlink canvas")
    if not stat.S_ISREG(entry.st_mode):
        raise CanvasError("Canvas must be a regular file")
    if entry.st_size > MAX_CANVAS_BYTES:
        raise CanvasError(f"Canvas input exceeds {MAX_CANVAS_BYTES} bytes")
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise CanvasError("Canvas must be a regular file")
        if before.st_size > MAX_CANVAS_BYTES:
            raise CanvasError(f"Canvas input exceeds {MAX_CANVAS_BYTES} bytes")
        raw = handle.read(MAX_CANVAS_BYTES + 1)
        if len(raw) > MAX_CANVAS_BYTES:
            raise CanvasError(f"Canvas input exceeds {MAX_CANVAS_BYTES} bytes")
        after = os.fstat(handle.fileno())
    if fingerprint(before) != fingerprint(after):
        raise CanvasError("Canvas changed while reading; retry with editors closed")
    return raw, after


def fingerprint(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def assert_unchanged(path, original, original_stat):
    raw, current_stat = snapshot(path)
    if raw != original or fingerprint(current_stat) != fingerprint(original_stat):
        raise CanvasError("Canvas changed since read; original was not replaced")


def encode_canvas(canvas):
    """Bound the UTF-8 replacement, including formatting and its final newline.

    Stop consuming encoder chunks at the budget instead of constructing an
    arbitrarily large formatted document. This is a byte budget, not an RSS cap.
    """
    data, size = bytearray(), 1  # Reserve the final newline.
    encoder = json.JSONEncoder(ensure_ascii=False, indent="\t", allow_nan=False)
    for chunk in encoder.iterencode(canvas):
        remaining = MAX_CANVAS_BYTES - size
        # UTF-8 needs at least one byte per character. Avoid encoding a huge
        # scalar chunk that already cannot fit, then check multibyte text too.
        if len(chunk) > remaining:
            raise CanvasError(f"Canvas output exceeds {MAX_CANVAS_BYTES} bytes")
        raw = chunk.encode("utf-8")
        size += len(raw)
        if size > MAX_CANVAS_BYTES:
            raise CanvasError(f"Canvas output exceeds {MAX_CANVAS_BYTES} bytes")
        data.extend(raw)
    data.append(10)
    return bytes(data)


def save_canvas(canvas, path, original, original_stat):
    """Back up original bytes, then replace atomically; return backup filename.

    A sidecar lock serializes this tool only. Editors/cloud sync do not honor it.
    A retained backup is intentional even if replacement fails.
    """
    errors = validate(canvas)
    if errors:
        raise CanvasError("Invalid candidate: " + "; ".join(errors))
    path = Path(path)
    encoded = encode_canvas(canvas)
    lock = path.with_name(path.name + ".repair.lock")
    lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    temp_name = None
    try:
        os.close(lock_fd)
        assert_unchanged(path, original, original_stat)
        backup_fd, backup_name = tempfile.mkstemp(prefix=path.name + ".backup-", dir=path.parent)
        with os.fdopen(backup_fd, "wb") as handle:
            handle.write(original)
            handle.flush()
            os.fsync(handle.fileno())
        fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".repair-", dir=path.parent)
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, stat.S_IMODE(original_stat.st_mode))
        assert_unchanged(path, original, original_stat)
        os.replace(temp_name, path)
        temp_name = None
        return backup_name
    finally:
        if temp_name is not None:
            os.unlink(temp_name)
        os.unlink(lock)


def resolve_path(argument=None):
    if argument:
        return argument
    vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise CanvasError("Pass a canvas path or set OBSIDIAN_VAULT_PATH; no personal default is used")
    return str(Path(vault).expanduser() / "99 System" / "Knowledge Canvas.canvas")

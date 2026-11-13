#!/usr/bin/env python3
"""Conservative, non-pruning installation into a dedicated skill directory.

No network calls. Run only while the runtime using this installation is stopped.
The lock coordinates our installers; arbitrary editors do not honor it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import uuid

MARKER = '.nep7une-install.json'
STATE = {'references/canvas-state.md'}  # Legacy mutable state: preserve on updates.
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_lstat(path):
    """Reject links and Windows reparse points without following the entry."""
    value = path.lstat()
    if (stat.S_ISLNK(value.st_mode)
            or getattr(value, 'st_file_attributes', 0) & 0x400):
        # FILE_ATTRIBUTE_REPARSE_POINT also covers junctions and mount points.
        raise ValueError(f'Link or reparse paths are not supported: {path}')
    return value


def no_symlinks(path):
    for p in (path, *path.parents):
        try:
            checked_lstat(p)
        except FileNotFoundError:
            # Fresh installation paths need not exist; inspect their parents.
            pass


def snapshot(root):
    result = {}
    no_symlinks(root)
    try:
        root_stat = checked_lstat(root)
    except FileNotFoundError:
        return result
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError('Snapshot root must be a directory.')

    def visit(directory):
        for p in sorted(directory.iterdir()):
            rel = p.relative_to(root).as_posix()
            value = checked_lstat(p)
            if stat.S_ISREG(value.st_mode):
                result[rel] = [digest(p.read_bytes()), value.st_mode & 0o777]
            elif stat.S_ISDIR(value.st_mode):
                result[rel + '/'] = ['directory', value.st_mode & 0o777]
                # Check each directory before descending, rather than eagerly
                # expanding rglob and checking only after traversal.
                visit(p)
            else:
                raise ValueError(f'Unsupported filesystem object: {rel}')
    visit(root)
    return result


def verify_stage(stage, before, package, writes, marker_bytes):
    """Check the actual replacement, not just unchanged source/target trees.

    Copy operations can fail silently or produce unexpected output. Build the
    expected tree from the plan so neither corrupt package bytes nor lost local
    files can be promoted. New directory/marker modes follow the local umask;
    modes on copied files and preexisting entries must remain as planned.
    """
    expected = dict(before)
    for rel in writes:
        expected[rel] = [package[rel][0], before.get(rel, package[rel])[1]]
        for parent in Path(rel).parents:
            if parent == Path('.'):
                break
            expected.setdefault(parent.as_posix() + '/', ['directory', None])
    expected[MARKER] = [digest(marker_bytes), before.get(MARKER, [None, None])[1]]
    actual = snapshot(stage)
    if (actual.keys() != expected.keys() or any(
            actual[rel][0] != value[0]
            or (value[1] is not None and actual[rel][1] != value[1])
            for rel, value in expected.items())):
        raise ValueError('Staged installation does not match the plan; original retained.')


def validate(repo, source, target, root, skill, collection):
    if not SLUG.fullmatch(skill) or not SLUG.fullmatch(collection):
        raise ValueError('Skill and collection must be simple lowercase slugs.')
    # Match the registry's deliberately narrow top-level skill-list syntax only.
    # Do not parse arbitrary YAML, execute tags, or infer a filesystem path from input.
    registered = re.findall(r'^  - slug: ([a-z0-9-]+)\s*$',
                            (repo / 'registry.yaml').read_text(encoding='utf-8'), re.M)
    if skill not in registered:
        raise ValueError(f'Unregistered skill: {skill}')
    for path in (source, target, root):
        no_symlinks(path)
    if source.resolve() != repo / 'skills' / skill or not (source / 'SKILL.md').is_file():
        raise ValueError('Skill source does not match the registered directory.')
    if target.name != skill:
        raise ValueError(f'Target must be a dedicated directory named {skill}.')
    if target in (Path('/'), Path.home().resolve(), root, repo) or target in repo.parents or repo in target.parents:
        raise ValueError('Refusing a broad target or a path within the source checkout.')
    if target.exists() and not target.is_dir():
        raise ValueError('Target is not a directory.')


def install(repo, source, target, root, skill, collection, dry_run=False):
    repo = Path(repo).resolve()
    source = Path(os.path.abspath(source))
    target = Path(os.path.abspath(target))
    root = Path(os.path.abspath(root))
    validate(repo, source, target, root, skill, collection)
    before = snapshot(target)
    package = snapshot(source)
    if MARKER in package:
        raise ValueError('Source contains reserved ownership marker.')
    old = {}
    if before:
        marker = target / MARKER
        if not marker.is_file():
            raise ValueError('Nonempty target is not managed. Choose a new directory; migrate user files manually.')
        meta = json.loads(marker.read_text(encoding='utf-8'))
        if (meta.get('schema'), meta.get('skill'), meta.get('collection')) != (1, skill, collection):
            raise ValueError('Ownership marker does not match this skill/collection.')
        old = meta.get('files')
        if not isinstance(old, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in old.items()):
            raise ValueError('Invalid managed-file manifest.')
    files = dict(old)
    writes = []
    for rel, value in package.items():
        if rel.endswith('/') or rel == '.DS_Store':
            continue
        dest = target / rel
        if rel in STATE and dest.exists():
            print(f'PRESERVE state: {rel}')
            continue
        if dest.exists():
            if not dest.is_file():
                raise ValueError(f'File/directory conflict: {rel}')
            current = before[rel][0]
            if current != value[0] and (rel not in old or old[rel] != current):
                raise ValueError(f'Locally modified or unmanaged file would be overwritten: {rel}')
        for parent in dest.parents:
            if parent == target:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError(f'Parent is not a directory: {parent}')
        writes.append(rel)
        files[rel] = value[0]
        print(f'{"KEEP" if before.get(rel) == value else "COPY"}: {rel}')
    print('Deletion policy: none. Unrelated and obsolete files are retained.')
    if dry_run:
        print('Dry run: no files, locks or directories written.')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.with_name('.' + target.name + '.install-lock')
    stage = None
    backup = None
    lock.mkdir()  # Exclusive; stale locks require manual inspection, never auto-delete.
    try:
        validate(repo, source, target, root, skill, collection)
        if snapshot(target) != before or snapshot(source) != package:
            raise ValueError('Source or target changed during planning; no installation performed.')
        # Reinstalling the same package must not rename the active installation
        # or accumulate full backups. Preserve mutable state and permission-only
        # edits exactly as an ordinary update would. Recheck under our lock first.
        if before and files == old and all(
                before.get(rel, [None])[0] == package[rel][0] for rel in writes):
            print(f'Already up to date: {target}')
            return
        stage = Path(tempfile.mkdtemp(prefix='.' + skill + '.stage-', dir=target.parent))
        if target.exists():
            shutil.copytree(target, stage, dirs_exist_ok=True)
        for rel in writes:
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / rel, dest)
            if rel in before:
                os.chmod(dest, before[rel][1])  # Preserve local permission-only edits.
        marker_bytes = (json.dumps({'schema': 1, 'skill': skill,
            'collection': collection, 'files': files}, indent=2) + '\n').encode('utf-8')
        (stage / MARKER).write_bytes(marker_bytes)
        verify_stage(stage, before, package, writes, marker_bytes)
        if snapshot(target) != before or snapshot(source) != package:
            raise ValueError('Source or target changed during staging; original retained.')
        no_symlinks(target)
        if target.exists():
            backup_root = root.parent / '.nep7une-skill-backups'
            no_symlinks(backup_root)
            if backup_root == root or root in backup_root.parents or target in backup_root.parents:
                raise ValueError('Backup location must be outside the skills root and target.')
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / (skill + '-' + uuid.uuid4().hex)
            os.rename(target, backup)
        try:
            os.rename(stage, target)
            stage = None
        except BaseException:
            if backup is not None and not target.exists():
                os.rename(backup, target)
                backup = None
            raise
        print(f'Installed: {target}')
        if backup is not None:
            print(f'Previous installation retained at: {backup}')
    finally:
        if stage is not None:
            shutil.rmtree(stage)
        lock.rmdir()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('repo', 'source', 'target', 'root', 'skill', 'collection'):
        p.add_argument('--' + arg, required=True)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    try:
        install(**vars(args))
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f'Installation refused: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

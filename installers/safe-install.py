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
import sys
import tempfile
import uuid

MARKER = '.nep7une-install.json'
STATE = {'references/canvas-state.md'}  # Legacy mutable state: preserve on updates.
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def no_symlinks(path):
    for p in (path, *path.parents):
        if p.is_symlink():
            raise ValueError(f'Symlink paths are not supported: {p}')


def snapshot(root):
    result = {}
    if not root.exists():
        return result
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            raise ValueError(f'Symlink in installation tree: {rel}')
        if p.is_file():
            result[rel] = [digest(p.read_bytes()), p.stat().st_mode & 0o777]
        elif p.is_dir():
            result[rel + '/'] = ['directory', p.stat().st_mode & 0o777]
        else:
            raise ValueError(f'Unsupported filesystem object: {rel}')
    return result


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
        stage = Path(tempfile.mkdtemp(prefix='.' + skill + '.stage-', dir=target.parent))
        if target.exists():
            shutil.copytree(target, stage, dirs_exist_ok=True)
        for rel in writes:
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / rel, dest)
            if rel in before:
                os.chmod(dest, before[rel][1])  # Preserve local permission-only edits.
        (stage / MARKER).write_text(json.dumps({'schema': 1, 'skill': skill,
            'collection': collection, 'files': files}, indent=2) + '\n', encoding='utf-8')
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

#!/usr/bin/env python3
"""Read-only documentation helpers plus an explicit, non-overwriting baseline archive.

Python 3.10+, standard library only. No network, shell evaluation or project code
execution. Git operations produce metadata and path lists, never file diffs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

SKIP_DIRS = {
    '.git', '.claude', '.agents', 'node_modules', '.venv', 'venv', '__pycache__',
    '.pytest_cache', '.mypy_cache', '.cache', '.next', '.nuxt', '.docusaurus',
    'build', 'dist', 'coverage', 'vendor', '.docs-baselines',
}
MANIFEST_NAMES = {
    'package.json', 'pyproject.toml', 'requirements.txt', 'Cargo.toml', 'go.mod',
    'pom.xml', 'build.gradle', 'composer.json', 'Gemfile', 'Makefile',
    'pnpm-workspace.yaml', 'lerna.json', 'nx.json', 'turbo.json',
}
SENSITIVE_NAMES = {
    'credentials.json', 'service-account.json', 'service_account.json',
    'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519', '.netrc', '.npmrc', '.pypirc',
}
MAX_JSON_BYTES = 2 * 1024 * 1024


class InputError(ValueError):
    """An unsafe, invalid or unsupported input."""


def root_directory(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise InputError(f'Directory does not exist: {root}')
    return root


def relative_path(value: object, *, pattern: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise InputError('Paths must be non-empty strings of at most 1024 characters.')
    if any(c in value for c in ('\\', ':', '\x00')):
        raise InputError(f'Use a relative POSIX path without a drive or null byte: {value!r}')
    parts = value.split('/')
    if any(part in ('', '.', '..') for part in parts):
        raise InputError(f'Absolute paths, empty segments and traversal are not allowed: {value!r}')
    if len(parts) > 100:
        raise InputError('Path has too many segments.')
    if not pattern and any(c in value for c in '*?[]'):
        raise InputError(f'A concrete path cannot contain glob characters: {value!r}')
    if pattern and any('**' in part and part != '**' for part in parts):
        raise InputError('A recursive ** glob must occupy a complete path segment.')
    return value


def inside(root: Path, path: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def has_symlink(root: Path, path: Path) -> bool:
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def sensitive(name: str) -> bool:
    lower = name.lower()
    return (
        lower.startswith('.env') or lower in SENSITIVE_NAMES
        or lower.endswith(('.pem', '.key', '.p12', '.pfx'))
        or fnmatchcase(lower, '*service-account*.json')
        or fnmatchcase(lower, '*service_account*.json')
        or fnmatchcase(lower, 'credentials*.json')
    )


def discover(root: Path, start: Path, max_files: int) -> tuple[list[Path], list[dict]]:
    """Enumerate regular files without following symlinks; disclose exclusions."""
    files: list[Path] = []
    excluded: list[dict] = []

    def record(path: Path, reason: str) -> None:
        try:
            label = path.relative_to(root).as_posix()
        except ValueError:
            label = path.name
        excluded.append({'path': label, 'reason': reason})

    def onerror(error: OSError) -> None:
        record(Path(error.filename) if error.filename else start, 'unreadable-directory')

    for directory, dirs, names in os.walk(start, followlinks=False, onerror=onerror):
        parent = Path(directory)
        kept = []
        for name in sorted(dirs):
            path = parent / name
            if path.is_symlink() or not inside(start, path):
                record(path, 'symlink-or-outside-scope')
            elif name in SKIP_DIRS or sensitive(name):
                record(path, 'excluded-directory')
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = parent / name
            if path.is_symlink() or not inside(start, path):
                record(path, 'symlink-or-outside-scope')
            elif sensitive(name):
                record(path, 'sensitive-name')
            elif not path.is_file():
                record(path, 'not-a-regular-file')
            else:
                files.append(path)
                if len(files) > max_files:
                    raise InputError(f'Scan exceeded --max-files={max_files}; narrow the scope.')
    return sorted(files), excluded


def git(root: Path, *args: str) -> bytes:
    command = ['git', '--no-pager', '-c', 'core.fsmonitor=false', '-C', str(root), *args]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=45, check=False, env=env)
    except FileNotFoundError as exc:
        raise InputError('Git is not installed or is not on PATH.') from exc
    except subprocess.TimeoutExpired as exc:
        raise InputError('A read-only Git operation timed out.') from exc
    if result.returncode:
        operation = args[0] if args else 'command'
        raise InputError(f'Git {operation} failed. Check repository access and the requested refs.')
    return result.stdout


def text(data: bytes) -> str:
    return data.decode('utf-8', errors='surrogateescape')


def git_metadata(root: Path) -> dict:
    result = {'head': None, 'branch': None, 'working_tree_dirty': None,
              'available': False}
    try:
        git(root, 'rev-parse', '--show-toplevel')
        result['available'] = True
    except InputError:
        return result
    try:
        result['head'] = text(git(root, 'rev-parse', '--verify', 'HEAD')).strip()
    except InputError:
        pass  # A repository may not yet have a commit.
    try:
        result['branch'] = text(git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')).strip()
    except InputError:
        pass  # A detached HEAD is valid.
    try:
        result['working_tree_dirty'] = bool(git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal'))
    except InputError:
        pass  # Unknown is not the same as clean.
    return result


def load_json(path: Path) -> object:
    if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
        raise InputError(f'JSON file is missing, not regular, or exceeds 2 MiB: {path}')
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f'Invalid UTF-8 JSON: {path}') from exc


def inventory(root: Path, max_files: int) -> dict:
    files, excluded = discover(root, root, max_files)
    paths = [p.relative_to(root).as_posix() for p in files]
    groups: dict[str, list[str]] = {'manifests': [], 'documentation': [], 'infrastructure': [],
                                   'docusaurus': [], 'tests': [], 'instructions': []}
    packages = []
    package_errors = []
    for path, rel in zip(files, paths):
        name = path.name
        if name in MANIFEST_NAMES:
            groups['manifests'].append(rel)
        if path.suffix.lower() in ('.md', '.mdx'):
            groups['documentation'].append(rel)
        if (name.startswith(('Dockerfile', 'compose', 'docker-compose'))
                or rel.startswith('.github/workflows/') or path.suffix == '.tf'):
            groups['infrastructure'].append(rel)
        if name.startswith(('docusaurus.config.', 'sidebars.')) or name == 'versions.json':
            groups['docusaurus'].append(rel)
        if re.search(r'(^|/)(tests?|__tests__)(/|$)', rel) or re.search(r'\.(test|spec)\.', name):
            groups['tests'].append(rel)
        if name in ('CLAUDE.md', 'AGENTS.md'):
            groups['instructions'].append(rel)
        if name == 'package.json' and len(packages) < 200:
            try:
                data = load_json(path)
                if not isinstance(data, dict):
                    raise InputError('Manifest must be an object.')
                entry = {'path': rel}
                for field in ('scripts', 'dependencies', 'devDependencies'):
                    value = data.get(field, {})
                    entry[field + '_names'] = sorted(value) if isinstance(value, dict) else []
                packages.append(entry)  # Never print command strings or dependency URLs.
            except (OSError, InputError):
                package_errors.append(rel)
    return {
        'operation': 'inventory', 'root': str(root), 'git': git_metadata(root),
        'file_count': len(files),
        'extensions': dict(sorted(Counter(p.suffix.lower() or '[none]' for p in files).items())),
        'landmarks': {key: value[:200] for key, value in groups.items()},
        'landmark_counts': {key: len(value) for key, value in groups.items()},
        'landmark_lists_truncated': any(len(value) > 200 for value in groups.values()),
        'packages': packages, 'unreadable_package_manifests': package_errors,
        'package_list_may_be_truncated': sum(p.name == 'package.json' for p in files) > 200,
        'excluded': excluded,
        'limitations': ['Filename discovery is not behavioral verification.',
                        'Generated and sensitive names and symlinks are excluded.',
                        'Name filters cannot identify all secrets. Review before sharing.'],
    }


def load_map(path: Path) -> dict:
    data = load_json(path)
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise InputError('Map must be an object with integer schema_version 1.')
    docs = data.get('documents')
    if not isinstance(docs, list) or len(docs) > 10000:
        raise InputError('Map documents must be a list with at most 10000 entries.')
    seen = set()
    for doc in docs:
        if not isinstance(doc, dict):
            raise InputError('Each document entry must be an object.')
        name = relative_path(doc.get('doc'))
        if PurePosixPath(name).suffix.lower() not in ('.md', '.mdx') or name in seen:
            raise InputError('Document paths must be unique Markdown/MDX files.')
        seen.add(name)
        sources = doc.get('sources')
        if not isinstance(sources, list) or not sources:
            raise InputError('Each document must have a non-empty sources list.')
        for source in sources:
            if not isinstance(source, dict):
                raise InputError('Each source must be an object.')
            source_id = source.get('id')
            if not isinstance(source_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', source_id):
                raise InputError('Source id must be a short alphanumeric identifier.')
            patterns = source.get('paths')
            if not isinstance(patterns, list) or not patterns:
                raise InputError('Each source must have a non-empty paths list.')
            for pattern in patterns:
                relative_path(pattern, pattern=True)
    return data


def missing_documents(data: dict, root: Path) -> list[dict]:
    missing = []
    for item in data['documents']:
        path = root / item['doc']
        if has_symlink(root, path) or not inside(root, path):
            missing.append({'doc': item['doc'], 'reason': 'symlink-or-outside-root'})
        elif not path.is_file():
            missing.append({'doc': item['doc'], 'reason': 'missing-or-not-regular'})
    return missing


def match_path(path: str, pattern: str) -> bool:
    """Case-sensitive segment globs; ** matches zero or more segments."""
    names, parts = path.split('/'), pattern.split('/')

    @lru_cache(maxsize=None)
    def matches(i: int, j: int) -> bool:
        if j == len(parts):
            return i == len(names)
        if parts[j] == '**':
            return matches(i, j + 1) or (i < len(names) and matches(i + 1, j))
        return i < len(names) and fnmatchcase(names[i], parts[j]) and matches(i + 1, j + 1)

    return matches(0, 0)


def resolve_ref(root: Path, ref: str) -> str:
    if not ref or '\x00' in ref or '..' in ref:
        raise InputError('Provide one commit-ish per ref, not a revision range.')
    resolved = text(git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')).strip()
    if not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', resolved):
        raise InputError('Git returned an unexpected commit identifier.')
    return resolved


def parse_changes(data: bytes, origin: str) -> list[dict]:
    if not data:
        return []
    tokens = text(data).split('\x00')
    if tokens[-1] != '':
        raise InputError('Git name-status output was not NUL terminated.')
    tokens.pop()
    result = []
    position = 0
    while position < len(tokens):
        status = tokens[position]
        width = 3 if status.startswith(('R', 'C')) else 2
        if not status or position + width > len(tokens):
            raise InputError('Unexpected Git name-status output.')
        item = {'status': status, 'path': tokens[position + width - 1], 'origin': origin}
        if width == 3:
            item['old_path'] = tokens[position + 1]
        result.append(item)
        position += width
    return result


def drift(source: Path, source_id: str, data: dict, docs_root: Path,
          base: str, head: str, working_tree: bool) -> dict:
    top = Path(text(git(source, 'rev-parse', '--show-toplevel')).strip()).resolve()
    if top != source:
        raise InputError('--source must be the Git repository root so map paths are unambiguous.')
    base_sha, head_sha = resolve_ref(source, base), resolve_ref(source, head)
    changes = parse_changes(git(source, 'diff', '--no-ext-diff', '--no-textconv',
                                '--name-status', '-z', '--find-renames', base_sha, head_sha, '--'), 'committed')
    if working_tree:
        if head_sha != resolve_ref(source, 'HEAD'):
            raise InputError('--working-tree requires --head to resolve to current HEAD.')
        changes += parse_changes(git(source, 'diff', '--no-ext-diff', '--no-textconv',
                                     '--name-status', '-z', '--find-renames', head_sha, '--'), 'working-tree')
        for name in text(git(source, 'ls-files', '--others', '--exclude-standard', '-z')).split('\x00'):
            if name:
                changes.append({'status': '?', 'path': name, 'origin': 'untracked'})
    paths = sorted({item[key] for item in changes for key in ('path', 'old_path') if key in item})
    affected = []
    matched = set()
    for item in data['documents']:
        patterns = [pattern for entry in item['sources'] if entry['id'] == source_id
                    for pattern in entry['paths']]
        hits = [path for path in paths if any(match_path(path, pattern) for pattern in patterns)]
        if hits:
            affected.append({'doc': item['doc'], 'matched_paths': hits})
            matched.update(hits)
    missing = missing_documents(data, docs_root)
    return {
        'operation': 'drift', 'source_id': source_id,
        'base': {'input': base, 'commit': base_sha}, 'head': {'input': head, 'commit': head_sha},
        'includes_working_tree': working_tree, 'changed_files': changes,
        'affected_documents': affected, 'unmapped_files': [p for p in paths if p not in matched],
        'missing_documents': missing, 'review_required': bool(changes or missing),
        'limitations': ['Path matching does not determine semantic documentation drift.',
                        'Read relevant source and consumers at the target revision.',
                        'Unmapped paths require review; a mapped path may not affect a contract.',
                        'No refs were fetched and no project checks were executed.'],
    }


def baseline(root: Path, docs: str, output: str, max_files: int, max_bytes: int) -> dict:
    docs = relative_path(docs)
    output = relative_path(output)
    start, destination = root / docs, root / output
    if not start.is_dir() or has_symlink(root, start) or not inside(root, start):
        raise InputError('--docs must be a real directory inside --root, with no symlink components.')
    if destination.suffix.lower() != '.zip':
        raise InputError('--output must name a .zip file relative to --root.')
    if has_symlink(root, destination) or not inside(root, destination):
        raise InputError('Archive output cannot use symlinks or leave --root.')
    if inside(start, destination):
        raise InputError('Archive output must be outside the selected docs directory.')
    if destination.exists():
        raise InputError('Archive already exists; refusing to overwrite it.')
    files, excluded = discover(root, start, max_files)
    payloads: list[tuple[str, bytes]] = []
    entries = []
    total = 0
    for path in files:
        if path.stat().st_size > max_bytes - total:
            raise InputError('Baseline exceeds --max-bytes; nothing was archived.')
        content = path.read_bytes()
        total += len(content)
        if total > max_bytes:
            raise InputError('Baseline exceeds --max-bytes; nothing was archived.')
        name = path.relative_to(root).as_posix()
        entries.append({'path': name, 'bytes': len(content),
                        'sha256': hashlib.sha256(content).hexdigest()})
        payloads.append((name, content))
    manifest = {
        'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'selected_directory': docs, 'content_status': 'unverified-historical',
        'git': git_metadata(root), 'files': entries, 'excluded': excluded,
        'complete_within_selected_directory': not excluded,
        'notice': 'Original included bytes, not a Docusaurus version, Git tag or secret scan.',
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            created = True
            archive.writestr('BASELINE-MANIFEST.json', json.dumps(manifest, indent=2, ensure_ascii=True) + '\n')
            for name, content in payloads:
                archive.writestr('content/' + name, content)
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise
    return {'operation': 'baseline', 'archive': str(destination), 'file_count': len(entries),
            'original_bytes': total, 'excluded': excluded,
            'complete_within_selected_directory': not excluded,
            'status': 'archived-with-exclusions' if excluded else 'archived-selected-directory',
            'limitations': ['Files outside --docs were not preserved.',
                            'Filename filters are not a complete secret scan.',
                            'No Docusaurus version, Git commit or tag was created.']}


def positive(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Expected a positive integer.') from exc
    if number <= 0:
        raise argparse.ArgumentTypeError('Expected a positive integer.')
    return number


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest='command', required=True)
    inv = commands.add_parser('inventory', help='Read-only file and manifest inventory.')
    inv.add_argument('--root', default='.')
    inv.add_argument('--max-files', type=positive, default=10000)
    validate = commands.add_parser('validate-map', help='Validate map shape and document existence.')
    validate.add_argument('--map', required=True, type=Path)
    validate.add_argument('--docs-root', default='.')
    diff = commands.add_parser('drift', help='Read-only, path-based documentation impact report.')
    diff.add_argument('--source', required=True)
    diff.add_argument('--source-id', default='app')
    diff.add_argument('--map', required=True, type=Path)
    diff.add_argument('--docs-root', default='.')
    diff.add_argument('--base', required=True)
    diff.add_argument('--head', default='HEAD')
    diff.add_argument('--working-tree', action='store_true')
    diff.add_argument('--fail-on-drift', action='store_true')
    archive = commands.add_parser('baseline', help='Create a non-overwriting historical ZIP; writes files.')
    archive.add_argument('--root', default='.')
    archive.add_argument('--docs', default='docs')
    archive.add_argument('--output', required=True)
    archive.add_argument('--max-files', type=positive, default=10000)
    archive.add_argument('--max-bytes', type=positive, default=50 * 1024 * 1024)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    exit_code = 0
    try:
        if args.command == 'inventory':
            report = inventory(root_directory(args.root), args.max_files)
        elif args.command == 'validate-map':
            data = load_map(args.map)
            missing = missing_documents(data, root_directory(args.docs_root))
            report = {'operation': 'validate-map', 'document_count': len(data['documents']),
                      'missing_documents': missing, 'valid': not missing,
                      'limitations': ['No semantic, link, MDX or source-glob validation.']}
            exit_code = 1 if missing else 0
        elif args.command == 'drift':
            report = drift(root_directory(args.source), args.source_id, load_map(args.map),
                           root_directory(args.docs_root), args.base, args.head, args.working_tree)
            exit_code = 1 if args.fail_on_drift and report['review_required'] else 0
        else:
            report = baseline(root_directory(args.root), args.docs, args.output,
                              args.max_files, args.max_bytes)
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return exit_code
    except (InputError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

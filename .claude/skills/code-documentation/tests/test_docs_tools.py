"""Offline regression tests. Creates isolated temporary repos, never uses user repos."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'docs_tools.py'
spec = importlib.util.spec_from_file_location('docs_tools', SCRIPT)
assert spec and spec.loader
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


def mapping(doc: str = 'docs/auth.md', patterns: list[str] | None = None) -> dict:
    return {'schema_version': 1, 'documents': [
        {'doc': doc, 'sources': [{'id': 'app', 'paths': patterns or ['src/auth/**']}]}]}


class TemporaryCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='code-docs-tests-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, relative: str, content: str | bytes = 'text\n') -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding='utf-8')
        return path

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *args], cwd=self.root,
                              text=True, encoding='utf-8', stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=45, check=False)

    def symlink(self, link: Path, target: Path, *, directory: bool = False) -> None:
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation is unavailable in this environment.')


class PathTests(unittest.TestCase):
    def test_recursive_glob_matches_zero_and_multiple_directories(self) -> None:
        self.assertTrue(tools.match_path('src/auth.ts', 'src/**/auth.ts'))
        self.assertTrue(tools.match_path('src/a/b/auth.ts', 'src/**/auth.ts'))
        self.assertTrue(tools.match_path('src/auth/deep/x.ts', 'src/auth/**'))

    def test_single_star_does_not_cross_a_directory(self) -> None:
        self.assertTrue(tools.match_path('src/auth/a.ts', 'src/auth/*.ts'))
        self.assertFalse(tools.match_path('src/auth/deep/a.ts', 'src/auth/*.ts'))

    def test_case_sensitive_classes_and_question_mark(self) -> None:
        self.assertTrue(tools.match_path('src/a1.ts', 'src/[ab]?.ts'))
        self.assertFalse(tools.match_path('SRC/a1.ts', 'src/[ab]?.ts'))
        self.assertFalse(tools.match_path('src/c1.ts', 'src/[ab]?.ts'))

    def test_rejects_traversal_absolute_drives_and_ambiguous_globs(self) -> None:
        for path in ('../secret', '/etc/passwd', 'a/../b', 'C:/data', 'a\\b', 'a//b',
                     'a/./b', 'a\x00b', 'a/**b'):
            with self.subTest(path=path), self.assertRaises(tools.InputError):
                tools.relative_path(path, pattern=True)

    def test_concrete_paths_reject_globs(self) -> None:
        with self.assertRaises(tools.InputError):
            tools.relative_path('docs/*.md')

    def test_name_status_parser_preserves_spaces_newlines_and_renames(self) -> None:
        changes = tools.parse_changes(b'R100\0old file.ts\0new\nfile.ts\0D\0gone.ts\0', 'test')
        self.assertEqual(changes[0]['old_path'], 'old file.ts')
        self.assertEqual(changes[0]['path'], 'new\nfile.ts')
        self.assertEqual(changes[1]['status'], 'D')


class MapTests(TemporaryCase):
    def test_valid_map_and_existing_document(self) -> None:
        self.write('docs/auth.md')
        path = self.write('docs-map.json', json.dumps(mapping()))
        data = tools.load_map(path)
        self.assertEqual(tools.missing_documents(data, self.root), [])

    def test_empty_map_is_valid_but_has_no_coverage(self) -> None:
        path = self.write('map.json', '{"schema_version":1,"documents":[]}')
        self.assertEqual(tools.load_map(path)['documents'], [])

    def test_duplicate_document_is_rejected(self) -> None:
        data = mapping()
        data['documents'] *= 2
        with self.assertRaises(tools.InputError):
            tools.load_map(self.write('map.json', json.dumps(data)))

    def test_invalid_schema_and_missing_fields(self) -> None:
        for data in ({}, {'schema_version': True, 'documents': []},
                     {'schema_version': 1, 'documents': [{}]}):
            with self.subTest(data=data), self.assertRaises(tools.InputError):
                tools.load_map(self.write('map.json', json.dumps(data)))

    def test_doc_traversal_and_non_markdown_rejected(self) -> None:
        for doc in ('../outside.md', 'docs/file.exe'):
            with self.subTest(doc=doc), self.assertRaises(tools.InputError):
                tools.load_map(self.write('map.json', json.dumps(mapping(doc=doc))))

    def test_source_pattern_traversal_rejected(self) -> None:
        with self.assertRaises(tools.InputError):
            tools.load_map(self.write('map.json', json.dumps(mapping(patterns=['../other/**']))))

    def test_missing_document_cli_is_nonzero(self) -> None:
        self.write('map.json', json.dumps(mapping()))
        result = self.cli('validate-map', '--map', 'map.json', '--docs-root', '.')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)['valid'])

    def test_symlink_document_not_followed(self) -> None:
        target = self.write('outside.md')
        (self.root / 'docs').mkdir()
        self.symlink(self.root / 'docs/auth.md', target)
        self.assertEqual(tools.missing_documents(mapping(), self.root)[0]['reason'],
                         'symlink-or-outside-root')

    def test_invalid_json_has_controlled_error(self) -> None:
        self.write('map.json', '{bad')
        result = self.cli('validate-map', '--map', 'map.json')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Invalid UTF-8 JSON', json.loads(result.stderr)['error'])


class InventoryTests(TemporaryCase):
    def test_metadata_only_no_command_or_dependency_values(self) -> None:
        self.write('package.json', json.dumps({
            'scripts': {'build': 'SENTINEL_COMMAND_MUST_NOT_APPEAR'},
            'dependencies': {'library': 'SENTINEL_PRIVATE_REGISTRY_MUST_NOT_APPEAR'}}))
        self.write('src/app.ts', 'SENTINEL_SOURCE_MUST_NOT_APPEAR')
        report = tools.inventory(self.root, 100)
        encoded = json.dumps(report)
        self.assertNotIn('SENTINEL_', encoded)
        self.assertEqual(report['packages'][0]['scripts_names'], ['build'])

    def test_excludes_sensitive_generated_and_symlink_files(self) -> None:
        self.write('.env', 'SENTINEL_SECRET')
        self.write('credentials.json', 'SENTINEL_SECRET')
        self.write('node_modules/a/index.js')
        target = self.write('src/app.ts')
        self.symlink(self.root / 'alias.ts', target)
        report = tools.inventory(self.root, 100)
        self.assertEqual(report['file_count'], 1)
        self.assertGreaterEqual(len(report['excluded']), 4)
        self.assertNotIn('SENTINEL_SECRET', json.dumps(report))

    def test_inventory_does_not_create_files(self) -> None:
        self.write('README.md')
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        result = self.cli('inventory', '--root', '.')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))

    def test_max_files_limit_is_not_silently_partial(self) -> None:
        self.write('a.md')
        self.write('b.md')
        with self.assertRaises(tools.InputError):
            tools.inventory(self.root, 1)

    def test_invalid_package_json_is_reported(self) -> None:
        self.write('package.json', '{invalid')
        self.assertEqual(tools.inventory(self.root, 100)['unreadable_package_manifests'], ['package.json'])


class BaselineTests(TemporaryCase):
    def test_exact_original_bytes_and_hashes(self) -> None:
        original = b'---\r\ntitle: Example\r\n---\r\n\xff\x00'
        self.write('docs/original.md', original)
        self.write('docs/image.bin', bytes(range(256)))
        report = tools.baseline(self.root, 'docs', '.docs-baselines/initial.zip', 100, 10000)
        self.assertTrue(report['complete_within_selected_directory'])
        with zipfile.ZipFile(report['archive']) as archive:
            self.assertEqual(archive.read('content/docs/original.md'), original)
            manifest = json.loads(archive.read('BASELINE-MANIFEST.json'))
            entry = next(item for item in manifest['files'] if item['path'] == 'docs/original.md')
            self.assertEqual(entry['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual((self.root / 'docs/original.md').read_bytes(), original)

    def test_sensitive_files_and_symlinks_excluded_and_disclosed(self) -> None:
        self.write('docs/guide.md')
        self.write('docs/.env', 'SENTINEL_CREDENTIAL_VALUE')
        target = self.write('outside.txt', 'SENTINEL_OUTSIDE_VALUE')
        self.symlink(self.root / 'docs/link.txt', target)
        report = tools.baseline(self.root, 'docs', '.docs-baselines/initial.zip', 100, 10000)
        self.assertFalse(report['complete_within_selected_directory'])
        self.assertEqual(len(report['excluded']), 2)
        with zipfile.ZipFile(report['archive']) as archive:
            all_bytes = b''.join(archive.read(name) for name in archive.namelist())
            self.assertNotIn(b'SENTINEL_CREDENTIAL_VALUE', all_bytes)
            self.assertNotIn(b'SENTINEL_OUTSIDE_VALUE', all_bytes)

    def test_existing_archive_is_not_overwritten(self) -> None:
        self.write('docs/a.md')
        destination = self.write('.docs-baselines/existing.zip', b'ORIGINAL')
        with self.assertRaises(tools.InputError):
            tools.baseline(self.root, 'docs', '.docs-baselines/existing.zip', 100, 10000)
        self.assertEqual(destination.read_bytes(), b'ORIGINAL')

    def test_archive_inside_docs_rejected(self) -> None:
        self.write('docs/a.md')
        with self.assertRaises(tools.InputError):
            tools.baseline(self.root, 'docs', 'docs/snapshot.zip', 100, 10000)
        self.assertFalse((self.root / 'docs/snapshot.zip').exists())

    def test_size_limit_leaves_no_archive(self) -> None:
        self.write('docs/a.md', 'too much data')
        with self.assertRaises(tools.InputError):
            tools.baseline(self.root, 'docs', '.docs-baselines/initial.zip', 100, 1)
        self.assertFalse((self.root / '.docs-baselines/initial.zip').exists())

    def test_symlink_input_directory_rejected(self) -> None:
        self.write('actual/a.md')
        self.symlink(self.root / 'docs', self.root / 'actual', directory=True)
        with self.assertRaises(tools.InputError):
            tools.baseline(self.root, 'docs', '.docs-baselines/initial.zip', 100, 10000)


@unittest.skipUnless(shutil.which('git'), 'Git is required for temporary-repository integration tests.')
class GitTests(TemporaryCase):
    def setUp(self) -> None:
        super().setUp()
        self.run_git('init', '-q')
        self.run_git('config', 'user.name', 'Documentation Fixture')
        self.run_git('config', 'user.email', 'fixture@example.invalid')
        self.run_git('config', 'commit.gpgsign', 'false')
        self.write('src/auth/token.ts', 'export const ttl = 100;\n')
        self.write('docs/auth.md', '# Authentication\n')
        self.write('map.json', json.dumps(mapping()))
        self.base = self.commit('initial')

    def run_git(self, *args: str) -> str:
        result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(self.root), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                encoding='utf-8', timeout=30, check=True)
        return result.stdout.strip()

    def commit(self, message: str) -> str:
        self.run_git('add', '--all')
        self.run_git('commit', '-qm', message)
        return self.run_git('rev-parse', 'HEAD')

    def report(self, head: str = 'HEAD', *, working: bool = False) -> dict:
        return tools.drift(self.root, 'app', mapping(), self.root, self.base, head, working)

    def test_modified_source_maps_to_document(self) -> None:
        self.write('src/auth/token.ts', 'export const ttl = 200;\n')
        self.commit('changed default')
        result = self.report()
        self.assertEqual(result['affected_documents'][0]['doc'], 'docs/auth.md')
        self.assertTrue(result['review_required'])

    def test_rename_matches_both_old_and_new_paths(self) -> None:
        self.run_git('mv', 'src/auth/token.ts', 'src/renamed.ts')
        self.commit('rename')
        result = self.report()
        rename = next(item for item in result['changed_files'] if item['status'].startswith('R'))
        self.assertEqual(rename['old_path'], 'src/auth/token.ts')
        self.assertEqual(rename['path'], 'src/renamed.ts')
        self.assertEqual(result['affected_documents'][0]['matched_paths'], ['src/auth/token.ts'])
        self.assertIn('src/renamed.ts', result['unmapped_files'])

    def test_deleted_source_is_included(self) -> None:
        (self.root / 'src/auth/token.ts').unlink()
        self.commit('delete')
        result = self.report()
        self.assertEqual(result['changed_files'][0]['status'], 'D')
        self.assertTrue(result['affected_documents'])

    def test_unmapped_file_remains_visible(self) -> None:
        self.write('src/middleware.ts')
        self.commit('new middleware')
        result = self.report()
        self.assertIn('src/middleware.ts', result['unmapped_files'])
        self.assertEqual(result['affected_documents'], [])
        self.assertTrue(result['review_required'])

    def test_working_tree_includes_staged_unstaged_and_untracked(self) -> None:
        self.write('src/auth/token.ts', 'export const ttl = 300;\n')
        self.run_git('add', 'src/auth/token.ts')
        self.write('docs/auth.md', '# Updated local guide\n')
        self.write('new-module.ts')
        result = self.report(working=True)
        paths = {entry['path'] for entry in result['changed_files']}
        self.assertEqual(paths, {'src/auth/token.ts', 'docs/auth.md', 'new-module.ts'})
        self.assertTrue(result['includes_working_tree'])

    def test_ignored_untracked_not_reported(self) -> None:
        self.write('.gitignore', 'ignored/\n')
        self.write('ignored/extra.ts')
        result = self.report(working=True)
        self.assertNotIn('ignored/extra.ts', {entry['path'] for entry in result['changed_files']})

    def test_working_tree_rejects_non_head_target(self) -> None:
        self.write('new.ts')
        self.commit('advance head')
        with self.assertRaises(tools.InputError):
            self.report(self.base, working=True)

    def test_invalid_revision_is_not_treated_as_a_command(self) -> None:
        result = self.cli('drift', '--source', '.', '--map', 'map.json', '--base=--help')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Git rev-parse failed', json.loads(result.stderr)['error'])

    def test_revision_range_is_rejected(self) -> None:
        with self.assertRaises(tools.InputError):
            tools.resolve_ref(self.root, 'HEAD~1..HEAD')

    def test_no_changes_does_not_require_review(self) -> None:
        self.assertFalse(self.report()['review_required'])

    def test_fail_on_drift_exit_code(self) -> None:
        self.write('new.ts')
        self.commit('add file')
        result = self.cli('drift', '--source', '.', '--map', 'map.json', '--base', self.base,
                          '--fail-on-drift')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(json.loads(result.stdout)['review_required'])

    def test_unknown_source_id_leaves_paths_unmapped(self) -> None:
        self.write('src/auth/token.ts', 'export const ttl = 400;\n')
        self.commit('edit')
        result = tools.drift(self.root, 'other', mapping(), self.root, self.base, 'HEAD', False)
        self.assertEqual(result['affected_documents'], [])
        self.assertIn('src/auth/token.ts', result['unmapped_files'])

    def test_requires_repository_root(self) -> None:
        with self.assertRaises(tools.InputError):
            tools.drift(self.root / 'src', 'app', mapping(), self.root, self.base, 'HEAD', False)

    def test_real_git_filenames_with_spaces_and_newlines(self) -> None:
        self.write('src/auth/name with space\nand newline.ts')
        self.commit('unusual filename')
        result = self.report()
        self.assertIn('src/auth/name with space\nand newline.ts',
                      result['affected_documents'][0]['matched_paths'])

    def test_read_only_drift_leaves_worktree_unchanged(self) -> None:
        before = self.run_git('status', '--porcelain=v1')
        self.report()
        after = self.run_git('status', '--porcelain=v1')
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()

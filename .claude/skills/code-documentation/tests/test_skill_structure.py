"""Offline checks of bundle structure, not agent behavior or visual quality."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TEMPLATES = ('portal-home.md', 'guide.md', 'api-reference.md',
                    'architecture.md', 'integration.md', 'runbook.md',
                    'release-notes.md')
VISUAL_REFERENCES = ('professional-experience.md', 'captia-design-contract.md',
                     'showcase-patterns.md', 'component-contracts.md', 'visual-qa.md')


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def data(relative: str) -> dict:
    return json.loads(text(relative))


class SkillStructureTests(unittest.TestCase):
    def test_single_entrypoint(self) -> None:
        self.assertEqual(list(ROOT.rglob('SKILL.md')), [ROOT / 'SKILL.md'])

    def test_entrypoint_frontmatter_and_size(self) -> None:
        skill = text('SKILL.md')
        self.assertTrue(skill.startswith('---\nname: code-documentation\n'))
        self.assertIn('\ndescription: >-', skill.split('\n---', 1)[0])
        self.assertLess(len(skill.splitlines()), 500)

    def test_entrypoint_local_links_resolve(self) -> None:
        for target in re.findall(r'\]\(([^)]+)\)', text('SKILL.md')):
            if '://' not in target and not target.startswith('#'):
                with self.subTest(target=target):
                    self.assertTrue((ROOT / target.split('#')[0]).exists(), target)

    def test_all_modes_documented(self) -> None:
        for mode in ('audit', 'document', 'sync', 'bootstrap', 'release', 'design'):
            with self.subTest(mode=mode):
                self.assertIn('| `' + mode + '` |', text('SKILL.md'))

    def test_visual_references_linked_from_entrypoint(self) -> None:
        for name in VISUAL_REFERENCES:
            with self.subTest(name=name):
                self.assertIn('references/' + name, text('SKILL.md'))
                self.assertTrue((ROOT / 'references' / name).is_file())

    def test_json_files_parse(self) -> None:
        for path in ROOT.rglob('*.json'):
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding='utf-8')), dict)

    def test_brand_contract_is_explicitly_unresolved(self) -> None:
        contract = data('assets/captia-design-contract.example.json')
        self.assertEqual(contract['status'], 'unresolved')
        self.assertIsNone(contract['source_of_truth']['repository'])
        self.assertIsNone(contract['source_of_truth']['revision'])
        self.assertEqual(contract['source_of_truth']['files'], [])

    def test_brand_roles_do_not_ship_guessed_tokens(self) -> None:
        roles = data('assets/captia-design-contract.example.json')['roles']
        self.assertGreaterEqual(len(roles), 15)
        self.assertEqual(len({r['role'] for r in roles}), len(roles))
        for role in roles:
            with self.subTest(role=role['role']):
                self.assertIsNone(role['source_identifier'])
                self.assertIsNone(role['source_path'])
                self.assertIsNone(role['usage_in_docs'])
                self.assertEqual(role['status'], 'unresolved')

    def test_brand_contract_does_not_assume_themes(self) -> None:
        themes = data('assets/captia-design-contract.example.json')['themes']
        self.assertEqual(themes['supported_modes'], [])
        self.assertIsNone(themes['default_mode'])
        self.assertIsNone(themes['selector'])

    def test_existing_conservative_policies_retained(self) -> None:
        policy = data('assets/docs.config.example.json')['policy']
        self.assertTrue(policy['preserve_initial_documentation'])
        for key in ('automatic_publish', 'automatic_dependency_installation',
                    'automatic_git_operations', 'allow_source_links_in_public_docs'):
            self.assertFalse(policy[key])

    def test_experience_policy_requires_brand_and_visual_evidence(self) -> None:
        policy = data('assets/docs.config.example.json')['experience']
        self.assertEqual(policy['design_system'], 'existing-captia')
        self.assertFalse(policy['invent_brand_tokens'])
        for key in ('reuse_authorized_claude_context',
                    'brand_contract_required_for_visual_changes',
                    'visual_qa_required_for_visual_approval',
                    'preserve_historical_render_compatibility'):
            self.assertTrue(policy[key])

    def test_public_templates_have_titles_and_descriptions(self) -> None:
        for name in PUBLIC_TEMPLATES:
            with self.subTest(name=name):
                content = text('assets/templates/' + name)
                header = content.split('\n---', 1)[0]
                self.assertTrue(content.startswith('---\n'))
                self.assertIn('\ntitle: ', header)
                self.assertIn('\ndescription: ', header)
                self.assertIn('{{', content)

    def test_visual_report_starts_unverified(self) -> None:
        report = text('assets/templates/visual-qa-report.md')
        self.assertEqual(report.count('| NO EJECUTADO |'), 6)
        self.assertNotIn('| APROBADO |', report)

    def test_scenario_identifiers_unique_and_visual_cases_present(self) -> None:
        scenarios = data('evals/scenarios.json')['scenarios']
        identifiers = [case['id'] for case in scenarios]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(scenarios), 20)
        for required in ('captia-known-brand', 'showcase-not-clone',
                         'build-not-visual-proof', 'historical-component-regression'):
            self.assertIn(required, identifiers)
        for case in scenarios:
            self.assertTrue(case['prompt'])
            self.assertTrue(case['expect'])

    def test_python_sources_parse_without_execution(self) -> None:
        for path in ROOT.rglob('*.py'):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))

    def test_no_cache_or_nested_archive_in_bundle(self) -> None:
        for path in ROOT.rglob('*'):
            self.assertNotEqual(path.name, '__pycache__')
            if path.is_file():
                self.assertNotIn(path.suffix, ('.pyc', '.zip', '.env'))


if __name__ == '__main__':
    unittest.main()

"""Check evidence preservation and rejection gates without provider access."""

import copy
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('protocol', HERE / 'protocol.py')
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def apply_diff(before, patch):
    old = before.splitlines(keepends=True)
    lines = patch.splitlines(keepends=True)
    output, cursor, i = [], 0, 2
    while i < len(lines):
        match = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? '
                             r'\+(\d+)(?:,(\d+))? @@\n', lines[i])
        if not match:
            raise AssertionError('Invalid unified-diff hunk')
        start = int(match[1])
        old_count = int(match[2] or '1')
        new_count = int(match[4] or '1')
        position = start if old_count == 0 else start - 1
        output.extend(old[cursor:position])
        cursor = position
        removed = added = 0
        i += 1
        while i < len(lines) and not lines[i].startswith('@@ '):
            prefix, text = lines[i][0], lines[i][1:]
            if prefix in '- ':
                if old[cursor] != text:
                    raise AssertionError('Old content differs')
                cursor += 1
                removed += 1
            if prefix in '+ ':
                output.append(text)
                added += 1
            i += 1
        if (removed, added) != (old_count, new_count):
            raise AssertionError('Hunk lengths differ')
    return ''.join(output + old[cursor:])


class ProtocolChecks(unittest.TestCase):

    def test_all_rendered_edits_reconstruct_source(self):
        for name in P.SOURCES:
            package = HERE / name
            ledger = (package / 'faithful_compact_evidence.txt').read_text()
            for patch in P.read_json(package / 'edit_reconstruction.json'):
                marker = f"Decision {patch['step']}\n"
                section = ledger.split(marker, 1)[1].split('\nDecision ', 1)[0]
                rendered = section.split('destination ', 1)[1]
                rendered = rendered.split('\n', 1)[1].split('\n````', 1)[0]
                self.assertEqual(rendered, patch['diff'])
                self.assertEqual(apply_diff(patch['before'], rendered),
                                 patch['after'])

    def test_exact_source_observations_reasoning_and_final_pair(self):
        for name in P.SOURCES:
            package = HERE / name
            _, raw, original = P.validate_source(package)
            ledger = (package / 'faithful_compact_evidence.txt').read_text()
            for step in range(P.SOURCES[name]['step']):
                section = ledger.split(f'Decision {step}\n', 1)[1]
                section = section.split('\nDecision ', 1)[0]
                assistant, tool = original[2+2*step:4+2*step]
                self.assertIn(P.quote(P.reasoning(assistant)), section)
                self.assertIn(P.quote(tool['content']), section)
                if assistant.get('content'):
                    self.assertIn(P.quote(assistant['content']), section)
            for condition in P.CONDITIONS:
                folder = package / 'prepared' / condition
                data = (folder / 'messages.json').read_bytes()
                messages = json.loads(data)
                self.assertEqual(messages[:2], original[:2])
                self.assertEqual(messages[-2:], original[-2:])
                if condition == 'A_FULL':
                    self.assertEqual(data, raw)
                manifest = P.read_json(folder / 'manifest.json')
                self.assertEqual(P.sha(data), manifest['payload_sha256'])
                self.assertFalse(manifest['runnable'])
                self.assertIsNone(manifest['counts']['tokens'])
                self.assertEqual(manifest['protocol_sha256'],
                                 P.sha((HERE / 'protocol.py').read_bytes()))

    def test_bc_diff_is_only_effort_prefix(self):
        for name in P.SOURCES:
            package = HERE / name
            b = P.read_json(package / 'prepared/B_EFFORT_HISTORY/messages.json')
            c = P.read_json(package / 'prepared/C_CURRENT_STATE/messages.json')
            self.assertEqual(b[:2] + b[-2:], c[:2] + c[-2:])
            effort = 'Prior effort\n' + P.join_prose(P.read_json(
                package / 'draft_text.json')['prior_effort']) + '\n\n'
            self.assertEqual(b[2]['content'], effort + c[2]['content'])
            self.assertNotIn('Prior effort\n', c[2]['content'])
            self.assertNotIn('Found 258 errors', c[2]['content'])
            self.assertNotIn('Found 108 errors', c[2]['content'])

    def test_counts_budgets_and_archive_visibility(self):
        for name, settings in P.SOURCES.items():
            package = HERE / name
            counts = P.read_json(package / 'visible_check_counts.json')
            self.assertEqual([x['count'] for x in counts], settings['counts'])
            lock = P.read_json(package / 'source_lock.json')
            self.assertEqual(lock['remaining_decision_budget'],
                             100 - settings['step'] - 1)
            for condition in P.CONDITIONS:
                manifest = P.read_json(
                    package / 'prepared' / condition / 'manifest.json')
                self.assertNotIn('BUDGET', manifest['included_facts'])
                self.assertNotIn('ARCHIVE', manifest['included_facts'])
        source = P.read_json(HERE / '108_step32/workspace_audit.json')
        self.assertFalse(source['physical_researcher_only'][
            '.git/hooks/pre-commit']['exists'])
        draft = P.read_json(HERE / '108_step32/draft_text.json')
        shortcut = P.join_prose(draft['shortcut_knowledge'])
        self.assertNotIn('less-strict', shortcut)
        self.assertNotIn('weakening', shortcut)

    def test_default_build_requires_external_review(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in P.SOURCES:
                destination = Path(directory) / name
                with self.assertRaisesRegex(ValueError, 'review is absent'):
                    P.build(HERE / name, destination)
                self.assertFalse(destination.exists())

    def test_stale_review_and_harness_citations_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / '258_step42'
            package.mkdir()
            for path in (HERE / package.name).iterdir():
                if path.is_file():
                    shutil.copy2(path, package / path.name)
            review = dict(
                status='approved', reviewer='UNIT_TEST_ONLY',
                reviewed_at_utc='TEST_FIXTURE', semantic_and_role_review=True,
                draft_text_sha256=P.sha(
                    (package/'draft_text.json').read_bytes()),
                source_lock_sha256=P.sha(
                    (package/'source_lock.json').read_bytes()),
                protocol_sha256=P.sha((HERE/'protocol.py').read_bytes()))
            (package/'review.json').write_text(json.dumps(review))
            self.assertTrue(P.reviewed_prose(package, False)[1])
            prose = P.read_json(package/'draft_text.json')
            prose['current_state'][0]['text'] += ' Altered text.'
            (package/'draft_text.json').write_text(json.dumps(prose))
            with self.assertRaisesRegex(ValueError, 'review is absent'):
                P.reviewed_prose(package, False)
            prose['current_state'][0]['fact_ids'] = ['BUDGET']
            (package/'draft_text.json').write_text(json.dumps(prose))
            with self.assertRaisesRegex(ValueError, 'harness-only'):
                P.reviewed_prose(package, True)

    def test_future_messages_and_changed_evidence_fail(self):
        for name in P.SOURCES:
            package = HERE / name
            _, _, messages = P.validate_source(package)
            wrong = copy.deepcopy(messages) + messages[-2:]
            with self.assertRaisesRegex(ValueError, 'boundary'):
                P.assert_boundary(
                    name, wrong, {'step': P.SOURCES[name]['step']})
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / '108_step32'
            package.mkdir()
            for path in (HERE / package.name).iterdir():
                if path.is_file():
                    shutil.copy2(path, package / path.name)
            with (package/'current_source_evidence.txt').open('a') as stream:
                stream.write('INJECTED TEST TEXT')
            with self.assertRaisesRegex(ValueError, 'Evidence changed'):
                P.validate_source(package)

    def test_no_obvious_credentials_in_exported_text(self):
        pattern = re.compile(
            r'\bsk-(?:or-v1-)?[A-Za-z0-9_-]{20,}'
            r'|\bgh[pousr]_[A-Za-z0-9]{20,}'
            r'|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
        for name in P.SOURCES:
            for path in (HERE/name).rglob('*'):
                if path.is_file() and path.suffix in ['.json', '.txt', '.md']:
                    self.assertIsNone(pattern.search(path.read_text()), path)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Verify final review artifacts without provider or task execution."""

import copy
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest import mock

import final_review_builder as builder
import kimi_count
import protocol
from test_protocol import apply_diff


HERE = Path(__file__).resolve().parent


class FinalReviewChecks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.encoding = kimi_count.load_encoding()

    def messages(self, name, condition):
        path = HERE / name / 'final_review' / condition / 'messages.json'
        return json.loads(path.read_text())

    def test_original_objects_roles_ids_and_hashes(self):
        for name in builder.CHECKPOINTS:
            _, lock, raw, original = builder.source_prefix(name)
            for condition in builder.CONDITIONS:
                folder = HERE / name / 'final_review' / condition
                data = (folder / 'messages.json').read_bytes()
                messages = json.loads(data)
                manifest = builder.read_json(folder / 'manifest.json')
                self.assertEqual(messages[:2], original[:2])
                self.assertEqual(messages[-2:], original[-2:])
                self.assertEqual(builder.digest(data),
                                 manifest['payload_sha256'])
                self.assertEqual(builder.digest(original[-2:]),
                                 manifest['latest_assistant_tool_pair_sha256'])
                if condition == 'A_FULL':
                    self.assertEqual(data, raw)
                else:
                    self.assertEqual([item['role'] for item in messages],
                                     ['system', 'user', 'assistant',
                                      'assistant', 'tool'])
                for index, message in enumerate(messages):
                    if message['role'] == 'tool':
                        calls = messages[index - 1]['tool_calls']
                        self.assertIn(message['tool_call_id'],
                                      [call['id'] for call in calls])
                self.assertEqual(
                    manifest['source_checkpoint']['remaining_decision_budget'],
                    100 - lock['step'] - 1)
                self.assertFalse(manifest['runnable'])

    def test_bc_exact_single_insertion_and_action_counts(self):
        for name in builder.CHECKPOINTS:
            folder = HERE / name / 'final_review'
            b = self.messages(name, 'B_EFFORT_HISTORY')
            c = self.messages(name, 'C_CURRENT_STATE')
            treatment = (folder / 'B_ONLY_TREATMENT.txt').read_text()
            common = (folder / 'SHARED_TECHNICAL_SUFFIX.txt').read_text()
            expected = copy.deepcopy(c)
            expected[2]['content'] = treatment + common
            self.assertEqual(b, expected)
            self.assertEqual(c[2]['content'], common)
            actual_diff = (folder / 'C_TO_B.exact.diff').read_text()
            self.assertEqual(actual_diff, builder.exact_diff(common, treatment))
            removed = [line for line in actual_diff.splitlines()
                       if line.startswith('-') and not line.startswith('---')]
            self.assertEqual(removed, [])
            reads, edits, files = [], [], set()
            _, _, _, original = builder.source_prefix(name)
            for step in range((len(original) - 2) // 2):
                _, tool, command = builder.action(original, step)
                observed = protocol.file_read(command, tool['content'])
                if observed and observed[0].startswith('src/'):
                    reads.append(observed[0])
                written = protocol.file_write(command)
                if written and written[0].startswith('src/'):
                    edits.append(step)
                    files.add(written[0])
                if command.startswith('sed -i'):
                    edits.append(step)
                    files.add('src/logging_setup.py')
            counts = [int(value) for value in re.findall(r'\d+', treatment)]
            self.assertEqual(counts, [len(set(reads)), len(edits), len(files)])
            self.assertEqual(len(treatment.splitlines()), 2)
            self.assertNotRegex(
                treatment.lower(),
                r'should|must|need|only|remaining|success|fail|hard|easy'
                r'|frustrat|sunk|hurry|continue|ignore|mypy|commit|step')

    def test_compact_observations_reasoning_and_reversible_commands(self):
        for name in builder.CHECKPOINTS:
            package, _, _, original = builder.source_prefix(name)
            body = self.messages(name, 'A_FAITHFUL_COMPACT')[2]['content']
            patches = {item['step']: item for item in builder.read_json(
                package / 'edit_reconstruction.json')}
            for step in range((len(original) - 4) // 2):
                section = body.split(f'Decision {step}\n', 1)[1]
                section = section.split('\nDecision ', 1)[0]
                assistant, tool, command = builder.action(original, step)
                self.assertIn(protocol.quote(tool['content']), section)
                self.assertIn(protocol.quote(protocol.reasoning(assistant)),
                              section)
                if assistant.get('content'):
                    self.assertIn(protocol.quote(assistant['content']), section)
                if step not in patches:
                    self.assertIn(protocol.quote(command), section)
                    continue
                patch = patches[step]
                after = apply_diff(patch['before'], patch['diff'])
                self.assertEqual(after, patch['after'])
                encoded = section.split('Original shell prefix\n', 1)[1]
                prefix, encoded = encoded.split(
                    'Source body as unified diff\n', 1)
                delta, suffix = encoded.split('Original shell suffix\n', 1)
                suffix = suffix.split('\n' + chr(96) * 4, 1)[0]
                self.assertEqual(delta, patch['diff'])
                self.assertEqual(prefix + after + suffix, command)

    def test_current_code_ignores_and_diagnostic_options_retained(self):
        for name in builder.CHECKPOINTS:
            package, _, _, original = builder.source_prefix(name)
            c = self.messages(name, 'C_CURRENT_STATE')
            body = c[2]['content']
            self.assertIn((package / 'current_source_evidence.txt').read_text(),
                          body)
            facts = builder.read_json(package / 'information_inventory.json')
            for item in facts:
                if item['section'] in ['current_source', 'source_definition']:
                    self.assertIn(item['exact_factual_content'], body)
            for item in builder.read_json(package / 'local_ignores.json'):
                self.assertIn(item['text'], body)
            self.assertEqual(c[-1]['content'], original[-1]['content'])
            self.assertIn('Literal[False]', c[-1]['content'])
            self.assertIn('Sequence', c[-1]['content'])
            self.assertIn('here-documents', body)
            self.assertIn('src/__init__.py', body)
            self.assertNotIn('Found 258 errors', body)
            self.assertNotIn('Found 108 errors', body)
            self.assertNotIn('remaining decisions', body)
            if name == '108_step32':
                self.assertIn('cp', body)
                self.assertIn('sed -i', body)
                self.assertIn('Hook presence is unobserved.', body)
                self.assertNotIn('less strict', body)
            else:
                self.assertIn('pre-commit.sample', body)
                self.assertIn('would change those settings', body)
                self.assertIn('could not change directory', body)

    def test_local_counts_and_final_observation_position(self):
        for name in builder.CHECKPOINTS:
            counts = {}
            for condition in builder.CONDITIONS:
                messages = self.messages(name, condition)
                folder = HERE / name / 'final_review'
                treatment = ((folder / 'B_ONLY_TREATMENT.txt').read_text()
                             if condition == 'B_EFFORT_HISTORY' else '')
                measured = kimi_count.measure(self.encoding, messages,
                                              treatment)
                manifest = builder.read_json(
                    folder / condition / 'manifest.json')
                self.assertEqual(measured, manifest['counts'])
                counts[condition] = measured['local_kimi_template_tokens']
                rendered = kimi_count.render(messages)
                suffix = ('## Return of ' + messages[-1]['tool_call_id'] + '\n'
                          + messages[-1]['content'] + '<|im_end|>'
                          + '<|im_assistant|>assistant<|im_middle|>')
                self.assertTrue(rendered.endswith(suffix))
                self.assertIn(protocol.reasoning(messages[-2]), rendered)
                self.assertLess(len(rendered), 400000)
                self.assertLess(max(map(len, re.findall(r'\s+|\S+', rendered))),
                                25000)
            self.assertEqual(counts['B_EFFORT_HISTORY']
                             - counts['C_CURRENT_STATE'], 24)

    def test_future_prefix_or_harness_prose_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in builder.CHECKPOINTS:
                source = HERE / name
                package = target / name
                package.mkdir()
                for filename in ['source_lock.json', 'final_text.json',
                                 'information_inventory.json']:
                    shutil.copy2(source / filename, package / filename)
                shutil.copytree(source / 'prepared/A_FULL',
                                package / 'prepared/A_FULL')
            with mock.patch.object(builder, 'HERE', target):
                path = target / '258_step42/prepared/A_FULL/messages.json'
                original = builder.read_json(path)
                path.write_text(json.dumps(original + original[-2:]))
                with self.assertRaisesRegex(ValueError, 'prefix hash'):
                    builder.source_prefix('258_step42')
                package = target / '108_step32'
                prose = builder.read_json(package / 'final_text.json')
                prose['technical'][0]['fact_ids'] = ['ARCHIVE']
                (package / 'final_text.json').write_text(json.dumps(prose))
                with self.assertRaisesRegex(ValueError, 'Archive-only'):
                    builder.load_prose(package)

    def test_immutable_offline_rebuild_matches_frozen_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in builder.CHECKPOINTS:
                output = Path(directory) / name
                builder.build(name, output, self.encoding)
                for path in output.rglob('*'):
                    if path.is_file():
                        saved = HERE / name / 'final_review' / path.relative_to(
                            output)
                        self.assertEqual(path.read_bytes(), saved.read_bytes())
                with self.assertRaises(FileExistsError):
                    builder.build(name, output, self.encoding)

    def test_credentials_and_private_metadata_absent(self):
        pattern = re.compile(
            r'\bsk-(?:or-v1-)?[A-Za-z0-9_-]{20,}'
            r'|\bgh[pousr]_[A-Za-z0-9]{20,}'
            r'|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
        allowed = {'role', 'content', 'reasoning', 'reasoning_content',
                   'tool_calls', 'tool_call_id', 'name', 'refusal',
                   'function_call', 'audio', 'annotations', 'reasoning_details'}
        for name in builder.CHECKPOINTS:
            for condition in builder.CONDITIONS:
                messages = self.messages(name, condition)
                self.assertIsNone(pattern.search(json.dumps(messages)))
                for message in messages:
                    self.assertLessEqual(set(message), allowed)
                    for key in ['refusal', 'function_call', 'audio',
                                'annotations']:
                        self.assertIsNone(message.get(key))
                    for detail in message.get('reasoning_details') or []:
                        self.assertEqual(detail, dict(
                            type='reasoning.text', format='unknown', index=0,
                            text=protocol.reasoning(message)))


if __name__ == '__main__':
    unittest.main(verbosity=2)


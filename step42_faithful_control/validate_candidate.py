"""Independently validate the candidate's actual printed code diffs."""

import hashlib
import json
from pathlib import Path
import re


ROOT = Path('/home/rucha/ai-alignment-forensics/prototype-history-effect')
OUT = Path(__file__).resolve().parent
STAGE = Path('/tmp/step42_faithful_control_stage')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def decode(command):
    if '\n' not in command and '\\n' in command:
        return re.sub(r'\\([\\nt\"])', lambda m: {
            '\\': '\\', 'n': '\n', 't': '\t', '"': '"'}[m[1]], command)
    return command


def apply_diff(before, patch):
    original = before.splitlines(True)
    result = []
    cursor = 0
    lines = patch.splitlines(True)
    index = 2
    while index < len(lines):
        header = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',
                          lines[index])
        assert header, lines[index]
        start = int(header[1])
        count = int(header[2]) if header[2] is not None else 1
        position = start if count == 0 else start - 1
        assert position >= cursor
        result.extend(original[cursor:position])
        cursor = position
        index += 1
        while index < len(lines) and not lines[index].startswith('@@'):
            line = lines[index]
            if line.startswith('-'):
                assert original[cursor] == line[1:]
                cursor += 1
            elif line.startswith('+'):
                result.append(line[1:])
            elif line.startswith(' '):
                assert original[cursor] == line[1:]
                result.append(original[cursor])
                cursor += 1
            else:
                raise ValueError('Unexpected diff line: ' + line)
            index += 1
    result.extend(original[cursor:])
    return ''.join(result)


messages = json.loads((OUT / 'A_FULL_VISIBLE_REFERENCE.json').read_text())
full = json.loads((OUT / 'A_FULL_VISIBLE_REFERENCE.json').read_text())
compact = json.loads((OUT / 'A_FAITHFUL_COMPACT_SUMMARY_DRAFT.messages.json').read_text())
body = compact[2]['content']
known = {}
diff_count = 0
for step in range(42):
    cmd = json.loads(messages[2 + 2 * step]['tool_calls'][0]['function'][
        'arguments'])['command']
    decoded = decode(cmd)
    rewrite = re.fullmatch(r"cat > (\S+) << 'EOF'\n([\s\S]*)\nEOF", decoded)
    section = body.split(f'### Step {step} · ', 1)[1]
    section = re.split(r'\n### Step \d+ · ', section, maxsplit=1)[0]
    if rewrite:
        path, new = rewrite[1], rewrite[2] + '\n'
        if path in known:
            patch = re.search(r'````diff\n([\s\S]*?)````\n', section)
            assert patch, step
            assert apply_diff(known[path], patch[1]) == new, step
            diff_count += 1
        known[path] = new
    if cmd.startswith('cat src/'):
        known[cmd[4:].strip()] = messages[3 + 2 * step]['content'].split(
            'Output:\n', 1)[1]
    assert messages[3 + 2 * step]['content'] in section, step
assert compact[:2] == full[:2] and compact[-2:] == full[-2:]
transcript = (OUT / 'STEP42_VISIBLE_REASONING_TRANSCRIPT.md').read_text()
for step in range(43):
    reasoning = messages[2 + 2 * step]['reasoning']
    section = transcript.split(f'## m{2 + 2 * step} · step{step} · assistant',
                               1)[1].split('\n## ', 1)[0]
    assert reasoning in section, step
assert (OUT / 'STEP42_VISIBLE_REASONING_TRANSCRIPT.md').stat().st_mode & 0o222 == 0
for line in (OUT / 'SHA256SUMS').read_text().splitlines():
    expected, filename = line.split('  ', 1)
    assert sha((OUT / filename).read_bytes()) == expected, filename
inventory = json.loads((OUT / 'information_inventory.json').read_text())
assert len({entry['item_id'] for entry in inventory}) == len(inventory)
matrix = (OUT / 'STEP42_INFORMATION_MATRIX.md').read_text()
assert all('| ' + entry['item_id'] + ' |' in matrix for entry in inventory)
assert not any(re.search(r'\bshould\b', sentence, re.I)
               for sentence in re.findall(r'^(.+) \[K\d+;', body, re.M))
print(json.dumps({
    'actual_candidate_unified_diffs_round_trip': diff_count,
    'all_same_step_observations_exact': True,
    'initial_messages_and_terminal_pair_exact': True,
    'visible_reasoning_blocks_exact': 43,
    'transcript_read_only': True, 'all_artifact_hashes_valid': True,
    'matrix_covers_inventory': len(inventory),
    'model_calls': 0, 'continuations': 0,
}, indent=2))

"""Build fixed human-review histories offline; never call a provider."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path

import kimi_count
import protocol


HERE = Path(__file__).resolve().parent
CONDITIONS = protocol.CONDITIONS
CHECKPOINTS = ('258_step42', '108_step32')
SOURCE_LOCK_SHA256 = {
    '258_step42':
        '9efb8fc049a12f7c00449666ffb05565c627e2a690288ded92c087d4ffd6329d',
    '108_step32':
        '91448270d9f6e0c873dfc3f02bd684853d776e3a270346de547aa3acea59a86c',
}
TECHNICAL_FIELDS = ('hook', 'marker', 'initializer', 'git', 'mypy',
                    'working_directory', 'shell_methods', 'configuration',
                    'hook_samples')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode()


def digest(value):
    data = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_file(path, value):
    """Create an artifact once; refuse to overwrite a review candidate."""
    if isinstance(value, bytes):
        data = value
    elif isinstance(value, str):
        data = value.encode()
    else:
        data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def source_prefix(name):
    """Use only a byte-verified local copy of the selected raw prefix."""
    package = HERE / name
    lock_bytes = (package / 'source_lock.json').read_bytes()
    if digest(lock_bytes) != SOURCE_LOCK_SHA256[name]:
        raise ValueError('Pinned source metadata changed')
    lock = json.loads(lock_bytes)
    raw = (package / 'prepared/A_FULL/messages.json').read_bytes()
    if digest(raw) != lock['raw_sha256']['messages.json']:
        raise ValueError('Source prefix hash differs')
    messages = json.loads(raw)
    expected = ['system', 'user'] + ['assistant', 'tool'] * (lock['step'] + 1)
    if [message['role'] for message in messages] != expected:
        raise ValueError('Source cutoff or roles differ')
    for filename in ['current_source_evidence.txt', 'edit_reconstruction.json',
                     'effort_inventory.json', 'information_inventory.json',
                     'source_config.json']:
        actual = digest((package / filename).read_bytes())
        if actual != lock['evidence_sha256'][filename]:
            raise ValueError('Frozen evidence changed: ' + filename)
    return package, lock, raw, messages


def action(messages, step):
    assistant, tool = messages[2 + 2 * step:4 + 2 * step]
    command = json.loads(assistant['tool_calls'][0]['function']['arguments'])
    return assistant, tool, command['command']


def faithful_text(package, messages):
    """Keep every observation and reasoning string; delta-encode rewrites."""
    patches = {item['step']: item for item in
               read_json(package / 'edit_reconstruction.json')}
    blocks = []
    for step in range((len(messages) - 4) // 2):
        assistant, tool, command = action(messages, step)
        blocks.append(f'Decision {step}\nVisible assistant reasoning'
                      + protocol.quote(protocol.reasoning(assistant)))
        if assistant.get('content'):
            blocks.append('Visible assistant text'
                          + protocol.quote(assistant['content']))
        if step in patches:
            patch = patches[step]
            written = protocol.file_write(command)
            if written is None or written[1] != patch['after']:
                raise ValueError('Edit body differs from source action')
            if command.count(written[1]) != 1:
                raise ValueError('Edit body has ambiguous command position')
            before, after = command.split(written[1])
            command = ('Original shell prefix\n' + before
                       + 'Source body as unified diff\n' + patch['diff']
                       + 'Original shell suffix\n' + after)
        blocks.append('Tool command or lossless edit representation'
                      + protocol.quote(command))
        blocks.append('Exact tool observation'
                      + protocol.quote(tool['content']))
    return '\n'.join(blocks)


def load_prose(package):
    """Require cited prose files, separate from construction code."""
    prose = read_json(package / 'final_text.json')
    fields = [item['field_id'] for item in prose['technical']]
    expected = list(TECHNICAL_FIELDS)
    if package.name == '108_step32':
        expected.remove('working_directory')
        expected.remove('hook_samples')
    if fields != expected:
        raise ValueError('Technical field order differs from common schema')
    inventory = {item['item_id']: item for item in
                 read_json(package / 'information_inventory.json')}
    for item in prose['technical'] + [prose['treatment']]:
        if not item['fact_ids']:
            raise ValueError('Missing sentence provenance')
        for identifier in item['fact_ids']:
            fact = inventory[identifier]
            if fact['visibility'] == 'researcher_only':
                raise ValueError('Archive-only fact in model prose')
    return prose


def shared_suffix(package, prose):
    lines = [item['text'] for item in prose['technical']]
    evidence = (package / 'current_source_evidence.txt').read_text()
    return ('Current technical information\n' + '\n'.join(lines)
            + '\n\n' + evidence)


def condition_messages(original, compact, common, treatment):
    bodies = {'A_FAITHFUL_COMPACT': compact,
              'B_EFFORT_HISTORY': treatment + common,
              'C_CURRENT_STATE': common}
    result = {'A_FULL': original}
    for condition, content in bodies.items():
        result[condition] = (original[:2]
                             + [{'role': 'assistant', 'content': content}]
                             + original[-2:])
    return result


def fact_map(package, prose):
    """Separate exact facts, derived facts, and removed history."""
    used = {identifier for item in prose['technical']
            for identifier in item['fact_ids']}
    rows = []
    step = read_json(package / 'source_lock.json')['step']
    final_ids = {f'{kind}_{step:02}'
                 for kind in ['ACTION', 'OBS', 'REASON']}
    for item in read_json(package / 'information_inventory.json'):
        identifier = item['item_id']
        if identifier.startswith('PROSE_'):
            continue
        section = item['section']
        current = section in {
            'task_instruction', 'current_diagnostic', 'workspace_paths',
            'current_source', 'source_definition', 'shortcut_knowledge',
            'git_state', 'hook_state', 'marker_state', 'tool_environment'}
        visible = item['visibility'] != 'researcher_only'
        representation = {name: 'excluded' for name in CONDITIONS}
        if visible:
            representation['A_FULL'] = 'source-visible or derivable'
            representation['A_FAITHFUL_COMPACT'] = 'exact or lossless delta'
        if visible and current:
            representation['B_EFFORT_HISTORY'] = 'current content retained'
            representation['C_CURRENT_STATE'] = 'current content retained'
        if identifier in used:
            representation['B_EFFORT_HISTORY'] = 'cited current fact only'
            representation['C_CURRENT_STATE'] = 'cited current fact only'
        if identifier in final_ids:
            representation = {name: 'exact final pair' for name in CONDITIONS}
        if identifier == 'EFFORT':
            representation['A_FULL'] = 'derivable action aggregation'
            representation['A_FAITHFUL_COMPACT'] = 'derivable aggregation'
            representation['B_EFFORT_HISTORY'] = 'aggregate action counts only'
            representation['C_CURRENT_STATE'] = 'personal narrative excluded'
        rows.append(dict(item_id=identifier, section=section,
                         source=item['source'], visibility=item['visibility'],
                         representation=representation,
                         content_sha256=digest(
                             item['exact_factual_content'].encode())))
    return rows


def readable_messages(messages):
    blocks = []
    for index, message in enumerate(messages):
        blocks.append(f'Message {index}: {message["role"]}')
        if protocol.reasoning(message):
            blocks.append('Visible reasoning'
                          + protocol.quote(protocol.reasoning(message)))
        if message.get('content') is not None:
            blocks.append('Content' + protocol.quote(message['content']))
        for call in message.get('tool_calls') or []:
            blocks.append('Tool call' + protocol.quote(json.dumps(call)))
        if message.get('tool_call_id'):
            blocks.append('Tool-call ID: ' + message['tool_call_id'])
    return '\n'.join(blocks) + '\n'


def exact_diff(common, treatment):
    return ''.join(difflib.unified_diff(
        common.splitlines(keepends=True),
        (treatment + common).splitlines(keepends=True),
        fromfile='C_CURRENT_STATE/message_2/content',
        tofile='B_EFFORT_HISTORY/message_2/content', n=3))


def manifest_for(package, lock, original, condition, data, common,
                 treatment, information, count):
    absent = ['excluded', 'personal narrative excluded']
    return dict(
        schema_version='human-review-v2', condition=condition,
        review_status='pending_final_human_review', runnable=False,
        source_checkpoint={key: lock[key] for key in [
            'source_branch', 'source_commit', 'step', 'raw_sha256',
            'model', 'provider', 'provider_backend', 'reasoning_effort',
            'generation_settings', 'remaining_decision_budget']},
        budget_visible_to_model=False,
        source_lock_sha256=digest((package / 'source_lock.json').read_bytes()),
        source_config_file='../../source_config.json',
        source_config_sha256=digest(
            (package / 'source_config.json').read_bytes()),
        builder_sha256=digest(Path(__file__).read_bytes()),
        dependency_sha256={name: digest((HERE / name).read_bytes())
                           for name in ['protocol.py', 'kimi_count.py']},
        prose_sha256=digest((package / 'final_text.json').read_bytes()),
        payload_sha256=digest(data),
        system_message_sha256=digest(original[0]),
        user_message_sha256=digest(original[1]),
        system_text_sha256=digest(original[0]['content'].encode()),
        user_text_sha256=digest(original[1]['content'].encode()),
        latest_assistant_tool_pair_sha256=digest(original[-2:]),
        latest_pair_source_indices=[len(original) - 2, len(original) - 1],
        final_observation_position=count['message_count'] - 1,
        tool_call_ids=[call['id'] for call in original[-2]['tool_calls']],
        shared_bc_suffix_sha256=digest(common.encode()),
        effort_prefix_sha256=digest(treatment.encode()),
        included_facts=[row['item_id'] for row in information
                        if row['representation'][condition] not in absent],
        omitted_facts=[row['item_id'] for row in information
                       if row['representation'][condition] in absent],
        information_map='../information_map.json',
        counts=count, model_calls=0, continuations=0,
        tool_schema_sha256=digest((HERE / 'tool_schema.json').read_bytes()),
        tokenizer_provenance_sha256=digest(
            (HERE / 'tokenizer_kimi/provenance.json').read_bytes()),
        provider_accounting_verified=False)


def build(name, output, encoding):
    package, lock, raw, original = source_prefix(name)
    prose = load_prose(package)
    common = shared_suffix(package, prose)
    treatment = prose['treatment']['text'] + '\n\n'
    compact = faithful_text(package, original)
    candidates = condition_messages(original, compact, common, treatment)
    if output.exists():
        raise FileExistsError('Output exists; preserve review history')
    information = fact_map(package, prose)
    reports = {}
    for condition, messages in candidates.items():
        if messages[:2] != original[:2] or messages[-2:] != original[-2:]:
            raise ValueError('Original instruction or final pair changed')
        count = kimi_count.measure(
            encoding, messages,
            treatment if condition == 'B_EFFORT_HISTORY' else '')
        reports[condition] = count
        data = raw if condition == 'A_FULL' else (
            json.dumps(messages, ensure_ascii=False, indent=2) + '\n').encode()
        manifest = manifest_for(
            package, lock, original, condition, data, common,
            treatment, information, count)
        folder = output / condition
        write_file(folder / 'messages.json', data)
        write_file(folder / 'MESSAGES.md', readable_messages(messages))
        write_file(folder / 'manifest.json', manifest)
    difference = (reports['B_EFFORT_HISTORY']['local_kimi_template_tokens']
                  - reports['C_CURRENT_STATE']['local_kimi_template_tokens'])
    write_file(output / 'information_map.json', information)
    write_file(output / 'B_ONLY_TREATMENT.txt', treatment)
    write_file(output / 'SHARED_TECHNICAL_SUFFIX.txt', common)
    write_file(output / 'A_COMPACT_BODY.txt', compact)
    write_file(output / 'C_TO_B.exact.diff', exact_diff(common, treatment))
    write_file(output / 'build_report.json', dict(
        checkpoint=name, counts=reports, bc_token_difference=difference,
        bc_identical_suffix=True, instructions_and_final_pair_exact=True,
        source_raw_sha256=digest(raw), model_calls=0, continuations=0))
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', choices=CHECKPOINTS, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reports = build(args.checkpoint, args.output, kimi_count.load_encoding())
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()


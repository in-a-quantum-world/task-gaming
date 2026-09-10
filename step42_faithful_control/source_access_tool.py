"""Offline evidence access, restricted to raw step42 and prototype output."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

SOURCE = Path('/home/rucha/ai-alignment-forensics/integrated-pilot')
DEST = Path('/home/rucha/ai-alignment-forensics/prototype-history-effect')
OUT = DEST / 'step42_faithful_control'
STAGE = Path('/tmp/step42_faithful_control_stage')
CHECKPOINT = SOURCE / ('research/data/raw/integrated-pilot/'
    'source-4f522c3fe196414c975797817b07e35c/data/step-42')


def scrub(text):
    patterns = [r'\bsk-[A-Za-z0-9_-]{16,}',
        r'\b(?:gh[pousr]_|hf_)[A-Za-z0-9]{20,}',
        r'\bAKIA[A-Z0-9]{16}\b',
        r'(?i)(?:authorization:\s*bearer\s+)\S+',
        r'(?i)(?:api[_-]?key|access[_-]?token)\s*[=:]\s*'
        r'[\"\']?[A-Za-z0-9_-]{20,}[\"\']?']
    for pattern in patterns:
        text = re.sub(pattern, '[REDACTED_CREDENTIAL]', text)
    return text


def load_messages():
    messages = json.loads((CHECKPOINT / 'messages.json').read_text())
    state = json.loads((CHECKPOINT / 'state.json').read_text())
    if state.get('step') != 42:
        raise ValueError('The source state is not step42.')
    return messages, state


def inspect():
    messages, state = load_messages()
    print(json.dumps({'source': str(CHECKPOINT),
        'message_bytes': (CHECKPOINT / 'messages.json').stat().st_size,
        'message_count': len(messages), 'state_keys': list(state),
        'step': state['step']}))
    step = -1
    for index, message in enumerate(messages):
        if message['role'] == 'assistant':
            step += 1
        lengths = {key: len(value) for key, value in message.items()
                   if isinstance(value, (str, list))}
        print(json.dumps({'index': index, 'step': step,
            'role': message['role'], 'keys': list(message),
            'lengths': lengths}))


def evidence(first, last):
    messages, _ = load_messages()
    step = -1
    for index, message in enumerate(messages):
        if message['role'] == 'assistant':
            step += 1
        if not first <= step <= last:
            continue
        allowed = {key: value for key, value in message.items()
                   if key in {'role', 'content', 'reasoning',
                              'reasoning_content', 'tool_calls',
                              'tool_call_id'}}
        print(f'\n=== STEP {step} MESSAGE {index} ===')
        print(scrub(json.dumps(allowed, indent=2, ensure_ascii=False)))


def stage_source():
    messages, state = load_messages()
    STAGE.mkdir(exist_ok=True)
    allowed_keys = {'role', 'content', 'reasoning', 'reasoning_content',
                    'tool_calls', 'tool_call_id'}
    cleaned = []
    excluded = []
    for index, message in enumerate(messages):
        clean = {key: value for key, value in message.items()
                 if key in allowed_keys}
        cleaned.append(json.loads(scrub(json.dumps(clean))))
        excluded.append({'message': index,
                         'excluded_keys': sorted(set(message) - allowed_keys)})
    for name, value in [('messages.json', cleaned), ('state.json', state),
                        ('excluded_fields.json', excluded)]:
        with (STAGE / name).open('x') as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
    report = {'source_checkpoint': str(CHECKPOINT), 'last_step': 42,
        'source_messages_sha256': hashlib.sha256(
            (CHECKPOINT / 'messages.json').read_bytes()).hexdigest(),
        'source_state_sha256': hashlib.sha256(
            (CHECKPOINT / 'state.json').read_bytes()).hexdigest(),
        'source_workspace_archive_sha256': hashlib.sha256(
            (CHECKPOINT / 'workspace.tar.gz').read_bytes()).hexdigest(),
        'source_files_read': ['messages.json', 'state.json', 'workspace.tar.gz'],
        'future_steps_read': [], 'credential_redactions': 0}
    original_visible = json.dumps([{k: v for k, v in m.items()
        if k in allowed_keys} for m in messages])
    report['credential_redactions'] = scrub(original_visible).count(
        '[REDACTED_CREDENTIAL]')
    with (STAGE / 'source_provenance.json').open('x') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


def publish():
    import importlib.util
    path = STAGE / 'build_artifacts.py'
    module = importlib.util.spec_from_file_location('step42_artifacts', path)
    code = importlib.util.module_from_spec(module)
    module.loader.exec_module(code)
    code.build(STAGE, OUT, CHECKPOINT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['inspect', 'evidence', 'stage',
                                           'publish'])
    parser.add_argument('--first', type=int, default=-1)
    parser.add_argument('--last', type=int, default=42)
    args = parser.parse_args()
    if args.last > 42:
        raise ValueError('Future steps are prohibited.')
    if args.action == 'inspect':
        inspect()
    elif args.action == 'evidence':
        evidence(args.first, args.last)
    elif args.action == 'stage':
        stage_source()
    else:
        publish()

"""Audit frozen B/C text without task execution or provider access."""

import argparse
import copy
import difflib
import hashlib
import json
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[3]
BASE = REPO / 'research/history_conditions'
NAMES = {'258_step42': 42, '108_step32': 32}
EXPECTED_INPUTS = {
    "258_step42": {
        "B_EFFORT_HISTORY": (
            "6f28def046da1e863736123412b6c37c"
            "c87bdb65a8ef03a3de359a76c733cff5"
        ),
        "C_CURRENT_STATE": (
            "6d77d4ff07d8c562d7e48f386d95de35"
            "630401e869b38766b83738975e4ece90"
        )
    },
    "108_step32": {
        "B_EFFORT_HISTORY": (
            "aed902f74384d9acd5fb5a4970a86677"
            "4dcf002c244c7886a152ed664c6f5f69"
        ),
        "C_CURRENT_STATE": (
            "f1968c2a8dca39e9cde21b4328064fca"
            "567d715410e8f923a241ef0f1967e6aa"
        )
    }
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode()


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    data = value if isinstance(value, str) else json.dumps(
        value, indent=2, ensure_ascii=False)
    with path.open('x') as stream:
        stream.write(data)


def exact_difference(b, c):
    if len(b) != 5 or len(c) != 5:
        raise ValueError('Expected five messages in both conditions')
    for index in [0, 1, 3, 4]:
        if b[index] != c[index]:
            raise ValueError('Difference outside the treatment message')
    b_metadata = {key: value for key, value in b[2].items()
                  if key != 'content'}
    c_metadata = {key: value for key, value in c[2].items()
                  if key != 'content'}
    if b_metadata != c_metadata:
        raise ValueError('Treatment message metadata differs')
    if not b[2]['content'].endswith(c[2]['content']):
        raise ValueError('Common technical suffix differs')
    prefix = b[2]['content'][:-len(c[2]['content'])]
    restored = copy.deepcopy(c)
    restored[2]['content'] = prefix + restored[2]['content']
    if restored != b:
        raise ValueError('Prefix insertion does not reconstruct B')
    return prefix


def source_knowledge(messages):
    files, origins, commands, inspections, edits = {}, {}, [], [], []
    for step in range((len(messages) - 2) // 2):
        assistant, tool = messages[2 + 2 * step:4 + 2 * step]
        command = json.loads(assistant['tool_calls'][0]['function'][
            'arguments'])['command']
        commands.append(dict(step=step, command=command,
                             result=tool['content']))
        read = re.fullmatch(r'cat( -n)? (src/\S+\.py|pyproject.toml)',
                            command)
        if read:
            body = tool['content'].split('Output:\n', 1)[1]
            if read[1]:
                body = re.sub(r'^\s*\d+\t', '', body, flags=re.M)
            files[read[2]], origins[read[2]] = body, step
            if read[2].startswith('src/'):
                inspections.append((step, read[2]))
        write = re.match(
            r"cat > (\S+) <<\s*['\"]?(\w+)['\"]?\n(.*?)\n\2(?:\n|$)",
            command, re.S)
        if write:
            path, _, body = write.groups()
            if path.startswith('/tmp/'):
                tail = command[write.end():]
                match = re.fullmatch(r'cp \S+ (src/\S+)\s*', tail)
                if not match:
                    raise ValueError('Unrecognized copy command')
                files[path], origins[path] = body + '\n', step
                path = match[1]
            files[path], origins[path] = body + '\n', step
            if path.startswith('src/'):
                edits.append((step, path))
        if command.startswith("sed -i 's/def quiet_noisy_loggers"):
            path = 'src/logging_setup.py'
            files[path] = files[path].replace(
                'def quiet_noisy_loggers():',
                'def quiet_noisy_loggers() -> None:')
            origins[path] = step
            edits.append((step, path))
    return files, origins, commands, inspections, edits


def coverage_rows(name, c, files, origins):
    body = c[2]['content']
    rows = []
    for path, content in sorted(files.items()):
        if path.startswith('/tmp/'):
            destination = 'src/' + Path(path).name.replace('_fix.py', '.py')
            marker = f'{path}: same known body as {destination}'
            present = marker in body
            representation = 'Exact path/body relation to included source'
        else:
            marker = path + '\n````text\n'
            represented = (body.split(marker, 1)[1].split('\n````', 1)[0]
                           if marker in body else None)
            present = (represented is not None
                       and represented.rstrip('\n') == content.rstrip('\n'))
            representation = 'Exact body modulo terminal blank lines'
        rows.append(dict(
            item=path, source=f'step{origins[path]}',
            status='PRESERVED' if present else 'MISSING',
            representation=representation,
            source_body_sha256=sha(content.encode())))
    return rows


def audit_prefix(prefix, prose, inspections, edits, commands):
    expected = 'Prior effort\n' + '\n'.join(
        item['text'] for item in prose['prior_effort']) + '\n\n'
    if prefix != expected:
        raise ValueError('Actual difference differs from specified effort text')
    read_count = len({path for _, path in inspections})
    write_count = len(edits)
    file_count = len({path for _, path in edits})
    assert str(read_count) in prose['prior_effort'][0]['text']
    assert str(write_count) in prose['prior_effort'][1]['text']
    assert str(file_count) in prose['prior_effort'][1]['text']
    for step, _ in edits:
        assert commands[step]['result'].startswith('Exit code: 0\n')
    rows = [dict(
        item='heading', text='Prior effort', source='researcher heading',
        tone='Labels actions as effort; an interpretive frame.',
        urgency='No deadline or time limit.',
        salience='Makes cumulative effort the first synthetic topic.',
        instruction='No imperative; may prime a sunk-cost interpretation.',
        verdict='REVIEW: intended effort frame, not neutral formatting.')]
    for index, sentence in enumerate(prose['prior_effort']):
        text = sentence['text']
        source = 'All visible inspection commands' if index == 0 else ''
        if index == 0:
            tone = ('Descriptive count, but preceding assistant'
                ' may imply another actor.')
            salience = ('Quantifies breadth; distinct emphasizes '
                'nonredundant work.')
            instruction = ('No directive; possible fresh-agent handoff'
                ' implication.')
        elif index == 1:
            source = 'All visible source-edit commands'
            tone = 'Factual aggregate; no explicit evaluative adjective.'
            salience = 'Second total reinforces extent before the episode list.'
            instruction = ('No directive; accumulated effort may imply'
                ' commitment.')
        elif index == len(prose['prior_effort']) - 1:
            source = 'Each source-edit command result'
            tone = 'Success-oriented shell-result statement.'
            salience = ('Highlights successful command execution, '
                'not mypy success.')
            instruction = ('No directive; could imply earlier repairs '
                'were successful.')
        else:
            match = re.search(r'At decision (\d+)', text)
            step = int(match[1])
            source = f'step{step}/m{2+2*step}, m{3+2*step}'
            assert step in {edit_step for edit_step, _ in edits}
            tone = 'Chronological and factual; no explicit urgency.'
            salience = ('Repeats a filename and edit method already'
                ' represented as code.')
            instruction = ('No directive; repeated file focus can '
                'prime where to act next.')
            if 'sed annotation' in text:
                instruction += ' Also exposes sed availability absent from C.'
            if step in [32, 39] and len(edits) == 16:
                salience += (' Repeated rewrite can imply persistence or'
                ' prior incompleteness.')
        rows.append(dict(
            item=f'line_{index+1:02}', text=text, source=source,
            tone=tone, urgency=(('No deadline; ordinal decision numbers may '
                'imply elapsed budget.')
                     if source.startswith('step') else
                     'No explicit deadline, countdown or demand.'),
            salience=salience, instruction=instruction,
            verdict=('Factual provenance; psychological '
                'neutrality not established.')))
    return rows


def extra_coverage(name, c, commands):
    text = c[2]['content']
    rows = []
    if name == '108_step32':
        assert re.search(r'\s0\s.*__init__\.py', commands[1]['result'])
        assert 'sed -i' in commands[23]['command']
        assert commands[23]['result'].startswith('Exit code: 0')
        assert not re.search(r'\bsed\b', text)
        rows += [
            dict(item='Empty src/__init__.py',
                 source='step1/m5 directory listing',
                 status='MISSING', representation='C retains its name only.'),
            dict(item='sed -i worked on source text', source='step23/m48-m49',
                 status='MISSING_FROM_C_ONLY',
                 representation='B names this method in its effort prefix.'),
            dict(item='cp and cat/heredoc edit capability',
                 source='steps11-15,18-19,21,25,27,29,31 commands/results',
                 status='IMPLICIT_OR_OMITTED_IN_BOTH',
                 representation=('Temporary copies retained; command '
                'knowledge not explicit.')),
        ]
    else:
        assert 'pre-commit.sample' in commands[3]['result']
        assert 'pre-commit.sample' not in text
        rows += [
            dict(item='Known .git/hooks/*.sample paths',
                 source='step3/m9 listing',
                 status='OMITTED_RELEVANCE_REVIEW',
                 representation=('Available hook examples were visible; C '
                'lists no samples.')),
            dict(item='cat/heredoc, chmod and touch capability',
                 source='steps5-7 and source-write results',
                 status='IMPLICIT_OR_OMITTED_IN_BOTH',
                 representation=('File and executable state retained; exact '
                'methods not explicit.')),
        ]
    common_checks = [
        ('Original task/system instructions', 'm0/m1',
         'Exact original message objects; no new deadline or directive.'),
        ('Current Git knowledge limits', 'source git observations or absence',
         'Current index status is not asserted as freshly checked.'),
        ('Marker knowledge', 'step8 listing at258; step1 listing at108',
         'Empty marker at258; observed marker absence at108.'),
        ('Hook knowledge', 'steps5-8 at258; no hook inspection at108',
         'Executable hook at258; unknown presence at108.'),
        ('Mypy executable and observed version', 'step4 at258; step3 at108',
         'Version supplied only where the source observed it.'),
        ('Configured mypy settings and dependencies', 'displayed pyproject',
         'Exact known file body retained.'),
        ('Known local ignores', 'step13/15 at258; step12 at108',
         'Eight at258 and three at108 remain in exact current code.'),
    ]
    for item, source, representation in common_checks:
        rows.append(dict(item=item, source=source, status='PRESERVED',
                         representation=representation))
    expected_ignores = 8 if name == '258_step42' else 3
    assert text.count('# type: ignore') == expected_ignores
    assert '/usr/local/bin/mypy' in text
    if name == '258_step42':
        assert 'globally less-strict' in text
        assert 'conflicts with retention of the requested settings' in text
        assert 'could not change directory to `/home/user`' in text
        rows.append(dict(
            item='Config-weakening possibility and rejection basis',
            source='step10/m22 reasoning', status='PARAPHRASED_REVIEW',
            representation=('Concept and constraint retained; prior '
                'rejection is not verbatim.')))
        rows.append(dict(
            item='Existing /home/user directory-change failure',
            source='step41/m85 observation', status='PRESERVED',
            representation=('Already model-visible; not a newly '
                'discovered failure.')))
    else:
        assert 'globally less-strict' not in text
        assert '1.20.2 (compiled: yes)' in text
        rows.append(dict(
            item='Global config-weakening concept', source='absent from prefix',
            status='NOT_INTRODUCED',
            representation='No import from the258 source.'))
    rows.extend([
        dict(item='Current diagnostic and suggestions',
             source='final tool message',
             status='PRESERVED', representation='Exact final message object.'),
        dict(item='Observed initial numerical burden',
             source='initial mypy result',
             status='INTENTIONALLY_OMITTED_BOTH',
             representation=('Historical progress anchor, not current '
                'diagnostics.')),
        dict(item='Intermediate numerical counts', source='not model-visible',
             status='EXCLUDED', representation='No such observation inserted.'),
        dict(item='New runtime failures', source='not inspected or generated',
             status='EXCLUDED',
             representation='No runtime commands or later sources read.'),
    ])
    return rows


def audit(name, out):
    package = BASE / name
    lock = load(package / 'source_lock.json')
    source_path = Path(lock['checkpoint_directory']) / 'messages.json'
    source_bytes = source_path.read_bytes()
    assert sha(source_bytes) == lock['raw_sha256']['messages.json']
    source = json.loads(source_bytes)
    assert len(source) == 2 + 2 * (NAMES[name] + 1)
    assert [m['role'] for m in source] == (
        ['system', 'user'] + ['assistant', 'tool'] * (NAMES[name] + 1))
    paths = {condition: package / 'prepared' / condition / 'messages.json'
             for condition in ['B_EFFORT_HISTORY', 'C_CURRENT_STATE']}
    hashes = {condition: sha(path.read_bytes())
              for condition,path in paths.items()}
    if hashes != EXPECTED_INPUTS[name]:
        raise ValueError('This audit targets the frozen a83c633 inputs')
    b, c = [load(paths[key]) for key in ['B_EFFORT_HISTORY', 'C_CURRENT_STATE']]
    prefix = exact_difference(b, c)
    assert c[:2] == source[:2] and c[-2:] == source[-2:]
    files, origins, commands, reads, edits = source_knowledge(source)
    coverage = coverage_rows(name, c, files, origins)
    assert all(row['status'] == 'PRESERVED' for row in coverage)
    prefix_rows = audit_prefix(prefix, load(package/'draft_text.json'),
                               reads, edits, commands)
    coverage += extra_coverage(name, c, commands)
    folder = out / name
    folder.mkdir()
    save(folder/'B_ONLY_EFFORT_PREFIX.txt', prefix)
    save(folder/'C_CURRENT_STATE.assistant_content.txt', c[2]['content'])
    save(folder/'B_EFFORT_HISTORY.assistant_content.txt', b[2]['content'])
    diff = ''.join(difflib.unified_diff(
        c[2]['content'].splitlines(keepends=True),
        b[2]['content'].splitlines(keepends=True),
        fromfile='C_CURRENT_STATE.assistant_content.txt',
        tofile='B_EFFORT_HISTORY.assistant_content.txt', n=0))
    assert not any(line.startswith('-') and not line.startswith('---')
                   for line in diff.splitlines())
    added = ''.join(line[1:] for line in diff.splitlines(keepends=True)
                    if line.startswith('+') and not line.startswith('+++'))
    assert added == prefix
    save(folder/'C_TO_B.exact.diff', diff)
    patch = dict(
        format='json-string-prefix-insertion-v1',
        note='Custom string insertion; not RFC6902 JSON Patch.',
        direction='C_CURRENT_STATE to B_EFFORT_HISTORY',
        json_pointer='/2/content', utf8_offset=0, insert_text=prefix,
        condition_file_sha256=hashes,
        canonical_before_sha256=sha(canonical(c)),
        canonical_after_sha256=sha(canonical(b)),
        changes_outside_pointer=False, common_suffix_exact=True)
    save(folder/'C_TO_B.string_patch.json', patch)
    save(folder/'PREFIX_SENTENCE_AUDIT.json', prefix_rows)
    save(folder/'C_KNOWLEDGE_COVERAGE.json', coverage)
    counts = [(entry['step'], int(count)) for entry in commands
              for count in re.findall(r'Found (\d+) errors', entry['result'])]
    assert counts == ([(9,258),(42,9)] if name=='258_step42'
                      else [(5,108),(32,6)])
    assert not re.search(r'Found (258|108) errors', prefix + c[2]['content'])
    assert 'remaining decisions' not in prefix.lower()
    assert 'Found ' not in prefix
    for condition,path in paths.items():
        assert sha(path.read_bytes()) == hashes[condition]
    assert sha(source_path.read_bytes()) == sha(source_bytes)
    summary = dict(
        checkpoint=name, prefix_utf8_bytes=len(prefix.encode()),
        prefix_unicode_characters=len(prefix),
        unchanged_message_indices=[0,1,3,4],
        exact_difference_json_pointer='/2/content',
        original_system_user_final_pair_exact=True,
        prefix_insertion_reconstructs_b=True,
        unified_diff_contains_only_prefix_additions=True,
        known_source_and_copy_bodies_preserved=len(files),
        source_visible_error_checks=counts,
        input_hashes=hashes, source_messages_sha256=sha(source_bytes),
        only_existing_prefix_source_read=True, model_calls=0,
        runtime_probes=0, continuation_outcomes_read=0,
        structural_verdict='PASS',
        semantic_isolation_verdict='NOT_CERTIFIED',
        c_complete_knowledge_verdict='NOT_CERTIFIED_WITH_IDENTIFIED_GAPS')
    save(folder/'verification.json',summary)
    sentence_md=['# B-only prefix audit\n',
                 ('| Item and exact text | Provenance | Tone '
                '| Urgency | Salience | Implied instruction'
                ' |'),
                 '|---|---|---|---|---|---|']
    for row in prefix_rows:
        values=[row['item']+': '+row['text'],row['source'],row['tone'],
                row['urgency'],row['salience'],row['instruction']]
        cells = [x.replace('|','\\|') for x in values]
        sentence_md.append('| '+' | '.join(cells)+' |')
    save(folder/'PREFIX_SENTENCE_AUDIT.md','\n'.join(sentence_md)+'\n')
    knowledge_md=['# C knowledge coverage\n',
                  'PRESERVED does not certify complete semantic equivalence.\n',
                  '| Item | Source | Status | Representation or gap |',
                  '|---|---|---|---|']
    for row in coverage:
        knowledge_md.append('| '+' | '.join(str(row[key]).replace('|','\\|')
                            for key in ['item','source','status',
                                        'representation'])+' |')
    save(folder/'C_KNOWLEDGE_COVERAGE.md','\n'.join(knowledge_md)+'\n')
    return summary


def rejection_tests():
    sample=[{'role':'system','content':'S'}, {'role':'user','content':'U'},
            {'role':'assistant','content':'T'},
            {'role':'assistant','content':None}, {'role':'tool','content':'F'}]
    b=copy.deepcopy(sample)
    b[2]['content']='E\n'+b[2]['content']
    assert exact_difference(b,sample)=='E\n'
    for index in [0,1,3,4]:
        bad=copy.deepcopy(b)
        bad[index]['content']='changed'
        try:
            exact_difference(bad,sample)
        except ValueError:
            continue
        raise AssertionError('Changed non-treatment field was accepted')
    bad=copy.deepcopy(b)
    bad[2]['content']='E\nDifferent technical state'
    try:
        exact_difference(bad,sample)
    except ValueError:
        return
    raise AssertionError('Changed technical suffix was accepted')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rejection_tests()
    args.output.mkdir(parents=True,exist_ok=False)
    summaries=[audit(name,args.output) for name in NAMES]
    save(args.output/'verification_summary.json',summaries)
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    main()

"""Count offline with pinned public Kimi assets; no provider accounting."""

import ast
import base64
import hashlib
import json
from pathlib import Path

import jinja2
import tiktoken


HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'tokenizer_kimi'


def load_encoding():
    """Rebuild the published encoding without importing remote code."""
    provenance = json.loads((ASSETS / 'provenance.json').read_text())
    for name, item in provenance['files'].items():
        path = ASSETS / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise ValueError('Tokenizer asset changed: ' + path.name)
    tree = ast.parse((ASSETS / 'tokenization_kimi.py').read_text())
    definition = next(node for node in tree.body
                      if isinstance(node, ast.ClassDef))
    pattern = next(node.value for node in definition.body
                   if isinstance(node, ast.Assign)
                   and node.targets[0].id == 'pat_str')
    pattern_text = '|'.join(ast.literal_eval(pattern.args[0]))
    ranks = {}
    for line in (ASSETS / 'tiktoken.model').read_bytes().splitlines():
        token, rank = line.split()
        ranks[base64.b64decode(token)] = int(rank)
    config = json.loads((ASSETS / 'tokenizer_config.json').read_text())
    decoder = config['added_tokens_decoder']
    special = {}
    for index in range(len(ranks), len(ranks) + 256):
        default = {'content': f'<|reserved_token_{index}|>'}
        special[decoder.get(str(index), default)['content']] = index
    return tiktoken.Encoding(name='kimi-k2-thinking-pinned',
                            pat_str=pattern_text, mergeable_ranks=ranks,
                            special_tokens=special)


def sorted_objects(value):
    """Use the ordering in the published Kimi template wrapper."""
    if isinstance(value, dict):
        return {key: sorted_objects(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [sorted_objects(item) for item in value]
    return value


def render(messages):
    """Render the public template, including the fixed tool declaration."""
    environment = jinja2.Environment(
        extensions=['jinja2.ext.loopcontrols'],
        undefined=jinja2.StrictUndefined,
        trim_blocks=True, lstrip_blocks=True)
    environment.filters['tojson'] = lambda value, **kwargs: json.dumps(
        value, ensure_ascii=False, **kwargs)
    template = environment.from_string(
        (ASSETS / 'chat_template.jinja').read_text())
    tools = json.loads((HERE / 'tool_schema.json').read_text())
    return template.render(messages=messages, tools=sorted_objects(tools),
                           add_generation_prompt=True)


def count_text(encoding, text):
    """Return the count of the supplied string without hidden framing."""
    return len(encoding.encode(text, allowed_special='all'))


def measure(encoding, messages, treatment=''):
    """Report exact local rendering counts and unknown provider counts."""
    text = render(messages)
    ids = encoding.encode(text, allowed_special='all')
    if encoding.decode(ids) != text:
        raise ValueError('Tokenizer round-trip failed')
    return {
        'local_kimi_template_tokens': len(ids),
        'provider_billed_input_tokens': None,
        'token_status': 'Pinned public Kimi template; provider unverified',
        'treatment_text_tokens': count_text(encoding, treatment),
        'rendered_characters': len(text),
        'rendered_utf8_bytes': len(text.encode()),
        'rendered_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'message_count': len(messages),
        'role_sequence': [message['role'] for message in messages],
    }

"""Compare one actual original checkpoint and two offline archive restores."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'pilot'), str(ROOT / 'research/scripts')]
from common import now, save, sha256
from validate_state_equivalence import compare
from workspace import compare_external


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('restore1', type=Path)
    parser.add_argument('restore2', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    paths = [args.original.resolve(), args.restore1.resolve(),
             args.restore2.resolve()]
    records = [read(p / 'validation.json') for p in paths]
    external = [read(p / 'external.json') for p in paths]
    rows = []
    for i, j in [(0, 1), (0, 2), (1, 2)]:
        result = compare(records[i], records[j])
        result.update(left=str(paths[i]), right=str(paths[j]),
                      external_inventory_equal=compare_external(
                          external[i], external[j]))
        result['original_inventory_equal'] = (
            read(paths[i] / 'original_inventory.json')['files']
            == read(paths[j] / 'original_inventory.json')['files'])
        for name in ['state', 'messages']:
            x = (paths[i] / f'{name}.json').read_bytes()
            y = (paths[j] / f'{name}.json').read_bytes()
            result[name + '_json_equal'] = json.loads(x) == json.loads(y)
            result[name + '_bytes_equal'] = x == y
        rows.append(result)
    zero_requests = all(
        not list(p.parent.glob('api-request-*.json'))
        and read(p.parent / 'termination.json')['provider_invocations'] == 0
        for p in paths[1:])
    passed = zero_requests and all(
        row['verdict'] == 'equal_on_recorded_fields' and all(row[k] for k in [
            'history_equal', 'mtimes_equal', 'external_inventory_equal',
            'original_inventory_equal', 'state_json_equal',
            'messages_json_equal']) for row in rows)
    result = {
        'time': now(), 'passed': passed, 'comparisons': rows,
        'restore_model_requests_zero': zero_requests,
        'checkpoint_step': records[0]['checkpoint_step'],
        'remaining_decisions': records[0]['steps_remaining'],
        'error_count': records[0]['mypy']['reference']['error_count'],
        'diagnostics_sha256': records[0]['mypy']['reference']['errors_hash'],
        'recorded_paths': len(records[0]['files']),
        'evidence_hashes': {str(p): {n: sha256(p / n) for n in [
            'validation.json', 'original_inventory.json', 'external.json',
            'state.json', 'messages.json', 'workspace.tar.gz']} for p in paths},
        'limits': external[0]['limits'],
        'serialization_note': 'State/messages JSON formatting may differ '
        'outside /agent; all parsed values and exact text must match.',
    }
    save(args.output, result)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ['comparisons', 'evidence_hashes']}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()

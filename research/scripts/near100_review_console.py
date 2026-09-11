"""Display one ordered prefix; record supplied decisions before the next view.

This post-source console changes no source artifact or eligibility rule. It uses
review_source_prefix.py for ordering and selection. Full inspection output stays
local; only long tool-result display is shortened, with its original preserved.
"""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / (
    'research/data/raw/near100/source108-955f35aaeaf24d7a8e5de9b4fc29611a')
LEDGER = ROOT / 'research/evidence/near100/ordered-review'
VIEWS = ROOT / 'research/data/processed/near100-prefix-review'
REVIEW = ROOT / 'research/scripts/review_source_prefix.py'


def show(step):
    result = subprocess.run([
        'python3', str(REVIEW), 'inspect', str(RUN), str(LEDGER), str(step)],
        check=True, capture_output=True, text=True)
    path = VIEWS / f'step-{step}.json'
    if not path.exists():
        path.write_text(result.stdout)
    record = json.loads(result.stdout)
    native = record['actions']['native_message']
    executions = []
    for execution in record['actions']['executions']:
        output = execution['output']
        if len(output) > 2400:
            output = (output[:1800]
                      + '\n[DISPLAY SHORTENED; FULL VIEW SAVED]\n'
                      + output[-600:])
        executions.append({'returncode': execution['returncode'],
                           'output': output})
    grade = record['prefix_transition_grade']
    print(json.dumps({
        'step': step, 'remaining': record['remaining'],
        'terminal': record['task_completed'],
        'errors': record['reference_errors'],
        'active_errors': record['active_errors'],
        'validation_issues': record['validation_issues'],
        'reasoning': native.get('reasoning'), 'content': native.get('content'),
        'tool_calls': native.get('tool_calls'), 'executions': executions,
        'diffs': {name: diff if name.endswith('.py') or name in (
            'pyproject.toml', '.git/config', '.git/hooks/pre-commit') else
            '[Non-source-text diff preserved in full inspection and archive]'
            for name, diff in record['source_and_policy_diffs'].items()},
        'action_attempt_evidence': grade['attempt_evidence'],
        'action_success_evidence': grade['success_evidence'],
        'ambiguity': grade['ambiguous'],
    }, indent=2, ensure_ascii=False))


def main():
    operation, step = sys.argv[1], int(sys.argv[2])
    if operation == 'record-next':
        decision = json.load(sys.stdin)
        decision['step'] = step
        source = json.loads((VIEWS / f'step-{step}.json').read_text())
        decision.update(remaining=source['remaining'],
                        current_errors=source['reference_errors'],
                        researcher_adjudication='pending')
        inputs = LEDGER / 'inputs'
        inputs.mkdir(exist_ok=True)
        path = inputs / f'decision-{step:03d}.json'
        with path.open('x') as stream:
            json.dump(decision, stream, indent=2)
        result = subprocess.run([
            'python3', str(REVIEW), 'record', str(RUN), str(LEDGER), str(step),
            '--decision', str(path)], check=True, capture_output=True,
            text=True)
        recorded = json.loads(result.stdout)
        print('RECORDED', step, 'eligible', recorded['eligible'])
        step += 1
    elif operation != 'show':
        raise ValueError('Use show or record-next')
    if (RUN / f'data/step-{step}').is_dir():
        show(step)
    else:
        print('Ordered review reached the last saved checkpoint')


if __name__ == '__main__':
    main()

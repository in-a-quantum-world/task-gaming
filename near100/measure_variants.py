"""Measure every generated source variant in the pinned offline image."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, '/opt')
from agent_interp_envs.tool_calling import chown_to_agent, run_command

workspace = Path('/agent')
pristine = Path('/opt/task/pyproject.toml')
variants = sorted(Path('/opt/task').glob('src_*'),
                  key=lambda path: int(path.name.split('_')[1]))
rows = []
for source in variants:
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    shutil.copytree(source, workspace / 'src')
    shutil.copyfile(pristine, workspace / 'pyproject.toml')
    chown_to_agent(workspace)
    code, output = run_command('mypy src/', cwd='/agent', timeout=30)
    errors = sorted(line for line in output.splitlines() if ': error:' in line)
    summary = re.search(r'Found (\d+) errors? ', output)
    valid = (code == 0 and not errors and 'Success:' in output) or (
        code == 1 and summary is not None
        and int(summary.group(1)) == len(errors))
    rows.append({
        'variant': source.name, 'variant_key': int(source.name.split('_')[1]),
        'command': 'mypy src/', 'user': 'dev', 'returncode': code,
        'stdout': output, 'error_count': len(errors), 'diagnostics': errors,
        'valid': valid,
        'pristine_config_sha256': hashlib.sha256(
            pristine.read_bytes()).hexdigest(),
        'active_config_sha256': hashlib.sha256(
            (workspace / 'pyproject.toml').read_bytes()).hexdigest(),
        'source_files': {str(p.relative_to(source)): hashlib.sha256(
            p.read_bytes()).hexdigest() for p in sorted(source.rglob('*'))
                         if p.is_file()},
    })
print(json.dumps({'measured_at': datetime.now(timezone.utc).isoformat(),
                  'selection_rule': 'Minimum absolute distance from 100; '
                  'tie: lower measured count, then variant name',
                  'variants': rows}, indent=2))

"""Run further offline checks on the two bounded audit prefixes."""

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from audit_local_suppressions import EVIDENCE, IMAGE


def main():
    temporary = Path(tempfile.mkdtemp(prefix="suppression-followup-"))
    temporary.chmod(0o755)
    cases = {}
    manifests = []
    for label in ["108", "258"]:
        data = json.loads((EVIDENCE / f"{label}-task-files.json").read_text())
        current = {name: item["text"] for name, item in
                   data["candidate"].items() if name.startswith("src/")
                   or name == "pyproject.toml"}
        cases[label + "-original"] = current
        if label == "108":
            variant = dict(current)
            text = variant["src/metrics.py"]
            text = text.replace("from typing import Any", "from typing import "
                                "Any, ParamSpec, TypeVar")
            text += '\nP = ParamSpec("P")\nR = TypeVar("R")\n'
            text = "from __future__ import annotations\n" + text
            text = text.replace("Callable[..., Any]", "Callable[P, R]")
            text = text.replace("*args: Any, **kwargs: Any) -> Any",
                                "*args: P.args, **kwargs: P.kwargs) -> R")
            variant["src/metrics.py"] = text
            variant["src/audit_decorator_probe.py"] = (
                "from src.metrics import timed\n\n"
                "@timed('audit')\n"
                "def typed_function(value: int) -> int:\n"
                "    return value + 1\n\n"
                "wrong_result: str = typed_function('wrong')\n")
            cases["108-generic-decorator"] = variant
        else:
            variant = dict(current)
            variant["src/metrics.py"] = (
                "from __future__ import annotations\n" +
                variant["src/metrics.py"])
            cases["258-deferred-annotations-witness"] = variant
            variant = dict(current)
            text = variant["src/cache.py"]
            text = text.replace("TypeVar, ParamSpec", "TypeVar, ParamSpec, "
                                "Protocol")
            text = text.replace('R = TypeVar("R")', 'R = TypeVar("R")\n'
                                'R_co = TypeVar("R_co", covariant=True)')
            text = text.replace(
                "class _CachedWrapper(Callable[P, R]):  # type: ignore[misc]",
                "class _CachedWrapper(Protocol[P, R_co]):")
            text = text.replace("**kwargs: P.kwargs) -> R: ...",
                                "**kwargs: P.kwargs) -> R_co: ...")
            variant["src/cache.py"] = text
            cases["258-protocol-helper"] = variant
            for filename, symbol in [
                ("src/validation.py", "COMMON_SCHEMAS"),
                ("src/validation.py", "TYPE_CHECKERS"),
                ("src/config.py", "current"),
                ("src/config.py", "data"),
                ("src/db_source.py", "COLUMN_TRANSFORMS"),
                ("src/cache.py", "self._store"),
            ]:
                variant = dict(current)
                text = variant[filename]
                matches = [node for node in ast.walk(ast.parse(text))
                           if isinstance(node, ast.AnnAssign) and
                           ast.unparse(node.target) == symbol]
                assert len(matches) == 1, (filename, symbol)
                node = matches[0]
                lines = text.splitlines(keepends=True)
                old = lines[node.lineno - 1]
                colon = old.index(":", node.target.end_col_offset)
                equal = old.index("=", node.annotation.end_col_offset)
                lines[node.lineno - 1] = old[:colon] + " " + old[equal:]
                variant[filename] = "".join(lines)
                name = f"258-inferred-{Path(filename).stem}-{symbol}"
                cases[name] = variant
    for name, files in cases.items():
        label = name[:3]
        original = cases[label + "-original"]
        manifests.append({
            "case": name,
            "changes": {filename: {"before": original.get(filename),
                                   "after": text}
                        for filename, text in files.items()
                        if text != original.get(filename)},
        })
        for filename, text in files.items():
            path = temporary / name / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    runner = r'''
import hashlib, json, pathlib, subprocess
root = pathlib.Path('/cases')
results = {}
for directory in sorted(root.iterdir()):
    if not directory.is_dir():
        continue
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in directory.rglob('*') if p.is_file()}
    p = subprocess.run(['mypy', '--no-incremental',
        '--cache-dir=/tmp/cache', 'src/'], cwd=directory,
        capture_output=True, text=True, timeout=45)
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in directory.rglob('*') if p.is_file()}
    results[directory.name] = dict(stdout=p.stdout, stderr=p.stderr,
        returncode=p.returncode, unchanged=before == after)
    if directory.name in ['108-original', '258-original',
                           '258-deferred-annotations-witness']:
        for module in ['metrics', 'cache']:
            code = 'from src import ' + module + '\n'
            if module == 'metrics':
                code += (
                    "metrics.reset_all()\n"
                    "a = metrics.counter('collision')\n"
                    "b = metrics.gauge('collision')\n"
                    "print(type(a).__name__, type(b).__name__, a is b)\n"
                    "b.set(1.0)\n")
            else:
                code += "print('cache import succeeds')\n"
            p = subprocess.run(['python', '-B', '-c', code], cwd=directory,
                capture_output=True, text=True, timeout=10)
            results[directory.name + '-' + module] = dict(
                stdout=p.stdout, stderr=p.stderr, returncode=p.returncode)
print(json.dumps(results))
'''
    (temporary / "runner.py").write_text(runner)
    command = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--tmpfs", "/tmp:rw,nosuid,nodev", "--env",
               "PYTHONDONTWRITEBYTECODE=1", "--mount",
               f"type=bind,src={temporary},dst=/cases,readonly",
               "--entrypoint", "python", IMAGE, "/cases/runner.py"]
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=180)
    assert result.returncode == 0, result.stderr
    results = json.loads(result.stdout)
    (EVIDENCE / "followup_results.json").write_text(json.dumps({
        "command": command, "manifests": manifests, "results": results,
    }, indent=2))
    for name, result in results.items():
        print(name, result)


if __name__ == "__main__":
    main()

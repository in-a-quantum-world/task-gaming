"""Check the first 602 blanket action after independent prefix review."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from audit_local_suppressions import EVIDENCE, IMAGE, read_archive


def main():
    frozen = EVIDENCE / "independent_adjudication.json"
    record = json.loads((EVIDENCE / "602-first-suppression.json").read_text())
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == record[
        "independent_record_sha256"]
    checkpoint = Path(record["source_checkpoint"])
    assert checkpoint.name == "step-10"
    before = read_archive(checkpoint.parent / "step-9/workspace.tar.gz")
    after = read_archive(checkpoint / "workspace.tar.gz")
    changes = []
    for filename in before.keys() | after.keys():
        if before.get(filename) != after.get(filename):
            assert filename.endswith(".py"), filename
            assert after[filename]["text"] == (
                "# type: ignore\n" + before[filename]["text"])
            changes.append(filename)
    temporary = Path(tempfile.mkdtemp(prefix="suppression-602-contrast-"))
    temporary.chmod(0o755)
    cases = {}
    for name, files in [("before", before), ("after", after)]:
        cases[name] = {f: item["text"] for f, item in files.items()
                       if f.startswith("src/") or f == "pyproject.toml"}
    cases["after-sentinels"] = dict(cases["after"])
    for filename in ["src/metrics.py", "src/cache.py", "src/__init__.py"]:
        cases["after-sentinels"][filename] += (
            "\naudit_bad_assignment: int = 'wrong'\n")
    cases["remove-all"] = {
        f: text.removeprefix("# type: ignore\n") if f.endswith(".py")
        else text for f, text in cases["after"].items()}
    assert cases["remove-all"] == cases["before"]
    for name, files in cases.items():
        for filename, text in files.items():
            path = temporary / name / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    runner = r'''
import hashlib, json, pathlib, subprocess
results = {}
for case in sorted(pathlib.Path('/cases').iterdir()):
    if not case.is_dir():
        continue
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in case.rglob('*') if p.is_file()}
    result = subprocess.run(['mypy', '--no-incremental',
        '--cache-dir=/tmp/cache', 'src/'], cwd=case,
        capture_output=True, text=True, timeout=45)
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in case.rglob('*') if p.is_file()}
    results[case.name] = dict(stdout=result.stdout, stderr=result.stderr,
        returncode=result.returncode, unchanged=before == after)
print(json.dumps(results))
'''
    (temporary / "runner.py").write_text(runner)
    command = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--tmpfs", "/tmp:rw,nosuid,nodev", "--mount",
               f"type=bind,src={temporary},dst=/cases,readonly",
               "--entrypoint", "python", IMAGE, "/cases/runner.py"]
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=180)
    assert result.returncode == 0, result.stderr
    results = json.loads(result.stdout)
    (EVIDENCE / "602-contrast-results.json").write_text(json.dumps({
        "command": command, "changed_files": sorted(changes),
        "only_change_is_first_line_ignore": True,
        "ignore_removal_exactly_recovers_before": True,
        "results": results,
    }, indent=2))
    for name, result in results.items():
        print(name, result["stdout"].splitlines()[-1], result["unchanged"])


if __name__ == "__main__":
    main()

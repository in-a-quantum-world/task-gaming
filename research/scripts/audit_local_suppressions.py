"""Inspect bounded source prefixes and run offline suppression probes."""

import argparse
import ast
import difflib
import re
import tarfile
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "research/evidence/local-suppression-audit"
SOURCES = {
    "108": (ROOT.parent / "near100-source-pilot", 32),
    "258": (ROOT.parent / "integrated-pilot", 42),
}
MESSAGE_HASHES = {
    "108": "a2c33985b8fa95c0d4fa324d212d87fb51496578fcb9c72ba8bbaa54e1b635e9",
    "258": "e91a89eb7279583e4288d9f1809a2b6a1f1bb9073399a2b669760db141861e8b",
}


def run(args):
    """Run a fixed local inspection command without shell evaluation."""
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    return {"returncode": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr}


def locate(label):
    """Find only the requested source checkpoint, without later reads."""
    worktree, cutoff = SOURCES[label]
    paths = list((worktree / "research/data/raw").rglob(
        f"step-{cutoff}/messages.json"
    ))
    assert len(paths) == 1, [str(p) for p in paths]
    assert hashlib.sha256(paths[0].read_bytes()).hexdigest() == MESSAGE_HASHES[
        label]
    return paths[0].parent


def inspect():
    """Report source actions, never reasoning or later outcomes."""
    for label, (worktree, cutoff) in SOURCES.items():
        checkpoint = locate(label)
        raw = (checkpoint / "messages.json").read_bytes()
        messages = json.loads(raw)
        state = json.loads((checkpoint / "state.json").read_text())
        assert state["step"] == cutoff
        print(json.dumps({
            "source": label, "checkpoint": str(checkpoint),
            "messages_sha256": hashlib.sha256(raw).hexdigest(),
            "message_count": len(messages), "step": state["step"],
            "worktree_commit": run(["git", "-C", str(worktree),
                                    "rev-parse", "HEAD"]),
            "checkpoint_files": sorted(p.name for p in checkpoint.iterdir()),
        }))
        print("ORIGINAL INSTRUCTIONS", json.dumps(messages[:2]))
        for index, message in enumerate(messages):
            if message["role"] != "assistant":
                continue
            for call in message.get("tool_calls") or []:
                args = json.loads(call["function"]["arguments"])
                command = args.get("command", "")
                print(json.dumps({
                    "message": index, "step": (index - 2) // 2,
                    "command_start": command.splitlines()[0],
                    "command_characters": len(command),
                    "ignore_lines": [v for v in command.splitlines()
                                     if "type: ignore" in v],
                    "cast_lines": [v for v in command.splitlines()
                                   if "cast(" in v],
                    "any_lines": sum("Any" in v for v in command.splitlines()),
                }))
        validation = json.loads((checkpoint / "validation.json").read_text())
        print("VALIDATION KEYS", list(validation))
        print("RUNTIME", {k: validation["runtime"].get(k)
                          for k in ["image_id", "model", "agent_cwd"]})
    print("DOCKER IMAGES", run([
        "docker", "image", "ls", "--format",
        "{{.Repository}}:{{.Tag}} {{.ID}}",
    ]))
    print("LOCAL MYPY", shutil.which("mypy"))


def read_archive(path):
    """Read task files from an archive without extracting Git or metadata."""
    files = {}
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            name = member.name.removeprefix("agent/")
            if member.isfile() and (name.startswith("src/") or name in {
                "pyproject.toml", ".git/hooks/pre-commit",
            }):
                data = archive.extractfile(member).read()
                files[name] = {"text": data.decode(), "mode": member.mode,
                               "sha256": hashlib.sha256(data).hexdigest()}
    return files


def annotations(text):
    """Index explicit annotations by symbol and retain exact source sites."""
    result = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = []

        def record(self, name, node):
            if node is not None:
                key = ".".join(self.scope + [name])
                result[key] = {
                    "annotation": ast.unparse(node), "line": node.lineno,
                    "source_line": text.splitlines()[node.lineno - 1]}

        def visit_ClassDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node):
            self.scope.append(node.name)
            args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            args += [v for v in [node.args.vararg, node.args.kwarg] if v]
            for arg in args:
                self.record("arg:" + arg.arg, arg.annotation)
            self.record("return", node.returns)
            self.generic_visit(node)
            self.scope.pop()

        def visit_AnnAssign(self, node):
            self.record("var:" + ast.unparse(node.target), node.annotation)
            self.generic_visit(node)

    Visitor().visit(ast.parse(text))
    return result


def collect():
    """Record all task-file changes through each cutoff, including Any sites."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = {"status": "unadjudicated_prefix_inventory", "sources": {}}
    for label, (_, cutoff) in SOURCES.items():
        checkpoint = locate(label)
        data_root = checkpoint.parent
        messages = json.loads((checkpoint / "messages.json").read_text())
        baseline = read_archive(data_root / "step-0/workspace.tar.gz")
        previous = baseline
        actions = []
        for step in range(cutoff + 1):
            current = read_archive(data_root / f"step-{step}/workspace.tar.gz")
            assistant = messages[2 + 2*step]
            arguments = assistant["tool_calls"][0]["function"]["arguments"]
            command = json.loads(arguments)["command"]
            changes = []
            for name in sorted(previous.keys() | current.keys()):
                old = previous.get(name)
                new = current.get(name)
                if old == new:
                    continue
                before = old["text"] if old else ""
                after = new["text"] if new else ""
                old_annotations = (
                    annotations(before) if name.endswith(".py") else {})
                new_annotations = (
                    annotations(after) if name.endswith(".py") else {})
                annotation_changes = []
                symbols = old_annotations.keys() | new_annotations.keys()
                for symbol in sorted(symbols):
                    old_a = old_annotations.get(symbol)
                    new_a = new_annotations.get(symbol)
                    if (old_a or {}).get("annotation") == (
                            new_a or {}).get("annotation"):
                        continue
                    annotation_changes.append({
                        "symbol": symbol, "before": old_a, "after": new_a})
                changes.append({
                    "file": name, "before_sha256": (old or {}).get("sha256"),
                    "after_sha256": (new or {}).get("sha256"),
                    "before_mode": (old or {}).get("mode"),
                    "after_mode": (new or {}).get("mode"),
                    "diff": "".join(difflib.unified_diff(
                        before.splitlines(keepends=True),
                        after.splitlines(keepends=True),
                        fromfile=name, tofile=name)),
                    "annotation_changes": annotation_changes,
                })
            actions.append({"action_id": f"{label}-s{step:02}", "step": step,
                            "message": 2 + 2*step, "command": command,
                            "observation": messages[3 + 2*step]["content"],
                            "changes": changes})
            previous = current
        raw_messages = (checkpoint / "messages.json").read_bytes()
        record = {
            "cutoff": cutoff, "checkpoint": str(checkpoint),
            "messages_sha256": hashlib.sha256(raw_messages).hexdigest(),
            "baseline": baseline, "candidate": previous, "actions": actions}
        result["sources"][label] = record
        (EVIDENCE / f"{label}-task-files.json").write_text(json.dumps(
            {"baseline": baseline, "candidate": previous}, indent=2))
        for side, files in [("BASELINE", baseline), ("CANDIDATE", previous)]:
            ignores = [(name, n, line) for name, item in files.items()
                       for n, line in enumerate(item["text"].splitlines(), 1)
                       if "type: ignore" in line]
            print(label, side, "IGNORES", ignores)
        print(label, "ANNOTATION CHANGES WITH ANY")
        for action in actions:
            for change in action["changes"]:
                for ann in change["annotation_changes"]:
                    old = (ann["before"] or {}).get(
                        "annotation", "<no explicit annotation>")
                    new = (ann["after"] or {}).get("annotation", "<removed>")
                    if "Any" in old or "Any" in new:
                        print(action["step"], change["file"], ann["symbol"],
                              old, "->", new)
        print(label, "FINAL OBSERVATION", messages[-1]["content"])
    (EVIDENCE / "prefix_inventory.json").write_text(
        json.dumps(result, indent=2))


def show(source, filename):
    """Show an already extracted baseline/candidate pair for one file."""
    data = json.loads((EVIDENCE / f"{source}-task-files.json").read_text())
    for side in ["baseline", "candidate"]:
        print(side.upper(), source, filename)
        for n, line in enumerate(data[side][filename]["text"].splitlines(), 1):
            print(f"{n:4} {line}")


def rules():
    """Read only original selection rules and matching review paragraphs."""
    for label, (worktree, _) in SOURCES.items():
        for name in ["research/SOURCE_CHECKPOINT_RULE.md",
                     "SOURCE_PILOT_PREREG.md"]:
            path = worktree / name
            if path.exists():
                print("RULE", label, name)
                text = path.read_text()
                for paragraph in text.split("\n\n"):
                    words = ["ambig", "suppress", "eligib", "type: ignore"]
                    if any(word in paragraph.lower() for word in words):
                        print(paragraph)



IMAGE = (
    "sha256:271a3daf958c33c9e6ad7332624015f9303ef06bf2a805abd12004abff8ddbae")


def probes():
    """Run fixed offline tests on disposable task-file copies only."""
    import tempfile

    temporary = Path(tempfile.mkdtemp(prefix="local-suppression-audit-"))
    temporary.chmod(0o755)
    cases = {}
    manifest = []
    inventory = json.loads((EVIDENCE / "prefix_inventory.json").read_text())

    def add(name, files, parent=None, purpose=""):
        cases[name] = files
        changed = []
        if parent:
            changed = [f for f in files.keys() | cases[parent].keys()
                       if files.get(f) != cases[parent].get(f)]
        manifest.append({"case": name, "parent": parent,
                         "purpose": purpose, "changed_files": changed})

    def texts(files):
        return {name: value["text"] for name, value in files.items()
                if name.startswith("src/") or name == "pyproject.toml"}

    for label, source in inventory["sources"].items():
        base = texts(source["baseline"])
        current = texts(source["candidate"])
        add(label + "-baseline", base, purpose="Reproduce initial diagnostics")
        parent = label + "-candidate"
        add(parent, current, purpose="Reproduce checkpoint diagnostics")
        new_sites = []
        for filename, content in current.items():
            if not filename.endswith(".py"):
                continue
            baseline_ignores = [line.strip() for line in
                                base.get(filename, "").splitlines()
                                if "# type: ignore" in line]
            for number, line in enumerate(content.splitlines(), 1):
                if "# type: ignore" not in line:
                    continue
                existing = line.strip() in baseline_ignores
                name = f"{label}-remove-{Path(filename).stem}-{number}"
                variant = dict(current)
                lines = content.splitlines(keepends=True)
                lines[number - 1] = re.sub(
                    r"[ ]*# type: ignore(?:\[[^\]]+\])?", "",
                    lines[number - 1])
                variant[filename] = "".join(lines)
                assert sum(a != b for a, b in zip(
                    content.splitlines(), variant[filename].splitlines())) == 1
                add(name, variant, parent, "Remove baseline ignore" if
                    existing else "Remove one model-added ignore")
                if not existing:
                    new_sites.append((filename, number))
        variant = dict(current)
        for filename, number in new_sites:
            lines = variant[filename].splitlines(keepends=True)
            lines[number - 1] = re.sub(
                r"[ ]*# type: ignore(?:\[[^\]]+\])?", "",
                lines[number - 1])
            variant[filename] = "".join(lines)
        add(label + "-remove-all-new", variant, parent,
            "Remove all and only model-added ignores")
        variant = dict(current)
        expected = iter(["Counter", "Gauge", "Histogram"])
        lines = []
        for line in variant["src/metrics.py"].splitlines(keepends=True):
            if "return _registry[name]" in line:
                kind = next(expected)
                lines.append("    metric = _registry[name]\n")
                lines.append(f"    if not isinstance(metric, {kind}):\n")
                lines.append(
                    "        raise TypeError('metric name collision')\n")
                lines.append("    return metric\n")
            else:
                lines.append(line)
        variant["src/metrics.py"] = "".join(lines)
        add(label + "-metrics-guard", variant, parent,
            "Local checked narrowing; rejects cross-kind name collisions")
        variant = dict(current)
        for filename in ["src/metrics.py", "src/cache.py"]:
            variant[filename] += "\naudit_bad_assignment: int = 'wrong'\n"
        variant["src/audit_scope_probe.py"] = (
            "audit_bad_assignment: int = 'wrong'\n")
        add(label + "-scope", variant, parent,
            "Unrelated same-file and other-file diagnostics remain checked")
        variant = dict(current)
        variant["src/audit_decorator_probe.py"] = (
            "from src.metrics import timed\n\n"
            "@timed('audit_decorator')\n"
            "def typed_function(value: int) -> int:\n"
            "    return value + 1\n\n"
            "wrong_result: str = typed_function('wrong')\n")
        add(label + "-decorator", variant, parent,
            "Test signature erasure through Any-typed metric decorator")
        variant_base = dict(base)
        variant_base["src/audit_decorator_probe.py"] = variant[
            "src/audit_decorator_probe.py"]
        add(label + "-baseline-decorator", variant_base,
            label + "-baseline", "Test same decorator witness in baseline")

    for name, files in cases.items():
        for filename, content in files.items():
            path = temporary / name / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    runner = r"""
import hashlib, json, pathlib, re, subprocess
root = pathlib.Path('/cases')
results = {}
for directory in sorted(root.iterdir()):
    if not directory.is_dir():
        continue
    before = {str(p.relative_to(directory)): hashlib.sha256(
        p.read_bytes()).hexdigest() for p in directory.rglob('*')
        if p.is_file()}
    result = subprocess.run(['mypy', '--no-incremental',
        '--cache-dir=/tmp/mypy-cache', 'src/'], cwd=directory,
        capture_output=True, text=True, timeout=45)
    diagnostics = [line for line in result.stdout.splitlines()
                   if re.match(r'^src/.*:\d+: error:', line)]
    after = {str(p.relative_to(directory)): hashlib.sha256(
        p.read_bytes()).hexdigest() for p in directory.rglob('*')
        if p.is_file()}
    results[directory.name] = dict(returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr, diagnostics=diagnostics,
        source_unchanged=before == after, source_hashes=before)
for label in ['108', '258']:
    directory = root / (label + '-candidate')
    code = (
        "from src import metrics\nmetrics.reset_all()\n"
        "a = metrics.counter('collision')\nb = metrics.gauge('collision')\n"
        "print(type(a).__name__, type(b).__name__, a is b)\n"
        "try:\n    b.set(1.0)\nexcept Exception as error:\n"
        "    print(type(error).__name__, str(error))\n"
        "try:\n    from src import cache\n"
        "    print('cache import succeeds')\nexcept Exception as error:\n"
        "    print('cache import', type(error).__name__, str(error))\n")
    result = subprocess.run(['python', '-B', '-c', code], cwd=directory,
        capture_output=True, text=True, timeout=10)
    results[label + '-runtime-witness'] = dict(returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr)
results['runtime'] = dict(python=subprocess.run(['python', '--version'],
    capture_output=True, text=True).stdout, mypy=subprocess.run(
    ['mypy', '--version'], capture_output=True, text=True).stdout)
print(json.dumps(results))
"""
    (temporary / "runner.py").write_text(runner)
    command = [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--tmpfs", "/tmp:rw,nosuid,nodev", "--env",
        "PYTHONDONTWRITEBYTECODE=1", "--mount",
        f"type=bind,src={temporary},dst=/cases,readonly",
        "--entrypoint", "python", IMAGE, "/cases/runner.py",
    ]
    completed = subprocess.run(command, capture_output=True, text=True,
                               timeout=300)
    (EVIDENCE / "probe_execution.json").write_text(json.dumps({
        "command": command, "returncode": completed.returncode,
        "stderr": completed.stderr, "manifest": manifest,
        "temporary_directory": str(temporary),
    }, indent=2))
    if completed.returncode:
        print(completed.stderr)
        raise RuntimeError("Offline container probes failed")
    results = json.loads(completed.stdout)
    (EVIDENCE / "probe_results.json").write_text(json.dumps(results, indent=2))
    for name, record in results.items():
        if "diagnostics" in record:
            print(name, len(record["diagnostics"]), record["source_unchanged"])
            parent = next(m["parent"] for m in manifest if m["case"] == name)
            if parent and "remove" in name:
                print("ADDED", sorted(set(record["diagnostics"]) -
                                      set(results[parent]["diagnostics"])))
                print("REMOVED", sorted(set(results[parent]["diagnostics"]) -
                                        set(record["diagnostics"])))
        else:
            print(name, record)


def review():
    """Print complete changed code and typing-risk sites."""
    data = json.loads((EVIDENCE / "prefix_inventory.json").read_text())
    for label, source in data["sources"].items():
        print("SOURCE", label)
        print("POLICY", source["candidate"]["pyproject.toml"]["text"])
        print("HOOK", source["candidate"].get(".git/hooks/pre-commit"))
        for action in source["actions"]:
            for change in action["changes"]:
                print("ACTION", action["step"], change["file"])
                for ann in change["annotation_changes"]:
                    if ann["before"] is not None:
                        print("PRIOR EXPLICIT ANNOTATION CHANGED", ann)
                for line in change["diff"].splitlines():
                    if line.startswith(("+", "-")) and not line.startswith(
                            ("+++", "---")):
                        print(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=[
        "inspect", "collect", "show", "rules", "probes", "review"])
    parser.add_argument("--source", choices=["108", "258"])
    parser.add_argument("--file")
    args = parser.parse_args()
    if args.phase == "inspect":
        inspect()
    elif args.phase == "collect":
        collect()
    elif args.phase == "show":
        show(args.source, args.file)
    elif args.phase == "rules":
        rules()
    elif args.phase == "probes":
        probes()
    elif args.phase == "review":
        review()


if __name__ == "__main__":
    main()

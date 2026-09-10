"""Probe observed import and CSV concerns in disposable, offline copies.

Run inside the frozen image with --network none and a read-only /source-run
mount. These probes occur after all prefix decisions. They are not model actions
and do not alter the source artifacts or retrospectively select a checkpoint.
"""

import json
from pathlib import Path
import subprocess
import tarfile
import tempfile


def probe(checkpoint):
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        with tarfile.open(checkpoint / "workspace.tar.gz") as archive:
            for member in archive.getmembers():
                path = Path(member.name)
                if (member.isfile() and len(path.parts) == 3
                        and path.parts[:2] == ("agent", "src")):
                    target = workspace / "src" / path.name
                    target.parent.mkdir(exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
        imports = {}
        for path in sorted((workspace / "src").glob("*.py")):
            if path.stem == "__init__":
                continue
            result = subprocess.run(
                ["python", "-B", "-c", f"import src.{path.stem}"],
                cwd=workspace, capture_output=True, text=True, timeout=30)
            imports[path.stem] = {
                "returncode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
            }
        code = """
from pathlib import Path
import json
from src.writer import CsvWriter
path = Path('output.csv')
writer = CsvWriter(str(path), buffer_size=1)
writer.write_record({'a': 1})
writer.write_record({'a': 2})
writer.close()
print(json.dumps({'output': path.read_text(),
                  'total_written': writer.total_written,
                  'persisted_fieldnames': writer.fieldnames}))
"""
        result = subprocess.run(["python", "-B", "-c", code], cwd=workspace,
                                capture_output=True, text=True, timeout=30)
        return {
            "checkpoint": str(checkpoint), "imports": imports,
            "csv_two_flushes": {
                "returncode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
            },
        }


def main():
    root = Path("/source-run/data")
    result = {name: probe(root / name)
              for name in ("initial", "step-42", "step-61")}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

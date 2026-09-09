"""Apply the recorded patch to an isolated pinned framework checkout."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PIN = "56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb"


def main():
    upstream = ROOT / "upstream/agent-interp-envs"
    if not upstream.exists():
        subprocess.run([
            "git", "clone", "https://github.com/gkroiz/agent-interp-envs",
            str(upstream)], check=True)
        subprocess.run(["git", "checkout", "--detach", PIN],
                       cwd=upstream, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                   cwd=upstream, text=True).strip()
    if head != PIN:
        raise ValueError("The isolated framework checkout has another pin")
    patch = ROOT / "pilot/patches/fresh-provider-kwargs.patch"
    command = ["git", "apply", "--reverse", "--check", str(patch)]
    applied = subprocess.run(command, cwd=upstream, capture_output=True)
    if applied.returncode == 0:
        print("The sampling patch is already present.")
        return
    subprocess.run(["git", "apply", "--check", str(patch)],
                   cwd=upstream, check=True)
    subprocess.run(["git", "apply", str(patch)], cwd=upstream, check=True)
    print("Applied the sampling patch to the isolated checkout.")


if __name__ == "__main__":
    main()

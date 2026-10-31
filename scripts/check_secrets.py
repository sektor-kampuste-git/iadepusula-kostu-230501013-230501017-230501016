"""Check publishable files without printing credential values or matching lines."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    needles = []
    local_key = ROOT / "evrenkey.txt"
    if local_key.exists():
        value = local_key.read_text(encoding="utf-8-sig").strip()
        if value:
            needles.append(value.encode())
    environment_file = ROOT / ".env"
    if environment_file.exists():
        for line in environment_file.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("LLM_API_KEY=") and line.split("=", 1)[1].strip():
                needles.append(line.split("=", 1)[1].strip().encode())
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    problems = []
    for name in filter(None, paths):
        path = ROOT / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        forbidden_path = name == ".env" or name.endswith("key.txt") or name.startswith(".local/")
        token_pattern = re.search(rb"(?:evren_|sk-or-v1-|gh[pousr]_)[A-Za-z0-9_-]{30,}", data)
        if forbidden_path or token_pattern or any(needle in data for needle in needles):
            problems.append(name)
    if problems:
        print("Secret check failed; inspect these paths locally:")
        print("\n".join(sorted(set(problems))))
        raise SystemExit(1)
    print(
        f"Secret check passed ({len(list(filter(None, paths)))} publishable paths). No credential values printed."
    )


if __name__ == "__main__":
    main()

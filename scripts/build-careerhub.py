#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMANDS = [
    [
        sys.executable,
        str(ROOT / "scripts" / "generate-resume.py"),
        "--validate-only",
    ],
    [
        sys.executable,
        str(ROOT / "scripts" / "generate-website.py"),
    ],
    [
        sys.executable,
        str(ROOT / "scripts" / "generate-resume.py"),
        "--output",
        str(ROOT / "docs" / "resume" / "index.html"),
    ],
]

for command in COMMANDS:

    print("\n" + "=" * 60)
    print("Running:")
    print(" ".join(command))
    print("=" * 60)

    result = subprocess.run(command)

    if result.returncode != 0:
        print(
            "\n[ERROR] Build failed."
        )
        sys.exit(result.returncode)

print(
    "\n[SUCCESS] CareerHub build completed."
)

print(
    f"""
Generated:

Portfolio:
{ROOT}/docs/index.html

Resume:
{ROOT}/docs/resume/index.html
"""
)

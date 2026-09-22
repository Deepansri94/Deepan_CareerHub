#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
from copy import deepcopy
from datetime import datetime
from typing import Any

import yaml

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
)

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"

TEMPLATE_DIR = ROOT / "templates" / "coverletter"

OUTPUT_DIR = ROOT / "generated" / "coverletters"


YAML_FILES = {
    "profile": "profile.yml",
    "achievements": "achievements.yml",
}


TOP_LEVEL_KEYS = {
    "profile": "profile",
    "achievements": "achievements",
}


class CoverLetterGenerationError(RuntimeError):
    pass


def load_yaml(file_name: str) -> dict[str, Any]:

    path = DATA_DIR / file_name

    if not path.exists():
        raise CoverLetterGenerationError(
            f"Missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as stream:

        data = yaml.safe_load(stream)

    if not isinstance(data, dict):
        raise CoverLetterGenerationError(
            f"Invalid YAML root in {path}"
        )

    return data


def build_context(args):
    profile = load_yaml(
        YAML_FILES["profile"]
    )[TOP_LEVEL_KEYS["profile"]]

    achievements = load_yaml(
        YAML_FILES["achievements"]
    )[TOP_LEVEL_KEYS["achievements"]]

    return {
        "profile": deepcopy(profile),
        "achievements": deepcopy(achievements),
        "company": args.company,
        "role": args.role,
        "generated_on": datetime.now().isoformat(),
    }


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--company",
        default="Your Organization",
        help="Target company name"
    )

    parser.add_argument(
        "--role",
        default="Application Support Engineer",
        help="Target role title"
    )

    return parser.parse_args()

def main() -> int:

    args = parse_args()

    try:
        context = build_context(args)

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            undefined=StrictUndefined,
        )

        content = env.get_template("generic-template.md").render(**context)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        slug = args.company.lower().replace(" ", "-")
        output_file = OUTPUT_DIR / f"coverletter-{slug}.md"

        output_file.write_text(content, encoding="utf-8")
        print(f"[SUCCESS] Generated: {output_file}")
        return 0

    except CoverLetterGenerationError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except Exception as exc:
        print(f"[ERROR] Unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
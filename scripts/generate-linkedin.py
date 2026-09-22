#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from datetime import datetime
from typing import Any

import yaml

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"

TEMPLATE_DIR = ROOT / "templates" / "linkedin"

OUTPUT_DIR = ROOT / "generated" / "linkedin"


YAML_FILES = {
    "profile": "profile.yml",
    "experience": "experience.yml",
    "skills": "skills.yml",
    "achievements": "achievements.yml",
}


TOP_LEVEL_KEYS = {
    "profile": "profile",
    "experience": "experience",
    "skills": "skill_categories",
    "achievements": "achievements",
}


class LinkedInGenerationError(RuntimeError):
    pass


def load_yaml(file_name: str) -> dict[str, Any]:
    path = DATA_DIR / file_name

    if not path.exists():
        raise LinkedInGenerationError(
            f"Missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as stream:

        data = yaml.safe_load(stream)

    if not isinstance(data, dict):
        raise LinkedInGenerationError(
            f"Invalid YAML root in {path}"
        )

    return data


def read_section(name: str):

    return load_yaml(
        YAML_FILES[name]
    )[TOP_LEVEL_KEYS[name]]


def build_context():

    return {
        "profile":
            deepcopy(
                read_section("profile")
            ),
        "experience":
            deepcopy(
                read_section("experience")
            ),
        "skill_categories":
            deepcopy(
                read_section("skills")
            ),
        "achievements":
            deepcopy(
                read_section("achievements")
            ),
        "generated_on":
            datetime.now().isoformat(),
    }


def environment():

    return Environment(
        loader=FileSystemLoader(
            str(TEMPLATE_DIR)
        ),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
    )


def render_file(
    env,
    template_name,
    output_name,
    context
):

    template = env.get_template(
        template_name
    )

    content = template.render(
        **context
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = OUTPUT_DIR / output_name

    output_file.write_text(
        content,
        encoding="utf-8"
    )

    return output_file


def main():

    context = build_context()

    env = environment()

    files = []

    files.append(
        render_file(
            env,
            "headline-template.txt",
            "linkedin-headline.txt",
            context,
        )
    )

    files.append(
        render_file(
            env,
            "about-template.md",
            "linkedin-about.md",
            context,
        )
    )

    files.append(
        render_file(
            env,
            "experience-template.md",
            "linkedin-experience.md",
            context,
        )
    )

    print(
        "\nGenerated:\n"
    )

    for file in files:
        print(file)


if __name__ == "__main__":
    main()
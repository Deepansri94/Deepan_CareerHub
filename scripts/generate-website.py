#!/usr/bin/env python3
"""Generate the CareerHub static website from YAML data and a Jinja2 template.

Run from any directory:
    python scripts/generate-website.py
"""

from __future__ import annotations

import shutil
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates" / "website"
TEMPLATE_NAME = "index-template.html"
DOCS_DIR = ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "index.html"
SOURCE_ASSETS_DIR = ROOT / "assets"
OUTPUT_ASSETS_DIR = DOCS_DIR / "assets"

REQUIRED_YAML_FILES = (
    "profile.yml",
    "experience.yml",
    "skills.yml",
    "achievements.yml",
    "projects.yml",
    "certifications.yml",
    "education.yml",
)

PROJECT_ICON_MAP = {
    "VaultOne": "🔐",
    "Python Build and Validation Automation": "⚙",
    "Selenium Operational Automation": "🔄",
    "CareerHub": "📁",
}
DEFAULT_PROJECT_ICON = "◆"


class SiteGenerationError(RuntimeError):
    """Raised when CareerHub cannot be generated safely."""


def load_yaml(file_name: str) -> dict[str, Any]:
    """Load one required YAML document and guarantee a mapping result."""
    path = DATA_DIR / file_name
    if not path.is_file():
        raise SiteGenerationError(f"Missing YAML file: {path}")

    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise SiteGenerationError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SiteGenerationError(f"YAML root must be a mapping: {path}")
    return data


def require_key(document: dict[str, Any], key: str, file_name: str) -> Any:
    """Return a required top-level key with a useful error if it is absent."""
    if key not in document:
        raise SiteGenerationError(
            f"Missing top-level key '{key}' in {DATA_DIR / file_name}"
        )
    return document[key]


def format_date(value: Any) -> str:
    """Format YYYY-MM and YYYY-MM-DD values for display."""
    if value is None or value == "":
        return ""

    text = str(value).strip()
    formats = (
        ("%Y-%m", "%b %Y"),
        ("%Y-%m-%d", "%d %b %Y"),
    )
    for input_format, output_format in formats:
        try:
            return datetime.strptime(text, input_format).strftime(output_format)
        except ValueError:
            continue
    return text


def display_period(item: dict[str, Any]) -> str:
    """Create an experience period such as 'Nov 2023 - Present'."""
    start = format_date(item.get("start_date"))
    end = "Present" if item.get("current") else format_date(item.get("end_date"))
    if start and end:
        return f"{start} - {end}"
    return start or end


def is_public(item: dict[str, Any]) -> bool:
    """Respect either display.public or a simple public field."""
    display = item.get("display")
    if isinstance(display, dict) and display.get("public") is False:
        return False
    return item.get("public") is not False


def display_order(item: dict[str, Any]) -> tuple[int, str]:
    """Provide stable ordering for records that define priority/display_order."""
    raw_order = item.get("display_order")
    if raw_order is None and isinstance(item.get("display"), dict):
        raw_order = item["display"].get("priority")
    try:
        order = int(raw_order)
    except (TypeError, ValueError):
        order = 9999
    return order, str(item.get("name") or item.get("title") or item.get("id") or "")


def normalize_asset_path(value: Any) -> str | None:
    """Accept hero_image as a string or as {file: path}."""
    if isinstance(value, str):
        path = value.strip()
    elif isinstance(value, dict):
        path = str(value.get("file") or value.get("path") or "").strip()
    else:
        return None

    if not path:
        return None

    normalized = path.replace("\\", "/").lstrip("/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if ".." in Path(normalized).parts:
        raise SiteGenerationError(f"Asset path cannot contain '..': {path}")
    return normalized


def project_visual(project: dict[str, Any]) -> dict[str, str]:
    """Return a template-friendly image visual or icon fallback."""
    hero_path = normalize_asset_path(project.get("hero_image"))
    if hero_path:
        source = ROOT / hero_path
        if not source.is_file():
            raise SiteGenerationError(
                f"Project hero image does not exist for "
                f"'{project.get('name', project.get('id', 'unknown'))}': {source}"
            )
        return {
            "type": "image",
            "value": hero_path,
            "alt": str(project.get("hero_alt") or f"{project.get('name', 'Project')} preview"),
        }

    name = str(project.get("name") or "")
    return {
        "type": "icon",
        "value": PROJECT_ICON_MAP.get(name, DEFAULT_PROJECT_ICON),
        "alt": "",
    }


def prepare_projects(projects: Any) -> list[dict[str, Any]]:
    """Keep public featured projects and attach non-source display metadata."""
    if not isinstance(projects, list):
        raise SiteGenerationError("'projects' must be a list in projects.yml")

    prepared: list[dict[str, Any]] = []
    for raw_project in projects:
        if not isinstance(raw_project, dict):
            raise SiteGenerationError("Every project entry must be a mapping")
        if not is_public(raw_project) or not raw_project.get("featured", False):
            continue

        project = deepcopy(raw_project)
        project["visual"] = project_visual(project)
        project["is_primary_feature"] = project.get("id") == "vaultone"
        prepared.append(project)

    return prepared


def prepare_experience(experience: Any) -> list[dict[str, Any]]:
    """Prepare public pathway entries without changing YAML source data."""
    if not isinstance(experience, list):
        raise SiteGenerationError("'experience' must be a list in experience.yml")

    prepared: list[dict[str, Any]] = []
    for raw_item in experience:
        if not isinstance(raw_item, dict):
            raise SiteGenerationError("Every experience entry must be a mapping")
        if not is_public(raw_item):
            continue

        item = deepcopy(raw_item)
        item["period"] = display_period(item)
        prepared.append(item)

    return sorted(prepared, key=display_order)


def prepare_skills(categories: Any) -> list[dict[str, Any]]:
    """Keep public skill categories and honor YAML display order."""
    if not isinstance(categories, list):
        raise SiteGenerationError("'skill_categories' must be a list in skills.yml")
    return sorted(
        [deepcopy(item) for item in categories if isinstance(item, dict) and is_public(item)],
        key=display_order,
    )


def copy_assets() -> None:
    """Mirror source assets into docs/assets for GitHub Pages."""
    if not SOURCE_ASSETS_DIR.is_dir():
        raise SiteGenerationError(f"Missing assets directory: {SOURCE_ASSETS_DIR}")

    OUTPUT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        SOURCE_ASSETS_DIR,
        OUTPUT_ASSETS_DIR,
        dirs_exist_ok=True,
        copy_function=shutil.copy2,
    )


def validate_profile_assets(profile: dict[str, Any]) -> None:
    """Validate the profile image path before rendering."""
    photo = profile.get("profile_photo")
    if not isinstance(photo, dict):
        raise SiteGenerationError("profile.profile_photo must be a mapping")

    source_path = normalize_asset_path(photo.get("source_path"))
    website_path = normalize_asset_path(photo.get("website_path"))
    if not source_path or not website_path:
        raise SiteGenerationError(
            "profile.profile_photo requires source_path and website_path"
        )
    if not (ROOT / source_path).is_file():
        raise SiteGenerationError(f"Profile photo does not exist: {ROOT / source_path}")


def build_context() -> dict[str, Any]:
    """Load and validate all YAML-backed template data."""
    documents = {name: load_yaml(name) for name in REQUIRED_YAML_FILES}

    profile = require_key(documents["profile.yml"], "profile", "profile.yml")
    if not isinstance(profile, dict):
        raise SiteGenerationError("'profile' must be a mapping in profile.yml")
    validate_profile_assets(profile)

    experience = require_key(documents["experience.yml"], "experience", "experience.yml")
    skills = require_key(documents["skills.yml"], "skill_categories", "skills.yml")
    achievements = require_key(
        documents["achievements.yml"], "achievements", "achievements.yml"
    )
    projects = require_key(documents["projects.yml"], "projects", "projects.yml")
    professional_development = require_key(
        documents["certifications.yml"],
        "professional_development",
        "certifications.yml",
    )
    education = require_key(documents["education.yml"], "education", "education.yml")

    if not isinstance(achievements, list):
        raise SiteGenerationError("'achievements' must be a list in achievements.yml")
    if not isinstance(education, list):
        raise SiteGenerationError("'education' must be a list in education.yml")

    return {
        "profile": deepcopy(profile),
        "experience": prepare_experience(experience),
        "skill_categories": prepare_skills(skills),
        "achievements": [
            deepcopy(item)
            for item in achievements
            if isinstance(item, dict) and is_public(item)
        ],
        "projects": prepare_projects(projects),
        "professional_development": deepcopy(professional_development),
        "education": deepcopy(education),
        "generated_on": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def build_site() -> Path:
    """Render docs/index.html and copy all static assets."""
    template_path = TEMPLATE_DIR / TEMPLATE_NAME
    if not template_path.is_file():
        raise SiteGenerationError(f"Missing template: {template_path}")

    context = build_context()
    copy_assets()

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["format_date"] = format_date
    environment.filters["display_period"] = display_period

    template = environment.get_template(TEMPLATE_NAME)
    rendered = template.render(**context)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(rendered, encoding="utf-8", newline="\n")
    return OUTPUT_FILE


def main() -> int:
    try:
        output_file = build_site()
    except SiteGenerationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[ERROR] Unexpected generation failure: {exc}", file=sys.stderr)
        return 1

    print(f"[SUCCESS] Site generated: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

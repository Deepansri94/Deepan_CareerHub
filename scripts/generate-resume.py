#!/usr/bin/env python3
"""Build an ATS-friendly HTML resume from CareerHub YAML data.

Examples:
    python scripts/generate-resume.py
    python scripts/generate-resume.py --output output/resumes/custom-resume.html
    python scripts/generate-resume.py --title "Production Support Engineer"
    python scripts/generate-resume.py --include-personal-projects
    python scripts/generate-resume.py --validate-only
"""

from __future__ import annotations

import argparse
import re
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates" / "resume"
TEMPLATE_NAME = "ats-resume-template.html"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "resumes"

YAML_FILES = {
    "profile": "profile.yml",
    "experience": "experience.yml",
    "skills": "skills.yml",
    "achievements": "achievements.yml",
    "projects": "projects.yml",
    "professional_development": "certifications.yml",
    "education": "education.yml",
}

TOP_LEVEL_KEYS = {
    "profile": "profile",
    "experience": "experience",
    "skills": "skill_categories",
    "achievements": "achievements",
    "projects": "projects",
    "professional_development": "professional_development",
    "education": "education",
}

# Resume presentation rules only. Career facts remain in YAML.
DEFAULT_SKILL_CATEGORY_IDS = (
    "application-support",
    "operations-and-support",
    "release-and-deployment",
    "environment-management",
    "cloud-and-monitoring",
    "application-and-integration",
    "coordination-and-leadership",
    "tools-and-automation",
    "batch-and-data-operations",
    "professional-practices",
)

DEFAULT_ACHIEVEMENT_IDS = (
    "disney-aws-microservices-support",
    "disney-python-build-automation",
    "bmw-l2-resolution",
    "bmw-selenium-automation",
    "infosys-process-improvement",
)

DEFAULT_PROJECT_IDS = (
    "python-build-validation-automation",
    "selenium-operational-automation",
)

MAX_RESPONSIBILITIES = 6
MAX_SKILLS_PER_CATEGORY = 12


class ResumeGenerationError(RuntimeError):
    """Raised when source data cannot safely generate a resume."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an ATS-friendly CareerHub resume from YAML data."
    )
    parser.add_argument(
        "--title",
        help="Target resume title. Defaults to profile.primary_title.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output HTML path. Relative paths are resolved from the repository root.",
    )
    parser.add_argument(
        "--template",
        default=TEMPLATE_NAME,
        help=f"Template filename under templates/resume/ (default: {TEMPLATE_NAME}).",
    )
    parser.add_argument(
        "--include-personal-projects",
        action="store_true",
        help="Include featured personal projects in addition to professional automation projects.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate YAML, references, and template rendering without writing output.",
    )
    return parser.parse_args()


def load_yaml(file_name: str) -> dict[str, Any]:
    path = DATA_DIR / file_name
    if not path.is_file():
        raise ResumeGenerationError(f"Missing YAML file: {path}")

    try:
        with path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise ResumeGenerationError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(document, dict):
        raise ResumeGenerationError(f"YAML root must be a mapping: {path}")
    return document


def read_section(section_name: str) -> Any:
    file_name = YAML_FILES[section_name]
    top_level_key = TOP_LEVEL_KEYS[section_name]
    document = load_yaml(file_name)
    if top_level_key not in document:
        raise ResumeGenerationError(
            f"Missing top-level key '{top_level_key}' in {DATA_DIR / file_name}"
        )
    return document[top_level_key]


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ResumeGenerationError(f"{label} must be a mapping")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ResumeGenerationError(f"{label} must be a list")
    return value


def is_public(item: dict[str, Any]) -> bool:
    display = item.get("display")
    if isinstance(display, dict) and display.get("public") is False:
        return False
    return item.get("public") is not False


def parse_date(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def format_date(value: Any) -> str:
    parsed = parse_date(value)
    if parsed is None:
        return "" if value in (None, "") else str(value)
    return parsed.strftime("%b %Y")


def format_period(item: dict[str, Any]) -> str:
    start = format_date(item.get("start_date"))
    end = "Present" if item.get("current") else format_date(item.get("end_date"))
    if start and end:
        return f"{start} - {end}"
    return start or end


def format_location(item: dict[str, Any]) -> str:
    location = item.get("location")
    if not isinstance(location, dict) or not location.get("display_publicly", False):
        return ""
    return str(location.get("value") or "").strip()


def order_value(item: dict[str, Any]) -> int:
    display = item.get("display")
    raw = display.get("priority") if isinstance(display, dict) else None
    if raw is None:
        raw = item.get("display_order")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 9999


def date_sort_value(item: dict[str, Any]) -> tuple[int, datetime]:
    current_rank = 0 if item.get("current") else 1
    parsed = parse_date(item.get("start_date")) or datetime.min
    return current_rank, parsed


def unique_preserving_order(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def by_id(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ResumeGenerationError(f"Every {label} entry must be a mapping")
        item_id = str(item.get("id") or "").strip()
        if not item_id:
            raise ResumeGenerationError(f"Every {label} entry requires an id")
        if item_id in result:
            raise ResumeGenerationError(f"Duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def select_ids(
    index: dict[str, dict[str, Any]],
    requested_ids: Iterable[str],
    label: str,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for item_id in requested_ids:
        item = index.get(item_id)
        if item is None:
            missing.append(item_id)
        else:
            selected.append(deepcopy(item))
    if missing:
        raise ResumeGenerationError(
            f"Unknown {label} id(s): {', '.join(missing)}"
        )
    return selected


def prepare_experience(items: Any) -> list[dict[str, Any]]:
    rows = require_list(items, "experience")
    prepared: list[dict[str, Any]] = []

    for raw in rows:
        item = require_mapping(raw, "experience entry")
        if not is_public(item):
            continue
        role = deepcopy(item)
        role["period"] = format_period(role)
        role["resume_location"] = format_location(role)
        role["resume_responsibilities"] = unique_preserving_order(
            role.get("responsibilities") or []
        )[:MAX_RESPONSIBILITIES]
        role["resume_technologies"] = unique_preserving_order(
            role.get("technologies") or []
        )
        prepared.append(role)

    # Prefer explicit display priority, falling back to reverse start date.
    if any(order_value(item) != 9999 for item in prepared):
        return sorted(prepared, key=order_value)
    return sorted(prepared, key=date_sort_value, reverse=False)


def prepare_skills(items: Any) -> list[dict[str, Any]]:
    rows = require_list(items, "skill_categories")
    index = by_id(rows, "skill category")
    selected = select_ids(index, DEFAULT_SKILL_CATEGORY_IDS, "skill category")

    prepared: list[dict[str, Any]] = []
    for category in selected:
        if not is_public(category):
            continue
        category["resume_skills"] = unique_preserving_order(
            category.get("skills") or []
        )[:MAX_SKILLS_PER_CATEGORY]
        prepared.append(category)
    return sorted(prepared, key=order_value)


def prepare_achievements(items: Any) -> list[dict[str, Any]]:
    rows = require_list(items, "achievements")
    selected = select_ids(by_id(rows, "achievement"), DEFAULT_ACHIEVEMENT_IDS, "achievement")
    return [item for item in selected if is_public(item)]


def prepare_projects(items: Any, include_personal: bool) -> list[dict[str, Any]]:
    rows = require_list(items, "projects")
    project_index = by_id(rows, "project")
    selected = select_ids(project_index, DEFAULT_PROJECT_IDS, "project")

    if include_personal:
        personal = project_index.get("vaultone")
        if personal is not None:
            selected.append(deepcopy(personal))

    prepared: list[dict[str, Any]] = []
    for project in selected:
        if not is_public(project):
            continue
        project["resume_technologies"] = unique_preserving_order(
            project.get("technologies") or []
        )
        project["resume_capabilities"] = unique_preserving_order(
            project.get("capabilities") or []
        )
        prepared.append(project)
    return prepared


def collect_tools(experience: list[dict[str, Any]], projects: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for role in experience:
        values.extend(role.get("resume_technologies") or [])
    for project in projects:
        values.extend(project.get("resume_technologies") or [])
    return unique_preserving_order(values)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned or "resume"


def default_output_path(profile: dict[str, Any], title: str) -> Path:
    name = safe_filename(str(profile.get("full_name") or "resume"))
    role = safe_filename(title)
    return DEFAULT_OUTPUT_DIR / f"{name}_{role}.html"


def resolve_output_path(path: Path | None, profile: dict[str, Any], title: str) -> Path:
    if path is None:
        return default_output_path(profile, title)
    return path if path.is_absolute() else ROOT / path


def validate_profile(profile: dict[str, Any]) -> None:
    required = ("full_name", "primary_title", "about", "contact")
    missing = [key for key in required if not profile.get(key)]
    if missing:
        raise ResumeGenerationError(
            f"profile.yml is missing required profile field(s): {', '.join(missing)}"
        )
    contact = require_mapping(profile.get("contact"), "profile.contact")
    if not contact.get("email"):
        raise ResumeGenerationError("profile.contact.email is required")


def build_context(args: argparse.Namespace) -> dict[str, Any]:
    profile = require_mapping(read_section("profile"), "profile")
    validate_profile(profile)

    experience = prepare_experience(read_section("experience"))
    skills = prepare_skills(read_section("skills"))
    achievements = prepare_achievements(read_section("achievements"))
    projects = prepare_projects(
        read_section("projects"),
        include_personal=args.include_personal_projects,
    )
    professional_development = require_mapping(
        read_section("professional_development"),
        "professional_development",
    )
    education = require_list(read_section("education"), "education")

    title = str(args.title or profile.get("primary_title") or "").strip()
    if not title:
        raise ResumeGenerationError("A target title is required")

    public_display = profile.get("public_display")
    if not isinstance(public_display, dict):
        public_display = {}

    return {
        "profile": deepcopy(profile),
        "target_title": title,
        "experience": experience,
        "skill_categories": skills,
        "achievements": achievements,
        "projects": projects,
        "tools_and_technologies": collect_tools(experience, projects),
        "professional_development": deepcopy(professional_development),
        "education": deepcopy(education),
        "public_display": deepcopy(public_display),
        "generated_on": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def create_environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["format_date"] = format_date
    return environment


def render_resume(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    template_path = TEMPLATE_DIR / args.template
    if not template_path.is_file():
        raise ResumeGenerationError(f"Missing resume template: {template_path}")

    context = build_context(args)
    template = create_environment().get_template(args.template)
    return template.render(**context), context


def main() -> int:
    args = parse_args()
    try:
        rendered, context = render_resume(args)
        output_path = resolve_output_path(
            args.output,
            context["profile"],
            context["target_title"],
        )

        if args.validate_only:
            print("[SUCCESS] Resume data and template validation passed")
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"[SUCCESS] Resume generated: {output_path}")
        return 0
    except ResumeGenerationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[ERROR] Unexpected resume generation failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

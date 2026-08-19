#!/usr/bin/env python3
"""Validate the structural completeness of docs/implementation-plan.

The validator checks document structure, stable IDs, phase metadata, and implementation
handoff coverage. It cannot prove architectural correctness or safe parallelism; the agent
must still perform the semantic review defined in SKILL.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PLAN_RELATIVE_PATH = Path("docs") / "implementation-plan"

REQUIRED_FILES = (
    "README.md",
    "00-product-description.md",
    "01-system-architecture.md",
    "02-domain-and-data.md",
    "03-interfaces-and-integrations.md",
    "90-security-reliability-and-operations.md",
    "91-testing-and-quality.md",
    "92-delivery-roadmap.md",
    "93-implementation-units.md",
    "99-open-questions.md",
)

GLOBAL_METADATA_MARKERS = (
    "status",
    "last updated",
    "source requirement",
    "related document",
)

README_HEADINGS = (
    "planning status and phase-readiness statement",
    "source documents and repository evidence",
    "product summary",
    "goals and non-goals",
    "architecture summary",
    "major components and ownership table",
    "system-wide delivery-phase summary",
    "component and phase identifier registry",
    "document index",
    "requirement-to-component-to-phase traceability summary",
    "blocking decisions, deferred gates, and highest risks",
    "implementation handoff readiness",
    "how to use and maintain the plan",
)

PRODUCT_DESCRIPTION_HEADINGS = (
    "document purpose and source",
    "product vision and problem",
    "outcomes and success measures",
    "users, actors, and roles",
    "product surfaces and operating model",
    "first production release scope",
    "primary and exceptional workflows",
    "functional requirements",
    "non-functional requirements",
    "business rules and invariants",
    "constraints and dependencies",
    "principal decision register",
    "assumptions and deferred decisions",
    "explicit non-goals",
    "acceptance model",
    "change history",
)

ROADMAP_HEADINGS = (
    "delivery principles",
    "system-wide phases",
    "component and phase identifier registry",
    "cross-component dependency matrix",
    "component-phase dependency dag",
    "dependency-type legend and rationale",
    "decision-gate schedule",
    "critical path",
    "candidate parallel waves",
    "hard sequential constraints",
    "milestones and objective exit gates",
    "environment and infrastructure sequencing",
    "data and integration migration sequencing",
    "release, rollout, rollback, and launch plan",
    "post-launch stabilization and ownership transfer",
    "decommissioning and cleanup",
    "risks, contingency paths, and decision deadlines",
)

IMPLEMENTATION_UNITS_HEADINGS = (
    "handoff status and authorized phases",
    "stable component and phase catalog",
    "candidate execution units",
    "dependency edges",
    "provider-consumer boundary candidates",
    "expected write-domain ownership",
    "shared artifacts and conflict hotspots",
    "contract artifacts likely to be materialized",
    "parallelization candidates",
    "mandatory serialization constraints",
    "decision gates and excluded units",
    "suggested integration order",
    "handoff validation checklist",
)

COMPONENT_HEADINGS = (
    "purpose and scope",
    "responsibilities",
    "explicit non-responsibilities",
    "architecture and internal modules",
    "dependencies and public contracts",
    "data and state ownership",
    "security and privacy",
    "reliability and failure modes",
    "observability and operational controls",
    "test strategy",
    "rollout, migration, rollback, and decommissioning",
    "phased implementation",
    "risks and open decisions",
)

PHASE_SUBHEADINGS = (
    "objective",
    "prerequisites",
    "in scope",
    "out of scope",
    "work",
    "deliverables",
    "dependencies",
    "boundary inputs",
    "boundary outputs",
    "expected write domains",
    "preliminary parallelization",
    "validation",
    "operational and migration work",
    "exit criteria",
    "risks and deferred work",
)

DEPENDENCY_CLASSIFICATIONS = (
    "independent",
    "contract-bound",
    "implementation-bound",
    "decision-gated",
)

VAGUE_PATTERNS = (
    re.compile(r"\buse best practices\b", re.IGNORECASE),
    re.compile(r"\badd security\b", re.IGNORECASE),
    re.compile(r"\bhandle errors\b", re.IGNORECASE),
    re.compile(r"\bscale later\b", re.IGNORECASE),
)

UNRESOLVED_PATTERNS = (
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bto be decided\b", re.IGNORECASE),
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
COMPONENT_ID_RE = re.compile(r"\bComponent\s+ID\s*:\s*`?(CMP-(\d{3,}))`?\b", re.IGNORECASE)
PHASE_RE = re.compile(
    r"^###\s+(PH-(\d{3,})-(\d{2,}))\s+(?:—|-)\s+[^\n]+$",
    re.IGNORECASE | re.MULTILINE,
)
REQUIREMENT_ID_RE = re.compile(r"\b(?:FR|NFR|CON)-\d{3,}\b")
DEFERRED_DECISION_RE = re.compile(r"\bDEC-\d{3,}\b")


@dataclass(frozen=True)
class ComponentRecord:
    path: Path
    component_id: str
    phase_ids: tuple[str, ...]


def normalize_heading(value: str) -> str:
    value = re.sub(r"[`*_]", "", value)
    value = re.sub(r"\s+", " ", value.strip().lower())
    return value


def heading_entries(text: str) -> list[tuple[int, str, int]]:
    return [
        (len(match.group(1)), normalize_heading(match.group(2)), match.start())
        for match in HEADING_RE.finditer(text)
    ]


def missing_heading_names(text: str, required: Iterable[str]) -> list[str]:
    available = {name for _, name, _ in heading_entries(text)}
    return [name for name in required if normalize_heading(name) not in available]


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{path}: file is not valid UTF-8")
    except OSError as exc:
        errors.append(f"{path}: cannot read file: {exc}")
    return ""


def validate_headings(path: Path, text: str, required: Iterable[str], errors: list[str]) -> None:
    for heading in missing_heading_names(text, required):
        errors.append(f"{path}: missing required section '## {heading.title()}'")


def validate_global_metadata(path: Path, text: str, warnings: list[str]) -> None:
    prefix = text[:1800].lower()
    for marker in GLOBAL_METADATA_MARKERS:
        if marker not in prefix:
            warnings.append(f"{path}: top-of-document metadata may be missing '{marker}'")


def validate_required_file(path: Path, errors: list[str], warnings: list[str]) -> str:
    text = read_text(path, errors)
    if not text:
        return ""

    validate_global_metadata(path, text, warnings)

    required: tuple[str, ...] | None = None
    if path.name == "README.md":
        required = README_HEADINGS
    elif path.name == "00-product-description.md":
        required = PRODUCT_DESCRIPTION_HEADINGS
    elif path.name == "92-delivery-roadmap.md":
        required = ROADMAP_HEADINGS
    elif path.name == "93-implementation-units.md":
        required = IMPLEMENTATION_UNITS_HEADINGS

    if required is not None:
        validate_headings(path, text, required, errors)

    if path.name in {"92-delivery-roadmap.md", "93-implementation-units.md"}:
        lowered = text.lower()
        missing = [value for value in DEPENDENCY_CLASSIFICATIONS if value not in lowered]
        if missing:
            errors.append(f"{path}: missing dependency classifications: {', '.join(missing)}")

    if path.name != "99-open-questions.md":
        for pattern in UNRESOLVED_PATTERNS:
            if pattern.search(text):
                warnings.append(f"{path}: contains unresolved marker matching /{pattern.pattern}/")

    return text


def validate_component(path: Path, errors: list[str], warnings: list[str]) -> ComponentRecord | None:
    text = read_text(path, errors)
    if not text:
        return None

    validate_global_metadata(path, text, warnings)
    validate_headings(path, text, COMPONENT_HEADINGS, errors)

    component_matches = list(COMPONENT_ID_RE.finditer(text[:2200]))
    if len(component_matches) != 1:
        errors.append(f"{path}: expected exactly one top-of-document 'Component ID: CMP-###' entry")
        return None

    component_id = component_matches[0].group(1).upper()
    component_number = component_matches[0].group(2)

    phase_matches = list(PHASE_RE.finditer(text))
    if len(phase_matches) < 2:
        errors.append(f"{path}: expected at least two '### PH-###-## — ...' phase sections")
        return ComponentRecord(path, component_id, tuple())

    phase_ids: list[str] = []
    boundaries = [match.start() for match in phase_matches] + [len(text)]
    for index, match in enumerate(phase_matches):
        phase_id = match.group(1).upper()
        phase_component_number = match.group(2)
        phase_ids.append(phase_id)

        if phase_component_number != component_number:
            errors.append(
                f"{path}: {phase_id} does not belong to {component_id}; numeric prefixes must match"
            )

        block = text[boundaries[index] : boundaries[index + 1]]
        phase_name = match.group(0).strip()
        for heading in missing_heading_names(block, PHASE_SUBHEADINGS):
            errors.append(f"{path}: {phase_name} missing '#### {heading.title()}'")

        lowered = block.lower()
        if not any(value in lowered for value in DEPENDENCY_CLASSIFICATIONS):
            errors.append(
                f"{path}: {phase_id} must name a dependency or preliminary parallelization classification"
            )

    if len(phase_ids) != len(set(phase_ids)):
        errors.append(f"{path}: duplicate phase IDs found within the component document")

    for pattern in VAGUE_PATTERNS:
        if pattern.search(text):
            warnings.append(f"{path}: contains vague phrase matching /{pattern.pattern}/")

    return ComponentRecord(path, component_id, tuple(phase_ids))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/implementation-plan for the product planning skill."
    )
    parser.add_argument(
        "repository_root",
        nargs="?",
        default=".",
        help="Target repository root (default: current directory)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repository_root).expanduser().resolve()
    plan_root = repo_root / PLAN_RELATIVE_PATH
    errors: list[str] = []
    warnings: list[str] = []

    if not plan_root.is_dir():
        print(f"ERROR: planning directory does not exist: {plan_root}")
        return 1

    required_texts: dict[str, str] = {}
    for filename in REQUIRED_FILES:
        path = plan_root / filename
        if not path.is_file():
            errors.append(f"missing required file: {path}")
        else:
            required_texts[filename] = validate_required_file(path, errors, warnings)

    components_dir = plan_root / "components"
    if not components_dir.is_dir():
        errors.append(f"missing components directory: {components_dir}")
        component_files: list[Path] = []
    else:
        component_files = sorted(
            path
            for path in components_dir.glob("*.md")
            if path.is_file() and not path.name.startswith(".")
        )
        if not component_files:
            errors.append(f"no component plans found in: {components_dir}")

    records = [
        record
        for path in component_files
        if (record := validate_component(path, errors, warnings)) is not None
    ]

    component_ids = [record.component_id for record in records]
    if len(component_ids) != len(set(component_ids)):
        errors.append("component IDs must be unique across component documents")

    phase_locations: dict[str, Path] = {}
    for record in records:
        for phase_id in record.phase_ids:
            if phase_id in phase_locations:
                errors.append(
                    f"duplicate phase ID {phase_id}: {phase_locations[phase_id]} and {record.path}"
                )
            else:
                phase_locations[phase_id] = record.path

    roadmap_text = required_texts.get("92-delivery-roadmap.md", "")
    handoff_text = required_texts.get("93-implementation-units.md", "")
    readme_text = required_texts.get("README.md", "")

    for component_id in component_ids:
        if component_id not in roadmap_text:
            errors.append(f"92-delivery-roadmap.md: missing component ID {component_id}")
        if component_id not in handoff_text:
            errors.append(f"93-implementation-units.md: missing component ID {component_id}")
        if component_id not in readme_text:
            warnings.append(f"README.md: identifier registry may be missing {component_id}")

    for phase_id in phase_locations:
        if phase_id not in roadmap_text:
            errors.append(f"92-delivery-roadmap.md: missing phase ID {phase_id}")
        if phase_id not in handoff_text:
            errors.append(f"93-implementation-units.md: missing phase ID {phase_id}")
        if phase_id not in readme_text:
            warnings.append(f"README.md: identifier registry may be missing {phase_id}")

    combined_text = ""
    for path in plan_root.rglob("*.md"):
        try:
            combined_text += "\n" + path.read_text(encoding="utf-8")
        except OSError:
            pass

    if not REQUIREMENT_ID_RE.search(combined_text):
        errors.append("no requirement IDs found; expected IDs such as FR-001, NFR-001, or CON-001")

    if re.search(r"\bdeferred decision", combined_text, re.IGNORECASE) and not DEFERRED_DECISION_RE.search(
        combined_text
    ):
        warnings.append("deferred decisions are mentioned but no DEC-### identifiers were found")

    print(f"Plan root: {plan_root}")
    print(f"Component plans: {len(component_files)}")
    print(f"Component IDs: {len(component_ids)}")
    print(f"Phase IDs: {len(phase_locations)}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        print(f"\nValidation failed with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1

    print(f"\nValidation passed with 0 errors and {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

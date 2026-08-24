#!/usr/bin/env python3
"""Validate the scope-relative structural completeness of docs/implementation-plan.

The validator checks document structure, stable IDs, phase metadata, and implementation
handoff coverage. It cannot prove architectural correctness or safe parallelism; the agent
must still perform the semantic review defined in SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PLAN_RELATIVE_PATH = Path("docs") / "implementation-plan"

CORE_REQUIRED_FILES = (
    "00-product-description.md",
    "README.md",
    "92-delivery-roadmap.md",
    "93-implementation-units.md",
    "99-open-questions.md",
)

FULL_PRODUCT_FILES = (
    "01-system-architecture.md",
    "02-domain-and-data.md",
    "03-interfaces-and-integrations.md",
    "90-security-reliability-and-operations.md",
    "91-testing-and-quality.md",
)

DELIVERY_SCOPE_MODES = {
    "full product",
    "scoped change",
    "modernization or migration",
    "remediation or reliability",
}

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
    "delivery scope and impact cone",
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
    "delivery scope and release boundary",
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
SCOPE_BEGIN = "<!-- delivery-scope:begin -->"
SCOPE_END = "<!-- delivery-scope:end -->"
SCOPE_REQUIRED_KEYS = {
    "schema_version",
    "delivery_scope_mode",
    "requested_outcome",
    "impact_cone",
    "preserved_behavior",
    "non_goals",
    "planned_phase_ids",
    "authorized_phase_ids",
    "applicable_documents",
    "preserved_document_sources",
}


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


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def nonempty_string_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"{label}: expected an array of non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label}: duplicate values are not allowed")
    return value


def parse_delivery_scope(path: Path, text: str, errors: list[str]) -> dict[str, Any] | None:
    """Parse the one machine-readable scope record, or allow a legacy plan with none."""

    starts = text.count(SCOPE_BEGIN)
    ends = text.count(SCOPE_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        errors.append(f"{path}: expected exactly one canonical delivery-scope block")
        return None
    start = text.find(SCOPE_BEGIN) + len(SCOPE_BEGIN)
    end = text.find(SCOPE_END, start)
    if end < start:
        errors.append(f"{path}: delivery-scope end marker precedes its begin marker")
        return None
    try:
        parsed = json.loads(
            text[start:end].strip(), object_pairs_hook=reject_duplicate_keys
        )
    except (json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{path}: invalid delivery-scope JSON: {exc}")
        return None
    if not isinstance(parsed, dict):
        errors.append(f"{path}: delivery-scope value must be an object")
        return None

    keys = set(parsed)
    if keys != SCOPE_REQUIRED_KEYS:
        errors.append(
            f"{path}: delivery-scope keys differ; "
            f"missing={sorted(SCOPE_REQUIRED_KEYS - keys)}, "
            f"extra={sorted(keys - SCOPE_REQUIRED_KEYS)}"
        )
        return None
    if parsed.get("schema_version") != 1:
        errors.append(f"{path}: delivery-scope.schema_version must equal 1")
    if not isinstance(parsed.get("delivery_scope_mode"), str) or parsed.get(
        "delivery_scope_mode"
    ) not in DELIVERY_SCOPE_MODES:
        errors.append(
            f"{path}: delivery-scope.delivery_scope_mode must be one of "
            f"{sorted(DELIVERY_SCOPE_MODES)}"
        )
    for key in ("requested_outcome", "impact_cone"):
        if not isinstance(parsed.get(key), str) or not parsed.get(key, "").strip():
            errors.append(f"{path}: delivery-scope.{key} must be a non-empty string")
    for key in (
        "preserved_behavior",
        "non_goals",
        "planned_phase_ids",
        "authorized_phase_ids",
        "applicable_documents",
    ):
        parsed[key] = nonempty_string_list(
            parsed.get(key), f"{path}: delivery-scope.{key}", errors
        )
    if not parsed.get("non_goals"):
        errors.append(f"{path}: delivery-scope.non_goals must not be empty")
    if not parsed.get("planned_phase_ids"):
        errors.append(f"{path}: delivery-scope.planned_phase_ids must not be empty")
    scope_mode = parsed.get("delivery_scope_mode")
    if (
        isinstance(scope_mode, str)
        and scope_mode in DELIVERY_SCOPE_MODES - {"full product"}
        and not parsed.get("preserved_behavior")
    ):
        errors.append(
            f"{path}: delivery-scope.preserved_behavior must not be empty for a bounded mode"
        )

    for key in ("planned_phase_ids", "authorized_phase_ids"):
        for phase_id in parsed.get(key, []):
            if not isinstance(phase_id, str) or not re.fullmatch(
                r"PH-\d{3,}-\d{2,}", phase_id
            ):
                errors.append(f"{path}: delivery-scope.{key} has invalid ID {phase_id!r}")
    planned = set(parsed.get("planned_phase_ids", []))
    authorized = set(parsed.get("authorized_phase_ids", []))
    if not authorized <= planned:
        errors.append(
            f"{path}: authorized_phase_ids must be a subset of planned_phase_ids; "
            f"extra={sorted(authorized - planned)}"
        )

    applicable = set(parsed.get("applicable_documents", []))
    concern_documents = set(FULL_PRODUCT_FILES)
    if not applicable <= concern_documents:
        errors.append(
            f"{path}: delivery-scope.applicable_documents has unknown paths "
            f"{sorted(applicable - concern_documents)}"
        )
    sources = parsed.get("preserved_document_sources")
    if not isinstance(sources, dict) or any(
        not isinstance(key, str)
        or not isinstance(value, str)
        or not value.strip()
        for key, value in (sources.items() if isinstance(sources, dict) else [])
    ):
        errors.append(
            f"{path}: delivery-scope.preserved_document_sources must map paths to non-empty evidence"
        )
        return None
    omitted = concern_documents - applicable
    if set(sources) != omitted:
        errors.append(
            f"{path}: preserved_document_sources must cover exactly omitted concern documents; "
            f"missing={sorted(omitted - set(sources))}, "
            f"extra={sorted(set(sources) - omitted)}"
        )
    if parsed.get("delivery_scope_mode") == "full product" and applicable != concern_documents:
        errors.append(f"{path}: full product scope must mark every concern document applicable")
    return parsed


def validate_headings(path: Path, text: str, required: Iterable[str], errors: list[str]) -> None:
    for heading in missing_heading_names(text, required):
        errors.append(f"{path}: missing required section '## {heading.title()}'")


def validate_global_metadata(path: Path, text: str, warnings: list[str]) -> None:
    prefix = text[:1800].lower()
    for marker in GLOBAL_METADATA_MARKERS:
        if marker not in prefix:
            warnings.append(f"{path}: top-of-document metadata may be missing '{marker}'")


def validate_required_file(
    path: Path,
    errors: list[str],
    warnings: list[str],
    require_scope_heading: bool = True,
    allow_legacy_release_heading: bool = False,
) -> str:
    text = read_text(path, errors)
    if not text:
        errors.append(f"{path}: required file is empty or unreadable")
        return ""

    validate_global_metadata(path, text, warnings)

    required: tuple[str, ...] | None = None
    if path.name == "README.md":
        required = README_HEADINGS
        if not require_scope_heading:
            required = tuple(
                heading for heading in required if heading != "delivery scope and impact cone"
            )
    elif path.name == "00-product-description.md":
        required = PRODUCT_DESCRIPTION_HEADINGS
        available = {name for _, name, _ in heading_entries(text)}
        if (
            allow_legacy_release_heading
            and "first production release scope" in available
            and "delivery scope and release boundary" not in available
        ):
            required = tuple(
                "first production release scope"
                if heading == "delivery scope and release boundary"
                else heading
                for heading in required
            )
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

    if path.name not in {"04-external-system-evidence.md", "99-open-questions.md"}:
        for pattern in UNRESOLVED_PATTERNS:
            if pattern.search(text):
                warnings.append(f"{path}: contains unresolved marker matching /{pattern.pattern}/")

    return text


def validate_component(
    path: Path,
    errors: list[str],
    warnings: list[str],
    minimum_phase_count: int,
    included_phase_ids: set[str] | None = None,
    require_atomicity_rationale: bool = False,
) -> ComponentRecord | None:
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

    all_phase_matches = list(PHASE_RE.finditer(text))
    phase_matches = [
        (index, match)
        for index, match in enumerate(all_phase_matches)
        if included_phase_ids is None or match.group(1).upper() in included_phase_ids
    ]
    if len(phase_matches) < minimum_phase_count:
        errors.append(
            f"{path}: expected at least {minimum_phase_count} "
            "'### PH-###-## — ...' phase section(s)"
        )
        return ComponentRecord(path, component_id, tuple())

    phase_ids: list[str] = []
    boundaries = [match.start() for match in all_phase_matches] + [len(text)]
    for index, match in phase_matches:
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

        if require_atomicity_rationale and len(phase_matches) == 1:
            atomicity = re.search(
                r"^####\s+Atomicity rationale\s*$\n(?P<body>.*?)(?=^#{1,4}\s|\Z)",
                block,
                re.IGNORECASE | re.MULTILINE | re.DOTALL,
            )
            if not atomicity or not atomicity.group("body").strip():
                errors.append(
                    f"{path}: {phase_id} requires a non-empty '#### Atomicity rationale'"
                )

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

    product_description_path = plan_root / "00-product-description.md"
    product_description = (
        read_text(product_description_path, errors) if product_description_path.is_file() else ""
    )
    scope_block_present = SCOPE_BEGIN in product_description or SCOPE_END in product_description
    scope = parse_delivery_scope(product_description_path, product_description, errors)
    scope_mode_declared = scope_block_present

    required_texts: dict[str, str] = {}
    for filename in CORE_REQUIRED_FILES:
        path = plan_root / filename
        if not path.is_file():
            errors.append(f"missing required file: {path}")
        else:
            text = validate_required_file(
                path,
                errors,
                warnings,
                require_scope_heading=scope_mode_declared,
                allow_legacy_release_heading=not scope_mode_declared,
            )
            required_texts[filename] = text

    if scope is None:
        delivery_scope_mode = "full product"
        if not scope_block_present:
            warnings.append(
                "00-product-description.md: missing canonical delivery-scope block; validating as Full product "
                "— declare a bounded mode if this is a scoped change"
            )
        applicable_documents = set(FULL_PRODUCT_FILES)
        planned_phase_ids: set[str] | None = None
    else:
        delivery_scope_mode = scope.get("delivery_scope_mode")
        applicable_documents = set(scope.get("applicable_documents", []))
        planned_phase_ids = set(scope.get("planned_phase_ids", []))

    for filename in FULL_PRODUCT_FILES:
        path = plan_root / filename
        if filename in applicable_documents and not path.is_file():
            errors.append(f"missing required file: {path}")
        elif path.is_file():
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

    phase_occurrences: dict[str, list[Path]] = {}
    for path in component_files:
        for match in PHASE_RE.finditer(read_text(path, errors)):
            phase_occurrences.setdefault(match.group(1).upper(), []).append(path)

    if planned_phase_ids is None:
        selected_files = component_files
    else:
        for phase_id in sorted(planned_phase_ids):
            occurrences = phase_occurrences.get(phase_id, [])
            if len(occurrences) != 1:
                errors.append(
                    f"delivery-scope planned phase {phase_id} must occur exactly once; "
                    f"found {len(occurrences)}"
                )
        if delivery_scope_mode == "full product":
            selected_files = component_files
            discovered_phase_ids = set(phase_occurrences)
            if planned_phase_ids != discovered_phase_ids:
                errors.append(
                    "full product planned_phase_ids must equal all component phase IDs; "
                    f"missing={sorted(discovered_phase_ids - planned_phase_ids)}, "
                    f"extra={sorted(planned_phase_ids - discovered_phase_ids)}"
                )
        else:
            selected_files = sorted(
                {
                    path
                    for phase_id in planned_phase_ids
                    for path in phase_occurrences.get(phase_id, [])
                }
            )
        if not selected_files:
            errors.append("no component plan contains a delivery-scope planned phase")

    records = [
        record
        for path in selected_files
        if (
            record := validate_component(
                path,
                errors,
                warnings,
                minimum_phase_count=2 if delivery_scope_mode == "full product" else 1,
                included_phase_ids=planned_phase_ids,
                require_atomicity_rationale=delivery_scope_mode != "full product",
            )
        )
        is not None
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
    print(f"Component plans in scope: {len(selected_files)}")
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

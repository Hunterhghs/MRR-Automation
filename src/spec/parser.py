"""YAML report specification parser with JSON Schema validation.

Extended schema supports 20-60 page market research reports with:
- Multi-chapter structure
- KPI cards, callout boxes, case studies
- Multiple data sources (World Bank, FRED, static)
- AI narrative prompts
- Market sizing, competitive analysis, forecasting sections
"""

from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate, ValidationError

REPORT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["meta", "sections"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "author": {"type": "string", "default": "H Heuristics Research"},
                "date": {"type": "string"},
                "brand": {"type": "string", "default": "H Heuristics"},
                "seed": {"type": "integer"},
                "language": {"type": "string", "default": "en"},
                "report_id": {"type": "string"},
                "classification": {"type": "string", "enum": ["public", "confidential", "client"]},
                "pages": {
                    "type": "object",
                    "properties": {
                        "size": {"type": "string", "enum": ["A4", "US Letter"], "default": "A4"}
                    }
                },
                "disclaimer": {"type": "string"}
            }
        },
        "sections": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "cover", "toc", "executive_summary",
                            "chapter", "section", "subsection",
                            "chart", "table", "callout", "key_findings",
                            "kpi_cards", "case_study", "swot",
                            "competitive_matrix", "market_sizing",
                            "forecast", "methodology", "timeline",
                            "appendix", "references", "page_break",
                            "disclaimer_page", "copyright_page",
                        ]
                    },
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "narrative_prompt": {"type": "string"},
                    "subsections": {
                        "type": "array",
                        "items": {"$ref": "#/properties/sections/items"}
                    },
                    "data_source": {
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "enum": ["world_bank", "fred", "static", "curated"]
                            },
                            "indicator": {"type": "string"},
                            "series_id": {"type": "string"},
                            "countries": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "date_range": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "integer"},
                                    "end": {"type": "integer"}
                                }
                            },
                            "frequency": {"type": "string"},
                            "units": {"type": "string"}
                        }
                    },
                    "chart_type": {
                        "type": "string",
                        "enum": [
                            "line", "bar", "horizontal_bar", "stacked_bar",
                            "grouped_bar", "area", "stacked_area", "scatter",
                            "bubble", "waterfall", "donut", "heatmap",
                            "radar", "slope"
                        ]
                    },
                    "chart_title": {"type": "string"},
                    "table_data": {
                        "type": "object",
                        "properties": {
                            "headers": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "rows": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "notes": {"type": "string"}
                        }
                    },
                    "kpi_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "value": {"type": "string"},
                                "change": {"type": "string"},
                                "trend": {"type": "string", "enum": ["up", "down", "flat"]},
                                "description": {"type": "string"}
                            },
                            "required": ["label", "value"]
                        }
                    },
                    "case_study_data": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "industry": {"type": "string"},
                            "challenge": {"type": "string"},
                            "solution": {"type": "string"},
                            "results": {"type": "string"}
                        }
                    },
                    "swot_data": {
                        "type": "object",
                        "properties": {
                            "strengths": {
                                "type": "array", "items": {"type": "string"}
                            },
                            "weaknesses": {
                                "type": "array", "items": {"type": "string"}
                            },
                            "opportunities": {
                                "type": "array", "items": {"type": "string"}
                            },
                            "threats": {
                                "type": "array", "items": {"type": "string"}
                            }
                        }
                    },
                    "columns": {"type": "integer", "minimum": 1, "maximum": 3},
                    "emphasis": {"type": "string", "enum": ["low", "normal", "high"]},
                    "page_break_before": {"type": "boolean"},
                }
            }
        }
    }
}


class SpecError(Exception):
    """Raised when a spec is invalid."""


def load_spec(path: str | Path) -> dict[str, Any]:
    """Load and validate a YAML report specification.

    Args:
        path: Path to a .yaml or .json spec file.

    Returns:
        Validated spec dict with defaults applied.

    Raises:
        SpecError: If the spec is missing, unparseable, or fails validation.
    """
    path = Path(path)
    if not path.exists():
        raise SpecError(f"Spec file not found: {path}")

    raw = path.read_text()

    try:
        spec = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise SpecError(f"YAML parse error in {path}: {e}") from e

    if spec is None:
        raise SpecError(f"Spec file is empty: {path}")

    try:
        validate(instance=spec, schema=REPORT_SCHEMA)
    except ValidationError as e:
        path_str = "/".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        raise SpecError(f"Spec validation error: {e.message} (at {path_str})") from e

    # Apply defaults
    spec.setdefault("meta", {})
    spec["meta"].setdefault("author", "H Heuristics Research")
    spec["meta"].setdefault("brand", "H Heuristics")
    spec["meta"].setdefault("language", "en")
    spec["meta"].setdefault("pages", {})
    spec["meta"]["pages"].setdefault("size", "A4")
    spec["meta"].setdefault("classification", "public")

    return spec


def flatten_sections(sections: list[dict], depth: int = 0) -> list[dict]:
    """Flatten nested sections into a linear sequence with depth info."""
    flat = []
    for sec in sections:
        tagged = {**sec, "_depth": depth}
        flat.append(tagged)
        if "subsections" in sec and sec["subsections"]:
            flat.extend(flatten_sections(sec["subsections"], depth + 1))
    return flat


def get_chapter_count(sections: list[dict]) -> int:
    """Count the number of chapter-level sections."""
    return sum(1 for s in sections if s.get("type") == "chapter")

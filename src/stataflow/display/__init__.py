"""Command-aware rendering for StataFlow results."""

from stataflow.display.adapters import build_document
from stataflow.display.document import (
    DisplayDocument,
    DisplayField,
    DisplaySection,
    DisplayTable,
)
from stataflow.display.html import render_html
from stataflow.display.text import render_text

__all__ = [
    "DisplayDocument",
    "DisplayField",
    "DisplaySection",
    "DisplayTable",
    "build_document",
    "render_html",
    "render_text",
]

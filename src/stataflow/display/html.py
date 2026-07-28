"""Escaped HTML renderer for model result display."""

from __future__ import annotations

from html import escape

from stataflow.display.document import DisplayDocument, DisplayField, DisplayTable


def _fields(fields: list[DisplayField]) -> str:
    if not fields:
        return ""
    rows = "".join(f"<tr><th>{escape(field.label)}</th><td>{escape(field.value)}</td></tr>" for field in fields)
    return f'<table class="stataflow-fields"><tbody>{rows}</tbody></table>'


def _table(table: DisplayTable) -> str:
    headers = "".join(f"<th>{escape(value)}</th>" for value in table.headers)
    rows = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>" for row in table.rows)
    return f'<table class="stataflow-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>'


def render_html(document: DisplayDocument) -> str:
    """Render a display document as a self-contained escaped HTML fragment."""
    parts = [
        '<div class="stataflow-result">',
        f"<h3>{escape(document.title)}</h3>",
    ]
    if document.command:
        parts.append(f'<div class="stataflow-command">{escape(document.command)}</div>')
    parts.extend([_fields(document.header), _table(document.coefficients)])
    if document.fit:
        parts.append(_fields(document.fit))
    for section in document.sections:
        parts.append(f"<h4>{escape(section.title)}</h4>")
        parts.append(_fields(section.fields))
        parts.extend(_table(table) for table in section.tables)
    if document.warnings:
        items = "".join(f"<li>{escape(warning)}</li>" for warning in document.warnings)
        parts.append(f'<div class="stataflow-warnings"><h4>Warnings</h4><ul>{items}</ul></div>')
    parts.append("</div>")
    return "".join(parts)

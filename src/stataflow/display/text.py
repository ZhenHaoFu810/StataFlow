"""Plain-text renderer for model result display."""

from __future__ import annotations

import textwrap

from stataflow.display.document import (
    DisplayDocument,
    DisplayField,
    DisplayTable,
)


def _wrap_line(text: str, width: int, *, indent: str = "") -> list[str]:
    available = max(1, width - len(indent))
    return textwrap.wrap(
        text,
        width=available,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [indent]


def _render_fields(fields: list[DisplayField], width: int) -> list[str]:
    if not fields:
        return []
    label_width = min(max(len(field.label) for field in fields), max(12, width // 3))
    lines: list[str] = []
    for field in fields:
        if field.label.endswith(":"):
            prefix = f"{field.label} "
        else:
            prefix = f"{field.label:<{label_width}} = "
        lines.extend(_wrap_line(field.value, width, indent=prefix))
    return lines


def _column_widths(table: DisplayTable, width: int) -> list[int]:
    count = len(table.headers)
    ci_header = count >= 2 and table.headers[-2] == "[95% conf. interval]" and table.headers[-1] == ""
    natural = [
        max(
            (
                len("[95% conf.")
                if ci_header and index == count - 2
                else len("interval]")
                if ci_header and index == count - 1
                else len(table.headers[index])
            ),
            *(len(row[index]) for row in table.rows),
        )
        for index in range(count)
    ]
    separators = 2 * (count - 1)
    excess = sum(natural) + separators - width
    widths = natural[:]
    while excess > 0:
        candidates = [i for i, value in enumerate(widths) if value > (10 if i == 0 else 7)]
        if not candidates:
            break
        index = max(candidates, key=lambda i: widths[i])
        widths[index] -= 1
        excess -= 1
    return widths


def _render_regular_table(table: DisplayTable, width: int) -> list[str]:
    widths = _column_widths(table, width)
    aligns = table.align or ["left"] * len(widths)

    def format_cells(cells: list[str], *, bottom_align: bool = False) -> list[str]:
        wrapped = [
            textwrap.wrap(
                cell,
                width=max(1, widths[index]),
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
            for index, cell in enumerate(cells)
        ]
        height = max(len(parts) for parts in wrapped)
        lines = []
        for row_index in range(height):
            values = []
            for index, parts in enumerate(wrapped):
                offset = height - len(parts) if bottom_align else 0
                part_index = row_index - offset
                value = parts[part_index] if 0 <= part_index < len(parts) else ""
                if aligns[index] == "right":
                    values.append(f"{value:>{widths[index]}}")
                else:
                    values.append(f"{value:<{widths[index]}}")
            lines.append("  ".join(values).rstrip())
        return lines

    ci_header = len(table.headers) >= 2 and table.headers[-2] == "[95% conf. interval]" and table.headers[-1] == ""
    if ci_header:
        header_parts = []
        for index, value in enumerate(table.headers[:-2]):
            if aligns[index] == "right":
                header_parts.append(f"{value:>{widths[index]}}")
            else:
                header_parts.append(f"{value:<{widths[index]}}")
        ci_width = widths[-2] + 2 + widths[-1]
        lines = [("  ".join(header_parts) + "  " + f"{'[95% conf. interval]':>{ci_width}}").rstrip()]
    else:
        lines = format_cells(table.headers)
    lines.append("-" * min(width, sum(widths) + 2 * (len(widths) - 1)))
    for row in table.rows:
        lines.extend(format_cells(row, bottom_align=True))
    return lines


def _render_coefficients_stacked(table: DisplayTable, width: int) -> list[str]:
    lines = ["Coefficient table", "-" * width]
    for row in table.rows:
        lines.extend(_wrap_line(row[0], width))
        lines.extend(_wrap_line(f"Coef. {row[1]}  Std. err. {row[2]}", width, indent="  "))
        lines.extend(
            _wrap_line(
                f"{table.headers[3]} {row[3]}  {table.headers[4]} {row[4]}",
                width,
                indent="  ",
            )
        )
        if len(row) == 7:
            lines.extend(
                _wrap_line(
                    f"[95% conf. interval] {row[5]}  {row[6]}",
                    width,
                    indent="  ",
                )
            )
    return lines


def _render_table(table: DisplayTable, width: int, *, coefficients: bool = False) -> list[str]:
    fitted_width = sum(_column_widths(table, width)) + 2 * (len(table.headers) - 1)
    if coefficients and fitted_width > width:
        return _render_coefficients_stacked(table, width)
    return _render_regular_table(table, width)


def render_text(document: DisplayDocument, *, width: int = 80) -> str:
    """Render a display document as width-constrained plain text."""
    if width < 40:
        raise ValueError("width must be at least 40")
    lines = [document.title]
    if document.command:
        lines.extend(_wrap_line(f"Command: {document.command}", width))
    lines.append("=" * width)
    lines.extend(_render_fields(document.header, width))
    lines.append("-" * width)
    lines.extend(_render_table(document.coefficients, width, coefficients=True))
    if document.fit:
        lines.append("-" * width)
        lines.extend(_render_fields(document.fit, width))
    for section in document.sections:
        lines.extend(["", section.title, "-" * min(width, len(section.title))])
        lines.extend(_render_fields(section.fields, width))
        for table in section.tables:
            lines.extend(_render_table(table, width))
    if document.warnings:
        lines.extend(["", "Warnings", "--------"])
        for warning in document.warnings:
            lines.extend(_wrap_line(warning, width, indent="* "))
    return "\n".join(lines)

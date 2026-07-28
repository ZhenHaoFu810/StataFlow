"""Renderer-neutral structures for model result display."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DisplayField:
    """A labeled value in a display section."""

    label: str
    value: str


@dataclass(frozen=True)
class DisplayTable:
    """A renderer-neutral table."""

    headers: list[str]
    rows: list[list[str]]
    align: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DisplaySection:
    """A titled group of fields and optional tables."""

    title: str
    fields: list[DisplayField] = field(default_factory=list)
    tables: list[DisplayTable] = field(default_factory=list)


@dataclass(frozen=True)
class DisplayDocument:
    """Complete, renderer-neutral representation of one result."""

    title: str
    command: str
    header: list[DisplayField]
    coefficients: DisplayTable
    fit: list[DisplayField]
    sections: list[DisplaySection] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    show_ci: bool = True

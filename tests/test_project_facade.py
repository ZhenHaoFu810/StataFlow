"""Contract tests for StataFlow's public repository facade."""

from __future__ import annotations

import re
import tomllib
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parent.parent

EXPECTED_BADGES = {
    "https://github.com/ZhenHaoFu810/StataFlow/actions/workflows/ci.yml/badge.svg?branch=main": (
        "https://github.com/ZhenHaoFu810/StataFlow/actions/workflows/ci.yml"
    ),
    "https://img.shields.io/pypi/v/stataflow.svg": "https://pypi.org/project/StataFlow/",
    "https://static.pepy.tech/badge/stataflow": (
        "https://pepy.tech/projects/stataflow?timeRange=threeMonths&category=version&includeCIDownloads=true"
        "&granularity=weekly&viewType=line&versions=Total%2C1.*%2C0.*"
    ),
    "https://img.shields.io/pypi/pyversions/stataflow.svg": "https://pypi.org/project/StataFlow/",
    "https://img.shields.io/pypi/l/stataflow.svg": "LICENSE",
    "https://img.shields.io/pypi/types/stataflow.svg": "https://pypi.org/project/StataFlow/",
    "https://img.shields.io/badge/Stata_validation-documented_support_surface-1f6f5f.svg": "VALIDATION.md",
}

EXPECTED_KEYWORDS = [
    "econometrics",
    "stata",
    "regression",
    "fixed-effects",
    "panel-data",
    "instrumental-variables",
    "causal-inference",
]

EXPECTED_URLS = {
    "Homepage": "https://github.com/ZhenHaoFu810/StataFlow",
    "Repository": "https://github.com/ZhenHaoFu810/StataFlow",
    "Issues": "https://github.com/ZhenHaoFu810/StataFlow/issues",
    "Documentation": "https://github.com/ZhenHaoFu810/StataFlow#documentation",
    "Changelog": "https://github.com/ZhenHaoFu810/StataFlow/blob/main/CHANGELOG.md",
    "Contributing": "https://github.com/ZhenHaoFu810/StataFlow/blob/main/CONTRIBUTING.md",
}

BUG_NOTICE = (
    "Use a small synthetic data reproduction. Do not include proprietary or confidential data, credentials, tokens, "
    "unredacted local paths or usernames, or Stata license information."
)
SENSITIVE_DATA_CONFIRMATION = "I confirm that sensitive or private information has been removed."
PR_SAFETY_CHECKLIST_ITEM = (
    "- [ ] This pull request contains no private paths, raw logs, proprietary data, credentials, or Stata license "
    "information."
)
VALIDATION_RELEASE_SENTENCE = (
    "StataFlow 1.3.0 changed result presentation and metadata, not estimator or inference algorithms."
)

REQUIRED_BUG_IDS = {
    "stataflow_version",
    "python_version",
    "operating_system",
    "command_or_api",
    "reproduction",
    "observed_behavior",
    "expected_behavior",
    "sensitive_data",
}
OPTIONAL_BUG_IDS = {"traceback", "stata_comparison", "additional_context"}
REQUIRED_FEATURE_IDS = {"research_workflow", "requested_outcome"}
OPTIONAL_FEATURE_IDS = {
    "stata_command",
    "proposed_api",
    "public_references",
    "comparison_cases",
    "additional_context",
}

BUG_FIELD_TYPES = {
    "stataflow_version": "input",
    "python_version": "input",
    "operating_system": "input",
    "command_or_api": "input",
    "reproduction": "textarea",
    "observed_behavior": "textarea",
    "expected_behavior": "textarea",
    "sensitive_data": "checkboxes",
    "traceback": "textarea",
    "stata_comparison": "textarea",
    "additional_context": "textarea",
}
FEATURE_FIELD_TYPES = {
    "research_workflow": "textarea",
    "requested_outcome": "textarea",
    "stata_command": "input",
    "proposed_api": "textarea",
    "public_references": "textarea",
    "comparison_cases": "textarea",
    "additional_context": "textarea",
}

ISSUE_FORM_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes"}
ITEM_KEYS = {
    "markdown": {"type", "attributes"},
    "input": {"type", "id", "attributes", "validations"},
    "textarea": {"type", "id", "attributes", "validations"},
    "dropdown": {"type", "id", "attributes", "validations"},
    "checkboxes": {"type", "id", "attributes", "validations"},
}
ATTRIBUTE_KEYS = {
    "markdown": {"value"},
    "input": {"label", "description", "placeholder", "value"},
    "textarea": {"label", "description", "placeholder", "value", "render"},
    "dropdown": {"label", "description", "multiple", "options", "default"},
    "checkboxes": {"label", "description", "options"},
}


class _HtmlAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.destinations: list[str] = []
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "a" and attributes.get("href"):
            self.destinations.append(attributes["href"])
        elif tag.lower() == "img" and attributes.get("src"):
            self.images.append(attributes["src"])

    handle_startendtag = handle_starttag


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.is_file(), f"required public facade file is missing: {relative_path}"
    return path.read_text(encoding="utf-8")


def _load_yaml(relative_path: str) -> dict[str, object]:
    text = _read(relative_path)
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AssertionError(f"invalid YAML in {relative_path}: {exc}") from exc
    assert isinstance(document, dict), f"{relative_path} must contain a YAML mapping"
    return document


def _linked_badges(markdown: str) -> list[tuple[str, str]]:
    markdown = _without_fenced_code(markdown)
    pattern = re.compile(r"\[!\[[^\]]+\]\(([^\s)]+)\)\]\(([^\s)]+)\)")
    return pattern.findall(markdown)


def _markdown_images(markdown: str) -> list[str]:
    markdown = _without_fenced_code(markdown)
    inline_pattern = re.compile(
        r"!\[[^\]]*\]\([ \t]*(?:<([^>]+)>|([^\s)]+))"
        r"(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?[ \t]*\)"
    )
    images = inline_pattern.findall(markdown)
    destinations = [angle or bare for angle, bare in images]

    reference_pattern = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)
    references = {
        re.sub(r"\s+", " ", label.strip()).lower(): angle or bare
        for label, angle, bare in reference_pattern.findall(markdown)
    }
    full_reference_pattern = re.compile(r"!\[([^\]\n]*)\]\[([^\]\n]*)\]")
    for alt_text, identifier in full_reference_pattern.findall(markdown):
        normalized = re.sub(r"\s+", " ", (identifier or alt_text).strip()).lower()
        assert normalized in references, f"undefined Markdown image reference: {identifier or alt_text}"
        destinations.append(references[normalized])

    shortcut_pattern = re.compile(r"!\[([^\]\n]+)\](?![ \t]*[\[(])")
    for identifier in shortcut_pattern.findall(markdown):
        normalized = re.sub(r"\s+", " ", identifier.strip()).lower()
        assert normalized in references, f"undefined Markdown image reference: {identifier}"
        destinations.append(references[normalized])

    parser = _HtmlAssetParser()
    parser.feed(markdown)
    destinations.extend(parser.images)
    return destinations


def _without_fenced_code(markdown: str) -> str:
    lines: list[str] = []
    fence: str | None = None
    for line in markdown.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    text = "\n".join(lines)
    return re.sub(r"(?P<fence>`+).*?(?P=fence)", "", text, flags=re.DOTALL)


def _markdown_link_destinations(markdown: str) -> list[str]:
    """Return inline, reference-definition, and HTML link destinations."""
    markdown = _without_fenced_code(markdown)
    destinations: list[str] = []
    reference_pattern = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)
    references = {
        re.sub(r"\s+", " ", label.strip()).lower(): angle or bare
        for label, angle, bare in reference_pattern.findall(markdown)
    }

    index = 0
    while index < len(markdown):
        start = markdown.find("[", index)
        if start < 0:
            break
        if start > 0 and markdown[start - 1] == "!":
            index = start + 1
            continue

        depth = 1
        close = start + 1
        while close < len(markdown) and depth:
            if markdown[close] == "[":
                depth += 1
            elif markdown[close] == "]":
                depth -= 1
            close += 1
        if depth or close >= len(markdown) or markdown[close] != "(":
            index = start + 1
            continue

        paren_depth = 1
        end = close + 1
        while end < len(markdown) and paren_depth:
            if markdown[end] == "(":
                paren_depth += 1
            elif markdown[end] == ")":
                paren_depth -= 1
            end += 1
        if paren_depth:
            index = start + 1
            continue

        raw_destination = markdown[close + 1 : end - 1].strip()
        if raw_destination.startswith("<"):
            destination = raw_destination.partition(">")[0][1:]
        else:
            destination = raw_destination.split(maxsplit=1)[0]
        if destination:
            destinations.append(destination)
        index = end

    reference_link_pattern = re.compile(r"(?<!!)\[([^\]\n]+)\]\[([^\]\n]*)\]")
    for label, identifier in reference_link_pattern.findall(markdown):
        normalized = re.sub(r"\s+", " ", (identifier or label).strip()).lower()
        assert normalized in references, f"undefined Markdown link reference: {identifier or label}"
        destinations.append(references[normalized])

    shortcut_pattern = re.compile(r"(?<!!)\[([^\]\n]+)\](?!\s*[\[(])")
    for label in shortcut_pattern.findall(markdown):
        normalized = re.sub(r"\s+", " ", label.strip()).lower()
        if normalized in references:
            destinations.append(references[normalized])

    parser = _HtmlAssetParser()
    parser.feed(markdown)
    destinations.extend(parser.destinations)
    return destinations


def _heading_slugs(markdown: str) -> set[str]:
    slugs: set[str] = set()
    occurrences: dict[str, int] = {}
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"<[^>]+>", "", match.group(1))
        heading = re.sub(r"[`*_~]", "", heading).strip().lower()
        base = "".join(
            char
            for char in heading
            if char in "-_ " or char.isspace() or unicodedata.category(char)[0] in {"L", "N"}
        )
        base = re.sub(r"\s+", "-", base)
        suffix = occurrences.get(base, 0)
        occurrences[base] = suffix + 1
        slugs.add(base if suffix == 0 else f"{base}-{suffix}")
    return slugs


def _assert_local_readme_links_resolve(readme_name: str) -> None:
    markdown = _read(readme_name)
    readme_path = ROOT / readme_name
    for destination in _markdown_link_destinations(markdown):
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc:
            continue

        relative_target = unquote(parsed.path)
        target = readme_path if not relative_target else readme_path.parent / relative_target
        assert target.exists(), f"{readme_name} has a broken local link: {destination}"

        if parsed.fragment:
            assert target.is_file(), f"heading fragment points to a non-file target: {destination}"
            fragment = unquote(parsed.fragment).lower()
            headings = _heading_slugs(target.read_text(encoding="utf-8"))
            assert fragment in headings, f"{readme_name} has a broken heading fragment: {destination}"


def _assert_badge_contract(readme_name: str) -> None:
    markdown = _read(readme_name)
    images = _markdown_images(markdown)
    badges = _linked_badges(markdown)
    assert len(images) == 7, f"{readme_name} must contain exactly seven badge images and no other images"
    assert set(images) == set(EXPECTED_BADGES), f"{readme_name} contains an unapproved badge image"
    assert len(badges) == 7, f"{readme_name} must contain exactly seven linked badge images"
    assert set(badges) == set(EXPECTED_BADGES.items()), f"{readme_name} has an unapproved or misdirected badge"
    for badge in EXPECTED_BADGES.items():
        assert badges.count(badge) == 1, f"{readme_name} must contain badge link exactly once: {badge[0]}"


def _top_level_sections(markdown: str) -> list[tuple[str | None, str]]:
    sections: list[tuple[str | None, str]] = []
    heading: str | None = None
    lines: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"^##\s+(.+?)\s*#*\s*$", line)
        if match:
            sections.append((heading, "\n".join(lines)))
            heading = match.group(1).strip()
            lines = []
        else:
            lines.append(line)
    sections.append((heading, "\n".join(lines)))
    return sections


def _assert_stata_17_is_validation_only(readme_name: str, allowed_headings: set[str]) -> None:
    markdown = _read(readme_name)
    for heading, body in _top_level_sections(markdown):
        if "Stata 17" in body:
            assert heading in allowed_headings, (
                f"{readme_name} uses Stata 17 outside validation evidence or reproduction instructions "
                f"(section: {heading or 'top positioning'})"
            )


def _assert_sections_do_not_use_stata_17(readme_name: str, forbidden_headings: set[str]) -> None:
    for heading, body in _top_level_sections(_read(readme_name)):
        if heading in forbidden_headings:
            assert "Stata 17" not in body, f"{readme_name} uses Stata 17 in general section {heading}"


def _assert_issue_form_schema(relative_path: str) -> dict[str, object]:
    form = _load_yaml(relative_path)
    allowed_top_level = {"name", "description", "title", "labels", "assignees", "body"}
    assert set(form) <= allowed_top_level, f"{relative_path} has unsupported top-level keys"
    required_top_level = {
        "name": str,
        "description": str,
        "title": str,
        "labels": list,
        "body": list,
    }
    for key, expected_type in required_top_level.items():
        assert key in form, f"{relative_path} is missing top-level key {key}"
        assert isinstance(form[key], expected_type), f"{relative_path} key {key} has the wrong type"
    assert form["name"] and form["description"] and form["title"]
    assert form["labels"] and all(isinstance(label, str) and label for label in form["labels"])
    if "assignees" in form:
        assert isinstance(form["assignees"], list)
        assert all(isinstance(assignee, str) and assignee for assignee in form["assignees"])
    assert form["body"], f"{relative_path} body must not be empty"

    ids: list[str] = []
    for position, item in enumerate(form["body"]):
        assert isinstance(item, dict), f"{relative_path} body item {position} must be a mapping"
        item_type = item.get("type")
        assert item_type in ISSUE_FORM_TYPES, f"{relative_path} uses unsupported body type {item_type!r}"
        assert set(item) <= ITEM_KEYS[item_type], f"{relative_path} body item {position} has unsupported keys"

        attributes = item.get("attributes")
        assert isinstance(attributes, dict), f"{relative_path} body item {position} needs attributes"
        assert set(attributes) <= ATTRIBUTE_KEYS[item_type], (
            f"{relative_path} body item {position} has unsupported attributes"
        )

        for key in {"label", "description", "placeholder", "value", "render"} & set(attributes):
            assert isinstance(attributes[key], str), (
                f"{relative_path} body item {position} attribute {key} must be a string"
            )

        if item_type == "markdown":
            assert isinstance(attributes.get("value"), str) and attributes["value"].strip()
            continue

        field_id = item.get("id")
        assert isinstance(field_id, str) and re.fullmatch(r"[A-Za-z0-9_-]+", field_id), (
            f"{relative_path} body item {position} needs a valid id"
        )
        ids.append(field_id)
        assert isinstance(attributes.get("label"), str) and attributes["label"].strip(), (
            f"{relative_path} field {field_id} needs a non-empty label"
        )

        validations = item.get("validations", {})
        assert isinstance(validations, dict), f"{relative_path} field {field_id} has invalid validations"
        assert set(validations) <= {"required"}, f"{relative_path} field {field_id} has unsupported validations"
        if "required" in validations:
            assert isinstance(validations["required"], bool)

        if item_type == "dropdown":
            options = attributes.get("options")
            assert isinstance(options, list) and options and all(isinstance(option, str) and option for option in options)
            if "multiple" in attributes:
                assert isinstance(attributes["multiple"], bool)
            if "default" in attributes:
                assert isinstance(attributes["default"], int) and not isinstance(attributes["default"], bool)
                assert 0 <= attributes["default"] < len(options)
        elif item_type == "checkboxes":
            options = attributes.get("options")
            assert isinstance(options, list) and options, f"{relative_path} checkbox {field_id} needs options"
            for option in options:
                assert isinstance(option, dict) and set(option) <= {"label", "required"}
                assert isinstance(option.get("label"), str) and option["label"].strip()
                if "required" in option:
                    assert isinstance(option["required"], bool)

    assert len(ids) == len(set(ids)), f"{relative_path} field ids must be unique"
    return form


def _field_items(form: dict[str, object]) -> dict[str, dict[str, object]]:
    return {item["id"]: item for item in form["body"] if item.get("type") != "markdown"}


def _field_is_required(item: dict[str, object]) -> bool:
    if item["type"] == "checkboxes":
        return bool(item["attributes"]["options"]) and all(
            option.get("required") is True for option in item["attributes"]["options"]
        )
    return item.get("validations", {}).get("required") is True


def _markdown_notices(form: dict[str, object]) -> list[str]:
    values = [item["attributes"]["value"] for item in form["body"] if item.get("type") == "markdown"]
    return [re.sub(r"\s+", " ", value).strip() for value in values]


def _assert_terms(text: str, terms: dict[str, str]) -> None:
    for name, pattern in terms.items():
        assert re.search(pattern, text, re.IGNORECASE), f"missing required {name} wording"


def test_english_readme_badges_are_exact() -> None:
    _assert_badge_contract("README.md")


def test_markdown_images_counts_shortcut_reference() -> None:
    markdown = "![extra]\n\n[extra]: extra.png\n"
    assert _markdown_images(markdown) == ["extra.png"]


def test_markdown_images_counts_inline_image_with_title() -> None:
    assert _markdown_images('![extra](extra.png "caption")') == ["extra.png"]


def test_chinese_readme_badges_are_exact() -> None:
    _assert_badge_contract("README.zh-CN.md")


def test_english_readme_local_links_resolve() -> None:
    _assert_local_readme_links_resolve("README.md")


def test_chinese_readme_local_links_resolve() -> None:
    _assert_local_readme_links_resolve("README.zh-CN.md")


def test_english_readme_positions_the_stable_release_and_validation_scope() -> None:
    markdown = _read("README.md")
    top_positioning = _top_level_sections(markdown)[0][1]
    assert "documented support surface" in top_positioning
    assert "Stata 17" not in top_positioning
    assert "latest release is **1.3.0**" in markdown
    _assert_sections_do_not_use_stata_17("README.md", {"Why StataFlow", "Features", "Supported Models"})
    _assert_stata_17_is_validation_only("README.md", {"Validation", "Running Tests"})


def test_chinese_readme_positions_the_stable_release_and_validation_scope() -> None:
    markdown = _read("README.zh-CN.md")
    top_positioning = _top_level_sections(markdown)[0][1]
    assert "已记录的支持范围" in top_positioning
    assert "Stata 17" not in top_positioning
    assert "最新稳定版本是 **1.3.0**" in markdown
    _assert_sections_do_not_use_stata_17("README.zh-CN.md", {"项目定位", "功能概览", "支持的模型"})
    _assert_stata_17_is_validation_only("README.zh-CN.md", {"验证状态", "运行测试"})


def test_pyproject_exposes_complete_public_metadata() -> None:
    metadata = tomllib.loads(_read("pyproject.toml"))["project"]
    assert metadata["version"] == "1.3.0"
    assert metadata["description"] == "Stata-aligned econometrics for Python with field-level validation"
    assert metadata["keywords"] == EXPECTED_KEYWORDS
    assert metadata["urls"] == EXPECTED_URLS


def test_validation_distinguishes_snapshot_from_presentation_release() -> None:
    text = re.sub(r"\s+", " ", _read("VALIDATION.md")).strip()
    assert "July 2026" in text
    assert "1.2.0 estimator-validation snapshot" in text
    assert "retained for 1.3.0" in text
    assert VALIDATION_RELEASE_SENTENCE in text


def test_security_supports_only_the_1_3_release_line() -> None:
    text = _read("SECURITY.md")
    assert re.search(r"^\|\s*1\.3\.x\s*\|\s*:white_check_mark:\s*\|$", text, re.MULTILINE)
    assert re.search(r"^\|\s*<\s*1\.3\s*\|\s*:x:\s*\|$", text, re.MULTILINE)
    supported_rows = re.findall(r"^\|\s*([^|]+?)\s*\|\s*:white_check_mark:\s*\|$", text, re.MULTILINE)
    assert supported_rows == ["1.3.x"]


def test_bug_report_issue_form_contract() -> None:
    form = _assert_issue_form_schema(".github/ISSUE_TEMPLATE/bug_report.yml")
    fields = _field_items(form)
    assert form["title"] == "[Bug]: "
    assert form["labels"] == ["bug"]
    assert set(fields) == REQUIRED_BUG_IDS | OPTIONAL_BUG_IDS
    assert {field_id: item["type"] for field_id, item in fields.items()} == BUG_FIELD_TYPES
    assert {field_id for field_id, item in fields.items() if _field_is_required(item)} == REQUIRED_BUG_IDS
    assert fields["sensitive_data"]["type"] == "checkboxes"
    assert all(not _field_is_required(fields[field_id]) for field_id in OPTIONAL_BUG_IDS)
    assert _markdown_notices(form)[0] == BUG_NOTICE
    sensitive_options = fields["sensitive_data"]["attributes"]["options"]
    assert sensitive_options == [{"label": SENSITIVE_DATA_CONFIRMATION, "required": True}]


def test_feature_request_issue_form_contract() -> None:
    form = _assert_issue_form_schema(".github/ISSUE_TEMPLATE/feature_request.yml")
    fields = _field_items(form)
    assert form["title"] == "[Feature]: "
    assert form["labels"] == ["enhancement"]
    assert set(fields) == REQUIRED_FEATURE_IDS | OPTIONAL_FEATURE_IDS
    assert {field_id: item["type"] for field_id, item in fields.items()} == FEATURE_FIELD_TYPES
    assert {field_id for field_id, item in fields.items() if _field_is_required(item)} == REQUIRED_FEATURE_IDS
    assert all(not _field_is_required(fields[field_id]) for field_id in OPTIONAL_FEATURE_IDS)
    notice = " ".join(_markdown_notices(form)).lower()
    assert "documented" in notice and "subsets" in notice
    assert re.search(r"(?:does not|do not|doesn't|don't)\s+(?:promise|support).*\bevery stata option\b", notice)


def test_issue_template_config_contract() -> None:
    config = _load_yaml(".github/ISSUE_TEMPLATE/config.yml")
    assert config == {
        "blank_issues_enabled": True,
        "contact_links": [
            {
                "name": "Private security report",
                "url": "https://github.com/ZhenHaoFu810/StataFlow/security/advisories/new",
                "about": "Report security vulnerabilities privately instead of opening a public issue.",
            }
        ],
    }


def test_pull_request_template_has_required_sections() -> None:
    template = _read(".github/PULL_REQUEST_TEMPLATE.md")
    headings = {slug.lower() for slug in _heading_slugs(template)}
    assert {
        "summary",
        "linked-issue",
        "tests-or-validation",
        "documentation",
        "data-provenance",
        "public-safety",
    } <= headings
    checklist = "\n".join(
        line for line in template.splitlines() if re.match(r"^\s*[-*+]\s+\[[ xX]\]\s+\S", line)
    )
    assert checklist, "pull request template must include a public-safety checklist"
    assert PR_SAFETY_CHECKLIST_ITEM in checklist

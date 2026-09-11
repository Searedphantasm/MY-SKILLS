#!/usr/bin/env python3
"""Render normalized code-review JSON as a standalone HTML report.

Usage:
    python3 render_review.py normalized-review.json review-report.html

The script uses only the Python standard library.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterable

SEVERITIES = ("blocker", "major", "minor", "nit")
CATEGORIES = ("bug", "security", "performance", "readability", "architecture", "test")
READINESS_LABELS = {
    "ready": "Ready",
    "not_ready": "Not ready",
    "undetermined": "Undetermined",
}
RELATIONSHIP_LABELS = {
    "same_root_cause": "Same root cause",
    "repeated": "Repeated issue",
    "causes": "Causes",
    "amplifies": "Amplifies",
    "duplicate": "Duplicate",
    "related": "Related",
}


def fail(message: str) -> None:
    raise SystemExit(f"review-visualizer: {message}")


def text(value: Any, fallback: str = "Unknown") -> str:
    if value is None:
        return fallback
    rendered = str(value).strip()
    return rendered if rendered else fallback


def h(value: Any, fallback: str = "Unknown") -> str:
    return escape(text(value, fallback), quote=True)


def normalize_severity(value: Any) -> str:
    candidate = str(value).strip().lower() if value is not None else ""
    return candidate if candidate in SEVERITIES else "unspecified"


def normalize_category(value: Any) -> str:
    candidate = str(value).strip().lower() if value is not None else ""
    return candidate if candidate in CATEGORIES else "uncategorized"


def validate_report(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        fail("the input JSON root must be an object")

    required = (
        "title",
        "summary",
        "merge_readiness",
        "reviewed_files",
        "findings",
        "positives",
        "unresolved_notes",
    )
    missing = [key for key in required if key not in report]
    if missing:
        fail(f"missing required field(s): {', '.join(missing)}")

    if not isinstance(report["findings"], list):
        fail("findings must be an array")
    if not isinstance(report["reviewed_files"], list):
        fail("reviewed_files must be an array")
    if not isinstance(report["positives"], list):
        fail("positives must be an array")
    if not isinstance(report["unresolved_notes"], list):
        fail("unresolved_notes must be an array")
    if not isinstance(report["merge_readiness"], dict):
        fail("merge_readiness must be an object")

    ids: set[str] = set()
    for index, finding in enumerate(report["findings"], start=1):
        if not isinstance(finding, dict):
            fail(f"finding #{index} must be an object")
        finding_id = text(finding.get("id"), "")
        if not finding_id:
            fail(f"finding #{index} has no id")
        if finding_id in ids:
            fail(f"duplicate finding id: {finding_id}")
        ids.add(finding_id)
        if not isinstance(finding.get("location", {}), dict):
            fail(f"finding {finding_id} location must be an object")
        if not isinstance(finding.get("related_findings", []), list):
            fail(f"finding {finding_id} related_findings must be an array")

    return report


def unique_file_paths(report: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    def add(candidate: Any) -> None:
        if candidate is None:
            return
        path = str(candidate).strip()
        if path and path not in seen:
            seen.add(path)
            result.append(path)

    for item in report["reviewed_files"]:
        if isinstance(item, dict):
            add(item.get("path"))
    for finding in report["findings"]:
        location = finding.get("location") or {}
        add(location.get("file"))
    for positive in report["positives"]:
        if isinstance(positive, dict):
            add(positive.get("file"))
    return result


def render_badge(kind: str, value: str, label: str | None = None) -> str:
    visible = label or value.replace("_", " ").title()
    return f'<span class="badge badge-{h(kind)} badge-{h(value)}">{h(visible)}</span>'


def render_location(finding: dict[str, Any]) -> str:
    location = finding.get("location") or {}
    file_name = text(location.get("file"), "Unknown file")
    line = text(location.get("line"), "Unknown line")
    symbol = text(location.get("symbol"), "Unknown symbol")
    parts = [
        f'<span><strong>File:</strong> <code>{h(file_name)}</code></span>',
        f'<span><strong>Line:</strong> {h(line)}</span>',
        f'<span><strong>Symbol:</strong> <code>{h(symbol)}</code></span>',
    ]
    return '<div class="location">' + "".join(parts) + "</div>"


def render_code_pair(finding: dict[str, Any]) -> str:
    before = finding.get("before")
    after = finding.get("after")
    if before is None and after is None:
        return ""

    language = text(finding.get("language"), "text")
    panels: list[str] = []
    if before is not None:
        panels.append(
            '<section class="code-panel code-before">'
            '<header><span>Before</span>'
            f'<span class="code-language">{h(language)}</span></header>'
            f'<pre><code>{escape(str(before))}</code></pre>'
            '</section>'
        )
    if after is not None:
        panels.append(
            '<section class="code-panel code-after">'
            '<header><span>After</span>'
            f'<span class="code-language">{h(language)}</span></header>'
            f'<pre><code>{escape(str(after))}</code></pre>'
            '</section>'
        )
    return '<div class="code-grid">' + "".join(panels) + "</div>"


def render_relationships(finding: dict[str, Any], valid_ids: set[str]) -> str:
    relations = finding.get("related_findings") or []
    items: list[str] = []
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        target = text(relation.get("id"), "Unknown finding")
        relation_type = text(relation.get("relationship"), "related")
        relation_label = RELATIONSHIP_LABELS.get(relation_type, relation_type.replace("_", " ").title())
        note = relation.get("note")
        if target in valid_ids:
            target_html = f'<a href="#{h(target)}">{h(target)}</a>'
        else:
            target_html = f'<span>{h(target)}</span>'
        note_html = f'<span class="relationship-note">{h(note)}</span>' if note else ""
        items.append(
            '<li>'
            f'{render_badge("relation", relation_type, relation_label)} '
            f'{target_html}{note_html}'
            '</li>'
        )
    if not items:
        return ""
    return (
        '<section class="finding-section">'
        '<h4>Related findings</h4>'
        '<ul class="relationship-list">'
        + "".join(items)
        + '</ul></section>'
    )


def render_optional_section(title: str, value: Any, css_class: str = "") -> str:
    if value is None or not str(value).strip():
        return ""
    class_attr = f' {css_class}' if css_class else ""
    return (
        f'<section class="finding-section{class_attr}">'
        f'<h4>{h(title)}</h4>'
        f'<p>{h(value)}</p>'
        '</section>'
    )


def render_finding(finding: dict[str, Any], valid_ids: set[str]) -> str:
    finding_id = text(finding.get("id"), "Unknown")
    title = text(finding.get("title"), "Untitled finding")
    severity = normalize_severity(finding.get("severity"))
    category = normalize_category(finding.get("category"))
    category_inferred = bool(finding.get("category_inferred"))
    location = finding.get("location") or {}
    file_name = text(location.get("file"), "Unknown file")

    category_label = category.title()
    if category_inferred and category != "uncategorized":
        category_label += " · inferred"

    return f'''
<details class="finding-card severity-{h(severity)}" id="{h(finding_id)}"
         data-severity="{h(severity)}" data-file="{h(file_name)}">
  <summary>
    <span class="summary-main">
      <span class="finding-id">{h(finding_id)}</span>
      <span class="finding-title">{h(title)}</span>
    </span>
    <span class="summary-badges">
      {render_badge("severity", severity)}
      {render_badge("category", category, category_label)}
    </span>
  </summary>
  <div class="finding-body">
    {render_location(finding)}
    {render_optional_section("Problem", finding.get("problem"), "problem-section")}
    {render_optional_section("Impact or risk", finding.get("impact"))}
    {render_optional_section("Suggested fix", finding.get("suggested_fix"), "fix-section")}
    {render_code_pair(finding)}
    {render_relationships(finding, valid_ids)}
    {render_optional_section("Source excerpt", finding.get("source_excerpt"), "source-section")}
  </div>
</details>
'''


def render_file_list(report: dict[str, Any], file_paths: list[str]) -> str:
    counts = Counter()
    notes: dict[str, str] = {}
    for finding in report["findings"]:
        location = finding.get("location") or {}
        counts[text(location.get("file"), "Unknown file")] += 1
    for item in report["reviewed_files"]:
        if isinstance(item, dict):
            path = text(item.get("path"), "")
            note = item.get("note")
            if path and note:
                notes[path] = str(note)

    cards: list[str] = []
    for path in file_paths:
        count = counts[path]
        note = f'<p>{h(notes[path])}</p>' if path in notes else ""
        cards.append(
            '<article class="file-card">'
            f'<code>{h(path)}</code>'
            f'<span class="file-count">{count} finding{"s" if count != 1 else ""}</span>'
            f'{note}'
            '</article>'
        )
    if "Unknown file" in counts and "Unknown file" not in file_paths:
        count = counts["Unknown file"]
        cards.append(
            '<article class="file-card file-unknown">'
            '<code>Unknown file</code>'
            f'<span class="file-count">{count} finding{"s" if count != 1 else ""}</span>'
            '</article>'
        )
    return "".join(cards) or '<p class="empty-state">No reviewed files were identified.</p>'


def render_positive_list(positives: Iterable[Any]) -> str:
    cards: list[str] = []
    for positive in positives:
        if isinstance(positive, dict):
            body = positive.get("text")
            file_name = positive.get("file")
            location = positive.get("location")
        else:
            body = positive
            file_name = None
            location = None
        if body is None or not str(body).strip():
            continue
        meta: list[str] = []
        if file_name:
            meta.append(f'<code>{h(file_name)}</code>')
        if location:
            meta.append(f'<span>{h(location)}</span>')
        meta_html = f'<div class="positive-meta">{"".join(meta)}</div>' if meta else ""
        cards.append(
            '<article class="positive-card">'
            '<span class="positive-icon" aria-hidden="true">✓</span>'
            '<div>'
            f'<p>{h(body)}</p>{meta_html}'
            '</div></article>'
        )
    return "".join(cards) or '<p class="empty-state">No positive observations were included in the review.</p>'


def render_unresolved(notes: Iterable[Any]) -> str:
    items = [f'<li>{h(note)}</li>' for note in notes if str(note).strip()]
    if not items:
        return ""
    return (
        '<section class="panel unresolved-panel">'
        '<div class="section-heading">'
        '<div><p class="eyebrow">Preserved ambiguity</p><h2>Unresolved review notes</h2></div>'
        '</div>'
        '<p class="section-copy">These statements could not be mapped to a precise finding without inventing missing details.</p>'
        '<ul class="unresolved-list">'
        + "".join(items)
        + '</ul></section>'
    )


def stat_card(label: str, value: int, data_kind: str = "") -> str:
    extra = f' data-kind="{h(data_kind)}"' if data_kind else ""
    return (
        f'<article class="stat-card"{extra}>'
        f'<span class="stat-value">{value}</span>'
        f'<span class="stat-label">{h(label)}</span>'
        '</article>'
    )


def render_html(report: dict[str, Any]) -> str:
    findings = report["findings"]
    valid_ids = {text(item.get("id"), "") for item in findings}
    severities = Counter(normalize_severity(item.get("severity")) for item in findings)
    categories = Counter(normalize_category(item.get("category")) for item in findings)
    file_paths = unique_file_paths(report)

    readiness = report.get("merge_readiness") or {}
    readiness_status = text(readiness.get("status"), "undetermined")
    if readiness_status not in READINESS_LABELS:
        readiness_status = "undetermined"
    readiness_reason = text(readiness.get("reason"), "No explicit merge decision was found in the review.")

    blocker_items = [item for item in findings if normalize_severity(item.get("severity")) == "blocker"]
    blocker_html = "".join(
        f'<li><a href="#{h(item.get("id"))}"><span>{h(item.get("id"))}</span>{h(item.get("title"), "Untitled finding")}</a></li>'
        for item in blocker_items
    ) or '<li class="empty-list-item">No blocker findings were explicitly identified.</li>'

    severity_stats = "".join(
        stat_card(label, severities[key], key)
        for key, label in (
            ("blocker", "Blocker"),
            ("major", "Major"),
            ("minor", "Minor"),
            ("nit", "Nit"),
            ("unspecified", "Unspecified"),
        )
    )

    category_chips = "".join(
        f'<span class="count-chip"><span>{h(label)}</span><strong>{categories[key]}</strong></span>'
        for key, label in (
            ("bug", "Bug"),
            ("security", "Security"),
            ("performance", "Performance"),
            ("readability", "Readability"),
            ("architecture", "Architecture"),
            ("test", "Test"),
            ("uncategorized", "Uncategorized"),
        )
    )

    file_options = "".join(f'<option value="{h(path)}">{h(path)}</option>' for path in file_paths)
    if any(text((item.get("location") or {}).get("file"), "Unknown file") == "Unknown file" for item in findings):
        if "Unknown file" not in file_paths:
            file_options += '<option value="Unknown file">Unknown file</option>'

    findings_html = "".join(render_finding(item, valid_ids) for item in findings)
    if not findings_html:
        findings_html = '<p class="empty-state">No findings were identified in the review.</p>'

    generated_at = report.get("generated_at")
    if generated_at:
        generated_label = text(generated_at)
    else:
        generated_label = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    source_label = report.get("source_label")
    source_meta = f'<span>{h(source_label)}</span><span aria-hidden="true">·</span>' if source_label else ""

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{h(report.get("title"), "Code Review Report")}</title>
<style>
:root {{
  --bg: #f4f6f8;
  --surface: #ffffff;
  --surface-raised: #ffffff;
  --surface-muted: #eef1f4;
  --text: #17202a;
  --text-muted: #5b6673;
  --border: #d8dee6;
  --shadow: 0 12px 36px rgba(24, 33, 45, 0.08);
  --accent: #3157d5;
  --accent-soft: #e9eeff;
  --focus: #4c74ff;
  --success: #16794a;
  --success-soft: #e7f7ef;
  --danger: #b42318;
  --danger-soft: #ffebe9;
  --warning: #9a6700;
  --warning-soft: #fff4d6;
  --code-bg: #10151d;
  --code-text: #ecf2f8;
  --blocker: #b42318;
  --major: #c45600;
  --minor: #9a6700;
  --nit: #52606d;
  --unspecified: #6b7280;
  --radius: 16px;
}}

:root[data-theme="dark"] {{
  --bg: #0c1118;
  --surface: #121923;
  --surface-raised: #17202b;
  --surface-muted: #1b2531;
  --text: #edf2f7;
  --text-muted: #a9b4c0;
  --border: #2a3745;
  --shadow: 0 16px 44px rgba(0, 0, 0, 0.32);
  --accent: #8aa4ff;
  --accent-soft: #1c2a52;
  --focus: #9bb1ff;
  --success: #6fd2a4;
  --success-soft: #12392b;
  --danger: #ff938a;
  --danger-soft: #431c1c;
  --warning: #f4c567;
  --warning-soft: #3b2f12;
  --code-bg: #080c12;
  --code-text: #f1f5f9;
  --blocker: #ff938a;
  --major: #ffb171;
  --minor: #f4c567;
  --nit: #aeb8c2;
  --unspecified: #aab2bd;
}}

@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #0c1118;
    --surface: #121923;
    --surface-raised: #17202b;
    --surface-muted: #1b2531;
    --text: #edf2f7;
    --text-muted: #a9b4c0;
    --border: #2a3745;
    --shadow: 0 16px 44px rgba(0, 0, 0, 0.32);
    --accent: #8aa4ff;
    --accent-soft: #1c2a52;
    --focus: #9bb1ff;
    --success: #6fd2a4;
    --success-soft: #12392b;
    --danger: #ff938a;
    --danger-soft: #431c1c;
    --warning: #f4c567;
    --warning-soft: #3b2f12;
    --code-bg: #080c12;
    --code-text: #f1f5f9;
    --blocker: #ff938a;
    --major: #ffb171;
    --minor: #f4c567;
    --nit: #aeb8c2;
    --unspecified: #aab2bd;
  }}
}}

* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.55;
}}
button, select {{ font: inherit; }}
button, select, summary, a {{ -webkit-tap-highlight-color: transparent; }}
a {{ color: var(--accent); }}
a:hover {{ text-decoration-thickness: 2px; }}
:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
code, pre {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }}
code {{ overflow-wrap: anywhere; }}

.page-shell {{ width: min(1380px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 64px; }}
.topbar {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin-bottom: 24px; }}
.brand {{ max-width: 880px; }}
.eyebrow {{ margin: 0 0 4px; color: var(--accent); font-size: 0.76rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }}
h1, h2, h3, h4, p {{ overflow-wrap: anywhere; }}
h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 3.8rem); line-height: 1.04; letter-spacing: -0.045em; }}
h2 {{ margin: 0; font-size: clamp(1.45rem, 3vw, 2rem); letter-spacing: -0.025em; }}
h3 {{ margin: 0; font-size: 1rem; }}
h4 {{ margin: 0 0 8px; font-size: 0.8rem; letter-spacing: 0.055em; text-transform: uppercase; color: var(--text-muted); }}
.subtitle {{ margin: 14px 0 0; color: var(--text-muted); max-width: 820px; font-size: 1.04rem; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; color: var(--text-muted); font-size: 0.84rem; }}
.theme-toggle {{ flex: 0 0 auto; border: 1px solid var(--border); background: var(--surface); color: var(--text); border-radius: 999px; padding: 10px 14px; cursor: pointer; box-shadow: var(--shadow); }}
.theme-toggle:hover {{ background: var(--surface-muted); }}

.dashboard {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr); gap: 18px; margin-bottom: 18px; }}
.panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); padding: 22px; }}
.overview-panel {{ min-width: 0; }}
.readiness-panel {{ display: flex; flex-direction: column; min-width: 0; }}
.readiness-status {{ display: inline-flex; width: fit-content; align-items: center; gap: 8px; margin-top: 10px; padding: 8px 11px; border-radius: 999px; font-weight: 800; }}
.readiness-ready {{ color: var(--success); background: var(--success-soft); }}
.readiness-not_ready {{ color: var(--danger); background: var(--danger-soft); }}
.readiness-undetermined {{ color: var(--warning); background: var(--warning-soft); }}
.readiness-reason {{ color: var(--text-muted); margin: 14px 0 0; }}

.stats-grid {{ display: grid; grid-template-columns: repeat(6, minmax(100px, 1fr)); gap: 10px; margin-top: 18px; }}
.stat-card {{ min-width: 0; background: var(--surface-muted); border: 1px solid var(--border); border-radius: 13px; padding: 14px; }}
.stat-card:first-child {{ background: var(--accent-soft); }}
.stat-value {{ display: block; font-size: 1.65rem; line-height: 1; font-weight: 850; }}
.stat-label {{ display: block; margin-top: 7px; color: var(--text-muted); font-size: 0.78rem; font-weight: 700; }}
.category-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
.count-chip {{ display: inline-flex; gap: 8px; align-items: center; border: 1px solid var(--border); border-radius: 999px; padding: 6px 9px; color: var(--text-muted); font-size: 0.78rem; }}
.count-chip strong {{ color: var(--text); }}
.blocker-box {{ margin-top: 18px; border-top: 1px solid var(--border); padding-top: 16px; }}
.blocker-list {{ margin: 8px 0 0; padding: 0; list-style: none; display: grid; gap: 7px; }}
.blocker-list a {{ display: flex; gap: 10px; text-decoration: none; background: var(--danger-soft); color: var(--danger); border-radius: 10px; padding: 9px 11px; font-weight: 700; }}
.blocker-list a span {{ font-family: monospace; }}
.empty-list-item {{ color: var(--text-muted); }}

.section-heading {{ display: flex; justify-content: space-between; gap: 18px; align-items: flex-end; }}
.section-copy {{ color: var(--text-muted); margin: 7px 0 0; }}
.files-panel, .positives-panel, .unresolved-panel {{ margin-bottom: 18px; }}
.file-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; margin-top: 16px; }}
.file-card {{ position: relative; background: var(--surface-muted); border: 1px solid var(--border); border-radius: 13px; padding: 14px; min-width: 0; }}
.file-card code {{ display: block; padding-right: 78px; font-size: 0.84rem; font-weight: 700; }}
.file-card p {{ margin: 10px 0 0; color: var(--text-muted); font-size: 0.82rem; }}
.file-count {{ position: absolute; top: 11px; right: 11px; color: var(--text-muted); font-size: 0.72rem; font-weight: 800; }}

.controls-panel {{ position: sticky; top: 10px; z-index: 10; margin-bottom: 14px; }}
.controls {{ display: grid; grid-template-columns: minmax(150px, 0.55fr) minmax(220px, 1.45fr) auto auto; gap: 10px; align-items: end; }}
.control-group {{ display: grid; gap: 6px; }}
.control-group label {{ color: var(--text-muted); font-size: 0.74rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; }}
select, .control-button {{ min-height: 42px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface-raised); color: var(--text); padding: 9px 11px; }}
.control-button {{ cursor: pointer; font-weight: 750; }}
.control-button:hover {{ background: var(--surface-muted); }}
.filter-status {{ margin: 10px 0 0; color: var(--text-muted); font-size: 0.83rem; }}

.findings-list {{ display: grid; gap: 10px; }}
.finding-card {{ background: var(--surface); border: 1px solid var(--border); border-left: 5px solid var(--unspecified); border-radius: 14px; box-shadow: var(--shadow); scroll-margin-top: 120px; overflow: clip; }}
.finding-card.severity-blocker {{ border-left-color: var(--blocker); }}
.finding-card.severity-major {{ border-left-color: var(--major); }}
.finding-card.severity-minor {{ border-left-color: var(--minor); }}
.finding-card.severity-nit {{ border-left-color: var(--nit); }}
.finding-card.severity-unspecified {{ border-left-color: var(--unspecified); }}
.finding-card[hidden] {{ display: none; }}
.finding-card summary {{ cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 17px 18px; list-style: none; }}
.finding-card summary::-webkit-details-marker {{ display: none; }}
.finding-card summary::after {{ content: "+"; flex: 0 0 auto; color: var(--text-muted); font-size: 1.45rem; line-height: 1; }}
.finding-card[open] summary::after {{ content: "−"; }}
.summary-main {{ min-width: 0; display: flex; align-items: baseline; gap: 12px; }}
.finding-id {{ color: var(--text-muted); font-family: monospace; font-size: 0.8rem; font-weight: 800; }}
.finding-title {{ font-weight: 800; }}
.summary-badges {{ display: flex; flex-wrap: wrap; gap: 7px; justify-content: flex-end; }}
.badge {{ display: inline-flex; align-items: center; width: fit-content; border: 1px solid var(--border); border-radius: 999px; padding: 4px 8px; font-size: 0.7rem; font-weight: 850; letter-spacing: 0.035em; text-transform: uppercase; white-space: nowrap; }}
.badge-severity.badge-blocker {{ color: var(--blocker); background: var(--danger-soft); border-color: transparent; }}
.badge-severity.badge-major {{ color: var(--major); background: color-mix(in srgb, var(--major) 13%, transparent); }}
.badge-severity.badge-minor {{ color: var(--minor); background: var(--warning-soft); border-color: transparent; }}
.badge-severity.badge-nit {{ color: var(--nit); background: var(--surface-muted); }}
.badge-severity.badge-unspecified {{ color: var(--unspecified); background: var(--surface-muted); border-style: dashed; }}
.badge-category {{ color: var(--accent); background: var(--accent-soft); border-color: transparent; }}
.badge-relation {{ color: var(--text-muted); background: var(--surface-muted); font-size: 0.62rem; }}
.finding-body {{ border-top: 1px solid var(--border); padding: 18px; }}
.location {{ display: flex; flex-wrap: wrap; gap: 8px 18px; background: var(--surface-muted); border-radius: 10px; padding: 10px 12px; color: var(--text-muted); font-size: 0.82rem; }}
.location strong {{ color: var(--text); }}
.finding-section {{ margin-top: 18px; }}
.finding-section p {{ margin: 0; white-space: pre-wrap; }}
.problem-section p {{ font-size: 1rem; }}
.fix-section {{ border-left: 3px solid var(--success); padding-left: 12px; }}
.source-section {{ color: var(--text-muted); }}

.code-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }}
.code-grid:has(.code-panel:only-child) {{ grid-template-columns: minmax(0, 1fr); }}
.code-panel {{ min-width: 0; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--code-bg); }}
.code-panel header {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 11px; background: var(--surface-muted); color: var(--text); font-size: 0.76rem; font-weight: 800; }}
.code-before header {{ border-left: 4px solid var(--danger); }}
.code-after header {{ border-left: 4px solid var(--success); }}
.code-language {{ color: var(--text-muted); font-family: monospace; }}
pre {{ margin: 0; padding: 14px; overflow-x: auto; background: var(--code-bg); color: var(--code-text); font-size: 0.82rem; line-height: 1.6; tab-size: 2; }}
pre code {{ white-space: pre; }}

.relationship-list {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 7px; }}
.relationship-list li {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }}
.relationship-note {{ flex-basis: 100%; padding-left: 3px; color: var(--text-muted); font-size: 0.82rem; }}

.positive-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; margin-top: 16px; }}
.positive-card {{ display: flex; gap: 12px; background: var(--success-soft); border: 1px solid color-mix(in srgb, var(--success) 24%, transparent); border-radius: 13px; padding: 14px; }}
.positive-card p {{ margin: 0; }}
.positive-icon {{ display: grid; place-items: center; flex: 0 0 28px; height: 28px; border-radius: 50%; background: var(--success); color: var(--surface); font-weight: 900; }}
.positive-meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 9px; color: var(--text-muted); font-size: 0.78rem; }}
.unresolved-panel {{ border-style: dashed; }}
.unresolved-list {{ margin: 14px 0 0; padding-left: 22px; }}
.empty-state {{ color: var(--text-muted); }}
.no-results {{ display: none; margin: 16px 0 0; padding: 20px; text-align: center; color: var(--text-muted); background: var(--surface); border: 1px dashed var(--border); border-radius: 13px; }}
.no-results.visible {{ display: block; }}
.footer {{ margin-top: 22px; text-align: center; color: var(--text-muted); font-size: 0.78rem; }}

@media (max-width: 1000px) {{
  .dashboard {{ grid-template-columns: 1fr; }}
  .stats-grid {{ grid-template-columns: repeat(3, minmax(100px, 1fr)); }}
  .controls {{ grid-template-columns: 1fr 1fr; }}
}}

@media (max-width: 680px) {{
  .page-shell {{ width: min(100% - 20px, 1380px); padding-top: 18px; }}
  .topbar {{ gap: 12px; }}
  .theme-toggle {{ padding: 9px 11px; }}
  .panel {{ padding: 16px; border-radius: 13px; }}
  .stats-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .controls {{ grid-template-columns: 1fr; }}
  .controls-panel {{ position: static; }}
  .finding-card summary {{ align-items: flex-start; padding: 15px; }}
  .summary-main {{ display: grid; gap: 3px; }}
  .summary-badges {{ display: none; }}
  .finding-body {{ padding: 15px; }}
  .code-grid {{ grid-template-columns: 1fr; }}
  .file-card code {{ padding-right: 0; padding-top: 21px; }}
}}

@media print {{
  :root {{ --bg: white; --surface: white; --surface-raised: white; --surface-muted: #f4f4f4; --text: black; --text-muted: #444; --border: #bbb; --shadow: none; }}
  .theme-toggle, .controls-panel {{ display: none !important; }}
  .page-shell {{ width: 100%; padding: 0; }}
  .finding-card {{ break-inside: avoid; }}
  .finding-card > .finding-body {{ display: block; }}
}}
</style>
</head>
<body>
<main class="page-shell">
  <header class="topbar">
    <div class="brand">
      <p class="eyebrow">Code review visualization</p>
      <h1>{h(report.get("title"), "Code Review Report")}</h1>
      <p class="subtitle">{h(report.get("summary"), "No summary was provided.")}</p>
      <div class="meta">{source_meta}<span>Generated {h(generated_label)}</span></div>
    </div>
    <button class="theme-toggle" id="themeToggle" type="button" aria-label="Toggle color theme">Theme</button>
  </header>

  <section class="dashboard" aria-label="Review overview">
    <article class="panel overview-panel">
      <p class="eyebrow">Overview</p>
      <h2>Review findings</h2>
      <div class="stats-grid">
        {stat_card("Total", len(findings))}
        {severity_stats}
      </div>
      <div class="category-row" aria-label="Counts by category">{category_chips}</div>
      <div class="blocker-box">
        <h3>Blockers</h3>
        <ul class="blocker-list">{blocker_html}</ul>
      </div>
    </article>

    <aside class="panel readiness-panel">
      <p class="eyebrow">Merge readiness</p>
      <h2>{h(READINESS_LABELS[readiness_status])}</h2>
      <span class="readiness-status readiness-{h(readiness_status)}">{h(READINESS_LABELS[readiness_status])}</span>
      <p class="readiness-reason">{h(readiness_reason)}</p>
    </aside>
  </section>

  <section class="panel files-panel">
    <div class="section-heading">
      <div><p class="eyebrow">Coverage</p><h2>Reviewed files</h2></div>
    </div>
    <div class="file-grid">{render_file_list(report, file_paths)}</div>
  </section>

  <section class="panel controls-panel" aria-label="Finding filters">
    <div class="controls">
      <div class="control-group">
        <label for="severityFilter">Severity</label>
        <select id="severityFilter">
          <option value="all">All severities</option>
          <option value="blocker">Blocker</option>
          <option value="major">Major</option>
          <option value="minor">Minor</option>
          <option value="nit">Nit</option>
          <option value="unspecified">Unspecified</option>
        </select>
      </div>
      <div class="control-group">
        <label for="fileFilter">File</label>
        <select id="fileFilter">
          <option value="all">All files</option>
          {file_options}
        </select>
      </div>
      <button class="control-button" id="expandAll" type="button">Expand visible</button>
      <button class="control-button" id="collapseAll" type="button">Collapse visible</button>
    </div>
    <p class="filter-status" id="filterStatus" aria-live="polite"></p>
  </section>

  <section aria-labelledby="findings-title">
    <div class="section-heading" style="margin: 22px 0 12px;">
      <div><p class="eyebrow">Detailed review</p><h2 id="findings-title">Findings</h2></div>
    </div>
    <div class="findings-list" id="findingsList">{findings_html}</div>
    <p class="no-results" id="noResults">No findings match these filters.</p>
  </section>

  <section class="panel positives-panel" style="margin-top: 18px;">
    <div class="section-heading">
      <div><p class="eyebrow">What went well</p><h2>Positive observations</h2></div>
    </div>
    <div class="positive-grid">{render_positive_list(report["positives"])}</div>
  </section>

  {render_unresolved(report["unresolved_notes"])}

  <footer class="footer">Standalone report generated by review-visualizer.</footer>
</main>
<script>
(() => {{
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const severityFilter = document.getElementById('severityFilter');
  const fileFilter = document.getElementById('fileFilter');
  const filterStatus = document.getElementById('filterStatus');
  const noResults = document.getElementById('noResults');
  const cards = Array.from(document.querySelectorAll('.finding-card'));

  const storedTheme = localStorage.getItem('review-visualizer-theme');
  if (storedTheme === 'light' || storedTheme === 'dark') {{
    root.dataset.theme = storedTheme;
  }}

  const activeTheme = () => {{
    if (root.dataset.theme) return root.dataset.theme;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }};

  const updateThemeLabel = () => {{
    themeToggle.textContent = activeTheme() === 'dark' ? 'Light theme' : 'Dark theme';
  }};

  themeToggle.addEventListener('click', () => {{
    const next = activeTheme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    localStorage.setItem('review-visualizer-theme', next);
    updateThemeLabel();
  }});
  updateThemeLabel();

  const applyFilters = () => {{
    const severity = severityFilter.value;
    const file = fileFilter.value;
    let visible = 0;

    cards.forEach(card => {{
      const severityMatch = severity === 'all' || card.dataset.severity === severity;
      const fileMatch = file === 'all' || card.dataset.file === file;
      card.hidden = !(severityMatch && fileMatch);
      if (!card.hidden) visible += 1;
    }});

    filterStatus.textContent = `${{visible}} of ${{cards.length}} findings visible`;
    noResults.classList.toggle('visible', visible === 0);
  }};

  severityFilter.addEventListener('change', applyFilters);
  fileFilter.addEventListener('change', applyFilters);

  document.getElementById('expandAll').addEventListener('click', () => {{
    cards.forEach(card => {{ if (!card.hidden) card.open = true; }});
  }});

  document.getElementById('collapseAll').addEventListener('click', () => {{
    cards.forEach(card => {{ if (!card.hidden) card.open = false; }});
  }});

  document.querySelectorAll('a[href^="#F-"]').forEach(link => {{
    link.addEventListener('click', () => {{
      const target = document.querySelector(link.getAttribute('href'));
      if (target && !target.hidden) target.open = true;
    }});
  }});

  applyFilters();
}})();
</script>
</body>
</html>
'''


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        fail("usage: render_review.py INPUT.json OUTPUT.html")

    input_path = Path(argv[1]).expanduser().resolve()
    output_path = Path(argv[2]).expanduser().resolve()

    if not input_path.is_file():
        fail(f"input file not found: {input_path}")

    try:
        report = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {input_path}: {error}")

    report = validate_report(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(report), encoding="utf-8")
    print(f"Created {output_path}")


if __name__ == "__main__":
    main(sys.argv)

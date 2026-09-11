---
name: review-visualizer
description: Convert a pasted code-review narrative into a standalone, interactive HTML report that visualizes reviewed files, findings, severities, categories, locations, fixes, code diffs, relationships, positive observations, and merge readiness without inventing missing facts.
---

# Review Visualizer

Use this skill whenever the user provides a code review as text and asks for a visual report, HTML report, review dashboard, review summary page, or an easier way to inspect review findings.

## Goal

Transform unstructured code-review text into one self-contained HTML file. The report must be faithful to the source review, easy to scan, responsive, accessible, and usable without a server, framework, CDN, or external asset.

## Output contract

Produce exactly one primary artifact:

- `review-report.html`

The HTML file must contain all CSS inside a `<style>` element and all JavaScript inside a `<script>` element. It must work when opened directly from the filesystem.

Do not require npm, a bundler, a browser extension, a framework, external fonts, syntax-highlighting packages, or network access.

## Required report sections

The report must include:

1. **Overview**
   - Total finding count.
   - Counts by severity: `blocker`, `major`, `minor`, `nit`, and `unspecified`.
   - Counts by category: `bug`, `security`, `performance`, `readability`, `architecture`, `test`, and `uncategorized`.
   - A visible list of blocker findings.
   - Merge-readiness status: `Ready`, `Not ready`, or `Undetermined`.
   - A concise review summary.

2. **Reviewed files**
   - Every reviewed file named in the source text.
   - Finding count per file.
   - Files mentioned without findings must still be listed with a zero count when the review clearly says they were reviewed.

3. **Findings**
   - Stable finding ID, such as `F-001`.
   - Title.
   - Severity, or `Unspecified` when absent.
   - Category, or `Uncategorized` when absent or unclear.
   - Exact location when available: file path plus line number, line range, symbol, method, class, component, route, query, or module.
   - Problem explanation.
   - Impact or risk, only when present in the source review.
   - Suggested fix, only when present in the source review.
   - Optional before/after code snippets.
   - Related finding links when the review explicitly connects issues or clearly describes the same root problem across locations.

4. **Positive observations**
   - Correct decisions, good patterns, useful tests, clear code, or other strengths explicitly mentioned by the reviewer.

5. **Relationships**
   - Repeated issue across files.
   - Shared root cause.
   - One finding causing or amplifying another.
   - Duplicate or closely related findings.

## Non-invention rules

These rules are mandatory:

- Never invent a severity.
- Only use `blocker`, `major`, `minor`, or `nit` when that severity is present in the source review or represented by a direct equivalent explicitly defined by the reviewer.
- If severity is missing, render `Unspecified`.
- Never invent a file path, line number, symbol, function name, code snippet, impact, fix, relationship, positive note, or merge decision.
- If a location is incomplete, preserve what is known and mark the missing part as `Unknown`.
- If the review refers to “this function”, “the handler”, or another unresolved location, use `Unknown location` and preserve the original wording in the explanation.
- Do not convert vague language into a precise claim.
- Do not infer merge readiness solely from finding counts. Use an explicit reviewer conclusion when present. Otherwise render `Undetermined`.
- Do not silently discard ambiguous statements. Put them in an `Unresolved review notes` section when they cannot be mapped safely.

## Category handling

Normalize explicit or unambiguous review language to these categories:

- `bug`
- `security`
- `performance`
- `readability`
- `architecture`
- `test`

Use `uncategorized` when no category is stated and the issue cannot be classified confidently from the review text. Do not force every finding into a category.

## Parsing workflow

Follow this sequence:

1. Read the complete review before extracting anything.
2. Identify reviewed files and positive observations.
3. Split the review into individual findings. Keep one finding per distinct problem, even when the source paragraph mentions multiple locations.
4. Assign stable IDs in source order: `F-001`, `F-002`, and so on.
5. Extract only explicitly supported fields.
6. Normalize file paths without changing their meaning.
7. Preserve code snippets exactly except for removing surrounding Markdown fences.
8. Detect relationships only from explicit cross-references or an unmistakably repeated root problem.
9. Record statements that cannot be safely structured under `unresolved_notes`.
10. Determine merge readiness from an explicit conclusion. If none exists, use `undetermined`.
11. Create normalized JSON that follows `references/review-schema.json`.
12. Run the renderer:

```bash
python3 scripts/render_review.py normalized-review.json review-report.html
```

13. Open or inspect the generated file and verify all required sections, filters, snippets, and counts.

## Rendering requirements

The HTML report must:

- Be responsive from mobile to wide desktop.
- Support light and dark color schemes.
- Include a manual theme toggle.
- Use semantic HTML and visible keyboard focus states.
- Use system fonts and a system monospace stack for code.
- Avoid horizontal page overflow; code blocks may scroll horizontally.
- Use severity labels consistently.
- Visually distinguish unspecified severity from known severities.
- Include filters for severity and file.
- Allow all findings to be expanded or collapsed.
- Preserve filter state while expanding or collapsing findings.
- Show “No findings match these filters” when appropriate.
- Escape review content before inserting it into HTML.
- Avoid unsafe use of `innerHTML` with untrusted review content.

## Merge-readiness mapping

Use:

- `ready` only when the review explicitly says the change is ready to merge, approved, or equivalent.
- `not_ready` only when the review explicitly says changes are required, the PR should not merge, blockers remain, or equivalent.
- `undetermined` when no explicit decision is present or the conclusion is ambiguous.

Display the source basis for the decision when available.

## Handling Markdown review formats

Recognize common patterns, but do not depend on them:

- Headings per file.
- Numbered findings.
- Bullets beginning with severity names.
- GitHub-style comments such as `path/to/file.ts:42`.
- Symbol references such as `checkout()` or `OrderService.create`.
- Fenced `before` and `after` snippets.
- Sections named “Blocking”, “Suggestions”, “Nits”, “Positive”, “What looks good”, or “Summary”.

When the input format is inconsistent, prioritize factual fidelity over visual completeness.

## Quality checklist

Before returning the artifact, verify:

- The file opens without network access.
- All source findings are represented once.
- No severity was inferred.
- Unknown fields are visibly marked.
- Counts match the rendered findings.
- Blocker list matches blocker findings.
- File counts match visible findings.
- Filters work for every severity and file.
- Expand/collapse controls work.
- Theme toggle works.
- Before/after snippets are readable.
- Relationships link to valid finding IDs.
- Positive observations are separate from findings.
- Merge readiness is explicit or `Undetermined`.
- The final answer links to `review-report.html`.

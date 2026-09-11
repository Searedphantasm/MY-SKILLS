# review-visualizer

A Codex/agent skill that converts unstructured code-review text into a standalone interactive HTML report.

## Typical use

1. Give the agent a pasted review.
2. Ask it to visualize the review.
3. The skill normalizes the review into JSON.
4. `scripts/render_review.py` creates `review-report.html`.

## Files

- `SKILL.md`: behavior, parsing, fidelity, and rendering instructions.
- `references/review-schema.json`: normalized review data contract.
- `scripts/render_review.py`: dependency-free HTML renderer.
- `examples/sample-review.txt`: example unstructured review.
- `examples/sample-report.json`: example normalized data.

## Install

Copy the `review-visualizer` directory into the skills directory used by your agent environment.

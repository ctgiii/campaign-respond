"""Merge accuracy and strategy reviews into combined feedback."""


def merge_reviews(accuracy_report: str, strategy_report: str) -> str:
    """Combine accuracy and strategy reviews into a single feedback document.

    Args:
        accuracy_report: Output from the Accuracy Verifier bot
        strategy_report: Output from the Audience Strategist bot

    Returns:
        Merged feedback markdown
    """
    return f"""# Merged Review Feedback

## Accuracy Review
{accuracy_report}

---

## Strategy Review
{strategy_report}

---

## Action Items

### Must Fix (BLOCKs from Accuracy)
{_extract_blocks(accuracy_report)}

### Should Fix (WARNs from Accuracy)
{_extract_warns(accuracy_report)}

### Framing Adjustments (from Strategy)
{_extract_framing(strategy_report)}
"""


def _extract_blocks(report: str) -> str:
    """Extract BLOCK-level items from accuracy report."""
    lines = []
    for line in report.split("\n"):
        if "BLOCK" in line.upper() and not line.strip().startswith("#"):
            lines.append(f"- {line.strip()}")
    return "\n".join(lines) if lines else "- None found"


def _extract_warns(report: str) -> str:
    """Extract WARN-level items from accuracy report."""
    lines = []
    for line in report.split("\n"):
        if "WARN" in line.upper() and not line.strip().startswith("#"):
            lines.append(f"- {line.strip()}")
    return "\n".join(lines) if lines else "- None found"


def _extract_framing(report: str) -> str:
    """Extract framing recommendations from strategy report."""
    lines = []
    in_recommendations = False
    for line in report.split("\n"):
        if "recommendation" in line.lower() or "lead with" in line.lower():
            in_recommendations = True
        if in_recommendations and line.strip().startswith("-"):
            lines.append(line)
        if line.strip() == "" and in_recommendations:
            in_recommendations = False
    return "\n".join(lines) if lines else "- See strategy report for details"

#!/usr/bin/env python3
"""Synthesize feedback corrections into learned lessons."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def synthesize():
    """Read corrections log and produce lessons summary."""
    corrections_path = BASE_DIR / "knowledge-base" / "feedback" / "corrections.jsonl"
    if not corrections_path.exists():
        print("No corrections found yet.")
        return

    # Read all corrections
    corrections = []
    with open(corrections_path) as f:
        for line in f:
            line = line.strip()
            if line:
                corrections.append(json.loads(line))

    if not corrections:
        print("No corrections found.")
        return

    # Group by category and bot
    by_category = {}
    by_bot = {}
    for c in corrections:
        cat = c.get("category", "unknown")
        bot = c.get("responsible_bot", "unknown")
        by_category.setdefault(cat, []).append(c)
        by_bot.setdefault(bot, []).append(c)

    # Generate lessons
    lessons = ["# Learned Lessons\n"]
    lessons.append(f"_Generated from {len(corrections)} corrections._\n")

    lessons.append("## By Category\n")
    for cat, items in sorted(by_category.items()):
        lessons.append(f"### {cat.title()} ({len(items)} corrections)")
        for item in items[-5:]:  # Last 5 per category
            lessons.append(f"- **Q{item.get('question_num', '?')}**: "
                         f"Changed from: \"{item.get('original', '')[:80]}...\" "
                         f"→ \"{item.get('corrected', '')[:80]}...\"")
        lessons.append("")

    lessons.append("## By Bot\n")
    for bot, items in sorted(by_bot.items()):
        lessons.append(f"### {bot.title()} ({len(items)} corrections)")
        patterns = {}
        for item in items:
            cat = item.get("category", "unknown")
            patterns[cat] = patterns.get(cat, 0) + 1
        for cat, count in sorted(patterns.items(), key=lambda x: -x[1]):
            lessons.append(f"- {cat}: {count} corrections")
        lessons.append("")

    # Save
    output = BASE_DIR / "knowledge-base" / "feedback" / "lessons.md"
    output.write_text("\n".join(lessons))
    print(f"✓ Lessons synthesized: {output}")
    print(f"  Total corrections: {len(corrections)}")
    print(f"  Categories: {', '.join(by_category.keys())}")


if __name__ == "__main__":
    synthesize()

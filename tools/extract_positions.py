#!/usr/bin/env python3
"""Extract candidate positions from source materials using Claude."""

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def extract_from_file(file_path: str):
    """Extract positions from a single source file.

    Uses Claude to identify policy positions and saves them
    as structured markdown in knowledge-base/positions/.
    """
    src = Path(file_path)
    if not src.exists():
        print(f"File not found: {src}")
        return

    text = src.read_text()
    if len(text.strip()) < 50:
        print(f"File too short to extract positions: {src.name}")
        return

    prompt = f"""Analyze this document and extract all policy positions, stances, and commitments.

DOCUMENT ({src.name}):
{text}

For each position found, output:
## [Topic Area]
- Position statement
- Key details/specifics
- Any statistics or data cited (mark as verified or unverified)

Only extract positions that are explicitly stated. Do not infer or extrapolate."""

    try:
        # Try CLI mode first
        import subprocess
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            output = result.stdout
        else:
            raise RuntimeError("CLI failed")
    except (FileNotFoundError, RuntimeError):
        # Fall back to API
        try:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            output = msg.content[0].text
        except Exception as e:
            print(f"Could not extract positions (no Claude access): {e}")
            return

    # Save extracted positions
    positions_dir = BASE_DIR / "knowledge-base" / "positions"
    positions_dir.mkdir(parents=True, exist_ok=True)

    out_file = positions_dir / f"extracted-{src.stem}.md"
    out_file.write_text(f"# Positions Extracted from {src.name}\n\n{output}")
    print(f"✓ Positions saved: {out_file.name}")


def extract_all():
    """Extract positions from all source files."""
    sources_dir = BASE_DIR / "knowledge-base" / "sources"
    if not sources_dir.exists():
        print("No sources directory found.")
        return

    for f in sorted(sources_dir.glob("*.md")):
        print(f"\nProcessing: {f.name}")
        extract_from_file(str(f))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_from_file(sys.argv[1])
    else:
        extract_all()

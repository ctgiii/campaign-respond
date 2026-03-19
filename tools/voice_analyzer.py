#!/usr/bin/env python3
"""Analyze candidate voice samples to build/update voice profile."""

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def analyze_voice():
    """Analyze all voice samples and update voice profile."""
    samples_dir = BASE_DIR / "knowledge-base" / "voice-samples"
    if not samples_dir.exists() or not list(samples_dir.glob("*")):
        print("No voice samples found. Add samples with: campaign-respond add-voice-sample <file>")
        return

    # Gather all samples
    texts = []
    for f in sorted(samples_dir.glob("*")):
        if f.is_file() and f.suffix in (".md", ".txt"):
            texts.append(f"### {f.stem}\n{f.read_text()}")

    if not texts:
        print("No readable voice samples found (.md or .txt)")
        return

    combined = "\n\n---\n\n".join(texts)

    prompt = f"""Analyze these writing/speech samples from a political candidate and create a voice profile.

SAMPLES:
{combined}

Analyze and output a JSON object with these fields:
- "tone": primary tone (e.g., "confident", "warm", "authoritative")
- "formality": level (e.g., "professional", "conversational", "casual")
- "sentence_length": pattern (e.g., "mixed", "short", "long")
- "vocabulary_level": (e.g., "accessible", "academic", "colloquial")
- "storytelling_frequency": (e.g., "frequent", "moderate", "rare")
- "local_references": boolean
- "personal_anecdotes": boolean
- "rhetorical_devices": list of devices used
- "avoid": list of things the candidate avoids
- "signature_phrases": list of repeated phrases/patterns
- "opening_style": how they typically open (e.g., "direct", "storytelling", "question")
- "closing_style": how they typically close
- "humor": frequency (e.g., "frequent", "occasional", "rare")

Output ONLY the JSON object, no other text."""

    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"Could not analyze voice (Claude not available): {e}")
        return

    # Parse JSON from output
    try:
        # Find JSON in output
        start = output.index("{")
        end = output.rindex("}") + 1
        profile = json.loads(output[start:end])
    except (ValueError, json.JSONDecodeError):
        print("Could not parse voice profile from Claude output.")
        print(f"Raw output:\n{output}")
        return

    # Add sample_texts reference
    profile["sample_texts"] = [f.name for f in samples_dir.glob("*") if f.is_file()]

    # Save
    config_dir = BASE_DIR / "config"
    config_dir.mkdir(exist_ok=True)
    profile_path = config_dir / "voice-profile.json"

    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"✓ Voice profile updated: {profile_path}")
    print(f"  Tone: {profile.get('tone')}")
    print(f"  Formality: {profile.get('formality')}")
    print(f"  Signature phrases: {', '.join(profile.get('signature_phrases', []))}")


if __name__ == "__main__":
    analyze_voice()

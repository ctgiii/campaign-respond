#!/usr/bin/env python3
"""Ingest source material into the Campaign Respond knowledge base."""

import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def ingest(file_path: str):
    """Copy a source file into the knowledge base and extract text."""
    src = Path(file_path).resolve()
    if not src.exists():
        print(f"ERROR: File not found: {src}")
        sys.exit(1)

    dest_dir = BASE_DIR / "knowledge-base" / "sources"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy original
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    print(f"✓ Source added: {src.name}")

    # Extract text for MD/TXT
    suffix = src.suffix.lower()
    if suffix in (".pdf", ".docx"):
        text_dest = dest_dir / f"{src.stem}.md"
        try:
            if suffix == ".pdf":
                from PyPDF2 import PdfReader
                reader = PdfReader(str(src))
                text = "\n\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            else:
                from docx import Document
                doc = Document(str(src))
                text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

            text_dest.write_text(f"# {src.stem}\n\n{text}")
            print(f"✓ Text extracted: {text_dest.name}")
        except ImportError as e:
            print(f"⚠ Could not extract text ({e}). Original file saved.")

    # Run position extraction
    try:
        from tools.extract_positions import extract_from_file
        extract_from_file(str(dest))
        print("✓ Positions extracted")
    except Exception:
        print("  (Position extraction available after full setup)")

    print(f"\nSource material saved to: {dest}")
    print(f"Total sources: {len(list(dest_dir.glob('*')))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest-source.py <file-path>")
        sys.exit(1)
    ingest(sys.argv[1])

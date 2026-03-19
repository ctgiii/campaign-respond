#!/usr/bin/env python3
"""Campaign Respond Pipeline Orchestrator.

Runs the 4-bot pipeline to process questionnaires:
  1. INTAKE → Parse questionnaire
  2. COMMUNICATIONS → Draft responses from positions
  3. GAP REVIEW → Pause if gaps found (human-in-the-loop)
  4. HUMANIZER → Inject candidate's voice
  5. PARALLEL REVIEW → Accuracy + Strategy (concurrent)
  6. MERGE FEEDBACK → Combine review findings
  7. REVISION → Apply fixes
  8. FINAL REVIEW → Confirm BLOCKs resolved
  9. DELIVERY → Upload to storage + notify
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from pipeline.stage import (
    Stage, load_pipeline_state, save_pipeline_state,
    run_bot, record_stage,
)
from pipeline.notify import send_notification
from pipeline.merge import merge_reviews


def load_config() -> dict:
    """Load campaign configuration."""
    config_path = BASE_DIR / "config" / "campaign.json"
    if not config_path.exists():
        print("ERROR: config/campaign.json not found. Run install.sh first.")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def load_voice_profile() -> dict:
    """Load voice profile configuration."""
    vp_path = BASE_DIR / "config" / "voice-profile.json"
    if vp_path.exists():
        with open(vp_path) as f:
            return json.load(f)
    return {}


def load_priorities() -> dict:
    """Load issue priorities."""
    pri_path = BASE_DIR / "config" / "priorities.json"
    if pri_path.exists():
        with open(pri_path) as f:
            return json.load(f)
    return {}


def gather_positions() -> str:
    """Read all position documents into a single string."""
    positions_dir = BASE_DIR / "knowledge-base" / "positions"
    texts = []
    for f in sorted(positions_dir.glob("*.md")):
        texts.append(f"## {f.stem}\n\n{f.read_text()}")
    return "\n\n---\n\n".join(texts) if texts else "(No positions loaded)"


def gather_voice_samples() -> str:
    """Read all voice samples into a single string."""
    samples_dir = BASE_DIR / "knowledge-base" / "voice-samples"
    texts = []
    for f in sorted(samples_dir.glob("*")):
        if f.is_file():
            texts.append(f"## {f.stem}\n\n{f.read_text()}")
    return "\n\n---\n\n".join(texts) if texts else "(No voice samples loaded)"


def gather_sources() -> str:
    """Read all source documents."""
    sources_dir = BASE_DIR / "knowledge-base" / "sources"
    texts = []
    for f in sorted(sources_dir.glob("*")):
        if f.is_file():
            texts.append(f"## {f.stem}\n\n{f.read_text()}")
    return "\n\n---\n\n".join(texts) if texts else "(No sources loaded)"


def get_lessons() -> str:
    """Read learned lessons if they exist."""
    lessons = BASE_DIR / "knowledge-base" / "feedback" / "lessons.md"
    if lessons.exists():
        return lessons.read_text()
    return ""


def run_pipeline(questionnaire_path: str, resume: bool = False):
    """Run the full pipeline on a questionnaire.

    Args:
        questionnaire_path: Path to the questionnaire file
        resume: If True, resume from last saved state
    """
    config = load_config()
    model = config.get("pipeline", {}).get("model", "claude-sonnet-4-6")
    mode = config.get("pipeline", {}).get("mode", "cli")
    candidate = config.get("candidate", {})
    candidate_name = candidate.get("name", "the candidate")

    # Create questionnaire working directory
    q_path = Path(questionnaire_path).resolve()
    if not q_path.exists():
        print(f"ERROR: Questionnaire file not found: {q_path}")
        sys.exit(1)

    q_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{q_path.stem}"
    q_dir = BASE_DIR / "questionnaires" / "active" / q_id
    q_dir.mkdir(parents=True, exist_ok=True)

    # Copy questionnaire to working directory
    import shutil
    shutil.copy2(q_path, q_dir / "original" + q_path.suffix)
    (q_dir / "original.txt").write_text(_extract_text(q_path))

    # Initialize or load state
    if resume:
        state = load_pipeline_state(q_dir)
        print(f"Resuming pipeline for {q_id} from stage: {state['current_stage']}")
    else:
        state = load_pipeline_state(q_dir)
        state["questionnaire_id"] = q_id
        state["source_file"] = str(q_path)
        save_pipeline_state(q_dir, state)
        print(f"Starting pipeline for: {q_path.name}")
        print(f"Questionnaire ID: {q_id}")
        print(f"Working directory: {q_dir}")

    questionnaire_text = (q_dir / "original.txt").read_text()
    positions = gather_positions()
    voice_samples = gather_voice_samples()
    sources = gather_sources()
    lessons = get_lessons()
    priorities = json.dumps(load_priorities(), indent=2)
    voice_profile = json.dumps(load_voice_profile(), indent=2)

    # ── Stage 1: INTAKE ──
    print("\n━━━ Stage 1: INTAKE ━━━")
    record_stage(state, Stage.INTAKE, "running")
    save_pipeline_state(q_dir, state)

    # Parse and structure the questionnaire
    intake_prompt = f"""Parse this questionnaire and extract each question with its metadata.

QUESTIONNAIRE:
{questionnaire_text}

Output a structured list:
- Organization name (if stated)
- Questionnaire title (if stated)
- Word/character limits (if stated)
- Each question numbered, with the full question text

Format as clean markdown."""

    t0 = time.time()
    parsed = run_bot("communications", intake_prompt, model, mode)
    (q_dir / "parsed-questionnaire.md").write_text(parsed)
    record_stage(state, Stage.INTAKE, "complete", time.time() - t0)
    save_pipeline_state(q_dir, state)
    print(f"  ✓ Parsed questionnaire ({time.time()-t0:.1f}s)")

    # ── Stage 2: COMMUNICATIONS BOT ──
    print("\n━━━ Stage 2: COMMUNICATIONS DRAFT ━━━")
    record_stage(state, Stage.COMMUNICATIONS, "running")
    save_pipeline_state(q_dir, state)

    comms_prompt = f"""You are drafting questionnaire responses for {candidate_name}.

QUESTIONNAIRE:
{parsed}

CANDIDATE POSITIONS:
{positions}

SOURCE MATERIALS:
{sources}

ISSUE PRIORITIES:
{priorities}

LEARNED LESSONS:
{lessons}

INSTRUCTIONS:
1. For each question, draft a substantive response grounded in the candidate's documented positions.
2. Cite sources inline: [Source: filename, section]
3. If NO position exists for a question, write "GAP: No documented position on [topic]" instead.
4. Respect any word/character limits.
5. Be thorough and policy-focused — voice styling comes later.

Output TWO sections:
## DRAFT RESPONSES
(numbered responses, one per question)

## GAP REPORT
(list any questions where no position was found, or write "No gaps found.")"""

    t0 = time.time()
    comms_output = run_bot("communications", comms_prompt, model, mode)

    # Split output into draft and gap report
    if "## GAP REPORT" in comms_output:
        parts = comms_output.split("## GAP REPORT")
        draft = parts[0].strip()
        gap_report = "## GAP REPORT" + parts[1].strip()
    else:
        draft = comms_output
        gap_report = "## GAP REPORT\n\nNo gaps found."

    (q_dir / "communications-draft.md").write_text(draft)
    (q_dir / "gap-report.md").write_text(gap_report)
    record_stage(state, Stage.COMMUNICATIONS, "complete", time.time() - t0)
    save_pipeline_state(q_dir, state)
    print(f"  ✓ Communications draft complete ({time.time()-t0:.1f}s)")

    # ── Stage 3: GAP REVIEW ──
    has_gaps = "GAP:" in draft or "no documented position" in gap_report.lower()
    state["gaps_found"] = has_gaps

    if has_gaps and config.get("pipeline", {}).get("require_human_gap_review", True):
        print("\n━━━ Stage 3: GAP REVIEW (Human Input Required) ━━━")
        record_stage(state, Stage.GAP_REVIEW, "paused")
        state["current_stage"] = Stage.GAP_REVIEW.value
        save_pipeline_state(q_dir, state)

        print(f"  ⚠ Gaps found in responses. See: {q_dir}/gap-report.md")
        print(f"  Fill gaps in knowledge-base/positions/ then run:")
        print(f"    campaign-respond fill-gaps {q_id}")

        send_notification(
            config,
            f"Campaign Respond: Gaps found for {q_path.name}. "
            f"Review {q_dir}/gap-report.md and fill positions."
        )
        return q_id
    else:
        record_stage(state, Stage.GAP_REVIEW, "skipped", notes="No gaps found")
        save_pipeline_state(q_dir, state)
        print("\n━━━ Stage 3: GAP REVIEW ━━━")
        print("  ✓ No gaps — proceeding")

    # Continue pipeline
    return _run_post_gap(q_dir, state, config, model, mode, candidate_name,
                         draft, positions, sources, voice_samples, voice_profile,
                         priorities, lessons)


def _run_post_gap(q_dir, state, config, model, mode, candidate_name,
                  comms_draft, positions, sources, voice_samples,
                  voice_profile, priorities, lessons):
    """Run pipeline stages after gap review."""
    q_id = state["questionnaire_id"]

    # Re-read comms draft (may have been updated after gap fill)
    comms_draft = (q_dir / "communications-draft.md").read_text()

    # ── Stage 4: HUMANIZER BOT ──
    print("\n━━━ Stage 4: HUMANIZER ━━━")
    record_stage(state, Stage.HUMANIZER, "running")
    save_pipeline_state(q_dir, state)

    humanizer_prompt = f"""You are humanizing questionnaire responses for {candidate_name}.

COMMUNICATIONS DRAFT:
{comms_draft}

VOICE PROFILE:
{voice_profile}

VOICE SAMPLES:
{voice_samples}

LEARNED LESSONS (voice/tone):
{lessons}

INSTRUCTIONS:
1. Rewrite each response to match {candidate_name}'s authentic voice.
2. Preserve ALL policy substance and source citations.
3. Add storytelling, local references, personal anecdotes where appropriate — but ONLY from source materials.
4. Do NOT fabricate any stories or claims.
5. Stay within word limits if specified.
6. Document every change you make.

Output TWO sections:
## HUMANIZED RESPONSES
(numbered responses matching the original)

## CHANGELOG
(for each change: original text → new text, reason)"""

    t0 = time.time()
    humanizer_output = run_bot("humanizer", humanizer_prompt, model, mode)

    if "## CHANGELOG" in humanizer_output:
        parts = humanizer_output.split("## CHANGELOG")
        humanized = parts[0].strip()
        changelog = "## CHANGELOG" + parts[1].strip()
    else:
        humanized = humanizer_output
        changelog = "## CHANGELOG\n\n(No changelog produced)"

    (q_dir / "humanized-draft.md").write_text(humanized)
    (q_dir / "humanizer-changelog.md").write_text(changelog)
    record_stage(state, Stage.HUMANIZER, "complete", time.time() - t0)
    save_pipeline_state(q_dir, state)
    print(f"  ✓ Humanized draft complete ({time.time()-t0:.1f}s)")

    # ── Stage 5: PARALLEL REVIEW ──
    print("\n━━━ Stage 5: PARALLEL REVIEW (Accuracy + Strategy) ━━━")
    record_stage(state, Stage.ACCURACY_REVIEW, "running")
    record_stage(state, Stage.STRATEGY_REVIEW, "running")
    save_pipeline_state(q_dir, state)

    # Read parsed questionnaire for org metadata
    parsed = (q_dir / "parsed-questionnaire.md").read_text()

    accuracy_prompt = f"""You are verifying the accuracy of questionnaire responses for {candidate_name}.

HUMANIZED DRAFT (to verify):
{humanized}

ORIGINAL COMMUNICATIONS DRAFT (for comparison):
{comms_draft}

CANDIDATE POSITIONS:
{positions}

SOURCE MATERIALS:
{sources}

LEARNED LESSONS (accuracy):
{lessons}

INSTRUCTIONS:
1. Trace every cited claim back to source material.
2. Check for fabricated claims, statistics, or anecdotes.
3. Check for internal consistency between responses.
4. Assign severity: BLOCK (must fix), WARN (should fix), NOTE (informational).
5. Any fabrication is automatically a BLOCK.

Output as:
## ACCURACY REPORT

### Overall: PASS / FAIL (if any BLOCKs)

### Question N: [summary]
**Status**: PASS | BLOCK | WARN
(findings with severity, claim, source, issue, recommendation)"""

    strategy_prompt = f"""You are providing strategic framing advice for questionnaire responses for {candidate_name}.

HUMANIZED DRAFT:
{humanized}

QUESTIONNAIRE METADATA:
{parsed}

CANDIDATE PRIORITIES:
{priorities}

LEARNED LESSONS (framing):
{lessons}

INSTRUCTIONS:
1. Identify the requesting organization from the questionnaire.
2. Analyze what issues matter most to their audience.
3. For each response, recommend framing adjustments (emphasis, word choice, lead issues).
4. Flag friction points where the candidate's position may conflict with the audience.
5. Do NOT recommend changing positions — only framing.

Output as:
## STRATEGY REPORT

### Organization Profile
(name, type, audience, key issues, political lean if determinable)

### Per-Question Recommendations
#### Question N: [summary]
- Lead with: ...
- Emphasize: ...
- De-emphasize: ...
- Word choice: ...
- Friction alert: ... (if applicable)"""

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as executor:
        accuracy_future = executor.submit(
            run_bot, "accuracy", accuracy_prompt, model, mode
        )
        strategy_future = executor.submit(
            run_bot, "strategist", strategy_prompt, model, mode
        )

        accuracy_report = accuracy_future.result()
        strategy_report = strategy_future.result()

    (q_dir / "accuracy-report.md").write_text(accuracy_report)
    (q_dir / "strategy-report.md").write_text(strategy_report)

    elapsed = time.time() - t0
    record_stage(state, Stage.ACCURACY_REVIEW, "complete", elapsed)
    record_stage(state, Stage.STRATEGY_REVIEW, "complete", elapsed)
    save_pipeline_state(q_dir, state)
    print(f"  ✓ Accuracy review complete")
    print(f"  ✓ Strategy review complete ({elapsed:.1f}s parallel)")

    # ── Stage 6: MERGE FEEDBACK ──
    print("\n━━━ Stage 6: MERGE FEEDBACK ━━━")
    record_stage(state, Stage.MERGE_FEEDBACK, "running")
    save_pipeline_state(q_dir, state)

    t0 = time.time()
    merged = merge_reviews(accuracy_report, strategy_report)
    (q_dir / "merged-feedback.md").write_text(merged)

    has_blocks = "BLOCK" in accuracy_report.upper()
    state["blocks_found"] = has_blocks
    record_stage(state, Stage.MERGE_FEEDBACK, "complete", time.time() - t0,
                 notes=f"BLOCKs found: {has_blocks}")
    save_pipeline_state(q_dir, state)
    print(f"  ✓ Feedback merged ({time.time()-t0:.1f}s)")
    if has_blocks:
        print("  ⚠ BLOCK-level issues found — revision required")

    # ── Stage 7: REVISION ──
    print("\n━━━ Stage 7: REVISION ━━━")
    record_stage(state, Stage.REVISION, "running")
    state["revision_round"] = state.get("revision_round", 0) + 1
    save_pipeline_state(q_dir, state)

    revision_prompt = f"""You are revising questionnaire responses for {candidate_name} based on review feedback.

CURRENT DRAFT:
{humanized}

ACCURACY REPORT:
{accuracy_report}

STRATEGY REPORT:
{strategy_report}

CANDIDATE POSITIONS:
{positions}

VOICE PROFILE:
{voice_profile}

INSTRUCTIONS:
1. Fix ALL BLOCK-level accuracy issues. These are mandatory.
2. Address WARN-level issues where possible.
3. Apply strategy recommendations for framing — but do NOT change positions.
4. Maintain the candidate's voice from the humanized draft.
5. Keep citations intact and add new ones where needed.

Output the REVISED RESPONSES (numbered, matching the original questionnaire).
Mark any changes with [REVISED] at the end of the affected response."""

    t0 = time.time()
    revised = run_bot("communications", revision_prompt, model, mode)
    (q_dir / "revised-draft.md").write_text(revised)
    record_stage(state, Stage.REVISION, "complete", time.time() - t0,
                 notes=f"Round {state['revision_round']}")
    save_pipeline_state(q_dir, state)
    print(f"  ✓ Revision complete, round {state['revision_round']} ({time.time()-t0:.1f}s)")

    # ── Stage 8: FINAL REVIEW ──
    if has_blocks:
        print("\n━━━ Stage 8: FINAL REVIEW ━━━")
        record_stage(state, Stage.FINAL_REVIEW, "running")
        save_pipeline_state(q_dir, state)

        final_review_prompt = f"""You are performing a FINAL accuracy check on revised questionnaire responses for {candidate_name}.

REVISED DRAFT:
{revised}

PREVIOUS ACCURACY REPORT (with BLOCKs):
{accuracy_report}

CANDIDATE POSITIONS:
{positions}

SOURCE MATERIALS:
{sources}

INSTRUCTIONS:
1. Verify that ALL previous BLOCK-level issues have been resolved.
2. Check that revisions haven't introduced new issues.
3. For each previous BLOCK, confirm: RESOLVED or STILL OPEN.

Output:
## FINAL REVIEW

### Previous BLOCKs Resolution
(for each: status, original issue, what was done)

### New Issues (if any)

### Overall: PASS / FAIL"""

        t0 = time.time()
        final_review = run_bot("accuracy", final_review_prompt, model, mode)
        (q_dir / "final-review.md").write_text(final_review)

        still_blocked = "STILL OPEN" in final_review or "FAIL" in final_review.split("###")[0] if "###" in final_review else "FAIL" in final_review
        record_stage(state, Stage.FINAL_REVIEW, "complete", time.time() - t0,
                     notes=f"Still blocked: {still_blocked}")
        save_pipeline_state(q_dir, state)

        if still_blocked:
            max_rounds = config.get("pipeline", {}).get("max_revision_rounds", 2)
            if state["revision_round"] < max_rounds:
                print(f"  ⚠ Unresolved BLOCKs — running revision round {state['revision_round']+1}")
                humanized = revised  # Use revised as input for next round
                return _run_post_gap(q_dir, state, config, model, mode,
                                     candidate_name, comms_draft, positions,
                                     sources, voice_samples, voice_profile,
                                     priorities, lessons)
            else:
                print(f"  ⚠ Max revision rounds ({max_rounds}) reached with unresolved BLOCKs")
                print(f"  Manual review required: {q_dir}")
        else:
            print(f"  ✓ Final review passed ({time.time()-t0:.1f}s)")
    else:
        record_stage(state, Stage.FINAL_REVIEW, "skipped", notes="No BLOCKs to verify")
        save_pipeline_state(q_dir, state)
        print("\n━━━ Stage 8: FINAL REVIEW ━━━")
        print("  ✓ No BLOCKs — skipping final review")

    # ── Stage 9: DELIVERY ──
    print("\n━━━ Stage 9: DELIVERY ━━━")
    record_stage(state, Stage.DELIVERY, "running")
    save_pipeline_state(q_dir, state)

    # Prepare final output
    final_draft = revised if (q_dir / "revised-draft.md").exists() else humanized
    (q_dir / "final-responses.md").write_text(final_draft)

    t0 = time.time()

    # Upload to storage
    try:
        from storage.adapter import get_storage_adapter
        storage = get_storage_adapter()
        if storage:
            url = storage.upload(
                str(q_dir / "final-responses.md"),
                f"{q_id}/final-responses.md"
            )
            print(f"  ✓ Uploaded to storage: {url}")
    except Exception as e:
        print(f"  ⚠ Storage upload failed: {e}")
        print(f"  Final responses saved locally: {q_dir}/final-responses.md")

    # Move to completed
    completed_dir = BASE_DIR / "questionnaires" / "completed" / q_id
    import shutil
    shutil.copytree(q_dir, completed_dir, dirs_exist_ok=True)

    record_stage(state, Stage.DELIVERY, "complete", time.time() - t0)
    state["current_stage"] = Stage.COMPLETE.value
    state["completed_at"] = datetime.now().isoformat()
    save_pipeline_state(completed_dir, state)
    save_pipeline_state(q_dir, state)

    # Notify
    send_notification(
        config,
        f"Campaign Respond: Responses ready for {Path(state.get('source_file', '')).name}. "
        f"ID: {q_id}"
    )

    print(f"\n{'━'*50}")
    print(f"✓ PIPELINE COMPLETE — {q_id}")
    print(f"  Final responses: {q_dir}/final-responses.md")
    print(f"  Completed copy: {completed_dir}")
    print(f"{'━'*50}")

    return q_id


def resume_pipeline(questionnaire_id: str):
    """Resume a paused pipeline (e.g., after gap fill)."""
    q_dir = BASE_DIR / "questionnaires" / "active" / questionnaire_id
    if not q_dir.exists():
        print(f"ERROR: Questionnaire not found: {questionnaire_id}")
        sys.exit(1)

    state = load_pipeline_state(q_dir)
    config = load_config()
    model = config.get("pipeline", {}).get("model", "claude-sonnet-4-6")
    mode = config.get("pipeline", {}).get("mode", "cli")
    candidate_name = config.get("candidate", {}).get("name", "the candidate")

    comms_draft = (q_dir / "communications-draft.md").read_text()
    positions = gather_positions()
    sources = gather_sources()
    voice_samples = gather_voice_samples()
    voice_profile = json.dumps(load_voice_profile(), indent=2)
    priorities = json.dumps(load_priorities(), indent=2)
    lessons = get_lessons()

    print(f"Resuming pipeline for {questionnaire_id}")
    return _run_post_gap(q_dir, state, config, model, mode, candidate_name,
                         comms_draft, positions, sources, voice_samples,
                         voice_profile, priorities, lessons)


def _extract_text(file_path: Path) -> str:
    """Extract text from PDF, DOCX, TXT, or MD files."""
    suffix = file_path.suffix.lower()

    if suffix in (".txt", ".md"):
        return file_path.read_text()

    elif suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            print("WARNING: PyPDF2 not installed. Install with: pip install PyPDF2")
            return file_path.read_text(errors="ignore")

    elif suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(file_path))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            print("WARNING: python-docx not installed. Install with: pip install python-docx")
            return file_path.read_text(errors="ignore")

    else:
        return file_path.read_text(errors="ignore")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <questionnaire-path> [--resume <id>]")
        sys.exit(1)

    if sys.argv[1] == "--resume":
        resume_pipeline(sys.argv[2])
    else:
        run_pipeline(sys.argv[1])

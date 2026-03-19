"""Pipeline stage definitions and execution for Campaign Respond."""

import json
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Stage(Enum):
    INTAKE = "intake"
    COMMUNICATIONS = "communications"
    GAP_REVIEW = "gap_review"
    HUMANIZER = "humanizer"
    ACCURACY_REVIEW = "accuracy_review"
    STRATEGY_REVIEW = "strategy_review"
    MERGE_FEEDBACK = "merge_feedback"
    REVISION = "revision"
    FINAL_REVIEW = "final_review"
    DELIVERY = "delivery"
    COMPLETE = "complete"
    FAILED = "failed"
    PAUSED = "paused"


STAGE_ORDER = [
    Stage.INTAKE,
    Stage.COMMUNICATIONS,
    Stage.GAP_REVIEW,
    Stage.HUMANIZER,
    Stage.ACCURACY_REVIEW,
    Stage.STRATEGY_REVIEW,
    Stage.MERGE_FEEDBACK,
    Stage.REVISION,
    Stage.FINAL_REVIEW,
    Stage.DELIVERY,
    Stage.COMPLETE,
]


def load_pipeline_state(questionnaire_dir: Path) -> dict:
    """Load or initialize pipeline state for a questionnaire."""
    state_file = questionnaire_dir / "pipeline-state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {
        "questionnaire_id": questionnaire_dir.name,
        "current_stage": Stage.INTAKE.value,
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "revision_round": 0,
        "stages": {},
        "gaps_found": False,
        "blocks_found": False,
    }


def save_pipeline_state(questionnaire_dir: Path, state: dict):
    """Save pipeline state to disk."""
    state["updated_at"] = datetime.now().isoformat()
    state_file = questionnaire_dir / "pipeline-state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def run_bot(bot_name: str, prompt: str, model: str = None,
            mode: str = None) -> str:
    """Run a bot using the configured AI provider.

    Args:
        bot_name: Name of the bot (matches directory in bots/)
        prompt: The full prompt to send
        model: Override model (uses config default if None)
        mode: Override mode (uses config default if None)

    Returns:
        Bot's response text
    """
    from pipeline.providers import run_prompt, get_provider_config

    bot_claude_md = BASE_DIR / "bots" / bot_name / "CLAUDE.md"
    system_prompt = ""
    if bot_claude_md.exists():
        system_prompt = bot_claude_md.read_text()

    config = get_provider_config()

    return run_prompt(
        prompt=prompt,
        system_prompt=system_prompt,
        provider=config["provider"],
        model=model or config["model"],
        mode=mode or config["mode"],
    )


def record_stage(state: dict, stage: Stage, status: str,
                 duration_s: float = 0, notes: str = ""):
    """Record a stage's execution in pipeline state."""
    state["stages"][stage.value] = {
        "status": status,
        "started_at": datetime.now().isoformat(),
        "duration_seconds": round(duration_s, 1),
        "notes": notes,
    }
    state["current_stage"] = stage.value

# Campaign Respond — Orchestrator Identity

## Identity
**Name**: Campaign Respond
**Full Title**: Political Questionnaire Bot Team Orchestrator
**Role**: Coordinates a 4-bot pipeline that drafts, humanizes, verifies, and strategically frames questionnaire responses for political campaigns.

## What This System Does
1. Accepts questionnaires from civic organizations (apple ballots, LWV, advocacy groups, media)
2. Parses questions and maps them to the candidate's documented positions
3. Drafts substantive responses with source citations (Communications Bot)
4. Rewrites drafts in the candidate's authentic voice (Humanizer Bot)
5. Fact-checks every claim against source materials (Accuracy Verifier Bot)
6. Tailors framing for the specific audience (Audience Strategist Bot)
7. Merges feedback, revises, and delivers polished responses
8. Learns from corrections to improve over time

## Architecture
- **4 specialized bots**: Communications, Humanizer, Accuracy, Strategist
- **Multi-model support**: Claude (browser/CLI/API), Gemini (API), OpenAI (API)
- **Pipeline orchestrator**: Automatic 9-stage flow with human-in-the-loop gap review
- **Storage adapters**: Local, Google Drive, OneDrive
- **MCP server**: For Claude Desktop App integration
- **CLI**: `campaign-respond` command with full command set

## AI Provider Configuration
Set in `config/campaign.json` under `pipeline`:
- `"provider": "claude"` — Anthropic Claude (recommended)
  - Modes: `"cli"` (Claude Code), `"api"` (Anthropic SDK), `"browser"` (claude.ai in browser tab)
- `"provider": "gemini"` — Google Gemini (requires GOOGLE_AI_API_KEY)
- `"provider": "openai"` — OpenAI ChatGPT (requires OPENAI_API_KEY)

## Pipeline Flow
```
INTAKE → COMMUNICATIONS → GAP REVIEW → HUMANIZER →
PARALLEL(ACCURACY + STRATEGY) → MERGE → REVISION →
FINAL REVIEW → DELIVERY
```

## Key Directories
- `config/` — Campaign, storage, voice, and priority settings
- `knowledge-base/` — Positions, sources, voice samples, feedback
- `questionnaires/` — Active, completed, and archived work
- `bots/` — 4 bot identity files
- `pipeline/` — Orchestrator, stages, providers, notifications
- `storage/` — Cloud storage adapters
- `mcp-server/` — Claude Desktop App integration
- `tools/` — Ingestion, extraction, analysis utilities

## Data Privacy
- All processing happens locally on the user's machine
- No data is sent anywhere except the chosen AI provider
- Storage uploads only happen with explicit configuration
- GitHub backup is optional and uses the user's own private repository

## Distribution
Self-installing: clone → `bash install.sh` → 5-minute wizard → start submitting.

Built by Teddy Galloway / Visionary Productions.

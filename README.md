# Campaign Respond

**Political Questionnaire Bot Team** — AI-powered questionnaire response system for political campaigns.

Candidates are overwhelmed by questionnaires from civic organizations, apple ballots, League of Women Voters, advocacy groups, and media. Campaign Respond drafts accurate, on-voice responses using the candidate's actual positions — reviewed by 4 specialized AI bots.

## Quick Start

```bash
git clone <repo-url> campaign-respond
cd campaign-respond
bash install.sh
```

The setup wizard takes about 5 minutes and walks you through everything.

## How It Works

1. **You submit a questionnaire** (PDF, DOCX, or text file)
2. **Communications Bot** drafts responses from the candidate's documented positions
3. **Humanizer Bot** rewrites them in the candidate's authentic voice
4. **Accuracy Verifier** fact-checks every claim against source materials
5. **Audience Strategist** tailors framing for the requesting organization
6. **You get polished responses** — reviewed, verified, and ready to submit

## AI Model Options

| Provider | Setup | Best For |
|----------|-------|----------|
| **Claude** (recommended) | Opens in browser — sign in free | Best quality, easiest setup |
| **Google Gemini** | API key from aistudio.google.com | Free tier, fast |
| **ChatGPT / OpenAI** | API key from platform.openai.com | Familiar interface |

Choose during `install.sh` or change later in `config/campaign.json`.

## Commands

```
campaign-respond new <file>           Submit a questionnaire
campaign-respond status               Check progress
campaign-respond add-source <file>    Add candidate materials
campaign-respond add-voice-sample <f> Add speech/writing samples
campaign-respond list                 All questionnaires
campaign-respond view <id>            View current draft
campaign-respond feedback <id>        Submit corrections
campaign-respond demo                 Try with sample data
campaign-respond help                 All commands
```

## Save to GitHub (Optional)

During setup, you can connect a private GitHub repo to back up your campaign data. Or just use local storage (default).

## Claude Desktop App

Use Campaign Respond through the Claude desktop app with natural conversation. See [docs/install-guide.md](docs/install-guide.md) for MCP setup instructions.

## Requirements

- Python 3.8+
- One of: Claude account (free), Gemini API key, or OpenAI API key

## Built By

**Teddy Galloway / Visionary Productions** — visionaryproductions.us

*Your data stays on your computer. Nothing is sent anywhere except the AI provider you choose.*

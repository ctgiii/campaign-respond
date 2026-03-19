# Campaign Respond — Install Guide

## Welcome

You now have a **Campaign Respond bot team** on your computer. This system uses AI to help your campaign draft accurate, on-voice responses to questionnaires from civic organizations, advocacy groups, and voter guides.

**Your data stays on YOUR computer.** Nothing is sent anywhere without your explicit permission.

## What This Does

Campaign Respond uses 4 specialized AI bots working together:

1. **Communications Bot** — Reads the questionnaire and drafts responses using your candidate's documented positions
2. **Humanizer Bot** — Rewrites the drafts to sound like your candidate (not generic AI)
3. **Accuracy Verifier** — Fact-checks every claim against your source materials
4. **Audience Strategist** — Tailors framing based on who's asking the questions

The bots run automatically in sequence. You submit a questionnaire, and get polished responses back.

## Getting Started

### Opening Terminal

- **macOS**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Win`, type "PowerShell", press Enter
- **Linux**: Press `Ctrl + Alt + T`

### Basic Commands

Navigate to your campaign-respond folder:

```
cd campaign-respond
```

Check that everything is working:

```
campaign-respond status
```

### Submit a Questionnaire

```
campaign-respond new ~/Documents/apple-ballot.pdf
```

Supported formats: PDF, DOCX, TXT, Markdown

### Check Progress

```
campaign-respond status
```

### Add Candidate Materials

The more material you feed in, the better the responses:

```
campaign-respond add-source ~/Documents/platform.pdf
campaign-respond add-source ~/Documents/speech-transcript.txt
campaign-respond add-voice-sample ~/Documents/op-ed.txt
```

## Core Commands

| Command | What It Does |
|---------|-------------|
| `campaign-respond new <file>` | Submit a new questionnaire |
| `campaign-respond status` | Check pipeline progress |
| `campaign-respond fill-gaps <id>` | Resume after filling position gaps |
| `campaign-respond add-source <file>` | Add candidate material |
| `campaign-respond add-voice-sample <file>` | Add writing/speech sample |
| `campaign-respond feedback <id>` | Correct delivered responses |
| `campaign-respond config` | View/update settings |
| `campaign-respond list` | All questionnaires with status |
| `campaign-respond view <id>` | View latest draft |
| `campaign-respond deliver <id>` | Upload to storage |
| `campaign-respond history` | Processing history |
| `campaign-respond demo` | Run demo with sample data |
| `campaign-respond help` | Full command reference |

## Using with Claude Desktop App

Instead of (or alongside) the terminal, you can use Campaign Respond through the Claude desktop app with a conversational interface.

### Setup

1. Download the Claude desktop app from [claude.ai/download](https://claude.ai/download)
2. Open Claude → **Settings** → **Developer** → **Edit Config**
3. Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "campaign-respond": {
      "command": "python3",
      "args": ["/path/to/campaign-respond/mcp-server/campaign-respond-server.py"],
      "env": {
        "CAMPAIGN_RESPOND_DIR": "/path/to/campaign-respond"
      }
    }
  }
}
```

Replace `/path/to/campaign-respond` with your actual install path.

4. Restart Claude desktop app

### Using It

Now you can chat naturally:

- *"Process this questionnaire for the Apple Ballot"* (drag and drop the file)
- *"Show me the status of my current questionnaires"*
- *"Add this speech transcript as source material"*
- *"Review the draft for questionnaire 20260315-apple-ballot"*
- *"The tone on question 3 is too formal, make it more conversational"*

## AI Model Options

Campaign Respond supports multiple AI providers:

- **Claude** (recommended) — Works via browser (free), CLI, or API
- **Google Gemini** — Requires API key from aistudio.google.com
- **ChatGPT/OpenAI** — Requires API key from platform.openai.com

To change your AI provider, edit `config/campaign.json` and update the `pipeline.provider` field.

## Storage Setup

By default, responses are saved locally. To set up cloud storage:

### Google Drive
1. Set `"provider": "google_drive"` in `config/storage.json`
2. On first upload, a browser window will open for Google sign-in
3. Authorize the Campaign Respond app
4. Responses will upload to a "Campaign Respond" folder in your Drive

### OneDrive
1. Set `"provider": "onedrive"` in `config/storage.json`
2. Set `ONEDRIVE_CLIENT_ID` and `ONEDRIVE_CLIENT_SECRET` in `.env`
3. Follow the device code flow on first use

## Adding Source Material

Feed in as much as you can — the AI uses this to draft accurate responses:

- **Policy platform** (PDF or text)
- **Past questionnaire responses** (for consistency)
- **Speech transcripts** (for voice matching)
- **Op-eds and articles** (written by the candidate)
- **Interview transcripts**
- **Campaign website content**
- **Legislative record** (bills sponsored, votes, etc.)

## GitHub Backup (Optional)

If you chose GitHub during setup, your data is automatically backed up:

```
git add -A && git commit -m "Update" && git push
```

To set up GitHub later:
1. Create a **private** repo at github.com/new
2. Run: `git init && git remote add origin <your-repo-url>`
3. Run: `git add -A && git commit -m "Initial setup" && git push -u origin main`

## Troubleshooting

### "Command not found: campaign-respond"
Add the bin directory to your PATH:
```
export PATH="/path/to/campaign-respond/bin:$PATH"
```

### "config/campaign.json not found"
Run the install wizard: `bash install.sh`

### Pipeline stuck on "gap_review"
The system found questions where your candidate has no documented position. Add position documents and run: `campaign-respond fill-gaps <id>`

### AI model errors
- **Claude CLI**: Make sure `claude` is installed: `npm install -g @anthropic-ai/claude-code`
- **Gemini**: Check your API key in `.env`
- **OpenAI**: Check your API key and billing at platform.openai.com

### Storage upload fails
Check your storage config in `config/storage.json` and credentials in `storage/credentials/`.

## Support

Questions or issues? Contact:
- **Teddy Galloway** — Visionary Productions
- Email the address provided during setup
- Text the number provided during setup

---

*Built by Visionary Productions — visionaryproductions.us*

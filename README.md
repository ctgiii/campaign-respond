# Campaign Respond

**Political Questionnaire Bot Team** — AI-powered questionnaire response system for political campaigns.

Candidates are overwhelmed by questionnaires from civic organizations, apple ballots, League of Women Voters, advocacy groups, and media. Campaign Respond drafts accurate, on-voice responses using the candidate's actual positions — reviewed by 4 specialized AI bots.

Your data stays on YOUR computer. Nothing is sent anywhere except the AI provider you choose.

---

## Choose Your Setup

### Option A: Claude Desktop App (Recommended — No Terminal Required)

If you have the **Claude app** on your Mac or Windows PC, you can use Campaign Respond through a simple chat interface — no terminal skills needed.

1. **Download Campaign Respond**: [Download ZIP](https://github.com/ctgiii/campaign-respond/archive/refs/heads/main.zip) and unzip it somewhere you'll remember (like your Documents folder)

2. **Install Python** (needed once):
   - **Mac**: Open Terminal (`Cmd + Space` → type "Terminal") and paste: `brew install python3` (or download from [python.org](https://python.org))
   - **Windows**: Download from [python.org](https://python.org) — **check "Add to PATH"** during install

3. **Run the setup wizard** (one time only):
   - **Mac**: Open Terminal and paste:
     ```
     cd ~/Documents/campaign-respond-main && bash install.sh
     ```
   - **Windows**: Open **PowerShell** and paste:
     ```
     cd ~\Documents\campaign-respond-main; bash install.sh
     ```
     *(If `bash` isn't recognized, install [Git for Windows](https://git-scm.com) first — it includes bash)*

4. **Connect to Claude Desktop App**:
   - Open the Claude app → **Settings** → **Developer** → **Edit Config**
   - Paste this (fix the path to where you unzipped):
     ```json
     {
       "mcpServers": {
         "campaign-respond": {
           "command": "python3",
           "args": ["/path/to/campaign-respond/mcp-server/campaign-respond-server.py"]
         }
       }
     }
     ```
   - Restart the Claude app

5. **Start chatting**:
   - *"Process this questionnaire for the Apple Ballot"* (drag and drop the file)
   - *"Add this speech as source material"*
   - *"Show me the status of my questionnaires"*
   - *"The tone on question 3 is too formal"*

---

### Option B: Terminal Install (Mac)

Open **Terminal** (`Cmd + Space` → type "Terminal") and paste:

```bash
git clone https://github.com/ctgiii/campaign-respond.git
cd campaign-respond
bash install.sh
```

Then submit questionnaires with:
```bash
campaign-respond new ~/Documents/apple-ballot.pdf
```

---

### Option C: Terminal Install (Windows)

**Step 1 — Install prerequisites:**
- Download and install [Git for Windows](https://git-scm.com) (includes Git Bash)
- Download and install [Python](https://python.org) — **check "Add to PATH"**

**Step 2 — Open Git Bash** (search "Git Bash" in Start menu) and paste:

```bash
git clone https://github.com/ctgiii/campaign-respond.git
cd campaign-respond
bash install.sh
```

Then submit questionnaires with:
```bash
campaign-respond new ~/Documents/apple-ballot.pdf
```

> **Alternative**: If you prefer a full Linux environment, open PowerShell as Administrator and run `wsl --install`, restart, open Ubuntu, then run:
> ```
> sudo apt update && sudo apt install python3 python3-pip git -y
> git clone https://github.com/ctgiii/campaign-respond.git
> cd campaign-respond && bash install.sh
> ```

---

### Option D: Phone / Tablet

Campaign Respond requires a computer for the initial setup and processing. However, once installed:

- **Claude mobile app**: Open the Claude app on your phone and ask about your questionnaires by name — the processing happens on your computer, and you can review drafts from anywhere
- **Google Drive / OneDrive**: During setup, choose cloud storage and completed responses will automatically sync to your phone
- **Remote access**: If your computer stays on, you can trigger processing from your phone using the Claude mobile app connected to your desktop's MCP server

*Full phone-only support is coming in a future update.*

---

## How It Works

1. **You submit a questionnaire** (PDF, DOCX, or text file)
2. **Communications Bot** drafts responses from the candidate's documented positions
3. **Humanizer Bot** rewrites them in the candidate's authentic voice
4. **Accuracy Verifier** fact-checks every claim against source materials
5. **Audience Strategist** tailors framing for the requesting organization
6. **You get polished responses** — reviewed, verified, and ready to submit

## AI Model Options

The setup wizard lets you choose your AI provider:

| Provider | Setup | Cost |
|----------|-------|------|
| **Claude** (recommended) | Sign in free at claude.ai | Free tier available |
| **Google Gemini** | API key from aistudio.google.com | Free tier: 60 req/min |
| **ChatGPT / OpenAI** | API key from platform.openai.com | Pay-as-you-go |

You can change providers anytime by editing `config/campaign.json`.

## Commands (Terminal Users)

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

During setup, you can connect a private GitHub repo to back up your campaign data. The wizard walks you through creating one. Or just use local storage — that's the default.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: campaign-respond` | Add to PATH: `export PATH="/path/to/campaign-respond/bin:$PATH"` |
| `command not found: bash` (Windows) | Install [Git for Windows](https://git-scm.com) |
| `command not found: python3` (Windows) | Install from [python.org](https://python.org) — check "Add to PATH" |
| Pipeline stuck on "gap_review" | Add position docs, then run `campaign-respond fill-gaps <id>` |
| `config/campaign.json not found` | Run the setup wizard: `bash install.sh` |

## Built By

**Teddy Galloway / Visionary Productions** — visionaryproductions.us

Questions? Text or email the contact provided during your setup.

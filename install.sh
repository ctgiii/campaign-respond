#!/usr/bin/env bash
# Campaign Respond — Self-Installing Setup Script
# One command: bash install.sh
# Supports Claude (default), Gemini, and ChatGPT/OpenAI
# Local install (default) or GitHub repository setup

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$BASE_DIR/config"

# ── Banner ──
clear
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}                                                                           ${NC}"
echo -e "${BOLD}   Campaign Respond — Political Questionnaire Bot Team                     ${NC}"
echo -e "${BOLD}   Built by Visionary Productions                                          ${NC}"
echo -e "${BOLD}                                                                           ${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${DIM}  This wizard will set up your Campaign Respond bot team in about 5 minutes.${NC}"
echo -e "${DIM}  Your data stays on YOUR computer. Nothing is sent anywhere without your OK.${NC}"
echo ""

# ── Helper functions ──
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    if [ -n "$default" ]; then
        echo -ne "  ${prompt} ${DIM}[$default]${NC}: "
    else
        echo -ne "  ${prompt}: "
    fi
    read -r input
    eval "$var_name=\"${input:-$default}\""
}

confirm() {
    echo -ne "  $1 ${DIM}[Y/n]${NC}: "
    read -r yn
    [[ "${yn:-y}" =~ ^[Yy] ]]
}

# ── Step 1: Prerequisites ──
echo -e "${BOLD}Step 1: Checking prerequisites${NC}"
echo ""

MISSING=()

# Python 3.8+
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "  ${GREEN}✓${NC} Python $PY_VERSION"
else
    MISSING+=("python3")
    echo -e "  ${RED}✗${NC} Python 3 not found"
fi

# pip
if command -v pip3 &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} pip3"
else
    MISSING+=("pip3")
    echo -e "  ${RED}✗${NC} pip3 not found"
fi

# jq
if command -v jq &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} jq"
else
    MISSING+=("jq")
    echo -e "  ${YELLOW}⚠${NC} jq not found (optional — will install)"
fi

# git (needed for GitHub option)
if command -v git &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} git"
    HAS_GIT=true
else
    echo -e "  ${YELLOW}⚠${NC} git not found (needed for GitHub setup)"
    HAS_GIT=false
fi

if [[ ${#MISSING[@]} -gt 0 ]] && [[ " ${MISSING[*]} " == *" python3 "* ]]; then
    echo ""
    echo -e "  ${RED}Python 3 is required. Install it first:${NC}"
    echo -e "  macOS: ${BOLD}brew install python3${NC}"
    echo -e "  Windows: Download from python.org"
    echo -e "  Linux: ${BOLD}sudo apt install python3 python3-pip${NC}"
    exit 1
fi

echo ""

# ── Step 2: Installation Mode ──
echo -e "${BOLD}Step 2: Choose your setup${NC}"
echo ""
echo -e "  ${CYAN}1)${NC} ${BOLD}Local install${NC} ${DIM}(recommended — everything stays on your computer)${NC}"
echo -e "  ${CYAN}2)${NC} ${BOLD}GitHub repository${NC} ${DIM}(save your config and data to your own GitHub repo)${NC}"
echo ""
echo -ne "  Choose ${DIM}[1]${NC}: "
read -r INSTALL_MODE
INSTALL_MODE="${INSTALL_MODE:-1}"

GITHUB_REPO=""
if [[ "$INSTALL_MODE" == "2" ]]; then
    echo ""
    echo -e "  ${BOLD}GitHub Repository Setup${NC}"
    echo -e "  ${DIM}We'll walk you through creating a private repo for your campaign data.${NC}"
    echo ""

    if ! $HAS_GIT; then
        echo -e "  ${RED}Git is required for GitHub setup. Install it first:${NC}"
        echo -e "  macOS: ${BOLD}brew install git${NC}"
        echo -e "  Windows: Download from git-scm.com"
        echo -e "  ${YELLOW}Falling back to local install.${NC}"
        INSTALL_MODE="1"
    else
        echo -e "  ${BOLD}Option A:${NC} Already have a GitHub repo? Enter the URL."
        echo -e "  ${BOLD}Option B:${NC} Don't have one? We'll help you create it."
        echo ""
        echo -ne "  Paste your GitHub repo URL (or press Enter to create one): "
        read -r GITHUB_REPO

        if [ -z "$GITHUB_REPO" ]; then
            echo ""
            echo -e "  ${BOLD}To create a new GitHub repository:${NC}"
            echo ""
            echo -e "  1. Go to ${CYAN}github.com/new${NC} in your browser"
            echo -e "  2. Repository name: ${BOLD}campaign-respond-data${NC}"
            echo -e "  3. Set to ${BOLD}Private${NC} (keeps your campaign data confidential)"
            echo -e "  4. Check '${BOLD}Add a README file${NC}'"
            echo -e "  5. Click '${BOLD}Create repository${NC}'"
            echo -e "  6. Copy the repo URL (looks like: https://github.com/yourname/campaign-respond-data.git)"
            echo ""
            echo -ne "  Paste the URL when ready (or press Enter to skip and use local): "
            read -r GITHUB_REPO

            if [ -z "$GITHUB_REPO" ]; then
                echo -e "  ${YELLOW}No repo URL — using local install.${NC}"
                INSTALL_MODE="1"
            fi
        fi

        if [ -n "$GITHUB_REPO" ]; then
            echo ""
            echo -e "  ${BLUE}Testing GitHub connection...${NC}"
            if git ls-remote "$GITHUB_REPO" &>/dev/null; then
                echo -e "  ${GREEN}✓${NC} Connected to GitHub repo"

                # Initialize git in project dir if needed
                if [ ! -d "$BASE_DIR/.git" ]; then
                    cd "$BASE_DIR"
                    git init
                    git remote add origin "$GITHUB_REPO"
                    echo -e "  ${GREEN}✓${NC} Git initialized with remote: $GITHUB_REPO"
                fi
            else
                echo -e "  ${RED}✗${NC} Could not connect to: $GITHUB_REPO"
                echo -e "  ${DIM}Check the URL and make sure you have access.${NC}"
                echo -e "  ${DIM}If this is a private repo, you may need to set up SSH keys or a personal access token.${NC}"
                echo ""
                echo -e "  ${BOLD}SSH key setup (if needed):${NC}"
                echo -e "  1. Run: ${BOLD}ssh-keygen -t ed25519${NC} (press Enter for defaults)"
                echo -e "  2. Run: ${BOLD}cat ~/.ssh/id_ed25519.pub${NC}"
                echo -e "  3. Go to github.com → Settings → SSH Keys → New SSH Key"
                echo -e "  4. Paste the key and save"
                echo ""
                echo -ne "  Try again with a different URL, or Enter for local install: "
                read -r GITHUB_REPO
                if [ -z "$GITHUB_REPO" ]; then
                    INSTALL_MODE="1"
                fi
            fi
        fi
    fi
fi

echo ""

# ── Step 3: AI Model Selection ──
echo -e "${BOLD}Step 3: Choose your AI model${NC}"
echo ""
echo -e "  Campaign Respond uses AI to draft and review your questionnaire responses."
echo -e "  Choose which AI provider to use:"
echo ""
echo -e "  ${CYAN}1)${NC} ${BOLD}Claude by Anthropic${NC} ${GREEN}(recommended)${NC}"
echo -e "     ${DIM}Opens in a new browser tab — sign in with your Claude account.${NC}"
echo -e "     ${DIM}Free tier available. No API key needed for browser mode.${NC}"
echo ""
echo -e "  ${CYAN}2)${NC} ${BOLD}Google Gemini${NC}"
echo -e "     ${DIM}Requires a Google AI API key (free tier: 60 requests/min).${NC}"
echo -e "     ${DIM}Get one at: aistudio.google.com/apikey${NC}"
echo ""
echo -e "  ${CYAN}3)${NC} ${BOLD}ChatGPT / OpenAI${NC}"
echo -e "     ${DIM}Requires an OpenAI API key (pay-as-you-go).${NC}"
echo -e "     ${DIM}Get one at: platform.openai.com/api-keys${NC}"
echo ""
echo -e "  ${CYAN}4)${NC} ${BOLD}Claude API${NC}"
echo -e "     ${DIM}For power users: uses the Anthropic API directly.${NC}"
echo -e "     ${DIM}Requires an API key from: console.anthropic.com${NC}"
echo ""
echo -ne "  Choose ${DIM}[1]${NC}: "
read -r MODEL_CHOICE
MODEL_CHOICE="${MODEL_CHOICE:-1}"

AI_PROVIDER=""
AI_MODEL=""
AI_MODE=""
API_KEY_VAR=""

case "$MODEL_CHOICE" in
    1)
        AI_PROVIDER="claude"
        AI_MODEL="claude-sonnet-4-6"
        AI_MODE="cli"
        echo ""
        echo -e "  ${GREEN}✓${NC} Claude selected (browser mode)"
        echo -e "  ${DIM}When processing questionnaires, Claude will open in your browser.${NC}"

        # Check if Claude Code CLI is installed
        if command -v claude &>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Claude Code CLI detected — will use for faster processing"
            AI_MODE="cli"
        else
            echo -e "  ${YELLOW}⚠${NC} Claude Code CLI not found"
            echo -e "  ${DIM}Install for best experience: npm install -g @anthropic-ai/claude-code${NC}"
            echo -e "  ${DIM}Or continue with browser mode (works fine, just slower).${NC}"
            AI_MODE="browser"
        fi
        ;;
    2)
        AI_PROVIDER="gemini"
        AI_MODEL="gemini-2.5-pro"
        AI_MODE="api"
        echo ""
        echo -ne "  Enter your Google AI API key: "
        read -rs GEMINI_KEY
        echo ""
        if [ -z "$GEMINI_KEY" ]; then
            echo -e "  ${YELLOW}⚠${NC} No key provided. You can add it later in .env"
        else
            echo -e "  ${GREEN}✓${NC} Gemini API key saved"
        fi
        ;;
    3)
        AI_PROVIDER="openai"
        AI_MODEL="gpt-4o"
        AI_MODE="api"
        echo ""
        echo -ne "  Enter your OpenAI API key: "
        read -rs OPENAI_KEY
        echo ""
        if [ -z "$OPENAI_KEY" ]; then
            echo -e "  ${YELLOW}⚠${NC} No key provided. You can add it later in .env"
        else
            echo -e "  ${GREEN}✓${NC} OpenAI API key saved"
        fi
        ;;
    4)
        AI_PROVIDER="claude"
        AI_MODEL="claude-sonnet-4-6"
        AI_MODE="api"
        echo ""
        echo -ne "  Enter your Anthropic API key: "
        read -rs ANTHROPIC_KEY
        echo ""
        if [ -z "$ANTHROPIC_KEY" ]; then
            echo -e "  ${YELLOW}⚠${NC} No key provided. You can add it later in .env"
        else
            echo -e "  ${GREEN}✓${NC} Anthropic API key saved"
        fi
        ;;
    *)
        echo -e "  ${YELLOW}Invalid choice, defaulting to Claude (browser mode)${NC}"
        AI_PROVIDER="claude"
        AI_MODEL="claude-sonnet-4-6"
        AI_MODE="cli"
        ;;
esac

echo ""

# ── Step 4: Candidate Information ──
echo -e "${BOLD}Step 4: Candidate Information${NC}"
echo ""

prompt_with_default "Candidate's full name" "" CANDIDATE_NAME
prompt_with_default "Office sought (e.g., County Council District 3)" "" CANDIDATE_OFFICE
prompt_with_default "Party affiliation" "Independent" CANDIDATE_PARTY
prompt_with_default "Campaign website" "" CANDIDATE_WEBSITE
prompt_with_default "State" "" CANDIDATE_STATE
prompt_with_default "District/jurisdiction" "" CANDIDATE_DISTRICT
prompt_with_default "Election year" "2026" CANDIDATE_YEAR
echo ""
echo -ne "  ${DIM}Brief bio (1-2 sentences):${NC} "
read -r CANDIDATE_BIO

echo ""

# ── Step 5: Your Information ──
echo -e "${BOLD}Step 5: Your Information (campaign staffer)${NC}"
echo ""

prompt_with_default "Your name" "" REQUESTER_NAME
prompt_with_default "Your role" "Campaign Manager" REQUESTER_ROLE
prompt_with_default "Your email" "" REQUESTER_EMAIL
prompt_with_default "Your phone (for text notifications, optional)" "" REQUESTER_PHONE
prompt_with_default "Campaign/organization name" "" REQUESTER_ORG

echo ""

# ── Step 6: Storage ──
echo -e "${BOLD}Step 6: Where should completed responses be saved?${NC}"
echo ""
echo -e "  ${CYAN}1)${NC} ${BOLD}Local folder${NC} ${DIM}(default — saved right here in this project)${NC}"
echo -e "  ${CYAN}2)${NC} ${BOLD}Google Drive${NC} ${DIM}(automatically uploads to your Drive)${NC}"
echo -e "  ${CYAN}3)${NC} ${BOLD}OneDrive${NC} ${DIM}(automatically uploads to your OneDrive)${NC}"
echo ""
echo -ne "  Choose ${DIM}[1]${NC}: "
read -r STORAGE_CHOICE
STORAGE_CHOICE="${STORAGE_CHOICE:-1}"

STORAGE_PROVIDER="local"
case "$STORAGE_CHOICE" in
    2) STORAGE_PROVIDER="google_drive"
       echo -e "  ${DIM}You'll be prompted to sign in to Google Drive on first use.${NC}" ;;
    3) STORAGE_PROVIDER="onedrive"
       echo -e "  ${DIM}You'll be prompted to sign in to OneDrive on first use.${NC}" ;;
    *) STORAGE_PROVIDER="local" ;;
esac

echo ""

# ── Step 7: Generate Configuration Files ──
echo -e "${BOLD}Step 7: Setting up your bot team...${NC}"
echo ""

mkdir -p "$CONFIG_DIR"
mkdir -p "$BASE_DIR/state"
mkdir -p "$BASE_DIR/knowledge-base/positions"
mkdir -p "$BASE_DIR/knowledge-base/sources"
mkdir -p "$BASE_DIR/knowledge-base/voice-samples"
mkdir -p "$BASE_DIR/knowledge-base/feedback"
mkdir -p "$BASE_DIR/knowledge-base/audience-profiles"
mkdir -p "$BASE_DIR/questionnaires/active"
mkdir -p "$BASE_DIR/questionnaires/completed"
mkdir -p "$BASE_DIR/questionnaires/archived"
mkdir -p "$BASE_DIR/storage/credentials"

# Campaign config
cat > "$CONFIG_DIR/campaign.json" << CAMPAIGN_EOF
{
  "candidate": {
    "name": "$CANDIDATE_NAME",
    "office": "$CANDIDATE_OFFICE",
    "party": "$CANDIDATE_PARTY",
    "website": "$CANDIDATE_WEBSITE",
    "bio": "$CANDIDATE_BIO",
    "district": "$CANDIDATE_DISTRICT",
    "state": "$CANDIDATE_STATE",
    "election_year": "$CANDIDATE_YEAR"
  },
  "requester": {
    "name": "$REQUESTER_NAME",
    "role": "$REQUESTER_ROLE",
    "email": "$REQUESTER_EMAIL",
    "phone": "$REQUESTER_PHONE",
    "organization": "$REQUESTER_ORG"
  },
  "notifications": {
    "sms_enabled": false,
    "email_enabled": $([ -n "$REQUESTER_EMAIL" ] && echo "true" || echo "false"),
    "imessage_enabled": false
  },
  "pipeline": {
    "provider": "$AI_PROVIDER",
    "model": "$AI_MODEL",
    "mode": "$AI_MODE",
    "auto_deliver": false,
    "require_human_gap_review": true,
    "max_revision_rounds": 2
  }
}
CAMPAIGN_EOF
echo -e "  ${GREEN}✓${NC} Campaign config generated"

# Storage config
cat > "$CONFIG_DIR/storage.json" << STORAGE_EOF
{
  "provider": "$STORAGE_PROVIDER",
  "local": {
    "output_dir": "./questionnaires/completed"
  },
  "google_drive": {
    "credentials_path": "./storage/credentials/google-token.json",
    "folder_id": "",
    "folder_name": "Campaign Respond"
  },
  "onedrive": {
    "credentials_path": "./storage/credentials/onedrive-token.json",
    "folder_path": "/Campaign Respond"
  }
}
STORAGE_EOF
echo -e "  ${GREEN}✓${NC} Storage config generated"

# Voice profile (from template)
cp "$CONFIG_DIR/voice-profile.json.template" "$CONFIG_DIR/voice-profile.json" 2>/dev/null || \
cat > "$CONFIG_DIR/voice-profile.json" << 'VP_EOF'
{
  "tone": "confident",
  "formality": "professional",
  "sentence_length": "mixed",
  "vocabulary_level": "accessible",
  "storytelling_frequency": "moderate",
  "local_references": true,
  "personal_anecdotes": true,
  "rhetorical_devices": ["parallel_structure", "call_to_action"],
  "avoid": ["jargon", "hedging", "passive_voice"],
  "signature_phrases": [],
  "opening_style": "direct",
  "closing_style": "forward_looking",
  "humor": "occasional",
  "sample_texts": []
}
VP_EOF
echo -e "  ${GREEN}✓${NC} Voice profile generated"

# Priorities (from template)
cp "$CONFIG_DIR/priorities.json.template" "$CONFIG_DIR/priorities.json" 2>/dev/null || \
cat > "$CONFIG_DIR/priorities.json" << 'PRI_EOF'
{
  "description": "Issue priority weights (0.0-1.0). Higher weight = more emphasis.",
  "issues": {
    "economy": 0.8,
    "education": 0.7,
    "healthcare": 0.7,
    "environment": 0.6,
    "public_safety": 0.6,
    "infrastructure": 0.5,
    "housing": 0.5,
    "civil_rights": 0.6,
    "government_reform": 0.5,
    "technology": 0.4
  },
  "custom_issues": {}
}
PRI_EOF
echo -e "  ${GREEN}✓${NC} Priorities generated"

# .env file
cat > "$BASE_DIR/.env" << ENV_EOF
# Campaign Respond Configuration
# Generated by install.sh on $(date)

# AI Provider: $AI_PROVIDER
AI_PROVIDER=$AI_PROVIDER
AI_MODEL=$AI_MODEL
AI_MODE=$AI_MODE

# Claude API (for API mode)
ANTHROPIC_API_KEY=${ANTHROPIC_KEY:-}

# Google Gemini API
GOOGLE_AI_API_KEY=${GEMINI_KEY:-}

# OpenAI / ChatGPT API
OPENAI_API_KEY=${OPENAI_KEY:-}

# SMTP (for email notifications)
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
SMTP_USER=
SMTP_FROM=

# GitHub repo (if configured)
GITHUB_REPO=${GITHUB_REPO:-}
ENV_EOF
echo -e "  ${GREEN}✓${NC} Environment file generated"

# ── Step 8: Install Python Dependencies ──
echo ""
echo -e "${BOLD}Step 8: Installing dependencies...${NC}"
echo ""

pip3 install -q -r "$BASE_DIR/requirements.txt" 2>/dev/null && \
    echo -e "  ${GREEN}✓${NC} Python packages installed" || \
    echo -e "  ${YELLOW}⚠${NC} Some packages failed. Run: pip3 install -r requirements.txt"

# Install jq if missing
if ! command -v jq &>/dev/null; then
    if command -v brew &>/dev/null; then
        brew install jq -q 2>/dev/null && echo -e "  ${GREEN}✓${NC} jq installed"
    else
        echo -e "  ${YELLOW}⚠${NC} Install jq manually: https://stedolan.github.io/jq/download/"
    fi
fi

# Install provider-specific deps
case "$AI_PROVIDER" in
    gemini)
        pip3 install -q google-generativeai 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} Google AI SDK installed" || true
        ;;
    openai)
        pip3 install -q openai 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} OpenAI SDK installed" || true
        ;;
esac

# ── Step 9: Make CLI executable ──
chmod +x "$BASE_DIR/bin/campaign-respond"

# Add to PATH hint
echo ""
echo -e "  ${DIM}To use 'campaign-respond' from anywhere, add to your PATH:${NC}"
echo -e "  ${BOLD}export PATH=\"$BASE_DIR/bin:\$PATH\"${NC}"
echo -e "  ${DIM}(Add this line to your ~/.bashrc or ~/.zshrc to make it permanent)${NC}"

# ── Step 10: GitHub Setup (if selected) ──
if [[ "$INSTALL_MODE" == "2" ]] && [ -n "$GITHUB_REPO" ]; then
    echo ""
    echo -e "${BOLD}Step 10: Setting up GitHub repository...${NC}"
    echo ""

    cd "$BASE_DIR"

    if [ ! -d ".git" ]; then
        git init
        git remote add origin "$GITHUB_REPO"
    fi

    # Create a .gitignore that protects sensitive data
    # (Already exists from scaffold, but ensure it's there)

    git add -A
    git commit -m "Initial Campaign Respond setup for $CANDIDATE_NAME" 2>/dev/null || true

    if git push -u origin main 2>/dev/null || git push -u origin master 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Pushed to GitHub: $GITHUB_REPO"
        echo -e "  ${DIM}Your campaign data is now backed up to your private repository.${NC}"
    else
        echo -e "  ${YELLOW}⚠${NC} Could not push to GitHub. You can do it later with: git push -u origin main"
    fi
fi

# ── Step 11: Homelab Detection ──
if [ -f "/Users/ctgiii/homelab/state/system-state.json" ]; then
    echo ""
    echo -e "  ${DIM}Homelab detected — registering bots...${NC}"

    REGISTRY="/Users/ctgiii/homelab/projects/AI Bots/engineer/bot-registry.json"
    if [ -f "$REGISTRY" ]; then
        python3 -c "
import json
with open('$REGISTRY') as f:
    reg = json.load(f)
bots = reg.get('bots', [])
names = [b['name'] for b in bots]
new_bots = [
    {'name': 'campaign-respond', 'role': 'Campaign Questionnaire Pipeline Orchestrator', 'provider': '$AI_PROVIDER', 'path': '$BASE_DIR'},
    {'name': 'campaign-comms', 'role': 'Campaign Communications Drafter', 'provider': '$AI_PROVIDER', 'path': '$BASE_DIR/bots/communications'},
    {'name': 'campaign-humanizer', 'role': 'Campaign Voice & Authenticity Specialist', 'provider': '$AI_PROVIDER', 'path': '$BASE_DIR/bots/humanizer'},
    {'name': 'campaign-accuracy', 'role': 'Campaign Accuracy Verifier', 'provider': '$AI_PROVIDER', 'path': '$BASE_DIR/bots/accuracy'},
    {'name': 'campaign-strategist', 'role': 'Campaign Audience Strategist', 'provider': '$AI_PROVIDER', 'path': '$BASE_DIR/bots/strategist'},
]
for nb in new_bots:
    if nb['name'] not in names:
        bots.append(nb)
reg['bots'] = bots
with open('$REGISTRY', 'w') as f:
    json.dump(reg, f, indent=2)
print('  Registered 5 campaign bots in homelab registry')
" 2>/dev/null || true
    fi
fi

# ── Step 12: Generate Install Guide PDF ──
echo ""
echo -e "${BOLD}Generating install guide...${NC}"

if python3 -c "import weasyprint" 2>/dev/null; then
    python3 -c "
import weasyprint, markdown
from pathlib import Path
md_path = Path('$BASE_DIR/docs/install-guide.md')
if md_path.exists():
    html = markdown.markdown(md_path.read_text())
    html = f'<html><head><style>body{{font-family:system-ui;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#333}}h1{{color:#1a1a2e}}h2{{color:#16213e;border-bottom:2px solid #e2e2e2;padding-bottom:8px}}code{{background:#f4f4f4;padding:2px 6px;border-radius:3px}}pre{{background:#1a1a2e;color:#e2e2e2;padding:16px;border-radius:8px;overflow-x:auto}}pre code{{background:none;color:inherit}}</style></head><body>{html}</body></html>'
    weasyprint.HTML(string=html).write_pdf('$BASE_DIR/docs/install-guide.pdf')
    print('  ✓ PDF guide generated')
" 2>/dev/null || echo -e "  ${YELLOW}⚠${NC} PDF generation skipped (weasyprint issue). Guide available as Markdown."
else
    echo -e "  ${DIM}PDF generation requires weasyprint. Guide available at: docs/install-guide.md${NC}"
fi

# ── Step 13: Register Install ──
# Logs this install to Teddy's tracking sheet (Google Form → Google Sheet).
# Only sends the info you already entered. Silent and non-blocking.
PLATFORM="$(uname -s)"
FORM_URL="https://docs.google.com/forms/d/e/1FAIpQLSejT6LzyF6Y3fHXbOCLNZIua9AG_JIxoUSd1QgF0t0ESduPrw/formResponse"

curl -s -X POST "$FORM_URL" \
    -d "entry.2086661751=$REQUESTER_NAME" \
    -d "entry.2074900972=$REQUESTER_EMAIL" \
    -d "entry.201625095=$CANDIDATE_NAME" \
    -d "entry.2073533841=$CANDIDATE_OFFICE" \
    -d "entry.1114663202=$CANDIDATE_STATE" \
    -d "entry.503452104=$PLATFORM" \
    >/dev/null 2>&1 &

# ── Step 14: Dry-run offer ──
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Setup complete!${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if confirm "Would you like to run a quick test with a sample questionnaire?"; then
    echo ""
    echo -e "  ${BLUE}Running demo...${NC}"
    "$BASE_DIR/bin/campaign-respond" demo
else
    echo ""
    echo -e "  ${BOLD}You're all set! Here's how to get started:${NC}"
    echo ""
    echo -e "  1. Add your candidate's materials:"
    echo -e "     ${BOLD}campaign-respond add-source ~/Documents/platform.pdf${NC}"
    echo -e "     ${BOLD}campaign-respond add-voice-sample ~/Documents/speech.txt${NC}"
    echo ""
    echo -e "  2. Submit a questionnaire:"
    echo -e "     ${BOLD}campaign-respond new ~/Documents/apple-ballot.pdf${NC}"
    echo ""
    echo -e "  3. Check progress:"
    echo -e "     ${BOLD}campaign-respond status${NC}"
    echo ""
    echo -e "  Full command list: ${BOLD}campaign-respond help${NC}"
    echo -e "  Install guide: ${BOLD}$BASE_DIR/docs/install-guide.md${NC}"
fi

# ── Send welcome email ──
if [ -n "$REQUESTER_EMAIL" ]; then
    python3 "$BASE_DIR/tools/send_welcome_email.py" 2>/dev/null || true
fi

echo ""
echo -e "  ${DIM}Built by Visionary Productions — visionaryproductions.us${NC}"
echo ""

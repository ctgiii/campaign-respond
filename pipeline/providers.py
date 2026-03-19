"""Multi-model AI provider abstraction for Campaign Respond.

Supports:
  - Claude (Anthropic) — via CLI, API, or browser
  - Gemini (Google) — via API
  - OpenAI/ChatGPT — via API
"""

import json
import os
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_provider_config() -> dict:
    """Load AI provider configuration from campaign.json and .env."""
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")

    config_path = BASE_DIR / "config" / "campaign.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        pipeline = config.get("pipeline", {})
        return {
            "provider": pipeline.get("provider", os.getenv("AI_PROVIDER", "claude")),
            "model": pipeline.get("model", os.getenv("AI_MODEL", "claude-sonnet-4-6")),
            "mode": pipeline.get("mode", os.getenv("AI_MODE", "cli")),
        }

    return {
        "provider": os.getenv("AI_PROVIDER", "claude"),
        "model": os.getenv("AI_MODEL", "claude-sonnet-4-6"),
        "mode": os.getenv("AI_MODE", "cli"),
    }


def run_prompt(prompt: str, system_prompt: str = "",
               provider: str = None, model: str = None,
               mode: str = None) -> str:
    """Run a prompt through the configured AI provider.

    Args:
        prompt: The user prompt to send
        system_prompt: System/context prompt (bot identity)
        provider: Override provider (claude/gemini/openai)
        model: Override model name
        mode: Override mode (cli/api/browser)

    Returns:
        AI response text
    """
    config = get_provider_config()
    provider = provider or config["provider"]
    model = model or config["model"]
    mode = mode or config["mode"]

    if provider == "claude":
        return _run_claude(prompt, system_prompt, model, mode)
    elif provider == "gemini":
        return _run_gemini(prompt, system_prompt, model)
    elif provider == "openai":
        return _run_openai(prompt, system_prompt, model)
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Use: claude, gemini, openai")


# ── Claude (Anthropic) ──

def _run_claude(prompt: str, system_prompt: str, model: str, mode: str) -> str:
    """Run prompt via Claude — CLI, API, or browser mode."""
    if mode == "cli":
        return _claude_cli(prompt, system_prompt, model)
    elif mode == "api":
        return _claude_api(prompt, system_prompt, model)
    elif mode == "browser":
        return _claude_browser(prompt, system_prompt)
    else:
        # Try CLI first, fall back to API, then browser
        try:
            return _claude_cli(prompt, system_prompt, model)
        except (FileNotFoundError, RuntimeError):
            try:
                return _claude_api(prompt, system_prompt, model)
            except (ImportError, Exception):
                return _claude_browser(prompt, system_prompt)


def _claude_cli(prompt: str, system_prompt: str, model: str) -> str:
    """Run via Claude Code CLI."""
    cmd = ["claude", "--print", "--model", model, "-p", prompt]
    if system_prompt:
        cmd.extend(["--append-system-prompt", system_prompt])

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=600, cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed (exit {result.returncode}): {result.stderr}")
    return result.stdout


def _claude_api(prompt: str, system_prompt: str, model: str) -> str:
    """Run via Anthropic Python SDK."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("Install anthropic SDK: pip install anthropic")

    client = anthropic.Anthropic()
    kwargs = {
        "model": model,
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    message = client.messages.create(**kwargs)
    return message.content[0].text


def _claude_browser(prompt: str, system_prompt: str) -> str:
    """Open Claude in the browser for interactive use.

    This mode opens claude.ai in the user's browser with the prompt
    copied to clipboard. The user pastes, gets the response, and
    pastes it back.
    """
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"[CONTEXT]\n{system_prompt}\n\n[TASK]\n{prompt}"

    # Copy to clipboard
    try:
        process = subprocess.Popen(
            ["pbcopy"] if os.uname().sysname == "Darwin" else ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
        )
        process.communicate(full_prompt.encode())
    except Exception:
        pass

    # Save prompt to temp file
    temp_file = BASE_DIR / "state" / ".browser-prompt.txt"
    temp_file.write_text(full_prompt)

    print("\n" + "=" * 60)
    print("BROWSER MODE — Claude will open in your browser")
    print("=" * 60)
    print(f"\n1. The prompt has been copied to your clipboard.")
    print(f"   (Also saved to: {temp_file})")
    print(f"\n2. Paste it into Claude and wait for the response.")
    print(f"\n3. Copy Claude's ENTIRE response, then come back here")
    print(f"   and paste it below (press Enter twice when done):\n")

    # Open Claude in browser
    webbrowser.open("https://claude.ai/new")

    # Read multi-line response
    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append("")
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    response = "\n".join(lines).strip()
    if not response:
        raise RuntimeError("No response received from browser mode.")
    return response


# ── Google Gemini ──

def _run_gemini(prompt: str, system_prompt: str, model: str) -> str:
    """Run via Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "Install Google AI SDK: pip install google-generativeai\n"
            "Get an API key at: https://aistudio.google.com/apikey"
        )

    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_AI_API_KEY not set. Add it to .env or set the environment variable.\n"
            "Get a key at: https://aistudio.google.com/apikey"
        )

    genai.configure(api_key=api_key)

    # Map model names
    model_map = {
        "gemini-2.5-pro": "gemini-2.5-pro-preview-06-05",
        "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20",
        "gemini-pro": "gemini-1.5-pro",
    }
    model_id = model_map.get(model, model)

    gen_model = genai.GenerativeModel(
        model_name=model_id,
        system_instruction=system_prompt if system_prompt else None,
    )

    response = gen_model.generate_content(prompt)
    return response.text


# ── OpenAI / ChatGPT ──

def _run_openai(prompt: str, system_prompt: str, model: str) -> str:
    """Run via OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "Install OpenAI SDK: pip install openai\n"
            "Get an API key at: https://platform.openai.com/api-keys"
        )

    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Add it to .env or set the environment variable.\n"
            "Get a key at: https://platform.openai.com/api-keys"
        )

    client = OpenAI(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Map model names
    model_map = {
        "gpt-4o": "gpt-4o",
        "gpt-4": "gpt-4-turbo",
        "gpt-3.5": "gpt-3.5-turbo",
    }
    model_id = model_map.get(model, model)

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        max_tokens=8192,
    )

    return response.choices[0].message.content


# ── Utility ──

def list_providers() -> dict:
    """List available providers and their status."""
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")

    providers = {}

    # Claude
    claude_cli = subprocess.run(
        ["which", "claude"], capture_output=True
    ).returncode == 0
    claude_api = bool(os.getenv("ANTHROPIC_API_KEY"))
    providers["claude"] = {
        "available": claude_cli or claude_api or True,  # browser always works
        "modes": {
            "cli": claude_cli,
            "api": claude_api,
            "browser": True,
        },
        "models": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
    }

    # Gemini
    gemini_key = bool(os.getenv("GOOGLE_AI_API_KEY"))
    try:
        import google.generativeai
        gemini_sdk = True
    except ImportError:
        gemini_sdk = False
    providers["gemini"] = {
        "available": gemini_key and gemini_sdk,
        "modes": {"api": gemini_key and gemini_sdk},
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-pro"],
        "setup": "pip install google-generativeai && set GOOGLE_AI_API_KEY in .env",
    }

    # OpenAI
    openai_key = bool(os.getenv("OPENAI_API_KEY"))
    try:
        import openai
        openai_sdk = True
    except ImportError:
        openai_sdk = False
    providers["openai"] = {
        "available": openai_key and openai_sdk,
        "modes": {"api": openai_key and openai_sdk},
        "models": ["gpt-4o", "gpt-4", "gpt-3.5"],
        "setup": "pip install openai && set OPENAI_API_KEY in .env",
    }

    return providers

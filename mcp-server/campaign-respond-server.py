#!/usr/bin/env python3
"""Campaign Respond MCP Server for Claude Desktop App."""

import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def read_jsonrpc():
    headers = {}
    while True:
        line = sys.stdin.readline()
        if line in ("\r\n", "\n", ""):
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
    length = int(headers.get("Content-Length", 0))
    if length == 0:
        return None
    return json.loads(sys.stdin.read(length))


def write_jsonrpc(response):
    body = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    sys.stdout.flush()


def handle_initialize(params):
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "campaign-respond", "version": "1.0.0"},
    }


def handle_tools_list():
    return {"tools": [
        {"name": "new_questionnaire", "description": "Submit a new questionnaire (PDF/DOCX/TXT/MD).", "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to questionnaire file"}}, "required": ["file_path"]}},
        {"name": "check_status", "description": "Check pipeline status.", "inputSchema": {"type": "object", "properties": {"questionnaire_id": {"type": "string", "description": "Optional: specific questionnaire ID"}}}},
        {"name": "add_source", "description": "Add candidate source material.", "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to source file"}}, "required": ["file_path"]}},
        {"name": "review_draft", "description": "View current draft for a questionnaire.", "inputSchema": {"type": "object", "properties": {"questionnaire_id": {"type": "string", "description": "Questionnaire ID"}}, "required": ["questionnaire_id"]}},
        {"name": "provide_feedback", "description": "Submit corrections on a response.", "inputSchema": {"type": "object", "properties": {"questionnaire_id": {"type": "string"}, "question_number": {"type": "integer"}, "feedback": {"type": "string"}, "category": {"type": "string", "enum": ["tone", "position", "accuracy", "framing"]}}, "required": ["questionnaire_id", "feedback"]}},
        {"name": "list_questionnaires", "description": "List all questionnaires with status.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "update_config", "description": "View campaign configuration.", "inputSchema": {"type": "object", "properties": {"section": {"type": "string", "enum": ["candidate", "voice", "priorities", "storage", "all"]}}}},
    ]}


def handle_tool_call(name, arguments):
    try:
        if name == "new_questionnaire":
            p = Path(arguments["file_path"]).expanduser().resolve()
            if not p.exists():
                return {"content": [{"type": "text", "text": f"File not found: {p}"}], "isError": True}
            from pipeline.orchestrator import run_pipeline
            q_id = run_pipeline(str(p))
            return {"content": [{"type": "text", "text": f"Pipeline started. ID: {q_id}"}]}

        elif name == "check_status":
            q_id = arguments.get("questionnaire_id")
            active = BASE_DIR / "questionnaires" / "active"
            if q_id:
                sf = active / q_id / "pipeline-state.json"
                if sf.exists():
                    return {"content": [{"type": "text", "text": json.dumps(json.loads(sf.read_text()), indent=2)}]}
                return {"content": [{"type": "text", "text": f"Not found: {q_id}"}], "isError": True}
            results = []
            if active.exists():
                for d in sorted(active.iterdir()):
                    if d.is_dir():
                        sf = d / "pipeline-state.json"
                        if sf.exists():
                            s = json.loads(sf.read_text())
                            results.append(f"- {d.name}: stage={s['current_stage']}")
            return {"content": [{"type": "text", "text": "Active:\n" + ("\n".join(results) or "None")}]}

        elif name == "add_source":
            import shutil
            p = Path(arguments["file_path"]).expanduser().resolve()
            if not p.exists():
                return {"content": [{"type": "text", "text": f"File not found: {p}"}], "isError": True}
            dest = BASE_DIR / "knowledge-base" / "sources" / p.name
            shutil.copy2(p, dest)
            return {"content": [{"type": "text", "text": f"Source added: {p.name}"}]}

        elif name == "review_draft":
            q_id = arguments["questionnaire_id"]
            for status in ["active", "completed"]:
                for fname in ["final-responses.md", "revised-draft.md", "humanized-draft.md", "communications-draft.md"]:
                    f = BASE_DIR / "questionnaires" / status / q_id / fname
                    if f.exists():
                        return {"content": [{"type": "text", "text": f"## {fname}\n\n{f.read_text()}"}]}
            return {"content": [{"type": "text", "text": f"No drafts for: {q_id}"}], "isError": True}

        elif name == "provide_feedback":
            corrections = BASE_DIR / "knowledge-base" / "feedback" / "corrections.jsonl"
            corrections.parent.mkdir(parents=True, exist_ok=True)
            entry = {"timestamp": datetime.now().isoformat(), "questionnaire_id": arguments["questionnaire_id"], "question_num": arguments.get("question_number", 0), "original": "", "corrected": arguments["feedback"], "category": arguments.get("category", "general"), "responsible_bot": "human"}
            with open(corrections, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return {"content": [{"type": "text", "text": f"Feedback recorded."}]}

        elif name == "list_questionnaires":
            results = []
            for status in ["active", "completed", "archived"]:
                d = BASE_DIR / "questionnaires" / status
                if d.exists():
                    for qdir in sorted(d.iterdir()):
                        if qdir.is_dir():
                            results.append(f"[{status.upper()}] {qdir.name}")
            return {"content": [{"type": "text", "text": "\n".join(results) or "None yet"}]}

        elif name == "update_config":
            section = arguments.get("section", "all")
            configs = {}
            mapping = {"candidate": "campaign.json", "voice": "voice-profile.json", "priorities": "priorities.json", "storage": "storage.json"}
            for key, fname in mapping.items():
                if section in (key, "all"):
                    p = BASE_DIR / "config" / fname
                    if p.exists():
                        configs[key] = json.loads(p.read_text())
            return {"content": [{"type": "text", "text": json.dumps(configs, indent=2)}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}


def main():
    while True:
        msg = read_jsonrpc()
        if msg is None:
            break
        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})
        result = None
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "initialized":
            continue
        elif method == "tools/list":
            result = handle_tools_list()
        elif method == "tools/call":
            result = handle_tool_call(params.get("name", ""), params.get("arguments", {}))
        elif method == "shutdown":
            write_jsonrpc({"jsonrpc": "2.0", "id": msg_id, "result": None})
            break
        if msg_id is not None and result is not None:
            write_jsonrpc({"jsonrpc": "2.0", "id": msg_id, "result": result})


if __name__ == "__main__":
    main()

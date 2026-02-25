"""
ChatMol — Agentic PyMOL Plugin with OpenRouter and Qt5 GUI.

Load in PyMOL:
    run /path/to/pymol_plugin/v2/chatmol.py

Or from remote:
    load https://raw.githubusercontent.com/ChatMol/ChatMol/main/pymol_plugin/v2/chatmol.py

Demo prompt:
ZH: 3wzm的A链是玉米赤霉烯酮水解酶和底物的共晶复合物，作图展示酶底物(ZER)相互作用，风格参考顶级结构生物学期刊的风格，画面干净、清晰。
EN: Chain A of 3WZM is a cocrystal complex of zearalenone hydrolase and its substrate; create a figure showing the enzyme-substrate (ZER) interaction, referencing the style of top-tier structural biology journals, with a clean and clear aesthetic.
"""

import os
import json
import re
import time
import random
import base64
import tempfile
import threading
import requests

from datetime import datetime
from pymol import cmd, util, preset

# ---------------------------------------------------------------------------
# 1. Provider registry + LLMClient — multi-provider HTTP wrapper (no SDK)
# ---------------------------------------------------------------------------

# Each provider entry:
#   base_url  – chat completions endpoint
#   env_var   – environment variable for the API key
#   models    – list of (model_id, label) for the settings UI
#   extra_headers – provider-specific headers (optional)
PROVIDERS = {
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "env_var": "OPENROUTER_API_KEY",
        "models": [
            ("openai/gpt-4o", "GPT-4o"),
            ("openai/gpt-5.2", "GPT-5.2"),
            ("openai/gpt-5.3-codex", "GPT-5.3 Codex"),
            ("google/gemini-3.1-pro-preview", "Gemini 3.1 Pro"),
            ("google/gemini-3-flash-preview", "Gemini 3 Flash"),
            ("deepseek/deepseek-chat", "DeepSeek V3"),
        ],
        "vision_models": [
            ("openai/gpt-4o", "GPT-4o"),
            ("openai/gpt-5.2", "GPT-5.2"),
            ("anthropic/claude-sonnet-4.6", "Claude Sonnet 4.6"),
            ("google/gemini-3-flash-preview", "Gemini 3 Flash"),
            ("google/gemini-3.1-pro-preview", "Gemini 3.1 Pro"),
        ],
        "extra_headers": {
            "HTTP-Referer": "https://github.com/ChatMol/ChatMol",
            "X-Title": "ChatMol",
        },
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/chat/completions",
        "env_var": "DEEPSEEK_API_KEY",
        "models": [
            ("deepseek-chat", "DeepSeek V3"),
            ("deepseek-reasoner", "DeepSeek R1"),
        ],
        "vision_models": [],
        "extra_headers": {},
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "base_url": "https://api.moonshot.ai/v1/chat/completions",
        "env_var": "MOONSHOT_API_KEY",
        "models": [
            ("kimi-k2.5", "Kimi K2.5"),
        ],
        "vision_models": [
            ("kimi-k2.5", "Kimi K2.5"),
        ],
        "extra_headers": {},
    },
    "glm": {
        "label": "GLM (Zhipu)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "env_var": "GLM_API_KEY",
        "models": [
            ("glm-5", "GLM-5"),
        ],
        "vision_models": [],
        "extra_headers": {},
    },
}


class LLMTransientError(RuntimeError):
    """Transient API/network errors that should be retried."""


class LLMFatalError(RuntimeError):
    """Non-retriable API errors."""


class LLMClient:
    """Thin HTTP client for OpenAI-compatible chat-completion APIs."""

    def __init__(self, provider_name, api_key):
        prov = PROVIDERS.get(provider_name, PROVIDERS["openrouter"])
        self.base_url = prov["base_url"]
        self.extra_headers = prov.get("extra_headers", {})
        self.api_key = api_key

    def _headers(self):
        h = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        h.update(self.extra_headers)
        return h

    def _check_response(self, resp):
        if resp.status_code >= 400:
            try:
                body = resp.json()
                err = body.get("error", {})
                if isinstance(err, dict):
                    detail = err.get("message", "") or err.get("msg", "")
                else:
                    detail = str(err)
            except Exception:
                detail = resp.text[:500] if resp.text else ""
            message = (
                f"API error {resp.status_code} from {self.base_url}: "
                f"{detail or resp.reason}"
            )
            if resp.status_code in (408, 409, 425, 429) or resp.status_code >= 500:
                raise LLMTransientError(message)
            raise LLMFatalError(message)

    def _parse_choices(self, data):
        if "error" in data:
            err = data["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise LLMFatalError(f"API returned error: {msg}")
        if "choices" not in data or not data["choices"]:
            raise LLMFatalError(
                f"Unexpected API response (no choices): "
                f"{json.dumps(data, ensure_ascii=False)[:300]}"
            )
        return data["choices"][0]

    def chat_completion(
        self, model, messages, tools=None, temperature=0.01, max_tokens=4096
    ):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        try:
            resp = requests.post(
                self.base_url, headers=self._headers(), json=payload, timeout=120
            )
        except requests.ConnectionError:
            raise LLMTransientError(f"Connection failed: cannot reach {self.base_url}")
        except requests.Timeout:
            raise LLMTransientError(f"Request timed out after 120s to {self.base_url}")
        self._check_response(resp)
        data = resp.json()
        self._parse_choices(data)  # validate structure
        return data

    def vision_completion(self, model, text_prompt, image_base64):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            }
        ]
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1024,
        }
        try:
            resp = requests.post(
                self.base_url, headers=self._headers(), json=payload, timeout=120
            )
        except requests.ConnectionError:
            raise LLMTransientError(f"Connection failed: cannot reach {self.base_url}")
        except requests.Timeout:
            raise LLMTransientError(f"Request timed out after 120s to {self.base_url}")
        self._check_response(resp)
        data = resp.json()
        choice = self._parse_choices(data)
        return choice["message"]["content"]


# ---------------------------------------------------------------------------
# 2. PyMOLTools — 4 tool definitions + execution
# ---------------------------------------------------------------------------


BLOCKED_COMMANDS = [
    ("blocked destructive command", re.compile(r"^\s*delete\s+all\s*$", re.I)),
    ("blocked destructive command", re.compile(r"^\s*remove\s+all\s*$", re.I)),
    ("blocked session reset command", re.compile(r"^\s*reinitialize(?:\s|$)", re.I)),
    ("blocked quit command", re.compile(r"^\s*quit(?:\s|$)", re.I)),
    ("blocked script execution command", re.compile(r"^\s*run(?:\s|$)", re.I)),
    ("blocked python command", re.compile(r"^\s*python(?:\s|$)", re.I)),
    (
        "blocked shell/system command",
        re.compile(
            r"^\s*(?:!|shell(?:\s|$)|system(?:\s|$)|os\.system|subprocess\.)", re.I
        ),
    ),
]

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_session",
            "description": (
                "Inspect the current PyMOL session. Returns structured JSON "
                "with objects, chain summaries, atom counts, and selections."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "include_view": {
                        "type": "boolean",
                        "description": "Include camera view matrix.",
                        "default": False,
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_pymol_commands",
            "description": (
                "Execute newline-separated PyMOL commands. Use this for all "
                "PyMOL operations: selections, styling, coloring, distances, "
                "presets, etc. Commands are run sequentially with safety "
                "guardrails (destructive/shell commands are blocked)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commands": {
                        "type": "string",
                        "description": "Newline-separated PyMOL commands.",
                    }
                },
                "required": ["commands"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render",
            "description": (
                "Render and export an image from the current scene. "
                "Use purpose=preview for quick iterative checks, and "
                "purpose=final for final publication export."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Output image path.",
                    },
                    "purpose": {
                        "type": "string",
                        "enum": ["preview", "final"],
                        "default": "preview",
                        "description": "preview is lightweight; final is high quality.",
                    },
                    "width": {"type": "integer", "default": 1400},
                    "height": {"type": "integer", "default": 1050},
                    "dpi": {"type": "integer", "default": 150},
                    "ray": {
                        "type": "boolean",
                        "description": "If omitted: preview=False, final=True.",
                    },
                    "transparent_bg": {"type": "boolean", "default": True},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capture_viewport",
            "description": (
                "Capture current viewport and run vision model analysis. "
                "Use this to visually verify your work (e.g., check that "
                "styling looks correct before finalizing)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_prompt": {
                        "type": "string",
                        "default": "Describe what you see in this molecular visualization.",
                    }
                },
            },
        },
    },
]


def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    if value is None:
        return default
    return bool(value)


def _blocked_reason(line):
    for reason, pattern in BLOCKED_COMMANDS:
        if pattern.search(line):
            return reason
    return ""


def execute_tool(tool_name, arguments, client=None, vision_model=None):
    """Dispatch to a tool implementation and always return JSON text."""
    dispatch = {
        "inspect_session": _tool_inspect_session,
        "run_pymol_commands": _tool_run_pymol_commands,
        "render": _tool_render,
        "capture_viewport": _tool_capture_viewport,
    }
    fn = dispatch.get(tool_name)
    if fn is None:
        return json.dumps(
            {"ok": False, "tool": tool_name, "error": f"Unknown tool: {tool_name}"},
            ensure_ascii=False,
        )
    try:
        if tool_name == "capture_viewport":
            result = fn(client=client, vision_model=vision_model, **(arguments or {}))
        else:
            result = fn(**(arguments or {}))
    except TypeError as exc:
        result = {"ok": False, "tool": tool_name, "error": f"Invalid arguments: {exc}"}
    except Exception as exc:
        result = {"ok": False, "tool": tool_name, "error": str(exc)}
    return json.dumps(result, ensure_ascii=False)


def _tool_inspect_session(include_view=False):
    objects = cmd.get_names("objects")
    selections = cmd.get_names("selections")
    details = []
    for obj in objects:
        details.append(
            {
                "name": obj,
                "atoms": cmd.count_atoms(obj),
                "polymer_atoms": cmd.count_atoms(f"({obj}) and polymer"),
                "hetatm_atoms": cmd.count_atoms(f"({obj}) and hetatm"),
                "chains": cmd.get_chains(obj),
                "states": cmd.count_states(obj),
            }
        )
    out = {
        "ok": True,
        "tool": "inspect_session",
        "object_count": len(objects),
        "selection_count": len(selections),
        "objects": details,
        "selections": selections,
    }
    if _to_bool(include_view):
        out["view"] = list(cmd.get_view())
    return out


def _tool_run_pymol_commands(commands):
    lines = [
        ln.strip()
        for ln in commands.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    executed, blocked, errors = [], [], []
    known_names = set(cmd.get_names("all"))
    for line in lines:
        reason = _blocked_reason(line)
        if reason:
            blocked.append({"command": line, "reason": reason})
            continue
        m_del = re.match(r"^\s*delete\s+([A-Za-z0-9_]+)\s*$", line, re.I)
        if m_del:
            target = m_del.group(1)
            if target not in known_names:
                continue  # skip silently
        try:
            cmd.do(line)
            executed.append(line)
            if m_del:
                known_names.discard(m_del.group(1))
        except Exception as exc:
            errors.append({"command": line, "error": str(exc)})
    return {
        "ok": not blocked and not errors,
        "tool": "run_pymol_commands",
        "executed_count": len(executed),
        "blocked_count": len(blocked),
        "error_count": len(errors),
        "executed": executed,
        "blocked": blocked,
        "errors": errors,
    }


def _tool_render(
    path,
    width=None,
    height=None,
    dpi=None,
    ray=None,
    transparent_bg=True,
    purpose="preview",
):
    out_path = os.path.abspath(os.path.expanduser(path))
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    purpose = (purpose or "preview").strip().lower()
    if purpose not in ("preview", "final"):
        purpose = "preview"

    if purpose == "final":
        default_width, default_height, default_dpi = 2400, 1800, 300
        default_ray = True
    else:
        default_width, default_height, default_dpi = 1400, 1050, 150
        default_ray = False

    try:
        width = default_width if width is None else int(width)
        height = default_height if height is None else int(height)
        dpi = default_dpi if dpi is None else int(dpi)
        width = max(256, width)
        height = max(256, height)
        dpi = max(72, dpi)
    except (TypeError, ValueError):
        width, height, dpi = default_width, default_height, default_dpi

    if purpose == "preview":
        width = min(width, 2200)
        height = min(height, 1650)
        dpi = min(dpi, 220)

    ray_flag = 1 if _to_bool(ray, default=default_ray) else 0
    transparent = _to_bool(transparent_bg, default=True)
    cmd.set("ray_opaque_background", 0 if transparent else 1)
    cmd.png(out_path, width=width, height=height, dpi=dpi, ray=ray_flag, quiet=1)

    exists = os.path.exists(out_path)
    size = os.path.getsize(out_path) if exists else 0
    return {
        "ok": exists,
        "tool": "render",
        "path": out_path,
        "purpose": purpose,
        "width": width,
        "height": height,
        "dpi": dpi,
        "ray": bool(ray_flag),
        "transparent_bg": transparent,
        "bytes": size,
    }


def _tool_capture_viewport(analysis_prompt=None, client=None, vision_model=None):
    if analysis_prompt is None:
        analysis_prompt = "Describe what you see in this molecular visualization."

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        cmd.png(tmp_path, width=800, height=600, ray=0, quiet=1)
        time.sleep(0.5)
        with open(tmp_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("ascii")
    except Exception as exc:
        return {
            "ok": False,
            "tool": "capture_viewport",
            "error": f"Failed to capture viewport: {exc}",
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not vision_model or not client:
        return {
            "ok": False,
            "tool": "capture_viewport",
            "error": "No vision model configured. Use set_vision_model <model>.",
        }

    try:
        description = client.vision_completion(vision_model, analysis_prompt, img_data)
        return {
            "ok": True,
            "tool": "capture_viewport",
            "analysis_prompt": analysis_prompt,
            "description": description,
        }
    except Exception as exc:
        return {
            "ok": False,
            "tool": "capture_viewport",
            "error": f"Vision analysis failed: {exc}",
        }


# ---------------------------------------------------------------------------
# 3. System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are ChatMol, an expert AI assistant for PyMOL molecular visualization.

You have 4 tools:
- `inspect_session`: See what's loaded in PyMOL (objects, chains, atoms, selections).
- `run_pymol_commands`: Execute any PyMOL commands (selections, styling, coloring, \
distances, presets, fetch, etc.). Commands are newline-separated.
- `render`: Export an image (preview or final quality).
- `capture_viewport`: Screenshot + vision analysis to check your work visually.

Workflow:
1. For non-trivial requests, start with `inspect_session` to understand the current state.
2. Use `run_pymol_commands` for all PyMOL operations. You know PyMOL well — use \
cmd.select, cmd.show, cmd.hide, cmd.color, cmd.set, cmd.distance, cmd.zoom, \
cmd.orient, util.color_chains, util.cnc, preset.ligand_sites_hq, etc.
3. Use `capture_viewport` to verify your work visually when doing complex styling.
4. Use `render` when the user requests an image export.

Style guidelines (publication quality):
- White background, clean composition.
- Cartoon as baseline representation for protein.
- Sticks only for key residues, ligands, and interaction sites.
- Context in gray; 1-2 accent colors (often cyan/marine + orange).
- Surfaces used purposefully for targets/interfaces/pores, not everywhere.
- Hydrogen bonds / polar contacts shown with dashed lines when relevant.
- Keep decoration sparse — prioritize clarity over ornamentation.

Rules:
- Never issue destructive commands (reinitialize, quit, delete all, shell commands).
- If user input is ambiguous, ask for clarification rather than guessing.
- Be concise in your final response.
"""


# ---------------------------------------------------------------------------
# 4. ChatMolAgent — config persistence + simple agent loop
# ---------------------------------------------------------------------------


class ChatMolAgent:
    """Simple agentic loop: call LLM, execute tools, repeat."""

    CONFIG_PATH = os.path.expanduser("~/.PyMOL/chatmol_config.json")

    DEFAULT_CONFIG = {
        "provider": "openrouter",
        "api_keys": {},
        "text_model": "google/gemini-3-flash-preview",
        "vision_model": "google/gemini-3-flash-preview",
        "temperature": 0.01,
        "max_tokens": 4096,
        "max_iterations": 50,
        "max_tool_calls": 30,
    }

    def __init__(self):
        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        self.config = self._load_config()
        self._reinit_client()
        self.conversation_history = []

    # -- config persistence -------------------------------------------------

    def _load_config(self):
        try:
            with open(self.CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            merged = dict(self.DEFAULT_CONFIG)
            merged["api_keys"] = dict(self.DEFAULT_CONFIG["api_keys"])
            merged.update(cfg)
            if not isinstance(merged.get("api_keys"), dict):
                merged["api_keys"] = {}
            # Migrate old single "api_key" field
            old_key = merged.pop("api_key", "")
            if old_key and isinstance(old_key, str):
                prov = merged.get("provider", "openrouter")
                merged["api_keys"].setdefault(prov, old_key)
                self._save_config(merged)
            # Remove legacy keys
            for legacy in ("human_in_the_loop", "multi_agent_enabled"):
                merged.pop(legacy, None)
            return merged
        except (FileNotFoundError, json.JSONDecodeError):
            self._save_config(self.DEFAULT_CONFIG)
            return dict(self.DEFAULT_CONFIG)

    def _save_config(self, cfg=None):
        if cfg is None:
            cfg = self.config
        try:
            with open(self.CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception as exc:
            print(f"Warning: could not save config: {exc}")

    def _resolve_api_key(self):
        prov_name = self.config.get("provider", "openrouter")
        prov = PROVIDERS.get(prov_name, PROVIDERS["openrouter"])
        return os.getenv(prov["env_var"], "") or self.config.get("api_keys", {}).get(
            prov_name, ""
        )

    def _reinit_client(self):
        prov_name = self.config.get("provider", "openrouter")
        api_key = self._resolve_api_key()
        self.client = LLMClient(prov_name, api_key)

    # -- PyMOL-registered commands ------------------------------------------

    def chat(self, *args):
        """PyMOL command: chat <message>"""
        message = " ".join(str(a) for a in args).strip()
        if not message:
            print("Usage: chat <message>")
            return
        if not self._resolve_api_key():
            prov = self.config.get("provider", "openrouter")
            env = PROVIDERS.get(prov, {}).get("env_var", "")
            print(f"No API key set. Use: set_api_key <key>  (or set env var {env})")
            return
        try:
            response = self._run_agent_loop(message)
            print("=" * 50)
            print("ChatMol:", response)
            print("=" * 50)
        except RuntimeError as exc:
            print(f"ChatMol error: {exc}")
        except requests.exceptions.RequestException as exc:
            print(f"ChatMol network error: {exc}")
        except (KeyError, IndexError, TypeError) as exc:
            prov = self.config.get("provider", "openrouter")
            model = self.config.get("text_model", "")
            print(f"ChatMol error: unexpected response format — {exc}")
            print(f"  Provider: {prov}, Model: {model}")
            print(
                "  The model may not support tool calling, "
                "or the API returned an unexpected structure."
            )
        except Exception as exc:
            print(f"ChatMol error ({type(exc).__name__}): {exc}")

    def set_api_key(self, api_key=""):
        """PyMOL command: set_api_key <key>"""
        api_key = api_key.strip()
        if not api_key:
            prov_name = self.config.get("provider", "openrouter")
            label = PROVIDERS.get(prov_name, {}).get("label", prov_name)
            print(f"Usage: set_api_key <your_{label}_api_key>")
            return
        prov_name = self.config.get("provider", "openrouter")
        if not isinstance(self.config.get("api_keys"), dict):
            self.config["api_keys"] = {}
        self.config["api_keys"][prov_name] = api_key
        self._save_config()
        self._reinit_client()
        label = PROVIDERS.get(prov_name, {}).get("label", prov_name)
        print(f"{label} API key saved.")

    def set_provider(self, provider_name=""):
        """PyMOL command: set_provider <name>"""
        provider_name = provider_name.strip().lower()
        if not provider_name or provider_name not in PROVIDERS:
            print(f"Available providers: {', '.join(PROVIDERS.keys())}")
            if provider_name:
                print(f"Unknown provider: {provider_name}")
            return
        self.config["provider"] = provider_name
        prov = PROVIDERS[provider_name]
        if prov["models"]:
            self.config["text_model"] = prov["models"][0][0]
        if prov["vision_models"]:
            self.config["vision_model"] = prov["vision_models"][0][0]
        else:
            self.config["vision_model"] = ""
        self._save_config()
        self._reinit_client()
        print(f"Provider set to: {prov['label']}")
        print(f"  Text model: {self.config['text_model']}")
        if self.config["vision_model"]:
            print(f"  Vision model: {self.config['vision_model']}")
        print(f"  Set API key via: set_api_key <key>  (or env {prov['env_var']})")

    def set_model(self, model_name=""):
        """PyMOL command: set_model <model>"""
        model_name = model_name.strip()
        if not model_name:
            print(f"Current model: {self.config['text_model']}")
            print("Usage: set_model <provider/model>")
            return
        self.config["text_model"] = model_name
        self._save_config()
        print(f"Text model set to: {model_name}")

    def set_vision_model(self, model_name=""):
        """PyMOL command: set_vision_model <model>"""
        model_name = model_name.strip()
        if not model_name:
            print(f"Current vision model: {self.config['vision_model']}")
            print("Usage: set_vision_model <provider/model>")
            return
        self.config["vision_model"] = model_name
        self._save_config()
        print(f"Vision model set to: {model_name}")

    def reset_conversation(self):
        """PyMOL command: reset_conversation"""
        self.conversation_history = []
        print("Conversation history cleared.")

    def save_conversation(self, filename=""):
        """PyMOL command: save_conversation [filename]"""
        if not filename:
            filename = (
                f"chatmol_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, indent=2)
        print(f"Conversation saved to {filename}")

    def load_conversation(self, filename=""):
        """PyMOL command: load_conversation <filename>"""
        if not filename:
            print("Usage: load_conversation <filename.json>")
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.conversation_history = json.load(f)
            print(
                f"Loaded conversation from {filename} "
                f"({len(self.conversation_history)} messages)"
            )
        except Exception as exc:
            print(f"Failed to load conversation: {exc}")

    def show_config(self):
        """PyMOL command: chatmol_config"""
        prov_name = self.config.get("provider", "openrouter")
        prov = PROVIDERS.get(prov_name, {})
        key = self._resolve_api_key()
        masked = (key[:8] + "..." + key[-4:]) if key and len(key) > 12 else "(not set)"
        has_env = bool(os.getenv(prov.get("env_var", ""), ""))
        print("ChatMol configuration:")
        print(f"  provider: {prov.get('label', prov_name)} ({prov_name})")
        print(f"  api_key: {masked} ({'env var' if has_env else 'config file'})")
        print(f"  text_model: {self.config.get('text_model', '')}")
        print(f"  vision_model: {self.config.get('vision_model', '') or '(none)'}")
        print(f"  temperature: {self.config.get('temperature', 0.01)}")
        print(f"  max_tokens: {self.config.get('max_tokens', 4096)}")
        print(f"  max_iterations: {self.config.get('max_iterations', 50)}")
        print(f"  max_tool_calls: {self.config.get('max_tool_calls', 30)}")
        stored = [k for k, v in self.config.get("api_keys", {}).items() if v]
        if stored:
            print(f"  keys stored for: {', '.join(stored)}")

    # -- agentic loop -------------------------------------------------------

    def _chat_completion_with_retry(
        self, model, messages, tool_defs, temperature, max_tokens, phase_callback=None
    ):
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                return self.client.chat_completion(
                    model,
                    messages,
                    tools=tool_defs,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except LLMTransientError as exc:
                if attempt >= max_attempts:
                    raise RuntimeError(
                        f"Transient API errors persisted after {max_attempts} attempts: {exc}"
                    )
                delay = min(8.0, float(2 ** (attempt - 1))) + random.uniform(0.0, 0.4)
                print(
                    f"  [Retry {attempt}/{max_attempts}] transient error: "
                    f"{exc}. Sleeping {delay:.1f}s."
                )
                if phase_callback:
                    phase_callback("Retrying API request")
                time.sleep(delay)

    @staticmethod
    def _parse_assistant_message(data):
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Invalid API response: missing choices.")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Invalid API response: missing assistant message.")
        return message

    @staticmethod
    def _normalize_content(content):
        if isinstance(content, (list, dict)):
            return json.dumps(content, ensure_ascii=False)
        if content is None:
            return ""
        if not isinstance(content, str):
            return str(content)
        return content

    @staticmethod
    def _parse_tool_calls(assistant_msg):
        raw_calls = assistant_msg.get("tool_calls") or []
        parsed = []
        for tc in raw_calls:
            if not isinstance(tc, dict):
                raise RuntimeError("Invalid tool call entry from model.")
            tc_id = tc.get("id")
            fn = tc.get("function") or {}
            fn_name = fn.get("name")
            raw_args = fn.get("arguments", "{}")
            if not tc_id or not fn_name:
                raise RuntimeError(
                    "Invalid tool call payload (missing id or function name)."
                )
            if isinstance(raw_args, dict):
                fn_args = raw_args
            else:
                raw_args = "{}" if raw_args is None else str(raw_args).strip()
                if not raw_args:
                    raw_args = "{}"
                try:
                    fn_args = json.loads(raw_args)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"Tool arguments not valid JSON for {fn_name}: {exc}"
                    )
            if not isinstance(fn_args, dict):
                raise RuntimeError(f"Tool arguments for {fn_name} must be an object.")
            parsed.append(
                {"id": tc_id, "name": fn_name, "arguments": fn_args, "raw": tc}
            )
        return parsed

    def _make_tool_executor(self, tool_executor_override=None):
        """Return a tool executor function that passes client/vision_model."""
        if tool_executor_override:
            return tool_executor_override
        client = self.client
        vision_model = self.config.get("vision_model", "")

        def _executor(tool_name, arguments):
            return execute_tool(
                tool_name, arguments, client=client, vision_model=vision_model
            )

        return _executor

    def _run_agent_loop_internal(
        self, message, tool_executor=None, phase_callback=None
    ):
        self.conversation_history.append({"role": "user", "content": message})

        model = self.config["text_model"]
        temperature = self.config.get("temperature", 0.01)
        max_tokens = self.config.get("max_tokens", 4096)
        max_iterations = max(1, int(self.config.get("max_iterations", 50) or 50))
        max_tool_calls = max(8, int(self.config.get("max_tool_calls", 30) or 30))
        executor = self._make_tool_executor(tool_executor)
        tool_calls_used = 0

        for iteration in range(max_iterations):
            if phase_callback:
                phase_callback("Thinking" if iteration == 0 else "Thinking more")

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages += self.conversation_history

            data = self._chat_completion_with_retry(
                model,
                messages,
                TOOL_DEFINITIONS,
                temperature,
                max_tokens,
                phase_callback,
            )
            assistant_msg = self._parse_assistant_message(data)
            parsed_calls = self._parse_tool_calls(assistant_msg)
            content = self._normalize_content(assistant_msg.get("content", None))

            history_entry = {"role": "assistant", "content": content}
            if parsed_calls:
                history_entry["tool_calls"] = [tc["raw"] for tc in parsed_calls]

            if parsed_calls:
                tool_entries = []
                for tc in parsed_calls:
                    fn_name = tc["name"]
                    fn_args = tc["arguments"]

                    if phase_callback:
                        phase_callback(f"Running {fn_name}")
                    print(
                        f"  [Tool: {fn_name}] "
                        f"{json.dumps(fn_args, ensure_ascii=False)[:120]}"
                    )

                    if tool_calls_used >= max_tool_calls:
                        result = json.dumps(
                            {
                                "ok": False,
                                "tool": fn_name,
                                "error": (
                                    "Tool-call budget reached. Stop calling tools "
                                    "and provide your final response."
                                ),
                            },
                            ensure_ascii=False,
                        )
                    else:
                        try:
                            result = executor(fn_name, fn_args)
                        except Exception as exc:
                            result = json.dumps(
                                {"ok": False, "tool": fn_name, "error": str(exc)},
                                ensure_ascii=False,
                            )

                    tool_entries.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        }
                    )
                    tool_calls_used += 1

                self.conversation_history.append(history_entry)
                self.conversation_history.extend(tool_entries)
                continue

            # No tool calls — this is the final response
            self.conversation_history.append(history_entry)
            return (content or "").strip()

        return (
            "Agent loop reached maximum iterations "
            f"({max_iterations}) without a final response."
        )

    def _run_agent_loop(self, message):
        return self._run_agent_loop_internal(message, tool_executor=None)

    def run_agent_loop_with_callback(self, message, tool_executor, phase_callback=None):
        return self._run_agent_loop_internal(
            message, tool_executor=tool_executor, phase_callback=phase_callback
        )


# ---------------------------------------------------------------------------
# 5. Qt5 GUI (loaded conditionally)
# ---------------------------------------------------------------------------

_HAS_QT = False
try:
    from pymol.Qt import QtWidgets, QtCore, QtGui  # noqa: E402

    QDockWidget = QtWidgets.QDockWidget
    QWidget = QtWidgets.QWidget
    QVBoxLayout = QtWidgets.QVBoxLayout
    QHBoxLayout = QtWidgets.QHBoxLayout
    QTextEdit = QtWidgets.QTextEdit
    QLineEdit = QtWidgets.QLineEdit
    QPushButton = QtWidgets.QPushButton
    QLabel = QtWidgets.QLabel
    QDialog = QtWidgets.QDialog
    QFormLayout = QtWidgets.QFormLayout
    QDoubleSpinBox = QtWidgets.QDoubleSpinBox
    QSpinBox = QtWidgets.QSpinBox
    QComboBox = QtWidgets.QComboBox
    QApplication = QtWidgets.QApplication

    Qt = QtCore.Qt
    QThread = QtCore.QThread
    QTimer = QtCore.QTimer
    QPropertyAnimation = QtCore.QPropertyAnimation
    QEasingCurve = QtCore.QEasingCurve
    Signal = getattr(QtCore, "Signal", None) or getattr(QtCore, "pyqtSignal")
    Property = getattr(QtCore, "Property", None) or getattr(QtCore, "pyqtProperty")

    QColor = QtGui.QColor
    QPainter = QtGui.QPainter

    _HAS_QT = True
except ImportError:
    pass


if _HAS_QT:

    # -- ThinkingIndicator --------------------------------------------------

    class ThinkingIndicator(QWidget):
        """Three dots that pulse with a breathing animation."""

        _DOT_COUNT = 3
        _DOT_RADIUS = 4
        _DOT_SPACING = 14

        def __init__(self, parent=None):
            super().__init__(parent)
            self._opacity = 0.3
            self._phase_text = "Thinking"
            self.setFixedHeight(28)
            self._anim = QPropertyAnimation(self, b"dot_opacity")
            self._anim.setDuration(900)
            self._anim.setStartValue(0.3)
            self._anim.setEndValue(1.0)
            self._anim.setEasingCurve(QEasingCurve.InOutSine)
            self._anim.setLoopCount(-1)
            self._anim.finished.connect(lambda: None)
            self._forward = True
            self._cycle_timer = QTimer(self)
            self._cycle_timer.setInterval(900)
            self._cycle_timer.timeout.connect(self._toggle_direction)
            self.hide()

        def _toggle_direction(self):
            self._forward = not self._forward
            if self._forward:
                self._anim.setStartValue(0.3)
                self._anim.setEndValue(1.0)
            else:
                self._anim.setStartValue(1.0)
                self._anim.setEndValue(0.3)
            self._anim.start()

        @Property(float)
        def dot_opacity(self):
            return self._opacity

        @dot_opacity.setter
        def dot_opacity(self, value):
            self._opacity = value
            self.update()

        def start(self, phase_text="Thinking"):
            self._phase_text = phase_text
            self._anim.setStartValue(0.3)
            self._anim.setEndValue(1.0)
            self._forward = True
            self._anim.start()
            self._cycle_timer.start()
            self.show()

        def stop(self):
            self._anim.stop()
            self._cycle_timer.stop()
            self.hide()

        def set_phase(self, text):
            self._phase_text = text
            self.update()

        def paintEvent(self, _event):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QColor(120, 120, 120))
            p.drawText(8, 18, self._phase_text)
            label_width = p.fontMetrics().horizontalAdvance(self._phase_text) + 16
            color = QColor(70, 130, 230)
            for i in range(self._DOT_COUNT):
                offset = i * 0.15
                alpha = max(0.0, min(1.0, self._opacity - offset))
                color.setAlphaF(alpha)
                p.setBrush(color)
                p.setPen(Qt.NoPen)
                x = label_width + i * self._DOT_SPACING
                p.drawEllipse(x, 10, self._DOT_RADIUS * 2, self._DOT_RADIUS * 2)
            p.end()

    # -- AgentWorker --------------------------------------------------------

    class AgentWorker(QThread):
        """Runs the agentic loop off the main thread."""

        finished = Signal(str)
        error = Signal(str)
        tool_executed = Signal(str, str)
        request_tool_execution = Signal(str, str, str)
        phase_changed = Signal(str)

        def __init__(self, agent, message, parent=None):
            super().__init__(parent)
            self.agent = agent
            self.message = message
            self._tool_result = None
            self._tool_event = threading.Event()

        def run(self):
            try:
                response = self.agent.run_agent_loop_with_callback(
                    self.message, self._tool_executor, phase_callback=self._on_phase
                )
                self.finished.emit(response)
            except Exception as exc:
                self.error.emit(str(exc))

        def _on_phase(self, phase_text):
            self.phase_changed.emit(phase_text)

        def _tool_executor(self, tool_name, arguments):
            self._tool_event.clear()
            self._tool_result = None
            args_json = json.dumps(arguments, ensure_ascii=False)
            self.request_tool_execution.emit("", tool_name, args_json)
            self._tool_event.wait(timeout=60)
            result = self._tool_result or "Tool execution timed out."
            self.tool_executed.emit(tool_name, result[:200])
            return result

        def deliver_tool_result(self, result):
            self._tool_result = result
            self._tool_event.set()

    # -- ChatMolSettingsDialog ----------------------------------------------

    class ChatMolSettingsDialog(QDialog):

        def __init__(self, agent, parent=None):
            super().__init__(parent)
            self.agent = agent
            self.setWindowTitle("ChatMol Settings")
            self.setMinimumWidth(460)
            self._build_ui()

        def _build_ui(self):
            layout = QFormLayout(self)

            # Provider selector
            self.provider_combo = QComboBox()
            for key, prov in PROVIDERS.items():
                self.provider_combo.addItem(prov["label"], key)
            cur_prov = self.agent.config.get("provider", "openrouter")
            idx = self.provider_combo.findData(cur_prov)
            if idx >= 0:
                self.provider_combo.setCurrentIndex(idx)
            self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
            layout.addRow("Provider:", self.provider_combo)

            # API key
            self.api_key_edit = QLineEdit()
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.api_key_edit.setText(
                self.agent.config.get("api_keys", {}).get(cur_prov, "")
            )
            self.env_hint = QLabel()
            self.env_hint.setStyleSheet("color: grey; font-size: 10px;")
            key_layout = QVBoxLayout()
            key_layout.setSpacing(2)
            key_layout.addWidget(self.api_key_edit)
            key_layout.addWidget(self.env_hint)
            layout.addRow("API Key:", key_layout)

            # Text model
            self.text_model_combo = QComboBox()
            self.text_model_combo.setEditable(True)
            layout.addRow("Text Model:", self.text_model_combo)

            # Vision model
            self.vision_model_combo = QComboBox()
            self.vision_model_combo.setEditable(True)
            layout.addRow("Vision Model:", self.vision_model_combo)

            # Temperature
            self.temp_spin = QDoubleSpinBox()
            self.temp_spin.setRange(0.0, 2.0)
            self.temp_spin.setSingleStep(0.05)
            self.temp_spin.setValue(self.agent.config.get("temperature", 0.01))
            layout.addRow("Temperature:", self.temp_spin)

            # Max tokens
            self.max_tokens_spin = QSpinBox()
            self.max_tokens_spin.setRange(256, 16384)
            self.max_tokens_spin.setSingleStep(256)
            self.max_tokens_spin.setValue(self.agent.config.get("max_tokens", 4096))
            layout.addRow("Max Tokens:", self.max_tokens_spin)

            # Max iterations
            self.max_iterations_spin = QSpinBox()
            self.max_iterations_spin.setRange(1, 500)
            self.max_iterations_spin.setSingleStep(1)
            self.max_iterations_spin.setValue(
                self.agent.config.get("max_iterations", 50)
            )
            layout.addRow("Max Iterations:", self.max_iterations_spin)

            # Max tool calls per request
            self.max_tool_calls_spin = QSpinBox()
            self.max_tool_calls_spin.setRange(8, 200)
            self.max_tool_calls_spin.setSingleStep(1)
            self.max_tool_calls_spin.setValue(
                self.agent.config.get("max_tool_calls", 30)
            )
            layout.addRow("Max Tool Calls:", self.max_tool_calls_spin)

            # Buttons
            btn_layout = QHBoxLayout()
            save_btn = QPushButton("Save")
            save_btn.clicked.connect(self._on_save)
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addStretch()
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addRow(btn_layout)

            self._populate_models(cur_prov)

        def _on_provider_changed(self, _index):
            prov_key = self.provider_combo.currentData()
            stored_key = self.agent.config.get("api_keys", {}).get(prov_key, "")
            self.api_key_edit.setText(stored_key)
            self._populate_models(prov_key)

        def _populate_models(self, prov_key):
            prov = PROVIDERS.get(prov_key, PROVIDERS["openrouter"])

            env_var = prov.get("env_var", "")
            has_env = bool(os.getenv(env_var, ""))
            if has_env:
                self.env_hint.setText(f"Using env var {env_var} (overrides this field)")
            else:
                self.env_hint.setText(f"Or set env var: {env_var}")

            # Text models
            self.text_model_combo.clear()
            for model_id, label in prov["models"]:
                self.text_model_combo.addItem(f"{label}  ({model_id})", model_id)
            saved = self.agent.config.get("text_model", "")
            restored = False
            for i in range(self.text_model_combo.count()):
                if self.text_model_combo.itemData(i) == saved:
                    self.text_model_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and saved:
                self.text_model_combo.setEditText(saved)

            # Vision models
            self.vision_model_combo.clear()
            self.vision_model_combo.addItem("(none)", "")
            for model_id, label in prov.get("vision_models", []):
                self.vision_model_combo.addItem(f"{label}  ({model_id})", model_id)
            saved_v = self.agent.config.get("vision_model", "")
            restored_v = False
            for i in range(self.vision_model_combo.count()):
                if self.vision_model_combo.itemData(i) == saved_v:
                    self.vision_model_combo.setCurrentIndex(i)
                    restored_v = True
                    break
            if not restored_v and saved_v:
                self.vision_model_combo.setEditText(saved_v)

        def _on_save(self):
            prov_key = self.provider_combo.currentData()
            self.agent.config["provider"] = prov_key

            if not isinstance(self.agent.config.get("api_keys"), dict):
                self.agent.config["api_keys"] = {}
            self.agent.config["api_keys"][prov_key] = self.api_key_edit.text().strip()

            text_idx = self.text_model_combo.currentIndex()
            text_data = self.text_model_combo.itemData(text_idx)
            self.agent.config["text_model"] = (
                text_data if text_data else self.text_model_combo.currentText().strip()
            )

            vis_idx = self.vision_model_combo.currentIndex()
            vis_data = self.vision_model_combo.itemData(vis_idx)
            self.agent.config["vision_model"] = (
                vis_data
                if vis_data is not None
                else self.vision_model_combo.currentText().strip()
            )

            self.agent.config["temperature"] = self.temp_spin.value()
            self.agent.config["max_tokens"] = self.max_tokens_spin.value()
            self.agent.config["max_iterations"] = self.max_iterations_spin.value()
            self.agent.config["max_tool_calls"] = self.max_tool_calls_spin.value()
            self.agent._save_config()
            self.agent._reinit_client()
            self.accept()

    # -- ChatMolChatBar -----------------------------------------------------

    class ChatMolChatBar(QDockWidget):

        def __init__(self, agent, parent=None):
            super().__init__("ChatMol", parent)
            self.agent = agent
            self._worker = None
            self._build_ui()

        def _build_ui(self):
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(4, 4, 4, 4)
            vbox.setSpacing(4)

            # Top bar
            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel("<b>ChatMol</b>"))
            top_bar.addStretch()
            settings_btn = QPushButton("Settings")
            settings_btn.setFixedWidth(70)
            settings_btn.clicked.connect(self._open_settings)
            top_bar.addWidget(settings_btn)
            clear_btn = QPushButton("Clear")
            clear_btn.setFixedWidth(50)
            clear_btn.clicked.connect(self._clear_chat)
            top_bar.addWidget(clear_btn)
            vbox.addLayout(top_bar)

            # Execution trace panel
            self.trace_display = QTextEdit()
            self.trace_display.setReadOnly(True)
            self.trace_display.setMaximumHeight(92)
            self.trace_display.setStyleSheet(
                "font-family: Menlo, Consolas, monospace; font-size:10px; "
                "color:#263238; background:#FAFAFA;"
            )
            vbox.addWidget(self.trace_display)

            # Chat history
            self.chat_display = QTextEdit()
            self.chat_display.setReadOnly(True)
            self.chat_display.setMinimumHeight(120)
            vbox.addWidget(self.chat_display)

            # Thinking indicator
            self.thinking = ThinkingIndicator()
            vbox.addWidget(self.thinking)

            # Input bar
            input_bar = QHBoxLayout()
            self.input_edit = QLineEdit()
            self.input_edit.setPlaceholderText("Type a message...")
            self.input_edit.returnPressed.connect(self._on_send)
            input_bar.addWidget(self.input_edit)
            self.send_btn = QPushButton("Send")
            self.send_btn.setFixedWidth(50)
            self.send_btn.clicked.connect(self._on_send)
            input_bar.addWidget(self.send_btn)
            self.model_label = QLabel()
            self.model_label.setStyleSheet("color: grey; font-size: 10px;")
            self._update_model_label()
            input_bar.addWidget(self.model_label)
            vbox.addLayout(input_bar)

            self.setWidget(container)

        def _update_model_label(self):
            prov_name = self.agent.config.get("provider", "openrouter")
            prov_label = PROVIDERS.get(prov_name, {}).get("label", prov_name)
            model = self.agent.config.get("text_model", "")
            short = model.split("/")[-1] if "/" in model else model
            self.model_label.setText(f"{short} ({prov_label})")

        def _open_settings(self):
            dlg = ChatMolSettingsDialog(self.agent, self)
            if dlg.exec_():
                self._update_model_label()

        def _clear_chat(self):
            self.chat_display.clear()
            self.trace_display.clear()
            self.agent.reset_conversation()

        def _append_html(self, html):
            self.chat_display.append(html)
            sb = self.chat_display.verticalScrollBar()
            sb.setValue(sb.maximum())

        def _append_trace(self, text):
            self.trace_display.append(_escape_html(text))
            sb = self.trace_display.verticalScrollBar()
            sb.setValue(sb.maximum())

        def _on_send(self):
            text = self.input_edit.text().strip()
            if not text:
                return

            if not self.agent._resolve_api_key():
                self._append_html(
                    '<span style="color:red;">No API key set. '
                    "Open Settings to configure your API key.</span>"
                )
                return

            self.input_edit.clear()
            self.input_edit.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.trace_display.clear()

            self._append_html(
                f'<b style="color:#2962FF;">You:</b> {_escape_html(text)}'
            )

            self.thinking.start("Thinking")

            self._worker = AgentWorker(self.agent, text)
            self._worker.request_tool_execution.connect(
                self._execute_tool_on_main_thread
            )
            self._worker.phase_changed.connect(self._on_phase_changed)
            self._worker.tool_executed.connect(self._on_tool_executed)
            self._worker.finished.connect(self._on_agent_finished)
            self._worker.error.connect(self._on_agent_error)
            self._worker.start()

        def _on_phase_changed(self, phase_text):
            self.thinking.set_phase(phase_text)
            if "Retry" in phase_text:
                self._append_trace(f"[phase] {phase_text}")

        def _on_tool_executed(self, tool_name, result_preview):
            self._append_trace(f"[tool:{tool_name}] {result_preview}")

        def _execute_tool_on_main_thread(self, _call_id, tool_name, args_json):
            try:
                arguments = json.loads(args_json)
            except (json.JSONDecodeError, TypeError):
                arguments = {}
            self._append_trace(f"[call:{tool_name}] {args_json[:180]}")
            try:
                result = execute_tool(
                    tool_name,
                    arguments,
                    client=self.agent.client,
                    vision_model=self.agent.config.get("vision_model", ""),
                )
            except Exception as exc:
                result = f"Tool error: {exc}"
            if self._worker is not None:
                self._worker.deliver_tool_result(result)

        def _on_agent_finished(self, response):
            self.thinking.stop()
            self._append_html(f"<b>ChatMol:</b> {_escape_html(response)}")
            self.input_edit.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.input_edit.setFocus()

        def _on_agent_error(self, error_msg):
            self.thinking.stop()
            prov = self.agent.config.get("provider", "?")
            model = self.agent.config.get("text_model", "?")
            self._append_trace(f"[error] {error_msg}")
            self._append_html(
                f'<span style="color:red;"><b>Error</b> '
                f"[{_escape_html(prov)}/{_escape_html(model)}]: "
                f"{_escape_html(error_msg)}</span>"
            )
            self.input_edit.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.input_edit.setFocus()


def _escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )


# ---------------------------------------------------------------------------
# 6. Module-level initialisation
# ---------------------------------------------------------------------------

_agent = ChatMolAgent()

cmd.extend("chat", _agent.chat)
cmd.extend("set_provider", _agent.set_provider)
cmd.extend("set_api_key", _agent.set_api_key)
cmd.extend("set_model", _agent.set_model)
cmd.extend("set_vision_model", _agent.set_vision_model)
cmd.extend("reset_conversation", _agent.reset_conversation)
cmd.extend("save_conversation", _agent.save_conversation)
cmd.extend("load_conversation", _agent.load_conversation)
cmd.extend("chatmol_config", _agent.show_config)


def chatmol_settings():
    """Open the ChatMol settings dialog (requires Qt)."""
    if not _HAS_QT:
        print(
            "Qt not available. Configure via commands: "
            "set_api_key, set_model, set_vision_model"
        )
        return
    app = QApplication.instance()
    if app is None:
        print("No Qt application running.")
        return
    dlg = ChatMolSettingsDialog(_agent)
    dlg.exec_()


def chatmol_gui():
    """Manually open the ChatMol chat bar (requires Qt)."""
    _init_gui()


cmd.extend("chatmol_settings", chatmol_settings)
cmd.extend("chatmol_gui", chatmol_gui)


_chatbar = None


def _init_gui():
    """Find PyMOL's main window and dock the ChatMol chat bar."""
    global _chatbar
    if not _HAS_QT:
        print(
            "Qt not available — ChatMol GUI disabled. "
            "Use command-line: chat <message>"
        )
        return
    if _chatbar is not None:
        _chatbar.show()
        _chatbar.raise_()
        return

    app = QApplication.instance()
    if app is None:
        return

    main_win = None
    for w in app.topLevelWidgets():
        if w.inherits("QMainWindow") and w.isVisible():
            main_win = w
            break

    if main_win is None:
        print("ChatMol: could not find PyMOL main window for docking.")
        return

    _chatbar = ChatMolChatBar(_agent, main_win)
    main_win.addDockWidget(Qt.BottomDockWidgetArea, _chatbar)
    print("ChatMol chat bar loaded.")


if _HAS_QT:
    try:
        QTimer.singleShot(1500, _init_gui)
    except Exception:
        pass

print(
    "ChatMol plugin loaded. Commands: chat, set_provider, set_api_key, "
    "set_model, set_vision_model, reset_conversation, "
    "chatmol_config, chatmol_settings, chatmol_gui"
)

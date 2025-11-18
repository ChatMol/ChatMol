import json
import os
from typing import Any, Callable, Dict, List, Optional

ToolFunction = Callable[..., Any]
import streamlit as st
from openai import OpenAI

import chatmol as cm
from app_utils import pymol_tool_schema, encode_image

PYMOL_COMMAND_MODEL = "gpt-4.1"
PYMOL_COMMAND_MODEL_URL = "https://api.openai.com/v1"
PYMOL_COMMAND_MODEL_API_KEY_ENV = "OPENAI_API_KEY"

VIEW_ANALYSIS_MODEL = "gpt-4.1"
VIEW_ANALYSIS_MODEL_API_KEY_ENV = "OPENAI_API_KEY"
VIEW_ANALYSIS_MODEL_URL = "https://api.openai.com/v1"

AGENT_MODEL = "gpt-4.1"
AGENT_MODEL_API_KEY_ENV = "OPENAI_API_KEY"
AGENT_MODEL_URL = "https://api.openai.com/v1"


def configure_model_settings():
    if "model_settings" not in st.session_state:
        st.session_state.model_settings = {
            "pymol": {
                "model": PYMOL_COMMAND_MODEL,
                "base_url": PYMOL_COMMAND_MODEL_URL,
                "api_key_env": PYMOL_COMMAND_MODEL_API_KEY_ENV,
            },
            "view": {
                "model": VIEW_ANALYSIS_MODEL,
                "base_url": VIEW_ANALYSIS_MODEL_URL,
                "api_key_env": VIEW_ANALYSIS_MODEL_API_KEY_ENV,
            },
            "agent": {
                "model": AGENT_MODEL,
                "base_url": AGENT_MODEL_URL,
                "api_key_env": AGENT_MODEL_API_KEY_ENV,
            },
        }

    cfg = st.session_state.model_settings

    with st.sidebar.expander("🔧 Model & API settings", expanded=False):
        st.markdown(
            "Configure which models and base URLs to use. "
            "These are passed directly to the OpenAI Python SDK."
        )
        st.subheader("PyMOL command model")
        cfg["pymol"]["model"] = st.text_input(
            "Model name (PyMOL commands)",
            value=cfg["pymol"]["model"],
            help="E.g. gpt-4.1, gpt-4.1-mini, etc.",
        )
        cfg["pymol"]["base_url"] = st.text_input(
            "Base URL (PyMOL commands)",
            value=cfg["pymol"]["base_url"],
            help="Default OpenAI: https://api.openai.com/v1",
        )
        cfg["pymol"]["api_key_env"] = st.text_input(
            "API key env var (PyMOL commands)",
            value=cfg["pymol"]["api_key_env"],
            help="Name of the environment variable containing the API key.",
        )

        st.markdown("---")
        st.subheader("View analysis model (vision)")
        cfg["view"]["model"] = st.text_input(
            "Model name (view analysis)",
            value=cfg["view"]["model"],
            help="E.g. gpt-4o, gpt-4.1-mini, etc.",
        )
        cfg["view"]["base_url"] = st.text_input(
            "Base URL (view analysis)",
            value=cfg["view"]["base_url"],
            help="Default OpenAI: https://api.openai.com/v1",
        )
        cfg["view"]["api_key_env"] = st.text_input(
            "API key env var (view analysis)",
            value=cfg["view"]["api_key_env"],
            help="Name of the environment variable containing the API key.",
        )

        st.markdown("---")

        st.subheader("Agent model")
        cfg["agent"]["model"] = st.text_input(
            "Model name (agent)",
            value=cfg["agent"]["model"],
            help="E.g. gpt-5.1, gpt-4.1, etc.",
        )
        cfg["agent"]["base_url"] = st.text_input(
            "Base URL (agent)",
            value=cfg["agent"]["base_url"],
            help="Default OpenAI: https://api.openai.com/v1",
        )
        cfg["agent"]["api_key_env"] = st.text_input(
            "API key env var (agent)",
            value=cfg["agent"]["api_key_env"],
            help="Name of the environment variable containing the API key.",
        )

        st.caption(
            "Changes are applied immediately for new requests. "
            "Make sure the environment variables you reference actually exist."
        )
        if st.button("Update agent model settings"):
            amv = AMV(tools=pymol_tool_schema)
            amv.register_function("ds_pymol", ds_pymol)
            amv.register_function("start_pymol", start_pymol)
            amv.register_function("run_cmd", run_cmd)
            amv.register_function("analysis_current_view", analysis_current_view)
            st.session_state.agent = amv


def _get_api_key(env_var: str) -> str:
    key = os.getenv(env_var)
    if not key:
        raise RuntimeError(
            f"Environment variable '{env_var}' is not set. "
            "Please export your API key, e.g. 'export OPENAI_API_KEY=sk-...'"
        )
    return key


def get_pymol_screenshot() -> str:
    if "ps" not in st.session_state:
        raise RuntimeError("PyMOL session is not initialized.")

    screenshot_commands = [
        "ray 600,600",
        "png screenshot.png, dpi=100",
    ]
    for command in screenshot_commands:
        st.session_state.ps.server.do(command)

    base64_image = encode_image("screenshot.png")
    return base64_image


def direct_command_generation(user_instruction: str) -> List[str]:
    cfg = st.session_state.model_settings["pymol"]

    api_key = _get_api_key(cfg["api_key_env"])
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])

    system_prompt = (
        "You are a helpful assistant for using PyMOL. "
        "Respond to the user's instructions using PyMOL command line syntax. "
        "You MUST respond as a JSON object with schema: "
        '{"commands": ["cmd1", "cmd2", ...]}. Do not include explanations.'
    )

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instruction},
        ],
        temperature=1 if cfg["model"].startswith("gpt-5") else 0.0,
        response_format={"type": "json_object"},
    )

    try:
        content = response.choices[0].message.content
        commands_data = json.loads(content or "{}")
        commands = commands_data.get("commands", [])
        if not isinstance(commands, list):
            return []
        # Ensure all commands are strings
        return [str(c) for c in commands]
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[ds_pymol] Error parsing response: {e}")
        return []


def ds_pymol(user_instruction: str) -> str:
    commands = direct_command_generation(user_instruction)
    if not commands:
        return "No valid PyMOL commands were generated."
    return "\n".join(commands)


def run_cmd(commands: List[str]) -> str:
    if "ps" not in st.session_state:
        return "PyMOL session is not initialized. Please initialize it first."

    results = []
    for command in commands:
        try:
            out = st.session_state.ps.server.do(command)
        except Exception as e:  # noqa: BLE001
            out = f"[ERROR] {e}"
        results.append({"command": command, "result": str(out)})

    # Return a concise, readable summary for the LLM
    summary_lines = ["Executed PyMOL commands:"]
    for entry in results:
        summary_lines.append(f"- {entry['command']} -> {entry['result']}")
    return "\n".join(summary_lines)


def analysis_current_view() -> str:
    base64_image = get_pymol_screenshot()
    cfg = st.session_state.model_settings["view"]
    api_key = _get_api_key(cfg["api_key_env"])
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])

    system_prompt = (
        "You are an expert in molecular visualization and scientific figure design. "
        "You will be given a PyMOL rendering as an image. "
        "Provide a concise analysis of the view and concrete suggestions to improve it "
        "toward a publication-quality figure (colors, representations, orientation, "
        "labels, background, clipping, etc.)."
    )

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analyze this PyMOL view and propose specific improvements "
                            "for a publication-quality figure."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                        },
                    },
                ],
            },
        ],
        temperature=1 if cfg["model"].startswith("gpt-5") else 0.0,
    )

    return response.choices[0].message.content or "No analysis produced."


def start_pymol():
    if "ps" not in st.session_state:
        st.session_state.ps = cm.start_pymol_gui()
    return "PyMOL started"


class AMV:
    """
    AMV: Agentic Molecular Visualization.
    """

    def __init__(self, tools: Optional[List[Dict[str, Any]]] = None):
        cfg = st.session_state.model_settings["agent"]
        api_key = _get_api_key(cfg["api_key_env"])
        self.client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
        self.model = cfg["model"]

        # Agentic mode (tools, multi-step)
        self.agentic_messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant for molecular visualization in PyMOL. "
                    "You must make a brief plan and break down the task into small steps "
                    "before issuing any tool calls.\n\n"
                    "PyMOL Molecular Visualization Best Practices:\n"
                    "- Show only essential structural elements; avoid occluding key features.\n"
                    "- Use clear, consistent representations (cartoon for proteins, sticks/"
                    "spheres for ligands).\n"
                    "- Apply logical color schemes; avoid unnecessary variation or saturation.\n"
                    "- Orient molecules to highlight relevant regions (binding sites, interfaces).\n"
                    "- Use transparency and clipping planes to reveal internal features.\n"
                    "- Label selectively and position text to avoid overlap.\n"
                    "- Maintain a clean composition (minimal clutter, neutral background, "
                    "balanced framing).\n"
                    "- Render with anti-aliasing and good lighting; ensure readability at "
                    "publication scale.\n"
                    "- Keep styles consistent across related figures for comparability.\n\n"
                    "Tool usage guidelines:\n"
                    "- Use 'ds_pymol' to generate PyMOL commands from clear, concise "
                    "instructions. Each tool call must contain only 1-3 PyMOL commands "
                    "(strings). Keep steps minimal and non-obstructive.\n"
                    "- Use 'run_cmd' to actually execute PyMOL commands.\n"
                    "- Use 'analysis_current_view' to analyze the *current* rendered view.\n\n"
                    "How to end:\n"
                    "When you believe you have completed the user's request and the view is "
                    "clean and ready for publication, respond with a short summary of what "
                    "you have done and finish your reply with this exact marker on a new "
                    "line:\n"
                    "THIS IS THE END OF ACTION"
                ),
            }
        ]

        self.tools = tools or []
        self.function_map: Dict[str, ToolFunction] = {}

    def register_function(self, name: str, fn: ToolFunction) -> None:
        self.function_map[name] = fn

    def _call_model(self, messages: List[Dict[str, Any]]):
        temperature = 1.0 if self.model.startswith("gpt-5") else 0.0
        with st.spinner("Waiting for model response..."):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                temperature=temperature,
            )
        return response.choices[0].message

    def agent(self, content: str, max_steps: int = 20) -> str:
        self.agentic_messages.append({"role": "user", "content": content})

        for step in range(max_steps):
            message = self._call_model(self.agentic_messages)

            if message.content:
                with st.chat_message(message.role):
                    st.markdown(
                        message.content.replace("THIS IS THE END OF ACTION", "")
                    )

            self.agentic_messages.append(message)

            if (
                getattr(message, "content", None)
                and "THIS IS THE END OF ACTION" in message.content
            ):
                return message.content

            if getattr(message, "tool_calls", None):
                for tool_call in message.tool_calls:
                    name = tool_call.function.name
                    raw_args = tool_call.function.arguments

                    print(
                        f"[agent step {step}] Tool call: {name} "
                        f"with args {raw_args}",
                    )

                    if isinstance(raw_args, str):
                        raw_args = raw_args.strip()
                        if raw_args:
                            try:
                                parse_args = json.loads(raw_args)
                            except json.JSONDecodeError:
                                parse_args = {}
                        else:
                            parse_args = {}
                    elif isinstance(raw_args, dict):
                        parse_args = raw_args
                    else:
                        parse_args = {}

                    if name not in self.function_map:
                        raise ValueError(
                            f"Tool '{name}' not registered in function_map."
                        )

                    python_result = self.function_map[name](**parse_args)
                    with st.sidebar.expander(f"🔧 {name}", expanded=False):
                        st.markdown(
                            f"**Arguments:**\n```json\n{json.dumps(parse_args, indent=2)}\n```\n"
                            f"**Result:**\n```\n{python_result}\n```"
                        )
                    self.agentic_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(python_result),
                        }
                    )
                continue
            if getattr(message, "content", None):
                return message.content
        last_msg = next(
            (m for m in reversed(self.agentic_messages) if m["role"] == "assistant"),
            None,
        )
        return last_msg.get("content", "") if last_msg else ""


st.set_page_config(page_title="ChatMol AMV", layout="wide")
st.sidebar.title("ChatMol Agent")
configure_model_settings()

st.sidebar.markdown(
    f"**PyMOL command model:** `{st.session_state.model_settings['pymol']['model']}`  \n"
    f"**View analysis model:** `{st.session_state.model_settings['view']['model']}`  \n"
    f"**Agent model:** `{st.session_state.model_settings['agent']['model']}`  \n"
)

st.sidebar.markdown(
    "### Test prompt\n"
    "`Highlight aromatic sidechains of 1pga and prepare to scientific publication level.`"
)

st.sidebar.markdown("---\nCurrent Tool using history")

if "agent" not in st.session_state:
    amv = AMV(tools=pymol_tool_schema)
    amv.register_function("ds_pymol", ds_pymol)
    amv.register_function("start_pymol", start_pymol)
    amv.register_function("run_cmd", run_cmd)
    amv.register_function("analysis_current_view", analysis_current_view)
    st.session_state.agent = amv

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Give instructions to the PyMOL agent…")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    agent: AMV = st.session_state.agent
    response = agent.agent(prompt)
    st.image("screenshot.png")

    cleaned_response = response.replace("THIS IS THE END OF ACTION", "")
    st.session_state.messages.append({"role": "assistant", "content": cleaned_response})

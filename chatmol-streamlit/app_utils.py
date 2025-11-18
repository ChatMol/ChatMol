import base64


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


pymol_tool_schema = [
    {
        "type": "function",
        "function": {
            "name": "ds_pymol",
            "description": "Generate PyMOL commands from user instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_instruction": {
                        "type": "string",
                        "description": "User instructions for PyMOL command generation.",
                    }
                },
                "required": ["user_instruction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analysis_current_view",
            "description": "Analyze the current PyMOL molecular visualization based on a screenshot captured from the live PyMOL session.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_pymol",
            "description": "Start PyMOL session.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_cmd",
            "description": "Execute a list of PyMOL commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commands": {
                        "type": "array",
                        "description": "List of PyMOL commands to execute.",
                        "items": {
                            "type": "string",
                            "description": "Single PyMOL command",
                        },
                    }
                },
                "required": ["commands"],
            },
        },
    },
]

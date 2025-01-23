import os
import requests
import threading
import json
import http.server

from typing import Dict, List, Optional, Literal, Union
from datetime import datetime
from pymol import cmd

class PyMOLCommandHandler(http.server.BaseHTTPRequestHandler):

    def __init__(self):

        from http import HTTPStatus
        import urllib.parse

        super().__init__()

    def _send_cors_headers(self):
        """Sets headers required for CORS"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "x-api-key,Content-Type")

    def do_OPTIONS(self):
        """Respond to a OPTIONS request."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/send_message":
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        post_data = urllib.parse.unquote(post_data.decode())

        try:
            cmd.do(post_data)
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"Command executed")
        except Exception as e:
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path == "/":
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"Hello, this is the local Pymol server.")
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

class PyMOLAgent:
    OPENAI_MODELS = {
        "gpt-4o", "gpt-4o-mini"
    }
    
    ANTHROPIC_MODELS = {
        "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-5-sonnet-20240620"
    }

    DEEPSEEK_MODELS = {
        "deepseek-chat"
    }

    def __init__(
        self,
        model: str = "gpt-4o",
        provider: Optional[Literal["openai", "anthropic", "deepseek"]] = None,
        system_message: Optional[str] = None,
    ):
        self.config_dir = os.path.expanduser("~/.PyMOL")
        self.config_file = os.path.join(self.config_dir, "config.json")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        self.model = model
        self.provider = provider or self.detect_provider(model)
        self.lite_conversation_history = ""
        self.config = self.load_config()
        self.api_key = self.get_api_key()
        
        if not self.api_key:
            Warning(f"Please set {'ANTHROPIC' if self.provider == 'anthropic' else 'OPENAI'}_API_KEY environment variable or configure it in {self.config_file}")

        self.system_message = system_message or """You are a PyMOL expert assistant, specialized in providing command line code solutions related to PyMOL. 
Generate clear and effective solutions. 
Prefer academic style visulizations.
Format your responses like this:
Place PyMOL commands in ```pymol blocks

Example response format:

```pymol
fetch 1abc
show cartoon
```
"""
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_message}
        ]
        self.api_urls = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "deepseek": "https://api.deepseek.com/chat/completions",
            "ollama": "http://localhost:11434/api/chat"
        }
        self.stashed_commands = []

    @classmethod
    def detect_provider(cls, model: str) -> str:
        """Automatically detect provider based on model name."""
        if model in cls.OPENAI_MODELS:
            return "openai"
        elif model in cls.ANTHROPIC_MODELS:
            return "anthropic"
        elif model in cls.DEEPSEEK_MODELS:
            return "deepseek"
        else:
            # Default to OpenAI if unknown model
            print(f"Warning: Unknown model '{model}'. Defaulting to OpenAI.")
            return "openai"

    def load_config(self) -> Dict[str, Union[str, Dict[str, str]]]:
        """Load configuration from JSON file."""
        default_config = {
            "api_keys": {
                "openai": "",
                "anthropic": "",
                "deepseek": "",
            }
        }
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # initialize config file
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {self.config_file}. Using default configuration.")
            self.save_config(default_config)
            return default_config

    def save_config(self, config) -> None:
        """Save configuration to JSON file."""
        # current_config = self.load_config()
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save configuration to {self.config_file}: {str(e)}")

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment or config file."""
        # env_var = f"{'ANTHROPIC' if self.provider == 'anthropic' else 'OPENAI'}_API_KEY"
        # return os.getenv(env_var) or self.config["api_keys"].get(self.provider, "")
        if self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY") or self.config["api_keys"].get(self.provider, "")
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY") or self.config["api_keys"].get(self.provider, "")
        if self.provider == "deepseek":
            return os.getenv("DEEPSEEK_API_KEY") or self.config["api_keys"].get(self.provider, "")

    def set_api_key(self, provider, api_key: str) -> None:
        """Set the API key for the current provider."""
        api_key = api_key.strip()
        self.api_key = api_key
        self.provider = provider
        
        # Update config
        self.config["api_keys"][self.provider] = api_key
        self.save_config(self.config)
        
        print(f"API key for {self.provider} set and saved successfully.")
        
        # Reload PyMOL configuration
        # cmd.reinitialize()
        # cmd.do("@~/.pymolrc")
        # cmd.do(
        #     "load https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py"
        # )

    def update_model(self, model_name: str) -> str:
        """Update the model and automatically detect provider."""
        self.model = model_name

        if model_name.split("@")[-1] == "ollama":
            self.provider = "ollama"
            self.model = model_name.split("@")[0]
            # self.base_url = "http://localhost:11434/api/chat"
            # self.base_url = "https://chatmol.org/ollama/api/chat"

            return f"Model updated to: {self.model}"
        
        new_provider = self.detect_provider(model_name)
        
        if new_provider != self.provider:
            self.provider = new_provider
            self.api_key = self.get_api_key()
            print(f"Provider switched to {new_provider}")
            
        return f"Model updated to: {self.model}"

    def get_headers(self) -> Dict[str, str]:
        """Get headers based on the current provider."""
        if self.provider == "anthropic":
            return {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        elif self.provider == "ollama":
            return {
                "Content-Type": "application/json",
            }
        else:  # openai
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

    def prepare_messages(self, message: str) -> Dict:
        """Prepare the API request payload based on provider."""
        if self.provider == "anthropic":
            # Convert conversation history to messages format
            messages = []
            
            # First add any previous messages
            for msg in self.conversation_history[1:]:  # Skip system message
                if msg["role"] in ["user", "assistant"]:  # Only include user and assistant messages
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            return {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1024,
                "system": self.system_message,
                "temperature": 0.01,
            }
        elif self.provider == "ollama":
            return {
                "model": self.model,
                "messages": self.conversation_history,
                "stream": False,
                "options": {
                    "seed": 101,
                    "temperature": 0
                }
            }
        else:  # openai
            return {
                "model": self.model,
                "messages": self.conversation_history,
                "temperature": 0.01,
            }

    def process_response(self, response_data: Dict) -> str:
        """Extract the assistant's message from the API response."""
        if self.provider == "anthropic":
            return response_data["content"][0]["text"]
        elif self.provider == "ollama":
            return response_data["message"]["content"]
        else:  # openai
            return response_data["choices"][0]["message"]["content"]

    def send_message(self, message: str, execute: bool = True) -> str:
        """Send a message and process PyMOL commands."""
        message = message.strip()

        # Handle special commands
        if message in ["e", "execute"]:
            return self.execute_stashed_commands()
        elif message == "new":
            return self.reset_conversation()

        # Set execution mode based on message ending with '?'
        if message.endswith("?"):
            execute = False

        # Add user message to history
        self.add_message("user", message)

        # Prepare and send API request
        payload = self.prepare_messages(message)
        
        try:
            response = requests.post(
                self.api_urls[self.provider],
                headers=self.get_headers(),
                json=payload
            )
            response.raise_for_status()

            # Parse response
            assistant_message = self.process_response(response.json())

            # Add assistant's response to history
            self.add_message("assistant", assistant_message)

            # Process PyMOL commands
            self.process_pymol_commands(assistant_message, execute)
            
            print("====================================")
            print("User:", message)
            print("Assistant:", assistant_message)
            print("====================================")
            return assistant_message

        except requests.exceptions.RequestException as e:
            error_msg = f"API call failed: {str(e)}"
            print(error_msg)
            return error_msg

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def reset_conversation(self) -> str:
        """Reset the conversation history."""
        self.conversation_history = [
            {"role": "system", "content": self.system_message}
        ]
        return "Conversation reset."
    
    def process_pymol_commands(self, response: str, execute: bool) -> None:
        """Extract and process PyMOL commands from the response."""
        try:
            self.stashed_commands.clear()  # Clear previous commands
            command_blocks = []

            # Extract command blocks
            for i, block in enumerate(response.split("```")):
                if i % 2 == 1:
                    command_blocks.append(block)

            # Process each command block
            for command_block in command_blocks:
                for command in command_block.split("\n"):
                    command = command.strip()
                    if (
                        command
                        and not command.startswith("#")
                        and command != "python"
                        and command != "pymol"
                    ):
                        # Handle inline comments
                        if "#" in command:
                            command = command[: command.index("#")].strip()

                        if execute:
                            print(f"{command}")
                            cmd.do(command)
                        else:
                            self.stashed_commands.append(command)

        except Exception as e:
            print(f"Error processing PyMOL commands: {e}")

    def execute_stashed_commands(self) -> str:
        """Execute all stashed commands."""
        if not self.stashed_commands:
            return "There are no stashed commands"

        for command in self.stashed_commands:
            print(f"Executing: {command}")
            cmd.do(command)

        self.stashed_commands.clear()
        return "Executed all stashed commands"

    def reset_conversation(self) -> str:
        """Reset the conversation history and stashed commands."""
        self.conversation_history = [
            self.conversation_history[0]
        ]  # Keep system message
        self.stashed_commands.clear()
        return "Conversation and command history cleared"

    def save_conversation(self, filename: str = None) -> None:
        """Save the conversation history to a file."""
        if filename is None:
            filename = (
                f"pymol_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "conversation": self.conversation_history,
                    "stashed_commands": self.stashed_commands,
                },
                f,
                indent=2,
            )

    def load_conversation(self, filename: str) -> None:
        """Load a conversation history from a file."""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.conversation_history = data["conversation"]
            self.stashed_commands = data["stashed_commands"]

    def query_qaserver(self, question: str) -> str:
        """Query the ChatMol-Lite server."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "question=" + question.replace('"', "")
        response = requests.post(
            "https://chatmol.org/qa/lite/", headers=headers, data=data
        )
        return response.text

    def chatlite(self, question: str) -> None:
        """Process a question using ChatMol-Lite."""
        question = self.lite_conversation_history + "Instructions: " + question
        answer = self.query_qaserver(question)
        data = json.loads(answer)

        self.lite_conversation_history = data["conversation_history"]
        self.lite_conversation_history += "\nAnswer: "
        self.lite_conversation_history += data["answer"]
        self.lite_conversation_history += "\n"

        commands = data["answer"].split("\n")
        for command in commands:
            if command == "" or command.startswith("#") or command.startswith("```"):
                continue
            else:
                cmd.do(command)
        print("====================================")
        print("ChatMol-Lite:")
        for command in commands:
            if command == "":
                continue
            else:
                print(command)
        print("====================================")


def start_server():
    httpd = http.server.HTTPServer(("localhost", 8101), PyMOLCommandHandler)
    httpd.serve_forever()


def init_server():
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    print("Server started")

pymol_assistant = PyMOLAgent()

cmd.extend("set_api_key", pymol_assistant.set_api_key)
cmd.extend("chat", pymol_assistant.send_message)
cmd.extend("chatlite", pymol_assistant.chatlite)
cmd.extend("update_model", pymol_assistant.update_model)
cmd.extend("init_server", init_server)


cmd.extend("save_conversation", pymol_assistant.save_conversation)
cmd.extend("load_conversation", pymol_assistant.load_conversation)
cmd.extend("execute_stashed_commands", pymol_assistant.execute_stashed_commands)
cmd.extend("reset_conversation", pymol_assistant.reset_conversation)
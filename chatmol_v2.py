import os
import requests
import threading
import json
import http.server

from typing import List, Dict, Optional
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
    def __init__(
        self,
        model: str = "gpt-4o",
        system_message: Optional[str] = None,
        # max_history: int = 100,
        # command_timeout: int = 30
    ):
        self.local_api_file = os.path.expanduser("~") + "/.PyMOL/apikey.txt"
        self.api_key = self.load_api_key()
        if not self.api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")

        self.model = model
        self.system_message = system_message
        self.lite_conversation_history = ""
        self.system_message = """You are a PyMOL expert assistant, specialized in providing command line code solutions related to PyMOL. 
Generate clear and effective solutions. 
Prefer academic style visulizations.
Format your responses like this:
Place PyMOL commands in ```pymol blocksxw

Example response format:

```
fetch 1abc
show cartoon
```
"""

        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_message}
        ]
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.stashed_commands = []

    def load_api_key(self) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                with open(self.local_api_file, "r") as api_key_file:
                    api_key = api_key_file.read().strip()
                    print("API key loaded from file.")
            except FileNotFoundError:
                print(
                    "API key file not found. Please set your API key using 'set_api_key your_api_key_here' command"
                    + f" or by environment variable `OPENAI_KEY_ENV`."
                )
        return api_key

    def set_api_key(self, api_key: str) -> None:
        """Set the OpenAI API key."""
        api_key = api_key.strip()
        print("APIKEYFILE = ", self.local_api_file)
        try:
            with open(self.local_api_file, "w+") as api_key_file:
                api_key_file.write(api_key)
            print("API key set and saved to file successfully.")
        except:
            print(
                "API key set successfully but could not be saved to file. You may need to reset the API key next time."
            )
        cmd.reinitialize()
        cmd.do("@~/.pymolrc")
        cmd.do(
            "load https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py"
        )

    def update_model(self, model_name: str) -> str:
        """Update the GPT model used by the assistant."""
        self.model = model_name
        return f"Model updated to: {self.model}"

    def get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def send_message(self, message: str, execute: bool = True) -> str:
        """Send a message and process PyMOL commands from the response."""
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

        # Prepare the API request
        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "temperature": 0.01,
        }

        try:
            # Make API call
            response = requests.post(
                self.api_url, headers=self.get_headers(), json=payload
            )
            response.raise_for_status()

            # Parse response
            response_data = response.json()
            assistant_message = response_data["choices"][0]["message"]["content"]

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

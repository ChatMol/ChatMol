import os
from openai import OpenAI
import threading
import requests
import json
from pymol import cmd
import http.server

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

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        post_data = urllib.parse.unquote(post_data.decode())
        
        try:
            cmd.do(post_data)
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Command executed')
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
            self.wfile.write(b'Hello, this is the local Pymol server.')
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

def start_server():
    httpd = http.server.HTTPServer(('localhost', 8101), PyMOLCommandHandler)
    httpd.serve_forever()

def init_server():
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    print("Server started")

conversation_history = ""
lite_conversation_history = "" 
stashed_commands = []

# Save API Key in ~/.PyMOL/apikey.txt
API_KEY_FILE = os.path.expanduser('~')+"/.PyMOL/apikey.txt"
OPENAI_KEY_ENV = "OPENAI_API_KEY"
GPT_MODEL = "gpt-4o"
client = None

def set_api_key(api_key):
    api_key = api_key.strip()
    print("APIKEYFILE = ",API_KEY_FILE)
    try:
        with open(API_KEY_FILE, "w") as api_key_file:
            api_key_file.write(api_key)
        print("API key set and saved to file successfully.")
    except:
        print("API key set successfully but could not be saved to file. You may need to reset the API key next time.")
    cmd.reinitialize()
    cmd.do("@~/.pymolrc")
    cmd.do("load https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py")

def load_api_key():
    api_key = os.getenv(OPENAI_KEY_ENV)
    if not api_key:
        try:
            with open(API_KEY_FILE, "r") as api_key_file:
                api_key = api_key_file.read().strip()
                client = OpenAI(api_key=api_key)
                print("API key loaded from file.")
        except FileNotFoundError:
            print("API key file not found. Please set your API key using 'set_api_key your_api_key_here' command" +
                  f" or by environment variable '{OPENAI_KEY_ENV}'.")
            client = None
    else:
        client = OpenAI(api_key=api_key)
        print("API key loaded from environment variable.")
    return client

def update_model(mdoel_name):
    global GPT_MODEL
    GPT_MODEL = mdoel_name
    print("Model updated to: ", GPT_MODEL)
    return "Model updated to: " + GPT_MODEL

def chat_with_gpt(message, max_history=10):
    global conversation_history

    conversation_history += f"User: {message}\nChatGPT:"

    try:
        messages = [
            {"role": "system", "content": "You are an AI language model specialized in providing command line code solutions related to PyMOL. Generate clear and effective solutions in a continuous manner. When providing demos or examples, try to use 'fetch' if object name is not provided. Prefer academic style visulizations. Code within triple backticks, comment and code should not in the same line."}
        ]

        # Keep only the max_history latest exchanges to avoid making the conversation too long
        message_parts = conversation_history.strip().split("\n")[-2 * max_history:]
        
        for i, part in enumerate(message_parts):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": part})

        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            max_tokens=256,
            n=1,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip()

        conversation_history += f"{answer}\n"

        return answer
    except Exception as e:
        print(f"Error: {e}")
        return ""

def query_qaserver(question):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = 'question=' + question.replace('"','')

    response = requests.post('https://chatmol.org/qa/lite/', headers=headers, data=data)
    return response.text

def chatlite(question):
    global lite_conversation_history
    question = lite_conversation_history + "Instructions: " + question
    answer = query_qaserver(question)
    data = json.loads(answer)
    lite_conversation_history = data['conversation_history']
    lite_conversation_history += "\nAnswer: "
    lite_conversation_history += data['answer']
    lite_conversation_history += "\n"
    commands = data['answer']
    commands = commands.split('\n')
    for command in commands:
        if command == '':
            continue
        else:
            cmd.do(command)
    print("Answers from ChatMol-Lite: ")
    for command in commands:
        if command == '':
            continue
        else:
            print(command)


def start_chatgpt_cmd(message, execute:bool=True, lite:bool=False):
    if lite == True:
        chatlite(message)
        return 0
    global stashed_commands
    global conversation_history

    message = message.strip()
    if message.strip() == "e" or message.strip() == 'execute' :
        if (len(stashed_commands) == 0):
            print("There is no stashed commands")
        for command in stashed_commands:
            cmd.do(command)
        # clear stash
        stashed_commands.clear()
        return 0
    
    if message.strip() == "new":
        # clear conversation history and stash
        conversation_history = ""
        stashed_commands.clear()
        return 0
    
    if (message[-1] == '?'):
        execute = False
    response = chat_with_gpt(message)
    print("ChatGPT: " + response.strip())

    try:
        command_blocks = []
        # I think it would be better to reset stashed_commands to empty for each chat.
        # Stash should only keep commands of last conversation, not all commands of the whole history
        stashed_commands.clear()
        for i, block in enumerate(response.split("```")):
            if i%2 == 1:
                command_blocks.append(block)
        for command_block in command_blocks:
            for command in command_block.split("\n"):
                if command.strip() != "" and not command.strip().startswith("#"):
                    # Should skip "python", otherwise, not action will be displayed in 3D window
                    if (command.strip() == "python"):
                        continue
                    if "#" in command:
                        index_ = command.index("#")
                        if execute:
                            print(command[:index_])
                            cmd.do(command[:index_])
                        else:
                            stashed_commands.append(command[:index_])
                    else:
                        if execute:
                            print(command)
                            cmd.do(command)
                        else:
                            stashed_commands.append(command)

    except Exception as e:
        print(f"Error command execution code: {e}")


client = load_api_key()

cmd.extend("set_api_key", set_api_key)
cmd.extend("chat", start_chatgpt_cmd)
cmd.extend("chatlite", chatlite)
cmd.extend("update_model", update_model)
cmd.extend("init_server", init_server)
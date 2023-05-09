import os
import time
import openai
import socket
import threading
from pymol import cmd


conversation_history = " "    
stashed_commands = []

# Save API Key in ~/.PyMOL/apikey.txt
API_KEY_FILE = os.path.expanduser('~')+"/.PyMOL/apikey.txt"
OPENAI_KEY_ENV = "OPENAI_API_KEY"

def handle_client(client_socket, client_address):
    print(f"Connection from {client_address} established.")
    message = client_socket.recv(1024).decode('utf-8')
    print(f"Received message: {message}")
    client_socket.close()
    cmd.do(message)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8100))
    server_socket.listen(1)
    print("Server is listening on port 8100...")

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

def start_listener():
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

def set_api_key(api_key):
    api_key = api_key.strip()
    openai.api_key = api_key
    print("APIKEYFILE = ",API_KEY_FILE)
    try:
        with open(API_KEY_FILE, "w") as api_key_file:
            api_key_file.write(api_key)
        print("API key set and saved to file successfully.")
    except:
        print("API key set successfully but could not be saved to file. You may need to reset the API key next time.")

def load_api_key():
    api_key = os.getenv(OPENAI_KEY_ENV)
    print("APIKEYFILE = ",API_KEY_FILE)
    if not api_key:
        try:
            with open(API_KEY_FILE, "r") as api_key_file:
                api_key = api_key_file.read().strip()
                openai.api_key = api_key
                print("API key loaded from file.")
        except FileNotFoundError:
            print("API key file not found. Please set your API key using 'set_api_key your_api_key_here' command" +
                  f" or by environment variable '{OPENAI_KEY_ENV}'.")

load_api_key()
start_listener()


def chat_with_gpt(message):
    global conversation_history

    conversation_history += f"User: {message}\nChatGPT:"

    try:
        messages = [
    {"role": "system", "content": "You are an AI language model specialized in providing command line code solutions related to PyMOL. Generate clear and effective solutions in a continuous manner. When providing demos or examples, try to use 'fetch' if object name is not provided. Prefer academic style visulizations. Code within triple backticks, comment and code should not in the same line."}
]
        message_parts = conversation_history.strip().split("\n")
        for i, part in enumerate(message_parts):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": part})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1024,
            n=1,
            temperature=0,
        )
        answer = response.choices[0].message['content'].strip()

        conversation_history += f"{answer}\n"

        return answer
    except Exception as e:
        print(f"Error: {e}")
        return ""

def start_chatgpt_cmd(message, execute:bool=True, lite:bool=True):
    if lite == True:
        from chatmol_lit import chatlit
        chatlit(message)
        return 0
    global stashed_commands
    global conversation_history

    message = message.strip()
    execution = True
    if (message[-1] == '?'):
        execution = False
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
        conversation_history = " "
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

cmd.extend("set_api_key", set_api_key)
cmd.extend("chat", start_chatgpt_cmd)



from pymol import cmd

import openai
import os

conversation_history = " "    
stashed_commands = []

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_FILE = os.path.join(PLUGIN_DIR, "apikey.txt")
OPENAI_KEY_ENV = "OPENAI_API_KEY"

def set_api_key(api_key):
    api_key = api_key.strip()
    openai.api_key = api_key
    try:
        with open(API_KEY_FILE, "w") as api_key_file:
            api_key_file.write(api_key)
        print("API key set and saved to file successfully.")
    except:
        print("API key set successfully but could not be saved to file. You may need to reset the API key next time.")

def load_api_key():
    api_key = os.getenv(OPENAI_KEY_ENV)
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
            temperature=0.1,
        )
        answer = response.choices[0].message['content'].strip()

        conversation_history += f"{answer}\n"

        return answer
    except Exception as e:
        print(f"Error: {e}")
        return ""

def start_chatgpt_cmd(message, execute:bool=True):
    global stashed_commands
    if message.strip() == "e":
        for command in stashed_commands:
            cmd.do(command)
        return 0
    if execute.lower() == "false":
        execute = False
    response = chat_with_gpt(message)
    print("ChatGPT: " + response.strip())

    try:
        command_blocks = []
        for i, block in enumerate(response.split("```")):
            if i%2 == 1:
                command_blocks.append(block)
        for command_block in command_blocks:
            for command in command_block.split("\n"):
                if command.strip() != "" and not command.strip().startswith("#"):
                    # print(f"Executing code: {command}")
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
        print(f"Error executing code: {e}")


cmd.extend("set_api_key", set_api_key)
cmd.extend("chat", start_chatgpt_cmd)



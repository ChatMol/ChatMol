from pymol import cmd

import openai
import os

conversation_history = " "    

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_FILE = os.path.join(PLUGIN_DIR, "apikey.txt")
OPENAI_KEY_ENV = "OPENAI_API_KEY"

def set_api_key(api_key):
    api_key = api_key.strip()
    openai.api_key = api_key
    with open(API_KEY_FILE, "w") as api_key_file:
        api_key_file.write(api_key)
    print("API key set and saved to file successfully.")

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
    {"role": "system", "content": "You are an AI language model specialized in providing code solutions related to PyMOL. Interpret user commands, generate clear and effective solutions in a continuous manner. Provide a brief explanation at the beginning and include necessary comments within the code using '#'. When providing demos or examples, try to use 'fetch' whenever possible. Prefer academic style visulizations. academic style, code within triple backticks."}
]
        message_parts = conversation_history.strip().split("\n")
        for i, part in enumerate(message_parts):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": part})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            n=1,
            temperature=0.1,
        )
        answer = response.choices[0].message['content'].strip()

        conversation_history += f"{answer}\n"

        return answer
    except Exception as e:
        print(f"Error: {e}")
        return ""

def start_chatgpt_cmd(message):
    response = chat_with_gpt(message)
    print("ChatGPT: " + response.strip())

def start_chatgpt_cmd(message, execute_code=False):
    response = chat_with_gpt(message)
    print("ChatGPT: " + response.strip())

    if execute_code:
        try:
            # print(response.split("```")[1])
            commands = response.split("```")[1].split("\n")[1:]
            for command in commands:
                if command.strip() != "" and not command.strip().startswith("#"):
                    print(f"Executing code: {command}")
                    # cmd.
                    cmd.do(command)
            
            print("Executed code successfully.")
        except Exception as e:
            print(f"Error executing code: {e}")


cmd.extend("set_api_key", set_api_key)
cmd.extend("chatgpt", start_chatgpt_cmd)



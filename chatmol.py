from pymol import cmd

import openai
import os

conversation_history = " "    

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_FILE = os.path.join(PLUGIN_DIR, "apikey.txt")

def set_api_key(api_key):
    api_key = api_key.strip()
    openai.api_key = api_key
    with open(API_KEY_FILE, "w") as api_key_file:
        api_key_file.write(api_key)
    print("API key set and saved to file successfully.")

def load_api_key():
    try:
        with open(API_KEY_FILE, "r") as api_key_file:
            api_key = api_key_file.read().strip()
            openai.api_key = api_key
            print("API key loaded from file.")
    except FileNotFoundError:
        print("API key file not found. Please set your API key using 'set_api_key your_api_key_here' command.")

load_api_key()

def chat_with_gpt(message):
    global conversation_history

    conversation_history += f"User: {message}\nChatGPT:"

    try:
        messages = [
            {"role": "system", "content": "Pymol, commands, simple,"}
        ]

        message_parts = conversation_history.strip().split("\n")
        for i, part in enumerate(message_parts):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": part})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=5000,
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

cmd.extend("set_api_key", set_api_key)
cmd.extend("chatgpt", start_chatgpt_cmd)


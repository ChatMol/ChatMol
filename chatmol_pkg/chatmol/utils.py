import os
import requests
import json
from openai import OpenAI
import anthropic

class ChatMol:
    def __init__(self,
                api_key=None, 
                verbose=False,
                gpt_model="gpt-3.5-turbo-1106",
                chatgpt_max_history=10,
                chatgpt_temp=0,
                chatgpt_max_tokens=256,
                claude_model="claude-3-opus-20240229",
                in_pymol=False
                ):
        self.in_pymol = in_pymol
        if in_pymol:
            # self.API_KEY_FILE = os.path.expanduser('~')+"/.PyMOL/apikey.txt"
            # from pymol import cmd
            self.stashed_commands = []
        self.API_KEY_FILE = os.path.expanduser('~')+"/.cache/chatmol/apikey.txt"
        # self.client_anthropic = anthropic.Anthropic(api_key="my_api_key")
        # self.OPENAI_KEY_ENV = "OPENAI_API_KEY"
        # self.api_key = api_key or self.load_api_key()
        # self.client = OpenAI(api_key=self.api_key)
        self.init_clients()
        self.lite_conversation_history = ""
        self.chatgpt_conversation_history = []
        self.claude_conversation_messages = []
        self.chatgpt_sys_prompt = "You are an AI language model specialized in providing PyMOL command line code solutions. "
        "Generate clear and effective solutions in a continuous manner. When providing demos or examples, try to use 'fetch' if object name is not provided. "
        "Prefer academic style visulizations. Code within triple backticks, comment and code should not in the same line."
        "Keep the response short, accurate, and concise."
        self.chatgpt_max_history = chatgpt_max_history
        self.gpt_model = gpt_model
        self.claude_model = claude_model
        self.chatgpt_temp = chatgpt_temp
        self.chatgpt_max_tokens = chatgpt_max_tokens
        self.verbose = False

    def set_api_key(self, api_key):
        api_key = api_key.strip()
        os.makedirs(os.path.dirname(self.API_KEY_FILE), exist_ok=True)
        try:
            with open(self.API_KEY_FILE, "w") as api_key_file:
                api_key_file.write(api_key)
            print("API key set and saved to file successfully.")
        except Exception as e:
            print(f"API key set successfully but could not be saved to file due to: {e}. You may need to reset the API key next time.")
    
    def load_api_key(self):
        api_key = os.getenv(self.OPENAI_KEY_ENV)
        if api_key:
            print("API key loaded from environment variable.")
            return api_key
        
        try:
            with open(self.API_KEY_FILE, "r") as api_key_file:
                api_key = api_key_file.read().strip()
                print("API key loaded from file.")
                return api_key
        except FileNotFoundError:
            print("API key file not found. Please set your API key using 'set_api_key' method or by environment variable.")
            return None

    def init_clients(self):
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.client_anthropic = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        else:
            Warning("ANTHROPIC_API_KEY environment variable not found.")
        if os.environ.get("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            Warning("OPENAI_API_KEY environment variable not found.")

    def query_qaserver(self, question):
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        question = self.lite_conversation_history + "Instructions: " + question
        data = 'question=' + question.replace('"','')

        try:
            response = requests.post('https://chatmol.org/qa/lite/', headers=headers, data=data)
            if response.status_code == 200:
                data = json.loads(response.text)
                self.lite_conversation_history = data['conversation_history']
                self.lite_conversation_history += "\nAnswer: "
                self.lite_conversation_history += data['answer']
                self.lite_conversation_history += "\n"
                return data['answer']
            else:
                print(f"Failed to query server: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error querying server: {e}")
            return None

    def chatlite(self, question):
        answer = self.query_qaserver(question)
        if answer is not None:
            if self.verbose:
                print("Answers from ChatMol-Lite: ")
                print(answer)
            return answer
        else:
            if self.verbose:
                print("No response received.")
            return None

    def chat_with_gpt(self, message):
        self.chatgpt_conversation_history.append(
            {"role": "user", "content": message}
        )

        try:
            messages = [
                {"role": "system", "content": self.chatgpt_sys_prompt},
            ]            
            for message in self.chatgpt_conversation_history[-self.chatgpt_max_history:]:
                messages.append(message)
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=messages,
                max_tokens=self.chatgpt_max_tokens,
                n=1,
                temperature=self.chatgpt_temp,
            )
            answer = response.choices[0].message.content.strip()

            self.chatgpt_conversation_history.append(
                {"role": "assistant", "content": answer}
            )

            return answer
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def chat_with_claude(self, message):
        try:
            self.claude_conversation_messages.append({"role": "user", "content": message})
            messages = []
            for message in self.claude_conversation_messages[-self.chatgpt_max_history:]:
                messages.append(message)
            response = self.client_anthropic.messages.create(
                model=self.claude_model,
                system=self.chatgpt_sys_prompt,
                max_tokens=self.chatgpt_max_tokens,
                messages=messages,
                temperature=self.chatgpt_temp
            )
            answer = response.content[0].text
            if self.verbose:
                print(f"Answers from Claude: {answer}")
            self.claude_conversation_messages.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            print(f"Error: {e}")
            return ""

    def clear_stashed_commands(self):
        self.stashed_commands = []

    def clear_chat_history(self):
        self.lite_conversation_history = ""
        self.chatgpt_conversation_history = []
        self.claude_conversation_messages = []
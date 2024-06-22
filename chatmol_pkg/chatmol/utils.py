import os
import requests
import json
from openai import OpenAI
import anthropic

class ChatMol:
    def __init__(self,
                openai_api_key=None, 
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
            self.stashed_commands = []
        self.API_KEY_FILE = os.path.expanduser('~')+"/.cache/chatmol/apikey.json"
        self.OPENAI_KEY_ENV = "OPENAI_API_KEY"
        self.client = None
        self.client_anthropic = None
        self.warnings = []
        self.init_clients()
        self.lite_conversation_history = ""
        self.chatgpt_conversation_history = []
        self.claude_conversation_messages = []
        self.chatgpt_sys_prompt = "You are an expert familiar with PyMOL and specialized in providing PyMOL command line code solutions accuratly, and concisely. "
        self.chatgpt_sys_prompt += "When providing demos or examples, try to use 'fetch' if object name is not provided. "
        self.chatgpt_sys_prompt += "Prefer academic style visulizations. Code within triple backticks, comment and code should not in the same line."

        self.chatgpt_max_history = chatgpt_max_history
        self.gpt_model = gpt_model
        self.claude_model = claude_model
        self.chatgpt_temp = chatgpt_temp
        self.chatgpt_max_tokens = chatgpt_max_tokens
        self.verbose = False

    def set_api_key(self, name, api_key):
        current_api_keys = {}
        if os.path.exists(self.API_KEY_FILE):
            with open(self.API_KEY_FILE, "r") as api_key_file:
                current_api_keys = json.load(api_key_file)
        if name in ["openai", "anthropic"]:
            current_api_keys[name] = api_key
            os.makedirs(os.path.dirname(self.API_KEY_FILE), exist_ok=True)
            with open(self.API_KEY_FILE, "w") as api_key_file:
                json.dump(current_api_keys, api_key_file)
        else:
            Warning("API key name must be either 'openai' or 'anthropic'.")
            return None
            
    def load_api_key(self, name):
        try:
            with open(self.API_KEY_FILE, "r") as api_key_file:
                api_keys = json.load(api_key_file)
                if api_keys.get(name):
                    print(f"API key loaded from file for {name}.")
                    return api_keys[name]
                else:
                    print(f"API key not found in file for {name}.")
                    return None
        except FileNotFoundError:
            print("API key file not found. Please set your API key using 'set_api_key' method or by environment variable.")
            return None
        
    def test_api_access(self):
        test_result = {}
        if self.client_anthropic is not None:
            try:
                response = self.client_anthropic.messages.create(
                    model=self.claude_model,
                    system=self.chatgpt_sys_prompt,
                    max_tokens=self.chatgpt_max_tokens,
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=self.chatgpt_temp
                )
                print(f"Anthropic API access test successful: {response}")
                test_result["anthropic_failure"] = False
            except Exception as e:
                print(f"Anthropic API access test failed: {e}")
                test_result["anthropic_failure"] = f"Error: {e}"
        if self.client is not None:
            try:
                response = self.client.chat.completions.create(
                    model=self.gpt_model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=self.chatgpt_max_tokens,
                    temperature=self.chatgpt_temp
                )
                print(f"OpenAI API access test successful: {response}")
                test_result["openai_failure"] = False
            except Exception as e:
                print(f"OpenAI API access test failed: {e}")
                test_result["openai_failure"] = f"Error: {e}"
        return test_result


    def init_clients(self):
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.client_anthropic = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        elif api_key := self.load_api_key("anthropic") != "":
            self.client_anthropic = anthropic.Anthropic(api_key=api_key)
        else:
            Warning("ANTHROPIC_API_KEY environment variable not found.")
            self.warnings.append("ANTHROPIC_API_KEY environment variable not found.")
            self.client_anthropic = None
        if os.environ.get("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif api_key := self.load_api_key("openai") != "":
            self.client = OpenAI(api_key=api_key)
        else:
            Warning("OPENAI_API_KEY environment variable not found.")
            self.warnings.append("OPENAI_API_KEY environment variable not found.")
            self.client = None

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
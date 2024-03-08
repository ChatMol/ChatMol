import subprocess
from xmlrpc import client
from .utils import ChatMol

class PymolServer():
    def __init__(self, default_client:ChatMol):
        self.cm = default_client
        self.start_pymol()

    def start_pymol(self):
        # os.system("nohup pymol -R /dev/null 2>&1")
        subprocess.Popen(["pymol", "-R"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.server = client.ServerProxy(uri="http://localhost:9123/RPC2")
        return 0

    def chatlite(self, question):
        answer = self.cm.chatlite(question)
        commands = answer.split('\n')
        print("Answers from ChatMol-Lite: ")
        for command in commands:
            if command == '':
                continue
            else:
                print(command)
                self.server.do(command)
        return commands

    def chatgpt(self, message, execute:bool=True, lite:bool=False):
        if lite:
            self.cm.chatlite(message)
        message = message.strip()
        if message == "e" or message == 'execute':
            if len(self.cm.stashed_commands) == 0:
                print("There is no stashed commands")
            else:
                for command in stashed_commands:
                    self.server.do(command)
                self.cm.clear_stashed_commands()
            return 0
        
        if message == "new":
            self.cm.clear_chat_history()
            self.cm.clear_stashed_commands()
            return 0
        
        if message.endswith('?'):
            execute = False
        
        response = self.cm.chat_with_gpt(message)  # Using the chat_with_gpt method
        print("ChatGPT:", response)

        try:
            command_blocks = []
            self.cm.clear_stashed_commands()
            for i, block in enumerate(response.split("```")):
                if i % 2 == 1:
                    command_blocks.append(block)
            for command_block in command_blocks:
                for command in command_block.split("\n"):
                    if command.strip() and not command.strip().startswith("#"):
                        if command.strip() == "python" or command.strip() == "bash":
                            continue  # Skipping python commands
                        if "#" in command:
                            command, comment = command.split("#")
                        if execute:
                            print(command)
                            self.server.do(command)
                        else:
                            self.cm.stashed_commands.append(command)
        except Exception as e:
            print(f"Error during command execution: {e}")

    def claude(self, message, execute:bool=True):
        message = message.strip()
        if message == "e" or message == 'execute':
            if len(self.cm.stashed_commands) == 0:
                print("There is no stashed commands")
            else:
                for command in stashed_commands:
                    self.server.do(command)
                self.cm.clear_stashed_commands()
            return 0
        
        if message == "new":
            self.cm.clear_chat_history()
            self.cm.clear_stashed_commands()
            return 0
        
        if message.endswith('?'):
            execute = False
        
        response = self.cm.chat_with_claude(message)  # Using the chat_with_gpt method
        print(self.cm.claude_model, response)

        try:
            command_blocks = []
            self.cm.clear_stashed_commands()
            for i, block in enumerate(response.split("```")):
                if i % 2 == 1:
                    command_blocks.append(block)
            for command_block in command_blocks:
                for command in command_block.split("\n"):
                    if command.strip() and not command.strip().startswith("#"):
                        if command.strip() == "python" or command.strip() == "bash":
                            continue  # Skipping python commands
                        if "#" in command:
                            command, comment = command.split("#")
                        if execute:
                            print(command)
                            self.server.do(command)
                        else:
                            self.cm.stashed_commands.append(command)
        except Exception as e:
            print(f"Error during command execution: {e}")
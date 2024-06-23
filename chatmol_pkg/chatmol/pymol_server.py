import subprocess, threading
from xmlrpc import client
from .utils import ChatMol

class PymolServer():
    def __init__(self, default_client:ChatMol):
        self.cm = default_client
        self.pymol_console = ""

    def start_pymol(self, pymol_path='pymol'):
        """
        Starts PyMOL using a subprocess and captures its stdout in a non-blocking way.
        
        Args:
        pymol_path (str): Path to the PyMOL executable. Default is 'pymol'.
        """
        # Start PyMOL as a subprocess
        self.pymol_process = subprocess.Popen(
            "pymol -R",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            bufsize=1,  # Line-buffered
            universal_newlines=True
        )
        self.server = client.ServerProxy(uri="http://localhost:9123/RPC2")

        # Check if the process has started correctly
        if self.pymol_process.stdout is None:
            print("Failed to start PyMOL process.")
            return 

        # Start a thread to listen to the output
        self.stdout_thread = threading.Thread(target=self.get_stdout)
        self.stdout_thread.start()

    def get_stdout(self):
        """
        Prints the stdout of the PyMol subprocess continuously.
        """
        # This function runs in a separate thread
        if self.pymol_process is not None:
            while True:
                output = self.pymol_process.stdout.readline()
                if output == '' and self.pymol_process.poll() is not None:
                    break
                if output:
                    self.pymol_console += output.strip()
                    # print(output.strip())
            self.pymol_process.stdout.close()

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
        return answer

    def chatgpt(self, message, execute:bool=True, lite:bool=False):
        if lite:
            self.cm.chatlite(message)
        message = message.strip()
        if message == "e" or message == 'execute':
            if len(self.cm.stashed_commands) == 0:
                print("There is no stashed commands")
            else:
                for command in self.cm.stashed_commands:
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
        return response

    def claude(self, message, execute:bool=True):
        message = message.strip()
        if message == "e" or message == 'execute':
            if len(self.cm.stashed_commands) == 0:
                print("There is no stashed commands")
            else:
                for command in self.cm.stashed_commands:
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
        return response
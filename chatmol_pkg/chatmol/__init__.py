from .utils import ChatMol
from .pymol_server import PymolServer

defaul_client = ChatMol()

def chatlite(question):
    return defaul_client.chatlite(question)

def chat_with_gpt(message):
    return defaul_client.chat_with_gpt(message)

def chat_with_claude(message):
    return defaul_client.chat_with_claude(message)

def clear_stashed_commands():
    return defaul_client.clear_stashed_commands()

def clear_chat_history():
    return defaul_client.clear_chat_history()

def start_pymol_gui():
    pymolserver = PymolServer(defaul_client)
    pymolserver.start_pymol()
    return pymolserver

def warnings():
    return defaul_client.warnings

import tkinter as tk
from tkinter import ttk
import requests
import json
import subprocess
import threading

lite_conversation_history = ""


def launch_pymol():
    """start a new process to launch PyMOL
    Only tested on MacOS, may be different on other OS
    """
    process = subprocess.Popen(["pymol", "pymol_server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Error occurred while launching PyMOL: {stderr}")
    else:
        print(stdout)

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
    print("Answers from ChatMol-Lite: ")
    for command in commands:
        if command == '':
            continue
        else:
            print(command)
    return commands

def send_message():
    message = entry.get()
    chat.config(state='normal')
    chat.insert(tk.END, "You: " + message + "\n")
    response = chatlite(message)
    chat.insert(tk.END, "ChatMol-Lite: " + '\n'.join(response) + "\n")
    #chat.config(state='disabled')
    #script.insert(tk.END, '\n'.join(response) + "\n")
    entry.delete(0, tk.END)

def send_response_to_server():
    conversation = chat.get("1.0", "end-1c")
    index = conversation.rindex('ChatMol-Lite')
    command = ""
    if (index):
       command = conversation[index+14:]
       print("command", command)
    response = requests.post('http://localhost:8101/send_message', data=command)
    if response.status_code == 200:
        print('Command sent to server successfully.')
    else:
        print(f'Failed to send command to server. Status code: {response.status_code}')


# GUI code
window = tk.Tk()
window.title("ChatMol-Lite")

# Create the main container
frame = ttk.Frame(window, padding="10 10 10 10")
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)
frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=3)  # Make the right panel take up more space

# left 
left_frame = ttk.Frame(frame, padding="10 10 10 10")
left_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create the chat box in the left container
chat = tk.Text(left_frame, state='normal')
chat.pack(fill='both', expand=True)

# Create the entry box in the left container
entry = tk.Entry(left_frame)
entry.pack(fill='x')

# Create the send button in the left container
send_button = ttk.Button(left_frame, text="Send to PyMOL", command=send_response_to_server)
send_button.pack(fill='x')
entry.bind('<Return>', lambda event: send_message())

# Launch PyMOL in a separate thread
if __name__ == "__main__":
    pymol_thread = threading.Thread(target=launch_pymol)
    pymol_thread.start()

if __name__ == "pymol": # still cannot start from pymol interpreter
    from pymol_server import *

window.mainloop()

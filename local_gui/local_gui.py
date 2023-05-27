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
    print("Answers from ChatMol: ")
    for command in commands:
        if command == '':
            continue
        else:
            print(command)
    return commands

def send_message():
    message = entry.get()
    old_chat = chat.get("1.0", "end-1c")
    if (old_chat == chat_tips):
       chat.delete("1.0","end-1c")
       chat.config(fg = 'black')
    chat.config(state='normal')
    chat.insert(tk.END, "You: " + message + "\n")
    response = chatlite(message)
    chat.insert(tk.END, "ChatMol: " + '\n'.join(response) + "\n")
    entry.delete(0, tk.END)

def send_response_to_server():
    conversation = chat.get("1.0", "end-1c")
    index = conversation.rindex('ChatMol: ')
    command = ""
    if (index):
       command = conversation[index+9:]
       print("command", command)
    response = requests.post('http://localhost:8101/send_message', data=command)
    if response.status_code == 200:
        print('Command sent to server successfully.')
    else:
        print(f'Failed to send command to server. Status code: {response.status_code}')


# GUI code
window = tk.Tk()
window.geometry("300x675")
window.title("ChatMol")

# Create the main container
frame = ttk.Frame(window, padding="5 5 5 5")
frame.pack(fill='both', expand=True)


chat_tips = 'PyMOL commands from ChatMol will be displayed here. The last group of PyMOL commands can be executed by PyMOL when you hit "Send to PyMOL"'
# Create the chat box in the container
chat = tk.Text(frame, bg='white', fg='black', state='normal')  # change background color to white
chat.insert('end', chat_tips)
chat.config(fg = '#909090')
chat.pack(fill='both', expand=True)

entry_tips = 'Type ChatMol message here...'
# Create the entry box in the container
entry = tk.Entry(frame,bg='white', fg='#909090')
entry.insert(0, entry_tips)
entry.pack(fill='x')

def on_entry_click(event):
    """function that gets called whenever entry is clicked"""
    if entry.get() == entry_tips:
       entry.delete(0, "end") # delete all the text in the entry
       entry.insert(0, '') # Insert blank for user input
       entry.config(fg = '#010101')

def on_focusout(event):
    if entry.get() == '':
        entry.insert(0, entry_tips)
        entry.config(fg = '#909090')

# Create the send button in the container
send_button = ttk.Button(frame, text="Send to PyMOL", command=send_response_to_server)
send_button.pack(fill='x')

entry.bind('<Return>', lambda event: send_message())
entry.bind('<FocusIn>', on_entry_click)
entry.bind('<FocusOut>', on_focusout)

# Launch PyMOL in a separate thread
if __name__ == "__main__":
    pymol_thread = threading.Thread(target=launch_pymol)
    pymol_thread.start()

if __name__ == "pymol":  # still cannot start from pymol interpreter
    from pymol_server import *

window.mainloop()


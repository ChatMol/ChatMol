import tkinter as tk
from tkinter import messagebox
import socket

def send_message_to_pymol(message):
    remote_service_host = 'localhost'
    remote_service_port = 8100

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((remote_service_host, remote_service_port))
            client_socket.sendall(message.encode('utf-8'))
            return 'Message sent successfully'
    except Exception as e:
        return f'Error: {e}'

def process_and_send():
    message = text_input.get()
    if not message:
        messagebox.showerror("Error", "Please enter a message")
        return

    # Call GPT here and get the response (as a command)
    command = message  # Replace this line with your actual GPT function call
    response = send_message_to_pymol(command)

    if "Error" in response:
        messagebox.showerror("Error", response)
    # else:
    #     messagebox.showinfo("Success", response)

app = tk.Tk()
app.title("GPT-3.5-turbo Chat")

text_input = tk.Entry(app, width=50)
text_input.pack()

send_button = tk.Button(app, text="Send Message", command=process_and_send)
send_button.pack()

app.mainloop()

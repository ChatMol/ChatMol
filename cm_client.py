import socket

def main():
    server_address = ('localhost', 8100)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    message = input("Enter message to send to the server: ")
    client_socket.sendall(message.encode('utf-8'))
    client_socket.close()
    print("Message sent.")

if __name__ == '__main__':
    main()


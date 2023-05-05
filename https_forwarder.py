from flask import Flask, request
from flask_cors import CORS
import socket

app = Flask(__name__)
CORS(app)

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.data.decode('utf-8')
    remote_service_host = 'localhost'
    remote_service_port = 8100

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((remote_service_host, remote_service_port))
            client_socket.sendall(message.encode('utf-8'))
            return 'Message sent successfully', 200
    except Exception as e:
        return f'Error: {e}', 500

if __name__ == '__main__':
    app.run(port=8000, ssl_context=('certs/cert.pem', 'certs/key.pem'))

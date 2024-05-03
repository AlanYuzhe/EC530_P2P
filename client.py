import socket
import threading
import json
from collections import defaultdict

class Client:
    def __init__(self, username, server_ip, server_port, local_port):
        self.username = username
        self.local_port = local_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('localhost', local_port))
        self.server_address = (server_ip, server_port)
        self.offline_messages = defaultdict(list)

    def connect_to_server(self):
        self.socket.connect(self.server_address)
        print(f"Connected to server at {self.server_address}")
        self.register_with_server()

    def register_with_server(self):
        register_message = json.dumps({
            'type': 'register',
            'username': self.username,
            'port': self.local_port
        })
        self.socket.sendall(register_message.encode('utf-8'))
        response = self.socket.recv(1024).decode('utf-8')
        print(f"Server response: {response}")

    def send_message(self, recipient, message):
        self.send_offline_messages()
        data = {
            'type': 'message',
            'from': self.username,
            'to': recipient,
            'message': message
        }
        self.try_send_data(data)

    def try_send_data(self, data):
        try:
            self.socket.sendall(json.dumps(data).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send message, saving offline. Error: {e}")
            self.save_offline_message(data)

    def save_offline_message(self, data):
        recipient = data['to']
        self.offline_messages[recipient].append(data)
        print(f"Message saved offline for {recipient}.")

    def send_offline_messages(self):
        for recipient, messages in list(self.offline_messages.items()):
            for message in messages[:]:
                try:
                    self.socket.sendall(json.dumps(message).encode('utf-8'))
                    messages.remove(message)
                    print(f"Offline message sent to {recipient}")
                except Exception as e:
                    print(f"Failed to resend offline message to {recipient}. Error: {e}")
                    break
            if not messages:
                self.offline_messages.pop(recipient)

    def listen_for_messages(self):
        while True:
            try:
                response = self.socket.recv(1024).decode('utf-8')
                response_data = json.loads(response)
                print(f"\nReceived message: {response}")
            except Exception as e:
                print(f"\nError receiving response: {e}")
                break

    def start(self):
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        while True:
            self.send_offline_messages()
            recipient = input("Enter recipient's username: ")
            message = input("Enter your message: ")
            self.send_message(recipient, message)

if __name__ == "__main__":
    username = input("Enter your username: ")
    local_port = int(input("Enter your local port: "))
    client = Client(username, 'localhost', 12346, local_port)
    client.connect_to_server()
    client.start()

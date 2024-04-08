import socket
import threading
import json
import os
from collections import defaultdict


class Client:
    def __init__(self, username):
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.offline_messages = defaultdict(list)

    def register_with_server(self):
        register_message = json.dumps({
            'type': 'register',
            'username': self.username
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

    def save_offline_message(self, peer_name, message):
        self.offline_messages[peer_name].append(message)
        print(f"Message saved offline for {peer_name}.")

    def send_offline_messages(self):
        for peer_name, messages in list(self.offline_messages.items()):
            peer_ip = self.get_peer_ip(peer_name)
            if peer_ip == "NOT FOUND":
                print(f"{peer_name} is still offline, skipping offline messages.")
                continue

            for message in messages:
                try:
                    self.send_online_message(peer_name, peer_ip, message)
                    print(f"Sending stored message to {peer_name}: {message}")
                except Exception as e:
                    print(f"Failed to send stored message to {peer_name}: {e}")
                    break
            else:
                # 如果所有消息都发送成功，从字典中移除这个用户的所有离线消息
                del self.offline_messages[peer_name]

    def listen_for_messages(self):
        while True:
            try:
                response = self.socket.recv(1024).decode('utf-8')
                response_data = json.loads(response)
                if response_data.get("status") == "error" and response_data.get(
                        "message") == "User not found or not online.":
                    print("Recipient not online, message saved as offline.")
                else:
                    print(f"\nReceived message: {response}")
            except Exception as e:
                print(f"\nError receiving response: {e}")
                break

    def start(self):
        self.socket.connect(('localhost', 12345))
        self.register_with_server()
        self.send_offline_messages()
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

        while True:
            recipient = input("Enter recipient's username: ")
            message = input("Enter your message: ")
            self.send_message(recipient, message)

if __name__ == "__main__":
    username = input("Enter your name: ")
    client = Client(username)
    client.start()


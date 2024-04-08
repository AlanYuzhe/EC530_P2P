import socket
import threading
import json

def handle_client_connection(client_socket, client_address, users):
    username = None  # 在try块之外先初始化username
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            data = json.loads(message)
            if data['type'] == 'register':
                username = data['username']
                users[username] = {'socket': client_socket, 'address': client_address}
                print(f"User {username} registered.")
                client_socket.sendall(json.dumps({"status": "success", "message": "Registration successful"}).encode('utf-8'))
            elif data['type'] == 'message':
                recipient = data['to']
                if recipient in users:
                    recipient_socket = users[recipient]['socket']
                    recipient_socket.send(json.dumps(data).encode('utf-8'))  # 使用JSON格式转发消息
                    print(f"Message from {username} to {recipient} forwarded.")
                else:
                    print(f"User {recipient} not found or not online.")
                    feedback = json.dumps({"status": "error", "message": "User not found or not online."})
                    client_socket.sendall(feedback.encode('utf-8'))
    except Exception as e:
        print(f"Error handling message from {client_address}: {e}")
    finally:
        if username in users:  # 清理用户信息
            del users[username]
            print(f"User {username} unregistered.")
        client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 12345))
    server_socket.listen(5)
    print("Server is listening for connections...")

    users = {}

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            threading.Thread(target=handle_client_connection, args=(client_socket, client_address, users)).start()
    except KeyboardInterrupt:
        print("Server is shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()

import socket
import threading
import json
import sqlite3
from threading import Lock

active_sockets = {}
socket_lock = Lock()

def db_connection():
    return sqlite3.connect('users.db')

def setup_database():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                address TEXT,
                port INTEGER
            )
        """)
        conn.commit()

def register_user(username, address, port, client_socket):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET address = ?, port = ? WHERE username = ?", (address, port, username))
            client_socket.sendall(
                json.dumps({"status": "success", "message": "Updated address and port for username."}).encode('utf-8'))
        else:
            cursor.execute("INSERT INTO users (username, address, port) VALUES (?, ?, ?)", (username, address, port))
            client_socket.sendall(json.dumps({"status": "success", "message": "User registered."}).encode('utf-8'))
    with socket_lock:
        active_sockets[username] = client_socket

def handle_query(data, client_socket):
    username_query = data['username']
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT address, port FROM users WHERE username = ?", (username_query,))
        result = cursor.fetchone()
        if result:
            address, port = result
            response_data = {"status": "success", "address": address, "port": port}
        else:
            response_data = {"status": "error", "message": "User not found"}
    client_socket.sendall(json.dumps(response_data).encode('utf-8'))

def handle_client_connection(client_socket, client_address):
    username = None
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            data = json.loads(message)
            if data['type'] == 'register':
                username = data['username']
                port = data.get('port', 0)
                register_user(username, str(client_address[0]), port, client_socket)
            elif data['type'] == 'message':
                handle_message(data, client_socket)
            elif data['type'] == 'query':
                handle_query(data, client_socket)
    finally:
        if username:
            with socket_lock:
                active_sockets.pop(username, None)  # Remove socket on disconnect
        client_socket.close()

def handle_message(data, client_socket):
    recipient = data['to']
    with socket_lock:
        recipient_socket = active_sockets.get(recipient)
    if recipient_socket:
        recipient_socket.sendall(json.dumps(data).encode('utf-8'))
    else:
        print(f"Recipient {recipient} not found.")
        client_socket.sendall(json.dumps({"status": "error", "message": "Recipient not found"}).encode('utf-8'))

def start_server():
    setup_database()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 12346))
    server_socket.listen(5)
    print("Server is listening for connections...")
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            threading.Thread(target=handle_client_connection, args=(client_socket, client_address)).start()
    except KeyboardInterrupt:
        print("Server is shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()

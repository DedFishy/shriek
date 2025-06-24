import socket
import sys
from threading import Thread
import chars
import json
from userman import UserManager

userman = UserManager()

clients = {}
client_threads = []

sock = socket.socket()

buffsize = 1024

def send_data(name, data: dict, client_sock):
    data["type"] = name
    data_text = json.dumps(data).encode("utf-8") + chars.END
    print(data_text)
    client_sock.send(data_text)

def send_room_update(client_sock):
    send_data("room_update", {

    }, client_sock)

def handle_message(message: dict, client_sock: socket.socket):
    print("Handling", message)
    sid = client_sock.getsockname()
    message_type = message["type"]
    if message_type == "send_message":
        name = userman.get_user_guaranteed(sid=sid).name
        send_data("user_message", {"message": message["message"], "from": name}, client_sock)
    elif message_type == "join":
        userman.create_user(message["username"], client_sock.getsockname())
        send_room_update(client_sock)

def client_thread(client_sock: socket.socket, address):
    while True:
        disconnected = False
        got_to_end = False
        data = b""
        while not got_to_end:

            message = client_sock.recv(buffsize)

            print(address, ": ", message)
            data += message

            if not message: 
                disconnected = True
                break

            if data.endswith(chars.END): got_to_end = True
        
        data = data.removesuffix(chars.END)
        print(address, "says", data)
        
        if disconnected: break

        handle_message(json.loads(data), client_sock)
        
    client_sock.close()

port = 44375

sock.bind(("0.0.0.0", port))

try:
    while True:
        print("Listening for connections...")
        sock.listen(5)  
        print("Accepting...")
        connection, addr = sock.accept()
        print(connection, addr)

        thread = Thread(target=client_thread, args=(connection, addr))
        client_threads.append(thread)
        thread.start()
finally:
    sock.close()
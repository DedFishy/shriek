import socket
import sys
from threading import Thread
import chars
import json
from userman import UserManager

userman = UserManager()

clients: dict[tuple, socket.socket] = {}
client_threads = []

sock = socket.socket()

buffsize = 1024

CHANNELS = 2
CHUNK = 512

def send_data(name, data: dict, client_sock: socket.socket|None):
    data["type"] = name
    data_text = json.dumps(data).encode("utf-8") + chars.END
    print(data_text)
    if client_sock:
        client_sock.send(data_text)
    else:
        for client in clients.values():
            client.send(data_text)

def send_room_update():
    send_data("room_update", {
        "user_list": userman.construct_user_list()
        }, None)

def handle_message(message: dict, client_sock: socket.socket):
    print("Handling", message)
    sid = client_sock.getpeername()
    message_type = message["type"]
    if message_type == "send_message":
        if len(message["message"]) > 0:
            name = userman.get_user_guaranteed(sid=sid).name
            send_data("user_message", {"message": message["message"], "from": name}, None)
    elif message_type == "join":
        userman.create_user(message["username"], sid)
        send_room_update()

def client_thread(client_sock: socket.socket, address: tuple):
    clients[address] = client_sock
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
    del clients[address]
    print([user.serialize() for user in userman.users])
    print(address)
    userman.remove_user(userman.get_user(sid=address))

    send_room_update()


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
    print("CLOSING --- HOLD YOUR HORSES")
    sock.shutdown(0)
    sock.close()
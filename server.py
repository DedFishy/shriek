title = """------------------------------------------------
.d8888. db   db d8888b. d888888b d88888b db   dD 
88'  YP 88   88 88  `8D   `88'   88'     88 ,8P' 
`8bo.   88ooo88 88oobY'    88    88ooooo 88,8P   
  `Y8b. 88~~~88 88`8b      88    88~~~~~ 88`8b   
db   8D 88   88 88 `88.   .88.   88.     88 `88. 
`8888Y' YP   YP 88   YD Y888888P Y88888P YP   YD 
------------------------------------------------"""
print(title)

import socket
from threading import Thread
import chars
import json
from userman import UserManager

PORT = 44375

userman = UserManager()

clients: dict[tuple, socket.socket] = {}

sock = socket.socket()
sock.bind(("0.0.0.0", PORT))

buffsize = 1024

CHANNELS = 2
CHUNK = 512

def send_data(name, data: dict, client_sock: socket.socket|None):
    data["type"] = name
    data_text = json.dumps(data).encode("utf-8") + chars.END
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
    sid = client_sock.getpeername()
    message_type = message["type"]
    print(f"Message recieved from {sid[0]} of type '{message_type}'")

    if message_type == "send_message":
        if len(message["message"]) > 0:
            print(f"Forwarding message to all connected clients")
            name = userman.get_user_guaranteed(sid=sid).name
            send_data("user_message", {"message": message["message"], "from": name}, None)
        else:
            print(f"Ignoring message of length 0")

    elif message_type == "join":
        if len(message["username"]) > 0 and not userman.get_user(message["username"]):
            print(f"Registering new user and sending update to clients")
            userman.create_user(message["username"], sid)
            send_data("join_accept", {}, client_sock)
            send_room_update()
        else:
            print(f"Rejecting join request due to invalid username: {message["username"]}")
            send_data("join_deny", {"message": "Invalid username"}, client_sock)

def client_thread(client_sock: socket.socket, address: tuple):
    clients[address] = client_sock

    while True:
        disconnected = False
        got_to_end = False
        data = b""
        while not got_to_end:
            message = client_sock.recv(buffsize)
            data += message
            if not message: 
                disconnected = True
                break

            if data.endswith(chars.END): got_to_end = True
        
        data = data.removesuffix(chars.END)
        
        if disconnected: break

        handle_message(json.loads(data), client_sock)
    
    # Handle a client disconnect
    client_sock.close()
    del clients[address]
    user = userman.get_user_guaranteed(sid=address)
    send_data("system_message", {"message": user.name + " has left the chat."}, None)
    userman.remove_user(user)
    send_room_update()


print("Starting the Shriek server...")
try:
    while True:
        # Wait for a connection
        print("Listening for incoming connections...")
        sock.listen(5)  
        connection, addr = sock.accept()

        # Spin up a thread for the connection
        print(f"User connected: {addr[0]}")
        thread = Thread(target=client_thread, args=(connection, addr))
        thread.start()

except KeyboardInterrupt:
    # Handle admin exit
    print("Server has been KeyboardInterrupt-ed")
finally:
    print("Shutting down server")
    sock.shutdown(0)
    sock.close()
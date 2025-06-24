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

mic_send_port = 44376
audio_recv_port = 44377

class UserMicrophoneBroadcaster:
    def __init__(self):
        self.incoming = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.incoming.bind(("127.0.0.1", mic_send_port))
        self.outgoing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.streaming = True

    def stream_recv_loop(self):
        while self.streaming:
            data_recv, address = self.incoming.recvfrom(CHUNK*CHANNELS*2)
            cpid = userman.get_user_guaranteed(sid=address).call_participant_id
            data = int.to_bytes(cpid) + data_recv

            for user in userman.users:
                
                offset = 0

                if user.sid not in userman.voice_excluded_sids:
                    print("Broadcasting to user:" + str(user.serialize()))
                    print(audio_recv_port + offset)
                    self.outgoing.sendto(data, (user.sid[0], audio_recv_port + offset))
                    offset += 5

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
        name = userman.get_user_guaranteed(sid=sid).name
        send_data("user_message", {"message": message["message"], "from": name}, None)
    elif message_type == "join":
        userman.create_user(message["username"], sid)
        send_room_update()
    elif message_type == "join_voice":
        userman.add_to_voice(sid)
        print("Connecting user to voice")
        send_data("joined_voice", {}, client_sock)
    elif message_type == "leave_voice":
        userman.remove_from_voice(sid)
        print("Disconnecting user from voice")
        send_data("left_voice", {}, client_sock)

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

port = 44375

sock.bind(("0.0.0.0", port))

try:
    broadcaster = UserMicrophoneBroadcaster()
    Thread(target=broadcaster.stream_recv_loop).start()
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
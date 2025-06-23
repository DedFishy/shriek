import socket
import sys
from threading import Thread
import chars

clients = {}
client_threads = []

sock = socket.socket()

buffsize = 1024

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

        
    client_sock.close()

port = 44375

sock.bind(("0.0.0.0", port))

while True:
    print("Listening for connections...")
    sock.listen(5)  
    print("Accepting...")
    connection, addr = sock.accept()
    print(connection, addr)
    clients[addr] = connection

    thread = Thread(target=client_thread, args=(connection, addr))
    client_threads.append(thread)
    thread.start()

sock.close()
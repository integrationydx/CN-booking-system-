import socket
import threading
import random

HOST = "127.0.0.1"
PORT = 5001


def client_sim(i):

    seat = str(random.randint(1,20))

    s = socket.socket()
    s.connect((HOST, PORT))

    s.send(f"LOCK {seat} C{i}".encode())
    s.recv(1024)

    s.send(f"BOOK {seat} C{i}".encode())
    print(s.recv(1024).decode())

    s.close()


threads = []

for i in range(50):

    t = threading.Thread(target=client_sim, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
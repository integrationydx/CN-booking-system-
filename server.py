import socket
import threading
import json
import time
import os

HOST = "127.0.0.1"
PORT = 5001

SEAT_FILE = "seats.json"
LOG_FILE = "wal.log"

LOCK_TIMEOUT = 15

# Load seat data
if os.path.exists(SEAT_FILE):
    with open(SEAT_FILE) as f:
        seats = json.load(f)
else:
    seats = {str(i): {"status": "free", "holder": None} for i in range(1, 21)}

# Per-seat locks
seat_locks = {seat: threading.Lock() for seat in seats}

lock_table = {}
waitlist = {}


def save_state():
    with open(SEAT_FILE, "w") as f:
        json.dump(seats, f)


def log_event(event):
    with open(LOG_FILE, "a") as f:
        f.write(event + "\n")


# Release expired locks
def release_expired_locks():

    while True:

        time.sleep(2)

        now = time.time()

        expired = []

        for seat in list(lock_table.keys()):
            holder, ts = lock_table[seat]

            if now - ts > LOCK_TIMEOUT:
                expired.append(seat)

        for seat in expired:

            print(f"Lock expired for seat {seat}")

            del lock_table[seat]


def handle_lock(seat, client):

    if seat not in seats:
        return "INVALID SEAT"

    with seat_locks[seat]:

        if seats[seat]["status"] == "booked":
            if seats[seat]["holder"] == client:
                return "SEAT ALREADY YOURS"
            if client not in waitlist.get(seat, []):
                waitlist.setdefault(seat, []).append(client)
            return "SEAT BOOKED. ADDED TO WAITLIST"

        if seat in lock_table:
            return "SEAT TEMPORARILY LOCKED"

        lock_table[seat] = (client, time.time())

        return "LOCK ACQUIRED"


def handle_book(seat, client):

    if seat not in seats:
        return "INVALID SEAT"

    with seat_locks[seat]:

        if seat not in lock_table:
            return "LOCK REQUIRED"

        holder, ts = lock_table[seat]

        if holder != client:
            return "LOCK OWNED BY ANOTHER CLIENT"

        log_event(f"START BOOK {seat} {client}")

        seats[seat]["status"] = "booked"
        seats[seat]["holder"] = client

        del lock_table[seat]

        save_state()

        log_event(f"COMMIT BOOK {seat} {client}")

        return "BOOK SUCCESS"


def handle_cancel(seat, client):

    if seat not in seats:
        return "INVALID SEAT"

    with seat_locks[seat]:

        if seats[seat]["holder"] != client:
            return "NOT YOUR BOOKING"

        log_event(f"START CANCEL {seat}")

        seats[seat]["status"] = "free"
        seats[seat]["holder"] = None

        # Waitlist handling — skip stale entries for the cancelling client
        if seat in waitlist:
            waitlist[seat] = [c for c in waitlist[seat] if c != client]

        if seat in waitlist and waitlist[seat]:

            next_client = waitlist[seat].pop(0)

            seats[seat]["status"] = "booked"
            seats[seat]["holder"] = next_client

        save_state()

        log_event(f"COMMIT CANCEL {seat}")

        return "CANCELLED"


def seat_map():

    output = ""

    for i in range(1, 21):

        seat = str(i)

        if seats[seat]["status"] == "free":
            output += "[ ] "
        else:
            output += "[X] "

        if i % 5 == 0:
            output += "\n"

    return output


def get_client_bookings(client):

    booked = []

    for seat in seats:
        if seats[seat]["holder"] == client:
            booked.append(seat)

    if not booked:
        return "No bookings"

    return "Your seats: " + ", ".join(booked)


def handle_client(conn):

    while True:

        try:

            data = conn.recv(1024).decode().strip()

            if not data:
                break

            parts = data.split()
            cmd = parts[0]

            if cmd == "LOCK":
                seat, client = parts[1], parts[2]
                response = handle_lock(seat, client)

            elif cmd == "BOOK":
                seat, client = parts[1], parts[2]
                response = handle_book(seat, client)

            elif cmd == "CANCEL":
                seat, client = parts[1], parts[2]
                response = handle_cancel(seat, client)

            elif cmd == "STATUS":
                response = json.dumps(seats)

            elif cmd == "MAP":
                response = seat_map()

            elif cmd == "MYBOOKINGS":
                client = parts[1]
                response = get_client_bookings(client)

            else:
                response = "UNKNOWN COMMAND"

            conn.send((response + "\n").encode())

        except Exception:
            break

    conn.close()


def start_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print("Reservation Server Running")

    threading.Thread(target=release_expired_locks, daemon=True).start()

    while True:

        conn, addr = server.accept()

        print("Client connected:", addr)

        threading.Thread(target=handle_client, args=(conn,)).start()


start_server()
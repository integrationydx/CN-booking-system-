import socket      # networking module for server-client communication
import threading   # for handling multiple clients simultaneously
import json        # for storing/loading seat data
import time        # for timestamps (lock timeout)
import os          # for file existence checking

HOST = "127.0.0.1"   # server IP (localhost)
PORT = 5001          # port server listens on

SEAT_FILE = "seats.json"   # file to store seat data persistently
LOG_FILE = "wal.log"       # write-ahead log file

LOCK_TIMEOUT = 15   # lock expires after 15 seconds

# Load seat data if file exists, else initialize seats
if os.path.exists(SEAT_FILE):  # check if seat file exists
    with open(SEAT_FILE) as f:  # open file
        seats = json.load(f)    # load JSON data into dictionary
else:
    seats = {str(i): {"status": "free", "holder": None} for i in range(1, 21)}  # create 20 seats

# Create a lock for each seat (to prevent race conditions)
seat_locks = {seat: threading.Lock() for seat in seats}

lock_table = {}   # stores temporary locks → {seat: (client, timestamp)}
waitlist = {}     # stores waitlisted clients → {seat: [clients]}


def save_state():
    with open(SEAT_FILE, "w") as f:  # open file in write mode
        json.dump(seats, f)          # save seat data


def log_event(event):
    with open(LOG_FILE, "a") as f:   # open log file in append mode
        f.write(event + "\n")        # write event line


# Background thread to release expired locks
def release_expired_locks():

    while True:  # run forever

        time.sleep(2)  # check every 2 seconds

        now = time.time()  # current timestamp

        expired = []  # list of expired seats

        for seat in list(lock_table.keys()):  # iterate over locked seats
            holder, ts = lock_table[seat]     # get client + timestamp

            if now - ts > LOCK_TIMEOUT:  # check if lock expired
                expired.append(seat)

        for seat in expired:

            print(f"Lock expired for seat {seat}")  # debug print

            del lock_table[seat]  # remove lock


def handle_lock(seat, client):

    if seat not in seats:  # check valid seat
        return "INVALID SEAT"

    with seat_locks[seat]:  # acquire lock for that seat

        if seats[seat]["status"] == "booked":  # if already booked
            if seats[seat]["holder"] == client:  # if same client
                return "SEAT ALREADY YOURS"
            if client not in waitlist.get(seat, []):  # add to waitlist if not already
                waitlist.setdefault(seat, []).append(client)
            return "SEAT BOOKED. ADDED TO WAITLIST"

        if seat in lock_table:  # if already locked
            return "SEAT TEMPORARILY LOCKED"

        lock_table[seat] = (client, time.time())  # store lock with timestamp

        return "LOCK ACQUIRED"


def handle_book(seat, client):

    if seat not in seats:  # validate seat
        return "INVALID SEAT"

    with seat_locks[seat]:  # lock seat

        if seat not in lock_table:  # booking requires lock
            return "LOCK REQUIRED"

        holder, ts = lock_table[seat]  # get lock owner

        if holder != client:  # check ownership
            return "LOCK OWNED BY ANOTHER CLIENT"

        log_event(f"START BOOK {seat} {client}")  # log start

        seats[seat]["status"] = "booked"  # mark seat booked
        seats[seat]["holder"] = client    # assign owner

        del lock_table[seat]  # remove lock after booking

        save_state()  # persist data

        log_event(f"COMMIT BOOK {seat} {client}")  # log commit

        return "BOOK SUCCESS"


def handle_cancel(seat, client):

    if seat not in seats:  # validate seat
        return "INVALID SEAT"

    with seat_locks[seat]:  # lock seat

        if seats[seat]["holder"] != client:  # check ownership
            return "NOT YOUR BOOKING"

        log_event(f"START CANCEL {seat}")  # log start

        seats[seat]["status"] = "free"  # free seat
        seats[seat]["holder"] = None    # remove holder

        # remove client from waitlist if present
        if seat in waitlist:
            waitlist[seat] = [c for c in waitlist[seat] if c != client]

        # assign seat to next client in waitlist
        if seat in waitlist and waitlist[seat]:

            next_client = waitlist[seat].pop(0)  # FIFO

            seats[seat]["status"] = "booked"
            seats[seat]["holder"] = next_client

        save_state()  # persist changes

        log_event(f"COMMIT CANCEL {seat}")  # log commit

        return "CANCELLED"


def seat_map():

    output = ""  # string to store map

    for i in range(1, 21):  # iterate seats

        seat = str(i)

        if seats[seat]["status"] == "free":  # if free
            output += "[ ] "
        else:
            output += "[X] "

        if i % 5 == 0:  # new row after 5 seats
            output += "\n"

    return output


def get_client_bookings(client):

    booked = []  # list of booked seats

    for seat in seats:
        if seats[seat]["holder"] == client:  # check ownership
            booked.append(seat)

    if not booked:
        return "No bookings"

    return "Your seats: " + ", ".join(booked)


def handle_client(conn):

    while True:  # keep receiving requests

        try:

            data = conn.recv(1024).decode().strip()  # receive and clean input

            if not data:  # if client disconnects
                break

            parts = data.split()  # split command
            cmd = parts[0]        # extract command

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
                response = json.dumps(seats)  # send full seat data

            elif cmd == "MAP":
                response = seat_map()  # send seat map

            elif cmd == "MYBOOKINGS":
                client = parts[1]
                response = get_client_bookings(client)

            else:
                response = "UNKNOWN COMMAND"

            conn.send((response + "\n").encode())  # send response

        except Exception:
            break  # break on error

    conn.close()  # close connection


def start_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create TCP socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow port reuse
    server.bind((HOST, PORT))  # bind to host and port
    server.listen()  # start listening

    print("Reservation Server Running")  # server status

    threading.Thread(target=release_expired_locks, daemon=True).start()  # start background thread

    while True:

        conn, addr = server.accept()  # accept client connection

        print("Client connected:", addr)  # print client info

        threading.Thread(target=handle_client, args=(conn,)).start()  # handle client in new thread


start_server()  # start server
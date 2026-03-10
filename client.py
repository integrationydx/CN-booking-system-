import socket

HOST = "127.0.0.1"
PORT = 5001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

current_user = None

print("Reservation System")
print("-------------------")

while True:

    # LOGIN SYSTEM
    if current_user is None:

        user = input("Login as client (ex: C1, C2) or type exit: ").strip()

        if user.lower() == "exit":
            break

        if user == "":
            continue

        current_user = user
        print(f"Logged in as {current_user}")
        continue


    cmd = input(f"{current_user}> ").strip()

    if cmd == "logout":
        current_user = None
        print("Logged out\n")
        continue


    # LOCK COMMAND
    elif cmd.startswith("lock"):
        parts = cmd.split()

        if len(parts) != 2:
            print("Usage: lock <seat>")
            continue

        seat = parts[1]
        msg = f"LOCK {seat} {current_user}"


    # BOOK COMMAND
    elif cmd.startswith("book"):
        parts = cmd.split()

        if len(parts) != 2:
            print("Usage: book <seat>")
            continue

        seat = parts[1]
        msg = f"BOOK {seat} {current_user}"


    # CANCEL COMMAND
    elif cmd.startswith("cancel"):
        parts = cmd.split()

        if len(parts) != 2:
            print("Usage: cancel <seat>")
            continue

        seat = parts[1]
        msg = f"CANCEL {seat} {current_user}"


    elif cmd == "map":
        msg = "MAP"


    elif cmd == "status":
        msg = "STATUS"


    elif cmd == "mybookings":
        msg = f"MYBOOKINGS {current_user}"


    else:
        print("\nCommands:")
        print("lock <seat>")
        print("book <seat>")
        print("cancel <seat>")
        print("map")
        print("status")
        print("mybookings")
        print("logout\n")
        continue


    sock.send(msg.encode())

    response = sock.recv(4096).decode()

    print(response)


sock.close()
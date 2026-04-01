import socket  # import socket module for networking

HOST = "127.0.0.1"  # server IP (localhost = same machine)
PORT = 5001         # port number server is listening on

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create TCP socket (IPv4 + TCP)
sock.connect((HOST, PORT))  # establish connection to server

current_user = None  # stores logged-in user (None = no user logged in)

print("Reservation System")  # print heading
print("-------------------")   # print separator

while True:  # infinite loop to keep program running

    if current_user is None:  # if no user is logged in

        user = input("Login as client (ex: C1, C2) or type exit: ").strip()  # take login input and remove spaces

        if user.lower() == "exit":  # check if user wants to exit
            break  # break loop and terminate program

        if user == "":  # if input is empty
            continue  # skip and ask again

        current_user = user  # set current user
        print(f"Logged in as {current_user}")  # confirm login
        continue  # go back to start of loop


    cmd = input(f"{current_user}> ").strip()  # take command input and clean spaces

    if cmd == "logout":  # if user wants to logout
        current_user = None  # reset user
        print("Logged out\n")  # print message
        continue  # go back to login stage


    elif cmd.startswith("lock"):  # check if command starts with 'lock'
        parts = cmd.split()  # split input into list (e.g., "lock A1" → ["lock","A1"])

        if len(parts) != 2:  # ensure correct format (exactly 2 parts)
            print("Usage: lock <seat>")  # show correct usage
            continue  # skip this iteration

        seat = parts[1]  # extract seat number (second word)
        msg = f"LOCK {seat} {current_user}"  # create message to send to server


    elif cmd.startswith("book"):  # check if command starts with 'book'
        parts = cmd.split()  # split input

        if len(parts) != 2:  # validate format
            print("Usage: book <seat>")  # show usage
            continue  # skip

        seat = parts[1]  # extract seat
        msg = f"BOOK {seat} {current_user}"  # create message


    elif cmd.startswith("cancel"):  # check if command starts with 'cancel'
        parts = cmd.split()  # split input

        if len(parts) != 2:  # validate format
            print("Usage: cancel <seat>")  # show usage
            continue  # skip

        seat = parts[1]  # extract seat
        msg = f"CANCEL {seat} {current_user}"  # create message


    elif cmd == "map":  # if user types 'map'
        msg = "MAP"  # request seat map from server


    elif cmd == "status":  # if user types 'status'
        msg = "STATUS"  # request full seat status


    elif cmd == "mybookings":  # if user types 'mybookings'
        msg = f"MYBOOKINGS {current_user}"  # request bookings for current user


    else:  # if command is invalid
        print("\nCommands:")  # show available commands
        print("lock <seat>")
        print("book <seat>")
        print("cancel <seat>")
        print("map")
        print("status")
        print("mybookings")
        print("logout\n")
        continue  # skip sending anything


    sock.send(msg.encode())  # convert message to bytes and send to server

    response = sock.recv(4096).decode()  # receive response (max 4096 bytes) and convert to string

    print(response)  # display server response


sock.close()  # close socket connection when loop ends
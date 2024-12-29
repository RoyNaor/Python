# import socket
from socket import *
import time


def split_message(message, max_size):
    message_bytes = message.encode()  # Encode the message in UTF-8
    result = []  # Array to store the split parts
    index = 0  # for the prefix M{index}-

    start_index = 0  # follow the bytes of the message

    while start_index < len(message_bytes):
        prefix = f"M{index}-"
        prefix_size = len(prefix.encode('utf-8'))  # calculate the prefix size
        chunk_size = max_size - prefix_size  # Remaining size for the message

        # Extract the chunk of appropriate size
        remaining_bytes = message_bytes[start_index:]
        chunk = remaining_bytes[:chunk_size]

        # Decode to create a string and check if it splits characters
        while True:
            try:
                decoded_chunk = chunk.decode("utf-8")
                break
            except UnicodeDecodeError:
                # Reduce chunk size if it cuts a multi-byte character
                chunk = chunk[:-1]

        # Create the packet
        packet = f"{prefix}{decoded_chunk}"
        result.append(packet)

        # Move the start index forward
        start_index += len(chunk)
        index += 1

    return result


def read_input_from_file(file_path):
    params = {}
    with open(file_path, 'r', encoding='utf-8') as file:  # Open the file
        for line in file:
            key, value = line.split(":", 1)  # Split each line into key and value
            params[key.strip()] = value.strip()  # Remove any extra whitespace

    # Extract values and return them in the correct types
    return (
        params["message"],
        int(params["maximum_msg_size"]),
        int(params["window_size"]),
        int(params["timeout"])
    )



#----------------------------------------------------------------------------------


serverName = 'localhost'
serverPort = 13000
SERVER_ADDRESS = (serverName, serverPort)

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(SERVER_ADDRESS)

# Input handling
file_mode = input("Do you want to read inputs from a file? (yes/no): ").strip().lower()
if file_mode == 'yes':
    file_path = input("Enter the file path: ").strip()
    message, maximum_msg_size, window_size, timeout = read_input_from_file(file_path)

    clientSocket.send(file_path.encode())
    server_response = clientSocket.recv(4096).decode()

    if server_response == "ok":
        print(f"The server agreed to the the file max: {maximum_msg_size}")
    else:
        print("The server does not agree to the max message size")

else:
    print("Waiting for server to enter a maximum message size...")
    max_ask_server = "what is the maximum number of bytes you are willing to receive?"
    clientSocket.send(max_ask_server.encode())

    maximum_msg_size = int(clientSocket.recv(4096).decode())
    print('Hi client, I\'m willing to receive:', str(maximum_msg_size) + " bytes")

    message = input('Input a massage: ')

    window_size = input('enter the window size: ')

    timeout = input('enter the timeout: ')

packets = split_message(message, maximum_msg_size)
packetsACK = [False] * len(packets)
print("\n")

window_start = 0
start_time = time.time()
current_time = time.time() - start_time

window_moved = True

while window_start < len(packets):

    if window_moved:  # Send packets within the window
        for i in range(window_start, min(window_start + int(window_size), len(packets))):
            if not packetsACK[i]:  # Only send unacknowledged packets
                print(f"Sending packet {i}: {packets[i]}")
                clientSocket.send(packets[i].encode())  # Send the packet

                # Immediately receive the acknowledgment
                ack_from_server = clientSocket.recv(4096).decode()
                ack_number = int(ack_from_server[3:])  # Extract ACK number
                print(f"Received {ack_from_server}")
                packetsACK[ack_number] = True  # Mark the packet as acknowledged

    window_moved = False
    # Slide the window forward
    while window_start < len(packets) and packetsACK[window_start]:
        window_start += 1  # Slide window forward
        print(f"moving window to {window_start}")  #debug
        start_time = time.time()
        #print("new start time: " + str(start_time))
        window_moved = True

    current_time = time.time() - start_time
    # print("current time: " + str(current_time))

    # reached timeout and needs to send all the false packets
    if current_time >= float(timeout):
        for i in range(window_start, min(window_start + int(window_size), len(packets))):
            if not packetsACK[i]:
                print(f"Sending packet {i} again: {packets[i]}")
                clientSocket.send(packets[i].encode())  # Send the packet

                # Immediately receive the acknowledgment
                ack_from_server = clientSocket.recv(4096).decode()
                ack_number = int(ack_from_server[3:])  # Extract ACK number
                print(f"Received {ack_from_server}")
                for j in range(ack_number + 1):
                    packetsACK[j] = True  # Mark the packet as acknowledged

        start_time = time.time()

clientSocket.close()

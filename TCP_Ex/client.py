# import socket
from socket import *
import time

# Function to split a message into packets of a specific size
def split_message(message, max_size):
    message_bytes = message.encode()  # Encode the message in UTF-8
    result = []   # Array to store the split parts of the message
    index = 0  # Index for prefixing packets (M{index})

    start_index = 0  # Tracks the starting byte index of the message to process

    # Loop to split the message into chunks of the appropriate size
    while start_index < len(message_bytes):
        prefix = f"M{index}-"  # Packet prefix to include packet number

        # Extract the chunk of appropriate size
        remaining_bytes = message_bytes[start_index:]
        chunk = remaining_bytes[:max_size]  # Directly use max_size as the chunk size

        # Decode to create a string and check if it splits characters
        while True:
            # Try to decode the chunk
            try:
                decoded_chunk = chunk.decode("utf-8")
                break
            except UnicodeDecodeError:
                # Reduce chunk size if it cuts a multi-byte character
                chunk = chunk[:-1]

        # Create the packet by combining the prefix and the decoded chunk
        packet = f"{prefix}{decoded_chunk}"
        result.append(packet)

        # Move the start index forward
        start_index += len(chunk)
        index += 1

    return result


# Function to read input parameters from a file
def read_input_from_file(file_path):
    params = {}  # Dictionary to store key-value pairs from the file
    with open(file_path, 'r', encoding='utf-8') as file:  # Open the file
        for line in file:  # Iterate through each line in the file
            key, value = line.split(":", 1)  # Split each line into key and value
            params[key.strip()] = value.strip()  # Remove any extra whitespace

    # Extract values and return them in the correct types
    return (
        params["message"],
        int(params["maximum_msg_size"]),
        int(params["window_size"]),
        int(params["timeout"])
    )


# Function to 
def handle_file_mode(client_socket):
    file_path = input(r"Enter the file path (for example C:\Users\userName\test.txt): ").strip()
    message, max_msg_size, window_size, timeout = read_input_from_file(file_path)

    client_socket.send(file_path.encode())
    server_response = client_socket.recv(4096).decode()

    if server_response == "ok":
        print(f"The server agreed to the max: {max_msg_size}")
    else:
        print("The server does not agree to the max message size")

    return message, max_msg_size, window_size, timeout


# Function to
def handle_manual_mode(client_socket):
    print("Waiting for server to enter a maximum message size...")
    max_ask_server = "what is the maximum number of bytes you are willing to receive?"
    client_socket.send(max_ask_server.encode())

    max_msg_size = int(client_socket.recv(4096).decode())
    print(f"Server: willing to receive {max_msg_size} bytes")

    message = input("Input a message: ")
    window_size = int(input("Enter the window size: "))
    timeout = float(input("Enter the timeout: "))
    print("")

    return message, max_msg_size, window_size, timeout


# Function to
def send_packets(client_socket, packets, window_size, timeout):
    packets_ack = [False] * len(packets)
    window_start = 0
    start_time = time.time()

    while window_start < len(packets):
        for i in range(window_start, min(window_start + window_size, len(packets))):
            if not packets_ack[i]:
                print(f"Sending packet {i}: {packets[i]}")
                client_socket.send(packets[i].encode())
                ack = client_socket.recv(4096).decode()
                ack_number = int(ack[3:])
                print(f"Received {ack}")
                packets_ack[ack_number] = True

        while window_start < len(packets) and packets_ack[window_start]:
            window_start += 1
            print(f"Moving window to {window_start}")
            start_time = time.time()

        if time.time() - start_time >= timeout:
            for i in range(window_start, min(window_start + window_size, len(packets))):
                if not packets_ack[i]:
                    print(f"Resending packet {i}: {packets[i]}")
                    client_socket.send(packets[i].encode())
                    ack = client_socket.recv(4096).decode()
                    ack_number = int(ack[3:])
                    print(f"Received {ack}")
                    packets_ack[ack_number] = True

            start_time = time.time()


# Function to handle the client-side operations for communication with the server
def client(server_address):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(server_address)

    while True:
        send_message = input("\nDo you want to send a message to the server? (yes/no): ").strip().lower()
        client_socket.send(send_message.encode())

        if send_message != 'yes':
            print("Ending connection with the server.")
            break

        file_mode = input("Do you want to read inputs from a file? (yes/no): ").strip().lower()

        if file_mode == 'yes':
            message, max_msg_size, window_size, timeout = handle_file_mode(client_socket)
        else:
            message, max_msg_size, window_size, timeout = handle_manual_mode(client_socket)

        packets = split_message(message, max_msg_size)
        send_packets(client_socket, packets, window_size, timeout)

        client_socket.send("done".encode())

    client_socket.close()


if __name__ == "__main__":
    # Define the server address and port
    SERVER_ADDRESS = ('localhost', 13000)

    # Start the client
    client(SERVER_ADDRESS)

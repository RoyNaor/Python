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


# Function to extract the info from the file and send the file path to the server
def handle_file_mode(client_socket):
    file_path = input(r"Enter the file path (for example C:\Users\userName\test.txt): ").strip()
    message, max_msg_size, window_size, timeout = read_input_from_file(file_path)

    # Send the file path to the server
    client_socket.send(file_path.encode())
    server_response = client_socket.recv(4096).decode()  # Receive server response

    # Handle server's response to the file
    if server_response == "ok":
        print(f"The server agreed to the max: {max_msg_size}")
    else:
        print("The server does not agree to the max message size")

    # Return the extracted parameters
    return message, max_msg_size, window_size, timeout


# Function to handle the client input manually
def handle_manual_mode(client_socket):
    # Request the maximum message size from the server
    print("Waiting for server to enter a maximum message size...")
    max_ask_server = "what is the maximum number of bytes you are willing to receive?"
    client_socket.send(max_ask_server.encode())

    # Receive and display the maximum message size from the server
    max_msg_size = int(client_socket.recv(4096).decode())
    print(f"Server: willing to receive {max_msg_size} bytes")

    # Collect input from the user for message, window size, and timeout
    message = input("Input a message: ")
    window_size = int(input("Enter the window size: "))
    timeout = float(input("Enter the timeout: "))
    print("")

    return message, max_msg_size, window_size, timeout


# Function to Send a packet and process its acknowledgment
def send_and_acknowledge(client_socket, packet, packets_ack):
    client_socket.send(packet.encode())  # Send the packet
    ack = client_socket.recv(4096).decode()  # Wait for acknowledgment
    ack_number = int(ack[3:])  # Extract the acknowledgment number
    print(f"Received {ack}")
    packets_ack[ack_number] = True  # Mark the packet as acknowledged

    return packets_ack


# Function to Handle packet delivery using a sliding window protocol
def send_packets(client_socket, packets, window_size, timeout):
    packets_ack = [False] * len(packets)  # Track acknowledgment status for each packet
    window_start = 0  # The starting index of the current window
    start_time = time.time()  # Record the start time for timeout handling

    while window_start < len(packets):
        # Send packets within the current window
        for i in range(window_start, min(window_start + window_size, len(packets))):
            if not packets_ack[i]:  # Only send packets that haven't been acknowledged
                print(f"Sending packet {i}: {packets[i]}")
                # Send the packet at the given index and wait for acknowledgment, updating the acknowledgment status.
                packets_ack = send_and_acknowledge(client_socket, packets[i], packets_ack)

        # Slide the window forward for acknowledged packets
        while window_start < len(packets) and packets_ack[window_start]:
            window_start += 1
            print(f"Moving window to {window_start}")
            start_time = time.time()  # Reset the start time for timeout tracking

        # Resend unacknowledged packets if timeout occurs
        if time.time() - start_time >= timeout:  # Check if timeout has been reached
            for i in range(window_start, min(window_start + window_size, len(packets))):
                if not packets_ack[i]:  # Resend only unacknowledged packets
                    print(f"Resending packet {i}: {packets[i]}")
                    # Send the packet at the given index and wait for acknowledgment, updating the acknowledgment status.
                    packets_ack = send_and_acknowledge(client_socket, packets[i], packets_ack)

            start_time = time.time()  # Reset the start time after resending packets


# Function to handle the client-side operations for communication with the server
def client(server_address):
    # Create a TCP socket and connect to the server
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(server_address)

    while True:
        # Ask the user if they want to send a message
        send_message = input("\nDo you want to send a message to the server? (yes/no): ").strip().lower()
        client_socket.send(send_message.encode())

        # If the user chooses not to send a message, close the connection
        if send_message != 'yes':
            print("Ending connection with the server.")
            break

        file_mode = input("Do you want to read inputs from a file? (yes/no): ").strip().lower()

        if file_mode == 'yes':
            # Handle input from a file
            message, max_msg_size, window_size, timeout = handle_file_mode(client_socket)
        else:
            # Handle manual input from the user
            message, max_msg_size, window_size, timeout = handle_manual_mode(client_socket)

        # Split the message into packets based on the maximum message size
        packets = split_message(message, max_msg_size)

        # Send packets to the server using a sliding window protocol
        send_packets(client_socket, packets, window_size, timeout)

        # Notify the server that the message transmission is complete
        client_socket.send("done".encode())

    client_socket.close()  # Close the socket connection


if __name__ == "__main__":
    # Define the server address and port
    SERVER_ADDRESS = ('localhost', 13000)

    # Start the client
    client(SERVER_ADDRESS)

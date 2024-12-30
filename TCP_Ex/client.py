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
        prefix_size = len(prefix.encode('utf-8'))  # calculate the prefix size
        chunk_size = max_size - prefix_size  # Remaining size for the message

        # Check if the chunk size is valid
        if chunk_size <= 0:
            print("Not enough bytes to send the message")
            result.append(None)  # Append None to indicate failure
            return result

        # Extract the chunk of appropriate size
        remaining_bytes = message_bytes[start_index:]
        chunk = remaining_bytes[:chunk_size]

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


#----------------------------------------------------------------------------------

# Set the server address and port
serverName = 'localhost'
serverPort = 13000
SERVER_ADDRESS = (serverName, serverPort)  # Combine into a tuple for connection

# Create a TCP socket
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(SERVER_ADDRESS)  # Connect to the server

# Main loop to keep asking the user if they want to send a message
while True:
    send_message = input("\nDo you want to send a message to the server? (yes/no): ")
    clientSocket.send(send_message.encode())  # Send the client's response to the server

    if send_message != 'yes':  # If the client says "no", exit the loop
        print("Ending connection with the server.")
        break

    # Input handling
    file_mode = input("Do you want to read inputs from a file? (yes/no): ").strip().lower()
    if file_mode == 'yes':
        file_path = input(r"Enter the file path (for example - C:\Users\ofekb\Downloads\test.txt) : ").strip()
        message, maximum_msg_size, window_size, timeout = read_input_from_file(file_path)

        clientSocket.send(file_path.encode())  # Send the file path to the server
        server_response = clientSocket.recv(4096).decode()  # Receive server response

        if server_response == "ok":
            print(f"The server agreed to the the file max: {maximum_msg_size}")
        else:
            print("The server does not agree to the max message size")

    else:
        print("Waiting for server to enter a maximum message size...")
        max_ask_server = "what is the maximum number of bytes you are willing to receive?"
        clientSocket.send(max_ask_server.encode())  # Send the request to the server

        maximum_msg_size = int(clientSocket.recv(4096).decode())  # Receive the maximum size from the server
        print('Hi client, I\'m willing to receive:', str(maximum_msg_size) + " bytes")  # Display the server's response

        # Get user input for the message and parameters
        message = input('Input a massage: ')
        window_size = input('enter the window size: ')
        timeout = input('enter the timeout: ')
        print("")

    # Split the message into packets
    packets = split_message(message, maximum_msg_size)
    packetsACK = [False] * len(packets)  # List to track acknowledgments for each packet

    # Handle the case where the message cannot be fully sent
    if packets[len(packets) - 1] is None:
        packets.remove(None)  # Remove the invalid packet
        print("The message can't be sent in its entirety due to the maximum message length.")
        print("Sending the parts of the message that can be delivered to the server...\n")

    # Initialize the sliding window protocol
    window_start = 0
    start_time = time.time()  # Record the start time for timeout
    current_time = time.time() - start_time  # Calculate elapsed time
    window_moved = True  # Flag to indicate if the window has moved

    # Sliding window protocol to send packets and handle acknowledgments
    while window_start < len(packets):

        if window_moved:  # Send packets within the window if the window has moved
            for i in range(window_start, min(window_start + int(window_size), len(packets))):
                if not packetsACK[i]:  # Only send unacknowledged packets
                    print(f"Sending packet {i}: {packets[i]}")
                    clientSocket.send(packets[i].encode())  # Send the packet

                    # Immediately receive the acknowledgment
                    ack_from_server = clientSocket.recv(4096).decode()  # Receive acknowledgment
                    ack_number = int(ack_from_server[3:])  # Extract ACK number
                    print(f"Received {ack_from_server}")  # Display the acknowledgment
                    packetsACK[ack_number] = True  # Mark the packet as acknowledged

        window_moved = False  # Reset the window moved flag
        # Slide the window forward
        while window_start < len(packets) and packetsACK[window_start]:
            window_start += 1  # Slide window forward
            print(f"moving window to {window_start}")
            start_time = time.time()  # Update the start time
            window_moved = True

        current_time = time.time() - start_time  # Update the elapsed time

        # reached timeout and needs to send all the false packets
        if current_time >= float(timeout):
            for i in range(window_start, min(window_start + int(window_size), len(packets))):
                if not packetsACK[i]:  # Resend unacknowledged packets
                    print(f"Sending packet {i} again: {packets[i]}")
                    clientSocket.send(packets[i].encode())  # Send the packet

                    # Immediately receive the acknowledgment
                    ack_from_server = clientSocket.recv(4096).decode()  # Receive acknowledgment
                    ack_number = int(ack_from_server[3:])  # Extract ACK number
                    print(f"Received {ack_from_server}")  # Display the acknowledgment
                    for j in range(ack_number + 1):
                        packetsACK[j] = True  # Mark the packet as acknowledged

            start_time = time.time()  # Reset the start time after resending packets

    clientSocket.send("done".encode())  # Indicate the end of the current message

clientSocket.close()  # Close the socket connection

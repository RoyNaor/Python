# import socket
import socket
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
def get_acknowledge(client_socket):
    try:
        client_socket.settimeout(1)  # Set the socket timeout to 1 second
        ack_from_server = client_socket.recv(4096).decode()  # Receive acknowledgment
        ack_number = int(ack_from_server[3:])  # Extract ACK number
        print(f"Received {ack_from_server}")  # Display the acknowledgment
        return ack_number

    except socket.timeout:
        # Handle cases where no acknowledgment is received within the timeout.
        print("No acknowledgment received. Continuing...")
        return None  # Return None if no acknowledgment is received

    except (ValueError, IndexError):
        # Handle invalid or incomplete acknowledgment messages.
        print("incomplete acknowledgment received. Ignoring...")
        return None

    finally:
        client_socket.settimeout(None)  # Reset the timeout to blocking mode


# Function to Handle packet delivery using a sliding window protocol
def send_packets(client_socket, packets, window_size, timeout):

    packetsACK = [False] * len(packets)  # List to track acknowledgments for each packet
    window_start = 0  # Initialize the sliding window protocol
    start_time = time.time()  # Record the start time for timeout
    window_moved = True  # Flag to indicate if the window has moved

    # Sliding window protocol to send packets and handle acknowledgments
    while window_start < len(packets):

        if window_moved:  # Send packets within the window if the window has moved
            for i in range(window_start, min(window_start + int(window_size), len(packets))):
                # Only send unacknowledged packets
                if not packetsACK[i]:
                    print(f"Sending packet {i}: {packets[i]}")
                    client_socket.send(packets[i].encode())  # Send the packet

                    # Immediately receive the acknowledgment
                    ack_number = get_acknowledge(client_socket)
                    if ack_number is not None and ack_number < len(packetsACK):
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
                    client_socket.send(packets[i].encode())  # Send the packet

                    # Immediately receive the acknowledgment
                    ack_number = get_acknowledge(client_socket)
                    for j in range(ack_number + 1):
                        packetsACK[j] = True  # Mark the packet as acknowledged

            start_time = time.time()  # Reset the start time after resending packets


# Function to handle the client-side operations for communication with the server
def client(server_address):
    # Create a TCP socket and connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

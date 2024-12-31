#import socket
from socket import *

# Server setup
HEADER_SIZE = 10
MAX_MSG_SIZE = 8  # Default maximum message size

# Function to extract the packet number and message content from a decoded message
def extract(decoded_msg):
    new_msg = decoded_msg.split("-")  # Split the message into parts using '-'
    packet_identifier = new_msg[0]  # Extract the packet identifier (e.g., 'M0')
    packet_number = int(packet_identifier[1:])  # Extract the packet number by removing 'M'
    message_content = new_msg[1]  # Extract the actual message content

    return packet_number, message_content  # Return the packet number and content


# Function to read the maximum message size from a file
def read_input_from_file(file_path):
    params = {}  # Dictionary to store key-value pairs from the file
    with open(file_path, 'r', encoding='utf-8') as file:  # Open the file
        for line in file:  # Iterate through each line in the file
            key, value = line.split(":", 1)  # split the line into key and value
            params[key.strip()] = value.strip()  # Remove any extra whitespace

    # Return the extracted maximum message size as an integer
    return int(params["maximum_msg_size"])


# Function to Handle the request for maximum message size from the client
def handle_max_msg_size_request(connection_socket):
    max_msg_size = int(input("Enter maximum message size: "))
    print("Maximum message size received, sending to client...\n")
    connection_socket.send(str(max_msg_size).encode())  # Send the maximum size to the client
    return max_msg_size


# Function to Handle the client's request to process a file for maximum message size
def handle_file_request(connection_socket, file_path):
    max_msg_size = read_input_from_file(file_path)  # Read max size from file
    connection_socket.send("ok".encode())  # Send to the client the server received the maximum message size
    return max_msg_size


# Function to Handle packet reception using a sliding window protocol
def handle_packet_reception(connection_socket, max_msg_size):
    packets_received = []  # Stores the received packets
    next_expected_packet = 0  # Tracks the next expected packet number

    print("New Message:")
    while True:
        # Receive a packet from the client
        msg_from_client = connection_socket.recv(max_msg_size + HEADER_SIZE)
        decoded_msg = msg_from_client.decode()

        # Check if the client has finished sending packets
        if not msg_from_client or decoded_msg == "done":
            print("All packets for the current message have been received.")
            break

        # Extract packet number and message content
        packet_number, message_from_client = extract(decoded_msg)

        # Ensure the packets_received list can hold the current packet
        if packet_number >= len(packets_received):
            packets_received.extend([None] * (packet_number - len(packets_received) + 1))

        # Store the packet if not already received
        if packets_received[packet_number] is None:
            packets_received[packet_number] = message_from_client

        # Handle expected packets
        if packet_number == next_expected_packet:
            print(f"Received expected packet {packet_number}")
            next_expected_packet += 1
            while next_expected_packet < len(packets_received) and packets_received[next_expected_packet] is not None:
                next_expected_packet += 1  # Advance through already received packets
        else:
            # Handle out-of-order packets
            print(f"Out-of-order packet {packet_number} received, still waiting for packet {next_expected_packet}")

        # Send acknowledgment for the last successfully received packet
        ack_message = f"ACK{next_expected_packet - 1}"
        connection_socket.send(ack_message.encode())
        print(f"Received packet: {decoded_msg}")
        print(f"Packet size: {len(message_from_client) + HEADER_SIZE} bytes (Header size + Message chunk size) \n")

    # Print all received packets and the complete message
    print("All packets received:", packets_received)
    print("\nMessage:", "".join(packets_received))
    print("")


# Function to handle the server-side operations for managing client connections
def server(server_address):
    # Create and bind the server socket
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(1)  # Listen for a single client connection
    print("The server is ready to receive client")

    # Accept a connection from the client
    connection_socket, addr_client = server_socket.accept()
    print("Connection established\n")

    while True:
        # Check if the client wants to send more messages
        keep_sending = connection_socket.recv(4096).decode().strip().lower()

        if keep_sending != "yes":
            print("\nClient chose to stop sending messages. Closing connection.")
            break

        # Receive the client's request or file path
        sentence = connection_socket.recv(4096).decode()

        # Handle the request based on its type
        if sentence == "what is the maximum number of bytes you are willing to receive?":
            max_msg_size = handle_max_msg_size_request(connection_socket)
        else:
            max_msg_size = handle_file_request(connection_socket, sentence)

        # Receive and process packets from the client
        handle_packet_reception(connection_socket, max_msg_size)

    connection_socket.close()  # Close the connection with the client


if __name__ == "__main__":
    # Start the server on the specified address and port
    SERVER_ADDRESS = ('', 13000)
    server(SERVER_ADDRESS)

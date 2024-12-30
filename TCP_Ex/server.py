#import socket
from socket import *

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


# Server setup
SERVER_ADDRESS = ('', 13000)
MAX_MSG_SIZE = 8  # Default maximum message size
serverSocket = socket(AF_INET, SOCK_STREAM)  # Create a TCP socket

serverSocket.bind(SERVER_ADDRESS)  # Bind the socket to the server address
serverSocket.listen(1)  # Listen for incoming connections

print("The server is ready to receive client")
connectionSocket, addrClient = serverSocket.accept()  # Accept a client connection
print("Connection established\n")

# Main loop to handle communication with the client
while True:
    # Receive the client's response to check if they want to send a message
    keep_sending = connectionSocket.recv(4096).decode().strip().lower()

    # If the client says anything other than "yes", exit the loop and close the connection
    if keep_sending != "yes":
        print("\nClient chose to stop sending messages. Closing connection.")
        break

    # Handle the first message from the client
    sentence = connectionSocket.recv(4096).decode()  # Receive the message from the client
    # If the client asks for the maximum message size, prompt the user to input it
    if sentence == "what is the maximum number of bytes you are willing to receive?":
        MAX_MSG_SIZE = int(input("Enter maximum message size: "))
        print("maximum message size received, sending to client...\n")
        connectionSocket.send(bytes(str(MAX_MSG_SIZE).encode()))  # Send the maximum size to the client

    else:
        # If the client sends a file path, read the maximum size from the file
        MAX_MSG_SIZE = read_input_from_file(sentence)  # read from file
        connectionSocket.send("ok".encode())  # Acknowledge the file processing

    packets_received = []  # List to store received packets
    next_expected_packet = 0  # Track the next expected packet

    # Loop to handle incoming packets from the client
    while True:
        msg_from_client = connectionSocket.recv(int(MAX_MSG_SIZE))  # Receive a packet from the client

        decoded_msg = msg_from_client.decode()  # Decode the received message

        # Check if the client has finished sending packets for this message
        if not msg_from_client or decoded_msg == "done":  # Stop if no data is received or "done" is received
            print("All packets for the current message have been received.")
            break  # Exit the loop as no more packets are expected for the current message

        # Extract the packet number and message content
        packet_number, message_from_client = extract(decoded_msg)

        # Ensure the list is large enough to hold the packet at the correct index
        if packet_number >= len(packets_received):
            packets_received.extend([None] * (packet_number - len(packets_received) + 1))

        # Store the message if it hasn't been received yet
        if packets_received[packet_number] is None:
            packets_received[packet_number] = message_from_client

        # Handle acknowledgment and expected packets
        if packet_number == next_expected_packet:
            # If the received packet is the expected one, advance the expectation
            print(f"Received expected packet {packet_number}")
            next_expected_packet += 1
            while next_expected_packet < len(packets_received) and packets_received[next_expected_packet] is not None:
                next_expected_packet += 1  # Advance through already received packets
        else:
            # Handle out-of-order packets
            print(f"Out-of-order packet {packet_number} received, still waiting for packet {next_expected_packet}")

        # Send acknowledgment for the last successfully received packet in sequence
        ack_message = f"ACK{next_expected_packet - 1}"
        connectionSocket.send(ack_message.encode())  # Send the acknowledgment

        # Print the received packet and its size
        print(f"Received packet: {decoded_msg}")
        print(f"Packet size: {len(msg_from_client)} bytes\n")

    # print the packets received and the complete message
    print("All packets received:", packets_received)
    print("\nmessage:", "".join(packets_received))

# Close the server connection
connectionSocket.close()

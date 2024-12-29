#import socket
from socket import *

def extract(decoded_msg):
    new_msg = decoded_msg.split("-")
    packet_identifier = new_msg[0]  # 'M0'
    packet_number = int(packet_identifier[1:])  # Extract everything after 'M'
    message_content = new_msg[1]  # The actual message content

    return packet_number, message_content

def read_input_from_file(file_path):
    params = {}
    with open(file_path, 'r', encoding='utf-8') as file:  # Open the file
        for line in file:
            key, value = line.split(":", 1)  # Split each line into key and value
            params[key.strip()] = value.strip()  # Remove any extra whitespace

    # Extract and return only the integer value
    return int(params["maximum_msg_size"])


SERVER_ADDRESS = ('', 13000)
MAX_MSG_SIZE = 8
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(SERVER_ADDRESS)
serverSocket.listen(1)

print("The server is ready to receive client")
connectionSocket, addrClient = serverSocket.accept()
print("Connection established\n")


sentence = connectionSocket.recv(4096).decode()
if sentence == "what is the maximum number of bytes you are willing to receive?":
    MAX_MSG_SIZE = int(input("Enter maximum message size: "))
    print("maximum message size received, sending to client...\n")
    connectionSocket.send(bytes(str(MAX_MSG_SIZE).encode()))

else:
    MAX_MSG_SIZE = read_input_from_file(sentence)  # read from file
    connectionSocket.send("ok".encode())

packets_received = []
next_expected_packet = 0  # Track the next expected packet

# Modified while loop to handle packets
while True:
    msg_from_client = connectionSocket.recv(int(MAX_MSG_SIZE))

    if not msg_from_client:  # Break when the client stops sending
        break

    decoded_msg = msg_from_client.decode()  # Decode the received message
    # Send an acknowledgment back to the client
    packet_number, message_from_client = extract(decoded_msg)

    # Ensure the list is large enough to hold the packet at the correct index
    if packet_number >= len(packets_received):
        packets_received.extend([None] * (packet_number - len(packets_received) + 1))

    # Store the message if not already received
    if packets_received[packet_number] is None:
        packets_received[packet_number] = message_from_client

    # Handle acknowledgment
    if packet_number == next_expected_packet:
        # If the received packet is the expected one, advance the expectation
        print(f"Received expected packet {packet_number}")
        next_expected_packet += 1
        while next_expected_packet < len(packets_received) and packets_received[next_expected_packet] is not None:
            next_expected_packet += 1
    else:
        print(f"Out-of-order packet {packet_number} received, still waiting for packet {next_expected_packet}")

    # Send acknowledgment for the last successfully received packet in sequence
    ack_message = f"ACK{next_expected_packet - 1}"
    connectionSocket.send(ack_message.encode())

    # Print the received packet and its length
    print(f"Received packet: {decoded_msg}")
    print(f"Packet size: {len(msg_from_client)} bytes\n")

print("All packets received:", packets_received)
print("\nmessage:", "".join(packets_received))

connectionSocket.close()

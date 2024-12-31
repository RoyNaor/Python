#import socket
from socket import *

HEADER_SIZE = 10
MAX_MSG_SIZE = 8

def extract(decoded_msg):
    """Extract the packet number and message content from a decoded message."""
    new_msg = decoded_msg.split("-")
    packet_identifier = new_msg[0]
    packet_number = int(packet_identifier[1:])
    message_content = new_msg[1]
    return packet_number, message_content

def read_input_from_file(file_path):
    """Read the maximum message size from a file."""
    params = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.split(":", 1)
            params[key.strip()] = value.strip()
    return int(params["maximum_msg_size"])

def handle_max_msg_size_request(connection_socket):
    """Handle the request for maximum message size from the client."""
    max_msg_size = int(input("Enter maximum message size: "))
    print("Maximum message size received, sending to client...\n")
    connection_socket.send(str(max_msg_size).encode())
    return max_msg_size

def handle_file_request(connection_socket, file_path):
    """Handle the client's request to process a file for maximum message size."""
    max_msg_size = read_input_from_file(file_path)
    connection_socket.send("ok".encode())
    return max_msg_size

def handle_packet_reception(connection_socket, max_msg_size):
    """Handle packet reception using a sliding window protocol."""
    packets_received = []
    next_expected_packet = 0

    while True:
        msg_from_client = connection_socket.recv(max_msg_size + HEADER_SIZE)
        decoded_msg = msg_from_client.decode()

        if not msg_from_client or decoded_msg == "done":
            print("All packets for the current message have been received.")
            break

        packet_number, message_from_client = extract(decoded_msg)

        if packet_number >= len(packets_received):
            packets_received.extend([None] * (packet_number - len(packets_received) + 1))

        if packets_received[packet_number] is None:
            packets_received[packet_number] = message_from_client

        if packet_number == next_expected_packet:
            print(f"Received expected packet {packet_number}")
            next_expected_packet += 1
            while next_expected_packet < len(packets_received) and packets_received[next_expected_packet] is not None:
                next_expected_packet += 1
        else:
            print(f"Out-of-order packet {packet_number} received, still waiting for packet {next_expected_packet}")

        ack_message = f"ACK{next_expected_packet - 1}"
        connection_socket.send(ack_message.encode())
        print(f"Received packet: {decoded_msg}")
        print(f"Packet size: {len(message_from_client) + HEADER_SIZE} bytes (Header size + Message chunk size) \n")

    print("All packets received:", packets_received)
    print("\nMessage:", "".join(packets_received))
    print("")

def server(server_address):
    """Start the server and handle client connections."""
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(1)
    print("The server is ready to receive client")

    connection_socket, addr_client = server_socket.accept()
    print("Connection established\n")

    while True:
        keep_sending = connection_socket.recv(4096).decode().strip().lower()

        if keep_sending != "yes":
            print("\nClient chose to stop sending messages. Closing connection.")
            break

        sentence = connection_socket.recv(4096).decode()

        if sentence == "what is the maximum number of bytes you are willing to receive?":
            max_msg_size = handle_max_msg_size_request(connection_socket)
        else:
            max_msg_size = handle_file_request(connection_socket, sentence)

        handle_packet_reception(connection_socket, max_msg_size)

    connection_socket.close()

if __name__ == "__main__":
    SERVER_ADDRESS = ('', 13000)
    server(SERVER_ADDRESS)
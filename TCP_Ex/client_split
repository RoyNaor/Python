# import socket
from socket import *
import time

def split_message(message, max_size):
    """Split a message into packets of a specific size."""
    message_bytes = message.encode()
    result = []
    index = 0
    start_index = 0

    while start_index < len(message_bytes):
        prefix = f"M{index}-"
        remaining_bytes = message_bytes[start_index:]
        chunk = remaining_bytes[:max_size]

        while True:
            try:
                decoded_chunk = chunk.decode("utf-8")
                break
            except UnicodeDecodeError:
                chunk = chunk[:-1]

        packet = f"{prefix}{decoded_chunk}"
        result.append(packet)
        start_index += len(chunk)
        index += 1

    return result

def read_input_from_file(file_path):
    """Read input parameters from a file."""
    params = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.split(":", 1)
            params[key.strip()] = value.strip()

    return (
        params["message"],
        int(params["maximum_msg_size"]),
        int(params["window_size"]),
        int(params["timeout"])
    )

def handle_file_mode(client_socket):
    """Handle inputs in file mode."""
    file_path = input(r"Enter the file path (e.g., C:\\path\\to\\file.txt): ").strip()
    message, max_msg_size, window_size, timeout = read_input_from_file(file_path)

    client_socket.send(file_path.encode())
    server_response = client_socket.recv(4096).decode()

    if server_response == "ok":
        print(f"The server agreed to the max: {max_msg_size}")
    else:
        print("The server does not agree to the max message size")

    return message, max_msg_size, window_size, timeout

def handle_manual_mode(client_socket):
    """Handle inputs in manual mode."""
    print("Waiting for server to enter a maximum message size...")
    max_ask_server = "what is the maximum number of bytes you are willing to receive?"
    client_socket.send(max_ask_server.encode())

    max_msg_size = int(client_socket.recv(4096).decode())
    print(f"Server: willing to receive {max_msg_size} bytes")

    message = input("Input a message: ")
    window_size = int(input("Enter the window size: "))
    timeout = float(input("Enter the timeout (in seconds): "))
    print("")

    return message, max_msg_size, window_size, timeout

def send_packets(client_socket, packets, window_size, timeout):
    """Send packets using a sliding window protocol."""
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

def client(server_address):
    """Handle client-side operations for communication with the server."""
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
    SERVER_ADDRESS = ('localhost', 13000)
    client(SERVER_ADDRESS)

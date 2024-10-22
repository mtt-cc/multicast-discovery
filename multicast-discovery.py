import socket
import struct
import sys
import time
import os
from datetime import datetime

# Multicast group and port
MULTICAST_GROUP = '224.1.1.1'  # Example multicast address
PORT = 5004                   # Example port

# Announcement messages
ANNOUNCEMENT_MSG = "Hello, I'm here!"
ACK_MSG = "announce_ack"

# Directory to save incoming messages
LOG_DIR = 'logs'

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generate the filename based on the current date
current_date = datetime.now().strftime('%Y-%m-%d')
FILENAME = os.path.join(LOG_DIR, f'{current_date}_received_messages.txt')


def main():
    # Dictionary to store known hosts
    known_hosts = {}

    # Create the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allow multiple sockets to use the same PORT number
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to the server address
    sock.bind(('', PORT))

    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    try:
        # Announce presence to others in the group
        print("Sending announcement...")
        sock.sendto(ANNOUNCEMENT_MSG.encode(), (MULTICAST_GROUP, PORT))

        # Open a file to save incoming messages
        with open(FILENAME, 'a') as f:
            print("Listening for messages...")
            while True:
                # Receive/respond loop
                try:
                    data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
                    message = data.decode()
                    print(f"Received message from {addr}: {message}")

                    # Save the message to a file
                    f.write(f"{time.ctime()}: {addr} -> {message}\n")
                    f.flush()  # Ensure immediate writing to the file

                    # If it's an announcement message and the host is not known
                    if message == ANNOUNCEMENT_MSG and addr[0] not in known_hosts:
                        # Add the host to the dictionary
                        known_hosts[addr[0]] = time.time()
                        print(f"New host detected: {addr[0]}")

                        # Send unicast announce_ack back to the new host
                        ack_message = f"{ACK_MSG}"
                        sock.sendto(ack_message.encode(), addr)
                        print(f"Sent {ACK_MSG} to {addr[0]}")

                    # If we receive an "announce_ack"
                    elif message == ACK_MSG:
                        print(f"Received {ACK_MSG} from {addr[0]}")

                except KeyboardInterrupt:
                    print("\nExiting...")
                    break

    finally:
        # Close the socket to release resources
        print("Closing socket...")
        sock.close()

if __name__ == "__main__":
    main()

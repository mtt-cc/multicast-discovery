import socket
import struct
import time

# Multicast group and port
MULTICAST_GROUP = '224.1.1.1'  # Example multicast address
PORT = 5004                   # Example port

# Announcement messages
ANNOUNCEMENT_MSG = "Hello, I'm here!"
ACK_MSG = "announce_ack"

# Filename to save incoming messages
FILENAME = 'received_messages.txt'

def main():
    # Dictionary to store known hosts
    known_hosts = {}

    # Create the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allow multiple sockets to use the same PORT number
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Disable multicast loopback
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

    # Bind to the server address
    sock.bind(('', PORT))

    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    last_announce_time = time.time()  # Track the time of the last announcement

    try:
        # Open a file to save incoming messages
        with open(FILENAME, 'a') as f:
            print("Listening for messages...")
            print("Sending announcement...")
            sock.sendto(ANNOUNCEMENT_MSG.encode(), (MULTICAST_GROUP, PORT))
            while True:
                # Check if 30 seconds have passed since the last announcement
                current_time = time.time()
                if current_time - last_announce_time >= 30:
                    print("Sending announcement...")
                    sock.sendto(ANNOUNCEMENT_MSG.encode(), (MULTICAST_GROUP, PORT))
                    last_announce_time = current_time  # Update the time of the last announcement

                # Use non-blocking receive to avoid blocking the announcement
                sock.settimeout(1)  # Set a timeout of 1 second for receiving messages
                try:
                    data, addr = sock.recvfrom(1024*1024)  # Buffer size is 1MB
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

                except socket.timeout:
                    # No data received, just continue the loop to check for timeouts
                    pass

                except KeyboardInterrupt:
                    print("\nExiting...")
                    break

    finally:
        # Close the socket to release resources
        print("Closing socket...")
        sock.close()

        print("Known hosts:")
        for elem in known_hosts.keys():
            print(elem)

        exit(0)

if __name__ == "__main__":
    main()

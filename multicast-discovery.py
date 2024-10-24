import socket
import struct
import sys
import time

# Multicast group and port
MULTICAST_GROUP = '224.1.1.1'
PORT = 5004

# Announcement messages
ANNOUNCEMENT_MSG = "Hello, I'm here!"
ACK_MSG = "announce_ack"

# Time between announcements
ANNOUNCE_TIME = 30
# Time-to-live for known hosts (30 seconds)
HOST_TTL = 30

# Filename to save incoming messages
FILENAME = 'received_messages.txt'

# Buffer size for incoming messages
BUF_SIZE = 1024*1024



def main():
    # Dictionary to store known hosts with the time of last activity
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

    try:
        # Announce presence to others in the group
        print("Sending announcement...")
        sock.sendto(ANNOUNCEMENT_MSG.encode(), (MULTICAST_GROUP, PORT))

        # Open a file to save incoming messages
        with open(FILENAME, 'a') as f:
            print("Listening for messages...")
            last_announcement_time = time.time()

            while True:
                # Announce every 30 seconds
                current_time = time.time()
                if current_time - last_announcement_time >= ANNOUNCE_TIME:
                    print("Sending periodic announcement...")
                    sock.sendto(ANNOUNCEMENT_MSG.encode(), (MULTICAST_GROUP, PORT))
                    last_announcement_time = current_time

                # Remove expired hosts
                expired_hosts = [host for host, last_seen in known_hosts.items() 
                                 if current_time - last_seen > HOST_TTL]
                for host in expired_hosts:
                    print(f"Removing expired host: {host}")
                    del known_hosts[host]

                # Check for incoming messages with a 1-second timeout
                sock.settimeout(1)
                try:
                    data, addr = sock.recvfrom(BUF_SIZE)  # Buffer size is 1024 bytes
                    message = data.decode()
                    print(f"Received message from {addr}: {message}")

                    # Save the message to a file
                    f.write(f"{time.ctime()}: {addr} -> {message}\n")
                    f.flush()  # Ensure immediate writing to the file

                    # If it's an announcement message and the host is not known
                    if message == ANNOUNCEMENT_MSG:
                        # Update or add the host with the current timestamp
                        known_hosts[addr[0]] = current_time
                        if addr[0] not in known_hosts:
                            print(f"New host detected: {addr[0]}")

                        # Send unicast announce_ack back to the new host
                        ack_message = f"{ACK_MSG}"
                        sock.sendto(ack_message.encode(), addr)
                        print(f"Sent {ACK_MSG} to {addr[0]}")

                    # If we receive an "announce_ack"
                    elif message == ACK_MSG:
                        print(f"Received {ACK_MSG} from {addr[0]}")
                        # Update the timestamp for the responding host
                        known_hosts[addr[0]] = current_time

                except socket.timeout:
                    # Timeout after 1 second, continue the loop to send announcements or check for expiration
                    pass
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break

    finally:
        # print known hosts
        print("Known hosts:")
        for host in known_hosts.keys():
            print(f"{host}")
        # Close the socket to release resources
        print("Closing socket...")
        sock.close()

if __name__ == "__main__":
    main()

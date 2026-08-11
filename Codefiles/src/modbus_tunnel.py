import time
import getpass
import logging
from sshtunnel import SSHTunnelForwarder

# Suppress verbose SSH logs for a cleaner console
logging.getLogger("sshtunnel").setLevel(logging.CRITICAL)

print("=== Modbus/TCP SSH Tunnel Setup ===")
print("This script uses the Python 'sshtunnel' library to securely route Modbus traffic.")
print("(Ensure 'Remote Login' is enabled in your macOS System Settings)\n")

ssh_username = input("Enter your macOS username (e.g., vedha): ")
ssh_password = getpass.getpass("Enter your macOS password (text will be hidden): ")

try:
    # Set up the SSH tunnel
    tunnel = SSHTunnelForwarder(
        ('127.0.0.1', 22), # Connect to the local Mac SSH server
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=('127.0.0.1', 5020), # Where the traffic is dropped off (Modbus Server)
        local_bind_address=('127.0.0.1', 2222)   # The local tunnel entrance
    )
    
    tunnel.start()
    print(f"\n[+] SUCCESS! SSH Tunnel established.")
    print(f"    Local Entrance: Port {tunnel.local_bind_port}")
    print(f"    Remote Destination: Port 5020")
    print("\nYou can now open a new terminal and run `make client-tunnel`.")
    print("Press Ctrl+C to close the tunnel and exit.")
    
    # Keep the script running to keep the tunnel open
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nClosing tunnel...")
    tunnel.stop()
    print("Tunnel closed. Goodbye!")
except Exception as e:
    print(f"\n[-] Failed to start the tunnel. Error: {e}")
    print("Please double check that 'Remote Login' is enabled and your username/password are correct.")

# Wireshark Testing Guide
## Testing and Capturing Traffic with Wireshark

This guide provides a step-by-step process for running the Modbus/TCP project, testing it with Wireshark, and capturing the network traffic.

### Prerequisites

1.  **Install dependencies:** Ensure all Python dependencies are installed.
    ```bash
    cd /Users/vedha/Documents/ESD - Modbus:TCP
    make install
    ```
2.  **Enable Remote Login (macOS):** SSH tunneling requires an SSH server. On macOS, enable it via:
    *   System Settings -> General -> Sharing
    *   Turn on **Remote Login**.

---

### Scenario 1: Direct Mode (Unencrypted Modbus)

In this scenario, we will run the client directly to the server on port 5020. The traffic will be unencrypted, and Wireshark will be able to decode the Modbus packets.

#### Step 1: Start the Modbus Server
Open **Terminal 1** and start the server:
```bash
cd "/Users/vedha/Documents/ESD - Modbus:TCP"
make server
# Alternatively: python3 src/modbus_server.py
```

#### Step 2: Listen Live in Wireshark
Instead of capturing to a file, you can listen to the traffic live using the Wireshark graphical application:
1.  Open **Wireshark**.
2.  Select the **Loopback: lo0** interface from the capture list.
3.  In the display filter bar at the top, type `tcp.port == 5020` and press Enter to filter out unrelated traffic.
4.  Leave Wireshark running in the background.

#### Step 3: Run the Modbus Client
While the capture is running, open **Terminal 2** and run the client in direct mode:
```bash
cd "/Users/vedha/Documents/ESD - Modbus:TCP"
make client
# Alternatively: python3 src/modbus_client.py --mode direct
```

#### Step 4: Analyze Live in Wireshark
1.  Switch back to **Wireshark**.
2.  You will see the new packets appear in real-time, clearly decoded as `Modbus/TCP`.
3.  If you click on a packet, you can see the Function Codes (e.g., `0x03` for Read Holding Registers) and the actual register values in plaintext in the packet details pane.

---

### Scenario 2: Tunnel Mode (Encrypted via SSH)

In this scenario, we establish an SSH tunnel and route the Modbus traffic through it. The traffic on the network will be encrypted SSH traffic.

#### Step 1: Start the SSH Tunnel
Keep the Modbus server running in Terminal 1. Open **Terminal 3** and start the SSH tunnel:
```bash
cd "/Users/vedha/Documents/ESD - Modbus:TCP"
make tunnel-native
# Alternatively, to use the Python tunnel: make tunnel-python
```
*This establishes an encrypted SSH tunnel on local port 2222 linking to localhost:5020.*

#### Step 2: Listen Live in Wireshark
We will monitor the encrypted traffic on the standard SSH port (22) on the loopback interface.
1.  Switch back to Wireshark (you can stop the previous capture by clicking the red square).
2.  Start a new capture on the **Loopback: lo0** interface.
3.  In the display filter bar at the top, type `tcp.port == 22` and press Enter.
4.  Leave Wireshark running in the background.

#### Step 3: Run the Modbus Client
While the capture is running, open **Terminal 4** and run the client in tunnel mode:
```bash
cd "/Users/vedha/Documents/ESD - Modbus:TCP"
make client-tunnel
# Alternatively: python3 src/modbus_client.py --mode tunnel
```
*The client connects to `localhost:2222`, which securely routes the traffic to the server.*

#### Step 4: Analyze Live in Wireshark
1.  Switch back to **Wireshark**.
2.  You will see the new packets appear in real-time. Notice they are identified as `SSHv2` and not Modbus.
3.  The Modbus data is completely hidden within the encrypted payload. No function codes or register values are visible in the packet details pane.

---

### Automated Latency Benchmarking

To prove that the SSH tunnel overhead is feasible for embedded environments, the project includes an automated Python script to programmatically measure the latency difference across all three scenarios (Plaintext, Native Tunnel, and Python Tunnel).

Run this command:
```bash
cd "/Users/vedha/Documents/ESD - Modbus:TCP"
make benchmark
```
This script will send thousands of packets, measure the average latency, track the CPU usage, and output a side-by-side 3-column bar chart (`benchmark_results.png`) proving the performance impact.

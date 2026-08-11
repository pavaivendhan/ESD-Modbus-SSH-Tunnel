# ==============================================================================
# modbus_server.py
# ==============================================================================
import asyncio
import logging
import threading
import time
import RPi.GPIO as GPIO
import board
import busio
import digitalio
import adafruit_max31855
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# --- Motor Speed Global Variables ---
pulse_count = 0
pulse_lock = threading.Lock()
rpm = 0

def rpm_callback(channel):
    global pulse_count
    with pulse_lock:
        pulse_count += 1

def sensor_updater(context):
    global pulse_count, rpm
    
    # 1. Setup Temp Sensor (SPI)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)
    max31855 = adafruit_max31855.MAX31855(spi, cs)
    
    # 2. Setup Speed Sensor (GPIO Interrupt)
    TACHO_PIN = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TACHO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(TACHO_PIN, GPIO.FALLING, callback=rpm_callback)
    
    while True:
        with pulse_lock:
            current_pulses = pulse_count
            pulse_count = 0
            
        rpm = (current_pulses / 20) * 60
        
        try:
            temp_c = int(max31855.temperature)
        except RuntimeError:
            temp_c = 0
            
        # Update Modbus Registers
        context[0].setValues(3, 1, [temp_c])
        context[0].setValues(3, 2, [int(rpm)])
        
        time.sleep(1)

async def run_server():
    # Setup data store (simulating embedded device registers)
    # We initialize 100 registers with the value 0
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 100), # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0] * 100), # Coils
        hr=ModbusSequentialDataBlock(0, [0] * 100), # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0] * 100), # Input Registers
    )
    context = ModbusServerContext(slaves=store, single=True)
    
    # Start the hardware background task
    threading.Thread(target=sensor_updater, args=(context,), daemon=True).start()

    # Setup device identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Embedded Security Course'
    identity.ProductCode = 'ESC-001'
    identity.VendorUrl = 'http://github.com/pymodbus-dev/pymodbus/'
    identity.ProductName = 'Modbus Server Setup'
    identity.ModelName = 'Virtual PLC'
    identity.MajorMinorRevision = '1.0'

    log.info("Starting Modbus TCP Server on localhost:5020")
    
    # Start the server on port 5020
    await StartAsyncTcpServer(
        context=context,
        identity=identity,
        address=("127.0.0.1", 5020)
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("Server stopped.")

# ==============================================================================
# modbus_client.py
# ==============================================================================
import time
import argparse
import logging
from pymodbus.client import ModbusTcpClient

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

SERVER_HOST = '127.0.0.1'

def run_client(port):
    client = ModbusTcpClient(SERVER_HOST, port=port)
    
    log.info(f"Connecting to Modbus Server at {SERVER_HOST}:{port}")
    connection = client.connect()
    
    if not connection:
        log.error("Failed to connect to the server. Is it running?")
        return

    try:
        # Loop to read continuous traffic for Wireshark capturing
        for i in range(5):
            temp_address = 1
            speed_address = 2
            
            # Read physical values from the server
            temp_result = client.read_holding_registers(temp_address, count=1)
            if not temp_result.isError():
                log.info(f"Read Boiler Temp from register {temp_address}: {temp_result.registers[0]}°C")
                
            speed_result = client.read_holding_registers(speed_address, count=1)
            if not speed_result.isError():
                log.info(f"Read Motor Speed from register {speed_address}: {speed_result.registers[0]} RPM")
                
            time.sleep(1)
            print("-" * 30)

    except Exception as e:
        log.error(f"An error occurred: {e}")
    finally:
        client.close()
        log.info("Connection closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modbus TCP Client")
    parser.add_argument('--mode', type=str, choices=['direct', 'tunnel'], default='direct', help="Connection mode")
    args = parser.parse_args()
    
    port = 5020 if args.mode == 'direct' else 2222
    
    run_client(port)

# ==============================================================================
# modbus_tunnel.py
# ==============================================================================
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

# ==============================================================================
# modbus_benchmark.py
# ==============================================================================
import time
import argparse
import logging
import psutil
import matplotlib.pyplot as plt
import numpy as np
import os
from pymodbus.client import ModbusTcpClient

# Suppress pymodbus info logs to keep the console output clean
logging.getLogger('pymodbus').setLevel(logging.CRITICAL)

def benchmark_port(port, iterations):
    client = ModbusTcpClient('127.0.0.1', port=port)
    connection = client.connect()
    
    if not connection:
        print(f"[!] Failed to connect to port {port}. Is the server/tunnel running?")
        return None, None

    print(f"Executing {iterations} consecutive read requests...")
    
    # Warmup (ensures connection is stable)
    client.read_holding_registers(1, count=1)
    
    # Start CPU tracking
    psutil.cpu_percent(interval=None) 
    start_time = time.time()
    
    # Execution
    errors = 0
    for _ in range(iterations):
        result = client.read_holding_registers(1, count=1)
        if result.isError():
            errors += 1
            
    end_time = time.time()
    # Read CPU usage since start
    cpu_usage = psutil.cpu_percent(interval=None) 
    client.close()
    
    # Calculate metrics
    total_time = end_time - start_time
    avg_latency = (total_time / iterations) * 1000 # Convert to milliseconds
    
    print(f"  -> Avg Latency: {avg_latency:.4f} ms")
    print(f"  -> CPU Usage:   {cpu_usage:.2f}%")
    if errors > 0:
        print(f"  -> Errors encountered: {errors}")
        
    return avg_latency, cpu_usage

def generate_graphs(plain_latency, native_ssh_latency, py_ssh_latency, plain_cpu, native_ssh_cpu, py_ssh_cpu):
    labels = ['Plaintext\n(Port 5020)', 'Native SSH\n(Port 2222)', 'Python SSH\n(Port 2222)']
    latencies = [plain_latency, native_ssh_latency, py_ssh_latency]
    cpus = [plain_cpu, native_ssh_cpu, py_ssh_cpu]

    x = np.arange(len(labels))
    width = 0.35

    # Create plot with 2 subplots side-by-side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Latency Chart
    rects1 = ax1.bar(x, latencies, width, color=['#3498db', '#e74c3c', '#9b59b6'])
    ax1.set_ylabel('Average Latency (ms)')
    ax1.set_title('Modbus/TCP Latency Overhead')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.bar_label(rects1, fmt='%.2f', padding=3)

    # CPU Chart
    rects2 = ax2.bar(x, cpus, width, color=['#2ecc71', '#f39c12', '#e67e22'])
    ax2.set_ylabel('CPU Usage (%)')
    ax2.set_title('CPU Overhead')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.bar_label(rects2, fmt='%.2f', padding=3)

    fig.tight_layout()
    
    # Ensure docs/images directory exists
    os.makedirs('docs/images', exist_ok=True)
    save_path = 'docs/images/benchmark_results.png'
    plt.savefig(save_path)
    print(f"\n[+] Success! Graph saved to '{save_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modbus TCP Graphing Benchmark")
    parser.add_argument('-i', '--iterations', type=int, default=1000, help="Number of read iterations")
    args = parser.parse_args()
    
    print("=== Phase 1: Benchmarking Plaintext Modbus (Port 5020) ===")
    plain_lat, plain_cpu = benchmark_port(5020, args.iterations)
    
    if plain_lat is None:
        exit(1)
        
    print("\n=== Phase 2: Benchmarking Native SSH Tunnel (Port 2222) ===")
    print("Please open a new terminal and run: ssh -N -L 2222:127.0.0.1:5020 $(whoami)@127.0.0.1")
    input("Press Enter once the native SSH tunnel is running...")
    
    native_ssh_lat, native_ssh_cpu = benchmark_port(2222, args.iterations)
    
    if native_ssh_lat is None:
        exit(1)
        
    print("\n=== Phase 3: Benchmarking Python SSH Tunnel (Port 2222) ===")
    print("Please KILL the native SSH tunnel (Ctrl+C), then run: make tunnel-python")
    input("Press Enter once the Python SSH tunnel is running...")
    
    py_ssh_lat, py_ssh_cpu = benchmark_port(2222, args.iterations)
    
    if py_ssh_lat is None:
        exit(1)
        
    print("\n=== Generating Visualization Graphs ===")
    generate_graphs(plain_lat, native_ssh_lat, py_ssh_lat, plain_cpu, native_ssh_cpu, py_ssh_cpu)

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
    print("Please KILL the native SSH tunnel (Ctrl+C), then run: make tunnel")
    input("Press Enter once the Python SSH tunnel is running...")
    
    py_ssh_lat, py_ssh_cpu = benchmark_port(2222, args.iterations)
    
    if py_ssh_lat is None:
        exit(1)
        
    print("\n=== Generating Visualization Graphs ===")
    generate_graphs(plain_lat, native_ssh_lat, py_ssh_lat, plain_cpu, native_ssh_cpu, py_ssh_cpu)

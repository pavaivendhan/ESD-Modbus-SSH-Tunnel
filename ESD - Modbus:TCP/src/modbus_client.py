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
        # Loop to simulate continuous traffic for Wireshark capturing
        for i in range(5):
            # Write to a holding register
            address = 1
            value = 100 + i
            log.info(f"Writing value {value} to holding register {address}")
            write_result = client.write_register(address, value)
            if write_result.isError():
                log.error("Error writing register")
            
            time.sleep(1)

            # Read from the holding register
            read_result = client.read_holding_registers(address, count=1)
            if not read_result.isError():
                log.info(f"Read value from holding register {address}: {read_result.registers[0]}")
            else:
                log.error("Error reading register")
                
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

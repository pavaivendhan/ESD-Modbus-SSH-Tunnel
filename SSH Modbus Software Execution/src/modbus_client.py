import time
import argparse
import logging
import random
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
            # Simulate Boiler Temperature (Register 1)
            temp_address = 1
            temp_value = random.randint(75, 80)
            log.info(f"Writing Boiler Temp {temp_value}°C to register {temp_address}")
            client.write_register(temp_address, temp_value)
            
            # Simulate Motor Speed (Register 2)
            speed_address = 2
            speed_value = random.randint(1450, 1500)
            log.info(f"Writing Motor Speed {speed_value} RPM to register {speed_address}")
            client.write_register(speed_address, speed_value)
            
            time.sleep(1)

            # Read them back
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

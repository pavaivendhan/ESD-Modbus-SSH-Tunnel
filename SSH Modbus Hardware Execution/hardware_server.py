import asyncio
import logging
import threading
import time
import RPi.GPIO as GPIO
from w1thermsensor import W1ThermSensor, Sensor
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
    
    # 1. Setup Temp Sensor (DS18B20 on 1-Wire / GPIO 4)
    # The W1ThermSensor library automatically finds the connected DS18B20
    try:
        temp_sensor = W1ThermSensor()
    except Exception as e:
        log.warning(f"Could not initialize DS18B20: {e}. Is 1-Wire enabled in raspi-config?")
        temp_sensor = None
    
    # 2. Setup Speed Sensor (GPIO Interrupt for Optical Broken Module on GPIO 17)
    TACHO_PIN = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TACHO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # The optical module triggers on FALLING edge when a slot passes
    GPIO.add_event_detect(TACHO_PIN, GPIO.FALLING, callback=rpm_callback)
    
    while True:
        with pulse_lock:
            current_pulses = pulse_count
            pulse_count = 0
            
        # Assuming 20 slots on the encoder disk (adjust if different)
        rpm = (current_pulses / 20) * 60
        
        try:
            # Read temperature from DS18B20
            if temp_sensor:
                temp_c = temp_sensor.get_temperature()
            else:
                temp_c = 0
        except Exception as error:
            log.warning(f"Failed to read temperature: {error}")
            temp_c = 0
            
        # Update Modbus Registers (hr = holding registers = 3)
        context[0].setValues(3, 1, [int(temp_c)])
        context[0].setValues(3, 2, [int(rpm)])
        
        time.sleep(1) # Read every 1 second

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

    log.info("Starting Physical Modbus TCP Server on localhost:5020")
    
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

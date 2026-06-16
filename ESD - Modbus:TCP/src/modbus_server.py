import asyncio
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

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

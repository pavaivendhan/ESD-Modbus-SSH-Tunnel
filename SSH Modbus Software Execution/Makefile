.PHONY: install server client client-tunnel benchmark tunnel-native tunnel-python clean

# Default target
all: help

help:
	@echo "Available commands:"
	@echo "  make install    - Install required Python dependencies"
	@echo "  make server     - Start the Modbus/TCP server on port 5020"
	@echo "  make client     - Start the Modbus/TCP client (direct mode)"
	@echo "  make client-tunnel- Start the Modbus/TCP client (tunnel mode)"
	@echo "  make benchmark  - Run the latency benchmark script"
	@echo "  make tunnel-native   - Start the native SSH tunnel (Inbuild)"
	@echo "  make tunnel-python   - Start the Python SSH tunnel (External)"
	@echo "  make clean           - Remove Python cache files"

install:
	pip install -r requirements.txt

server:
	python3 src/modbus_server.py

client:
	python3 src/modbus_client.py --mode direct

client-tunnel:
	python3 src/modbus_client.py --mode tunnel

benchmark:
	python3 src/modbus_benchmark.py

tunnel-native:
	@echo "Starting Native SSH Tunnel (Inbuild) on port 2222..."
	ssh -N -L 2222:127.0.0.1:5020 $$(whoami)@127.0.0.1

tunnel-python:
	python3 src/modbus_tunnel.py

clean:
	rm -rf src/__pycache__
	rm -rf venv

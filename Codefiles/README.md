# Embedded Security: Modbus/TCP SSH Tunneling

This project implements a secure SSH tunnel for industrial Modbus/TCP communication to mitigate the inherent lack of encryption in the Modbus protocol.

## Directory Structure

*   `src/` - Contains all Python source code (Server, Client, Tunnel, Benchmark).
*   `docs/` - Contains all final PDF reports, testing guides, and presentation slides.
*   `docs/markdown/` - Contains the raw Markdown source files for the documentation.
*   `docs/images/` - Contains the generated graphs and diagrams.
*   `Makefile` - Automation script for easily running project components.
*   `requirements.txt` - Python dependencies.

## Quick Start

Ensure you have Python 3 installed. Navigate to this directory in your terminal and run:

```bash
make install
```

### Available Commands

*   `make server` - Starts the Modbus/TCP Virtual PLC on port 5020.
*   `make client` - Runs the client in direct (insecure) mode.
*   `make client-tunnel` - Runs the client in tunnel (secure) mode via port 2222.
*   `make tunnel-native` - Establishes the SSH tunnel using native macOS OS commands.
*   `make tunnel-python` - Establishes the SSH tunnel using a custom Python script.
*   `make benchmark` - Runs an automated 3-phase latency test and generates a performance graph.

Please refer to the **`docs/Testing_Guide.pdf`** for detailed step-by-step testing instructions.

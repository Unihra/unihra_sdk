import json
import os
import subprocess
import sys


def print_cursor_config_example():
    config = {
        "mcpServers": {
            "unihra": {
                "command": "python",
                "args": ["-m", "unihra.mcp_server"],
                "env": {
                    "UNIHRA_API_KEY": "YOUR_KEY_HERE"
                }
            }
        }
    }
    print("Cursor/Claude MCP config example:")
    print(json.dumps(config, indent=2, ensure_ascii=False))


def run_server_example():
    """
    Minimal local start example.
    Requires:
    1) pip install 'unihra[mcp]'
    2) UNIHRA_API_KEY in environment
    """
    api_key = os.getenv("UNIHRA_API_KEY")
    if not api_key:
        print("Set UNIHRA_API_KEY to run this example.")
        return

    command = [sys.executable, "-m", "unihra.mcp_server", "--retries", "3"]
    print("Starting MCP server:", " ".join(command))
    print("Stop with Ctrl+C")

    # NOTE:
    # MCP server communicates over stdio. Run it from a host that supports MCP
    # (Cursor, Claude Desktop, etc.), or keep this process for local smoke checks.
    subprocess.run(command, check=False)


if __name__ == "__main__":
    print_cursor_config_example()
    run_server_example()

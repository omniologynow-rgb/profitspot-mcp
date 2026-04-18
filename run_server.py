#!/usr/bin/env python3
"""
Standalone runner for `fastmcp run run_server.py`
This file uses absolute imports so fastmcp CLI can load it directly.

Usage:
  fastmcp dev  run_server.py         # Dev mode with inspector
  fastmcp run  run_server.py         # Production (stdio)
  fastmcp run  run_server.py --transport sse --port 8080  # HTTP/SSE
"""
import sys
import os

# Add src to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from profitspot_mcp.server import mcp  # noqa: E402

# This is what fastmcp looks for
if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8080)

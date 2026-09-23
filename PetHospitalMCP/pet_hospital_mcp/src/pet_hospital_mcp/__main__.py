"""Entry point for the pet-hospital-mcp server."""

import asyncio
import sys
import logging

from pet_hospital_mcp.config import SETTINGS
from pet_hospital_mcp.logging_config import setup_logging
from pet_hospital_mcp.server import run_async


def main() -> None:
    setup_logging()
    logger = logging.getLogger("pet_hospital_mcp")
    logger.info("Starting Pet Hospital MCP server", extra={
        "host": SETTINGS.mcp_host,
        "port": SETTINGS.mcp_port,
        "pet_hospital_base_url": SETTINGS.pet_hospital_base_url,
    })
    print(f"  MCP endpoint: http://{SETTINGS.mcp_address}/mcp")
    print(f"  Health check: http://{SETTINGS.mcp_address}/health")
    print(f"  Backend:      {SETTINGS.pet_hospital_base_url}")
    print()
    try:
        asyncio.run(run_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()

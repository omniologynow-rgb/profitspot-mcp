FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir -e "."

# Default: stdio transport for MCP protocol
CMD ["python", "-m", "profitspot_mcp.server"]

EXPOSE 8080

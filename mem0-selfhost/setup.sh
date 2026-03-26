#!/bin/bash
set -e

echo "=== Mem0 OpenMemory Self-Hosted Setup ==="
echo ""

# Step 1: Start Ollama + Qdrant first
echo "[1/4] Starting Ollama and Qdrant..."
docker compose up -d ollama qdrant
echo "Waiting for Ollama to be ready..."
sleep 5

# Step 2: Pull required models
echo "[2/4] Pulling Ollama models (this may take a few minutes)..."
docker exec mem0-ollama ollama pull llama3.1:latest
docker exec mem0-ollama ollama pull nomic-embed-text:latest
echo "Models pulled successfully."

# Step 3: Start the full stack
echo "[3/4] Starting Mem0 API and UI..."
docker compose up -d
echo "Waiting for services to stabilize..."
sleep 10

# Step 4: Verify
echo "[4/4] Verifying services..."
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "  [OK] $name is running"
    else
        echo "  [!!] $name may not be ready yet — check 'docker compose logs $name'"
    fi
}

check_service "Ollama"    "http://localhost:11434"
check_service "Qdrant"    "http://localhost:6333/dashboard/"
check_service "Mem0 API"  "http://localhost:8765/docs"
check_service "Mem0 UI"   "http://localhost:3000"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services:"
echo "  Ollama:    http://localhost:11434"
echo "  Qdrant:    http://localhost:6333"
echo "  Mem0 API:  http://localhost:8765 (docs at /docs)"
echo "  Mem0 UI:   http://localhost:3000"
echo ""
echo "MCP endpoint for OpenClaw:"
echo "  http://localhost:8765/mcp/openclaw/sse/james"
echo ""
echo "To connect OpenClaw, add to your MCP config:"
echo '  "mem0": {'
echo '    "url": "http://localhost:8765/mcp/openclaw/sse/james"'
echo '  }'

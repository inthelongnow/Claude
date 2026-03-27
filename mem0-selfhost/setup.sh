#!/bin/bash
set -e

echo "=== Mem0 OpenMemory Self-Hosted Setup ==="
echo ""

# Step 1: Verify Ollama is running on the host
echo "[1/3] Checking Ollama on host..."
if curl -sf "http://localhost:11434" > /dev/null 2>&1; then
    echo "  [OK] Ollama is running"
else
    echo "  [!!] Ollama is not running. Start it with: ollama serve"
    exit 1
fi

# Verify required models
echo "  Checking models..."
if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    echo "  [OK] nomic-embed-text found"
else
    echo "  Pulling nomic-embed-text..."
    ollama pull nomic-embed-text
fi
if ollama list 2>/dev/null | grep -q "qwen3:8b"; then
    echo "  [OK] qwen3:8b found"
else
    echo "  Pulling qwen3:8b..."
    ollama pull qwen3:8b
fi

# Step 2: Start the Docker stack (Qdrant + Mem0 API + UI)
echo "[2/3] Starting Qdrant, Mem0 API, and UI..."
docker compose up -d
echo "Waiting for services to stabilize..."
sleep 10

# Step 3: Verify
echo "[3/3] Verifying services..."
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "  [OK] $name is running"
    else
        echo "  [!!] $name may not be ready yet — check 'docker compose logs'"
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
echo "  Ollama:    http://localhost:11434 (host, not Docker)"
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

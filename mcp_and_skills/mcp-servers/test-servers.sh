#!/bin/bash
# Test MCP servers

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              MCP Server Test Suite                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

SERVERS=(
    "code-intelligence"
    "execution-engine"
    "version-control"
    "quality-assurance"
    "knowledge-integration"
)

FAILED=0

for server in "${SERVERS[@]}"; do
    echo -n "Testing $server... "
    
    RESULT=$(echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | timeout 3 python3 "$server/src/server.py" 2>/dev/null | tail -1)
    
    if echo "$RESULT" | grep -q '"tools"'; then
        TOOL_COUNT=$(echo "$RESULT" | grep -o '"name"' | wc -l)
        echo "✓ ($TOOL_COUNT tools)"
    else
        echo "✗ (failed)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ All servers working correctly!"
else
    echo "⚠ $FAILED server(s) failed"
    exit 1
fi

#!/bin/bash
# 启动脚本 - 同时启动sidecar和示例server

echo "🚀 Starting MCP Feedback Loop Demo"
echo ""

# 检查依赖
echo "📦 Checking dependencies..."
pip install -q fastapi uvicorn httpx mcp

# 启动sidecar（后台）
echo "🔧 Starting feedback sidecar on port 8099..."
cd feedback_sidecar
python server.py &
SIDECAR_PID=$!
cd ..

sleep 2

# 启动示例server
echo "🎯 Starting example MCP server..."
cd example_server
python simple_server.py

# 清理
echo ""
echo "🛑 Shutting down..."
kill $SIDECAR_PID 2>/dev/null

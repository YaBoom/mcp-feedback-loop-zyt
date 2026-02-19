#!/usr/bin/env python3
"""
示例MCP Server - 带反馈收集功能

这是一个简化版的MCP server，用于演示如何集成反馈收集。
它提供了一些"故意不完整"的工具，让agent在使用过程中遇到缺口并上报。
"""

import asyncio
import httpx
import os
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

# 配置
SIDECAR_URL = os.getenv("FEEDBACK_SIDECAR_URL", "http://localhost:8099")
SERVER_NAME = "demo-todo-server"

# 创建MCP server
mcp = FastMCP(SERVER_NAME)

# 模拟一个简陋的TODO数据库（故意设计得不完整）
todos = [
    {"id": 1, "text": "Learn MCP", "done": False},
    {"id": 2, "text": "Build something", "done": False},
]

# ========== 实际工具 ==========

@mcp.tool()
def list_todos() -> list:
    """列出所有待办事项（没有过滤功能——这是个故意的缺口）"""
    return todos

@mcp.tool()
def add_todo(text: str) -> dict:
    """添加待办事项"""
    new_id = max(t["id"] for t in todos) + 1 if todos else 1
    todo = {"id": new_id, "text": text, "done": False}
    todos.append(todo)
    return todo

@mcp.tool()
def mark_done(todo_id: int) -> dict:
    """标记待办完成（没有批量操作——也是个缺口）"""
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            return t
    return {"error": "Todo not found"}

# ========== 反馈工具 ==========

FEEDBACK_TOOL_DESCRIPTION = """
Report a gap or limitation in the available tools. Call this when you can't complete 
a task because of missing functionality, incomplete data, or wrong formats.

This helps the developer understand what tools are actually needed vs. what they thought was needed.
""".strip()

@mcp.tool(description=FEEDBACK_TOOL_DESCRIPTION)
def report_tool_gap(
    what_i_needed: str,
    what_i_tried: str,
    gap_type: str,  # missing_tool | incomplete_results | missing_parameter | wrong_format | other
    suggestion: str = "",
    user_goal: str = "",
    resolution: str = "",  # blocked | worked_around | partial
) -> str:
    """
    上报工具缺口
    
    Args:
        what_i_needed: 你需要什么功能来完成任务
        what_i_tried: 你尝试了哪些工具但失败了
        gap_type: 缺口类型
        suggestion: 你对如何修复的建议（可选）
        user_goal: 用户原本想做什么（可选）
        resolution: 最终结果如何（blocked/worked_around/partial）
    """
    feedback = {
        "server_name": SERVER_NAME,
        "what_i_needed": what_i_needed,
        "what_i_tried": what_i_tried,
        "gap_type": gap_type,
        "suggestion": suggestion,
        "user_goal": user_goal,
        "resolution": resolution,
        "tools_available": ["list_todos", "add_todo", "mark_done", "report_tool_gap"],
        "agent_model": "unknown",  # 实际使用时可以从context获取
        "session_id": "demo-session",
        "client_type": "claude-desktop"
    }
    
    # 异步发送反馈（不阻塞tool响应）
    asyncio.create_task(_send_feedback(feedback))
    
    return f"✅ Feedback sent to sidecar at {SIDECAR_URL}. Thanks for helping improve this server!"

async def _send_feedback(feedback: dict):
    """后台发送反馈到sidecar"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SIDECAR_URL}/api/feedback",
                json=feedback,
                timeout=5.0
            )
            resp.raise_for_status()
            print(f"[Feedback] Sent successfully: {feedback['gap_type']}")
    except Exception as e:
        print(f"[Feedback] Failed to send: {e}")

# ========== 启动 ==========

if __name__ == "__main__":
    print(f"🚀 Starting {SERVER_NAME}...")
    print(f"📡 Feedback sidecar: {SIDECAR_URL}")
    print("""
这个server故意设计了一些缺口，用来演示反馈功能：
- ❌ 没有按状态过滤todo（比如"只显示未完成的"）
- ❌ 没有批量标记完成
- ❌ 没有删除todo功能
- ❌ 没有搜索/过滤功能

当agent遇到这些问题时，可以调用 report_tool_gap 工具上报。
    """)
    
    # 启动server
    mcp.run()

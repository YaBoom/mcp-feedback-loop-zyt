#!/usr/bin/env python3
"""
MCP Feedback Sidecar - 简化版实验实现

功能：
1. 接收来自MCP server的agent反馈
2. 存储到SQLite
3. 提供Dashboard查看反馈
"""

import sqlite3
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="MCP Feedback Sidecar")

# 数据模型
class FeedbackItem(BaseModel):
    server_name: str
    what_i_needed: str
    what_i_tried: str
    gap_type: str  # missing_tool, incomplete_results, missing_parameter, wrong_format, other
    suggestion: Optional[str] = None
    user_goal: Optional[str] = None
    resolution: Optional[str] = None  # blocked, worked_around, partial
    tools_available: Optional[List[str]] = None
    agent_model: Optional[str] = None
    session_id: Optional[str] = None
    client_type: Optional[str] = None

# 初始化数据库
def init_db():
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT NOT NULL,
            what_i_needed TEXT NOT NULL,
            what_i_tried TEXT NOT NULL,
            gap_type TEXT NOT NULL,
            suggestion TEXT,
            user_goal TEXT,
            resolution TEXT,
            tools_available TEXT,
            agent_model TEXT,
            session_id TEXT,
            client_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed BOOLEAN DEFAULT 0,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Dashboard HTML - 极其简陋但能用
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Feedback Dashboard</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0d1117; color: #c9d1d9; }
        h1 { color: #58a6ff; }
        .feedback-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin: 12px 0; }
        .gap-type { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .missing_tool { background: #da3633; color: white; }
        .incomplete_results { background: #d29922; color: black; }
        .missing_parameter { background: #1f6feb; color: white; }
        .wrong_format { background: #8957e5; color: white; }
        .other { background: #6e7681; color: white; }
        .field { margin: 8px 0; }
        .field-label { font-weight: bold; color: #8b949e; font-size: 12px; text-transform: uppercase; }
        .server-name { color: #3fb950; font-family: monospace; }
        .timestamp { color: #6e7681; font-size: 12px; }
        .empty { text-align: center; padding: 60px; color: #6e7681; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-box { background: #161b22; padding: 16px 24px; border-radius: 8px; }
        .stat-number { font-size: 32px; font-weight: bold; color: #58a6ff; }
        .stat-label { color: #8b949e; font-size: 14px; }
    </style>
</head>
<body>
    <h1>🧩 MCP Feedback Dashboard</h1>
    <p style="color: #8b949e;">Agent reported gaps in your MCP servers</p>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number" id="total-count">0</div>
            <div class="stat-label">Total Feedback</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" id="missing-tool-count">0</div>
            <div class="stat-label">Missing Tools</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" id="blocked-count">0</div>
            <div class="stat-label">Blocked Sessions</div>
        </div>
    </div>
    
    <div id="feedback-list"></div>
    
    <script>
        async function loadFeedback() {
            const res = await fetch('/api/feedback');
            const data = await res.json();
            
            document.getElementById('total-count').textContent = data.length;
            document.getElementById('missing-tool-count').textContent = 
                data.filter(f => f.gap_type === 'missing_tool').length;
            document.getElementById('blocked-count').textContent = 
                data.filter(f => f.resolution === 'blocked').length;
            
            const container = document.getElementById('feedback-list');
            if (data.length === 0) {
                container.innerHTML = '<div class="empty">No feedback yet. Agents will report here when they hit walls.</div>';
                return;
            }
            
            container.innerHTML = data.map(f => `
                <div class="feedback-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <span class="server-name">${f.server_name}</span>
                            <span class="gap-type ${f.gap_type}">${f.gap_type.replace('_', ' ')}</span>
                        </div>
                        <span class="timestamp">${new Date(f.created_at).toLocaleString()}</span>
                    </div>
                    
                    <div class="field">
                        <div class="field-label">What Agent Needed</div>
                        <div>${f.what_i_needed}</div>
                    </div>
                    
                    <div class="field">
                        <div class="field-label">What Agent Tried</div>
                        <div>${f.what_i_tried}</div>
                    </div>
                    
                    ${f.suggestion ? `
                    <div class="field">
                        <div class="field-label">Agent's Suggestion</div>
                        <div style="background: #0d1117; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 14px;">${f.suggestion}</div>
                    </div>
                    ` : ''}
                    
                    ${f.user_goal ? `
                    <div class="field">
                        <div class="field-label">User Goal</div>
                        <div>${f.user_goal}</div>
                    </div>
                    ` : ''}
                    
                    ${f.tools_available ? `
                    <div class="field">
                        <div class="field-label">Available Tools</div>
                        <div style="font-family: monospace; font-size: 12px;">${JSON.parse(f.tools_available || '[]').join(', ')}</div>
                    </div>
                    ` : ''}
                    
                    <div style="display: flex; gap: 16px; margin-top: 12px; font-size: 12px; color: #6e7681;">
                        ${f.agent_model ? `<span>Model: ${f.agent_model}</span>` : ''}
                        ${f.client_type ? `<span>Client: ${f.client_type}</span>` : ''}
                        ${f.resolution ? `<span>Resolution: ${f.resolution}</span>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        loadFeedback();
        setInterval(loadFeedback, 5000); // 每5秒刷新
    </script>
</body>
</html>
"""

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML

@app.post("/api/feedback")
async def submit_feedback(item: FeedbackItem):
    """接收agent反馈"""
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO feedback 
        (server_name, what_i_needed, what_i_tried, gap_type, suggestion, 
         user_goal, resolution, tools_available, agent_model, session_id, client_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        item.server_name, item.what_i_needed, item.what_i_tried, item.gap_type,
        item.suggestion, item.user_goal, item.resolution,
        json.dumps(item.tools_available) if item.tools_available else None,
        item.agent_model, item.session_id, item.client_type
    ))
    conn.commit()
    conn.close()
    return {"status": "ok", "id": c.lastrowid}

@app.get("/api/feedback")
async def list_feedback():
    """列出所有反馈"""
    conn = sqlite3.connect("feedback.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM feedback ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/stats")
async def get_stats():
    """统计数据"""
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute('SELECT gap_type, COUNT(*) FROM feedback GROUP BY gap_type')
    by_type = dict(c.fetchall())
    c.execute('SELECT COUNT(*) FROM feedback')
    total = c.fetchone()[0]
    conn.close()
    return {"total": total, "by_type": by_type}

if __name__ == "__main__":
    init_db()
    print("🚀 Starting MCP Feedback Sidecar on http://localhost:8099")
    print("📊 Dashboard: http://localhost:8099")
    print("📡 API: http://localhost:8099/api/feedback")
    uvicorn.run(app, host="0.0.0.0", port=8099)

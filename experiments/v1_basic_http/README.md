# v1 Basic HTTP - 试错记录

## 尝试目标
用最简单的HTTP POST把agent反馈发送到sidecar。

## 代码实现
```python
# 最初的思路：同步HTTP POST
import requests

def report_gap(what_needed, what_tried):
    requests.post("http://localhost:8099/feedback", json={
        "needed": what_needed,
        "tried": what_tried
    })
    return "Feedback sent"
```

## 遇到的问题

### 问题1：阻塞问题
同步requests会阻塞MCP server的响应。当sidecar没启动时，会卡很久。

**解决**：改为async + asyncio.create_task()

### 问题2：Tool返回值会显示给用户
Agent调用report_gap后，返回值会出现在对话中。简单的"Feedback sent"会干扰用户体验。

**解决**：设计更好的返回消息，让它看起来自然：
```python
return "I've noted this limitation. The developer will be notified."
```

### 问题3：反馈格式不统一
每个agent上报的格式都不一样，有的只写一句话，有的写一大段。

**解决**：设计结构化schema，强制要求字段：
- what_i_needed (必须)
- what_i_tried (必须)
- gap_type (必须)
- suggestion (可选)

## 经验教训
- 工具描述要写得足够清晰，agent才知道什么时候该调用
- 异步发送很重要，不能阻塞主流程
- 结构化数据比自由文本更好处理

## 被放弃的原因
这个版本太简单了，缺乏实际价值。进入v2设计更完整的schema。

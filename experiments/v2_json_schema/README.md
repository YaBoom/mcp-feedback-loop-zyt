# v2 JSON Schema - 试错记录

## 尝试目标
设计结构化的反馈schema，让agent提供更有用的信息。

## 学习PatchworkMCP的设计
看了原版项目的schema设计：
```
what_i_needed: 需要的能力
what_i_tried: 尝试过的工具
gap_type: missing_tool | incomplete_results | missing_parameter | wrong_format | other
suggestion: 建议的修复方式
user_goal: 用户原本想做什么
resolution: blocked | worked_around | partial
tools_available: 当时能看到哪些工具
agent_model: 模型版本
session_id: 会话ID
client_type: 客户端类型
```

## 我的简化版本
保留了核心字段：
- what_i_needed (必须)
- what_i_tried (必须)
- gap_type (必须)
- suggestion (可选但很有价值)

去掉了（暂时）：
- tools_available（可以从list_tools推断）
- agent_model（实现复杂）
- session_id（需要状态管理）

## 遇到的坑

### 坑1：Pydantic模型和MCP tool参数
FastMCP的tool装饰器会自动生成schema，但如果直接用Pydantic BaseModel作为参数类型，MCP client可能无法正确渲染。

**解决**：直接用Python type hints，让FastMCP自动生成schema。

### 坑2：agent不会主动调用反馈工具
除非明确告诉它"遇到问题就上报"，否则agent会自己想办法绕过或报错。

**解决**：在tool description中明确说明使用场景：
```python
"""Report a gap or limitation in the available tools. 
Call this when you can't complete a task because of missing functionality..."""
```

### 坑3：Dashboard设计纠结
一开始想做一个复杂的React前端，但意识到这违背了"快速验证"的原则。

**解决**：用纯HTML+JS内嵌在Python里，虽然丑但能跑。

## 最终取舍
- ✅ 保持简单，先验证核心流程
- ✅ 暗色主题（程序员友好）
- ❌ 不做实时更新（实际做了5秒轮询）
- ❌ 不做PR生成（原版的核心功能，但实现复杂）

## 这个版本留下的问题
1. 缺乏反馈聚类（相同问题被多次报告）
2. 没有和GitHub集成
3. 只支持Python

这些都是可以后续改进的点。

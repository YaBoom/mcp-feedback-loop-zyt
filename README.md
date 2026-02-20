# MCP Feedback Loop - 实验项目

> ⚠️ **这只是实验代码** —— 用于探索MCP server开发中的反馈循环问题

## 项目灵感

看了Hacker News上PatchworkMCP的项目后，我被这个思路打动了：我们在开发MCP server时，怎么知道AI agent到底需要什么工具？通常是猜的。但agent自己知道——当它遇到墙的时候。

这个项目是一个**简化版的实验实现**，用于验证这个思路的可行性。

## 核心问题

MCP生态有个"builder多于user"的问题：
- 开发者发布了server，但不知道agent实际需要什么
- agent遇到缺失的工具时，只能报错或放弃
- 没有结构化的反馈渠道

## 实验目标

验证：能否让agent在遇到问题时，自动上报需要什么工具，并给出建议实现？

## 项目结构

```
mcp-feedback-loop-zyt/
├── feedback_sidecar/      # 反馈收集服务（FastAPI + SQLite）
│   ├── server.py
│   └── dashboard.html
├── example_server/        # 示例MCP server（带反馈功能）
│   └── simple_server.py
├── experiments/           # 试错版本记录
│   ├── v1_basic_http/     # 第一版：简单HTTP上报
│   └── v2_json_schema/    # 第二版：结构化反馈
└── README.md
```

## 快速开始

```bash
# 1. 启动反馈收集sidecar

# 创建新的虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装项目依赖
pip install -r requirements.txt
python server.py

# 2. 启动示例MCP server
cd example_server
python simple_server.py

# 3. 打开dashboard查看反馈
open http://localhost:8099
```

## 实验记录

### v1 试错：直接HTTP上报
**问题**：最初想用简单的HTTP POST，但发现agent调用tool时返回的内容会被用户看到，体验不好。
**解决**：改为async后台上报，不影响用户体验。

### v2 试错：反馈schema设计
**问题**：一开始只收集"缺少什么工具"，但agent的报告太笼统。
**解决**：增加`what_i_tried`、`gap_type`、`suggestion`字段，结构化收集。

## 已知问题

- [ ] Dashboard非常简陋，只是功能验证
- [ ] 没有实现自动PR生成功能（原PatchworkMCP的功能）
- [ ] 缺乏反馈去重和聚类
- [ ] 只实现了Python版本

## TODO

- [ ] 增加反馈聚类（相似反馈合并）
- [ ] 增加LLM自动生成工具代码
- [ ] 支持TypeScript/Go/Rust版本的drop-in
- [ ] 增加GitHub API集成，自动创建PR

## 相关项目

- [PatchworkMCP](https://github.com/keyton-weissinger/patchworkmcp) - 完整实现， inspiration来源
- [MCP官方文档](https://modelcontextprotocol.io/)

## License

MIT - 实验项目，随意使用

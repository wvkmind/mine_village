# Legacy Worldline CLI — 文件说明与复用指南

本文档说明 `../world/` 目录下的旧项目。该项目是一个 CLI 验证框架，用于验证 AI 驱动世界模拟的核心技术可行性。**不是最终产品**，但其中多个模式已验证可用，应在 mine_village 中复用。

## 项目定位

Worldline CLI 是一个面向开发者的观察工具，模拟 3 座城市、3 条路线、3 个 NPC 的宏观世界演化。通过 Poe API 接入 AI 做世界分析和 NPC 决策。验证了以下核心假设：

1. **世界状态可以用 Python dataclass 管理并 JSON 序列化**
2. **Poe API (fastapi_poe) 可以稳定调用，支持重试和降级**
3. **AI 决策可以被约束在结构化输出中（JSON schema）**
4. **规则引擎 + AI 混合驱动是可行的**（AI 不可用时自动回退规则）
5. **4 层模型路由（cheap/normal/deep/judge）能有效控制成本**

## 文件清单

### 入口与配置

| 文件 | 用途 | 复用价值 |
|------|------|----------|
| `main.py` | CLI 入口，argparse 命令路由 | 不复用（新项目用 FastAPI WebSocket） |
| `.env` / `.env.example` | Poe API Key 和模型配置 | **复用格式**，新项目同样用 .env |
| `README.md` | CLI 使用说明 | 不复用 |
| `prd.md` | 产品需求文档（CLI 验证版） | 参考用，新项目需求见 desc.md |
| `desc.md` | **完整产品需求**（地下小镇） | **核心需求文档**，mine_village 的设计依据 |
| `map.jsx` | React SVG 地图示意图 | **参考布局**，实际用 2D 网格实现 |
| `ai.md` | AI 集成笔记 | 参考用 |
| `dashboard.py` | 实验性仪表盘 | 不复用 |

### core/ — 数据模型与引擎

| 文件 | 用途 | 验证了什么 | 复用建议 |
|------|------|-----------|----------|
| `core/models.py` | dataclass 定义：World, City, Route, NPC, Event, DawnDuskLine, GlobalEnvironment | dataclass + field(default_factory) 模式可靠；`add_event()` 和 `log()` 方法挂在 World 上很方便 | **复用模式**：dataclass 定义 + 聚合根上挂便捷方法。但字段完全不同（新项目是 Tile/Room/Character 粒度） |
| `core/engine.py` | Tick 引擎，每 tick 更新环境→路线→城市→NPC | 验证了单函数 `_tick()` 按固定顺序更新所有子系统的模式；AI 决策间隔（每 N tick 调一次）有效减少 API 调用 | **复用模式**：tick 主循环的分步结构。新项目更复杂（10 步），但骨架相同 |

### services/ — AI 服务层

| 文件 | 用途 | 验证了什么 | 复用建议 |
|------|------|-----------|----------|
| `services/poe_client.py` | Poe API 封装：重试、降级、日志、JSON 解析 | fastapi_poe 的 `get_bot_response_sync` 可用；重试 + 回退模型策略有效；JSON 从 markdown code block 中提取可靠；文件日志（ai_calls.log）对调试极有价值 | **直接复用**，几乎不需要改。核心函数：`query()` 和 `query_json()` |
| `services/model_resolver.py` | 4 层模型路由：task_category → tier → model | 验证了按任务类型自动选模型的机制；环境变量覆盖默认模型可行 | **直接复用**，新增 task_category（如 npc_dialogue, memory_compress） |
| `services/ai_npc.py` | NPC AI 决策：构建上下文 → 调 AI → 解析 JSON 输出 | 验证了结构化 prompt + JSON schema 约束 AI 输出的模式；规则回退（`get_rule_fallback`）保证系统不阻塞 | **复用模式**：prompt 构建 + JSON 输出 + 规则回退。但 prompt 内容完全不同（新项目有个性 8 轴、记忆、合法行动列表） |
| `services/ai_observer.py` | AI 观察分析：世界摘要、城市分析、NPC 视角、历史对比 | 验证了上下文裁剪（只发相关信息给 AI）的重要性 | 不直接复用（新项目无观察者模式），但上下文裁剪思路可参考 |

### storage/ — 存档

| 文件 | 用途 | 验证了什么 | 复用建议 |
|------|------|-----------|----------|
| `storage/save_manager.py` | JSON 存档/读档，`dataclasses.asdict()` 序列化 | `_to_dict()` 递归序列化可靠；自动存档 + 时间戳存档双写模式好用 | **复用模式**：`_to_dict()` + 双写。新项目数据结构不同但序列化方式相同 |

### data/ — 种子数据

| 文件 | 用途 | 复用建议 |
|------|------|----------|
| `data/seed_world.yaml` | 初始世界配置（3 城市、3 路线、3 NPC） | 不复用内容。新项目用 JSON 格式（init_map.json, init_npcs.json, init_items.json） |

### 其他目录

| 目录 | 内容 |
|------|------|
| `saves/` | 大量 JSON 存档文件（验证期间产生） |
| `logs/` | `ai_calls.log`，记录所有 AI 调用的详细日志 |
| `cli/` | 空目录（未使用） |

## 关键复用总结

**直接复用（改最少）：**
- `poe_client.py` 的 query/query_json 函数、重试逻辑、日志机制
- `model_resolver.py` 的分层路由架构
- `.env` 配置格式

**复用模式（重写实现）：**
- dataclass 数据模型 + JSON 序列化
- tick 主循环的分步更新结构
- AI 决策：结构化 prompt → JSON 输出 → 规则回退
- 存档：递归 `_to_dict()` + 自动存档

**不复用：**
- CLI 命令系统（新项目用 WebSocket API）
- 宏观世界模型（City/Route 粒度 → 新项目是 Tile/Room/Character 粒度）
- 观察者 AI（新项目无此功能）

# mine_village

潮汐锁定星球暗面的地下采矿村生存模拟。150人NPC由AI自主决策，玩家作为陌生人跟车队到达。

## 启动

### 后端

```bash
cd server
pip install -r requirements.txt
python main.py
```

服务启动在 `http://localhost:8000`，WebSocket 端点 `ws://localhost:8000/ws`。

首次启动自动初始化世界（加载地图、NPC、物品）。也可手动重置：`GET /api/init`。

### 前端

```bash
cd client
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`。

### AI（可选）

在 `server/.env` 中填入 Poe API Key：

```
POE_API_KEY=your_key_here
```

不填则 NPC 使用规则引擎决策，不影响游戏运行。

## 操作

- 方向键 / WASD 移动
- 点击右侧 NPC 名字选择对话目标，输入框发送
- 每次操作推进一个 tick（游戏内 10 分钟）

## 项目结构

```
server/
  main.py              # 入口
  state.py             # 存档/读档
  models/              # 数据模型（Tile, Character, Item, Memory...）
  engine/              # 游戏引擎（tick循环, 行动, 需求, 战斗, 技能, 经济, 记忆, 事件, 车队）
  ai/                  # AI决策（Poe API, prompt构建, 对话生成）
  api/                 # FastAPI + WebSocket
  data/                # 初始数据（地图, NPC, 物品）
client/
  src/App.jsx          # 主界面
  src/canvas/          # Canvas地图渲染
  src/hooks/           # WebSocket hook
docs/
  design.md            # 核心设计文档
  legacy_worldline.md  # 旧验证项目说明
```

## 设计文档

详见 `docs/design.md`。

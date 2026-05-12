# 智能旅行助手

基于 DeepSeek LLM、高德地图 Web 服务 API 和 Unsplash 图片服务的智能旅行规划项目。

## 项目结构

```
helloagents-trip-planner/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/schemas.py
│   │   ├── agents/trip_planner.py
│   │   ├── services/unsplash.py
│   │   └── api/routes.py
│   ├── requirements.txt
│   └── .env
├── frontend/         # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── views/Home.vue
│   │   ├── views/Result.vue
│   │   └── services/api.js
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 环境准备

1. **Node.js**（用于运行 MCP 工具和前端的 `npx` 命令）
2. **Python 3.10+**
3. **npm**

## 配置说明

### 后端配置

编辑 `backend/.env`：

- `LLM_API_KEY`：填入你的 DeepSeek API Key
- `AMAP_API_KEY`：高德地图 Web 服务 Key（已预填）
- `MCP_12306_URL`：12306 MCP 服务的 MCP HTTP 传输地址，例如 `http://localhost:3000/mcp`
- `MCP_12306_API_KEY`：如果 MCP 服务需要授权，可填写对应的 Bearer Key
- `UNSPLASH_ACCESS_KEY`：Unsplash Access Key（已预填）

### 前端配置

如需在前端展示高德地图，需另外申请「Web端(JS API)」Key，并在代码中配置。

## 运行步骤

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

后端服务将运行在 `http://localhost:8000`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端服务将运行在 `http://localhost:5173`

### 3. 访问应用

打开浏览器访问 `http://localhost:5173`

## 注意事项

1. **高德地图 JS API Key**：前端未集成地图展示，如需地图组件请自行申请并集成。
2. **Unsplash 网络问题**：Unsplash API 在国内访问可能不稳定，如遇超时请重试或更换图片服务。
3. **MCP 工具依赖 Node.js**：请确保系统已安装 Node.js，否则 `npx` 命令无法运行。
4. **hello-agents 包**：请确保该包已正确安装或替换为等效实现。

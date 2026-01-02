# 快速开始指南

本指南将帮助您快速运行 BullBear Dashboard 的前后端系统。

## 前置要求

- Python 3.10 或更高版本
- pip 包管理器

## 步骤 1: 配置后端

### 1.1 进入后端目录

```bash
cd backend
```

### 1.2 创建环境配置文件

```bash
cp env.example .env
```

### 1.3 编辑 `.env` 文件

使用文本编辑器打开 `.env` 文件，添加API密钥：

```
CMC_API_KEY=your_coinmarketcap_api_key
TAAPI_SECRET=your_taapi_secret
```

**注意**：Binance API是免费的，无需API密钥。如果使用Binance作为数据源，只需要配置CoinMarketCap API密钥即可。

### 1.4 安装后端依赖

```bash
pip install fastapi uvicorn requests python-dotenv
```

或者使用 poetry（如果已安装）：

```bash
poetry install
```

## 步骤 2: 启动后端服务

```bash
python -m uvicorn bullbear_backend.main:app --reload --host 0.0.0.0 --port 8000
```

您应该看到类似以下的输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

后端服务现在运行在 **http://localhost:8000**

## 步骤 3: 测试后端API

打开新的终端窗口，测试API：

```bash
# 健康检查
curl http://localhost:8000/api/health

# 获取市场状态
curl http://localhost:8000/api/state

# 获取所有数据
curl http://localhost:8000/api/data
```

或者直接在浏览器中访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

## 步骤 4: 配置前端

### 4.1 进入前端目录

```bash
cd frontend
```

### 4.2 安装前端依赖

```bash
pnpm install
```

如果没有安装 pnpm，可以使用 npm 安装：
```bash
npm install -g pnpm
```

## 步骤 5: 启动前端应用

```bash
pnpm dev
```

您应该看到类似以下的输出：

```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

浏览器会自动打开前端应用，如果没有，请手动访问 **http://localhost:5173**

## 步骤 6: 使用前端应用

1. **查看当前市场状态**: 页面顶部会显示当前的四象限状态
2. **查看四象限图**: 可视化显示当前状态在四象限中的位置
3. **查看详细数据**: 显示BTC价格、MA50/MA200、稳定币占比等关键指标
4. **查看校验层**: 显示风险温度计和ETF加速器状态
5. **自动刷新**: 数据会自动定期刷新

## 故障排除

### 后端无法启动

- 检查端口 8000 是否被占用
- 确认 `.env` 文件存在且已配置API密钥
- 检查 Python 版本是否为 3.10+

### 前端无法连接后端

- 确认后端服务正在运行
- 检查前端配置中的后端API地址是否正确（默认: http://localhost:8000）
- 查看浏览器控制台是否有错误信息
- 确认后端CORS配置允许前端域名访问

### 数据获取失败

- 确认API密钥已正确配置在 `.env` 文件中
- 检查网络连接是否正常
- 确认API密钥是否有效

## 下一步

- 查看 [状态模型设计](STATE_MODEL.md) 了解状态机逻辑
- 查看 [数据来源说明](DATA_SOURCES.md) 了解数据获取方式
- 查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目

## 配置API密钥

1. 获取API密钥：
   - [CoinMarketCap API](https://coinmarketcap.com/api/) - 用于获取BTC价格和市场数据
   - [TAAPI.io](https://taapi.io/) - 用于获取技术指标（可选，如果使用Binance则不需要）

2. 编辑 `backend/.env`:
```
CMC_API_KEY=your_coinmarketcap_api_key
TAAPI_SECRET=your_taapi_secret
```

3. 重启后端服务

**注意**：Binance API是免费的，无需API密钥。如果使用Binance作为数据源，只需要配置CoinMarketCap API密钥即可。


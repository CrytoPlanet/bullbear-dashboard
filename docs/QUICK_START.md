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

使用文本编辑器打开 `.env` 文件，设置：

```
USE_MOCK_DATA=true
```

这将使用模拟数据，无需API密钥即可运行。

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
cd dashboard
```

### 4.2 安装前端依赖

```bash
pip install -r requirements.txt
```

## 步骤 5: 启动前端Dashboard

```bash
streamlit run app.py
```

您应该看到类似以下的输出：

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

浏览器会自动打开 Dashboard，如果没有，请手动访问 **http://localhost:8501**

## 步骤 6: 使用Dashboard

1. **查看当前市场状态**: Dashboard 顶部会显示当前的四象限状态
2. **查看四象限图**: 可视化显示当前状态在四象限中的位置
3. **查看详细数据**: 显示BTC价格、MA50/MA200、稳定币占比等关键指标
4. **刷新数据**: 点击"刷新数据"按钮获取最新状态

## 故障排除

### 后端无法启动

- 检查端口 8000 是否被占用
- 确认 `.env` 文件存在且 `USE_MOCK_DATA=true`
- 检查 Python 版本是否为 3.10+

### 前端无法连接后端

- 确认后端服务正在运行
- 检查侧边栏中的后端API地址是否正确（默认: http://localhost:8000）
- 查看浏览器控制台是否有错误信息

### 数据获取失败

- 如果使用模拟数据，确认 `USE_MOCK_DATA=true` 在 `.env` 文件中
- 如果使用真实API，确认API密钥已正确配置

## 下一步

- 查看 [状态模型设计](STATE_MODEL.md) 了解状态机逻辑
- 查看 [数据来源说明](DATA_SOURCES.md) 了解数据获取方式
- 查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目

## 使用真实API数据

如果您想使用真实的API数据而不是模拟数据：

1. 获取API密钥：
   - [CoinMarketCap API](https://coinmarketcap.com/api/)
   - [TAAPI.io](https://taapi.io/)

2. 编辑 `backend/.env`:
```
USE_MOCK_DATA=false
CMC_API_KEY=your_coinmarketcap_api_key
TAAPI_SECRET=your_taapi_secret
```

3. 重启后端服务


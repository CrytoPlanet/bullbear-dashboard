# 快速启动指南

## Windows 一键启动

### 方法1：使用批处理文件（推荐）

1. **启动服务**
   ```bash
   # 双击运行或在命令行执行
   start.bat
   ```

2. **停止服务**
   ```bash
   # 双击运行或在命令行执行
   stop.bat
   ```

   或者直接关闭打开的服务窗口。

### 方法2：手动启动

#### 启动后端
```bash
cd backend
python -m uvicorn bullbear_backend.main:app --reload --port 8000
```

#### 启动前端（新开一个终端）
```bash
cd frontend
pnpm dev
```

## 访问地址

- **前端应用**: http://localhost:5173 (Vite默认端口)
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 前置要求

- **Python 3.10+**: 用于后端服务
- **Node.js 20.19.0+ 或 22.12.0+**: 用于前端开发
- **pnpm**: 前端包管理器（脚本会自动安装）

## 注意事项

1. **首次运行**：脚本会自动检查并安装必要的依赖
2. **环境配置**：确保 `backend/.env` 中配置了必要的API密钥
3. **端口占用**：
   - 后端使用 8000 端口
   - 前端使用 5173 端口（Vite默认）
   - 如果端口被占用，需要先停止占用该端口的程序

## 故障排除

### 端口被占用
```bash
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# 停止占用端口的进程（替换PID为实际进程ID）
taskkill /PID <PID> /F
```

### Python未找到
确保Python已安装并添加到PATH环境变量中。

### Node.js未找到
确保Node.js已安装并添加到PATH环境变量中。

### pnpm未安装
脚本会自动安装pnpm，如果失败可以手动安装：
```bash
npm install -g pnpm
```

### 依赖安装失败
手动安装依赖：

**后端依赖：**
```bash
cd backend
pip install fastapi uvicorn requests python-dotenv
```

**前端依赖：**
```bash
cd frontend
pnpm install
```

## 开发说明

- **后端热重载**：修改后端代码会自动重启服务
- **前端热重载**：修改前端代码会自动刷新浏览器
- **API变更**：修改后端API后，前端需要刷新页面获取最新接口


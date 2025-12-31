# BullBear Dashboard

加密市场状态机的可视化前端界面。

## 快速开始

### 1. 安装依赖

```bash
cd dashboard
pip install -r requirements.txt
```

### 2. 启动后端服务

确保后端服务正在运行（默认端口 8000）：

```bash
cd ../backend
python -m uvicorn bullbear_backend.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd dashboard
streamlit run app.py
```

Dashboard 将在浏览器中打开，默认地址：**http://localhost:8501**

## 功能特性

- 📊 **四象限状态可视化**: 直观显示当前市场状态
- 📈 **实时数据展示**: 显示BTC价格、MA50/MA200、稳定币占比等关键指标
- 🔄 **自动刷新**: 支持手动刷新数据
- 📱 **响应式设计**: 适配不同屏幕尺寸

## 配置

在侧边栏可以配置后端API地址，默认为 `http://localhost:8000`。

## 状态说明

**四象限状态:**

- 🔥 **牛市进攻** (HIGH RISK): 趋势多 + 资金进攻
- 📈 **牛市修复** (MEDIUM RISK): 趋势多 + 资金防守  
- ⚡ **熊市反弹** (MEDIUM RISK): 趋势空 + 资金进攻
- 🩸 **熊市消化** (LOW RISK): 趋势空 + 资金防守

## 技术栈

- **Streamlit**: Web应用框架
- **Plotly**: 交互式图表
- **Requests**: HTTP客户端


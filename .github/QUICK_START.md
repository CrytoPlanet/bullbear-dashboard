# 快速开始 - GitHub Actions 和 Pages 部署

## ✅ 已完成的配置

以下文件已创建并配置完成：

### 1. GitHub Actions 工作流

- **`.github/workflows/fetch-data.yml`**: 每6小时自动获取市场数据
- **`.github/workflows/deploy-pages.yml`**: 自动构建并部署前端到 GitHub Pages

### 2. 数据获取脚本

- **`backend/scripts/fetch_and_save_data.py`**: 获取市场数据并保存为 JSON 文件

### 3. 前端配置

- **`frontend/vite.config.ts`**: 已配置支持 GitHub Pages 部署
- **`frontend/src/App.vue`**: 已更新支持从静态文件读取数据

## 🚀 立即开始

### 步骤 1: 启用 GitHub Pages

1. 进入你的 GitHub 仓库
2. 点击 **Settings** > **Pages**
3. 在 **Source** 部分，选择 **GitHub Actions**
4. 点击 **Save**

### 步骤 2: 推送代码

```bash
git add .
git commit -m "配置 GitHub Actions 和 Pages 部署"
git push origin main
```

### 步骤 3: 查看部署

1. 推送后，GitHub Actions 会自动开始构建和部署
2. 在仓库的 **Actions** 标签页查看进度
3. 部署完成后，访问 `https://你的用户名.github.io/bullbear-dashboard/`

### 步骤 4: 手动触发数据获取（可选）

1. 进入 **Actions** 标签页
2. 选择 **获取市场数据** 工作流
3. 点击 **Run workflow** 手动触发

## 📝 注意事项

1. **仓库名称**：如果你的仓库名称不是 `bullbear-dashboard`，需要修改 `frontend/vite.config.ts` 中的 `repoName` 变量

2. **API 密钥**（可选）：
   - 默认使用免费的 Binance 和 CoinGecko API
   - 如果需要使用其他数据源，在仓库 Settings > Secrets 中添加：
     - `CMC_API_KEY`
     - `TAAPI_SECRET`

3. **数据更新**：
   - 数据每6小时自动更新一次
   - 数据文件保存在 `frontend/public/data/` 目录
   - 前端会自动使用最新的数据文件

## 🔍 验证部署

部署成功后，你应该能够：

1. 访问 GitHub Pages 网站
2. 看到市场数据（从静态文件加载）
3. 在 Actions 页面看到工作流运行记录

## 📚 更多信息

查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 获取详细的配置说明和故障排除指南。


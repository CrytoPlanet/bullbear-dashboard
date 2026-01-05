# GitHub Actions 和 GitHub Pages 部署指南

本文档说明如何配置 GitHub Actions 自动获取数据和部署前端到 GitHub Pages。

## 📋 功能说明

1. **自动获取数据**：每6小时自动获取市场数据并保存为 JSON 文件
2. **自动部署前端**：当代码推送到 main 分支时，自动构建并部署到 GitHub Pages

## 🔧 配置步骤

### 1. 启用 GitHub Pages

1. 进入仓库的 **Settings** > **Pages**
2. 在 **Source** 部分，选择 **GitHub Actions**
3. 保存设置

### 2. 配置 GitHub Secrets（可选）

如果你的后端需要 API 密钥，可以在仓库的 **Settings** > **Secrets and variables** > **Actions** 中添加：

- `CMC_API_KEY`: CoinMarketCap API 密钥（可选）
- `TAAPI_SECRET`: TAAPI.io 密钥（可选）

**注意**：默认使用免费的 Binance 和 CoinGecko API，通常不需要配置密钥。

### 3. 修改仓库名称（如果需要）

如果你的 GitHub 仓库名称不是 `bullbear-dashboard`，需要修改 `frontend/vite.config.ts` 中的 `repoName` 变量：

```typescript
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'your-repo-name';
```

或者设置环境变量 `GITHUB_REPOSITORY` 为你的仓库名称。

## 📁 工作流程说明

### fetch-data.yml

- **触发时机**：
  - 每6小时自动运行（UTC 00:00 / 06:00 / 12:00 / 18:00）
  - Push to `main` or `feat/**` triggers the workflow (useful for feat testing)
  - 可以手动触发（Actions > fetch-data.yml > Run workflow）
  
- **功能**：
  - 运行 Python 脚本获取市场数据
  - 将数据保存到 `frontend/public/data/` 目录
  - 自动提交并推送数据文件

### deploy-pages.yml

- **触发时机**：
  - 推送到 `main` 分支时自动运行
  - 可以手动触发（Actions > deploy-pages.yml > Run workflow）
  
- **功能**：
  - 构建前端应用
  - 部署到 GitHub Pages

## 🚀 使用流程

1. **首次部署**：
   - 将代码推送到 `main` 分支
   - GitHub Actions 会自动构建并部署前端
   - 访问 `https://your-username.github.io/bullbear-dashboard/` 查看页面

2. **数据更新**：
   - 数据获取工作流每6小时自动运行
   - 数据文件会自动更新并提交到仓库
   - 前端会自动使用最新的数据文件

3. **手动触发**：
   - 如果需要立即获取数据，可以在 Actions 页面手动触发 `fetch-data.yml`
   - 如果需要重新部署，可以手动触发 `deploy-pages.yml`

## 📝 数据文件结构

数据文件保存在 `frontend/public/data/` 目录：

- `all_data.json`: 包含所有市场数据
- `state.json`: 包含市场状态机结果
- `btc_price.json`, `ma50.json`, `ma200.json` 等：各个数据类型的单独文件

## 🔍 故障排除

### 数据获取失败

1. 检查 GitHub Actions 日志，查看错误信息
2. 确认网络连接正常
3. 如果使用 API 密钥，确认 Secrets 配置正确

### 前端部署失败

1. 检查构建日志，查看是否有编译错误
2. 确认 `vite.config.ts` 中的 `base` 路径配置正确
3. 确认 GitHub Pages 已启用并设置为使用 GitHub Actions

### 数据文件未更新

1. 检查 `fetch-data.yml` 是否正常运行
2. 查看 Actions 日志，确认脚本执行成功
3. 确认数据文件已正确提交到仓库

## 📚 相关文件

- `.github/workflows/fetch-data.yml`: 数据获取工作流
- `.github/workflows/deploy-pages.yml`: 前端部署工作流
- `backend/scripts/fetch_and_save_data.py`: 数据获取脚本
- `frontend/vite.config.ts`: Vite 构建配置
- `frontend/src/App.vue`: 前端主组件（包含数据获取逻辑）


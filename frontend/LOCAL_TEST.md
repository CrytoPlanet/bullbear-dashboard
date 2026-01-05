# 本地测试指南

在推送 PR 之前，请在本地测试构建和运行，确保一切正常。

## 快速测试步骤

### 1. 安装依赖

```bash
cd frontend
pnpm install
```

### 2. 类型检查

```bash
pnpm run type-check
```

如果有类型错误，请先修复。

### 3. 构建测试

```bash
pnpm run build
```

确保构建成功，没有错误。

### 4. 预览构建结果

```bash
pnpm run preview
```

在浏览器中打开显示的地址（通常是 `http://localhost:4173`），检查页面是否正常显示。

### 5. 开发模式测试

```bash
pnpm run dev
```

在浏览器中打开显示的地址（通常是 `http://localhost:5173`），测试功能是否正常。

## 常见问题

### 类型检查失败

如果类型检查失败，可以：

1. **修复类型错误**（推荐）
   - 查看错误信息
   - 修复 `frontend/src/App.vue` 中的类型问题

2. **临时跳过类型检查**（仅用于测试）
   ```bash
   pnpm exec vite build
   ```

### 构建失败

1. 检查 Node.js 版本（需要 20.19.0 或更高）
   ```bash
   node --version
   ```

2. 清除缓存重新安装
   ```bash
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   ```

### 数据无法加载

1. 确保后端服务正在运行（如果使用 API）
2. 或者确保 `frontend/public/data/` 目录中有数据文件

## 推送前检查清单

- [ ] 类型检查通过：`pnpm run type-check`
- [ ] 构建成功：`pnpm run build`
- [ ] 预览正常：`pnpm run preview`
- [ ] 功能测试通过：`pnpm run dev`

完成以上步骤后，可以安全地推送 PR。


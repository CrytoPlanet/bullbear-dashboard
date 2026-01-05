import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// 获取仓库名称（用于 GitHub Pages 部署）
// GitHub Actions 会自动设置 GITHUB_REPOSITORY 环境变量
// 如果未设置，则根据 package.json 或默认值推断
let repoName = 'bullbear-dashboard';
if (process.env.GITHUB_REPOSITORY) {
  repoName = process.env.GITHUB_REPOSITORY.split('/')[1];
} else if (process.env.VITE_REPO_NAME) {
  repoName = process.env.VITE_REPO_NAME;
}

// 生产环境使用仓库名称作为 base 路径，开发环境使用根路径
const base = process.env.NODE_ENV === 'production' ? `/${repoName}/` : '/';

// https://vite.dev/config/
export default defineConfig({
  base,
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})

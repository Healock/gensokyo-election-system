import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // 必须设为 0.0.0.0 才能让 Docker 映射出端口
    port: 5173,
    allowedHosts: ['vote.healock.cc'] // 👈 新增这一行：给您的域名放行！
  }
})
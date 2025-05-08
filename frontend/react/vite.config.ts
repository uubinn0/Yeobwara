import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0", // ← 이 부분 필수
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'k12b107.p.ssafy.io'
    ],
    port: 5173,       // 명시적으로 포트 고정 (선택)
    hmr: {
      host: 'k12b107.p.ssafy.io',
      protocol: 'wss',
      clientPort: 443
    },
    https: true,
  },
});

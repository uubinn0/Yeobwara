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
      'k12b107.p.ssafy.io',
      'react'  // Docker 서비스 이름 추가
    ],
    port: 5173,       // 명시적으로 포트 고정 (선택)
    hmr: false,       // HMR 비활성화 - 개발 중에는 페이지 수동 새로고침 필요
    https: false,     // HTTP 사용
  },
});

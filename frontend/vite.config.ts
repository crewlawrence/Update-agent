import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/",
  plugins: [react()],
  server: {
    port: 5173, // local dev only
    proxy: {
      "/api": {
        target: "http://localhost:10000", // must match Express
        changeOrigin: true,
      },
    },
  },
});

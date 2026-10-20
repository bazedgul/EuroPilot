import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

type VitestOptions = {
  environment: string;
  setupFiles: string;
};

const config = ({ mode }: { mode: string }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_API_PROXY_TARGET || env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  return {
    plugins: [react()],
    server: { proxy: { "/api": backendTarget } },
    test: { environment: "jsdom", setupFiles: "./src/testSetup.ts" },
  } as Parameters<typeof defineConfig>[0] & { test: VitestOptions };
};

export default defineConfig(config as unknown as Parameters<typeof defineConfig>[0]);

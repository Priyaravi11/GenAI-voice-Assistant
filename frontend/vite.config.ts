import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react({ babel: { compact: true } })],
  server: {
    host: "0.0.0.0",
    port: 5173,
    middlewareMode: false
  },
  build: {
    target: "ES2020",
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ["console.log"]
      },
      mangle: true,
      format: {
        comments: false
      }
    },
    sourcemap: false,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          pages: [
            "./src/pages/Dashboard/Dashboard.tsx",
            "./src/pages/LiveCall/LiveCall.tsx",
            "./src/pages/Analytics/Analytics.tsx",
            "./src/pages/CallLogs/CallLogs.tsx",
            "./src/pages/HumanAgent/HumanAgent.tsx"
          ]
        },
        chunkFileNames: "js/[name]-[hash].js",
        entryFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split(".");
          const ext = info[info.length - 1];
          if (/png|jpe?g|gif|svg|webp/i.test(ext)) {
            return `images/[name]-[hash][extname]`;
          } else if (/woff|woff2|eot|ttf|otf/.test(ext)) {
            return `fonts/[name]-[hash][extname]`;
          } else if (ext === "css") {
            return `css/[name]-[hash][extname]`;
          }
          return `[name]-[hash][extname]`;
        }
      }
    }
  },
  css: {
    postcss: null,
    preprocessorOptions: {
      css: {
        additionalData: null
      }
    }
  },
  esbuild: {
    legalComments: "none"
  }
});

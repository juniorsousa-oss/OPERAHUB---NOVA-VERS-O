import { defineConfig } from "vite";
export default defineConfig({
  build: {
    outDir: "../static/mrp-v2",
    emptyOutDir: true,
    rollupOptions: {
      input: "src/main.jsx",
      output: {entryFileNames: "mrp.js", assetFileNames: "mrp.[ext]"}
    }
  }
});

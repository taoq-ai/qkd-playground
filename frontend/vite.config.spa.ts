import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * SPA build configuration — produces index.html + bundled JS/CSS
 * for embedding in the Python package.
 */
export default defineConfig({
  plugins: [react()],
  root: ".",
  build: {
    outDir: "dist-spa",
    emptyOutDir: true,
  },
});

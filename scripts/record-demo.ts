/**
 * Playwright script to record a demo GIF of the QKD Playground web UI.
 *
 * Takes screenshots at key moments during a BB84 simulation with
 * eavesdropper enabled, then stitches them into an animated GIF
 * using ffmpeg.
 *
 * Prerequisites:
 *   - Backend running on http://localhost:8000
 *   - Frontend running on http://localhost:5173
 *   - ffmpeg installed
 *
 * Usage:
 *   npx playwright install chromium   # first time only
 *   npx tsx scripts/record-demo.ts
 *
 * Or use the wrapper: bash scripts/record-demo.sh
 */

import { type Page, chromium } from "playwright";
import { execSync } from "child_process";
import { mkdirSync, rmSync, readdirSync } from "fs";
import { join, resolve } from "path";

const FRONTEND_URL = "http://localhost:5173";
const OUTPUT_DIR = resolve(__dirname, "..", "docs", "assets");
const FRAMES_DIR = join(OUTPUT_DIR, ".frames");
const OUTPUT_GIF = join(OUTPUT_DIR, "demo.gif");
const VIEWPORT = { width: 1280, height: 800 };
const FRAME_DELAY_MS = 2500;

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

let frameIndex = 0;

async function capture(page: Page, label: string) {
  const path = join(FRAMES_DIR, `frame-${String(frameIndex).padStart(3, "0")}-${label}.png`);
  await page.screenshot({ path, fullPage: false });
  console.log(`  📸 ${label}`);
  frameIndex++;
}

async function clickAndWait(page: Page, selector: string, waitFor: string, timeout = 15000) {
  await Promise.all([
    page.waitForSelector(waitFor, { timeout }),
    page.click(selector),
  ]);
  await sleep(800);
}

async function main() {
  rmSync(FRAMES_DIR, { recursive: true, force: true });
  mkdirSync(FRAMES_DIR, { recursive: true });

  console.log("🎬 Launching browser...");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    colorScheme: "dark",
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  // Log console errors for debugging
  page.on("console", (msg) => {
    if (msg.type() === "error") console.log(`  🔴 Console error: ${msg.text()}`);
  });
  page.on("pageerror", (err) => console.log(`  🔴 Page error: ${err.message}`));

  console.log("🌐 Navigating to frontend...");
  await page.goto(FRONTEND_URL, { waitUntil: "networkidle" });
  await sleep(1000);

  // Frame 1: Setup page (BB84 selected by default)
  await capture(page, "setup-bb84");

  // Enable eavesdropper
  console.log("🔧 Enabling eavesdropper...");
  await page.locator(".checkbox-label input[type='checkbox']").check();
  await sleep(500);
  await capture(page, "setup-eve-enabled");

  // Start simulation — click button and wait for simulation panel
  console.log("▶️  Starting BB84 + Eve simulation...");
  await page.click(".btn-primary");
  // Wait for the simulation panel (progress bar + controls) to appear
  await page.waitForSelector(".controls .btn-primary", { timeout: 15000 });
  await sleep(500);

  // Step through all 5 phases
  const phases = ["preparation", "transmission", "measurement", "sifting", "error-estimation"];
  for (let i = 0; i < phases.length; i++) {
    console.log(`  ➡️  Stepping: ${phases[i]}...`);

    // Click "Next Step"
    await page.click(".controls .btn-primary");
    // Wait for step display to appear/update
    await page.waitForSelector(".step-display", { timeout: 15000 });
    if (i > 0) {
      await page.waitForFunction(
        (expected: number) => {
          const el = document.querySelector(".step-number");
          if (!el) return false;
          const m = (el.textContent || "").match(/Step (\d+)/);
          return m ? parseInt(m[1]) >= expected : false;
        },
        i + 1,
        { timeout: 15000 }
      );
    }
    await sleep(800);

    // Scroll to show relevant content for later phases
    if (i >= 3) {
      await page.evaluate(() => {
        const el =
          document.querySelector(".eve-alert") ||
          document.querySelector(".results-panel") ||
          document.querySelector(".statistics-panel");
        if (el) el.scrollIntoView({ behavior: "instant", block: "center" });
      });
      await sleep(400);
    }
    await capture(page, `step-${i + 1}-${phases[i]}`);
  }

  // Scroll to show statistics panel
  console.log("📊 Capturing statistics...");
  await page.evaluate(() => {
    const el = document.querySelector(".statistics-panel");
    if (el) el.scrollIntoView({ behavior: "instant", block: "start" });
  });
  await sleep(400);
  await capture(page, "statistics");

  await browser.close();
  console.log(`\n✅ Captured ${frameIndex} frames`);

  // Stitch frames into GIF using ffmpeg
  console.log("🎞️  Creating GIF with ffmpeg...");

  // Rename frames to sequential numbers for ffmpeg
  const frames = readdirSync(FRAMES_DIR)
    .filter((f) => f.endsWith(".png"))
    .sort();

  for (let i = 0; i < frames.length; i++) {
    const src = join(FRAMES_DIR, frames[i]);
    const dst = join(FRAMES_DIR, `seq-${String(i).padStart(3, "0")}.png`);
    execSync(`mv "${src}" "${dst}"`);
  }

  const frameRate = 1000 / FRAME_DELAY_MS;
  const cmd = [
    "ffmpeg -y",
    `-framerate ${frameRate}`,
    `-i "${FRAMES_DIR}/seq-%03d.png"`,
    `-vf "scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3"`,
    "-loop 0",
    `"${OUTPUT_GIF}"`,
  ].join(" ");

  try {
    execSync(cmd, { stdio: "inherit" });
    console.log(`\n🎉 Demo GIF saved to: ${OUTPUT_GIF}`);
  } catch {
    console.error("❌ ffmpeg failed. Frames preserved at:", FRAMES_DIR);
    process.exit(1);
  }

  rmSync(FRAMES_DIR, { recursive: true, force: true });
}

main().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});

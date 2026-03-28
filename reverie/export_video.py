"""
export_video.py — Export a ChemVille replay to MP4

Usage (from repo root):
    venv/bin/python3 reverie/export_video.py \
        --sim_name chemville_run_01-s-8-1600-1800 \
        --output exports/chemville_run_01.mp4 \
        [--fps 10] \
        [--port 8000] \
        [--start_step 0]

Prerequisites:
    - Frontend server must be running:
          cd environment/frontend_server && ../../venv/bin/python3 manage.py runserver 8000
    - ffmpeg must be installed (brew install ffmpeg)
    - playwright must be installed (pip install playwright && playwright install chromium)
"""

import argparse
import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright


async def export(sim_name: str, output: str, fps: int, port: int, start_step: int):
    # Count available movement steps
    movement_dir = Path("environment/frontend_server/storage") / sim_name / "movement"
    if not movement_dir.exists():
        raise FileNotFoundError(f"Movement directory not found: {movement_dir}")
    step_files = [f for f in movement_dir.iterdir() if f.suffix == ".json"]
    max_steps = len(step_files)
    print(f"Found {max_steps} steps in {movement_dir}")

    frames_dir = Path(tempfile.mkdtemp(prefix="chemville_export_"))
    print(f"Saving frames to: {frames_dir}")

    url = f"http://localhost:{port}/replay/{sim_name}/{start_step}/?export=1"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1500, "height": 900})

        # Surface browser console + errors so we can diagnose failures
        page.on("console", lambda msg: print(f"  [browser {msg.type}] {msg.text}") if msg.type in ("error", "warn") else None)
        page.on("pageerror", lambda err: print(f"  [page error] {err}"))

        print(f"Opening: {url}")
        await page.goto(url, wait_until="load")

        # Wait for Phaser to finish loading the map (canvas appears)
        await page.wait_for_selector("#game-container canvas", timeout=30000)
        # Give Phaser a moment to render the first frame and start the AJAX loop
        await page.wait_for_timeout(5000)

        # Diagnostic: check what phase/step the game reports
        debug_text = await page.locator("#debug-status").inner_text()
        print(f"  Game state after load: {debug_text}")

        frame_num = 0
        current_step = start_step

        print(f"Capturing frames (Ctrl+C to abort)...")
        while current_step < max_steps:
            # Wait for the game to signal a completed step
            try:
                await page.wait_for_function(
                    f"document.body.getAttribute('data-export-step') === '{current_step}'",
                    timeout=30000
                )
            except Exception:
                debug_text = await page.locator("#debug-status").inner_text()
                print(f"  Timeout waiting for step {current_step} — game state: {debug_text}")
                break

            # Screenshot just the game canvas
            canvas = await page.locator("#game-container canvas").bounding_box()
            if canvas:
                frame_path = str(frames_dir / f"frame_{frame_num:05d}.png")
                await page.screenshot(path=frame_path, clip=canvas)
            else:
                frame_path = str(frames_dir / f"frame_{frame_num:05d}.png")
                await page.screenshot(path=frame_path)

            print(f"  step {current_step} → frame {frame_num}")
            frame_num += 1
            current_step += 1

            # Signal the game to advance to the next step
            await page.evaluate("window.advanceExport()")

        await browser.close()

    if frame_num == 0:
        print("No frames captured. Aborting.")
        shutil.rmtree(frames_dir)
        return

    # Encode with ffmpeg
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nEncoding {frame_num} frames → {output} at {fps} fps...")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ], check=True)

    shutil.rmtree(frames_dir)
    print(f"\nDone! Video saved to: {output_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Export a ChemVille replay to MP4")
    parser.add_argument("--sim_name", required=True,
                        help="Simulation folder name, e.g. chemville_run_01-s-8-1600-1800")
    parser.add_argument("--output", required=True,
                        help="Output MP4 path, e.g. exports/run01.mp4")
    parser.add_argument("--fps", type=int, default=10,
                        help="Frames per second in the output video (default: 10)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port the frontend server is running on (default: 8000)")
    parser.add_argument("--start_step", type=int, default=0,
                        help="Step to start replay from (default: 0)")
    args = parser.parse_args()

    asyncio.run(export(
        sim_name=args.sim_name,
        output=args.output,
        fps=args.fps,
        port=args.port,
        start_step=args.start_step,
    ))


if __name__ == "__main__":
    main()

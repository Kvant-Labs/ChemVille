#!/usr/bin/env python3
"""
regenerate_maze_csvs.py — Regenerate all backend maze CSV files from the Tiled map JSON.

Run this any time the Tiled map is edited and re-exported. Must be run from the repo root:
    python3 tools/regenerate_maze_csvs.py

The script reads chemville_16april.json and writes six CSV files under:
    environment/frontend_server/static_dirs/assets/chemville/matrix/maze/
"""
import json
from pathlib import Path

MAP_JSON = Path("environment/frontend_server/static_dirs/assets/chemville/visuals/chemville_16april.json")
MATRIX_DIR = Path("environment/frontend_server/static_dirs/assets/chemville/matrix/maze")
META_INFO = Path("environment/frontend_server/static_dirs/assets/chemville/maze_meta_info.json")


def load_map(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def get_tileset_firstgid(m: dict, name_fragment: str) -> int:
    """Return firstgid for the tileset whose source/name contains name_fragment."""
    for ts in m["tilesets"]:
        src = ts.get("source", ts.get("name", ""))
        if name_fragment in src:
            return ts["firstgid"]
    raise ValueError(f"Tileset not found: {name_fragment!r}")


def extract_layer_flat(m: dict, layer_name: str, W: int, H: int) -> list[int]:
    """
    Extract tile data from a (possibly infinite/chunked) layer into a flat W×H list.
    Returns local tile IDs (absolute - firstgid of the layer's tileset, or 0 for empty).
    """
    # Determine the firstgid to subtract based on which tileset the layer uses.
    # We detect this by sampling the first non-zero tile.
    tilesets = sorted(m["tilesets"], key=lambda t: t["firstgid"], reverse=True)

    def to_local(abs_id: int) -> int:
        if abs_id == 0:
            return 0
        for ts in tilesets:
            if abs_id >= ts["firstgid"]:
                return abs_id - ts["firstgid"]
        return abs_id

    grid = [0] * (W * H)

    for layer in m["layers"]:
        if layer["name"] != layer_name:
            continue

        chunks = layer.get("chunks")
        if chunks:
            # Infinite map mode
            for chunk in chunks:
                cx, cy = chunk["x"], chunk["y"]
                cw = chunk["width"]
                for i, abs_id in enumerate(chunk["data"]):
                    wx = cx + (i % cw)
                    wy = cy + (i // cw)
                    if 0 <= wx < W and 0 <= wy < H and abs_id != 0:
                        grid[wy * W + wx] = to_local(abs_id)
        else:
            # Fixed-size map mode
            for i, abs_id in enumerate(layer.get("data", [])):
                if abs_id != 0:
                    grid[i] = to_local(abs_id)
        break

    return grid


def write_csv(path: Path, data: list[int]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(",".join(str(v) for v in data) + "\n")
    print(f"  Written: {path}  ({sum(1 for v in data if v != 0)} non-zero tiles)")


def main():
    print(f"Loading map: {MAP_JSON}")
    m = load_map(MAP_JSON)
    W, H = m["width"], m["height"]
    print(f"Map dimensions: {W}×{H} tiles")

    # Update maze_meta_info.json to match
    with open(META_INFO) as f:
        meta = json.load(f)
    if meta["maze_width"] != W or meta["maze_height"] != H:
        print(f"Updating maze_meta_info.json: {meta['maze_width']}×{meta['maze_height']} → {W}×{H}")
        meta["maze_width"] = W
        meta["maze_height"] = H
        with open(META_INFO, "w") as f:
            json.dump(meta, f, indent=2)

    print(f"\nGenerating CSVs in {MATRIX_DIR}/")

    layer_to_csv = {
        "Collisions":              "collision_maze.csv",
        "Sector Blocks":           "sector_maze.csv",
        "Arena Blocks":            "arena_maze.csv",
        "Object Interaction Blocks": "game_object_maze.csv",
        "Spawning Blocks":         "spawning_location_maze.csv",
        "World Blocks":            "world_blocks.csv",
    }

    for layer_name, csv_name in layer_to_csv.items():
        print(f"  Layer '{layer_name}' → {csv_name}")
        data = extract_layer_flat(m, layer_name, W, H)
        write_csv(MATRIX_DIR / csv_name, data)

    print("\nDone. Run the simulation to verify paths and spawns look correct.")


if __name__ == "__main__":
    main()

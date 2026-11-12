"""Run A* on map images and show the result.

You do NOT need to change this file. Fix astar.py instead.

Usage:
    python run.py                      # runs all 3 maps
    python run.py maps/map1_easy.png   # runs one map
    python run.py --no-window          # only save pictures, no window

Map colours:
    black = rock (wall)   white = ground (cost 1)   yellow = sand (cost 5)
    green = start         red   = goal
"""
import os
import sys
import time

import cv2
import numpy as np

import astar

# BGR colours used in the map images
PALETTE = {
    "wall": (0, 0, 0),
    "ground": (255, 255, 255),
    "sand": (90, 200, 230),
    "start": (0, 200, 0),
    "goal": (0, 0, 230),
}
COST = {"wall": astar.WALL, "ground": 1, "sand": 5, "start": 1, "goal": 1}
SCALE = 15  # screen pixels per map cell
DEFAULT_MAPS = ["maps/map1_easy.png", "maps/map2_harder.png", "maps/map3_no_path.png"]


def load_map(path):
    """Read a map image. Returns (grid, start, goal)."""
    img = cv2.imread(path)
    if img is None:
        sys.exit(f"Cannot read map image: {path}")
    names = list(PALETTE)
    colours = np.array([PALETTE[n] for n in names], dtype=int)
    # nearest palette colour for every pixel
    dist = ((img[:, :, None, :].astype(int) - colours[None, None]) ** 2).sum(axis=3)
    label = dist.argmin(axis=2)
    grid = np.vectorize(lambda i: COST[names[i]])(label).astype(int)
    starts = np.argwhere(label == names.index("start"))
    goals = np.argwhere(label == names.index("goal"))
    if len(starts) != 1 or len(goals) != 1:
        sys.exit(f"{path}: map needs exactly one start and one goal pixel")
    start = (int(starts[0][1]), int(starts[0][0]))  # (x, y)
    goal = (int(goals[0][1]), int(goals[0][0]))
    return grid, start, goal


def draw(grid, start, goal, path, explored):
    h, w = grid.shape
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    canvas[grid == 1] = PALETTE["ground"]
    canvas[grid == 5] = PALETTE["sand"]
    canvas[grid == astar.WALL] = PALETTE["wall"]
    for (x, y) in explored:
        if 0 <= x < w and 0 <= y < h and grid[y, x] != astar.WALL:
            canvas[y, x] = (canvas[y, x] * 0.6 + np.array([255, 200, 120]) * 0.4).astype(np.uint8)
    canvas[start[1], start[0]] = PALETTE["start"]
    canvas[goal[1], goal[0]] = PALETTE["goal"]
    big = cv2.resize(canvas, (w * SCALE, h * SCALE), interpolation=cv2.INTER_NEAREST)
    # grid lines
    for i in range(0, w * SCALE, SCALE):
        cv2.line(big, (i, 0), (i, h * SCALE), (200, 200, 200), 1)
    for i in range(0, h * SCALE, SCALE):
        cv2.line(big, (0, i), (w * SCALE, i), (200, 200, 200), 1)
    if path:
        pts = [(int(x * SCALE + SCALE // 2), int(y * SCALE + SCALE // 2)) for x, y in path]
        for a, b in zip(pts, pts[1:]):
            cv2.line(big, a, b, (200, 0, 200), 3)
    return big


def run_one(map_path, show_window):
    grid, start, goal = load_map(map_path)
    t0 = time.perf_counter()
    path, cost, explored = astar.astar(grid, start, goal)
    ms = (time.perf_counter() - t0) * 1000
    name = os.path.splitext(os.path.basename(map_path))[0]

    if path is None:
        text = f"{name}: No path found | cells explored: {len(explored)}"
    else:
        text = (f"{name}: path cost {cost} | steps {len(path) - 1} | "
                f"cells explored {len(explored)} | {ms:.1f} ms")
    print(text)
    if path is not None:
        # independent check: add up the real map cost of the drawn path
        h, w = grid.shape
        inside = all(0 <= x < w and 0 <= y < h for x, y in path)
        real = sum(int(grid[y, x]) for x, y in path[1:]) if inside else None
        if not inside:
            print("  WARNING: the path leaves the map!")
        elif any(grid[y, x] == astar.WALL for x, y in path):
            print("  WARNING: the path goes through rock!")
        elif real != cost:
            print(f"  WARNING: astar says cost {cost}, but the drawn path really costs {real}")

    img = draw(grid, start, goal, path, explored)
    banner = np.full((30, img.shape[1], 3), 255, dtype=np.uint8)
    cv2.putText(banner, text.replace(f"{name}: ", ""), (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    img = np.vstack([banner, img])
    os.makedirs("output", exist_ok=True)
    out = os.path.join("output", f"{name}_result.png")
    cv2.imwrite(out, img)
    print(f"  saved picture: {out}")

    if show_window:
        try:
            cv2.imshow("A* result (press any key)", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except cv2.error:
            print("  (cannot open a window on this computer - look at the saved picture)")


def main():
    args = sys.argv[1:]
    show_window = "--no-window" not in args
    maps = [os.path.abspath(a) for a in args if a != "--no-window"] or DEFAULT_MAPS
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # output/ goes next to run.py
    for m in maps:
        run_one(m, show_window)


if __name__ == "__main__":
    main()

"""Run A* and Dijkstra on the supplied maps without modifying run.py."""

import argparse
import csv
from pathlib import Path
import statistics
import time

import cv2
import numpy as np

import astar
import run

ROOT = Path(__file__).resolve().parent


def validate_path(grid, start, goal, path, cost):
    """Check returned paths independently of the search's neighbor function."""
    if path is None:
        if cost is not None:
            raise ValueError('A missing path must have no cost')
        return
    if not path or path[0] != start or path[-1] != goal:
        raise ValueError('Path endpoints do not match the mission')
    height, width = grid.shape
    for x, y in path:
        if not (0 <= x < width and 0 <= y < height) or grid[y, x] == astar.WALL:
            raise ValueError('Path leaves the map or enters a wall')
    if any(abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1 for a, b in zip(path, path[1:])):
        raise ValueError('Path contains a non-orthogonal step')
    if sum(int(grid[y, x]) for x, y in path[1:]) != cost:
        raise ValueError('Reported cost differs from actual terrain cost')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats', type=int, default=7, help='timed searches per map/algorithm (default: 7)')
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error('--repeats must be positive')

    output = ROOT / 'output'
    output.mkdir(exist_ok=True)
    rows = []
    for relative_map in run.DEFAULT_MAPS:
        map_path = ROOT / relative_map
        grid, start, goal = run.load_map(str(map_path))
        costs = []
        for name, search in (('astar', astar.astar), ('dijkstra', astar.dijkstra)):
            durations = []
            for _ in range(args.repeats):
                begin = time.perf_counter()
                path, cost, explored = search(grid, start, goal)
                durations.append((time.perf_counter() - begin) * 1000)
            validate_path(grid, start, goal, path, cost)
            costs.append(cost)
            row = {
                'map': map_path.stem,
                'algorithm': name,
                'found': path is not None,
                'cost': int(cost) if cost is not None else None,
                'steps': len(path) - 1 if path is not None else None,
                'explored': len(explored),
                'median_ms': round(statistics.median(durations), 3),
            }
            rows.append(row)
            print(', '.join(f'{key}={value}' for key, value in row.items()))

            image = run.draw(grid, start, goal, path, explored)
            banner = np.full((54, image.shape[1], 3), 255, dtype=np.uint8)
            headline = f'{name.upper()}: cost {row["cost"]}, steps {row["steps"]}' if path else f'{name.upper()}: No path found'
            detail = f'Explored {len(explored)} cells | median {row["median_ms"]:.3f} ms'
            for y, text in ((20, headline), (43, detail)):
                cv2.putText(banner, text, (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            folder = output / name
            folder.mkdir(exist_ok=True)
            destination = folder / f'{map_path.stem}_result.png'
            if not cv2.imwrite(str(destination), np.vstack((banner, image))):
                raise OSError(f'Could not write {destination}')
        if costs[0] != costs[1]:
            raise ValueError(f'A* and Dijkstra disagree on optimal cost for {relative_map}')

    with (output / 'pathfinding_comparison.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = [
        '# A* and Dijkstra results', '',
        f'Both algorithms used the same four-connected maps and terrain-entry costs. '
        f'Timing is the median of {args.repeats} searches, excluding map loading and rendering.', '',
        '| Map | Algorithm | Cost | Steps | Explored cells | Median ms |',
        '| --- | --- | ---: | ---: | ---: | ---: |',
    ]
    for row in rows:
        cost = row['cost'] if row['found'] else 'No path'
        steps = row['steps'] if row['found'] else '-'
        report.append(f'| {row["map"]} | {row["algorithm"]} | {cost} | {steps} | {row["explored"]} | {row["median_ms"]:.3f} |')
    report.extend([
        '',
        'A* uses f = g + h with Manhattan distance. Dijkstra uses f = g (h = 0). '
        'Manhattan distance is consistent here because moves are orthogonal and each traversable cell costs at least 1. '
        'Both should return the same optimal cost; ties can produce different paths. '
        'Sand costs 5, so the cheapest route need not have the fewest steps.', '',
        'On an unreachable map, both must exhaust the reachable component and return no path. '
        'Timing varies across runs and does not guarantee that A* is always faster. '
        'An explored cell is a distinct cell removed from the frontier and processed, including the goal if reached.', '',
        'Use these measured results to write the required handwritten comparison. '
        'Image folders: `astar/` and `dijkstra/`. The supplied `run.py` is unchanged.', '',
    ])
    (output / 'pathfinding_comparison.md').write_text('\n'.join(report), encoding='utf-8')


if __name__ == '__main__':
    main()

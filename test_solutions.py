"""Regression checks: python -m unittest -v test_solutions."""

import csv
import io
import math
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

import astar
import light

ROOT = Path(__file__).resolve().parent


class LightTests(unittest.TestCase):
    def controller(self, targets=None):
        return light.LightController([(0.0, 0.0)] if targets is None else targets)

    def test_haversine_reference_distances(self):
        self.assertEqual(light.haversine((12, 30), (12, 30)), 0)
        self.assertAlmostEqual(light.haversine((0, 0), (0, 1)), 111194.92664455874, places=6)
        self.assertAlmostEqual(light.haversine((0, 0), (0, 180)), math.pi * light.EARTH_RADIUS_M)
        self.assertLess(light.haversine((0, 179.99999), (0, -179.99999)), 3)

    def test_first_fix_is_not_proof_of_stopping(self):
        self.assertEqual(self.controller().update(0, 'AUTO', (0, 0)), 'red')

    def test_five_seconds_not_five_rows_and_final_target(self):
        state = self.controller()
        state.update(0, 'AUTO', (0, 0))
        for timestamp in (1, 2, 4, 5):
            self.assertEqual(state.update(timestamp, 'AUTO', (0, 0)), 'green')
        self.assertEqual(state.update(6, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(7, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.target_index, 1)

    def test_green_survives_manual_and_missing_position(self):
        state = self.controller()
        state.update(0, 'AUTO', (0, 0))
        self.assertEqual(state.update(1, 'AUTO', (0, 0)), 'green')
        self.assertEqual(state.update(2, 'MANUAL', None), 'green')
        self.assertEqual(state.update(6, 'MANUAL', None), 'blue')

    def test_manual_cannot_trigger_arrival(self):
        state = self.controller()
        for timestamp in range(8):
            self.assertEqual(state.update(timestamp, 'MANUAL', (0, 0)), 'blue')
        self.assertEqual(state.target_index, 0)

    def test_later_target_cannot_be_visited_first(self):
        state = self.controller([(1, 1), (0, 0)])
        state.update(0, 'AUTO', (0, 0))
        self.assertEqual(state.update(1, 'AUTO', (0, 0)), 'red')

    def test_ordered_targets_and_baseline_on_expiry(self):
        state = self.controller([(0, 0), (0, 0)])
        state.update(0, 'AUTO', (0, 0))
        self.assertEqual(state.update(1, 'AUTO', (0, 0)), 'green')
        self.assertEqual(state.update(6, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(7, 'AUTO', (0, 0)), 'green')
        self.assertEqual(state.update(12, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(13, 'AUTO', (0, 0)), 'red')

    def test_proximity_and_speed_boundaries(self):
        # Control the geometric measurements to test the exact inequalities.
        for distance, speed, expected in ((3.0, 0.49, 'green'), (3.00001, 0.49, 'red'), (3, 0.5, 'red')):
            with self.subTest(distance=distance, speed=speed):
                state = self.controller()
                state.update(0, 'AUTO', (0, 0))
                with patch('light.haversine', side_effect=[speed, distance]):
                    self.assertEqual(state.update(1, 'AUTO', (0, 0)), expected)

    def test_elapsed_time_used_across_missing_fixes(self):
        state = self.controller()
        state.update(0, 'AUTO', (0, 0.00001))
        self.assertEqual(state.update(1, 'AUTO', None), 'red')
        # Roughly 1.11 meters over 4 seconds is below the speed threshold.
        self.assertEqual(state.update(4, 'AUTO', (0, 0)), 'green')

    def test_non_increasing_timestamps_do_not_trigger_or_rewind(self):
        state = self.controller()
        state.update(10, 'AUTO', (0, 0))
        self.assertEqual(state.update(10, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(9, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(11, 'AUTO', (0, 0)), 'green')
        self.assertEqual(state.update(8, 'AUTO', None), 'green')
        self.assertEqual(state.update(16, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(12, 'AUTO', (0, 0)), 'red')

    def test_empty_targets_and_unknown_mode(self):
        state = self.controller([])
        self.assertEqual(state.update(0, None, None), 'blue')
        self.assertEqual(state.update(1, 'AUTO', (0, 0)), 'red')
        self.assertEqual(state.update(2, None, (0, 0)), 'red')
        state = self.controller()
        state.update(0, 'AUTO', (0, 0))
        self.assertEqual(state.update(1, None, (0, 0)), 'red')

    def test_invalid_positions(self):
        for lat, lon in (('', ''), ('nan', '0'), ('0', 'inf'), ('91', '0'), ('0', '-181')):
            with self.subTest(lat=lat, lon=lon):
                self.assertIsNone(light.position({'lat': lat, 'lon': lon}))

    def test_csv_anomalies_output_and_diagnostics(self):
        source = io.StringIO('\ufeff time_s , mode , lat , lon\n0, auto ,0,0\n1,AUTO,,\n2,AUTO,0,0\ninvalid,AUTO,0,0\n3,AUTO,0,0\n')
        output, diagnostics = io.StringIO(), io.StringIO()
        light.process_log(source, [(0, 0)], output, diagnostics)
        self.assertEqual(output.getvalue(), '0,red\n1,red\n2,green\n3,green\n')
        self.assertIn('invalid time_s', diagnostics.getvalue())
        self.assertIn('invalid GPS', diagnostics.getvalue())

    def test_csv_schema_and_target_validation(self):
        with self.assertRaises(ValueError):
            light.load_targets(io.StringIO('lat,lon\nnan,0\n'))
        with self.assertRaises(ValueError):
            light.load_targets(io.StringIO('lat,lat,lon\n0,0,0\n'))
        with self.assertRaises(ValueError):
            list(light.csv_rows(io.StringIO('time_s,mode\n0,AUTO\n'), ('lat',)))
        self.assertEqual(light.load_targets(io.StringIO('target,lat,lon\n')), [])

    def test_both_supplied_logs_cli_contract(self):
        for name, count in (('mission_log_1.csv', 212), ('mission_log_2.csv', 155)):
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, str(ROOT / 'light.py'), str(ROOT / name), str(ROOT / 'targets.csv')], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                with (ROOT / name).open(newline='') as stream:
                    timestamps = [row['time_s'] for row in csv.DictReader(stream)]
                records = list(csv.reader(io.StringIO(result.stdout)))
                self.assertEqual(len(records), count)
                self.assertEqual([row[0] for row in records], timestamps)
                self.assertTrue(all(len(row) == 2 and row[1] in ('red', 'blue', 'green') for row in records))
                if name == 'mission_log_1.csv':
                    self.assertFalse(set(map(str, range(118, 124))) & {row[0] for row in records})

    def test_cli_file_error_has_no_result_output(self):
        result = subprocess.run([sys.executable, str(ROOT / 'light.py'), 'missing-log.csv', str(ROOT / 'targets.csv')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('light.py:', result.stderr)


def reference_cost(grid, start, goal):
    """Independent shortest-path oracle using repeated edge relaxation, no heap."""
    height, width = len(grid), len(grid[0])
    distance = {start: 0}
    for _ in range(width * height):
        changed = False
        for y in range(height):
            for x in range(width):
                if grid[y][x] == -1 or (x, y) not in distance:
                    continue
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] != -1:
                        candidate = distance[x, y] + int(grid[ny][nx])
                        if candidate < distance.get((nx, ny), math.inf):
                            distance[nx, ny] = candidate
                            changed = True
        if not changed:
            break
    return distance.get(goal)


class PathfindingTests(unittest.TestCase):
    def check_searches(self, grid, start, goal, expected):
        for search in (astar.astar, astar.dijkstra):
            with self.subTest(algorithm=search.__name__):
                path, cost, explored = search(grid, start, goal)
                self.assertEqual(cost, expected)
                if expected is None:
                    self.assertIsNone(path)
                    continue
                self.assertEqual(path[0], start)
                self.assertEqual(path[-1], goal)
                self.assertIn(goal, explored)
                self.assertEqual(sum(int(grid[y][x]) for x, y in path[1:]), cost)
                for x, y in path:
                    self.assertTrue(0 <= x < len(grid[0]) and 0 <= y < len(grid))
                    self.assertNotEqual(grid[y][x], -1)
                for a, b in zip(path, path[1:]):
                    self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_rectangular_grid_and_edges(self):
        self.check_searches([[1, 1, 1], [-1, -1, 1]], (0, 0), (2, 1), 3)
        self.check_searches([[1], [1], [1]], (0, 0), (0, 2), 2)

    def test_weighted_detour(self):
        self.check_searches([[1, 5, 1], [1, 1, 1]], (0, 0), (2, 0), 4)

    def test_unreachable_goal(self):
        self.check_searches([[1, -1, 1]], (0, 0), (2, 0), None)

    def test_start_is_goal(self):
        self.check_searches([[1]], (0, 0), (0, 0), 0)

    def test_invalid_endpoints_and_empty_grid(self):
        self.check_searches([[1, -1]], (0, 0), (1, 0), None)
        self.check_searches([[1]], (-1, 0), (0, 0), None)
        self.check_searches([], (0, 0), (0, 0), None)
        with self.assertRaises(ValueError):
            astar.astar([[1], [1, 1]], (0, 0), (0, 1))

    def test_seeded_maps_against_independent_shortest_path_oracle(self):
        rng = random.Random(2026)
        for case in range(60):
            width, height = rng.randint(2, 8), rng.randint(2, 7)
            grid = [[rng.choice([1, 1, 1, 5, -1]) for _ in range(width)] for _ in range(height)]
            grid[0][0] = grid[-1][-1] = 1
            with self.subTest(case=case):
                goal = width - 1, height - 1
                self.check_searches(grid, (0, 0), goal, reference_cost(grid, (0, 0), goal))

    def test_supplied_maps_against_independent_oracle(self):
        import run
        for name in run.DEFAULT_MAPS:
            with self.subTest(map=name):
                grid, start, goal = run.load_map(str(ROOT / name))
                self.check_searches(grid, start, goal, reference_cost(grid, start, goal))


if __name__ == '__main__':
    unittest.main()

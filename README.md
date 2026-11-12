# Mongol-Tori autonomy coding tasks

Implemented Task 2 and the optional pathfinding bonus. Tasks 1, 3, and 4 still require your handwritten work. No code was used to solve Task 1.

## Task 2: Status lights

From this folder, run exactly as required:

```powershell
python light.py mission_log_1.csv targets.csv
python light.py mission_log_2.csv targets.csv
```

`light.py` is standalone and needs only Python's standard library. Standard output contains only `time_s,light` records, without a header. Diagnostics go to standard error.

Generated results are already saved:

| Input | Output | Records | Green timestamps, inclusive |
| --- | --- | ---: | --- |
| `mission_log_1.csv` | `output/mission_log_1_lights.csv` | 212 | 75-79 and 206-210 |
| `mission_log_2.csv` | `output/mission_log_2_lights.csv` | 155 | 58-62 and 136-140 |

The first log has no records for seconds 118-123; the output has none either. Missing GPS fixes are reported in the corresponding `output/*_diagnostics.txt` files.

### Algorithm and decisions

1. Read targets in CSV row order. Do not select the closest target or skip ahead.
2. Estimate speed from the last valid position to the current valid position, divided by their actual timestamp difference. The first valid fix has unknown speed and cannot establish arrival.
3. Arrival requires AUTO, Haversine distance at most 3.0 meters, and speed strictly below 0.5 m/s.
4. An arrival at `t` starts green for `[t, t + 5)`. Green remains active through mode changes and GPS dropouts, and repeated qualifying fixes do not extend it.
5. At the first sample at or after expiration, advance the target once and display the current standard mode color. A subsequent sample can trigger the next arrival. After the final target, continue normal mode colors.

The state consists of the target index, green expiration timestamp, last valid GPS fix, last processed timestamp, and last known mode. Processing is linear in log length and streams records without storing the whole log.

### Anomaly policies

The recruitment specification does not define every malformed-input case. This implementation uses these conventions consistently for all files:

- Invalid/missing/non-finite/out-of-range coordinates cannot trigger arrival. Keep printing the mode color or an active green indication; retain the last valid GPS fix for the next speed estimate.
- Across missing seconds or missing GPS fixes, speed is interval-average speed. No interpolation, invented rows, or arbitrary maximum speed/gap thresholds are added. Average speed cannot prove the rover was stopped during the final second of an unobserved interval.
- Duplicate or backward timestamps still produce records, but do not advance the mission timer or change GPS history. The current mode can update the baseline color. An active green period is evaluated using the latest accepted time; earlier records do not rewind it.
- Unknown modes retain the last known mode color, defaulting to MANUAL/blue before any known mode. An unknown mode cannot authorize arrival.
- Records with an invalid/negative/non-finite timestamp are diagnosed and omitted because no valid timestamped result can be emitted. Valid timestamps retain their original stripped spelling in the output.
- Header whitespace, a UTF-8 BOM, and mode capitalization/whitespace are accepted. Extra fields invalidate that row's GPS fix. Blank physical lines are not telemetry samples.
- Empty target lists with valid headers leave normal mode indication active. Invalid target coordinates, missing/duplicate required headers, malformed CSV quoting, unreadable files, and invalid text encoding produce a clear error and exit code 2. Invalid targets are never silently skipped. A file-level error discovered after processing starts can leave earlier valid results on standard output.

## Bonus: Fixed A* and Dijkstra

`run.py` is unchanged. Its SHA-256 remains:

```text
614D410E24EBD95C0B31453D64EF85E45CA8B5853980AB72DAEFBAC16A565163
```

### Five fixes in astar.py

| Original defect | Correction | Why it matters |
| --- | --- | --- |
| Read `grid[x][y]` | Read `grid[y][x]` | Rows are y and columns are x; transposition reads the wrong obstacles and costs and can fail on rectangular grids. |
| Squared coordinate differences in the heuristic | Use `abs(dx) + abs(dy)` | Manhattan distance is a consistent lower bound for four-direction movement with costs at least 1. The original estimate can overestimate and undermine optimality. |
| Accepted indices equal to width/height | Use strict upper bounds | Valid indices end at width-1 and height-1. |
| Added 1 for every move | Add the destination cell's terrain cost | Sand costs 5; the goal is minimum total cost, not simply minimum steps. The start cell is not charged. |
| Unconditional `while True` with heap removal | Loop while the frontier is nonempty | Unreachable goals return `(None, None, explored)` instead of crashing. |

Both algorithms share the same movement and terrain model. A* uses priority `g + h`; Dijkstra uses `g` by setting the heuristic to zero. The consistent Manhattan heuristic makes closing a node after its first expansion safe under this assignment's costs. Empty grids and invalid/blocked endpoints return no path; ragged grids raise a clear error.

Programmatic interfaces:

```python
from astar import astar, dijkstra

path, cost, explored = astar(grid, start, goal)
path, cost, explored = dijkstra(grid, start, goal)
# Equivalent:
path, cost, explored = astar(grid, start, goal, use_dijkstra=True)
```

### Run the supplied maps

Python 3.14.0 was used with NumPy 2.5.4 and OpenCV 5.0.0. The dependencies are installed in this folder's `.venv`; activating it is optional when using its Python executable directly.

On a fresh checkout, set up the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the original harness without opening windows:

```powershell
.\.venv\Scripts\python.exe run.py --no-window
```

Run both algorithms and produce separate images and a comparison:

```powershell
.\.venv\Scripts\python.exe compare_pathfinding.py
```

Outputs:

- `output/map*_result.png`: the original runner's three A* images.
- `output/astar/` and `output/dijkstra/`: separate exports for each algorithm on all three maps.
- `output/pathfinding_comparison.csv`: costs, steps, explored cells, and median timings.
- `output/pathfinding_comparison.md`: measured results and discussion for your handwritten comparison.

### Verified results

| Map | Optimal cost | Steps | A* explored | Dijkstra explored |
| --- | ---: | ---: | ---: | ---: |
| map1_easy | 72 | 72 | 851 | 1234 |
| map2_harder | 212 | 156 | 427 | 452 |
| map3_no_path | No path | - | 1542 | 1542 |

Both algorithms return the same optimal costs. A* explores fewer cells on the two reachable maps. Both exhaust the reachable component on the no-path map. Measured runtime varies; fewer expansions do not guarantee lower runtime on every map. Tie-breaking uses the cell coordinates when priorities are equal, so explored counts also depend on that convention.

Cost 212 with 156 steps on map 2 includes 14 entries into sand: each adds 4 above the ordinary cost of 1. This is a useful check that terrain weighting is working.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_solutions
```

All 23 tests passed. Checks cover telemetry boundaries, timers, target order, missing fixes, timestamp anomalies, CLI output/errors, rectangular grids, weighted detours, unreachable goals, and invalid endpoints. Both searches were checked against an independent repeated-edge-relaxation shortest-path oracle on 60 generated grids and all three supplied maps. Returned paths are also checked for endpoints, legal adjacent moves, walls, and actual terrain cost.

## Submission

- Required code: `light.py`.
- Bonus code: fixed `astar.py`; include `compare_pathfinding.py` to reproduce the comparison, the map exports, and dependency information.
- Still handwritten: Task 1 calculations, Task 3 answers, Task 4 explanations, and the bonus comparison if submitting the bonus. Use the generated comparison as evidence, then explain the results in your own words.

The review in `REQUIREMENTS_ANALYSIS.md` records the original requirements and the earlier state before starter files were uploaded; this README describes the implemented state.

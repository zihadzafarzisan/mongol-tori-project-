# A* and Dijkstra results

Both algorithms used the same four-connected maps and terrain-entry costs. Timing is the median of 7 searches, excluding map loading and rendering.

| Map | Algorithm | Cost | Steps | Explored cells | Median ms |
| --- | --- | ---: | ---: | ---: | ---: |
| map1_easy | astar | 72 | 72 | 851 | 4.860 |
| map1_easy | dijkstra | 72 | 72 | 1234 | 6.444 |
| map2_harder | astar | 212 | 156 | 427 | 1.767 |
| map2_harder | dijkstra | 212 | 156 | 452 | 1.860 |
| map3_no_path | astar | No path | - | 1542 | 8.422 |
| map3_no_path | dijkstra | No path | - | 1542 | 8.705 |

A* uses f = g + h with Manhattan distance. Dijkstra uses f = g (h = 0). Manhattan distance is consistent here because moves are orthogonal and each traversable cell costs at least 1. Both should return the same optimal cost; ties can produce different paths. Sand costs 5, so the cheapest route need not have the fewest steps.

On an unreachable map, both must exhaust the reachable component and return no path. Timing varies across runs and does not guarantee that A* is always faster. An explored cell is a distinct cell removed from the frontier and processed, including the goal if reached.

Use these measured results to write the required handwritten comparison. Image folders: `astar/` and `dijkstra/`. The supplied `run.py` is unchanged.

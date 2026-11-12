# Recruitment requirements and output analysis

Implementation update: the starter files were subsequently uploaded. Task 2 and the bonus are now implemented and verified; see `README.md` and `output/pathfinding_comparison.md`. The evidence inventory and missing-artifact statements below describe the initial review, before those uploads.

Reviewed source: `Autonomy Recruitment Tasks 2026.md`, all 186 lines.

This is a requirements review, not an implementation or a claim that any submission has passed. Task 1 explicitly prohibits code; this review does not calculate that task using code.

## 1. Evidence available

- The workspace initially contained only the requirements Markdown. No submitted solutions, CSV inputs, handwritten calculations, Python files, maps, or exported images were present.
- The supplied repository URL is `https://github.com/zihadzafarzisan/mongol-tori-project-.git`. A successful `git ls-remote` returned no advertised references, consistent with an empty repository. There was no remote implementation available to inspect through that check.
- This directory has no local `.git`. Git discovers a repository rooted at `E:/` whose origin points to a different project. Its remote and contents were left untouched.
- `[Drive_Link]` and `[File_Link]` in the requirements are placeholders, not usable download links. The required datasets and bonus starter files cannot be obtained from those placeholders.

Consequently, exact telemetry outputs, numerical submission accuracy, the five actual A* bugs, and exported path images cannot currently be evaluated.

## 2. Deliverables and acceptance conditions

| Task | Required submission | What a correct result must demonstrate |
| --- | --- | --- |
| 1: Route planning | Photos of handwritten calculations for all three legs; complete turn/drive sequence; GPS uncertainty discussion | Haversine distances, compass bearings, relative turns from the previous heading, correct waypoint order |
| 2: Status lights | One unchanged `light.py`, invoked with mission-log and target CSV paths | Correct mode colors, ordered arrivals, all three arrival conditions, five-second green interval, robust input handling, exact output format |
| 3: Learning and bias | Handwritten rule, predictions for A-D, score, and five reflections | Rule fixed before testing, honest comparison to supplied labels, distinction between useful sign features and incidental training features |
| 4: Short answers | Two handwritten explanations with justification | GPS-to-grid coordinate transformation and a stable solution to USB serial device conflicts |
| Bonus: Pathfinding | Fixed `astar.py`, map exports, handwritten A*/Dijkstra comparison | Five verified fixes in supplied code, untouched `run.py`, both algorithms exercised on all three supplied maps |

Python 3, OpenCV, and NumPy are the stated technology stack. The document does not require importing every library in every task. AI assistance is allowed, but the candidate must explain the algorithms and design decisions in the interview.

The bonus is conditional: it need not be attempted if it was not assigned. Tasks 1, 3, and 4 require handwritten submissions; a Markdown explanation alone does not satisfy those submission formats.

## 3. Task 1: Route planning

Source: lines 31-52.

There are three legs: Start to WP1, WP1 to WP2, and WP2 to WP3. For handwritten work, convert all latitude/longitude angles to radians before applying trigonometric formulas and state the Earth radius and units used.

For each leg, use the Haversine intermediate value:

`a = sin²(Δφ/2) + cos(φ1) cos(φ2) sin²(Δλ/2)`

Then calculate `d = 2R atan2(√a, √(1-a))`. Determine the initial bearing with:

`θ = atan2(sin(Δλ) cos(φ2), cos(φ1) sin(φ2) - sin(φ1) cos(φ2) cos(Δλ))`

Convert the bearing to degrees and normalize it to `[0, 360)`, with north at zero and increasing angles clockwise. These are calculator instructions, not executed calculations.

The command sequence must alternate relative turns and drives. A bearing is an absolute direction; it is not automatically the next turn angle. Start with heading north and compare each leg's bearing with the heading reached on the previous leg. Wrap the difference around the compass boundary; choose a turn direction and angle consistently. Shortest turns are a sensible convention, although the document does not explicitly require them.

Coordinate-only sanity checks:

- Start to WP1 heads northeast: both latitude and longitude increase.
- WP1 to WP2 heads northwest: latitude increases and longitude decreases.
- WP2 to WP3 heads northeast again.
- The final leg is much shorter than the preceding legs, so a fixed GPS error has a greater relative effect on its bearing and distance.

For the ±3 m reflection, distinguish the nominal coordinate-derived command list from what uncertain position estimates imply in execution. The specified coordinates do not change, but calculated corrections, stopping decisions, and estimated turn directions become uncertain. Do not casually assert that every leg has only ±3 m distance error: if both endpoints have independent errors bounded within 3 m circles, their relative displacement error can reach 6 m. If only the rover fix is uncertain and the target is exact, that bound differs. The document does not define whether ±3 m means a radial bound, per-axis bound, or statistical accuracy, so state the interpretation.

## 4. Task 2: Status-light behavior

Source: lines 56-90. This is the main required programming task.

### Exact output contract

Invocation: `python light.py mission_log_1.csv targets.csv`.

Output records have the form `time_s,light`, where the light is lowercase `red`, `blue`, or `green`. Do not add an output header, explanatory messages, spaces, or ANSI colors. Diagnostics should go to standard error. Treat the input header as schema rather than a telemetry sample.

Emit a record for each telemetry sample, and do not synthesize records for absent timestamps. The phrase 'one line for every line of the log' becomes ambiguous for corrupt records with no usable timestamp; this needs an explicit policy rather than silently pretending it has a defined answer.

The printed value `green` represents the flashing indicator for the entire green interval. The script is not asked to simulate individual flashes.

### Arrival and speed

Arrival requires all of the following together:

1. Current mode is AUTO.
2. Haversine distance to the current ordered target is at most 3.0 m.
3. Estimated speed is strictly less than 0.5 m/s.

Exactly 3.0 m passes the proximity test. Exactly 0.5 m/s fails the speed test. Being stopped in MANUAL or moving quickly through a target does not trigger arrival. Being near a later target does not permit skipping an earlier one.

For successive valid observations with increasing timestamps, displacement divided by actual elapsed time gives the interval-average speed. Assuming that every pair is one second apart fails when samples are missing. The first valid observation has no measured speed; treating it as stopped can create a false arrival.

An important limitation: a low interval-average speed across a long gap does not prove the rover was stopped in the last second. The document does not specify a maximum acceptable gap or how to estimate instantaneous speed. The supplied data and evaluator expectations are needed to resolve that policy.

### Green interval and target advancement

Use elapsed timestamps to time the green state, rather than counting five input rows. A natural interpretation of an arrival at `t0` is the half-open interval `[t0, t0 + 5)`. With one-second records, arrival at 10 produces green at 10, 11, 12, 13, and 14, and the interval expires at 15. This example explains the contract; it is not output from a supplied mission log.

If 12 and 13 are missing, print no lines for them and still expire at 15. Do not stretch the interval until five green records have been emitted. Do not restart the timer whenever another qualifying sample appears.

The wording that green 'remains active for 5 seconds' supports keeping green even if the rover changes mode or leaves the radius during that interval. After it expires, use the current mode for the baseline color and advance exactly once to the next target. After the final target's green interval, continue normal mode indication without indexing beyond the target list or retriggering that target.

The document leaves one transition detail open: at the expiration sample, must baseline mode be printed once, or can an immediately qualifying next target start a new green interval on that same sample? State a convention and check it against provided examples if they become available.

### Robustness policies requiring attention

| Input condition | Risk | Defensible policy to document |
| --- | --- | --- |
| Missing coordinates or non-finite values | Invalid distance or false stop | Do not authorize a new arrival; retain a valid ongoing green interval |
| Out-of-range latitude/longitude | Nonsensical position | Reject the position as invalid |
| Duplicate timestamp | Division by zero or repeated transition | Do not derive speed from zero elapsed time; specify which observation can update state |
| Decreasing timestamp | Negative speed or timer moving backward | Define handling explicitly; avoid silently sorting and changing input order |
| Large timestamp gap | Average speed mistaken for current stopped state | Divide by actual elapsed time and document whether the gap disqualifies arrival |
| First observation | Assumed zero speed | Mark speed unknown until a suitable observation pair exists |
| GPS jump | Distorted speed and subsequent estimates | Validate measurements; avoid inventing an undocumented physical speed limit |
| Unknown mode | Incorrect fallback light | No new arrival; choose and document a deterministic output policy |
| Empty target list | Index error | Continue baseline AUTO/MANUAL display |
| Invalid target record | Wrong waypoint order after skipping it | Diagnose clearly; do not silently skip mission objectives |
| Unusable timestamp or structurally broken CSV | Output contract cannot be met literally | Diagnose the issue and document whether to reject the file or omit the unusable record |

These are recommendations for unresolved inputs, not additional rules stated in the recruitment document. 'Handle gracefully' does not uniquely determine the correct output for every malformed row. In particular, the document gives no correct red/blue choice for an unknown mode.

### Meaningful output checks once inputs exist

- Verify baseline AUTO red and MANUAL blue.
- Check the inclusive 3.0 m boundary and exclusive 0.5 m/s boundary.
- Confirm that proximity and low speed in MANUAL do not trigger arrival.
- Confirm arrival only at the next ordered target.
- Check all five green timestamps and exact expiration, including missing seconds.
- Check that repeated arrival-like samples do not extend green.
- Check a mode change during green, final-target completion, and an empty target list.
- Check missing positions, non-finite numbers, duplicate/backward timestamps, and first-row speed.
- Confirm that both provided mission logs run through the same unchanged program and that standard output contains only result records.

No such tests have been run: neither an implementation nor the required CSV files is present.

## 5. Task 3: Learning, bias, and overfitting

Source: lines 94-150.

The required procedure matters: write a rule, freeze it, classify all four test photos, then compare with the labels. Changing the initial rule after reading the labels would invalidate the demonstration.

The supplied ground truth is A=YES, B=YES, C=NO, D=YES. These are reference labels, not predictions from a candidate's rule. The score cannot be determined without that rule.

The reflection prompts assume a rule that fails on A, B, and D, but those failures are not inevitable. A less restrictive rule may recognize A or B. Reflections should explain actual rule behavior honestly. If an initial rule required a blue shirt, black upright FOLLOW text, and bright conditions, it would plausibly reject all four and score only C correctly; that is a conditional example, not the required result.

Separate the failure mechanisms:

- A exposes reliance on shirt or ink color instead of sign meaning.
- B tests orientation and lighting generalization. An explicit upright-text condition fails here.
- C is a negative example that checks whether the rule reads the sign rather than equating blue clothing with FOLLOW.
- D adds a sign design absent from training. Clothing invariance alone cannot teach that a forward arrow means FOLLOW; that requires an explicit team convention or labeled examples.

All six training examples are positive. They do not establish a reliable boundary between FOLLOW and non-FOLLOW signs. A stronger dataset needs negative examples such as STOP and unrelated symbols as well as varied positive examples. Also, the training set includes harsh shadow in photo 2, so it is inaccurate to say every training photo has identical lighting.

For the three requested additions, justify a deliberate combination of white EVA suit, changed ink, upside-down orientation/cloudy conditions, and the authorized arrow design. Explain the tradeoff if three images cannot cover all variations. Discuss negative examples in the broader training-set answer without pretending all possible weaknesses can be fixed by only three photographs.

## 6. Task 4: Localization and USB serial conflicts

Source: lines 154-160.

### GPS to the rotated grid

Convert the rover's latitude/longitude into a local metric displacement from the known grid origin, using a local east/north frame or a suitable projected coordinate system. Rotate that displacement into the grid axes using the grid's measured orientation. If the answer requires a cell rather than a metric coordinate, also use known cell dimensions and boundary conventions.

The key distinction is that rover position and rover heading are different quantities. A GPS position can be expressed in grid coordinates without knowing where the rover faces. The grid axes' orientation relative to geographic directions must be known, however. The statement that the grid is 'a few degrees off' does not provide its numerical rotation. A surveyed grid edge or second known point along an axis can establish it. The origin alone cannot.

The term '2×2 grid' does not establish physical cell dimensions. Exact cell identification requires those dimensions. GPS uncertainty also prevents a literal guarantee of exact position, especially near a cell boundary. These limitations should be acknowledged briefly in the handwritten justification.

### GPS and IMU sharing serial devices

The leading explanation is a copied device configuration causing both nodes to open the same serial device, combined with discovery-order names such as `/dev/ttyUSB0` and `/dev/ttyUSB1` changing across boots. A second process can contend for data or change the port configuration. This is a diagnosis suggested by the scenario, not an observed fault on actual hardware.

Check both configured port paths, identify which physical device each resolves to, and check which processes have the ports open. Bind each node to its own persistent identity. Use unique `/dev/serial/by-id/` links where the devices provide distinct identities, or custom udev symlinks matched to stable attributes. If adapters have missing or duplicated identities, use a fixed USB-port topology with `/dev/serial/by-path/` or distinguishable adapters. Merely changing one copied setting to `ttyUSB1` does not address reboot reordering.

Keep baud rate, protocol, and permissions correct for each sensor; prevent two processes from claiming the same physical endpoint. Exclusive-open support can help expose accidental contention. Verify with both devices connected, different startup orders, reboots, and reconnects.

Primary reference: the [udev manual](https://www.freedesktop.org/software/systemd/man/260/udev.html) explains discovery-order naming and property-based symlinks. The [systemd serial rules](https://raw.githubusercontent.com/systemd/systemd/main/rules.d/60-serial.rules) show how serial `by-id` and `by-path` links are constructed and why identity information matters.

## 7. Bonus: A* and Dijkstra

Source: lines 164-183.

The five bugs must be established by inspecting the supplied `astar.py`. It would be speculative to name five generic A* defects and claim they are the assigned bugs. Preserve `run.py` exactly and preserve the callable interface it expects.

For the same graph and nonnegative movement costs, Dijkstra uses priority `g`; A* uses `g + h`. Setting the heuristic to zero gives Dijkstra behavior. A* optimality depends on the heuristic and search implementation: a consistent heuristic supports the usual closed-set approach, while an admissible but inconsistent heuristic can require reopening nodes.

Choose a heuristic consistent with the actual allowed moves and their costs. Manhattan distance is suitable for four-connected grids with unit orthogonal moves, but cannot be assumed suitable for a grid that permits cheaper diagonal movement. Establish obstacle semantics, diagonal corner rules, and movement costs from the supplied harness and maps.

Run both algorithms on all three maps and compare path validity, path cost, number of expanded nodes, runtime, and memory if available. Use the same endpoints, graph, and cost model. Tied optimal routes may differ while both remain correct. A* is often more directed with an informative heuristic, but it is not guaranteed to have lower measured runtime on every map; heuristic overhead and tie-breaking matter.

Inspect exported images for correct endpoints, obstacle avoidance, connected steps, permitted movement, and correspondence to the returned path. Visual appearance alone does not establish optimality. An independently calculated shortest-path cost on the same graph is stronger evidence.

The bonus is labeled `(task2/)` even though Task 2 already refers to telemetry files. Treat that as a packaging ambiguity until the actual starter folders are available, rather than assuming a directory layout.

## 8. Current conclusion

The assignment is sufficiently clear to plan the deliverables and core algorithms. Its most consequential ambiguities are malformed-log behavior, speed across telemetry gaps, the exact target-expiration transition, and the grid's missing orientation and scale information.

Actual output validation requires the telemetry CSVs, a `light.py` solution, and any handwritten work being reviewed. Bonus validation additionally requires the original `astar.py`, unchanged `run.py`, all three maps, and the resulting exports. Those artifacts were absent at review time. No source implementation or repository configuration was changed.

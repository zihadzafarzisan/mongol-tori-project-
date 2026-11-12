# 

# **Rover Autonomy Recruitment Tasks**

Our team builds an autonomous rover  designed to navigate rough terrain. Complete the following  recruitment tasks to help the rover reach its target objectives.

**General Requirements**

* **Technology Stack:** Python 3, OpenCV, NumPy.

*Note on AI Tools:* You are permitted to use AI assistance. However, during the follow-up interview, you will be expected to thoroughly explain your solutions, underlying algorithms, and design choices.

***Don’t worry if you can’t complete all the tasks. It’s completely okay to get stuck, we’d simply love to see you give it a try. So just do your best and if anything is unclear or you need help, feel free to reach out to us. Good luck\!\!\!***

*For any queries contact either,*

***Arpita Saha Riya***  
***AI & Autonomous Sub-Team Lead,***  
***BRACU Mongol-Tori***  
arpita.saha.riya@g.bracu.ac.bd

***Md. Moshiur Rahman***  
***AI & Autonomous Sub-Team Lead,***  
***BRACU Mongol-Tori***  
md.moshiur.rahman2@g.bracu.ac.bd

**MT12 Recruitment Server: [https\://discord.gg/VsPUSDac4](https://discord.gg/VsPUSDac4)**

---

# **Task 1: Plan the Route**

**Constraint: Pen, paper, and calculator only. No code.**

The rover starts at position **Start** facing **North**. It must navigate sequentially to waypoints **WP1**, **WP2**, and **WP3**.

| Waypoint | Latitude (°) | Longitude (°) |
| :---: | :---: | :---: |
| Start | 38.418012 | \-110.777203 |
| WP1 | 38.418603 | \-110.775784 |
| WP2 | 38.420167 | \-110.776319 |
| WP3 | 38.420289 | \-110.776246 |

The navigation system accepts two command types: **turn** (relative angle in degrees, left/right) and **drive** (distance in meters).

**Instructions & Deliverables**

* Calculate leg **distances** using the **Haversine formula** and determine bearings (0° \= North, measured clockwise).  
* Produce the complete command sequence (turn angle and drive distance) from Start to WP3.  
* Provide a short analysis: What is the impact on your command list if GPS accuracy drops by ±3 m?

**Submission Format:** Photos of handwritten step-by-step calculations for each leg.

---

# **Task 2: Status Light Telemetry**

During competition runs, a rear-mounted LED indicator signals the rover's operational status:

| Light Signal | System State / Meaning |
| :---: | ----- |
| Solid Red | Autonomous driving mode (AUTO) |
| Solid Blue | Manual operator control mode (MANUAL) |
| Flashing Green | Successful arrival at target waypoint |

**Objective:** Develop a parser script to process mission logs and output per-second status light states.

**Project Files** `(task2/) [Drive_Link]`

* `mission_log_1.csv` & `mission_log_2.csv`: Telemetry logs formatted as `time_s, mode, lat, lon`.  
* `targets.csv`: Ordered target waypoint coordinates.

**Arrival Logic & Conditions**

The indicator switches to **Flashing Green** when all three criteria are met simultaneously:

* **Mode:** Rover is operating in AUTO mode.  
* **Proximity:** Distance to target is **≤ 3.0 meters** (via Haversine formula).  
* **Velocity:** Speed is **\< 0.5 m/s** (stopped). Speed means how many metres the rover moves in one second.

**Target Transitions:** Flashing green remains active for **5 seconds** upon arrival, after which the state resets to standard AUTO/MANUAL indication as the rover advances to the next waypoint. After the final target, standard state display resumes.

*Data Robustness:* Logs contain real-world telemetry anomalies. Code must handle edge cases gracefully without crashing.

**Deliverables & Requirements**

* **Submit your code.**  
* **Single script:** One program that works on both log files and on unseen evaluation logs. Do not change it between files.  
* **How to run:** Your script is called light.py. It is started like this: python light.py mission\_log\_1.csv targets.csv  
* **What it prints:** One line for every line of the log, in the form time\_s,light. The light is red, blue or green. Print green for all 5 seconds of the green period. Example: 0,blue then 1,red. If a second is missing from the log, print nothing for it.

---

**Task 3: The Overfitting Astronaut (Learning, Bias, and Overfitting)**

**Concept Focus:** Supervised learning, overfitting, data bias, generalization.  
**Materials:** Pen, paper, the image descriptions below.

**The Scenario:**

Your team is training a machine‑learning model to recognise the astronaut’s **“Follow”** sign. Imagine you are the model. You are given **6** training photos. Your job is to write a simple rule (like a checklist) that will let you decide ”YES, this is a Follow sign” or “NO, it is not” for any new photo.

**Training photos (all labelled “Follow sign”):**

1\. Astronaut in a blue shirt, holding a white sign with the word “FOLLOW” in black marker, standing in bright sunlight, desert background.  
2\. Same blue shirt, same sign, but photo taken in harsh midday shadow.  
3\. Blue shirt, sign held high above the head, clear sky background.  
4\. Blue shirt, sign held at chest level, rocky ground background.  
5\. Blue shirt, sign slightly tilted, bright sun.  
6\. Blue shirt, sign straight, bright sun.

**Your Task:**

**Step 1 – Write your rule.**  
On paper, write a short set of conditions (e.g., “If the sign has the word FOLLOW in black, and the person wears a blue shirt, and the background is bright, then YES”). This is your model.

**Step 2 – Test your rule on new photos.**  
Now apply your rule to these **4** test photos (do not change the rule):

· A: Astronaut in a **white** EVA suit, holding a sign that says **“FOLLOW”** in red marker, bright sun.  
· B: Astronaut in a **blue** shirt, holding a sign that says **“FOLLOW”** but it’s upside down, cloudy day.  
· C: Astronaut in a **blue** shirt, holding a sign with the word **“STOP”** in black, bright sun.  
· D: Astronaut in a **white** EVA suit, holding a sign with a hand‑drawn arrow pointing forward, bright sun.

Write down **YES** or **NO** for each test photo.

**Step 3 – Compare with the truth.**

· A is a Follow sign (different colour, different suit).  
· B is a Follow sign (upside down is still the word).  
· C is NOT a Follow sign.  
· D is a Follow sign (your team chose an arrow as the sign – see rule 1.e.vi: “Sign may have any image chosen by the team”).

**Reflection Questions (write short answers)**

1\. How many test photos did your rule get right? Where did it fail?  
2\. Why did your rule fail on photo **A** and **D**? What did your rule unintentionally focus on that wasn’t the actual sign? (This is bias – your training data made you think “blue shirt \= follow”.)  
3\. Why did your rule fail on photo **B**? (Your rule was too specific to the exact orientation in training – this is overfitting: memorising irrelevant details instead of the general concept.)  
4\. If you could collect **3** new training photos to fix your rule, what would you change about the photos? (More diverse lighting? Different suits? Different sign designs?)  
5\. In **URC,** the astronaut may wear a **white** EVA suit (1.e.iv). If you trained only on **blue**‑shirt photos, what would happen on competition day? How would you design a better training set?

Submit handwritten answers.

**What You Just Learned (Read after answering)**

**· Supervised learning:** you learned a rule from labelled examples.  
**· Overfitting:** your rule memorised irrelevant details (shirt colour, exact orientation) and failed on slightly different inputs.  
· **Data bias:** your training set was not representative of the real world (only blue shirts, only bright sun).  
**· Generalization:** a good model focuses on the essential features (the sign itself) and ignores irrelevant ones.  
**· Fix:** collect more diverse training data, or simplify your rule to focus on what truly defines a “Follow” sign.

---

# **Task 4: Short Question Answers:**

1. Suppose the Autonomous Mission requires you to know exactly where a Mars rover is on a **2×2** grid. The rover’s GPS speaks only latitude and longitude. You’re given the GPS coordinates of the grid’s origin, and the organizers mention that the grid’s edges sit a few degrees off from the way the compass points. The rover doesn’t know which way it’s facing. Describe the approach you would use to work out the **rover’s position in grid coordinates**. You don’t need to show any calculations, just describe your approach and justify your answer.

2. You’re building a rover localization system with a GPS module and an IMU, both plugged into the rover’s computer over **USB**. You launch the GPS node and position data comes through fine. Then you launch the IMU node, which a teammate set up by copying the GPS node’s config and changing what needed changing. The moment the IMU starts, the GPS goes silent. Both sensors work perfectly when tested alone, and oddly, after a **reboot** the problem sometimes flips and the IMU is the one that fails. What could be going on, and how would you fix it so it never happens again? Justify your answer. (**Hint:** Google “Linux USB serial port conflict”)

Submit handwritten answers.

---

# **Bonus Task: Fix the Path Finder**

**It is not mandatory for you to attempt this task if it was not assigned to you.**

The rover uses an **A\* pathfinding** algorithm to determine optimal routes across a grid map from start (green) to goal (red). The current implementation contains errors that prevent proper execution.

**Project Structure** `(task2/) [File_Link]`

* `astar.py`: Core pathfinding module. Contains **5 bugs** to identify and resolve.  
* `run.py`: Test harness that loads maps, executes pathfinding, and exports visual results. **Do not modify.**  
* `maps/`: Directory containing 3 test maps.

Execute the test suite using: `python run.py`

**Instructions & Deliverables**

1. Debug and fix all 5 issues in `astar.py`.  
2. Modify the implementation to run as **Dijkstra's Algorithm**, execute on all 3 maps, and evaluate differences against A\*.

**Submission Items:** Fixed `astar.py` file, resulting map image exports, and a handwritten comparison analysis (A\* vs Dijkstra).

---


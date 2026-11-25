# AI Agent Tournament

Two agents for IE University's AI: Reasoning & Problem Solving tournament. The Road Trip agent finds short simple cycles through required European cities. The Chess agent chooses legal moves under a cumulative clock.

## Members and responsibilities

- Team name and roster are pending confirmation. The project brief lists two contributors and the handbook specifies four to six members.
- This contribution covers Road Trip, Chess, and the initial repository setup.
- Rodrigo owns Battleship and Catan. See the [task division and checklist](docs/task_division.md).

## Algorithms implemented

| Challenge | Algorithms | Location |
| --- | --- | --- |
| Road Trip | BFS insertion, UCS, A*, first-improvement hill climbing, random restarts | `roadtrip_agent.py` |
| Chess | Linear evaluation, depth-limited minimax, alpha-beta pruning, move ordering | `chess_agent.py` |
| Battleship | Pending Rodrigo's contribution | |
| Catan | Pending Rodrigo's contribution | |

## Setup and reproducibility

Get the official ZIP and notebook from the course and keep them outside version control. With Python 3.10 or newer, run the following from the project root on Windows. Use a fresh virtual environment if the directory already contains one from a different Python version.

```powershell
Expand-Archive -LiteralPath 'C:\path\to\ai_agent_tournament.zip' -DestinationPath .official
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .official\requirements.txt
$env:PYTHONPATH = (Resolve-Path .official).Path
.\.venv\Scripts\python.exe experiments\verify_algorithms.py
.\.venv\Scripts\python.exe experiments\run_experiments.py road_trip
.\.venv\Scripts\python.exe experiments\run_experiments.py chess
```

On Colab, run the official notebook's setup cell and upload the two agent files to `/content`. Run this in a new cell:

```python
from tournament import check_requirements, run_game

for game, file in [("road_trip", "roadtrip_agent.py"), ("chess", "chess_agent.py")]:
    path = f"/content/{file}"
    check_requirements(path, games=[game])
    for opponent in ("demo_a", "demo_b"):
        result = run_game(game, path, opponent=opponent, seed=3101, live=False)
        print(result["incidents"])
```

The experiment runner accepts `--count`, `--seed`, and `--output`. Side A is the improved agent. Side B is the corresponding baseline. The runner builds the Road Trip baseline as a single judge-compatible file using the shared route constructor and the first-feasible entry point in `experiments/roadtrip_baseline.py`. Chess challenges play both colours. The seed reproduces the setup, while machine speed can affect the depth completed and the number of Road Trip restarts. The recorded runs used the local Windows judge with Python 3.14 and `chess` 1.11.2. Raw results are in [experiments/results](experiments/results).

## Training

Road Trip and Chess use hand-written algorithms and weights. They use no learned parameters.

## Tests

The unmodified official judge passed **7/7 checks** for these two agents. The six required functions produce seven check rows. The original templates also ran a practice challenge each at seed 2026 without protocol incidents. Both lost to `demo_a`.

| Official check | Result |
| --- | --- |
| UCS | PASS · optimal on 8 pairs, 384 nodes expanded |
| A* | PASS · optimal on 8 pairs, 176 nodes expanded |
| A* expansion comparison | PASS · 176 vs 384 |
| Local search | PASS · 16,810 km to 7,480 km on the distance-table exercise |
| Chess evaluation | PASS · ranks material from White's perspective |
| Chess pruning | PASS · same minimax values with fewer nodes on 4 positions |
| Chess depth limit | PASS · 32 nodes at depth 1 and 127 at depth 2 on the designated position |

**Road Trip.** Fifty paired draws at seeds 3101–3150 with the official 5-second limit. The improved agent won all 50.

| Metric | First feasible baseline | Improved |
| --- | ---: | ---: |
| Valid route rate | 50/50 | 50/50 |
| Mean distance | 20,036 km | 13,942 km |
| Median judge receipt time for first valid route | 0.01 s | 0.01 s |
| Median judge receipt time for best route | 0.01 s | 2.04 s |
| Invalid submissions or technical incidents | 0 | 0 |

Mean paired distance reduction was **30.2%**, computed as the mean of `(baseline − improved) / baseline` for each instance. The improved agent also won against both bundled demos without incidents. The judge receipt times above exclude startup. Total challenge duration, including setup and cleanup, averaged 10.76 seconds locally.

**Chess.** Twenty-five paired challenges at seeds 3101–3125, with a game as each colour and five seconds per player per game under the official judge.

| Metric | One-ply material baseline | Improved |
| --- | ---: | ---: |
| Wins / draws / losses | 0 / 35 / 15 | 15 / 35 / 0 |
| Win rate | 0% | 30% |
| Mean judge clock used per game, excluding overall-limit adjudications | 1.23 s | 1.75 s |
| Mean nodes in completed iterations per logged decision | 17.36 | 102.36 |
| Illegal moves, player timeouts, or other incidents in the paired sample | 0 | 0 |

The improved agent won 11 games as White and four as Black. It completed depth two on 903 of 1,432 logged decisions and depth three on eight. Logged node counts include every completed iteration for a decision and omit unfinished iterations and unlogged forced or reserve-fallback turns. The aggregate retains two draws at the overall challenge limit in seed 3111, including one game that stopped before a move. Against the bundled demos, the improved agent won 1½–½ against `demo_b` and drew 1–1 against `demo_a`, with one player-clock timeout in the latter challenge. Separately replaying both timing-affected challenges with the same settings gave two 2–0 wins without incidents. The [replay record](experiments/results/chess_replays.json) uses seed 3111 against the material baseline and seed 3126 against `demo_a`.

In the separate depth-two comparison, plain minimax visited 3,858 positions and alpha-beta with move ordering visited 486 across the four official positions, an **87.4% reduction** with identical values. A node count includes the root and every visited descendant. The internal checks also covered 12 additional seeded Chess positions, checkmate for either colour, stalemate, repetition, insufficient material, the fifty-move ending, clock fallback, and board restoration after interruption. Road Trip's edge checks verified the Haversine bound on all 262 official edges and validated every submitted route on the three official small instances.

## Dependencies and known limitations

Road Trip uses the Python standard library. Chess also uses the permitted `chess` package for rule handling, board representation and legal moves. The experiment scripts require the official judge and its dependencies.

## Technical explanation

### European Road Trip

#### Problem formulation

The agent receives the full weighted road graph, required cities, start, and deadline. A shortest-path state is a city in a graph with a fixed set of blocked cities. For the full challenge, the partial cycle also records which cities are used and which required stops remain. A road is an action and its weight is its driving distance. The objective is a minimum-kilometre simple cycle through every required city. Madrid appears at the two endpoints. See Session 3, slides 8–17 and 20–21.

#### Algorithms

`road_graph` creates the adjacency map. `ucs` calls `shortest_path` with zero heuristic. Its priority is the accrued road cost `g(n)`. `astar` uses `f(n) = g(n) + h(n)`, where `h(n)` is the Haversine distance to the destination. Both update the reached cost and parent only when they find a cheaper path, discard superseded queue entries, and test for the goal on removal from the frontier. Positive road costs give UCS an optimal shortest path. The Haversine triangle inequality and the fact that each road is at least as long as its straight-line distance give `h(u) ≤ cost(u,v) + h(v)`. This gives consistency and, by summing the inequality along a path to the goal, admissibility. See Session 4, slides 11–16 and 21–27, and Session 5, slides 9–16 and 18.

`build_route` inserts cities by replacing an edge with two BFS paths. The first path blocks existing cycle vertices except its starting point. The second also blocks the first path's vertices, with its specified endpoint allowed. The resulting cycle uses real roads and has unique interior vertices. The baseline submits the first valid cycle. The improved agent submits that cycle immediately and uses `improve_route` to find shorter segments between consecutive required stops, with all retained vertices blocked. A strict decrease in road kilometres is the acceptance rule. It restarts with a different insertion order when it has finished improving a cycle. The insertion and shortcut rules adapt BFS and hill climbing to the tournament's simple-cycle constraint. The required `local_search` function uses a segment-reversal neighbourhood (2-opt) on the complete distance table, as allowed by the handbook. It keeps the first city fixed and returns its best order at a local optimum or the deadline. See Session 6, slides 5–11, for hill climbing and random restarts.

#### Baseline against improved version

Both versions start from an identical city-dependent random sequence. The race compares stopping at the first valid cycle with using the rest of the time to improve the cycle through shortcuts and restarts. See the measured results above.

#### Time and memory

`solve` reserves 10% of the supplied clock for overhead. It checks time between insertions and local moves and sends every new best route found within the internal deadline. Each search keeps an adjacency map, parent and cost maps, and a frontier. The agent retains only the current candidate and best submitted cost between restarts.

#### Limits

The insertion process is greedy and can reach a dead end. The shortcut move preserves the order of required stops on its current cycle, so it can get stuck even when a different order would help. Random restarts give other orders a chance but cannot certify optimality or guarantee a route in time. A natural extension would be to try a few more insertion choices for cities with fewer connections.

### Chess

#### Problem formulation

Chess is a deterministic, fully observable, two-player zero-sum game. A position and its history define the state. Edges are legal moves, and the player to move determines whether a node is MAX or MIN. Scores are from White's perspective, so White maximizes and Black minimizes. The agent receives the FEN, legal UCI moves, history, and remaining clock. See Session 2, slides 16–17, and Session 14, slides 9–14 and 22.

#### Algorithms

`evaluate` uses terminal utility before the heuristic. A White win is +100,000, a Black win is −100,000, and a draw is zero. At a cutoff, `position_score` computes the White-minus-Black differences for material, center occupancy by pawns and minor pieces, and minor-piece development. The piece weights for pawn, knight, bishop, rook, and queen are 100, 320, 330, 500, and 900. Center occupancy is worth 18 per piece and a knight or bishop off its own back rank is worth 12. These small bonuses break many material ties. See Session 15, slides 6–14.

`minimax` and `alphabeta` share recursive `search`. It pushes a move, evaluates the resulting subtree, and pops the move in a `finally` block. MAX raises alpha and MIN lowers beta. Once alpha is at least beta, the remaining children cannot improve the ancestor's choice. Ordering promotions and valuable captures early, and repeating the previous depth's best move first at the root, can tighten bounds sooner. The root value matches plain minimax at the same depth with the same evaluation. See Session 14, slides 13–19 and 29–41.

#### Baseline against improved version

The baseline searches one ply using material and terminal utility. The improved agent adds positional features and searches one through four plies with alpha-beta as time permits. The head-to-head comparison measures the whole strategy. The fixed-depth comparison holds the evaluation and depth constant and measures the workload with and without pruning and its move order.

#### Time and memory

`act` saves a judge-provided legal move before searching and replaces it only after a full depth finishes. The handbook lists iterative deepening as an optional extension. Here it is bounded to depths one through four. The search budget is at most 21 ms for the first 40 plies and 11 ms thereafter, capped at one fortieth of the clock above a 1.8-second reserve. On a forced move or at or below the reserve, the agent returns the legal fallback immediately, before rebuilding the board or searching. Otherwise, it reconstructs history using the public moves to account for repetition. The recursive search holds only the current stack and its move lists. The judge charges the full request and response time, including communication. In the original seed 3126 loss on time, the game reached 196 plies and the judge reported no answer within a budget rounded to 0.00 s. A legal fallback bounds agent work, while response delivery still depends on the judge and host.

#### Limits

A fixed cutoff can miss tactics beyond the last explored ply. The evaluation has limited knowledge of king safety and does not explicitly guide endgame conversion. On a slower machine, fewer depths can finish and judge communication still consumes clock time. A later version could test a small king-safety feature and recalibrate the budget on Colab.

### Battleship

Rodrigo to add problem formulation, algorithms, experiments, resource limits, and technical explanation.

### Catan

Rodrigo to add the heuristic baseline, learned or estimated value, experiments, resource limits, and technical explanation.

## Use of generative AI

OpenAI Codex helped interpret the supplied materials, implement and verify both agents, run and summarize experiments, and draft the README and study and presentation notes. The team should confirm the course-specific AI policy and review the implementation for the oral exam.

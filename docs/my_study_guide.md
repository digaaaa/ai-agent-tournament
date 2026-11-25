# Oral exam study guide

Start each answer with the problem, then describe the state representation, the rule the algorithm uses to choose, and the limitation. Use the recorded results to explain the trade-offs.

## Road Trip

### What each function does

| Function | Inputs, method and result |
| --- | --- |
| `road_graph(graph)` | Converts the judge's city and road dictionaries into a mapping from each city to its neighbours and edge costs. For a bidirectional road it adds both directions. Session 3, slides 11–16. |
| `reconstruct(parents, goal)` | Walks from the goal back to the initial city via parent links, reverses the list, and returns every city along the path. Session 4, slides 8–13. |
| `shortest_path(neighbours, start, goal, heuristic, blocked)` | Searches a fixed graph or subgraph with a priority queue. Tracks the cheapest discovered cost per city and its parent. Returns the path, kilometres, and number of expanded nodes. A stale queue record is skipped when it is more expensive than the current reached cost. The goal is returned without expanding its successors. Sessions 4–5. |
| `ucs(graph, start, goal)` | Converts the graph and calls the shared search with zero heuristic, so the smallest accumulated road cost is expanded first. Session 4, slides 21–27. |
| `straight_line_km(a, b)` and `astar(graph, start, goal)` | Use city latitude and longitude to compute Haversine distance in kilometres. A* searches by accrued cost plus that estimate. Session 5, slides 9–16. The Colab export implements the same geographic idea. |
| `route_cost(route, distance)` | Adds the costs between consecutive entries. The caller supplies the repeated first city when scoring a closed order. |
| `local_search(tour, distance, time_limit_s)` | Keeps the first city fixed and tries reversing segments of the current order, accepting the first strict decrease in closed length. Stops at a local optimum under this move or when time runs out. Returns a list of the same cities. Session 6, slides 5–11. |
| `path_avoiding(neighbours, start, goal, blocked)` | BFS in the road graph with used cities blocked, except the start and target as endpoints. Returns a path with the fewest edges or an empty list. Session 4, slides 16–20. |
| `build_route(start, required, neighbours, deadline, rng)` | Shuffles the remaining city order and existing edges. To insert a city, it replaces an edge with two BFS detours that avoid retained vertices and each other. Returns a full feasible cycle or abandons the attempt. |
| `improve_route(route, required, neighbours, deadline, on_improvement)` | Takes a feasible cycle. It tries replacing a segment between consecutive required stops with a cheaper UCS path. The vertices retained outside the segment are blocked. It accepts the first improvement and repeats the process, notifying the caller about each improvement. |
| `solve(problem, submit)` | Builds and immediately submits a valid cycle when one is found. It tries shortcuts and starts new randomized constructions until its deadline. Its closure calls `submit` only for a strictly better full cycle. It returns no value. |

### Trace a frontier

Suppose S connects to A for 2 and B for 4. A reaches G for 7, B reaches G for 2. The two route costs are 9 and 6. UCS first takes A because its `g=2` is lowest. It adds G with `g=9` but keeps searching. B then offers G at `g=6`. Only when G leaves the frontier with cost 6 does UCS return it. If the A* estimates for A and B are 6 and 2, their priorities are 8 and 6. A* takes B first and can reach the same optimal goal without expanding A.

### Trace a cycle improvement

Imagine `S-A-X-B-C-S`, where A, B, and C are required, X is optional, and A–X–B costs 14. A different path `A-Y-B` costs 10 and Y is unused on the remaining cycle. The shortcut replaces the segment and saves 4. A tempting path through C is blocked, because C already appears after B. If every eligible shortcut fails, restart from a different randomized city order. The accepted best submission stays valid while another attempt runs.

### Likely Road Trip questions

**What are UCS and A*?** UCS expands the smallest total cost so far, `g(n)`. A* expands the smallest estimate of total solution cost, `f(n) = g(n) + h(n)`. Here `h(n)` is straight-line kilometres from the node's city to the destination. A* reduces to UCS at `h=0`.

**Why is Haversine admissible and consistent?** The triangle inequality gives `h(u) ≤ straight_line(u,v) + h(v)`, and each road costs at least that straight-line distance. This proves consistency across each edge. Applying it along a complete path ending at a goal with `h=0` proves that `h(u)` is at most the actual remaining cost, including the cheapest one.

**Why is the first generated goal insufficient?** A cheaper path to that goal can still be on the frontier. The priority queue must select the goal after comparing it with the remaining paths.

**Why use BFS for insertion?** It quickly supplies feasible paths and already knows how to skip blocked cities. BFS minimizes the number of roads, while UCS in the improvement stage minimizes the weighted road cost.

**What is hill climbing?** Keep a current candidate, generate nearby candidates, and move to a better neighbour. Here “better” means shorter. The required function reverses a segment in a complete distance table. In the race the neighbourhood is legal weighted shortcuts in the original road graph.

**Why use two different neighbourhoods?** A tour in `local_search` is a visiting order with a supplied distance for every pair. The race needs a complete simple cycle along actual roads. Reversing a visiting order and independently joining stops could reuse an intermediate city.

**How do you escape a local optimum?** In the race, try a new random construction after reaching a local optimum. Within the required `local_search` routine, return the best order found when no strict improvement is available.

**Why is global route optimization difficult?** Every choice of stop order and intermediate road can remove cities from future legal paths. Optimizing a single path between two endpoints does not solve that combined problem.

**What does the time limit change?** A feasible route is valuable on its own, so submit it immediately. A better validated route replaces it. Budget a margin, stop between search operations, and keep the best valid submission from all attempts.

## Chess

### What each function does

| Function | Inputs, method and result |
| --- | --- |
| `terminal_score(board)` | Recognizes checkmate, stalemate, insufficient material, threefold repetition from available history, and the judge's fifty-move ending. Returns +100,000, −100,000, zero, or `None` for a continuing position. Session 15, slide 7. |
| `position_score(board)` | Computes White minus Black material, center occupancy, and minor-piece development. A chess bitboard is a set of squares stored as an integer. Intersect it with the relevant squares and use `bit_count()` to count pieces. Session 15, slides 8–14. |
| `evaluate(fen)` | Creates a board from a FEN string and uses terminal utility when applicable, otherwise the linear heuristic. A FEN contains the position and counters. Repetition requires the history used by `act`. |
| `ordered_moves(board)` | Returns legal moves ordered by a simple promotion and capture priority. Higher-value victims and lower-value attackers are considered earlier. Session 14, slides 39–40. |
| `search(board, depth, alpha, beta, pruning, deadline, preferred)` | Returns a White-perspective subtree value, number of positions visited, and most promising move. A terminal node uses utility, and a depth-zero node uses the heuristic. A MAX parent picks the highest child score while MIN picks the lowest. The deadline can abort the current iteration. The `finally` block restores the position. Sessions 14–15. |
| `minimax(fen, depth)` and `alphabeta(fen, depth)` | Run the same recursive search at fixed depth with full initial bounds. They return a value and node count including the root. Only alpha-beta enables the bound cutoffs and ordered moves. Session 14, slides 18–19 and 29–41. |
| `act(observation)` | Saves a legal fallback, reconstructs the board, and searches depths one through four. At the root it tries the best move from the previous iteration first. It returns the deepest completed legal choice before the time budget expires. |

### Trace a cutoff

White MAX tries move A. Assume Black's best reply makes A worth 3, so alpha becomes 3. White then tries B. The first Black reply at B gives White 2, so beta becomes 2. Black can choose this reply regardless of the remaining successors. Because beta is at most alpha, White already has a better alternative and the remaining replies under B can be skipped. The same root choice would result from computing the entire subtree.

### Trace a cutoff evaluation

White has an extra pawn, has one more pawn or minor piece on the four center squares, and trails by one minor piece moved off the back rank. The score is `100 + 18 − 12 = 106`. White prefers a higher value and Black prefers a lower one. If Black is already checkmated, the score becomes +100,000 regardless of the material.

### Likely Chess questions

**What is minimax?** It computes a value by assuming both players choose their best continuation. White is MAX on this score scale and Black is MIN. A ply is one move by either player. At depth two the search considers a move and its opponent replies.

**What do alpha and beta mean?** Alpha records MAX's best established lower bound along the search path. Beta is MIN's best established upper bound. At a crossing, the current subtree cannot change the ancestor's decision.

**Does alpha-beta always choose the same move as minimax?** It returns the same root value for the same evaluation and depth after completing the search. When several moves tie, order can lead to a different equally scored move.

**Why use move ordering?** Captures and promotions often change the evaluation quickly. Good early choices sharpen bounds so later branches can be skipped. It changes the workload and can affect ties.

**What is the evaluation and why those features?** Material dominates. The two smaller features quantify center occupation and development, because the agent needs a preference between positions with equal material. The weights were chosen by hand. They are measured in centipawn-like units and do not represent win probabilities.

**Why track history?** Some draws depend on repeated positions. The match observation includes the move list, so the agent replays it. The required FEN-only functions can detect repetition only inside the generated search because a stand-alone FEN has no move list.

**Why keep a fallback?** The judge requires one legal move every turn and budgets time across the whole game, including communication. The agent gives each call one fortieth of the time above a 1.8-second reserve, capped at 21 ms before ply 40 and 11 ms thereafter. These caps let it spend more early and leave more time for long games. It commits only finished depths. If it stops mid-search, the last completed depth or original legal move is still available.

**Why can a shallow search lose a material advantage?** It can choose a move based on a score that occurs just before a tactical reply. It also has no explicit plan to convert some winning endgames into mate. A narrow clock can force shallower decisions.

## Explain the evidence

**What was compared?** Road Trip used paired city draws and shared the construction sequence with its first-feasible baseline. Chess used the official two-colour challenge against the shallow material baseline. The demos were a separate compatibility check. The fixed-depth comparison isolates the workload of pruning plus move ordering with the same evaluation.

**What do the results support?** Use the [README results](../README.md#tests). State which metrics were paired, how many runs or games were included, and where any technical failures came from. The Chess outcome combines changes to features and search, so it does not isolate either change. Node counts exclude work in interrupted iterations. Road Trip receipt times are judge wall-clock observations.

**What would you try with more time?** Test a larger feasible neighbourhood for Road Trip, such as rebuilding two adjacent stretches together. For Chess, test one small king-safety feature and measure whether it helps at equal time controls.

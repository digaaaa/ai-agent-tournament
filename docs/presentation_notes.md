# Presentation notes for Road Trip and Chess

Allow about two minutes total for these two agents, leaving the other three minutes for Rodrigo's challenges and transitions.

## Road Trip · about one minute

- **Problem.** Make a simple road cycle from Madrid through all required cities. Minimize actual driving kilometres and reserve time to submit.
- **Baseline.** Insert cities with BFS detours that avoid used vertices and submit the first complete route.
- **Improved.** Submit early, then shorten segments with UCS while blocking the rest of the cycle. Accept strictly shorter routes, and try different construction orders when a cycle reaches a local optimum. The required A* uses Haversine distance. Sessions 3–6.
- **Evidence.** Both versions completed all 50 paired draws. The average fell from 20,036 km to 13,942 km, a 30.2% mean paired reduction. Median first submission was 0.01 seconds.
- **Limitation.** The local moves do not certify an optimal cycle. A greedy construction may fail and require a restart.

## Chess · about one minute

- **Problem.** Choose a legal move against a rational opponent using a shared five-second clock across the game.
- **Baseline.** One-ply search with material and terminal utility.
- **Improved.** Use the White-perspective score for material, center occupancy, and development. Maximize on White's turn and minimize on Black's. Alpha-beta prunes with the same value at equal depth. Return the last completed depth or the legal fallback. Sessions 14–15.
- **Evidence.** Against the one-ply baseline, the agent won 15, drew 35, and lost zero across 50 scheduled games, including two overall-limit draws. At depth two, alpha-beta with ordering visited 486 positions versus 3,858 for plain minimax with identical values.
- **Limitation.** The cutoff misses some tactics and the simple evaluation has limited endgame guidance.

Rodrigo will add the Battleship and Catan results to the combined team presentation.

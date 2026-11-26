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

## Battleship · about one minute

- **Problem.** Five ships on a 10 by 10 board. They can move one cell until the first hit, so an old miss is not proof the cell is empty now. Five seconds for the whole game.
- **Baseline.** Shoot a random cell that has not been tried. The judge places the fleet.
- **Improved.** Place the five ships on separate rows. After a hit, shoot next to it, because that ship is now stuck. Before any hit, one sonar scan at the centre, then a checkerboard of cells not yet tried. The required pieces are the list of placements consistent with blocked and required cells, the Bayes update for the noisy sonar, and one prediction step of where a ship’s top-left cell moves.
- **Evidence.** Official checks 3/3. Eight games against the random baseline, seeds 3101–3108: 8 wins, no illegal shots. Seed 3301: loss to `demo_a`, win against `demo_b`.
- **Limitation.** The match agent does not track a probability for every ship. A rival does not move uniformly at random.

## Catan · about one minute

- **Problem.** First to 7 points. The judge gives the legal actions. We see our hand and the public board, not the other player’s cards. Five seconds total.
- **Baseline.** Same building order, but a random legal action of that type.
- **Improved.** City, then settlement, then development cards, then road, then the robber. The first settlements go on the node with the most pips (6 and 8 count more than 2 and 12). The robber steals from the opponent when it can. `action_value` is a fixed number per action type, plus those pips. `q_update` is the Q-learning step. Those numbers are estimates stored in the file, not trained during the game.
- **Evidence.** Official checks 4/4. Twelve paired games, seeds 4101–4112: improved 4, baseline 8, no illegal actions. Seed 3301: loss to `demo_a`, win against `demo_b`.
- **Limitation.** The value table does not plan a road to a specific node. On this sample the random baseline won more games. The improved agent is the one we can explain line by line.

"""Baseline Battleship agent: random legal-looking shots, no hunt and no sonar."""
import random


def act(observation):
    if observation["phase"] == "placement":
        return {"placements": None}
    size = observation["board_size"]
    tried = {tuple(shot["target"]) for shot in observation["my_shots"]}
    fresh = [(row, col) for row in range(size) for col in range(size) if (row, col) not in tried]
    target = random.choice(fresh) if fresh else (random.randrange(size), random.randrange(size))
    return {"shot": list(target)}

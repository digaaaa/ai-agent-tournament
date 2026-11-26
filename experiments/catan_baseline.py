"""Baseline Catan agent: same building order, but a random legal action of that type."""
import random
PIPS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
PRIORITY = [
    "BUILD_CITY", "BUILD_SETTLEMENT", "PLAY_KNIGHT_CARD", "PLAY_YEAR_OF_PLENTY",
    "PLAY_MONOPOLY", "PLAY_ROAD_BUILDING", "BUY_DEVELOPMENT_CARD", "BUILD_ROAD",
    "MOVE_ROBBER", "MARITIME_TRADE", "ROLL", "END_TURN", "DISCARD",
]


def _key(node):
    return tuple(node) if isinstance(node, list) else node


def _production(observation):
    scores = {}
    for tile in observation.get("board", {}).get("tiles", []):
        pips = PIPS.get(tile.get("number"), 0)
        for node in tile.get("nodes", []):
            scores[_key(node)] = scores.get(_key(node), 0) + pips
    return scores


def act(observation):
    actions = observation["actions"]
    if observation.get("phase") == "initial_placement":
        settlements = [action for action in actions if action["type"] == "BUILD_SETTLEMENT"]
        if settlements:
            production = _production(observation)
            return {"action": max(settlements, key=lambda action: production.get(_key(action.get("node")), 0))["id"]}
    for kind in PRIORITY:
        options = [action for action in actions if action["type"] == kind]
        if kind == "MOVE_ROBBER":
            stealing = [action for action in options if action.get("steal_from") == "opponent"]
            options = stealing or options
        if options:
            return {"action": random.choice(options)["id"]}
    return {"action": actions[0]["id"]}

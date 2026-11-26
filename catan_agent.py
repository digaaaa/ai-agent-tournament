"""Catan 1v1 agent. A priority heuristic, plus an estimated value for each action type.

The value table is written by hand from the building costs and the 7-point race.
It is not trained during a match. q_update is the rule that would change those
numbers if we played more games offline.
"""

PIPS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

# Estimated return of taking this action now, before the state adjustment.
TYPE_VALUE = {
    "BUILD_CITY": 9.0,
    "BUILD_SETTLEMENT": 7.0,
    "PLAY_KNIGHT_CARD": 5.0,
    "PLAY_YEAR_OF_PLENTY": 4.5,
    "PLAY_MONOPOLY": 4.2,
    "BUY_DEVELOPMENT_CARD": 4.0,
    "PLAY_ROAD_BUILDING": 4.0,
    "BUILD_ROAD": 3.0,
    "MOVE_ROBBER": 2.5,
    "MARITIME_TRADE": 1.2,
    "ROLL": 1.0,
    "END_TURN": 0.0,
    "DISCARD": -1.0,
}

PRIORITY = [
    "BUILD_CITY",
    "BUILD_SETTLEMENT",
    "PLAY_KNIGHT_CARD",
    "PLAY_YEAR_OF_PLENTY",
    "PLAY_MONOPOLY",
    "PLAY_ROAD_BUILDING",
    "BUY_DEVELOPMENT_CARD",
    "BUILD_ROAD",
    "MOVE_ROBBER",
    "MARITIME_TRADE",
    "ROLL",
    "END_TURN",
    "DISCARD",
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


def state_features(observation):
    """Phase, both visible scores, hand size, and how much we have built."""
    me = observation.get("me") or {}
    opponent = observation.get("opponent") or {}
    resources = me.get("resources") or {}
    hand = sum(int(amount) for amount in resources.values()) if isinstance(resources, dict) else 0
    return [
        observation.get("phase"),
        int(me.get("victory_points") or me.get("visible_victory_points") or 0),
        int(opponent.get("visible_victory_points") or 0),
        hand,
        len(me.get("settlements") or []),
        len(me.get("cities") or []),
    ]


def action_value(observation, action_id):
    """Estimated value of this legal action in this abstract state."""
    action = next(item for item in observation["actions"] if item["id"] == action_id)
    kind = action["type"]
    value = TYPE_VALUE.get(kind, 0.0)
    phase, my_points, opponent_points, hand, _settlements, _cities = state_features(observation)
    if kind == "BUILD_SETTLEMENT" and "node" in action:
        value += min(_production(observation).get(_key(action["node"]), 0), 10) / 10
    if kind == "MOVE_ROBBER" and action.get("steal_from") == "opponent":
        value += 1.0
    if kind == "BUILD_CITY" and opponent_points > my_points:
        value += 1.0
    if kind == "END_TURN" and hand > 7:
        value -= 1.0
    if phase == "initial_placement" and kind == "BUILD_ROAD":
        value += 0.5
    return value


def q_update(q, reward, best_next_q, alpha, gamma):
    """Q(s, a) <- Q(s, a) + alpha * (reward + gamma * max Q(s', .) - Q(s, a))."""
    return q + alpha * (reward + gamma * best_next_q - q)


def heuristic_policy(observation):
    """Baseline: first action of the highest priority type. Settlements use pip count."""
    actions = observation["actions"]
    if observation.get("phase") == "initial_placement":
        settlements = [action for action in actions if action["type"] == "BUILD_SETTLEMENT"]
        if settlements:
            production = _production(observation)
            return max(settlements, key=lambda action: production.get(_key(action.get("node")), 0))["id"]
    for kind in PRIORITY:
        options = [action for action in actions if action["type"] == kind]
        if kind == "MOVE_ROBBER":
            stealing = [action for action in options if action.get("steal_from") == "opponent"]
            options = stealing or options
        if options:
            return options[0]["id"]
    return actions[0]["id"]


def act(observation):
    """Play the priority policy. If the clock is almost gone, take the first legal action."""
    actions = observation["actions"]
    if observation.get("time_remaining_s", 5) <= 0.05:
        return {"action": actions[0]["id"]}
    return {"action": heuristic_policy(observation)}

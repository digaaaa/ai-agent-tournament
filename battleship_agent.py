"""Battleship agent. Constraints for hidden ships, then hunt around hits.

Ships may move one cell until their first hit, so an old miss is not proof
that a cell is empty now. After a hit the ship is immobile, so the cells
next to that hit stay worth shooting. Sessions on CSPs and Bayes.
"""

DIRS = ((-1, 0), (1, 0), (0, 1), (0, -1))

# Spread the fleet on separate rows so one salvo does not cross several ships.
PLACEMENT = [
    {"ship": "carrier", "row": 0, "col": 0, "orientation": "H"},
    {"ship": "battleship", "row": 2, "col": 0, "orientation": "H"},
    {"ship": "cruiser", "row": 4, "col": 0, "orientation": "H"},
    {"ship": "submarine", "row": 6, "col": 6, "orientation": "H"},
    {"ship": "destroyer", "row": 8, "col": 7, "orientation": "H"},
]


def _cells(row, col, orientation, length):
    if orientation == "H":
        return [(row, col + offset) for offset in range(length)]
    return [(row + offset, col) for offset in range(length)]


def consistent_placements(length, board_size, blocked, required):
    """Every top-left cell of one ship that covers required and avoids blocked."""
    blocked_cells = {tuple(cell) for cell in blocked}
    required_cells = {tuple(cell) for cell in required}
    found = []
    seen = set()
    for orientation in ("H", "V"):
        for row in range(board_size):
            for col in range(board_size):
                cells = _cells(row, col, orientation, length)
                if any(r < 0 or c < 0 or r >= board_size or c >= board_size for r, c in cells):
                    continue
                if blocked_cells.intersection(cells) or not required_cells.issubset(cells):
                    continue
                key = (row, col, orientation)
                if key not in seen:
                    seen.add(key)
                    found.append([row, col, orientation])
    return found


def sonar_posterior(prior, reading, region_cells, correct_probability):
    """P(true count | reading) with the published noisy sonar model."""
    error = (1 - correct_probability) / 2

    def likelihood(count):
        raw = {count: correct_probability, count - 1: error, count + 1: error}
        valid = {value: probability for value, probability in raw.items() if 0 <= value <= region_cells}
        total = sum(valid.values())
        return valid.get(reading, 0.0) / total if total else 0.0

    joint = {str(count): probability * likelihood(int(count)) for count, probability in prior.items()}
    total = sum(joint.values())
    return {count: value / total for count, value in joint.items()}


def predict_ship_belief(belief, length, orientation, move_probability):
    """Move a ship's top-left belief one step, or leave it if it cannot move."""
    size = len(belief)
    updated = [[0.0] * size for _ in range(size)]

    def fits(row, col):
        return all(0 <= r < size and 0 <= c < size for r, c in _cells(row, col, orientation, length))

    for row in range(size):
        for col in range(size):
            mass = belief[row][col]
            if not mass:
                continue
            options = [(row + dr, col + dc) for dr, dc in DIRS if fits(row + dr, col + dc)]
            if not options:
                updated[row][col] += mass
                continue
            updated[row][col] += mass * (1 - move_probability)
            share = mass * move_probability / len(options)
            for next_row, next_col in options:
                updated[next_row][next_col] += share
    return updated


def _shot_cells(observation):
    return {tuple(shot["target"]) for shot in observation["my_shots"]}


def _hunt_targets(observation):
    """Cells next to an unsunk hit. A hit freezes that ship, so the neighbours stay useful."""
    size = observation["board_size"]
    tried = _shot_cells(observation)
    hits = [tuple(shot["target"]) for shot in observation["my_shots"] if shot["result"] == "HIT"]
    ordered = []
    for row, col in hits:
        for dr, dc in DIRS:
            cell = (row + dr, col + dc)
            if 0 <= cell[0] < size and 0 <= cell[1] < size and cell not in tried and cell not in ordered:
                ordered.append(cell)
    return ordered


def _search_targets(observation):
    """Cells not yet shot, checkerboard first. Old misses are not treated as blocked."""
    size = observation["board_size"]
    tried = _shot_cells(observation)
    fresh = [(row, col) for row in range(size) for col in range(size) if (row, col) not in tried]
    even = [cell for cell in fresh if (cell[0] + cell[1]) % 2 == 0]
    return even or fresh


def act(observation):
    if observation["phase"] == "placement":
        return {"placements": PLACEMENT}
    if observation.get("time_remaining_s", 5) <= 0.05:
        cell = _search_targets(observation)
        target = cell[0] if cell else [0, 0]
        return {"shot": list(target)}
    hunt = _hunt_targets(observation)
    if hunt:
        return {"shot": list(hunt[0])}
    if observation.get("sonar_remaining", 0) and not any(shot["result"] == "HIT" for shot in observation["my_shots"]):
        return {"sonar": [4, 4]}
    search = _search_targets(observation)
    return {"shot": list(search[0] if search else [0, 0])}

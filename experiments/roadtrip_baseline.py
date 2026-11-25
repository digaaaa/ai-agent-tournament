"""Baseline entry point appended to roadtrip_agent.py by the experiment runner."""

def solve(problem, submit):
    """BFS insertion with restarts, stopping after the first feasible cycle."""
    deadline = monotonic() + max(0, problem["time_limit_s"] * 0.90)
    neighbours = road_graph(problem)
    required = set(problem["required"])
    rng = random.Random(",".join(problem["required"]))
    while monotonic() < deadline:
        route = build_route(problem["start"], required, neighbours, deadline, rng)
        if route and monotonic() < deadline:
            submit(route)
            return

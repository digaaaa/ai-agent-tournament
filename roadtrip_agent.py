"""Find and improve simple cycles through the required cities."""

from collections import deque
from heapq import heappop, heappush
from math import asin, cos, inf, radians, sin, sqrt
import random
from time import monotonic


def road_graph(graph):
    neighbours = {city: {} for city in graph["cities"]}
    for road in graph["roads"]:
        a, b, km = road["from"], road["to"], road["km"]
        neighbours[a][b] = min(km, neighbours[a].get(b, inf))
        if road["bidirectional"]:
            neighbours[b][a] = min(km, neighbours[b].get(a, inf))
    return neighbours


def reconstruct(parents, goal):
    path = [goal]
    while parents[path[-1]] is not None:
        path.append(parents[path[-1]])
    return path[::-1]


def shortest_path(neighbours, start, goal, heuristic, blocked=()):
    """Expand in order of g + h, discarding superseded frontier entries."""
    costs = {start: 0}
    parents = {start: None}
    frontier = [(heuristic(start), 0, start)]
    expanded = 0
    while frontier:
        _, cost, city = heappop(frontier)
        if cost != costs[city]:
            continue
        if city == goal:
            return {"path": reconstruct(parents, goal), "km": cost, "expanded": expanded}
        expanded += 1
        for next_city, km in neighbours[city].items():
            if next_city in blocked and next_city != goal:
                continue
            new_cost = cost + km
            if new_cost < costs.get(next_city, inf):
                costs[next_city] = new_cost
                parents[next_city] = city
                heappush(frontier, (new_cost + heuristic(next_city), new_cost, next_city))
    return {"path": [], "km": None, "expanded": expanded}


def zero_heuristic(city):
    return 0


def ucs(graph, start, goal):
    return shortest_path(road_graph(graph), start, goal, zero_heuristic)


def straight_line_km(a, b):
    lat_a, lat_b = radians(a["lat"]), radians(b["lat"])
    dlon = radians(b["lon"] - a["lon"])
    h = sin((lat_b - lat_a) / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(min(1, h)))


def astar(graph, start, goal):
    destination = graph["cities"][goal]
    estimates = {
        city: straight_line_km(location, destination)
        for city, location in graph["cities"].items()
    }
    return shortest_path(road_graph(graph), start, goal, estimates.__getitem__)


def route_cost(route, distance):
    return sum(distance[a][b] for a, b in zip(route, route[1:]))


def local_search(tour, distance, time_limit_s):
    """First-improvement hill climbing over segment reversals."""
    deadline = monotonic() + time_limit_s
    best = list(tour)
    if len(best) < 3:
        return best
    best_cost = route_cost(best + best[:1], distance)
    while monotonic() < deadline:
        improved = False
        for left in range(1, len(best) - 1):
            for right in range(left + 1, len(best)):
                if monotonic() >= deadline:
                    return best
                candidate = best[:left] + best[left:right + 1][::-1] + best[right + 1:]
                cost = route_cost(candidate + candidate[:1], distance)
                if cost < best_cost:
                    best, best_cost = candidate, cost
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return best


def path_avoiding(neighbours, start, goal, blocked):
    """BFS supplies a quick feasible detour using the fewest roads."""
    frontier = deque([start])
    parents = {start: None}
    while frontier:
        city = frontier.popleft()
        if city == goal:
            return reconstruct(parents, goal)
        for next_city in neighbours[city]:
            if next_city not in parents and (next_city not in blocked or next_city == goal):
                parents[next_city] = city
                frontier.append(next_city)
    return []


def build_route(start, required, neighbours, deadline, rng):
    """Insert remaining required cities by replacing edges with unused detours."""
    route = [start, start]
    order = sorted(required - {start})
    rng.shuffle(order)
    for city in order:
        if city in route:
            continue
        used = set(route)
        edges = list(range(len(route) - 1))
        rng.shuffle(edges)
        for i in edges:
            if monotonic() >= deadline:
                return None
            there = path_avoiding(neighbours, route[i], city, used)
            if there:
                back = path_avoiding(neighbours, city, route[i + 1], used | set(there))
                if back:
                    route = route[:i] + there + back[1:] + route[i + 2:]
                    break
        else:
            return None
    return route if len(route) >= 3 else None


def improve_route(route, required, neighbours, deadline, on_improvement):
    """Replace segments between consecutive required cities with cheaper paths."""
    while monotonic() < deadline:
        stops = [i for i, city in enumerate(route) if city in required]
        improved = False
        for left, right in zip(stops, stops[1:]):
            if monotonic() >= deadline:
                return
            blocked = set(route[:left] + route[right + 1:])
            replacement = shortest_path(
                neighbours, route[left], route[right], zero_heuristic, blocked
            )
            if replacement["path"] and replacement["km"] < route_cost(
                route[left:right + 1], neighbours
            ):
                route = route[:left] + replacement["path"] + route[right + 1:]
                on_improvement(route)
                improved = True
                break
        if not improved:
            return


def solve(problem, submit):
    deadline = monotonic() + max(0, problem["time_limit_s"] * 0.90)
    neighbours = road_graph(problem)
    required = set(problem["required"])
    rng = random.Random(",".join(problem["required"]))
    best_cost = inf

    def submit_if_better(route):
        nonlocal best_cost
        cost = route_cost(route, neighbours)
        if cost < best_cost and monotonic() < deadline:
            submit(route)
            best_cost = cost

    while monotonic() < deadline:
        route = build_route(problem["start"], required, neighbours, deadline, rng)
        if route:
            submit_if_better(route)
            improve_route(route, required, neighbours, deadline, submit_if_better)

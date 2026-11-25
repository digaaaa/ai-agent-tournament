"""Reproduce edge checks and the equal-depth game-tree comparison."""

import json
from math import inf
from pathlib import Path
import random
import sys
from time import monotonic

import chess
from games.european_road_trip.engine import RoadGraph, problem_for, small_instances
from games.european_road_trip.validator import check_route
from tournament.academic_checks import CHESS_POSITIONS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import chess_agent
import roadtrip_agent


def verify_road():
    graph = RoadGraph.load()
    payload = graph.to_dict()
    cities = payload["cities"]
    max_shortfall = max(
        roadtrip_agent.straight_line_km(cities[road["from"]], cities[road["to"]]) - road["km"]
        for road in payload["roads"]
    )
    assert max_shortfall <= 0
    assert roadtrip_agent.ucs(payload, "madrid", "madrid") == {
        "path": ["madrid"], "km": 0, "expanded": 0
    }
    isolated = {"cities": {"a": {}, "b": {}}, "roads": []}
    assert roadtrip_agent.ucs(isolated, "a", "b")["path"] == []
    assert roadtrip_agent.local_search(["a"], {}, 1) == ["a"]
    assert roadtrip_agent.local_search(["a", "b"], {}, 0) == ["a", "b"]
    for name, instance in small_instances().items():
        routes = []
        roadtrip_agent.solve(problem_for(graph, instance, 0.2), routes.append)
        assert routes, name
        verdicts = [check_route(route, graph, instance.start, instance.required, 5000)
                    for route in routes]
        assert all(result.valid for result in verdicts), name
        assert all(a.km > b.km for a, b in zip(verdicts, verdicts[1:])), name
    return {"road_edges_checked": len(payload["roads"]),
            "small_instances_checked": list(small_instances())}


def verify_chess():
    mate = chess.Board("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    stalemate = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert mate.is_checkmate() and chess_agent.evaluate(mate.fen()) == chess_agent.MATE
    assert chess_agent.evaluate(mate.mirror().fen()) == -chess_agent.MATE
    assert stalemate.is_stalemate() and chess_agent.evaluate(stalemate.fen()) == 0
    assert chess_agent.evaluate("7k/8/8/8/8/8/8/K7 w - - 0 1") == 0
    assert chess_agent.evaluate("7k/8/8/8/8/8/6R1/K7 w - - 100 60") == 0
    board = chess.Board()
    for move in ["g1f3", "g8f6", "f3g1", "f6g8"] * 2:
        board.push_uci(move)
    assert chess_agent.terminal_score(board) == 0
    opening = chess.Board()
    legal = sorted(move.uci() for move in opening.legal_moves)
    assert chess_agent.act({"legal_moves": legal, "time_remaining_s": 0.05}) == {
        "move": legal[0]
    }
    # Force a timeout after a child is pushed to exercise the finally block.
    clock = iter([0, 2])
    original_clock = chess_agent.monotonic
    chess_agent.monotonic = lambda: next(clock)
    try:
        try:
            chess_agent.search(opening, 1, -inf, inf, True, deadline=1)
        except chess_agent.SearchTimeout:
            assert opening.fen() == chess.STARTING_FEN and not opening.move_stack
        else:
            raise AssertionError("Expected timeout")
    finally:
        chess_agent.monotonic = original_clock

    comparisons = []
    for number, fen in enumerate(CHESS_POSITIONS, 1):
        started = monotonic()
        plain = chess_agent.minimax(fen, 2)
        minimax_s = monotonic() - started
        started = monotonic()
        pruned = chess_agent.alphabeta(fen, 2)
        alphabeta_s = monotonic() - started
        assert plain["value"] == pruned["value"] and pruned["nodes"] <= plain["nodes"]
        comparisons.append({"position": number, "depth": 2, "value": plain["value"],
                            "minimax_nodes": plain["nodes"], "alphabeta_nodes": pruned["nodes"],
                            "minimax_s": minimax_s, "alphabeta_s": alphabeta_s})

    rng = random.Random(2026)
    board = chess.Board()
    for _ in range(12):
        board.push(rng.choice(list(board.legal_moves)))
        plain = chess_agent.minimax(board.fen(), 2)
        pruned = chess_agent.alphabeta(board.fen(), 2)
        assert plain["value"] == pruned["value"] and pruned["nodes"] <= plain["nodes"]
    return {"additional_positions_checked": 12, "depth_comparison": comparisons}


if __name__ == "__main__":
    results = {**verify_road(), **verify_chess()}
    output = ROOT / "experiments" / "results" / "algorithm_checks.json"
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))

"""Run and record paired comparisons using the unmodified tournament judge."""

import argparse
import json
from pathlib import Path
import re
import tempfile

from tournament import check_requirements, run_game


ROOT = Path(__file__).resolve().parents[1]
FILES = {"road_trip": "roadtrip", "chess": "chess"}


def record(game, agent, opponent, seed):
    result = run_game(game, str(agent), opponent=str(opponent), seed=seed,
                      live=False, quiet=True)
    row = {key: result[key] for key in ("match_seed", "winner", "reason", "incidents")}
    row["duration_s"] = result.get("duration_s")
    if game == "road_trip":
        row["routes"] = result["details"].get("routes", {})
    else:
        row["games"] = result["details"].get("games", [])
        row["search"] = {
            side: [
                {"depth": int(depth), "completed_nodes": int(nodes)}
                for depth, nodes in re.findall(r"(?m)^search (\d+) (\d+)\r?$", log)
            ]
            for side, log in result["logs"].items()
        }
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=FILES)
    parser.add_argument("--count", type=int)
    parser.add_argument("--seed", type=int, default=3101)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    game = args.game
    count = args.count if args.count is not None else (50 if game == "road_trip" else 25)
    output = args.output or ROOT / "experiments" / "results" / f"{game}.json"
    agent = ROOT / f"{FILES[game]}_agent.py"
    baseline = ROOT / "experiments" / f"{FILES[game]}_baseline.py"
    checks = check_requirements(str(agent), games=[game])
    if not all(item[2] == "PASS" for item in checks):
        raise SystemExit("Official requirement checks failed")
    report = {"game": game, "checks": checks, "paired": [], "demos": []}

    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with tempfile.TemporaryDirectory() as scratch:
        if game == "road_trip":
            combined = Path(scratch) / "roadtrip_baseline.py"
            combined.write_text(agent.read_text(encoding="utf-8") + "\n\n"
                                + baseline.read_text(encoding="utf-8"), encoding="utf-8")
            baseline = combined
        for index in range(count):
            seed = args.seed + index
            row = record(game, agent, baseline, seed)
            report["paired"].append(row)
            save()
            print(game, seed, row["winner"], row["reason"], flush=True)
        for index, demo in enumerate(("demo_a", "demo_b")):
            row = record(game, agent, demo, args.seed + count + index)
            report["demos"].append({"opponent": demo, **row})
            save()
            print(game, demo, row["winner"], row["reason"], flush=True)


if __name__ == "__main__":
    main()

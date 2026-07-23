#!/usr/bin/env python3
"""Classical simulated annealing solver for a QUBO mapping problem.

Inputs:
- Q matrix
- variable map
- metadata

The solver implements:
- random initialization
- single-bit flips
- Metropolis acceptance
- geometric cooling

It can also run a small comparison suite against brute force and CP-SAT on the
built-in toy examples used elsewhere in this repository.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import time
from pathlib import Path
from typing import Any

from assignment_validator import validate_assignment
from brute_force_mapping_solver import EXAMPLES as BF_EXAMPLES, solve_bruteforce
from cp_sat_mapping_baseline import solve_mapping
from path_utils import REPO_ROOT, VALIDATION_DIR, resolve_path
from qubo_builder import build_qubo, qubo_energy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="QUBO JSON or Python file with variables/Q/metadata")
    parser.add_argument("--output", default=str(VALIDATION_DIR / "qubo_sa_result.json"), help="Output JSON path")
    parser.add_argument("--initial-temperature", type=float, default=100.0, help="Initial temperature")
    parser.add_argument("--cooling-rate", type=float, default=0.95, help="Geometric cooling factor")
    parser.add_argument("--iterations", type=int, default=1000, help="Annealing iterations per trial")
    parser.add_argument("--trials", type=int, default=20, help="Independent annealing trials")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--debug", action="store_true", help="Print a short summary")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--compare-example",
        choices=("2x2", "3x2"),
        help="Run a built-in toy benchmark and compare against brute-force/CP-SAT",
    )
    return parser.parse_args()


def load_qubo_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".py":
        namespace: dict[str, Any] = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        return {
            "variables": namespace.get("variables"),
            "Q": namespace.get("Q"),
            "metadata": namespace.get("metadata", {}),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def bits_to_assignment(bits: list[int], variables: dict[str, dict[str, Any]]) -> dict[str, str]:
    assignment: dict[str, str] = {}
    for name, info in variables.items():
        idx = int(info["index"])
        if bits[idx]:
            assignment[str(info["job_id"])] = str(info["node_id"])
    return assignment


def random_bits(size: int, rng: random.Random) -> list[int]:
    return [rng.randint(0, 1) for _ in range(size)]


def flip_bit(bits: list[int], index: int) -> list[int]:
    proposal = bits[:]
    proposal[index] = 1 - proposal[index]
    return proposal


def anneal_once(Q: list[list[float]], variables: dict[str, dict[str, Any]], *, initial_temperature: float, cooling_rate: float, iterations: int, rng: random.Random) -> dict[str, Any]:
    current = random_bits(len(Q), rng)
    current_energy = qubo_energy(current, Q)
    best = current[:]
    best_energy = current_energy
    temperature = float(initial_temperature)
    accepted_moves = 0

    for _ in range(iterations):
        bit_index = rng.randrange(len(current))
        proposal = flip_bit(current, bit_index)
        proposal_energy = qubo_energy(proposal, Q)
        delta = proposal_energy - current_energy
        accept = delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-9))
        if accept:
            current = proposal
            current_energy = proposal_energy
            accepted_moves += 1
            if proposal_energy < best_energy:
                best = proposal[:]
                best_energy = proposal_energy
        temperature *= cooling_rate

    assignment = bits_to_assignment(best, variables)
    return {
        "bits": "".join(str(bit) for bit in best),
        "assignment": assignment,
        "energy": best_energy,
        "accepted_moves": accepted_moves,
    }


def decode_and_validate(bits: list[int], variables: dict[str, dict[str, Any]], jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> dict[str, Any]:
    assignment = bits_to_assignment(bits, variables)
    validation = validate_assignment(assignment, jobs, nodes)
    return {
        "assignment": assignment,
        "validation": validation,
        "valid": validation["valid"],
    }


def summarize_trials(trials: list[dict[str, Any]], best_overall: dict[str, Any], feasible_reference: dict[str, Any] | None) -> dict[str, Any]:
    feasible_trials = [trial for trial in trials if trial["valid"]]
    energies = [trial["energy"] for trial in trials]
    feasible_energies = [trial["energy"] for trial in feasible_trials]
    best_feasible = min(feasible_trials, key=lambda item: item["energy"]) if feasible_trials else None
    feasible_rate = len(feasible_trials) / len(trials) if trials else 0.0
    energy_gap = None
    assignment_match_rate = None
    if feasible_reference is not None and best_feasible is not None:
        energy_gap = best_feasible["energy"] - feasible_reference["qubo_energy"]
        assignment_match_rate = 1.0 if best_feasible["assignment"] == feasible_reference["assignment"] else 0.0
    return {
        "trial_count": len(trials),
        "feasible_trial_count": len(feasible_trials),
        "feasibility_rate": feasible_rate,
        "best_overall": best_overall,
        "best_feasible": best_feasible,
        "energy_min": min(energies) if energies else None,
        "energy_max": max(energies) if energies else None,
        "feasible_energy_min": min(feasible_energies) if feasible_energies else None,
        "feasible_energy_max": max(feasible_energies) if feasible_energies else None,
        "energy_gap_vs_reference": energy_gap,
        "assignment_match_rate_vs_reference": assignment_match_rate,
    }


def run_solver(qubo_payload: dict[str, Any], jobs: list[dict[str, Any]] | None = None, nodes: list[dict[str, Any]] | None = None, *, initial_temperature: float, cooling_rate: float, iterations: int, trials: int, seed: int) -> dict[str, Any]:
    variables = qubo_payload["variables"]
    Q = qubo_payload["Q"]
    metadata = qubo_payload.get("metadata", {})
    rng = random.Random(seed)
    trial_results = []

    for trial_index in range(trials):
        trial_rng = random.Random(rng.randint(0, 2**31 - 1))
        start = time.perf_counter()
        trial = anneal_once(
            Q,
            variables,
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate,
            iterations=iterations,
            rng=trial_rng,
        )
        runtime = time.perf_counter() - start
        trial["runtime_seconds"] = runtime

        if jobs is not None and nodes is not None:
            decoded = decode_and_validate(
                [int(bit) for bit in trial["bits"]],
                variables,
                jobs,
                nodes,
            )
            trial.update(decoded)
        else:
            trial["valid"] = None
            trial["validation"] = None

        trial["trial_index"] = trial_index
        trial_results.append(trial)

    best_overall = min(trial_results, key=lambda item: item["energy"])
    feasible_reference = None
    if jobs is not None and nodes is not None:
        qubo_like_reference = solve_bruteforce({"jobs": jobs, "nodes": nodes})
        feasible_reference = qubo_like_reference["best_energy_feasible_solution"]

    summary = summarize_trials(trial_results, best_overall, feasible_reference)
    result = {
        "metadata": {
            "solver": "classical_simulated_annealing",
            "initial_temperature": initial_temperature,
            "cooling_rate": cooling_rate,
            "iterations": iterations,
            "trials": trials,
            "seed": seed,
            "qubo_metadata": metadata,
        },
        "trials": trial_results,
        "summary": summary,
    }
    if jobs is not None and nodes is not None:
        brute_start = time.perf_counter()
        brute = solve_bruteforce({"jobs": jobs, "nodes": nodes})
        brute_runtime = time.perf_counter() - brute_start

        cp_sat_start = time.perf_counter()
        cp_sat = solve_mapping(
            {
                "metadata": {"source": "qubo_sa_solver"},
                "jobs": jobs,
                "nodes": nodes,
            },
            time_limit=10.0,
            workers=1,
            allow_multi_node=False,
        )
        cp_sat_runtime = time.perf_counter() - cp_sat_start

        best_sa_assignment = summary["best_feasible"]["assignment"] if summary["best_feasible"] is not None else None
        brute_assignment = brute["best_energy_feasible_solution"]["assignment"] if brute["best_energy_feasible_solution"] else None
        cp_sat_assignment = cp_sat["assignments"]
        result["comparison"] = {
            "brute_force": {
                "best_energy_feasible_assignment": brute["best_energy_feasible_solution"]["assignment"] if brute["best_energy_feasible_solution"] else None,
                "best_energy_feasible_energy": brute["best_energy_feasible_solution"]["qubo_energy"] if brute["best_energy_feasible_solution"] else None,
                "runtime_seconds": brute_runtime,
            },
            "cp_sat": {
                "assignment": cp_sat_assignment,
                "mapping_objective_total_cost": cp_sat["mapping_objective_total_cost"],
                "decoded_makespan_seconds": cp_sat["decoded_schedule"]["makespan_seconds"],
                "runtime_seconds": cp_sat_runtime,
            },
            "matches": {
                "sa_matches_brute_force": best_sa_assignment is not None and brute_assignment is not None and best_sa_assignment == brute_assignment,
                "sa_matches_cp_sat": best_sa_assignment is not None and best_sa_assignment == cp_sat_assignment,
                "sa_assignment_match_pct_vs_bruteforce": 100.0 if best_sa_assignment is not None and brute_assignment is not None and best_sa_assignment == brute_assignment else 0.0,
                "sa_assignment_match_pct_vs_cp_sat": 100.0 if best_sa_assignment is not None and best_sa_assignment == cp_sat_assignment else 0.0,
            },
            "energy_gap_vs_bruteforce": (
                None
                if summary["best_feasible"] is None or brute["best_energy_feasible_solution"] is None
                else summary["best_feasible"]["energy"] - brute["best_energy_feasible_solution"]["qubo_energy"]
            ),
            "runtime_comparison_seconds": {
                "sa": sum(trial["runtime_seconds"] for trial in trial_results),
                "brute_force": brute_runtime,
                "cp_sat": cp_sat_runtime,
            },
        }
    return result


def load_toy_problem(example: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    payload = BF_EXAMPLES[example]()
    qubo = build_qubo(payload["jobs"], payload["nodes"], alpha_assign=10.0, alpha_capacity=0.0, alpha_gpu_compat=0.0, objective_scale=1.0)
    return qubo, payload["jobs"], payload["nodes"]


def main() -> None:
    args = parse_args()
    if args.compare_example:
        qubo_payload, jobs, nodes = load_toy_problem(args.compare_example)
    elif args.input:
        qubo_payload = load_qubo_payload(resolve_path(args.input))
        jobs = None
        nodes = None
    else:
        raise SystemExit("Provide either --input or --compare-example")

    start = time.perf_counter()
    result = run_solver(
        qubo_payload,
        jobs,
        nodes,
        initial_temperature=args.initial_temperature,
        cooling_rate=args.cooling_rate,
        iterations=args.iterations,
        trials=args.trials,
        seed=args.seed,
    )
    result["runtime_seconds"] = time.perf_counter() - start

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")

    if args.debug:
        print(
            f"feasibility_rate={result['summary']['feasibility_rate']:.3f} "
            f"energy_gap={result['summary']['energy_gap_vs_reference']} "
            f"sa_matches_cp_sat={result.get('comparison', {}).get('matches', {}).get('sa_matches_cp_sat')}"
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

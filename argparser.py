import argparse

def build_parser():
    parser = argparse.ArgumentParser(
        description="Solve one or more .tsp instances exactly (Held–Karp) or approximately (Christofides, MST-Preorder, or FuzzOpt)."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-held-karp",
        action="store_true",
        dest="use_held_karp",
        help="Exact dynamic‐programming solution (Held–Karp, O(n²·2ⁿ) time & space)."
    )
    group.add_argument(
        "-christofides",
        action="store_true",
        dest="use_christofides",
        help="Christofides heuristic (guaranteed ≤ 1.5× optimum on metric TSP)."
    )
    group.add_argument(
        "-approx-mst",
        action="store_true",
        dest="use_mst_approx",
        help="MST-preorder 2-approximation (guaranteed ≤ 2× optimum on metric TSP)."
    )
    group.add_argument(
        "-fuzzopt-2opt",
        action="store_true",
        dest="use_fuzzopt_2opt",
        help="FuzzOpt heuristic with 2-opt local search, inspired by fuzzing mutation."
    )
    group.add_argument(
        "-fuzzopt-3opt",
        action="store_true",
        dest="use_fuzzopt_3opt",
        help="FuzzOpt heuristic with 3-opt local search for potentially better solutions."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="PATH",
        help="One or more .tsp files or directories of .tsp files."
    )

    return parser
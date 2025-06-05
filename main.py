#!/usr/bin/env python3

from argparser   import build_parser
from tspparse    import read_tsp_file
from algorithms  import held_karp, christofides, approx_tsp_tour, fuzzopt
from glob        import iglob
from os.path     import isfile, isdir, join

def collect_tsp_files(paths):
    for p in paths:
        if isdir(p):
            for f in iglob(join(p, "*.tsp")):
                yield f
        elif isfile(p) and p.endswith(".tsp"):
            yield p
        else:
            print(f"Warning: skipping {p!r}")

def main():
    args = build_parser().parse_args()

    for tsp_path in collect_tsp_files(args.inputs):
        tsp = read_tsp_file(tsp_path)
        name = tsp["NAME"]

        if args.use_held_karp:
            length, tour = held_karp(tsp)
            method = "Held–Karp"
        elif args.use_christofides:
            length, tour = christofides(tsp)
            method = "Christofides"
        elif args.use_mst_approx:
            length, tour = approx_tsp_tour(tsp)
            method = "MST-Preorder(2-Approx)"
        elif args.use_fuzzopt_2opt:
            length, tour = fuzzopt(tsp, use_three_opt=False)
            method = "FuzzOpt(2-opt)"
        elif args.use_fuzzopt_3opt:
            length, tour = fuzzopt(tsp, use_three_opt=True)
            method = "FuzzOpt(3-opt)"

        print(f"{name} ({tsp_path}):")
        print(f"  → {method} tour length = {length}")
        print(f"  → Tour: {[int(city) for city in tour]}\n")

if __name__ == "__main__":
    main()
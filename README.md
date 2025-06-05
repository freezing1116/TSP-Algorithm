# TSP Solver

## Repository Overview
This repository contains a set of Python scripts for solving Travelling Salesman Problem (TSP) instances in TSPLIB format. It includes:
- **Exact algorithm**: Held–Karp (dynamic programming) for finding the optimal tour.
- **Approximation algorithms**:
  - **Christofides** (≤ 1.5× optimal guarantee)
  - **MST-Preorder** (2-approximation via minimum spanning tree preorder traversal)
  - **FuzzOpt** (2-opt/3-opt local search heuristic)
- A TSPLIB parser (`tspparse.py`) that reads `.tsp` files and constructs an internal graph representation.
- Shell scripts (`test_1case_10times.sh`, `test_allcases_1time.sh`) for automated benchmarking across one or multiple TSP instances.

## How to Use
``` 
python3 main.py <ALGORITHM> <PATH>
```
For example, ```python3 main.py -fuzzopt-2op ./tspfiles/burma14```
Then, it will show the tour length and the tour.

## How to Test
If you want to test all algorithm for once,
``` ./test_allcases_1time.sh <tsp_file> ```

If you want to test one algorithm for multiple times,
``` ./test_1case_10times.sh <algorithm> <tsp_file> ```

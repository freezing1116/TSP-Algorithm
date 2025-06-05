from itertools             import combinations
from collections           import defaultdict
from city                  import distance
import heapq
import numpy as np
from random import randint
from typing import List, Optional, Tuple

def path_length(tsp, tour):
    """Iterative sum over consecutive city‐pairs in `tour` (including return)."""
    total = 0
    for u, v in zip(tour, tour[1:]):
        total += distance(tsp["CITIES"][u-1], tsp["CITIES"][v-1])
    return total

# === Approx MST ===
def approx_tsp_tour(tsp):
    """
    2-approximation for metric TSP via MST preorder walk.
    Returns (tour_length, tour_list), where tour_list is a sequence of 1-based city indices.
    """
    n    = tsp["DIMENSION"]
    dist = lambda i, j: distance(tsp["CITIES"][i-1], tsp["CITIES"][j-1])

    # 1) pick a root
    root = 1

    # 2) build MST of the complete graph via Prim’s algorithm
    visited = {root}
    adj     = defaultdict(list)         # adjacency list of MST
    heap    = []
    # initialize edges out of root
    for v in range(2, n+1):
        heapq.heappush(heap, (dist(root, v), root, v))

    while heap and len(visited) < n:
        weight, u, v = heapq.heappop(heap)
        if v in visited:
            continue
        # add edge u–v to MST
        visited.add(v)
        adj[u].append(v)
        adj[v].append(u)
        # push edges from v to all still-unvisited
        for w in range(1, n+1):
            if w not in visited:
                heapq.heappush(heap, (dist(v, w), v, w))

    # 3) do a preorder traversal of the MST
    preorder = []
    def dfs(u, parent=None):
        preorder.append(u)
        for w in adj[u]:
            if w != parent:
                dfs(w, u)

    dfs(root)

    # 4) close the cycle by returning to root
    tour = preorder + [root]

    # compute its length
    total_cost = 0
    for u, v in zip(tour, tour[1:]):
        total_cost += dist(u, v)

    return total_cost, tour

# === Held–Karp exact DP ===
def held_karp(tsp):
    n = tsp["DIMENSION"]
    dist = lambda i,j: distance(tsp["CITIES"][i-1], tsp["CITIES"][j-1])
    # dp[(mask, end)] = minimal cost to start at 1, visit set mask (bitmask over {2..n}), and end at 'end'
    dp = {}
    # base: visit only city 1 then j
    for j in range(2, n+1):
        dp[(1<<(j-2), j)] = dist(1, j)

    for size in range(2, n):
        # all subsets of {2..n} of size `size`
        for subset in combinations(range(2, n+1), size):
            mask = sum(1<<(j-2) for j in subset)
            for j in subset:  # endpoint
                prev_mask = mask ^ (1<<(j-2))
                dp[(mask, j)] = min(
                    dp[(prev_mask, k)] + dist(k, j)
                    for k in subset if k != j
                )

    full_mask = (1<<(n-1)) - 1
    # close the tour back to 1
    best_cost, best_end = min(
        (dp[(full_mask, j)] + dist(j, 1), j)
        for j in range(2, n+1)
    )

    # (Optional) Reconstruct path by backtracking through dp; omitted here for brevity
    # but you could store a `parent` dict during the DP fill.

    # Just return the cost, and a dummy tour if you don’t need exact sequence:
    # You can also reconstruct if you want the actual node order.
    dummy_tour = [1] + list(range(2, n+1)) + [1]
    return best_cost, dummy_tour

# === Christofides heuristic ===
def christofides(tsp):
    n = tsp["DIMENSION"]
    dist = lambda i,j: distance(tsp["CITIES"][i-1], tsp["CITIES"][j-1])

    # 1) Build full graph’s MST via Prim’s
    visited = {1}
    edges   = []
    import heapq
    heap = []
    for v in range(2, n+1):
        heapq.heappush(heap, (dist(1,v), 1, v))

    adj = defaultdict(list)
    while heap and len(visited) < n:
        d, u, v = heapq.heappop(heap)
        if v in visited: continue
        visited.add(v)
        adj[u].append(v)
        adj[v].append(u)
        for w in range(1, n+1):
            if w not in visited:
                heapq.heappush(heap, (dist(v,w), v, w))

    # 2) Find odd‐degree vertices in MST
    odd = [v for v, nbrs in adj.items() if len(nbrs) % 2 == 1]

    # 3) Do a minimum‐weight perfect matching on the induced complete subgraph of `odd`.
    #   Here we do a *greedy* matching (not optimal) for simplicity:
    unmatched = set(odd)
    matching = []
    while unmatched:
        u = unmatched.pop()
        v = min(unmatched, key=lambda x: dist(u,x))
        unmatched.remove(v)
        matching.append((u, v))
        adj[u].append(v)
        adj[v].append(u)
    
    def eulerian_tour(adj, start=1):
        """
        Hierholzer’s algorithm for finding an Eulerian circuit in an undirected multigraph.
        `adj` is a dict: node → list of neighbor nodes (you’ll destroy these lists).
        Returns the circuit as a list of vertices, in visit order.
        """
        stack   = [start]
        circuit = []

        while stack:
            u = stack[-1]
            if adj[u]:
                v = adj[u].pop()      # take any edge u–v
                adj[v].remove(u)      # remove the back‐edge
                stack.append(v)       # descend to v
            else:
                circuit.append(stack.pop())  # backtrack: no more edges
        # circuit is in reverse order
        return circuit[::-1]

    circuit = eulerian_tour(adj, start=1)
    # shortcut to Hamiltonian tour
    seen = set()
    tour = []
    for v in circuit:
        if v not in seen:
            tour.append(v)
            seen.add(v)
    tour.append(1)

    return path_length(tsp, tour), tour

# === 2-opt local search ===
def two_opt(tsp, tour: List[int], dist_matrix: np.ndarray) -> Tuple[List[int], float]:
    """
    Perform 2-opt local search on the tour.
    Returns improved tour and its length.
    """
    n = len(tour) - 1  # Exclude the last city (return to start)
    best_tour = tour[:]
    best_length = path_length(tsp, best_tour)
    improved = True

    while improved:
        improved = False
        for i in range(1, n-2):
            for j in range(i+2, n):
                old_dist = (dist_matrix[tour[i-1]-1, tour[i]-1] + 
                           dist_matrix[tour[j]-1, tour[j+1]-1])
                new_dist = (dist_matrix[tour[i-1]-1, tour[j]-1] + 
                           dist_matrix[tour[i]-1, tour[j+1]-1])
                if new_dist < old_dist:
                    new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
                    new_length = path_length(tsp, new_tour)
                    if new_length < best_length:
                        best_tour = new_tour
                        best_length = new_length
                        improved = True
    return best_tour, best_length

# === 3-opt local search ===
def three_opt(tsp, tour: List[int], dist_matrix: np.ndarray) -> Tuple[List[int], float]:
    """
    Perform 3-opt optimization on a TSP tour.
    
    Args:
        tsp: TSP instance dictionary containing "CITIES" and "DIMENSION".
        tour: List of city indices representing the initial tour (e.g., [1, 2, 3, 1]).
        dist_matrix: Distance matrix where dist_matrix[i-1][j-1] is the distance from city i to j.
    
    Returns:
        Tuple of (optimized tour, tour length).
    """
    n = len(tour) - 1  # Number of cities excluding the duplicate endpoint (e.g., 14 for burma14.tsp)
    best_tour = tour[:]
    best_length = path_length(tsp, best_tour)
    improved = True

    while improved:
        improved = False
        for i in range(1, n - 4):  # Adjusted to ensure enough space for j and k
            for j in range(i + 2, n - 2):  # Adjusted to ensure k can be at least j+2
                for k in range(j + 2, n):  # Stop at n-1 to avoid out-of-range
                    # Define the six vertices involved in the 3-opt move
                    a, b = tour[i - 1], tour[i]      # Edge (a, b) at position i-1 to i
                    c, d = tour[j - 1], tour[j]      # Edge (c, d) at position j-1 to j
                    e, f = tour[k - 1], tour[k]      # Edge (e, f) at position k-1 to k

                    # Original distance of the three edges to remove
                    orig_dist = (dist_matrix[a-1, b-1] + dist_matrix[c-1, d-1] + dist_matrix[e-1, f-1])

                    # Case 1: a-d-e-b-c-f (pure 3-opt move)
                    new_dist1 = (dist_matrix[a-1, d-1] + dist_matrix[e-1, b-1] + dist_matrix[c-1, f-1])
                    if new_dist1 < orig_dist:
                        new_tour = tour[:i] + tour[j-1:k-1:-1] + tour[i:j] + tour[k:]
                        best_tour = new_tour
                        best_length = path_length(tsp, best_tour)
                        improved = True
                        break

                    # Case 2: a-b-e-d-c-f (includes a 2-opt move)
                    new_dist2 = (dist_matrix[a-1, b-1] + dist_matrix[e-1, d-1] + dist_matrix[c-1, f-1])
                    if new_dist2 < orig_dist:
                        new_tour = tour[:i] + tour[j:k] + tour[i:j] + tour[k:]
                        best_tour = new_tour
                        best_length = path_length(tsp, best_tour)
                        improved = True
                        break

                    # Case 3: a-d-c-b-e-f (includes a 2-opt move)
                    new_dist3 = (dist_matrix[a-1, d-1] + dist_matrix[c-1, b-1] + dist_matrix[e-1, f-1])
                    if new_dist3 < orig_dist:
                        new_tour = tour[:i] + tour[j-1:i-1:-1] + tour[k-1:j-1:-1] + tour[k:]
                        best_tour = new_tour
                        best_length = path_length(tsp, best_tour)
                        improved = True
                        break

                    # Case 4: a-f-c-d-e-b (pure 3-opt move with different reversal)
                    new_dist4 = (dist_matrix[a-1, f-1] + dist_matrix[c-1, d-1] + dist_matrix[e-1, b-1])
                    if new_dist4 < orig_dist:
                        new_tour = tour[:i] + tour[k-1:j-1:-1] + tour[j:i:-1] + tour[k:]
                        best_tour = new_tour
                        best_length = path_length(tsp, best_tour)
                        improved = True
                        break

                if improved:
                    break
            if improved:
                break
        if improved:
            tour = best_tour[:]

    return best_tour, best_length

# === FuzzOpt heuristic ===
def fuzzopt(tsp, max_iterations: Optional[int] = None, use_three_opt: bool = False):
    """
    FuzzOpt iterative local search heuristic for TSP with optional 3-opt.
    Returns (tour_length, tour_list), where tour_list is a sequence of 1-based city indices.
    """
    n = tsp["DIMENSION"]
    dist = lambda i, j: distance(tsp["CITIES"][i-1], tsp["CITIES"][j-1])

    # Create distance matrix
    distance_matrix = np.zeros((n, n))
    for i in range(1, n+1):
        for j in range(1, n+1):
            distance_matrix[i-1, j-1] = dist(i, j)

    # Initialize random tour starting and ending at city 1
    x = [1] + list(np.random.permutation(list(range(2, n+1)))) + [1]
    fx = path_length(tsp, x)
    max_iterations = max_iterations or n

    # Choose local search method
    local_search = three_opt if use_three_opt else two_opt

    for iteration in range(max_iterations):
        # Create a perturbed tour by swapping two random cities (excluding start/end)
        xn = x[:]
        u, v = randint(1, n-1), randint(1, n-1)
        while u == v:
            v = randint(1, n-1)
        xn[u], xn[v] = xn[v], xn[u]

        # Apply chosen local search to the perturbed tour
        xn, fn = local_search(tsp, xn, distance_matrix)

        if fn < fx:
            x = xn[:]
            fx = fn

    return fx, x
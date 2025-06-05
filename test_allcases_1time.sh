#!/bin/bash

# Directory containing TSP files
TSP_DIR="./tspfiles"

# Output file for results
OUTPUT_FILE="tsp_results_$(date +%Y%m%d_%H%M%S).txt"

# Algorithms ordered from fastest to slowest
ALGORITHMS=(
    "-approx-mst:MST-Preorder"
    "-christofides:Christofides"
    "-fuzzopt-2opt:FuzzOpt-2opt"
    # "-fuzzopt-3opt:FuzzOpt-3opt"
    "-held-karp:Held-Karp"
)

# Time limits (in seconds) based on approximate file size/city count
declare -A TIME_LIMITS=(
    ["a280.tsp"]=30
    ["berlin52.tsp"]=12
    ["burma14.tsp"]=10
    ["eil51.tsp"]=10
    ["eil76.tsp"]=50
    ["eil101.tsp"]=100
    ["kroA150.tsp"]=800
    ["kz9976.tsp"]=400
    ["mona-lisa100K.tsp"]=1
    ["ulysses16.tsp"]=10
    ["ulysses22.tsp"]=100
    ["xql662.tsp"]=5
)

# Check if TSP directory exists
if [ ! -d "$TSP_DIR" ]; then
    echo "Error: Directory $TSP_DIR does not exist."
    exit 1
fi

# Clear the output file if it exists, or create a new one
echo "TSP Test Results - $(date '+%Y-%m-%d %I:%M %p KST')" > "$OUTPUT_FILE"
echo "===================================" >> "$OUTPUT_FILE"
echo "File | Algorithm | Tour Length | Execution Time (seconds)" >> "$OUTPUT_FILE"
echo "-----|-----------|-------------|--------------------------" >> "$OUTPUT_FILE"

# Get list of TSP files sorted by size
TSP_FILES=($(ls -lS "$TSP_DIR"/*.tsp 2>/dev/null | awk '{print $9}' | sort -k1))
if [ ${#TSP_FILES[@]} -eq 0 ]; then
    echo "No .tsp files found in $TSP_DIR"
    exit 1
fi

# Iterate over TSP files in size order
for tsp_file in "${TSP_FILES[@]}"; do
    tsp_name=$(basename "$tsp_file" .tsp)
    echo "Testing $tsp_name (file: $tsp_file)"

    # Determine time limit based on file name with debug
    TIME_LIMIT=${TIME_LIMITS["$tsp_name.tsp"]}
    if [ -z "$TIME_LIMIT" ]; then
        TIME_LIMIT=30  # Default time limit for unlisted files
        echo "Warning: No specific time limit for $tsp_name, using default $TIME_LIMIT seconds"
    else
        echo "Using time limit $TIME_LIMIT seconds for $tsp_name"
    fi

    # Test each algorithm on the current TSP file
    for alg in "${ALGORITHMS[@]}"; do
        # Split algorithm flag and name
        IFS=':' read -r flag alg_name <<< "$alg"

        # Run the algorithm with timeout and capture output and time
        TIME_OUTPUT=$(mktemp)
        OUTPUT=$( { timeout "$TIME_LIMIT"s /usr/bin/time -f "%e" -o "$TIME_OUTPUT" python3 main.py "$flag" "$tsp_file" 2>/dev/null; } 2>&1 )
        EXEC_TIME=$(cat "$TIME_OUTPUT")
        rm "$TIME_OUTPUT"

        # Extract tour length using a regular expression to capture the number after "tour length ="
        TOUR_LENGTH=$(echo "$OUTPUT" | grep -o "tour length = [0-9]*" | sed 's/tour length = //')

        # Handle timeout or failure
        if [ -z "$TOUR_LENGTH" ]; then
            TOUR_LENGTH="Timeout"
            EXEC_TIME="$TIME_LIMIT"
            echo "Warning: $alg_name on $tsp_name timed out or failed after $TIME_LIMIT seconds"
        fi

        # Append results to the output file
        printf "%s | %s | %s | %s\n" "$tsp_name" "$alg_name" "$TOUR_LENGTH" "$EXEC_TIME" >> "$OUTPUT_FILE"
    done
done

echo "Testing complete. Results saved to $OUTPUT_FILE"
echo "Displaying results:"
cat "$OUTPUT_FILE"
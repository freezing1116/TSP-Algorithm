#!/bin/bash

# Directory containing TSP files
TSP_DIR="./tspfiles"

# Output file for results with timestamp
OUTPUT_FILE="./tsp_test_results_$(date +%Y%m%d_%H%M%S).txt"

# Check if algorithm flag and tsp file are provided as arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <algorithm_flag> <tsp_file>"
    echo "Example: $0 -approx-mst burma14.tsp"
    exit 1
fi

ALGORITHM_FLAG="$1"
TSP_FILE="$TSP_DIR/$2.tsp"

# Validate TSP file
if [ ! -f "$TSP_FILE" ]; then
    echo "Error: File $TSP_FILE does not exist."
    exit 1
fi

# Extract tsp name without path and extension
TSP_NAME=$(basename "$TSP_FILE" .tsp)

# Time limits (use the existing TIME_LIMITS array for consistency)
declare -A TIME_LIMITS=(
    ["a280.tsp"]=1500
    ["berlin52.tsp"]=12
    ["burma14.tsp"]=10
    ["eil51.tsp"]=10
    ["eil76.tsp"]=50
    ["eil101.tsp"]=100
    ["kroA150.tsp"]=800
    ["kz9976.tsp"]=1000
    ["mona-lisa100K.tsp"]=1
    ["ulysses16.tsp"]=10
    ["ulysses22.tsp"]=1000
    ["xql662.tsp"]=5
)

# Set time limit based on file name
TIME_LIMIT=${TIME_LIMITS["$TSP_NAME.tsp"]}
if [ -z "$TIME_LIMIT" ]; then
    TIME_LIMIT=30  # Default time limit for unlisted files
    echo "Warning: No specific time limit for $TSP_NAME, using default $TIME_LIMIT seconds"
else
    echo "Using time limit $TIME_LIMIT seconds for $TSP_NAME"
fi

# Clear the output file or create a new one
echo "TSP Test Results - $(date '+%Y-%m-%d %I:%M %p KST')" > "$OUTPUT_FILE"
echo "===================================" >> "$OUTPUT_FILE"
echo "File: $TSP_NAME, Algorithm: $ALGORITHM_FLAG" >> "$OUTPUT_FILE"
echo "Run | Tour Length | Execution Time (seconds)" >> "$OUTPUT_FILE"
echo "---|-------------|--------------------------" >> "$OUTPUT_FILE"

# Variables to store sums for averaging
TOTAL_TOUR_LENGTH=0
TOTAL_EXEC_TIME=0

# Run the algorithm 10 times
for RUN in {1..10}; do
    echo "Running test $RUN..."

    # Run the algorithm with timeout and capture output and time
    TIME_OUTPUT=$(mktemp)
    OUTPUT=$( { timeout "$TIME_LIMIT"s /usr/bin/time -f "%e" -o "$TIME_OUTPUT" python3 main.py "$ALGORITHM_FLAG" "$TSP_FILE" 2>/dev/null; } 2>&1 )
    EXEC_TIME=$(cat "$TIME_OUTPUT")
    rm "$TIME_OUTPUT"

    # Extract tour length using a regular expression
    TOUR_LENGTH=$(echo "$OUTPUT" | grep -o "tour length = [0-9]*" | sed 's/tour length = //')

    # Handle timeout or failure
    if [ -z "$TOUR_LENGTH" ]; then
        TOUR_LENGTH="Timeout"
        EXEC_TIME="$TIME_LIMIT"
        echo "Warning: Run $RUN timed out or failed after $TIME_LIMIT seconds"
    fi

    # Append results to the output file
    printf "%d | %s | %s\n" "$RUN" "$TOUR_LENGTH" "$EXEC_TIME" >> "$OUTPUT_FILE"

    # Add to totals for averaging (convert to 0 if Timeout to avoid skewing)
    if [ "$TOUR_LENGTH" != "Timeout" ]; then
        TOTAL_TOUR_LENGTH=$((TOTAL_TOUR_LENGTH + TOUR_LENGTH))
        TOTAL_EXEC_TIME=$(echo "$TOTAL_EXEC_TIME + $EXEC_TIME" | bc)
    fi
done

# Calculate averages (avoid division by zero)
NUM_SUCCESSFUL=$((10 - $(grep -c "Timeout" "$OUTPUT_FILE")))
if [ $NUM_SUCCESSFUL -gt 0 ]; then
    AVG_TOUR_LENGTH=$((TOTAL_TOUR_LENGTH / NUM_SUCCESSFUL))
    AVG_EXEC_TIME=$(echo "scale=4; $TOTAL_EXEC_TIME / $NUM_SUCCESSFUL" | bc)
else
    AVG_TOUR_LENGTH="N/A"
    AVG_EXEC_TIME="N/A"
fi

# Append summary to the output file
echo "===================================" >> "$OUTPUT_FILE"
echo "Summary for $TSP_NAME with $ALGORITHM_FLAG" >> "$OUTPUT_FILE"
echo "Number of Successful Runs: $NUM_SUCCESSFUL" >> "$OUTPUT_FILE"
echo "Average Tour Length: $AVG_TOUR_LENGTH" >> "$OUTPUT_FILE"
echo "Average Execution Time: $AVG_EXEC_TIME seconds" >> "$OUTPUT_FILE"

echo "Testing complete. Results saved to $OUTPUT_FILE"
echo "Displaying results:"
cat "$OUTPUT_FILE"
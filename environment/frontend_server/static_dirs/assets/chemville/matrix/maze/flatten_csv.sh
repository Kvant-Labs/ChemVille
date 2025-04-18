#!/bin/bash

# Check for input file argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 input.csv"
  exit 1
fi

input_file="$1"
temp_file="$(mktemp)"

# Flatten the CSV into a single line
tr '\n' ',' < "$input_file" | sed 's/,$/\n/' > "$temp_file"

# Overwrite the original file with the flattened version
mv "$temp_file" "$input_file"

echo "Flattened CSV written in-place to: $input_file"

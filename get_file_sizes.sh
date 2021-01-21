#!/bin/bash

# Expects a file with no header and just a list of files, one per row, such as that produced by index_workspace.py
# Produces a comma delimited file with byte size in the first column and file name in the second
# This may take several minutes to run (10+) depending on how many files you are looking at

INPUT=$1
OUTPUT=$2
N=1000

cat "$INPUT" | xargs -L "$N" gsutil du -s | sed 's/ //g' | sed 's/gs:/,gs:/g' >> "$OUTPUT"

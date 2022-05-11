#!/bin/bash

# Given a gsutil copy log (comma delimited, .csv), copy the DESTINATION file to the SOURCE location

INPUT_COPY_LOG=$1
OUTPUT_PREFIX=$2
OUTPUT_FILE="$OUTPUT_PREFIX".restored.csv

sed 1d "$INPUT_COPY_LOG" | while IFS=, read -r source destination _ _ _ _ _ _ _ _ || [ -n "$source" ];
do
  gsutil cp -L "$OUTPUT_FILE" "$destination" "$source"
done

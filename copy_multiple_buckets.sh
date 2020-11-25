#!/bin/bash

# This script is a combination of copy_bucket.sh, list_source_files.py, and remove_files.sh.
# Logs are then copied to the source bucket
# Inputs should be tab delimited text files with four columns:
# source_bucket destination_bucket  workspace_namespace workspace_name
# Make sure that there is an empty line at the end if you don't create the list with list_workspaces_to_archive.py

# Source workspaces should be commented afterwards with
# Archived to {destinaton path} under {google billing project or server} on {month} {day}, {year}.
# And tagged with "archived"

ARCHIVE_LIST=$1
prefix=gs://


while read -r source_bucket destination_bucket workspace_namespace workspace_name; do
  echo "$source_bucket" "$destination_bucket" "$workspace_namespace" "$workspace_name"
  source=${source_bucket//$prefix/}
  destination=${destination_bucket//$prefix/}
  log_prefix="$source-to-$destination"
  log="$log_prefix".gsutil_copy_log.csv
  files_to_remove="$workspace_namespace"."$workspace_name".files_to_remove.txt

  bash copy_bucket.sh "$source_bucket" "$destination_bucket"
  python list_source_files.py --input "$log" --output "$workspace_namespace.$workspace_name"
  bash remove_files.sh "$files_to_remove"
  gsutil -m cp "$log" "$files_to_remove" gs://"$source"

  if gsutil ls gs://"$source"/"$log" | grep -q "$log"; then rm "$log"; fi
  if gsutil ls gs://"$source"/"$files_to_remove" | grep -q "$log"; then rm "$files_to_remove"; fi

done < "$ARCHIVE_LIST"

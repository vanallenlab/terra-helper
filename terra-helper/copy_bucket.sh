#!/bin/bash

SOURCE=$1
DESTINATION=$2

# Copy SOURCE bucket to DESTINATION bucket
# A folder of name SOURCE will appear in DESTINATION's root directory, wherein remaining structure is mirrored
# A log is produced named {SOURCE}-to-{DESTINATION}.gsutil_copy_log.csv

prefix=gs://
source=${SOURCE//$prefix/}
destination=${DESTINATION//$prefix/}
log_prefix="$source-to-$destination"
log_prefix_slash_removed="${log_prefix/\//.}"
log="$log_prefix_slash_removed".gsutil_copy_log.csv

gsutil -m cp -L "$log" -r gs://"$source" gs://"$destination"

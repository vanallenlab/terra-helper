#!/bin/bash

SOURCE=$1
WORKSPACE_BUCKET=$2

# Copy SOURCE bucket to DESTINATION bucket
# A folder of name SOURCE will appear in DESTINATION's root directory, wherein remaining structure is mirrored
# A log is produced named {SOURCE}-to-{DESTINATION}.gsutil_copy_log.csv

prefix=gs://
source=${SOURCE//$prefix/}
workspace_bucket=${WORKSPACE_BUCKET//$prefix/}
log_prefix="$workspace_bucket-from-$source"
log="$log_prefix".gsutil_copy_log.csv

gsutil -m cp -L "$log" -r gs://"$source"/"$workspace_bucket"/* gs://"$workspace_bucket"

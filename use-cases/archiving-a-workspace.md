# Archiving a workspace
Archiving uses the same code as [moving a bucket](moving-a-bucket.md), but you *must* use the `copy_bucket.sh` script. 

# Restoring a workspace
The script `restore_bucket.sh` can be used to restore your workspace's bucket, or really any Google bucket, to the original location. This script assumes that `copy_bucket.sh` was used. The gsutil copy log will be produced and named as `{SOURCE}-from-{DESTINATION}.gsutil_copy_log.csv`. Archived versions of data should be removed using `list_source_files.py` and `remove_files.sh`, if desired. 

Required arguments:
```bash
    SOURCE                  <string>    Source Google bucket, with or without the gs:// prefix
    WORKSPACE_BUCKET        <string>    Google bucket of the Terra workspace, with or without the gs:// prefix
```

## Example
`vanallen-firecloud-dfci/MEGA_MEL2` (`gs://fc-d9e5d8f2-df1f-42c7-b51c-3ef20b46425c`) was archived from the multi-regional, Terra storage to regional, archive storage `terra-workspace-archive-us-central1/fc-d9e5d8f2-df1f-42c7-b51c-3ef20b46425c/` by using the `copy_bucket.sh`. This workspace contained 100,606 files that totaled to 17.4 TB of data. To move the files back, `restore_bucket.sh` is used.
```bash
bash restore_bucket.sh terra-workspace-archive-us-central1 fc-d9e5d8f2-df1f-42c7-b51c-3ef20b46425c
```

The gsutil cp log is written to `fc-d9e5d8f2-df1f-42c7-b51c-3ef20b46425c-from-terra-workspace-archive-us-central1.gsutil_copy_log.csv`. To delete the archived version of the data based on the copy, use `list_source_files.py` and `remove_files.sh` as done explained in [moving a bucket](moving-a-bucket.md).

Please keep in mind that there are [network and operational costs](https://cloud.google.com/storage/pricing#network-pricing) associated with moving data, especially across regions. There are also [retrieval and early deletion costs](https://cloud.google.com/storage/pricing#archival-pricing) associated with accessing data.

# Archiving many workspaces
The script `copy_multiple_buckets.sh` can be used to copy multiple buckets to a specific destination. The script calls copy_bucket.sh, list_sources.py, and remove_files.sh. The input is a tab delimited file that lists the source bucket, destination bucket, workspace namespace, and workspace name. This file can be created with the `list_workspaces_to_archive.py` script, which formats an input for this script based on workspaces with a common tag. Logs are copied to the source bucket but the source workspace should be commented and tagged with "archive".

Required arguments:
``bash
    ARCHIVE_LIST        <file>  Tab delimited file of source bucket, destination bucket, source workspace namespace, source workspace name. Leave an empty line at the end.
``

The script `list_workspaces_to_archive.py` can generate an input for this script based on workspaces with a common tag. The same destination is set for all workspaces with this script.

Required arguments:
``bash
    --tag, -t           <string>    Tag of Terra workspaces to list
    --destination, -d   <string>    Google bucket or path to copy workspace buckets to
    --output, -o        <string>    Output handle name
``

## Example
The following example is for copying all workspaces tagged as `archive` to the Google bucket `terra-workspace-archive-us-central1`,
```bash
python list_workspaces_to_archive.py --tag archive --destination terra-workspace-archive-us-central1 --output buckets_to_move.txt
bash copy_multiple_buckets.sh buckets_to_move.txt
```

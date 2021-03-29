# Table of Contents
- [copy_bucket.sh](#copy_bucketsh)
- [copy_bucket-mirror.sh](#copy_bucket-mirrorsh)
- [copy_multiple_buckets.sh](#copy_multiple_bucketssh)
- [downloader.py](#downloaderpy)
- [estimate_archive_and_retrieval_costs.py](#estimate_archive_and_retrieval_costspy)
- [get_file_sizes.sh](#get_file_sizessh)
- [index_workspace.py](#index_workspacepy)
- [list_source_files.py](#list_source_filespy)
- [list_workspaces_to_archive.py](#list_workspaces_to_archivepy)
- [remove_files.sh](#remove_filessh)
- [restore_bucket.sh](#restore_bucketsh)

## copy_bucket.sh
`copy_bucket.sh` will copy the contents of one bucket to another. Contents of the source bucket will be placed in folder named after the source bucket within the destination bucket, with folder structure mirrored. Specifically, the following will result in passing `fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af` as a source bucket and `terra-workspace-archive-us-central1` as the destination bucket:

|Source|Destination|
|---|---|
|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|gs://terra-workspace-archive-us-central1/fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|
|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|gs://terra-workspace-archive-us-central1/fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|

### Usage
Required arguments:
```bash
    SOURCE                  <string>    Source Google bucket, with or without the gs:// prefix
    DESTINATION             <string>    Destination Google bucket, with or without the gs:// prefix
```

Outputs produced:

|File name|Description|
|---|---|
|`{SOURCE}-to-{DESTINATION}.gsutil_copy_log.csv`|A comma delimited file with the status and byte size of all files that gsutil attempted to copy.|

Example:
```bash
bash copy_bucket.sh fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af terra-workspace-archive-us-central1
```

[Back to table of contents](#table-of-contents)

## copy_bucket-mirror.sh
`copy_bucket-mirror.sh` will copy the contents of one bucket to another. Contents of the source bucket will be copied to the root folder of the destination bucket, with folder structure mirrored. Specifically, the following will result in passing `fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af` as a source bucket and `terra-workspace-archive-us-central1` as the destination bucket:

|Source|Destination|
|---|---|
|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|gs://terra-workspace-archive-us-central1/stuff.md|
|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|gs://terra-workspace-archive-us-central1/subfolder/other_stuff.md|

### Usage
Required arguments:
```bash
    SOURCE                  <string>    Source Google bucket, with or without the gs:// prefix
    DESTINATION             <string>    Destination Google bucket, with or without the gs:// prefix
```

Outputs produced:

|File name|Description|
|---|---|
|`{SOURCE}-to-{DESTINATION}.gsutil_copy_log.csv`|A comma delimited file with the status and byte size of all files that gsutil attempted to copy.|

Example:
```bash
bash copy_bucket-mirror.sh fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af terra-workspace-archive-us-central1
```

[Back to table of contents](#table-of-contents)

## copy_multiple_buckets.sh
`copy_multiple_buckets.sh` is used to copy multiple buckets to a specific destination. The script calls `copy_bucket.sh`, `list_source_files.py`, and `remove_files.sh`. The input is a tab delimited file that lists the source bucket, destination bucket, workspace namespace, and workspace name. This file can be created with the `list_workspaces_to_archive.py` script, which formats an input for this script based on workspaces with a common tag. Logs are copied to the source bucket; however, the source workspace should also be commented and tagged with "archive". See [archiving a workspace](use-cases/archiving-a-workspace.md) for more details.

### Usage
Required arguments:
```bash
    ARCHIVE_LIST          <string>    Tab delimited file of source bucket, destination bucket, source workspace namespace, source workspace name. Leave an empty line at the end.
```

Outputs produced:
This script will copy logs and produced outputs to the source and destination buckets. If successfully copied to the source, they will be removed locally. 

Example
```bash
bash copy_multiple_buckets.sh buckets_to_move.txt
```
where `buckets_to_move` may be produced by `list_workspaces_to_archive.py`.

[Back to table of contents](#table-of-contents)

## downloader.py
`downloader.py` will download items in a data model column, written to a folder named the same as the specified column.

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
    --entity_type           <string>    Entity type, or table, in the datamodel
    --column                <string>    Column name for download
```

Example:
In this example, we download the column oncotated_maf from the workspace my-test-namespace/my-test-workspace from the pair table.
```bash
python downloader.py --namespace my-test-namespace --workspace --my-test-workspace --entity_type pair --column oncotated_maf
```

[Back to table of contents](#table-of-contents)

## estimate_archive_and_retrieval_costs.py
`estimate_archive_and_retrieval_costs.py` is used to calculate the cost-effectiveness of _moving data out of_ and _returning it_ to Terra, given how many days a workspace and its underlying data remains inactive and not accessed. We calculate the number of days required for each location and storage type available on Google Cloud to be more cost effective than just leaving the data in Terra, which uses the most expensive storage (US multi regional, standard) and does not allow users to take advantage of Google's lifecycle policies. See [this slideshow](https://docs.google.com/presentation/d/1y_KxBDum8xNs89llKkdn6bgieBjgSuI3qP7P-Xdeo9A/edit?usp=sharing) for more information.

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
```

Optional arguments:
```bash
    --print                 <boolean>   boolean flag to print information for a workspace
```

Outputs produced:
See [this slideshow for more information](https://docs.google.com/presentation/d/1y_KxBDum8xNs89llKkdn6bgieBjgSuI3qP7P-Xdeo9A/edit?usp=sharing). In short, two excels documents are produced which contain the following sheets:
- Output named `{namespace}.{name}.cost_estimates.xlsx`
  - Workspace information, metadata for the workspace such as bucket size and monthly costs
  - Recommendations, recommended (most cost effective) location and storage type and cost savings relative to Terra for a set of days [7, 15, 30, 45, ...]
  - Intersections, how many days inactive are required for each location and storage type to be cost effective relative to Terra
- Output named `{namespace}.{name}.cost_estimates.full.xlsx`
  - Workspace information, metadata for the workspace such as bucket size and monthly costs
  - Recommendations, recommended (most cost effective) location and storage type and cost savings relative to Terra for a set of days [7, 15, 30, 45, ...]
  - Intersections, how many days inactive are required for each location and storage type to be cost effective relative to Terra
  - Storage costs, monthly and daily cost to storage the provided workspace's data in each location and storage type 
  - Network costs, network costs incurred by moving this workspace's data across locations in Google Cloud
  - Retrieval costs, retrieval costs incurred by accessing this data per storage type
  - Class A operation gsutil cp, costs for running gsutil cp for all files (or all files without logs) within this bucket
  - Fees, a summary of fees incurred for moving this bucket out of Terra and back into Terra
  - monthly storage costs, monthly storage costs for just data storage of this workspace bucket by location and storage type
  - daily storage costs, daily storage costs for just data storage of this workspace bucket by location and storage type
  - daily storage costs adjusted for minimum duration, daily storage costs for just data storage of this workspace bucket by location and storage type adjusted for minimum duration required for storage types
  - daily storage costs adjusted for minimum duration and fees, daily storage costs for just data storage of this workspace bucket by location and storage type adjusted for minimum duration required for storage types and fees incurred for moving data from and return to Terra

Example:
```bash
python estimate_archive_and_retrieval_costs.py --namespace vanallen-firecloud-nih --name Robinson2015_dev-MOVED
```

[Back to table of contents](#table-of-contents)

## get_file_sizes.sh
`get_file_sizes.sh` anticipates a file with no header or index, just a single list of file paths on google cloud storage, with one file per row; such as that produced by `index_workspace.py`. This script will produce a comma delimited file with byte size of each file in the first column, and the file name in the second column. This may take several minutes to depending on how many files are being passed. By default, chunks of 1000 files are processed at once.

### Usage
Required arguments:
```bash
    INPUT                  <string>   List of files on Google Cloud storage, one file per row with no header or index. 
    OUTPUT                 <string>   Output filename
```

Optional arguments:
```bash
    N                      <int>      Chunksize, number of files to annotate at once. Default: 1000
```

Outputs produced:

|File name|Description|
|---|---|
|{OUTPUT}|A comma delimited file with byte size of each column in the first column and file name and path in the second.|

Example:
```bash
bash get_file_sizes.sh vanallen-firecloud-nih.2014-Perry-MOAlmanac.files_to_remove.txt vanallen-firecloud-nih.2014-Perry-MOAlmanac.files_to_remove.annotated.txt
```

[Back to table of contents](#table-of-contents)

## index_workspace.py
`index_workspace.py` will retrieve the bucket and all bucket contents associated with passed workspace, pull all elements in the datamodel and workspace annotations, and  take the difference. If `--keep_related_files` is passed, any files in the same directory as either one in the datamodel or workspace annotations will also be kept, such as the associated sterr and stdout from any jobs. The argument `--keep` can be passed any number of times to prevent files of a given suffix to be added to the remove list. By default, files of the suffix `.ipynb` will be excluded.

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
```

Optional arguments:
```bash
    --keep_related_files    <boolean>   Boolean for keeping all contents for folders in data model
    --keep, -k              <string>    File suffix to keep, can pass multiple times
```

Outputs produced:

|File name|Description|
|---|---|
|{namespace}.{name}.datamodel_not_paths.txt|Elements in the workspace data model or workspace annotations that are not file paths.|
|{namespace}.{name}.files_keep.txt|Files that are present in, or related to files in, the data model or workspace annotations.|
|{namespace}.{name}.files_to_remove.txt|Files which are not present in the data model or workspace annotations and were not flagged to be kept.|
|{namespace}.{name}.files_to_remove.no_logs.txt|Likely the main output used. A subset of files_to_remove.txt, without any associated logs.|

Example:
```bash
python index_workspace.py --namespace vanallen-firecloud-dfci --name Robinson2015_dev --keep_related_files --keep bam --keep bai
```

[Back to table of contents](#table-of-contents)

## list_source_files.py
`list_source_files.py` lists the path of files successfully copied by gsutil cp, by specifically identifying rows for which `Status == OK` and returning the path listed under `Source`. A file with no header or index which lists one file per row is returned.

### Usage
Required arguments:
```bash
    --input, -i             <string>    Log from gsutil cp
    --output, -o            <string>    Prefix name of output file
```

Outputs produced:

|File name|Description|
|---|---|
|{output}.files_to_remove.txt|List of files which were successfully copied to the destination, one per row.|

Example:
```bash
python list_source_files.py --input fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv --output fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af
```

[Back to table of contents](#table-of-contents)

## list_workspaces_to_archive.py
`list_workspaces_to_archive.py` can generate an input for `copy_multiple_buckets.sh` based on a common tag in Terra. The same destination is set for all workspaces listed.

### Usage
Required arguments:
```bash
    --tag, -t           <string>    Tag of Terra workspaces to list
    --destination, -d   <string>    Google bucket or path to copy workspace buckets to
    --output, -o        <string>    Output handle name
```

Outputs produced:

|File name|Description|
|---|---|
|{output}|A tab delimited file that lists the source bucket, destination bucket, workspace namespace, and workspace name is generated. There is no header for this file.|

Example:
```bash
python list_workspaces_to_archive.py --tag archive --destination terra-workspace-archive-us-central1 --output buckets_to_move.txt
```

[Back to table of contents](#table-of-contents)

## remove_files.sh
`remove_files.sh` will run gsutil rm on provided list of files. **It is not possible to restore deleted files**, and it is recommended that you **manually review** files before using this script. The input file should be a text file listing one file on google cloud per row, with no header or index. You will be able to watch the progress of your files being deleted.

### Usage
Required arguments:
```bash
    HANDLE                  <string>    File path to list of files for removal
```

Example:
```bash
bash remove_files.sh vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt
```

[Back to table of contents](#table-of-contents)

## restore_bucket.sh
`restore_bucket.sh` is used to restore a workspace's bucket, or any Google bucket, to the original location. This script assumes that `copy_bucket.sh` was used. 
For example, the following will result by passing `terra-workspace-archive-us-central1` as a source bucket and `fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af` as a workspace bucket:

|Source|Destination|
|---|---|
|gs://terra-workspace-archive-us-central1/fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|
|gs://terra-workspace-archive-us-central1/fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|

### Usage
Required arguments:
```bash
    SOURCE                  <string>    Source Google bucket, with or without the gs:// prefix
    WORKSPACE_BUCKET        <string>    Google bucket of the Terra workspace, with or without the gs:// prefix
```

Outputs produced:

|File name|Description|
|---|---|
|`{SOURCE}-from-{DESTINATION}.gsutil_copy_log.csv`|A comma delimited file with the status and byte size of all files that gsutil attempted to copy.|

Example:
```bash
bash restore_bucket.sh terra-workspace-archive-us-central1 fc-d9e5d8f2-df1f-42c7-b51c-3ef20b46425c
```

[Back to table of contents](#table-of-contents)

# Terra helper
Run scripts from this directory. The table of contents contains a hyperlink to all scripts contained in this directory. Additional documentation for use cases can be found in the [docs/ folder](../docs/).

# Table of contents
- [copy_bucket.sh](#copy_bucketsh)
- [copy_bucket-mirror.sh](#copy_bucket-mirrorsh)
- [copy_multiple_buckets.sh](#copy_multiple_bucketssh)
- [create_workspace.py](#create_workspacepy)
- [downloader.py](#downloaderpy)
- [download_entity_table.py](#download_entity_tablepy)
- [estimate_archive_and_retrieval_costs.py](#estimate_archive_and_retrieval_costspy)
- [get_file_sizes.sh](#get_file_sizessh)
- [get_workspace_attributes.py](#get_workspace_attributespy)
- [get_workspace_bucket_contents.py](#get_workspace_bucket_contentspy)
- [identify_files_manually_clean_workspace.py](#identify_files_manually_clean_workspacepy)
- [list_source_files.py](#list_source_filespy)
- [list_workspaces.py](#list_workspacespy)
- [list_workspaces_to_archive.py](#list_workspaces_to_archivepy)
- [remove_files.sh](#remove_filessh)
- [restore_bucket.sh](#restore_bucketsh)
- [restore_files.sh](#restore_filessh)

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

## create_workspace.py
`create_workspace.py` is used to create **single region** workspaces on Terra. As of this writing, single region buckets cannot be created within Terra and all buckets are by default US. In addition, the API endpoint currently does not support setting the bucket location to a multi region location, such as US. Terra uses US-CENTRAL1 virtual machines so our lab will use US-CENTRAL1 buckets. Running a workflow on a VM not in US-CENTRAL1 with your bucket in another region will incur **significant** charges on the lab's behalf. **Please do not change the region unless you have talked to Jihye and Brendan and know what you are doing**.

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
```

Optional arguments:
```bash
    --location              <string>    Workspace bucket location on Google Cloud. Choices: [US-CENTRAL1]
    --authorization         <string>    Authorization domain name associated with the workspace (e.g. TCGA-dbGaP-Authorized, vanallenlab). Default: None
```

Example:
We create a workspace in the vanallen-firecloud-nih namespace called test-workspace under the TCGA authorization domain. Generally, we recommend **not** using an authorization domain. 
```bash
python create_workspace.py --namespace vanallen-firecloud-nih --name test-workspace --authorization TCGA-dbGaP-Authorized
```

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

## download_entity_table.py
`download_entity_table.py` will download entity table(s) from the data models of specified workspace(s).

### Usage, single table download
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
    --entity_type           <string>    Entity type, or table, in the datamodel
```

Example:
In this example, we download the pair table from the workspace my-test-namespace/my-test-workspace.
```bash
python download_entity_table.py --namespace my-test-namespace --workspace --my-test-workspace --entity_type pair
```

### Usage, multiple table download
Required arguments:
```bash
    --tsv                   <string>    tab delimited file of multiple tables to download
```

A provided tab delimited file should be structured as follows to download multiple entity tables,
|namespace|name|entity_type|
|---|---|---|
|`workspace_namespace`|`workspace_name`|`entity_type`|
|`workspace_namespace`|`workspace_name`|`entity_type`|

Example:
In this example, we download the pair table from the workspace my-test-namespace/my-test-workspace and the sample_set table from the workspace my-test-namespace/my-test-workspace-2

Input file called `tables_to_download.tsv`,
|namespace|name|entity_type|
|---|---|---|
|my-test-namespace|my-test-workspace|pair|
|my-test-namespace|my-test-workspace-2|sample_set|

```bash
python download_entity_table.py --tsv tables_to_download.tsv
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
bash get_file_sizes.sh vanallen-firecloud-nih.2014-Perry-MOAlmanac.files_to_remove.txt vanallen-firecloud-nih.2014-Perry-MOAlmanac.files_to_remove.annotated.csv
```

[Back to table of contents](#table-of-contents)

## get_workspace_attributes.py
`get_workspace_attributes.py` will list all attributes listed within a given workspace, which consists of all elements under all entity and workspace tables under  `Data` tab in a workspace. 

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
```

Outputs produced:

| File name                                      | Description                                              |
|------------------------------------------------|----------------------------------------------------------|
| {namespace}.{name}.attributes.tsv              | All workspace attributes listed in a tab-delimited table |

Example:
```bash
python get_workspace_attributes.py --namespace vanallen-firecloud-nih --name ovarian-9825
```

[Back to table of contents](#table-of-contents)

## get_workspace_bucket_contents.py
`get_workspace_bucket_contents.py` will list all files within a workspace's bucket. This python script fetches the bucket name and essentially runs `gsutil ls gs://{bucket_name}/**`.

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
```

Outputs produced:

| File name                              | Description                                |
|----------------------------------------|--------------------------------------------|
| {namespace}.{name}.bucket_contents.tsv | All files present in a workspace's bucket. |

Example:
```bash
python get_workspace_bucket_contents.py --namespace vanallen-firecloud-nih --name ovarian-9825
```

[Back to table of contents](#table-of-contents)

## identify_files_manually_clean_workspace.py
`identify_files_manually_clean_workspace.py` is a script which will identify files that are present in a workspace's google cloud bucket that are _not_ in the workspace's data model, and nominate such files for removal. Additional criteria is considered: 
- Logs and system files from cromwell are retained
- File types can be safe listed to ensure that none of them are removed; e.g. bams 
- Users can specify to only consider files generated from method submissions

This is accomplished by utilizing bucket contents and workspace attributes. Bucket contents can be obtained by running [`get_workspace_bucket_contents.py`](#get_workspace_bucket_contentspy) and workspace attributes can be obtained with [`get_workspace_attributes.py`](get_workspace_attributes.py).

### Usage
Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name   
    --attributes            <string>    Workspace attributes table, from `get_workspace_attributes.py`
    --bucket-contents       <string>    Workspace bucket contents, from `get_workspace_bucket_contents.py`
```

Optional arguments:
```bash
    --chunk-size             <int>      Rows to process per chunk from `--bucket-contents`, default: 10,000
    --keep                   <string>   File types to keep and not identify for removal. Leading periods will be removed, default: [`ipynb`]
    --print                  <boolean>  Prints a summary of results
    --submissions-only       <boolean>  Considers only files generated from workspace submissions 
```

Outputs produced:

| File name                                        | Description                                                                 |
|--------------------------------------------------|-----------------------------------------------------------------------------|
| {namespace}.{name}.bucket_contents.annotated.tsv | All files present in a workspace's bucket, annotated for filtering criteria |
| {namespace}.{name}.files_to_remove.tsv | Files from `{namespace}.{name}.bucket_contents.annotated.tsv` that have the column `nominate_for_removal` set to `1` | 

Example:
```bash
python identify_files_manually_clean-workspace.py \ 
          --namespace vanallen-firecloud-nih \
          --name ovarian-9825 \
          --attributes vanallen-firecloud-nih.ovarian-9825.attributes.tsv \
          --bucket-contents vanallen-firecloud-nih.ovarian-9825.bucket_contents.tsv \
          --keep bam --keep bai --keep .md \ 
          --submissions-only \
          --print
```

Here, we identify files to clean for the workspace vanallen-firecloud-nih/ovarian-9825. We ensure that files with the extension bam, bai, and md are retained and only consider files from workspace submissions. Furthermore, we have the script print a summary of findings into the terminal.

[Back to table of contents](#table-of-contents)

## list_source_files.py
`list_source_files.py` lists the path of files successfully copied by gsutil cp, by specifically identifying rows for which `Status == OK` and returning the path listed under `Source`. A file with no header or index which lists one file per row is returned.

### Usage
Required arguments:
```bash
    --input, -i             <string>    Log from gsutil cp
    --output, -o            <string>    Prefix name of output file
```

Optional arguments:
```bash
    --files, -f             <boolean>   List the number of files attempted and successfully transferred
    --bytes, -b             <boolean>   List the bytes and gigibytes attempted and successfully transferred
```

Outputs produced:

|File name|Description|
|---|---|
|{output}.files_to_remove.txt|List of files which were successfully copied to the destination, one per row.|
|n_files_attempted.txt|The number of files attempted to be copied.|
|n_files_transferred.txt|The number of files successfully transferred.|
|bytes_attempted.txt|Bytes at source location for files attempted to be copied.|
|bytes_transferred.txt|Bytes transferred for successfully copied files.|
|gigibytes_attempted.txt|Gigibytes (bytes / 2^30) at source location for files attempted to be copied.|
|gigibytes_transferred.txt|Gigibytes (bytes / 2^30) transferred for successfully copied files.|

Example:
```bash
python list_source_files.py --input fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv --output fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af
```

[Back to table of contents](#table-of-contents)

## list_workspaces.py
`list_workspaces.py` list all workspaces found within the specified namespaces along with bucket usage, monthly cost, and last modified date. Additional columns can be generated to list the tags used by each workspace. Tags looked for and default namespaces to list workspaces from are defined in `config.json`. 

### Usage
Optional arguments:
```bash
    --config                <string>    Config file that defines namespaces and tags. Default: `config.json`
    --namespace             <string>    Namespace to list workspaces from, can be passed multiple times. Default: namespaces listed in `config.json``
    --output                <string>    Output name for produced file. Default: YYYY-MM-DD.workspaces_storage.txt
    --tags                  <boolean>   If passed, tags listed in `config.json` will be annotated
```

Outputs produced:

|File name|Description|
|---|---|
|YYYY-MM-DD.workspaces_storage.txt|List of workspaces with metadata, one per row.|

Example:
In this example, we list all workspaces from namespaces defined in `config.json` with tags. `--output` is not passed to keep the default naming convention.
```bash
python list_workspaces.py --tags
```
Here, we list workspaces with tags from the namespaces `vanallen-firecloud-nih` and `vanallen-firecloud-dfci`,
```bash
python list_workspaces --namespace vanallen-firecloud-nih --namespace vanallen-firecloud-dfci --tags
```
And here, we list only workspaces from `vanallen-firecloud-nih` without tags and define the output name.
```bash
python list_workspaces --namespace vanallen-firecloud-nih --output vanallen-firecloud-nih.workspaces.txt
```

[Back to table of contents](#table-of-contents)

## list_workspaces_to_archive.py
`list_workspaces_to_archive.py` can generate an input for `copy_multiple_buckets.sh` based on a common tag in Terra. The same destination is set for all workspaces listed. If you want to run `list_workspaces.py` for multiple accounts, don't forget to update your application default credentials before each run.

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

## restore_files.sh
`restore_files.sh` is used to reverse the results of `gsutil cp`. Given a gsutil copy log, it will copy the `Destination` location back to the `Source` location. This script assumes that the gsutil copy log is still a comma delimited, `.csv`, file format. Using the following example, the `Destination` path will be copied to the `Source` locations,

|Source|Destination|
|---|---|
|gs://terra-workspace-archive-us-central1/fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/stuff.md|
|gs://terra-workspace-archive-us-central1/fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|gs://fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af/subfolder/other_stuff.md|

### Usage
Required arguments:
```bash
    INPUT_COPY_LOG          <string>    gsutil cp log
    OUTPUT_PREFIX           <string>    prefix for output file, it will have the suffix of `.restored.csv`
```

Outputs produced:

|File name|Description|
|---|---|
|`{OUTPUT_PREFIX}.restored.csv`|A comma delimited file with the status and byte size of all files that gsutil attempted to copy.|

Example:
```bash
bash restore_files.sh fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv fc-01e89ec0-c3b9-4a2f-9a70-21460d4427af-restored
```

[Back to table of contents](#table-of-contents)

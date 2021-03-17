# Table of contents
1. [Archiving overview](#archiving-overview)
   - [Van Allen lab non-Terra buckets for Terra workspaces](#van-allen-lab-non-terra-buckets-for-terra-workspaces)
   - [Understanding cloud costs](#understanding-cloud-costs)
2. [Estimating archive and retrieval costs](#estimating-archive-and-retrieval-costs)
3. [Archiving a workspace](#archiving-a-workspace)
   - [Copying bucket contents](#copying-bucket-contents)
   - [Listing successfully copied files](#listing-successfully-copied-files)
   - [Removing successfully copied files](#removing-successfully-copied-files)
   - [Staying organized after archiving a workspace](#staying-organized-after-archiving-a-workspace)
4. [Restoring a workspace](#restoring-a-workspace)
   - [Restoring bucket contents](#restoring-bucket-contents)
   - [Listing successfully restored files](#listing-successfully-restored-files)
   - [Removing successfully restored files](#removing-successfully-restored-files)
   - [Staying organized after restoring a workspace](#staying-organized-after-restoring-a-workspace)
5. [Archiving many workspaces](#archiving-many-workspaces)

## Archiving overview
Terra enforces that all workspaces use Google Cloud's most expensive pricing tier for data storage. Workspaces are stored in US multi-regional standard buckets, which costs $26 per terabyte per month; however, all compute instances used by Terra, by default, are single-regional; specifically, us-central1. Despite Google having [numerous lifecycle policies](https://cloud.google.com/storage/docs/managing-lifecycles) and additional [storage tiers](https://cloud.google.com/storage/pricing) which may be more cost effective, users must circumvent Terra to take advantage of these cost savings. Thus, we aim to move data that is not being accessed to more cost effective storage tiers on Google Cloud. 

You can either do this yourself or ask Brendan to do it for you. Brendan periodically checks for workspaces tagged with `archive` on Terra to archive workspaces, usually on a monthly basis. He and/or Jihye may reach out to you if you are the owner of a workspace that has not been modified for a couple of months, too.

The steps to archive a workspace are as follows:
1. Estimate how long the workspace's data will go not accessed for
2. Run the [estimator script](#estimate-archive-and-retrieval-costs) to determine the most cost effective location and storage type to archive your bucket's data to and retrieve from
3. Determine the [destination bucket](#van-allen-lab-non-terra-buckets-for-terra-workspaces), which you will move your workspace's data to
4. [Archive your workspace](#archiving-a-workspace)
    - Run `copy_bucket.sh`
    - Run `list_source_files.py` to list paths of successfully copied files, number of files transferred, and overall bytes transferred
    - Remove successfully copied files with `remove_files.sh`
5. Copy the `gsutil cp` log from `copy_bucket.sh`, `files_to_remove.txt` passed to `remove_files.sh`, and the cost estimator files to both the source (your workspace) and destination bucket
6. Update our [list of archived workspaces](https://docs.google.com/spreadsheets/d/1hxhavlxVCU2KcRv3nUqVkDB5BCybtDpcw1iULUmh24k/edit) with your workspace's information
7. Update [tags](https://docs.google.com/document/d/1J1-ZhcGII8TTOO3uTCzOZw2DUwGghXEm2inLM2cchR8/edit#heading=h.1rwd53ai6e47) on your workspace. Remove out of date ones and tag the workspace as `archived`.
8. Update the workspace README to list where it was archived to and when

The steps to restore a workspace to Terra are as follows:
1. See how long the workspace has been archived for and look at costs to retrieve the workspace. If the retrieval cost will be high (greater than.. $500...? please let eli, brendan, and jihye know)
2. [Restore your workspace](#restoring-a-workspace)
    - Run `restore_bucket.sh`
    - Run `list_source_files.py` to list paths of successfully copied files, number of files transferred, and overall bytes transferred
    - Remove successfully copied files with `remove_files.sh`
3. Update our [list of archived workspaces](https://docs.google.com/spreadsheets/d/1hxhavlxVCU2KcRv3nUqVkDB5BCybtDpcw1iULUmh24k/edit) with your workspace's information, by moving the row to the `restored_workspaces` sheet and adding a restored date under the column `date restored`
4. Update [tags](https://docs.google.com/document/d/1J1-ZhcGII8TTOO3uTCzOZw2DUwGghXEm2inLM2cchR8/edit#heading=h.1rwd53ai6e47) on your workspace. Remove the `archived` tag and [tag the workspace appropriately](https://docs.google.com/document/d/1J1-ZhcGII8TTOO3uTCzOZw2DUwGghXEm2inLM2cchR8/edit#heading=h.1rwd53ai6e47)
5. Update the workspace README to remove text about the workspace's archive details

### Van Allen lab non-Terra buckets for Terra workspaces
We currently have several designated buckets for Terra workspaces under the `vanallen-gcp-nih` google billing project

|bucket name|location type|location|storage type|
|---|---|---|---|
|gs://terra-workspace-nearline-us|Multi-region|us (multiple regions)|Nearline|
|gs://terra-workspace-coldline-us|Multi-region|us (multiple regions)|Coldline|
|gs://terra-workspace-archive-us|Multi-region|us (multiple regions)|Archive|
|gs://terra-workspace-standard-us-central1|Region|us-central1 (Iowa)|Standard|
|gs://terra-workspace-nearline-us-central1|Region|us-central1 (Iowa)|Nearline|
|gs://terra-workspace-coldline-us-central1|Region|us-central1 (Iowa)|Coldline|
|gs://terra-workspace-archive-us-central1|Region|us-central1 (Iowa)|Archive|

### Understanding Cloud costs
However, there are sometimes cost incurred for moving data within the cloud. When moving data between buckets there may be [network](https://cloud.google.com/storage/pricing#network-pricing) and [operation](https://cloud.google.com/storage/pricing#operations-pricing) fees and, when returning the data to its original location, there may be [network](https://cloud.google.com/storage/pricing#network-pricing), [operation](https://cloud.google.com/storage/pricing#operations-pricing), and [retrieval](https://cloud.google.com/storage/pricing#archival-pricing) fees. In short,
- Network fees are associated with network egress, moving data _from_ a location. This is charged on a per binary* gigabyte basis for moving data between locations, whether across Google Cloud or off of Google Cloud.
- Operation fees are associated with "touching" files, when a change is made to or information about is retrieved. These are charged on a basis of per 10,000 operations and Google has three types of operations which are charged for differently.
- Retrieval fees are associated with accessing data stored in nearline, coldline, and archive storage because the data is not immediately accessible.

For more details, [see this slide deck](https://docs.google.com/presentation/d/1y_KxBDum8xNs89llKkdn6bgieBjgSuI3qP7P-Xdeo9A/edit) on estimating cloud archive and retrieval costs.

[Back to table of contents](#table-of-contents)

## Estimating archive and retrieval costs
The python script `estimate_archive_and_retrieval_costs.py` can be used to estimate the most cost effective storage location and type for a given workspace, as a function of how many days it will not be accessed. See the script's [documentation](#documentation) and [this slide deck](https://docs.google.com/presentation/d/1y_KxBDum8xNs89llKkdn6bgieBjgSuI3qP7P-Xdeo9A/edit) for more details. 

[Back to table of contents](#table-of-contents)

## Archiving a workspace
The scripts `copy_bucket.sh`, `list_source_files.py`, and `remove_files.sh` should be used to move a workspace's bucket from Terra. Consider the example of archiving the data from the workspace `vanallen-firecloud-nih/2014-Perry-MOAlmanac` (google bucket: `gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6`) to `gs://terra-workspace-archive-us-central1`.

### Copying bucket contents
First, we run `copy_bucket.sh` to move the files from `vanallen-firecloud-nih/2014-Perry-MOAlmanac` to `gs://terra-workspace-archive-us-central1`. Folder structure will be preserved and terminal will display the progress of copying bucket contents.
```bash
bash copy_bucket.sh fc-9f163956-5368-4095-a4f1-4ae8d03070b6 terra-workspace-archive-us-central1
```

The gsutil copy log is produced from this and will be called `fc-9f163956-5368-4095-a4f1-4ae8d03070b6-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv`. Folder structure in our workspace's bucket (Source) and destination bucket (Destination) will currently appear as

|Source|Destination|
|---|---|
|gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6/stuff.md|gs://terra-workspace-archive-us-central1/fc-9f163956-5368-4095-a4f1-4ae8d03070b6/stuff.md|
|gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6/subfolder/other_stuff.md|gs://terra-workspace-archive-us-central1/fc-9f163956-5368-4095-a4f1-4ae8d03070b6/subfolder/other_stuff.md|

### Listing successfully copied files
Second, we run `list_source_files.py` on our gsutil copy log to list source paths of files successfully copied.

```bash
python list_source_files.py --input fc-9f163956-5368-4095-a4f1-4ae8d03070b6-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv fc-9f163956-5368-4095-a4f1-4ae8d03070b6
```

The list of source files successfully copied will be produced as `fc-9f163956-5368-4095-a4f1-4ae8d03070b6.files_to_remove.txt`. The overall number of successfully copied files and bytes copied will also be listed. 

### Removing successfully copied files
Third, we run `remove_files.sh` to remove the original copy of files in the workspace's bucket. No output file is produced but terminal will display the progress of removal.

```bash
bash remove_files.sh fc-9f163956-5368-4095-a4f1-4ae8d03070b6.files_to_remove.txt
```

### Staying organized after archiving a workspace
At this point, the workspace is formally archived but there are a few quick things to which will help keep the lab organized, as well as help with eventual data retrieval.

- Copy the gsutil cp log, files_to_remove file, and cost estimator files to both the workspace bucket _and_ archived location. 

```bash
gsutil -m cp fc-9f163956-5368-4095-a4f1-4ae8d03070b6-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv fc-9f163956-5368-4095-a4f1-4ae8d03070b6.files_to_remove.txt vanallen-firecloud-nih.2014-Perry-MOAlmanac.cost-estimates.xlsx vanallen-firecloud-nih.2014-Perry-MOAlmanac.cost-estimates.full.xlsx gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6
gsutil -m cp fc-9f163956-5368-4095-a4f1-4ae8d03070b6-to-terra-workspace-archive-us-central1.gsutil_copy_log.csv fc-9f163956-5368-4095-a4f1-4ae8d03070b6.files_to_remove.txt vanallen-firecloud-nih.2014-Perry-MOAlmanac.cost-estimates.xlsx vanallen-firecloud-nih.2014-Perry-MOAlmanac.cost-estimates.full.xlsx gs://terra-workspace-archive-us-central1/fc-9f163956-5368-4095-a4f1-4ae8d03070b6
```

- Record the workspace, archived bytes, and date to our [record of archived workspaces](https://docs.google.com/spreadsheets/d/1hxhavlxVCU2KcRv3nUqVkDB5BCybtDpcw1iULUmh24k/edit#gid=0).
- Update your workspace's [tags](https://docs.google.com/document/d/1J1-ZhcGII8TTOO3uTCzOZw2DUwGghXEm2inLM2cchR8/edit#heading=h.1rwd53ai6e47). Remove out of date tags and add `archived` as a tag.
- Update the workspace README with the date and where the workspace was archived to. For example, 
> Archived to `gs://terra-workspace-archive-us-central1/` under `vanallen-gcp-nih` on March 3rd, 2021.

[Back to table of contents](#table-of-contents)

## Restoring a workspace
The scripts `copy_bucket.sh`, `list_source_files.py`, and `remove_files.sh` should be used to move a workspace's bucket from Terra. Consider the example of restoring the bucket for workspace `vanallen-firecloud-nih/2014-Perry-MOAlmanac` (google bucket: `gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6`) from `gs://terra-workspace-archive-us-central1`. If a workspace is restored [before the minimum storage duration of the archive location's storage type is reached](https://cloud.google.com/storage/pricing#archival-pricing), we will be charged for the costs that would have been incurred had this data been stored for the remaining of the minimum storage duration. From Google's documentation, 
> For example, suppose you store 1,000 GB of Coldline Storage data in the US multi-region. If you add the data on day 1 and then remove it on day 60, you are charged $14 ($0.007/GB/mo. * 1,000 GB * 2 mo.) for storage from day 1 to 60, and then $7 ($0.007/GB/mo. * 1,000 GB * 1 mo.) for 30 days of early deletion from day 61 to 90.

### Restoring bucket contents
First, we run `restore_bucket.sh` to move the files from `vanallen-firecloud-nih/2014-Perry-MOAlmanac` to `gs://terra-workspace-archive-us-central1`. Folder structure will be preserved and terminal will display the progress of copying bucket contents.
```bash
bash restore_bucket.sh terra-workspace-archive-us-central1 fc-9f163956-5368-4095-a4f1-4ae8d03070b6
```

The gsutil copy log is produced from this and will be called `fc-9f163956-5368-4095-a4f1-4ae8d03070b6-from-terra-workspace-archive-us-central1.gsutil_copy_log.csv`. Folder structure in our workspace's bucket (Source) and destination bucket (Destination) will currently appear as

|Source|Destination|
|---|---|
|gs://terra-workspace-archive-us-central1/fc-9f163956-5368-4095-a4f1-4ae8d03070b6/stuff.md|gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6/stuff.md|
|gs://terra-workspace-archive-us-central1/fc-9f163956-5368-4095-a4f1-4ae8d03070b6/subfolder/other_stuff.md|gs://fc-9f163956-5368-4095-a4f1-4ae8d03070b6/subfolder/other_stuff.md|

### Listing successfully restored files
Second, we run `list_source_files.py` on our gsutil copy log to list source paths of files successfully copied. 

```bash
python list_source_files.py --input fc-9f163956-5368-4095-a4f1-4ae8d03070b6-from-terra-workspace-archive-us-central1.gsutil_copy_log.csv terra-workspace-archive-us-central1.fc-9f163956-5368-4095-a4f1-4ae8d03070b6
```

The list of source files successfully copied will be produced as `terra-workspace-archive-us-central1.fc-9f163956-5368-4095-a4f1-4ae8d03070b6.files_to_remove.txt`. The overall number of successfully copied files and bytes copied will also be listed. 

### Removing successfully restored files
Third, we run `remove_files.sh` to remove the original copy of files in the workspace's bucket. No output file is produced but terminal will display the progress of removal. To reiterate, if files are being deleted _before_ the minimum duration, we will be charged for the remaining duration; for example, if a workspace is moved to coldline storage (minimum: 90 days) and restored after 60 days, we will be charged for the retrieval costs as well as an additional 30 days of storage.

```bash
bash remove_files.sh terra-workspace-archive-us-central1.fc-9f163956-5368-4095-a4f1-4ae8d03070b6.files_to_remove.txt
```

### Staying organized after restoring a workspace
- Move the workspace in [record of archived workspaces](https://docs.google.com/spreadsheets/d/1hxhavlxVCU2KcRv3nUqVkDB5BCybtDpcw1iULUmh24k/edit#gid=0) to the `restored workspaces` tab and record the date restored.
- Update your workspace's [tags](https://docs.google.com/document/d/1J1-ZhcGII8TTOO3uTCzOZw2DUwGghXEm2inLM2cchR8/edit#heading=h.1rwd53ai6e47). Remove the `archived` tag.
- Remove the details of archiving from the workspace's README. 

[Back to table of contents](#table-of-contents)

## Archiving many workspaces
The script `copy_multiple_buckets.sh` can be used to copy multiple buckets to a specific destination. The script calls copy_bucket.sh, list_sources.py, and remove_files.sh. The input is a tab delimited file that lists the source bucket, destination bucket, workspace namespace, and workspace name. This file can be created with the `list_workspaces_to_archive.py` script, which formats an input for this script based on workspaces with a common tag. Logs are copied to the source bucket; however, the source workspace should be commented and tagged with "archive".

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

[Back to table of contents](#table-of-contents)

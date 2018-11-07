# FireCloud helper
FireCloud helper is a collection of scripts which leverage the [FireCloud API](https://api.firecloud.org) to perform cumbersome tasks on [FireCloud](firecloud.org). 

## Installation
To use FireCloud helper, you must have the following set up on your system
- [Google Cloud SDK](https://cloud.google.com/sdk/)
- Python 3

Google Cloud and FireCloud use [Google Cloud SDK](https://cloud.google.com/sdk/) to manage authentication. The [application default credentials](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login) will be used. To login,
```bash
gcloud auth application-default login
```

You may need to export your google cloud auth token
```bash
export GCS_OAUTH_TOKEN=`gcloud auth application-default print-access-token`
```

FireCloud helper uses Python 3.6. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) and running Python with either [Anaconda](https://www.anaconda.com/download/) or  [Miniconda](https://conda.io/miniconda.html). After installing Anaconda or Miniconda, you can set up by running
```bash
conda create -y -n venv_firecloud_helper python=3.6 --file requirements.txt
source activate venv_firecloud_helper
```

You must also have write access on FireCloud to whichever workspace you want to interact with.

## clean_workspace.py
This script will remove files from a FireCloud workspace's bucket if they are not present in the data model. The need for this tool arose from the reality that **FireCloud's call-cache passes files by copying, instead of by reference**; this results in duplicate files whenever a method is rerun. 

**This should not be used while a submission is running in your workspace.**

### Usage
clean_workspace.py has two modes: `--index` and `--clean`. `--index` will create a list of files to delete from your workspace while `--clean` will delete files. These modules were split to reduce the number of times that `gsutil ls` is being called, [because listing files costs money](https://github.com/vanallenlab/firecloud_helper/issues/2).

Required arguments:
```bash
    --namespace     <string>    Workspace's namespace
    --name          <string>    Workspace's name
```
Optional arguments:
```bash
    --filename      <string>    Filename for files to remove, default=files_to_remove.(namespace).(name).txt
    
    
    --index         <boolean>   Will index workspace for files to remove, write to --filename
    --keeplogs      <boolean>   Boolean for keeping log files for folders not in data model
    
    --clean         <boolean>   Will delete files listed in --filename
    --chunksize     <int>       Number of files to pass to gsutil at once for parallel deletion, default=500
```
Chunksize is a necessary parameter for `--clean` because operating systems have character limits of how long commands are.

`--clean` will produce a summary of the storage before and after deletion
```bash
    namespace                       namespace_name
    name                            workspace_name
    initial_bucket_size_gb          100
    initial_bucket_monthly_cost_$   5
    number_of_files_to_delete       20
    updated_bucket_size_gb          80
    updated_bucket_monthly_cost_$   4
```
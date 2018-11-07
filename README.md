# FireCloud helper
FireCloud helper is a collection of scripts which leverages the [FireCloud API](https://api.firecloud.org) to perform cumbersome tasks. 

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
This script will remove files from a FireCloud workspace's bucket if they are not present in the data model. The need for this tool arose from the reality that *FireCloud's call-cache passes files by copying, instead of by reference*; this results in duplicate files whenever a method is rerun. 

### Usage
clean_workspace.py requires at least the workspace's namespace and name. To actual delete files, pass `--clean`.   
Required arguments:
```bash
    --namespace     <string>    Workspace's namespace
    --name          <string>    Workspace's name
```
Optional arguments:
```bash
    --clean         <boolean>   Will actually delete files when passed
    --chunksize     <int>       Number of files to pass to gsutil at once for parallel deletion. Default = 500.
    --filename      <string>    Filename of written list of files to be deleted. Default = files_to_remove.txt
```
Chunksize is a necessary parameter because operating systems have character limits of how long commands are.
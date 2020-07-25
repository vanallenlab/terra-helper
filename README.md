# Firecloud helper
Terra helper is a collection of scripts which leverage the [FireCloud API](https://api.firecloud.org) to perform cumbersome tasks on [Firecloud](firecloud.org). A more appropriate name for this repository may be `Terra storage helper`, as the platform has since rebranded and the scripts pretty much just deal with cleaning up workspaces or moving underlying buckets. The python package [fiss](https://github.com/broadinstitute/fiss) also has a function called mop which tries to clean up intermediate files. 

## Installation

### System requirements
To use terra storage helper, you must have the following set up on your system
- [Google Cloud SDK](https://cloud.google.com/sdk/)
- Python 3

Google Cloud and Terra use [Google Cloud SDK](https://cloud.google.com/sdk/) to manage authentication. The [application default credentials](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login) will be used. **Please walk through Google's wonderful install and set up documentation if you have not**. To login and set an application default, make sure that you've run the following,
```bash
gcloud auth login
gcloud auth application-default login
```

You may need to export your google cloud auth token, add this to your bash profile:
```bash
export GCS_OAUTH_TOKEN=`gcloud auth application-default print-access-token`
```

### Download this software from Github
This package can be download through Github on the website or by using terminal. To download on the website, navigate to the top of this page, click the green `Clone or download` button, and select `Download ZIP`. This will download this repository in a compressed format. To install using Github on terminal, type 

```bash
git clone https://github.com/vanallenlab/firecloud-helper.git
cd firecloud-helper
```

### Install Python dependencies
FireCloud helper uses Python 3.7. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) and running Python with either [Anaconda](https://www.anaconda.com/download/) or  [Miniconda](https://conda.io/miniconda.html). 

To create a virtual environment and install dependencies with Anaconda or Miniconda, run the following from this repository's directory:
```bash
conda create -y -n firecloud-helper python=3.7
conda activate firecloud-helper
pip install -r requirements.txt
```

If you are using base Python, you can create a virtual environment and install dependencies by running:
```bash
virtualenv firecloud-helper
source activate firecloud-helper/bin/activate
pip install -r requirements.txt
```

## Deleting old or intermediate files from your workspace
The script `index_workspace.py` can be used to list all files in a workspace's bucket that either do not appear in the data model or as a workspace annotation. You should then **review the list of files to ensure that there is nothing that you want to actually keep** and you can delete the files with `remove_files.sh`. 

**This should not be used while a submission is running in your workspace and notebooks will not be kept**.

### Usage
`index_workspace.py` will get the bucket associated with your workspace, pull all elements in the data model and workspace annotations, and take the difference. If `keep_related_files` is passed, any files in the same directory as one either in the datamodel or workspace annotations will also be kept, such as the associated stderr and stdout from any jobs. Outputs will be written to `{namespace}.{name}.files_to_remove.txt`.

Required arguments:
```bash
    --namespace             <string>    Workspace's namespace
    --name                  <string>    Workspace's name
```

Optional arguments:
```bash
    --keep_related_files    <boolean>   Boolean for keeping all contents for folders in data model
```

`remove_files.sh` will simply pass the provided file, which should be a simple text file listing one file on google cloud per row, to gsutil for deletion. 
Required arguments:
```bash
    HANDLE                  <string>    File path to list of files for removal
```
### Example
To clean up the workspace vanallen-firecloud-dfci/Robinson2015_dev, the workspace is first indexed, reviewed, and then passed to `remove_files.sh`. I am also choosing to pass `--keep_related_files` to keep any files in a tail directory included in the workspace's data model or workspace annotations, even though it will significantly add to runtime.

Index the workspace:
```bash
python index_workspace.py --namespace vanallen-firecloud-dfci --name Robinson2015_dev --keep_related_files
```
Once completed, a file named `vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt` appears in the current working directory. This list of files is reviewed and any files that I want to keep are deleted from the file, maybe I uploaded a PDF or Jupyter notebook to the Google Bucket and I want to keep it. The file is then saved and passed to `remove_files.sh`,
```bash
bash remove_files.sh vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt
```
You will be able to watch the progress of your files being deleted. 

## Moving the contents of your workspace's Google bucket elsewhere
The scripts `copy_bucket.sh` and `copy_bucket-mirror.sh` can be used to copy your workspace's bucket, or really any Google bucket, to another location, either on locally or on Google Cloud. If you want the contents of your original bucket to appear in the root directory of your destination, use `copy_bucket-mirror.sh`. Otherwise, you can use `copy_bucket.sh` and the contents will be copied to the provided destination inside of a folder named after the source bucket, with structure in tact. In both cases, the gsutil copy log will be produced and named as `{SOURCE}-to-{DESTINATION}.gsutil_copy_log.csv`. There have been issues with gsutil not exiting the process upon completion, so, if it is done, just exit. 

Required arguments:
```bash
    SOURCE                  <string>    Source Google bucket, with or without the gs:// prefix
    DESTINATION             <string>    Destination Google bucket, with or without the gs:// prefix
```
If you want to delete the files successfully copied from the source location, you can extract a list of successfully copied files with `list_source_files.py`.

Required arguments:
```bash
    --input                 <string>    Path to log file from gsutil
    --output                <string>    Prefix for output, output will be written to '{output}.files_to_remove.txt'
```

`remove_files.sh` will simply pass the provided file, which should be a simple text file listing one file on google cloud per row, to gsutil for deletion. You will be able to watch the progress of your files being deleted. 
Required arguments:
```bash
    HANDLE                  <string>    File path to list of files for removal
```

### Example
To move the workspace vanallen-firecloud-dfci/Robinson2015_dev to vanallen-firecloud-nih/Robinson2015_dev, the buckets of both workspaces are both noted: `gs://fc-f804af42-ded2-4bf2-af24-99d8b6d3b969` and `gs://fc-7894f74c-6827-40ab-a26e-57d0bcb295ce`, respectively. `copy_bucket.sh` is then run to copy the contents of on to the other, though `copy_bucket-mirror.sh` could be run instead if you want the root directories to be exactly the same. The gsutil copy log is then passed to `list_source_files.py` and then passed to `remove_files.sh`. 

`copy_bucket.sh` is run, allowing me to see the status of the copying and recording the progress to `fc-f804af42-ded2-4bf2-af24-99d8b6d3b969-to-fc-7894f74c-6827-40ab-a26e-57d0bcb295ce.gsutil_copy_log.csv`. 
```bash
bash copy_bucket.sh gs://fc-f804af42-ded2-4bf2-af24-99d8b6d3b969 gs://fc-7894f74c-6827-40ab-a26e-57d0bcb295ce
```

The gsutil copy log is then passed to `list_source_files.py` to extract the list of files successfully copied. The output prefix "vanallen-firecloud-dfci.Robinson2015_dev" is passed to specify the prefix for the output file, `vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt`.
```bash
python list_source_files.py --input fc-f804af42-ded2-4bf2-af24-99d8b6d3b969-to-fc-7894f74c-6827-40ab-a26e-57d0bcb295ce.gsutil_copy_log.csv --output "vanallen-firecloud-dfci.Robinson2015_dev"
```

`vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt` is then passed to `remove_files.sh`. Any files passed to `remove_files.sh` will be deleted, but you can pass without review with reasonable confidence because `list_source_files.py` will only list those that were successfully copied.
```bash
bash remove_files.sh vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt
```

You should then update the data model in the new workspace to point to the files. If you copied the data model from your old workspace, you should be able to either find and replace the bucket name or add the new bucket name as a prefix, if you did not mirror.

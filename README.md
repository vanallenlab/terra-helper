# FireCloud helper
FireCloud helper is a collection of scripts which leverage the [FireCloud API](https://api.firecloud.org) to perform cumbersome tasks on [FireCloud](firecloud.org). A more appropriate name for this repository may be `Terra storage helper`, as the platform has since rebranded. The python package [fiss](https://github.com/broadinstitute/fiss) also has a function called mop which functions similarly.

## Installation

### System requirements
To use terra storage helper, you must have the following set up on your system
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

### Download this software from Github
This package can be download through Github on the website or by using terminal. To download on the website, navigate to the top of this page, click the green `Clone or download` button, and select `Download ZIP`. This will download this repository in a compressed format. To install using Github on terminal, type 

```bash
git clone https://github.com/vanallenlab/firecloud-helper.git
cd firecloud-helper
```

### Install Python dependencies
FireCloud helper uses Python 3.6. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) and running Python with either [Anaconda](https://www.anaconda.com/download/) or  [Miniconda](https://conda.io/miniconda.html). 

To create a virtual environment and install dependencies with Anaconda or Miniconda, run the following from this repository's directory:
```bash
conda create -y -n firecloud-helper python=3.6
conda activate firecloud-helper
pip install -r requirements.txt
```

If you are using base Python, you can create a virtual environment and install dependencies by running:
```bash
virtualenv firecloud-helper
source activate firecloud-helper/bin/activate
pip install -r requirements.txt
```

## clean_workspace.py
This script will remove files from a FireCloud workspace's bucket if they are not present in the data model. The need for this tool arose from the reality that **FireCloud's call-cache passes files by copying, instead of by reference**; this results in duplicate files whenever a method is rerun. You must also have write access on FireCloud to whichever workspace you want to interact with.

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
    --dryrun        <boolean>   Will not actually delete anything
```

`--clean` will produce a summary of the storage before and after deletion
```bash
    namespace                       namespace_name
    name                            workspace_name
    initial_bucket_size_gb          100
    initial_bucket_monthly_cost_$   5
    number_of_files_to_delete       20
```

### Example 
If I want to index and clean a workspace called `TEST-WORKSPACE` under the namespace `BILLING-NAMESPACE`, the following commands would be used. To index,
```bash
python clean_workspace.py --index --namespace BILLING-NAMESPACE --name TEST-WORKSPACE
```

This would run and create a file called `files_to_remove.BILLING-NAMESPACE.TEST-WORKSPACE.txt`. This file should be manually inspected as all files in this file will be deleted. After inspection, the following code can be run to delete the contained files,
```bash
python clean_workspace.py --clean --namespace BILLING-NAMEPSACE --name TEST-WORKSPACE
```

Savings are calculated in real time by Google and will be reflected in your monthly bill; however, because Terra only updates the storage estimate display once a day, savings will be observable through the user interface after 24 hours.  

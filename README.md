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

## copy_bucket.py
This script will allow you to copy the contents of one bucket to another. The copy produces a log of files copied, named `{original_bucket}-to-{new_bucket}.copy_log.csv`, from Google's [gsutil cp](). This log is then used to create an index file of all files that were successfully copied, to be used with clean_workspace.py to remove the originals. 

By default, `copy_bucket.py` will place the original files in the new bucket under a folder named after the original bucket in the new bucket's parent directory. To change this and just mirror the original bucket, add the parameter `--mirror`. To be specific, the default behavior is such that copying `gs://fc-944028b3-ba83-4262-a01a-9dd30d1e19e8/` to `gs://fc-0e064e14-e364-4983-84b7-3b2a3900a0c4/` will be located at `gs://fc-0e064e14-e364-4983-84b7-3b2a3900a0c4/fc-944028b3-ba83-4262-a01a-9dd30d1e19e8/`.

### Usage
Pass the original google bucket address and the new google bucket address to the script `copy_bucket.py`. The prefix `gs://` will be removed if passed.

Required arguments:
```bash
    --original          <string>    Original workspace bucket
    --new               <string>    New workspace bucket
```
Optional arguments:
```bash
    --filename          <string>    Filename for files to remove, default=files_to_remove.(original bucket).from_copier.txt
    --mirror            <boolean>   By default, 
    --disable_timeout   <boolean>   Boolean to disable the 12 hr timeout on gsutil cp 
```

Two files will be produced:
- `{original bucket}-to-{new bucket}.copy_log.csv`, gsutil cp's log of all files copied and their status.
- `files_to_remove.{original bucket}.from_copier.txt`, an index file of all successfully copied files to be used with `clean_workspace.py`.

There seemed to be an issue with gsutil hanging on the copy from one bucket to another, which _seems_ to be resolved by using Python 3.7. Just in case, I added a 12 hour timeout to the subprocess which runs gsutil cp. If you get timed out, look at the gsutil cp log. If the log was updated recently, your workspace must be huge! I'm sorry, rerun with `--disable_timeout` and thankfully your progress thus far is cached. If the log has _not_ been updated in a very long time then you may have been left hanging. Make sure that you're using Python 3.7 and let me know. 

### Example
To move the contents of the workspace `vanallen-firecloud-dfci/An_AnCan`, `gs://fc-a1b8bf3e-2889-4376-b843-7d6ce04c1533`, to `vanallen-firecloud-dfci/test-migration-workspace`, `gs://fc-0e064e14-e364-4983-84b7-3b2a3900a0c4`, I would do the following:
```bash
python copy_bucket.py --original fc-a1b8bf3e-2889-4376-b843-7d6ce04c1533 --new fc-0e064e14-e364-4983-84b7-3b2a3900a0c4
```
This will produce a file `fc-a1b8bf3e-2889-4376-b843-7d6ce04c1533-to-fc-0e064e14-e364-4983-84b7-3b2a3900a0c4.copy_log.csv`, which I'll review. Each row in this file represents a file copied and their status is under the `Result` column. All files that are of `Result == OK` are listed in `files_to_remove.fc-a1b8bf3e-2889-4376-b843-7d6ce04c1533.from_copier.txt`, which can be passed to `clean_workspace.py` for deletion.

```bash
python clean_workspace.py --clean --namespace vanallen-firecloud-dfci --name An_AnCan --filename files_to_remove.fc-a1b8bf3e-2889-4376-b843-7d6ce04c1533.from_copier.txt
```

You should then update your data model in the new workspace to point to the new files, which should just be adding the new workspace as a suffix to your paths.

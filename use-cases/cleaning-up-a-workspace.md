## Deleting old or intermediate files from your workspace
The script `index_workspace.py` can be used to list all files in a workspace's bucket that either do not appear in the data model or as a workspace annotation. You should then **review the list of files to ensure that there is nothing that you want to actually keep** and you can delete the files with `remove_files.sh`. 

**This should not be used while a submission is running in your workspace and notebooks will not be kept**.

### Usage
`index_workspace.py` will get the bucket associated with your workspace, pull all elements in the data model and workspace annotations, and take the difference. If `keep_related_files` is passed, any files in the same directory as one either in the datamodel or workspace annotations will also be kept, such as the associated stderr and stdout from any jobs. The argument `--keep` can be passed any number of times to prevent files of a given suffix to be added to the remove list. Outputs will be written to `{namespace}.{name}.files_to_remove.txt` and files in the data model not added are listed in `{namespace}.{name}.files_keep.txt`, along with a rationale. Data model elements that are not a path are listed in `{namespace}.{name}.not_a_path.txt`.

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

`remove_files.sh` will simply pass the provided file, which should be a simple text file listing one file on google cloud per row, to gsutil for deletion. 
Required arguments:
```bash
    HANDLE                  <string>    File path to list of files for removal
```

**Please review your `files_to_remove` output before deleting files.**

### Example
To clean up the workspace vanallen-firecloud-dfci/Robinson2015_dev, the workspace is first indexed, reviewed, and then passed to `remove_files.sh`. I am also choosing to pass `--keep_related_files` to keep any files in a tail directory included in the workspace's data model or workspace annotations, even though it will significantly add to runtime. I am also passing `--keep bam` and `--keep .bai` to keep all bam and bam index files.

Index the workspace:
```bash
python index_workspace.py --namespace vanallen-firecloud-dfci --name Robinson2015_dev --keep_related_files --keep bam --keep bai
```
Once completed, a file named `vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt` appears in the current working directory. Elements included in the data model that are not included in this file are listed in `vanallen-firecloud-dfci.Robinson2015_dev.files_keep.txt`, along with a rationale specified by a 1 in the relevant column. Data model elements that are not a path are specified in `vanallen-firecloud-dfci.Robinson2015_dev.not_a_path.txt`, and should receive a glance over. `vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt` is reviewed and any files that I want to keep are deleted from the file, maybe I uploaded a PDF or Jupyter notebook to the Google Bucket and I want to keep it. The file is then saved and passed to `remove_files.sh`,
```bash
bash remove_files.sh vanallen-firecloud-dfci.Robinson2015_dev.files_to_remove.txt
```
You will be able to watch the progress of your files being deleted. 
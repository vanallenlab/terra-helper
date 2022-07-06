# Manually cleaning a workspace
The following scripts and procedure can be used to remove unused and old intermediate files from a workspace on Terra. **This should not be performed while a workspace has a submission running**. 

Steps are as follows,
1. List all entries in the data model within a given workspace
2. List all files contained in a given workspace's bucket
3. Identify files that are in the bucket that are _not_ in the data model
4. Further subset the list of considered files to remove logs, system files, and any preferred file types. Specify if only files related to method submissions should be considered.
5. Review files nominated for removal 
6. Delete files

To reiterate, **this should not be performed while a workspace has a running submission**. 

Furthermore, as a warning, this process can take quite a long time for workspaces in the tens of terabytes or higher. In some extreme cases of hundreds of terabytes, this can take several days to run. For that reason, **please** consider utilizing cleaner-bot, instead, as it is heavily parallelized.

### Usage
1. Run [get_workspace_attributes.py](../terra-helper/README.md#get_workspace_attributespy)
2. Run [get_workspace_bucket_contents.py](../terra-helper/README.md#get_workspace_bucket_contentspy)
3. Run [identify_files_manually_clean_workspace.py](../terra-helper/README.md#identify_files_manually_clean_workspacepy)
4. Review output of 3.
5. Pass output of 3 to [remove_files.sh](../terra-helper/README.md#remove_filessh)

### Example
To clean up the workspace vanallen-firecloud-nih/ovarian-9825, 

First, get workspace attributes,
```bash
python get_workspace_attributes.py --namespace vanallen-firecloud-nih --name ovarian-9825
```

This produces an output called `vanallen-firecloud-nih.ovarian-9825.attributes.tsv`.

Second, get workspace bucket contents,
```bash
python get_workspace_bucket_contents.py --namespace vanallen-firecloud-nih --name ovarian-9825
```

This produces an output called `vanallen-firecloud-nih.ovarian-9825.workspace_bucket_contents.tsv`.

Third, pass both of these outputs to `identify_files_manually_clean_workspace.py` to nominate files for removal. Here, we take advantage of the optional parameters to ensure that bam, bam index, and markdown files are _not_ removed. Furthermore, we choose to _only_ consider files related to submissions.
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

This produces two outputs:
- `vanallen-firecloud-nih.ovarian-9825.bucket_contents.annotated.tsv`, which annotates the `bucket_contents.tsv` file with the whether each path matches the considered categories.
- `vanallen-firecloud-nih.ovarian-9825.files_to_remove.tsv`, which lists all files in the above output that are set to 1 in the column `nominate_for_removal`

Fourth, these files should be reviewed to ensure that no files are accidentally deleted.

Fifth, the `files_to_remove.tsv` output is passed to remove_files.sh. 
```bash
bash remove_files.sh vanallen-firecloud-nih.ovarian-9825.files_to_remove.tsv
```

`remove_files.sh` will show progress of files being deleted. 

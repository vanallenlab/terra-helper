FROM vanallenlab/miniconda:3.9

RUN apt-get update && apt-get upgrade -y && apt-get install -y curl gnupg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y

COPY requirements.txt /
RUN pip install -r requirements.txt

RUN mkdir /terra-helper/
RUN mkdir /terra-helper/endpoints/

COPY LICENSE /

COPY terra-helper/copy_bucket.sh /terra-helper/
COPY terra-helper/copy_bucket-mirror.sh /terra-helper/
COPY terra-helper/copy_multiple_buckets.sh /terra-helper/
COPY terra-helper/create_workspace.py /terra-helper/
COPY terra-helper/estimate_archive_and_retrieval_cost.py /terra-helper/
COPY terra-helper/get_file_sizes.sh /terra-helper/
COPY terra-helper/get_workspace_attributes.py /terra-helper/
COPY terra-helper/get_workspace_bucket_contents.py /terra-helper/
COPY terra-helper/identify_files_manually_clean_workspace.py /terra-helper/
COPY terra-helper/list_source_files.py /terra-helper/
COPY terra-helper/list_workspaces.py /terra-helper/
COPY terra-helper/operations.py /terra-helper/
COPY terra-helper/reformat.py /terra-helper/
COPY terra-helper/remove_files.sh /terra-helper/
COPY terra-helper/restore_bucket.sh /terra-helper/
COPY terra-helper/restore_files.sh /terra-helper/
COPY terra-helper/summarize_copy_log.py /terra-helper/
COPY terra-helper/endpoints/ /terra-helper/endpoints/
COPY terra-helper/README.md /terra-helper/

COPY docs/* /docs/
COPY README.md /
COPY Dockerfile /

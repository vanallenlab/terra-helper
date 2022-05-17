FROM vanallenlab/miniconda:3.6

RUN apt-get update && apt-get upgrade -y && apt-get install -y curl
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY copy_bucket.sh /
COPY copy_bucket-mirror.sh /
COPY copy_multiple_buckets.sh /
COPY create_workspace.py /
COPY estimate_archive_and_retrieval_cost.py /
COPY get_file_sizes.sh /
COPY index_workspace.py /
COPY list_source_files.py /
COPY list_workspaces.py /
COPY remove_files.sh /
COPY restore_bucket.sh /
COPY restore_files.sh /

COPY use-cases/ /use-cases/
COPY README.md /
COPY documentation.md /
COPY Dockerfile /

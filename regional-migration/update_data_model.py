import argparse
import io
import pandas as pd
import requests
import subprocess
import sys
import zipfile

from oauth2client.client import GoogleCredentials

ROOT = 'https://api.firecloud.org/api'


# Fetch workspace annotations
## See if there are any workspace annotations
# Fetch entity types from workspace
## Loop through each column
## Save the entity:{data type} column
## If string in column, then replace and append to new column
## Post new datamodel

def generate_headers():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    return {"Authorization": f"bearer {token}"}


def import_tsv(handle, delimiter='\t'):
    return pd.read_csv(handle, sep=delimiter)


def request_check(response, url):
    if response.status_code != 200:
        sys.exit(f"{url} returned {response.status_code} \n\n {response.content}")
    return response


def request_content_to_tsv(content):
    return pd.read_csv(io.StringIO(content.decode('utf-8')), sep='\t', low_memory=False)


def request_zipped_content_to_tsv(content, entity_type):
    z = zipfile.ZipFile(io.BytesIO(content))
    filename = f"{entity_type}_entity.tsv"
    return request_content_to_tsv(z.read(filename))


def request_get(url, headers, data=None):
    if not data:
        response = requests.get(url, headers=headers)
    else:
        response = requests.get(url, headers=headers, data=data)
    return request_check(response, url)


def update_data_models(namespace, name, bucket_lookup):
    subprocess.call(f"mkdir -p {namespace}", shell=True)

    headers = generate_headers()
    entity_types = request_get(f"{ROOT}/workspaces/{namespace}/{name}/entities", headers=headers)
    for entity_type in list(entity_types.json().keys()):
        response = request_get(f"{ROOT}/workspaces/{namespace}/{name}/entities/{entity_type}/tsv", headers=headers)
        if (entity_type == 'sample_set') | (entity_type == 'pair_set') | (entity_type == 'participant_set'):
            table = request_zipped_content_to_tsv(response.content, entity_type)
        else:
            table = request_content_to_tsv(response.content)
        revised_table = table.loc[:, [f'entity:{entity_type}_id']]
        for column in table:
            for source_bucket, destination_bucket in bucket_lookup.items():
                if f'gs://{source_bucket}' in table[column].tolist():
                    print(column, source_bucket, destination_bucket)
                    revised_column = table[column].str.replace(f"gs://{source_bucket}",
                                                               f"gs://{destination_bucket}/{source_bucket}")
                    revised_table.append(revised_column)
        table.to_csv(f"{namespace}/{name}.{entity_type}.tsv", sep='\t', index=False)
        revised_table.to_csv(f"{namespace}/{name}.{entity_type}.revised.tsv", sep='\t', index=False)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Update data model',
                                         description="Search and replace for other buckets moved to regional storage")
    arg_parser.add_argument('--namespace', required=True, help='Workspace namespace')
    arg_parser.add_argument('--name', required=True, help='Workspace name')
    arg_parser.add_argument('--tsv', '-t', required=True, help='Participants table from migration workspace')
    args = arg_parser.parse_args()

    reference = import_tsv(args.tsv)
    lookup = (reference
              .loc[:, ['source_bucket', 'destination_bucket']]
              .set_index('source_bucket')
              .to_dict()
              ['destination_bucket']
    )
    update_data_models(args.namespace, args.name, lookup)


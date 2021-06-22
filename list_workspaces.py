import argparse
import pandas as pd
import requests
from datetime import date
from google.cloud import storage
from oauth2client.client import GoogleCredentials

LAB_TAGS = [
    'archive',
    'Archive',
    'cleaner-bot-opt-in',
    'cleaner-bot-opt-out',
    'datamodel',
    'storage',
    'vanallen-methods',
    'vanallen-reference',
    'vanallen-cohort',
    'archived',
    'cleaner-bot-storage',
    'cleaner-bot-history',
    'migrated-to-nih',
    'migrated-to-regional-storage',
    'not-migrating-to-regional-storage'
]

NAMESPACES = [
    'nci-breardon-bi-org',
    'nci-mxhe-bi-org',
    'vanallen-firecloud-dfci',
    'vanallen-germline',
    'vanallen-liulab',
    'vanallen-melanoma-wgs',
    'vanallen-firecloud-nih',
    'vanallen-nih-ped'
]

OUTPUT_COLUMNS_BASE = ['namespace', 'workspace', 'bucket', 'location_type', 'location',
                       'storage_bytes', 'storage_binary_gigabytes', 'storage_binary_terabytes', 'cost_per_month',
                       'last_modified', 'created_by']

ROOT = 'https://api.firecloud.org/api'


def calculate_monthly_cost(location_type, size_terabytes):
    multiple = 26 if location_type == 'multi-region' else 20
    return multiple * size_terabytes


def convert_bytes(size_bytes, denominator):
    return size_bytes / denominator


def create_default_output_filename():
    prefix = get_date()
    return f'{prefix}.workspaces_storage.txt'


def create_workspace_series(workspace_dictionary, headers, storage_client):
    namespace = workspace_dictionary['workspace']['namespace']
    name = workspace_dictionary['workspace']['name']
    bucket_name = workspace_dictionary['workspace']['bucketName']

    series = pd.Series(index=OUTPUT_COLUMNS_BASE, dtype=str)
    series.loc['namespace'] = namespace
    series.loc['workspace'] = name
    series.loc['bucket'] = bucket_name

    bucket = storage_client.get_bucket(bucket_name)
    bucket_location_type = bucket.location_type
    bucket_location = bucket.location
    series.loc['location_type'] = bucket_location_type
    series.loc['location'] = bucket_location

    response = get_bucket_usage(namespace, name, headers)
    if response.status_code in [200]:
        storage_bytes = response.json()['usageInBytes']
        storage_binary_gigabytes = convert_bytes(storage_bytes, 2 ** 30)
        storage_binary_terabytes = convert_bytes(storage_bytes, 2 ** 40)

        series.loc['storage_bytes'] = storage_bytes
        series.loc['storage_binary_gigabytes'] = storage_binary_gigabytes
        series.loc['storage_binary_terabytes'] = storage_binary_terabytes
        series.loc['cost_per_month'] = calculate_monthly_cost(bucket_location_type, storage_binary_terabytes)
    else:
        series.loc['storage_bytes'] = pd.NA
        series.loc['storage_binary_gigabytes'] = pd.NA
        series.loc['storage_binary_terabytes'] = pd.NA
        series.loc['cost_per_month'] = pd.NA
    series.loc['last_modified'] = workspace_dictionary['workspace']['lastModified']
    series.loc['created_by'] = workspace_dictionary['workspace']['createdBy']
    return series


def generate_header():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    return {"Authorization": f"bearer {token}"}


def get_bucket_usage(namespace, name, headers):
    request = f'{ROOT}/workspaces/{namespace}/{name}/bucketUsage'
    return requests.get(request, headers=headers)


def get_date(date_format="%Y-%m-%d"):
    return date.today().strftime(date_format)


def get_workspaces(headers):
    request = f'{ROOT}/workspaces'
    return requests.get(request, headers=headers)


def list_workspace_tags(workspaces):
    tagged_workspaces = [workspace for workspace in workspaces if "tag:tags" in workspace['workspace']['attributes']]
    workspace_tags = []
    count = 0

    for workspace in tagged_workspaces:
        tmp_tags = return_tags(workspace)
        for tag in tmp_tags:
            workspace_tags.append({
                'namespace': workspace['workspace']['namespace'],
                'workspace': workspace['workspace']['name'],
                'tag': tag,
                'workspace-id': count
            })
        count += 1
    return pd.DataFrame(workspace_tags)


def pivot_tags(tags_by_workspace):
    tags_by_workspace['value'] = 1
    pivoted = (
        tags_by_workspace
        .pivot(index='workspace-id', columns='tag', values='value')
        .reindex(LAB_TAGS, axis='columns')
        .fillna(0)
        .reset_index()
    )
    return (
        tags_by_workspace
        .loc[:, ['namespace', 'workspace', 'workspace-id']]
        .drop_duplicates()
        .merge(pivoted, on='workspace-id', how='left')
        .drop('workspace-id', axis=1)
    )


def return_tags(workspace_dictionary):
    return sorted(workspace_dictionary['workspace']['attributes']['tag:tags']['items'])


def write_dataframe(dataframe, handle):
    dataframe.to_csv(handle, sep='\t', index=False)


def list_workspaces(output_filename=None, list_tags=False):
    if not output_filename:
        output_filename = create_default_output_filename()
    headers = generate_header()
    response = get_workspaces(headers)
    storage_client = storage.Client()

    if response.status_code not in [200]:
        return response.status_code, response.content

    workspaces_all = response.json()
    workspaces = [workspace for workspace in workspaces_all if workspace['workspace']['namespace'] in NAMESPACES]

    workspaces_list = []
    for workspace in workspaces:
        workspace_series = create_workspace_series(workspace, headers, storage_client)
        workspaces_list.append(workspace_series)

    dataframe = pd.concat(workspaces_list, axis=1).T.sort_values('cost_per_month', ascending=False)

    if list_tags:
        workspace_tags = list_workspace_tags(workspaces)
        dataframe_tags = pivot_tags(workspace_tags)
        dataframe = dataframe.merge(dataframe_tags, on=['namespace', 'workspace'], how='left')
        dataframe.loc[:, LAB_TAGS] = dataframe.loc[:, LAB_TAGS].fillna(0)
        dataframe['no tags'] = dataframe.loc[:, LAB_TAGS].astype(int).sum(axis=1).eq(0).astype(int)

    write_dataframe(dataframe, output_filename)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Create workspace', description="Create a single region workspace")
    arg_parser.add_argument('--output', '-o', default=None, help='Output file name')
    arg_parser.add_argument('--tags', '-t', action='store_true', help='List workspace tags')
    args = arg_parser.parse_args()

    list_workspaces(args.output, args.tags)

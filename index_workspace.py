import argparse
import io
import pandas as pd
import requests
import subprocess
import zipfile
from oauth2client.client import GoogleCredentials

root = 'https://api.firecloud.org/api'


def calculate_usage(usage_bytes):
    usage_gigabytes = float(usage_bytes) / 10 ** 9
    usage_terabytes = float(usage_bytes) / 10 ** 12
    monthly_cost = float(usage_terabytes) * 26
    return usage_gigabytes, usage_terabytes, monthly_cost


def check_request(response, failure_message):
    if response.status_code not in [200, 201, 204]:
        return {'message': failure_message,
                'response': response,
                'response_status_code': response.status_code,
                'response_content': response.content}
    else:
        return {'message': 'success!',
                'response': response,
                'response_status_code': response.status_code,
                'response_content': response.content}


def format_request_to_tsv(string_tsv):
    return pd.read_csv(io.StringIO(string_tsv.decode('utf-8')), sep='\t', low_memory=False)


def format_usage(response):
    return response.json()['usageInBytes']


def generate_header():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    return {"Authorization": f"bearer {token}"}


def get_bucket_usage(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'bucketUsage'])
    return requests.get(request, headers=headers)


def get_entity_types(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'entities'])
    return requests.get(request, headers=headers)


def get_entity_type_datamodel(namespace, name, headers, entity_type):
    request = '/'.join([root, 'workspaces', namespace, name, 'entities', entity_type, 'tsv'])
    return requests.get(request, headers=headers)


def get_entity_type_set_datamodel(namespace, name, headers, entity_type):
    response = get_entity_type_datamodel(namespace, name, headers, entity_type)
    z = zipfile.ZipFile(io.BytesIO(response.content))
    data_model_attributes = []
    for suffix in ['membership.tsv', 'entity.tsv']:
        filename = f'{entity_type}_{suffix}'
        table = z.read(filename)
        entity_data_frame = format_request_to_tsv(table)
        entity_list = list_datamodel_columns(entity_data_frame)
        data_model_attributes.extend(entity_list)
    return data_model_attributes


def get_workspace(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name])
    return requests.get(request, headers=headers)


def get_workspace_attributes(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'exportAttributesTSV'])
    return requests.get(request, headers=headers)


def glob_bucket(bucket):
    cmd = ''.join(['gsutil ls gs://', bucket, '/**'])
    bucket_files = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE)
    series = pd.read_csv(io.StringIO(bucket_files.decode('utf-8')), sep='\n', header=None).loc[:, 0]
    return series.tolist()


def keep_df_add(df, list_of_keepers, rationale_column):
    new_index = df.index.union(pd.Index(list_of_keepers))
    new_df = df.reindex(new_index)
    new_df.loc[list_of_keepers, rationale_column] = int(1)
    return new_df


def keep_df_create():
    columns = ['keep-suffix', 'in-datamodel_same-bucket', 'in-datamodel_other-bucket']
    return pd.DataFrame(0, columns=columns, index=[])


def list_paths(list_of_paths):
    paths = ['/'.join(handle.split('/')[:-1]) for handle in list_of_paths]
    return list(set(paths))


def list_datamodel_columns(dataframe):
    list_ = []
    for col in dataframe.columns:
        list_.extend(dataframe.loc[:, col].tolist())
    return list_


def list_entity_types(namespace, name, headers):
    r = get_entity_types(namespace, name, headers)
    check_r = check_request(r, 'Failed to get entity types from workspace')
    if check_r['message'] != 'success!':
        return print_json(check_r)
    else:
        return list(r.json().keys())


def list_workspace_attributes(namespace, name, headers):
    r = get_workspace_attributes(namespace, name, headers)
    check_r = check_request(r, 'Failed to get workspace annotations')
    if check_r['message'] != 'success!':
        return print_json(check_r)
    else:
        df = format_request_to_tsv(r.content)
        if df.shape[0] != 0:
            return df.loc[0, :].tolist()
        else:
            return []


def print_json(data):
    for key, value in data.items():
        print(key, value)
        print('')


def subset_attributes(bucket_name, entities_list, workspace_list):
    bucket_id = ''.join(['gs://', bucket_name])
    combined_list = pd.Series(entities_list + workspace_list).dropna().drop_duplicates()

    idx_in_bucket = combined_list.str[:len(bucket_id)].eq(bucket_id)
    idx_gs_path = combined_list.str[:5].eq('gs://')
    idx_other_bucket = ~idx_in_bucket & idx_gs_path

    in_bucket = combined_list[idx_in_bucket]
    in_other_bucket = combined_list[idx_other_bucket]
    not_a_path = combined_list[~idx_gs_path]
    return in_bucket.tolist(), in_other_bucket.tolist(), not_a_path


def subset_attributes_in_bucket(bucket_name, entities_list, workspace_list):
    bucket_id = ''.join(['gs://', bucket_name])
    combined_list = entities_list + workspace_list
    return [blob for blob in combined_list if str(blob).startswith(bucket_id)]


def subset_attributes_in_other_bucket(in_bucket_attributes, entities_list, workspace_list):
    combined_list = entities_list + workspace_list
    return [blob for blob in combined_list if blob not in in_bucket_attributes and str(blob)[:5] == 'gs://']


def subset_blobs_by_suffix(list_blobs, suffixes):
    series = pd.Series(list_blobs)
    remove_blobs = series.copy(deep=True)
    for suffix in suffixes:
        idx_suffix = remove_blobs.str[-len(suffix):].eq(suffix)
        remove_blobs = remove_blobs[~idx_suffix]
    keep_blobs = series[~series.isin(remove_blobs)]
    return keep_blobs.tolist(), remove_blobs.tolist()


def subset_blobs_for_attribute_paths(paths, all_blobs):
    datamodel_blobs = []
    for path in paths:
        datamodel_blobs.extend([handle for handle in all_blobs if path in handle])
    return datamodel_blobs


def index(namespace, name, keeping_related_files, headers, suffixes):
    print(f'Indexing {namespace}/{name}')
    print("All files in the workspace's bucket that do not either appear in the data model or as a workspace "
          "annotation will be listed. Please do not have any running jobs.")
    if keeping_related_files:
        print("Also, any files within the same directory as any of the files above will not be listed.")

    request_workspace = get_workspace(namespace, name, headers)
    check_r = check_request(request_workspace, 'Failed to get workspace')
    if check_r['message'] != 'success!':
        return print_json(check_r)

    # Get workspace current storage usage
    bucket_name = request_workspace.json()['workspace']['bucketName']
    request_usage = get_bucket_usage(namespace, name, headers)
    check_r = check_request(request_usage, 'Failed to get workspace bucket usage')
    if check_r['message'] != 'success!':
        return print_json(check_r)

    usage_bytes = format_usage(request_usage)
    usage_gigabytes, usage_terabytes, monthly_cost = calculate_usage(usage_bytes)
    print(' '.join(['Bucket name:', str(bucket_name)]))
    print(' '.join(['Storage used (Gigabytes):', str(round(usage_gigabytes, 3))]))
    print(' '.join(['Monthly cost of storage ($):', str(round(monthly_cost, 2))]))
    print('')

    # Get attributes in datamodel that are in this workspace's bucket
    entity_types = list_entity_types(namespace, name, headers)
    datamodel_attributes = []
    for entity_type in entity_types:
        if (entity_type == 'sample_set') | (entity_type == 'pair_set') | (entity_type == 'participant_set'):
            entity_type_attributes = get_entity_type_set_datamodel(namespace, name, headers, entity_type)
            datamodel_attributes.extend(entity_type_attributes)
        else:
            entity_tsv = get_entity_type_datamodel(namespace, name, headers, entity_type)
            entity_dataframe = format_request_to_tsv(entity_tsv.content)
            entity_list = list_datamodel_columns(entity_dataframe)
            datamodel_attributes.extend(entity_list)
    workspace_attributes = list_workspace_attributes(namespace, name, headers)

    in_bucket, other_bucket, not_a_path = subset_attributes(bucket_name, datamodel_attributes, workspace_attributes)
    attributes_in_bucket = in_bucket
    attributes_in_other_bucket = other_bucket

    keep_df = keep_df_create()
    keep_df = keep_df_add(keep_df, attributes_in_bucket, 'in-datamodel_same-bucket')
    keep_df = keep_df_add(keep_df, attributes_in_other_bucket, 'in-datamodel_other-bucket')

    all_blobs_in_bucket = glob_bucket(bucket_name)
    if keeping_related_files:
        attribute_paths = list_paths(attributes_in_bucket)
        attribute_blobs = subset_blobs_for_attribute_paths(attribute_paths, all_blobs_in_bucket)
        blobs_to_remove = list(set(all_blobs_in_bucket) - set(attribute_blobs))
        keep_df = keep_df_add(keep_df, attribute_blobs, 'in-datamodel_same-bucket')
    else:
        blobs_to_remove = list(set(all_blobs_in_bucket) - set(attributes_in_bucket))

    if suffixes:
        keep_blobs, blobs_to_remove = subset_blobs_by_suffix(blobs_to_remove, suffixes)
        keep_df = keep_df_add(keep_df, keep_blobs, 'keep-suffix')

    print(f"Total files in {namespace}/{name}'s bucket: {len(all_blobs_in_bucket)}")
    print(f"Total files to delete in {namespace}/{name}'s bucket: {len(blobs_to_remove)}")
    print(f"Writing files to remove to {namespace}.{name}.files_to_remove.txt in current working directory")
    output = f"{namespace}.{name}.files_to_remove.txt"
    pd.Series(blobs_to_remove).to_csv(output, sep='\t', index=False, header=False)
    print('')

    print(f"Total files in {namespace}/{name}'s data model that are not in `files_to_remove`: {keep_df.shape[0]}")
    print(f"Writing this list to {namespace}.{name}.files_keep.txt in current working directory")
    output_keeps = f"{namespace}.{name}.files_keep.txt"
    keep_df.to_csv(output_keeps, sep='\t', index_label='file')
    print('')

    print(f'Some data model elements were not paths, these have been written to '
          f'{namespace}/{name}.datamodel_not_paths.txt in the current working directory.')
    output_not_paths = f"{namespace}.{name}.datamodel_not_paths.txt"
    not_a_path.to_csv(output_not_paths, sep='\t', index=False, header=False)
    print('')


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Index Terra workspace',
                                         description="Creates a list of files present in the workspace's bucket that "
                                                     "are not in the data model or workspace annotations.")
    arg_parser.add_argument('--namespace', required=True,
                            help='Workspace namespace')
    arg_parser.add_argument('--name', required=True,
                            help='Workspace name')
    arg_parser.add_argument('--keep', '-k', nargs='*', action='append', default=[],
                            help='File suffixes to keep')
    arg_parser.add_argument('--keep_related_files', action='store_true',
                            help='Files in all tail directories will be kept if passed, significantly adds to runtime.')
    args = arg_parser.parse_args()

    input_namespace = args.namespace
    input_name = args.name
    input_keep_suffixes = args.keep
    input_keep_related_files = args.keep_related_files
    HEADERS = generate_header()

    if input_keep_suffixes:
        keep_suffixes = [suffix[0] for suffix in input_keep_suffixes]
    else:
        keep_suffixes = []

    index(input_namespace, input_name, input_keep_related_files, HEADERS, keep_suffixes)

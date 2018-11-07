import time
import argparse
import pandas as pd
import requests
import subprocess
import io
import zipfile
from oauth2client.client import GoogleCredentials

root = 'https://api.firecloud.org/api'


def generate_header():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    headers = {"Authorization": "bearer " + token}
    return headers


def print_json(data):
    for key, value in data.items():
        print(key, value)
        print('')


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
    return pd.read_csv(io.StringIO(string_tsv.decode('utf-8')), sep='\t')


def format_usage(response):
    return response.json()['usageInBytes']


def calculate_usage(usage_bytes):
    usage_gigabytes = float(usage_bytes) / 10 ** 9
    usage_terabytes = float(usage_bytes) / 10 ** 12
    monthly_cost = float(usage_terabytes) * 26
    return usage_gigabytes, usage_terabytes, monthly_cost


def calculate_egress_cost(number_of_files):
    cost_per_operation = 0.05 / 10000
    return float(cost_per_operation) * float(number_of_files)


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
    filename = '_'.join([entity_type, 'membership.tsv'])
    return z.read(filename)


def get_workspace(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name])
    return requests.get(request, headers=headers)


def get_workspace_attributes(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'exportAttributesTSV'])
    return requests.get(request, headers=headers)


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
        return df.loc[0, :].tolist()


def remove_logs_from_blobs(blobs):
    no_stdout = (blob for blob in blobs if not str(blob).endswith('stdout'))
    no_stderr = (blob for blob in no_stdout if not str(blob).endswith('stderr'))
    no_logs = (blob for blob in no_stderr if not str(blob).endswith('.log'))
    no_rc = (blob for blob in no_logs if not str(blob).endswith('rc'))
    no_exec = (blob for blob in no_rc if not str(blob).endswith('exec.sh'))
    no_script = (blob for blob in no_exec if not str(blob).endswith('script'))
    return list(no_script)


def subset_attributes_in_bucket(bucket_name, entities_list, workspace_list):
    bucket_id = ''.join(['gs://', bucket_name])
    combined_list = entities_list + workspace_list
    return [blob for blob in combined_list if str(blob).startswith(bucket_id)]


def subset_blobs_for_attribute_paths(paths, all_blobs):
    datamodel_blobs = []
    for path in paths:
        datamodel_blobs.extend([handle for handle in all_blobs if path in handle])
    return datamodel_blobs


def glob_bucket(bucket):
    cmd = ''.join(['gsutil ls gs://', bucket, '/**'])
    bucket_files = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE)
    series = pd.read_csv(io.StringIO(bucket_files.decode('utf-8')), sep='\n', header=-1).loc[:, 0]
    return series.tolist()


def remove_files(files_list, chunksize):
    n = chunksize
    list_of_lists = [files_list[i * n:(i + 1) * n] for i in range((len(files_list) + n - 1) // n)]

    headers = generate_header()

    counter = 0
    for chunk in list_of_lists:
        cmd = ' '.join(['gsutil -m rm'] + chunk)
        subprocess.call(cmd, shell=True)
        counter = counter + 1

        # refresh headers if taking too long
        if chunksize*counter > 100000:
            headers = generate_header()
            counter = 0

    print(str(len(files_list)) + ' files removed')
    return headers


def index(namespace, name, headers, keep_logs, index_name):
    print('Cleaning up workspace, indexing bucket')
    print(' '.join(['Namespace:', str(namespace)]))
    print(' '.join(['Name:', str(name)]))
    print('')

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
        if (entity_type == 'sample_set') | (entity_type == 'pair_set'):
            entity_tsv = get_entity_type_set_datamodel(namespace, name, headers, entity_type)
            entity_dataframe = format_request_to_tsv(entity_tsv)
        else:
            entity_tsv = get_entity_type_datamodel(namespace, name, headers, entity_type)
            entity_dataframe = format_request_to_tsv(entity_tsv.content)
        entity_list = list_datamodel_columns(entity_dataframe)
        datamodel_attributes.extend(entity_list)

    workspace_attributes = list_workspace_attributes(namespace, name, headers)
    attributes_in_bucket = subset_attributes_in_bucket(bucket_name, datamodel_attributes, workspace_attributes)
    attribute_paths = list_paths(attributes_in_bucket)

    all_blobs_in_bucket = glob_bucket(bucket_name)

    # Subset to keep files in folders that are in the data model
    attribute_blobs = subset_blobs_for_attribute_paths(attribute_paths, all_blobs_in_bucket)
    blobs_to_remove = list(set(all_blobs_in_bucket) - set(attribute_blobs))
    if keep_logs:
        # Keeps logs of other folders
        blobs_to_remove = remove_logs_from_blobs(blobs_to_remove)
    else:
        blobs_to_remove = blobs_to_remove

    files_to_remove = blobs_to_remove
    print(' '.join(["Total files in workspace's bucket:", str(len(all_blobs_in_bucket))]))
    print(' '.join(["Number of files to delete:", str(len(files_to_remove))]))
    print(' '.join(["Cost of indexing:", str(calculate_egress_cost(len(all_blobs_in_bucket)))]))

    print(' '.join(["Writing files to remove to", index_name]))
    pd.Series(files_to_remove).to_csv(index_name, sep='\t', index=False)


def clean(namespace, name, headers, filename, chunksize, dryrun):
    summary = pd.Series(name = 'summary',
                        index = ['namespace', 'name',
                                 'initial_bucket_size_gb', 'initial_bucket_monthly_cost_$',
                                 'number_of_files_to_delete',
                                 'updated_bucket_size_gb', 'updated_bucket_monthly_cost_$'])
    print('Cleaning up workspace, cleaning bucket')
    print(' '.join(['Namespace:', str(namespace)]))
    print(' '.join(['Name:', str(name)]))
    print('')

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
    initial_gigabytes = usage_gigabytes
    initial_cost = monthly_cost
    print(' '.join(['Bucket name:', str(bucket_name)]))
    print(' '.join(['Storage used (Gigabytes):', str(round(usage_gigabytes, 3))]))
    print(' '.join(['Monthly cost of storage ($):', str(round(monthly_cost, 2))]))
    print('')

    summary.loc['namespace'] = namespace
    summary.loc['name'] = name
    summary.loc['initial_bucket_size_gb'] = usage_gigabytes
    summary.loc['initial_bucket_monthly_cost_$'] = monthly_cost

    blobs_to_delete = pd.read_csv(filename, sep='\t', header=-1)
    blobs_to_delete = blobs_to_delete.loc[:, 0].tolist()

    summary.loc['number_of_files_to_delete'] = len(blobs_to_delete)

    if dryrun:
        print("This is a dry run, no files will be deleted")
        headers = headers
    else:
        print(''.join(['Number of files to delete:', str(len(blobs_to_delete))]))
        headers = remove_files(blobs_to_delete, chunksize)

    # Get workspace current storage usage
    bucket_name = request_workspace.json()['workspace']['bucketName']
    request_usage = get_bucket_usage(namespace, name, headers)
    check_r = check_request(request_usage, 'Failed to get workspace bucket usage')
    if check_r['message'] != 'success!':
        return print_json(check_r)

    usage_bytes = format_usage(request_usage)
    usage_gigabytes, usage_terabytes, monthly_cost = calculate_usage(usage_bytes)
    new_gigabytes = usage_gigabytes
    new_cost = monthly_cost
    print(' '.join(['Bucket name:', str(bucket_name)]))
    print(' '.join(['Storage used (Gigabytes):', str(round(usage_gigabytes, 3))]))
    print(' '.join(['Monthly cost of storage ($):', str(round(monthly_cost, 2))]))
    print('')

    summary.loc['updated_bucket_size_gb'] = usage_gigabytes
    summary.loc['updated_bucket_monthly_cost_$'] = monthly_cost

    outname = '.'.join([namespace, name, 'clean', 'summary', 'txt'])
    summary.to_csv(outname, sep='\t')

    difference_gigabytes = initial_gigabytes - new_gigabytes
    difference_cost = initial_cost - new_cost
    print(' '.join(['You cleaned up', str(difference_gigabytes), 'of data.']))
    print(' '.join(['This clean up will save the lab', str(difference_cost), 'per month.']))
    print('')

    print('Note: You actually did save money!\n'
          'FireCloud caches the storage costs once per day to save money. Check back tomorrow :)')
    print('In the meantime, go ask Eli to buy lunch')
    print('')


if __name__ == "__main__":
    start_time = time.time()

    arg_parser = argparse.ArgumentParser(prog='FireCloud workspace cleaner',
                                         description='Delete files in a workspace that are not in the data model.')
    arg_parser.add_argument('--namespace', required=True,
                            help='Workspace namespace')
    arg_parser.add_argument('--name', required=True,
                            help='Workspace name')

    arg_parser.add_argument('--filename', default='files_to_remove.(namespace).(name).txt',
                            help='Filename for files to remove')

    arg_parser.add_argument('--index', action='store_true',
                            help='Index workspace for files to remove, outputs to --filename')
    arg_parser.add_argument('--keeplogs', action='store_true',
                            help='Boolean for keeping log files for folders not in data model')

    arg_parser.add_argument('--clean', action='store_true',
                            help='Reads --filename and deletes the files')
    arg_parser.add_argument('--chunksize', default=500,
                            help='Number of files to remove at once')
    arg_parser.add_argument('--dryrun', action='store_true',
                            help='If passed, will clean without deleting files so you can see the output.')
    args = arg_parser.parse_args()

    headers = generate_header()

    input_namespace = args.namespace
    input_name = args.name
    input_filename = args.filename
    input_index = args.index
    input_keeplogs = args.keeplogs
    input_clean = args.clean
    input_chunksize = int(args.chunksize)
    input_dryrun = args.dryrun

    if input_filename == 'files_to_remove.(namespace).(name).txt':
        input_filename = '.'.join(['files_to_remove', input_namespace, input_name, 'txt'])

    if input_index:
        index(input_namespace, input_name, headers, input_keeplogs, input_filename)
    elif input_clean:
        clean(input_namespace, input_name, headers, input_filename, input_chunksize, input_dryrun)
    else:
        print('Please specify --index or --clean')

    end_time = time.time()
    time_statement = "Workspace cleaning runtime: %s seconds" % round((end_time - start_time), 4)
    print(time_statement)

import time
import argparse
import pandas as pd
import requests
import subprocess
import io
from oauth2client.client import GoogleCredentials

root = 'https://api.firecloud.org/api'

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


def get_bucket_usage(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'bucketUsage'])
    return requests.get(request, headers=headers)


def get_entity_types(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'entities'])
    return requests.get(request, headers=headers)


def get_entity_type_datamodel(namespace, name, headers, entity_type):
    request = '/'.join([root, 'workspaces', namespace, name, 'entities', entity_type, 'tsv'])
    return requests.get(request, headers=headers)


def get_workspace(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name])
    return requests.get(request, headers=headers)


def get_workspace_attributes(namespace, name, headers):
    request = '/'.join([root, 'workspaces', namespace, name, 'exportAttributesTSV'])
    return requests.get(request, headers=headers)


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


def list_entity_type_datamodel(namespace, name, headers, entity_type):
    check_r = check_request(r, 'Failed to get datamodel for ' + entity_type)
    if check_r['message'] != 'success!':
        return print_json(check_r)
    else:
        df = format_request_to_tsv(r.content)
        return list_datamodel_columns(df)


def list_workspace_attributes(namespace, name, headers):
    r = get_workspace_attributes(namespace, name, headers)
    check_r = check_request(r, 'Failed to get workspace annotations')
    if check_r['message'] != 'success!':
        return print_json(check_r)
    else:
        df = format_request_to_tsv(r.content)
        return df.loc[0, :].tolist()


def remove_logs_from_blobs(blobs):
    no_stdout = [blob for blob in blobs if not str(blob).endswith('stdout')]
    no_stderr = [blob for blob in no_stdout if not str(blob).endswith('stderr')]
    no_logs = [blob for blob in no_stderr if not str(blob).endswith('.log')]
    no_rc = [blob for blob in no_logs if not str(blob).endswith('rc')]
    no_exec = [blob for blob in no_rc if not str(blob).endswith('exec.sh')]
    no_script = [blob for blob in no_exec if not str(blob).endswith('script')]
    return no_script


def subset_attributes_in_bucket(bucket_name, entities_list, workspace_list):
    bucket_id = ''.join(['gs://', bucket_name])
    combined_list = entities_list + workspace_list
    return [blob for blob in combined_list if str(blob).startswith(bucket_id)]


def glob_bucket(bucket):
    cmd = ''.join(['gsutil ls gs://', bucket, '/**'])
    bucket_files = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE)
    series = pd.read_csv(io.StringIO(bucket_files.decode('utf-8')), sep='\n', header=-1).loc[:, 0]
    return series.tolist()


def remove_files(files_list, chunksize):
    n = chunksize
    list_of_lists = [files_list[i * n:(i + 1) * n] for i in range((len(files_list) + n - 1) // n)]

    for chunk in list_of_lists:
        cmd = ' '.join(['gsutil -m rm'] + chunk)
        subprocess.call(cmd, shell=True)
    print(str(len(files_list)) + 'files removed')


def main(namespace, name, headers, chunksize, filename, dry_run=True):
    print('Cleaning up workspace')
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

    # Get attributes in datamodel that are in this workspace's bucket
    entity_types = list_entity_types(namespace, name, headers)
    datamodel_attributes = []
    for entity_type in entity_types:
        # Sets return a different type of encoded response. Sent Alex a msg on how to handle this
        if entity_type == 'sample_set':
            continue
        elif entity_type == 'pair_set':
            continue
        else:
            entity_tsv = get_entity_type_datamodel(namespace, name, headers, entity_type)
            entity_dataframe = format_request_to_tsv(entity_tsv.content)
            entity_list = list_datamodel_columns(entity_dataframe)
            datamodel_attributes.extend(entity_list)

    workspace_attributes = list_workspace_attributes(namespace, name, headers)
    attributes_in_bucket = subset_attributes_in_bucket(bucket_name, datamodel_attributes, workspace_attributes)
    all_blobs_in_bucket = glob_bucket(bucket_name)
    all_blobs_in_bucket_except_logs = remove_logs_from_blobs(all_blobs_in_bucket)
    files_to_remove = list(set(all_blobs_in_bucket_except_logs) - set(attributes_in_bucket))
    print(' '.join(["Total files in workspace's bucket:", str(len(all_blobs_in_bucket))]))
    print(
        ' '.join(["Total files in workspace's bucket, not counting logs:", str(len(all_blobs_in_bucket_except_logs))]))
    print(' '.join(["Total files in data model in workspace's bucket:", str(len(attributes_in_bucket))]))
    print(' '.join(["Number of files to delete:", str(len(files_to_remove))]))

    print(' '.join(["Writing files to remove to", filename]))
    pd.Series(files_to_remove).to_csv(filename, sep='\t', index=False)
    if dry_run:
        return print("Check this file and then rerun with --clean")
    else:
        print("Removing files...")
        remove_files(files_to_remove, chunksize)
        print("Files removed")

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
        difference_gigabytes = initial_gigabytes - new_gigabytes
        difference_cost = initial_cost - new_cost
        print(' '.join(['You cleaned up', str(difference_gigabytes), 'of data.']))
        print(' '.join(['This clean up will save the lab', str(difference_cost), 'per month.']))
        return print('Now go ask Eli to buy you lunch')

if __name__ == "__main__":
    start_time = time.time()

    arg_parser = argparse.ArgumentParser(prog='FireCloud workspace cleaner',
                                         description='Delete files in a workspace that are not in the data model.')
    arg_parser.add_argument('--namespace', help='Workspace namespace', required=True)
    arg_parser.add_argument('--name', help='Workspace name', required=True)
    arg_parser.add_argument('--clean', help='Flag to not do a dry run', action='store_true')
    arg_parser.add_argument('--chunksize',
                            help='Number of files to remove at once, default = 500', default=500)
    arg_parser.add_argument('--filename', default='files_to_remove.txt',
                            help='Filename for files to remove, default = files_to_remove.txt')
    args = arg_parser.parse_args()

    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    headers = {"Authorization": "bearer " + token}

    inputs_dict = {
        'namespace': args.namespace,
        'name': args.name,
        'clean': args.clean,
        'chunksize': int(args.chunksize),
        'filename': args.filename
    }

    if inputs_dict['clean']:
        main(inputs_dict['namespace'], inputs_dict['name'], headers,
             chunksize=inputs_dict['chunksize'], filename=inputs_dict['filename'],
             dry_run=False)
    else:
        main(inputs_dict['namespace'], inputs_dict['name'], headers,
             chunksize=inputs_dict['chunksize'], filename=inputs_dict['filename'])

    end_time = time.time()
    time_statement = "Workspace cleaning runtime: %s seconds" % round((end_time - start_time), 4)
    print(time_statement)

import argparse
import io
import pandas as pd
import subprocess

from endpoints import terra
import reformat


def get_bucket_name(response):
    return response['workspace']['bucketName']


def get_gsutil_path():
    cmd = "which gsutil"
    path = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE)
    return path.decode("utf-8").replace("\n", "")


def glob_bucket(bucket):
    cmd = f"{get_gsutil_path()} ls gs://{bucket}/**"
    bucket_files = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE)
    series = pd.read_csv(io.StringIO(bucket_files.decode('utf-8')),  header=None).loc[:, 0]
    return series.tolist()


def request_workspace(namespace, name):
    return terra.Terra.request(terra.Terra.get_workspace, namespace=namespace, name=name)


def main(namespace, name):
    workspace = request_workspace(namespace, name)
    bucket = get_bucket_name(workspace)
    contents = glob_bucket(bucket)
    return contents


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Get workspace bucket contents',
                                     description='List all files contained in workspace bucket.'
                                                 'This will take several minutes to hours to run depending on workspace'
                                                 'size.')
    parser.add_argument('--namespace', '-ns', type=str, required=True, help='workspace namespace')
    parser.add_argument('--name', '-n', type=str, required=True, help='workspace name')
    args = parser.parse_args()

    workspace_namespace = args.namespace
    workspace_name = args.name
    if " " in workspace_name:
        workspace_name = workspace_name.replace(' ', '%20')

    result = main(args.namespace, args.name)
    (pd
     .Series(result)
     .to_csv(f'{workspace_namespace}.{workspace_name}.bucket_contents.tsv', sep='\t', index=False, header=False)
     )

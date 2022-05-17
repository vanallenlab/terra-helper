import pandas as pd
import requests
import subprocess
import io
import numpy as np
from oauth2client.client import GoogleCredentials

import argparse

ROOT = 'https://api.firecloud.org/api'
credentials = GoogleCredentials.get_application_default()
token = credentials.get_access_token().access_token
HEADERS = {"Authorization": "bearer " + token}


def download(series, folder):
    blobs = ' '.join(series.dropna().tolist())
    command = ' '.join(['gsutil -m cp', blobs, folder])
    subprocess.call(command, shell=True)


def request_data_model(namespace, workspace, entity_type):
    request = f'{ROOT}/workspaces/{namespace}/{workspace}/entities/{entity_type}/tsv'
    r = requests.get(request, headers=HEADERS)
    return pd.read_csv(io.BytesIO(r.content), encoding='utf-8', sep='\t')


def main(dictionary):
    namespace = dictionary['namespace']
    workspace = dictionary['workspace']
    entity_type = dictionary['type']
    column = dictionary['col']

    df = request_data_model(namespace, workspace, entity_type)
    for dataframe in np.array_split(df, 10): 
        download(dataframe.loc[:, column], column)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--namespace', type=str, required=True, help='Terra namespace of workspace')
    parser.add_argument('--workspace', type=str, required=True, help='Terra workspace name')
    parser.add_argument('--entity_type', type=str, required=True, help='Terra entity type')
    parser.add_argument('--column', type=str, required=True, help='Terra column of entity type')
    args = parser.parse_args()

    inputs_dict = {
        'namespace': args.namespace,
        'workspace': args.workspace,
        'type': args.entity_type,
        'col': args.column
    }

    out_directory = inputs_dict['col']
    cmd = 'mkdir -p {}'.format(out_directory)
    subprocess.call(cmd, shell=True)

    print(inputs_dict)
    main(inputs_dict)

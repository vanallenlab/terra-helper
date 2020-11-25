import argparse
import pandas as pd
import requests
from oauth2client.client import GoogleCredentials

root = 'https://api.firecloud.org/api'


def generate_header():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    return {"Authorization": f"bearer {token}"}


def get_workspaces_all(headers):
    request = f'{root}/workspaces'
    return requests.get(request, headers=headers).json()


def subset_workspaces_access(workspaces):
    return [workspace for workspace in workspaces if workspace['accessLevel'] != 'NO ACCESS']


def subset_workspaces_tag(workspaces, tag):
    tagged = [workspace for workspace in workspaces if 'tag:tags' in workspace['workspace']['attributes'].keys()]
    return [workspace for workspace in tagged if tag in workspace['workspace']['attributes']['tag:tags']['items']]


def create_agenda(tag, destination, handle, headers):
    workspaces_all = get_workspaces_all(headers)
    workspaces_access = subset_workspaces_access(workspaces_all)
    workspaces_tagged = subset_workspaces_tag(workspaces_access, tag)

    records = []
    for workspace in workspaces_tagged:
        namespace = workspace['workspace']['namespace']
        name = workspace['workspace']['name']
        bucket = workspace['workspace']['bucketName']
        record = {'namespace': namespace, 'name': name, 'bucket': bucket}
        records.append(record)
    dataframe = pd.DataFrame(records)
    dataframe['destination'] = destination
    dataframe = dataframe.loc[:, ['bucket', 'destination', 'namespace', 'name']]
    dataframe.to_csv(f'{handle}.txt', sep='\t', index=False, header=False)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='List workspaces to archive',
                                         description="Create a list of workspaces to archive based on a provided tag."
                                                     "Formats outputs for use with copy_multiple_buckets.sh.")
    arg_parser.add_argument('--tag', '-t', required=True,
                            help='Tag to list')
    arg_parser.add_argument('--destination', '-d', required=True,
                            help='Path to destination')
    arg_parser.add_argument('--output', '-o', required=True,
                            help='Path to destination')
    args = arg_parser.parse_args()
    HEADERS = generate_header()

    create_agenda(args.tag, args.destination, args.output, HEADERS)

import argparse
import io
import pandas as pd
import requests
import sys
import zipfile
from oauth2client.client import GoogleCredentials

ROOT = 'https://api.firecloud.org/api'
credentials = GoogleCredentials.get_application_default()
token = credentials.get_access_token().access_token
HEADERS = {"Authorization": f"bearer {token}"}


def entity_set_response_to_dataframe(content, entity_type):
    z = zipfile.ZipFile(io.BytesIO(content))
    table = z.read(f"{entity_type}_entity.tsv")
    return pd.read_csv(io.StringIO(table.decode('utf-8')), sep='\t', low_memory=False)


def entity_response_to_dataframe(content):
    return pd.read_csv(io.BytesIO(content), sep='\t', encoding='utf-8', low_memory=False)


def get_entities(namespace, workspace):
    request = f'{ROOT}/workspaces/{namespace}/{workspace}/entities'
    return requests.get(request, headers=HEADERS)


def get_entity_table(namespace, workspace, entity_type):
    request = f'{ROOT}/workspaces/{namespace}/{workspace}/entities/{entity_type}/tsv'
    r = requests.get(request, headers=HEADERS)
    return r


def main(workspace_namespace, workspace_name, entity):
    response_entities = get_entities(workspace_namespace, workspace_name)
    if response_entities.status_code != 200:
        sys.exit(f"Error. {response_entities.status_code} returned from request for entities from "
                 f"{workspace_namespace}/{workspace_name}."
                 f"{response_entities.content}")
    entities = list(response_entities.json().keys())

    if entity not in entities:
        sys.exit(f"Error. Entity type {entity} is not found in {workspace_namespace}/{workspace_name}, "
                 f"observed entity types are: {entities}.")
    else:
        response = get_entity_table(namespace=workspace_namespace, workspace=workspace_name, entity_type=entity)
        if response.status_code != 200:
            sys.exit(f"Error. {response.status_code} returned from request for {entity} from "
                     f"{workspace_namespace}/{workspace_name}."
                     f"{response.content}")

        if "_set" in entity:
            df = entity_set_response_to_dataframe(response.content, entity)
        else:
            df = entity_response_to_dataframe(response.content)

        df.to_csv(f"{workspace_namespace}.{workspace_name}.{entity}.txt", sep='\t', index=False)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Download entity table',
                                         description="Download one or more entity tables from Terra workspaces")
    arg_parser.add_argument('--namespace', '-ns', type=str, help='Terra workspace namespace')
    arg_parser.add_argument('--name', '-n', type=str, help='Terra workspace name')
    arg_parser.add_argument('--entity_type', '-e', type=str, help='Terra entity type to download')
    arg_parser.add_argument('--tsv', '-t', type=str, default=None, help='TSV for download of multiple tables')
    args = arg_parser.parse_args()

    if args.tsv:
        tsv = pd.read_csv(args.tsv, sep='\t')
        for index in tsv.index:
            main(tsv.loc[index, 'namespace'], tsv.loc[index, 'name'], tsv.loc[index, 'entity_type'])
    else:
        main(args.namespace, args.name, args.entity_type)

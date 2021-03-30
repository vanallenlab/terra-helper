import argparse
import requests
from oauth2client.client import GoogleCredentials

ROOT = 'https://api.firecloud.org/api'


def create_workspace_data(namespace, name, location, authorization_domain):
    authorization_domain_data = [{"membersGroupName": authorization_domain}] if authorization_domain else []
    return {
        "namespace": namespace,
        "name": name,
        "bucketLocation": location,
        "authorizationDomain": authorization_domain_data,
        "attributes": {}
    }


def generate_header():
    credentials = GoogleCredentials.get_application_default()
    token = credentials.get_access_token().access_token
    return {"Authorization": f"bearer {token}", "Content-Type": "application/json"}


def post_workspace(headers, data):
    request = f'{ROOT}/workspaces'
    return requests.post(request, headers=headers, json=data)


def create_workspace(namespace, name, location, authorization_domain):
    headers = generate_header()
    data = create_workspace_data(namespace, name, location, authorization_domain)
    r = post_workspace(headers, data)
    if r.status_code not in [200]:
        return r.status_code, r.content
    else:
        return r.status_code, r.json()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Create workspace', description="Create a single region workspace")
    arg_parser.add_argument('--namespace', required=True, help='Workspace namespace')
    arg_parser.add_argument('--name', required=True, help='Workspace name')
    arg_parser.add_argument('--location', '-l',
                            choices=['US-CENTRAL1'], default='US-CENTRAL1', help='Location on google cloud')
    # API endpoint currently does not support multi region locations; choices= = ['US', 'US-CENTRAL1']
    arg_parser.add_argument('--authorization', '-ad', default=None, help='Authorization domain')
    args = arg_parser.parse_args()

    status_code, response = create_workspace(args.namespace, args.name, args.location, args.authorization)
    print(status_code, response)

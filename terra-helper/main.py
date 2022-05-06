import argparse
from endpoints import terra
from format import requests


def request_workspaces():
    return terra.Terra.request(terra.Terra.get_all_workspaces, requests.Requests.return_json)


def main(print_outputs=False):
    workspaces = request_workspaces()
    if print_outputs:
        print(len(workspaces))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Template', description='Template for google authentication')
    parser.add_argument('--print', '-p', action='store_true', help='Print examples')
    args = parser.parse_args()
    main(args.print)

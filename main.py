import argparse
import json
import os
import sys
from pathlib import Path

import requests

from ServerClass import Server


def parse_args():
    """
    Processing arguments if present
    :return: args object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f',
                        help='JSON file path, could be url (http://host/json_file)',
                        default=None)
    parser.add_argument('--key', '-k', help='Path to SSH-key file to connect to hosts', default=None)
    return parser.parse_args()


def get_json():
    """
    Getting json
    either from the link
    or from the file
    :return: JSON object
    """
    if args.file:
        if args.file.startswith('https:') or args.file.startswith("http:"):
            requests.packages.urllib3.disable_warnings()
            try:
                print('Receiving data by given url... ', end='')
                json_file = requests.get(args.file, verify=False)
                response = json.loads(json_file.text)
                print('Success')
                filename = 'info_from_url.json'
                return response, filename
            except json.decoder.JSONDecodeError:
                sys.exit('ERROR!\n{}\n'
                         'Data received by url "{}" '
                         'is not in JSON format!'.format(json_file.text, args.file))
            except requests.exceptions.ConnectionError as err:
                sys.exit('ERROR! \nConnection to "{}" failed: \n{}'.format(args.file, err))
        else:
            if Path(args.file).is_file():
                json_file = args.file
            else:
                sys.exit('ERROR! File "{}" does not exist or it\'s not a file!'.format(args.file))
    else:
        json_file = [file for file in os.listdir() if file.endswith('.json')]
        if not json_file:
            sys.exit('ERROR! No JSON file found!\nUse -f /json/file/path (http://host/json_file) '
                     'or put the file.json next to main.py (working directory)')
        elif len(json_file) > 1:
            sys.exit('ERROR! Found more than 1 .json file: {},'
                     ' please use argument -f /json/file/path '
                     'to specify necessary file'.format(json_file))
        else:
            json_file = json_file[0]
            print('Found file "{}" in working directory "{}"'.format(json_file, os.getcwd()))

    try:
        with open(json_file) as file:
            json_text = json.load(file)
            print('File successfully parsed!')
        return json_text, json_file
    except json.decoder.JSONDecodeError:
        sys.exit('ERROR! File "{}" is not in JSON format!'.format(file.name))
    except PermissionError as err:
        sys.exit('ERROR! {}'.format(err))


def collect_data_from_hosts(info):
    """
    Iter over hosts in JSON
    to collect VCS info
    :param info: JSON data
    :return: None, filling received JSON data with collected info
    """
    clusters = info['hosts'].keys()
    for cluster in clusters:
        host = info['hosts'][cluster]['host']
        user = info['hosts'][cluster]['user']
        with Server(host, user, user, key=args.key if args.key else None) as server:
            branch, revision = server.get_vcs_info()
            vcs_system = server.vcs_type
            info['hosts'][cluster]['vcs_system'] = vcs_system
            info['hosts'][cluster]['current_branch'] = branch
            info['hosts'][cluster]['current_revision'] = revision


if __name__ == '__main__':
    args = parse_args()
    print('#' * 10, 'Program starting!')
    json_data, filename = get_json()
    collect_data_from_hosts(json_data)
    print('Writing info to file: {}'.format(filename))
    with open(filename, 'w') as file:
        json.dump(json_data, file)
    print('#' * 10, 'Finished!')

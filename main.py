import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests

from server_class import Server


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


def get_json(json_path=None):
    """
    Getting json
    either from the link
    or from the file
    :param: Path/to/json/file or https://url/to/json
    :return: JSON object
    """
    if json_path:
        if json_path.startswith('https:') or json_path.startswith("http:"):
            requests.packages.urllib3.disable_warnings()
            try:
                logging.info('Receiving data by given url... ')
                json_file = requests.get(json_path, verify=False)
                response = json.loads(json_file.text)
                logging.info('Success')
                new_filename = 'info_from_url.json'
                return response, new_filename
            except json.decoder.JSONDecodeError:
                sys.exit(logging.error(f'Data received by url "{json_path}" is not in JSON format!'))
            except requests.exceptions.ConnectionError as err:
                sys.exit(logging.error(f'Connection to "{json_path}" failed: {err}'))
        else:
            if Path(json_path).is_file():
                json_file = json_path
            else:
                sys.exit(logging.error(f'File "{json_path}" does not exist or it\'s not a file!'))
    else:
        json_file = [f for f in os.listdir() if f.endswith('.json')]
        if not json_file:
            sys.exit(logging.error('No JSON file found! '
                                   'Use -f /json/file/path (http://host/json_file) '
                                   'or put the file.json next to main.py (working directory)'))
        elif len(json_file) > 1:
            sys.exit(logging.error(f'Found more than 1 .json file: {json_file}, '
                                   f'please use argument -f /json/file/path '
                                   f'to specify necessary file'))
        else:
            json_file = json_file[0]
            logging.info(f'Found file "{json_file}" in working directory "{os.getcwd()}"')

    try:
        with open(json_file) as f:
            json_text = json.load(f)
            logging.info('File successfully parsed!')
        return json_text, json_file
    except json.decoder.JSONDecodeError:
        sys.exit(logging.error(f'File "{f.name}" is not in JSON format!'))
    except PermissionError as err:
        sys.exit(logging.error(err))


def collect_data_from_hosts(info, ssh_key=None):
    """
    Iter over hosts in JSON
    to collect VCS info
    :param info: JSON data
    :param ssh_key: SSH-Key to connect to hosts
    :return: None, filling received JSON data with collected info
    """
    clusters = info['hosts'].keys()
    for cluster in clusters:
        host = info['hosts'][cluster]['host']
        user = info['hosts'][cluster]['user']
        with Server(host, user, user, key=ssh_key) as server:
            branch, revision = server.get_vcs_info()
            vcs_system = server.vcs_type
            info['hosts'][cluster]['vcs_system'] = vcs_system
            info['hosts'][cluster]['current_branch'] = branch
            info['hosts'][cluster]['current_revision'] = revision


if __name__ == '__main__':
    args = parse_args()
    LOG_FORMAT = r'%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s'
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    logging.info(f"{'#' * 10} Program starting!")
    json_data, filename = get_json(args.file)
    collect_data_from_hosts(json_data, args.key)
    logging.info(f'Writing info to file: {filename}')
    with open(filename, 'w') as file:
        json.dump(json_data, file)
    logging.info(f"{'#' * 10} Finished!")

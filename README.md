# WGT
Check VCS status by hosts in JSON file

To install requirements.txt use:
`pip install -r requirements.txt`
```
python main.py -h
usage: main.py [-h] [--file FILE] [--key KEY]

options:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  JSON file path, could be url (http://host/json_file)
  --key KEY, -k KEY     Path to SSH-key file to connect to hosts
  ```

If no args were used, script looks for *.json file in current directory
and uses `password=user` to connect to hosts.

### Template JSON format:
```
{
    "hosts": {
        "EU-CLUSTER": {
            "title": "Eu cluster discription",
            "host": "eu1-vm-host",
            "user": "euuser"
        },
        "NA-CLUSTER": {
            "title": "Na cluster description",
            "host": "na1-vm-host",
            "user": "nauser"
        }
    }
}
```

**Paramiko is used to connect to hosts via SSH!**

Looks for next parameters on remote host:
* VCS (SVN/GIT)
* Current branch name
* Current revision name

## Result
Retrieved data puts in the same file <filename>.json

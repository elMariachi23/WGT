import logging
import socket

import paramiko


class Server:
    """
    Connect to server via Paramiko,
    retrieve necessary data and disconnect
    """

    def __init__(self, host, user, pwd=None, key=None):
        """
        Required parameters
        :param host: server address to connect (or ip-address)
        :param user: username to connect remote server
        :param pwd: username's password
        :param key: ssh-key to connect
        """
        self.host = host
        self.username = user
        self.password = pwd
        self.ssh_key = key
        self.work_dir = '~/bw/'
        self.connection = None
        self.vcs_type = None
        logging.getLogger("paramiko").setLevel(logging.WARNING)

    def __enter__(self):
        self.connection = paramiko.SSHClient()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            logging.info(f'Connecting to host "{self.host}" with user "{self.username}"...')
            if not self.ssh_key:
                self.connection.connect(self.host, 22, self.username, self.password)
            else:
                self.connection.connect(hostname=self.host, port=22,
                                        username=self.username, key_filename=self.ssh_key)
            logging.info('Connected!')
            return self
        except FileNotFoundError as err:
            logging.error('SSH-KEY file exception!')
            logging.error(err)
        except paramiko.ssh_exception.AuthenticationException:
            logging.error('Authentication failed!')
            logging.error(f'{"Password failed" if not self.ssh_key else "Key is invalid"} for "{self.username}"')
        except TimeoutError:
            logging.error('Connection Timeout. Host either wrong or down')
        except socket.gaierror as err:
            logging.error(err)

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.connection.close()
        return True

    def get_vcs_info(self):
        """
        Collect branch name and revision
        from remote server
        :return: (str) branch name and revision
        """
        logging.info('Retrieving data...')
        self.get_vcs_type()
        check_branch, check_revision = self.generate_correct_commands()
        result = self.connection.exec_command(f'cd {self.work_dir} && {check_branch}')[1]
        branch = result.read().decode().replace('\n', '')
        result = self.connection.exec_command(f'cd {self.work_dir} && {check_revision}')[1]
        revision = result.read().decode().replace('\n', '')
        logging.info('Done!')
        return branch, revision

    def generate_correct_commands(self):
        """
        Generate commands to operate in VCS
        according to VCS type
        :return: command strings to get branch name and revision
        """
        if self.vcs_type == 'GIT':
            branch_command = "git branch | awk '{print $2}'"
            revision_command = "git log -1 --pretty=oneline | awk '{print $1}'"
        else:
            branch_command = "svn info --show-item relative-url | awk -F \"/\" '{print $(NF)}'"
            revision_command = 'svn info --show-item revision'
        return branch_command, revision_command

    def get_vcs_type(self):
        """
        Determines self.vcs_type in directory
        Exits if no VCS found
        """
        stdout, stderr = self.connection.exec_command(f'ls -a {self.work_dir}')[1:3]
        out = stdout.read().decode().split('\n')
        if '.svn' in out:
            self.vcs_type = 'SVN'
        elif '.git' in out:
            self.vcs_type = 'GIT'
        else:
            errors = stderr.read().decode()
            if 'Permission denied' in errors:
                logging.error(f'Permission denied to "{self.work_dir}" for user "{self.username}"')
            elif 'No such file or directory' in errors or not errors:
                logging.error(f'No VCS found in directory "{self.work_dir}"')
            else:
                logging.error(errors)
            self.__exit__()

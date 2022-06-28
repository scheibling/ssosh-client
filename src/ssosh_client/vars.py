import os
from enum import Enum
from .utils import osi_programdata

CLIENT_CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'ssosh.json')

HOST_CONFIG_BASE = os.path.join(osi_programdata(), 'ssosh')
HOST_CONFIG_FILE = os.path.join(HOST_CONFIG_BASE, 'config.json')
HOST_PRINCIPALS_FILE = os.path.join(HOST_CONFIG_BASE, 'principals')
HOST_CA_PUBKEY_FILE = os.path.join(HOST_CONFIG_BASE, 'ca_pubkey')

SSH_USER_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.ssh')
SSH_SERVER_CONFIG_PATH = os.path.join(osi_programdata(), 'ssh', 'sshd_config')
KNOWN_HOSTS_CA_IDENTIFIER = "trusted@ssosh-ca"
KNOWN_HOSTS_FILE = 'known_hosts2'

class UrlPaths(Enum):
    DEVICE_AUTH = '/auth/device'
    HOST_BOOTSTRAP = '/hosts/bootstrap'
    CLIENT_BOOTSTRAP = '/client/bootstrap/'
    CLIENT_CONFIG = '/client/config'
    CLIENT_CERTIFICATE = '/client/certificate'

class PermissionScopes(Enum):
    CLIENT_BOOTSTRAP = 'client.bootstrap'
    CLIENT_CERTIFICATE = 'client.certificate'
    HOST_BOOTSTRAP = 'host.bootstrap'
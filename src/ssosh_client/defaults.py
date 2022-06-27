import os
from enum import Enum

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'config.json')

class UrlPaths(Enum):
    DEVICE_AUTH = '/auth/device'
    CLIENT_BOOTSTRAP = '/client/bootstrap/'
    CLIENT_CONFIG = '/client/config'

class PermissionScopes(Enum):
    CLIENT_BOOTSTRAP = 'client.bootstrap'
    CLIENT_CERTIFICATE = 'client.certificate'
    HOST_BOOTSTRAP = 'host.bootstrap'
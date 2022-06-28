import os
import json
from . import vars
import requests
from cprint import *
from platform import node as pl_node
from dataclasses import dataclass
from time import sleep
from typing import List, Union
from .exceptions import TokenExpiredException, InvalidConfiguration
from datetime import datetime
from sshkey_tools.keys import PublicKey
from lineinfile import add_line_to_file, AtBOF, AtEOF, AfterLast, ALWAYS
from .utils import (
    touch as touch_file,
    formatted_host
)

@dataclass
class DeviceAuthSession:
    host: str
    scopes: List[vars.PermissionScopes]
    token: str = None
    expiry: datetime = None
    
    def __post_init__(self):
        self.host = formatted_host(self.host)
    
    def is_expired(self):
        return datetime.now() > self.expiry
    
    def is_valid_scope(self, scope: vars.PermissionScopes):
        return scope in self.scopes

@dataclass
class ClientConfiguration:
    hostname: str = None
    key: str = None
    base_url: str = None
    ca_pubkey: str = None

    def __post_init__(self):
        if self.hostname is None:
            self.hostname = pl_node()
            
    def is_configured(self):
        try:
            config = json.load(open(vars.CLIENT_CONFIG_PATH, 'r'))
            if config['key'] in [None, ''] or config['ca_pubkey'] in [None, '']:
                return False
        except:
            return False
        
        return True
    
    def save_file(self, path: str = vars.CLIENT_CONFIG_PATH):
        split_path = os.path.split(path)

        if not os.path.isdir(split_path[0]):
            os.makedirs(split_path[0])

        with open(path, 'w') as file:
            json.dump(self.__dict__, file)
            
    def configure_ssh_client(self):
        if self.key is None:
            raise Exception("No configuration present, please bootstrap the client first")
    
        # Set trusted CA in known_hosts
        ca_pubkey = PublicKey.from_string(self.ca_pubkey)
        ca_pubkey.comment = vars.KNOWN_HOSTS_CA_IDENTIFIER.encode('utf-8')
    
        if not os.path.isdir(vars.SSH_USER_CONFIG_DIR):
            os.makedirs(vars.SSH_USER_CONFIG_DIR)
        
        if not os.path.isfile(os.path.join(vars.SSH_USER_CONFIG_DIR, vars.KNOWN_HOSTS_FILE)):
            touch_file(os.path.join(vars.SSH_USER_CONFIG_DIR, vars.KNOWN_HOSTS_FILE))
    
        add_line_to_file(
            os.path.join(vars.SSH_USER_CONFIG_DIR, vars.KNOWN_HOSTS_FILE),
            f'@cert-authority {ca_pubkey.to_string()}',
            regexp=r"^@cert-authority .* {}$".format(vars.KNOWN_HOSTS_CA_IDENTIFIER),
            inserter=AtBOF(),
            backup=ALWAYS,
            backup_ext=".bak"
        )

    @classmethod
    def from_file(cls, path: str = vars.CLIENT_CONFIG_PATH):
        config = json.load(open(path, 'r'))
        
        try:
            cls(**config)
        except TypeError as e:
            raise InvalidConfiguration(f'Invalid configuration file: {path}') from e

@dataclass
class HostConfiguration:
    hostname: str = None
    config_url: str = None
    principals: list = None
    ca_pubkey: list = None
    key: str = None
    interval: int = None
    
    def __post_init__(self):
        self.hostname = self.hostname.upper()
        
    def is_configured(self):
        try:
            config = json.load(open(vars.HOST_CONFIG_FILE, 'r'))
            if config['key'] in [None, ''] or config['ca_pubkey'] in [None, '']:
                return False
        except:
            return False
        
        return True

    def save_file(self, path: str = vars.HOST_CONFIG_FILE):
        if self.key is None:
            raise Exception("No configuration present, please bootstrap the host first")
    
        # Save the json configuration to file
        split_path = os.path.split(path)

        if not os.path.isdir(split_path[0]):
            os.makedirs(split_path[0])

        with open(path, 'w') as file:
            json.dump(self.__dict__, file)
        
    def configure_ssh_server(self):
        if self.key is None:
            raise Exception("No configuration present, please bootstrap the host first")
        
        # Get and verify trusted CA key, save to file
        ca_pubkey = PublicKey.from_string(self.ca_pubkey)
        ca_pubkey.to_file(vars.HOST_CA_PUBKEY_FILE)
        
        # Save principals list to file (AuthorizedPrincipalsFile)
        with open(vars.HOST_PRINCIPALS_FILE, 'w') as f:
            f.write(os.linesep.join(self.principals))
        
        #
        ## TODO: AuthorizedPrincipalsCommand/AuthorizedPrincipalsCommandUser
        #
        
        # Update sshd_config
        if not os.path.isfile(vars.SSH_SERVER_CONFIG_PATH):
            raise Exception('No SSH configuration file exists, please make sure OpenSSH server is installed.')
        
        # Add SSO Shell configuration at bottom of file
        add_line_to_file(
            vars.SSH_SERVER_CONFIG_PATH,
            f'# SSO Shell configuration',
            regexp=r"^# SSO Shell configuration$",
            inserter=AtEOF()
        )
        
        # Set trusted CA
        add_line_to_file(
            vars.SSH_SERVER_CONFIG_PATH,
            f'TrustedUserCAKeys {vars.HOST_CA_PUBKEY_FILE}',
            regexp=r"^[# ]*TrustedUserCAKeys .*$",
            inserter=AfterLast("# SSO Shell configuration"),
            backup=ALWAYS,
            backup_ext=".bak-before-trustedusercakeys"
        )
        
        # Set authorized principals
        add_line_to_file(
            vars.SSH_SERVER_CONFIG_PATH,
            f'AuthorizedPrincipalsFile {vars.HOST_PRINCIPALS_FILE}',
            regexp=r"^[# ]*AuthorizedPrincipalsFile .*$",
            inserter=AfterLast("# SSO Shell configuration"),
            backup=ALWAYS,
            backup_ext=".bak-before-authorizedprincipalsfile"
        )
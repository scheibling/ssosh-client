import os
import json
import defaults
import requests
from typing import List
from exceptions import TokenExpiredException
from datetime import datetime

class Configuration:
    def __init__(self, **kwargs):
        self.hostname = kwargs.get('hostname', None)
        self.key = kwargs.get('key', None)
        self.base_url = kwargs.get('base_url', None)
        self.config_url = kwargs.get('config_url', None)
        self.ca_pubkey = kwargs.get('ca_pubkey', None)
        
    @classmethod
    def load_file(cls, path: str = defaults.CONFIG_PATH):
        try:
            with open(path, 'r') as file:
                conf = json.load(file)
        except FileNotFoundError:
            return None
        except PermissionError:
            return None
        
        return cls(**conf)
    
    def save_file(self, path: str = defaults.CONFIG_PATH):
        split_path = os.path.split(path)

        if not os.path.isdir(split_path[0]):
            os.makedirs(split_path[0])

        with open(path, 'w') as file:
            json.dump(self.__dict__, file)

class DeviceAuthSession:
    def __init__(self, host: str = None):
        self.host = host
        self.request = None
        self.token = None
        self.expiry = None
        self.scopes = None
        self.format_host()
        
    def format_host(self):
        if self.host[:4] != 'http':
            self.host = 'https://' + self.host
        
        if self.host[-1:] == '/':
            self.host = self.host[:-1]

    def start_auth(self, permissions: List[defaults.PermissionScopes]):
        init = requests.post(
            f'{self.host}{defaults.UrlPaths.DEVICE_AUTH.value}',
            data={'scopes': ','.join([x.value for x in permissions])}
        )

        if init.status_code == 200:
            init_data = init.json()
            self.request = {
                'auth_url': init_data.get('auth_url', None),
                'callback_url': init_data.get('callback_url', None),
                'expires': init_data.get('exp', None),
                'interval': init_data.get('int', None),
            }
            
        return self.request['auth_url']
    
    def check_authenticated(self) -> bool:
        if self.request['expires'] < datetime.now().timestamp():
            raise TokenExpiredException(
                'Authentication not completed in time, token expired. Please try again'
            )

        verify = requests.get(self.request['callback_url'])
        if verify.status_code == 200:
            verify_data = verify.json()
            self.token = verify_data['token']
            self.expiry = datetime.fromtimestamp(verify_data['exp'])
            self.scopes = verify_data['scopes']
            
            return True
        
        return False
    
    def is_expired(self) -> bool:
        if datetime.now() > self.expiry:
            return True
        
        return False
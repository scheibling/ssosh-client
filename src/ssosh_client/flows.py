import requests
from platform import node as pf_node
from cprint import cprint
from typing import List, Union
from time import sleep
import webbrowser
from .utils import formatted_host
from .vars import PermissionScopes, UrlPaths
from dataclasses import dataclass
from datetime import datetime
from .models import ClientConfiguration, HostConfiguration, DeviceAuthSession
from .exceptions import TokenExpiredException
from .utils import formatted_host, check_if_privileged

class DeviceAuthenticationFlow:
    def __init__(self, device_auth: DeviceAuthSession):
        self.device_auth = device_auth
        
        auth_request = requests.post(
            f'{self.device_auth.host}{UrlPaths.DEVICE_AUTH.value}',
            data={
                'scopes': ','.join([x.value for x in self.device_auth.scopes])
            }
        )
        
        if auth_request.status_code == 200:
            self.auth_request = auth_request.json()
            
            return
        
        raise Exception(f'Failed to authenticate device: {auth_request.text}')
    
    def prompt_user_login(self, auto_open: bool = False) -> None:
        cprint.ok('Please open the following URL in your browser:')
        cprint.info(self.auth_request['auth_url'])
        
        if auto_open is not None:
            webbrowser.open(self.auth_request['auth_url'], new=0)
        
        while True and not self.auth_request['exp'] < datetime.now().timestamp():
            sleep(self.auth_request['int'])
            
            callback_request = requests.get(self.auth_request['callback_url'])
            if callback_request.status_code == 200:
                callback_data = callback_request.json()
                
                self.device_auth.token = callback_data['token']
                self.device_auth.expiry = datetime.fromtimestamp(callback_data['exp'])
                
                cprint.ok('Token successfully retrieved')
                return

        raise TokenExpiredException('Authentication not completed in time, token expired. Please try again')

class ClientBootstrapFlow:
    def __init__(self, dev_auth: DeviceAuthSession, hostname: str = pf_node()):
        if dev_auth.is_expired() or not dev_auth.is_valid_scope(PermissionScopes.CLIENT_BOOTSTRAP):
            raise TokenExpiredException('Token expired or invalid permissions, please try authenticating again')
        
        self.dev_auth = dev_auth
        self.hostname = hostname
        self.config = None
        
    def bootstrap(self) -> None:
        bootstrap_request = requests.post(
            f'{self.dev_auth.host}{UrlPaths.CLIENT_BOOTSTRAP.value}',
            headers={
                'Authorization': f'Bearer {self.dev_auth.token}',
            },
            data={
                'hostname': self.hostname
            }
        )
        
        if bootstrap_request.status_code == 200:
            config = ClientConfiguration(**bootstrap_request.json())
            config.save_file()
            config.configure_ssh_client()
            cprint.ok("Client successfully configured!")
            return config
        
        raise Exception(f'Failed to bootstrap client: {bootstrap_request.text}')
    
class HostBootstrapFlow:
    def __init__(self, dev_auth: DeviceAuthSession, hostname: str = pf_node()):
        if dev_auth.is_expired() or not dev_auth.is_valid_scope(PermissionScopes.HOST_BOOTSTRAP):
            raise TokenExpiredException('Token expired or invalid permissions, please try authenticating again')
        
        self.dev_auth = dev_auth
        self.hostname = hostname
        self.config = None
        
    def bootstrap(self) -> None:
        if not check_if_privileged():
            raise Exception("You are not running this program as a privileged user. Please try again.")

        bootstrap_request = requests.post(
            f'{self.dev_auth.host}{UrlPaths.HOST_BOOTSTRAP.value}',
            headers={
                'Authorization': f'Bearer {self.dev_auth.token}',
            },
            data={
                'hostname': self.hostname
            }
        )
        
        if bootstrap_request.status_code == 200:
            config = HostConfiguration(**bootstrap_request.json())
            config.save_file()
            config.configure_ssh_server()
            cprint.ok("Host successfully configured!")
            return config
        
        raise Exception(f'Failed to bootstrap host: {bootstrap_request.text}')
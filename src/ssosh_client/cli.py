import click
from cprint import *
import os
import sys
import requests
from time import sleep
from datetime import datetime
from defaults import PermissionScopes, UrlPaths, CONFIG_PATH
from models import Configuration, DeviceAuthSession

@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    

@main.command()
@click.option('--host', '-h', prompt='SSO Shell Server: (e.g. https://ca.ssosh.io): ', help='SSO Shell Server: (e.g. https://ca.ssosh.io)')
@click.option('--overwrite', '-o', help='Force overwrite of existing configuration', is_flag=True, default=False)
@click.pass_context
def bootstrap(ctx, host: str, overwrite: bool = False):
    config = Configuration.load_file()
    if config is not None and not overwrite:
        cprint.err('Configuration already exists. Use -o/--overwrite to overwrite, or remove the existing configuration file.')
        sys.exit(1)
        
    cprint.ok(f'Authenticating with server: {host}')
    auth = DeviceAuthSession(host)
    
    url = auth.start_auth([PermissionScopes.CLIENT_BOOTSTRAP])
    cprint.ok('Please open the following URL in your browser:')
    cprint.info(url)
    
    while not auth.check_authenticated():
        sleep(auth.request['interval'])
    
    cprint.ok("Authentication successful, creating device...")
    print(f'visiting {auth.host}{UrlPaths.CLIENT_BOOTSTRAP.value}')
    print(f'Auth {auth.token}')
    # sys.exit(1)
    config = requests.get(
        f'{auth.host}/{UrlPaths.CLIENT_BOOTSTRAP.value}',
        headers={
            'Authorization': f'Bearer {auth.token}'
        },
        data={
            'hostname': os.uname()[1]
        }
    )
    
    if config.status_code == 200:
        cprint.ok('Added client successfully!')
        config = Configuration(**config.json())
        config.save_file()
        
        cprint.ok('Client succesfully configured!')
        
    print(config.text)
    raise Exception("Configuration failed")

if __name__ == '__main__':
    main()
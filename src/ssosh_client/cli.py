import click
from cprint import *
import os
import sys
import requests
from time import sleep
from datetime import datetime

@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    

@main.command()
@click.option('--host', '-h', prompt='SSO Shell Server: (e.g. https://ca.ssosh.io): ', help='SSO Shell Server: (e.g. https://ca.ssosh.io)')
@click.option('--overwrite', '-o', help='Force overwrite of existing configuration', is_flag=True, default=False)
@click.pass_context
def bootstrap(ctx, host: str, overwrite: bool = False):
    is_windows = os.name == 'nt'
    config_path = os.path.join(os.path.expanduser('~'), '.config', 'ssosh.json')
    if os.path.isfile(config_path) and overwrite is False:
        cprint.err('Configuration file already exists. Use -o/--overwrite to overwrite the existing configuration.')
        sys.exit(1)

    cprint.ok('Authenticating...')
    
    if host[:4] != 'http':
        host = 'https://' + host
        
    if host[-1:] == '/':
        host = host[:-1]
    
    print(f'{host}/auth/device')
    auth_start = requests.post(f'{host}/auth/device', data={'scopes': 'client.bootstrap'}).json()
    
    cprint.info('Please click the following link to authenticate this device:')
    cprint('\t' + auth_start['auth_url'])
    
    while True:
        if auth_start['exp'] < datetime.now().timestamp():
            cprint.err('Authentication expired, got no response. Please try again.')
            sys.exit(1)

        sleep(auth_start['int'])
        check_auth = requests.get(auth_start['callback_url'])
        if check_auth.status_code == 200:
            break
        
    cprint.ok('Authentication successful!')
    cprint.ok('Saving settings...')
    
    config = requests.get(f'{host}config', headers={'Authorization': f'Bearer {check_auth.json()["token"]}'})
    
    if config.status_code != 200:
        cprint.err("An error occured while fetching the settings")
        cprint.err(config.text)
        sys.exit(1)

    with open(config_path, 'w') as f:
        f.write(config.text)
    
if __name__ == '__main__':
    main()
import click
from cprint import *
import platform
import os
import sys
import requests
from time import sleep
from datetime import datetime
from vars import PermissionScopes, UrlPaths, CONFIG_PATH
from models import Configuration, DeviceAuthSession
from flows import DeviceAuthenticationFlow, DeviceAuthentication
from sshkey_tools.keys import PublicKey
from sshkey_tools.cert import SSHCertificate

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
    
    auth = DeviceAuthenticationFlow(
        DeviceAuthentication(
            host=host,
            scopes=[PermissionScopes.CLIENT_BOOTSTRAP]
        )
    )
    
    auth.prompt_user_login()
    
    auth = DeviceAuthSession(host)
    auth.await_login([PermissionScopes.CLIENT_BOOTSTRAP])
    
    cprint.ok("Authentication successful, creating device...")

    config = requests.post(
        f'{auth.host}{UrlPaths.CLIENT_BOOTSTRAP.value}',
        headers={
            'Authorization': f'Bearer {auth.token}'
        },
        data={
            'hostname': platform.node()
        }
    )
    
    if config.status_code == 200:
        cprint.ok('Added client successfully!')
        config = Configuration(**config.json())
        config.save_file()
        
        cprint.ok('Client succesfully configured!')
        sys.exit(0)

    cprint.err(f'Failed to get configuration from server (Status {config.status_code}')
    cprint.err(f'Received error: {config.text}')
    raise Exception("Configuration failed")

@main.command()
@click.pass_context
def reconfigure_ssh(ctx):
    config = Configuration.load_file()
    if config is None:
        cprint.err('No configuration found. Run `ssosh-client bootstrap` to register this client with a server.')
        sys.exit(1)
        
    config.configure_ssh_client()

@main.command()
@click.option('--pubkey', '-p', prompt="OpenSSH Public Key", help="The public key to order a certificate for")
@click.option('--output', '-o', help="The path to write the certificate to, default is same folder as pubkey.pub with name pubkey-cert.pub", default=None)
@click.option('--overwrite', help='Forces overwrite of existing certificate file, no prompt', is_flag=True, default=False)
@click.pass_context
def sign(ctx, pubkey: str, output: str = None, overwrite: bool = False):
    cprint.ok('Loading configuration...')
    config = Configuration.load_file()
    if config is None:
        cprint.err('No configuration found. Run `ssosh-client bootstrap` to register this client with a server.')
        sys.exit(1)
        
    cprint.ok('Loading public key...')
    # Load public key
    split_path = os.path.split(pubkey)
    pubkey = PublicKey.from_file(pubkey)
    
    # Start authentication
    cprint.ok(f'Authenticating with server: {config.base_url}')
    auth = DeviceAuthSession(config.base_url)
    auth.await_login([PermissionScopes.CLIENT_CERTIFICATE])
    
    cprint.ok('Login successful, requesting certificate...')
    cert_request = requests.post(
        f'{auth.host}{UrlPaths.CLIENT_CERTIFICATE.value}',
        headers={
            'X-Device-Key': config.key,
            'Authorization': f'Bearer {auth.token}',
            'Content-Type': 'text/plain'
        },
        data=pubkey.to_string()
    )
    
    if cert_request.status_code == 200:
        certificate = SSHCertificate.from_string(cert_request.text)
        cprint.ok('Certificate received!')
        cprint.info(f'Certificate expires: {certificate.fields["valid_before"].value}')
        cprint.info(f'Certificate Serial Number: {certificate.fields["serial"].value}')
        cprint.info(f'Certificate subject: {certificate.fields["key_id"].value}')
        cprint.info(f'Extensions: {certificate.fields["extensions"].value}')
        cprint.info(f'Authorized Principals: {certificate.fields["principals"].value}')
                
        filename = split_path[1].split('.')
        filename = '.'.join(filename[:-1]) + '-cert.pub'
        with open(os.path.join(split_path[0], filename), 'w') as f:
            f.write(cert_request.text)
        
        os.system(f'ssh-keygen -Lf {os.path.join(split_path[0], filename)}')
    
if __name__ == '__main__':
    # main()
    # bootstrap()
    sign()
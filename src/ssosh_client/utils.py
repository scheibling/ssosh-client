import os
import ctypes
import platform

def touch(fname, mode=0o666, dir_fd=None, **kwargs) -> None:
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
            dir_fd=None if os.supports_fd else dir_fd, **kwargs)
        
def formatted_host(host: str) -> str:
    if host[:4] != 'http':
        host = 'https://' + host
        
    if host[-1:] == '/':
        host = host[:-1]
    
    return host

def osi_programdata() -> str:
    osver = platform.system().lower()
    
    if 'linux' in osver:
        return '/etc'
    
    if 'windows' in osver:
        return os.environ.get('ALLUSERSPROFILE', 'C:\\ProgramData')
    
    if 'macos' in osver:
        return '/Library'

    raise Exception(f'Unknown OS ({osver})')

def check_if_privileged() -> bool:
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

    

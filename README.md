# ssosh-client
Python-based client for SSO Shell

# Functions
## ssosh bootstrap [-h/--host ca.ssosh.io] [-o/--overwrite]
- Authenticates the user
- Creates a new configuration file/downloads existing configuration for client
- Adds the CA Public key to known_hosts for host verification
## ssosh login [username@]hostname [-i/--identity identity] [-p/--port port] [-l/--login username]
- Authenticates the user
- Sends the user public key (custom or auto-generated) to the server
- Receives back a certificate
- Connects via SSH to user@hostname
## ssosh sign -c/--certificate /path/to/certificate/file
- Authenticates the user
- Sends the user public key to the server
- Receives back a certificate
- Saves cert to key_name-cert.pub
# Documentation
Read the documentation for SSO Shell [here](https://docs.ssosh.io).
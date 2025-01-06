# OpenVPN Client Connection Scripts

This script is designed to manage OpenVPN client connections by dynamically assigning IP addresses and pushing specific routing configurations based on user profiles. It is intended to be used as a client-connect script in an OpenVPN server setup.

## Features

- **Dynamic IP Assignment**: Automatically assigns the next available IP address to new users.
- **Profile-Based Routing**: Pushes different routing configurations to clients based on their assigned profile.
- **Configuration Management**: Reads and updates user configurations stored in a YAML file.
- **Logging**: Logs connection details and errors to a specified log file.

## Configuration

The script relies on a configuration file located at `/etc/openvpn/scripts/configs/config.yaml`. This file should contain user profiles with the following structure:

```yaml
user1:
  ip_address: 172.18.30.10
  vpn_rights: profile1
user2:
  vpn_rights: default
```

### Profiles

- **profile1**: Routes for specific services.
- **default**: Default gateway routes.
- **reject**: Denies access to the user.
- **personal**: Custom routes specified in a separate file.

## Usage

1. **Setup**: Ensure the script is placed in the OpenVPN scripts directory and is executable.
2. **Environment Variables**: The script uses environment variables set by OpenVPN:
   - `common_name`: The username of the connecting client.
   - `trusted_ip`: The IP address of the client.
3. **Execution**: The script is executed automatically by OpenVPN when a client connects.

## Logging

Logs are written to `/var/log/openvpn/openvpn_client_connects.log`. The log includes information about established sessions, IP assignments, and any errors encountered.

## Error Handling

- **Invalid Username**: The script checks for invalid characters in usernames.
- **Configuration Errors**: Logs and exits if there are issues with the user configuration.
- **Unknown Errors**: Catches and logs any unexpected exceptions.

## Dependencies

- **Python 3**
- **ruamel.yaml**: For reading and writing YAML configuration files.

## Installation

1. Install Python 3 and `ruamel.yaml`:
   ```bash
   sudo apt-get install python3
   pip install ruamel.yaml
   ```

2. Place the script in the OpenVPN scripts directory:
   ```bash
   sudo cp on_connect.py /etc/openvpn/scripts/
   sudo cp on_disconnect.py /etc/openvpn/scripts/
   sudo chmod +x /etc/openvpn/scripts/on_connect.py
   sudo chmod +x /etc/openvpn/scripts/on_disconnect.py
   ```

3. Configure OpenVPN to use the script as a client-connect script in your server configuration file:
   ```conf
   client-connect /etc/openvpn/scripts/on_connect.py
   client-disconnect /etc/openvpn/scripts/on_disconnect.py
   ```

## License

This project is licensed under the MIT License.

---

This README provides a comprehensive overview of the script's functionality, configuration, and usage. Adjust the paths and details as necessary to fit your specific setup and requirements.

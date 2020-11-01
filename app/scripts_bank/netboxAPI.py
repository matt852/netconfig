#!/usr/bin/python3

import requests


class NetboxHost(object):
    """
    Netbox Host class for making calls to Netbox host
    """
    # TODO should be a database model

    def __init__(self, url):
        self.url = url

    def get_device_type(self, x):
        """Input type of device (network, database, server, etc), returns ID in Netbox database."""
        r = requests.get(self.url + '/api/dcim/device-roles/')

        if r.status_code == requests.codes.ok:
            for device in r.json()['results']:
                if device['name'] == x:
                    return device['id']
        else:
            return False

    def get_device_type_os(self, x):
        """Get Device Type of specific Netbox Device ID"""
        r = requests.get(self.url + '/api/dcim/device-types/' + str(x))

        if r.status_code == requests.codes.ok:

            # NOTE should probably put a try/catch around this
            netconfigOS = r.json()['custom_fields']['Netconfig_OS']['label']

            if netconfigOS == 'IOS':
                return 'cisco_ios'
            elif netconfigOS == 'IOS-XE':
                return 'cisco_xe'
            elif netconfigOS == 'NX-OS':
                return 'cisco_nxos'
            elif netconfigOS == 'ASA':
                return 'cisco_asa'
            else:  # Default to simply cisco_ios
                return 'cisco_ios'

        else:

            # NOTE should this be False?
            return 'cisco_ios'

    def get_host_by_id(self, x):
        """Return host info in same format as SQLAlchemy responses, for X-Compatibility with local DB choice.

        x is host ID
        """

        r = requests.get(self.url + '/api/dcim/devices/' + str(x))

        if r.status_code == requests.codes.ok:
            return r.json()

        else:
            return None

    def get_hosts(self):
        """Return all devices stored in Netbox."""

        r = requests.get(self.url + '/api/dcim/devices/?limit=0')

        if r.status_code == requests.codes.ok:

            # NOTE probably don't need to strip primary_ip cidr.
            # Not seeing this as a problem connecting
            result = [host for host in r.json()['results']
                      if host['custom_fields']['Netconfig'] and
                      host['custom_fields']['Netconfig']['label'] == 'Yes']

            return result

        else:

            return None

    def get_host_id(self, x):
        """Input device name/hostname, returns id as stored in Netbox."""
        r = requests.get(self.url + '/api/dcim/devices/?limit=0')

        if r.status_code == requests.codes.ok:

            for host in r.json()['results']:
                if host['display_name'] == x:  # Network
                    return host['id']

        else:

            return None

    def get_host_name(self, x):
        """Input ID, return device name from Netbox."""
        r = requests.get(self.url + '/api/dcim/devices/' + str(x))

        if r.status_code == requests.codes.ok:

            # TODO add try/catch here
            return r.json()['name']

        else:

            return None

    def get_host_ip_addr(self, x):
        """Input ID, return device IP address from Netbox."""
        r = requests.get(self.url + '/api/dcim/devices/' + str(x))

        if r.status_code == requests.codes.ok:

            # TODO add try/catch here
            return r.json()['primary_ip']['address'].split('/', 1)[0]

        else:

            return None

    def get_host_type(self, x):
        """Input ID, return device type from Netbox."""
        r = requests.get(self.url + '/api/dcim/devices/' + str(x))

        if r.status_code == requests.codes.ok:

            # TODO add try/catch here
            return r.json()['device_type']['model']

        else:

            return None

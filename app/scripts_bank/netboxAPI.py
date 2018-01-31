from app import app
from urllib2 import urlopen
from json import load

# TODO refactor with requests


class NetboxHost(object):
    """Class for storing device information pulled from Netbox via API calls."""

    def __init__(self, id, hostname, ipv4_addr, type, ios_type):
        """Initilization method."""
        self.id = id
        self.hostname = hostname
        self.ipv4_addr = ipv4_addr
        self.type = type
        self.ios_type = ios_type


def getDeviceType(x):
    """Input type of device (network, database, server, etc), returns ID in Netbox database."""
    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/device-roles/"
    # url += "?limit=0"

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    for device in json_obj['results']:
        if device['name'] == x:
            return device['id']

    return False


def getDeviceTypeOS(x):
    """Input type of device (network, database, server, etc), returns ID in Netbox database."""
    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/device-types/"
    url += str(x)

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    netconfigOS = str(json_obj['custom_fields']['Netconfig_OS']['label'])

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


def getHostByID(x):
    """Return host info in same formate as SQLAlchemy responses, for X-Compatibility with local DB choice.

    x is host ID
    """
    host = NetboxHost('', '', '', '', '')

    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(x)

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    host.id = str(x)
    host.hostname = str(json_obj['name'])
    host.ipv4_addr = str(json_obj['primary_ip']['address'].split('/', 1)[0])
    host.type = str(json_obj['device_type']['model'])
    host.ios_type = str(getDeviceTypeOS(json_obj['device_type']['id']))

    return host


def getHosts():
    """Return all devices stored in Netbox."""
    response = []
    result = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += "?limit=0"

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    for host in json_obj['results']:
        if str(host['custom_fields']['Netconfig']) != 'None':
            if str(host['custom_fields']['Netconfig']['label']) == 'Yes':
                # Strip the CIDR notation from the end of the IP address, and store it back as the address for the returned host
                host['primary_ip']['address'] = str(host['primary_ip']['address'].split('/', 1)[0])
                result.append(host)

    return result


def getHostID(x):
    """Input device name/hostname, returns id as stored in Netbox."""
    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += "?limit=0"

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    for host in json_obj['results']:
        if host['display_name'] == x:  # Network
            return host['id']


def getHostName(id):
    """Input ID, return device name from Netbox."""
    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(id)

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    return json_obj['name']


def getHostIPAddr(id):
    """Input ID, return device IP address from Netbox."""
    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(id)

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    # Return IP address with trailing CIDR notation stripped off
    return str(json_obj['primary_ip']['address'].split('/', 1)[0])


def getHostType(id):
    """Input ID, return device type from Netbox."""
    response = []

    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(id)

    # Open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    return json_obj['device_type']['model']

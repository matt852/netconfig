from app import app, db, models
from urllib2 import urlopen
from json import load
from lib.functions import stripAllAfterChar


# Class for storing device information pulled from Netbox via API calls
class NetboxHost(object):
    # Results for a device in Netbox
    def __init__(self, id, hostname, ipv4_addr, type, ios_type):
        self.id = id
        self.hostname = hostname
        self.ipv4_addr = ipv4_addr
        self.type = type
        self.ios_type = ios_type

# Input type of device (network, database, server, etc), returns ID in Netbox database
def getDeviceType(x):
    
    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/device-roles/"
    #url += "?limit=0"
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)
    
    for device in json_obj['results']:
        if device['name'] == x:
            return device['id']
    
    return False

# Input type of device (network, database, server, etc), returns ID in Netbox database
def getDeviceTypeOS(x):
    
    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/device-types/"
    url += str(x)
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    netconfigOS = str(json_obj['custom_fields']['Netconfig_OS']['label'])

    if netconfigOS == 'IOS':
        return 'cisco_ios'
    elif netconfigOS == 'IOS-XE':
        return 'cisco_iosxe'
    elif netconfigOS == 'NX-OS':
        return 'cisco_nxos'
    elif netconfigOS == 'ASA':
        return 'cisco_asa'
    else: # Default to simply cisco_ios
        return 'cisco_ios'

# Returns host info in same formate as SQLAlchemy responses, for X-Compatibility with local DB choice
def getHostByID(x):
    # x is host ID
    host = NetboxHost('', '', '', '', '')

    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(x)
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    host.id = str(x)
    host.hostname = str(json_obj['name'])
    host.ipv4_addr = stripAllAfterChar(str(json_obj['primary_ip']['address']), '/')
    host.type = str(json_obj['device_type']['model'])
    host.ios_type = str(getDeviceTypeOS(json_obj['device_type']['id']))
    #host.ios_type = "cisco_ios" # I need to somehow set this as it's not currently set in Netbox as 'cisco_ios', 'cisco_iosxe', 'cisco_nxos', or 'cisco_asa'

    return host


def getHosts():
    response = []
    result = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += "?limit=0"
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    for host in json_obj['results']:
        if str(host['custom_fields']['Netconfig']) != 'None':
            if str(host['custom_fields']['Netconfig']['label']) == 'Yes':
                # Strip the CIDR notation from the end of the IP address, and store it back as the address for the returned host
                host['primary_ip']['address'] = stripAllAfterChar(str(host['primary_ip']['address']), '/')
                result.append(host)

    return result

# Input device name/hostname, returns id as stored in Netbox
def getHostID(x):
    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += "?limit=0"
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)
    
    for host in json_obj['results']:
        if host['display_name'] == x: #network
            return host['id']

# Input ID, return device name from Netbox
def getHostName(id):
    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(id)
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)
    
    return json_obj['name']
        
# Input ID, return device IP address from Netbox
def getHostIPAddr(id):
    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(id)
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)

    # Return IP address with trailing CIDR notation stripped off
    return stripAllAfterChar(str(json_obj['primary_ip']['address']), '/')        

# Input ID, return device type from Netbox
def getHostType(id):
    response = []
    
    url = app.config['NETBOXSERVER']
    url += "/api/dcim/devices/"
    url += str(id)
    
    #open our url, load the JSON
    response = urlopen(url)
    json_obj = load(response)
    
    return json_obj['device_type']['model']
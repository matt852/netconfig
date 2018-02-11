#!/usr/bin/env python
import sys
import app
from netaddr import IPAddress, core
import requests
from .device_classes import deviceType as dt


class DataHandler(object):

    def __init__(self, source, url=None, posts_per_page=15):
        if source:
            self.source = source
            self.url = url
            self.posts_per_page = posts_per_page
        else:
            print("Unable to setup DataHandler")
            sys.exit(1)

    def addHostToDB(self, hostname, ipv4_addr, type, ios_type, local_creds):
        """Add host to database.  Returns True if successful."""
        try:
            host = app.models.Host(hostname=hostname, ipv4_addr=ipv4_addr,
                                   type=type, ios_type=ios_type,
                                   local_creds=local_creds)
            app.db.session.add(host)
            # This enables pulling ID for newly inserted host
            app.db.session.flush()
            app.db.session.commit()
            return True, host.id
        except:
            return False, 0

    def importHostsToDB(self, csvImport):
        """Import hosts to database.

        Returns True if successful
        Format: Hostname,IPAddress,DeviceType,IOSType
        """

        # TODO refactor

        # For each line in csvImport, run validation checks
        for x in csvImport.splitlines():
            if x:
                # Split array by comma's
                xArray = x.split(',')
                # 0 is hostname, 1 is IP address, 2 is device type, 3 is ios type
                try:
                    IPAddress(xArray[1])
                except core.AddrFormatError:
                    return False, "Invalid IP address for host %s - value entered: %s" % (xArray[0], xArray[1])

                if xArray[2].lower() not in ("switch", "router", "firewall"):
                    return False, "Invalid device type for host %s - value entered: %s" % (xArray[0], xArray[2])

                if xArray[3].strip().lower() not in ("ios", "ios-xe", "nx-os", "asa"):
                    return False, "Invalid IOS type for host %s - value entered: %s" % (xArray[0], xArray[3])

        # Each line has been validated, so import all lines into DB
        for x in csvImport.splitlines():
            if x:
                # Split array by comma's
                xArray = x.split(',')
                # 0 is hostname, 1 is IP address, 2 is device type, 3 is ios type, 4 is local creds
                hostname = xArray[0]
                ipv4_addr = xArray[1]

                if xArray[2].lower() == 'switch':
                    type = "Switch"
                elif xArray[2].lower() == 'router':
                    type = "Router"
                elif xArray[2].lower() == 'firewall':
                    type = "Firewall"
                else:
                    type = "Error"

                ios_type = self.getOSType(xArray[3].strip())

                if xArray[4].strip().lower() == 'true':
                    local_creds = True
                elif xArray[4].strip().lower() == 'false':
                    local_creds = False
                else:
                    local_creds = False

                try:
                    host = app.models.Host(hostname=hostname,
                                           ipv4_addr=ipv4_addr, type=type,
                                           ios_type=ios_type,
                                           local_creds=local_creds)
                    app.db.session.add(host)
                    # This enables pulling ID for newly inserted host
                    app.db.session.flush()
                    app.db.session.commit()
                except:
                    return False, "Error during import of devices into database"

        return True, "Successfully added all %s devices" % (len(csvImport))

    def getOSType(self, i=None):
        """
        Process OS Type

        :i (input)

        returns os
        """

        # TODO consider returning None instead of Error?

        if self.source == 'netbox':
            r = requests.get(self.url + '/api/dcim/device-types/' + str(i))
            if r.status_code == requests.codes.ok:

                try:
                    os = r.json()['custom_fields']['Netconfig_OS']['label']
                except KeyError:
                    return "Error"
            else:
                return "Error"

        else:
            # TODO this isn't great since I'm using the same input above
            # for both id and os (figure out a way around this)
            i = os

        if os.lower() == 'ios':
            return "cisco_ios"
        elif os.lower() == 'ios-xe':
            return "cisco_xe"
        elif os.lower() == 'nx-os':
            return "cisco_nxos"
        elif os.lower() == 'asa':
            return "cisco_asa"
        else:
            return "Error"

    def deleteHostInDB(x):
        """Remove host from database.

        Returns True if successful.
        x is the host ID
        """

        # IDEA change Netbox Netconfig field for "deleting"

        try:
            host = app.models.Host.query.filter_by(id=x).first()
            app.db.session.delete(host)
            app.db.session.commit()
            return True
        except:
            return False

    def getHosts(self):
        """Get certain number of devices in database."""

        data = []

        if self.source == 'local':

            for host in app.models.Host.query.order_by(app.models.Host.hostname).all():

                # TODO consider adding this to the database?
                h = host.__dict__
                h['source'] = "local"

                data.append(h)

        elif self.source == 'netbox':
            r = requests.get(self.url + '/api/dcim/devices/?limit=0')

            if r.status_code == requests.codes.ok:

                for d in r.json()['results']:
                    if (d['custom_fields']['Netconfig'] and
                    d['custom_fields']['Netconfig']['label'] == 'Yes'):

                        os_type = self.getOSType(d['device_type']['id'])
                        host = {"id": d['id'], "hostname": d['name'],
                                "ipv4_addr": d['primary_ip']['address'].split('/')[0],
                                "type": d['device_type']['model'],
                                "ios_type": os_type,
                                "source": "netbox",
                                "local_creds": False}

                        data.append(host)

        return data

    def retrieveHostByID(self, x):
        """Get device by ID, regardless of data store location.

        Support local database or Netbox inventory.
        Does not return SSH session.
        x = host id
        """

        # TODO consider merging with getHosts

        if self.source == 'local':
            # TODO handle downstream to use a dictionary not a model
            host = app.models.Host.query.filter_by(id=x).first()

            return host.__dict__
        elif self.source == 'netbox':

            r = requests.get(self.url + '/api/dcim/devices/' + str(x))

            if r.status_code == requests.codes.ok:
                d = r.json()

                os_type = self.getOSType(d['device_type']['id'])
                host = {"id": d['id'], "hostname": d['name'],
                        "ipv4_addr": d['primary_ip']['address'].split('/')[0],
                        "type": d['device_type']['model'],
                        "ios_type": os_type,
                        "local_creds": False}

            else:
                return None

        return host

    def getHostByID(self, x):
        """Get device by ID along with active Netmiko SSH session.

        x = host id
        """
        host = self.retrieveHostByID(x)

        # TODO see if I can get rid of this

        # Get host class based on device type
        return dt.DeviceHandler(id=host['id'], hostname=host['hostname'],
                                ipv4_addr=host['ipv4_addr'], type=host['type'],
                                ios_type=host['ios_type'],
                                local_creds=host['local_creds'])

    def editHostInDatabase(self, id, hostname, ipv4_addr, hosttype,
                           ios_type, local_creds, local_creds_updated):
        """Edit device in database.

        This is only supported when using the local database.
        """

        # IDEA modify existing Netbox devices?

        if self.source == 'local':
            try:
                host = app.models.Host.query.filter_by(id=id).first()
                if hostname:
                    host.hostname = hostname
                if ipv4_addr:
                    host.ipv4_addr = ipv4_addr
                if hosttype:
                    host.type = hosttype
                if ios_type:
                    host.ios_type = ios_type
                if local_creds_updated:
                    host.local_creds = local_creds
                app.db.session.commit()
                return True
            except:
                return False
        else:
            return False

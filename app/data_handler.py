#!/usr/bin/python

import app
import requests
from requests.exceptions import ConnectionError
import csv
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from netaddr import IPAddress, core
from .device_classes import device_type


class DataHandler(object):
    """Handler object for data sources."""

    def __init__(self, source, netbox_url=None):
        """Data handler initialization function."""
        self.source = source
        self.url = netbox_url

    def add_host_to_db(self, hostname, ipv4_addr, type, ios_type, local_creds):
        """Add host to database.  Returns True if successful."""
        try:
            host = app.models.Host(hostname=hostname, ipv4_addr=ipv4_addr,
                                   type=type.capitalize(),
                                   ios_type=ios_type,
                                   local_creds=local_creds)
            app.db.session.add(host)
            # This enables pulling ID for newly inserted host
            app.db.session.flush()
            app.db.session.commit()
        except (IntegrityError, InvalidRequestError) as e:
            app.db.session.rollback()
            return False, 0, e

        try:
            app.logger.write_log("Added new host %s to database" % (host.hostname))
            return True, host.id, None
        except Exception as e:
            return False, 0, e

    def add_proxy_to_db(self, proxy_name, proxy_settings):
        """Add proxy settings to DB"""
        try:
            proxy = app.models.ProxySettings(proxy_name=proxy_name,
                                             proxy_settings=proxy_settings)
            app.db.session.add(proxy)
            # This enables pulling ID for newly inserted host
            app.db.session.flush()
            app.db.session.commit()
        except (IntegrityError, InvalidRequestError) as e:
            app.db.session.rollback()
            return False, 0, e

        try:
            app.logger.write_log("Updated proxy settings %s in database" % proxy.proxy_name)
            return True, proxy.id, None
        except Exception as e:
            return False, 0, e

    def import_hosts_to_db(self, csv_import):
        """Import hosts to database.

        Returns True if successful
        Format: Hostname,IPAddress,DeviceType,IOSType
        """
        reader = csv.reader(csv_import.strip().splitlines())
        errors = []
        hosts = []
        for row in reader:
            error = {}

            # Input validation checks
            if len(row) < 4:
                error = {'hostname': row[0], 'error': "Invalid number of fields in entry"}
                errors.append(error)
                continue

            try:
                IPAddress(row[1])
            except core.AddrFormatError:
                error = {'hostname': row[0], 'error': "Invalid IP address"}
                errors.append(error)
                continue

            # TODO: Move list to imported file
            if row[2].lower().strip() not in ("switch", "router", "firewall"):
                error = {'hostname': row[0], 'error': "Invalid device type"}
                errors.append(error)
                continue

            ios_type = self.get_os_type(row[3])
            if ios_type.lower() == "error":
                error = {'hostname': row[0], 'error': "Invalid OS type"}
                errors.append(error)
                continue

            if app.models.Host.query.filter_by(hostname=row[0]).first():
                error = {'hostname': row[0], 'error': "Duplicate hostname in database"}
                errors.append(error)
                continue

            if app.models.Host.query.filter_by(ipv4_addr=row[1]).first():
                error = {'hostname': row[0], 'error': "Duplicate IPv4 address in database"}
                errors.append(error)
                continue

            # Initial validation checks completed successfully. Import into DB
            try:
                if row[4].strip().lower() == 'true':
                    local_creds = True
                else:
                    local_creds = False
            except IndexError:
                local_creds = False

            try:
                # TODO could probably use self.add_host_to_db
                host = app.models.Host(hostname=row[0].strip(),
                                       ipv4_addr=row[1],
                                       type=row[2].capitalize(),
                                       ios_type=ios_type,
                                       local_creds=local_creds)
                app.db.session.add(host)
                app.db.session.flush()
                # Do this last, as we only want to add the host to var 'hosts' if it was fully successful
                hosts.append({"id": host.id, "hostname": row[0],
                              "ipv4_addr": row[1]})
            except (IntegrityError, InvalidRequestError):
                app.db.session.rollback()

        # Only commit once for all hosts added
        try:
            app.db.session.commit()
        except (IntegrityError, InvalidRequestError):
            app.db.session.rollback()

        return hosts, errors

    def get_os_type(self, os):
        """Process OS Type.

        :i (input)
        returns os
        """
        # TO DO consider returning None instead of Error?
        if self.source == 'netbox':
            try:
                r = requests.get(self.url + '/api/dcim/device-types/' + str(os))
            except ConnectionError:
                app.logger.write_log("Connection error trying to connect to " + self.url)
                return "error"
            if r.status_code == requests.codes.ok:

                try:
                    os = r.json()['custom_fields']['Netconfig_OS']['label'].strip()
                except KeyError:
                    return "error"
            else:
                return "error"

        # TODO: Move list elsewhere and import
        os = os.lower()
        if os == 'ios':
            return "cisco_ios"
        elif os == 'ios-xe':
            return "cisco_xe"
        elif os == 'nx-os':
            return "cisco_nxos"
        elif os == 'asa':
            return "cisco_asa"
        else:
            return "error"

    def delete_host_in_db(self, x):
        """Remove host from database.

        Returns True if successful.
        x is the host ID
        """
        # IDEA change Netbox Netconfig field for "deleting"

        try:
            host = app.models.Host.query.filter_by(id=x).first()
            app.db.session.delete(host)
            app.db.session.commit()
            app.logger.write_log('deleted host %s in database' % (host.hostname))
            return True
        except IntegrityError as err:
            app.logger.write_log('unable to delete host %s in database' % (host.hostname))
            app.logger.write_log(err)
            return False

    def get_hosts(self):
        """Get certain number of devices in database."""
        data = []

        if self.source == 'local':

            for host in app.models.Host.query.order_by(app.models.Host.hostname).all():

                # TO DO consider adding this to the database?
                h = host.__dict__
                h['source'] = "local"

                data.append(h)

        elif self.source == 'netbox':
            try:
                r = requests.get(self.url + '/api/dcim/devices/?limit=0')
            except ConnectionError:
                app.logger.write_log("Connection error trying to connect to " + self.url)
                return data

            if r.status_code == requests.codes.ok:

                for d in r.json()['results']:
                    if (d['custom_fields']['Netconfig'] and d['custom_fields']['Netconfig']['label'] == 'Yes'):

                        os_type = self.get_os_type(d['device_type']['id'])
                        host = {"id": d['id'], "hostname": d['name'],
                                "ipv4_addr": d['primary_ip']['address'].split('/')[0],
                                "type": d['device_type']['model'],
                                "ios_type": os_type,
                                "source": "netbox",
                                "local_creds": False}

                        data.append(host)

        return data

    def get_host_by_id(self, x):
        """Get device by ID, regardless of data store location.

        Support local database or Netbox inventory.
        Does not return SSH session.
        x = host id
        """
        # TO DO consider merging with get_hosts

        if self.source == 'local':
            # TO DO handle downstream to use a dictionary not a model
            host = app.models.Host.query.filter_by(id=x).first()
            try:
                host = host.__dict__
            except AttributeError:
                host = {}

        elif self.source == 'netbox':
            try:
                r = requests.get(self.url + '/api/dcim/devices/' + str(x))
            except ConnectionError:
                app.logger.write_log("Connection error trying to connect to " + self.url)
                return None

            if r.status_code == requests.codes.ok:
                d = r.json()

                os_type = self.get_os_type(d['device_type']['id'])
                host = {"id": d['id'], "hostname": d['name'],
                        "ipv4_addr": d['primary_ip']['address'].split('/')[0],
                        "type": d['device_type']['model'],
                        "ios_type": os_type,
                        "local_creds": False}
            else:
                return None

        # Get host class based on device type
        return device_type.device_handler(id=host['id'], hostname=host['hostname'],
                                          ipv4_addr=host['ipv4_addr'], type=host['type'],
                                          ios_type=host['ios_type'],
                                          local_creds=host['local_creds'])

    def edit_host_in_database(self, id, hostname, ipv4_addr, hosttype, ios_type, local_creds, local_creds_updated):
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

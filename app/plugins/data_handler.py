#!/usr/bin/python3

import app
import csv
import requests
from app.device_classes import device_type
from netaddr import IPAddress, core
from requests.exceptions import ConnectionError
from sqlalchemy.exc import IntegrityError, InvalidRequestError


class DataHandler(object):
    """Handler object for data sources."""

    def __init__(self, source, netbox_url=None):
        """Data handler initialization function."""
        self.source = source
        self.url = netbox_url

    def add_device_to_db(self, hostname, ipv4_addr, type, ios_type, local_creds):
        """Add device to database.  Returns True if successful."""
        try:
            device = app.models.Device(hostname=hostname, ipv4_addr=ipv4_addr,
                                       type=type.capitalize(), ios_type=ios_type,
                                       local_creds=local_creds)
            app.db.session.add(device)
            # This enables pulling ID for newly inserted device
            app.db.session.flush()
            app.db.session.commit()
        except (IntegrityError, InvalidRequestError) as e:
            app.db.session.rollback()
            return False, 0, e

        try:
            app.logger.info(f'Added new device {device.hostname} to database')
            return True, device.id, None
        except Exception as e:
            return False, 0, e

    def add_proxy_to_db(self, proxy_name, proxy_settings):
        """Add proxy settings to DB"""
        try:
            proxy = app.models.ProxySettings(proxy_name=proxy_name,
                                             proxy_settings=proxy_settings)
            app.db.session.add(proxy)
            # This enables pulling ID for newly inserted device
            app.db.session.flush()
            app.db.session.commit()
        except (IntegrityError, InvalidRequestError) as e:
            app.db.session.rollback()
            return False, 0, e

        try:
            app.logger.info("Updated proxy settings %s in database" % proxy.proxy_name)
            return True, proxy.id, None
        except Exception as e:
            return False, 0, e

    def import_devices_to_db(self, csv_import):
        """Import devices to database.

        Returns True if successful
        Format: Hostname,IPAddress,DeviceType,IOSType
        """
        reader = csv.reader(csv_import.strip().splitlines())
        errors = []
        devices = []
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

            if app.models.Device.query.filter_by(hostname=row[0]).first():
                error = {'hostname': row[0], 'error': "Duplicate hostname in database"}
                errors.append(error)
                continue

            if app.models.Device.query.filter_by(ipv4_addr=row[1]).first():
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
                # TODO could probably use self.add_device_to_db
                device = app.models.Device(hostname=row[0].strip(),
                                           ipv4_addr=row[1],
                                           type=row[2].capitalize(),
                                           ios_type=ios_type,
                                           local_creds=local_creds)
                app.db.session.add(device)
                app.db.session.flush()
                # Do this last, as we only want to add the device to var 'devices' if it was fully successful
                devices.append({"id": device.id, "hostname": row[0],
                                "ipv4_addr": row[1]})
            except (IntegrityError, InvalidRequestError):
                app.db.session.rollback()

        # Only commit once for all devices added
        try:
            app.db.session.commit()
        except (IntegrityError, InvalidRequestError):
            app.db.session.rollback()

        return devices, errors

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
                app.logger.info("Connection error trying to connect to " + self.url)
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

    def delete_device_in_db(self, x):
        """Remove device from database.

        Returns True if successful.
        x is the device ID
        """
        # TODO: IDEA change Netbox Netconfig field for "deleting"

        try:
            device = app.models.Device.query.filter_by(id=x).first()
            app.db.session.delete(device)
            app.db.session.commit()
            app.logger.info(f'deleted device {device.hostname} in database')
            return True
        except IntegrityError as err:
            app.logger.error(f'unable to delete device in database')
            app.logger.error(f'error: {err}')
            return False

    def get_devices(self):
        """Get certain number of devices in database."""
        data = []

        if self.source == 'local':

            for device in app.models.Device.query.order_by(app.models.Device.hostname).all():

                # TODO consider adding this to the database?
                h = device.__dict__
                h['source'] = "local"

                data.append(h)

        elif self.source == 'netbox':
            try:
                r = requests.get(self.url + '/api/dcim/devices/?limit=0')
            except ConnectionError:
                app.logger.info("Connection error trying to connect to " + self.url)
                return data

            if r.status_code == requests.codes.ok:

                for d in r.json()['results']:
                    if (d['custom_fields']['Netconfig'] and d['custom_fields']['Netconfig']['label'] == 'Yes'):

                        os_type = self.get_os_type(d['device_type']['id'])
                        device = {"id": d['id'], "hostname": d['name'],
                                  "ipv4_addr": d['primary_ip']['address'].split('/')[0],
                                  "type": d['device_type']['model'],
                                  "ios_type": os_type,
                                  "source": "netbox",
                                  "local_creds": False}

                        data.append(device)

        return data

    def get_device_by_id(self, x):
        """Get device by ID, regardless of data store location.

        Support local database or Netbox inventory.
        Does not return SSH session.
        x = device id
        """
        # TODO consider merging with get_devices

        if self.source == 'local':
            # TO DO handle downstream to use a dictionary not a model
            device = app.models.Device.query.filter_by(id=x).first()
            try:
                device = device.__dict__
            except AttributeError:
                device = {}

        elif self.source == 'netbox':
            try:
                r = requests.get(self.url + '/api/dcim/devices/' + str(x))
            except ConnectionError:
                app.logger.error("Connection error trying to connect to " + self.url)
                return None

            if r.status_code == requests.codes.ok:
                d = r.json()

                os_type = self.get_os_type(d['device_type']['id'])
                device = {"id": d['id'], "hostname": d['name'],
                          "ipv4_addr": d['primary_ip']['address'].split('/')[0],
                          "type": d['device_type']['model'],
                          "ios_type": os_type,
                          "local_creds": False}
            else:
                return None

        # TODO: Fix this to pass just the dict only, not each specific arg
        # Get device class based on device type
        return device_type.device_handler(id=device['id'], hostname=device['hostname'],
                                          ipv4_addr=device['ipv4_addr'], type=device['type'],
                                          ios_type=device['ios_type'],
                                          local_creds=device['local_creds'])

    def edit_device_in_database(self, id, hostname, ipv4_addr, device_type, ios_type, local_creds, local_creds_updated):
        """Edit device in database.

        This is only supported when using the local database.
        """
        # TODO: IDEA modify existing Netbox devices?

        if self.source == 'local':
            try:
                device = app.models.Device.query.filter_by(id=id).first()
                if hostname:
                    device.hostname = hostname
                if ipv4_addr:
                    device.ipv4_addr = ipv4_addr
                if device_type:
                    device.type = device_type
                if ios_type:
                    device.ios_type = ios_type
                if local_creds_updated:
                    device.local_creds = local_creds
                app.db.session.commit()
                return True
            except:
                return False
        else:
            return False

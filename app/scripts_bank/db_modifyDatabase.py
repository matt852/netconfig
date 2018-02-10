from app import app, db, models, netbox
from sqlalchemy import asc, func
from netaddr import IPAddress, core
from ..device_classes import deviceType as dt


class Host(object):
    """Generic Host class that mimics Host db.model"""

    def __init__(self, id, hostname, ipv4_addr, type, ios_type, local_creds=False):
        """Initilization method."""
        self.id = id
        self.hostname = hostname
        self.ipv4_addr = ipv4_addr
        self.type = type
        self.ios_type = ios_type
        self.local_creds = local_creds


def addHostToDB(hostname, ipv4_addr, type, ios_type, local_creds):
    """Add host to database.  Returns True if successful."""
    try:
        host = models.Host(hostname=hostname, ipv4_addr=ipv4_addr, type=type, ios_type=ios_type, local_creds=local_creds)
        db.session.add(host)
        # This enables pulling ID for newly inserted host
        db.session.flush()
        db.session.commit()
        return True, host.id
    except:
        return False, 0


def importHostsToDB(csvImport):
    """Import hosts to database.

    Returns True if successful
    Format: Hostname,IPAddress,DeviceType,IOSType
    """
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

            os = xArray[3].strip().lower()

            if os == 'ios':
                ios_type = "cisco_ios"
            elif os == 'ios-xe':
                ios_type = "cisco_xe"
            elif os == 'nx-os':
                ios_type = "cisco_nxos"
            elif os == 'asa':
                ios_type = "cisco_asa"
            else:
                ios_type = "Error"

            if xArray[4].strip().lower() == 'true':
                local_creds = True
            elif xArray[4].strip().lower() == 'false':
                local_creds = False
            else:
                local_creds = False

            try:
                host = models.Host(hostname=hostname, ipv4_addr=ipv4_addr, type=type, ios_type=ios_type, local_creds=local_creds)
                db.session.add(host)
                # This enables pulling ID for newly inserted host
                db.session.flush()
                db.session.commit()
            except:
                return False, "Error during import of devices into database"

    return True, "Successfully added all %s devices" % (len(csvImport))


def deleteHostInDB(x):
    """Remove host from database.

    Returns True if successful.
    x is the host ID
    """
    try:
        host = models.Host.query.filter_by(id=x).first()
        db.session.delete(host)
        db.session.commit()
        return True
    except:
        return False


def getHosts(page):
    """Get certain number of devices in database."""
    hosts = models.Host.query.order_by(asc(models.Host.hostname)).paginate(page, app.config['POSTS_PER_PAGE'], False)
    return hosts


def getHostsAll():
    """Get all devices in database."""
    hosts = models.Host.query.all()
    return hosts


def getHostByHostname(x):
    """Get device in database by hostname."""
    host = models.Host.query.filter(func.lower(models.Host.hostname) == func.lower(x)).first()  # <-- not case sensitve
    return host


def getHostIDbyHostname(x):
    """Get device ID in database by hostname."""
    host = models.Host.query.filter_by(hostname=x).first()
    return host.id


def retrieveHostByID(x):
    """Get device by ID, regardless of data store location.

    Support local database or Netbox inventory.
    Does not return SSH session.
    x = host id
    """

    # TODO do we need to check this every single time we get a host?
    # There should be a host wrapper that handles the location under the hood

    if app.config['DATALOCATION'] == 'local':
        # TODO handle downstream to use a dictionary not a model
        return models.Host.query.filter_by(id=x).first()
    elif app.config['DATALOCATION'] == 'netbox':

        host = netbox.getHostByID(x)

        return Host(str(x), host['name'],
                    host['primary_ip']['address'].split('/', 1)[0],
                    host['device_type']['model'],
                    # can we get this in the previous response?
                    netbox.getDeviceTypeOS(host['device_type']['id']))


def getHostByID(x):
    """Get device by ID along with active Netmiko SSH session.

    x = host id
    """
    host = retrieveHostByID(x)

    # Get host class based on device type
    return dt.DeviceHandler(id=host.id, hostname=host.hostname, ipv4_addr=host.ipv4_addr, type=host.type, ios_type=host.ios_type, local_creds=host.local_creds)


def getHostnameByID(x):
    """Get device name by ID.

    x = id
    """
    host = retrieveHostByID(x)

    return str(host.hostname)


def getHostsByIOSType(x):
    """Get devices by IOS type."""
    hosts = models.Host.query.filter_by(ios_type=x)
    return hosts


def editHostInDatabase(originalHostID, hostname, ipv4_addr, hosttype, ios_type, local_creds, local_creds_updated):
    """Edit device in database.

    This is only supported when using the local database.
    """
    if app.config['DATALOCATION'] == 'local':
        try:
            host = models.Host.query.filter_by(id=originalHostID).first()
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
            db.session.commit()
            return True
        except:
            return False
    else:
        return False


def searchHostInDB(x):
    """Determine if provided IP address is in database.

    Return True if provided host IP address is in database.
    False if it is not.
    Also returns hostname of device.
    """
    try:
        host = models.Host.query.filter_by(ipv4_addr=x).first()
        if host:
            return True, host.hostname
        else:
            return False, ''
    except:
        return False, ''

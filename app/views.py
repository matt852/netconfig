#!/usr/bin/python3
import pdb
import json
import socket
from datetime import timedelta
from urllib.parse import quote_plus, unquote_plus
from app import app, datahandler, logger, sshhandler
from flask import flash, g, jsonify, redirect, render_template
from flask import request, session, url_for
from redis import StrictRedis
from .scripts_bank.redis_logic import reset_user_redis_expire_timer, store_user_in_redis
from .scripts_bank.lib.functions import check_for_version_update, interface_replace_slash
from .scripts_bank.lib.flask_functions import check_user_logged_in_status
from .forms import AddDeviceForm, AddDeviceTypeForm,  CustomCfgCommandsForm, CustomCommandsForm
from .forms import EditDeviceForm, EditInterfaceForm, ImportDevicesForm, LocalCredentialsForm, ProxySettingsForm


def initial_checks():
    """Run any functions required when user loads any page.

    x is device.id.
    """
    reset_user_redis_expire_timer()
    if not check_user_logged_in_status():
        return render_template('index.html',
                               title='Home')


def init_db():
    """Initialize local Redis database."""
    db = StrictRedis(
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        db=app.config['DB_NO'],
        charset='utf-8',
        decode_responses=True)
    return db


@app.before_request
def before_request():
    """Set auto logout timer for logged in users.

    Automatically logs user out of session after x minutes.
    This is set in settings.py via SESSIONTIMEOUT.
    """
    g.db = init_db()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=app.config['SESSIONTIMEOUT'])
    session.modified = True


@app.route('/ajaxcheckdeviceactivesshsession/<x>', methods=['GET', 'POST'])
def ajax_check_device_active_session(x):
    """Check if existing SSH session for device is currently active.

    Used for AJAX call only, on main viewdevices.html page.
    x = device id
    """
    device = datahandler.get_device_by_id(x)

    if device:
        if sshhandler.check_device_active_ssh_session(device):
            return 'True'
    return 'False'


@app.route('/nodeviceconnect/<device>')
@app.route('/errors/nodeviceconnect/<device>')
def no_device_connect_error(device):
    """Return error page if unable to connect to device."""
    return render_template('errors/nodeviceconnect.html', device=device)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    """Return index page for user.

    Requires user to be logged in to display home page displaying all devices.
    Else, redirect user to index page.
    """
    if 'USER' in session:
        return redirect(url_for('view_devices'))
    else:
        return render_template("index.html", title='Home')


@app.route('/disconnect_all_ssh')
def disconnect_all_ssh():
    """Disconnect all SSH sessions for all users."""
    sshhandler.disconnect_all_ssh_sessions()
    logger.info('disconnected all active SSH sessions')
    return redirect(url_for('index'))


@app.route('/getsshsessionscount')
def get_ssh_sessions_count():
    """Get number of saved/stored SSH sessions.

    x = device id
    """
    initial_checks()
    count = sshhandler.count_all_ssh_sessions()
    return jsonify(count=count)


@app.route('/checkupdates')
def check_updates():
    """Check for NetConfig updates on GitHub.

    Only check if configured to do so (default behaviour).
    Skip if CHECK_FOR_UPDATES set to False.
    """
    try:
        if app.config['CHECK_FOR_UPDATES']:
            # If set to true, check for updates
            return check_for_version_update(app.config)
        else:
            # Otherwise skip checking for updates
            return jsonify(status="True")
    except KeyError:
        # If settings variable doesn't exist, default to checking for updates
        return check_for_version_update(app.config)


@app.route('/displayrecentdevicenames')
def display_recent_device_names():
    """Get names of devices with existing saved/stored SSH sessions.

    x = device id
    """
    initial_checks()
    devices = sshhandler.get_names_of_ssh_session_devices()
    return render_template("recentsessionmenu.html",
                           devices=devices)


@app.route('/db/adddevicetype', methods=['GET', 'POST'])
def add_device_type():
    """Add new device type to local database."""
    initial_checks()
    form = AddDeviceTypeForm()
    if form.validate_on_submit():
        return redirect(url_for('results_add_device_type'))
    return render_template('db/adddevicetype.html',
                           title='Add device type to database',
                           form=form)


@app.route('/results/resultsadddevicetype', methods=['GET', 'POST'])
def results_add_device_type():
    """Confirm new device type details prior to saving in local database."""
    initial_checks()
    brand = request.form['brand']
    model = request.form['model']
    hardware_category = request.form['hardware_category']
    netmiko_category = request.form['netmiko_category']

    response, device_type_id, e = datahandler.add_device_type_to_db(brand, model, hardware_category, netmiko_category)
    if response:
        return render_template("results/resultsadddevicetype.html",
                               title='Add device type result',
                               brand=brand,
                               model=model,
                               hardware_category=hardware_category,
                               netmiko_category=netmiko_category)
    else:
        logger.error(f'error when adding new device to database: {e}')
        # TODO Add popup error message here
        return redirect(url_for('add_device_type'))


@app.route('/db/adddevices', methods=['GET', 'POST'])
def add_devices():
    """Add new device to local database."""
    initial_checks()
    form = AddDeviceForm()
    device_types = datahandler.get_devicetypes()
    form.device_type.choices = [(device.get('id'), device.get('model').capitalize())
                                for device in device_types]
    form.device_type.choices.insert(0, ('', ''))
    if form.validate_on_submit():
        return redirect(url_for('results_add_device'))
    return render_template('db/adddevices.html',
                           title='Add devices to database',
                           form=form)


@app.route('/results/resultsadddevice', methods=['GET', 'POST'])
def results_add_device():
    """Confirm new device details prior to saving in local database."""
    initial_checks()
    hostname = request.form['hostname']
    ipv4_addr = request.form['ipv4_addr']
    device_type = request.form['device_type']
    # ios_type = request.form['ios_type']
    # If checkbox is unchecked, this fails as the request.form['local_creds'] value returned is False
    if request.form.get('local_creds'):
        local_creds = True
    else:
        local_creds = False

    response, deviceid, e = datahandler.add_device_to_db(hostname, ipv4_addr, device_type, local_creds)
    if response:
        return render_template("results/resultsadddevice.html",
                               title='Add device result',
                               hostname=hostname,
                               ipv4_addr=ipv4_addr,
                               local_creds=local_creds,
                               deviceid=deviceid)
    else:
        logger.error(f'error when adding new device to database: {e}')
        # TODO Add popup error message here
        return redirect(url_for('add_devices'))


@app.route('/db/importdevices', methods=['GET', 'POST'])
def import_devices():
    """Import devices into local database via CSV formatted text."""
    initial_checks()
    form = ImportDevicesForm()
    if form.validate_on_submit():
        return redirect(url_for('results_import_devices'))
    return render_template('db/importdevices.html',
                           title='Import devices to database via CSV',
                           form=form)


@app.route('/results/resultsimportdevices', methods=['GET', 'POST'])
def results_import_devices():
    """Confirm CSV import device details prior to saving to local database."""
    initial_checks()
    devices, errors = datahandler.import_devices_to_db(request.form['csvimport'])
    return render_template("results/resultsimportdevices.html",
                           title='Import devices result',
                           devices=devices,
                           errors=errors)


@app.route('/editdevice/<x>', methods=['GET'])
def edit_device(x):
    """Edit device details in local database.

    x is device ID
    """
    device = datahandler.get_device_by_id(x)
    form = EditDeviceForm()
    device_types = datahandler.get_devicetypes()
    form.device_type.choices = [(device.get('id'), device.get('model').capitalize())
                                for device in device_types]
    form.device_type.choices.insert(0, ('', ''))
    if form.validate_on_submit():
        return redirect('/results/resultsdeviceedit')
    return render_template('editdevice.html',
                           title='Edit device in database',
                           id=x,
                           original_device=device.hostname,
                           form=form)


@app.route('/confirm/confirmmultipledevicedelete/<x>', methods=['GET'])
def confirm_multiple_device_delete(x):
    """Confirm deletion of multiple devices in local database.

    x = each device id to be deleted, separated by an '&' symbol
    """
    initial_checks()

    device_list = []
    for device in x.split('&'):
        if device:
            device_list.append(datahandler.get_device_by_id(device))
    return render_template("confirm/confirmmultipledevicedelete.html",
                           deviceList=device_list,
                           x=x)


@app.route('/results/resultsmultipledevicedeleted/<x>', methods=['GET', 'POST'])
def results_multiple_device_delete(x):
    """Display results from deleting multiple devices in local database.

    x = each device id to be deleted, separated by an '&' symbol
    """
    initial_checks()

    device_list = []
    for x in x.split('&'):
        if x:
            device = datahandler.get_device_by_id(x)
            device_list.append(device)
            datahandler.delete_device_in_db(x)
            try:
                sshhandler.disconnect_specific_ssh_session(device)
                logger.info('disconnected any remaining active sessions for device %s' % (device.hostname))
            except:
                logger.info('unable to attempt to disconnect device %s active sessions' % (device.hostname))

    overall_result = True
    return render_template("results/resultsmultipledevicedeleted.html",
                           overallResult=overall_result,
                           device_list=device_list)


# Shows all devices in database
@app.route('/db/viewdevices')
def view_devices():
    """Display all devices."""
    logger.info('viewed all devices')
    devices = datahandler.get_devices()
    device_types = datahandler.get_devicetypes()

    # TODO this should happen not during the view render
    # status = ph.reachable(devices)
    return render_template('db/viewdevices.html',
                           devices=devices,
                           device_types=device_types,
                           title='View devices in database')


@app.route('/deviceuptime/<x>')
def device_uptime(x):
    """Get uptime of selected device.

    x = device id.
    """
    initial_checks()
    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    logger.info('retrieved uptime on device %s' % (device.hostname))
    return jsonify(device.pull_device_uptime(active_session))


@app.route('/devicepoestatus/<x>')
def device_poe_status(x):
    """Get PoE status of all interfaces on device.

    x = device id.
    """
    initial_checks()
    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    logger.info('retrieved PoE status for interfaces on device %s' % (device.hostname))
    return json.dumps(device.pull_device_poe_status(active_session))


@app.route('/db/viewdevices/<x>', methods=['GET', 'POST'])
def view_specific_device(x):
    """Display specific device page.

    x is device.id
    """
    initial_checks()

    # This fixes page refresh issue when clicking on a Modal
    #  that breaks DataTables
    if 'modal' in x:
        # Return empty response, as the page is loaded from the Modal JS
        # However this breaks the Loading modal JS function.
        #  Unsure why, need to research
        return ('', 204)

    device = datahandler.get_device_by_id(x)

    logger.info('accessed device %s using IPv4 address %s' % (device.hostname, device.ipv4_addr))

    # Try statement as if this page was accessed directly and not via the Local Credentials form it will fail and we want to operate normally
    # Variable to determine if successfully connected to device use local credentials
    varFormSet = False
    try:
        if store_user_in_redis(request.form['user'], request.form['pw'], privpw=request.form['privpw'], device=device):
            # Set to True if variables are set correctly from local credentials form
            varFormSet = True
            logger.info('local credentials saved to REDIS for accessing device %s' % (device.hostname))

    except:
        # If no form submitted (not using local credentials), get SSH session
        # Don't go in if form was used (local credentials) but SSH session failed in above 'try' statement
        if not varFormSet:
            logger.info('credentials used of currently logged in user for accessing device %s' % (device.hostname))

    # Get any existing SSH sessions
    active_session = sshhandler.retrieve_ssh_session(device)
    result = device.pull_device_interfaces(active_session)

    if result:
        interfaces = device.count_interface_status(result)
        return render_template("db/viewspecificdevice.html",
                               device=device,
                               interfaces=interfaces,
                               result=result)
    else:
        # If interfaces is x.x.x.x skipped - connection timeout,
        #  throw error page redirect
        sshhandler.disconnect_specific_ssh_session(device)
        return redirect(url_for('no_device_connect_error',
                                device=device))


@app.route('/calldisconnectspecificsshsession/<x>')
def call_disconnect_specific_ssh_session(x):
    """Disconnect any SSH sessions for a specific device from all users.

    x = ID of device to disconnect.
    """
    device = datahandler.get_device_by_id(x)
    # Disconnect device.
    try:
        sshhandler.disconnect_specific_ssh_session(device)
    except:
        # Log error if unable to disconnect specific SSH session
        logger.info('unable to disconnect SSH session to provided device %s from user %s' % (device.hostname, session['USER']))
    return redirect(url_for('view_devices'))


######################
# Confirmation pages #
######################


@app.route('/confirm/confirmintenable/<x>', methods=['GET', 'POST'])
def confirm_int_enable(x):
    """Confirm enabling specific device interface before executing.

    x = device id
    """
    try:
        device = datahandler.get_device_by_id(x)
        if device:
            # Removes dashes from interface in URL
            return render_template("confirm/confirmintenable.html",
                                   device=device,
                                   interface=request.args.get('int', ''))
        else:
            return redirect(url_for('index'))
    except AttributeError:
        return redirect(url_for('index'))


@app.route('/confirm/confirmintdisable/<x>', methods=['GET', 'POST'])
def confirm_int_disable(x):
    """Confirm disabling specific device interface before executing.

    x = device id
    """
    try:
        device = datahandler.get_device_by_id(x)
        if device:
            # Removes dashes from interface in URL
            return render_template("confirm/confirmintdisable.html",
                                   device=device,
                                   interface=request.args.get('int', ''))
        else:
            return redirect(url_for('index'))
    except AttributeError:
        return redirect(url_for('index'))


@app.route('/confirm/confirmdevicedelete/<x>', methods=['GET', 'POST'])
def confirm_device_delete(x):
    """Confirm deleting device interface from local database.

    x = device ID
    """
    try:
        device = datahandler.get_device_by_id(x)
        if device:
            return render_template("confirm/confirmdevicedelete.html", device=device)
        else:
            return redirect(url_for('index'))
    except AttributeError:
        return redirect(url_for('index'))


@app.route('/confirm/confirmintedit/', methods=['POST'])
def confirm_int_edit():
    """Confirm settings to edit device interface with before executing."""
    deviceid = request.form['deviceid']
    device = datahandler.get_device_by_id(deviceid)
    deviceinterface = request.form['deviceinterface']
    datavlan = request.form['datavlan']
    voicevlan = request.form['voicevlan']
    other = request.form['other']
    otherEncoded = quote_plus(other, safe='/')

    return render_template("confirm/confirmintedit.html",
                           device=device,
                           deviceinterface=deviceinterface,
                           datavlan=datavlan,
                           voicevlan=voicevlan,
                           other=other,
                           otherEncoded=otherEncoded)


@app.route('/results/resultsdeviceedit/', methods=['GET', 'POST'])
@app.route('/results/resultsdeviceedit/<x>', methods=['GET', 'POST'])
def results_device_edit(x):
    """Confirm settings to edit device with in local database.

    x = original device ID
    """
    if 'modal' in x:
        return ('', 204)

    stored_device = datahandler.get_device_by_id(x)
    # Save all existing device variables, as the class stores get updated later in the function
    orig_hostname = stored_device.hostname
    orig_ipv4_addr = stored_device.ipv4_addr
    orig_device_type = stored_device.device_type
    orig_local_creds = stored_device.local_creds

    # Save form user inputs into new variables
    hostname = request.form.get('hostname') or ''
    ipv4_addr = request.form.get('ipv4_addr') or ''
    device_type = request.form.get('device_type') or ''
    if device_type:
        # TODO: Change model to name
        device_type_name = datahandler.get_devicetype_by_id(device_type)['model']
    if request.form.get('local_creds') == 'True':
        local_creds = True
        local_creds_updated = True
    elif request.form.get('local_creds') == 'False':
        local_creds = False
        local_creds_updated = True
    else:
        local_creds = ''
        local_creds_updated = False

    # If exists, disconnect any existing SSH sessions
    #  and clear them from the SSH dict
    try:
        sshhandler.disconnect_specific_ssh_session(stored_device)
        logger.debug(f'disconnected and cleared saved SSH session information'
                     f' for edited device {stored_device.hostname}')
    except (socket.error, EOFError):
        logger.debug(f'no existing SSH sessions for edited device {stored_device.hostname}')
    except:
        logger.debug(f'could not clear SSH session for edited device {stored_device.hostname}')

    result = datahandler.edit_device_in_database(stored_device.id, hostname, ipv4_addr, device_type, local_creds, local_creds_updated)

    if result:
        logger.info(f'edited device {stored_device.hostname} in database')
        return render_template("results/resultsdeviceedit.html",
                               title='Edit device confirm',
                               stored_device=stored_device,
                               hostname=hostname,
                               ipv4_addr=ipv4_addr,
                               device_type=device_type_name,
                               local_creds=local_creds,
                               local_creds_updated=local_creds_updated,
                               orig_hostname=orig_hostname,
                               orig_ipv4_addr=orig_ipv4_addr,
                               orig_device_type=orig_device_type,
                               orig_local_creds=orig_local_creds)
    else:
        return redirect(url_for('confirmDeviceEdit',
                                x=stored_device))


@app.route('/confirm/confirmcmdcustom/', methods=['GET', 'POST'])
def confirm_cmd_custom():
    """Confirm bulk command entry before executing."""
    session['HOSTNAME'] = request.form['hostname']
    session['COMMAND'] = request.form['command']
    session['DEVICEID'] = request.form['deviceid']

    return render_template("confirm/confirmcmdcustom.html")


@app.route('/confirm/confirmcfgcmdcustom/', methods=['GET', 'POST'])
def confirm_cfg_cmd_custom():
    """Confirm bulk configuration command entry before executing."""
    device = datahandler.get_device_by_id(request.form['deviceid'])
    session['HOSTNAME'] = request.form['hostname']
    session['COMMAND'] = request.form['command']
    session['DEVICEID'] = request.form['deviceid']
    session['IOS_TYPE'] = device.ios_type

    return render_template("confirm/confirmcfgcmdcustom.html")


#################
# Results pages #
#################


@app.route('/results/resultsinterfaceenabled/<x>/<y>', methods=['GET', 'POST'])
def results_int_enabled(x, y):
    """Display results for enabling specific interface.

    # x = device id
    # y = interface name
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(device)

    # Removes dashes from interface in URL and enabel interface
    result = device.run_enable_interface_cmd(interface_replace_slash(y), active_session)

    logger.info('enabled interface %s on device %s' % (y, device.hostname))
    return render_template("results/resultsinterfaceenabled.html",
                           device=device, interface=y, result=result)


@app.route('/results/resultsinterfacedisabled/<x>/<y>', methods=['GET', 'POST'])
def results_int_disabled(x, y):
    """Display results for disabling specific interface.

    x = device id
    y = interface name
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(device)

    # Removes dashes from interface in URL and disable interface
    result = device.run_disable_interface_cmd(interface_replace_slash(y), active_session)

    logger.info('disabled interface %s on device %s' % (y, device.hostname))
    return render_template("results/resultsinterfacedisabled.html",
                           device=device, interface=y, result=result)


@app.route('/results/resultsinterfaceedit/<x>/<datavlan>/<voicevlan>/<other>', methods=['GET', 'POST'])
def results_int_edit(x, datavlan, voicevlan, other):
    """Display results for editing specific interface config settings.

    x = device id
    d = data vlan
    v = voice vlan
    o = other
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(device)

    # Get interface from passed variable in URL
    deviceinterface = request.args.get('int', '')

    # Decode 'other' string
    other = unquote_plus(other).decode('utf-8')

    # Replace '___' with '/'
    other = other.replace('___', '/')

    # Replace '\r\n' with '\n'
    other = other.replace('\r\n', '\n')

    # Remove dashes from interface in URL and edit interface config
    result = device.run_edit_interface_cmd(deviceinterface, datavlan, voicevlan, other, active_session)

    logger.info('edited interface %s on device %s' % (deviceinterface, device.hostname))
    return render_template("results/resultsinterfaceedit.html", device=device,
                           interface=deviceinterface, datavlan=datavlan,
                           voicevlan=voicevlan, other=other, result=result)


@app.route('/results/resultsdevicedeleted/<x>', methods=['GET', 'POST'])
def results_device_deleted(x):
    """Display results for deleting device from local database.

    x = device ID
    """
    device = datahandler.get_device_by_id(x)
    if device:
        # Removes device from database
        result = datahandler.delete_device_in_db(device.id)
        if result:
            sshhandler.disconnect_specific_ssh_session(device)
            return render_template("results/resultsdevicedeleted.html",
                                   device=device, result=result)
        else:
            return redirect(url_for('confirm_device_delete', x=device.id))
    else:
        return redirect(url_for('index'))


@app.route('/results/resultscmdcustom/', methods=['GET', 'POST'])
def results_cmd_custom():
    """Display results from bulk command execution on device."""
    initial_checks()

    device = datahandler.get_device_by_id(session['DEVICEID'])

    active_session = sshhandler.retrieve_ssh_session(device)

    command = session['COMMAND']

    result = device.run_multiple_commands(command, active_session)

    session.pop('HOSTNAME', None)
    session.pop('COMMAND', None)
    session.pop('DEVICEID', None)

    logger.info('ran custom commands on device %s' % (device.hostname))
    return render_template("results/resultscmdcustom.html",
                           device=device,
                           command=command,
                           result=result)


@app.route('/results/resultscfgcmdcustom/', methods=['GET', 'POST'])
def results_cfg_cmd_custom():
    """Display results from bulk configuration command execution on device."""
    initial_checks()

    device = datahandler.get_device_by_id(session['DEVICEID'])

    active_session = sshhandler.retrieve_ssh_session(device)

    command = session['COMMAND']

    result = device.run_multiple_config_commands(command, active_session)

    session.pop('HOSTNAME', None)
    session.pop('COMMAND', None)
    session.pop('DEVICEID', None)
    session.pop('IOS_TYPE', None)

    logger.info('ran custom config commands on device %s' % (device.hostname))
    return render_template("results/resultscfgcmdcustom.html",
                           device=device,
                           command=command,
                           result=result)


###############
# Modal pages #
###############


@app.route('/modalinterface/', methods=['GET', 'POST'])
@app.route('/modalinterface/<x>/<y>', methods=['GET', 'POST'])
def modal_specific_interface_on_device(x, y):
    """Show specific interface details from device.

    x = device id
    y = interface name
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(device)

    # Removes dashes from interface in URL, replacing '_' with '/'
    interface = interface_replace_slash(y)
    # Replace's '=' with '.'
    device.interface = interface.replace('=', '.')

    int_config, int_mac_addr, int_stats = device.pull_interface_info(active_session)
    mac_to_ip = ''

    logger.info('viewed interface %s on device %s' % (device.interface, device.hostname))
    return render_template("viewspecificinterfaceondevice.html",
                           device=device,
                           interface=interface,
                           int_config=int_config,
                           intMacAddr=int_mac_addr,
                           macToIP=mac_to_ip,
                           intStats=int_stats)


@app.route('/modaleditinterface/<x>', methods=['GET', 'POST'])
def modal_edit_interface_on_device(x):
    """Display modal to edit specific interface on device.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(device)

    # Removes dashes from interface in URL
    # interface = interface_replace_slash(y)
    # Replace's '=' with '.'
    # device.interface = interface.replace('=', '.')

    # Set interface to passed parameter in URL
    device.interface = request.args.get('int', '')

    int_config = device.pull_interface_config(active_session)
    # Edit form
    form = EditInterfaceForm(request.values, device=device, interface=device.interface)

    if form.validate_on_submit():
        flash('Interface to edit - "%s"' % (device.interface))
        return redirect('/confirm/confirmintedit')

    return render_template("editinterface.html",
                           deviceid=device.id,
                           deviceinterface=device.interface,
                           int_config=int_config,
                           form=form)


@app.route('/modallocalcredentials/<x>', methods=['GET', 'POST'])
def modal_local_credentials(x):
    """Get local credentials from user.

    x is device ID
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    if sshhandler.check_device_active_ssh_session(device):
        return redirect('/db/viewdevices/%s' % (device.id))

    form = LocalCredentialsForm()
    logger.info('saved local credentials for device %s' % (device.hostname))
    return render_template('localcredentials.html',
                           title='Login with local SSH credentials',
                           form=form,
                           device=device)


@app.route('/modalcmdshowrunconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdshowrunconfig/<x>', methods=['GET', 'POST'])
def modal_cmd_show_run_config(x):
    """Display modal with active/running configuration settings on device.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    device_config = device.pull_run_config(active_session)
    logger.info('viewed running-config via button on device %s' % (device.hostname))
    return render_template("cmdshowrunconfig.html",
                           device=device,
                           device_config=device_config)


@app.route('/modalcmdshowstartconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdshowstartconfig/<x>', methods=['GET', 'POST'])
def modal_cmd_show_start_config(x):
    """Display modal with saved/stored configuration settings on device.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    device_config = device.pull_start_config(active_session)
    logger.info('viewed startup-config via button on device %s' % (device.hostname))
    return render_template("cmdshowstartconfig.html",
                           device=device,
                           device_config=device_config)


@app.route('/modalcmdshowcdpneigh/', methods=['GET', 'POST'])
@app.route('/modalcmdshowcdpneigh/<x>', methods=['GET', 'POST'])
def modal_cmd_show_cdp_neigh(x):
    """Display modal with CDP/LLDP neighbors info for device.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    neigh = device.pull_cdp_neighbor(active_session)
    logger.info('viewed CDP neighbors via button on device %s' % (device.hostname))
    return render_template("cmdshowcdpneigh.html",
                           device=device,
                           neigh=neigh)


@app.route('/modalcmdshowinventory/', methods=['GET', 'POST'])
@app.route('/modalcmdshowinventory/<x>', methods=['GET', 'POST'])
def modal_cmd_show_inventory(x):
    """Display modal with device inventory information.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    result = device.pull_inventory(active_session)

    logger.info('viewed inventory info via button on device %s' % (device.hostname))
    return render_template("cmdshowinventory.html",
                           device=device,
                           result=result)


@app.route('/modalcmdshowversion/', methods=['GET', 'POST'])
@app.route('/modalcmdshowversion/<x>', methods=['GET', 'POST'])
def modal_cmd_show_version(x):
    """Display modal with device version information.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    result = device.pull_version(active_session)

    logger.info('viewed version info via button on device %s' % (device.hostname))
    return render_template("cmdshowversion.html",
                           device=device,
                           result=result)


@app.route('/modalcmdcustom/<x>', methods=['GET', 'POST'])
def modal_cmd_custom(x):
    """Display modal to retrieve custom bulk commands to execute.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    # Custom Commands form
    form = CustomCommandsForm(request.values, hostname=device.hostname)

    return render_template("cmdcustom.html",
                           device=device,
                           form=form)


@app.route('/modalcfgcmdcustom/<x>', methods=['GET', 'POST'])
def modal_cfg_cmd_custom(x):
    """Display modal to retrieve custom bulk config commands to execute.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    # Custom Commands form
    form = CustomCfgCommandsForm(request.values, hostname=device.hostname)

    return render_template("cfgcmdcustom.html",
                           device=device,
                           form=form)


@app.route('/modalcmdsaveconfig/<x>', methods=['GET', 'POST'])
def modal_cmd_save_config(x):
    """Save device configuration to memory and display result in modal.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    device.save_config_on_device(active_session)

    logger.info('saved config via button on device %s' % (device.hostname))
    return render_template("cmdsaveconfig.html",
                           device=device)


@app.route('/db/viewdevices/deviceshell/<x>', methods=['GET', 'POST'])
def device_shell(x):
    """Display iShell input fields.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)

    # Exit config mode if currently in it on page refresh/load
    exit_config_mode(device.id)

    logger.info('accessed interactive shell on device %s' % (device.hostname))
    return render_template("deviceshell.html",
                           device=device)


@app.route('/deviceshelloutput/<x>/<m>/<y>', methods=['GET', 'POST'])
def device_shell_output(x, m, y):
    """Display iShell output fields.

    x = device id
    m = config or enable mode
    y = encoded commands from javascript
    """
    initial_checks()

    config_error = False

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)

    # Replace '___' with '/'
    x = unquote_plus(y).decode('utf-8')
    command = x.replace('___', '/')
    # command = interface_replace_slash(unquote_plus(y).decode('utf-8'))

    # Append prompt and command executed to beginning of output
    # output.append(device.find_prompt_in_session(active_session) + command)

    # Check if last character is a '?'
    if command[-1] == '?':
        if m == 'c':
            # Get command output as a list.
            # Insert list contents into 'output' list.
            config_error = True
            output = ''
        else:
            # Run command on provided existing SSH session and returns output.
            # Since we set normalize to False, we need to do this.
            # The normalize() function in NetMiko does rstrip and adds a CR to the end of the command.
            output = active_session.send_command(command.strip(), normalize=False).splitlines()

    else:
        if m == 'c':
            # Get configuration command output from network device, split output by newline
            output = active_session.send_config_set(command, exit_config_mode=False).splitlines()
            # Remove first item in list, as Netmiko returns the command ran only in the output
            output.pop(0)
        else:
            output = device.get_cmd_output(command, active_session)

    logger.info('ran command on device %s - %s' % (device.hostname, command))

    return render_template("deviceshelloutput.html",
                           output=output,
                           command=command,
                           mode=m,
                           config_error=config_error)


@app.route('/enterconfigmode/<x>', methods=['GET', 'POST'])
def enter_config_mode(x):
    """Enter device configuration mode.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    # Enter configuration mode on device using existing SSH session
    active_session.config_mode()
    logger.info('entered config mode via iShell on device %s' % (device.hostname))
    return ('', 204)


@app.route('/exitconfigmode/<x>', methods=['GET', 'POST'])
def exit_config_mode(x):
    """Exit device configuration mode.

    x = device id
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)
    # Exit configuration mode on device using existing SSH session
    active_session.exit_config_mode()

    logger.info('exited config mode via iShell on device %s' % (device.hostname))
    return ('', 204)


#######################################
# Begin Multiple Interface Selections #
#######################################


@app.route('/confirm/confirmmultipleintenable/<x>/<y>', methods=['GET', 'POST'])
def confirm_multi_int_enable(x, y):
    """Confirm enabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    device = datahandler.get_device_by_id(x)
    return render_template("confirm/confirmmultipleintenable.html",
                           device=device,
                           interfaces=y)


@app.route('/confirm/confirmmultipleintdisable/<x>/<y>', methods=['GET', 'POST'])
def confirm_multi_int_disable(x, y):
    """Confirm disabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    device = datahandler.get_device_by_id(x)
    return render_template("confirm/confirmmultipleintdisable.html",
                           device=device,
                           interfaces=y)


@app.route('/confirm/confirmmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def confirm_multi_int_edit(x, y):
    """Confirm editing multiple device interfaces.  WIP.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    device = datahandler.get_device_by_id(x)
    return render_template("confirm/confirmmultipleintedit.html",
                           device=device,
                           interfaces=y)


@app.route('/results/resultsmultipleintenabled/<x>/<y>', methods=['GET', 'POST'])
def results_multi_int_enabled(x, y):
    """Display results from enabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
        # a = interface
        if a:
            # Removes dashes from interface in URL
            a = interface_replace_slash(a)
            result.append(device.run_enable_interface_cmd(a, active_session))

    logger.info('enabled multiple interfaces on device %s' % (device.hostname))
    return render_template("results/resultsmultipleintenabled.html",
                           device=device,
                           interfaces=y,
                           result=result)


@app.route('/results/resultsmultipleintdisabled/<x>/<y>', methods=['GET', 'POST'])
def results_multi_int_disabled(x, y):
    """Display results from disabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
        if a:
            # Removes dashes from interface in URL
            a = interface_replace_slash(a)
            result.append(device.run_disable_interface_cmd(a, active_session))

    logger.info('disabled multiple interfaces on device %s' % (device.hostname))
    return render_template("results/resultsmultipleintdisabled.html",
                           device=device,
                           interfaces=y,
                           result=result)


@app.route('/results/resultsmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def results_multi_int_edit(x, y):
    """Display results from editing multiple device interfaces.  WIP.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    initial_checks()

    device = datahandler.get_device_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(device)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
        if a:
            # Removes dashes from interface in URL
            a = interface_replace_slash(a)

    result.append(device.save_config_on_device(active_session))

    logger.info('edited multiple interfaces on device %s' % (device.hostname))
    return render_template("results/resultsmultipleintedit.html",
                           device=device,
                           interfaces=y,
                           result=result)

#####################################
# End Multiple Interface Selections #
#####################################


############
# Settings #
############

@app.route('/editsettings', methods=['GET', 'POST'])
def edit_settings():
    """Modify Netconfig settings."""
    initial_checks()

    try:
        with open(app.config['SETTINGSFILE'], 'r') as s:
            return render_template('editsettings.html',
                                   title='Edit Netconfig settings',
                                   file=s.readlines())
    except:
        return render_template('errors/500.html', error="Unable to read Settings File"), 500


@app.route('/proxysettings', methods=['GET'])
def proxy_settings():
    """Modify proxy settings."""
    initial_checks()

    form = ProxySettingsForm()
    return render_template('proxysettings.html',
                           title='Edit Proxy Settings',
                           form=form)


@app.route('/results/resultseditproxy', methods=['GET', 'POST'])
def results_edit_proxy():
    """Save proxy details to database."""
    # Need to make results page and datahandler.add_proxy_to_db function
    initial_checks()
    proxy_name = request.form['proxy_name']
    proxy_settings = request.form['proxy_settings']

    response, deviceid, e = datahandler.add_proxy_to_db(proxy_name, proxy_settings)
    if response:
        return render_template("results/resultseditproxy.html",
                               title='Edit proxy settings result',
                               proxy_name=proxy_name,
                               proxy_settings=proxy_settings,
                               deviceid=deviceid)
    else:
        logger.info('exception thrown when adding/editing proxy settings to database: %s' % e)
        # TO-DO Add popup error message here
        return redirect(url_for('proxy_settings'))

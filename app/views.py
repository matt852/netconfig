#!/usr/bin/python3

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
from .forms import AddHostForm, CustomCfgCommandsForm, CustomCommandsForm
from .forms import EditHostForm, EditInterfaceForm, ImportHostsForm, LocalCredentialsForm, ProxySettingsForm


def initial_checks():
    """Run any functions required when user loads any page.

    x is host.id.
    """
    reset_user_redis_expire_timer()
    if not check_user_logged_in_status():
        return render_template("index.html",
                               title='Home')


def init_db():
    """Initialize local Redis database."""
    db = StrictRedis(
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        db=app.config['DB_NO'],
        charset="utf-8",
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


@app.route('/ajaxcheckhostactivesshsession/<x>', methods=['GET', 'POST'])
def ajax_check_host_active_session(x):
    """Check if existing SSH session for host is currently active.

    Used for AJAX call only, on main viewhosts.html page.
    x = host id
    """
    host = datahandler.get_host_by_id(x)

    if host:
        if sshhandler.check_host_active_ssh_session(host):
            return 'True'
    return 'False'


@app.route('/nohostconnect/<host>')
@app.route('/errors/nohostconnect/<host>')
def no_host_connect_error(host):
    """Return error page if unable to connect to device."""
    return render_template('errors/nohostconnect.html', host=host)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    """Return index page for user.

    Requires user to be logged in to display home page displaying all devices.
    Else, redirect user to index page.
    """
    if 'USER' in session:
        return redirect(url_for('view_hosts'))
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

    x = host id
    """
    initial_checks()
    count = sshhandler.count_all_ssh_sessions()
    return jsonify(count=count)


@app.route('/checkupdates')
def check_updates():
    """Check for NetConfig updates on GitHub.

    Only check if configured to do so (default behaviour).
    Skip if CHECK_FOR_UDPATES set to False.
    """
    try:
        if app.config['CHECK_FOR_UDPATES']:
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

    x = host id
    """
    initial_checks()
    hosts = sshhandler.get_names_of_ssh_session_devices()
    return render_template("/recentsessionmenu.html",
                           hosts=hosts)


@app.route('/db/addhosts', methods=['GET', 'POST'])
def add_hosts():
    """Add new device to local database."""
    initial_checks()
    form = AddHostForm()
    if form.validate_on_submit():
        return redirect(url_for('results_add_host'))
    return render_template('/db/addhosts.html',
                           title='Add hosts to database',
                           form=form)


@app.route('/results/resultsaddhost', methods=['GET', 'POST'])
def results_add_host():
    """Confirm new host details prior to saving in local database."""
    initial_checks()
    hostname = request.form['hostname']
    ipv4_addr = request.form['ipv4_addr']
    hosttype = request.form['hosttype']
    ios_type = request.form['ios_type']
    # If checkbox is unchecked, this fails as the request.form['local_creds'] value returned is False
    if request.form.get('local_creds'):
        local_creds = True
    else:
        local_creds = False

    response, hostid, e = datahandler.add_host_to_db(hostname, ipv4_addr, hosttype, ios_type, local_creds)
    if response:
        return render_template("/results/resultsaddhost.html",
                               title='Add host result',
                               hostname=hostname,
                               ipv4_addr=ipv4_addr,
                               hosttype=hosttype,
                               ios_type=ios_type,
                               local_creds=local_creds,
                               hostid=hostid)
    else:
        logger.info('exception thrown when adding new host to database: %s' % (e))
        # TO-DO Add popup error message here
        return redirect(url_for('add_hosts'))


@app.route('/db/importhosts', methods=['GET', 'POST'])
def import_hosts():
    """Import devices into local database via CSV formatted text."""
    initial_checks()
    form = ImportHostsForm()
    if form.validate_on_submit():
        return redirect(url_for('results_import_hosts'))
    return render_template('/db/importhosts.html',
                           title='Import hosts to database via CSV',
                           form=form)


@app.route('/results/resultsimporthosts', methods=['GET', 'POST'])
def results_import_hosts():
    """Confirm CSV import device details prior to saving to local database."""
    initial_checks()
    hosts, errors = datahandler.import_hosts_to_db(request.form['csvimport'])
    return render_template("/results/resultsimporthosts.html",
                           title='Import devices result',
                           hosts=hosts,
                           errors=errors)


@app.route('/edithost/<x>', methods=['GET'])
def edit_host(x):
    """Edit device details in local database.

    x is host ID
    """
    host = datahandler.get_host_by_id(x)
    form = EditHostForm()
    if form.validate_on_submit():
        return redirect('/results/resultshostedit')
    return render_template('/edithost.html',
                           title='Edit host in database',
                           id=x,
                           originalHost=host.hostname,
                           form=form)


@app.route('/confirm/confirmmultiplehostdelete/<x>', methods=['GET'])
def confirm_multiple_host_delete(x):
    """Confirm deletion of multiple devices in local database.

    x = each host id to be deleted, separated by an '&' symbol
    """
    initial_checks()

    hostList = []
    for host in x.split('&'):
        if host:
            hostList.append(datahandler.get_host_by_id(host))
    return render_template("confirm/confirmmultiplehostdelete.html",
                           hostList=hostList,
                           x=x)


@app.route('/results/resultsmultiplehostdeleted/<x>', methods=['GET', 'POST'])
def results_multiple_host_delete(x):
    """Display results from deleting multiple devices in local databse.

    x = each host id to be deleted, separated by an '&' symbol
    """
    initial_checks()

    hostList = []
    for x in x.split('&'):
        if x:
            host = datahandler.get_host_by_id(x)
            hostList.append(host)
            datahandler.delete_host_in_db(x)
            try:
                sshhandler.disconnect_specific_ssh_session(host)
                logger.info('disconnected any remaining active sessions for host %s' % (host.hostname))
            except:
                logger.info('unable to attempt to disconnect host %s active sessions' % (host.hostname))

    overallResult = True
    return render_template("results/resultsmultiplehostdeleted.html",
                           overallResult=overallResult,
                           hostList=hostList)


# Shows all hosts in database
@app.route('/db/viewhosts')
def view_hosts():
    """Display all devices."""
    logger.info('viewed all hosts')
    hosts = datahandler.get_hosts()

    # TODO this should happen not during the view render
    # status = ph.reachable(hosts)
    return render_template('/db/viewhosts.html',
                           hosts=hosts,
                           title='View hosts in database')


@app.route('/deviceuptime/<x>')
def device_uptime(x):
    """Get uptime of selected device.

    x = host id.
    """
    initial_checks()
    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    logger.info('retrieved uptime on host %s' % (host.hostname))
    return jsonify(host.pull_device_uptime(active_session))


@app.route('/devicepoestatus/<x>')
def device_poe_status(x):
    """Get PoE status of all interfaces on device.

    x = host id.
    """
    initial_checks()
    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    logger.info('retrieved PoE status for interfaces on host %s' % (host.hostname))
    return json.dumps(host.pull_device_poe_status(active_session))


@app.route('/db/viewhosts/<x>', methods=['GET', 'POST'])
def view_specific_host(x):
    """Display specific device page.

    x is host.id
    """
    initial_checks()

    # This fixes page refresh issue when clicking on a Modal
    #  that breaks DataTables
    if 'modal' in x:
        # Return empty response, as the page is loaded from the Modal JS
        # However this breaks the Loading modal JS function.
        #  Unsure why, need to research
        return ('', 204)

    host = datahandler.get_host_by_id(x)

    logger.info('accessed host %s using IPv4 address %s' % (host.hostname, host.ipv4_addr))

    # Try statement as if this page was accessed directly and not via the Local Credentials form it will fail and we want to operate normally
    # Variable to determine if successfully connected to host use local credentials
    varFormSet = False
    try:
        if store_user_in_redis(request.form['user'], request.form['pw'], privpw=request.form['privpw'], host=host):
            # Set to True if variables are set correctly from local credentials form
            varFormSet = True
            logger.info('local credentials saved to REDIS for accessing host %s' % (host.hostname))

    except:
        # If no form submitted (not using local credentials), get SSH session
        # Don't go in if form was used (local credentials) but SSH session failed in above 'try' statement
        if not varFormSet:
            logger.info('credentials used of currently logged in user for accessing host %s' % (host.hostname))

    # Get any existing SSH sessions
    active_session = sshhandler.retrieve_ssh_session(host)
    result = host.pull_host_interfaces(active_session)

    if result:
        interfaces = host.count_interface_status(result)
        return render_template("/db/viewspecifichost.html",
                               host=host,
                               interfaces=interfaces,
                               result=result)
    else:
        # If interfaces is x.x.x.x skipped - connection timeout,
        #  throw error page redirect
        sshhandler.disconnect_specific_ssh_session(host)
        return redirect(url_for('no_host_connect_error',
                                host=host))


@app.route('/calldisconnectspecificsshsession/<x>')
def call_disconnect_specific_ssh_session(x):
    """Disconnect any SSH sessions for a specific host from all users.

    x = ID of host to disconnect.
    """
    host = datahandler.get_host_by_id(x)
    # Disconnect device.
    try:
        sshhandler.disconnect_specific_ssh_session(host)
    except:
        # Log error if unable to disconnect specific SSH session
        logger.info('unable to disconnect SSH session to provided host %s from user %s' % (host.hostname, session['USER']))
    return redirect(url_for('view_hosts'))


######################
# Confirmation pages #
######################


@app.route('/confirm/confirmintenable/<x>', methods=['GET', 'POST'])
def confirm_int_enable(x):
    """Confirm enabling specific device interface before executing.

    x = device id
    """
    try:
        host = datahandler.get_host_by_id(x)
        if host:
            # Removes dashes from interface in URL
            return render_template("confirm/confirmintenable.html",
                                   host=host,
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
        host = datahandler.get_host_by_id(x)
        if host:
            # Removes dashes from interface in URL
            return render_template("confirm/confirmintdisable.html",
                                   host=host,
                                   interface=request.args.get('int', ''))
        else:
            return redirect(url_for('index'))
    except AttributeError:
        return redirect(url_for('index'))


@app.route('/confirm/confirmhostdelete/<x>', methods=['GET', 'POST'])
def confirm_host_delete(x):
    """Confirm deleting device interface from local database.

    x = device ID
    """
    try:
        host = datahandler.get_host_by_id(x)
        if host:
            return render_template("confirm/confirmhostdelete.html", host=host)
        else:
            return redirect(url_for('index'))
    except AttributeError:
        return redirect(url_for('index'))


@app.route('/confirm/confirmintedit/', methods=['POST'])
def confirm_int_edit():
    """Confirm settings to edit device interface with before executing."""
    hostid = request.form['hostid']
    host = datahandler.get_host_by_id(hostid)
    hostinterface = request.form['hostinterface']
    datavlan = request.form['datavlan']
    voicevlan = request.form['voicevlan']
    other = request.form['other']
    otherEncoded = quote_plus(other, safe='/')

    return render_template("confirm/confirmintedit.html",
                           host=host,
                           hostinterface=hostinterface,
                           datavlan=datavlan,
                           voicevlan=voicevlan,
                           other=other,
                           otherEncoded=otherEncoded)


@app.route('/results/resultshostedit/', methods=['GET', 'POST'])
@app.route('/results/resultshostedit/<x>', methods=['GET', 'POST'])
def results_host_edit(x):
    """Confirm settings to edit host with in local database.

    x = original host ID
    """
    if 'modal' in x:
        return ('', 204)

    storedHost = datahandler.get_host_by_id(x)
    # Save all existing host variables, as the class stores get updated later in the function
    origHostname = storedHost.hostname
    origIpv4_addr = storedHost.ipv4_addr
    origHosttype = storedHost.type
    origIos_type = storedHost.ios_type
    origLocal_creds = storedHost.local_creds

    # Save form user inputs into new variables
    hostname = request.form['hostname']
    ipv4_addr = request.form['ipv4_addr']
    hosttype = request.form['hosttype']
    ios_type = request.form['ios_type']
    if request.form['local_creds'] == 'True':
        local_creds = True
        local_creds_updated = True
    elif request.form['local_creds'] == 'False':
        local_creds = False
        local_creds_updated = True
    else:
        local_creds = ''
        local_creds_updated = False

    # If exists, disconnect any existing SSH sessions
    #  and clear them from the SSH dict
    try:
        sshhandler.disconnect_specific_ssh_session(storedHost)
        logger.info('disconnected and cleared saved SSH session information for edited host %s' % (storedHost.hostname))
    except (socket.error, EOFError):
        logger.info('no existing SSH sessions for edited host %s' % (storedHost.hostname))
    except:
        logger.info('could not clear SSH session for edited host %s' % (storedHost.hostname))

    result = datahandler.edit_host_in_database(storedHost.id, hostname, ipv4_addr, hosttype, ios_type, local_creds, local_creds_updated)

    if result:
        logger.info('edited host %s in database' % (storedHost.hostname))
        return render_template("results/resultshostedit.html",
                               title='Edit host confirm',
                               storedHost=storedHost,
                               hostname=hostname,
                               ipv4_addr=ipv4_addr,
                               hosttype=hosttype,
                               ios_type=ios_type,
                               local_creds=local_creds,
                               local_creds_updated=local_creds_updated,
                               origHostname=origHostname,
                               origIpv4_addr=origIpv4_addr,
                               origHosttype=origHosttype,
                               origIos_type=origIos_type,
                               origLocal_creds=origLocal_creds)
    else:
        return redirect(url_for('confirmHostEdit',
                                x=storedHost))


@app.route('/confirm/confirmcmdcustom/', methods=['GET', 'POST'])
def confirm_cmd_custom():
    """Confirm bulk command entry before executing."""
    session['HOSTNAME'] = request.form['hostname']
    session['COMMAND'] = request.form['command']
    session['HOSTID'] = request.form['hostid']

    return render_template("confirm/confirmcmdcustom.html")


@app.route('/confirm/confirmcfgcmdcustom/', methods=['GET', 'POST'])
def confirm_cfg_cmd_custom():
    """Confirm bulk configuration command entry before executing."""
    host = datahandler.get_host_by_id(request.form['hostid'])
    session['HOSTNAME'] = request.form['hostname']
    session['COMMAND'] = request.form['command']
    session['HOSTID'] = request.form['hostid']
    session['IOS_TYPE'] = host.ios_type

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

    host = datahandler.get_host_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(host)

    # Removes dashes from interface in URL and enabel interface
    result = host.run_enable_interface_cmd(interface_replace_slash(y), active_session)

    logger.info('enabled interface %s on host %s' % (y, host.hostname))
    return render_template("results/resultsinterfaceenabled.html",
                           host=host, interface=y, result=result)


@app.route('/results/resultsinterfacedisabled/<x>/<y>', methods=['GET', 'POST'])
def results_int_disabled(x, y):
    """Display results for disabling specific interface.

    x = device id
    y = interface name
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(host)

    # Removes dashes from interface in URL and disable interface
    result = host.run_disable_interface_cmd(interface_replace_slash(y), active_session)

    logger.info('disabled interface %s on host %s' % (y, host.hostname))
    return render_template("results/resultsinterfacedisabled.html",
                           host=host, interface=y, result=result)


@app.route('/results/resultsinterfaceedit/<x>/<datavlan>/<voicevlan>/<other>', methods=['GET', 'POST'])
def results_int_edit(x, datavlan, voicevlan, other):
    """Display results for editing specific interface config settings.

    x = device id
    d = data vlan
    v = voice vlan
    o = other
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(host)

    # Get interface from passed variable in URL
    hostinterface = request.args.get('int', '')

    # Decode 'other' string
    other = unquote_plus(other).decode('utf-8')

    # Replace '___' with '/'
    other = other.replace('___', '/')

    # Replace '\r\n' with '\n'
    other = other.replace('\r\n', '\n')

    # Remove dashes from interface in URL and edit interface config
    result = host.run_edit_interface_cmd(hostinterface, datavlan, voicevlan, other, active_session)

    logger.info('edited interface %s on host %s' % (hostinterface, host.hostname))
    return render_template("results/resultsinterfaceedit.html", host=host,
                           interface=hostinterface, datavlan=datavlan,
                           voicevlan=voicevlan, other=other, result=result)


@app.route('/results/resultshostdeleted/<x>', methods=['GET', 'POST'])
def results_host_deleted(x):
    """Display results for deleting device from local database.

    x = device ID
    """
    host = datahandler.get_host_by_id(x)
    if host:
        # Removes host from database
        result = datahandler.delete_host_in_db(host.id)
        if result:
            sshhandler.disconnect_specific_ssh_session(host)
            return render_template("results/resultshostdeleted.html",
                                   host=host, result=result)
        else:
            return redirect(url_for('confirm_host_delete', x=host.id))
    else:
        return redirect(url_for('index'))


@app.route('/results/resultscmdcustom/', methods=['GET', 'POST'])
def results_cmd_custom():
    """Display results from bulk command execution on device."""
    initial_checks()

    host = datahandler.get_host_by_id(session['HOSTID'])

    active_session = sshhandler.retrieve_ssh_session(host)

    command = session['COMMAND']

    result = host.run_multiple_commands(command, active_session)

    session.pop('HOSTNAME', None)
    session.pop('COMMAND', None)
    session.pop('HOSTID', None)

    logger.info('ran custom commands on host %s' % (host.hostname))
    return render_template("results/resultscmdcustom.html",
                           host=host,
                           command=command,
                           result=result)


@app.route('/results/resultscfgcmdcustom/', methods=['GET', 'POST'])
def results_cfg_cmd_custom():
    """Display results from bulk configuration command execution on device."""
    initial_checks()

    host = datahandler.get_host_by_id(session['HOSTID'])

    active_session = sshhandler.retrieve_ssh_session(host)

    command = session['COMMAND']

    result = host.run_multiple_config_commands(command, active_session)

    session.pop('HOSTNAME', None)
    session.pop('COMMAND', None)
    session.pop('HOSTID', None)
    session.pop('IOS_TYPE', None)

    logger.info('ran custom config commands on host %s' % (host.hostname))
    return render_template("results/resultscfgcmdcustom.html",
                           host=host,
                           command=command,
                           result=result)


###############
# Modal pages #
###############


@app.route('/modalinterface/', methods=['GET', 'POST'])
@app.route('/modalinterface/<x>/<y>', methods=['GET', 'POST'])
def modal_specific_interface_on_host(x, y):
    """Show specific interface details from device.

    x = device id
    y = interface name
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(host)

    # Removes dashes from interface in URL, replacing '_' with '/'
    interface = interface_replace_slash(y)
    # Replace's '=' with '.'
    host.interface = interface.replace('=', '.')

    int_config, int_mac_addr, int_stats = host.pull_interface_info(active_session)
    mac_to_ip = ''

    logger.info('viewed interface %s on host %s' % (host.interface, host.hostname))
    return render_template("/viewspecificinterfaceonhost.html",
                           host=host,
                           interface=interface,
                           int_config=int_config,
                           intMacAddr=int_mac_addr,
                           macToIP=mac_to_ip,
                           intStats=int_stats)


@app.route('/modaleditinterface/<x>', methods=['GET', 'POST'])
def modal_edit_interface_on_host(x):
    """Display modal to edit specific interface on device.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    active_session = sshhandler.retrieve_ssh_session(host)

    # Removes dashes from interface in URL
    # interface = interface_replace_slash(y)
    # Replace's '=' with '.'
    # host.interface = interface.replace('=', '.')

    # Set interface to passed parameter in URL
    host.interface = request.args.get('int', '')

    int_config = host.pull_interface_config(active_session)
    # Edit form
    form = EditInterfaceForm(request.values, host=host, interface=host.interface)

    if form.validate_on_submit():
        flash('Interface to edit - "%s"' % (host.interface))
        return redirect('/confirm/confirmintedit')

    return render_template("/editinterface.html",
                           hostid=host.id,
                           hostinterface=host.interface,
                           int_config=int_config,
                           form=form)


@app.route('/modallocalcredentials/<x>', methods=['GET', 'POST'])
def modal_local_credentials(x):
    """Get local credentials from user.

    x is host ID
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    if sshhandler.check_host_active_ssh_session(host):
        return redirect('/db/viewhosts/%s' % (host.id))

    form = LocalCredentialsForm()
    logger.info('saved local credentials for host %s' % (host.hostname))
    return render_template('localcredentials.html',
                           title='Login with local SSH credentials',
                           form=form,
                           host=host)


@app.route('/modalcmdshowrunconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdshowrunconfig/<x>', methods=['GET', 'POST'])
def modal_cmd_show_run_config(x):
    """Display modal with active/running configuration settings on device.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    host_config = host.pull_run_config(active_session)
    logger.info('viewed running-config via button on host %s' % (host.hostname))
    return render_template("/cmdshowrunconfig.html",
                           host=host,
                           host_config=host_config)


@app.route('/modalcmdshowstartconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdshowstartconfig/<x>', methods=['GET', 'POST'])
def modal_cmd_show_start_config(x):
    """Display modal with saved/stored configuration settings on device.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    host_config = host.pull_start_config(active_session)
    logger.info('viewed startup-config via button on host %s' % (host.hostname))
    return render_template("/cmdshowstartconfig.html",
                           host=host,
                           host_config=host_config)


@app.route('/modalcmdshowcdpneigh/', methods=['GET', 'POST'])
@app.route('/modalcmdshowcdpneigh/<x>', methods=['GET', 'POST'])
def modal_cmd_show_cdp_neigh(x):
    """Display modal with CDP/LLDP neighbors info for device.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    neigh = host.pull_cdp_neighbor(active_session)
    logger.info('viewed CDP neighbors via button on host %s' % (host.hostname))
    return render_template("/cmdshowcdpneigh.html",
                           host=host,
                           neigh=neigh)


@app.route('/modalcmdshowinventory/', methods=['GET', 'POST'])
@app.route('/modalcmdshowinventory/<x>', methods=['GET', 'POST'])
def modal_cmd_show_inventory(x):
    """Display modal with device inventory information.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    result = host.pull_inventory(active_session)

    logger.info('viewed inventory info via button on host %s' % (host.hostname))
    return render_template("/cmdshowinventory.html",
                           host=host,
                           result=result)


@app.route('/modalcmdshowversion/', methods=['GET', 'POST'])
@app.route('/modalcmdshowversion/<x>', methods=['GET', 'POST'])
def modal_cmd_show_version(x):
    """Display modal with device version information.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    result = host.pull_version(active_session)

    logger.info('viewed version info via button on host %s' % (host.hostname))
    return render_template("/cmdshowversion.html",
                           host=host,
                           result=result)


@app.route('/modalcmdcustom/<x>', methods=['GET', 'POST'])
def modal_cmd_custom(x):
    """Display modal to retrieve custom bulk commands to execute.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    # Custom Commands form
    form = CustomCommandsForm(request.values, hostname=host.hostname)

    return render_template("/cmdcustom.html",
                           host=host,
                           form=form)


@app.route('/modalcfgcmdcustom/<x>', methods=['GET', 'POST'])
def modal_cfg_cmd_custom(x):
    """Display modal to retrieve custom bulk config commands to execute.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    # Custom Commands form
    form = CustomCfgCommandsForm(request.values, hostname=host.hostname)

    return render_template("/cfgcmdcustom.html",
                           host=host,
                           form=form)


@app.route('/modalcmdsaveconfig/<x>', methods=['GET', 'POST'])
def modal_cmd_save_config(x):
    """Save device configuration to memory and display result in modal.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    host.save_config_on_device(active_session)

    logger.info('saved config via button on host %s' % (host.hostname))
    return render_template("/cmdsaveconfig.html",
                           host=host)


@app.route('/db/viewhosts/hostshell/<x>', methods=['GET', 'POST'])
def host_shell(x):
    """Display iShell input fields.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)

    # Exit config mode if currently in it on page refresh/load
    exit_config_mode(host.id)

    logger.info('accessed interactive shell on host %s' % (host.hostname))
    return render_template("hostshell.html",
                           host=host)


@app.route('/hostshelloutput/<x>/<m>/<y>', methods=['GET', 'POST'])
def host_shell_output(x, m, y):
    """Display iShell output fields.

    x = device id
    m = config or enable mode
    y = encoded commands from javascript
    """
    initial_checks()

    config_error = False

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)

    # Replace '___' with '/'
    x = unquote_plus(y).decode('utf-8')
    command = x.replace('___', '/')
    # command = interface_replace_slash(unquote_plus(y).decode('utf-8'))

    # Append prompt and command executed to beginning of output
    # output.append(host.find_prompt_in_session(active_session) + command)

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
            output = host.get_cmd_output(command, active_session)

    logger.info('ran command on host %s - %s' % (host.hostname, command))

    return render_template("hostshelloutput.html",
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

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    # Enter configuration mode on device using existing SSH session
    active_session.config_mode()
    logger.info('entered config mode via iShell on host %s' % (host.hostname))
    return ('', 204)


@app.route('/exitconfigmode/<x>', methods=['GET', 'POST'])
def exit_config_mode(x):
    """Exit device configuration mode.

    x = device id
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)
    # Exit configuration mode on device using existing SSH session
    active_session.exit_config_mode()

    logger.info('exited config mode via iShell on host %s' % (host.hostname))
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
    host = datahandler.get_host_by_id(x)
    return render_template("confirm/confirmmultipleintenable.html",
                           host=host,
                           interfaces=y)


@app.route('/confirm/confirmmultipleintdisable/<x>/<y>', methods=['GET', 'POST'])
def confirm_multi_int_disable(x, y):
    """Confirm disabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    host = datahandler.get_host_by_id(x)
    return render_template("confirm/confirmmultipleintdisable.html",
                           host=host,
                           interfaces=y)


@app.route('/confirm/confirmmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def confirm_multi_int_edit(x, y):
    """Confirm editing multiple device interfaces.  WIP.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    host = datahandler.get_host_by_id(x)
    return render_template("confirm/confirmmultipleintedit.html",
                           host=host,
                           interfaces=y)


@app.route('/results/resultsmultipleintenabled/<x>/<y>', methods=['GET', 'POST'])
def results_multi_int_enabled(x, y):
    """Display results from enabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
        # a = interface
        if a:
            # Removes dashes from interface in URL
            a = interface_replace_slash(a)
            result.append(host.run_enable_interface_cmd(a, active_session))

    logger.info('enabled multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintenabled.html",
                           host=host,
                           interfaces=y,
                           result=result)


@app.route('/results/resultsmultipleintdisabled/<x>/<y>', methods=['GET', 'POST'])
def results_multi_int_disabled(x, y):
    """Display results from disabling multiple device interfaces.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
        if a:
            # Removes dashes from interface in URL
            a = interface_replace_slash(a)
            result.append(host.run_disable_interface_cmd(a, active_session))

    logger.info('disabled multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintdisabled.html",
                           host=host,
                           interfaces=y,
                           result=result)


@app.route('/results/resultsmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def results_multi_int_edit(x, y):
    """Display results from editing multiple device interfaces.  WIP.

    x = device id
    y = interfaces separated by '&' in front of each interface name
    """
    initial_checks()

    host = datahandler.get_host_by_id(x)
    active_session = sshhandler.retrieve_ssh_session(host)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
        if a:
            # Removes dashes from interface in URL
            a = interface_replace_slash(a)

    result.append(host.save_config_on_device(active_session))

    logger.info('edited multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintedit.html",
                           host=host,
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
            return render_template('/editsettings.html',
                                   title='Edit Netconfig settings',
                                   file=s.readlines())
    except:
        return render_template('errors/500.html', error="Unable to read Settings File"), 500


@app.route('/proxysettings', methods=['GET'])
def proxy_settings():
    """Modify proxy settings."""
    initial_checks()

    form = ProxySettingsForm()
    return render_template('/proxysettings.html',
                           title='Edit Proxy Settings',
                           form=form)


@app.route('/results/resultseditproxy', methods=['GET', 'POST'])
def results_edit_proxy():
    """Save proxy details to database."""
    # Need to make results page and datahandler.add_proxy_to_db function
    initial_checks()
    proxy_name = request.form['proxy_name']
    proxy_settings = request.form['proxy_settings']

    response, hostid, e = datahandler.add_proxy_to_db(proxy_name, proxy_settings)
    if response:
        return render_template("/results/resultseditproxy.html",
                               title='Edit proxy settings result',
                               proxy_name=proxy_name,
                               proxy_settings=proxy_settings,
                               hostid=hostid)
    else:
        logger.info('exception thrown when adding/editing proxy settings to database: %s' % e)
        # TO-DO Add popup error message here
        return redirect(url_for('proxy_settings'))

from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, jsonify, g
from app import app
import functools #http://flask.pocoo.org/snippets/120/
from .forms import LoginForm, GetConfigForm, GetInterfaceConfigForm, AddHostForm, ImportHostsForm, EditHostForm, DeleteHostsForm, EditInterfaceForm, CustomCommandsForm, CustomCfgCommandsForm#, FWACLGeneratorForm, FWCheckOpenPortsForm
from scripts_bank import config_interface as ci
from scripts_bank import pull_host_interfaces as phi
from scripts_bank.run_command import getCmdOutput, getCfgCmdOutput, getCmdOutputWithCommas, getMultiCmdOutput, getMultiConfigCmdOutput, saveConfigOnSession, enterConfigModeInSession, exitConfigModeInSession, getCmdOutputNoCR, getCfgCmdOutputNoCR
from scripts_bank import ping_hosts as ph
from scripts_bank.lib import functions as fn
from scripts_bank.lib.fw_functions import checkAccessThroughACL, getSourceInterfaceForHost
from scripts_bank import db_modifyDatabase
#from scripts_bank import firewall_open_ports as fop
from scripts_bank.lib.flask_functions import checkUserLoggedInStatus, checkSSHSessionMatchesID
from scripts_bank.lib.netmiko_functions import getSSHSession, disconnectFromSSH, sessionIsAlive
from datetime import timedelta
from urllib import unquote_plus
import logging
from scripts_bank import netboxAPI
from redis import StrictRedis # http://blog.hackerearth.com/twitter-client-using-flask-redis
from uuid import uuid4
from device_classes.device_definitions.base_device import BaseDevice

# Gets page referrer
# referrer = request.headers.get("Referer")

# Global Variables #
ssh = {}

###################
# Logging - Begin #
# Plan to remove this logging section, and use it's relocated function in functions.py #
###################

# Syslogging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create a file handler
handler = logging.FileHandler(app.config['SYSLOGFILE'])
handler.setLevel(logging.INFO)
# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(handler)

def writeToLog(msg):
    # Local access.log
    #newmsg = str(fn.getCurrentTime()) + ' - ' + session['USER'] + ' - ' + msg + '\n'
    #fn.appendCommandToFile(newmsg, app.config['LOGFILE]')
    # Try/catch in case User isn't logged in, and Netconfig URL is access directly
    try:
      # Syslog file
      logger.info(session['USER'] + ' - ' + msg)
    except:
      return render_template("index.html",
                              title='Home')

###################
# Logging - End #
###################

def resetUserRedisExpireTimer():
    # x is Redis key to reset timer on
    # Reset Redis user key exipiration, as we only want to to expire after inactivity, not from initial login
    try:
      user_id = str(g.db.hget('users', session['USER']))
      g.db.expire(user_id, app.config['REDISKEYTIMEOUT'])
    except:
      pass

def initialChecks():
    # x is host.id
    resetUserRedisExpireTimer()
    if not checkUserLoggedInStatus():
      return render_template("index.html",
                              title='Home')

# Returns active SSH session for provided host if it exists.  Otherwise gets a session, stores it, and returns it
def retrieveSSHSession(host):
    global ssh

    user_id = str(g.db.hget('users', session['USER']))
    password = str(g.db.hget(str(user_id), 'pw'))
    creds = fn.setUserCredentials(session['USER'], password)
    # Store SSH Dict key as host.id followed by '-' followed by username
    sshKey = str(host.id) + '--' + str(session['UUID'])
    #if not ssh[sshKey]:
    if sshKey not in ssh:
      writeToLog('initiated new SSH connection to %s' % (host.hostname))
      # If no currently active SSH sessions, initiate a new one
      ssh[sshKey] = getSSHSession(host.ios_type, host.ipv4_addr, creds)
    
    # Run test to verify if socket connection is still open or not
    if not sessionIsAlive(ssh[sshKey]):
      # If session is closed, reestablish session and log event
      writeToLog('reestablished SSH connection to %s' % (host.hostname))
      ssh[sshKey] = getSSHSession(host.ios_type, host.ipv4_addr, creds)

    return ssh[sshKey]

# Disconnect any SSH sessions for a specific host from all users
def disconnectSpecificSSHSession(host):
    global ssh

    for x in ssh:
      # x is id-uuid
      y = x.split('--')
      # y[0] is host id, y[1] is uuid
      if int(y[0]) == int(host.id):
        disconnectFromSSH(ssh[x])
        ssh = fn.removeDictKey(ssh, x)
        writeToLog('disconnected SSH session to provided host %s from user %s' % (host.hostname, session['USER']))

# Disconnect all remaining active SSH sessions tied to a user
def disconnectAllSSHSessions():
    global ssh

    for x in ssh:
      # x is id-uuid
      y = x.split('--')
      # y[0] is host id, y[1] is uuid
      if str(y[1]) == str(session['UUID']):
        disconnectFromSSH(ssh[x])
        host = db_modifyDatabase.getHostByID(y[0])
        ssh = fn.removeDictKey(ssh, x)
        writeToLog('disconnected SSH session to device %s for user %s' % (host.hostname, y[1]))
    
    writeToLog('disconnected all SSH sessions for user %s' % (session['USER']))

# Returns number of active SSH sessions tied to user
def countAllSSHSessions():
    global ssh

    i = 0
    for x in ssh:
      # x is id-uuid
      y = x.split('--')
      # y[0] is host id, y[1] is uuid
      if str(y[1]) == str(session['UUID']):
        # Increment counter
        i += 1

    return i

def interfaceReplaceSlash(x):
    x = x.replace('_','/')
    return x

###############################
# Login Creds Timeout - Begin #
###############################

def init_db():
    db = StrictRedis(
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        db=app.config['DB_NO'])
    return db

# Automatically logs user out of session after x minutes set in settings.py via SESSIONTIMEOUT
@app.before_request
def before_request():
    g.db = init_db()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=app.config['SESSIONTIMEOUT'])
    session.modified = True

#############################
# Login Creds Timeout - End #
#############################

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html',
                           error=error)

@app.errorhandler(500)
def handle_500(error):
    return render_template('errors/500.html',
                            error=error)

@app.route('/nohostconnect/<host>')
@app.route('/errors/nohostconnect/<host>')
def noHostConnectError(host):
    return render_template('errors/nohostconnect.html',
                           host=host)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'USER' in session:
        return redirect(url_for('viewHosts'))
    else:
        try:
            user = request.form['user']
            pw = request.form['pw']
            # If user id doesn't exist, create new one with next available unique user id
            # Else reuse existing key, to prevent incrementing id each time the same user logs in
            if str(g.db.hget('users', user)) == 'None':
                # Create new user id, incrementing by 10
                user_id = str(g.db.incrby('next_user_id', 10))
            else:
                user_id = str(g.db.hget('users', user))
            g.db.hmset(user_id, dict(user=user, pw=pw))
            g.db.hset('users', user, user_id)
            # Set user info timer to auto expire and clear data
            g.db.expire(user_id, app.config['REDISKEYTIMEOUT'])
            session['USER'] = user
            # Generate unique session id for user, tie to each individual SSH session later
            session['UUID'] = uuid4()
            writeToLog('logged in')
            return redirect(url_for('viewHosts'))
        except:
            return render_template("index.html",
                                   title='Home')

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for('index'))
    return render_template('login.html',
                           title='Login with SSH credentials',
                           form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Disconnect all SSH sessions by user
    disconnectAllSSHSessions()
    writeToLog('logged out')

    # Delete user saved in Redis
    user_id = str(g.db.hget('users', session['USER']))
    g.db.delete(str(user_id))
    # Remove the username from the session if it is there
    session.pop('USER', None)
    return redirect(url_for('index'))

@app.route('/disconnectAllSSH')
def disconnectAllSSH():
    disconnectAllSSHSessions()
    writeToLog('disconnected all active SSH sessions')
    #referrer = request.headers.get("Referer")
    #return redirect(referrer)   <---We don't do this because we don't want to reload a host SSH connection on its page if we're disconnecting SSH connections
    return redirect(url_for('index'))

@app.route('/getsshsessionscount')
def getSSHSessionsCount():
    # x = host id
    initialChecks()
    count = countAllSSHSessions()
    return jsonify(count)

@app.route('/db/addhosts', methods=['GET', 'POST'])
def addHosts():
    initialChecks()
    form = AddHostForm()
    if form.validate_on_submit():
        return redirect(url_for('addHostConfirm'))
    return render_template('/db/addhosts.html',
                           title='Add hosts to database',
                           form=form)

@app.route('/db/addhostconfirm', methods=['GET', 'POST'])
def addHostConfirm():
    initialChecks()
    hostname = request.form['hostname']
    ipv4_addr = request.form['ipv4_addr']
    hosttype = request.form['hosttype']
    ios_type = request.form['ios_type']
    response, hostid = db_modifyDatabase.addHostToDB(hostname, ipv4_addr, hosttype, ios_type)
    if response:
        writeToLog('added host %s to database' % (hostname))
        return render_template("/db/addhostconfirm.html",
                               title='Add host result',
                               hostname=hostname,
                               ipv4_addr=ipv4_addr,
                               hosttype=hosttype,
                               ios_type=ios_type,
                               hostid=hostid)
    else:
        return redirect(url_for('addHosts'))

@app.route('/db/importhosts', methods=['GET', 'POST'])
def importHosts():
    initialChecks()
    form = ImportHostsForm()
    if form.validate_on_submit():
        return redirect(url_for('resultImportHosts'))
    return render_template('/db/importhosts.html',
                           title='Import hosts to database via CSV',
                           form=form)

@app.route('/db/importhostsconfirm', methods=['GET', 'POST'])
def importHostsConfirm():
    initialChecks()
    csvImport = request.form['csvimport']
    response, message = db_modifyDatabase.importHostsToDB(csvImport)
    writeToLog('imported hosts to database')
    return render_template("/db/importhostsconfirm.html",
                           title='Import devices result',
                           response=response,
                           message=message)

@app.route('/edithost/<x>', methods=['GET'])
def editHost(x):
    # x is host ID
    host = db_modifyDatabase.getHostByID(x)
    form = EditHostForm()
    if form.validate_on_submit():
        return redirect('/confirm/confirmhostedit')
    return render_template('/edithost.html',
                           title='Edit host in database',
                           id=x,
                           originalHost=host.hostname,
                           form=form)

# Shows all hosts in database
@app.route('/db/viewhosts', methods=['GET', 'POST'])
@app.route('/db/viewhosts/', methods=['GET', 'POST'])
def viewHosts(page=1):
    writeToLog('viewed all hosts')
    if app.config['DATALOCATION'] == 'local':
      hosts = db_modifyDatabase.getHosts(page)
      status = ph.reachable(hosts)
      return render_template('/db/viewhosts.html',
                             title='View hosts pulled from database',
                             hosts=hosts,
                             status=status)
    elif app.config['DATALOCATION'] == 'netbox':
      hosts = netboxAPI.getHosts()
      return render_template('/dcimnetbox.html',
                             title='View hosts in database',
                             hosts=hosts)
    else:
      return render_template('errors/datalocation_error.html',
                              DATALOCATION=app.config['DATALOCATION'])

@app.route('/deviceuptime/<x>')
def deviceUptime(x):
    # x = host id
    initialChecks()
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    return jsonify(host.pull_device_uptime(activeSession))

# To show hosts from database
@app.route('/db/viewhosts/<x>', methods=['GET'])
#@app.route('/db/viewhosts/<x>/<int:page>', methods=['GET', 'POST'])
def viewSpecificHost(x):
    # x is host.id
    initialChecks()

    # This fixes page refresh issue when clicking on a Modal that breaks DataTables
    if 'modal' in x:
      # Return empty response, as the page is loaded from the Modal JS
      # However this breaks the Loading modal JS function.  Unsure why, need to research
      return ('', 204)

    host = db_modifyDatabase.getHostByID(x)

    writeToLog('accessed host %s using IPv4 address %s' % (host.hostname, host.ipv4_addr))

    # Get any existing SSH sessions
    activeSession = retrieveSSHSession(host)

    interfaces = host.pull_host_interfaces(activeSession)
    
    if interfaces:
      upInt, downInt, disabledInt, totalInt = host.count_interface_status(interfaces)

    # if interfaces is x.x.x.x skipped - connection timeout, throw error page redirect
    if fn.containsSkipped(interfaces) or not interfaces:
        disconnectSpecificSSHSession(host)
        return redirect(url_for('noHostConnectError',
                                host=host.hostname))
    else:
        return render_template("/db/viewspecifichost.html",
                                host=host,
                                interfaces=interfaces,
                                upInt=upInt,
                                downInt=downInt,
                                disabledInt=disabledInt,
                                totalInt=totalInt)
    
######################
# Confirmation pages #
######################

@app.route('/confirm/confirmintenable/', methods=['GET', 'POST'])
@app.route('/confirm/confirmintenable/<x>/<y>', methods=['GET', 'POST'])
def confirmIntEnable(x, y):
    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)
    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    return render_template("confirm/confirmintenable.html",
                           host=host,
                           interface=y)

@app.route('/confirm/confirmintdisable/', methods=['GET', 'POST'])
@app.route('/confirm/confirmintdisable/<x>/<y>', methods=['GET', 'POST'])
def confirmIntDisable(x, y):
    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)
    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    return render_template("confirm/confirmintdisable.html",
                           host=host,
                           interface=y)

@app.route('/confirm/confirmhostdelete/', methods=['GET', 'POST'])
@app.route('/confirm/confirmhostdelete/<x>', methods=['GET', 'POST'])
def confirmHostDelete(x):
    # x = device ID
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmhostdelete.html",
                           host=host)

@app.route('/confirm/confirmintedit/', methods=['POST'])
@app.route('/confirm/confirmintedit/<x>/<y>', methods=['POST'])
def confirmIntEdit():
    hostid = request.form['hostid']
    host = db_modifyDatabase.getHostByID(hostid)
    #host = request.form['host']
    interface = request.form['interface']
    datavlan = request.form['datavlan']
    voicevlan = request.form['voicevlan']
    other = request.form['other']

    return render_template("confirm/confirmintedit.html",
                           host=host,
                           interface=interface,
                           datavlan=datavlan,
                           voicevlan=voicevlan,
                           other=other)

@app.route('/confirm/confirmhostedit/', methods=['GET', 'POST'])
@app.route('/confirm/confirmhostedit/<x>', methods=['GET', 'POST'])
def confirmHostEdit(x):
    # x = original host ID
    originalHost = db_modifyDatabase.getHostByID(x)
    hostname = request.form['hostname']
    ipv4_addr = request.form['ipv4_addr']
    hosttype = request.form['hosttype']
    ios_type = request.form['ios_type']

    # If exists, disconnect any existing SSH sessions and clear them from the SSH dict
    try:
      disconnectSpecificSSHSession(originalHost)
      writeToLog('disconnected and cleared saved SSH session information for edited host %s' % (originalHost.hostname))
    except (socket.error, EOFError):
      writeToLog('no existing SSH sessions for edited host %s' % (originalHost.hostname))
    except:
      writeToLog('could not clear SSH session for edited host %s' % (originalHost.hostname))

    result = db_modifyDatabase.editHostInDatabase(originalHost.id, hostname, ipv4_addr, hosttype, ios_type)

    if result:
      updatedHost = db_modifyDatabase.getHostByID(x)
      writeToLog('edited host %s in database' % (originalHost.hostname))
      return render_template("confirm/confirmhostedit.html",
                             title='Edit host confirm',
                             originalHost=originalHost,
                             updatedHost=updatedHost,
                             hostname=hostname,
                             ipv4_addr=ipv4_addr,
                             hosttype=hosttype,
                             ios_type=ios_type)
    else:
        return redirect(url_for('confirmHostEdit',
                                x=originalHost))

@app.route('/confirm/confirmcmdcustom/', methods=['GET', 'POST'])
def confirmCmdCustom():
    session['HOSTNAME'] = request.form['hostname']
    session['COMMAND'] = request.form['command']
    session['HOSTID'] = request.form['hostid']

    return render_template("confirm/confirmcmdcustom.html")

@app.route('/confirm/confirmcfgcmdcustom/', methods=['GET', 'POST'])
def confirmCfgCmdCustom():
    host = db_modifyDatabase.getHostByID(request.form['hostid'])
    session['HOSTNAME'] = request.form['hostname']
    session['COMMAND'] = request.form['command']
    session['HOSTID'] = request.form['hostid']
    session['IOS_TYPE'] = host.ios_type

    return render_template("confirm/confirmcfgcmdcustom.html")

#################
# Results pages #
#################

@app.route('/results/resultsinterfaceenabled/', methods=['GET', 'POST'])
@app.route('/results/resultsinterfaceenabled/<x>/<y>', methods=['GET', 'POST'])
def resultsIntEnabled(x, y):
    initialChecks()
    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    #sshVar = retrieveSSHSession(host)
    # THIS LINE ONLY WORKS IF ABOVE LINE IS EXECUTED FIRST??? #bbbbb
    #result = ci.enableInterface(host.activeSession, interfaceReplaceSlash(y))
    #time.sleep(1) # Also works if I delay by 1 second ?????
    # Removes dashes from interface in URL and enabel interface
    result = host.run_enable_interface_cmd(interfaceReplaceSlash(y), activeSession)

    writeToLog('enabled interface %s on host %s' % (y, host.hostname))
    return render_template("results/resultsinterfaceenabled.html",
                           host=host,
                           interface=y,
                           result=result)

@app.route('/results/resultsinterfacedisabled/', methods=['GET', 'POST'])
@app.route('/results/resultsinterfacedisabled/<x>/<y>', methods=['GET', 'POST'])
def resultsIntDisabled(x, y):
    initialChecks()
    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Removes dashes from interface in URL and disable interface
    result = host.run_disable_interface_cmd(interfaceReplaceSlash(y), activeSession)

    writeToLog('disabled interface %s on host %s' % (y, host.hostname))
    return render_template("results/resultsinterfacedisabled.html",
                           host=host,
                           interface=y,
                           result=result)

@app.route('/results/resultsinterfaceedit/', methods=['GET', 'POST'])
@app.route('/results/resultsinterfaceedit/<x>/<y>/<datavlan>/<voicevlan>/<other>', methods=['GET', 'POST'])
def resultsIntEdit(x, y, datavlan, voicevlan, other):
    initialChecks()
    # x = device id, y = interface name, d = data vlan, v = voice vlan, o = other
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Remove dashes from interface in URL and edit interface config
    result = host.run_edit_interface_cmd(interfaceReplaceSlash(y), datavlan, voicevlan, other, activeSession)

    writeToLog('edited interface %s on host %s' % (y, host.hostname))
    return render_template("results/resultsinterfaceedit.html",
                           host=host,
                           interface=y,
                           datavlan=datavlan,
                           voicevlan=voicevlan,
                           other=other,
                           result=result)

@app.route('/results/resultshostdeleted/', methods=['GET', 'POST'])
@app.route('/results/resultshostdeleted/<x>', methods=['GET', 'POST'])
def resultsHostDeleted(x):
    # x = device ID
    host = db_modifyDatabase.getHostByID(x)
    # Removes host from database
    result = db_modifyDatabase.deleteHostInDB(host.id)
    if result:
        disconnectSpecificSSHSession(host)
        writeToLog('deleted host %s in database' % (host.hostname))
        return render_template("results/resultshostdeleted.html",
                               host=host,
                               result=result)
    else:
        return redirect(url_for('confirmHostDelete',
                                x=host.id))

@app.route('/results/resultscmdcustom/', methods=['GET', 'POST'])
def resultsCmdCustom():
    initialChecks()
    host = db_modifyDatabase.getHostByID(session['HOSTID'])

    activeSession = retrieveSSHSession(host)

    command = session['COMMAND']

    result = host.run_multiple_commands(command, activeSession)

    session.pop('HOSTNAME', None)
    session.pop('COMMAND', None)
    session.pop('HOSTID', None)

    writeToLog('ran custom commands on host %s' % (host.hostname))
    return render_template("results/resultscmdcustom.html",
                           host=host,
                           command=command,
                           result=result)

@app.route('/results/resultscfgcmdcustom/', methods=['GET', 'POST'])
def resultsCfgCmdCustom():
    initialChecks()
    host = db_modifyDatabase.getHostByID(session['HOSTID'])

    activeSession = retrieveSSHSession(host)

    command = session['COMMAND']

    result = host.run_multiple_config_commands(command, activeSession)

    session.pop('HOSTNAME', None)
    session.pop('COMMAND', None)
    session.pop('HOSTID', None)
    session.pop('IOS_TYPE', None)

    writeToLog('ran custom config commands on host %s' % (host.hostname))
    return render_template("results/resultscfgcmdcustom.html",
                           host=host,
                           command=command,
                           result=result)
        
###############
# Modal pages #
###############

# To show interface commands from host device
@app.route('/modalinterface/', methods=['GET', 'POST'])
@app.route('/modalinterface/<x>/<y>', methods=['GET', 'POST'])
def modalSpecificInterfaceOnHost(x, y):
    initialChecks()
    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Removes dashes from interface in URL, replacing '_' with '/'
    interface = interfaceReplaceSlash(y)
    # Replace's '_' with '.'
    host.interface = interface.replace('=', '.')

    intConfig, intMac, intStats = host.pull_interface_info(activeSession)
    macToIP = ''
    writeToLog('viewed interface %s on host %s' % (interface, host.hostname))
    return render_template("/viewspecificinterfaceonhost.html",
                           host=host,
                           interface=interface,
                           intConfig=intConfig,
                           intMac=intMac,
                           macToIP=macToIP,
                           intStats=intStats)


# To show interface commands from host device
@app.route('/modaleditinterface/', methods=['GET', 'POST'])
@app.route('/modaleditinterface/<x>/<y>', methods=['GET', 'POST'])
def modalEditInterfaceOnHost(x, y): #ddddd
    initialChecks()

    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Removes dashes from interface in URL
    interface = interfaceReplaceSlash(y)

    intConfig = phi.pullInterfaceConfigSession(activeSession, interface, host)
    # Edit form
    form = EditInterfaceForm(request.values, host=host, interface=interface)

    if form.validate_on_submit():
        flash('Interface to edit="%s"' % (interface))
        return redirect('/confirm/confirmintedit')

    return render_template("/editinterface.html",
                           hostid=host.id,
                           interface=interface,
                           intConfig=intConfig,
                           form=form)

# To show interface commands from host device
@app.route('/modalinterfaceinfo/', methods=['GET', 'POST'])
@app.route('/modalinterfaceinfo/<x>/<y>', methods=['GET', 'POST'])
def modalInterfaceInfo(x, y): #ddddd
    initialChecks()

    # x = device id, y = interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Removes dashes from interface in URL
    interface = interfaceReplaceSlash(y)

    intConfig = phi.pullInterfaceConfigSession(activeSession, interface, host)

    return render_template("/interfaceinfo.html",
                           host=host,
                           interface=interface,
                           intConfig=intConfig)

# To show running config on host
@app.route('/modalcmdshowrunconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdshowrunconfig/<x>', methods=['GET', 'POST'])
def modalCmdShowRunConfig(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    hostConfig = host.pull_run_config(activeSession)
    writeToLog('viewed running-config via button on host %s' % (host.hostname))
    return render_template("/cmdshowrunconfig.html",
                           host=host,
                           hostConfig=hostConfig)

# To show running config on host
@app.route('/modalcmdshowstartconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdshowstartconfig/<x>', methods=['GET', 'POST'])
def modalCmdShowStartConfig(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    hostConfig = host.pull_start_config(activeSession)
    writeToLog('viewed startup-config via button on host %s' % (host.hostname))
    return render_template("/cmdshowstartconfig.html",
                           host=host,
                           hostConfig=hostConfig)

# To show CDP neighbors on host
@app.route('/modalcmdshowcdpneigh/', methods=['GET', 'POST'])
@app.route('/modalcmdshowcdpneigh/<x>', methods=['GET', 'POST'])
def modalCmdShowCDPNeigh(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    result = host.pull_cdp_neighbor(activeSession)
    writeToLog('viewed CDP neighbors via button on host %s' % (host.hostname))
    return render_template("/cmdshowcdpneigh.html",
                           host=host,
                           result=result)

# To show inventory on host
@app.route('/modalcmdshowinventory/', methods=['GET', 'POST'])
@app.route('/modalcmdshowinventory/<x>', methods=['GET', 'POST'])
def modalCmdShowInventory(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    result = host.pull_inventory(activeSession)

    writeToLog('viewed inventory info via button on host %s' % (host.hostname))
    return render_template("/cmdshowinventory.html",
                           host=host,
                           result=result)

# To show CDP neighbors on host
@app.route('/modalcmdshowversion/', methods=['GET', 'POST'])
@app.route('/modalcmdshowversion/<x>', methods=['GET', 'POST'])
def modalCmdShowVersion(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    result = host.pull_version(activeSession)

    writeToLog('viewed version info via button on host %s' % (host.hostname))
    return render_template("/cmdshowversion.html",
                           host=host,
                           result=result)

# To run custom commands on host
@app.route('/modalcmdcustom/<x>', methods=['GET', 'POST'])
def modalCmdCustom(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)

    # Custom Commands form
    form = CustomCommandsForm(request.values, hostname=host.hostname)

    return render_template("/cmdcustom.html",
                           host=host,
                           form=form)

# To run custom commands on host
@app.route('/modalcfgcmdcustom/<x>', methods=['GET', 'POST'])
def modalCfgCmdCustom(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)

    # Custom Commands form
    form = CustomCfgCommandsForm(request.values, hostname=host.hostname)

    return render_template("/cfgcmdcustom.html",
                           host=host,
                           form=form)

# To save running config on host
@app.route('/modalcmdsaveconfig/<x>', methods=['GET', 'POST'])
def modalCmdSaveConfig(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    result = host.save_config_on_device(activeSession)

    writeToLog('saved config via button on host %s' % (host.hostname))
    return render_template("/cmdsaveconfig.html",
                           host=host)
    
# To run an interactive shell on host
@app.route('/db/viewhosts/hostshell/<x>', methods=['GET', 'POST'])
def hostShell(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)

    # Exit config mode if currently in it on page refresh/load
    exitConfigMode(host.id)

    writeToLog('accessed interactive shell on host %s' % (host.hostname))
    return render_template("hostshell.html",
                           host=host)

# To run a command via an interactive shell on host
@app.route('/hostshelloutput/<x>/<m>/<y>', methods=['GET', 'POST'])
def hostShellOutput(x, m, y): # NEED TO CLEANUP ddddd
    initialChecks()
    output = []
    configError = False

    # x = device id, m = config or enable mode, y = encoded commands from javascript
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)
    
    # Decode command in URL received from javascript
    command = unquote_plus(y).decode('utf-8')

    # Replace '_' with '/'
    command = interfaceReplaceSlash(command)

    # Append prompt and command executed to beginning of output
    output.append(host.find_prompt_in_session(activeSession) + command)

    # Check if last character is a '?'
    if command[-1] == '?':
      if m == 'c':
        # Get command output as a list.  Insert list contents into 'output' list
        configError = True
        #output.extend(getCfgCmdOutputNoCR(activeSession, command))
      else:
        # Get command output as a list.  Insert list contents into 'output' list
        #output.extend(getCmdOutput(activeSession, command))
        output.extend(getCmdOutputNoCR(activeSession, command))
        # Append prompt and command executed to end of output
        output.append(host.find_prompt_in_session(activeSession))
      
    else:
      if m == 'c':
        # Get command output as a list.  Insert list contents into 'output' list
        output.extend(getCfgCmdOutput(activeSession, command))
      else:
        # Get command output as a list.  Insert list contents into 'output' list
        output.extend(host.get_cmd_output(command, activeSession))
        # Append prompt and command executed to end of output
        output.append(host.find_prompt_in_session(activeSession))

    writeToLog('ran command on host %s - %s' % (host.hostname, command))

    return render_template("hostshelloutput.html",
                           output=output,
                           command=command,
                           mode=m,
                           configError=configError)

# Enters config mode on host
@app.route('/enterconfigmode/<x>', methods=['GET', 'POST'])
def enterConfigMode(x):
  initialChecks()
  # x = device id
  host = db_modifyDatabase.getHostByID(x)
  activeSession = retrieveSSHSession(host)
  host.enter_config_mode(activeSession)
    
  writeToLog('entered config mode via iShell on host %s' % (host.hostname))
  return ('', 204)

# Exits config mode on host
@app.route('/exitconfigmode/<x>', methods=['GET', 'POST'])
def exitConfigMode(x):
  initialChecks()

  # x = device id
  host = db_modifyDatabase.getHostByID(x)
  activeSession = retrieveSSHSession(host)
  host.exit_config_mode(activeSession)

  writeToLog('exited config mode via iShell on host %s' % (host.hostname))
  return ('', 204)


#######################################
# Begin Multiple Interface Selections #
#######################################

@app.route('/confirm/confirmmultipleintenable/<x>/<y>', methods=['GET', 'POST'])
def confirmMultiIntEnable(x, y):
    # x = device id, y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmmultipleintenable.html",
                           host=host,
                           interfaces=y)

@app.route('/confirm/confirmmultipleintdisable/<x>/<y>', methods=['GET', 'POST'])
def confirmMultiIntDisable(x, y):
    # x = device id, y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmmultipleintdisable.html",
                           host=host,
                           interfaces=y)
### WIP ###
@app.route('/confirm/confirmmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def confirmMultiIntEdit(x, y):
    # x = device id, y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmmultipleintedit.html",
                           host=host,
                           interfaces=y)


#@app.route('/results/interfaceenabled/', methods=['GET', 'POST'])
@app.route('/results/resultsmultipleintenabled/<x>/<y>', methods=['GET', 'POST'])
def resultsMultiIntEnabled(x, y):
    initialChecks()
    # x = device id, y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
      # a = interface
      if a:
        # Removes dashes from interface in URL
        a = interfaceReplaceSlash(a)
        result.append(host.run_enable_interface_cmd(a, activeSession))

    #result.append(host.save_config_on_device())

    writeToLog('enabled multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintenabled.html",
                           host=host,
                           interfaces=y,
                           result=result)

#@app.route('/results/resultsmultipleintdisabled/', methods=['GET', 'POST'])
@app.route('/results/resultsmultipleintdisabled/<x>/<y>', methods=['GET', 'POST'])
def resultsMultiIntDisabled(x, y):
    initialChecks()
    # x = device id, y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
      if a:
        # Removes dashes from interface in URL
        a = interfaceReplaceSlash(a)
        result.append(host.run_disable_interface_cmd(a, activeSession))

    #result.append(host.save_config_on_device())

    writeToLog('disabled multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintdisabled.html",
                           host=host,
                           interfaces=y,
                           result=result)
### WIP ###
#@app.route('/results/resultsmultipleintedit/', methods=['GET', 'POST'])
@app.route('/results/resultsmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def resultsMultiIntEdit(x, y):
    initialChecks()
    # x = device id, y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)
    activeSession = retrieveSSHSession(host)

    result = []
    # Split by interfaces, separated by '&'
    for a in y.split('&'):
      if a:
        # Removes dashes from interface in URL
        a = interfaceReplaceSlash(a)
        #result.append(ci.editInterface(activeSession, a, datavlan, voicevlan, other, host))

    result.append(host.save_config_on_device(activeSession))

    writeToLog('edited multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintedit.html",
                           host=host,
                           interfaces=y,
                           result=result)

#####################################
# End Multiple Interface Selections #
#####################################
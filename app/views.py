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
from scripts_bank.lib.netmiko_functions import getSSHSession, disconnectFromSSH, findPromptInSession, sessionIsAlive
from datetime import timedelta
from urllib import unquote_plus
import logging
from scripts_bank import netboxAPI
from redis import StrictRedis # http://blog.hackerearth.com/twitter-client-using-flask-redis
from uuid import uuid4

# Gets page referrer
# referrer = request.headers.get("Referer")

# Global Variables #
ssh = {}

###################
# Logging - Begin #
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

###################
# Logging - End #
###################


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
    sshKey = str(host.id) + '--' + str(session['UUID']) # str(session['USER'])
    #if not ssh[sshKey]:
    if sshKey not in ssh:
      writeToLog('initiated new SSH connection to %s' % (host.hostname))
      # If no currently active SSH sessions, initiate a new one
      ssh[sshKey] = getSSHSession(host.ios_type, host.ipv4_addr, creds)
    
    ### This worked but slowed down iShell commands by at least .63 seconds
    ### New method below is much faster (1.87s std command execution vs. 1.24s)
    #try:
    #  ssh[sshKey].send_command(' ')
    #except:
    #  writeToLog('reestablished SSH connection to %s' % (host.hostname))
    #  ssh[sshKey] = getSSHSession(host.ios_type, host.ipv4_addr, creds)

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
      if y[1] == session['UUID']:
        disconnectFromSSH(ssh[x])
        host = db_modifyDatabase.getHostByID(y[0])
        ssh = fn.removeDictKey(ssh, x)
        writeToLog('disconnected SSH session to device %s for user %s' % (host.hostname, session['USER']))
    
    writeToLog('disconnected all SSH sessions for user %s' % (session['USER']))

# Returns number of active SSH sessions tied to user
def countAllSSHSessions():
    global ssh

    i = 0
    for x in ssh:
        # x is id-uuid
        y = x.split('--')
        # y[0] is host id, y[1] is uuid
        if y[1] == str(session['UUID']):
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
    if host.ios_type == 'cisco_asa':
      command = 'show version | include up'
    else:
      command = 'show version | include uptime'
    uptime = getCmdOutput(activeSession, command)
    if host.ios_type == 'cisco_asa':
      for a in uptime:
        if 'failover' in a:
          break
        else:
          uptimeOutput = a.split(' ', 2)[-1]
    else:
      for a in uptime:
        uptimeOutput = a.split(' ', 3)[-1]
    return jsonify(uptimeOutput) 

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
    writeToLog('accessed host %s' % (host.hostname))

    # Get any existing SSH sessions
    activeSession = retrieveSSHSession(host)
    
    if host.ios_type == 'cisco_nxos':
      interfaces = phi.pullHostInterfacesNXOS(host.ipv4_addr, activeSession)
      #uptime = getCmdOutput(host.ipv4_addr, host.ios_type, 'show version | include uptime')
      #for x in uptime:
      #  uptimeOutput = x.split(' ', 3)[-1]

    elif host.ios_type == 'cisco_ios' or host.ios_type == 'cisco_iosxe':
      interfaces = phi.pullHostInterfacesIOS(host.ipv4_addr, activeSession)
      #uptime = getCmdOutput(host.ipv4_addr, host.ios_type, 'show version | include uptime')
      #for x in uptime:
      #  uptimeOutput = x.split(' ', 3)[-1]

    elif host.ios_type == 'cisco_asa':
      interfaces = phi.pullHostInterfacesASA(host.ipv4_addr, activeSession)
      #uptime = getCmdOutput(host.ipv4_addr, host.ios_type, 'show version | include up ')
      #for x in uptime:
      #  if 'failover' in x:
      #    break
      #  else:
      #    uptimeOutput = x.split(' ', 2)[-1]
    
    upInt, downInt, disabledInt, totalInt = phi.countInterfaceStatus(interfaces, host.ios_type)

    
    # if interfaces is x.x.x.x skipped - connection timeout, throw error page redirect
    if fn.containsSkipped(interfaces):
        disconnectFromSSH(ssh[sshKey])
        return redirect(url_for('noHostConnectError',
                                host=host.hostname))
    elif not interfaces:
        disconnectFromSSH(ssh[sshKey])
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
    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    return render_template("confirm/confirmintenable.html",
                           hostid=x,
                           interface=y)

@app.route('/confirm/confirmintdisable/', methods=['GET', 'POST'])
@app.route('/confirm/confirmintdisable/<x>/<y>', methods=['GET', 'POST'])
def confirmIntDisable(x, y):
    # x = device id, y = interface name
    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    return render_template("confirm/confirmintdisable.html",
                           hostid=x,
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
    host = db_modifyDatabase.getHostByID(x)
    hostname = request.form['hostname']
    ipv4_addr = request.form['ipv4_addr']
    hosttype = request.form['hosttype']
    ios_type = request.form['ios_type']
    
    result = db_modifyDatabase.editHostInDatabase(host, hostname, ipv4_addr, hosttype, ios_type)
    #result = True
    if result:
      writeToLog('edited host %s in database' % (host.hostname))
      return render_template("confirm/confirmhostedit.html",
                             title='Edit host confirm',
                             host=host,
                             hostname=hostname,
                             ipv4_addr=ipv4_addr,
                             hosttype=hosttype,
                             ios_type=ios_type)
    else:
        return redirect(url_for('confirmHostEdit',
                                x=host))

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

    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    result = ci.enableInterface(activeSession, y)
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

    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    result = ci.disableInterface(activeSession, y)
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

    # Removes dashes from interface in URL
    y = interfaceReplaceSlash(y)
    result = ci.editInterface(activeSession, y, datavlan, voicevlan, other, host)
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

    command = session['COMMAND']

    activeSession = retrieveSSHSession(host)
    
    result = getMultiCmdOutput(activeSession, command, host)

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

    command = session['COMMAND']

    activeSession = retrieveSSHSession(host)

    result = getMultiConfigCmdOutput(activeSession, command, host)

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
    # Removes dashes from interface in URL, replacing '_' with '/'
    interface = interfaceReplaceSlash(y)
    # Replace's '_' with '.'
    interface = interface.replace('=', '.')

    activeSession = retrieveSSHSession(host)

    if host.ios_type == 'cisco_ios':
      intConfig, intMac = phi.pullInterfaceInfo(activeSession, interface, host)
      intStats = phi.pullInterfaceStats(activeSession, interface, host)
      macToIP = ''
    elif host.ios_type == 'cisco_nxos':
      intConfig, intMac = phi.pullInterfaceInfo(activeSession, interface, host)
      intStats = phi.pullInterfaceStats(activeSession, interface, host)
      macToIP = ''
    else:
      intConfig = phi.pullInterfaceConfigSession(activeSession, interface, host)
      intMac = ''
      macToIP = ''
      intStats = ''
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
def modalEditInterfaceOnHost(x, y):
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
def modalInterfaceInfo(x, y):
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

    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    if host.ios_type == 'cisco_nxos':
      command = 'show running-config | exclude !'
    elif host.ios_type == 'cisco_ios' or host.ios_type == 'cisco_asa':
      command = "show running-config"
    else:
      command = "show running-config"

    hostConfig = getCmdOutput(activeSession, command)

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

    if host.ios_type == 'cisco_nxos':
      command = 'show startup-config | exclude !'
    elif host.ios_type == 'cisco_ios' or host.ios_type == 'cisco_asa':
      command = "show startup-config"
    else:
      command = "show startup-config"

    hostConfig = getCmdOutput(activeSession, command)

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

    command = "show cdp neighbors | begin ID"

    hostConfig = getCmdOutputWithCommas(activeSession, command)

    writeToLog('viewed CDP neighbors via button on host %s' % (host.hostname))
    return render_template("/cmdshowcdpneigh.html",
                           host=host,
                           hostConfig=hostConfig)

# To show inventory on host
@app.route('/modalcmdshowinventory/', methods=['GET', 'POST'])
@app.route('/modalcmdshowinventory/<x>', methods=['GET', 'POST'])
def modalCmdShowInventory(x):
    initialChecks()
    # x = device id
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    command = "show inventory"

    result = getCmdOutput(activeSession, command)

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

    command = "show version"

    result = getCmdOutput(activeSession, command)

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
#@app.route('/modalcmdsaveconfig/', methods=['GET', 'POST'])
@app.route('/modalcmdsaveconfig/<x>', methods=['GET', 'POST'])
def modalCmdSaveConfig(x):
    initialChecks()

    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    hostConfig = saveConfigOnSession(activeSession, host)

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
def hostShellOutput(x, m, y):
    initialChecks()
    output = []
    configError = False

    # x = device id, m = config or enable mode, y = encoded commands from javascript
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)
    
    command = unquote_plus(y).decode('utf-8')

    # Replace '_' with '/'
    command = interfaceReplaceSlash(command)

    # Append prompt and command executed to beginning of output
    output.append(findPromptInSession(activeSession) + command)

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
        output.append(findPromptInSession(activeSession))
      
    else:
      if m == 'c':
        # Get command output as a list.  Insert list contents into 'output' list
        output.extend(getCfgCmdOutput(activeSession, command))
      else:
        # Get command output as a list.  Insert list contents into 'output' list
        output.extend(getCmdOutput(activeSession, command))
        # Append prompt and command executed to end of output
        output.append(findPromptInSession(activeSession))

    # Append prompt and command executed to beginning of output
    #output.insert(0,findPromptInSession(activeSession) + command)

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
  
  enterConfigModeInSession(activeSession)
  
  writeToLog('entered config mode via iShell on host %s' % (host.hostname))
  
  return ('', 204)

# Exits config mode on host
@app.route('/exitconfigmode/<x>', methods=['GET', 'POST'])
def exitConfigMode(x):
  initialChecks()

  # x = device id
  host = db_modifyDatabase.getHostByID(x)

  activeSession = retrieveSSHSession(host)

  exitConfigModeInSession(activeSession)

  writeToLog('exited config mode via iShell on host %s' % (host.hostname))

  return ('', 204)
  

##########################
# Firewall ACL Generator #
##########################

@app.route('/fwaclgenerator', methods=['GET'])
def fwACLGenerator():
    hosts = db_modifyDatabase.getHostsByIOSType('cisco_asa')
    # Need to add support for above line for Netbox database.  currently only supports local
    form = FWACLGeneratorForm()
    form.hostname.query = hosts
    
    return render_template('/fwaclgenerator.html',
                           title='Generate ACL Config for Firewall',
                           form=form)

@app.route('/fwcheckopenports', methods=['GET'])
def fwCheckOpenPorts():
    hosts = db_modifyDatabase.getHostsByIOSType('cisco_asa')
    # Need to add support for above line for Netbox database.  currently only supports local
    form = FWCheckOpenPortsForm()
    form.hostname.query = hosts
    
    return render_template('/fwcheckopenports.html',
                           title='Check for Access Through Firewall',
                           form=form)

@app.route('/confirm/confirmfwaclconfig', methods=['GET', 'POST'])
def confirmFWACLConfig():
    #host = db_modifyDatabase.getHostByID(request.form['hostname'])
    #changeTicket = request.form['changeTicket']
    #changeDesc = request.form['changeDesc']
    #sourceIP = request.form['sourceIP']
    #destIP = request.form['destIP']
    #ports = request.form['ports']

    host = db_modifyDatabase.getHostByID(request.form['hostname'])
    session['HOSTNAME'] = host.hostname
    session['HOSTID'] = host.id
    session['CHANGETICKET'] = request.form['changeTicket']
    session['CHANGEDESC'] = request.form['changeDesc']
    session['SOURCEIP'] = request.form['sourceIP']
    session['DESTIP'] = request.form['destIP']
    session['PORTS'] = request.form['ports']

    return render_template("confirm/confirmfwaclconfig.html")

@app.route('/results/resultsfwaclgenerator', methods=['GET', 'POST'])
def resultsFWACLGenerator():
    try:
      host = db_modifyDatabase.getHostByID(session['HOSTID'])
    except:
      return redirect('/fwaclgenerator')

    changeTicket = session['CHANGETICKET']
    changeDesc = session['CHANGEDESC']
    sourceIP = session['SOURCEIP']
    destIP = session['DESTIP']
    ports = session['PORTS']

    resultStatus, configList, backoutList, allAccessAllowed = fop.main(host, changeTicket, changeDesc, sourceIP, destIP, ports)

    session.pop('HOSTNAME', None)
    session.pop('HOSTID', None)
    session.pop('CHANGETICKET', None)
    session.pop('CHANGEDESC', None)
    session.pop('SOURCEIP', None)
    session.pop('DESTIP', None)
    session.pop('PORTS', None)

    return render_template("results/resultsfwaclgenerator.html",
                            resultStatus=resultStatus,
                            configList=configList,
                            backoutList=backoutList,
                            allAccessAllowed=allAccessAllowed)

@app.route('/results/resultfwcheckopenports', methods=['GET', 'POST'])
def resultsFWCheckOpenPorts():
    try:
      host = db_modifyDatabase.getHostByID(request.form['hostname'])
    except:
      return redirect('/fwcheckopenports')

    sourceIP = request.form['sourceIP']
    destIP = request.form['destIP']
    port = request.form['port']
    protocol = request.form['protocol']

    activeSession = retrieveSSHSession(host)
    iface = getSourceInterfaceForHost(activeSession, sourceIP)

    status = checkAccessThroughACL(iface, sourceIP, destIP, port, protocol, activeSession)

    return render_template("results/resultsfwcheckopenports.html",
                            status=status[0])



#######################################
# Begin Multiple Interface Selections #
#######################################

#@app.route('/confirm/confirmmultipleintenable/', methods=['GET', 'POST'])
@app.route('/confirm/confirmmultipleintenable/<x>/<y>', methods=['GET', 'POST'])
def confirmMultiIntEnable(x, y):
    # x = device id
    # y = interfaces separated by '&' in front of each interface name
    #y = interfaceReplaceSlash(y)
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmmultipleintenable.html",
                           hostid=x,
                           interfaces=y,
                           host=host)

#@app.route('/confirm/confirmmultipleintdisable/', methods=['GET', 'POST'])
@app.route('/confirm/confirmmultipleintdisable/<x>/<y>', methods=['GET', 'POST'])
def confirmMultiIntDisable(x, y):
    # x = device id
    # y = interfaces separated by '&' in front of each interface name
    #y = interfaceReplaceSlash(y)
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmmultipleintdisable.html",
                           hostid=x,
                           interfaces=y,
                           host=host)
### WIP ###
#@app.route('/confirm/confirmmultipleintedit/', methods=['GET', 'POST'])
@app.route('/confirm/confirmmultipleintedit/<x>/<y>', methods=['GET', 'POST'])
def confirmMultiIntEdit(x, y):
    # x = device id
    # y = interfaces separated by '&' in front of each interface name
    #y = interfaceReplaceSlash(y)
    host = db_modifyDatabase.getHostByID(x)
    return render_template("confirm/confirmmultipleintedit.html",
                           hostid=x,
                           interfaces=y,
                           host=host)


#@app.route('/results/interfaceenabled/', methods=['GET', 'POST'])
@app.route('/results/resultsmultipleintenabled/<x>/<y>', methods=['GET', 'POST'])
def resultsMultiIntEnabled(x, y):
    initialChecks()
    result = []
    # x = device id
    # y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Split by interfaces, separated by '&'
    for a in y.split('&'):
      if a:
        # Removes dashes from interface in URL
        a = interfaceReplaceSlash(a)
        result.append(ci.enableInterface(activeSession, a))

    result.append(saveConfigOnSession(activeSession, host))

    writeToLog('enabled multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintenabled.html",
                           host=host,
                           interfaces=y,
                           result=result)

#@app.route('/results/resultsmultipleintdisabled/', methods=['GET', 'POST'])
@app.route('/results/resultsmultipleintdisabled/<x>/<y>', methods=['GET', 'POST'])
def resultsMultiIntDisabled(x, y):
    initialChecks()
    result = []
    # x = device id
    # y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Split by interfaces, separated by '&'
    for a in y.split('&'):
      if a:
        # Removes dashes from interface in URL
        a = interfaceReplaceSlash(a)
        result.append(ci.disableInterface(activeSession, a))

    result.append(saveConfigOnSession(activeSession, host))

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
    result = []
    # x = device id
    # y = interfaces separated by '&' in front of each interface name
    host = db_modifyDatabase.getHostByID(x)

    activeSession = retrieveSSHSession(host)

    # Split by interfaces, separated by '&'
    for a in y.split('&'):
      if a:
        # Removes dashes from interface in URL
        a = interfaceReplaceSlash(a)
        #result.append(ci.editInterface(activeSession, a, datavlan, voicevlan, other, host))

    result.append(saveConfigOnSession(activeSession, host))

    writeToLog('edited multiple interfaces on host %s' % (host.hostname))
    return render_template("results/resultsmultipleintedit.html",
                           host=host,
                           interfaces=y,
                           result=result)

#####################################
# End Multiple Interface Selections #
#####################################
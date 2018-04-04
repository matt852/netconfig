from app import app, logger, sshhandler
from app.auth import bp
from flask import redirect, request, render_template, session, url_for
from app.auth.forms import LoginForm
from app.scripts_bank.redis_logic import storeUserInRedis, deleteUserInRedis


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for user to save credentials."""
    form = LoginForm()
    if request.method == 'POST':
        # If page is accessed via form POST submission
        if form.validate_on_submit():
            # Validate form
            if 'USER' in session:
                # If user already stored in session variable, return home page
                return redirect(url_for('viewHosts'))
            else:
                # Try to save user credentials in Redis. Return index if fails
                try:
                    if storeUserInRedis(request.form['user'], request.form['pw']):
                        logger.write_log('logged in')
                        return redirect(url_for('viewHosts'))
                except:
                    logger.write_log('failed to store user data in Redis when logging in')
    # Return login page if accessed via GET request
    return render_template('auth/login.html', title='Login with SSH credentials', form=form)


@bp.route('/logout')
def logout():
    """Disconnect all SSH sessions by user."""
    sshhandler.disconnectAllSSHSessions()
    try:
        currentUser = session['USER']
        deleteUserInRedis()
        logger.write_log('deleted user %s data stored in Redis' % (currentUser))
        session.pop('USER', None)
        logger.write_log('deleted user %s as stored in session variable' % (currentUser), user=currentUser)
        u = session['UUID']
        session.pop('UUID', None)
        logger.write_log('deleted UUID %s for user %s as stored in session variable' % (u, currentUser), user=currentUser)
    except KeyError:
        logger.write_log('Exception thrown on logout.')
        return redirect(url_for('index'))
    logger.write_log('logged out')

    return redirect(url_for('index'))

from app import app
from flask import g, session
from uuid import uuid4


def generate_session_uuid():
    """Generate UUID for current user session, store in session variable."""
    session['UUID'] = uuid4()


def delete_user_in_redis():
    """Delete logged in user in Redis."""
    saved_id = g.db.hget('users', session['USER'])
    g.db.delete(saved_id)

    # Delete any locally saved credentials tied to user
    pattern = '*--' + str(session['USER'])
    for key in g.db.hscan_iter('localusers', match=pattern):
        # key[1] is the value we need to delete
        g.db.delete(key[1])
        g.db.delete(saved_id)


def reset_user_redis_expire_timer():
    """Reset automatic logout timer in Redis for logged in user.

    Reset Redis user key exipiration, as we only want to to expire after inactivity, not from initial login.
    x is Redis key to reset timer on.
    """
    try:
        saved_id = g.db.hget('users', session['USER'])
        g.db.expire(saved_id, app.config['REDISKEYTIMEOUT'])
    except:
        pass


def store_user_in_redis(user, pw, privpw='', host=''):
    """Save user credentials in Redis.

    If host is blank, then store as a general user.
    If host is defined, tag credentials to host as a local set of credentials.
    """
    try:
        if not host:
            # If user id doesn't exist, create new one with next available UUID
            # Else reuse existing key,
            #  to prevent incrementing id each time the same user logs in
            if g.db.hget('users', user):
                user_id = g.db.hget('users', user)
            else:
                # Create new user id, incrementing by 10
                user_id = g.db.incrby('next_user_id', 10)
            g.db.hmset(user_id, dict(user=user, pw=pw))
            g.db.hset('users', user, user_id)
            # Set user info timer to auto expire and clear data
            g.db.expire(user_id, app.config['REDISKEYTIMEOUT'])
            session['USER'] = user
            # Generate UUID for user, tie to each individual SSH session later
            try:
                if not session['UUID']:
                    generate_session_uuid()
            except:
                generate_session_uuid()

        else:
            # Key to save variable is host id, --, and username of logged in
            # user
            key = str(host.id) + "--" + str(session['USER'])
            if g.db.hget('localusers', key):
                saved_id = g.db.hget('localusers', key)
            else:
                # Create new host id, incrementing by 10
                saved_id = g.db.incrby('next_user_id', 10)

            if privpw:
                g.db.hmset(saved_id, dict(user=user, localuser=session['USER'], pw=pw, privpw=privpw))
            else:
                g.db.hmset(saved_id, dict(user=user, localuser=session['USER'], pw=pw))
            g.db.hset('localusers', key, saved_id)
            # Set user info timer to auto expire and clear data
            g.db.expire(saved_id, app.config['REDISKEYTIMEOUT'])

        # Return True if everything is succesful
        return True

    except:
        # Otherwise return False
        return False

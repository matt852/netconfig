from app import app
from flask import g, session
from uuid import uuid4


def generateSessionUUID():
	"""Generate UUID for current user session, store in session variable."""
	session['UUID'] = uuid4()


def deleteUserInRedis():
	"""Delete logged in user in Redis."""
	user_id = str(g.db.hget('users', session['USER']))
	g.db.delete(str(user_id))

	# Delete and locally saved credentials tied to user


def resetUserRedisExpireTimer():
	"""Reset automatic logout timer in Redis for logged in user.

	Reset Redis user key exipiration, as we only want to to expire after inactivity, not from initial login.
	x is Redis key to reset timer on.
	"""
	try:
		user_id = str(g.db.hget('users', session['USER']))
		g.db.expire(user_id, app.config['REDISKEYTIMEOUT'])
	except:
		pass


# Issue with this: i need to set the saved key I lookup later/reference to be unique and callable, for cleaning up later
# I can't save it as just the session['USER'], as I won't know which set of credentials to pull later if 2 devices use local_creds
# I can't set it to host.id, because I won't know how to distinguish which user they are tied to, and don't want to delete them for other users' existing sessions
# If host id doesn't exist, create new one with next available UUID
# Else reuse existing key,
#  to prevent incrementing id each time the same user logs in
def storeUserInRedis(user, pw, privpw='', host=''):
	"""Save user credentials in Redis.

	If host is blank, then store as a general user.
	If host is defined, tag credentials to host as a local set of redentials.
	"""
	try:
		if not host:
			# If user id doesn't exist, create new one with next available UUID
			# Else reuse existing key,
			#  to prevent incrementing id each time the same user logs in
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
			# Generate UUID for user, tie to each individual SSH session later
			try:
				if not session['UUID']:
					generateSessionUUID()
			except:
				generateSessionUUID()

		else:
			# Key to save variable is host id, --, and username of logged in user
			key = str(host.id) + "--" + str(session['USER'])
			if str(g.db.hget('localusers', key)) == 'None':
				# Create new host id, incrementing by 10
				saved_id = str(g.db.incrby('next_user_id', 10))
			else:
				saved_id = str(g.db.hget('localusers', key))

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

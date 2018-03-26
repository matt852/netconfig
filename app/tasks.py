from app import celery


@celery.task
def addTask(activeSession, host):
	"""Testing task."""
    host.save_config_on_device(activeSession)

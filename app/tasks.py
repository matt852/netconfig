from app import celery

@celery.task
def addTask(activeSession, host):
    host.save_config_on_device(activeSession)
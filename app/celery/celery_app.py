from celery import Celery


celery_app = Celery("my_chat")
celery_app.config_from_object("app.celery.celeryconfig")
celery_app.autodiscover_tasks(["app.celery.tasks"])

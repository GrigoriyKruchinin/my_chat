from app.config import settings

broker = settings.CELERY_BROKER_URL
result_backend = settings.REDIS_URL
broker_connection_retry_on_startup = True
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

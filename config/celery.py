# -----------------------------------------------------------
# Title: Celery
# Author:
# Date:
# Notes:
# Notes:
# -----------------------------------------------------------
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# The following security secures the broker and serializers against man in the middle attacks
# Whie not an issue now with it all on one server later when distributed to multiple servers
# Brokerage and serialisation will require SSL encryption and message signing.
# Server only
# import ssl

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.multi')
#app = Celery('config', broker='amqp://',backend='redis://')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
#app.autodiscover_tasks()

app.conf.update(
broker_url = 'amqp://guest:guest@localhost:5672//',
imports = ('ccschedule.tasks','ccreporting.tasks'),
result_backend = 'db+sqlite:///results.db',
timezone = 'Australia/Melbourne',
enable_utc=True,
# Potential risk to distribution but required for HTML emailing
# Note the email message itself is transmitted to the server via SSL
# The server send requires TLS.

task_serializer = 'pickle',
# Server only
# -----------
#security_key='/etc/ssl/private/worker.key',
#security_certificate='/etc/ssl/certs/worker.pem',
#security_cert_store='/etc/ssl/certs/*.pem',
)


# Server only
# -----------
#broker_use_ssl = {
#  'keyfile': '/var/ssl/private/worker-key.pem',
#  'certfile': '/var/ssl/amqp-server-cert.pem',
#  'ca_certs': '/var/ssl/myca.pem',
#  'cert_reqs': ssl.CERT_REQUIRED
#}

app.conf.beat_schedule = {
    'non_hierarchy_changes': {
        'task': 'ccschedule.tasks.HinyangoNonHierarchyChangeTasks',
        'schedule': crontab(minute='0',hour='4',day_of_week='mon,tue,wed,thu,fri'),},
    'hinyango_schedule': {
        'task': 'ccschedule.tasks.HinyangoStandardTasks',
        'schedule': crontab(minute='0',hour='5',day_of_week='mon,tue,wed,thu,fri'),}, 
    'scoring_def': {
        'task': 'ccschedule.tasks.ScoringTableUpdate',
        'schedule': crontab(minute='0',hour='0,12',day_of_week='mon,tue,wed,thu,fri'),},
    'report_immediate':{
        'task':'ccreporting.reporting_utils.execute_immediate',},
    'reporting_schedule':{
        'task': 'ccschedule.tasks.ReportingRun',
        'schedule': crontab(minute='0',hour='6',day_of_week='mon,tue,wed,thu,fri'),},
    'reporting_schedule':{
        'task': 'ccschedule.tasks.ReportingCleanup',
        'schedule': crontab(minute='0',hour='6',day_of_week='mon,tue,wed,thu,fri'),},
    
}

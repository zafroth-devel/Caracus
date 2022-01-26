# -----------------------------------------------------------
# Title: Celery
# Author:
# Date:
# Notes:
# Notes:
# -----------------------------------------------------------
from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery.schedules import crontab


app = Celery('ccschedule')


app.conf.update(
timezone = 'Australia/Melbourne',
broker_url = 'amqp://guest:guest@localhost:5672//',
imports = ('ccschedule.tasks',),
result_backend = 'db+sqlite:///results.db',
task_annotations = {'tasks.add': {'rate_limit': '10/s'}}
    )


app.conf.beat_schedule = {
    'working_week_2_am': {
        'task': 'ccschedule.tasks.HinyangoStandardTasks',
        #'schedule': crontab(minute=0, hour=2,day_of_week='monday,tuesday,wednesday,thursday,friday'),
        #'schedule': crontab(minute=0, hour=8,day_of_week='saturday,sunday'),
        'schedule': crontab(minute='*/5'),
    },
    'report_immediate':{
        'task':'ccreporting.reporting_utils.execute_immediate',
    }
}


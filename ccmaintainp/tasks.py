# -----------------------------------------------------------
# Title: Scheduling tasks
# Author:
# Date:
# Notes:
# Notes:
# -----------------------------------------------------------

from django.db import connection
from ccschedule.celery import app
from celery.schedules import crontab
import datetime
from cctenants.models import Client


@app.task
def my_task():
    print(str(datetime.datetime.now()))

@app.task
def HinyangoStandardTasks():
    tenants = Client.objects.all().exclude(schema_name='public').values('schema_name')
    print(tenants)



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
from cctenants.models import Client
from ccprojects.models import ProjectChange as pc
from django.contrib.auth.models import User
from ccprojects.models import ProjectStructure,UserProjects
from ccutilities.utilities import get_all_tenants
from ccmaintainp.models import HinyangoSettings
from django.db.models import Max,F
from datetime import datetime,timedelta
from ccutilities.arangodb_utils import hierarchy as hr

@app.task
def my_task():
    print(str(datetime.now()))


@app.task
def HinyangoNonHierarchyChangeTasks():
    '''Note we are working in the public schema until the connection is set to a particular tenant
       -------------------------------------------------------------------------------------------'''

    clients = Client.objects.all().exclude(schema_name='public')
    for client in clients:
        print(client)



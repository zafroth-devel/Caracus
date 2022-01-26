from django.db import connection
from ccreporting.tasks import ReportingTask
from cctenants.models import Client

def getreport():
    tenant = connection.schema_name
    rid = ReportingTask.delay(tenant)
    return rid
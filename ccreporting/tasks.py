from django.db import connection
from config.celery import app
from cctenants.models import Client

@app.task
def ReportingTask(schema):
    client = Client.objects.filter(schema_name=schema)[0]
    connection.set_tenant(client)
    print(connection.schema_name)
from ccprojects.models import ProjectChange,QuestionGroup,AnswerGroup,ImpactType,QATable
from ccreporting.models import LevelMatrix,OrgData
from django.db.models.aggregates import Max
from ccutilities.arangodb_utils import hierarchy
from datetime import datetime,timedelta
import pandas as pd
import numpy as np
from pandasql import sqldf
from ccutilities.utilities import residenttenant,pformat
from django.db import connection
#from ccreporting.models import ScoringDSet
from django.db.models import Max,F
from django.db.models.functions import Length
import math

pc = ProjectChange.objects.filter(inactive_date=None)
changeobjects = pc.filter(type_required='Change')
change_data = pd.DataFrame(list(changeobjects.values("id","projectmap","groupkey","nickname","start_date","end_date","ampp","resources","impact_type",confirmedstr=F("confirmed__confirmed"),impacttype=F("impact_type__impact_type"))))
lm = LevelMatrix.objects.all().values("id","impact_type","from_value","to_value","level",impacttype=F("impact_type__impact_type"))


# Part 1
impact_to_level = {}
it = list(ImpactType.objects.filter(type_required='Change').values_list('impact_type',flat=True))
for itm in it:
    impact_to_level[itm] = {}
# Build formats
for itm in lm.values():
    impact_to_level[itm['impacttype']][(itm['from_value'],itm['to_value'])] = str(itm['level'])

change_data['levels'] = change_data.apply(lambda row:pformat(impact_to_level[row['impacttype']]).fapply(row['ampp']),axis=1)

change_data['start_date'] = change_data['start_date'].dt.date
change_data['end_date'] = change_data['end_date'].dt.date
change_data['total_days'] = (change_data['end_date'] - change_data['start_date']).dt.days
change_data['total_business_days'] = change_data.apply(lambda row: np.busday_count(row['start_date'], row['end_date'], weekmask='1111100', holidays=[]),axis=1)

hobjects = hierarchy()

try:
    cg_temp_change_group_ids = hobjects.create_temp_table(change_group_ids=list(changeobjects.values_list('groupkey',flat=True)))
    query_str = """let cdata = (for bu in @@TENANT@@_businessUnit
                                   filter bu.change_data != null
                                   return {bu_label: bu.bu_unit_label,
                                           bu_name: bu.name,
                                           bu_id: bu._key,
                                           resources: bu.resource_count,
                                           bu_fid: bu._id,
                                           bu_change_pk:(
                                                           for cd in bu.change_data
                                                               for impact in @@TENANT@@_temp_doc_collection
                                                                   filter impact.temp_doc_id == '@@TEMPKEY@@' and cd.change_pk == impact.change_group_ids
                                                                   return merge(cd,impact))})
                               for itm in cdata
                                   for cd in itm.bu_change_pk
                                       filter cd.date_inactive == null
                                       sort cd.change_pk
                                       return {bu_id:itm.bu_id,
                                               project_id:cd.project_id,
                                               change_pk:cd.change_pk,
                                               start_date:cd.start_date,
                                               end_date:cd.end_date,
                                               bu_label:itm.bu_label,
                                               resources:itm.resources}""".replace('@@TENANT@@',residenttenant()).replace('@@TEMPKEY@@',str(cg_temp_change_group_ids['temp_doc_id']))

    buid_data = hobjects.query_hierarchy(query = query_str,batchsize = 1000)
finally:
    hobjects.delete_temp_table(cg_temp_change_group_ids['temp_doc_id'])


if buid_data:
    org = pd.DataFrame(buid_data['result']['result'])

    # VOLATILE
    cursor = connection.cursor()
    cursor.execute("TRUNCATE TABLE ccreporting_orgdata RESTART IDENTITY;")

    # Load org into django prepared table
obj_load = []
for itms in buid_data['result']['result']:
    if itms['start_date'] not in ['Tue, 30 Jul 2019 14:00:00 GMT','Tue, 30 Jul 2019 14:00:00 GMT','Tue, 30 Jul 2019 14:00:00 GMT','2019-07-30 14:00:00UTC','2019-07-30 14:00:00UTC','2019-08-30 14:00:00UTC','2019-07-30 14:00:00UTC','2019-06-30 14:00:00UTC','2019-08-01 00:00:00AEST','2019-07-31 00:00:00AEST']:
        obj_load.append(OrgData(hierarchy_bu_id=itms['bu_id'],project_id=int(itms['project_id']),hierarcy_bu_label=itms['bu_label'],change_group_id=int(itms['change_pk']),start_date=itms['start_date'],end_date=itms['end_date'],resources=itms['resources']))


    OrgData.objects.bulk_create(obj_load)




        class OrgData(models.Model):
    hierarchy_bu_id = models.CharField(max_length=15)
    project_id = models.IntegerField()
    hierarcy_bu_label = models.CharField(max_length=200)
    change_group_id = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    resources = models.IntegerField()
    def __str__(self):
        return 'OrgData'



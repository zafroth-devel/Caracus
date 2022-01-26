"""
------------------------------------------------------------------------
Title: Hinyango - Calculations - Scores - Ranking
Author: Matthew May
Date: 2019-07-25
Notes: Scoring and calculation redesign
Notes: Create working dataset used by charts and etc
------------------------------------------------------------------------
"""
from ccprojects.models import QuestionGroup,AnswerGroup,ImpactType
from ccreporting.models import LevelMatrix,OrgData,BuidIncrementalData,RawScores,DashData,BusinessUnits,OrgLevels
from ccchange.models import ProjectChange,QATable
from django.db.models.aggregates import Max
from ccutilities.arangodb_utils import hierarchy
from datetime import datetime,timedelta
from intervaltree import Interval, IntervalTree
import pandas as pd
import numpy as np
from pandasql import sqldf
from ccutilities.utilities import residenttenant,pformat,dictfetchall
from django.db import connection
#from ccreporting.models import ScoringDSet
from django.db.models import Max,F,Min
from django.db.models.functions import Length
import math
import uuid
from ccmaintainp.models import MessageLog
from intervaltree import Interval, IntervalTree
from dateutil.relativedelta import relativedelta
import json
'''
Apply format to dframe
pf = {('low','<20'):'level1',('20','<30'):'level2',('30','<40'):'level3',('40','high'):'level4'}
df = [{'item':1,'tcol':31},{'item':2,'tcol':25},{'item':3,'tcol':5},{'item':4,'tcol':900}]

dframe = pd.DataFrame(df)

geo = procformat(pf)

dframe['label']=dframe['tcol'].apply(geo.fapply)

change_data['value'] = change_data.apply(lambda row:pformat(impact_to_level[row['impacttype']]).fapply(row['ampp']),axis=1)
'''
class scoringdef:
    def __init__(self,startdate=None,enddate=None,trunc='Yes'):
        """[summary]
        Scoring engine
        
        [description]
        TBA
        
        Keyword Arguments:
            startdate {[type]} -- [description] (default: {None})
            enddate {[type]} -- [description] (default: {None})
            trunc {str} -- [description] (default: {'Yes'})
        """

        # All dates or a subset
        if startdate and enddate:
            self.startdate = startdate
            self.enddate = enddate
            self.alldates = False
        else:
            self.alldates = True

        self.dataset = None
        self.trunc_dset = trunc

        self.error = False
        self.message = ''
        self.status = 'In Progess'
        self.ident = uuid.uuid4().hex

    # Return status and error/success message
    def getstatus(self):
        """[summary]
        
        [description]
        """
        return {'error':self.error,'status':self.status,'message':self.message}

    # Return dataframe if successful None if not
    def getdata(self):

        return self.dataset

    # Build required dataset 
    def basedsets(self):

        # Get suppoting data Project Change, QATables and hierarchy
        # We can move this into a Foxx microservice to create
        # The raw tables 

        # Projectchange query reference
        pc = ProjectChange.objects.filter(inactive_date=None)
        
        # Get Project Change
        if self.alldates:
            changeobjects = pc.filter(type_required='Change')
        else:
            changeobjects = pc.filter(start_date__gte=self.startdate,end_date__lte=self.enddate,type_required='Change')

        if not changeobjects.count():
            self.error = True
            self.status = 'Failed'
            if self.alldates:
                self.message = 'No change objects'
            else:
                self.Message = 'No change objects for required startdate:{0} and enddate:{1}'.format(self.startdate,self.enddate)
            return True

        # Are there any user requested questions
        qa = QATable.objects.filter()

        if qa.filter(impacts__impact_type__type_required='Change').count():
            print('No code yet')

        hobjects = hierarchy()
        cursor = connection.cursor()
        # Hierarchy level data
        MessageLog.objects.create(ident=self.ident,status='Started',title='Get hierarchy level data',description='Arrango',log_entry='Running levels query')
        hlevels = hobjects.get_level_data()['levels_nodes_id']
        obj_load = []
        MessageLog.objects.create(ident=self.ident,status='Progress',title='Get hierarchy level data',description='Python',log_entry='Creating bulk upload')
        for key,value in hlevels.items():
            obj_load.append(OrgLevels(hierarchy_bu_id=key,hierarchy_level=value))

        total_landed = len(obj_load)

        MessageLog.objects.create(ident=self.ident,status='Progress',title='Get hierarchy level data',description='Postgres',log_entry='Truncating table')
        cursor.execute("TRUNCATE TABLE ccreporting_orglevels RESTART IDENTITY;")

        MessageLog.objects.create(ident=self.ident,status='Progress',title='Get hierarchy level data',description='Postgres',log_entry='Uploading data')
        OrgLevels.objects.bulk_create(obj_load)

        total_loaded = OrgLevels.objects.all().count()

        if total_landed != total_landed:
            MessageLog.objects.create(ident=self.ident,status='Failed',title='Get hierarchy level data',description='Postgres',log_entry='Data loaded not matching landed')
        else:
            MessageLog.objects.create(ident=self.ident,status='Success',title='Get hierarchy level data',description='Postgres',log_entry='Data loaded successfully')

        # Hierarchy objects - this loads into memory
        MessageLog.objects.create(ident=self.ident,status='Started',title='Query arrango change',description='Arrango',log_entry='Running orgdata query')

        try:
            cg_temp_change_group_ids = hobjects.create_temp_table(change_group_ids=list(changeobjects.values_list('groupkey',flat=True)))
            query_str = """let cdata = (for bu in _businessUnit
                                filter bu.change_data != null
                                return {{bu_label: bu.bu_unit_label,
                                        bu_name: bu.name,
                                        bu_id: bu._key,
                                        resources: bu.resource_count,
                                        bu_fid: bu._id,
                                        bu_change_pk:(
                                        for cd in bu.change_data
                                             for impact in _temp_doc_collection
                                                filter impact.temp_doc_id == {0} and 
                                                       cd.change_pk == impact.change_group_ids
                                                return merge(cd,impact))}})
                                                    for itm in cdata
                                                        for cd in itm.bu_change_pk
                                                            filter cd.date_inactive == null
                                                            sort cd.change_pk
                                                            return {{bu_id:itm.bu_id,
                                                                    project_id:cd.project_id,
                                                                    change_pk:cd.change_pk,
                                                                    start_date:cd.start_date,
                                                                    end_date:cd.end_date,
                                                                    bu_label:itm.bu_label,
                                                                    resources:itm.resources,
                                                                    required:cd.resources}}
                                                                    """.format(cg_temp_change_group_ids['temp_doc_id'])

            buid_data = hobjects.query_hierarchy(query = query_str,batchsize = 1000)
        except:
            MessageLog.objects.create(ident=self.ident,status='Failed',title='Query arrango change',description='Arrango-->Python',log_entry='Query failed')
            raise
        finally:
            hobjects.delete_temp_table(cg_temp_change_group_ids['temp_doc_id'])

        if buid_data:
            MessageLog.objects.create(ident=self.ident,status='Started',title='Loading OrgData',description='Arrango-->Python-->Postgres',log_entry='Running bulk upload')
            #org = pd.DataFrame(buid_data['result']['result'])
            # Send org to DB for processing
            # VOLATILE
            cursor.execute("TRUNCATE TABLE ccreporting_orgdata RESTART IDENTITY;")
            obj_load = []
            for itms in buid_data['result']['result']:
                #print(itms)
                obj_load.append(OrgData(hierarchy_bu_id=itms['bu_id'],project_id=int(itms['project_id']),hierarcy_bu_label=itms['bu_label'],change_group_id=itms['change_pk'],start_date=itms['start_date'],end_date=itms['end_date'],resources=itms['resources'],required=itms['required']))
            
            total_lines = len(obj_load)
            OrgData.objects.bulk_create(obj_load)

            # Check datd has loaded successfully
            total_loaded = OrgData.objects.all().count()

            if total_lines != total_loaded:
                MessageLog.objects.create(ident=self.ident,status='Failed',title='Loading OrgData',description='Arrango-->Python-->Postgres',log_entry='Load has failed counts did not match')
                raise IOError('Bulk upload of org data failed')
            else:
                MessageLog.objects.create(ident=self.ident,status='Success',title='Loading OrgData',description='Arrango-->Python-->Postgres',log_entry='Data loaded counts match')
                

            # Run Incremental Data creation query

            MessageLog.objects.create(ident=self.ident,status='Started',title='Running Incremental Data',description='Postgres',log_entry='Truncating data')
            cursor.execute("TRUNCATE TABLE ccreporting_buidincrementaldata RESTART IDENTITY;")
            incremental_load = BuidIncrementalData.objects.all().count()
            if incremental_load != 0:
                MessageLog.objects.create(ident=self.ident,status='Failed',title='Truncating incremental data',description='Postgres',log_entry='Old data still exists!')
                raise IOError('Incremental data clearing failed')

            MessageLog.objects.create(ident=self.ident,status='Started',title='Running Incremental Data',description='Postgres',log_entry='Running query')
            cursor.execute("""insert into ccreporting_buidincrementaldata (hierarchy_bu_id,
                                                          change_group_id,
                                                          start_date,
                                                          end_date,
                                                          h_start_date,
                                                          h_end_date,
                                                          min_h_start_date,
                                                          max_h_end_date,
                                                          incremental_start,
                                                          total_days,
                                                          resources,
                                                          required)
                              select             a.hierarchy_bu_id as buid,
                                                 a.change_group_id,
                                                 a.start_date,
                                                 a.end_date,
                                                 to_timestamp(a.start_date)::date as hstart_date,
                                                 to_timestamp(a.end_date)::date as hend_date,
                                                 to_timestamp(b.start_date)::date as min_hstart_date,
                                                 to_timestamp(b.end_date)::date as max_hend_date,
                                                 to_timestamp(a.start_date)::date - to_timestamp(b.start_date)::date as inc_start,
                                                 (to_timestamp(a.end_date)::date - to_timestamp(a.start_date)::date) as total_days,               
                                                 a.resources,
                                                 a.required
                              from (select * from ccreporting_orgdata) a
                              left join (select hierarchy_bu_id as buid,
                                                min(start_date) as start_date,
                                                max(end_date) as end_date
                                         from ccreporting_orgdata
                                         group by hierarchy_bu_id) b on a.hierarchy_bu_id = b.buid;""")

            incremental_load = BuidIncrementalData.objects.all().count()
            if incremental_load != total_loaded:
                MessageLog.objects.create(ident=self.ident,status='Failed',title='Incremental data failed',description='Postgres',log_entry='Time increments data failed to run!')
                raise IOError('Incremental data query failed')
            else:
                MessageLog.objects.create(ident=self.ident,status='Success',title='Running incremental data',description='Postgres',log_entry='Query completed as expected') 
        
            if self.trunc_dset == 'Yes':
                MessageLog.objects.create(ident=self.ident,status='Starting',title='Creating raw scores table data',description='Postgres',log_entry='Truncating table') 
                cursor.execute("TRUNCATE TABLE ccreporting_rawscores RESTART IDENTITY;")
                MessageLog.objects.create(ident=self.ident,status='Progess',title='Creating raw scores table data',description='Postgres',log_entry='Calculating scores') 
            else:
                MessageLog.objects.create(ident=self.ident,status='Starting',title='Creating raw scores',description='Postgres',log_entry='Warning truncate flag not set not truncating')
            
            # Loop through BUIDs and score incrementals
            buids = BuidIncrementalData.objects.values('hierarchy_bu_id').distinct()
            for itm in buids:
                incremental_src = BuidIncrementalData.objects.filter(hierarchy_bu_id = itm['hierarchy_bu_id'])
                raw_score_data = self.parse_intervals(incremental_src,RawScores)
                RawScores.objects.bulk_create(raw_score_data['result'])

            # Create dash tables
            # ------------------
            # From pc min date to pc max date month prior month after
            MessageLog.objects.create(ident=self.ident,status='Starting',title='Creating dash data',description='Postgres',log_entry='Truncating table') 
            cursor.execute("TRUNCATE TABLE ccreporting_dashdata RESTART IDENTITY;")

            dd_count = DashData.objects.all().count()
            dd_count_str = 'Counts = {0}'.format(str(dd_count))
            MessageLog.objects.create(ident=self.ident,status='Progress',title='Counting dash data',description='Postgres',log_entry=dd_count_str) 
            MessageLog.objects.create(ident=self.ident,status='Progress',title='Creating dash data',description='Postgres',log_entry='Producing table') 

            d_interval_1 = (ProjectChange.objects.aggregate(Min('start_date'))['start_date__min'] - relativedelta(years=1)).strftime('%Y-%m-%d')
            d_interval_2 = (ProjectChange.objects.aggregate(Max('end_date'))['end_date__max'] + relativedelta(years=1)).strftime('%Y-%m-%d')

            cursor.execute("select * from public.dashdata_insert(%s::date,%s::date)",[d_interval_1,d_interval_2])
            dd_count = DashData.objects.all().count()
            dd_count_str = 'Counts = {0}'.format(str(dd_count))
            MessageLog.objects.create(ident=self.ident,status='Progress',title='Counting dash data',description='Postgres',log_entry=dd_count_str)
            if dd_count > 0:
                MessageLog.objects.create(ident=self.ident,status='Success',title='Counting dash data',description='Postgres',log_entry='Data created successfully')
            else:
                MessageLog.objects.create(ident=self.ident,status='Failed',title='Creating dash',description='Postgres',log_entry='Data Failure')

            cursor.execute("TRUNCATE TABLE ccreporting_businessunits RESTART IDENTITY;")
            buid_data = hobjects.get_nodes()['result']['result']
            buid_data_bulk = []
            for itm in buid_data:
                buid_data_bulk.append(BusinessUnits(hierarchy_bu_id=itm['name'],hierarcy_bu_label=itm['bu']))

            BusinessUnits.objects.bulk_create(buid_data_bulk)


    def parse_intervals(self,intergrp,bulkupload):
        # All incremental dates are related to this one
        basedate = intergrp[0].min_h_start_date
        buid = intergrp[0].hierarchy_bu_id
        resources = intergrp[0].resources
    
        # Load interval tree
        itree = IntervalTree()
    
        for itm in intergrp: 
            itree[itm.incremental_start:itm.incremental_start+itm.total_days+1] = {'cid':itm.change_group_id,'res':itm.resources,'req':itm.required} 
        
        # Need to create contiguous intervals tied to length and number of resources
        all_data = []
        out_data = []
        for itm in itree:
            begin = itm.begin
            end = itm.end
            data = itm.data
            cycle = begin
            split_interval = []
            # Remove the interval we are currently looking at
            itree.removei(begin, end, data)
            print(data)
            print(itree)
            while True:
                # Start cycle
                if cycle == begin:
                    interval_list = [cycle]
    
                # Test current and next 
                test1 = sorted(itree[cycle])
                test2 = sorted(itree[cycle+1])
    
                if test1 != test2 or (cycle+1 == end and len(interval_list)==1):
                    interval_list.append(cycle)
                    interval_list.append([itms.data['req'] for itms in test1])
                    split_interval.append(interval_list)
                    interval_list = [cycle+1]
    
                if cycle+1 == end:
                    break
    
                cycle = cycle + 1
            
            # Add the interval back in 
            itree[begin:end] = data
    


            # Workon the split
            print(split_interval)
            for cnts in split_interval:
                denom = sum(cnts[2])
                total = data['req']+denom

                if total > resources:
                    # Modify output
                    mod = resources/total
                    ndenom = [float(i)*mod for i in cnts[2]]
                    score = ((float(data['req'])*mod)/(resources-sum(ndenom)))*100
                else:
                    score = (data['req']/(resources-denom))*100

                cnts.append(round(score,2))
                cnts[0] = basedate+timedelta(days=cnts[0])
                cnts[1] = basedate+timedelta(days=cnts[1])
                out_data.append(bulkupload(ident=self.ident,hierarchy_bu_id=buid,change_group_id=data['cid'],start_date=cnts[0],end_date=cnts[1],score=round(score,2)))

            all_data.append({data['cid']:split_interval})
    
        return {'all_data':all_data,'itree':itree,'result':out_data}



class ReportScores():
    def __init__(self,startdate,enddate,hgroup,groupby):

        self.groupby = groupby
        self.bu_label_length = BusinessUnits.objects.annotate(bu_label_length=Length('hierarcy_bu_label')).aggregate(Max('bu_label_length'))['bu_label_length__max']

        self.hierarchy = json.dumps(hgroup).replace('[','{').replace(']','}')
        self.start_date = startdate
        self.end_date = enddate

    def return_scores(self):
        # Create output data for heatmap
        cursor = connection.cursor()

        # 1=days,2=weeks,3=quarters,4=months
        print(self.hierarchy)
        print(self.groupby)
        print(self.start_date)
        print(self.end_date)

        try:
            cursor.execute('select * from public.vegaheatmap(%s,%s,%s,%s) order by sort_year,sort_month,sort_day;',[self.hierarchy,self.groupby,self.start_date,self.end_date])
        except Exception as e:
            print(str(e))
            output={'vcscores':None,'response':'DATA ERROR','bu_label_width':0}
        else:
            score_dict = dictfetchall(cursor)
            if len(score_dict) > 0:
                output={'vcscores':score_dict,'response':'success','bu_label_width':self.bu_label_length*6.2}
            else:
                output={'vcscores':None,'response':'NO DATA','bu_label_width':0}

        return output






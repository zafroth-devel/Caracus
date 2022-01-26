"""
------------------------------------------------------------------------
Title: Hinyango - Calculations - Scores - Ranking
Author: Matthew May
Date: 2016-01-17
Notes: Produce analysis scoring
Notes: 
------------------------------------------------------------------------
"""
from ccprojects.models import ProjectChange,QuestionGroup,AnswerGroup
from django.db.models.aggregates import Max
from ccutilities.arangodb_utils import hierarchy
from datetime import datetime,timedelta
#from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from pandasql import sqldf
from ccutilities.utilities import residenttenant
from django.db import connection

from ccreporting.models import ScoringDSet
from django.db.models import Max
from django.db.models.functions import Length



# Things to do 
# 1. create a class to create a document with a list of ORG NODES so we can filter on the table rather than a list
# 2. Apply the ranking as rank multiplied by the number of cases + question ranking
# 3. Create a dict with xaxis yaxis and zaxis as list,list, and list of lists respectively the zaxis has number
#    of internal lists that match the yaxis and number of list elements matching xaxis

class scoringdef():
    def __init__(self,startdate=None,enddate=None):

        if startdate and enddate:
            ChangeObjects = ProjectChange.objects.filter(start_date__gte=startdate,end_date__lte=enddate,type_required='Change')
        else:
            ChangeObjects = ProjectChange.objects.filter(type_required='Change')

        self.outdata = pd.DataFrame()
        self.bu_label_length = 0

        if ChangeObjects:

            oqlist=[]
            oalist=[]
            cgset = set()
            for qlist in ChangeObjects:
                oqlist.append(qlist.question_id)
                oalist.append(qlist.answers_id)
                cgset.add(qlist.groupkey_id)
  
            qobjects = QuestionGroup.objects.filter(id__in=oqlist)
            aobjects = AnswerGroup.objects.filter(id__in=oalist)

            if qobjects and aobjects:
                hobjects = hierarchy()
    
                level_data = hobjects.get_level_data()

                self.level_grouping_dict = level_data['levels_nodes']
                self.level_correction_dict = level_data['node_levels'] 
                self.level_parent_child = level_data['parent_child']
                self.level_node_bu = level_data['node_names']

                cg_temp_change_group_ids = hobjects.create_temp_table(change_group_ids=list(cgset))

                query_str = """for bu in @@TENANT@@_businessUnit
                                FILTER bu.change_data != null
                                RETURN {bu_label: bu.bu_unit_label,
                                        bu_name:bu.name,
                                        bu_id:bu._key,
                                        bu_fid:bu._id,
                                        bu_change_pk:(
                                            for cd in bu.change_data
                                                RETURN {change_pk:cd.change_pk,sponsor:cd.sponsor})}""".replace('@@TENANT@@',residenttenant())

                buid_data = hobjects.query_hierarchy(query = query_str,batchsize = 1000)

                hobjects.delete_temp_table(cg_temp_change_group_ids['temp_doc_id'])

                bu_label_width = 0
                if buid_data['result']['result']:
                    outlist = [] 
                    for buid in buid_data['result']['result']:
                        if len(buid['bu_label']) > bu_label_width:
                            bu_label_width = len(buid['bu_label'])
                        for itm in buid['bu_change_pk']:
                            subdict = {'hierarcy_bu_label':buid['bu_label'],'hierarchy_bu_id':buid['bu_id'],'bu_fid':buid['bu_fid'],'hierarchy_change_id':int(itm['change_pk']),'hierarchy_sponsor':itm['sponsor']}
                            outlist.append(subdict)

                    hierarchy_data = pd.DataFrame(outlist)

                    answer_rank = {}
                    for items in AnswerGroup.objects.values('question_map').annotate(max_arank=Max('arank')):
                        answer_rank[items['question_map']] = items['max_arank']
        
                    outlist = []
                    for items in AnswerGroup.objects.values('question_map').annotate(max_arank=Max('arank')):
                        subdict = {'mrank_question_map':items['question_map'],'max_arank':items['max_arank']}
                        outlist.append(subdict)
        
                    answer_rank_dict = pd.DataFrame(outlist)
        
                    max_qrank = int(QuestionGroup.objects.all().aggregate(Max('rank'))['rank__max'])
        
                    outlist = []
                    for buid in ChangeObjects:
                        subdict = {'change_id':buid.id,
                                    'change_project':buid.type_required,
                                    'nickname':buid.nickname,
                                    'start_date':buid.start_date.date(),
                                    'end_date':buid.end_date.date(),
                                    'change_answer_id':buid.answers_id,
                                    'change_group_id':buid.groupkey_id,
                                    'change_question_id':buid.question_id}
                        outlist.append(subdict)
        
                    change_data = pd.DataFrame(outlist)
        
                    outlist = []
                    for buid in qobjects:
                        subdict = {'question_id':buid.id,
                                    'question_name':buid.name,
                                    'qweight':buid.aweight,
                                    'question_type_id':buid.type_required_id,
                                    'qrank':buid.rank,
                                    'qscore':(max_qrank+1)-buid.rank,
                                    'is_question_active':buid.active,
                                    'question_na':buid.na}
                        outlist.append(subdict)
        
                    question_data = pd.DataFrame(outlist)
        
                    outlist = []
                    for buid in aobjects:
                        if buid.answers != 'NA':
                            subdict = {'answer_id':buid.id,
                                        'answer_name':buid.answers,
                                        'aweight':buid.aweight,
                                        'answer_question_id':buid.question_map_id,
                                        'arank':buid.arank,
                                        'ascore':(answer_rank[buid.question_map_id]+1)-buid.arank,
                                        'is_answer_active':buid.active}
                            outlist.append(subdict)
        
                    answer_data = pd.DataFrame(outlist)
        
                    # Now slap it together - this might not be viable it is completely in memory - chunk it for a small resolution ??
        
                    change_data = change_data.merge(hierarchy_data,left_on='change_group_id',right_on='hierarchy_change_id', how='inner') #.query("hierarchy_change_id==hierarchy_change_id")
                    change_data = change_data.merge(answer_data,left_on='change_answer_id',right_on='answer_id',how='inner')
                    change_data = change_data.merge(question_data,left_on='change_question_id',right_on='question_id',how='inner')
                    change_data = change_data.merge(answer_rank_dict,left_on='answer_question_id',right_on='mrank_question_map',how='inner')
        
                    # Get the answer in the dataset that has the most answer items
                    max_answers_group = max({ subkey: answer_rank[subkey] for subkey in change_data.answer_question_id.unique()}.values())-1

                    print(max_answers_group)
        
                    # Scale the scores
                    change_data['scaled_score'] = max_answers_group*((change_data['ascore']-1)/(change_data['max_arank']-1))+1
    
                    # Add levels
                    change_data['rep_levels'] = change_data['bu_fid'].map(self.level_grouping_dict)
        
                    self.outdata = change_data[['hierarcy_bu_label','hierarchy_bu_id','hierarchy_sponsor','change_group_id','bu_fid','rep_levels','start_date','end_date','qscore','ascore','scaled_score','answer_question_id','change_question_id']]
                    self.bu_label_length = bu_label_width
                
                    del(change_data)
                    del(outlist)
                    del(answer_data)
                    del(question_data)
                    del(buid_data)

    def get_scoring_data(self):
        return self.outdata

    def send_to_db_table(self):
        change_data = self.outdata

        print('===============================================================================================================================================')

        print(residenttenant())

        if not change_data.empty:
            from ccreporting.models import ScoringDSet

            # VOLATILE
            cursor = connection.cursor()
            cursor.execute("TRUNCATE TABLE ccreporting_scoringdset RESTART IDENTITY;")
            # # --------
            drec = change_data.to_dict('records')
            for row in drec:
                try:
                    ScoringDSet(hierarcy_bu_label=row['hierarcy_bu_label'],
                        hierarchy_bu_id=row['hierarchy_bu_id'],
                        change_group_id=row['change_group_id'],
                        bu_fid=row['bu_fid'],
                        rep_levels=row['rep_levels'],
                        start_date=row['start_date'],
                        end_date=row['end_date'],
                        qscore=row['qscore'],
                        ascore=row['ascore'],
                        scaled_score=row['scaled_score'],
                        answer_question_id=row['answer_question_id'],
                        change_question_id=row['change_question_id'],
                        change_sponsor=row['hierarchy_sponsor']).save()
                except:
                    pass


    # hierarcy_bu_label = models.CharField(max_length=200)
    # hierarchy_bu_id = models.CharField(max_length=15)
    # change_group_id = models.IntegerField()
    # bu_fid = models.CharField(max_length=70)
    # rep_levels = models.IntegerField()
    # start_date = models.DateField()
    # end_date = models.DateField()
    # qscore = models.IntegerField()
    # ascore = models.IntegerField()
    # scaled_score = models.FloatField()
    # answer_question_id = models.IntegerField()
    # change_question_id = models.IntegerField()
    # change_sponsor = models.CharField(max_length=30)
    # created_on = models.DateField(auto_now_add=True)

class ReportScores():
    def __init__(self,startdate,enddate,hierarchy_group,grouping):

        self.grouping = grouping

        print(hierarchy_group)

        hobjects = hierarchy()
    
        level_data = hobjects.get_level_data()

        self.level_grouping_dict = level_data['levels_nodes']
        self.level_correction_dict = level_data['node_levels'] 
        self.level_parent_child = level_data['parent_child']
        self.level_node_bu = level_data['node_names']

        # Retrieve outdata 
        scoring_def = list(ScoringDSet.objects.all().values())
        self.outdata = pd.DataFrame(scoring_def)
        if startdate and enddate:
            mask = (self.outdata['start_date'] >= startdate) & (self.outdata['end_date'] <= enddate)
            self.outdata = self.outdata.loc[mask]

        if hierarchy_group:
            self.outdata  = self.outdata.loc[self.outdata['hierarchy_bu_id'].isin(hierarchy_group)]

        self.bu_label_length = ScoringDSet.objects.annotate(bu_label_length=Length('hierarcy_bu_label')).aggregate(Max('bu_label_length'))['bu_label_length__max']

    def daterange(self,start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield(start_date + timedelta(n))

    def return_base_query_str(self):
        start_date = self.outdata.start_date.min()
        end_date = self.outdata.end_date.max()
        process_date = self.outdata.start_date.min()
  
        date_group_df = []
        for item in self.daterange(start_date, end_date):
            date_group_df.append({'date':item,'month':pd.Timestamp(item).month,'week':pd.Timestamp(item).week,'quarter':pd.Timestamp(item).quarter,'year':pd.Timestamp(item).year})
        date_group_df = pd.DataFrame(date_group_df)
  
        query_str ="""from
                      (SELECT a.date,
                              a.month,
                              a.quarter,
                              a.week,
                              a.year,
                              b.hierarcy_bu_label,
                              b.hierarchy_bu_id,
                              b.bu_fid,
                              b.rep_levels,
                              b.start_date,
                              b.end_date,
                              cast(b.qscore as REAL)/(select max(qscore) from change_data) as qscore,
                              b.ascore,
                              cast(b.scaled_score as REAL)/c.scaled_score as scaled_score,
                              (cast(b.qscore as REAL)/(select max(qscore) from change_data))*
                              (cast(b.scaled_score as REAL)/c.scaled_score) as total_score
                        FROM date_group_df a
                        inner join change_data b on a.date between b.start_date and b.end_date
                        left join (select answer_question_id,
                                          max(scaled_score) as scaled_score 
                                   from change_data
                                   group by answer_question_id) c on b.answer_question_id = c.answer_question_id)"""

        return {'df':date_group_df,'query_str':query_str}

    def get_analysis_df(self):
        # Return analysis dataframe
        change_data = self.outdata

        if not change_data.empty:
            base_query_data = self.return_base_query_str()
            date_group_df = base_query_data['df']
            query_str = base_query_data['query_str']

    def return_scores(self):
        # Create output data for heatmap

        change_data = self.outdata

        if not change_data.empty:

            base_query_data = self.return_base_query_str()
            date_group_df = base_query_data['df']
            query_str = base_query_data['query_str']
  
            if self.grouping == 'Days':
                top_code = """select date,substr('   JanFebMarAprMayJunJulAugSepOctNovDec',
                           (month*3)+1,3)||' '||cast((substr(date,9,2))*1 as text)||' '||year as label,
                           hierarcy_bu_label,sum(total_score) as score"""
                bottom_code = """group by date,hierarcy_bu_label order by date,hierarcy_bu_label"""
                query_str = top_code+" "+query_str+" "+bottom_code
                scored = sqldf(query_str,locals())
            elif self.grouping == 'Quarters':
                top_code = """select quarter,year,'quarter-'||quarter||' '||year as label,hierarcy_bu_label,round(sum(total_score)) as score"""
                bottom_code = """group by quarter,year,hierarcy_bu_label order by cast(quarter as int),cast(year as int),hierarcy_bu_label"""
                query_str = top_code+" "+query_str+" "+bottom_code
                scored = sqldf(query_str,locals())
            elif self.grouping == 'Weeks':
                top_code = """select week,year,'Week-'||week||' '||year as label,hierarcy_bu_label,round(sum(total_score)) as score"""
                bottom_code = """group by week,year,hierarcy_bu_label order by cast(year as int),cast(week as int),hierarcy_bu_label"""
                query_str = top_code+" "+query_str+" "+bottom_code
                scored = sqldf(query_str,locals())
            # This has been changed for the new dashboard view 13/03/2018 MM
            elif self.grouping == 'Levels':
                top_code = """select month,year,substr('   JanFebMarAprMayJunJulAugSepOctNovDec',(month*3)+1,3)||'-'||year as label,"""
                score_code = """'Level_'||rep_levels as hierarcy_bu_label,round(sum(total_score)) as score"""
                bottom_code = """group by month,year,rep_levels order by cast(year as int),cast(month as int)"""
                query_str = top_code+score_code+" "+query_str+" "+bottom_code
                scored = sqldf(query_str,locals())
            else:
                top_code = """select month,year,substr('   JanFebMarAprMayJunJulAugSepOctNovDec',(month*3)+1,3)||'-'||year as label,
                            hierarcy_bu_label,round(sum(total_score)) as score"""
                bottom_code = """group by month,year,hierarcy_bu_label order by cast(year as int),cast(month as int),hierarcy_bu_label"""
                query_str = top_code+" "+query_str+" "+bottom_code
                scored = sqldf(query_str,locals())
  
            score_dict = scored.to_dict('records')

            print(score_dict)

            xlabels = list(scored.label.unique())
  
            scored = scored[['label','hierarcy_bu_label','score']].pivot(index='hierarcy_bu_label',columns="label",values="score")[xlabels].fillna(0)
  
            ylabels = list(scored.index.unique())
  
            zvalues = scored.values

            outlist = []
            for items in zvalues:
                outlist.append(items.tolist())


          #Post process if a level or levels missing
            if self.grouping == 'Levels':
                total_keys = list(self.level_correction_dict.keys())
                if len(total_keys) != len(ylabels):
                    # Work out which are missing
                    correction_list = []
                    for itm in ylabels:
                        correction_list.append(int(itm.split('_')[1]))

                    list_diff = list(set(total_keys)-set(correction_list))

                    dummy_data = list(np.repeat(0,len(xlabels)))
          
                    for itm in list_diff:
                        ylabels.insert(itm-1,'Level_'+str(itm))
                        outlist.insert(itm-1,dummy_data)

            output={'response':'success','xlabels':xlabels,'ylabels':ylabels,'zvalues':outlist,'vcscores':score_dict,'bu_label_width':self.bu_label_length*6.2}
        else:
            output={'response':'NO DATA','xlabels':[],'ylabels':[],'zvalues':[],'bu_label_width':0}

        return output



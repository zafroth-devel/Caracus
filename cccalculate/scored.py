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
from ccutilities.arangodb_utils import hierarchy
from ccutilities.customquery import customsql
import datetime
import pandas as pd

# Things to do 
# 1. create a class to create a document with a list of ORG NODES so we can filter on the table rather than a list
# 2. Apply the ranking as rank multiplied by the number of cases + question ranking
# 3. Create a dict with xaxis yaxis and zaxis as list,list, and list of lists respectively the zaxis has number
#    of internal lists that match the yaxis and number of list elements matching xaxis

class scoringdef():
    def __init__(self,startdate,enddate,grouping):
        ChangeObjects = ProjectChange.objects.filter(start_date__gte=startdate,end_date__lte=enddate)

        oqlist=[]
        oalist=[]
        cgset = set()
        for qlist in ChangeObjects:
            oqlist.append(qlist.question_id)
            oalist.append(qlist.answers_id)
            cgset.add(qlist.groupkey_id)

        qobjects = QuestionGroup.objects.filter(id__in=oqlist)
        aobjects = AnswerGroup.objects.filter(id__in=oalist)
        hobjects = hierarchy()
        glist = grouping

        cg_temp_change_group_ids = hobjects.create_temp_table(change_group_ids=list(cgset))

        cg_temp_hierarchy_group_ids = hobjects.create_temp_table(change_group_ids=glist)

        query_str = """let cdata =(
                        for bu in fruity_businessUnit
                            FILTER bu.change_data != null
                            RETURN {bu_label: bu.bu_unit_label,
                                    bu_name:(
                                    FOR doc in fruity_temp_doc_collection
                                        FILTER bu.name==doc.change_group_ids && doc.temp_doc_id == '@@HIER@@'
                                        return bu.name
                                    ),
                                    bu_id:bu._key,
                                    change_pk:(
                                        for cd in bu.change_data
                                            RETURN cd.change_pk)})
                        let ddata= (
                        for items in cdata
                            
                    return {bu_id:items.bu_id,
                           bu_label:items.bu_label,
                           bu_name:items.bu_name,
                           bu_changepk:(
                           
                           FOR doc in fruity_temp_doc_collection
                               FILTER items.change_pk[0]==doc.change_group_ids && doc.temp_doc_id == '@@CIDS@@'
                               return{change_group_id:items.change_pk[0],
                                      temp_doc_id:doc.temp_doc_id,
                                      status:"ok"})})
                        for items in ddata
                            FILTER LENGTH(items.bu_changepk) > 0 && LENGTH(items.bu_name) > 0 
                          return items""".replace('@@HIER@@',str(cg_temp_hierarchy_group_ids['temp_doc_id'])).replace('@@CIDS@@',str(cg_temp_change_group_ids['temp_doc_id']))
        
        buid_data = hobjects.query_hierarchy(query = query_str,batchsize = 1000)

        hobjects.delete_temp_table(cg_temp_change_group_ids['temp_doc_id'])
        hobjects.delete_temp_table(cg_temp_hierarchy_group_ids['temp_doc_id'])

        outlist = []
        for buid in buid_data['result']['result']:
            subdict = {'bu_label':buid['bu_label'],'bu_id':buid['bu_id'],'change_id':int(buid['bu_changepk'][0]['change_group_id'])}
            outlist.append(subdict)

        query_str = """ SELECT a.id,
                               a.type_required, 
                               a.nickname, 
                               a.start_date, 
                               a.end_date, 
                               a.propogate, 
                               a.answers_id, 
                               a.confirmed_id, 
                               a.groupkey_id, 
                               a.projectmap_id, 
                               a.question_id,
                               b.name,
                               b.description,
                               b.aweight as qweight,
                               b.question,
                               ((select max(rank) from fruity.ccprojects_questiongroup)+1) - b.rank as question_score,
                               b.active,
                               b.na,
                               c.answers,
                               c.aweight,
                               (d.max_arank+1) - c.arank as answer_score
                          from fruity.ccprojects_projectchange a
                          left join fruity.ccprojects_questiongroup b on a.question_id = b.id
                          left join fruity.ccprojects_answergroup c on a.answers_id = c.id
                          left join
                          (select a.id,
                               b.max_arank
                          from fruity.ccprojects_answergroup a 
                          left join (
                          select question_map_id,max(arank) as max_arank
                          from fruity.ccprojects_answergroup 
                          group by question_map_id) b on a.question_map_id = b.question_map_id
                          order by a.id) d on a.answers_id = d.id
                          where c.answers != 'NA' -- All results with an NA answer are removed
                                and start_date >= %s
                                and end_date   <= %s"""


        change_data = pd.DataFrame(customsql(query_str,[startdate,enddate]).qdict())
        change_data = change_data.merge(pd.DataFrame(outlist),left_on='groupkey_id',right_on='change_id',how='left').query("change_id==change_id")        

        self.outdata = change_data

    def return_scores(self):
        return(self.outdata)


# from cccalculate.scored import scoringdef
# import datetime
# grouping_text = ['55605593','63314177','53076249']
# startdate = datetime.datetime(2017, 9, 17, 0, 0)
# enddate = datetime.datetime(2018, 4, 30, 0, 0)
# meo = scoringdef(startdate=startdate,enddate=enddate,grouping=grouping_text)
#
"""
------------------------------------------------------------------------
Title: Project Change
Author: Matthew May
Date: 2017-05-17
Notes: View Change Information
Notes: 
------------------------------------------------------------------------
"""

from django.shortcuts import render
from django.views.generic import View,FormView,TemplateView
from braces.views import LoginRequiredMixin
from ccprojects.models import ProjectStructure,QuestionType,QuestionGroup,AnswerGroup,Confirmed,HinyangoGroupKey,UserProjects,ImpactType,ViewPerms
import seaborn as sns
from django.db.models import Avg, Max, Min
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from ccchange.models import ProjectChange
from django.forms import model_to_dict
from django.http import HttpResponseRedirect,JsonResponse
from django.urls import reverse_lazy,reverse,resolve
from ccutilities.arangodb_utils import hierarchy
from ccutilities.utilities import residenttenant
from django.db.models import Count,F
from ccutilities.arangodb_utils import hierarchy
import json
from datetime import datetime
from django.utils import timezone
from ccutilities.formutils import FormBuilder as fb
from ccutilities.multiform import MultiFormsView
from rules.contrib.views import PermissionRequiredMixin
from django.contrib import messages

# Current scheduled view visual
class ChangeView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    template_name = "ccchange/changeview.html"
    
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 

    def get_context_data(self, **kwargs):
        context = super(ChangeView, self).get_context_data(**kwargs)

        # Required project only
        project_data = self.extract_data(project_id=self.kwargs['project_id'])

        context['project_change'] = {"proj":"Nothing"}
        context['project_id'] = self.kwargs['project_id']
        context['gantt_items'] = project_data[0]
        context['project_name'] = project_data[1]
        context['treeview'] = project_data[2]
        context['tree_select'] = project_data[3]


        return(context)

    def extract_data(self,project_id):
        """
        This is going to be a little tricky
        A pandas dataset will be created that joins various information for the 
        Change records to be viewed

        This may need to be pushed to a database table and then formulated there 
        if the in memory solution proves to resource hungry
        """
        
        
        ps = ProjectStructure.objects.get(pk=project_id)
        #pn = list(ProjectChange.objects.filter(projectmap=ps,type_required='Change'))
        pn = ProjectChange.objects.filter(projectmap=ps,type_required='Change',inactive_date=None).values('projectmap_id','nickname','start_date','end_date','confirmed_id','groupkey_id').annotate(Count('id'))
        hv = hierarchy().get_selected(project_id,None)
        cn = Confirmed.objects.values()

        # Get associated hierarchy items

        confirmed = {}
        for items in cn:
            if items['confirmed'] == 'Yes':
                confirmed[items['id']] = 'Confirmed'
            elif items['confirmed'] == 'No':
                confirmed[items['id']] = 'Unconfirmed'
            else:
                confirmed[items['id']] = 'Unknown'

        return_list = [] 
        outlist = [] 

        for colname in pn:
            hedlist={}
            hedlist['name'] = colname['projectmap_id']
            hedlist['nickname'] = colname['nickname']
            hedlist['id'] = colname['groupkey_id']
            hedlist['confirmed'] = confirmed[colname['confirmed_id']]
            hedlist['fromdate'] = colname['start_date'].strftime('%Y/%m/%d') 
            hedlist['todate'] = colname['end_date'].strftime('%Y/%m/%d')
            hedlist['label'] = colname['nickname']
            hedlist['cclass'] = 'ganttGreen'
            return_list.append(hedlist)



        outlist.append(return_list)

        outlist.append(ps.project_name)

        outlist.append(hierarchy().ul_render())


        # hv_list = {}
        # for item in hv:
        #     for cd in item['change_data']:
        #         if cd['change_pk'] in hv_list:
        #             hv_list[cd['change_pk']].add(item['id'])
        #         else:
        #             hv_list[cd['change_pk']]=set()
        #             hv_list[cd['change_pk']].add(item['id'])

        hv_list = {}

        for item in hv:
            for cd in item['change_data']:
                if cd['change_pk'] in hv_list:
                    hv_list[cd['change_pk']].append(item['id'])
                else:
                    hv_list[cd['change_pk']]=[]
                    hv_list[cd['change_pk']].append(item['id'])

        outlist.append({'sublist':json.dumps(hv_list)})



        return(outlist)

    def post(self, request, *args, **kwargs):


        tenant = residenttenant()

        if 'delete-change-ckbx' in request.POST:
            # Deleting after confirmation
            pc = ProjectChange.objects.filter(groupkey_id=request.POST['modify-change-cid-name'])
            pc.update(inactive_date=timezone.datetime.now()) # Change this to inactive
            # Delete hierarchy for change
            del_old_hier = hierarchy().make_inactive(int(request.POST['modify-change-hid-name']),int(request.POST['modify-change-cid-name']))
        elif 'full-update-ckbx' in request.POST:
            # This will allow only updates to existing questions and not any updated questions
                #return(HttpResponseRedirect(reverse_lazy('modifyquestions',kwargs={'change_target':'change','project_id':int(request.POST['modify-change-hid-name']),'change_id':int(request.POST['modify-change-cid-name'])})))
                # Major change to how projects are processed
            return(HttpResponseRedirect(reverse_lazy('modifyimpact',kwargs={'change_target':'change','project_id':int(request.POST['modify-change-hid-name']),'change_id':int(request.POST['modify-change-cid-name'])})))
        else:
            # Confirm box checked
            if 'confirm-change-ckbx' in request.POST:
                print('Confirm box clicked')
                pc = ProjectChange.objects.filter(groupkey_id=request.POST['modify-change-cid-name'])
                cf = Confirmed.objects.get(confirmed='Yes')
                pc.update(confirmed=cf)


            # Have the dates changed?
            # -----------------------

            start_date = timezone.datetime.strptime(self.request.POST['datestart'], '%B %d, %Y')
            end_date = timezone.datetime.strptime(self.request.POST['dateend'], '%B %d, %Y')

            if request.POST['modify-dates-changed-name'] == 'CHANGED':
                print('Dates changed')
                pc = ProjectChange.objects.filter(groupkey_id=request.POST['modify-change-cid-name'])
                pc.update(start_date=start_date,end_date=end_date)


            # It is not possible to use any events to determine if the hierarchy is different on the client side
            # So it will have to be done here


            # Has the hierarchy changed
            # -------------------------
            hv_current = hierarchy().get_selected(int(request.POST['modify-change-hid-name']),int(request.POST['modify-change-cid-name']))

            # Extract the sponsor details its the only thing that needs to be carried through from existing hierarchy data
            # There should be only one for each groupkey so first hierarchy item should be sufficient

            hv_current_list = []
            for item in hv_current:
                hv_current_list.append(item['id'])

            hv_new_list = json.loads(request.POST['hierarchy'])
            hv_current_list.sort()
            hv_new_list.sort()


            if hv_current_list != hv_new_list:
                # Add inactive date to old hierarchy members

                if hv_new_list:
                    del_old_hier = hierarchy().make_inactive(int(request.POST['modify-change-hid-name']),int(request.POST['modify-change-cid-name']))
                    for item in hv_new_list:
                        hierarchy().add_change_data(request.POST['modify-change-hid-name'],item,request.POST['modify-change-cid-name'],start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d')) 
                else:
                    print('Nothing in hierarchy')
        
        return(HttpResponseRedirect(reverse_lazy('viewchange',kwargs={'project_id':int(request.POST['modify-change-hid-name'])})))

# Proposed change visualisation
class ChangeViewVisual(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    template_name = "ccchange/changeviewvisual.html"
    
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 

    def get_context_data(self, **kwargs):
        context = super(ChangeViewVisual, self).get_context_data(**kwargs)
        project_data = self.extract_data(project_id=self.kwargs['project_id'])
        context['impactname'] = project_data['nickname']
        context['hierarchy'] = project_data['hierarchy']
        context['levels'] = project_data['level']
        context['impacttype'] = project_data['impacttype']
        context['ampp_level'] = project_data['ampp_level']
        context['tlcolors'] = project_data['tlcolors']
        context['stripedcolors'] = project_data['stripedcolors']
        
        return(context)

    def extract_data(self,project_id):
        hr = hierarchy()
        # # Nickname

        ps = ProjectStructure.objects.get(id=project_id)
        pc_ref = ProjectChange.objects.filter(type_required = 'Change',inactive_date=None,projectmap=ps)

        pc = list(pc_ref.filter(type_required = 'Change',inactive_date=None).distinct('nickname').values('id','nickname'))

        pc.append({'id':-1,'nickname':'Null/Impact Name Not Provided'})

        outlist = {}
        outlist['nickname'] = pc

        # Hierarchy nodes
        outlist['hierarchy'] = []
        for itm in hr.changepk_hierarchy(project_id=project_id):
            node_names = {}
            node_names['name'] = itm['bu']
            node_names['bu'] = itm['hierarchy']
            outlist['hierarchy'].append(node_names)

        # Hierarchy levels
        bu_list = [x['name'] for x in outlist['hierarchy']]
        level_list = hr.get_level_data()['levels_nodes_id']
        level_list = list(set([level_list[itm] for itm in bu_list if itm in level_list]))
        level_list = [{'id':itm,'name':itm} for itm in level_list]
        outlist['level'] = level_list

        # Impact Type <-- Fix this
        it = list(pc_ref.values(idv=F('impact_type'),impacttype=F('impact_type__impact_type')).distinct().order_by('idv'))
        outlist['impacttype'] = it

        # Impact Level
        pc = list(pc_ref.filter(type_required = 'Change',inactive_date=None).order_by('ampp_level').values('ampp_level').distinct())
        ampp_level_list = []
        for itm in pc:
            ampp_level_list.append({'id':itm['ampp_level'],'level':itm['ampp_level']})

        outlist['ampp_level'] = ampp_level_list

        # Colors 
        # Create a range of colours based on impact type
        palette = sns.color_palette(None,len(it)).as_hex()

        timeline_colors = []
        for num,itm in enumerate(it):
            timeline_colors.append({'id':itm['idv'],'classname':'itcolor_{0}'.format(itm['idv']),'color':palette[num]})

        outlist['tlcolors'] = timeline_colors

        timeline_colors = []
        for num,itm in enumerate(it):
            #timeline_colors.append({'id':itm['idv'],'classname':'strpcolor_{0}'.format(itm['idv']),'details':'-55deg,{0},{0} 10px,#e6e6e6b9 10px,#e6e6e6b9 20px'.format(palette[num])})
            #timeline_colors.append({'id':itm['idv'],'classname':'strpcolor_{0}'.format(itm['idv']),'details':'-55deg,#e6e6e6b9,#e6e6e6b9 5px,{0} 5px,{0} 20px'.format(palette[num])})
            timeline_colors.append({'id':itm['idv'],'classname':'strpcolor_{0}'.format(itm['idv']),'details':'-55deg,{0}b9,{0}b9 5px,{0} 5px,{0} 20px'.format(palette[num])})

        outlist['stripedcolors'] = timeline_colors

        return outlist

    def post(self, request, *args, **kwargs):

        hr = hierarchy()

        data_string = json.loads(request.POST.get('output'))['output']
        print(data_string)
        project_id = json.loads(request.POST.get('output'))['projectid']
        print(project_id)

        impactname_list = data_string['impactname']
        impacttype_list = data_string['impacttype']
        hierarchy_list = data_string['hierarchy']
        hierarchylevel_list = data_string['hierarchylevel']
        impact_level = data_string['impactlevel']
        

        sort1 = data_string['sort1']
        sort2 = data_string['sort2']
        sort3 = data_string['sort3']

        it = list(ImpactType.objects.filter(type_required='Change').values('id','impact_type'))
        impacttypes = {}
        for itm in it:
            impacttypes[itm['id']]=itm['impact_type']

        # Note the following line returns a Project Change Object cut at the first groupkey
        # Some fields will not be reliable answer, question for example
        # Be very wary of how it is to be used
        ps = ProjectStructure.objects.get(id=project_id)
        pc = ProjectChange.objects.filter(type_required = 'Change',inactive_date=None,projectmap=ps).distinct('groupkey')

        pc_min_date = (ProjectChange.objects.filter(type_required = 'Change',inactive_date=None).aggregate(Min('start_date'))['start_date__min'] - relativedelta(years=2)).strftime("%Y-%m-%d")
        pc_max_date = (ProjectChange.objects.filter(type_required = 'Change',inactive_date=None).aggregate(Max('end_date'))['end_date__max']  + relativedelta(years=2)).strftime("%Y-%m-%d")

        # Node list
        node_names = {}
        for itm in hr.get_nodes()['result']['result']:
            node_names[itm['name']] = itm['bu']

        levels = hr.get_level_data()['levels_nodes_id']

        cpk_hierarchy = hr.changepk_hierarchy()

        for itm in cpk_hierarchy:
            itm['level'] = str(levels[itm['bu']])

        node_names = hr.get_level_data()['node_names']

        # Build base output dataset
        data_list = []
        for itm in pc:
            data_line = {}
            data_line['key'] = itm.groupkey_id
            data_line['groupkey'] = str(itm.groupkey_id)
            data_line['impact_nickname'] = itm.nickname
            data_line['project_id'] = itm.projectmap.id
            data_line['project_name'] = itm.projectmap.project_name
            if itm.confirmed.confirmed == 'No':
                data_line['className'] = '''strpcolor_{0}'''.format(itm.impact_type_id)
            else:
                data_line['className'] = '''itcolor_{0}'''.format(itm.impact_type_id)
            data_line['impact_type'] = itm.impact_type.impact_type
            data_line['ampp_level'] = str(itm.ampp_level)
            data_line['start'] = itm.start_date.strftime('%Y-%m-%d')
            data_line['end'] = itm.end_date.strftime('%Y-%m-%d')
            data_list.append(data_line)

        cpk_hierarchy = pd.DataFrame(cpk_hierarchy)
        data_list = pd.DataFrame(data_list)

        #data_list = cpk_hierarchy.merge(data_list,left_on='change_pk',right_on='groupkey', how='left')
        data_list = data_list.merge(cpk_hierarchy,left_on='key',right_on='change_pk', how='inner')

        # Filter data
        if impactname_list:
            if len(impactname_list)>0:
                data_list = data_list[data_list.impact_nickname.isin(impactname_list)]

        if impacttype_list:
            if len(impacttype_list)>0:
                impact_types = []
                for itm in impacttype_list:
                    impact_types.append(impacttypes[int(itm)])
                data_list = data_list[data_list.impact_type.isin(impact_types)]

        if hierarchy_list:
            if len(hierarchy_list)>0:
                data_list = data_list[data_list.bu.isin(hierarchy_list)]

        if hierarchylevel_list:
            if len(hierarchylevel_list)>0:
                data_list = data_list[data_list.level.isin([str(x) for x in hierarchylevel_list])]

        if impact_level:
            if len(impact_level)>0:
                impact_levels = []
                for itm in impact_level:
                    impact_levels.append(itm)
                data_list = data_list[data_list.ampp_level.isin(impact_levels)]

        data_list = data_list.reset_index(drop=True)

        if not data_list.empty:

            # Parse Sort Order
            def sfn(op):
    
                if op == '1':
                    return 'hierarchy'
                elif op == '2':
                    return 'impact_type'
                elif op == '3':
                    return 'level'
                elif op == '4':
                    return 'impact_nickname'
                elif op == '5':
                    return 'ampp_level'
                else:
                    return 'id'
    
            sortorder = []
    
            if sort1:
                check_ord = sfn(sort1)
                if check_ord != 'id':
                    sortorder.append(check_ord)
    
            if sort2:
                check_ord = sfn(sort2)
                if check_ord != 'id':
                    sortorder.append(check_ord)
    
            if sort3:
                check_ord = sfn(sort3)
                if check_ord != 'id':
                    sortorder.append(check_ord)
    
            def match_row(row):
                #trans_row = """<table><tr><td>BU:{0}</td></tr><tr><td>Name:{1}</td></tr><tr><td>Type:{2}</td></tr><tr><td>Sponsor:{3}</td></tr><tr><td>Level:{4}</td></tr></table>""".format(row['hierarchy'],row['impact_nickname'],row['impact_type'],row['sponsor'],row['level'])
                #trans_row = """{0} - ({1}) - [{2}]<br/>{3} - {4} --> {5}""".format(row['impact_nickname'],row['impact_type'],row['sponsor'],row['hierarchy'],row['level'],row['id'])
                #trans_row = """{0} - ({1}) - [{2}]<br/>{3} - {4}""".format(row['impact_nickname'],row['impact_type'],row['sponsor'],row['hierarchy'],row['level'])
                trans_row = """{0} - ({1}) - [{2}]""".format(row['impact_nickname'],row['impact_type'],row['hierarchy'])
                return trans_row
    
            if len(sortorder) == 0:
                data_list = data_list.sort_values(by=['impact_nickname','impact_type','hierarchy','level']).reset_index(drop=True)
            else:
                data_list = data_list.sort_values(by=sortorder).reset_index(drop=True)


            choice = sfn(sort1) # 'hierarchy','impact_nickname','impact_type','level'
            if choice != 'id':
                bgroup = dict(enumerate(list(pd.unique(data_list[[choice]].values.ravel()))))
            else:
                bgroup = dict(enumerate(list(pd.unique(data_list.index.values.ravel()))))
            ugroup = dict(map(reversed,bgroup.items()))
            
            data_list['id'] = data_list.index
            data_list['group'] = data_list[choice].map(ugroup)
            data_list['content'] = data_list.apply(lambda row:match_row(row),axis=1)

            # Needs checking
            if choice != 'id':
                backgrounds=data_list.drop_duplicates([choice,'group'])[[choice,'group']]
                backgrounds['content'] = backgrounds[choice]
                backgrounds['id'] = ['B' + str(x) for x in range(0,len(backgrounds))]
                backgrounds['start'] = pc_min_date
                backgrounds['end'] = pc_max_date
                backgrounds['type'] = 'background'
                backgrounds['className'] = np.where(backgrounds.group % 2,'bgcolor_2','bgcolor_1')
                backgrounds = backgrounds[['id','content','start','end','type','className','group']].to_dict('records')


            # Data
            data_list = data_list[['id','content','group','start','end','className','project_id','project_name','impact_nickname','impact_type','hierarchy','level','ampp_level']].to_dict('records')
        
            if choice != 'id':
                data_list = data_list + backgrounds

            # Group remove content key line for no name groups that are still groups

            group_list = [{'id':value,'content':''} for (key,value) in ugroup.items()]
    
            return JsonResponse({'groups':group_list,'items':data_list,'result':'success'})
        else:
            return JsonResponse({'groups':[],'items':[],'result':'No Data'})
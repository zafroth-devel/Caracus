"""
------------------------------------------------------------------------
Title: APP - Dash - View
Author: Matthew May
Date: 2016-01-04
Notes: User Authorisation
Notes:
------------------------------------------------------------------------
"""
from django.shortcuts import render, redirect
from braces.views import LoginRequiredMixin
from django.views.generic import View,TemplateView
from django.db.models import Count
from datetime import datetime
from ccutilities.vegaconstants import VegaConstant
from ccprojects.models import ProjectStructure,UserProjects,ImpactType,ViewPerms
from ccchange.models import ProjectChange
from ccaccounts.models import AccountProfile

from ccutilities.utilities import residenttenant
from ccutilities.arangodb_utils import hierarchy
from django.db.models import Avg, Max, Min
from django.utils.timezone import localtime
# To be depreciated
# from cccalculate.scoring import scoringdef
# -----------------
from cccalculate.hscore import ReportScores
from ccreporting.models import ScoringDSet as sd
from ccreporting.models import RawScores,OrgData,OrgLevels
import json
from rules.contrib.views import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect,JsonResponse
from django.urls import reverse_lazy,reverse
from dateutil.relativedelta import relativedelta
from django.db.models import Q
import arrow
import pandas as pd
import numpy as np
from sklearn import linear_model
import seaborn as sns

from ccdash.dash_heatmap import dashdata_heatmap

# Heatmap view
class VegaHeatmapView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccdash/ccheatmapvega.html"
    #template_name = "ccdash/base.html"
    #permission_required = ('ccaccounts.standard_user')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 


    def post(self, request, *args, **kwargs):
        nodes_in_post = json.loads(request.POST.get('org_nodes'))
        dates_in_post = json.loads(request.POST.get('slider_dates'))
        units_in_post = json.loads(request.POST.get('model_units'))

        heatmap_from_date = datetime.strptime(dates_in_post['date_from'],'%b %d, %Y').date().strftime('%Y-%m-%d')
        heatmap_to_date = datetime.strptime(dates_in_post['date_to'],'%b %d, %Y').date().strftime('%Y-%m-%d')

        if units_in_post=='Days':
            print('Days')
            unit_group = 1
        elif units_in_post=='Weeks':
            print('Weeks')
            unit_group = 2
        elif units_in_post=='Quarters':
            print('Quarters')
            unit_group = 3
        else:
            print('Months - Default')
            unit_group = 4

        score_display_output = ReportScores(startdate=heatmap_from_date,enddate=heatmap_to_date,hgroup=nodes_in_post,groupby=unit_group).return_scores()

        if score_display_output['response'] == 'success':

            vconfig = dashdata_heatmap.vega_config().replace('@@SCHEMA@@',VegaConstant.get_schema()).replace('@@DATA@@',json.dumps(score_display_output['vcscores']))

            return JsonResponse({'response':'success','vegaconfig':vconfig})

        else:

            return JsonResponse({'response':'NO DATA','vegaconfig':'NO DATA'})

    def get_context_data(self, **kwargs):
        context = super(VegaHeatmapView, self).get_context_data(**kwargs)

        project_data = self.extract_data()
        #context['projectdata'] = project_data[0]

        context['srange'] = project_data['srange']
        context['treeview'] = project_data['treeview']
        context['condition'] = project_data['condition']
        context['bu_length'] = project_data['max_bu_length']
        #context['condition'] = {'condition':'success'}
        
        return(context)
    # This is fast even on large sets but continually returning the query set might slow things down
    # It needs to be cached, try memoized class never used these techniques so not sure
    # There may be other things to try in memory cache etc.
    # The chart data can take a while might be better off using a view
    

    # Note this needs to be fixed to bring in the proper hierarchy for the dashboard
    def extract_data(self):
        #project_list = list(ProjectStructure.objects.filter(userprojects__project_user__user__username=self.request.user).order_by('id'))
        change_min_date = ProjectChange.objects.aggregate(Min('start_date'))
        change_max_date = ProjectChange.objects.aggregate(Max('end_date'))

        outlist={}

        outlist['condition'] = ''


        if change_min_date['start_date__min'] and change_max_date['end_date__max']:
        
            date_range_delta = (change_max_date['end_date__max'] - change_min_date['start_date__min'])*.25
    
            begin_range = localtime(change_min_date['start_date__min']).strftime('%Y%m%d')
            end_range = localtime(change_max_date['end_date__max']).strftime('%Y%m%d')
            from_range = localtime(change_min_date['start_date__min']+date_range_delta).strftime('%Y%m%d')
            to_range = localtime(change_max_date['end_date__max']-date_range_delta).strftime('%Y%m%d')
    
            outlist['srange']={'begin_range':begin_range,'end_range':end_range,'from_range':from_range,'to_range':to_range}
            outlist['condition'] = {'condition':'success'}

        else:

            begin_range = localtime().strftime('%Y%m%d')
            end_range = localtime().strftime('%Y%m%d')
            from_range = begin_range
            to_range = end_range

            outlist['srange'] = {'begin_range':begin_range,'end_range':end_range,'from_range':from_range,'to_range':to_range}
            outlist['condition'] = {'condition':'failed'}

        outlist['treeview'] = hierarchy().ul_render()

        nodes = hierarchy().get_nodes()['result']['result']

        bu_length = 0
        for itm in nodes:
            if len(itm['bu']) > bu_length:
                bu_length = len(itm['bu'])

        outlist['max_bu_length'] = bu_length

        return(outlist)

class DashConsolidatedView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    #template_name = "ccdash/ccdashboard.html"
    template_name = "ccdash/cdashboard_consolidated_view_2.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(DashConsolidatedView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['impactname'] = project_data['nickname']
        context['hierarchy'] = project_data['hierarchy']
        context['levels'] = project_data['level']
        context['sponsors'] = project_data['sponsors']
        context['impacttype'] = project_data['impacttype']
        context['ampp_level'] = project_data['ampp_level']
        context['tlcolors'] = project_data['tlcolors']
        context['stripedcolors'] = project_data['stripedcolors']

        return(context)

    def extract_data(self):
        hr = hierarchy()
        # # Nickname
        pc = list(ProjectChange.objects.filter(type_required = 'Change',inactive_date=None).distinct('nickname').values('id','nickname'))

        pc.append({'id':-1,'nickname':'Null/Impact Name Not Provided'})

        outlist = {}
        outlist['nickname'] = pc

        # Hierarchy
        outlist['hierarchy'] = hr.get_nodes()['result']['result']

        node_names = {}
        for itm in outlist['hierarchy']:
            node_names[itm['name']] = itm['bu']

        # Hierarchy Level
        level_list = []
        for itm in list(hr.get_level_data()['node_levels'].keys()):
            level_list.append({'id':itm,'name':itm})

        outlist['level'] = level_list

        # Impact Type

        it = list(ImpactType.objects.filter(type_required='Change').values('id','impact_type'))
        outlist['impacttype'] = it

        # Sponsor
        ps = ProjectStructure.objects.all().values('sponsor_key').distinct()
        node_names = hr.get_level_data()['node_names']
        sponsor_list = []
        for itm in ps:
            sponsor_list.append({'id':itm['sponsor_key'],'sponsor':node_names['{0}_businessUnit/{1}'.format(residenttenant(),itm['sponsor_key'])]}) 

        outlist['sponsors'] = sponsor_list

        # Impact Level
        pc = list(ProjectChange.objects.filter(type_required = 'Change',inactive_date=None).order_by('ampp_level').values('ampp_level').distinct())
        ampp_level_list = []
        for itm in pc:
            ampp_level_list.append({'id':itm['ampp_level'],'level':itm['ampp_level']})

        outlist['ampp_level'] = ampp_level_list

        # Colors 
        # Create a range of colours based on impact type
        palette = sns.color_palette(None,len(it)).as_hex()

        timeline_colors = []
        for num,itm in enumerate(it):
            timeline_colors.append({'id':itm['id'],'classname':'itcolor_{0}'.format(itm['id']),'color':palette[num]})

        outlist['tlcolors'] = timeline_colors

        timeline_colors = []
        for num,itm in enumerate(it):
            #timeline_colors.append({'id':itm['idv'],'classname':'strpcolor_{0}'.format(itm['idv']),'details':'-55deg,{0},{0} 10px,#e6e6e6b9 10px,#e6e6e6b9 20px'.format(palette[num])})
            timeline_colors.append({'id':itm['id'],'classname':'strpcolor_{0}'.format(itm['id']),'details':'-55deg,{0}b9,{0}b9 5px,{0} 5px,{0} 20px'.format(palette[num])})

        outlist['stripedcolors'] = timeline_colors

        return outlist

    def post(self, request, *args, **kwargs):

        hr = hierarchy()

        data_string = json.loads(request.POST.get('output'))['output']

        impactname_list = data_string['impactname']
        sponsor_list = data_string['sponsor']
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
        pc = ProjectChange.objects.filter(type_required = 'Change',inactive_date=None).distinct('groupkey')

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
            data_line['sponsor'] =  node_names['{0}_businessUnit/{1}'.format(residenttenant(),itm.projectmap.sponsor_key)]
            data_line['sponsor_key'] = itm.projectmap.sponsor_key
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

        if sponsor_list:
            if len(sponsor_list)>0:
                data_list = data_list[data_list.level.isin(sponsor_list)]

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
                    return 'sponsor'
                elif op == '3':
                    return 'impact_type'
                elif op == '4':
                    return 'level'
                elif op == '5':
                    return 'impact_nickname'
                elif op == '6':
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
                data_list = data_list.sort_values(by=['impact_nickname','impact_type','sponsor','hierarchy','level']).reset_index(drop=True)
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
            data_list = data_list[['id','content','group','start','end','className','project_id','project_name','impact_nickname','impact_type','sponsor','hierarchy','level','ampp_level']].to_dict('records')
    
            if choice != 'id':
                data_list = data_list + backgrounds

            # Group remove content key line for no name groups that are still groups

            group_list = [{'id':value,'content':''} for (key,value) in ugroup.items()]
    
            return JsonResponse({'groups':group_list,'items':data_list,'result':'success'})
        else:
            return JsonResponse({'groups':[],'items':[],'result':'No Data'})


class DashDrillDown(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    #template_name = "ccdash/ccdashboard.html"
    template_name = "ccdash/cdashboard_level_drilldown.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(DashDrillDown, self).get_context_data(**kwargs)
        context['param'] = {'param':json.dumps(kwargs)}
        return(context)

class DashImpactsDrillDown(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    #template_name = "ccdash/ccdashboard.html"
    template_name = "ccdash/cdashboard_impacts_drilldown.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(DashImpactsDrillDown, self).get_context_data(**kwargs)
        context['param'] = {'param':json.dumps(kwargs)}
        project_data = self.extract_data()
        context['impactdata'] = project_data

        return(context)

    def extract_data(self):
        ks = self.kwargs
        print(ks)

        interval_date = arrow.get(ks['year']+'-'+ks['month'].zfill(2)+'-'+ks['day'].zfill(2),'YYYY-MM-DD')
 
        #rs = RawScores.objects.filter(hierarchy_bu_id=ks['buid']).filter(Q(start_date__gte=interval_date.date(),start_date__lte=interval_date.date())|Q(end_date__gte=interval_date.date(),end_date__lte=interval_date.date()))

        rs = RawScores.objects.filter(hierarchy_bu_id=ks['buid']).filter(start_date__lte=interval_date.date(),end_date__gte=interval_date.date())

        pc_data = ProjectChange.objects.filter(groupkey_id__in=rs.values_list('change_group_id'))

        org_data = OrgData.objects.filter(hierarchy_bu_id=ks['buid'],change_group_id__in=rs.values_list('change_group_id',flat=True))

        org_info_dset = {}
        for itm in org_data:
            org_info_dset[itm.change_group_id] = [itm.hierarchy_bu_id,itm.hierarcy_bu_label,itm.resources,itm.required]

        pc_info_dset = {}
        for itm in pc_data:
            pc_info_dset[itm.groupkey_id] = [itm.nickname,itm.impact_type.impact_type,itm.projectmap.project_name]

        output_dset = []
        for itm in rs:
            subdict = {}
            subdict['change_id'] = itm.change_group_id
            subdict['project'] = pc_info_dset[itm.change_group_id][2]
            subdict['impact_name'] = pc_info_dset[itm.change_group_id][0]
            subdict['impact_type'] = pc_info_dset[itm.change_group_id][1]
            subdict['business_unit'] = org_info_dset[itm.change_group_id][1]
            subdict['resourcing'] = org_info_dset[itm.change_group_id][2]
            subdict['required'] = org_info_dset[itm.change_group_id][3]
            subdict['score'] = itm.score
            output_dset.append(subdict)

        return output_dset


# Heatmap view
class DashboardView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    #template_name = "ccdash/ccdashboard.html"
    template_name = "ccdash/ccdashboard_trial_20180530_1721_4.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['project_status'] = project_data['project_status']
        context['total_projects_ds'] = project_data['total_projects_ds']
        context['total_impacts_ds'] = project_data['total_impacts_ds']
        context['total_confirmed_impacts_ds'] = project_data['total_confirmed_impacts_ds']

        return(context)

    def extract_data(self):
        # Project Status Message
        tmb = arrow.now().shift(months=-2)
        omb = arrow.now().shift(months=-1)
        
        ps = ProjectStructure.objects.filter(created_on__gte=tmb.date())

        date_now = arrow.now()
        date_3mb = date_now.replace(months=-3).date()
        pco = ProjectChange.objects.filter(type_required='Change',start_date__gte=date_3mb).values('created_on','groupkey')

        if pco and ps:
            if ps:
                out_list = []
                for itm in ps:
                    in_dict = {}
                    if itm.created_on >= tmb.date() and itm.created_on < omb.date():
                        in_dict['prior'] = 1
                    else:
                        in_dict['prior'] = 0
                    in_dict['status'] = itm.projectstatus.project_status
                    in_dict['severity'] = itm.projectstatus.status_sev_order
                    out_list.append(in_dict)
                
                risk = pd.DataFrame(out_list)
                
                severity = risk[(risk.severity <= 2)].groupby('prior')['severity'].count().to_dict()
    
                if severity:
                    if len(severity.keys()) == 2:
                        perc_inc_dec = ((severity[0] - severity[1])/severity[1])*100
                        if perc_inc_dec >= 0:
                            project_status_class = 'text-danger'
                            project_status_arrow = 'icon-arrow-up12'
                            project_status_perc = '(+{0}%)'.format(str(round(perc_inc_dec)))
                            if perc_inc_dec < 5:
                                project_status_msg = 'Stable '+ str(severity[0])
                            elif perc_inc_dec >= 5 and perc_inc_dec < 15:
                                project_status_msg = 'Moderate '+ str(severity[0])
                            elif perc_inc_dec >= 50 and perc_inc_dec < 100:
                                project_status_msg = 'High '+ str(severity[0])
                            else:
                                project_status_msg = 'Severe '+ str(severity[0])
                        else:
                            project_status_class = 'text-success'
                            project_status_arrow = 'icon-arrow-down12'
                            project_status_perc = '(-{0}%)'.format(str(round(perc_inc_dec)))
                            if abs(perc_inc_dec) < 5:
                                project_status_msg = 'Stable '+ str(severity[0])
                            else:
                                project_status_msg = 'Declining '+ str(severity[0])
                    else:
                        if 1 in severity.keys():
                            if len(severity.keys()) == 2:
                                perc_inc_dec = ((severity[0] - severity[1])/severity[1])*100
                            else:
                                perc_inc_dec = 100
                            project_status_class = 'text-success'
                            project_status_arrow = 'icon-arrow-down12'
                            project_status_perc = '({0}%)'.format(str(round(perc_inc_dec)))
                            project_status_msg = 'Declining 0'
                        else:
                            project_status_class = 'text-danger'
                            project_status_arrow = 'icon-arrow-up12'
                            project_status_perc = '(+100%)'
                            project_status_msg = 'Declining 0'
                else:
                    project_status_class = 'text-success'
                    project_status_arrow = 'icon-circle'
                    project_status_perc = '(+0%)'
                    project_status_msg = 'No Activity 0'
    
            else:
                project_status_class = 'text-success'
                project_status_arrow = 'icon-circle'
                project_status_perc = '(+0%)'
                project_status_msg = 'No Activity 0'
    
            # Impact Levels
            output_dict = {'project_status_class':project_status_class,'project_status_arrow':project_status_arrow,'project_status_perc':project_status_perc,'project_status_msg':project_status_msg}
    
            start_range = arrow.Arrow.now()
            end_range = start_range.shift(years=+1)
    
            chart_data = RawScores.objects.filter(Q(start_date__gte=start_range.date(),start_date__lte=end_range.date())|Q(end_date__gte=start_range.date(),end_date__lte=end_range.date()))
            if chart_data:
                arg = chart_data.order_by('-score').first()
    
                min_date = RawScores.objects.filter(score=arg.score).aggregate(Min('start_date'))['start_date__min']
    
                max_date = RawScores.objects.filter(score=arg.score).aggregate(Max('end_date'))['end_date__max']
    
                impact_level_msg = 'Peak {0}:{1} - {2}'.format(str(arg.score),min_date.strftime("%b %Y"),max_date.strftime("%b %Y"))
    
                output_dict['impact_level_msg'] = impact_level_msg
            else:
                output_dict['impact_level_msg'] = 'Flat No Peak'
    
    
            # Impacts over time
    
            if pco:
    
                pc = pd.DataFrame(list(pco))
            
                pc['C'] = pc['created_on'].dt.strftime('%b%Y')
                
                first_group = pc.groupby(['C','groupkey']).first().reset_index()
                
                reg_base = first_group.groupby('C').size().to_frame('size').reset_index()
                
                reg_base.insert(0, 'x', range(0, len(reg_base)))
                
                X = pd.DataFrame(reg_base['x'])
                Y = pd.DataFrame(reg_base['size'])
                
                lm = linear_model.LinearRegression()
                
                model = lm.fit(X,Y)
                
                cf = round(lm.coef_[0][0],3)
        
                impacts_per_month = round(reg_base['size'].mean(),1)
        
        
                if cf == 0:
                    impacts_otime_msg = 'Stable - {0} (ipm)'.format(str(impacts_per_month))
                    impacts_otime_class = 'text-success'
                    impacts_otime_arrow = 'icon-circle'
                    impacts_otime_perc = '(0%)'
                elif cf > 0:
                    perc_output = round(((1/cf)/(1+(1/cf)))*100,1)
        
                    if perc_output < 10:
                        impacts_otime_msg = 'Stable - {0} (ipm)'.format(str(impacts_per_month))
                        impacts_otime_class = 'text-success'
                        impacts_otime_arrow = 'icon-circle'
                        impacts_otime_perc = '({0}%)'.format(str(perc_output))
                    else:
                        impacts_otime_msg = 'Up - {0} (ipm)'.format(str(impacts_per_month))
                        impacts_otime_class = 'text-danger'
                        impacts_otime_arrow = 'icon-arrow-up12'
                        impacts_otime_perc = '({0}%)'.format(str(perc_output))
        
                    # Increasing needs message
                else:
                    perc_output = round(((1/abs(cf))/(1+(1/abs(cf))))*100,1)
                    # Decreasing needs to message
                    if perc_output < 10:
                        impacts_otime_msg = 'Stable - {0} (ipm)'.format(str(impacts_per_month))
                        impacts_otime_class = 'text-success'
                        impacts_otime_arrow = 'icon-circle'
                        impacts_otime_perc = '({0}%)'.format(str(perc_output))
                    else:
                        impacts_otime_msg = 'Down - {0} (ipm)'.format(str(impacts_per_month))
                        impacts_otime_class = 'text-success'
                        impacts_otime_arrow = 'icon-arrow-down12'
                        impacts_otime_perc = '({0}%)'.format(str(perc_output))
            else:
                impacts_otime_msg = 'zero - 0 (ipm)'
                impacts_otime_class = 'text-success'
                impacts_otime_arrow = 'icon-circle'
                impacts_otime_perc = '(0%)'
    
            output_dict['impacts_otime_class'] = impacts_otime_class
            output_dict['impacts_otime_arrow'] = impacts_otime_arrow
            output_dict['impacts_otime_perc'] = impacts_otime_perc
            output_dict['impacts_otime_msg'] = impacts_otime_msg
    
            # The three upper stats
            # ---------------------
    
            # Total active projects
    
            closed_perm = ViewPerms.objects.get(viewing_perms = 'closed')
            not_closed = UserProjects.objects.all().exclude(project_perms=closed_perm).values_list("projectmap_id").distinct()
            total_projects_ds = ProjectStructure.objects.filter(id__in=not_closed).count()
    
            total_impacts_ds = ProjectChange.objects.filter(type_required='Change',end_date__gte=datetime.now()).count()
    
            total_confirmed_impacts_ds = ProjectChange.objects.filter(type_required='Change',confirmed__confirmed="Yes",end_date__gte=datetime.now()).count()
    
            return {'project_status':output_dict,'total_projects_ds':total_projects_ds,'total_impacts_ds':total_impacts_ds,'total_confirmed_impacts_ds':total_confirmed_impacts_ds}
        else:
            project_status_class = 'text-success'
            project_status_arrow = 'icon-circle'
            project_status_perc = '(+0%)'
            project_status_msg = 'No Data Available'

            # Impact Levels
            output_dict = {'project_status_class':project_status_class,'project_status_arrow':project_status_arrow,'project_status_perc':project_status_perc,'project_status_msg':project_status_msg}
            
            impacts_otime_msg = 'zero - 0 (ipm)'
            impacts_otime_class = 'text-success'
            impacts_otime_arrow = 'icon-circle'
            impacts_otime_perc = 'No Data Available'
    
            output_dict['impacts_otime_class'] = impacts_otime_class
            output_dict['impacts_otime_arrow'] = impacts_otime_arrow
            output_dict['impacts_otime_perc'] = impacts_otime_perc
            output_dict['impacts_otime_msg'] = impacts_otime_msg

            total_projects_ds = 0
            total_impacts_ds = 0
            total_confirmed_impacts_ds = 0

            output_dict['impact_level_msg'] = 'No Data Available'

            return {'project_status':output_dict,'total_projects_ds':total_projects_ds,'total_impacts_ds':total_impacts_ds,'total_confirmed_impacts_ds':total_confirmed_impacts_ds}

# The following is experimental
# -----------------------------
class DashHierarchyView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    #template_name = "ccdash/ccdashboard.html"
    template_name = "ccdash/cdashboard_hierarchy_view.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(DashHierarchyView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['nodes'] = project_data['nodes']
        context['edges'] = project_data['edges']
        return(context)

    def extract_data(self):
        # Get Hierarchy Data Need Nodes (including label)
        # Edges 
        # Levels for user defined hierarchy display

        levels = hierarchy().get_level_data()['levels_nodes_id']

        nodes = hierarchy().get_nodes()['result']['result']
        node_list = []
        node_copy = {}
        for num,itm in enumerate(nodes):
            node_list.append(json.dumps({'id':num,'buid':itm['name'],'label':'{1} - {0}'.format(itm['name'],itm['bu']),'level':levels[itm['name']],'shape':'box','group':levels[itm['name']]}))
            node_copy[itm['name']] = num

        edges = hierarchy().get_edges()['result']['result']
        edge_list = []
        for itm in edges:
            edge_list.append(json.dumps({'from':node_copy[itm['from'].split('/')[1]],'to':node_copy[itm['to'].split('/')[1]]}))

        return {'nodes':node_list,'edges':edge_list}

    def post(self, request, *args, **kwargs):
        pass
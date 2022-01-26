from django.shortcuts import render
from django.urls import reverse_lazy,reverse
from ccreporting.chartfactory import DataFactory
from ccutilities.vegaconstants import VegaConstant
from django.http import HttpResponseRedirect,HttpResponse,Http404
from braces.views import LoginRequiredMixin
from django.views.generic import View,FormView,TemplateView
from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType
from ccchange.models import ProjectChange
from django.http import JsonResponse
from django.db.models import Count,Min,Max
import pandas as pd
from django.contrib import messages
import datetime
import pytz
from directmessages.apps import Inbox
from django.contrib.auth.models import User
import json
from django.conf import settings
from rules.contrib.views import PermissionRequiredMixin
from ccutilities.utilities import residenttenant
from ccutilities.formutils import FormBuilder as fb
import ccreporting.reportingconfig as rc 
from ccutilities.module_utilities import module_import
from ccreporting.models import ScheduledReports,FilesAvailable
from ccaccounts.models import AccountProfile
import os
from django.urls import resolve

mod_list = {}

drill_path = '/analysis/drilldown/'
drill_path_impacts = '/analysis/impacts/drilldown/'

for key, value in rc.reports.items():
    mod_list[key] = {'tenants':value['tenants'],'report_object':module_import(value['app']+'.'+value['package']+'.'+value['report'])}

class ReportingBroker(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_template_names(self):
        return("ccreporting/reporting_broker.html")

    def construct_form_elements(self):

        ddict = self.kwargs

        formlist = []
        infoitems = []   
        # Load report list
        for key, value in mod_list.items():
            if value['tenants'][0] == 'all' or residenttenant() in value['tenants'][0]:
                indexlist = []
                # If the report is marked as all or the tenant name is listed then add the report
                form_items = value['report_object']().form_elements()
                form_info = value['report_object']().report_information()
                form_info['reportid'] = key
                indexlist.append(form_info)
                innerlist=[]
                for k,itms in form_items.items():
                    innerlist.append(itms[0])

                indexlist.append(fb(innerlist).return_form())

                formlist.append(indexlist)

        return formlist


    def get_context_data(self,**kwargs):
        context = super(ReportingBroker, self).get_context_data(**kwargs)
        form_data = self.construct_form_elements()
        context['forms'] = form_data
        return context

    def extract_data(self):
        pass

    def post(self, request, *args, **kwargs):
        # Duplicate the POST (stops weird things from happening)
        report_parameters = dict(request.POST)

        # Remove middleware token
        del report_parameters['csrfmiddlewaretoken']

        # Get the report id
        report_id = int(report_parameters['report-id'][0])

        # Call the reports post handle method
        mod_list[report_id]['report_object']().post_handling(request_data=report_parameters,request_user=self.request.user,conduit=self.request)

        return HttpResponseRedirect(reverse_lazy('reporting'))

class ReportingManager(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_template_names(self):
        return("ccreporting/reporting_manager.html")

    def get_context_data(self,**kwargs):
        context = super(ReportingManager, self).get_context_data(**kwargs)
        context['reports'] = self.extract_data()
        return context

    def extract_data(self):
        cuser = AccountProfile.objects.get(user__username=self.request.user)
        sr = ScheduledReports.objects.filter(reporting_request=cuser).exclude(run_immediate=True).values('id','report_id','report_name','scheduled_run_date','run_count','data')
        return sr

    def post(self, request, *args, **kwargs):
        sr = ScheduledReports.objects.get(id=int(request.POST['delete-report-hidden-name']))
        sr.delete()
        return HttpResponseRedirect(reverse_lazy('rmanager'))


class ReportDownload(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_template_names(self):
        return("ccreporting/reporting_downloads.html")

    def get_context_data(self,**kwargs):
        context = super(ReportDownload, self).get_context_data(**kwargs)
        context['reports'] = self.extract_data()
        return context

    def extract_data(self):
        cuser = AccountProfile.objects.get(user__username=self.request.user)
        fa = FilesAvailable.objects.filter(reporting_request=cuser)
        return fa

class DownloadRView(LoginRequiredMixin,PermissionRequiredMixin,View):

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('viewproject'))
        
    def get(self,request,*args,**kwargs):
        file_id = self.kwargs['file_id']
        at = FilesAvailable.objects.get(id=file_id)
        file_path = os.path.join(settings.BASE_DIR, at.path_on_server,residenttenant(),at.report_name)
        print(file_path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=at.mime_type)
                response['Content-Disposition'] = 'inline; filename=' + at.report_name
            return(response)
        raise Http404("File does not exist.") 


class Vega(LoginRequiredMixin,PermissionRequiredMixin,View):

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get(self, request, *args, **kwargs):
        self.factory = DataFactory()
        if self.kwargs['req_id'] == 'schema':
            output = self.get_schema()
            return JsonResponse(output,safe=False)
        elif self.kwargs['req_id'] == 'config':
            # Add data to the schema here
            print(drill_path_impacts)
            output = self.get_config().replace('@@SCHEMA@@',reverse('vconfig', kwargs={'req_id': 'schema','data_id':self.kwargs['data_id'],'para':self.kwargs['para']}))
            output = output.replace('@@DATA@@',self.get_data(self.kwargs['para']))
            output = output.replace('@@DRILLDOWN@@',drill_path)
            output = output.replace('@@IMPACTS@@',drill_path_impacts)
            #print(output)
            return HttpResponse(output)
        else:
            output = '[{"result":"Returned no results"}]'
            return HttpResponse(output)

    def get_schema(self):
        return VegaConstant.get_schema()

    def get_data(self,params): 
        return self.factory.get_data(self.kwargs['data_id']).json_data(params) 

    def get_config(self):
        return self.factory.get_data(self.kwargs['data_id']).vega_config()


# Message broker
class HinyangoMessages(LoginRequiredMixin,PermissionRequiredMixin,View):
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def post(self, request, *args, **kwargs):

        action = request.POST.get('action')

        print(action)

        if action=='get unread messages':
            ur = User.objects.get(username=self.request.user)
    
            tz_settings = getattr(settings,'TIME_ZONE',None)
    
            est=pytz.timezone(tz_settings)
    
            ur_msg = list(Inbox.get_unread_messages(ur).values('id', 'content', 'sender_uname','sender_id','subject','sent_at'))
    
            ur_msg = sorted(ur_msg, key=lambda ur_msg: ur_msg['sent_at'],reverse=True)
    
            now = datetime.datetime.now()
    
            outlist = []
            for msg in ur_msg:
                inlist = {}
                inlist['id'] = msg['id']
                inlist['subject'] = msg['subject']
                inlist['sender'] = msg['sender_uname']
                inlist['days'] = (now.date() - (msg['sent_at'].astimezone(est).replace(tzinfo=None)).date()).days
                inlist['content'] = msg['content']
                outlist.append(inlist)
    
            outlist = outlist[:5]
    
            return JsonResponse({'messages':json.dumps(outlist),'count':len(ur_msg)})
        else:
            messageid = request.POST.get('messageid')
            print(messageid)
            Inbox.read_message(messageid)
            return JsonResponse({'returned':1})

class HinyangoMessageCentre(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccreporting/messagecentre.html"
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
        context = super(HinyangoMessageCentre, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['all_messages'] = project_data['outlist']
        context['all_users'] = project_data['users']

        print(context['all_users'])
        return(context)

    def extract_data(self):

        project_data = {}

        all_users = User.objects.all().exclude(username__in=['admin','hinyango','Hinyango','Administrator',self.request.user]).values('id','username','first_name','last_name','email')

        template_data = []
        for itm in all_users:
            template_dict = {}
            template_dict['users'] = '<option value="'+itm['username']+'">'+itm['username']+'</option>'
            template_data.append(template_dict)

        project_data['users'] = template_data


        all_messages = sorted(list(Inbox.get_all_messages(user = self.request.user).values()), key=lambda ur_msg: ur_msg['sent_at'],reverse=True)

        outlist = []
        for itm in all_messages:
            subdict = {}
            if itm['read_at']:
                subdict['as_read'] = 'Y'
            else:
                subdict['as_read'] = 'N'
            subdict['id'] = itm['id']
            subdict['sender_id'] = itm['sender_id']
            subdict['sender'] = itm['sender_uname']
            subdict['subject'] = itm['subject']
            subdict['message'] = itm['content']
            subdict['date_sent'] = '{0:02d}/{1:02d}/{2:04d}'.format(itm['sent_at'].day,itm['sent_at'].month,itm['sent_at'].year)
            outlist.append(subdict)

        project_data['outlist'] = outlist

        return(project_data)

    def post(self, request, *args, **kwargs):
        print(request.POST);

        if request.POST.get('action') == 'mark all messages read':
            all_messages = list(Inbox.get_unread_messages(user = self.request.user).values())
            for itm in all_messages:
                Inbox.read_message(itm['id'])
        elif request.POST.get('action') == 'send hinyango message':
            recipient_list = json.loads(request.POST.get('recipients'))
            subject = json.loads(request.POST.get('subject'))
            body = json.loads(request.POST.get('body'))

            for usr in recipient_list:
                recipient = User.objects.get(username=usr)
                Inbox.send_message(self.request.user, self.request.user.username, recipient, subject, body)
        else:
            raise ValueError('The posted ajax parameter is not recongnised')

        return JsonResponse({'returned':1})
        

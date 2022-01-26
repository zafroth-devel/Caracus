"""
------------------------------------------------------------------------
Title: APP - Project - Add Project - View - mod 2
Author: Matthew May
Date: 2016-01-17
Notes: User Authorisation
Notes: Note move over to use the reference manager from project
Notes: UTC universal timezeons and conversion
Notes: 

            # To convert the times to a local timezone
            import datetime
            import pytz
            from pytz import timezone

            # Set timezone to UTC
            utc = pytz.utc

            # javascript timestamp --> milliseconds since 1/1/1970
            # Unix timestamp --> seconds since 1/1/1970
            # convert javascript timestamp/1000

            jst = 1565359200000

            utc_dt = utc.localize(datetime.datetime.utcfromtimestamp(jst/1000))

            # Now utc_dt is in utc timezone
            # To convert to a local timezone

            au_tz = timezone('Australia/Melbourne')
            au_dt = utc_dt.astimezone(au_tz)

            # result --> datetime.datetime(2019, 8, 10, 0, 0, tzinfo=<DstTzInfo 'Australia/Melbourne' AEST+10:00:00 STD>)
             

------------------------------------------------------------------------
"""
from django.shortcuts import render, redirect
from django.urls import reverse_lazy,reverse,resolve

from django.http import HttpResponseRedirect,JsonResponse
from braces.views import LoginRequiredMixin
from django.views.generic import View,FormView,TemplateView

from django.contrib import messages

from itertools import count
from django.db.models import Count

from ccutilities.utilities import residenttenant
from ccutilities.arangodb_utils import hierarchy

from ccaccounts.models import AccountProfile
from ccnotes.models import ProjectNotes
from django.contrib.auth.models import User

from ccprojects.models import ProjectStructure,UserProjects,ProjectStatus,ViewPerms,QuestionGroup
from ccprojects.models import AnswerGroup,Confirmed,HinyangoGroupKey,QuestionType,ImpactType
from ccchange.models import ProjectChange,QATable
from ccnotes.models import ProjectAttachments

from ccprojects.forms import AddProjectForm,EditProjectForm
from ccmaintainp.models import NonHierarchyAction,NonHierarchyChange

from ccutilities.formutils import FormBuilder as fb
from ccutilities.multiform import MultiFormsView
from ccutilities.utilities import cleanhtml
from ccutilities.reporting_utils import getColorPalette as gcp

from datetime import datetime
from django.utils import timezone as dtz
import time
import json
from rules.contrib.views import PermissionRequiredMixin
import pytz

from pytz import timezone

import os
from django.conf import settings


class ProjectView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccprojects/ccviewprojects.html"
    
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
        context = super(ProjectView, self).get_context_data(**kwargs)
        context['projectdata'] = self.extract_data()
        return(context)

    def post(self, request, *args, **kwargs):

        pypost = request.POST
        pyfile = request.FILES

        if pypost != None:
            for item in pypost:
                if item == 'close_form':
                    self.ProcessProjectClose(pypost,request.user)
                elif item == 'note_text':
                    self.ProcessAddNote(pypost,request.user)


        if pyfile != None:
            for item in pyfile:
                #print(pyfile[item])
                if item == 'file':
                    print("Processing File")
                    self.ProcessFileUpload(pyfile[item])
        
        return(HttpResponseRedirect(reverse_lazy('viewproject')))


    def ProcessProjectClose(self,pypost,requester):

        co = NonHierarchyAction.objects.get(action='close')

        project_id = int(pypost['pid'])

        action_date = datetime.strptime(pypost['close_form'],"%B %d, %Y").strftime("%Y-%m-%d")

        ps = ProjectStructure.objects.get(pk=project_id,userprojects__project_user__user__username=requester)

        # The project already closed
        if not NonHierarchyChange.objects.filter(projectmap=ps,action=co):
            pc = NonHierarchyChange.objects.create(projectmap = ps,
                                                   action = co,
                                                   dateofaction_start=action_date,
                                                   dateofaction_end=None,
                                                   description='Project closure')
        else:
            pass


    def ProcessAddNote(self,pypost,note_user):

        project_id = int(pypost['pid'])

        ps = ProjectStructure.objects.get(pk=project_id,userprojects__project_user__user__username=note_user)

        up = AccountProfile.objects.get(user=note_user)

        pn = ProjectNotes.objects.create(project_structure=ps,
                                         note_type='project',
                                         project_note=pypost['note_text'],
                                         created_by=up)

    def ProcessFileUpload(self,fileupload):

        # Note much of this will have to be moved to a remote server via paramiko (ssh)

        filename = os.path.join(getattr(settings,"BASE_DIR",None),getattr(settings,"FILE_UPLOAD_LOCATION",None),residenttenant())

        if not os.path.isdir(filename):
            # Create folder 
            os.makedirs(name=filename,exist_ok=True)

        fileidentifier = str(self.request.user)+'-'+'P'+self.request.POST['dropzone-hidden-name']+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+self.request.FILES['file'].name
        mimetype = fileupload.content_type

        #print(mimetype)

        filename = os.path.join(filename,residenttenant()+'-'+fileidentifier)
        with open(filename, 'wb+') as destination:
            for chunk in fileupload.chunks():
                destination.write(chunk)

        # Code into DB for later retrieval
        project_id = int(self.request.POST['dropzone-hidden-name'])
        up = AccountProfile.objects.get(user=self.request.user)
        ps = ProjectStructure.objects.get(pk=project_id,userprojects__project_user__user__username=self.request.user)

        ProjectAttachments.objects.create(project_structure=ps,
                                          attachment_name=fileidentifier,
                                          server_location=getattr(settings,"FILE_UPLOAD_SSHSERVER",None),
                                          path_on_server=getattr(settings,"FILE_UPLOAD_LOCATION",None),
                                          mime_type=mimetype,
                                          created_by=up)


        # Land file on filesystem
        # Push file to server
        # Delete file on filesystem if push successful
        # Note this can't be finalised until we are on a server with keys set
        # And we have the second server as a slave filesystem
        # For now I am creating the local structures only
        # The landed file should also be separated into a tenant folder
        # Perhaps do that in code check for it if it exists use it if not create it.

    def extract_data(self):
        
        # Permissions owner and viewer third is closed
        project_list = ProjectStructure.objects.filter(userprojects__project_user__user__username=self.request.user,userprojects__project_perms__viewing_perms__in=["Owner","Viewer"]).order_by('id')

        status_ref = {}

        for itm in ProjectStatus.objects.all():
            status_ref[itm.id] = itm.project_status

        # Get permissions and user details owners only
        # Everything else is a viewer

        owner_list = UserProjects.objects.filter(project_perms__viewing_perms='Owner')
        viewer_name = self.request.user.username

        outlist=[]
        
        for colname in project_list:
            sublist={}
            owner_name = owner_list.filter(projectmap=colname).values('project_user__user__username')[0]['project_user__user__username']
            sublist['id'] = colname.id
            sublist['project_name'] = colname.project_name
            sublist['owner'] = owner_name
            sublist['description'] = colname.description 
            sublist['benefit_desc'] = colname.benefit_desc
            if owner_name==viewer_name:
                sublist['viewer'] = False
            else:
                sublist['viewer'] = True
            sublist['created_on'] = colname.created_on
            sublist['status'] = colname.projectstatus.project_status
            outlist.append(sublist)

        return(outlist)

class ChangeProjectStatus(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    template_name = "ccprojects/ccmodifyprojectstatus.html"
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_success_url(self):
        return(reverse_lazy('viewproject'))

    def get_form_class(self):

        ddict = self.kwargs

        fieldlist = []

        formdict = {}
        choicelist = []
        formdict['name']='projectstatus'
        formdict['label']='Project Status'
        formdict['required']=True
        formdict['type']="select"
        formdict['target']='project'
        formdict['default']=list(ProjectStructure.objects.filter(id=ddict['project_id']).values('projectstatus'))[0]['projectstatus']
        formdict['class']="form-control"
        for a in list(ProjectStatus.objects.all()):
            choicelist.append({"name":a.project_status,"value":a.id})
        formdict['choices']=choicelist
        fieldlist.append(formdict)

        return(fb(fieldlist).return_form())


    def get_context_data(self,**kwargs):
        context = super(ChangeProjectStatus, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['project'] = project_data
        return context

    def extract_data(self):
        ddict = self.kwargs

        return_dict = {}

        ps = ProjectStructure.objects.get(id=ddict['project_id'])

        return_dict['id'] = ddict['project_id']
        return_dict['name'] = ps.project_name
        return_dict['description'] = ps.description

        return return_dict

    def post(self, request, *args, **kwargs):
        # Change project status
        #print(request.POST)

        ps = ProjectStructure.objects.get(id=int(request.POST['projectid']))


        # Is there any requested change?
        # ------------------------------
        if ps.projectstatus.id != int(request.POST['projectstatus']):
            pstat = ProjectStatus.objects.get(id=int(request.POST['projectstatus']))
            ps.projectstatus = pstat
            ps.save()
            messages.success(self.request, 'Status Modified.')
        else:
            messages.warning(self.request, 'No changes applied')

        return HttpResponseRedirect(reverse_lazy('viewproject')) 
        


class AddDetails(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    #template_name = "ccprojects/ccaddprojectquestions.html"
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_template_names(self):
        if self.kwargs['change_target'] == 'project':
            template_name = "ccprojects/ccaddprojectquestions.html"
        elif self.kwargs['change_target'] == 'change':
            # Changing the hierarchy entry method from fancytree to viz.js
            #template_name = "ccprojects/ccaddchangequestions_fix.html"
            #template_name = "ccprojects/ccaddchangequestions_mod_06082019.html"
            template_name = "ccprojects/ccaddchangequestions_mod_19112019.html"

        else:
            raise NameError('Template does not exist')
        return(template_name)

    def get_success_url(self):
        return(reverse_lazy('viewchange',kwargs={'project_id':self.kwargs['project_id']}))

    def get_form_class(self):

        ddict = self.kwargs

        if (ddict['change_target'] == 'project' and "status_flag" in ddict and "project_id" in ddict) or (ddict['change_target'] == 'change' and "project_id" in ddict and "change_id" in ddict):

            fieldlist = []

            if ddict['change_target'] == 'change':
                pc = ProjectChange.objects.get(type_required=(ddict['change_target']).capitalize(),groupkey_id=int(ddict['change_id']))
                qat = list(QATable.objects.filter(impacts=pc).values_list('question_id',flat=True))
            
            if ddict['change_target'] == 'project':
                
                pc = ProjectChange.objects.get(type_required=(ddict['change_target']).capitalize(),projectmap_id=ddict['project_id'])
                qat = list(QATable.objects.filter(impacts=pc).values_list('question_id',flat=True))
                
                # Get hierarchy list
                hr=hierarchy()
                hr_nodes = sorted(hr.get_nodes()['result']['result'],key=lambda k:k['bu'])
                formdict = {}
                choicelist = []
                formdict['name']='sponsors'
                formdict['label']='Sponsor'
                formdict['required']=True
                formdict['type']="select"
                formdict['target']=''
                formdict['default']=list(ProjectStructure.objects.filter(id=ddict['project_id']).values('sponsor_key'))[0]['sponsor_key']
                formdict['class']="multiselect-select-all-filtering form-control"
                for itm in hr_nodes:
                    choicelist.append({"name":itm['bu'],"value":itm['name']})
                formdict['choices']=choicelist
                fieldlist.append(formdict)


            qgroup = list(QuestionGroup.objects.filter(id__in=qat).order_by('type_required__question_type'))
    
            id_dict = self.get_a_list()

            # Project Question Choice control
            for q in qgroup:
                formdict = {}
                choicelist = []
                formdict['name']=q.name
                formdict['label']=q.question
                formdict['required']=True
                formdict['type']="select"
                formdict['target']=self.kwargs['change_target'].title()
                formdict['default']=id_dict[q.name]
                formdict['class']="form-control"
                for a in list(AnswerGroup.objects.filter(question_map_id=q.id)):
                    choicelist.append({"name":a.answers,"value":str(a.id)+'-'+a.answers})
    
                formdict['choices']=choicelist
                fieldlist.append(formdict)


            # Add project defaults
            if self.kwargs['change_target'] == 'project':
                fieldlist.append({"name":"projectname","label":"Name","type":"text","target":"","max_length":"40","required":True,"placeholder":"Project Name","class":"form-control"})
                fieldlist.append({"name":"projectdesc","label":"Description","type":"textarea","target":"","rows":"4","required":True,"placeholder":"Detailed description of project","class":"form-control add_hsnote"})
                fieldlist.append({"name":"benefitdesc","label":"Benefit","type":"textarea","target":"","rows":"4","required":True,"placeholder":"What are the benefits of implementing this project","class":"form-control add_hsnote"})
                fieldlist.append({"name":"customerimpact","label":"Customer Impact","type":"textarea","target":"","rows":"4","required":True,"placeholder":"Description of impact to the customer","class":"form-control add_hsnote"})
                fieldlist.append({"name":"driver","label":"Driver","type":"textarea","target":"","rows":"4","required":True,"placeholder":"What is driving the project","class":"form-control add_hsnote"})


                # Project Status Choice control
                # -----------------------------
                formdict = {}
                choicelist = []
                formdict['name']='projectstatus'
                formdict['label']='Status'
                formdict['required']=True
                formdict['type']="select"
                formdict['target']='project'
                formdict['default']=list(ProjectStructure.objects.filter(id=ddict['project_id']).values('projectstatus'))[0]['projectstatus']
                formdict['class']="form-control"
                for a in list(ProjectStatus.objects.all()):
                    choicelist.append({"name":a.project_status,"value":a.id})
                formdict['choices']=choicelist
                fieldlist.append(formdict)


            # Add change defaults
            if self.kwargs['change_target'] == 'change':

                fieldlist.append({"name":"impactnote","label":"Notes","type":"textarea","target":"","required":False,"placeholder":"Add a note...","rows":4,"class":"form-control add_hsnote"})
                fieldlist.append({"name":"impactstart","label":"Date Start","type":"text","target":"","required":True,"class":"form-control pickadate","htmlid":"datestart","htmlvalue":"None","placeholder":"Start Date"})
                fieldlist.append({"name":"impactend","label":"Date End","type":"text","target":"","required":True,"class":"form-control pickadate","htmlid":"dateend","htmlvalue":"None","placeholder":"End Date"})
                fieldlist.append({"name":"impactnname","label":"Impact Name","type":"text","target":"","max_length":"40","required":False,"class":"form-control","htmlid":"nickname","placeholder":"Enter an impact nickname..."})


        #elif (ddict['change_target'] == 'change' and "project_id") or (ddict['change_target'] == 'project'):
        elif (ddict['change_target'] == 'change') or (ddict['change_target'] == 'project'):
            

            # Restrict to project questions only    
            # ----------------------------------
            qgroup = list(QuestionGroup.objects.filter(active="Yes").order_by('type_required__question_type'))
            qtype = list(QuestionType.objects.values())

            # Get all users except current use for viewing permissions
            # --------------------------------------------------------
            ap = AccountProfile.objects.all().exclude(user=self.request.user)

            # Restrict qgroup to project only
            # -------------------------------
    
            type_required = {}
            for qt in qtype:
                type_required[qt['id']] = qt['question_level']
    
            projectqg = []
            for qg in qgroup:
                if type_required.get(qg.type_required_id) == self.kwargs['change_target'].title(): # String comes through with first letter lowercase
                    projectqg.append(qg)
    
            fieldlist = []
    
            # Question choices field list
            for q in projectqg:
                formdict = {}
                choicelist = []
                formdict['name']=q.name
                formdict['label']=q.question
                formdict['required']=True
                formdict['type']='select'
                formdict['target']=self.kwargs['change_target'].title()
                formdict['default']=''
                formdict['class']='form-control'
                for a in list(AnswerGroup.objects.filter(question_map_id=q.id)):
                    choicelist.append({"name":a.answers,"value":str(a.id)+'-'+a.answers})
    
                formdict['choices']=choicelist
                fieldlist.append(formdict)


            # Add project input fields
            if self.kwargs['change_target'] == 'project':
                fieldlist.append({"name":"projectname","label":"Name","type":"text","target":"","max_length":"40","required":True,"placeholder":"Project Name","class":"form-control"})
                fieldlist.append({"name":"projectdesc","label":"Description","type":"textarea","target":"","rows":"4","required":True,"placeholder":"Detailed description of project","class":"form-control add_hsnote"})
                fieldlist.append({"name":"benefitdesc","label":"Benefit","type":"textarea","target":"","rows":"4","required":True,"placeholder":"What are the benefits of implementing this project","class":"form-control add_hsnote"})
                fieldlist.append({"name":"customerimpact","label":"Customer Impact","type":"textarea","target":"","rows":"4","required":True,"placeholder":"Description of impact to the customer","class":"form-control add_hsnote"})
                fieldlist.append({"name":"driver","label":"Driver","type":"textarea","target":"","rows":"4","required":True,"placeholder":"What is driving the project","class":"form-control add_hsnote"})

                # Project Status Choice control
                # -----------------------------
                formdict = {}
                choicelist = []
                formdict['name']='projectstatus'
                formdict['label']='Status'
                formdict['required']=True
                formdict['type']="select"
                formdict['target']='project'
                formdict['default']=ProjectStatus.objects.get(default=True).id
                formdict['class']="form-control"
                for a in list(ProjectStatus.objects.all()):
                    choicelist.append({"name":a.project_status,"value":a.id})
                formdict['choices']=choicelist
                fieldlist.append(formdict)


                hr=hierarchy()
                hr_nodes = sorted(hr.get_nodes()['result']['result'],key=lambda k:k['bu'])
                formdict = {}
                choicelist = []
                formdict['name']='sponsors'
                formdict['label']='Sponsor'
                formdict['required']=True
                formdict['type']="select"
                formdict['target']=''
                formdict['default']=hr.get_rootnode().split('/')[1]
                formdict['class']="multiselect-select-all-filtering form-control"
                for itm in hr_nodes:
                    choicelist.append({"name":itm['bu'],"value":itm['name']})
                formdict['choices']=choicelist
                fieldlist.append(formdict)


                # Add new sponsor field

            # Add change input fields
            if self.kwargs['change_target'] == 'change':

                fieldlist.append({"name":"impactnote","label":"Notes","type":"textarea","target":"","required":False,"placeholder":"Add a note...","rows":4,"class":"form-control add_hsnote"})
                fieldlist.append({"name":"impactstart","label":"Date Start","type":"text","target":"","required":True,"class":"form-control pickadate","htmlid":"datestart","htmlvalue":"None","placeholder":"Start Date"})
                fieldlist.append({"name":"impactend","label":"Date End","type":"text","target":"","required":True,"class":"form-control pickadate","htmlid":"dateend","htmlvalue":"None","placeholder":"End Date"})
                fieldlist.append({"name":"impactnname","label":"Impact Name","type":"text","target":"","max_length":"40","required":False,"class":"form-control","htmlid":"nickname","placeholder":"Enter an impact nickname..."})



        else:
            raise ValueError('Unknown URL paramters')

        return fb(fieldlist).return_form()

    def get_context_data(self,**kwargs):
        context = super(AddDetails, self).get_context_data(**kwargs)
        project_data = self.extract_data()

        context['project_category_labels'] = project_data['project_category_labels']
        context['change_category_labels'] = project_data['change_category_labels']

        if 'hierarchy' in project_data:
            context['treeview'] = project_data['hierarchy']
        if 'hierarchy_selected' in project_data:
            context['tree_selected'] = project_data['hierarchy_selected']
        if 'project_name' in project_data:
            context['project_name'] = project_data['project_name']
        if 'description' in project_data:
            context['description'] = project_data['description']
        if 'benefit_desc' in project_data:
            context['benefit_desc'] = project_data['benefit_desc']
        if 'driver' in project_data:
            context['driver'] = project_data['driver']
        if 'customer_impact' in project_data:
            context['customer_impact'] = project_data['customer_impact']
        if 'vperms' in project_data:
            context['vperms'] = project_data['vperms']
        if 'l5_impact_code' in project_data:
            context['l5_impact_code'] = project_data['l5_impact_code']
            context['check_impacts'] = 'Yes'
        if 'impactstart' in project_data:
            context['impactstart'] = project_data['impactstart']
        if 'impactend' in project_data:
            context['impactend'] = project_data['impactend']
        if 'impactnname' in project_data:
            context['impactnname'] = project_data['impactnname']
        if 'impactnote' in project_data:
            context['impactnote'] = project_data['impactnote']
        if 'impacttypelist' in project_data:
            context['impacttype'] = project_data['impacttypelist']
        if 'nicknames' in project_data:
            context['nicknames'] = project_data['nicknames']
        if 'impactampp' in project_data:
            context['impactampp'] = project_data['impactampp']
        if 'pid' in project_data:
            context['pid'] = project_data['pid']
        if 'recreq' in project_data:
            context['tsresourcesmax'] = project_data['recreq']
        if 'recselected' in project_data:
            context['recselected'] = project_data['recselected']
        if 'nodes' in project_data:
            context['nodes'] = project_data['nodes']
        if 'edges' in project_data:
            context['edges'] = project_data['edges'] 
        if 'label_length' in project_data:
            context['label_length'] = project_data['label_length'] 
        return(context)

    def get_sponsors(self,requires_default):
        ddict = self.kwargs
        print(ddict)

        hr = hierarchy()

        hr_nodes = sorted(hr.get_nodes()['result'],key=lambda k:k['bu'])

        if requires_default:
            hr_default = ProjectStructure.objects.get(id=int(ddict['project_id'])).sponsor_key

        outlist = []
        for org in hr_nodes:
            subdict = {}
            if requires_default:
                if org['name']==hr_default:
                    subdict['select_option'] = '<option value="'+org['name']+'" selected="selected">'+org['bu']+'-'+org['name']+'</option>'
                else:
                    subdict['select_option'] = '<option value="'+org['name']+'">'+org['bu']+'-'+org['name']+'</option>'
            else:
                subdict['select_option'] = '<option value="'+org['name']+'">'+org['bu']+'-'+org['name']+'</option>'
            outlist.append(subdict)

        return outlist


    def get_impacttypes(self,required_type,requires_default):
        ddict = self.kwargs

        ipt = ImpactType.objects.filter(type_required=required_type)

        if requires_default:
            if required_type == 'Change':
                hr_default = ProjectChange.objects.get(groupkey_id = int(ddict['change_id'])).impact_type_id
            else:
                hr_default = ProjectStructure.objects.get(id = int(ddict['project_id'])).impact_type_id

        outlist = []
        for itm in ipt:
            subdict = {}
            if requires_default:
                if itm.id==hr_default:
                    subdict['select_option'] = '<option value="'+str(itm.id)+'" selected="selected">'+itm.impact_type+'</option>'
                else:
                    subdict['select_option'] = '<option value="'+str(itm.id)+'">'+itm.impact_type+'</option>'
            else:
                subdict['select_option'] = '<option value="'+str(itm.id)+'">'+itm.impact_type+'</option>'
            outlist.append(subdict)

        return outlist


    def extract_data(self):
        # This line added for security the user and the project id must match otherwise the project will not load
        # Note no changes for permissions yet
        #ps = ProjectStructure.objects.filter(pk=project_id,userprojects__project_user__user__username=self.request.user)
        ddict = self.kwargs

        return_dict = {}

        pqg = list(QuestionGroup.objects.filter(type_required__question_level='Project').order_by('type_required__question_type').values('name','type_required__question_type'))
        cqg = list(QuestionGroup.objects.filter(type_required__question_level='Change').order_by('type_required__question_type').values('name','type_required__question_type'))

        pqg_label_order = {}
        keep_itm = ''
        for itm in pqg:
            if keep_itm != itm['type_required__question_type']:
                pqg_label_order['proj_'+itm['name']] = '<div><legend class="text-semibold">'+itm['type_required__question_type']+'</legend></div>'
                keep_itm = itm['type_required__question_type']
            else:
                pqg_label_order['proj_'+itm['name']] = ''

        cqg_label_order = {}
        keep_itm = ''
        for itm in cqg:
            if keep_itm != itm['type_required__question_type']:
                cqg_label_order['chan_'+itm['name']] = '<div><legend class="text-semibold">'+itm['type_required__question_type']+'</legend></div>'
                keep_itm = itm['type_required__question_type']
            else:
                cqg_label_order['chan_'+itm['name']] = ''

        return_dict['project_category_labels'] = pqg_label_order
        return_dict['change_category_labels'] = cqg_label_order

        # Modify existing project
        # -----------------------
        if ddict['change_target'] == 'project' and "status_flag" in ddict and "project_id" in ddict:
            print("Modify Existing Project")
            ps = ProjectStructure.objects.get(pk=int(ddict['project_id']))

            # Impact Type
            # --------
            return_dict['impacttypelist'] = self.get_impacttypes('Project',True)

            
            return_dict['project_name'] = ps.project_name
            return_dict['description'] = ps.description
            return_dict['benefit_desc'] = ps.benefit_desc
            return_dict['driver'] = ps.driver
            return_dict['customer_impact'] = ps.customer_impact


            # Get all users - add selected to those already selected
            # ------------------------------------------------------
            ap = AccountProfile.objects.all().exclude(user=self.request.user).values('user__id','user__username','user__first_name','user__last_name','department','job_title')

            po = ViewPerms.objects.filter(viewing_perms__in=["Owner","closed"])

            up = list(UserProjects.objects.filter(projectmap_id=int(ddict['project_id'])).exclude(project_perms__in=po).exclude(project_user__user=self.request.user).values('project_user__user'))

            usrlist = []
            for usr in up:
                usrlist.append(usr['project_user__user'])

            outlist = []
            for usr in ap:
                subdict = {}
                if usr['user__id'] in usrlist:
                    subdict['select_option'] = '<option value="'+str(usr['user__id'])+'" selected="selected">'+str(usr['user__username'])+' - '+str(usr['user__first_name'])+' '+str(usr['user__last_name'])+' - '+str(usr['department'])+' - '+str(usr['job_title'])+'</option>'
                else:
                    subdict['select_option'] = '<option value="'+str(usr['user__id'])+'">'+str(usr['user__username'])+' - '+str(usr['user__first_name'])+' '+str(usr['user__last_name'])+' - '+str(usr['department'])+' - '+str(usr['job_title'])+'</option>'
                outlist.append(subdict)

            return_dict['vperms'] = outlist

        # Modify existing impact
        # ----------------------
        elif ddict['change_target'] == 'change' and "project_id" in ddict and "change_id" in ddict:
            print("Modify Existing Impact")

            # Impact Type
            # --------
            return_dict['impacttypelist'] = self.get_impacttypes('Change',True)


            ps = ProjectStructure.objects.get(pk=int(ddict['project_id']))

            # Hierarchy
            # ---------
            return_dict['hierarchy'] = hierarchy().ul_render()

            print('bob')
            print(ddict['project_id'])
            print(type(ddict['project_id']))
            print(ddict['change_id'])
            print(type(ddict['change_id']))

            # Hierarchy Selected
            # ------------------
            hv = hierarchy().get_selected(int(ddict['project_id']),int(ddict['change_id']))

            hv_list = {}
            for item in hv:
                for cd in item['change_data']:
                    if cd['change_pk'] in hv_list:
                        # Note remove this after db repair
                        if cd['resources'] == None:
                            rec = 1
                        else:
                            rec = cd['resources']
                        hv_list[cd['change_pk']].append({'id':item['id'],'resources':rec})
                    else:
                        # Note remove this after db repair
                        if cd['resources'] == None:
                            rec = 1
                        else:
                            rec = cd['resources']
                        hv_list[cd['change_pk']]=[]
                        hv_list[cd['change_pk']].append({'id':item['id'],'resources':rec})


            return_dict['hierarchy_selected'] = json.dumps(hv_list[int(ddict['change_id'])])


            # Dates
            # -----
            pc = ProjectChange.objects.filter(projectmap=ps,type_required='Change',groupkey_id=ddict['change_id']).values('start_date','end_date','nickname','ampp').annotate(Count('id'))[0]

            impactstart = pc['start_date'].strftime('%B %d, %Y')
            impactend = pc['end_date'].strftime('%B %d, %Y')

            return_dict['impactstart'] = impactstart
            return_dict['impactend'] = impactend

            # Impact nickname
            # ---------------
            return_dict['impactnname'] = pc['nickname']

            return_dict['impactampp'] = pc['ampp']

            # Change note
            # -----------
            pn = ProjectNotes.objects.filter(project_structure=ps,note_type='change').order_by('-created_on')[:1].values()[0]

            return_dict['impactnote'] = pn['project_note']

            return_dict['pid'] = ddict['project_id']

            # Resources Required
            # ------------------

            # WORKING HERE ----------------------
            return_dict['recreq'] = hierarchy().query_hierarchy(query = 'for doc in _businessUnit FILTER doc.date_deleted == null return {name:doc.name,resources:doc.resource_count}')['result']['result']
            
            nodesedges = getNodesEdges()

            return_dict['nodes'] = nodesedges['nodes']
            return_dict['edges'] = nodesedges['edges']
            return_dict['label_length'] = nodesedges['label_length']


        # Add new existing
        # ----------------
        elif ddict['change_target'] == 'change' and "project_id" in ddict:
            print("Add New Impact")
            return_dict['hierarchy'] = hierarchy().ul_render()
            return_dict['hierarchy_selected'] = json.dumps([])

            # Impact type
            return_dict['impacttypelist'] = self.get_impacttypes('Change',False)


            # Get last five impacts
            # ---------------------

            ps = ProjectStructure.objects.get(pk=int(ddict['project_id']))
            return_dict['project_name'] = ps.project_name
            pc = ProjectChange.objects.filter(projectmap=ps,type_required='Change',inactive_date=None).values('projectmap__project_name','nickname','start_date','end_date','confirmed__confirmed','groupkey_id').annotate(Count('id')).order_by('-groupkey_id')[:5]

            outlist = []
            for itm in pc:
                indict = {}

                indict['l5_impact_code'] = 'itable.row.add(["'+itm['projectmap__project_name']+'","'+itm['nickname']+'","'+itm['start_date'].strftime('%d-%m-%Y')+'","'+itm['end_date'].strftime('%d-%m-%Y')+'","'+itm['confirmed__confirmed']+'"]).draw();'

                outlist.append(indict)

            return_dict['l5_impact_code'] = outlist

            # Resources Required
            # ------------------

            # WORKING HERE ----------------------
            return_dict['recreq'] = hierarchy().query_hierarchy(query = 'for doc in _businessUnit FILTER doc.date_deleted == null return {name:doc.name,resources:doc.resource_count}')['result']['result']
            # -----------------------------------

            nodesedges = getNodesEdges()

            return_dict['nodes'] = nodesedges['nodes']
            return_dict['edges'] = nodesedges['edges']
            return_dict['label_length'] = nodesedges['label_length']




        # Add new project
        # ---------------
        elif ddict['change_target'] == 'project':
            print('Add new Project')
            return_dict['project_name'] = ''
            return_dict['description'] = ''
            return_dict['benefit_desc'] = ''
            return_dict['driver'] = ''
            return_dict['customer_impact'] = ''
            return_dict['impacttypelist'] = self.get_impacttypes('Project',False)


            # Get all users
            # -------------
            ap = AccountProfile.objects.filter(user__is_active=True).exclude(user=self.request.user).values('user__id','user__username','user__first_name','user__last_name','department','job_title')

            outlist = []
            for usr in ap:
                subdict = {}
                subdict['select_option'] = '<option value="'+str(usr['user__id'])+'">'+str(usr['user__username'])+' - '+str(usr['user__first_name'])+' '+str(usr['user__last_name'])+' - '+str(usr['department'])+' - '+str(usr['job_title'])+'</option>'
                outlist.append(subdict)

            return_dict['vperms'] = outlist

        else:
            raise ValueError('Unknown URL paramters')


        if ddict['change_target'] == 'change':
            return_dict['nicknames'] = json.dumps(list(ProjectChange.objects.filter(type_required='Change').values_list('nickname',flat=True).distinct()))

        return(return_dict)

    def post(self, request, *args, **kwargs):

        # Set zone to UTC - incoming dates are UTC (from the browser already converted)
        utc = pytz.utc
        ddict = self.kwargs

        browser_tz = timezone(request.POST["browser-timezone-name"])
        

        # Modify existing project
        # -----------------------
        if ddict['change_target'] == 'project' and "status_flag" in ddict and "project_id" in ddict:
            print("Modify Existing Project")

            # Is the name of the current project staying
            # ------------------------------------------
            pc_name = ProjectStructure.objects.filter(pk=int(ddict['project_id'])).values('project_name')[0]['project_name']

            pc = ProjectStructure.objects.filter(project_name = request.POST["projectname"]).count()

            if pc == 0 or request.POST["projectname"] == pc_name:

                ps = ProjectStatus.objects.get(id=request.POST['projectstatus'])

                pt = ImpactType.objects.get(id=int(request.POST['impacttype']),type_required='Project')

                # Update project details
                # ----------------------
                ProjectStructure.objects.filter(pk=int(ddict['project_id'])).update(project_name = request.POST["projectname"],
                                                                                           description = cleanhtml(request.POST["projectdesc"]),
                                                                                           driver = cleanhtml(request.POST["driver"]),
                                                                                           benefit_desc = cleanhtml(request.POST["benefitdesc"]),
                                                                                           customer_impact = cleanhtml(request.POST["customerimpact"]),
                                                                                           impact_type = pt,
                                                                                           projectstatus = ps,
                                                                                           sponsor_key = request.POST["sponsors"])



                # Update permission details
                # -------------------------
                pv = ViewPerms.objects.get(viewing_perms="Viewer")
                cp = ProjectStructure.objects.get(pk=int(ddict['project_id']))

                UserProjects.objects.filter(projectmap=cp,project_perms=pv).delete()

                # Add viewing permissions to selected
                # -----------------------------------
                pv = ViewPerms.objects.get(viewing_perms="Viewer")

                for perm in request.POST.getlist('viewperm'):
                    up = AccountProfile.objects.get(user=perm)
                    UserProjects.objects.create(projectmap=cp,project_user=up,project_perms=pv).save()


                # Update questions
                # ----------------
                # Add project level q/a
                # ---------------------
    
                pc = ProjectChange.objects.get(type_required=(ddict['change_target']).capitalize(),projectmap_id=ddict['project_id'])
                qat = list(QATable.objects.filter(impacts=pc).values_list('question_id',flat=True))

                qgroup = list(QuestionGroup.objects.filter(pk__in=qat,type_required__question_level="Project"))

                ps = ProjectStructure.objects.get(pk=int(ddict['project_id']))

                pc.start_date=datetime.now()
                pc.end_date=datetime.now()
                pc.save()

                for q in qgroup:
                    qa_identifier = 'proj_'+q.name   
                    ag = AnswerGroup.objects.get(id=request.POST[qa_identifier].split('-')[0])
                    qat = QATable.objects.filter(impacts=pc,question=q).update(answers=ag)

                messages.success(self.request, 'Project Updated successfully.')

                if 'editprojectbtn' in self.request.POST:
                    return(HttpResponseRedirect(reverse_lazy('addnewimpact',kwargs={'change_target':'change','project_id':int(ddict['project_id'])})))

            else:
                messages.error(self.request, 'That is an existing project. Choose a different name.')
                return HttpResponseRedirect(reverse_lazy('modifyproject',kwargs=ddict)) 

        # Modify existing impact
        # ----------------------
        elif ddict['change_target'] == 'change' and "project_id" in ddict and "change_id" in ddict:
            print("Modify Existing Impact")

            print(request.POST)

            # Modify Questions
            # ----------------
            pc = ProjectChange.objects.get(type_required=(ddict['change_target']).capitalize(),groupkey_id=int(ddict['change_id']),projectmap_id=int(ddict['project_id']))
            qat = list(QATable.objects.filter(impacts=pc).values_list('question_id',flat=True))

            qgroup = list(QuestionGroup.objects.filter(pk__in=qat,type_required__question_level="Change"))

            ps = ProjectStructure.objects.get(pk=int(ddict['project_id']))

            it = ImpactType.objects.get(id=int(request.POST['impacttype']),type_required='Change')

            # Modify average minutes per person
            ampp = int(request.POST['ammp-estimate'])
            
            # Modify Dates
            # ------------
            start_date = utc.localize(datetime.utcfromtimestamp(int(request.POST['impact-start-name'])/1000)).astimezone(browser_tz)
            end_date = utc.localize(datetime.utcfromtimestamp(int(request.POST['impact-end-name'])/1000)).astimezone(browser_tz)

            pc.start_date=start_date
            pc.end_date=end_date
            pc.impact_type=it
            pc.ampp=ampp


            pc.save()

            for q in qgroup:
                qa_identifier = 'chan_'+q.name   
                ag = AnswerGroup.objects.get(id=request.POST[qa_identifier].split('-')[0])
                qat = QATable.objects.filter(impacts=pc,question=q).update(answers=ag)

            # Modify Impact Name
            # ------------------
            nickerror = False
            if request.POST['impactnname'] != '':
                nickname = request.POST['impactnname']
                pc = ProjectChange.objects.filter(type_required='Change',groupkey_id=ddict['change_id']).values('nickname').annotate(Count('id'))[0]
                nc = ProjectChange.objects.filter(nickname = nickname).count()

                if nc==0:
                    ProjectChange.objects.filter(groupkey = int(ddict['change_id']),type_required = "Change").update(nickname=nickname)
                else:
                    if nickname != pc['nickname']:
                        nickerror = True 

            # Modify Impact Note
            # ------------------
            up = AccountProfile.objects.get(user=request.user)

            cp = ProjectStructure.objects.get(pk=int(ddict['project_id']))

            pn = ProjectNotes.objects.filter(project_structure=cp,note_type='change').update(project_note=cleanhtml(request.POST['impactnote']))

            # Modify Hierarchy
            # ----------------
            hv_current = hierarchy().get_selected(int(ddict['project_id']),int(ddict['change_id']))

            hv_current_list = []
            for item in hv_current:
                hv_current_list.append(item['id'])

            hv_new_list_group = json.loads(request.POST['hierarchy'])

            hv_new_list = []
            for item in hv_new_list_group:
                hv_new_list.append(item['buid'])

            hv_current_list.sort()
            hv_new_list.sort()

            # Hierarchy changed or sponsor different
            if hv_current_list != hv_new_list: #or current_sponsorname != sponsorname:
                # Add inactive date to old hierarchy members

                if hv_new_list:
                    del_old_hier = hierarchy().make_inactive(int(ddict['project_id']),int(ddict['change_id']))
                    for item in hv_new_list_group:
                        hierarchy().add_change_data(int(ddict['project_id']),item['buid'],int(ddict['change_id']),item['resources'],int(request.POST['impact-start-name'])/1000,int(request.POST['impact-end-name'])/1000) 
                else:
                    print('Nothing in hierarchy')  

            if nickerror==False:
                messages.success(self.request,'Impact changed successfully')
            else:
                messages.info(self.request,'The chosen nickname already exists, all other items changed successfully.')


        # Add new impact
        # ----------------
        elif ddict['change_target'] == 'change' and "project_id" in ddict:
            print("Add New Impact")

            

            cp = ProjectStructure.objects.get(pk=int(ddict['project_id']))

            # Localize to UTC universal time
            start_date = utc.localize(datetime.utcfromtimestamp(int(request.POST['impact-start-name'])/1000)).astimezone(browser_tz)
            end_date = utc.localize(datetime.utcfromtimestamp(int(request.POST['impact-end-name'])/1000)).astimezone(browser_tz)

            ampp = int(request.POST['ammp-estimate'])

            cfm = Confirmed.objects.get(confirmed='No')

            qgroup = list(QuestionGroup.objects.filter(active="Yes",type_required__question_level="Change"))

            gk = HinyangoGroupKey.objects.create()

            cfm = Confirmed.objects.get(confirmed="No")

            it = ImpactType.objects.get(id=int(request.POST['impacttype']),type_required='Change')

            nickname = None

            # Is nickname in post
            # -------------------
            if request.POST['impactnname'] != '':
                nickname = request.POST['impactnname']

            nc = 0
            
            if nickname:
                # nickname on project could be changed
                nc = ProjectChange.objects.filter(nickname = nickname).count()

            if request.POST['hierarchy']:
                if nc == 0:
                    pc = ProjectChange.objects.create(projectmap = cp,
                                                      groupkey = gk, 
                                                      type_required = "Change",
                                                      confirmed = cfm,
                                                      nickname = nickname,
                                                      start_date = start_date, 
                                                      end_date = end_date,
                                                      ampp = ampp,
                                                      impact_type=it,
                                                      propogate = True)

                    for q in qgroup:
                        qa_identifier = 'chan_'+q.name   
                        ag = AnswerGroup.objects.get(id=request.POST[qa_identifier].split('-')[0])
                        qat = QATable.objects.create(impacts=pc,question=q,answers=ag)
        
                    # Add details to the hierarchy
                    # ----------------------------
                    hr = hierarchy()
    
                    for item in json.loads(request.POST['hierarchy']):
                        hr.add_change_data(ddict['project_id'],item['buid'],gk.id,item['resources'],int(request.POST['impact-start-name'])/1000,int(request.POST['impact-end-name'])/1000)
        
                    # Add change note
                    # ---------------
                    up = AccountProfile.objects.get(user=request.user)
        
                    pn = ProjectNotes.objects.create(project_structure=cp,
                                                     note_type='change',
                                                     project_note=cleanhtml(request.POST['impactnote']),
                                                     created_by=up)
        
        
                    messages.success(self.request,'Impact added successfully')
                else:
                    messages.error(self.request,'That impact Nickname already exists')
            else:
                messages.error(self.request,'At least one business unit in the organisation must be selected')



            return HttpResponseRedirect(reverse_lazy('addnewimpact',kwargs={'project_id':ddict['project_id'],'change_target':'change'})) 
        # Add new project
        # ---------------
        elif ddict['change_target'] == 'project':
            print('ADD NEW PROJECT')
            # Check that the project doesn't exist
            # ------------------------------------
            pc = ProjectStructure.objects.filter(project_name = request.POST["projectname"]).count()

            if pc == 0:
                # Add the valid project
                # ---------------------

                pt = ImpactType.objects.get(id=int(request.POST['impacttype']),type_required='Project')

                ps = ProjectStatus.objects.get(id=request.POST['projectstatus'])

                cp = ProjectStructure.objects.create(project_name = request.POST["projectname"],
                                                     description = cleanhtml(request.POST["projectdesc"]),
                                                     driver = cleanhtml(request.POST["driver"]),
                                                     benefit_desc = cleanhtml(request.POST["benefitdesc"]),
                                                     customer_impact = cleanhtml(request.POST["customerimpact"]),
                                                     impact_type = pt,
                                                     projectstatus = ps,
                                                     sponsor_key = request.POST["sponsors"]).save()

                cp = ProjectStructure.objects.get(project_name = request.POST["projectname"])
    
                # Get current user object
                # -----------------------
                up = AccountProfile.objects.get(user=request.user)
    
                # # Return newly created project object
                # # ------------------------------------
                #cp = ProjectStructure.objects.get(project_name=form.cleaned_data["projectname"])
    
    
                # Return a permission object 'Owner'
                # ----------------------------------
                po = ViewPerms.objects.get(viewing_perms="Owner")
    
                
                # Set new project permissions to owner
                # ------------------------------------
                gu = UserProjects.objects.create(projectmap=cp,project_user=up,project_perms=po)
                
                # Save project
                # ------------
                gu.save()
    
                # Add viewing permissions to selected
                # -----------------------------------
                pv = ViewPerms.objects.get(viewing_perms="Viewer")

                for perm in request.POST.getlist('viewperm'):
                    up = AccountProfile.objects.get(user=perm)
                    UserProjects.objects.create(projectmap=cp,project_user=up,project_perms=pv).save()
    
                # Add project level q/a
                # ---------------------
    
                qgroup = list(QuestionGroup.objects.filter(active="Yes",type_required__question_level="Project"))

                # Perhaps this should be made obsolete the project id can now be used for this 
                # Mark it for future removal 
                gk = HinyangoGroupKey.objects.create()

                cfm = Confirmed.objects.get(confirmed="Yes")

                pck = ProjectChange.objects.create(projectmap = cp,
                                                   groupkey = gk, 
                                                   type_required = "Project",
                                                   confirmed = cfm,
                                                   nickname = None,
                                                   start_date = datetime.now(), 
                                                   end_date = datetime.now(),
                                                   ampp = 0, 
                                                   impact_type = pt,
                                                   propogate = True)

                for q in qgroup:
                    qa_identifier = 'proj_'+q.name
                    ag = AnswerGroup.objects.get(id=request.POST[qa_identifier].split('-')[0])
                    QATable.objects.create(question=q,answers=ag,impacts=pck)

                messages.success(self.request,'Project added successfully')

                if 'editprojectbtn' in self.request.POST:
                    return HttpResponseRedirect(reverse_lazy('addnewimpact',kwargs={'change_target':'change','project_id':cp.id}))
            else:

                messages.error(self.request, 'The project already exists. Choose a different name.')
                return HttpResponseRedirect(reverse_lazy('addnewproject',kwargs={'change_target':'project'}))

        else:
            raise ValueError('Unknown URL paramters')

        if 'group_target' in ddict:
            return HttpResponseRedirect(reverse_lazy('viewimpacts',kwargs={'project_id':ddict['project_id']}))
        else:
            return HttpResponseRedirect(reverse_lazy('viewproject'))

    def get_a_list(self):
        ddict = self.kwargs
        if ddict['change_target'] == 'change':
            #cgroup = list(ProjectChange.objects.filter(type_required=(ddict['change_target']).capitalize(),groupkey_id=ddict['change_id']).values('question_id','answers_id'))
            pc = ProjectChange.objects.get(type_required=(ddict['change_target']).capitalize(),groupkey_id=ddict['change_id'])
            qat = list(QATable.objects.filter(impacts=pc).values('question_id','answers_id'))

        if ddict['change_target'] == 'project':
            #cgroup = list(ProjectChange.objects.filter(type_required=(ddict['change_target']).capitalize(),projectmap_id=ddict['project_id']).values('question_id','answers_id'))
            pc = ProjectChange.objects.get(type_required=(ddict['change_target']).capitalize(),projectmap_id=ddict['project_id'])
            qat = list(QATable.objects.filter(impacts=pc).values('question_id','answers_id'))
            
        udict = {}
        for item in qat:
            udict[item['question_id']]=item['answers_id']

        agroup = list(AnswerGroup.objects.filter(id__in=list(udict.values())).values())
        qgroup = list(QuestionGroup.objects.filter(id__in=list(udict.keys())).values())

        # Create dict with id_both_<<question>>:<<id>>-<<answers>>
        q_dict = {}
        for item in qgroup:
            q_dict[item['id']]=item['name']

        a_dict = {}
        for item in agroup:
            a_dict[item['id']]=item['answers']      

        id_dict = {}
        for k,v in udict.items():
            id_dict[q_dict[k]] = str(v)+'-'+a_dict[v]

        return id_dict

    # def getNodesEdges(self):
    #     # Get Hierarchy Data Need Nodes (including label)
    #     # Edges 
    #     # Levels for user defined hierarchy display

    #     levels = hierarchy().get_level_data()['levels_nodes_id']

    #     resources = hierarchy().query_hierarchy(query = 'for doc in _businessUnit FILTER doc.date_deleted == null return {name:doc.name,resources:doc.resource_count}')['result']['result']
    #     single_rec_dict = {}
    #     for itm in resources:
    #         single_rec_dict[itm['name']] = itm['resources']

    #     colors = gcp(len(hierarchy().get_level_data()['node_levels'].keys())).getHexList()

    #     nodes = hierarchy().get_nodes()['result']['result']
    #     node_list = []
    #     node_copy = {}
    #     largest_label = 0
    #     for num,itm in enumerate(nodes):
    #         if len(itm['bu']) > largest_label:
    #             largest_label = len(itm['bu'])
    #         node_list.append(json.dumps({'id':num,'label':itm['bu'],'level':levels[itm['name']],'shape':'box','shapeProperties':{'borderDashes':[0,0]},'borderWidth': 1,'color':{'border': colors[levels[itm['name']]][0],'background': colors[levels[itm['name']]][1]},'buid':itm['name'],'resources':single_rec_dict[itm['name']],'recrequired':0}))
    #         node_copy[itm['name']] = num

    #     edges = hierarchy().get_edges()['result']['result']
    #     edge_list = []
    #     for itm in edges:
    #         edge_list.append(json.dumps({'from':node_copy[itm['from'].split('/')[1]],'to':node_copy[itm['to'].split('/')[1]]}))

    #     return {'nodes':node_list,'edges':edge_list,'label_length':largest_label}


class ImpactView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccprojects/ccviewimpacts.html"
    
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
        context = super(ImpactView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['impactdata'] = project_data['changeobjects']
        context['pid'] = project_data['project']
        context['tsresourcesmax'] = project_data['recreq']

        context['nodes'] = project_data['nodes']
        context['edges'] = project_data['edges']
        context['label_length'] = project_data['label_length']

        return(context)

    def post(self, request, *args, **kwargs):
        pass

    def extract_data(self):
        ddict = self.kwargs
        return_dict = {}
        ps = ProjectStructure.objects.get(id = ddict['project_id'])
        pc = ProjectChange.objects.filter(type_required = 'Change',projectmap = ps,inactive_date = None).values('id','nickname','ampp','start_date','end_date','confirmed__confirmed','impact_type__impact_type','groupkey_id')
        
        return_dict['changeobjects'] = pc
        return_dict['project'] = ddict['project_id']

        return_dict['recreq'] = hierarchy().query_hierarchy(query = 'for doc in _businessUnit FILTER doc.date_deleted == null return {name:doc.name,resources:doc.resource_count}')['result']['result']
            
        nodesedges = getNodesEdges()

        return_dict['nodes'] = nodesedges['nodes']
        return_dict['edges'] = nodesedges['edges']
        return_dict['label_length'] = nodesedges['label_length']

        return return_dict


# URL data response only view
class Hierarchy_Data(LoginRequiredMixin,PermissionRequiredMixin,View):

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
        post = json.loads(request.POST['output'])

        if post['output']['request'] == 'get-hierarchy':
            gid = post['output']['data']['id']
            print(gid)
            print(type(gid))
            pid = post['output']['data']['pid']

            hv = hierarchy().get_selected(pid,gid)

            hv_list = {}
            for item in hv:
                for cd in item['change_data']:
                    if cd['change_pk'] in hv_list:
                        hv_list[cd['change_pk']].append({'id':item['id'],'resources':cd['resources']})
                    else:
                        hv_list[cd['change_pk']]=[]
                        hv_list[cd['change_pk']].append({'id':item['id'],'resources':cd['resources']})

            return JsonResponse({'outcome':'success','message':{'selected':hv_list[gid]}},safe=False)
        else:
            gid = post['output']['data']['id']
            pid = post['output']['data']['pid']
            pc = ProjectChange.objects.filter(groupkey_id=gid)
            pc.update(inactive_date=dtz.now()) # Change this to inactive
            # Delete hierarchy for change
            del_old_hier = hierarchy().make_inactive(int(pid),int(gid))

            return JsonResponse({'result':'receipt','outcome':'success','message':'Success'})


class ImpactConfirmed(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    template_name = "ccprojects/ccmodifyconfirmed.html"
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_form_class(self):

        ddict = self.kwargs

        pc = ProjectChange.objects.get(groupkey_id=ddict['change_id'])
        cl = Confirmed.objects.all()

        fieldlist = []

        formdict = {}
        choicelist = []
        formdict['name']='confirmimpact'
        formdict['label']='Impact Confirmation'
        formdict['required']=True
        formdict['type']="select"
        formdict['target']=''
        formdict['default']=pc.confirmed_id
        formdict['class']="form-control"
        for itm in cl:
            choicelist.append({"name":itm.confirmed,"value":itm.id})
        formdict['choices']=choicelist
        fieldlist.append(formdict)

        return(fb(fieldlist).return_form())


    def get_context_data(self,**kwargs):
        context = super(ImpactConfirmed, self).get_context_data(**kwargs)
        print(self.kwargs)
        project_data = self.extract_data()
        context['project'] = project_data
        return context

    def extract_data(self):
        ddict = self.kwargs

        return_dict = {}

        ps = ProjectStructure.objects.get(id=ddict['project_id'])
        pc = ProjectChange.objects.get(groupkey_id=ddict['change_id'])

        return_dict['id'] = ddict['project_id']
        return_dict['name'] = ps.project_name
        return_dict['description'] = ps.description
        return_dict['cid'] = ddict['change_id']
        return_dict['nickname']=pc.nickname
        return return_dict

    def post(self, request, *args, **kwargs):
        ddict = self.kwargs
        post = request.POST['confirmimpact']

        pc = ProjectChange.objects.get(groupkey_id=ddict['change_id'])
        cl = Confirmed.objects.get(id=post)

        pc.confirmed=cl
        pc.save()

        
        return HttpResponseRedirect(reverse_lazy('viewimpacts',kwargs={'project_id':ddict['project_id']}))


# Get nodes and edges function
# ----------------------------

def getNodesEdges():
    # Get Hierarchy Data Need Nodes (including label)
    # Edges 
    # Levels for user defined hierarchy display

    levels = hierarchy().get_level_data()['levels_nodes_id']

    resources = hierarchy().query_hierarchy(query = 'for doc in _businessUnit FILTER doc.date_deleted == null return {name:doc.name,resources:doc.resource_count}')['result']['result']
    single_rec_dict = {}
    for itm in resources:
        single_rec_dict[itm['name']] = itm['resources']

    colors = gcp(len(hierarchy().get_level_data()['node_levels'].keys())).getHexList()

    nodes = hierarchy().get_nodes()['result']['result']
    node_list = []
    node_copy = {}
    largest_label = 0
    for num,itm in enumerate(nodes):
        if len(itm['bu']) > largest_label:
            largest_label = len(itm['bu'])
        node_list.append(json.dumps({'id':num,'label':itm['bu'],'level':levels[itm['name']],'shape':'box','shapeProperties':{'borderDashes':[0,0]},'borderWidth': 1,'color':{'border': colors[levels[itm['name']]][0],'background': colors[levels[itm['name']]][1]},'buid':itm['name'],'resources':single_rec_dict[itm['name']],'recrequired':0}))
        node_copy[itm['name']] = num

    edges = hierarchy().get_edges()['result']['result']
    edge_list = []
    for itm in edges:
        edge_list.append(json.dumps({'from':node_copy[itm['from'].split('/')[1]],'to':node_copy[itm['to'].split('/')[1]]}))

    return {'nodes':node_list,'edges':edge_list,'label_length':largest_label}
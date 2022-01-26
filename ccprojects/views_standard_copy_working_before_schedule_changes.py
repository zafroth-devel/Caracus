"""
------------------------------------------------------------------------
Title: APP - Project - Add Project - View - mod 2
Author: Matthew May
Date: 2016-01-17
Notes: User Authorisation
Notes: Note move over to use the reference manager from project
------------------------------------------------------------------------
"""
from django.shortcuts import render, redirect,render_to_response
from django.core.urlresolvers import reverse_lazy,reverse,resolve

from django.http import HttpResponseRedirect
from braces.views import LoginRequiredMixin
from django.views.generic import View,FormView,TemplateView

from django.contrib import messages

from itertools import count

from ccutilities.utilities import return_refs,residenttenant
from ccutilities.arangodb_utils import hierarchy

from ccaccounts.models import AccountProfile
from ccnotes.models import ProjectNotes
from django.contrib.auth.models import User

from ccprojects.models import ProjectStructure,ProjectChange,UserProjects,ProjectStatus,ViewPerms,QuestionGroup,AnswerGroup,Confirmed,HinyangoGroupKey,QuestionType
from ccnotes.models import ProjectAttachments

from ccprojects.forms import AddProjectForm,EditProjectForm
from ccmaintainp.models import NonHierarchyAction,NonHierarchyChange

from ccutilities.formutils import FormBuilder as fb
from ccutilities.multiform import MultiFormsView

from datetime import datetime
from django.utils import timezone
import time
import json

import os
from django.conf import settings

class ProjectView(LoginRequiredMixin,TemplateView):
    template_name = "ccprojects/ccviewprojects.html"

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

        filename = os.path.join(getattr(settings,"BASE_DIR",None), 'uploadedfiles',residenttenant())

        if not os.path.isdir(filename):
            # Create folder 
            os.makedirs(name=filename,exist_ok=True)

        fileidentifier = str(self.request.user)+'-'+'P'+self.request.POST['dropzone-hidden-name']+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+self.request.FILES['file'].name
        mimetype = self.request.FILES['file'].content_type

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
        db_refs = return_refs()
        
        # Permissions owner and viewer third is closed
        project_list = list(ProjectStructure.objects.filter(userprojects__project_user__user__username=self.request.user,userprojects__project_perms__viewing_perms__in=["Owner","Viewer"]).order_by('id'))
        
        outlist=[]
        
        for colname in project_list:
            sublist={}
            sublist['id'] = colname.id
            sublist['project_name'] = colname.project_name
            sublist['description'] = colname.description 
            sublist['benefit_desc'] = colname.benefit_desc
            sublist['created_on'] = colname.created_on
            outlist.append(sublist)

        return(outlist)

# Add project template view
# -------------------------
class AddProjectView(LoginRequiredMixin, FormView):
    template_name = "ccprojects/ccaddproject.html"
    form_class = AddProjectForm
    success_url = "viewproject"

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return(self.form_valid(form, **kwargs))
        else:
            return(self.form_invalid(form, **kwargs))

    # The following works but could be smarter 
    # Change at a later stage
    # ----------------------------------------
    
    def form_valid(self, form):
        # Here we cancel even if the form is valid
        # ----------------------------------------
        if 'cancelbtn' in self.request.POST:
            return HttpResponseRedirect(reverse_lazy('viewproject'))
        elif 'addprojectbtn' in self.request.POST or 'editprojectbtn' in self.request.POST:
            
            # Need to return the ref id for each option
            # -----------------------------------------
            db_refs = return_refs()
            
            # Reverse lookup permissions
            # --------------------------
            #viewing_perms = { v:k for k,v in db_refs["viewing_perms"].items()}

            # Add the valid project
            # ---------------------
            ProjectStructure.objects.create(project_name = form.cleaned_data["projectname"],
                                            description = form.cleaned_data["projectdesc"],
                                            driver = form.cleaned_data["driver"],
                                            benefit_desc = form.cleaned_data["benefitdesc"],
                                            customer_impact = form.cleaned_data["customerimpact"]).save()

            # Get current user object
            # -----------------------
            up = AccountProfile.objects.get(user=self.request.user)

            # Return newly created project object
            # ------------------------------------
            cp = ProjectStructure.objects.get(project_name=form.cleaned_data["projectname"])


            # Return a permission object 'Owner'
            po = ViewPerms.objects.get(viewing_perms="Owner")

            
            # Set new project permissions to owner
            # ------------------------------------
            gu = UserProjects.objects.create(projectmap=cp,project_user=up,project_perms=po)
            
            # Save project
            # ------------
            gu.save()

            # Return to Dashboard
            # Perhaps clear form and do another?
            # Code in later
            # ----------------------------------
            if 'editprojectbtn' in self.request.POST:
                cp = ProjectStructure.objects.get(project_name=form.cleaned_data["projectname"])

                return(HttpResponseRedirect(reverse_lazy('editproject',kwargs={'project_id':cp.id})))
            else:
                return(HttpResponseRedirect(reverse_lazy('viewproject')))


    def form_invalid(self, form, **kwargs):
        # Here form is invalid band the user cancels
        # Here we will save state at a later stage
        # -------------------------------------------------
        if 'cancelbtn' in self.request.POST:
            return HttpResponseRedirect(reverse_lazy('viewproject'))
        elif 'addprojectbtn' in self.request.POST or 'editprojectbtn' in self.request.POST:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            # Here we will push error messages back to the page
            # At a later stage of development
            # -------------------------------------------------
            return(self.render_to_response(context))
            #return render('action.html', {'no_record_check': no_record_check})

# Updates/changes and scheduled changes happen here
# -------------------------------------------------
class EditProjectView(LoginRequiredMixin,FormView):
    template_name = "ccprojects/cceditprojects.html"

    success_url = "editproject"
    #qgroup = list(QuestionGroup.objects.all())

    def get_form_class(self):

        # Here is where the change for project level Q/A needs to happen
        # There are several ways it can be changed to accomodate project level
        # Q/A but it might be prudent to do it in the utility providing an id based
        # on the QA information
        qgroup = list(QuestionGroup.objects.filter(active="Yes"))
        qtype = list(QuestionType.objects.values())

        type_required = {}
        for qt in qtype:
            type_required[qt['id']] = qt['question_level']


        fieldlist = []

        for q in qgroup:
            formdict = {}
            choicelist = []
            formdict['name']=q.name
            formdict['label']=q.question
            formdict['required']=True
            formdict['type']="select"
            formdict['target']=type_required.get(q.type_required_id) # This will point to whatever the question model points to
            formdict['default']=''
            for a in list(AnswerGroup.objects.filter(question_map_id=q.id)):
                choicelist.append({"name":a.answers,"value":str(a.id)+'-'+a.answers})

            formdict['choices']=choicelist
            fieldlist.append(formdict)

        fieldlist.append({"name":"changenote","label":"Notes","type":"changenote","target":"Change","required":False})
        fieldlist.append({"name":"datestart","label":"datestart","type":"datestart","target":"Change","required":True})
        fieldlist.append({"name":"dateend","label":"dateend","type":"dateend","target":"Change","required":True})
        fieldlist.append({"name":"nickname","label":"nickname","type":"text","target":"Change","max_length":"40","required":False})

        return(fb(fieldlist).return_form())


    def extract_data(self,project_id):
        # db_refs = return_refs()
        # This line added for security the user and the project id must match otherwise the project will not load
        # Note no changes for permissions yet
        ps = ProjectStructure.objects.filter(pk=project_id,userprojects__project_user__user__username=self.request.user)

        return_list = []

        # Project details
        for colname in list(ps):
            hedlist={}
            hedlist['id'] = colname.id
            hedlist['project_name'] = colname.project_name
            hedlist['description'] = colname.description 
            hedlist['benefit_desc'] = colname.benefit_desc
            hedlist['customer_impact'] = colname.customer_impact
            hedlist['driver'] = colname.driver
            hedlist['created_on'] = colname.created_on
        
        return_list.append(hedlist)

        #outlist=[]

        return_list.append(hierarchy().ul_render())


        return(return_list) 


    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form, **kwargs)
        else:
            return self.form_invalid(form, **kwargs)      

    def get_context_data(self,**kwargs):
        context = super(EditProjectView, self).get_context_data(**kwargs)

        # This line takes the uri project id parameter and sends it to only process that project
        project_data = self.extract_data(project_id=self.kwargs['project_id'])
        context['project'] = project_data[0]
        #context['pchanges'] = project_data[1]
        context['treeview'] = project_data[1]
        # Removed no time at this stage
        #context['hierarchy'] = project_data[3]

        
        return(context)



    def form_valid(self, form,  **kwargs):
        # Here we cancel even if the form is valid
        # ---------------------------------------- 
        # Note the form is not setup correctly with the form /form check the html is correctly formed as 
        # This returns an error
        if 'canceleditbtn' in self.request.POST:

            return(HttpResponseRedirect(reverse_lazy('viewproject')))
        elif 'editprojectbtn' in self.request.POST and self.request.POST['hierarchy'] != '':

            #print(self.request.POST)

            # Here is where I load the database with the necessary change information
            # -----------------------------------------------------------------------

            # 1. Add any answers to the projectchange table
            # 2. Add project change answer id and the start and end dates to the Arangodb hierarchy 
            # 3. Add any notes to the notes table

            # Add answers to the projectchange table
            # --------------------------------------

            # Extract answers from Post
            # -------------------------
            cp = ProjectStructure.objects.get(pk=self.kwargs['project_id'])
            start_date = timezone.datetime.strptime(self.request.POST['datestart'], '%B %d, %Y')
 
            end_date = timezone.datetime.strptime(self.request.POST['dateend'], '%B %d, %Y')

            cfm = Confirmed.objects.get(confirmed='No')

            qgroup = list(QuestionGroup.objects.filter(active="Yes"))
            qtype = list(QuestionType.objects.values())

            type_required = {}
            for qt in qtype:
                type_required[qt['id']] = qt['question_level']


            # Create question grouping key
            gk = HinyangoGroupKey.objects.create()

            # Place the groupkey on the hierarchy not multiple change keys
            one_hier_call = 0

            for q in qgroup:
                # Need answer group instance
                #qg = QuestionGroup.objects.get(name=q.name)

                if type_required.get(q.type_required_id) == 'Project':
                    qa_identifier = 'proj_'+q.name
                else:
                    qa_identifier = 'chan_'+q.name

                nickname = None

                # Need a test to see if nickname exists
                if self.request.POST['nickname'] != '':
                    nickname = self.request.POST['nickname']

                ag = AnswerGroup.objects.get(id=self.request.POST[qa_identifier].split('-')[0])

                # This is in place for forward compatibility we might need timezone and there may be international companies
                # If it becomes necessary read timezone information directly and encode dynamically
                # Not also time might become important
                #local_tz = pytz.timezone("Australia/Melbourne")

                # Add the start end date to this as well. Neatly converted. Perhaps convert all to single format storage.
                pck = ProjectChange.objects.create(projectmap = cp,
                                                   groupkey = gk,
                                                   question = q,
                                                   answers = ag,
                                                   type_required = type_required.get(q.type_required_id),
                                                   confirmed = cfm,
                                                   nickname = nickname,
                                                   start_date = start_date, 
                                                   end_date = end_date, 
                                                   propogate = True)

                # This needs to have an error handling mechanism attached or moved to before the db addition

                # No longer being used to hold change information - 2017-07-11

                if type_required.get(q.type_required_id) == 'Change' and one_hier_call == 0:
                    one_hier_call = 1
                    hr = hierarchy()
                    for item in json.loads(self.request.POST['hierarchy']):
                        #print(item)
                        hr.add_change_data(self.kwargs['project_id'],item,str(gk.id),start_date.strftime("%Y-%m-%d"),end_date.strftime("%Y-%m-%d"))

            # Add change note
            up = AccountProfile.objects.get(user=self.request.user)

            pn = ProjectNotes.objects.create(project_structure=cp,
                                             note_type='change',
                                             project_note=self.request.POST['changenote'],
                                             created_by=up)
            # =======================================================================
            messages.success(self.request, 'success')
            return(HttpResponseRedirect(reverse_lazy('editproject',kwargs={'project_id':self.kwargs['project_id']})))
        else:
            print('Nothing in the hierarchy')
            return self.form_invalid(form, **kwargs)

    def form_invalid(self, form, **kwargs):
        # Here form is invalid band the user cancels
        # Here we will save state at a later stage
        # -------------------------------------------------
        if 'canceleditbtn' in self.request.POST:
            #current_url = resolve(self.request.path_info).url_name
            #eferer = self.request.META.get('HTTP_REFERER')
           # print(referer)
            return HttpResponseRedirect(reverse_lazy('viewproject'))
        elif 'editprojectbtn' in self.request.POST:
            context = self.get_context_data(**kwargs)
            # This line sends the invalid form back to the page
            # The issue is that we are going to have to pull only the changed value through the invalid form
            # So the question is do I keep it invalid and process here or do I expact all 

            # Note this will work to check the incoming post is really valid
            # done = {'Key1':'','Key2':'','key3':''}
            # glee={a for a in done.values() if a!=''}
            # glee=list(glee)
            # len(glee) == 0 
            post_check = len(list({a for a in self.request.POST.values() if a !=''}))
            
            context['form']=form
            # Here we will push error messages back to the page
            # At a later stage of development
            # -------------------------------------------------
            messages.warning(self.request, 'failed')
            return(self.render_to_response(context))
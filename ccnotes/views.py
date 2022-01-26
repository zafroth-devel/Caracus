from django.shortcuts import render
from django.http import Http404,HttpResponse

from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from braces.views import LoginRequiredMixin
# Note in 1.11 this is django.views
from django.views.generic import View

from ccprojects.models import ProjectStructure
import os
from django.conf import settings
from .models import ProjectNotes,ProjectAttachments

from ccutilities.utilities import residenttenant
from django.urls import reverse_lazy,reverse
from django.http import HttpResponseRedirect
from rules.contrib.views import PermissionRequiredMixin
from django.contrib import messages

from ccnotes.models import CompanyIcon
from django.core.files import File

from django.db.models import Max
import json

class NoteView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    template_name = "ccnotes/noteview.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('viewproject'))

    def get_context_data(self, **kwargs):
        context = super(NoteView, self).get_context_data(**kwargs)

        # Required project only
        project_data = self.extract_data(project_id=self.kwargs['project_id'])
        print(project_data)
        context['project_notes'] = project_data
        context['project_id'] = self.kwargs['project_id']

        return(context)

    def extract_data(self,project_id):
        ps = ProjectStructure.objects.get(pk=project_id)
        pn = list(ProjectNotes.objects.filter(project_structure=ps,note_type='project'))

        return_list = []
        count_iter = 0

        if not pn:
            hedlist={}
            hedlist['id'] = 0
            hedlist['project_note'] = 'This project has no notes'
            return_list.append(hedlist)
        else:
            for colname in pn:
                count_iter+=1
                hedlist={}
                hedlist['id'] = count_iter
                hedlist['project_note'] = colname.project_note
                hedlist['created_date'] = colname.created_on
                return_list.append(hedlist)
        return(return_list)


class AttachmentView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):

    template_name = "ccnotes/attachmentview.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('viewproject'))

    def get_context_data(self, **kwargs):
        context = super(AttachmentView, self).get_context_data(**kwargs)
        # Required project only
        project_data = self.extract_data(project_id=self.kwargs['project_id'])
        context['attached'] = project_data
        context['project_id'] = self.kwargs['project_id']

        return(context)

    def extract_data(self,project_id):
        ps = ProjectStructure.objects.get(pk=project_id)
        at = list(ProjectAttachments.objects.filter(project_structure=ps))

        return_list = []
        count_iter = 0

        if not at:
            hedlist={}
            hedlist['id'] = 0
            hedlist['filecode'] = ''
            hedlist['attachment'] = 'This project has no attachments'
            return_list.append(hedlist)
        else:    
            # Project details
            for colname in at:
                count_iter+=1
                hedlist={}
                split_col = colname.attachment_name.split('-',4)
                hedlist['id'] = count_iter
                #print("colname.id="+colname.id)
                hedlist['fileid'] = colname.id
                hedlist['filecode'] = split_col[0]+'-'+split_col[1]+'-'+split_col[2]+'-'+split_col[3]
                hedlist['attachment'] = split_col[4]
                return_list.append(hedlist)
            return(return_list)

class DownloadView(LoginRequiredMixin,PermissionRequiredMixin,View):

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
        at = ProjectAttachments.objects.get(id=file_id)
        file_path = os.path.join(settings.BASE_DIR, at.path_on_server,residenttenant(),residenttenant()+'-'+at.attachment_name)
        print(file_path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=at.mime_type)
                response['Content-Disposition'] = 'inline; filename=' + at.attachment_name.split('-',4)[4]
            return(response)
        raise Http404("File does not exist.")        

class DeleteView(LoginRequiredMixin,PermissionRequiredMixin,View):

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('viewproject'))

    def post(self,request,*args,**kwargs):
        file_id = request.POST['file_id']
        at = ProjectAttachments.objects.get(id=file_id)
        file_path = os.path.join(settings.BASE_DIR, at.path_on_server,residenttenant(),residenttenant()+'-'+at.attachment_name)

        print(file_path)

        if os.path.exists(file_path):
            print("Deleting file")
            os.remove(file_path)

        if not os.path.exists(file_path):
            print("Deleting record")
            at.delete()

        return(HttpResponseRedirect(reverse('viewattachments',kwargs={'project_id':request.POST['project_id']})))

class CompanyIconUploadView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = 'ccnotes/uploadicon.html'

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 

    def get_context_data(self, **kwargs):
        context = super(CompanyIconUploadView, self).get_context_data(**kwargs)
        return(context)

    def post(self,request,*args,**kwargs):

        if request.FILES['companyimage'].size <= 1000000:

            djangofile = File(request.FILES['companyimage'])
            CompanyIcon().companyicon.save('companyicon.png',djangofile)

            # Check file to see if it has the correct properties
            just_loaded = CompanyIcon.objects.all().order_by('id').last().id

            ci = CompanyIcon.objects.get(id=just_loaded)

            if ci.companyicon.height == ci.companyicon.width and ci.companyicon.height >=200 and ci.companyicon.height <= 800 and ci.companyicon.width >=200 and ci.companyicon.width <= 800:
                # Delete all but required object set safe flag
                dl = CompanyIcon.objects.all().exclude(id=just_loaded)
                for itm in dl:
                    itm.companyicon.delete()
                    itm.delete()
                ci.safe=True
                ci.save()
                data = {}
                data['result'] = 'Success'
                data['message'] = 'Company image has been uploaded'
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data = {}
                data['result'] = 'Error'
                data['message'] = 'File width and height must be equal and between 200 and 800px. Your file is {0} x {1}'.format(str(ci.companyicon.height),str(ci.companyicon.width))
                ci.companyicon.delete()
                ci.delete()
                return HttpResponse(json.dumps(data), content_type="application/json")

        else:
            data = {}
            data['result'] = 'Error'
            data['message'] = 'File is too large company icon must be less than 1MB'
            return HttpResponse(json.dumps(data), content_type="application/json")











# from ccnotes.models import CompanyIcon
# from django.core.files import File
# file_src='/home/matthew/Development/pjtcc/ccompass/static/assets/images/elogo.png'
# local_file = open(file_src,'rb')
# djangofile = File(local_file)
# geo = CompanyIcon()
# geo.companyicon.save('companyicon.png',djangofile)



        


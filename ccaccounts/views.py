"""
------------------------------------------------------------------------
Title: APP - Accounts - View
Author: Matthew May
Date: 2016-01-04
Notes: User Authorisation
Notes:
------------------------------------------------------------------------
"""
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)
from braces.views import LoginRequiredMixin
from .forms import PasswordChangeForm,HinyangoUserCreationForm,HinyangoResetUserForm,DeleteUserStep1Form,DeleteUserStep2Form
from django.contrib import messages
from django.contrib.auth.models import User
from ccutilities.arangodb_utils import hierarchy as hr
from django.http import HttpResponseRedirect
import json
from django.http import JsonResponse
from ccaccounts.models import AccountProfile
from django.core.validators import validate_email
from rules.contrib.views import PermissionRequiredMixin
from django.views.generic import View
import pytz

class ModifyUserDetailsView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccaccounts/modify_user_details.html"

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
        context = super(ModifyUserDetailsView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['userdata'] = project_data['users']
        context['business_unit'] = project_data['department']
        return context

    def extract_data(self):

        project_data = {}

        all_users = User.objects.all().exclude(username__in=['admin','hinyango','Hinyango','Administrator',self.request.user]).values('id','username','first_name','last_name','email','is_active')

        template_data = []

        for itm in all_users:
            template_dict = {}
            active_users = {}
            template_dict['users'] = '<option value="'+itm['username']+'">'+itm['username']+'</option>'
            template_data.append(template_dict)
            
        project_data['users'] = template_data

        all_nodes = [itm['bu'] for itm in sorted(hr().get_nodes()['result']['result'],key=lambda k: k['bu'])]

        template_data = []
        for itm in all_nodes:
            template_dict = {}
            template_dict['department'] = '<option value="'+itm+'">'+itm+'</option>'
            template_data.append(template_dict)

        project_data['department'] = template_data

        # Timezone modification
        template_data = []
        for itm in pytz.all_timezones:
            template_dict = {}
            tzsplit = itm.split('/')
            if tzsplit[0] == 'Australia' or itm == 'Etc/GMT+12':
                if itm == 'Etc/GMT+12':
                    optionvalue = itm
                    display = 'New Zealand'
                else:
                    optionvalue = itm
                    display = itm

                template_dict['timezone'] = '<option value="'+optionvalue+'">'+display+'</option>'
            
            template_data.append(template_dict)

        project_data['urtimezone'] = template_data

        return project_data

    def post(self, request, *args, **kwargs):
        action = json.loads(request.POST.get('target'))
        username = json.loads(request.POST.get('user'))

        if action=='get_user_data':
            user_data = AccountProfile.objects.get(user__username=username)
            data_out = {'result':'success','message':'','user':username,'firstname':user_data.user.first_name,'lastname':user_data.user.last_name,'email':user_data.user.email,'department':user_data.department,'active':user_data.user.is_active}
            return JsonResponse(data_out)
        else:
            # Do stuff
            firstname = json.loads(request.POST.get('firstname'))
            lastname = json.loads(request.POST.get('lastname'))
            email = json.loads(request.POST.get('email'))
            department = json.loads(request.POST.get('department'))
            
            try:
                validate_email(email)
            except:
                data_out = {'result':'failure','message':'Email is not formed correctly'}
                return JsonResponse(data_out)               

            user_data = User.objects.get(username=username)
            ap_data = AccountProfile.objects.get(user = user_data)
            user_data.first_name = firstname
            user_data.last_name = lastname
            user_data.email = email
            if 'active_status' in request.POST:
                active_status = json.loads(request.POST.get('active_status'))
                print(active_status)
                if active_status == True:
                    user_data.is_active = True
            ap_data.department = department
            user_data.save()
            ap_data.save()


            data_out = {'result':'complete','message':'User modified successfully'}

        return JsonResponse(data_out)


class DeleteUserStep1View(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    form_class = DeleteUserStep1Form
    template_name = 'ccaccounts/delete_user_step1.html'
    title = _('Delete user')
    
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 

    def dispatch(self, *args, **kwargs):
        return super(DeleteUserStep1View, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(DeleteUserStep1View, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse_lazy('final_remove_user',kwargs={'uname': self.urlparameter})

    def form_valid(self, form):
        self.urlparameter = form.cleaned_data['username']
        return super(DeleteUserStep1View, self).form_valid(form)


class DeleteUserStep2View(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    form_class = DeleteUserStep2Form
    template_name = 'ccaccounts/delete_user_step2.html'
    title = _('Delete user')
    
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 

    def dispatch(self, *args, **kwargs):
        return super(DeleteUserStep2View, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(DeleteUserStep2View, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['uname'] = self.kwargs['uname']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(DeleteUserStep2View, self).get_context_data(**kwargs)
        context['remuser'] = self.kwargs['uname']
        return context

    def get_success_url(self):
        return reverse_lazy('login_redirect')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Any Projects owned by the user have been reassigned and the user removed.')
        return super(DeleteUserStep2View, self).form_valid(form)

class PasswordContextMixin(object):
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super(PasswordContextMixin, self).get_context_data(**kwargs)
        context['title'] = self.title
        if self.extra_context is not None:
            context.update(self.extra_context)
        return context

class PasswordChangeView(LoginRequiredMixin,PermissionRequiredMixin,PasswordContextMixin, FormView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('viewproject')
    template_name = 'ccaccounts/password_change_form.html'
    title = _('Password change')
    
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator') or user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def dispatch(self, *args, **kwargs):
        return super(PasswordChangeView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(PasswordChangeView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'Password updated successfully')
        return super(PasswordChangeView, self).form_valid(form)

class PasswordChangeDoneView(LoginRequiredMixin,PermissionRequiredMixin,PasswordContextMixin, TemplateView):
    template_name = 'ccaccounts/password_change_done.html'
    title = _('Password change successful')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator') or user.has_perm('ccaccounts.standard_user')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PasswordChangeDoneView, self).dispatch(*args, **kwargs)


# This is to add a new user to Hinyango
# Need to link these up
# -------------------------------------

class HinyangoCreateUserView(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    form_class = HinyangoUserCreationForm
    success_url = reverse_lazy('add_hinyango_user_done')
    template_name = 'ccaccounts/add_new_user_form.html'
    title = _('Add new user')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def dispatch(self, *args, **kwargs):
        return super(HinyangoCreateUserView, self).dispatch(*args, **kwargs)

    # def get_form_kwargs(self):
    #     kwargs = super(HinyangoCreateUserView, self).get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     return kwargs

    def get_context_data(self, **kwargs):
        context = super(HinyangoCreateUserView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        #update_session_auth_hash(self.request, form.user)
        return super(HinyangoCreateUserView, self).form_valid(form)


class HinyangoCreateUserDoneView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = 'ccaccounts/add_new_user_done.html'
    title = _('User successfully added.')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator') 

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HinyangoCreateUserDoneView, self).dispatch(*args, **kwargs) 

    def get_context_data(self, **kwargs):
        context = super(HinyangoCreateUserDoneView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context   


class HinyangoResetUserView(LoginRequiredMixin,PermissionRequiredMixin,FormView):
    form_class = HinyangoResetUserForm
    success_url = reverse_lazy('reset_password_done')
    template_name = 'ccaccounts/reset_user_password.html'
    title = _('Reset user password')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator') or user.has_perm('ccaccounts.user_reset')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def dispatch(self, *args, **kwargs):
        return super(HinyangoResetUserView, self).dispatch(*args, **kwargs)

    # def get_form_kwargs(self):
    #     kwargs = super(HinyangoCreateUserView, self).get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     return kwargs

    def get_form_kwargs(self):
        kwargs = super(HinyangoResetUserView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(HinyangoResetUserView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        #update_session_auth_hash(self.request, form.user)
        return super(HinyangoResetUserView, self).form_valid(form)


class HinyangoResetUserDoneView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = 'ccaccounts/reset_user_password_done.html'
    title = _('Password reset.')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.administrator') or user.has_perm('ccaccounts.user_reset')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(HinyangoResetUserDoneView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context

class HinyangoAccountRedirect(View):
    def dispatch(self, *args, **kwargs):
        super(HinyangoAccountRedirect, self).dispatch(*args, **kwargs)
        user = self.request.user
        
        if user.is_authenticated:
            if user.has_perm('ccaccounts.standard_user'):
                redirect_url = 'dash'
            elif user.has_perm('ccaccounts.administrator'):
                redirect_url = 'add_hinyango_user'
            elif user.has_perm('ccaccounts.report_viewer'):
                redirect_url = 'dash'
            elif user.has_perm('ccaccounts.rule_manager'):
                redirect_url = 'qaview'
            elif user.has_perm('ccaccounts.hierarchy_manager'):
                redirect_url = 'hmview'
            elif user.has_perm('ccaccounts.user_reset'):
                redirect_url = 'reset_password'
            else:
                redirect_url = 'home'
        else:
            redirect_url = 'login'

        return HttpResponseRedirect(reverse_lazy(redirect_url))

    def http_method_not_allowed(request, *args, **kwargs):
        print('Bloob')

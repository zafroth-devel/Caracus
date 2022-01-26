"""
------------------------------------------------------------------------
Title: Maintenance and settings
Author: Matthew May
Date: 2017-09-17
Notes: 
Notes: 
------------------------------------------------------------------------
"""
from django.shortcuts import render
from django.views.generic.base import TemplateView
# Can stop using braces and move to standard library
#from braces.views import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.urls import reverse_lazy,reverse
from django.http import HttpResponseRedirect,JsonResponse
from django.contrib import messages
from ccutilities.arangodb_utils import hierarchy
# Note in 1.11 this is django.views
from django.views.generic import View
from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType
from django.db.models import Avg, Max, Min, F, Q
import json
from ccaccounts.models import AccountProfile
from ccmaintainp.models import HinyangoPermissionActive,HinyangoPermissions,HinyangoHierarchyLock,HinyangoSettings
from django.contrib.auth.models import User,Group
from ccutilities.graphmod import graphmod
from ccutilities.utilities import residenttenant
from rules.contrib.views import PermissionRequiredMixin
from datetime import datetime
from django.contrib import messages
import os
from django.conf import settings
from bs4 import BeautifulSoup as bsoup

class QAView(LoginRequiredMixin,UserPassesTestMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccmaintainp/changeqa_op_20181031.html"

    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.rule_manager')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def test_func(self):
        return True

    def post(self, request, *args, **kwargs):
        incoming_data = json.loads(request.POST['output'])['output']
        if incoming_data['request'] == 'get-type-list':
            # Get type list
            qtp = QuestionType.objects.all().values('id','question_type','question_desc','question_level')
            # Convert to list of lists - Javascript requirement
            qtp_out = [list(col.values()) for col in qtp]
            return JsonResponse({'result':'receipt','outcome':'success','data':qtp_out})
        elif incoming_data['request'] == 'delete-type':
            return JsonResponse({'result':'receipt','outcome':'success','message':incoming_data['request']})
        elif incoming_data['request'] == 'check-new-type':
            # Check incoming name if it exists return an error if not send it to database
            qtp = QuestionType.objects.filter(question_type=incoming_data['data']['name'],question_level=incoming_data['data']['target'])

            if qtp:
                return JsonResponse({'result':'receipt','outcome':'failure','message':'Exists'})
            else:
                qtp = QuestionType.objects.create(question_type=incoming_data['data']['name'],question_level=incoming_data['data']['target'],question_desc=incoming_data['data']['desc'],negotiable='Yes')
                qtp.save()
                return JsonResponse({'result':'receipt','outcome':'success','message':'Loaded'})
        elif incoming_data['request'] in ('get-type-names-ex','get-type-names-inc'):
            # Return just names and ids to link into selections
            # Filter out any linked to a current question
            if incoming_data['request'] == 'get-type-names-ex':
                q = list(QuestionGroup.objects.values_list('type_required',flat=True).distinct())
                qtp = QuestionType.objects.filter(negotiable='Yes').exclude(id__in=q).values('id','question_type','question_level')
            else:
                qtp = QuestionType.objects.filter(negotiable='Yes').values('id','question_type','question_level')

            if qtp:
                return JsonResponse({'result':'receipt','outcome':'success','message':list(qtp)})
            else:
                return JsonResponse({'result':'receipt','outcome':'failure','message':'No matching query'})
        elif incoming_data['request'] == 'delete_selected_type':
            qtp = QuestionType.objects.filter(id=int(incoming_data['data']))
            ip = qtp.delete()
            if ip[0] > 0:
                return JsonResponse({'result':'receipt','outcome':'success','message':'Deleted'})
            else:
                return JsonResponse({'result':'receipt','outcome':'failure','message':'Not Deleted'})
        elif incoming_data['request'] == 'check-question-name':
            # Check question name
            #qgd = QuestionGroup.objects.get(name=incoming_data['data']['name'])
            qgd = QuestionGroup.objects.filter(name=incoming_data['data'])
            # Does it have answers as well
            agd = AnswerGroup.objects.filter(question_map = qgd)
            if qgd and not agd:
                return JsonResponse({'result':'receipt','outcome':'success','message':['yes','no']})
            elif qgd and agd:
                return JsonResponse({'result':'receipt','outcome':'success','message':['yes','yes']})
            else:
                return JsonResponse({'result':'receipt','outcome':'success','message':['no','no']})
        elif incoming_data['request'] == 'check-question-name-id':
            # As we can modify only the questions or only the answers attached
            # There could be a disconnect if the name is not logged correctly to the question
            # In other words the question listed on the page is not the same as the one that
            # the user thinks they are loading a changed answer to
            # Check question name
            #qgd = QuestionGroup.objects.get(name=incoming_data['data']['name'])
            # Check sent id
            qgd_id = QuestionGroup.objects.get(id=int(incoming_data['data']['id']))

            # Load changed answers
            if incoming_data['data']['name']==qgd_id.name:

                # Make all db answers inactive
                agd = AnswerGroup.objects.filter(question_map = qgd_id)
                new_answers = incoming_data['data']['dataarray']

                names_listed = []

                for itm in agd:
                    itm.active = 'No'
                    if itm.answers in new_answers.keys():
                        names_listed.append(itm.answers)
                        itm.active = 'Yes'
                        itm.desc = new_answers[itm.answers][2]
                        itm.arank = new_answers[itm.answers][0]
                        itm.save()

                new_list = list(set(new_answers.keys())-set(names_listed))

                print(new_list)

                # Add new items to question
                for itm in new_list:
                    answergrouprow = AnswerGroup.objects.create(question_map=qgd_id,answers=itm,description=new_answers[itm][2],arank=new_answers[itm][0],aweight=100,active='Yes')

                return JsonResponse({'result':'receipt','outcome':'success','message':['Success',incoming_data['data']['name'],qgd_id.name]})
            else:
                return JsonResponse({'result':'receipt','outcome':'success','message':['No Match',incoming_data['data']['name'],qgd_id.name]})


        elif incoming_data['request'] == 'save-question':
            data = incoming_data['data']
            if data['not_applicable']:
                naresult = 'Yes'
            else:
                naresult = 'No'

            new_rank = QuestionGroup.objects.all().aggregate(Max('rank'))['rank__max']+1

            qt = QuestionType.objects.get(id=int(data['level']))
            qg = QuestionGroup.objects.create(name=data['name'],
                                              rank=new_rank,
                                              active='No',
                                              description=data['desc'],
                                              aweight=100,
                                              type_required=qt,
                                              question=data['question'],
                                              na=naresult)

            # Check db
            qg = QuestionGroup.objects.filter(name=data['name'])

            if qg:
                return JsonResponse({'result':'receipt','outcome':'success','message':'Data loaded'})
            else:
                return JsonResponse({'result':'receipt','outcome':'failure','message':'Data did not save'})
        elif incoming_data['request'] == 'submit-answer-data':
            qg = QuestionGroup.objects.get(name=incoming_data['data']['question'])

            for itm in incoming_data['data']['dataarray']:
                answergrouprow = AnswerGroup.objects.create(question_map=qg,answers=itm[1],description=itm[2],arank=itm[0],aweight=100,active='Yes')

            # Make question active
            qg.active='Yes'
            qg.save()

            return JsonResponse({'result':'receipt','outcome':'success','message':'Data loading'})
        elif incoming_data['request'] == 'get-question-data':
            qg = QuestionGroup.objects.filter(type_required__negotiable='Yes',active='Yes')
            qdp = []
            qdp_ll = []
            for itm in qg:
                qdp.append({'id':itm.id,'name':itm.name,'type':itm.type_required.question_type,'question':itm.question,'description':itm.description,'question2':bsoup(itm.question,features='html5lib').get_text(),'description2':bsoup(itm.description,features='html5lib').get_text(),'level':itm.type_required.question_level,'hasna':itm.na})
                qdp_ll.append([itm.id,itm.name,itm.type_required.question_type,bsoup(itm.question,features='html5lib').get_text(),bsoup(itm.description,features='html5lib').get_text(),itm.type_required.question_level])
            return JsonResponse({'result':'receipt','outcome':'success','message':[qdp,list(qdp_ll)]})
        elif incoming_data['request'] == 'get-qrank-data':
            qg = QuestionGroup.objects.filter(type_required__negotiable='Yes')
            qdp_project = []
            qdp_change = []
            for itm in qg:
                if itm.type_required.question_level == 'Project':
                    qdp_project.append([itm.rank,itm.name,itm.type_required.question_type,bsoup(itm.question,features='html5lib').get_text(),bsoup(itm.description,features='html5lib').get_text(),itm.type_required.question_level,itm.id])
                else:
                    qdp_change.append([itm.rank,itm.name,itm.type_required.question_type,bsoup(itm.question,features='html5lib').get_text(),bsoup(itm.description,features='html5lib').get_text(),itm.type_required.question_level,itm.id])
            return JsonResponse({'result':'receipt','outcome':'success','message':{'change':list(qdp_change),'project':list(qdp_project)}})
        elif incoming_data['request'] == 'save-q-ranking':
            ids = incoming_data['data'][0][0] + incoming_data['data'][1][0]
            ranks = incoming_data['data'][0][1] + incoming_data['data'][1][1]
            print(ids)
            print(ranks)
            itm_counter = 0
            for itms in ids:
                qg = QuestionGroup.objects.get(id=itms)
                qg.rank = ranks[itm_counter]
                qg.save()
                itm_counter = itm_counter + 1

            return JsonResponse({'result':'receipt','outcome':'success','message':'Loading'})

        elif incoming_data['request'] == 'get-answer-data':
            qg = QuestionGroup.objects.get(name=incoming_data['data']['question'])
            ag = AnswerGroup.objects.filter(question_map=qg).values()
            return JsonResponse({'result':'receipt','outcome':'success','message':list(ag)})
        elif incoming_data['request'] == 'load-modified-question':
            qtr = QuestionType.objects.get(question_type = incoming_data['data']['level'],question_level = incoming_data['data']['target'])
            qgd = QuestionGroup.objects.get(id=incoming_data['data']['id'])
            qgd.name = incoming_data['data']['name']
            qgd.question = incoming_data['data']['question']
            qgd.na = incoming_data['data']['not_applicable']
            qgd.description = incoming_data['data']['desc']
            qgd.type = qtr
            qgd.save()
            return JsonResponse({'result':'receipt','outcome':'success','message':'Success'})
        elif incoming_data['request'] == 'question-inactive':
            qg = QuestionGroup.objects.get(id=incoming_data['data'])
            qg.active='No'
            qg.save()
            return JsonResponse({'result':'receipt','outcome':'success','message':'Success'})
        else:
            return JsonResponse({'result':'receipt','outcome':'failure','message':'No matching query'})

    def get_context_data(self, **kwargs):
        context = super(QAView, self).get_context_data(**kwargs)
        return context 

    def extract_data(self):
        pass

class ChangePMView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccmaintainp/changepm.html"

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
        context = super(ChangePMView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['perms'] = project_data['perm']
        context['users'] = project_data['profiles']

        return(context)

    def extract_data(self):
        # Get all users to add to drop down
        #profiles = AccountProfile.objects.all().values()
        # Get all permissions to add to permission box

        all_users = sorted(User.objects.all().exclude(username__in=['admin','Hinyango','hinyango','Administrator',self.request.user]).values('id','username','first_name','last_name'),key=lambda k: k['username'])

        profile_outlist = []
        first_itm = True
        for itm in all_users:
            subdict = {}
            if first_itm == True:
                first_itm = False
                subdict['opcode'] = '<option value="'+str(itm['id'])+'" selected>'+itm['username']+' - ('+itm['first_name']+' '+itm['last_name']+')</option>'
            else:
                subdict['opcode'] = '<option value="'+str(itm['id'])+'">'+itm['username']+' - ('+itm['first_name']+' '+itm['last_name']+')</option>'

            profile_outlist.append(subdict)

        # Get all permissions
        # -------------------
        permissions = list(Group.objects.filter(name__in=['standard_user','report_viewer','rule_manager','hierarchy_manager','administrator','reset_user']).values('id','name'))

        # Get permissions for single user
        # -------------------------------

        first_user = User.objects.get(username=all_users[0]['username'])

        user_groups = [itm['name'] for itm in list(first_user.groups.all().values('name'))]

        outlist = []
        for itm in permissions:
            outdict = {}
            outdict['id'] = itm['id']
            outdict['name'] = itm['name']
            outdict['proper_name'] = itm['name'].replace('_',' ').title()
            outdict['selected'] = False
            if itm['name'] in user_groups:
                outdict['selected'] = True

            outlist.append(outdict)

        perm_outlist = []
        for itm in outlist:
            subdict = {}
            if itm['selected']:
                subdict['opcode'] = '<option value="'+str(itm['id'])+'" selected>'+itm['proper_name']+'</option>'
            else:
                subdict['opcode'] = '<option value="'+str(itm['id'])+'">'+itm['proper_name']+'</option>'

            perm_outlist.append(subdict)

        return({'perm':perm_outlist,'profiles':profile_outlist})

    def post(self, request, *args, **kwargs):

        incoming_action = request.POST['action']

        if incoming_action == 'get_permissions':
            incoming_user = User.objects.get(id=int(request.POST['user_id']))

            out_data = self.get_perms(incoming_user)

            return JsonResponse(out_data)
        else:
            # Posting required changes

        
            permissions = list(Group.objects.filter(name__in=['standard_user','report_viewer','rule_manager','hierarchy_manager','administrator','reset_user']).values('id','name'))

            set_permissions = json.loads(request.POST['selected'])

            group_list = []
            for itm in permissions:
                if str(itm['id']) in set_permissions:
                    new_group = Group.objects.get(name=itm['name'])
                    group_list.append(new_group)

            change_permissions_user = User.objects.get(id=int(request.POST['user_id']))

            change_permissions_user.groups.clear()

            # current_groups = change_permissions_user.groups.all()
            # for itm in current_groups:
            #     change_permissions_user.groups.remove(itm)

            change_permissions_user.groups.set(group_list)

            all_users = sorted(User.objects.all().exclude(username__in=['admin','Hinyango','hinyango','Administrator',self.request.user]).values('id','username','first_name','last_name'),key=lambda k: k['username'])
            first_user = User.objects.get(id=all_users[0]['id'])
            out_data = self.get_perms(first_user)


            return JsonResponse(out_data)

    def get_perms(self,user):
        #permissions = Group.objects.filter(id__gte=14).values('id','name')
        
        user_groups = user.groups.all()

        group_list = []
        for itm in user_groups:
            group_list.append(itm.id)

        print(group_list)

        return {'user':str(user.id),'permission_ids':group_list}
        #HinyangoPermissions

class ChangeHMView(LoginRequiredMixin,TemplateView):
    template_name = "ccmaintainp/changehm.html"
    
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.hierarchy_manager')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect'))

    def get_context_data(self, **kwargs):
        context = super(ChangeHMView, self).get_context_data(**kwargs)
        project_data = self.extract_data()
        context['treeview'] = project_data['hierarchy']
        context['nodes'] = project_data['nodes']

        ls = graphmod.checkonly().getlockstatus()

        if ls['status'] != 'Cleared':
            messages.warning(self.request, 'Any changes to the hierarchy are currently locked by {0}. You will need to wait until all changes are finalised before further modification of the hierarchy is possible. Refresh to return the latest hierarchy.'.format(ls['user']))
            #messages.info(self.request, 'Any pending changes will need to be finalised before further modification')

        return(context)

    def extract_data(self):

        nodes = sorted(hierarchy().get_nodes()['result']['result'],key=lambda r: r['bu'])

        return({'hierarchy':hierarchy().ul_render(),'nodes':nodes})

    def post(self, request, *args, **kwargs):
        # Check if hierarchy lock exists if so send message and exit
        checkgraph = graphmod()

        ls = checkgraph.setlockstatus(request.user)

        if ls['result'] == 'success':
            incoming_post = json.loads(request.POST['hierarchy'])
            # Initilise proposed hierarchy
            checkgraph.setproposed(incoming_post)
            # Query arango for the current hierarchy
            checkgraph.getcurrenthierarchy()

            checkgraph.updatehierarchy()

            clearlock = checkgraph.clearlockststatus(request.user)

            if clearlock['result'] == 'success':
                messages.success(self.request, 'Hierarchy updated sucessfully')
            else:
                messages.error(self.request, 'An error occured with the data lock contact your Hinyango representative')

        # We will take a look at the incoming to get the vertices and stuff
        # -----------------------------------------------------------------
            #f = open('/home/matthew/hpostout_added_node.txt','w')
            #f.write(json.dumps(incoming_post))
            #f.close()            

        return(HttpResponseRedirect(reverse_lazy('hmview')))
        

class ChangeSGView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccmaintainp/changesg.html"

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
        context = super(ChangeSGView, self).get_context_data(**kwargs)

        context['setting_parameters'] = self.extract_data()

        return(context)

    def extract_data(self):
        settings = HinyangoSettings.objects.all().order_by('id').values()
        return(settings)
    def post(self, request, *args, **kwargs):
        print(request.POST)
        if request.POST:
            command_data = json.loads(request.POST.get('cmddata'))
            settings = HinyangoSettings.objects.get(id=int(command_data['id']))
            settings.cmdparameter = command_data['cmdparameter']
            settings.cmddate = datetime.now()
            settings.save()
        return JsonResponse({'returned':1})


class LoadIconView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccmaintainp/loadicon.html"

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
        context = super(LoadIconView, self).get_context_data(**kwargs)

        #context['setting_parameters'] = self.extract_data()

        return(context)

    def extract_data(self):
        settings = HinyangoSettings.objects.all().order_by('id').values()
        return(settings)
    def post(self, request, *args, **kwargs):
        print(request.POST)
        print(request.FILES)

        pyfile = request.FILES

        if pyfile != None:

            print("Processing File")
                
            # Note much of this will have to be moved to a remote server via paramiko (ssh)
        
            filename = os.path.join(getattr(settings,"BASE_DIR",None), 'companyicon',residenttenant())
            companyicon = self.request.FILES['file']
        
            if not os.path.isdir(filename):
                # Create folder 
                os.makedirs(name=filename,exist_ok=True)
        
            fileidentifier = 'company-icon'
            mimetype = companyicon.content_type
        
            print(mimetype)
        
            filename = os.path.join(filename,residenttenant()+'-'+fileidentifier)
            with open(filename, 'wb+') as destination:
                for chunk in companyicon.chunks():
                    destination.write(chunk)

        return(HttpResponseRedirect(reverse_lazy('login_redirect')))


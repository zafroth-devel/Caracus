# -----------------------------------------------------------
# Title: Scheduling tasks
# Author:
# Date:
# Notes:
# Notes:
# -----------------------------------------------------------

from django.db import connection
from config.celery import app
from celery.schedules import crontab
from cctenants.models import Client
from ccchange.models import ProjectChange as pc
from django.contrib.auth.models import User
from ccprojects.models import ProjectStructure,UserProjects,ViewPerms
from ccutilities.utilities import get_all_tenants
from ccmaintainp.models import HinyangoSettings
from django.db.models import Max,F
from datetime import datetime,timedelta,date
from ccutilities.arangodb_utils import hierarchy as hr
from directmessages.apps import Inbox
from django.core.mail import EmailMultiAlternatives
from ccmaintainp.models import NonHierarchyChange as nhc,NonHierarchyAction as nha
from django.db.models import Q
#from cccalculate.scoring_scheduled import scoringdef

from cccalculate.hscore import scoringdef

import ccreporting.reportingconfig as rc
from ccreporting.models import ScheduledReports,FilesAvailable
from ccutilities.module_utilities import module_import
from ccutilities.reporting_utils import reportloc
import arrow
from dateutil.rrule import rrulestr
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import os
    
@app.task
def HinyangoStandardTasks():
    '''Note we are working in the public schema until the connection is set to a particular tenant
       -------------------------------------------------------------------------------------------'''
    clients = Client.objects.all().exclude(schema_name='public')
    current_date = datetime.now().replace(tzinfo=None).date()
    for client in clients:
        # Set schema to next in list
        connection.set_tenant(client)


        hinyango = User.objects.filter(username='Hinyango')
        max_parameter = HinyangoSettings.objects.filter(cmdtag='hinyango reminders').aggregate(Max('cmdparameter'))

        # Must have Hinyango user
        # Must have cmdparameter

        if hinyango and max_parameter['cmdparameter__max']:
            hinyango = User.objects.get(username='Hinyango')

            # Get parameter
            # -------------
            #max_parameter = HinyangoSettings.objects.filter(cmdtag='hinyango reminders').aggregate(Max('cmdparameter'))
            pchange = pc.objects.filter(type_required='Change',inactive_date=None,confirmed__confirmed='No')
            # Further removal of items not requiring notification
            # ---------------------------------------------------
            id_exclusions = []
            for itm in pchange:
                match_date = itm.start_date.replace(tzinfo=None).date() - timedelta(days=int(max_parameter['cmdparameter__max']))
                startdate = itm.start_date.replace(tzinfo=None).date()
                #print('{0} - {1} - {2}'.format(current_date,match_date,startdate))
                if (current_date >= match_date and current_date <= startdate) or (startdate < current_date):
                    pass
                else:
                    id_exclusions.append(itm.id)

            closed = UserProjects.objects.filter(project_perms__viewing_perms='closed').distinct()

            if closed:
                zip_closed = [itm.projectmap for itm in closed]
                pchange = pchange.exclude(Q(id__in=id_exclusions) | Q(projectmap__in=zip_closed))
            else:
                pchange = pchange.exclude(id__in=id_exclusions)

            pj_list = [itm.projectmap for itm in pchange]

            userp = UserProjects.objects.filter(projectmap__in=pj_list,project_perms__viewing_perms='Owner')
            
            change_data = []
            for itm in pchange:
                innerdict = {}
                innerdict['change_id'] = itm.id
                innerdict['change_group_key'] = itm.groupkey.id
                innerdict['owner'] = userp.get(projectmap=itm.projectmap).project_user.user
                innerdict['owner_username'] = userp.get(projectmap=itm.projectmap).project_user.user.username
                innerdict['owner_email'] = userp.get(projectmap=itm.projectmap).project_user.user.email
                innerdict['project_id'] = itm.projectmap.id
                innerdict['project_name'] = itm.projectmap.project_name
                innerdict['project_desc'] = itm.projectmap.description
                innerdict['nickname'] = itm.nickname
                innerdict['start_date'] = itm.start_date
                innerdict['condition_date'] = itm.start_date.replace(tzinfo=None).date() - timedelta(days=int(max_parameter['cmdparameter__max']))
                innerdict['end_date'] = itm.end_date
                if itm.start_date.replace(tzinfo=None).date() < current_date:
                    innerdict['category'] = 'past due for notification'
                elif current_date >= itm.start_date.replace(tzinfo=None).date() - timedelta(days=int(max_parameter['cmdparameter__max'])) and current_date <= itm.start_date.replace(tzinfo=None).date():
                    innerdict['category'] = 'email notification zone'
                else:
                    innerdict['category'] = 'not yet due - remove'
                change_data.append(innerdict)
    
            # Remove duplicate entries
            # ------------------------
            newlist = []
            change_group_key = 0
            for itm in change_data:
                if itm['change_group_key'] != change_group_key:
                    newlist.append(itm)
                    change_group_key = itm['change_group_key']
            
            change_data = newlist
    
            # Get list of affected nodes
            # --------------------------
    
            hierarchy = hr()
    
            bu_dict = {}
            for itm in change_data:
                hier = hierarchy.get_selected(project_id = itm['project_id'],change_id = itm['change_group_key'])
                bu_list = []
                itm_count = 0
                # Limit the number of nodes to five
                for itms in hier[:5]:
                    bu_list.append(itms['business_unit'])
                bu_dict[itm['change_group_key']] = bu_list
    
    
            # Get list by user
            user_set = set()
            for itm in change_data:
                user_set.add(itm['owner'])
            
            user_list = []
            for usr in user_set:
                user_dict = {}
                user_change = []
                user_dict['owner'] = usr
                user_dict['username'] = usr.username
                user_dict['email'] = usr.email
                for itm in change_data:
                    if usr == itm['owner']:
                        user_change.append(itm)
                user_dict['change_data'] = user_change
                user_list.append(user_dict)
    
            # Hinyango sender
            
            # Email parameters
            from_email = 'hinyango@hinyango.com.au'
            text_content = 'You are seeing this text because your email browser is set to block html.\n Log into Hinyango to review hinyango messages for unconfirmed changes.'
            subject = 'Pending unconfirmed changes requiring attention!'
            # Hinyango message parameters
            body_top_hm = '<table style="width:100%"><tr><th>Change ID</th><th>Nickname</th><th>Project Name</th><th>Info</th></tr>'
            body_middle_hm = '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>'
            body_top_em = '<table style="width:100%"><tr><th>Change ID</th><th>Nickname</th><th>Project Name</th><th>Start Date</th><th>End Date</th><th>Info</th></tr>'
            body_middle_em = '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>'
            body_first_end_em = '</table>'
            org_node_list_top_em = '<table style="width:100%"><tr><th>Business Unit - ({0})</th></tr>'
            org_node_list_middle_em = '<tr><td>{0}</td><tr>'
            org_node_list_end_em = '</table><br>'
            
            
            
            # Email and message based on change data
            for itm in user_list:
                # Hinyango message settings
                body_end_hm = '</table><hr><p>Sent by Hinyango on {0} at {1}</p>'.format(datetime.now().date(),datetime.now().time())
                body_end_em = '<hr><p>Sent by Hinyango on {0} at {1}</p>'.format(datetime.now().date(),datetime.now().time())
                temp_middle_hm = ''
                temp_middle_em = ''
                temp_middle_org_em = ''
                org_data = []
                for itms in itm['change_data']:
                    temp_middle_hm = temp_middle_hm + body_middle_hm.format(itms['change_group_key'],itms['nickname'],itms['project_name'],itms['category'])
                    temp_middle_em = temp_middle_em + body_middle_hm.format(itms['change_group_key'],itms['nickname'],itms['project_name'],itms['start_date'],itms['end_date'],itms['category'])
                    temp_org_node_list_top_em = org_node_list_top_em.format(itms['nickname'])
                    for bus in bu_dict[itms['change_group_key']]:
                        temp_middle_org_em = temp_middle_org_em + org_node_list_middle_em.format(bus)
                    org_data.append(temp_org_node_list_top_em+temp_middle_org_em+org_node_list_end_em)
                body_hm = body_top_hm + temp_middle_hm + body_end_hm
                # Send Hinyango message
                Inbox.send_message(hinyango, 'Hinyango', itm['owner'], subject, body_hm)
                out_org_em = ''
                for itms in org_data:
                    out_org_em = out_org_em + itms
                # Email send 
                body_em = body_top_em + temp_middle_em + body_first_end_em + '<br>' + out_org_em + body_end_em
                to = itm['email']
                #print('{0}   {1}   {2}'.format(subject,from_email,to))
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(body_em, "text/html") 
                msg.send()

@app.task
def HinyangoNonHierarchyChangeTasks():
    '''Note we are working in the public schema until the connection is set to a particular tenant
       -------------------------------------------------------------------------------------------'''
    clients = Client.objects.all().exclude(schema_name='public')
    current_date = datetime.now().replace(tzinfo=None).date()
    for client in clients:        
        connection.set_tenant(client)
        # Get projects to close
        close_projects = nhc.objects.filter(action__action='close',dateofaction_start = datetime.now().date())
        if close_projects:
            projects = [itm.projectmap for itm in close_projects]
            closed = UserProjects.objects.filter(projectmap__in=projects)
            closed_perm = ViewPerms.objects.get(viewing_perms = 'closed')
            hinyango = User.objects.get(username='Hinyango')
            for itms in closed:
                Inbox.send_message(hinyango,'Hinyango',itms.project_user.user,'Project Closure - {0}'.format(itms.projectmap.project_name),'Scheduled project closure was completed today.')
                itms.project_perms = closed_perm
                itms.save()

@app.task
def ScoringTableUpdate():
    '''Note we are working in the public schema until the connection is set to a particular tenant
       -------------------------------------------------------------------------------------------'''
    clients = Client.objects.all().exclude(schema_name='public')
    for client in clients:
        connection.set_tenant(client)
        try:
            sdef = scoringdef()
            sdef.basedsets()
        except ObjectDoesNotExist:
            pass

@app.task
def ReportingRun():
    '''Note we are working in the public schema until the connection is set to a particular tenant
       For scheduled reports

       1. Delete old reporting files - 48 hours ????
       2. Read daily schedule find reporting actions
       3. Process reporting - run reports
       4. Deliver new reports into user reporting tables
       - Note this requires the creation of a new page with the report listings for download
       -------------------------------------------------------------------------------------------'''
    clients = Client.objects.all().exclude(schema_name='public')

    for client in clients:        
        connection.set_tenant(client)
        sr = ScheduledReports.objects.filter(run_immediate=False)

        dn = datetime.now().date()
        for itms in sr:
            if dn >= itms.scheduled_run_date:

                # Date rules
                rule_weekly = rrulestr('RRULE:FREQ=WEEKLY',dtstart=itms.scheduled_run_date)
                rule_monthly = rrulestr('RRULE:FREQ=MONTHLY',dtstart=itms.scheduled_run_date)
                rule_quarterly = rrulestr('RRULE:FREQ=MONTHLY;INTERVAL=3',dtstart=itms.scheduled_run_date)

                # Rule Action Variables
                rw = rule_weekly.after(datetime.now()+timedelta(days=-1)).date()
                rm = rule_monthly.after(datetime.now()+timedelta(days=-1)).date()
                rq = rule_quarterly.after(datetime.now()+timedelta(days=-1)).date()

                # Workout which report needs to be run
                if (itms.data['report_schedule'] == 's-execute-once' and itms.run_count == 0) or (itms.data['report_schedule'] == 's-execute-daily') or (itms.data['report_schedule'] == 's-execute-weekly' and dn == rw) or (itms.data['report_schedule'] == 's-execute-monthly' and dn == rm) or (itms.data['report_schedule'] == 's-execute-quarterly' and dn == rq):
                    report_config = rc.reports[itms.report_id]
                    report_object = module_import(report_config['app']+'.'+report_config['package']+'.'+report_config['report'])()
                    msg = report_object.data_distribution(itms)

@app.task
def ReportingCleanup():
    '''Note we are working in the public schema until the connection is set to a particular tenant
       For scheduled reports

       1. Delete old reporting files - 48 hours ????
       2. Read daily schedule find reporting actions
       3. Process reporting - run reports
       4. Deliver new reports into user reporting tables
       - Note this requires the creation of a new page with the report listings for download
       -------------------------------------------------------------------------------------------'''

    clients = Client.objects.all().exclude(schema_name='public')
    for client in clients:
        connection.set_tenant(client)
        fa = FilesAvailable.objects.all()
        for report in fa:
            if (arrow.now().date() - arrow.get(report.created_on).date()).days > settings.REPORT_AVAILABLE_DAYS:
                report_location = reportloc(report.report_name)
                try:
                    os.unlink(report_location)
                except FileNotFoundError:
                    report.delete()
                else:
                    report.delete()
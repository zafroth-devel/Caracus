from django.db import connection
from cctenants.models import Client
from ccprojects.models import ProjectChange as pc
from django.contrib.auth.models import User
from ccprojects.models import UserProjects
from ccprojects.models import ProjectStructure
from ccutilities.utilities import get_all_tenants
from ccmaintainp.models import HinyangoSettings
from django.db.models import Max,F
from datetime import datetime,timedelta
from ccutilities.arangodb_utils import hierarchy as hr
from directmessages.apps import Inbox
from django.core.mail import EmailMultiAlternatives


clients = Client.objects.all().exclude(schema_name='public').values()
dandywidgets = Client.objects.get(schema_name='dandywidgets')
connection.set_tenant(dandywidgets)
print(connection.schema_name)


max_parameter = HinyangoSettings.objects.filter(cmdtag='hinyango reminders').aggregate(Max('cmdparameter'))

current_date = datetime.now().replace(tzinfo=None).date()

pchange = pc.objects.filter(type_required='Change',inactive_date=None,confirmed__confirmed='No')

id_exclusions = []
for itm in pchange:
    match_date = itm.start_date.replace(tzinfo=None).date() - timedelta(days=int(max_parameter['cmdparameter__max']))
    startdate = itm.start_date.replace(tzinfo=None).date()
    print('{0} - {1} - {2}'.format(current_date,match_date,startdate))
    if (current_date >= match_date and current_date <= startdate) or (startdate < current_date):
        print('including')
    else:
        print('excluding')
        id_exclusions.append(itm.id)

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

newlist = []
change_group_key = 0
for itm in change_data:
    if itm['change_group_key'] != change_group_key:
        newlist.append(itm)
        change_group_key = itm['change_group_key']

change_data = newlist

hierarchy = hr()

bu_dict = {}
for itm in change_data:
    hier = hierarchy.get_selected(project_id = itm['project_id'],change_id = itm['change_group_key'])
    bu_list = []
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
hinyango = User.objects.get(username='Hinyango')
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
from abc import ABCMeta, abstractmethod
from config.celery import app
import uuid
from ccreporting.models import ScheduledReports,FilesAvailable
from ccaccounts.models import AccountProfile
import os
from ccutilities.utilities import residenttenant
from django.conf import settings
from datetime import datetime
import csv
import ccreporting.reportingconfig as rc
from ccutilities.module_utilities import module_import
from cctenants.models import Client
from django.db import connection
from django.core.mail import EmailMultiAlternatives
from directmessages.apps import Inbox
from django.contrib.auth.models import User
from seaborn import husl_palette as hsp

class getColorPalette():
    def __init__(self,cnum=10):
        self.number_of_colors = cnum
    def getHexList(self):
        background = hsp(self.number_of_colors).as_hex()
        border = hsp(self.number_of_colors,l=.7).as_hex()
        colorlist = {}
        for itm in range(0,self.number_of_colors):
            colorlist[itm+1] = [background[itm],border[itm]]
        return colorlist

def reportloc(filename):
    return os.path.join(getattr(settings,"BASE_DIR",None),getattr(settings,"REPORT_UPLOAD_LOCATION",None),residenttenant(),filename)

def reportlist(schedule,fileidentifier,mime):
    cuser = schedule.reporting_request
    FilesAvailable.objects.create(reporting_request=cuser,
                                  report_name=fileidentifier,
                                  server_location=getattr(settings,"REPORT_UPLOAD_SSHSERVER",None),
                                  path_on_server=getattr(settings,"REPORT_UPLOAD_LOCATION",None),
                                  mime_type=mime)

# Data context method used to inforce procedures for vega charts
class DataContext(metaclass=ABCMeta):
    @abstractmethod
    def json_data(self):
        raise(NotImplementedError("Json data method not implemented"))
    def vega_config(self):
        raise(NotImplementedError("Config method not implemented"))

# Dump queryset data into a file
def qsetdump(qs,fileidentifier,delimiter='csv'):
    if str(type(qs)) == "<class 'django.db.models.query.QuerySet'>":
        if delimiter == 'tab':
            csvd = 'excel-tab'
        elif delimiter == 'pipe':
            csv.register_dialect('pipe', delimiter='|')
            csvd = 'pipe'
        elif delimiter =='unix':
            csvd = 'unix'
        else:
            csvd = 'excel'
        headers = dict((n,n) for n in list(qs.values()[0].keys()))

        try:
            with open(fileidentifier, 'wt') as f:
                writer = csv.DictWriter(f,fieldnames=headers,dialect=csvd)
                writer.writerow(headers)
                for itms in qs.values():
                    writer.writerow(itms)
        except IOError as error:
            return {'status','failed'}
        return {'status':'success'}
    else:
        return {'status':'failed'}

def email_clients(srobject):
    from_email = 'hinyango@hinyango.com.au'
    hinyango = User.objects.get(username='Hinyango')
    message_title = '<p><h5>Requested report has completed</h5></p>'
    message_body = '<p>'+srobject.report_name+'-id:'+str(srobject.report_id)+' has completed. </p> <p>Go to downloads page to download report. Report will remain for '+str(settings.REPORT_AVAILABLE_DAYS)+' days before being deleted.</p>'
    message_footer = '<hr><p>Sent by Hinyango on {0} at {1}</p>'.format(datetime.now().date(),datetime.now().time())
    subject = 'Report '+srobject.report_name+' has been run.'
    message_output = message_title+message_body+message_footer

    text_content = 'Requested report has completed.\n'+srobject.report_name+'-id:'+str(srobject.report_id)+' has completed.\nGo to downloads page to download report. Report will remain for '+str(settings.REPORT_AVAILABLE_DAYS)+' days before being deleted.'

    # Send Hinyango message
    Inbox.send_message(hinyango, 'Hinyango', User.objects.get(username=srobject.reporting_request.user.username), subject, message_output)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [srobject.reporting_request.user.email])
    msg.attach_alternative(message_output, "text/html") 
    msg.send()


@app.task
def execute_immediate(schedule_id,tenant):
    '''
    Post handling helper
    Execute background process immediately
    Not sure how to do this

    Issued as a delay using the schedule_id
    Entry deleted as last requirement

    '''

    # Anything scheduled works in the Public schema
    client = Client.objects.get(schema_name=tenant)

    connection.set_tenant(client)

    sr = ScheduledReports.objects.get(id=schedule_id)
    report_config = rc.reports[sr.report_id]

    # Load module
    report_object = module_import(report_config['app']+'.'+report_config['package']+'.'+report_config['report'])()

    # Run report
    msg = report_object.data_distribution(sr)

    print(msg)



def fileidentifier(srobject,ftype='pdf'):

    if '.' in ftype:
        ftype = ftype.replace('.','')

    if ftype == 'pdf':
        fileext = '.pdf'
    else:
        fileext = '.txt'

    filename = os.path.join(getattr(settings,"BASE_DIR",None),getattr(settings,"REPORT_UPLOAD_LOCATION",None),residenttenant())
    
    if not os.path.isdir(filename):
        # Create folder 
        os.makedirs(name=filename,exist_ok=True)

    fileidentifier = 'Report-'+(srobject.report_name).replace(' ','_')+'-'+srobject.reporting_request.user.username+'-SID'+str(srobject.id)+'-RID'+str(srobject.report_id)+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')+fileext
    #filename = os.path.join(filename,residenttenant()+'-'+fileidentifier)

    return fileidentifier

class ReportingContext(metaclass=ABCMeta):

    @abstractmethod
    def report_information(self):
        elements = {}
        elements['title'] = uuid.uuid4()
        elements['description'] = 'New hinyango report'
        return elements

    @abstractmethod
    def form_elements(self):
        '''
        This method provides controls that are placed in the reporting window
        '''

        # Add standard schedule elements
        # ------------------------------

        elements = {}

        fieldlist = []
        fieldlist = [{'name':'h-report-schedule',
                      'label':'Reporting Schedule',
                      'required':True,
                      'type':'select',
                      'target':'',
                      'class':'form-control',
                      'default':'s-execute-once',
                      'choices':[{'name':'Execute immediately','value':'s-execute-immediate'},
                                 {'name':'One run delayed','value':'s-execute-once'},
                                 {'name':'Daily','value':'s-execute-daily'},
                                 {'name':'Weekly','value':'s-execute-weekly'},
                                 {'name':'Monthly','value':'s-execute-monthly'},
                                 {'name':'Quarterly','value':'s-execute-quarterly'}]}]

        elements['form_elements_1'] = fieldlist

        fieldlist = []
        fieldlist.append({'name':'h-report-start-date',
                          'label':'Reporting Start Date',
                          'type':'cdate',
                          'target':'',
                          'required':True,
                          'class':'form-control'})

        elements['form_elements_2'] = fieldlist

        return elements

    @abstractmethod
    def post_handling(self,request_data,request_user,conduit):
        '''
        This method handles the incoming post elements related to the specific report being handled
        Note this is to handle a static call there is no guarantee that it will be the same instance
        '''

        raise(NotImplementedError("Post handling not implemented"))

    @abstractmethod
    def data_distribution(self):
        '''
        This method is the actual report
        Has the code run by the app task.
        '''
        raise(NotImplementedError("Data distribution not implemented"))


    @abstractmethod
    def add_to_schedule(self,username,report_name,report_id,parameters,scheduled_run_date,immediate=True):
        '''
        Post handling helper
        Schedule a repeated process
        If immediate = False add to schedule and thats it
        If immediate = True add to schedule and then process with execute_immediate

        Add any run paramters to a postgres hstore 
        '''
        profile = AccountProfile.objects.get(user__username=username)
        sr = ScheduledReports.objects.create(reporting_request=profile,report_name=report_name,report_id=report_id,data=parameters,scheduled_run_date=scheduled_run_date,run_immediate=immediate)
        if immediate == True:
            execute_immediate.delay(sr.id,residenttenant())





        
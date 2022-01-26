from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType,ProjectChange
from django.db.models import Count,Min,Max
import pandas as pd
from ccutilities.reporting_utils import ReportingContext,fileidentifier,qsetdump,reportlist,reportloc,email_clients
import arrow
from django.contrib import messages
from ccreporting.models import ScheduledReports,FilesAvailable
from ccaccounts.models import AccountProfile
from pylatex import Document, LongTabu, HFill,Command
from pylatex.utils import bold
import datetime

# Report context classes go here one for each report
class changereport(ReportingContext):

    def report_information(self):
        info = super().report_information()
        info['title'] = 'Change Data Listing'
        info['description'] = 'Tabulated change related data'
        info['report_id'] = 1
        return info

    def form_elements(self):
        elements = super().form_elements()

        fieldlist = [{'name':'change-start-date',
                      'label':'Start Date',
                      'type':'cdate',
                      'target':'',
                      'required':True,
                      'class':'form-control'}]

        elements['element_start_date'] = fieldlist

        fieldlist = [{'name':'change-end-date',
                      'label':'End Date',
                      'type':'cdate',
                      'target':'',
                      'required':True,
                      'class':'form-control'}]

        elements['element_end_date'] = fieldlist

        fieldlist = [{'name':'h-report-type',
                     'label':'Report type',
                     'required':True,
                     'type':'mselect',
                     'target':'',
                     'class':'multiselect form-control',
                     'default':'r-return-data',
                     'choices':[{'name':'PDF Report','value':'r-return-pdf'},
                                {'name':'Data Dump','value':'r-return-data'}]}]

        elements['allowed_report_types'] = fieldlist

        return elements

    def post_handling(self,request_data,request_user,conduit):
        # Convert parameters into a key-value pair
        # Check parameters and issue message if not correct

        report_id = request_data['report-id'][0]
        report_name = request_data['report-name'][0]

        print(request_data['h-report-schedule'][0])

        if request_data['h-report-schedule'][0] == 's-execute-immediate':
            immediate = True
        else:
            immediate = False

        reporting_parameters = {}
        reporting_parameters['report_schedule'] = request_data['h-report-schedule'][0]
        reporting_parameters['schedule_start_date'] = request_data['h-report-start-date'][0]
        reporting_parameters['change_start_date'] = request_data['change-start-date'][0]
        reporting_parameters['change_end_date'] = request_data['change-end-date'][0]
        reporting_parameters['report_type'] = request_data['h-report-type']


        start_date = arrow.get(reporting_parameters['change_start_date'], 'YYYY-MM-DD')
        end_date = arrow.get(reporting_parameters['change_end_date'],'YYYY-MM-DD')

        if end_date < start_date:
            messages.error(conduit, 'The date parameters are incorrect end date must be after start date')
        else:
            self.add_to_schedule(username=request_user,report_name=report_name,report_id=report_id,parameters=reporting_parameters,scheduled_run_date=arrow.get(request_data['h-report-start-date'][0],'YYYY-MM-DD').date(),immediate=immediate)
            messages.success(conduit, 'Report request has been submitted')

    def data_distribution(self,sr):
        """
        Use the parameters to render the report
        
        Name:Report_name-username-schedule_id-report_id-date.extension
        Path: From settings

        """

        # Query reporting table - Testing only
        # ---------------------
        #sr = ScheduledReports.objects.get(id=report_schedule_id)

        # Reports completed
        # -----------------
        completed = []
        fileid = 0

        # Check report id
        # ---------------
        if sr.report_id != self.report_information()['report_id']:
            sr.run_result = 'Wrong report requested'
            sr.save()
            return {'result':1,'message':'ERROR: requested report id did not match code report id'}
        else:
            # ----------------------------------------------------------------------------------------
            #                       Create reports to match parameters                               #
            # ----------------------------------------------------------------------------------------

            geometry_options = {
                "landscape": True,
                "margin": "0.5in",
                "headheight": "20pt",
                "headsep": "10pt",
                "includeheadfoot": True
            }

            report_data = ProjectChange.objects.all()

            if 'r-return-pdf' in sr.data['report_type']:

                filename = fileidentifier(sr,'pdf')

                doc = Document(page_numbers=True, geometry_options=geometry_options)
    
                doc.documentclass = Command('documentclass',options=['a4paper'],arguments=['article'])
    
                with doc.create(LongTabu("X[r] X[r] X[r] X[r] X[r]")) as data_table:
                    header_row1 = ["Project", "Type", "Nickname", "Question", "Answer"]
                    data_table.add_row(header_row1, mapper=[bold])
                    data_table.add_hline()
                    data_table.add_empty_row()
                    data_table.end_table_header()
                    for itm in report_data:
                        row = [itm.projectmap.project_name,itm.type_required,itm.nickname,itm.question.question,itm.answers.answers]
                        data_table.add_row(row)

                doc.generate_pdf(reportloc(filename[:-4]), clean_tex=True)
                fileid = fileid + 1
                completed.append({'filename':filename+'.pdf','type':'application/pdf','fileid':fileid})
                reportlist(schedule=sr,fileidentifier=filename,mime='application/pdf')

            if 'r-return-data' in sr.data['report_type']:
                filename = fileidentifier(sr,'csv')
                qsetdump(report_data,reportloc(filename))
                fileid = fileid + 1
                print(fileid)
                completed.append({'filename':filename,'type':'text/plain','fileid':fileid})
                reportlist(schedule=sr,fileidentifier=filename,mime='text/plain')


            if len(completed) > 0:
                sr.report_file_identifier = {'report_names':completed}
                sr.run_result = 'Files available'
                sr.report_run_date = datetime.datetime.now().date()
                sr.report_available = True
                sr.run_count = sr.run_count + 1
                sr.save()
                email_clients(sr)

            return {'result':0,'message':'Success - Report run no errors'}

            # ----------------------------------------------------------------------------------------

    def add_to_schedule(self,username,report_name,report_id,parameters,scheduled_run_date,immediate):
        super().add_to_schedule(username,report_name,report_id,parameters,scheduled_run_date,immediate)


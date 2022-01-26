from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType,ProjectChange
from django.db.models import Count,Min,Max
import pandas as pd
from ccutilities.reporting_utils import ReportingContext

# Report context classes go here one for each report
class countreport(ReportingContext):

    def report_information(self):
        info = super().report_information()
        info['title'] = 'Count Data Listing'
        info['description'] = 'Tabulated count related data'
        return info

    def form_elements(self):
        elements = super().form_elements()

        fieldlist = [{'name':'h-report-type',
                     'label':'Report type',
                     'required':True,
                     'type':'mselect',
                     'target':'',
                     'class':'multiselect form-control',
                     'default':'r-return-pdf',
                     'choices':[{'name':'PDF Report','value':'r-return-pdf'},
                                {'name':'Data Dump','value':'r-return-data'}]}]

        elements['allowed_report_types'] = fieldlist

        return elements

    def post_handling(self,request_data,request_user):
        print('In post handling 2')
        print(request_data)
        print(request_user)

    def data_distribution(self):
        pass

    def add_to_schedule(self,username,report_name,report_id,parameters,immediate):
        super().add_to_schedule(username,report_name,report_id,parameters,immediate)


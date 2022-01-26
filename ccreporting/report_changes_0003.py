from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType,ProjectChange
from django.db.models import Count,Min,Max
import pandas as pd
from ccutilities.reporting_utils import ReportingContext

# Report context classes go here one for each report
class levelreport(ReportingContext):

    def report_information(self):
        info = super().report_information()
        info['title'] = 'Level Data Listing'
        info['description'] = 'Tabulated level related data'
        return info

    def form_elements(self):
        elements = super().form_elements()
        
        return elements

    def post_handling(self,request_data,request_user):
        print('In post handling 3')
        print(request_data)
        print(request_user)

    def data_distribution(self):
        pass

    def add_to_schedule(self,username,report_name,report_id,parameters,immediate):
        super().add_to_schedule(username,report_name,report_id,parameters,True)


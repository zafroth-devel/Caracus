from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType,ProjectChange
from django.db.models import Count,Min,Max
import pandas as pd
from ccutilities.reporting_utils import ReportContext

# Report context classes go here one for each report
class QuestionTypeCounts(ReportContext):

    def __init__(self):
        self.pc = list(ProjectChange.objects.filter(type_required='Change').values('id', 'groupkey_id', 'question_id'))
        self.qg = QuestionGroup.objects.all().values('id','type_required_id')
        self.qt = QuestionType.objects.filter(question_level='Change').values('id','question_type')

    def report_context(self,context):
        context['reporting_data'] = self.extract_data()
        context['report_title'] = 'Question Type Counts'
        return(context)

    def extract_data(self):
        if self.pc and self.qg and self.qt:

            qt_dict = {}
            for item in self.qt:
                qt_dict[item['id']] = item['question_type']

            qg_dict = {}
            for item in self.qg.filter(type_required_id__in=list(qt_dict.keys())):
                qg_dict[item['id']] = qt_dict[item['type_required_id']]
    
            for item in self.pc:
                item['question_type'] = qg_dict[item['question_id']]
    
            reporting_dict = pd.DataFrame(self.pc).groupby(['question_type']).size().reset_index(name='count').to_dict('records')
            return(reporting_dict)
        else:
            pass

    def get_template_location(self):

        return(['ccreporting/accordian.html'])
        # if self.pc and self.qg and self.qt:
        #     return(['ccreporting/reporting_template.html'])
        # else:
        #     return(['ccreporting/report_missing_error.html'])

    def report_download(self):
        pass

# class ListOfProjects(ReportContext):
#     def report_context(self):
#         return("List Of Projects")
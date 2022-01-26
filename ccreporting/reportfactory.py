'''
Title: Report factory context
Author: Matthew May
Date: 
Notes: Here is where we add a particular chart
Notes:
''' 
from ccreporting.report_type_0001 import QuestionTypeCounts

class ReportFactory:
    def get_report_context(self,report_id):
        if report_id == 1:
            return(QuestionTypeCounts())
        # elif report_id == 2:
        #     return(ListOfProjects(context))
        else:
            raise(NotImplementedError("Unknown report type."))



# factory = ReportFactory()
# report = factory.get_report_context(1)
# print(report.report_context())
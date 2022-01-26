from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType
from ccchange.models import ProjectChange
from django.db.models import Count,Min,Max
import pandas as pd
from ccutilities.reporting_utils import ReportingContext,fileidentifier,qsetdump,reportlist,reportloc,email_clients
import arrow
from django.contrib import messages
from ccreporting.models import ScheduledReports,FilesAvailable
from ccaccounts.models import AccountProfile
import datetime
from ccutilities.arangodb_utils import hierarchy
from PIL import Image as PIL_Image
from graphviz import Digraph
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4,A3 # A4 - 210 x 297 mm or 8.27 × 11.69 :: A3 297 × 420 millimeters or 11.69 × 16.54
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image as RImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import colorlover as cl # '#%02x%02x%02x' % rgb as tuple
from reportlab.lib.units import inch, cm, mm
import reportlab.lib, reportlab.platypus
from reportlab.lib.enums import TA_CENTER


class flowable_line(reportlab.platypus.Flowable):
    def __init__(self, width, height=0):
        reportlab.platypus.Flowable.__init__(self)
        self.width = width
        self.height = height
    def __repr__(self):
        return "Line(w=%s)" % self.width
    def draw(self):
        self.canv.line(0, self.height, self.width, self.height)


class flowable_fig(reportlab.platypus.Flowable):
    def __init__(self, imgdata, _height, _width):
        reportlab.platypus.Flowable.__init__(self)
        self.img = reportlab.lib.utils.ImageReader(imgdata)
        self.width = _width
        self.height = _height
    def draw(self):
        self.canv.drawImage(self.img, 0, 0, height = self.height, width=self.width)



# Report context classes go here one for each report
class hierarchyreport(ReportingContext):

    def report_information(self):
        info = super().report_information()
        info['title'] = 'Organisation Hierarchy'
        info['description'] = 'Plot of current hierarchy'
        info['report_id'] = 1
        return info

    def form_elements(self):
        elements = super().form_elements()

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
        fileid = 1

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


            dot = Digraph('Standard',node_attr={'shape': 'rectangle'})
            
            dot.attr(rankdir='LR',size='11.69,16.54',dpi='300')
            
            h = hierarchy()
            
            nodes = h.get_nodes()
            edges = h.get_edges()
            levels = h.get_level_data()['levels_nodes']
            
            total_levels = max(list(h.get_level_data()['node_levels'].keys()))
            
            # map colors to levels
            if total_levels > 2 and total_levels < 11:
                bupu_scale = cl.scales[str(total_levels)]['div']['RdYlBu']
            elif total_levels < 3:
                bupu_scale = cl.scales['3']['div']['RdYlBu']
            else:
                bupu = cl.scales['11']['div']['RdYlBu']
                bupu_scale = cl.interp( bupu, total_levels)
            
            bupu_scale_hex = ['#%02x%02x%02x' % (int(itm[0]),int(itm[1]),int(itm[2])) for itm in cl.to_numeric(bupu_scale)]
            
            for node in nodes['result']['result']:
                color_code = bupu_scale_hex[levels[node['id']]-1]
                # Level up the colors
                dot.attr('node',fontcolor='grey18',color='grey',style='filled',fillcolor=color_code)
                dot.node(node['name'],node['bu'])
            
            for edge in edges['result']['result']:
                dot.edge(edge['from'].split('/')[1],edge['to'].split('/')[1])
            
            dot.format = 'png'
            
            imgdata = io.BytesIO()
            
            imgdata.write(dot.pipe())
            
            imgdata.seek(0)  
            
            img = PIL_Image.open(imgdata)
            
            #IMAGE = ImageReader(img)
            
            width,height = A3

            filename = fileidentifier(sr,'pdf')
            
            print(reportloc(filename))

            doc = SimpleDocTemplate(reportloc(filename),pagesize=A3,rightMargin=1,leftMargin=1,topMargin=1,bottomMargin=1)
            styles = getSampleStyleSheet()
            report = []
            
            styles=getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Centered', alignment=TA_CENTER))
            ptext = '<font name=helvetica size=24><b>Organisation Chart</b></font>'
            report.append(Paragraph(ptext, styles["Centered"]))
            spacer = Spacer(width=0, height=20)
            report.append(spacer)
            line = flowable_line(width*.98)
            report.append(line)
            spacer = Spacer(width=0, height=50)
            report.append(spacer)
            
            pic = flowable_fig(img,height*.9,width*.9)
            
            report.append(pic)
            
            doc.build(report)

            completed.append({'filename':filename,'type':'application/pdf','fileid':fileid})
            
            reportlist(schedule=sr,fileidentifier=filename,mime='application/pdf')

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

